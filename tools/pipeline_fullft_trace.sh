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
# ⭐ THE BREAK IS AT STEP 13 IN TWO RUNS WITH DIFFERENT ASSEMBLIES, so it is a
# fixed event, not a flaky one: the instrument is pointed, not swept.
MAX_STEPS=${MAX_STEPS:-300}
WIN_FROM=${WIN_FROM:-10}; WIN_TO=${WIN_TO:-14}
# ⭐ THE ABLATION SWITCH. GRAD_CKPT=0 removes gradient checkpointing AND the
# enable_input_require_grads() it necessitates -- the two prime suspects, which
# come off together. The memory case for keeping them is 0.5 GiB at this shape.
GRAD_CKPT=${GRAD_CKPT:-1}
CKPT_FLAG=""
if [ "$GRAD_CKPT" = "0" ]; then
  CKPT_FLAG="--no-grad-checkpointing"
  CELL=fwnockpt-s$SEED
fi
# ⭐⭐ THE ATTENTION-KERNEL ABLATION. Every run of this arm has used the
# transformers default (fused SDPA) without ever saying so, making it the one
# major component that has been a CONSTANT rather than a variable — and the
# measurement contradicts the textbook backward (grad_K finite implies dS
# finite; dS and K finite should leave dQ finite; dQ is NaN anyway), which puts
# the answer inside the kernel rather than inside the math.
# ⛔ A ONE-BIT TEST WITH A PRE-DECLARED FORK, so neither branch can be chosen
# after the fact:
#   breaks at 13 under eager -> the fused kernel is EXONERATED and the fault is
#     in the model math; the finer per-tensor hooks then belong under eager,
#     where the intermediates SDPA fuses away are visible.
#   clean under eager        -> the fused kernel is IMPLICATED and the fix is a
#     config one; it must then be shown clean for a real stretch past 13, not
#     merely to 13.
ATTN_IMPL=${ATTN_IMPL:-}
ATTN_FLAG=""
if [ -n "$ATTN_IMPL" ]; then
  ATTN_FLAG="--attn-impl $ATTN_IMPL"
  CELL=fwattn-$ATTN_IMPL-s$SEED
fi

# ⛔⛔ AND AN EXPLICIT OVERRIDE, because two runs of the SAME arm are still two
# different experiments. The un-filtered-loss run uses the same config as the
# first trace, so without a distinct cell it would overwrite that trace's hub
# prefix — destroying the very artifact the comparison is against.
CELL=${CELL_OVERRIDE:-$CELL}

# ⛔ ROOT AND THE LOG ARE INITIALISED AFTER THE ABLATION SWITCH, so a
# checkpointing-off run cannot write into the checkpointing-on run's tree and be
# read afterwards as the same experiment.
ROOT=${ROOT:-runs/act2/fullft_trace_$CELL}
tlon_log_init "$ROOT" pipeline_fullft_trace.log
echo "  arm: CELL=$CELL  grad_checkpointing=$GRAD_CKPT  attn_impl=${ATTN_IMPL:-DEFAULT(sdpa)}  max_steps=$MAX_STEPS" | tee -a $LOG

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
    --max-steps $MAX_STEPS --trace-out $TRACE $CKPT_FLAG $ATTN_FLAG \
    --trace-window-from $WIN_FROM --trace-window-to $WIN_TO \
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
# ⛔ READS `loss_raw`, THE MODEL'S OWN VALUE. The filtered field prints beside
# it so the divergence is visible rather than inferred.
losses = [(r["step"], r.get("loss_raw")) for r in steps]
filt = [(r["step"], r.get("loss_LOGGED_FILTERED")) for r in steps]
print("  steps recorded: %d" % len(steps))
def _f(v):
    return None if v is None else round(v, 4)
print("  RAW loss  first 16: %s" % [(s, _f(l)) for s, l in losses[:16]])
print("  FILTERED  first 16: %s" % [(s, _f(l)) for s, l in filt[:16]])
nanstep = next((s for s, l in losses if l is not None and l != l), None)
print("  FIRST NaN *RAW* LOSS at step: %s" % nanstep)
for r in steps:
    if r.get("activation_absmax"):
        am = sorted(r["activation_absmax"].items(), key=lambda kv: -kv[1])[:4]
        print("  step %-3d act absmax top4: %s  nonfinite=%s"
              % (r["step"],
                 [(k.replace("model.layers.", "L"), round(v, 1)) for k, v in am],
                 (r.get("activation_nonfinite") or [])[:3]))
def _r(v, k=6):
    return None if v is None else round(v, k)
print("  grad_norm POSTCLIP first 8: %s"
      % [(r["step"], _r(r.get("grad_norm_total_POSTCLIP"))) for r in steps[:8]])
print("  grad_norm PRECLIP  first 8: %s"
      % [(r["step"], _r(r.get("grad_norm_total_PRECLIP_ours"))) for r in steps[:8]])
# ⭐⭐ TWO INDEPENDENT INSTRUMENTS ON THE SAME QUANTITY. Ours is summed from the
# per-parameter hooks; HF's comes back from clip_grad_norm_ itself. They should
# agree, and both should be non-finite at the break.
print("  --- PRE-CLIP GLOBAL NORM: ours vs HF's own ---")
for r in steps[:20]:
    hf = r.get("grad_norm_HF_preclip") or {}
    print("    step %-3d ours=%-14s   HF=%-14s (HF step %s)"
          % (r["step"], _r(r.get("grad_norm_total_PRECLIP_ours"), 3),
             _r(hf.get("value"), 3) if isinstance(hf.get("value"), float) else hf.get("value"),
             hf.get("hf_global_step")))
# ⛔⛔ THE COUNT THAT SEPARATES CAUSE FROM CASUALTY. If the pre-clip count is
# small and the post-clip count is 168 at the SAME step, the global clip norm
# did the spreading and the small set is the origin.
print("  --- NON-FINITE COUNT: pre-clip (cause) vs post-clip (spread) ---")
for r in steps[:20]:
    pre = r.get("grad_PRECLIP_nonfinite_n")
    post = r.get("grad_POSTCLIP_nonfinite_n")
    if pre or post:
        print("    step %-3d PRECLIP n=%-4s %s   POSTCLIP n=%s"
              % (r["step"], pre, (r.get("grad_PRECLIP_nonfinite_first") or [])[:3], post))
# ⭐⭐ THE TRAJECTORY ON THE CULPRIT. Compounding vs triggered is the whole
# difference between a fix aimed at the optimizer and a fix aimed at the data.
culprit = None
for r in steps:
    bad = r.get("grad_PRECLIP_nonfinite_first") or []
    if bad:
        culprit = bad[0]
        break
print("  FIRST PRE-CLIP OFFENDER: %s" % culprit)
if culprit:
    print("  --- absmax trajectory (pre-clip) on the offender and the top movers ---")
    watch = [culprit]
    for r in steps:
        am = r.get("grad_absmax_PRECLIP")
        if am:
            watch += [k for k, _ in sorted(am.items(), key=lambda kv: -(kv[1] if kv[1] == kv[1] else 0))[:4]]
            break
    seen = []
    for w in watch:
        if w not in seen:
            seen.append(w)
    for w in seen[:5]:
        traj = [(r["step"], _r((r.get("grad_absmax_PRECLIP") or {}).get(w), 3))
                for r in steps if r.get("grad_absmax_PRECLIP")]
        print("    %-52s %s" % (w.replace("model.layers.", "L"), traj))
for r in steps:
    arr = r.get("preclip_arrival_order")
    bad = set(r.get("grad_PRECLIP_nonfinite_first") or [])
    if arr and bad:
        order = [n for m, n in arr if m == 0]
        pos = [(i, n) for i, n in enumerate(order) if n in bad]
        print("  ARRIVAL ORDER at step %s: %d tensors finalised; first bad at position %s"
              % (r["step"], len(order), pos[:3]))
        break
fn = summary.get("first_nonfinite") if summary else None
print("  FIRST NON-FINITE: %s" % fn)
# ⛔ The pre-declared readings, decided here.
if fn is None:
    if losses and losses[-1][1] is not None and losses[-1][1] < 0.01:
        print("  READING: DEGENERATE OBJECTIVE — loss collapsed with NO non-finite")
        print("           value anywhere. The NaN in the full run is downstream;")
        print("           the objective itself produces no signal at real scale.")
    else:
        print("  READING: NO NON-FINITE VALUE ANYWHERE in %s steps." % len(steps))
        print("           The break has been at step 13 in THREE runs with three")
        print("           different assemblies, so passing 13 is a real signal.")
        print("  ⛔⛔ BUT 'DID NOT BREAK' IS NOT 'FIXED'. This run changed a")
        print("           component; what it licenses is 'the changed component is")
        print("           IMPLICATED', and nothing about whether the config trains")
        print("           to a usable model. A clean stretch far past 13 is the")
        print("           next question, not a conclusion available here.")
elif fn["quantity"] == "grad_PRECLIP":
    print("  READING: BACKWARD NUMERICAL, NAMED. %s tensor(s) went non-finite" % fn["n"])
    print("           INSIDE the backward, before any clipping: %s" % fn["tensors"][:4])
    print("           n=%s at step %s (rank %s)." % (fn["n"], fn["step"], fn["rank"]))
elif fn["quantity"] == "grad_POSTCLIP":
    print("  ⛔ READING: POST-CLIP ONLY — the pre-clip hook saw NOTHING non-finite")
    print("     at the step the post-clip scan did. That is not the clip spreading")
    print("     an overflow; it means the CLIP ITSELF produced the non-finite value")
    print("     from finite inputs, which is a different mechanism entirely.")
else:
    print("  READING: OPTIMIZER PATH — weights/moments went non-finite before any")
    print("           gradient did (%s, rank %s)." % (fn["quantity"], fn["rank"]))
PY

# ── 5 · THE GATE ON ~/DONE ──────────────────────────────────────────────────
TLON_SUMMARY="⭐ TRACE CAPTURED — $MAX_STEPS steps of the real config, PERSISTED"
tlon_persist_run_files "$PY" "$ROOT" "$HF_REPO"
tlon_mark_done "$HF_REPO" "step trace over $MAX_STEPS steps ($CELL)"
