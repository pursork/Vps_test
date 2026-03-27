from __future__ import annotations

import json
import re
from pathlib import Path

# ── 常量 ─────────────────────────────────────────────────────────────────────

_SPINNER_CHARS = set("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏|/-\\")
_BLOCK_CHARS   = set("█║╗╝═╔╚╠╣╦╩╬▀▄")

# ── 正则 ─────────────────────────────────────────────────────────────────────

# spinner 行：含 spinner 字符 + 以数字% 结尾
_SPINNER_LINE_RE  = re.compile(r"[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏].{0,10}\d+%\s*$")

# 赞助商横幅：同一大写词重复 ≥4 次
_BANNER_RE        = re.compile(r"^([A-Z]{3,})\1{3,}")

# wget # 进度条（两种格式）
_WGET_BAR_RE      = re.compile(r"^\s*[#=\s]{3,}\s+\d+\.?\d*%\s*$")
_WGET_BAR2_RE     = re.compile(r"^\s*[#=]{2,}")

# curl 统计表头 / 数据行
_CURL_HEADER_RE   = re.compile(r"^\s*%\s+Total\s+%\s+Received")
_CURL_DATA_RE     = re.compile(r"^\s*\d+\s+\d+[\d.]*[kMGT]?\s+\d+")

# wget 进度条（文件名+百分比+方括号）
_WGET_PROG_RE     = re.compile(r"^\s*[\w./\-_]+\s+\d+%\[")

# wget 保存完成行
_WGET_SAVED_RE    = re.compile(r"\d{4}-\d{2}-\d{2}.*saved \[")

# apt/dpkg 百分比进度（如 "0% [Working]"）
_APT_WORKING_RE   = re.compile(r"^\d+% \[")

# (Reading database ... XX%)
_APT_DB_RE        = re.compile(r"^\(Reading database\s")

# zip 压缩输出
_ZIP_RE           = re.compile(r"^\s+adding:\s+.+\(compressed \d+%\)")

# Broken pipe 错误
_BROKEN_PIPE_RE   = re.compile(r"write error: Broken pipe")

# ── 前缀过滤（startswith 匹配，效率高）──────────────────────────────────────

_APT_PREFIXES = (
    "Reading package lists",
    "Building dependency tree",
    "Reading state information",
    "The following additional packages",
    "The following NEW packages",
    "The following packages will be upgraded",
    "Need to get",
    "After this operation",
    "Fetched ",
    "Selecting previously unselected package",
    "Preparing to unpack",
    "Unpacking ",
    "Setting up ",
    "Processing triggers for",
    "Preconfiguring packages",
    "0 upgraded,",
    "Get:",
)

_WGET_PREFIXES = (
    "--20",           # --2026-03-27 20:13:06--
    "Resolving ",
    "Connecting to ",
    "HTTP request sent",
    "Location: http",
    "Reusing existing connection",
    "Length: ",
    "Saving to: ",
)


# ── 核心判断函数 ──────────────────────────────────────────────────────────────

def _is_noise_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False

    # spinner 动画行
    if any(c in _SPINNER_CHARS for c in s):
        if _SPINNER_LINE_RE.search(s) or s[-1] in _SPINNER_CHARS:
            return True

    # ASCII 艺术字（块字符占比 >30%）
    block_count = sum(1 for c in s if c in _BLOCK_CHARS)
    if len(s) > 5 and block_count / len(s) > 0.3:
        return True

    # 赞助商横幅
    if _BANNER_RE.match(s):
        return True

    # wget # 进度条
    if _WGET_BAR_RE.match(s) or _WGET_BAR2_RE.match(s):
        return True

    # curl 统计
    if _CURL_HEADER_RE.match(s) or _CURL_DATA_RE.match(s):
        return True

    # wget 进度条 / 保存完成
    if _WGET_PROG_RE.match(s) or _WGET_SAVED_RE.search(s):
        return True

    # apt/dpkg 安装日志
    if s.startswith(_APT_PREFIXES):
        return True
    if _APT_WORKING_RE.match(s) or _APT_DB_RE.match(s):
        return True

    # wget 下载过程
    if s.startswith(_WGET_PREFIXES):
        return True

    # zip 压缩输出
    if _ZIP_RE.match(line):
        return True

    # Broken pipe 错误
    if _BROKEN_PIPE_RE.search(s):
        return True

    return False


# ── 主函数 ───────────────────────────────────────────────────────────────────

def strip_ansi(text: str) -> str:
    # 去掉 ANSI 转义码
    text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)

    # 正确处理 \r：回车符代表"回到行首覆盖"，而非换行
    lines: list[str] = []
    current: list[str] = []
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\r" and i + 1 < len(text) and text[i + 1] == "\n":
            lines.append("".join(current))
            current = []
            i += 2
        elif c == "\r":
            current = []
            i += 1
        elif c == "\n":
            lines.append("".join(current))
            current = []
            i += 1
        else:
            current.append(c)
            i += 1
    if current:
        lines.append("".join(current))

    # 过滤噪音行 + 压缩连续空行
    cleaned: list[str] = []
    blank_streak = 0
    for line in lines:
        if _is_noise_line(line):
            continue
        if line.strip() == "":
            blank_streak += 1
            if blank_streak > 1:
                continue
        else:
            blank_streak = 0
        cleaned.append(line)

    return "\n".join(cleaned)


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

    output_path.write_text("\n\n".join(blocks).strip() + "\n", encoding="utf-8")
