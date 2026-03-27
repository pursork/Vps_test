from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vps_test.reporting import render_template
from vps_test.runtime import execute_suite


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the VPS test suite and render Module report.")
    parser.add_argument("--local", action="store_true", help="Execute on the current Debian/Linux host.")
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--label", default=None)
    args = parser.parse_args()

    if not args.local:
        raise SystemExit("当前仅实现 --local 入口，请在 Debian VPS 上本地执行。")

    root = Path(__file__).resolve().parents[1]
    output_root = root / "artifacts"
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = execute_suite(root=root, output_root=output_root, timeout_seconds=args.timeout_seconds, label=args.label)

    render_template(
        template_path=root / "templates" / "Module.txt",
        results_json_path=run_dir / "results.json",
        output_path=run_dir / "report.txt",
    )
    print(f"RUN_DIR={run_dir}")
    print(f"REPORT={run_dir / 'report.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
