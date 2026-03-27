from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


INTERACTIVE_PATTERNS = {
    "read": re.compile(rb"(^|\W)read(\s|-p|-r)", re.MULTILINE),
    "select": re.compile(rb"(^|\W)select(\W)", re.MULTILINE),
    "whiptail": re.compile(rb"whiptail"),
    "dialog": re.compile(rb"dialog"),
    "stty": re.compile(rb"stty"),
    "tput": re.compile(rb"tput"),
    "clear": re.compile(rb"(^|\W)clear(\W|$)", re.MULTILINE),
}


def classify_interactive(data: bytes) -> tuple[bool, list[str]]:
    hits = [name for name, pattern in INTERACTIVE_PATTERNS.items() if pattern.search(data)]
    return bool(hits), hits


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    raw_dir = root / "raw"
    metadata_path = raw_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    report = []

    for item in metadata:
        saved_path = item.get("saved_path")
        if not saved_path:
            item["interactive_risk"] = "unknown"
            report.append(item)
            continue
        data = (root / saved_path).read_bytes()
        interactive, hits = classify_interactive(data)
        item["interactive_risk"] = "possible" if interactive else "low"
        item["interactive_hits"] = hits
        item["has_ansi"] = b"\x1b[" in data
        item["has_bash_shebang"] = data.startswith(b"#!/bin/bash") or data.startswith(b"#!/usr/bin/env bash")
        report.append(item)

    (raw_dir / "analysis.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"analyzed {len(report)} sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
