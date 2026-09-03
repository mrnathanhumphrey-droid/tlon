#!/usr/bin/env bash
# ═══ KI-AS-TARGET MECHANISM PROBE — the on-instance pipeline ════════════════
#
# Does making `ki` a TARGET (not only a source) relieve the global ki-suppression?
# Prereg: docs/PREREG_KI_AS_TARGET_2026_08_26.md
#   sha256 9b21976c520f7e2660b95391fefc1a4355398a375399e4fe7175b3c35a37b0be
#
# ⛔⛔ THE STAGE ORDER IS THE EXPERIMENT'S INTEGRITY, NOT A CONVENIENCE.
# The throughput fallback CHANGES THE MDE (0.040 → 0.060) and therefore changes
# what counts as PARTIAL vs UNDERPOWERED. That is legitimate only if the branch
# was taken on THROUGHPUT and never on the EFFECT. So:
#
#     train both  →  THROUGHPUT GATE (commits N and MDE)  →  scored arms
#
# and every scored arm is stamped with the commitment's sha256. An arm generated
# before the commitment CANNOT carry its hash, and the analyser refuses it.
# **Do not reorder these stages.**
#
# ⛔⛔ NO STAGE MAY SWALLOW ITS OWN FAILURE, and NO STAGE MAY BE PIPED THROUGH
# `tail`. A previous pipeline reported success while all four stages had failed;
# a later one decapitated a traceback with `tail -4` and cost a session's
# diagnosis. `set -e` + the trap is what makes a red stage stop the run.
set -uo pipefail
trap 'rc=$?; if [ $rc -ne 0 ]; then
        echo "⛔ FAILED at stage: ${STAGE:-<before init>} (rc=$rc)" | tee -a "${LOG:-/dev/null}"
        echo "${STAGE:-<before init>} rc=$rc" > ~/FAILED
      fi' EXIT
set -e

ROOT=runs/act2/ki_target
mkdir -p $ROOT/logs
LOG=$ROOT/pipeline_ki_target.log
STAGE="init"
step() { STAGE="$1"; echo "=== [$1] $(date -u +%H:%M:%S) ===" | tee -a $LOG; }

MODEL=Qwen/Qwen2.5-7B-Instruct
# ⛔⛔ ONE SEQ/BATCH/ACCUM, USED BY EVERY GATE AND EVERY TRAINER SITE. They were
# two separate literals once and they DISAGREED — the gate measured seq 256 while
# the trainer ran 384, and the assert that should have caught it checked the
# trainer line, so the gate's edit no-opped and the assert passed anyway.
SEQ=384
BATCH=4
ACCUM=4
TURNS=40

C_BASE=$ROOT/corpus_bfresh
C_TREAT=$ROOT/corpus_treat
A_BASE=$ROOT/adapter_bfresh
A_TREAT=$ROOT/adapter_treat
A_PRIOR=runs/act2/adapter_mt            # existing, re-served: variance control

# ⛔ BOTH CORPORA ARE PINNED. Built locally and seed-deterministic; the box must
# reproduce them byte-for-byte or it is training on something else.
EXPECT_BASE_TRAIN=263fe3c8cbc5dd9ea7c517b7940a415f2f3b0f078117904e4205d5ab1a7eeea1
EXPECT_BASE_EVAL=a4e658f45581e76df1b85988000803d82704747c39c22514dd798118a2c19799
EXPECT_TREAT_TRAIN=781b1018ac3eef953c5dcb79354f922c1e39b1f94926161ca6ba2ff068421dcc
EXPECT_TREAT_EVAL=7559ee9ac9410827e915e4fd4b573ea26edd5c8058cf63f845e3bc0d3624d867

# ── 0 · PREFLIGHT ──────────────────────────────────────────────────────────
step preflight
python - <<'PY' 2>&1 | tee -a $LOG
# ⛔ IMPORT WHAT THE TRAINER IMPORTS, NOTHING ELSE. A preflight that fails on a
# package nothing needs is worse than none.
import torch, transformers, peft, numpy, jinja2, PIL
from datasets import load_dataset                       # noqa: F401
from peft import LoraConfig, get_peft_model             # noqa: F401
from transformers import (AutoModelForCausalLM, AutoTokenizer,   # noqa: F401
                          DataCollatorForLanguageModeling, Trainer)
print("  torch", torch.__version__, "cuda", torch.cuda.is_available())
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
tok.apply_chat_template([{"role": "user", "content": "x"}], tokenize=False)
assert (torch.randn(64, 64, device="cuda") @ torch.randn(64, 64, device="cuda")).shape
print("  ✅ chat template rendered; CUDA matmul ran")
PY

# ── 0.5 · ⛔⛔ DOES THE REPO EVEN PARSE UNDER *THIS* PYTHON? ────────────────
# This cost a live box. tools/act2_ki_attribution.py used a multi-line
# expression inside an f-string — PEP 701, fine on the 3.12 used for
# development, a hard SyntaxError on the 3.10 this image ships. Stage 1 died on
# a file it could not even import, with the meter running.
# ⚠️ AND THE LOCAL GUARD FOR IT CANNOT BE ast.parse(feature_version=...): that
# ACCEPTS the construct (measured). The only authority is the real interpreter,
# and it costs two seconds.
step syntax_floor
python --version | tee -a $LOG
python -m compileall -q tools/ tlon/ tests/ 2>&1 | tee -a $LOG
echo "  ✅ every module parses under $(python --version 2>&1)" | tee -a $LOG

# ── 1 · THE SUITE ──────────────────────────────────────────────────────────
step tests
python -m pytest tests/ -q 2>&1 | tee -a $LOG | tail -3

# ── 2 · REBUILD BOTH CORPORA AND PIN THEM ──────────────────────────────────
step corpora
python tools/act2_build_multiturn.py --chains 1445 --multiturn-fraction 0.5 \
  --map derived --out $C_BASE 2>&1 | tee -a $LOG
python tools/act2_build_multiturn.py --chains 1445 --multiturn-fraction 0.5 \
  --map stipulated --allow-stipulated --out $C_TREAT 2>&1 | tee -a $LOG

step corpus_pin
check() { [ "$(sha256sum $1 | cut -d' ' -f1)" = "$2" ] || {
            echo "⛔ sha mismatch: $1"; exit 1; }; }
check $C_BASE/train.jsonl  $EXPECT_BASE_TRAIN
check $C_BASE/eval.jsonl   $EXPECT_BASE_EVAL
check $C_TREAT/train.jsonl $EXPECT_TREAT_TRAIN
check $C_TREAT/eval.jsonl  $EXPECT_TREAT_EVAL
echo "  ✅ both corpora pinned" | tee -a $LOG
# ⭐ And the treatment corpus must SAY it is stipulated, in its own manifest.
python - <<'PY' 2>&1 | tee -a $LOG
import json, pathlib, sys
b = json.loads(pathlib.Path("runs/act2/ki_target/corpus_bfresh/manifest.json").read_text())
t = json.loads(pathlib.Path("runs/act2/ki_target/corpus_treat/manifest.json").read_text())
assert b["map_is_STIPULATED"] is False, "baseline corpus is stipulated?!"
assert t["map_is_STIPULATED"] is True, "treatment corpus lost its stipulation label"
assert t["map_stipulated_cells"] == {"ko": "ki"}, t["map_stipulated_cells"]
print(f"  ✅ baseline {b['map_label']} · treatment {t['map_label']} "
      f"{t['map_stipulated_cells']}")
print(f"  primary-measure rows: {t['PRIMARY_MEASURE_ROWS_common_uniform']} "
      f"(stipulated row EXCLUDED)")
PY

# ── 3 · ⛔⛔ THE TOKEN GATE. TRAINING DOES NOT START UNLESS THIS PASSES ──────
# Both arms must match run 3's compute AND each other, at 2 %. A compute
# difference between arms would confound the map effect with a training-budget
# effect — the one thing the whole design holds fixed.
step token_gate
python tools/act2_token_budget.py --model $MODEL --corpus $C_BASE --seq $SEQ \
  --baseline runs/act2/corpus/token_budget.json --tolerance 0.02 \
  --out $C_BASE/token_budget.json 2>&1 | tee -a $LOG
python tools/act2_token_budget.py --model $MODEL --corpus $C_TREAT --seq $SEQ \
  --baseline runs/act2/corpus/token_budget.json --tolerance 0.02 \
  --out $C_TREAT/token_budget.json 2>&1 | tee -a $LOG
python - <<'PY' 2>&1 | tee -a $LOG
import json, pathlib
def tot(p):
    d = json.loads(pathlib.Path(p).read_text())
    for k in ("total_tokens", "tokens", "n_tokens"):
        if k in d:
            return d[k]
    raise SystemExit(f"⛔ no token total in {p}: keys={sorted(d)}")
b = tot("runs/act2/ki_target/corpus_bfresh/token_budget.json")
t = tot("runs/act2/ki_target/corpus_treat/token_budget.json")
rel = abs(b - t) / b
print(f"  baseline {b:,}  treatment {t:,}  relative {rel:.4%}")
assert rel <= 0.02, (
    f"⛔⛔ ARM-VS-ARM COMPUTE MISMATCH {rel:.2%} > 2 %. The map effect would be "
    "confounded with a training-budget effect.")
print("  ✅ arms match each other within 2 %")
PY

# ── 4 · VRAM, MEASURED ─────────────────────────────────────────────────────
# ⛔ The planner's correction factor is NOT a constant (×0.955 to ×1.253 across
# measured anchors, sign-flipping). Apply the WORST factor to a hard wall.
step vram
# ⛔ THERE IS NO `act2_vram_plan.py` — the planner lives inside act2_finetune.py
# as `--plan`, and it applies NO correction factor. The correction is applied
# HERE, explicitly, at its WORST observed value.
python tools/act2_finetune.py --plan --params 7.62 --dtype bf16 \
  --seq $SEQ --batch $BATCH --accum $ACCUM --vram 39 \
  --corpus $C_BASE 2>&1 | tee -a $LOG
python - <<PY 2>&1 | tee -a $LOG
import pathlib, sys
sys.path.insert(0, "tools")
from act2_finetune import plan
# ⛔⛔ THE CORRECTION FACTOR IS NOT A CONSTANT. Measured anchors put it between
# ×0.955 and ×1.253 and it SIGN-FLIPS, so an average would hide the tail. The
# planner is a documented LOWER BOUND; the worst factor against a hard wall is
# the only honest read. (I fabricated a planner figure once — 27.9 against a
# printed 33.3 — which manufactured a false "consistently optimistic" pattern.
# The number below is computed here, never recalled.)
WORST, WALL = 1.253, 40.0
p = plan(7.62, "bf16", $SEQ, $BATCH, 152064)
raw = p["total_GiB"] if "total_GiB" in p else sum(
    v for k, v in p.items() if k.endswith("_GiB"))
print(f"  planner raw {raw:.1f} GiB · worst factor x{WORST} -> "
      f"{raw * WORST:.1f} GiB against a {WALL} GiB wall")
assert raw * WORST < WALL, (
    f"⛔⛔ {raw * WORST:.1f} GiB EXCEEDS the {WALL} GiB wall at seq=$SEQ "
    f"batch=$BATCH. grad-ckpt does NOT rescue this: the LOGITS term dominates "
    f"at this vocab size and checkpointing only touches activations.")
print("  ✅ fits at the worst observed correction")
PY

# ── 5 · TRAIN BOTH. Same hyperparameters, same seed, ONLY the map differs ───
step train_bfresh
python tools/act2_finetune.py --model $MODEL --out $A_BASE --corpus $C_BASE \
  --seq $SEQ --batch $BATCH --accum $ACCUM 2>&1 | tee -a $LOG

step train_treat
python tools/act2_finetune.py --model $MODEL --out $A_TREAT --corpus $C_TREAT \
  --seq $SEQ --batch $BATCH --accum $ACCUM 2>&1 | tee -a $LOG

# ── 6 · F-LOCAL on both, for continuity ────────────────────────────────────
# ⚠️ NOT a probe measure. Reported so a catastrophic training failure is visible
# before 178 exchanges are spent on a broken adapter.
step flocal
python tools/act2_flocal.py --model $MODEL --adapter $A_BASE --n 256 \
  --n-comp 256 2>&1 | tee -a $LOG
python tools/act2_flocal.py --model $MODEL --adapter $A_TREAT --n 256 \
  --n-comp 256 2>&1 | tee -a $LOG

# ── 7 · ⛔⛔ THE THROUGHPUT GATE. COMMITS N AND MDE BEFORE ANY SCORED ARM ────
# Times 3 exchanges, DISCARDS them, projects the full design, branches on the
# projection alone, and writes N_COMMITTED.json. Everything after this carries
# its sha. **This stage must precede stage 8. Do not reorder.**
step throughput_gate
python tools/act2_throughput_gate.py --model $MODEL --adapter $A_BASE \
  --turns $TURNS --timing-exchanges 3 \
  --out $ROOT/N_COMMITTED.json 2>&1 | tee -a $LOG
SHA=$(python -c "import hashlib,pathlib;print(hashlib.sha256(pathlib.Path('$ROOT/N_COMMITTED.json').read_bytes()).hexdigest())")
N_ARM=$(python -c "import json;print(json.load(open('$ROOT/N_COMMITTED.json'))['exchanges_per_arm'])")
N_VAR=$(python -c "import json;print(json.load(open('$ROOT/N_COMMITTED.json'))['variance_arm_exchanges'])")
echo "  ⭐⭐ COMMITTED ${N_ARM}/arm · sha $SHA" | tee -a $LOG

# ── 8 · THE SCORED ARMS. Every one stamped with the commitment sha ─────────
step arm_bfresh
for i in $(seq 1 $N_ARM); do
  python tools/act2_exchange_probe.py --model $MODEL --adapter $A_BASE \
    --turns $TURNS --history-window 1 --commitment $SHA \
    --out $ROOT/logs/bfresh_$i.json 2>&1 | tee -a $LOG
done

step arm_treat
for i in $(seq 1 $N_ARM); do
  python tools/act2_exchange_probe.py --model $MODEL --adapter $A_TREAT \
    --turns $TURNS --history-window 1 --commitment $SHA \
    --out $ROOT/logs/treat_$i.json 2>&1 | tee -a $LOG
done

# ⭐ THE RUN-TO-RUN VARIANCE CONTROL — same map as B-fresh, different training
# run. Without it, "the two trainings are comparable" is assumed, not measured.
step arm_bprior
for i in $(seq 1 $N_VAR); do
  python tools/act2_exchange_probe.py --model $MODEL --adapter $A_PRIOR \
    --turns $TURNS --history-window 1 --commitment $SHA \
    --out $ROOT/logs/bprior_$i.json 2>&1 | tee -a $LOG
done

# ── 9 · THE LOCKED READINGS ────────────────────────────────────────────────
step analyse
python tools/act2_ki_target_analyse.py --logs $ROOT/logs \
  --commitment-file $ROOT/N_COMMITTED.json 2>&1 | tee -a $LOG

step done
# ⭐ PULL THE PIPELINE LOG. Its absence last run is why §5's throughput had to
# become a gate instead of an estimate — the timings died with the box.
echo "⭐ ALL STAGES PASSED — pull $LOG BEFORE killing the box" | tee -a $LOG
touch ~/DONE
