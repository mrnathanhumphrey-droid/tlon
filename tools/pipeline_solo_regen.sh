#!/usr/bin/env bash
# ═══ SOLO REGENERATION — the 84 transcripts a self-terminating box took ══════
#
# ⛔⛔ THIS IS A PROBE RE-RUN, NOT A RETRAIN. The six adapters SURVIVED
# (`runs/act2/retrain12/SALVAGE_2026_09_04.md`): md5-verified against checksums
# computed on the box before the pull, and persisted to HF. What was lost was
# their 84 solo transcripts — 6 builds x 14 — because `retrain12` SUCCEEDED,
# wrote `~/DONE`, and its own watchdog terminated it within one 300 s poll.
# ⭐ GPU training is not bit-deterministic; retraining would produce DIFFERENT
# adapters under the same names, which is the caveat-in-the-name failure. These
# transcripts must come from THESE weights.
#
# ⛔⛔ THE PROCEDURE IS COPIED FROM pipeline_asymmetric_recert.sh LINE BY LINE,
# NOT REMEMBERED. The frozen ruler (`act2_distance`, ASYM_BUILDS) is computed
# over `<build>_solo_*.json` produced by act2_two_speaker_probe with
# `--no-injections --turns 40`. ⛔ NOT recipe_var's `arm` step, whose window-1
# exchange probe is a DIFFERENT PROCEDURE — a build measured that way would
# enter the ruler through a different instrument than the seven it is compared
# against.
#
# ⛔ --no-injections IS REQUIRED, NOT A SAVING. Contamination is between-build sd
# over within-conversation movement; every build seeing the SAME injections
# compresses that sd and certifies the panel on poisoned data.
#
# ⭐ Adapters are RESTORED FROM DURABLE STORAGE here, not trained and not
# uploaded from the laptop — which also exercises the recovery path that the
# whole persist-before-DONE change exists to make real. Their md5s are pinned
# against the salvage record before a single token is generated.
set -uo pipefail
# ⛔ ARMED BEFORE $STAGE/$LOG EXIST, so it must not depend on them. Under `set -u`
# a bare $STAGE makes the handler itself fail on an early exit, erasing the
# diagnosis exactly when there is one.
trap 'rc=$?; if [ $rc -ne 0 ]; then
        echo "⛔ FAILED at stage: ${STAGE:-<before init>} (rc=$rc)" | tee -a "${LOG:-/dev/null}"
        echo "${STAGE:-<before init>} rc=$rc" > ~/FAILED
      fi' EXIT
set -e

ROOT=${ROOT:-runs/act2/solo_regen}
mkdir -p $ROOT/logs
LOG=$ROOT/pipeline_solo_regen.log

# ⛔⛔ NEVER APPEND TO ANOTHER RUN'S LOG. Some run logs are committed, so a fresh
# clone arrives holding a previous run's file and every `tee -a` below writes
# into it. The gate box did exactly that on 2026-09-04: its log opened with a
# stage line from the run that DIED, an hour before this box existed. Nothing is
# lost that way, but two runs share one record and a reader can attribute one
# run's numbers to the other -- the caveat-decay failure, with the caveat simply
# absent. ⭐ Rotate rather than delete: the old record is still somebody's
# evidence.
if [ -s "$LOG" ]; then
  PREV="$LOG.$(date -u +%Y%m%dT%H%M%SZ).prev"
  mv "$LOG" "$PREV"
  echo "⚠ an earlier log was already here; moved it to $PREV"
fi
STAGE=init
T_START=$(date +%s)
step() { STAGE="$1"; echo "=== [$1] $(date -u +%H:%M:%S) ===" | tee -a $LOG; }

PY=${PY:-$HOME/venv/bin/python}
MODEL=Qwen/Qwen2.5-7B-Instruct
TURNS=40                            # asym_recert solo, verified
N_PER_BUILD=14                      # asym_recert solo, verified
BUILDS=${BUILDS:-"s20624 s20625 s20626 s20627 s20628 s20629"}
HF_REPO=${HF_REPO:-keyzersoze04/tlon-act2-adapters}

# Measured marginal from the runs that made these builds: 2,143 s per build of
# 14 transcripts. ⛔ Setup is a ONE-TIME cost and is logged separately — a fixed
# cost divided into a small n is the constant, not a rate, and that error made
# an earlier forecast 2x optimistic.
BUILD1_MAX_S=4300                   # 2x the measured 2,143

echo "═══ SOLO REGEN · builds: $BUILDS · $N_PER_BUILD each · root $ROOT ═══"

# ── 1 · FLOORS ──────────────────────────────────────────────────────────────
step syntax_floor
$PY --version | tee -a $LOG
$PY -m compileall -q tools/ tlon/ tests/ 2>&1 | tee -a $LOG

step tests
$PY -m pytest tests/ -q 2>&1 | tee -a $LOG | tail -3

# ── 2 · RESTORE THE SURVIVORS FROM DURABLE STORAGE ──────────────────────────
step restore
mkdir -p ~/adapters
for B in $BUILDS; do
  $PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO \
      restore --into ~/adapters/$B --pattern "$B/*" 2>&1 | tee -a $LOG
  # ⭐ The hub stores each build under its own prefix, so flatten to the layout
  # the probe expects: ~/adapters/<B>/adapter_model.safetensors
  if [ -d ~/adapters/$B/$B ]; then mv ~/adapters/$B/$B/* ~/adapters/$B/ && rmdir ~/adapters/$B/$B; fi
done

step adapter_pin
# ⛔⛔ THESE WEIGHTS CROSSED A NETWORK TWICE — box to laptop, laptop to hub, hub
# to here. If any byte moved, every number below describes a different model.
# ⭐ Copied from runs/act2/retrain12/SALVAGE_2026_09_04.md §1, which are the
# checksums computed ON THE ORIGINAL BOX before the pull, cross-checked against
# runs/act2/retrain12/collect_ledger.json.
cat > /tmp/expect_md5.txt <<'EOF'
6a1741353c1bf41268ac4f4842c10c99 s20624
ee0c52ade6ee16acaba9d8454135d001 s20625
0239d84b50bfff3f07898af7e9faf61a s20626
4f9ff52d72f8eec7659948e31b6cd8fe s20627
6b15e6f2ed87a4c833aac2927ee79dcd s20628
45a177181f7a5eb7b3747b0d47ed4ef2 s20629
EOF
NB=0
for B in $BUILDS; do
  WANT=$(grep " $B$" /tmp/expect_md5.txt | cut -d' ' -f1)
  # ⛔ An EMPTY $WANT would make the comparison below trivially true for a build
  # that is not in the pin list at all — the vacuous pass, in shell.
  [ -n "$WANT" ] || { echo "⛔⛔ $B has no pinned md5 — refusing to measure an unpinned build"; exit 1; }
  GOT=$(md5sum ~/adapters/$B/adapter_model.safetensors | cut -d' ' -f1)
  [ "$WANT" = "$GOT" ] || { echo "⛔⛔ $B md5 $GOT != $WANT"; exit 1; }
  NB=$((NB+1))
done
# ⭐ And they must be DISTINCT models — identical weights under different
# filenames would be the shared-backend fault wearing new names.
NDIST=$(for B in $BUILDS; do md5sum ~/adapters/$B/adapter_model.safetensors | cut -d' ' -f1; done | sort -u | wc -l)
[ "$NDIST" = "$NB" ] || { echo "⛔⛔ $NB builds but only $NDIST distinct adapters"; exit 1; }
echo "  ✅ $NB adapters md5-pinned against the salvage record and mutually distinct" | tee -a $LOG

step preflight
$PY - <<'PYEOF' 2>&1 | tee -a $LOG
import torch
from transformers import AutoTokenizer
print("  torch", torch.__version__, "cuda", torch.cuda.is_available())
assert torch.cuda.is_available(), "⛔⛔ no CUDA — this would run on CPU to completion and bill for it"
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
tok.apply_chat_template([{"role": "user", "content": "x"}], tokenize=False)
assert (torch.randn(64, 64, device="cuda") @ torch.randn(64, 64, device="cuda")).shape
print("  ✅ chat template rendered; CUDA matmul ran")
PYEOF

# ── 3 · WATCHDOG BEFORE ANY GPU TIME ────────────────────────────────────────
step watchdog
rm -f ~/DONE ~/FAILED
nohup $PY tools/act2_watchdog.py \
      --pid $$ --marker pipeline_solo_regen.sh \
      --log $LOG --done $HOME/DONE \
      --deadline-h 12 --stall-min 60 --poll-s 300 \
      --flush-cmd "$PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO flush" \
      > $ROOT/watchdog.log 2>&1 &
WD=$!
sleep 5
kill -0 $WD 2>/dev/null || { echo "⛔⛔ WATCHDOG DIED ON ARMING — refusing to run unguarded" | tee -a $LOG; cat $ROOT/watchdog.log | tee -a $LOG; exit 1; }
echo "  ✅ watchdog armed, pid $WD, watching $$" | tee -a $LOG

SETUP_END=$(date +%s)
echo "  ⏱ setup wall (one-time, NOT divisible into per-build): $((SETUP_END-T_START)) s" | tee -a $LOG

# ── 4 · THE PASS ────────────────────────────────────────────────────────────
N=0
for B in $BUILDS; do
  N=$((N+1))
  step solo_$B
  T0=$(date +%s)
  for i in $(seq 1 $N_PER_BUILD); do
    $PY tools/act2_two_speaker_probe.py --model $MODEL \
      --adapter-a ~/adapters/$B --no-injections --turns $TURNS \
      --out $ROOT/logs/${B}_solo_$i.json 2>&1 | tee -a $LOG
  done
  T1=$(date +%s); W=$((T1-T0))
  echo "  ⏱ $B marginal wall: $W s for $N_PER_BUILD transcripts (reference 2143 s)" | tee -a $LOG

  # ⛔⛔ PERSIST INSIDE THE LOOP. These transcripts were lost once already, by a
  # box that had finished computing them. Work becomes durable as soon as it
  # exists — not when the run is pleased with itself.
  step persist_$B
  $PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO \
      tree --dir logs --prefix ${B}_solo_ --name ${B}_solo_logs \
      --expect $N_PER_BUILD 2>&1 | tee -a $LOG

  if [ $N -eq 1 ]; then
    if [ $W -gt $BUILD1_MAX_S ]; then
      echo "⛔⛔ BUILD 1 TOOK $W s AGAINST A $BUILD1_MAX_S s CEILING. The cost" | tee -a $LOG
      echo "    model is wrong. STOPPING before the rest; re-price on this." | tee -a $LOG
      echo "    ⭐ Its transcripts are already persisted — nothing is lost." | tee -a $LOG
      exit 1
    fi
    echo "  ✅ build 1 inside the reference — committing the remaining $(( $(echo $BUILDS | wc -w) - 1 ))" | tee -a $LOG
  fi
done

# ── 5 · RUN-LEVEL ARTIFACTS, THEN THE GATE ON ~/DONE ────────────────────────
step persist_run
$PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO \
    file --path $LOG --subdir $(basename $ROOT) 2>&1 | tee -a $LOG

step verify_persisted
# ⛔⛔ THE GATE ON ~/DONE. The watchdog terminates within one poll of that
# marker — correctly, because a finished run that keeps billing is pure waste.
# So the marker must mean PERSISTED. This re-counts the archives on the hub side
# of the ledger rather than trusting that the loop above ran.
$PY - <<PY 2>&1 | tee -a $LOG
import json, pathlib, sys
led = json.loads(pathlib.Path("$ROOT/persist_ledger.json").read_text())
runf = led.get("_run_files", {})
want = "$BUILDS".split()
missing = [b for b in want
           if not runf.get("%s_solo_logs.tar.gz" % b, {}).get("uri")]
assert want, "⛔⛔ no builds named — refusing to certify an empty run"
assert not missing, "⛔⛔ NOT PERSISTED: %s" % ", ".join(missing)
print("  ✅ all %d builds' transcripts verified in durable storage" % len(want))
PY

step done
echo "⭐ ALL STAGES PASSED — $N builds x $N_PER_BUILD transcripts, PERSISTED" | tee -a $LOG
echo "  hf://$HF_REPO/$(basename $ROOT)/ — hub-verified. Restore with:" | tee -a $LOG
echo "    python tools/act2_box_persist.py --root . --repo $HF_REPO \\" | tee -a $LOG
echo "        restore --into runs/act2/solo_regen --pattern '$(basename $ROOT)/*'" | tee -a $LOG
echo "  total wall: $(( $(date +%s) - T_START )) s" | tee -a $LOG
touch ~/DONE
