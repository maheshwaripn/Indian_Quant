#!/usr/bin/env bash
set -euo pipefail
: "${IQ_REPO:?Set absolute repository path}"
: "${IQ_DATA:?Set immutable input snapshot path}"
: "${IQ_CALENDAR:?Set verified session calendar path}"
: "${IQ_BENCHMARK:?Set benchmark instrument ID}"
cd "$IQ_REPO"
mkdir -p workspace/runs
exec 9>workspace/research.lock
flock -n 9 || { echo 'Another research job is running' >&2; exit 1; }
run_id="scheduled-$(date -u +%Y%m%dT%H%M%S)-$$"
exec .venv/bin/python -m indian_quant run --data "$IQ_DATA" --calendar "$IQ_CALENDAR" \
  --benchmark "$IQ_BENCHMARK" --mode vps --output "workspace/runs/$run_id"
