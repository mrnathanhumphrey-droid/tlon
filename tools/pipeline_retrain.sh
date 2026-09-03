#!/usr/bin/env bash
# ═══ RETRAIN TO 12 — six new adapters, and the SOLO logs the ruler needs ════
#
# WHY 12. Power AT THE FLOOR (delta = FLOOR_ka = 0.100 ka), 28 replicates,
# clustered on the adapter:  6 -> 0.70-0.76 · 9 -> 0.83-0.94 · 10 -> 0.87-0.96
# · 12 -> 0.925 even at the conservative end of the heterogeneity band.
# 12 is the count that clears across the WHOLE band of a parameter nobody has
# measured. `runs/act2/adapter_sizing.json`.
#
# ⛔⛔ THE RECIPE IS COPIED FROM THE RUNS THAT MADE THE SURVIVORS, VERIFIED LINE
# BY LINE, NOT REMEMBERED. corpus + train from pipeline_recipe_variance.sh;
# F-LOCAL from the same; and the SOLO arm from pipeline_asymmetric_recert.sh —
# ⭐ NOT recipe_var's `arm` step. The frozen ruler is built by act2_distance from
# `runs/act2/asym_recert/logs/<build>_solo_*.json` (ASYM_BUILDS), so a new build
# measured with the window-1 exchange probe would enter the ruler through a
# DIFFERENT PROCEDURE than the six it is being compared against.
#
# ⛔ NEW NAMES. s20624… — never a retrained adapter wearing s20620's name. That
# build is lost; GPU training is not bit-deterministic; a substitute under the
# lost label is the caveat-in-the-name failure.
set -uo pipefail
trap 'rc=$?; if [ $rc -ne 0 ]; then
        echo "⛔ FAILED at stage: $STAGE (rc=$rc)" | tee -a $LOG
        echo "$STAGE rc=$rc" > ~/FAILED
      fi' EXIT
set -e

ROOT=runs/act2/retrain12
mkdir -p $ROOT/logs
LOG=$ROOT/pipeline_retrain.log
STAGE=init
T_START=$(date +%s)
step() { STAGE="$1"; echo "=== [$1] $(date -u +%H:%M:%S) ===" | tee -a $LOG; }

PY=${PY:-$HOME/venv/bin/python}
MODEL=Qwen/Qwen2.5-7B-Instruct
SEQ=384; BATCH=4; ACCUM=4          # recipe_var, verified
TURNS=40; N_PER_BUILD=14           # asym_recert solo, verified
NEW="20624 20625 20626 20627 20628 20629"

# Measured marginals from the runs that made the survivors:
#   train 12,960 s · flocal 495 s · solo 2,143 s  = 15,598 s per adapter.
# ⛔ The 1.24 GPU-h/adapter figure in PRICING §6 is from a DIFFERENT recipe and
# was already flagged there as unverified. It understates this by 3.5x.
ADAPTER1_MAX_S=23400               # 1.5x the measured 15,598

# ── 1 · FLOORS ──────────────────────────────────────────────────────────────
step syntax_floor
$PY --version | tee -a $LOG
$PY -m compileall -q tools/ tlon/ tests/ 2>&1 | tee -a $LOG
$PY -m pytest -q tests/test_provision.py tests/test_shared_memory_arm.py 2>&1 | tail -3 | tee -a $LOG

step name_guard
# ⛔⛔ REFUSE TO PRODUCE AN ADAPTER NAMED s20620. The lost build cannot be
# recreated and a substitute under its name would silently re-enter the frozen
# ruler's population as if nothing had happened.
for S in $NEW; do
  [ "$S" = "20620" ] && { echo "⛔⛔ s20620 IS LOST AND MUST NOT BE RECREATED" | tee -a $LOG; exit 1; }
done
echo "  ✅ no new build claims a lost build's name" | tee -a $LOG

step vram
$PY - <<PY 2>&1 | tee -a $LOG
import sys; sys.path.insert(0, "tools")
from act2_finetune import plan
WORST, WALL = 1.253, 40.0        # the factor is NOT a constant; use the worst
p = plan(7.62, "bf16", $SEQ, $BATCH, 152064)
raw = p["total_GiB"]
print(f"  planner raw {raw:.1f} GiB x{WORST} -> {raw*WORST:.1f} vs {WALL} wall")
assert raw * WORST < WALL, "⛔⛔ exceeds the wall"
print("  ✅ fits at the worst observed correction")
PY

# ── 2 · CORPORA ─────────────────────────────────────────────────────────────
step corpora
for S in $NEW; do
  # ⛔ --recipe is REQUIRED and EXPLICIT: this batch is the factorial's
  #    CONTROL arm, and an implicit recipe is an adapter in no cell.
  $PY tools/act2_build_multiturn.py --recipe content-free --chains 1445 --multiturn-fraction 0.5 \
    --map derived --seed $S --out $ROOT/corpus_s$S 2>&1 | tee -a $LOG
done
# ⛔ These seeds are NEW, so there is no prior sha to pin against. Record the
# shas so the NEXT run can pin, rather than pretending this one was pinned.
step corpus_record
for S in $NEW; do
  echo "  corpus_s$S train $(sha256sum $ROOT/corpus_s$S/train.jsonl | cut -c1-16)" | tee -a $LOG
  echo "  corpus_s$S eval  $(sha256sum $ROOT/corpus_s$S/eval.jsonl  | cut -c1-16)" | tee -a $LOG
done

# ── 3 · WATCHDOG BEFORE ANY GPU TIME ────────────────────────────────────────
step watchdog
rm -f ~/DONE ~/FAILED
nohup $PY tools/act2_watchdog.py \
      --pid $$ --marker pipeline_retrain.sh \
      --log $LOG --done $HOME/DONE \
      --deadline-h 40 --stall-min 90 --poll-s 300 \
      > $ROOT/watchdog.log 2>&1 &
WD=$!
sleep 5
kill -0 $WD 2>/dev/null || { echo "⛔⛔ WATCHDOG DIED ON ARMING — refusing to run unguarded" | tee -a $LOG; cat $ROOT/watchdog.log | tee -a $LOG; exit 1; }
echo "  ✅ watchdog armed, pid $WD, watching $$" | tee -a $LOG

SETUP_END=$(date +%s)
echo "  ⏱ setup wall (one-time): $((SETUP_END-T_START)) s" | tee -a $LOG

# ── 4 · TRAIN · GATE · MEASURE ──────────────────────────────────────────────
N=0
for S in $NEW; do
  N=$((N+1)); A=$ROOT/adapter_s$S
  T0=$(date +%s)

  step train_s$S
  $PY tools/act2_finetune.py --model $MODEL --out $A \
    --corpus $ROOT/corpus_s$S --seq $SEQ --batch $BATCH --accum $ACCUM \
    --seed $S 2>&1 | tee -a $LOG

  step flocal_s$S
  # ⛔ F-LOCAL is the F1 gate: cardless, unconstrained. A build that does not
  # clear it is not a fluent speaker and must not enter the population.
  $PY tools/act2_flocal.py --model $MODEL --adapter $A \
    --n 64 --n-comp 64 2>&1 | tee -a $LOG

  step solo_s$S
  # ⭐ THE RULER'S OWN PROCEDURE, matching ASYM_BUILDS exactly.
  for i in $(seq 1 $N_PER_BUILD); do
    $PY tools/act2_two_speaker_probe.py --model $MODEL \
      --adapter-a $A --no-injections --turns $TURNS \
      --out $ROOT/logs/s${S}_solo_$i.json 2>&1 | tee -a $LOG
  done

  T1=$(date +%s); W=$((T1-T0))
  echo "  ⏱ s$S total wall: $W s (measured reference 15598 s)" | tee -a $LOG
  md5sum $A/adapter_model.safetensors | tee -a $ROOT/adapter_md5.txt

  if [ $N -eq 1 ]; then
    PROJ=$(( W * 6 / 3600 ))
    echo "  ⏱ adapter 1 = $W s ⇒ 6 adapters project to ~${PROJ} GPU-h (reference 26)" | tee -a $LOG
    if [ $W -gt $ADAPTER1_MAX_S ]; then
      echo "⛔⛔ ADAPTER 1 EXCEEDED $ADAPTER1_MAX_S s. The cost model is wrong." | tee -a $LOG
      echo "    STOPPING before the remaining five. Re-price on this measurement." | tee -a $LOG
      echo "    ⛔ PULL $LOG AND $ROOT/ BEFORE KILLING THE BOX." | tee -a $LOG
      exit 1
    fi
    echo "  ✅ adapter 1 inside the reference — committing the remaining five" | tee -a $LOG
  fi
done

# ── 5 · THE MANIFEST THE LOCAL SIDE VERIFIES AGAINST ────────────────────────
step manifest
# ⛔⛔ COMPUTED ON THE BOX, BEFORE ANYTHING IS PULLED. A checksum taken from the
# copy, after the copy, verifies the copy against itself. This file is what
# act2_provision.verify_checksum compares each arrival to.
$PY - <<PY 2>&1 | tee -a $LOG
import hashlib, json, pathlib
root = pathlib.Path("$ROOT")
out = {}
for d in sorted(root.glob("adapter_s*")):
    f = d / "adapter_model.safetensors"
    if not f.exists():
        continue
    h = hashlib.md5()
    with open(f, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    out[d.name.replace("adapter_", "")] = {
        "md5": h.hexdigest(), "bytes": f.stat().st_size,
        "remote_path": str(f)}
(root / "manifest.json").write_text(json.dumps(out, indent=2))
print("  manifest: %d adapters" % len(out))
for k, v in out.items():
    print("   ", k, v["md5"], v["bytes"])
assert len(out) == 6, "expected 6 adapters, manifest has %d" % len(out)
PY

step done
echo "⭐ ALL STAGES PASSED — 6 new adapters + $N_PER_BUILD solo logs each" | tee -a $LOG
echo "⛔ PULL $LOG, $ROOT/manifest.json, the adapters AND $ROOT/logs/ BEFORE" | tee -a $LOG
echo "   KILLING THE BOX. The last box was terminated with an adapter still on" | tee -a $LOG
echo "   it and that adapter is gone permanently." | tee -a $LOG
echo "  total wall: $(( $(date +%s) - T_START )) s" | tee -a $LOG
touch ~/DONE
