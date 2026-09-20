#!/usr/bin/env bash
# ⛔⛔ THIS FILE EXISTS TO NOT REPEAT THE ORACLE'S TRAP.
# `D:\SportsThought`'s entrypoint binds `--host 127.0.0.1`, which is correct for
# something reached only through a Cloudflare Tunnel and CATASTROPHIC for a
# public app: uvicorn logs "Uvicorn running on http://127.0.0.1:8080", the
# health check inside the machine passes, and nothing on the internet can reach
# it. The bug looks exactly like a healthy boot. Bind 0.0.0.0 or do not bind.
set -euo pipefail

HOST="${TLON_HOST:-0.0.0.0}"
PORT="${PORT:-8080}"

if [ "$HOST" = "127.0.0.1" ] || [ "$HOST" = "localhost" ]; then
  echo "⛔⛔ REFUSING TO START: TLON_HOST=$HOST binds loopback only." >&2
  echo "   A public Fly app bound to loopback comes up clean and is" >&2
  echo "   unreachable from outside the machine. This is the Oracle's trap." >&2
  exit 1
fi

# ── the weights ─────────────────────────────────────────────────────────────
# The adapter (308 MB) is baked into the image: it is ours, it is small, and a
# machine that boots without it would serve the UNTUNED BASE, which scores 0.0%
# on write — it would answer in English and look fine. The base model (~14 GB)
# is NOT baked; it lives on the volume so an image rebuild does not re-push it.
export HF_HOME="${HF_HOME:-/data/hf}"
mkdir -p "$HF_HOME" "$(dirname "${TLON_DB:-/data/bench.sqlite3}")"

echo "tlön · host=$HOST port=$PORT adapter=${TLON_ADAPTER:-<default>}"
echo "      hf_home=$HF_HOME db=${TLON_DB:-/data/bench.sqlite3}"

# ⛔ ONE WORKER. The model is a single process-wide object on one GPU; a second
# uvicorn worker would load a second copy of the weights onto the same card and
# the first request to the second worker would OOM. Concurrency is handled
# inside the process by guard.py's slot, which is the only place that can see
# the GPU is singular.
exec uvicorn puzzle.server:app \
  --host "$HOST" \
  --port "$PORT" \
  --workers 1 \
  --timeout-keep-alive 75 \
  --proxy-headers \
  --forwarded-allow-ips '*'
