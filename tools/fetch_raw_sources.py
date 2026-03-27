from __future__ import annotations

import json
import sys
import urllib3
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vps_test.definitions import TEST_DEFINITIONS


USER_AGENTS = {
    "https://bench.sh": "curl/8.0.1",
    "https://nws.sh": "Wget/1.21.4",
}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    raw_dir = root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (compatible; vps-test-fetcher/1.0)"
    metadata: list[dict[str, object]] = []

    for item in TEST_DEFINITIONS:
        record: dict[str, object] = {
            "index": item.index,
            "name": item.name,
            "command": item.command,
            "source_url": item.source_url,
            "filename": item.filename_hint,
            "kind": item.kind,
        }
        headers = {}
        if item.source_url in USER_AGENTS:
            headers["User-Agent"] = USER_AGENTS[item.source_url]
        try:
            response = session.get(item.source_url, headers=headers, timeout=30, allow_redirects=True, verify=False)
            record["status_code"] = response.status_code
            record["final_url"] = response.url
            record["content_type"] = response.headers.get("content-type", "")
            output_path = raw_dir / item.filename_hint
            output_path.write_bytes(response.content)
            record["saved"] = True
            record["saved_path"] = str(output_path.relative_to(root)).replace("\\", "/")
            record["size"] = len(response.content)
        except Exception as exc:
            record["saved"] = False
            record["error"] = f"{type(exc).__name__}: {exc}"
        metadata.append(record)

    (raw_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {sum(1 for x in metadata if x.get('saved'))}/{len(metadata)} sources to {raw_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
