#!/usr/bin/env bash
# ═══ MULTI-TURN LOCALITY RUN — the on-instance pipeline ════════════════════
#
# Markov depth-1, force-connected, content-free. The corpus trains the painting
# habit; the arena measures whether force transmits (Q1) and whether the
# substrate can hold a flat prior (Q2).
#
# ⛔⛔ THE TOKEN MATCH IS A GATE, NOT A CHECK. Training does not start unless the
# corpus lands within 2 % of run 3's 9,542,574 tokens. A mismatch discovered
# after training is a wasted rental; discovered before, it is a rebuild.
#
# ⛔⛔ NO STAGE MAY SWALLOW ITS OWN FAILURE. A previous version of this file ran
# every stage unconditionally and reported success while ALL FOUR HAD FAILED.
# `set -e` plus the trap is what makes a red stage stop the run.
set -uo pipefail
trap 'rc=$?; if [ $rc -ne 0 ]; then
        echo "⛔ FAILED at stage: $STAGE (rc=$rc)" | tee -a $LOG
        echo "$STAGE rc=$rc" > ~/FAILED
      fi' EXIT
set -e

mkdir -p runs/act2/logs
LOG=runs/act2/logs/pipeline_mt.log
STAGE="init"
step() { STAGE="$1"; echo "=== [$1] $(date -u +%H:%M:%S) ===" | tee -a $LOG; }

MODEL=Qwen/Qwen2.5-7B-Instruct
CORPUS=runs/act2/corpus_mt
RUN3=runs/act2/run3_adapter

# ⛔ THE CORPUS IS PINNED. A pipeline that trains on whatever happens to be on
# disk cannot tell you what it trained on.
EXPECT_TRAIN=5fea15f19c5622946fadba6b3c09c189d2b5a60301c25d185db7d45d2860b559
EXPECT_EVAL=394234841b6d0f0e2858822b3d333a665092ca5472993b29a43df0d78277e085

# ── 0 · PREFLIGHT — exercise every import AND the paths that broke before ──
step preflight
python - <<'PY' 2>&1 | tee -a $LOG
# ⛔ IMPORT WHAT THE TRAINER ACTUALLY IMPORTS, NOTHING ELSE. The first version
# of this preflight imported `trl`, which act2_finetune.py does not use and
# requirements-lambda.txt does not pin — it would have failed the run at stage 0
# on a package nothing needs. A preflight that checks the wrong things is worse
# than none: it fails on absences that do not matter and passes over ones that do.
import torch, transformers, peft, numpy, jinja2, PIL
from datasets import load_dataset                       # noqa: F401
from peft import LoraConfig, get_peft_model             # noqa: F401
from transformers import (AutoModelForCausalLM, AutoTokenizer,   # noqa: F401
                          DataCollatorForLanguageModeling, Trainer)
print("  torch", torch.__version__, "cuda", torch.cuda.is_available())
print("  transformers", transformers.__version__, "peft", peft.__version__)
print("  numpy", numpy.__version__, "jinja2", jinja2.__version__)
# ⛔ jinja2 only fails at the FIRST REAL chat-template call, and numpy only at
# the first `np.ndarray[...]` annotation. Import success proved neither, four
# times. Exercise them.
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
tok.apply_chat_template([{"role": "user", "content": "x"}], tokenize=False)
assert (torch.randn(64, 64, device="cuda") @ torch.randn(64, 64, device="cuda")).shape
print("  ✅ chat template rendered; CUDA matmul ran")
PY

# ── 1 · THE SUITE ─────────────────────────────────────────────────────────
step tests
python -m pytest tests/ -q 2>&1 | tail -3 | tee -a $LOG

# ── 2 · THE CORPUS IS THE ONE WE BUILT ────────────────────────────────────
step corpus_pin
GOT_TRAIN=$(sha256sum $CORPUS/train.jsonl | cut -d' ' -f1)
GOT_EVAL=$(sha256sum $CORPUS/eval.jsonl | cut -d' ' -f1)
[ "$GOT_TRAIN" = "$EXPECT_TRAIN" ] || { echo "⛔ train.jsonl sha mismatch"; exit 1; }
[ "$GOT_EVAL"  = "$EXPECT_EVAL"  ] || { echo "⛔ eval.jsonl sha mismatch";  exit 1; }
echo "  ✅ corpus pinned" | tee -a $LOG
python - <<'PY' 2>&1 | tee -a $LOG
import json, pathlib
m = json.loads(pathlib.Path("runs/act2/corpus_mt/manifest.json").read_text())
print(f"  held variable: {m['held_variable']}")
print(f"  compute share requested {m['multiturn_fraction_requested_BY_COMPUTE']}, "
      f"rows derived {m['multiturn_fraction_by_rows_DERIVED']:.3f}")
print(f"  provocation sha {m['provocation_sha']}  forced {m['forced_cells']}")
PY

# ── 3 · ⛔⛔ THE TOKEN GATE. TRAINING DOES NOT START UNLESS THIS PASSES ─────
step token_gate
python tools/act2_token_budget.py --model $MODEL --corpus $CORPUS \
  --baseline runs/act2/corpus/token_budget.json --tolerance 0.02 \
  --out $CORPUS/token_budget.json 2>&1 | tee -a $LOG
echo "  ✅ tokens held against run 3 within 2 %" | tee -a $LOG

# ── 4 · TRAIN ─────────────────────────────────────────────────────────────
step train
python tools/act2_finetune.py --model $MODEL --out runs/act2/adapter_mt \
  --corpus $CORPUS --seq 256 --batch 8 --accum 2 2>&1 | tee -a $LOG

# ── 5 · F-LOCAL — render/speak/comprehension on the new adapter ────────────
# ⚠️ PRE-DECLARED NEUTRAL. At 0.5 compute the multi-turn task is a small
# perturbation on a nearly identical task, so render/speak barely moving is
# EXPECTED and is evidence of NOTHING. Q1 is the only evidence of learning.
step flocal
python tools/act2_flocal.py --model $MODEL --adapter runs/act2/adapter_mt \
  --n 256 --n-comp 256 2>&1 | tee -a $LOG

# ── 6 · THE FOUR ARMS ─────────────────────────────────────────────────────
# ⛔ Arm 1 is the one that must reproduce the measured null. If it does NOT
# degenerate we cannot reproduce our own null and NOTHING ELSE MAY BE READ.
step arm1_new_accumulate
python tools/act2_exchange_probe.py --model $MODEL --adapter runs/act2/adapter_mt \
  --turns 40 --out runs/act2/logs/arm1_new_accum.json 2>&1 | tee -a $LOG

step arm2_new_depth1
for i in $(seq 1 14); do
  python tools/act2_exchange_probe.py --model $MODEL --adapter runs/act2/adapter_mt \
    --turns 40 --history-window 1 \
    --out runs/act2/logs/arm2_new_w1_$i.json 2>&1 | tail -4 | tee -a $LOG
done

# ⭐ THE ATTRIBUTION BASELINE. Run 3 RE-SERVED under the same provocation, so
# Q1's clean-positive branch attributes to training + train-time contract and
# NEVER to serve-time contract matching.
step arm3_run3_reserved
for i in $(seq 1 14); do
  python tools/act2_exchange_probe.py --model $MODEL --adapter $RUN3 \
    --turns 40 --history-window 1 \
    --out runs/act2/logs/arm3_run3_w1_$i.json 2>&1 | tail -4 | tee -a $LOG
done

# ── 7 · RULING 15 — the temperature floor, at REAL conversational depth ────
step temp_floor
python tools/act2_temp_sweep.py --model $MODEL --adapter $RUN3 --depth 3 \
  --out runs/act2/logs/temp_floor_depth3.json 2>&1 | tee -a $LOG

step done
echo "⭐ ALL STAGES PASSED" | tee -a $LOG
touch ~/DONE
