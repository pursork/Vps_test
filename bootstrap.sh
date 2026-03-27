#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-/opt/vps_test}"
if ! command -v git >/dev/null 2>&1; then
  apt-get update
  apt-get install -y git curl wget python3 python3-venv python3-pip ca-certificates jq bc tar gzip unzip xz-utils lsb-release procps iproute2 net-tools dnsutils traceroute netcat-openbsd locales bash
fi

if [ ! -d "$ROOT_DIR/.git" ]; then
  git clone https://github.com/pursork/Vps_test.git "$ROOT_DIR"
fi

cd "$ROOT_DIR"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
python tools/fetch_raw_sources.py
python tools/analyze_sources.py
python tools/run_suite.py --local
