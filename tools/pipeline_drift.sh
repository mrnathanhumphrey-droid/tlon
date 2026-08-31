#!/usr/bin/env bash
# ═══ THE DRIFT RUN — LIVE vs YOKED on force:ka ══════════════════════════════
#
# Cold table: runs/act2/cold_table_ka.json  sha 84c2a1b5…  FROZEN before this ran.
# Estimand:   W2(LIVE) − W2(YOKED), paired per pair, clustered on the ADAPTER.
#
# ⛔ 80 TURNS, NOT 40. The frozen cold table is built on clouds where each
# speaker contributes 40 own turns. A 40-turn exchange gives each speaker 20,
# and force:ka's binomial se is 0.0754 at 40 turns against 0.1067 at 20 —
# comparing W2 across different cloud sizes is the sample-size confound that
# made the injection pool read 43.8 sd off-centre.
#
# ⛔ INJECTIONS OFF, AND THAT IS A DECISION: the cold table was computed with
# --no-injections, and 0 of 98 in-regime solo transcripts degenerated, so the
# self-reinforcing rut the injections were designed to break did not occur in
# this regime. Running them ON would perturb the dynamics and cost each speaker
# measurable turns, breaking the like-for-like match with the baseline.
set -uo pipefail
trap 'rc=$?; if [ $rc -ne 0 ]; then
        echo "⛔ FAILED at stage: $STAGE (rc=$rc)" | tee -a $LOG
        echo "$STAGE rc=$rc" > ~/FAILED
      fi' EXIT
set -e

ROOT=runs/act2/drift
mkdir -p $ROOT/logs $ROOT/control
LOG=$ROOT/pipeline_drift.log
STAGE=init
T_START=$(date +%s)
step() { STAGE="$1"; echo "=== [$1] $(date -u +%H:%M:%S) ===" | tee -a $LOG; }

PY=${PY:-$HOME/venv/bin/python}
MODEL=Qwen/Qwen2.5-7B-Instruct
TURNS=80
REPS=7
SELF_REPS=3
COLD_SHA=84c2a1b5128229037c979776a5693776369c11edb86c5ff27c6b68dacc9c1ade

# 6 fixed-corpus pairs (trainer seed only) + 6 cross-corpus, covering all 7
PAIRS="s20620:t30001 s20620:t30002 s20620:t30003 t30001:t30002 t30001:t30003 t30002:t30003 \
s20621:s20622 s20621:s20623 s20622:s20623 s20620:s20621 s20622:t30001 s20623:t30002"
SELF="s20620 s20621 s20622 s20623 t30001 t30002 t30003"

step cold_pin
# ⛔⛔ THIS WAS NOT A GUARD. It ran `sha256sum` on the FILE and printed it beside
# $COLD_SHA, which is the sha of the table's CONTENT computed before the sha
# field was embedded in it. Two different quantities by construction — so it
# printed an apparent mismatch, compared nothing, and continued. A check that
# cannot fail has been consulted, not passed.
GOT=$($PY -c "
import hashlib,json,pathlib
d=json.loads(pathlib.Path('runs/act2/cold_table_ka.json').read_text(encoding='utf-8'))
d.pop('sha256',None)
print(hashlib.sha256(json.dumps(d,indent=1,ensure_ascii=False,sort_keys=True).encode()).hexdigest())")
echo "  cold table content sha: $GOT" | tee -a $LOG
echo "  frozen reference:       $COLD_SHA" | tee -a $LOG
[ "$GOT" = "$COLD_SHA" ] || { echo "⛔⛔ COLD TABLE HAS MOVED — the baseline is not the frozen one" | tee -a $LOG; exit 1; }
echo "  ✅ cold table pinned" | tee -a $LOG

step syntax_floor
$PY --version | tee -a $LOG
$PY -m compileall -q tools/ tlon/ tests/ 2>&1 | tee -a $LOG

step tests
$PY -m pytest tests/ -q 2>&1 | tee -a $LOG | tail -3

step adapter_pin
cat > /tmp/expect.txt <<'EOF'
fc2084e767440acc85d848325aae9d0d s20620
03aab6f54c0c10fbae2be48664ba115a s20621
f451c60aad3e9580ee0dd8013388411f s20622
6ae36200571862f0e0eeed957c8d885d s20623
1e772c64c3097d631b10cfb957946ee0 t30001
3a889872dfbf14d9c686c640a5b07fe5 t30002
acbde5c9c1be43a0b3a840a35bcfe5fc t30003
EOF
for B in $SELF; do
  W=$(grep " $B$" /tmp/expect.txt | cut -d' ' -f1)
  G=$(md5sum ~/adapters/$B/adapter_model.safetensors | cut -d' ' -f1)
  [ "$W" = "$G" ] || { echo "⛔⛔ $B md5 $G != $W"; exit 1; }
done
echo "  ✅ 7 adapters md5-pinned" | tee -a $LOG

SETUP_END=$(date +%s)
echo "  ⏱ setup wall (one-time, NOT divisible per pair): $((SETUP_END-T_START)) s" | tee -a $LOG

# ── REAL PAIRS ──────────────────────────────────────────────────────────────
for P in $PAIRS; do
  A=${P%%:*}; B=${P#*:}
  step pair_${A}_${B}
  T0=$(date +%s)
  for i in $(seq 1 $REPS); do
    $PY tools/act2_two_speaker_probe.py --model $MODEL \
      --adapter-a ~/adapters/$A --adapter-b ~/adapters/$B \
      --skip-cold --no-injections --turns $TURNS \
      --out $ROOT/logs/${A}__${B}_$i.json 2>&1 | tee -a $LOG
  done
  T1=$(date +%s)
  echo "  ⏱ ${A}|${B} marginal wall: $((T1-T0)) s for $REPS replicates" | tee -a $LOG
done

# ── ⛔⛔ SELF-PAIR CONTROL — a PRECONDITION for any coupling claim ───────────
# Identical speakers cannot converge, so LIVE−YOKED MUST read ~0 here. If it
# does not, the pipeline manufactures drift and the real-pair result is
# confounded — and a manufactured drift would appear as W2(LIVE) < W2(YOKED),
# the exact signature of the wanted result.
for S in $SELF; do
  step selfpair_$S
  for i in $(seq 1 $SELF_REPS); do
    $PY tools/act2_two_speaker_probe.py --model $MODEL \
      --adapter-a ~/adapters/$S --adapter-b ~/adapters/$S --allow-self-pair \
      --skip-cold --no-injections --turns $TURNS \
      --out $ROOT/control/${S}__self_$i.json 2>&1 | tee -a $LOG
  done
done

step done
echo "⭐ ALL STAGES PASSED — pull $LOG BEFORE killing the box" | tee -a $LOG
touch ~/DONE
