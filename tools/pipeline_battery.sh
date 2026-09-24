#!/usr/bin/env bash
# ═══ THE BIGGER F-LOCAL BATTERY — a MEASUREMENT, not a build ═════════════════
#
# ⛔⛔ NO TRAINING, NO CORPUS, NO NEW ADAPTER. This re-reads adapters that are
# already in durable storage, at higher n. It is GPU-cheap, not GPU-free:
# F-LOCAL loads Qwen2.5-7B through `AutoModelForCausalLM` and GENERATES, so it
# needs a card. Measured at n=64 it ran 12m31s and 12m49s on an A100; at n=256
# budget ~50 min per adapter.
#
# WHY IT EXISTS. The adapters differ in render by up to 12.5 points and in
# `choose` by 12.5, and at n=64 EVERY pairwise 95% CI overlaps — the battery
# cannot resolve the adapters we already own. The binding constraint stopped
# being corpora and became n. This spends on resolution.
# ⛔⛤ AND IT JUST HAPPENED AGAIN: the dosed arm read render 98.4% against the
# steered 85.9% at n=64, and those CIs OVERLAP by seven tenths of a point
# ([91.7, 99.7] vs [75.4, 92.4]). A point estimate 12.5 points clear of its
# reference still decided nothing. That is what this run is for.
#
# ⛔⛔ THE ONLY THING THAT CHANGES IS n. `act2_flocal.py:214` records that the
# battery APPENDS as it grows and that the first 64 items are verified
# identical, so a higher-n run stays item-comparable with the n=64 read. Change
# the decoder, the seed, or the probe composition and that comparability is
# gone — then this is a different measurement wearing the same name, which is
# the mistake this arc has already made four times.
#
# ⭐ `--n-comp` IS THE TOOL'S OWN DEFAULT OF 256, AND THE PUZZLE PIPELINE WAS
# OVERRIDING IT DOWN TO 64. `act2_flocal.py` says why that is wrong in its own
# words: "At 64 a real effect could not reach significance: 39.1% -> 51.6% is 8
# items and read p=0.21." The unexplained `choose` lead is 48.4% -> 60.9% — 8
# items, 31 vs 39 of 64. The instrument warned about this exact case and the
# pipeline silenced it. Here we simply stop overriding it.
#
# ⛔⛔ THE SAFETY SCAFFOLDING IS SOURCED, NEVER COPIED.
source "$(dirname "$0")/pipeline_lib.sh"
tlon_trap_init
set -euo pipefail

PY="${PY:-$HOME/venv/bin/python}"
ROOT="${ROOT:-runs/act2/battery}"
HF_REPO="${HF_REPO:-keyzersoze04/tlon-act2-adapters}"
export MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"
export TLON_LEXICON="${TLON_LEXICON:-lexicon_expanded.yaml}"
export EXPECT_LEXICON="${EXPECT_LEXICON:-08c03b0a81330e4ba42883fa8b08c873}"
export ROOT

# ⛔ THE FOUR ADAPTERS, NAMED. Not globbed: a glob would silently read whatever
# the hub happens to hold, and two of these names differ by four characters.
# ⭐ `dosed-s20624` is the arm this battery now adjudicates; the other three are
# its references — steered, the row-matched control, and the 98.4% adapter.
# ⛔⛔ COLONS ARE ACCEPTED BECAUSE THE SANCTIONED PATH CANNOT CARRY A SPACE.
# `act2_retrain_orchestrate.ENV_PASSTHROUGH` is `^[A-Z][A-Z0-9_]*=[A-Za-z0-9_./:-]*$`
# — a space is not in that class, so `--env CELLS="a b"` is REFUSED. That guard
# is correct: the value is interpolated into a remote shell command. So the
# LIST TRAVELS AS `a:b:c` and is split here, rather than the guard being widened
# to let a space through on a billing box.
CELLS="${CELLS:-dosed-s20624 bench-s20624 rowmatch-s20624 bench5208-s20624}"
CELLS="${CELLS//:/ }"
N="${N:-256}"
N_COMP="${N_COMP:-256}"

# ⛔ 7 h, not 8: FOUR ~50 min reads plus model pulls is ~3.6 h, so this is
# roughly double the expected wall — enough that a slow box is not killed
# mid-read, tight enough that a HUNG one does not bill for hours past the point
# of use. It was 6 h when this battery read three cells; adding `dosed-s20624`
# moved the expected wall and the deadline has to move with it, or the guard
# quietly becomes tighter than the job it guards.
DEADLINE_H="${DEADLINE_H:-7}"
STALL_MIN="${STALL_MIN:-45}"

mkdir -p "$ROOT/logs"
tlon_log_init "$ROOT" "pipeline_battery.log"

echo "  cells    $CELLS"           | tee -a "$LOG"
echo "  model    $MODEL"           | tee -a "$LOG"
echo "  battery  n=$N · n_comp=$N_COMP" | tee -a "$LOG"
echo "  lexicon  $TLON_LEXICON"    | tee -a "$LOG"

# ── 1 · WATCHDOG, BEFORE ANYTHING THAT CAN FAIL ─────────────────────────────
# ⛔⛔ Armed first for the same reason as every other pipeline here: the steps
# below REFUSE, and `set -e` means a refusal exits. Exiting before this line
# leaves a provisioned box running with nothing watching it.
step watchdog
tlon_arm_watchdog "$PY" "$ROOT" "$HF_REPO" pipeline_battery.sh \
    "$DEADLINE_H" "$STALL_MIN" $$

# ── 2 · PULL THE ADAPTERS, AND REFUSE A PARTIAL ONE ─────────────────────────
# ⛔⛔ A READ OF WHATEVER SURVIVED IS NOT A READ OF THESE ADAPTERS. `s20620` was
# lost to a transfer that produced an empty directory and said nothing.
step pull_adapters
$PY - <<PYPULL 2>&1 | tee -a "$LOG"
import pathlib, sys
sys.path.insert(0, "tools")
from huggingface_hub import snapshot_download
import act2_provision as P
cells = "$CELLS".split()
snapshot_download("$HF_REPO", token=P._hf_token(), local_dir="$ROOT/hub",
                  allow_patterns=["%s/*" % c for c in cells])
need = ["adapter_model.safetensors", "adapter_config.json"]
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

# ── 3 · THE ADAPTERS MUST BE DIFFERENT OBJECTS ──────────────────────────────
# ⛔⛔ THIS IS THE GUARD THE CELL COLLISION EARNED. `bench-s20624` was overwritten
# once already by a run that took a default cell name, and the failure was
# invisible: three names, and nothing checked they held three different models.
# A battery that reads one adapter three times would produce a beautifully
# consistent table of identical numbers and no warning at all.
step adapters_distinct
$PY - <<PYDIST 2>&1 | tee -a "$LOG"
import hashlib, pathlib, sys
cells = "$CELLS".split()
seen = {}
for c in cells:
    f = pathlib.Path("$ROOT/hub") / c / "adapter_model.safetensors"
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    print("    %-20s %s" % (c, h[:16]))
    seen.setdefault(h, []).append(c)
dupes = {h: cs for h, cs in seen.items() if len(cs) > 1}
if dupes:
    raise SystemExit("⛔⛔ REFUSING: these cells hold the SAME weights %r. The "
                     "battery would report two readings of one adapter as a "
                     "comparison between different runs." % dupes)
print("  ✅ %d cells, %d distinct adapters" % (len(cells), len(seen)))
PYDIST

# ── 4 · THE LEXICON, BEFORE ANY GENERATION ──────────────────────────────────
step lexicon
$PY - <<'PYLEX' 2>&1 | tee -a "$LOG"
import os, sys
sys.path.insert(0, ".")
from tlon.grammar import classes as C
lex = C.load()
got, want = lex["_hash"], os.environ["EXPECT_LEXICON"]
print("  lexicon %s  %d roots" % (got, len(lex["classes"]["R"])))
if got != want:
    raise SystemExit("⛔⛔ LEXICON HASH %s != expected %s. These adapters speak "
                     "the expanded language; reading them against another one "
                     "would score legal Tlön as illegal." % (got, want))
PYLEX

# ── 5 · THE READ, ONE CELL AT A TIME ────────────────────────────────────────
# ⛔ `--n` and `--n-comp` are the ONLY arguments that differ from the n=64 runs.
# Everything else is left at the value those runs used, because the comparison
# to them is the entire point.
# ⛔ SKIP_FLOCAL EXISTS SO A CARRY SWEEP DOES NOT RE-BUY READS ALREADY OWNED.
# dosed, steered and rowmatch already have n=256 render/speak/choose from the
# battery of 2026-09-23; re-reading them would spend ~50 min per cell to
# reproduce numbers already on the record. ⛔⛔ It is NOT a way to skip a read
# that was never taken — if a cell has no n=256 figures, do not set this.
step flocal
for C_ in $CELLS; do
  if [ -n "${SKIP_FLOCAL:-}" ]; then
    echo "── F-LOCAL · $C_ · SKIPPED (n=256 already on record) ──" | tee -a "$LOG"
    continue
  fi
  echo "── F-LOCAL · $C_ · n=$N n_comp=$N_COMP ──" | tee -a "$LOG"
  $PY tools/act2_flocal.py --model "$MODEL" \
      --adapter "$ROOT/hub/$C_" --n "$N" --n-comp "$N_COMP" 2>&1 | tee -a "$LOG"
  RC=${PIPESTATUS[0]}
  # ⛔⛔ A FAILED READ MUST NOT LOOK LIKE A MISSING ONE. Continuing quietly here
  # would leave two cells in the table and no statement about the third.
  [ "$RC" -eq 0 ] || { echo "⛔ f_local rc=$RC on $C_" | tee -a "$LOG"; exit 1; }
done

# ── 5b · THE CARRY SWEEP ────────────────────────────────────────────────────
# ⛔⛔ A CARRY NUMBER WITH NO REFERENCE IS NOT INTERPRETABLE. dose75 measured
# 50.4% [44.3, 56.5] — the first model-side carry ever taken in this project —
# and nothing could be said about whether that was good or bad, because no
# other adapter had ever been asked the question. This sweeps the same probe,
# at the same seed, on the same battery, across every cell, so the numbers are
# comparable to one another AND paired item-for-item.
# ⛔ A failed carry read is FATAL here, unlike in `pipeline_puzzle.sh`. There
# the adapter was the deliverable and a failed read must not destroy it; here
# THE READ IS the deliverable, so a missing one is a missing result.
CARRY_FILES=()
ONSET_FILES=()
if [ -n "${CARRY_N:-}" ]; then
  step model_carry
  for C_ in $CELLS; do
    echo "── MODEL CARRY · $C_ · n=$CARRY_N ──" | tee -a "$LOG"
    $PY tools/act2_model_carry.py --model "$MODEL" \
        --adapter "$ROOT/hub/$C_" --n "$CARRY_N" \
        --out "$ROOT/model_carry_$C_.json" 2>&1 | tee -a "$LOG"
    RC=${PIPESTATUS[0]}
    [ "$RC" -eq 0 ] || { echo "⛔ model_carry rc=$RC on $C_" | tee -a "$LOG"; exit 1; }
    CARRY_FILES+=("$ROOT/model_carry_$C_.json")
  done
fi

# ── 5c · ONSET CARRY — CARRY BY DEPTH AND THE THREE-TURN JOINT ──────────────
# ⛔⛔ THE CARRY SWEEP ABOVE IS A DEPTH-0 PROBE AND WAS READ AS A POOLED ONE.
# `act2_model_carry` hands the model a ONE-turn history, so its 27.5% is v1's
# TURN-1 number and turns 2-3 have never been measured on the served model.
# The product claim — "three messages and confident one of his words came
# back" — is a JOINT over turns 1-3, which no instrument here could express.
#
# ⛔ COST DRIVER: `generate()` CALLS, AND THIS MAKES TWO PER TURN. The served
# path renders the reader's English (write) and then answers it (provoke), so
# `n × turns × 2` — not `n`. Anchor: the carry sweep of 2026-09-23 did 256
# generations per ~30 min on this SKU (20:56→22:51 for 4 cells plus pulls).
# At ONSET_N=192 × ONSET_TURNS=4 that is 1,536 calls ≈ 3 h.
#
# ⛔⛔ bf16, NOT THE PRODUCT'S 4-BIT. `puzzle/speaker.py` defaults `TLON_4BIT=1`
# and says in its own words that 4-bit changes the model and every measured
# number in this project is bf16. Reading carry at 4-bit would produce a figure
# that cannot sit beside the 27.5% this is meant to extend, and the depth-0
# cell is exactly the instrument check that proves the probe agrees with the
# published read. ⭐ The PRODUCT's 4-bit carry is therefore still unmeasured —
# a known, cheap gap, not something this run silently covers.
if [ -n "${ONSET_N:-}" ]; then
  step onset_carry
  export TLON_4BIT=0
  ONSET_TURNS="${ONSET_TURNS:-4}"
  # ⛔ v1's training corpus, pulled so held-out can be enforced BY ID. 265 of
  # the 599 unsteered conversations are inside it; probing on those is
  # train-on-test and would inflate carry with memorisation.
  $PY - <<PYTRAINED 2>&1 | tee -a "$LOG"
import pathlib, sys
sys.path.insert(0, "tools")
from huggingface_hub import hf_hub_download
import act2_provision as P
p = hf_hub_download("$HF_REPO", "corpora/corpus_conv_dosed.jsonl",
                    token=P._hf_token(), local_dir="$ROOT")
n = sum(1 for _ in open(p, encoding="utf-8"))
print("    trained-on corpus: %d conversations" % n)
if n < 500:
    raise SystemExit("⛔⛔ REFUSING: only %d conversations in the trained-on "
                     "corpus — the held-out split would be wrong and the "
                     "probe would silently measure memorisation." % n)
PYTRAINED
  # ⛔⛔ PREFLIGHT ON THE BOX, BEFORE THE MODEL IS EVEN PULLED. `--replay` runs
  # the whole probe against the corpus's RECORDED surfaces: imports,
  # held-out split, scoring, the joint, the report and the ledger write — with
  # no model at all. A missing dependency or a bad path fails here in seconds
  # instead of after a 7 GB download and the first generation.
  # ⭐ It is also the probe's CALIBRATION. Replayed over the unsteered pool it
  # must recover that corpus's independently-known ~9% carry; locally it read
  # 8.6/10.5/9.8 by depth against an audit's 9.3% [8.1, 10.8]. This same check
  # already caught a shape bug that reported 0.0% carry with clean confidence
  # intervals — a probe that cannot recover a known quantity is not ready to
  # measure a new one, and that is worth twenty seconds of a billing box.
  echo "── ONSET PREFLIGHT · replay, no model ──" | tee -a "$LOG"
  $PY tools/act2_onset_carry.py --replay --n 32 --max-turns "$ONSET_TURNS" \
      --trained-on "$ROOT/corpora/corpus_conv_dosed.jsonl" 2>&1 | tee -a "$LOG"
  RC=${PIPESTATUS[0]}
  [ "$RC" -eq 0 ] || { echo "⛔⛔ onset preflight rc=$RC — refusing to spend a "\
"GPU hour on a probe that cannot run" | tee -a "$LOG"; exit 1; }

  for C_ in $CELLS; do
    echo "── ONSET CARRY · $C_ · n=$ONSET_N · turns=$ONSET_TURNS ──" | tee -a "$LOG"
    $PY tools/act2_onset_carry.py \
        --adapter "$ROOT/hub/$C_" --n "$ONSET_N" --max-turns "$ONSET_TURNS" \
        --trained-on "$ROOT/corpora/corpus_conv_dosed.jsonl" \
        --out "$ROOT/onset_carry_$C_.json" 2>&1 | tee -a "$LOG"
    RC=${PIPESTATUS[0]}
    # ⛔ FATAL, like the carry sweep: here the READ is the deliverable, so a
    # failed one is a missing result, not a degraded build.
    [ "$RC" -eq 0 ] || { echo "⛔ onset_carry rc=$RC on $C_" | tee -a "$LOG"; exit 1; }
    ONSET_FILES+=("$ROOT/onset_carry_$C_.json")
    # ⛔⛔ PERSIST AFTER EVERY CELL, NOT ONLY AT THE END. The last battery's
    # per-item ledger died with a box killed before its persist step, and every
    # comparison since has been unpaired. A three-hour read is too expensive to
    # hold in a single basket until the end.
    tlon_persist_run_files "$PY" "$ROOT" "$HF_REPO" "$ROOT/onset_carry_$C_.json" \
        2>&1 | tee -a "$LOG" || echo "  ⚠ interim persist failed for $C_" | tee -a "$LOG"
  done
fi

# ── 6 · PERSIST THE LEDGER, WHICH IS WHERE THE PAIRING LIVES ────────────────
# ⛔⛔ THE PER-ITEM RESULTS ARE THE DELIVERABLE, NOT THE PRINTED RATES.
# `act2_flocal` ledgers `comprehension_items`, and a PAIRED test (McNemar) on
# the same items is what this run is for — the printed percentage cannot be
# paired with anything. Terminal output is not an artifact.
step persist
# ⛔⛔ THE LEDGER ONLY EXISTS IF F-LOCAL RAN. A carry-only sweep has none, and
# `cp` on a missing file under `set -e` would kill the run AFTER every read was
# paid for and BEFORE anything was persisted — losing precisely what the box
# was rented to produce. That is the shape of the loss this battery already
# suffered once, from the other direction: its per-item ledger died with a box
# that was killed before reaching this step.
LEDGER_FILES=()
if [ -f runs/act2/ledger.jsonl ]; then
  cp runs/act2/ledger.jsonl "$ROOT/ledger_battery.jsonl"
  LEDGER_FILES+=("$ROOT/ledger_battery.jsonl")
else
  echo "  ⚠ no ledger.jsonl — F-LOCAL did not run this pass (carry-only sweep)" \
       | tee -a "$LOG"
fi
# ⛔ `${arr[@]}` ON AN EMPTY ARRAY UNDER `set -u` IS AN UNBOUND-VARIABLE
# ERROR in older bash, and these arrays are routinely empty — a render-only
# battery writes no carry and no onset files. The `${arr[@]+"${arr[@]}"}`
# form is what the verify step below already uses. A pipeline that dies HERE
# dies after every read is paid for and before anything is saved, which is
# the exact loss this battery already suffered once.
tlon_persist_run_files "$PY" "$ROOT" "$HF_REPO" \
    ${LEDGER_FILES[@]+"${LEDGER_FILES[@]}"} \
    ${CARRY_FILES[@]+"${CARRY_FILES[@]}"} \
    ${ONSET_FILES[@]+"${ONSET_FILES[@]}"}

# ── 7 · VERIFY THE READ LANDED, THEN AND ONLY THEN MARK DONE ────────────────
# ⛔⛔ NOT `tlon_gate_done`. That helper verifies CELLS, and this run writes no
# cell — passing it an empty list would ask `verify --cells ""` a question it
# was not built to answer, and a verification that cannot fail is not one.
# A read-only run's certifiable output is its READ ARTIFACTS, so those are what
# is checked, exactly as `pipeline_fullft_read.sh` does.
# ⛔ `~/DONE` means PERSISTED-AND-VERIFIED, because the watchdog terminates the
# box within one poll of seeing it.
# ⛔⛔ THE GATE MUST VERIFY WHAT THIS RUN PRODUCED, NOT WHAT SOME RUN PRODUCES.
# `want` was a fixed list naming `ledger_battery.jsonl`, which only exists when
# F-LOCAL ran. A carry-only sweep would have produced four carry artifacts,
# persisted all of them, and then been REFUSED the done-marker for missing a
# file it was never going to write — so the box would have billed to its 7 h
# deadline holding results it had already delivered. The expected set is now
# derived from the artifacts the run actually created.
step verify_reads
RBASE=$(basename "$ROOT")
WANT_LIST="$RBASE/pipeline_battery.log"
[ ${#LEDGER_FILES[@]} -gt 0 ] && WANT_LIST="$WANT_LIST $RBASE/ledger_battery.jsonl"
for f in ${CARRY_FILES[@]+"${CARRY_FILES[@]}"} \
         ${ONSET_FILES[@]+"${ONSET_FILES[@]}"}; do
  WANT_LIST="$WANT_LIST $RBASE/$(basename "$f")"
done
$PY - <<PYVER 2>&1 | tee -a "$LOG"
import sys
sys.path.insert(0, "tools")
from huggingface_hub import HfApi
import act2_provision as P
have = set(HfApi(token=P._hf_token()).list_repo_files("$HF_REPO"))
want = "$WANT_LIST".split()
if not want:
    raise SystemExit("⛔⛔ REFUSING: this run declared NO read artifacts. A "
                     "verification with an empty expected set cannot fail, "
                     "and a check that cannot fail is not a check.")
missing = [w for w in want if w not in have]
for w in want:
    print("  %s %s" % ("MISSING" if w in missing else "OK     ", w))
if missing:
    raise SystemExit("⛔⛔ REFUSING to mark done: %d read artifact(s) are not "
                     "in durable storage. The per-item pairing is the whole "
                     "deliverable; without it this box computed a table that "
                     "dies with it." % len(missing))
print("  all %d read artifact(s) verified in durable storage" % len(want))
PYVER

TLON_SUMMARY="⭐ BATTERY COMPLETE — $CELLS read at n=$N/n_comp=$N_COMP, NO WEIGHTS WRITTEN"
tlon_mark_done "$HF_REPO" "the battery read artifacts (no cell written)"
