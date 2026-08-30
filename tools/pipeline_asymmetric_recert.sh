#!/usr/bin/env bash
# ═══ ASYMMETRIC SOLO PASS — the first right-regime transcripts in the project ═
#
# Prereg: docs/PREREG_ASYMMETRIC_RECERT_2026_08_30.md  sha a7bc2a7f…
#
# ⛔ --no-injections IS REQUIRED, NOT A SAVING. Contamination is between-build sd
# over within-conversation movement; every build would see the SAME injections,
# so a biased pool compresses that sd and the panel gets certified on poisoned
# data. The injected COLD baseline comes free with the drift run instead.
#
# ⭐ Adapters are UPLOADED here, not trained, so their md5s are pinned against
# the local values before a single token is generated.
set -uo pipefail
trap 'rc=$?; if [ $rc -ne 0 ]; then
        echo "⛔ FAILED at stage: $STAGE (rc=$rc)" | tee -a $LOG
        echo "$STAGE rc=$rc" > ~/FAILED
      fi' EXIT
set -e

ROOT=runs/act2/asym_recert
mkdir -p $ROOT/logs
LOG=$ROOT/pipeline_asymmetric_recert.log
STAGE=init
step() { STAGE="$1"; echo "=== [$1] $(date -u +%H:%M:%S) ===" | tee -a $LOG; }

MODEL=Qwen/Qwen2.5-7B-Instruct
TURNS=40
N_PER_BUILD=14
BUILDS="s20620 s20621 s20622 s20623 t30001 t30002 t30003"
PREREG_SHA=a7bc2a7fd30bc310cc53c4b3e24815c268c20d5495b02af7395e332193ece8b8

step prereg_pin
GOT=$(sha256sum docs/PREREG_ASYMMETRIC_RECERT_2026_08_30.md | cut -d' ' -f1)
[ "$GOT" = "$PREREG_SHA" ] || { echo "⛔⛔ prereg sha mismatch: $GOT"; exit 1; }
echo "  ✅ prereg pinned $PREREG_SHA" | tee -a $LOG

step syntax_floor
python3 --version | tee -a $LOG
python3 -m compileall -q tools/ tlon/ tests/ 2>&1 | tee -a $LOG
echo "  ✅ parses under $(python3 --version 2>&1)" | tee -a $LOG

step adapter_pin
# ⛔⛔ These weights crossed a network. If any byte moved, every number below
# describes a different model than the one on Nate's disk.
cat > /tmp/expect_md5.txt <<'EOF'
fc2084e767440acc85d848325aae9d0d s20620
03aab6f54c0c10fbae2be48664ba115a s20621
f451c60aad3e9580ee0dd8013388411f s20622
6ae36200571862f0e0eeed957c8d885d s20623
1e772c64c3097d631b10cfb957946ee0 t30001
3a889872dfbf14d9c686c640a5b07fe5 t30002
acbde5c9c1be43a0b3a840a35bcfe5fc t30003
EOF
for B in $BUILDS; do
  WANT=$(grep " $B$" /tmp/expect_md5.txt | cut -d' ' -f1)
  GOT=$(md5sum ~/adapters/$B/adapter_model.safetensors | cut -d' ' -f1)
  [ "$WANT" = "$GOT" ] || { echo "⛔⛔ $B md5 $GOT != $WANT"; exit 1; }
done
# ⭐ And they must be SEVEN DISTINCT models — identical weights would be the
# shared-backend fault wearing new filenames.
NDIST=$(cut -d' ' -f1 /tmp/expect_md5.txt | sort -u | wc -l)
[ "$NDIST" = "7" ] || { echo "⛔⛔ only $NDIST distinct adapters"; exit 1; }
echo "  ✅ 7 adapters md5-pinned and mutually distinct" | tee -a $LOG

step preflight
python3 - <<'PY' 2>&1 | tee -a $LOG
import torch
from transformers import AutoTokenizer
print("  torch", torch.__version__, "cuda", torch.cuda.is_available())
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
tok.apply_chat_template([{"role": "user", "content": "x"}], tokenize=False)
assert (torch.randn(64, 64, device="cuda") @ torch.randn(64, 64, device="cuda")).shape
print("  ✅ chat template rendered; CUDA matmul ran")
PY

step tests
python3 -m pytest tests/ -q 2>&1 | tee -a $LOG | tail -3

# ── the pass ────────────────────────────────────────────────────────────────
# ⭐ PER-BUILD WALL TIME IS LOGGED SEPARATELY FROM SETUP. A fixed cost divided
# by a small n is the constant, not a rate — that error made an earlier forecast
# 2x optimistic.
SETUP_END=$(date +%s)
echo "  setup wall: $((SETUP_END - $(date -u -d "$(head -1 $LOG | sed 's/.*] //;s/ ===//')" +%s 2>/dev/null || echo $SETUP_END))) s" | tee -a $LOG || true

for B in $BUILDS; do
  step solo_$B
  T0=$(date +%s)
  for i in $(seq 1 $N_PER_BUILD); do
    python3 tools/act2_two_speaker_probe.py --model $MODEL \
      --adapter-a ~/adapters/$B --no-injections --turns $TURNS \
      --out $ROOT/logs/${B}_solo_$i.json 2>&1 | tee -a $LOG
  done
  T1=$(date +%s)
  echo "  ⏱ $B marginal wall: $((T1-T0)) s for $N_PER_BUILD transcripts" | tee -a $LOG
done

step done
echo "⭐ ALL STAGES PASSED — pull $LOG BEFORE killing the box" | tee -a $LOG
touch ~/DONE
