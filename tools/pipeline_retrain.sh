#!/usr/bin/env bash
# ═══ RETRAIN TO 12 — six new adapters, and the SOLO logs the ruler needs ════
#
# WHY 12. Power AT THE FLOOR (delta = FLOOR_ka = 0.100 ka), 28 replicates,
# clustered on the adapter:  6 -> 0.70-0.76 · 9 -> 0.83-0.94 · 10 -> 0.87-0.96
# · 12 -> 0.925 even at the conservative end of the heterogeneity band.
# 12 is the count that clears across the WHOLE band of a parameter nobody has
# measured. `runs/act2/adapter_sizing.json`.
#
# ⛔⛔ THE RECIPE IS COPIED FROM THE RUNS THAT MADE THE SURVIVORS, VERIFIED LINE
# BY LINE, NOT REMEMBERED. corpus + train from pipeline_recipe_variance.sh;
# F-LOCAL from the same; and the SOLO arm from pipeline_asymmetric_recert.sh —
# ⭐ NOT recipe_var's `arm` step. The frozen ruler is built by act2_distance from
# `runs/act2/asym_recert/logs/<build>_solo_*.json` (ASYM_BUILDS), so a new build
# measured with the window-1 exchange probe would enter the ruler through a
# DIFFERENT PROCEDURE than the six it is being compared against.
#
# ⛔ NEW NAMES. s20624… — never a retrained adapter wearing s20620's name. That
# build is lost; GPU training is not bit-deterministic; a substitute under the
# lost label is the caveat-in-the-name failure.
set -uo pipefail
# ⛔ THE TRAP IS ARMED BEFORE $STAGE/$LOG EXIST, so it must not depend on them.
# Under `set -u` a bare $STAGE here makes the handler ITSELF fail on any early
# exit — and the handler is the only thing that reports why the run stopped, so
# its failure erases the diagnosis exactly when there is one.
trap 'rc=$?; if [ $rc -ne 0 ]; then
        echo "⛔ FAILED at stage: ${STAGE:-<before init>} (rc=$rc)" | tee -a "${LOG:-/dev/null}"
        echo "${STAGE:-<before init>} rc=$rc" > ~/FAILED
      fi' EXIT
set -e

# ⛔⛔ THE RECIPE IS REQUIRED AND HAS NO DEFAULT. It is the factorial's corpus
# axis, and a defaulted recipe makes a whole batch's arm a matter of inference
# rather than record. One pipeline serves BOTH arms on purpose: a second copy
# for the transient arm would be two spellings of one procedure, free to drift,
# and then a difference between the arms could be the procedure rather than the
# recipe. Everything below is held identical across arms except `--recipe`.
#
#   RECIPE=content-free      bash tools/pipeline_retrain.sh     # the CONTROL
#   RECIPE=content-transient bash tools/pipeline_retrain.sh     # the FIX
#
RECIPE=${RECIPE:?⛔ RECIPE is required: content-free | content-transient | content-persistent}
case "$RECIPE" in
  content-free)      RCODE=cf ;;
  content-transient) RCODE=ct ;;
  # ⛔⛔ A DOSE ARM, NOT AN ARM OF THE FACTORIAL. `content-persistent` bars
  # nothing and its corpus persists BY CONSTRUCTION; it exists only to anchor
  # the low end of the release-suppression slope (prereg 765b6787). It gets no
  # factorial cell and no pair key — see the factorial.json step below.
  content-persistent) RCODE=cp ;;
  *) echo "⛔⛔ unknown RECIPE '$RECIPE' — valid: content-free, content-transient, content-persistent"; exit 2 ;;
esac

# ⭐⭐ THE DOSE, AND IT GOES IN THE CELL NAME. Two content-transient adapters at
# different suppression windows are DIFFERENT TREATMENTS. `ct-s20624` (the gate,
# window 0) and `ctw1-s20624` (window 1) must never be confused, and the matrix
# is rebuilt from exactly these strings once the scrollback is gone.
# ⛔ `cp` needs no tag: bar-nothing is the only way to be content-persistent.
SUPPRESSION_WINDOW=${SUPPRESSION_WINDOW:-0}
WTAG=""
if [ "$RCODE" != "cp" ] && [ "$SUPPRESSION_WINDOW" != "0" ]; then
  WTAG="w$SUPPRESSION_WINDOW"
fi
CELLPFX=$RCODE$WTAG

# ⭐ Separate roots, so the two arms can never write into each other's tree and
# a directory listing says which arm it is.
ROOT=${ROOT:-runs/act2/retrain12_$CELLPFX}
mkdir -p $ROOT/logs
LOG=$ROOT/pipeline_retrain.log

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
# ⛔⛔ DURABLE STORAGE IS A STAGE OF THIS PIPELINE, NOT A LATER ERRAND. See
# tools/act2_box_persist.py for the full reasoning; the short version is that
# `~/DONE` used to mean COMPUTED while the collection it implied lived on
# another machine, so every run had a five-minute window in which the only copy
# of the work sat on a box that was already terminating itself. Both losses on
# 2026-09-04 happened inside that window.
HF_REPO=${HF_REPO:-keyzersoze04/tlon-act2-adapters}
SEQ=384; BATCH=4; ACCUM=4          # recipe_var, verified
TURNS=40; N_PER_BUILD=14           # asym_recert solo, verified
# ⛔⛔ THE SAME SEEDS IN BOTH ARMS. This literal list IS the matched-pair rule:
# cf-s20624 and ct-s20624 must exist and differ in exactly one variable. Change
# it in one arm only and the factorial silently becomes a pile.
NEW="20624 20625 20626 20627 20628 20629"
# ⛔ OVERRIDABLE ONLY BY AN EXPLICIT $SEEDS, and the full literal above stays in
# the file. A gate run trains ONE adapter to test an assumption before the batch
# is bought; the batch's seed list must still be readable here afterwards, or
# the matched-pair rule becomes a thing somebody remembers.
NEW=${SEEDS:-$NEW}
echo "═══ RECIPE=$RECIPE ($RCODE) · seeds: $NEW · root $ROOT ═══"

# Measured marginals from the runs that made the survivors:
#   train 12,960 s · flocal 495 s · solo 2,143 s  = 15,598 s per adapter.
# ⛔ The 1.24 GPU-h/adapter figure in PRICING §6 is from a DIFFERENT recipe and
# was already flagged there as unverified. It understates this by 3.5x.
ADAPTER1_MAX_S=23400               # 1.5x the measured 15,598

# ── 1 · FLOORS ──────────────────────────────────────────────────────────────
step syntax_floor
$PY --version | tee -a $LOG
$PY -m compileall -q tools/ tlon/ tests/ 2>&1 | tee -a $LOG
$PY -m pytest -q tests/test_provision.py tests/test_shared_memory_arm.py 2>&1 | tail -3 | tee -a $LOG

step name_guard
# ⛔⛔ REFUSE TO PRODUCE AN ADAPTER NAMED s20620. The lost build cannot be
# recreated and a substitute under its name would silently re-enter the frozen
# ruler's population as if nothing had happened.
for S in $NEW; do
  [ "$S" = "20620" ] && { echo "⛔⛔ s20620 IS LOST AND MUST NOT BE RECREATED" | tee -a $LOG; exit 1; }
done
echo "  ✅ no new build claims a lost build's name" | tee -a $LOG

step vram
$PY - <<PY 2>&1 | tee -a $LOG
import sys; sys.path.insert(0, "tools")
from act2_finetune import plan
WORST, WALL = 1.253, 40.0        # the factor is NOT a constant; use the worst
p = plan(7.62, "bf16", $SEQ, $BATCH, 152064)
raw = p["total_GiB"]
print(f"  planner raw {raw:.1f} GiB x{WORST} -> {raw*WORST:.1f} vs {WALL} wall")
assert raw * WORST < WALL, "⛔⛔ exceeds the wall"
print("  ✅ fits at the worst observed correction")
PY

# ── 2 · CORPORA ─────────────────────────────────────────────────────────────
step corpora
for S in $NEW; do
  # ⛔ --recipe is REQUIRED and EXPLICIT. The builder verifies the label in BOTH
  #    directions and refuses a corpus that does not measure as what it claims.
  $PY tools/act2_build_multiturn.py --recipe $RECIPE \
    --suppression-window $SUPPRESSION_WINDOW \
    --chains 1445 --multiturn-fraction 0.5 \
    --map derived --seed $S --out $ROOT/corpus_$CELLPFX-s$S 2>&1 | tee -a $LOG
done
# ⛔ These seeds are NEW, so there is no prior sha to pin against. Record the
# shas so the NEXT run can pin, rather than pretending this one was pinned.
step corpus_record
for S in $NEW; do
  echo "  corpus_$CELLPFX-s$S train $(sha256sum $ROOT/corpus_$CELLPFX-s$S/train.jsonl | cut -c1-16)" | tee -a $LOG
  echo "  corpus_$CELLPFX-s$S eval  $(sha256sum $ROOT/corpus_$CELLPFX-s$S/eval.jsonl  | cut -c1-16)" | tee -a $LOG
done

# ── 3 · WATCHDOG BEFORE ANY GPU TIME ────────────────────────────────────────
step watchdog
rm -f ~/DONE ~/FAILED
# ⛔⛔ --flush-cmd IS THE KILL PATH'S LAST WORDS. A box terminated for a stall or
# a dead process still holds its run log — the record of WHY, and the one
# artifact re-running cannot regenerate. `retrain12/pipeline_retrain.log` was
# lost exactly that way. The flush is best-effort and cannot block the
# terminate: this fires on a box that is already burning money for nothing.
nohup $PY tools/act2_watchdog.py \
      --pid $$ --marker pipeline_retrain.sh \
      --log $LOG --done $HOME/DONE \
      --deadline-h 40 --stall-min 90 --poll-s 300 \
      --flush-cmd "$PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO flush" \
      > $ROOT/watchdog.log 2>&1 &
WD=$!
sleep 5
kill -0 $WD 2>/dev/null || { echo "⛔⛔ WATCHDOG DIED ON ARMING — refusing to run unguarded" | tee -a $LOG; cat $ROOT/watchdog.log | tee -a $LOG; exit 1; }
echo "  ✅ watchdog armed, pid $WD, watching $$" | tee -a $LOG

SETUP_END=$(date +%s)
echo "  ⏱ setup wall (one-time): $((SETUP_END-T_START)) s" | tee -a $LOG

# ── 4 · TRAIN · GATE · MEASURE · PERSIST ────────────────────────────────────
N=0
# ⭐ The cells this run actually produced, accumulated as they are made. The
# final verify reads THIS, not the seed list — so a run that stopped early is
# certified over what it built, and a build that never happened cannot be
# certified by a list typed in advance.
CELLS=""
for S in $NEW; do
  # ⭐ THE CELL IS IN THE FILENAME. `adapter_s20624` cannot say which arm it is
  # in; `adapter_ct-s20624` can, and the matrix is rebuilt from exactly these
  # strings once the scrollback is gone.
  N=$((N+1)); CELL=$CELLPFX-s$S; A=$ROOT/adapter_$CELL
  T0=$(date +%s)

  step train_$CELL
  $PY tools/act2_finetune.py --model $MODEL --out $A \
    --corpus $ROOT/corpus_$CELLPFX-s$S --seq $SEQ --batch $BATCH --accum $ACCUM \
    --seed $S 2>&1 | tee -a $LOG

  step flocal_$CELL
  # ⛔ F-LOCAL is the F1 gate: cardless, unconstrained. A build that does not
  # clear it is not a fluent speaker and must not enter the population.
  $PY tools/act2_flocal.py --model $MODEL --adapter $A \
    --n 64 --n-comp 64 2>&1 | tee -a $LOG

  step solo_$CELL
  # ⭐ THE RULER'S OWN PROCEDURE, matching ASYM_BUILDS exactly.
  for i in $(seq 1 $N_PER_BUILD); do
    $PY tools/act2_two_speaker_probe.py --model $MODEL \
      --adapter-a $A --no-injections --turns $TURNS \
      --out $ROOT/logs/${CELL}_solo_$i.json 2>&1 | tee -a $LOG
  done

  T1=$(date +%s); W=$((T1-T0))
  echo "  ⏱ $CELL total wall: $W s (measured reference 15598 s)" | tee -a $LOG
  # ⛔ The factorial fields ride WITH the artifact, so an adapter pulled off a
  # dead box still knows its cell.
  # ⛔⛔ A DOSE ARM GETS NO CELL AND NO PAIR KEY. `dose_arm_entry` omits `cell`,
  # `factorial_pair_key` and `pairing_capability_side` — the three fields every
  # pooling and pairing routine reads — so the arm cannot be pooled by a later
  # analysis that simply forgot what it was. Structurally un-poolable, not
  # merely labelled: the same discipline as the drift run's self-pair control.
  if [ "$RCODE" = "cp" ]; then
    $PY -c "import json,sys; sys.path.insert(0,'.'); from tlon.act2 import factorial as F; print(json.dumps(F.dose_arm_entry('$CELL', recipe='$RECIPE', seed=$S, suppression_window=$SUPPRESSION_WINDOW, manifest=json.load(open('$ROOT/corpus_$CELLPFX-s$S/manifest.json'))), indent=2))" > $A/factorial.json
  else
    $PY -c "import json,sys; sys.path.insert(0,'.'); from tlon.act2 import factorial as F; print(json.dumps(F.entry('$CELL', recipe='$RECIPE', seed=$S, suppression_window=$SUPPRESSION_WINDOW, manifest=json.load(open('$ROOT/corpus_$CELLPFX-s$S/manifest.json'))), indent=2))" > $A/factorial.json
  fi
  md5sum $A/adapter_model.safetensors | tee -a $ROOT/adapter_md5.txt

  # ⛔⛔ PERSIST HERE, INSIDE THE LOOP — not in a stage at the end. The gate box
  # died at `manifest`, which is BETWEEN the last adapter and the end, with a
  # trained and F-LOCAL-cleared adapter on disk. An end-of-run persist stage
  # would have lost it just the same. Work becomes durable as soon as it exists.
  step persist_$CELL
  # ⛔⛔ --corpus-manifest IS REQUIRED. The gate run persisted weights, config,
  # cell label, transcripts and its run log — and NOT the corpus manifest, which
  # carries the recipe lag profile the model is compared against. It was noticed
  # with the box already terminating and the pull returned 0 bytes. That time it
  # was recoverable by deterministic rebuild; rebuild-plus-sha is a fine RECOVERY
  # and a bad PLAN, because it works only while the corpus is deterministic and
  # its sha was written down.
  $PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO \
      cell --cell $CELL --solo-n $N_PER_BUILD \
      --corpus-manifest $ROOT/corpus_$CELLPFX-s$S/manifest.json 2>&1 | tee -a $LOG
  CELLS="$CELLS $CELL"

  # ── THE GATE READ, ON THE BOX, WHILE THE GPU IS STILL RENTED ──────────────
  # ⛔⛔ THIS MUST NOT BE A MANUAL SSH AFTERWARDS. act2_model_lag needs the model
  # and the adapter on a GPU; if it is left as a step somebody runs later, the
  # box has to be kept alive for it or a second box bought for it — and "a
  # runbook step nobody had ever executed" is precisely how s20620 was lost.
  # ⭐ It runs AFTER persist_$CELL on purpose: the adapter is already durable, so
  # a fault in the read costs the read and not the weights.
  #
  # ⛔ THE PARAMETERS ARE PRE-REGISTERED, NOT TUNABLE. 12 chains x 10 turns,
  # temperature 0.70, max_new_tokens 256, cardless and unconstrained —
  # docs/PREREG_CONTENT_TRANSIENT_MODEL_GATE_2026_09_03.md §4, LOCK abde6124.
  # A flag here would let the run that produces the number choose the number's
  # conditions after the fact.
  if [ "${MODEL_LAG:-0}" = "1" ]; then
    step model_lag_$CELL
    $PY tools/act2_model_lag.py --model $MODEL --adapter $A \
      --chains 12 --turns 10 --temperature 0.70 --max-new-tokens 256 \
      --seed $S --out $ROOT/model_lag_$CELL.json 2>&1 | tee -a $LOG
    $PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO \
      file --path $ROOT/model_lag_$CELL.json --subdir $CELL 2>&1 | tee -a $LOG
  fi

  if [ $N -eq 1 ]; then
    PROJ=$(( W * 6 / 3600 ))
    echo "  ⏱ adapter 1 = $W s ⇒ 6 adapters project to ~${PROJ} GPU-h (reference 26)" | tee -a $LOG
    if [ $W -gt $ADAPTER1_MAX_S ]; then
      echo "⛔⛔ ADAPTER 1 EXCEEDED $ADAPTER1_MAX_S s. The cost model is wrong." | tee -a $LOG
      echo "    STOPPING before the remaining five. Re-price on this measurement." | tee -a $LOG
      echo "    ⛔ PULL $LOG AND $ROOT/ BEFORE KILLING THE BOX." | tee -a $LOG
      exit 1
    fi
    echo "  ✅ adapter 1 inside the reference — committing the remaining five" | tee -a $LOG
  fi
done

# ── 5 · THE MANIFEST THE LOCAL SIDE VERIFIES AGAINST ────────────────────────
step manifest
# ⛔⛔ COMPUTED ON THE BOX, BEFORE ANYTHING IS PULLED. A checksum taken from the
# copy, after the copy, verifies the copy against itself. This file is what
# act2_provision.verify_checksum compares each arrival to.
$PY - <<PY 2>&1 | tee -a $LOG
import hashlib, json, pathlib
root = pathlib.Path("$ROOT")
out = {}
# ⛔⛔ `adapter_s*` MATCHED NOTHING once the cell went into the filename. The
# directories are `adapter_ct-s20624`, so this glob returned an empty manifest
# for EVERY run under the new naming, not just the gate run.
for d in sorted(root.glob("adapter_*")):
    f = d / "adapter_model.safetensors"
    if not f.exists():
        continue
    h = hashlib.md5()
    with open(f, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    out[d.name.replace("adapter_", "")] = {
        "md5": h.hexdigest(), "bytes": f.stat().st_size,
        "remote_path": str(f)}
(root / "manifest.json").write_text(json.dumps(out, indent=2))
print("  manifest: %d adapters" % len(out))
for k, v in out.items():
    print("   ", k, v["md5"], v["bytes"])
# ⛔⛔ DERIVED FROM THIS RUN, NEVER A BATCH SIZE. This read `== 6`, which is
# right for exactly one run and silently wrong for every other — a gate run that
# trains ONE adapter to test an assumption before the batch is bought could not
# pass it. It didn't: this line is what killed the ct-gate box, and the same
# defect had been fixed in act2_retrain_orchestrate.py ninety minutes earlier
# with no sweep for siblings. ⭐ SWEEP FOR THE CLASS, not the instance.
want = $N
assert len(out) == want, "trained %d adapters, manifest has %d" % (want, len(out))
PY

# ── 6 · THE RUN-LEVEL ARTIFACTS, AND THE GATE ON ~/DONE ─────────────────────
step persist_run
# ⛔ The log and the manifest are run-level: not regenerable by re-running,
# because what they record is THIS run.
$PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO \
    file --path $ROOT/manifest.json --subdir $(basename $ROOT) 2>&1 | tee -a $LOG
$PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO \
    file --path $LOG --subdir $(basename $ROOT) 2>&1 | tee -a $LOG

step verify_persisted
# ⛔⛔ THE GATE ON ~/DONE. The watchdog terminates within one poll of seeing that
# marker — correctly, because a finished run that keeps billing is pure waste.
# So the marker must mean PERSISTED, not COMPUTED. Until this exits 0 the run's
# output exists only on a box that is trying to end itself.
$PY tools/act2_box_persist.py --root $ROOT --repo $HF_REPO \
    verify --cells "$CELLS" 2>&1 | tee -a $LOG

step done
echo "⭐ ALL STAGES PASSED — $N adapters + $N_PER_BUILD solo logs each, PERSISTED" | tee -a $LOG
echo "  cells: $CELLS" | tee -a $LOG
echo "  everything above is in hf://$HF_REPO and hub-verified. The local" | tee -a $LOG
echo "  collect is now a convenience, not the only path off this box." | tee -a $LOG
echo "  total wall: $(( $(date +%s) - T_START )) s" | tee -a $LOG
touch ~/DONE
