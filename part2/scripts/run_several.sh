#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python3 main.py \
  --vfs vfs/several.zip \
  --start-script start_scripts/startup.sh \
  --debug
