#!/usr/bin/env bash
# ═══ IDF-2 STEP P — THE POWER CHECK, BEFORE ANY ADAPTER IS BOUGHT ══════════
#
# `docs/PREREG_IDF2_2026_09_26.md`, LOCK `37363296`, §3A.
#
# ⭐⭐ WHY THIS RUNS FIRST AND ALONE. §6 has one failure branch that learns
# nothing: the bands not resolving. If `2 × between-seed SD > 15 points` the
# reading is "no verdict" no matter where the point estimate landed — three
# adapters bought, ~20 GPU-h spent, and the table could never have separated
# its own cells. C0 (`ct-s20624`) ALREADY EXISTS, so its seeded reads measure
# that SD on a real adapter at the real read size before a single training step
# is paid for.
#
# ⛔ EIGHT SEEDS, NOT THREE. Three reads give an SD with 2 degrees of freedom —
# noisy enough that the gate protecting the whole table would be the least
# reliable number in it. Eight give 7 df, and C0 is untrained so this buys them
# with READS ONLY. (Wilson, 2026-09-26, sign-off #4.)
#
# ⛔ NO TRAINING ANYWHERE BELOW, AND NOTHING IS PERSISTED OVER. This reads an
# object that exists; `tests/test_idf2_stepP.py` asserts the absence of any
# train or adapter-persist step, the way `test_reread_pipeline` does.
#
#   bash tools/pipeline_idf2_stepP.sh
#
set -uo pipefail
source "$(dirname "$0")/pipeline_lib.sh"
tlon_trap_init
set -e

CELL=${CELL:-ct-s20624}
ROOT=${ROOT:-runs/act2/idf2/stepP}
tlon_log_init "$ROOT" pipeline_idf2_stepP.log

PY=${PY:-$HOME/venv/bin/python}
MODEL=Qwen/Qwen2.5-7B-Instruct
HF_REPO=${HF_REPO:-keyzersoze04/tlon-act2-adapters}

# ⛔ The read geometry is the prereg's, not a default. §5: 48 chains × 10 turns,
# T = 0.7 / 256. At this size the lag-2 cell holds 384 pairs against C0's
# original 96, which is the whole reason the bar could not stay a z.
CHAINS=${CHAINS:-48}
TURNS=${TURNS:-10}
SEEDS=${SEEDS:-"20624 20625 20626 20627 20628 20629 20630 20631"}

step watchdog
# ⛔⛔ FIRST, BEFORE ANY GPU TIME. Hard rule, no exception. A read is shorter
# than a train, which makes an unguarded stall CHEAPER, not acceptable.
# ⛔ The marker is the SCRIPT BEING EXECUTED, never an output path —
# `is_the_job` matches argv so that `tail -f x.log` is not mistaken for the job.
# 8 reads × ~28 min ≈ 3.7 h, so a 9 h deadline is ~2.4× headroom and a 45 min
# stall window is ~1.6× one read's length.
tlon_arm_watchdog "$PY" "$ROOT" "$HF_REPO" pipeline_idf2_stepP.sh 9 45 $$

step prereg_lock
# ⛔ The body that this read is denominated against must still hash to its lock.
# A tampered prereg fails HERE — after the watchdog, before a GPU-hour.
$PY tools/lock_prereg.py docs/PREREG_IDF2_2026_09_26.md | tee -a "$LOG"

step adapter
# ⛔ Pulled from the hub, not assumed present. `ct-s20624`'s weights exist in
# exactly one place and it is not this box.
ADAPTER=$ROOT/adapter_$CELL
if [ ! -f "$ADAPTER/adapter_model.safetensors" ]; then
  $PY - <<'PYEOF' 2>&1 | tee -a "$LOG"
import os, pathlib, sys
sys.path.insert(0, "tools")
from huggingface_hub import hf_hub_download
from act2_provision import _hf_token
root = pathlib.Path(os.environ["ROOT"]) / ("adapter_" + os.environ["CELL"])
root.mkdir(parents=True, exist_ok=True)
for f in ("adapter_model.safetensors", "adapter_config.json"):
    p = hf_hub_download("keyzersoze04/tlon-act2-adapters",
                        "%s/%s" % (os.environ["CELL"], f), token=_hf_token())
    (root / f).write_bytes(pathlib.Path(p).read_bytes())
    print("  pulled", f)
PYEOF
fi

step reads
# ⛔⛔ EACH SEED IS ITS OWN PROCESS AND ITS OWN FILE. A single process looping
# eight reads would share one CUDA RNG lineage across them, so seed k+1 would
# not be independent of seed k — and the SD this whole step exists to measure
# is a BETWEEN-SEED spread. One process per seed is what makes them independent
# draws rather than eight samples from one stream.
# ⭐ And a crash at seed 6 then costs six reads, not eight.
for S in $SEEDS; do
  OUT=$ROOT/lag_${CELL}_s${S}.json
  if [ -f "$OUT" ]; then
    echo "  seed $S already read — skipping" | tee -a "$LOG"
    continue
  fi
  echo "  ── seed $S ──" | tee -a "$LOG"
  $PY tools/act2_model_lag.py \
      --model "$MODEL" --adapter "$ADAPTER" --object-kind adapter \
      --chains "$CHAINS" --turns "$TURNS" --seed "$S" \
      --temperature 0.7 --max-new-tokens 256 \
      --out "$OUT" 2>&1 | tee -a "$LOG"
done

step power
# The gate itself. Reads the eight files, computes `closes` in points of the
# 0c gap, and reports PASS/FAIL against `2 × SD ≤ 15 points`.
$PY tools/act2_idf2_power.py --root "$ROOT" --cell "$CELL" \
    --step0 runs/act2/idf2/step0.json \
    --out "$ROOT/power.json" 2>&1 | tee -a "$LOG"

# ⛔⛔ THE MARKER IS THE HELPER'S TO WRITE, NEVER THIS SCRIPT'S. `~/DONE` means
# PERSISTED-AND-VERIFIED and the watchdog terminates within one poll of seeing
# it, so a pipeline that touches it itself has quietly made every verification
# above advisory. Six older pipelines still do; `tests/test_pipeline_lib.py`
# PINS that list precisely so the debt cannot grow by one more script, and it
# caught this one on its first run.
#
# ⭐ `tlon_persist_run_files` + `tlon_mark_done` rather than `tlon_gate_done`,
# because Step P writes NO CELL — it reads an object that already exists. Its
# certification is over run files, the way `pipeline_battery.sh`'s is.
tlon_persist_run_files "$PY" "$ROOT" "$HF_REPO" \
    "$ROOT/power.json" $ROOT/lag_${CELL}_s*.json

TLON_SUMMARY="$(tail -n 12 "$ROOT/power.json" 2>/dev/null | head -n 1)"
tlon_mark_done "$HF_REPO" "IDF-2 Step P — 8 seeded C0 reads + power.json"
