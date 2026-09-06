#!/usr/bin/env bash
# ═══ THE FULL-WEIGHT ARM — PREREG a0450b36 ═════════════════════════════════
#
# One `_w` object: a full-weight fine-tune of Qwen2.5-7B-Instruct on the
# content-transient corpus at dose 0 (`dd40e22f85b0b6e4`), then the three-axis
# read. §5 is the configuration and it is HASHED — every value below that the
# prereg names is quoted from it, not chosen here.
#
# ⛔⛔ A SEPARATE SCRIPT, AND A SHARED SCAFFOLDING. The stage SEQUENCE genuinely
# differs from the LoRA arm — one object not six, no solo transcripts at persist
# time, an epoch-1 read with a pre-declared early-stop, `weight_arm_entry`
# instead of `entry` — so folding it into pipeline_retrain.sh would be
# conditionals at every stage. But the failure handler, the log rotation, the
# watchdog arming and the `~/DONE` gate are the logic both losses on 2026-09-04
# happened in, so those are SOURCED from pipeline_lib.sh and exist once.
#
#   HF_REPO=... bash tools/pipeline_fullft.sh
#
set -uo pipefail
source "$(dirname "$0")/pipeline_lib.sh"
tlon_trap_init
set -e

SEED=${SEED:-20624}
CELL=fw-s$SEED
ROOT=${ROOT:-runs/act2/fullft_$CELL}
tlon_log_init "$ROOT" pipeline_fullft.log

PY=${PY:-$HOME/venv/bin/python}
MODEL=Qwen/Qwen2.5-7B-Instruct
HF_REPO=${HF_REPO:-keyzersoze04/tlon-act2-adapters}

# ⛔⛔ EVERY VALUE HERE IS QUOTED FROM THE LOCKED §5, NOT CHOSEN. Changing one
# without a new prereg makes the run un-readable against the document that says
# what it means.
UNFREEZE_TOP=14                 # top 14 of 28 layers, 3.263 B trainable
OPTIM=adamw_bnb_8bit            # fp32 master params, 8-bit moments (FORCED)
LR=1e-5                         # 5e-6 is the (c) dial-back, a NEW prereg
SEQ=384                         # the gate's actual seq, not 256
BATCH=4; ACCUM=4                # effective 16, the gate's shape
VRAM_WALL=80                    # gpu_1x_h100_pcie
TRAINABLE_B=3.263
CORPUS_SHA=dd40e22f85b0b6e4     # §5: sha-verified BEFORE training

# ── 1 · WATCHDOG FIRST, BEFORE THE FLOORS ───────────────────────────────────
# ⛔⛔ THE ORDER IS THE PREREG'S (§8, R5) AND IT IS A CHANGE FROM THE LoRA ARM.
# The safety net deploys before the risk. A broken tree failing floors AFTER
# arming triggers the watchdog, which is its job; floors-first leaves the
# un-guarded idle window that leaked $0.75 twice.
step watchdog
# ⛔⛔ THE DEADLINE IS A COST BOUND, NOT ONLY A STALL GUARD, AND IT IS DERIVED
# FROM THE CARD'S PRICE. At $3.29/hr the standing $70-per-run alert is reached
# at 21.3 h, so a 24 h deadline would have let a hung run bill $79 — past the
# alert, by design, with nothing to stop it. 20 h caps the worst case at $65.80
# and still leaves ~2.5x headroom over the ~8 h estimate.
tlon_arm_watchdog "$PY" "$ROOT" "$HF_REPO" pipeline_fullft.sh 20 90 $$

# ── 2 · FLOORS ──────────────────────────────────────────────────────────────
step syntax_floor
$PY --version | tee -a $LOG
$PY -m compileall -q tools/ tlon/ tests/ 2>&1 | tee -a $LOG
# ⭐ The two suites that cover THIS arm, plus provisioning. A green suite proves
# the lane, not the answer — but a red one here costs nothing to find now and
# an H100-hour to find later.
$PY -m pytest -q tests/test_full_weight.py tests/test_w_object.py \
     tests/test_provision.py 2>&1 | tail -3 | tee -a $LOG

step optim_probe
# ⛔⛔ THE THIRD OBLIGATION, IN THE RUN'S OWN RECORD. The provisioner probes this
# too, but that proof lives in a terminal; this one lives in the log that gets
# persisted. It costs under a second and it forecloses the most expensive
# failure available here: training for hours, moving nothing, and producing a
# zero delta that looks exactly like the substrate finding.
$PY tools/act2_finetune.py --probe-optim --lr $LR 2>&1 | tee -a $LOG

step vram
# ⛔ Sized on the FULL-WEIGHT arithmetic. The planner's LoRA rows would report
# ~26 GiB for a job that needs 51 — the wrong number in the confident shape of
# a right one. And the +28 % is applied because `PLANNER_IS_A_LOWER_BOUND`.
$PY tools/act2_finetune.py --plan --params 7.616 \
    --trainable-params $TRAINABLE_B --moment-bytes 2 \
    --seq $SEQ --batch $BATCH --vram $VRAM_WALL 2>&1 | tee -a $LOG
$PY - <<PY 2>&1 | tee -a $LOG
import sys; sys.path.insert(0, "tools")
from act2_finetune import plan
p = plan(7.616, "bf16", $SEQ, $BATCH, True, trainable_b=$TRAINABLE_B,
         moment_bytes=2)
worst = p["total_GiB"] * 1.28
print("  planner %.1f GiB, +28%% worst-observed miss -> %.1f vs %d wall"
      % (p["total_GiB"], worst, $VRAM_WALL))
assert worst < $VRAM_WALL, "⛔⛔ exceeds the wall at the worst observed miss"
print("  ✅ fits with %.1f GiB of margin" % ($VRAM_WALL - worst))
PY

# ── 3 · THE CORPUS, SHA-PINNED BEFORE TRAINING ──────────────────────────────
step corpus
$PY tools/act2_build_multiturn.py --recipe content-transient \
    --suppression-window 0 --chains 1445 --multiturn-fraction 0.5 \
    --map derived --seed $SEED --out $ROOT/corpus_ct-s$SEED 2>&1 | tee -a $LOG

step corpus_pin
# ⛔⛔ PINNED, NOT RECORDED. Unlike the LoRA batch's new seeds, this corpus has a
# KNOWN sha: §5 names `dd40e22f85b0b6e4`, and the whole comparison to the gate
# rests on this being the same corpus. A mismatch here means the deterministic
# rebuild is broken and every downstream number is about a different language.
GOT=$(sha256sum $ROOT/corpus_ct-s$SEED/train.jsonl | cut -c1-16)
echo "  train sha $GOT (expected $CORPUS_SHA)" | tee -a $LOG
if [ "$GOT" != "$CORPUS_SHA" ]; then
  echo "⛔⛔ CORPUS SHA MISMATCH — refusing to train on a different corpus than the one §5 names" | tee -a $LOG
  exit 1
fi
echo "  ✅ corpus is byte-identical to the one §5 declares" | tee -a $LOG

step corpus_manifest
CM=$ROOT/corpus_ct-s$SEED/manifest.json
[ -f "$CM" ] || { echo "⛔⛔ no corpus manifest at $CM — it carries the corpus lag profile the model is compared against" | tee -a $LOG; exit 1; }

# ── 4 · LEG 1 — ONE EPOCH, THEN THE MANDATORY READ ──────────────────────────
# ⛔⛔ §5: "2 epochs declared, with a MANDATORY read at end of epoch 1", and a
# pre-declared early-stop if epoch 1 is GO on all three axes. Both branches are
# in the locked body, so neither is a choice made after seeing the number.
OUT=$ROOT/model_$CELL
SNAP=$ROOT/delta_snapshot.pt

step train_leg1
$PY tools/act2_finetune.py --model $MODEL --out $OUT \
    --corpus $ROOT/corpus_ct-s$SEED \
    --full --unfreeze-top $UNFREEZE_TOP --optim $OPTIM \
    --lr $LR --seq $SEQ --batch $BATCH --accum $ACCUM --epochs 1 \
    --seed $SEED --delta-snapshot-out $SNAP 2>&1 | tee -a $LOG

step factorial_json
# ⛔⛔ A `_w` OBJECT GETS NO CELL AND NO PAIR KEY. §0/§6: its weights changed, so
# it is not a member of the `_ctx` factorial and must never be pooled into one.
# `weight_arm_entry` is the only constructor that will build it, and `entry()`
# refuses outright.
$PY - <<PY 2>&1 | tee -a $LOG
import json, pathlib, sys
sys.path.insert(0, ".")
from tlon.act2.factorial import weight_arm_entry
from tlon.discourse.transient import CONTENT_TRANSIENT
e = weight_arm_entry("$CELL", recipe=CONTENT_TRANSIENT, seed=$SEED,
                     unfreeze_top=$UNFREEZE_TOP, prereg="a0450b36",
                     manifest=json.loads(pathlib.Path("$CM").read_text()))
pathlib.Path("$OUT/factorial.json").write_text(json.dumps(e, indent=2))
print("  ✅ %s: cell=%r pair_key=%r category=%s"
      % (e["name"], e["cell"], e.get("factorial_pair_key"),
         e["measurement_category"]))
PY

step persist_leg1
# ⭐ BEFORE the reads, not after. The object is ~13 GiB that cost H100-hours; a
# fault in the read should cost the read and not the weights.
$PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO \
    full-weight --cell $CELL --corpus-manifest $CM 2>&1 | tee -a $LOG

step flocal_epoch1
$PY tools/act2_flocal.py --model $OUT --n 64 2>&1 | tee -a $LOG

step lag_epoch1
$PY tools/act2_model_lag.py --model $OUT --object-kind full_weight \
    --chains 12 --turns 10 --temperature 0.70 --max-new-tokens 256 \
    --seed $SEED --out $ROOT/model_lag_${CELL}_e1.json 2>&1 | tee -a $LOG

step verdict_epoch1
# ⛔ `set -e` would abort on the STOP exit code, and a STOP at epoch 1 is not a
# pipeline failure — it is the branch §5 declares. Captured, not trapped.
E1=0
$PY tools/act2_fullft_verdict.py \
    --delta $OUT/weight_delta.json \
    --lag $ROOT/model_lag_${CELL}_e1.json \
    --ledger runs/act2/ledger.jsonl \
    --out $ROOT/verdict_${CELL}_e1.json 2>&1 | tee -a $LOG || E1=$?

if [ $E1 -eq 3 ]; then
  # ⛔⛔ §4.1: the weights did not move. No row of the table may be read, and
  # epoch 2 would only spend more money writing nothing.
  echo "⛔⛔ INSTRUMENT FAULT at epoch 1 — stopping. This is NOT evidence about the substrate." | tee -a $LOG
  exit 1
fi

if [ $E1 -eq 0 ]; then
  # ⭐ THE PRE-DECLARED EARLY-STOP. Stopping on a success condition written into
  # the hashed body is not threshold-fudging; it protects against an epoch-2
  # over-fit cratering the fluency that just passed.
  echo "⭐ EPOCH 1 IS GO ON ALL THREE AXES — stopping here per §5" | tee -a $LOG
  EPOCHS_RUN=1
  FINAL_LAG=$ROOT/model_lag_${CELL}_e1.json
  FINAL_VERDICT=$ROOT/verdict_${CELL}_e1.json
else
  echo "  epoch 1 is not GO-on-all-three; epoch 2 runs and epoch 2 is the verdict (§5)" | tee -a $LOG

  # ── 5 · LEG 2 — THE SECOND EPOCH ──────────────────────────────────────────
  step train_leg2
  # ⛔⛔ --delta-snapshot-in CARRIES THE BASE-MODEL SNAPSHOT. Without it this leg
  # would measure one epoch of movement and report it as the total, and a run
  # whose first epoch moved the weights and whose second did not would read
  # INSTRUMENT FAULT — the §4.1 guard firing on a run that worked.
  #
  # ⚠️ DEVIATION, RECORDED: the legs are separate `Trainer` invocations, so the
  # Adam moment estimates restart at epoch 2 rather than continuing. §5 declares
  # "2 epochs" and this is two epochs of data at the declared LR, but it is not
  # byte-identical to one continuous 2-epoch run. See DEVIATIONS.
  $PY tools/act2_finetune.py --model $OUT --out $OUT \
      --corpus $ROOT/corpus_ct-s$SEED \
      --full --unfreeze-top $UNFREEZE_TOP --optim $OPTIM \
      --lr $LR --seq $SEQ --batch $BATCH --accum $ACCUM --epochs 1 \
      --seed $SEED --delta-snapshot-in $SNAP 2>&1 | tee -a $LOG

  step persist_leg2
  $PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO \
      full-weight --cell $CELL --corpus-manifest $CM 2>&1 | tee -a $LOG

  step flocal_epoch2
  $PY tools/act2_flocal.py --model $OUT --n 64 2>&1 | tee -a $LOG

  step lag_epoch2
  $PY tools/act2_model_lag.py --model $OUT --object-kind full_weight \
      --chains 12 --turns 10 --temperature 0.70 --max-new-tokens 256 \
      --seed $SEED --out $ROOT/model_lag_${CELL}_e2.json 2>&1 | tee -a $LOG

  step verdict_epoch2
  E2=0
  $PY tools/act2_fullft_verdict.py \
      --delta $OUT/weight_delta.json \
      --lag $ROOT/model_lag_${CELL}_e2.json \
      --ledger runs/act2/ledger.jsonl \
      --out $ROOT/verdict_${CELL}_e2.json 2>&1 | tee -a $LOG || E2=$?
  if [ $E2 -eq 3 ]; then
    echo "⛔⛔ INSTRUMENT FAULT at epoch 2 — no row of the verdict table may be read." | tee -a $LOG
    exit 1
  fi
  EPOCHS_RUN=2
  FINAL_LAG=$ROOT/model_lag_${CELL}_e2.json
  FINAL_VERDICT=$ROOT/verdict_${CELL}_e2.json
fi

# ── 6 · THE GATE ON ~/DONE ──────────────────────────────────────────────────
TLON_SUMMARY="⭐ ALL STAGES PASSED — 1 \`_w\` object over $EPOCHS_RUN epoch(s), PERSISTED"
tlon_gate_done "$PY" "$ROOT" "$HF_REPO" "$CELL" \
    "$FINAL_LAG" "$FINAL_VERDICT" "$ROOT/verdict_${CELL}_e1.json"
