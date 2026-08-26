#!/usr/bin/env bash
# ═══ RUN 4 — §8.2, the corrected corpus. ON-INSTANCE PIPELINE ═══════════════
#
# ⛔⛔ IT WRITES `DONE` ONLY ON SUCCESS. The run-2 pipeline wrote DONE
# unconditionally and reported success while ALL FOUR STAGES HAD FAILED. Every
# stage here is checked, and a failure writes FAILED_<stage> and stops.
#
# ⛔ `set -e` alone is not enough — a failure inside a pipe or a subshell can
# still let the script reach the end. The exit trap is what actually decides.
set -uo pipefail

cd ~/tlon
mkdir -p runs/act2/logs
LOG=runs/act2/logs/pipeline.log
STAGE="init"

finish() {
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "⛔ FAILED at stage: $STAGE (rc=$rc)" | tee -a $LOG
    echo "$STAGE rc=$rc" > ~/FAILED
    rm -f ~/DONE
  fi
}
trap finish EXIT

step() { STAGE="$1"; echo "=== [$1] $(date -u +%H:%M:%S) ===" | tee -a $LOG; }
die()  { echo "⛔ $1" | tee -a $LOG; exit 1; }

MODEL=Qwen/Qwen2.5-7B-Instruct

# ── 0 · ⛔⛔ PREFLIGHT — IMPORT EVERYTHING EVERY STAGE WILL NEED, NOW ──────
#
# FOUR environment breaks in this arc, each found by a DIFFERENT stage, each
# with the meter running:
#   Pillow 9.0.1   → died importing PEFT
#   numpy/torch    → ABI breakage
#   Jinja2 3.0.3   → died at the first real GENERATION (stage 4)
#   numpy 1.21.5   → died at `DataCollatorForLanguageModeling`'s class body,
#                    which uses `np.ndarray[...]` — needs numpy ≥ 1.22 (stage 5,
#                    AFTER the baseline had already passed)
#
# ⛔⛔ THE LAST ONE IS THE LESSON AND IT WAS MY OWN NOTE THAT WAS WRONG. I wrote
# "numpy 1.21.5 … worked" into requirements-lambda.txt because nothing had failed
# yet. Nothing had failed because NOTHING ON THE PATH RUN SO FAR IMPORTED THE
# COLLATOR. Absence of a failure on an unexercised path is not evidence the path
# works — it is the absence of a test.
#
# ⭐ SO THE FIX IS STRUCTURAL, NOT ANOTHER PIN: import every symbol every later
# stage uses, and exercise the two runtime paths that import-time cannot see
# (chat templating, a CUDA matmul). Costs seconds; each of the four above cost
# between $0.30 and a 66-minute training run.
step "0-preflight"
python - <<'PY' 2>&1 | tee -a $LOG
import numpy, torch
assert tuple(int(x) for x in numpy.__version__.split(".")[:2]) >= (1, 22), (
    f"numpy {numpy.__version__} cannot subscript np.ndarray[...]; "
    "DataCollatorForLanguageModeling's class body needs >= 1.22")
assert torch.cuda.is_available(), "no CUDA"
a = torch.randn(8, 8, device="cuda")
assert float((a @ a).sum()) == float((a @ a).sum()), "cuda matmul is not finite"
# every symbol the later stages import
from transformers import (AutoModelForCausalLM, AutoTokenizer,          # noqa: F401
                          DataCollatorForLanguageModeling, Trainer,     # noqa: F401
                          TrainingArguments)                            # noqa: F401
from peft import LoraConfig, get_peft_model, PeftModel                  # noqa: F401
from datasets import load_dataset                                       # noqa: F401
# ⛔ THE PATH IMPORTS CANNOT REACH: templating only fails when something
# actually prompts the model. This is the jinja2 failure, caught in 2 seconds.
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
s = tok.apply_chat_template([{"role": "user", "content": "x"}], tokenize=False,
                            add_generation_prompt=True)
assert "<|im_start|>" in s, s[:80]
print(f"  ✅ preflight: numpy {numpy.__version__} · torch {torch.__version__} · "
      f"cuda live · trainer imports · chat template renders")
PY
[ "${PIPESTATUS[0]}" = "0" ] || die "preflight failed — fix the box before spending GPU time"

# ── 1 · the suite, on the box ─────────────────────────────────────────────
step "1-suite"
python -m pytest tests/ -q 2>&1 | tail -3 | tee -a $LOG
[ "${PIPESTATUS[0]}" = "0" ] || die "suite failed on the box"

# ── 2 · ⛔ THE CORPUS MUST BE THE ONE THAT WAS MEASURED ───────────────────
# The whole experiment is "tokens held to −0.13 %". That claim is about a
# specific file. If what landed here is not byte-identical to what was counted,
# the token match is a statement about a file that is not being trained on.
step "2-corpus-integrity"
EXPECT_TRAIN=7ee9c98a6ee9ae205ad8eebaffe27ef32da302764c9c5ee072f72e5485085772
GOT_TRAIN=$(sha256sum runs/act2/corpus/train.jsonl | cut -d' ' -f1)
echo "  train.jsonl sha256 $GOT_TRAIN" | tee -a $LOG
[ "$GOT_TRAIN" = "$EXPECT_TRAIN" ] || die "corpus sha MISMATCH — expected $EXPECT_TRAIN"
python - <<'PY' 2>&1 | tee -a $LOG
import json
rows = [json.loads(l) for l in open("runs/act2/corpus/train.jsonl", encoding="utf-8")]
assert len(rows) == 63603, f"rows {len(rows)}"
src = {}
for r in rows:
    src[r.get("source", "?")] = src.get(r.get("source", "?"), 0) + 1
print(f"  rows {len(rows):,} · {src}")
m = json.load(open("runs/act2/corpus/meta.json", encoding="utf-8"))
assert m["tokens"] == 9527752, m["tokens"]
assert m["token_verdict"] == "HELD", m["token_verdict"]
print(f"  tokens {m['tokens']:,} vs run3 {m['tokens_baseline_run3']:,} "
      f"({m['tokens_delta_fraction']:+.4%}) ⇒ {m['token_verdict']}")
print(f"  slot_floor {m['slot_floor']} · contrastive {m['contrastive_per_confusion']}"
      f"/confusion · pruned {m['pruned_over_seq']}")
PY
[ "${PIPESTATUS[0]}" = "0" ] || die "corpus content check failed"

# ── 3 · backbone ──────────────────────────────────────────────────────────
step "3-backbone"
python - <<PY 2>&1 | tail -2 | tee -a $LOG
from huggingface_hub import snapshot_download
print(snapshot_download("$MODEL"))
PY
[ "${PIPESTATUS[0]}" = "0" ] || die "backbone fetch failed"

# ── 4 · ⭐ BASELINE FIRST — the instrument's own canary ───────────────────
# The base model has not changed, so this number is KNOWN: render 0.0 %, speak
# 0.0 %. It is re-measured anyway because it is the cheapest available check
# that the gate on THIS box behaves like the gate on the last one. A non-zero
# baseline here would mean the environment, not the model, moved.
step "4-baseline"
python tools/act2_flocal.py --model $MODEL --n 64 --n-comp 64 2>&1 | tee -a $LOG
[ "${PIPESTATUS[0]}" = "0" ] || die "baseline gate failed"

# ── 5 · the fine-tune ─────────────────────────────────────────────────────
# ⛔ EVERY VARIABLE HELD TO RUN 3 EXCEPT THE TWO UNDER TEST:
#   bf16 · lr 1e-4 · rank 32 · 1 epoch · effective batch 16 · A100-40GB
#   batch 8 × accum 2 == run 3's batch 16 × accum 1 (same effective batch, same
#   step count, one extra forward) — forced by seq 256, which is itself forced:
#   at run 3's seq 192 this corpus loses the TARGET on 15.5 % of rows.
step "5-finetune"
python tools/act2_finetune.py --model $MODEL --out runs/act2/adapter \
  --dtype bf16 --seq 256 --batch 8 --accum 2 --epochs 1 \
  --lr 1e-4 --rank 32 --save-steps 500 2>&1 | tail -40 | tee -a $LOG
[ "${PIPESTATUS[0]}" = "0" ] || die "fine-tune failed"
[ -f runs/act2/adapter/adapter_model.safetensors ] || die "no adapter written"

# ── 6 · ⭐⭐ THE GATE. n=256, same battery as run 3's (8d21aa635d5729fd) ──
step "6-gate"
python tools/act2_flocal.py --model $MODEL --adapter runs/act2/adapter \
  --n 256 --n-comp 256 2>&1 | tee -a $LOG
[ "${PIPESTATUS[0]}" = "0" ] || die "gate failed"

# ── 7 · Diagnostic C — the curve, keyed on VALID not the saturated metric ─
step "7-diagnosis-c"
python tools/act2_diagnose_c.py --model $MODEL \
  --adapter-root runs/act2/adapter --n 12 2>&1 | tee -a $LOG
[ "${PIPESTATUS[0]}" = "0" ] || die "diagnosis C failed"

step "complete"
echo "ok" > ~/DONE
echo "⭐ ALL STAGES PASSED" | tee -a $LOG
