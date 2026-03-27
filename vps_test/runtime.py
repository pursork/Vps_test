from __future__ import annotations

import json
import os
import shutil
import signal
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from vps_test.definitions import TEST_DEFINITIONS, TestDefinition
from vps_test.reporting import strip_ansi

try:
    import pexpect
except Exception:  # pragma: no cover
    pexpect = None

COMMAND_OVERRIDES = {
    1: "printf '\\n\\n\\n\\n' | bash ./{name}",
    2: "chmod +x ./{name} && bash ./{name} -m 1",
    6: "printf '\\n' | bash ./{name}",
    7: "printf '\\n' | bash ./{name}",
    8: "chmod +x ./{name} && bash ./{name} -y",
    12: "printf '\\n' | bash ./{name}",
    13: "printf '1\\n' | bash ./{name}",
}

SUCCESS_MARKERS = {
    1: ["测试完成，点击查看你的结果链接：", "click to view your result link"],
    8: ["报告链接：https://Report.Check.Place/ip/", "Report link: https://Report.Check.Place/ip/"],
}


@dataclass
class TestRunResult:
    index: int
    name: str
    command: str
    workdir: str
    raw_output_path: str
    clean_output_path: str
    exit_code: int | None
    effective_exit_code: int | None
    duration_seconds: float
    timed_out: bool
    used_local_raw: bool
    source_path: str | None = None
    completion_marker: str | None = None
    error: str | None = None


def _prepare_command(test: TestDefinition, raw_dir: Path, workdir: Path) -> tuple[str, bool, str | None]:
    raw_path = raw_dir / test.filename_hint
    if raw_path.exists():
        target = workdir / raw_path.name
        shutil.copy2(raw_path, target)
        if test.kind == "binary":
            return f"chmod +x ./{target.name} && ./{target.name}", True, str(target)
        if test.index in COMMAND_OVERRIDES:
            return COMMAND_OVERRIDES[test.index].format(name=target.name), True, str(target)
        if test.index == 11:
            return f"sh ./{target.name}", True, str(target)
        return f"chmod +x ./{target.name} && bash ./{target.name}", True, str(target)
    return test.command, False, None


def _spawn_and_capture(command: str, workdir: Path, raw_output_path: Path, timeout_seconds: int) -> tuple[int | None, bool, str | None]:
    if pexpect is None:
        raise RuntimeError("pexpect 不可用，当前环境无法执行带交互容错的本地测试。")

    env = os.environ.copy()
    env.update(
        {
            "TERM": "xterm",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "DEBIAN_FRONTEND": "noninteractive",
        }
    )

    with raw_output_path.open("w", encoding="utf-8", errors="replace") as logfile:
        child = pexpect.spawn(
            "/usr/bin/env",
            ["bash", "-lc", command],
            cwd=str(workdir),
            env=env,
            encoding="utf-8",
            codec_errors="replace",
            timeout=8,
        )
        child.logfile = logfile
        started = time.monotonic()
        replies = 0
        max_replies = 12
        patterns = [
            r"(?i)\[[[:space:]]*[yY]/[nN][[:space:]]*\]",
            r"(?i)\((?:y|yes)/(?:n|no)\)",
            r"(?i)yes/no",
            r"(?i)continue\?",
            r"(?i)press (enter|return)",
            r"(?i)(?:choose|choice|select)[^\n]*:",
            r"(?i)请输入[^\n]*[:：]?",
            pexpect.EOF,
            pexpect.TIMEOUT,
        ]
        timed_out = False

        while True:
            if time.monotonic() - started > timeout_seconds:
                timed_out = True
                if child.isalive():
                    child.kill(signal.SIGTERM)
                break

            match = child.expect(patterns)
            if match in {0, 1, 2, 3} and replies < max_replies:
                child.sendline("y")
                replies += 1
                continue
            if match in {4, 5, 6} and replies < max_replies:
                child.sendline("")
                replies += 1
                continue
            if match == 7:
                break
            if match == 8:
                continue

        child.close(force=True)
        exit_code = child.exitstatus
        if exit_code is None and child.signalstatus is not None:
            exit_code = 128 + child.signalstatus
        return exit_code, timed_out, None


def _detect_completion_marker(index: int, text: str) -> str | None:
    for marker in SUCCESS_MARKERS.get(index, []):
        if marker in text:
            return marker
    return None


def execute_suite(root: Path, output_root: Path, timeout_seconds: int, label: str | None = None) -> Path:
    if os.name == "nt":
        raise RuntimeError("本地执行器目标环境是 Debian/Linux，请在远程 VPS 上运行。")

    run_id = label or time.strftime("%Y%m%d_%H%M%S")
    run_dir = output_root / run_id
    raw_dir = root / "raw"
    run_dir.mkdir(parents=True, exist_ok=True)
    results: list[TestRunResult] = []

    for test in TEST_DEFINITIONS:
        test_dir = run_dir / f"{test.index:02d}_{test.name}"
        test_dir.mkdir(parents=True, exist_ok=True)
        raw_output_path = test_dir / "raw_output.txt"
        clean_output_path = test_dir / "clean_output.txt"
        started = time.monotonic()

        command, used_local_raw, source_path = _prepare_command(test, raw_dir, test_dir)
        exit_code: int | None = None
        timed_out = False
        error: str | None = None

        try:
            exit_code, timed_out, error = _spawn_and_capture(command, test_dir, raw_output_path, timeout_seconds)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        if raw_output_path.exists():
            clean_text = strip_ansi(raw_output_path.read_text(encoding="utf-8", errors="replace"))
            clean_output_path.write_text(clean_text, encoding="utf-8")
        else:
            clean_text = error or ""
            clean_output_path.write_text(clean_text, encoding="utf-8")

        completion_marker = _detect_completion_marker(test.index, clean_text)
        effective_exit_code = 0 if completion_marker and exit_code not in {0, None} else exit_code

        results.append(
            TestRunResult(
                index=test.index,
                name=test.name,
                command=command,
                workdir=str(test_dir),
                raw_output_path=str(raw_output_path),
                clean_output_path=str(clean_output_path),
                exit_code=exit_code,
                effective_exit_code=effective_exit_code,
                duration_seconds=round(time.monotonic() - started, 2),
                timed_out=timed_out,
                used_local_raw=used_local_raw,
                source_path=source_path,
                completion_marker=completion_marker,
                error=error,
            )
        )

    results_path = run_dir / "results.json"
    results_path.write_text(
        json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return run_dir
