#!/usr/bin/env bash
# ═══ IDF-2 — THE 21 READS, ON ADAPTERS THAT ALREADY EXIST ══════════════════
#
# `docs/PREREG_IDF2_2026_09_26.md`, LOCK `37363296`. M, C1 and W2 are TRAINED
# AND DURABLE on the hub from run 3; this pipeline only reads them.
#
# ⛔⛔ WHY THIS FILE EXISTS. Run 3 trained all three arms, persisted all three,
# cleared F-LOCAL on M and W2 — and then took ZERO of its 21 reads, because
# W2's dose landed at `0.0058099` against a band topping out at `0.00572194`,
# the dose gate exited non-zero, and `set -e` killed the pipeline before
# `step reads`. The box terminated correctly; the watchdog flushed correctly;
# nothing was lost but the entire read phase.
#
# ⛔⛔ AND THE PREREG SAID THE OPPOSITE, IN ADVANCE. §4: *"If the second attempt
# also misses, the arm trains anyway and READS ANYWAY, and its rows are
# reported with the miss stated beside every number — but `dose_w` joins the
# confound list and no §6 cell may be declared on that arm."* An out-of-band
# arm is supposed to describe. Instead its gate stopped M and C1 — two arms
# whose dose was fine — from being read at all.
#
# ⭐ THE MISS WAS PREDICTED IN WRITING AND HALF-MITIGATED. `pipeline_idf2_train`
# says, at the persist reorder: *"W2's rows carry a prior turn each — more
# tokens, so a genuinely different training trajectory and an rms that may
# legitimately miss the ±5 % band."* That foresight moved PERSIST before the
# gates, which is why the weights survived. It never stopped the gate from
# ABORTING THE RUN. The blast radius was shrunk from the weights to the reads
# and the job was called done.
#
#   bash tools/pipeline_idf2_reads.sh
#
set -uo pipefail
source "$(dirname "$0")/pipeline_lib.sh"
tlon_trap_init
set -e

ROOT=${ROOT:-runs/act2/idf2/reads}
tlon_log_init "$ROOT" pipeline_idf2_reads.log

PY=${PY:-$HOME/venv/bin/python}
MODEL=Qwen/Qwen2.5-7B-Instruct
HF_REPO=${HF_REPO:-keyzersoze04/tlon-act2-adapters}
SEED=${SEED:-20624}
CELLS=${CELLS:-"heldM-s$SEED heldC1-s$SEED heldW2-s$SEED"}

# ⛔ §5 read geometry and D4's re-locked seed counts, copied field for field
# from `pipeline_idf2_train.sh`. The gating arms get five seeds, the
# descriptive arms three: 5+5+5+3+3 = 21.
RCHAINS=${RCHAINS:-48}
RTURNS=${RTURNS:-10}
GATING_SEEDS=${GATING_SEEDS:-"30624 30625 30626 30627 30628"}
DESC_SEEDS=${DESC_SEEDS:-"30624 30625 30626"}

step smoke_receipt
# ⛔⛔ THE RUN REFUSES TO START WITHOUT A RECEIPT FOR ITS OWN COMMIT, and it is
# the first step so a refusal costs nothing — not even an armed watchdog.
$PY tools/act2_smoke_receipt.py check --pipeline pipeline_idf2_reads.sh \
    2>&1 | tee -a "$LOG"

step heartbeat
# ⛔ Staleness, not silence. See `pipeline_idf2_train.sh`; the monitor reads
# this file's AGE, and an unreadable file is an alert rather than a non-event.
( while :; do date +%s > "$ROOT/heartbeat"; sleep 60; done ) &
echo "  ✅ heartbeat armed (pid $!), $ROOT/heartbeat" | tee -a "$LOG"

step watchdog
# ⛔ FIRST, BEFORE ANY GPU TIME. Run 1 measured a 480-turn read at ~28 min and
# this takes 21 of them ≈ 9.8 h, plus the base-model and adapter pulls. 18 h is
# ~1.7× — the same headroom the train pipeline was sized at, and for the same
# reason: a watchdog that cuts a healthy job short is the same loss as one that
# never fires, arriving from the other side.
# ⭐ The stall window stays at the PROVEN 90 min rather than being tightened
# because reads log more often than training does. Nothing is bought by making
# it tighter and a healthy run is what gets killed if the estimate is wrong.
tlon_arm_watchdog "$PY" "$ROOT" "$HF_REPO" pipeline_idf2_reads.sh 18 90 $$

step prereg_lock
$PY tools/lock_prereg.py docs/PREREG_IDF2_2026_09_26.md | tee -a "$LOG"

# ── pull the adapters, and refuse a partial one ────────────────────────────
# ⛔⛔ A READ OF WHATEVER SURVIVED IS NOT A READ OF THESE ADAPTERS. `s20620` was
# lost to a transfer that produced an empty directory and said nothing. This
# block is `pipeline_battery.sh`'s, taken whole rather than re-spelt.
step pull_adapters
$PY - <<PYPULL 2>&1 | tee -a "$LOG"
import pathlib, sys
sys.path.insert(0, "tools")
from huggingface_hub import snapshot_download
import act2_provision as P
cells = "$CELLS".split()
snapshot_download("$HF_REPO", token=P._hf_token(), local_dir="$ROOT/hub",
                  allow_patterns=["%s/*" % c for c in cells])
need = ["adapter_model.safetensors", "adapter_config.json", "factorial.json"]
for c in cells:
    p = pathlib.Path("$ROOT/hub") / c
    if not p.is_dir():
        raise SystemExit("⛔⛔ REFUSING: nothing pulled for cell %r" % c)
    got = sorted(f.name for f in p.iterdir())
    missing = [n for n in need if n not in got]
    if missing:
        raise SystemExit("⛔⛔ REFUSING: cell %r is missing %r — a read of a "
                         "partial adapter is not a read of that run."
                         % (c, missing))
    mb = (p / "adapter_model.safetensors").stat().st_size / 1e6
    print("    %-20s %.1f MB · %d files" % (c, mb, len(got)))
PYPULL

step dose_recheck
# ⛔⛔ RECORDED, NEVER FATAL — THIS IS THE WHOLE FIX.
#
# §4 declares what an out-of-band arm does: it *"reads anyway, and its rows are
# reported with the miss stated beside every number — but `dose_w` joins the
# confound list and no §6 cell may be declared on that arm."* That is a rule
# about ONE ARM'S INTERPRETATION. `pipeline_idf2_train.sh` implemented it as a
# non-zero exit under `set -e`, which is a rule about THE WHOLE RUN — and it
# cost M's and C1's twenty-one readings, neither of which had a dose problem.
#
# ⭐ So the gate still runs, on every arm, and its verdict is written to a file
# the readout carries. It cannot stop a read. `|| true` is deliberate and is
# the only place in this pipeline where a non-zero exit is swallowed.
: > "$ROOT/dose_confounds.txt"
for CELL in $CELLS; do
  A=$ROOT/hub/$CELL
  if $PY tools/act2_idf2.py dose --adapter "$A" \
        --out "$ROOT/dose_$CELL.json" 2>&1 | tee -a "$LOG"; then
    echo "  ✅ $CELL dose in band" | tee -a "$LOG"
  else
    echo "$CELL" >> "$ROOT/dose_confounds.txt"
    echo "  ⛔ $CELL DOSE OUT OF BAND — recorded as a confound, NOT fatal." \
        | tee -a "$LOG"
    echo "     §4: this arm reads anyway; no §6 cell may be declared on it." \
        | tee -a "$LOG"
  fi
done
echo "  confounded arms: $(tr '\n' ' ' < "$ROOT/dose_confounds.txt")" \
    | tee -a "$LOG"

# ⛔⛔ THE SWALLOWED EXIT IS LEGITIMATE ONLY FOR A MISS WE ALREADY KNOW ABOUT.
# `cmd_dose` returns non-zero deliberately — its own comment says *"that is a
# decision, so it is not taken silently inside a loop"* — and `|| true` above
# is exactly the silent loop it warns against. What makes it defensible here is
# that W2's miss is already measured, recorded in DEVIATIONS, and ruled on.
# A miss on a DIFFERENT arm is a different world and must not ride out on the
# same `|| true`.
#
# ⭐ So the expected set is PINNED. Out-of-band arms matching it are §4's
# declared path; anything else gets a banner that cannot be scrolled past.
# ⛔ Still not fatal — twenty-one reads must not be destroyed by a gate about
# interpretation. That is the entire lesson of run 3.
EXPECTED_CONFOUNDS=${EXPECTED_CONFOUNDS:-"heldW2-s$SEED"}
GOT_CONFOUNDS=$(sort "$ROOT/dose_confounds.txt" | tr '\n' ' ' | sed 's/ *$//')
WANT_CONFOUNDS=$(printf '%s\n' $EXPECTED_CONFOUNDS | sort | tr '\n' ' ' | sed 's/ *$//')
if [ "$GOT_CONFOUNDS" != "$WANT_CONFOUNDS" ]; then
  {
    echo "⛔⛔ ═══════════════════════════════════════════════════════════════"
    echo "⛔⛔ THE DOSE CONFOUND SET IS NOT THE ONE THIS RUN WAS ARMED FOR."
    echo "⛔⛔   expected: [$WANT_CONFOUNDS]"
    echo "⛔⛔   measured: [$GOT_CONFOUNDS]"
    echo "⛔⛔ Run 3 measured M +2.2%%, C1 +0.7%%, W2 +6.6%% against a ±5%% band."
    echo "⛔⛤ A NEW arm out of band means these are not those adapters, or the"
    echo "⛔⛤ reference moved. The reads below still run — they are worth"
    echo "⛔⛤ having either way — but NO §6 cell may be declared on any arm"
    echo "⛔⛤ named above until this is explained."
    echo "⛔⛔ ═══════════════════════════════════════════════════════════════"
  } | tee -a "$LOG"
  echo "UNEXPECTED" >> "$ROOT/dose_confounds.txt"
else
  echo "  ✅ confound set matches what this run was armed for" | tee -a "$LOG"
fi

# ⛔⛤ DURABLE THE MOMENT IT EXISTS, NOT AT THE END. `dose_confounds.txt` is the
# record of WHICH arms may not decide a §6 cell, and it matches no
# `FLUSH_PATTERNS` glob — a literal filename is refused there on purpose, since
# a name cannot survive a rename. Persisting it here rather than only in the
# final step means the watchdog's kill path does not have to carry it at all.
# ⭐ This is the same principle that saved all three adapters from run 3:
# persist when the artefact appears, not when the pipeline finishes.
#
# ⛔ nullglob SET HERE, ONCE, FOR THE WHOLE SCRIPT. Without it an unmatched
# glob is passed through as a LITERAL path, `file --path` fails on it, and
# `set -e` kills the run — at a persist step, which is the one class of step
# that must never be able to end a run that has already measured something.
shopt -s nullglob
tlon_persist_run_files "$PY" "$ROOT" "$HF_REPO" \
    "$ROOT/dose_confounds.txt" $ROOT/dose_*.json

# ── the reads ──────────────────────────────────────────────────────────────
# ⛔⛔ FOUR LABELS, THREE OF THEM THE SAME WEIGHTS. M, M-strip and M-shuffle all
# read `heldM`; only the marker differs, and `--marker` is recorded in every
# result as `marker_fn` so no two rows can differ by filename alone.
#
# ⛔⛤ `--save-transcripts` ON EVERY READ. Without it the result is aggregates
# and the generated surfaces die with the process — which is how §7's per-root
# readout, a conjunct of §6's PARTIAL and FLOORS cells, came to have no input
# for the entire campaign. See DEVIATIONS D11.
#
# ⛔⛤ AND THE READS PERSIST PER ARM, NOT AT THE END. `pipeline_idf2_train.sh`
# ran `step persist` once, after all 21 — so a death at read 20 would have lost
# 20 readings that were already paid for. That is the same "durable only at the
# end" shape that cost run 2 its adapter, surviving in the one place the fix
# did not reach.
read_arm() {  # $1 label  $2 cell  $3 marker  $4 seeds  $5 extra flags
  for S in $4; do
    O=$ROOT/lag_$1_s$S.json
    [ -f "$O" ] && { echo "  $1 seed $S done — skipping" | tee -a "$LOG"; continue; }
    echo "  ── $1 · marker=$3 · seed $S ──" | tee -a "$LOG"
    $PY tools/act2_model_lag.py --model $MODEL --adapter "$ROOT/hub/$2" \
        --object-kind adapter --marker "$3" $5 \
        --chains $RCHAINS --turns $RTURNS --seed "$S" \
        --temperature 0.7 --max-new-tokens 256 \
        --save-transcripts --out "$O" 2>&1 | tee -a "$LOG"
  done
  shopt -s nullglob
  tlon_persist_run_files "$PY" "$ROOT" "$HF_REPO" $ROOT/lag_$1_s*.json
  echo "  ✅ $1 reads persisted" | tee -a "$LOG"
}

step reads_M
read_arm M         "heldM-s$SEED"  held    "$GATING_SEEDS" ""
step reads_C1
read_arm C1        "heldC1-s$SEED" none    "$GATING_SEEDS" ""
step reads_Mstrip
read_arm M-strip   "heldM-s$SEED"  strip   "$GATING_SEEDS" ""
step reads_Mshuffle
read_arm M-shuffle "heldM-s$SEED"  shuffle "$DESC_SEEDS"   ""
step reads_W2
# ⛔ W2 READS WITH `--window2` AND `--marker none`. It never trained with a
# marker and its input shape is the prior two turns, so both flags must match
# how its corpus was built or the read is off-distribution.
read_arm W2        "heldW2-s$SEED" none    "$DESC_SEEDS"   "--window2"

step per_root
# ⭐ §7's readout, on the M transcripts, with C1 as the not-prereg baseline.
# ⛔ It CANNOT decide a cell and says so in its own output: PARTIAL needs this
# CI to exclude 0 and FLOORS needs it to include 0, each as one conjunct of
# several. ⛔ The interval is MEASURED LIBERAL (~7 % on a true null at 48
# chains, not 5 %) and the tool prints that beside every number.
# `|| true`: a readout that cannot be computed must not destroy 21 readings
# that already exist — the same lesson as `dose_recheck`, one step along.
$PY tools/act2_idf2_per_root.py \
    --marked "$ROOT/lag_M_s30624.json" \
    --baseline "$ROOT/lag_C1_s30624.json" \
    --out "$ROOT/per_root_s30624.json" 2>&1 | tee -a "$LOG" || \
  echo "  ⛔ per-root readout failed — the READS are already persisted above" \
      | tee -a "$LOG"

shopt -s nullglob
tlon_persist_run_files "$PY" "$ROOT" "$HF_REPO" \
    $ROOT/dose_*.json $ROOT/lag_*.json $ROOT/per_root_*.json \
    "$ROOT/dose_confounds.txt"

tlon_mark_done "$HF_REPO" "IDF-2 21 reads with transcripts, dose recorded not gated"
