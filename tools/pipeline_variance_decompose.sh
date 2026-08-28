#!/usr/bin/env bash
# ═══ VARIANCE DECOMPOSITION — data draw or training draw? ═══════════════════
#
# Prereg: docs/PREREG_VARIANCE_DECOMPOSE_2026_08_28.md
#
# ⭐ THE ONE THING THAT MAKES THIS WORK: the corpus is held BYTE-IDENTICAL to
# B-fresh's and only --seed (trainer init / shuffle / dropout) varies. Everything
# measured against S_combined = 0.1549, where seed drove BOTH corpus and trainer.
set -uo pipefail
trap 'rc=$?; if [ $rc -ne 0 ]; then
        echo "⛔ FAILED at stage: $STAGE (rc=$rc)" | tee -a $LOG
        echo "$STAGE rc=$rc" > ~/FAILED
      fi' EXIT
set -e

ROOT=runs/act2/var_decomp
mkdir -p $ROOT/logs
LOG=$ROOT/pipeline_variance_decompose.log
STAGE=init
step() { STAGE="$1"; echo "=== [$1] $(date -u +%H:%M:%S) ===" | tee -a $LOG; }

MODEL=Qwen/Qwen2.5-7B-Instruct
SEQ=384; BATCH=4; ACCUM=4; TURNS=40
EXCH_W1=14        # window-1, comparable to every prior arm
EXCH_ACC=8        # accumulating — the only regime where coupling can exist
SEEDS="30001 30002 30003"

# ⛔ THE SAME CORPUS B-FRESH TRAINED ON. Rebuilt from seed 20620 and sha-checked;
# if this does not match, the decomposition is meaningless because the corpus
# would be varying too.
CORPUS=$ROOT/corpus_fixed
EXPECT_TRAIN=263fe3c8cbc5dd9ea7c517b7940a415f2f3b0f078117904e4205d5ab1a7eeea1
EXPECT_EVAL=a4e658f45581e76df1b85988000803d82704747c39c22514dd798118a2c19799

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

# ── 1 · ONE CORPUS, PINNED TO B-FRESH'S ────────────────────────────────────
step corpus
python tools/act2_build_multiturn.py --chains 1445 --multiturn-fraction 0.5 \
  --map derived --seed 20620 --out $CORPUS 2>&1 | tee -a $LOG

step corpus_pin
GT=$(sha256sum $CORPUS/train.jsonl | cut -d' ' -f1)
GE=$(sha256sum $CORPUS/eval.jsonl  | cut -d' ' -f1)
[ "$GT" = "$EXPECT_TRAIN" ] || { echo "⛔⛔ train sha != B-fresh's — the corpus is NOT held fixed and the decomposition is void"; exit 1; }
[ "$GE" = "$EXPECT_EVAL"  ] || { echo "⛔⛔ eval sha != B-fresh's";  exit 1; }
echo "  ✅ corpus BYTE-IDENTICAL to B-fresh's ($EXPECT_TRAIN)" | tee -a $LOG

step token_gate
python tools/act2_token_budget.py --model $MODEL --corpus $CORPUS --seq $SEQ \
  --baseline runs/act2/corpus/token_budget.json --tolerance 0.02 \
  --out $CORPUS/token_budget.json 2>&1 | tee -a $LOG

step vram
python - <<PY 2>&1 | tee -a $LOG
import sys; sys.path.insert(0, "tools")
from act2_finetune import plan
WORST, WALL = 1.253, 40.0
p = plan(7.62, "bf16", $SEQ, $BATCH, 152064); raw = p["total_GiB"]
print(f"  planner raw {raw:.1f} GiB x{WORST} -> {raw*WORST:.1f} vs {WALL} wall")
assert raw * WORST < WALL, "⛔⛔ exceeds the wall"
print("  ✅ fits at the worst observed correction")
PY

# ── 2 · THREE TRAINERS ON THE SAME DATA ────────────────────────────────────
for S in $SEEDS; do
  step train_t$S
  python tools/act2_finetune.py --model $MODEL --out $ROOT/adapter_t$S \
    --corpus $CORPUS --seq $SEQ --batch $BATCH --accum $ACCUM --seed $S \
    2>&1 | tee -a $LOG

  step flocal_t$S
  python tools/act2_flocal.py --model $MODEL --adapter $ROOT/adapter_t$S \
    --n 64 --n-comp 64 2>&1 | tee -a $LOG

  # window-1: comparable to every prior arm, feeds the decomposition
  step arm_w1_t$S
  for i in $(seq 1 $EXCH_W1); do
    python tools/act2_exchange_probe.py --model $MODEL \
      --adapter $ROOT/adapter_t$S --turns $TURNS --history-window 1 \
      --out $ROOT/logs/t${S}_w1_$i.json 2>&1 | tee -a $LOG
  done

  # ⭐ ACCUMULATING: the only regime in which coupling can exist at all.
  # Each run emits its own yoked pair (interacting + frozen-partner control).
  step arm_acc_t$S
  for i in $(seq 1 $EXCH_ACC); do
    python tools/act2_exchange_probe.py --model $MODEL \
      --adapter $ROOT/adapter_t$S --turns $TURNS \
      --out $ROOT/logs/t${S}_acc_$i.json 2>&1 | tee -a $LOG
  done
done

# ── 3 · DECOMPOSE, RE-SCREEN, COUPLING ─────────────────────────────────────
step analyse
python tools/act2_variance_decompose.py --logs $ROOT/logs \
  --bfresh-logs runs/act2/ki_target/logs 2>&1 | tee -a $LOG

step done
echo "⭐ ALL STAGES PASSED — pull $LOG BEFORE killing the box" | tee -a $LOG
touch ~/DONE
