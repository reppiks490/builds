#!/usr/bin/env bash
# MYRIAD Ω: safe model pull. Does not silently install a model daemon.
set -euo pipefail
cd "$(dirname "$0")"
profile="${1:-balanced}"
case "$profile" in
  lite) model='qwen3.5:0.8b' ;;
  balanced) model='qwen3.5:4b' ;;
  pro) model='qwen3.5:9b' ;;
  *) echo 'Usage: bash bootstrap_unix.sh [lite|balanced|pro]' >&2;exit 2 ;;
esac
python3 bootstrap_models.py --profile "$profile" --pull
