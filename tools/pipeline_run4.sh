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
