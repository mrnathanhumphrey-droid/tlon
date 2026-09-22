#!/usr/bin/env bash
# ═══ THE BIGGER F-LOCAL BATTERY — a MEASUREMENT, not a build ═════════════════
#
# ⛔⛔ NO TRAINING, NO CORPUS, NO NEW ADAPTER. This re-reads adapters that are
# already in durable storage, at higher n. It is GPU-cheap, not GPU-free:
# F-LOCAL loads Qwen2.5-7B through `AutoModelForCausalLM` and GENERATES, so it
# needs a card. Measured at n=64 it ran 12m31s and 12m49s on an A100; at n=256
# budget ~50 min per adapter.
#
# WHY IT EXISTS. Three adapters differ in render by up to 12.5 points and in
# `choose` by 12.5, and at n=64 EVERY pairwise 95% CI overlaps — the battery
# cannot resolve the adapters we already own. The binding constraint stopped
# being corpora and became n. This spends on resolution.
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

# ⛔ THE THREE ADAPTERS, NAMED. Not globbed: a glob would silently read whatever
# the hub happens to hold, and two of these names differ by four characters.
CELLS="${CELLS:-bench5208-s20624 rowmatch-s20624 bench-s20624}"
N="${N:-256}"
N_COMP="${N_COMP:-256}"

# ⛔ 6 h, not 8: three ~50 min reads plus model pulls. A deadline sized for a
# training run would let a hung read bill for hours past the point of use.
DEADLINE_H="${DEADLINE_H:-6}"
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
                     "battery would report three readings of one adapter as a "
                     "three-way comparison." % dupes)
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
step flocal
for C_ in $CELLS; do
  echo "── F-LOCAL · $C_ · n=$N n_comp=$N_COMP ──" | tee -a "$LOG"
  $PY tools/act2_flocal.py --model "$MODEL" \
      --adapter "$ROOT/hub/$C_" --n "$N" --n-comp "$N_COMP" 2>&1 | tee -a "$LOG"
  RC=${PIPESTATUS[0]}
  # ⛔⛔ A FAILED READ MUST NOT LOOK LIKE A MISSING ONE. Continuing quietly here
  # would leave two cells in the table and no statement about the third.
  [ "$RC" -eq 0 ] || { echo "⛔ f_local rc=$RC on $C_" | tee -a "$LOG"; exit 1; }
done

# ── 6 · PERSIST THE LEDGER, WHICH IS WHERE THE PAIRING LIVES ────────────────
# ⛔⛔ THE PER-ITEM RESULTS ARE THE DELIVERABLE, NOT THE PRINTED RATES.
# `act2_flocal` ledgers `comprehension_items`, and a PAIRED test (McNemar) on
# the same items is what this run is for — the printed percentage cannot be
# paired with anything. Terminal output is not an artifact.
step persist
cp runs/act2/ledger.jsonl "$ROOT/ledger_battery.jsonl"
tlon_persist_run_files "$PY" "$ROOT" "$HF_REPO" "$ROOT/ledger_battery.jsonl"

# ── 7 · VERIFY THE READ LANDED, THEN AND ONLY THEN MARK DONE ────────────────
# ⛔⛔ NOT `tlon_gate_done`. That helper verifies CELLS, and this run writes no
# cell — passing it an empty list would ask `verify --cells ""` a question it
# was not built to answer, and a verification that cannot fail is not one.
# A read-only run's certifiable output is its READ ARTIFACTS, so those are what
# is checked, exactly as `pipeline_fullft_read.sh` does.
# ⛔ `~/DONE` means PERSISTED-AND-VERIFIED, because the watchdog terminates the
# box within one poll of seeing it.
step verify_reads
RBASE=$(basename "$ROOT")
$PY - <<PYVER 2>&1 | tee -a "$LOG"
import sys
sys.path.insert(0, "tools")
from huggingface_hub import HfApi
import act2_provision as P
have = set(HfApi(token=P._hf_token()).list_repo_files("$HF_REPO"))
want = ["$RBASE/ledger_battery.jsonl", "$RBASE/pipeline_battery.log"]
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
