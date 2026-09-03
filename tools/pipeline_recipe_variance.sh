#!/usr/bin/env bash
# ═══ RECIPE VARIANCE — does building this model twice give the same speaker? ══
#
# Prereg: docs/PREREG_RECIPE_VARIANCE_2026_08_27.md
# One map (DERIVED_v1). No treatment arm. Three new seeds; B-fresh (20620) is
# already measured and is the fourth draw.
#
# ⛔ NO THROUGHPUT BRANCH THIS TIME, ON PURPOSE. There is no fallback that
# preserves the estimate — dropping adapters is the one thing that destroys it.
# The cost is accepted up front rather than branched on. (Last run's "budget" was
# a switch, not a cap, and the unspecified third case cost ~$13.)
set -uo pipefail
trap 'rc=$?; if [ $rc -ne 0 ]; then
        echo "⛔ FAILED at stage: ${STAGE:-<before init>} (rc=$rc)" | tee -a "${LOG:-/dev/null}"
        echo "${STAGE:-<before init>} rc=$rc" > ~/FAILED
      fi' EXIT
set -e

ROOT=runs/act2/recipe_var
mkdir -p $ROOT/logs
LOG=$ROOT/pipeline_recipe_variance.log
STAGE=init
step() { STAGE="$1"; echo "=== [$1] $(date -u +%H:%M:%S) ===" | tee -a $LOG; }

MODEL=Qwen/Qwen2.5-7B-Instruct
SEQ=384; BATCH=4; ACCUM=4; TURNS=40; EXCH=14
SEEDS="20621 20622 20623"

# ⛔ Pinned from the local build. Seed-deterministic given fixed code — the box
# must reproduce them byte-for-byte or it is training on something else.
declare -A SHA_TRAIN SHA_EVAL
SHA_TRAIN[20621]=078b8ccd67e5047672214b170414ffe3b23cb306620b9864175df8ad1a19e49c
SHA_EVAL[20621]=64493de8a749e08ccc6df8301be8d1591f80b08589f6110c957a1532ccc7cd04
SHA_TRAIN[20622]=ca01ae3ed952a0a103d2540e35b476b97afa250f9004d438b69ed217f23d5700
SHA_EVAL[20622]=f8632d17a159a621df387a0c8e9b066eb08e04f5b6c8e73c3ffa85d7b7463546
SHA_TRAIN[20623]=cbd2aa768b36eef4a3ca0bca57cd97e89c60b25819c4f54970bc59443d265974
SHA_EVAL[20623]=1eafdf3ef4f8d797d9381597290188e1d6a5b41f43e4e75b5b2430ce591be815

# ── 0 · DOES THE REPO PARSE UNDER *THIS* PYTHON? ───────────────────────────
# ⛔⛔ The box runs 3.10; development is on 3.12. A PEP 701 f-string cost a live
# box at stage 1 last run, on a file that could not even be imported.
step syntax_floor
python --version | tee -a $LOG
python -m compileall -q tools/ tlon/ tests/ 2>&1 | tee -a $LOG
echo "  ✅ parses under $(python --version 2>&1)" | tee -a $LOG

step preflight
python - <<'PY' 2>&1 | tee -a $LOG
import torch, transformers, peft, numpy, jinja2, PIL
from transformers import AutoTokenizer
print("  torch", torch.__version__, "cuda", torch.cuda.is_available())
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
tok.apply_chat_template([{"role": "user", "content": "x"}], tokenize=False)
assert (torch.randn(64, 64, device="cuda") @ torch.randn(64, 64, device="cuda")).shape
print("  ✅ chat template rendered; CUDA matmul ran")
PY

step tests
python -m pytest tests/ -q 2>&1 | tee -a $LOG | tail -3

# ── 1 · THE THREE CORPORA, REBUILT AND PINNED ──────────────────────────────
step corpora
for S in $SEEDS; do
  # ⛔ --recipe REQUIRED: this pipeline builds the CONTROL arm.
  python tools/act2_build_multiturn.py --recipe content-free --chains 1445 --multiturn-fraction 0.5 \
    --map derived --seed $S --out $ROOT/corpus_s$S 2>&1 | tee -a $LOG
done

step corpus_pin
for S in $SEEDS; do
  GT=$(sha256sum $ROOT/corpus_s$S/train.jsonl | cut -d' ' -f1)
  GE=$(sha256sum $ROOT/corpus_s$S/eval.jsonl  | cut -d' ' -f1)
  [ "$GT" = "${SHA_TRAIN[$S]}" ] || { echo "⛔ s$S train sha mismatch"; exit 1; }
  [ "$GE" = "${SHA_EVAL[$S]}"  ] || { echo "⛔ s$S eval sha mismatch";  exit 1; }
  echo "  ✅ s$S pinned" | tee -a $LOG
done

# ── 2 · TOKEN GATE ─────────────────────────────────────────────────────────
# Verified locally before the box (+0.19 / -0.11 / -1.34 / -1.39 % vs run 3, max
# spread 1.58 %). Re-run here because the box is the environment that trains.
step token_gate
for S in $SEEDS; do
  python tools/act2_token_budget.py --model $MODEL --corpus $ROOT/corpus_s$S \
    --seq $SEQ --baseline runs/act2/corpus/token_budget.json --tolerance 0.02 \
    --out $ROOT/corpus_s$S/token_budget.json 2>&1 | tee -a $LOG
done

step vram
python - <<PY 2>&1 | tee -a $LOG
import sys; sys.path.insert(0, "tools")
from act2_finetune import plan
WORST, WALL = 1.253, 40.0        # the factor is NOT a constant; use the worst
p = plan(7.62, "bf16", $SEQ, $BATCH, 152064)
raw = p["total_GiB"]
print(f"  planner raw {raw:.1f} GiB x{WORST} -> {raw*WORST:.1f} vs {WALL} wall")
assert raw * WORST < WALL, "⛔⛔ exceeds the wall"
print("  ✅ fits at the worst observed correction")
PY

# ── 3 · TRAIN · F-LOCAL TRIPWIRE · EXCHANGES, PER SEED ─────────────────────
# ⭐ F-LOCAL at n=64, not 256: it is PRE-DECLARED NEUTRAL here and used only to
# catch a catastrophically broken adapter before 14 exchanges are spent on it.
# 256 samples would cost 45 min per adapter to buy precision on a neutral number.
for S in $SEEDS; do
  step train_s$S
  python tools/act2_finetune.py --model $MODEL --out $ROOT/adapter_s$S \
    --corpus $ROOT/corpus_s$S --seq $SEQ --batch $BATCH --accum $ACCUM \
    --seed $S 2>&1 | tee -a $LOG

  step flocal_s$S
  python tools/act2_flocal.py --model $MODEL --adapter $ROOT/adapter_s$S \
    --n 64 --n-comp 64 2>&1 | tee -a $LOG

  step arm_s$S
  for i in $(seq 1 $EXCH); do
    python tools/act2_exchange_probe.py --model $MODEL \
      --adapter $ROOT/adapter_s$S --turns $TURNS --history-window 1 \
      --out $ROOT/logs/s${S}_$i.json 2>&1 | tee -a $LOG
  done
done

# ── 4 · THE SPREAD ─────────────────────────────────────────────────────────
step analyse
python tools/act2_recipe_variance.py --logs $ROOT/logs \
  --bfresh-logs runs/act2/ki_target/logs 2>&1 | tee -a $LOG

step done
echo "⭐ ALL STAGES PASSED — pull $LOG BEFORE killing the box" | tee -a $LOG
touch ~/DONE
