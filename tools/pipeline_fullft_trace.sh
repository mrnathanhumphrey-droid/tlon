#!/usr/bin/env bash
# ═══ ROOT-CAUSE TRACE — the ACTUAL config, watched per step ═════════════════
#
# ⛔⛔ THIS BUYS THE TRACE, NOT THE MODEL. The full-weight run at `2d80803`
# (LOCK a0450b36) collapsed loss 7.548 -> ~0 within ~50 steps and produced a
# model with NaN in all 70 of its 1-D trainable tensors and none of its 98
# matrices. Five mechanisms are excluded by positive test, all in ISOLATION —
# and from outside, a degenerate objective, a forward/backward numerical
# failure, and an optimizer-path failure all look the same: loss goes to zero.
#
# ⭐⭐ ORDERING SEPARATES THEM, so this records gradients BEFORE the optimizer
# step and weights + moments AFTER it, every step, per module:
#
#     gradient non-finite first      -> forward/backward numerical
#     weight/moment non-finite first -> optimizer path
#     all finite, grad norm -> 0     -> degenerate objective, no NaN at all
#
# ⛔ THE CONFIG IS NOT CHANGED. A variant that trains clean says nothing about
# why the original broke. Everything below is the configuration that failed.
#
# ⛔ BOUNDED. The collapse hit by ~50, so MAX_STEPS captures it many times over
# for a fraction of an epoch. The deliverable is the trace.
#
set -uo pipefail
source "$(dirname "$0")/pipeline_lib.sh"
tlon_trap_init
set -e

SEED=${SEED:-20624}
CELL=fwtrace-s$SEED
PY=${PY:-$HOME/venv/bin/python}
MODEL=Qwen/Qwen2.5-7B-Instruct
HF_REPO=${HF_REPO:-keyzersoze04/tlon-act2-adapters}

# ⛔ IDENTICAL TO §5. Changing any of these makes this a different experiment.
UNFREEZE_TOP=14
OPTIM=adamw_bnb_8bit
LR=1e-5
SEQ=384
BATCH=4; ACCUM=4
CORPUS_SHA=dd40e22f85b0b6e4
MAX_STEPS=${MAX_STEPS:-300}
# ⭐ THE ABLATION SWITCH. GRAD_CKPT=0 removes gradient checkpointing AND the
# enable_input_require_grads() it necessitates -- the two prime suspects, which
# come off together. The memory case for keeping them is 0.5 GiB at this shape.
GRAD_CKPT=${GRAD_CKPT:-1}
CKPT_FLAG=""
if [ "$GRAD_CKPT" = "0" ]; then
  CKPT_FLAG="--no-grad-checkpointing"
  CELL=fwnockpt-s$SEED
fi

# ⛔ ROOT AND THE LOG ARE INITIALISED AFTER THE ABLATION SWITCH, so a
# checkpointing-off run cannot write into the checkpointing-on run's tree and be
# read afterwards as the same experiment.
ROOT=${ROOT:-runs/act2/fullft_trace_$CELL}
tlon_log_init "$ROOT" pipeline_fullft_trace.log
echo "  arm: CELL=$CELL  grad_checkpointing=$GRAD_CKPT" | tee -a $LOG

# ── 1 · WATCHDOG FIRST ──────────────────────────────────────────────────────
step watchdog
# ⭐ 4 h deadline, not 20: this run is ~30 minutes of work and a deadline sized
# for the full fine-tune would let a hang bill 20 h for a diagnostic.
tlon_arm_watchdog "$PY" "$ROOT" "$HF_REPO" pipeline_fullft_trace.sh 4 45 $$

# ── 2 · FLOORS ──────────────────────────────────────────────────────────────
step syntax_floor
$PY --version | tee -a $LOG
$PY -m compileall -q tools/ tlon/ tests/ 2>&1 | tee -a $LOG
$PY -m pytest -q tests/test_full_weight.py tests/test_w_object.py 2>&1 | tail -3 | tee -a $LOG

step optim_probe
$PY tools/act2_finetune.py --probe-optim --lr $LR 2>&1 | tee -a $LOG

# ── 3 · CORPUS, SHA-PINNED ──────────────────────────────────────────────────
step corpus
$PY tools/act2_build_multiturn.py --recipe content-transient \
    --suppression-window 0 --chains 1445 --multiturn-fraction 0.5 \
    --map derived --seed $SEED --out $ROOT/corpus_ct-s$SEED 2>&1 | tee -a $LOG

step corpus_pin
GOT=$(sha256sum $ROOT/corpus_ct-s$SEED/train.jsonl | cut -c1-16)
echo "  train sha $GOT (expected $CORPUS_SHA)" | tee -a $LOG
if [ "$GOT" != "$CORPUS_SHA" ]; then
  echo "⛔⛔ CORPUS SHA MISMATCH — this would diagnose a different corpus than the one that broke" | tee -a $LOG
  exit 1
fi
echo "  ✅ same corpus, byte-identical" | tee -a $LOG

# ── 4 · THE TRACED RUN ──────────────────────────────────────────────────────
OUT=$ROOT/model_$CELL
TRACE=$ROOT/step_trace.jsonl

step train_traced
# ⛔ `--max-steps` and `--trace-out` are the ONLY differences from the run that
# broke. Same model, same corpus, same scope, same optimizer, same LR, same
# shapes — so what this sees is the actual failure and not a neighbour of it.
$PY tools/act2_finetune.py --model $MODEL --out $OUT \
    --corpus $ROOT/corpus_ct-s$SEED \
    --full --unfreeze-top $UNFREEZE_TOP --optim $OPTIM \
    --lr $LR --seq $SEQ --batch $BATCH --accum $ACCUM --epochs 1 \
    --max-steps $MAX_STEPS --trace-out $TRACE $CKPT_FLAG \
    --seed $SEED 2>&1 | tee -a $LOG

# ⛔⛔ THE TRACE IS THE DELIVERABLE, SO IT PERSISTS BEFORE ANYTHING ELSE CAN GO
# WRONG. The last run's pipeline log was lost to a flush that named one file;
# this one's trace is the entire reason the box was rented.
step persist_trace
$PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO \
    file --path $TRACE --subdir $CELL 2>&1 | tee -a $LOG
if [ -f "$OUT/weight_delta.json" ]; then
  $PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO \
      file --path $OUT/weight_delta.json --subdir $CELL 2>&1 | tee -a $LOG
fi

step read_trace
# ⭐ THE READING, ON THE BOX, INTO THE LOG. The four pre-declared branches are
# decided by the trace itself, not by whoever opens it later.
$PY - <<PY 2>&1 | tee -a $LOG
import json, pathlib
rows = [json.loads(l) for l in
        pathlib.Path("$TRACE").read_text(encoding="utf-8").splitlines() if l.strip()]
steps = [r for r in rows if "step" in r]
summary = next((r["SUMMARY"] for r in rows if "SUMMARY" in r), None)
losses = [(r["step"], r["loss"]) for r in steps if r.get("loss") is not None]
print("  steps recorded: %d" % len(steps))
print("  loss first 8 : %s" % [(s, round(l, 4)) for s, l in losses[:8]])
print("  loss last 5  : %s" % [(s, round(l, 4)) for s, l in losses[-5:]])
gn = [(r["step"], r.get("grad_norm_total")) for r in steps]
print("  grad_norm first 8: %s" % [(s, None if g is None else round(g, 6)) for s, g in gn[:8]])
print("  grad_norm last 5 : %s" % [(s, None if g is None else round(g, 6)) for s, g in gn[-5:]])
fn = summary.get("first_nonfinite") if summary else None
print("  FIRST NON-FINITE: %s" % fn)
# ⛔ The four pre-declared readings, decided here.
if fn is None:
    zero = [g for _, g in gn if g is not None and g < 1e-8]
    if losses and losses[-1][1] is not None and losses[-1][1] < 0.01:
        print("  READING: DEGENERATE OBJECTIVE — loss collapsed with NO non-finite")
        print("           value anywhere. The NaN in the full run is downstream;")
        print("           the objective itself produces no signal at real scale.")
    else:
        print("  READING: TRAINED CLEANLY within %s steps — the fast-collapse" % len(steps))
        print("           regime is ruled out; a longer run is the next question.")
elif fn["quantity"] == "grad":
    print("  READING: FORWARD/BACKWARD NUMERICAL — the GRADIENT went non-finite")
    print("           first, on %s tensors (rank %s). Upstream of the optimizer." % (fn["n"], fn["rank"]))
else:
    print("  READING: OPTIMIZER PATH — weights/moments went non-finite before any")
    print("           gradient did (%s, rank %s)." % (fn["quantity"], fn["rank"]))
PY

# ── 5 · THE GATE ON ~/DONE ──────────────────────────────────────────────────
TLON_SUMMARY="⭐ TRACE CAPTURED — $MAX_STEPS steps of the real config, PERSISTED"
tlon_persist_run_files "$PY" "$ROOT" "$HF_REPO"
tlon_mark_done "$HF_REPO" "step trace over $MAX_STEPS steps ($CELL)"
