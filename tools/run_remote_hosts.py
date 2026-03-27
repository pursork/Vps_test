from __future__ import annotations

import argparse
import io
import json
import tarfile
import time
from pathlib import Path

import paramiko

POLL_INTERVAL_SECONDS = 20
MAX_REMOTE_WAIT_SECONDS = 6 * 3600


def build_archive(root: Path) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for path in root.rglob("*"):
            if any(part in {".git", ".venv", "artifacts", "remote_runs", "__pycache__"} for part in path.parts):
                continue
            tar.add(path, arcname=path.relative_to(root))
    buffer.seek(0)
    return buffer.read()


def connect_client(host: str, port: int, username: str, password: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=username, password=password, timeout=20, banner_timeout=20)
    return client


def run_command(client: paramiko.SSHClient, command: str, timeout: int = 120) -> tuple[int, str]:
    stdin, stdout, stderr = client.exec_command(command, get_pty=True, timeout=timeout)
    stdin.close()
    output = stdout.read().decode("utf-8", errors="replace") + stderr.read().decode("utf-8", errors="replace")
    return stdout.channel.recv_exit_status(), output


def build_remote_script(remote_base: str, remote_archive: str, run_label: str, timeout_seconds: int) -> str:
    return f"""#!/usr/bin/env bash
set -uo pipefail
export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
mkdir -p "{remote_base}"
RUN_LOG="{remote_base}/run.log"
RUN_EXIT="{remote_base}/run.exit"
rm -f "$RUN_EXIT"
(
  set -e
  tar -xzf "{remote_archive}" -C "{remote_base}"
  cd "{remote_base}"
  apt-get update
  apt-get install -y python3 python3-venv python3-pip curl wget git ca-certificates bash jq bc dnsutils iproute2 net-tools procps tar gzip unzip xz-utils traceroute netcat-openbsd locales
  python3 -m venv .venv
  . .venv/bin/activate
  python -m pip install -U pip
  python -m pip install -e .
  python tools/fetch_raw_sources.py
  python tools/analyze_sources.py
  python tools/run_suite.py --local --label {run_label} --timeout-seconds {timeout_seconds}
) >"$RUN_LOG" 2>&1
status=$?
printf '%s\\n' "$status" > "$RUN_EXIT"
exit "$status"
"""


def run_host(root: Path, host_cfg: dict[str, object], run_label: str, timeout_seconds: int) -> dict[str, object]:
    host = str(host_cfg["host"])
    port = int(host_cfg.get("port", 22))
    username = str(host_cfg.get("username", "root"))
    password = str(host_cfg["password"])
    remote_base = f"/root/vps_test_{run_label}"
    local_dir = root / "remote_runs" / host / run_label
    local_dir.mkdir(parents=True, exist_ok=True)
    session_log = local_dir / "session.log"
    remote_archive = f"{remote_base}.tar.gz"
    remote_script = f"{remote_base}.runner.sh"
    remote_pid = f"{remote_base}.runner.pid"

    client = connect_client(host, port, username, password)
    sftp = client.open_sftp()

    archive_bytes = build_archive(root)
    with sftp.open(remote_archive, "wb") as remote_file:
        remote_file.write(archive_bytes)
    with sftp.open(remote_script, "w") as script_file:
        script_file.write(build_remote_script(remote_base, remote_archive, run_label, timeout_seconds))
    sftp.close()

    run_command(client, f"chmod +x {remote_script}")
    _, launch_output = run_command(
        client,
        f"nohup bash {remote_script} >/dev/null 2>&1 </dev/null & echo $! > {remote_pid} && cat {remote_pid}",
    )
    launch_output = launch_output.strip()

    exit_code: int | None = None
    started = time.monotonic()
    while time.monotonic() - started < MAX_REMOTE_WAIT_SECONDS:
        try:
            code, status_output = run_command(
                client,
                (
                    f"if [ -f {remote_base}/run.exit ]; then printf 'DONE '; cat {remote_base}/run.exit; "
                    f"elif [ -f {remote_pid} ] && kill -0 $(cat {remote_pid}) 2>/dev/null; then echo RUNNING; "
                    "else echo LOST; fi"
                ),
            )
            _ = code
            status_output = status_output.strip()
        except Exception:
            client.close()
            time.sleep(3)
            client = connect_client(host, port, username, password)
            continue

        if status_output.startswith("DONE"):
            try:
                exit_code = int(status_output.split(maxsplit=1)[1])
            except Exception:
                exit_code = -1
            break
        if status_output == "LOST":
            exit_code = -1
            break
        time.sleep(POLL_INTERVAL_SECONDS)
    else:
        exit_code = -1

    sftp = client.open_sftp()
    try:
        sftp.get(f"{remote_base}/run.log", str(session_log))
    except Exception:
        session_log.write_text("", encoding="utf-8")

    remote_run_dir = f"{remote_base}/artifacts/{run_label}"
    for filename in ["results.json", "report.txt"]:
        try:
            sftp.get(f"{remote_run_dir}/{filename}", str(local_dir / filename))
        except Exception:
            pass

    sftp.close()
    client.close()
    return {
        "host": host,
        "exit_code": exit_code,
        "launcher_pid": launch_output,
        "local_dir": str(local_dir),
        "session_log": str(session_log),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the suite on multiple remote VPS hosts.")
    parser.add_argument("--hosts-file", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    hosts = json.loads(Path(args.hosts_file).read_text(encoding="utf-8"))
    run_label = time.strftime("%Y%m%d_%H%M%S")
    results = [run_host(root, host_cfg, run_label, args.timeout_seconds) for host_cfg in hosts]
    output_path = root / "remote_runs" / f"summary_{run_label}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
