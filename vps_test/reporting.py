from __future__ import annotations

import json
import re
from pathlib import Path


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text).replace("\r\n", "\n").replace("\r", "\n")


def load_template_headers(template_path: Path) -> list[str]:
    headers = []
    for line in template_path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\d+\.\s", line):
            headers.append(line)
    return headers


def render_template(template_path: Path, results_json_path: Path, output_path: Path) -> None:
    headers = load_template_headers(template_path)
    results = json.loads(results_json_path.read_text(encoding="utf-8"))
    blocks = []

    for idx, header in enumerate(headers, start=1):
        result = next((item for item in results if item["index"] == idx), None)
        output = "未执行"
        if result is not None:
            clean_output_path = Path(result["clean_output_path"])
            if clean_output_path.exists():
                output = strip_ansi(clean_output_path.read_text(encoding="utf-8", errors="replace")).strip()
            elif result.get("error"):
                output = f"执行失败: {result['error']}"
            else:
                output = f"执行结束，退出码: {result.get('exit_code')}"
        blocks.append(f"{header}\n{output or '无输出'}")

    output_path.write_text("\n".join(blocks).strip() + "\n", encoding="utf-8")
