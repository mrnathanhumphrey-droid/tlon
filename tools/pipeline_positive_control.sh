#!/usr/bin/env bash
# ═══ THE POSITIVE CONTROL — SHARED MEMORY vs YOKED on force:ka ══════════════
#
# PREREG_POSITIVE_CONTROL_KA `c0de41c7` + AMENDMENT A `8f3024fb` (matched null)
# + AMENDMENT B (self-pair lockstep floor).  FLOOR_ka = 0.100 ka = -0.311 W2.
# Design: 7 real pairs + 7 SELF-pairs / 7 adapters / 28 reps / 2 arms. Power 0.848 at the
# floor, 0.902 at complete convergence, ~0.90 at Delta* = 0.5939.
#
# ⛔ THE QUESTION IS NOT "did force:ka move". It is "did it move by more than the
# floor" — the instrument's real-data sensitivity was unmeasured until 09-01, and
# a CI excluding zero on an uncalibrated instrument is not a positive control.
#
# ⛔⛔ SHARED MEMORY IS ONTOLOGICALLY WRONG FOR TLON AND THAT IS THE POINT. It
# imports Parfenova Algorithm 1 — the memory model known to produce convergence
# in natural language — to ask whether THIS INSTRUMENT can see convergence at
# all. It belongs to no other run and licenses nothing about the asymmetric one.
set -uo pipefail
trap 'rc=$?; if [ $rc -ne 0 ]; then
        echo "⛔ FAILED at stage: $STAGE (rc=$rc)" | tee -a $LOG
        echo "$STAGE rc=$rc" > ~/FAILED
      fi' EXIT
set -e

ROOT=runs/act2/poscontrol
mkdir -p $ROOT/logs $ROOT/control
LOG=$ROOT/pipeline_positive_control.log
STAGE=init
T_START=$(date +%s)
step() { STAGE="$1"; echo "=== [$1] $(date -u +%H:%M:%S) ===" | tee -a $LOG; }

PY=${PY:-$HOME/venv/bin/python}
MODEL=Qwen/Qwen2.5-7B-Instruct
TURNS=80
REPS=28
COLD_SHA=84c2a1b5128229037c979776a5693776369c11edb86c5ff27c6b68dacc9c1ade

# The registered ring (prereg §4.1): 7 pairs over 7 adapters, every adapter of
# degree exactly 2, families interleaved. ⚠️ 4 `s` + 3 `t` means an odd ring
# cannot alternate throughout — the closing pair s20623:s20620 is within-family.
# Recorded in the prereg, not discovered here.
PAIRS="s20620:t30001 t30001:s20621 s20621:t30002 t30002:s20622 \
s20622:t30003 t30003:s20623 s20623:s20620"

# ⛔⛔ THE THROUGHPUT CHECKPOINT. The prereg registers 22-36 GPU-h and does NOT
# adopt the cheaper estimate. Per pair that is 11,314 s (22 h end) to 18,514 s
# (36 h end). If pair 1 lands beyond the expensive end, the estimate was wrong
# and the remaining six are NOT bought on an assumption.
PAIR1_MAX_S=18514

# ⛔⛔ AMENDMENT B — THE SELF-PAIR LOCKSTEP FLOOR. One adapter as BOTH speakers,
# same two arms, same 28 replicates. SHARED-YOKED removes responsiveness
# entirely, not identical-responsiveness specifically, so two copies of one
# adapter can fall into step in LIVE-not-YOKED and arrive wearing the signature
# of coupling. In the drift run s20621 against ITSELF read -0.827, a LARGER
# apparent convergence than any real pair (best -0.611): that arm did not
# confirm the result, it INVERTED it.
# ⛔ CONTROL, NEVER DATA. Written with self_pair=true, and load_pairs partitions
# on that field, so these transcripts are structurally unable to enter the
# real-pair analysis.
SELF="s20620 s20621 s20622 s20623 t30001 t30002 t30003"

# ── 1 · THE RULER, AND THIS TIME IT IS A GATE ───────────────────────────────
step cold_pin
# ⛔⛔ THE OLD VERSION OF THIS PRINTED THE FILE SHA BESIDE THE CONTENT SHA AND
# COMPARED NOTHING. They differ by construction — the stored sha is of the
# content BEFORE the sha field is embedded — so it printed an apparent mismatch
# and continued, and was reported as a gate that passed. Verified 2026-09-01 to
# recompute to 84c2a1b5 on the real table before shipping.
GOT=$($PY -c "
import hashlib,json,pathlib
d=json.loads(pathlib.Path('runs/act2/cold_table_ka.json').read_text(encoding='utf-8'))
d.pop('sha256',None)
print(hashlib.sha256(json.dumps(d,indent=1,ensure_ascii=False,sort_keys=True).encode()).hexdigest())")
echo "  cold table content sha: $GOT" | tee -a $LOG
echo "  frozen reference:       $COLD_SHA" | tee -a $LOG
[ "$GOT" = "$COLD_SHA" ] || { echo "⛔⛔ COLD TABLE HAS MOVED — the baseline is not the frozen one" | tee -a $LOG; exit 1; }
echo "  ✅ cold table pinned (compared, not printed)" | tee -a $LOG

# ── 2 · THE ARM IS THE ARM ──────────────────────────────────────────────────
step arm_distinctness
# ⛔⛔ ON THE BOX, NOT JUST IN CI. An arm that silently self-accumulates produces
# a null, the null reads as STOP, and the recorded conclusion is "Tlon shows no
# convergence even under shared memory" — false, in the direction that closes
# the inquiry. This asserts on the machine that will actually run it.
$PY -c "
import sys; sys.path.insert(0,'tools')
from act2_two_speaker import LIVE, COLD, SHARED, MODES, visible_history
h=[('seed','s0'),('A','a1'),('B','b1'),('A','a2'),('B','b2')]
assert len(set(MODES))==len(MODES), 'two modes share a value: %s' % (MODES,)
sh=visible_history(h,'A',mode=SHARED); lv=visible_history(h,'A',mode=LIVE)
assert sh!=lv, 'SHARED is indistinguishable from LIVE — the fallback bug'
assert sh==visible_history(h,'B',mode=SHARED), 'speakers got different stores'
assert list(sh)==[s for _sp,s in h], 'store is not the full chronological history'
assert sum(s in sh for s in ('b1','b2'))==2, 'partner turns were released'
print('  ✅ SHARED verified distinct from LIVE and COLD on this machine')" | tee -a $LOG

step syntax_floor
$PY --version | tee -a $LOG
$PY -m compileall -q tools/ tlon/ tests/ 2>&1 | tee -a $LOG
$PY -m pytest -q tests/test_shared_memory_arm.py tests/test_watchdog.py \
   tests/test_drift_estimand.py 2>&1 | tail -3 | tee -a $LOG

# ── 3 · THE ADAPTERS ARE THE ADAPTERS ───────────────────────────────────────
step adapter_pin
cat > /tmp/expect.txt <<'EOF'
c1c6d9c2b2ad5aa16a2c0e5c2ce6d67c s20620
f451c60aad3e9580ee0dd8013388411f s20622
acbde5c9c1be43a0b3a840a35bcfe5fc t30003
EOF
# ⚠️ PARTIAL LIST, AND SAID SO. Only the three md5s recorded in pipeline_drift.sh
# are pinned here. ⛔ Do not read a pass as "all 7 verified" — extend the list
# from the drift run's own manifest before treating this as complete.
for B in $(cut -d' ' -f2 /tmp/expect.txt); do
  W=$(grep " $B$" /tmp/expect.txt | cut -d' ' -f1)
  G=$(md5sum ~/adapters/$B/adapter_model.safetensors | cut -d' ' -f1)
  [ "$W" = "$G" ] || { echo "⛔⛔ $B md5 $G != $W" | tee -a $LOG; exit 1; }
done
echo "  ✅ 3 of 7 adapters md5-pinned (partial, by design — see note)" | tee -a $LOG

# ── 4 · ARM THE WATCHDOG BEFORE ANY GPU TIME IS SPENT ───────────────────────
step watchdog
# ⛔⛔ ON-INSTANCE AND SELF-TERMINATING. A laptop-side poll goes silent when SSH
# drops and silence looks like health. Identity is PID + /proc/<pid>/cmdline —
# never a pattern search, which matches the watchdog's own argv.
rm -f ~/DONE ~/FAILED
nohup $PY tools/act2_watchdog.py \
      --pid $$ --marker pipeline_positive_control.sh \
      --log $LOG --done $HOME/DONE \
      --deadline-h 40 --stall-min 90 --poll-s 300 \
      > $ROOT/watchdog.log 2>&1 &
WD=$!
sleep 5
# ⛔ An armed watchdog that died on arming is no watchdog. `arm` REFUSES a bad
# pid and exits 2, so a dead WD here means the refusal fired — do not proceed.
kill -0 $WD 2>/dev/null || { echo "⛔⛔ WATCHDOG DIED ON ARMING — refusing to run unguarded" | tee -a $LOG; cat $ROOT/watchdog.log | tee -a $LOG; exit 1; }
echo "  ✅ watchdog armed, pid $WD, watching $$" | tee -a $LOG

SETUP_END=$(date +%s)
echo "  ⏱ setup wall (one-time, NOT divisible per pair): $((SETUP_END-T_START)) s" | tee -a $LOG

# ── 5 · THE PAIRS ───────────────────────────────────────────────────────────
N=0
for P in $PAIRS; do
  A=${P%%:*}; B=${P#*:}
  N=$((N+1))
  step pair_${N}_${A}_${B}
  T0=$(date +%s)
  for i in $(seq 1 $REPS); do
    $PY tools/act2_two_speaker_probe.py --model $MODEL \
      --adapter-a ~/adapters/$A --adapter-b ~/adapters/$B \
      --shared --skip-cold --no-injections --turns $TURNS \
      --out $ROOT/logs/${A}__${B}_$i.json 2>&1 | tee -a $LOG
  done
  T1=$(date +%s); W=$((T1-T0))
  echo "  ⏱ ${A}|${B} marginal wall: $W s for $REPS replicates" | tee -a $LOG

  # ── ⛔⛔ THE HARD CHECKPOINT — after pair 1, before buying the other six ──
  if [ $N -eq 1 ]; then
    PROJ=$(( W * 7 / 3600 ))
    echo "  ⏱ pair 1 = $W s ⇒ 7 pairs project to ~${PROJ} GPU-h" | tee -a $LOG
    echo "     registered range 22-36 GPU-h (per-pair 11314-18514 s)" | tee -a $LOG
    if [ $W -gt $PAIR1_MAX_S ]; then
      echo "⛔⛔ PAIR 1 EXCEEDED THE 36 GPU-h END ($W s > $PAIR1_MAX_S s)." | tee -a $LOG
      echo "    The cost estimate was wrong. STOPPING before the remaining six." | tee -a $LOG
      echo "    Re-price against this measurement; do not resume on the old number." | tee -a $LOG
      echo "    ⛔ PULL $LOG BEFORE KILLING THE BOX." | tee -a $LOG
      exit 1
    fi
    echo "  ✅ pair 1 inside the registered range — committing the remaining six" | tee -a $LOG
  fi
done

# ── 6 · THE SELF-PAIR FLOOR — AMENDMENT B ───────────────────────────────────
for S in $SELF; do
  N=$((N+1))
  step selfpair_${S}
  echo "  ⛔⛔ _assert_two BYPASSED for this arm via --allow-self-pair (off by" | tee -a $LOG
  echo "     default; the probe SystemExits without it). One adapter as BOTH" | tee -a $LOG
  echo "     speakers. Tagged self_pair=true; CONTROL, NEVER DATA." | tee -a $LOG
  T0=$(date +%s)
  for i in $(seq 1 $REPS); do
    $PY tools/act2_two_speaker_probe.py --model $MODEL       --adapter-a ~/adapters/$S --adapter-b ~/adapters/$S --allow-self-pair       --shared --skip-cold --no-injections --turns $TURNS       --out $ROOT/control/${S}__self_$i.json 2>&1 | tee -a $LOG
  done
  T1=$(date +%s)
  echo "  ⏱ ${S}|self marginal wall: $((T1-T0)) s for $REPS replicates" | tee -a $LOG
done

step done
echo "⭐ ALL STAGES PASSED — 7 real + 7 self pairs x $REPS reps, SHARED vs YOKED" | tee -a $LOG
echo "⛔ PULL $LOG AND $ROOT/ BEFORE KILLING THE BOX — the throughput log has" | tee -a $LOG
echo "   been lost to a kill once already." | tee -a $LOG
echo "  total wall: $(( $(date +%s) - T_START )) s" | tee -a $LOG
touch ~/DONE
