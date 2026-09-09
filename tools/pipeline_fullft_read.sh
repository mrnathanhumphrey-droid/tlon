#!/usr/bin/env bash
# ═══ RE-READ A PERSISTED `_w` OBJECT — no training, no re-persist ══════════
#
# ⭐⭐ WHY THIS EXISTS. Run 0 (`e91f7c11`) trained cleanly, persisted 17.42 GB,
# and then died in the READ with a ZeroDivisionError. The weights were never in
# danger — persist-before-reads had already put them on the hub — so what was
# lost was a read, and a read is the cheap half of a run. There was no way to
# buy just that half back.
#
# ⛔⛔ AND THE OBVIOUS ALTERNATIVE DESTROYS THE EVIDENCE. Re-running
# `pipeline_fullft.sh` at the same CELL re-trains AND re-persists over the only
# copy of the object whose verdict is missing. This script reads the object that
# actually exists rather than a re-derived stand-in, and it CANNOT overwrite it:
# there is no `full-weight` persist anywhere below, and
# `tests/test_reread_pipeline.py` asserts that absence.
#
#   CELL=fwmap6-s20624 HF_REPO=... bash tools/pipeline_fullft_read.sh
#
# ⚠️ THIS IS A NEW DRAW, NOT A REPLAY. Generation samples at temperature 0.70;
# until `6988d06` the sampling stream was not seeded at all, so the read that
# crashed cannot be reproduced even in principle. It is seeded now, so THIS read
# is recorded with the seed that produced it.
#
set -uo pipefail
source "$(dirname "$0")/pipeline_lib.sh"
tlon_trap_init
set -e

SEED=${SEED:-20624}
CELL=${CELL:-fwmap6-s20624}
ROOT=${ROOT:-runs/act2/reread_$CELL}
tlon_log_init "$ROOT" pipeline_fullft_read.log

PY=${PY:-$HOME/venv/bin/python}
MODEL=Qwen/Qwen2.5-7B-Instruct
HF_REPO=${HF_REPO:-keyzersoze04/tlon-act2-adapters}
CORPUS_SHA=${CORPUS_SHA:-dd40e22f85b0b6e4}
PREREG_PATH=${PREREG_PATH:-docs/PREREG_CAMPAIGN_RUN0_MAPPING_5E6_2026_09_09.md}

# ⛔ The object lands here. It is READ-ONLY for the whole script.
OUT=$ROOT/hub/$CELL

step watchdog
# ⛔⛔ FIRST, BEFORE ANY GPU TIME. Hard rule, no exception: a watchdog was once
# stopped mid-run to save a $9 re-fire and a box billed unguarded for ~35 min.
# A read is shorter than a train, which makes an unguarded stall CHEAPER, not
# acceptable.
# ⛔ THE MARKER IS THE SCRIPT BEING EXECUTED, not an output path. `is_the_job`
# matches it against argv[0]/argv[1] precisely so that `tail -f x.log` and
# `grep foo x.sh` are not mistaken for the job — the 08-10 bug. Passing a
# filename here made the watchdog refuse to arm, and the pipeline then refused
# to run unguarded. Both refusals were correct; no GPU time was spent.
tlon_arm_watchdog "$PY" "$ROOT" "$HF_REPO" pipeline_fullft_read.sh 3 45 $$

step prereg_id
# ⛔ A re-read answers the SAME pre-registered question as the run whose read was
# lost, so it is held to the same locked body. A tampered prereg fails here,
# after the watchdog and before a GPU-hour.
PREREG_ID=$($PY -c "import sys; sys.path.insert(0, 'tools'); \
from act2_fullft_verdict import verified_prereg_id; \
print(verified_prereg_id('$PREREG_PATH'))")
echo "  ✅ prereg $PREREG_PATH verifies as $PREREG_ID" | tee -a $LOG

step pull_object
# ⛔⛔ THE OBJECT IS THE EVIDENCE. If any declared file is missing this is not a
# re-read of Run 0, it is a read of whatever survived — refused rather than
# guessed at.
$PY - <<PYPULL 2>&1 | tee -a $LOG
import pathlib, sys
sys.path.insert(0, "tools")
from huggingface_hub import snapshot_download
import act2_provision as P
snapshot_download("$HF_REPO", token=P._hf_token(), local_dir="$ROOT/hub",
                  allow_patterns=["$CELL/*"])
p = pathlib.Path("$OUT")
if not p.is_dir():
    raise SystemExit("REFUSING: nothing pulled to %s" % p)
got = sorted(f.name for f in p.iterdir())
for f in got:
    print("    %s  %.2f MB" % (f, (p / f).stat().st_size / 1e6))
need = ["model.safetensors", "config.json", "weight_delta.json",
        "tokenizer.json", "tokenizer_config.json"]
missing = [n for n in need if n not in got]
if missing:
    raise SystemExit("REFUSING: the persisted object is missing %r. A read of a "
                     "partial object is not a read of this run." % missing)
print("  the object is complete: %d file(s)" % len(got))
PYPULL

step corpus
# ⛔ Needed by `vocab_coverage`, which measures the per-leaf movement prediction
# from THIS corpus under THIS tokenizer. Never a constant.
$PY tools/act2_build_multiturn.py --recipe content-transient \
    --suppression-window 0 --chains 1445 --multiturn-fraction 0.5 \
    --map derived --seed $SEED --out $ROOT/corpus_ct-s$SEED 2>&1 | tee -a $LOG

step corpus_pin
GOT=$(sha256sum $ROOT/corpus_ct-s$SEED/train.jsonl | cut -c1-16)
echo "  train sha $GOT (expected $CORPUS_SHA)" | tee -a $LOG
if [ "$GOT" != "$CORPUS_SHA" ]; then
  echo "⛔⛔ CORPUS SHA MISMATCH — the coverage prediction would be about a different language" | tee -a $LOG
  exit 1
fi
echo "  ✅ corpus is byte-identical to the one §5 declares" | tee -a $LOG

step flocal_reread
$PY tools/act2_flocal.py --model $OUT --n 64 2>&1 | tee -a $LOG

step lag_reread
# ⭐ The seeded read. `--seed` now reaches the sampling stream as well as the
# seed surfaces, and the report records which.
$PY tools/act2_model_lag.py --model $OUT --object-kind full_weight \
    --chains 12 --turns 10 --temperature 0.70 --max-new-tokens 256 \
    --seed $SEED --out $ROOT/model_lag_${CELL}_reread.json 2>&1 | tee -a $LOG

step vocab_coverage
$PY tools/act2_vocab_coverage.py --model $MODEL \
    --corpus $ROOT/corpus_ct-s$SEED --out $ROOT/vocab_coverage.json 2>&1 | tee -a $LOG

step mapping_moved
# ⛔ PREREG c2a4f0ca §5 — asserted per declared leaf, against each leaf's OWN
# prediction. The delta being read is the one PERSISTED WITH THE OBJECT, so this
# re-check is about the same weights the lag profile above was taken from.
$PY - <<PYMAP 2>&1 | tee -a $LOG
import json, pathlib, sys
sys.path.insert(0, ".")
from tlon.act2.full_weight import MAPPING_MOVED, mapping_moved
d = json.loads(pathlib.Path("$OUT/weight_delta.json").read_text(encoding="utf-8"))
cov = json.loads(pathlib.Path("$ROOT/vocab_coverage.json").read_text(encoding="utf-8"))
print("  vocab coverage = %.6f (%d distinct ids / %d rows)"
      % (cov["coverage"], cov["distinct_token_ids"], cov["vocab_size"]))
verdict, why = mapping_moved(d, vocab_coverage=cov["coverage"])
print("  %s" % verdict)
print("  %s" % why)
if verdict != MAPPING_MOVED:
    print("  the floor table may NOT be read (PREREG c2a4f0ca §5/§7).")
    raise SystemExit(1)
print("  the verdict below is READABLE: both mapping halves trained.")
PYMAP

step verdict_reread
# ⛔ `set -e` would abort on a STOP exit code, and a STOP is a result, not a
# pipeline failure. Captured, not trapped.
EV=0
$PY tools/act2_fullft_verdict.py \
    --delta $OUT/weight_delta.json \
    --lag $ROOT/model_lag_${CELL}_reread.json \
    --ledger runs/act2/ledger.jsonl --prereg $PREREG_PATH \
    --out $ROOT/verdict_${CELL}_reread.json 2>&1 | tee -a $LOG || EV=$?

# ⛔⛔ NO EPOCH-2 BRANCH EXISTS HERE, AT ALL. This script re-reads an object; it
# has no training leg to fall into and nothing it could spend an epoch on. The
# exit code is RECORDED and the run ends either way — including exit 5, the
# unscoreable speaker, which is an honest result and not a reason to train.
case $EV in
  0) echo "⭐ GO on all three axes" | tee -a $LOG ;;
  3) echo "⛔⛔ INSTRUMENT FAULT — the §4.1 precondition did not pass. No row may be read." | tee -a $LOG ;;
  4) echo "⭐⭐ READABLE STOP (floored-but-fluent)" | tee -a $LOG ;;
  5) echo "⛔⛔ NO VERDICT — the speaker was UNSCOREABLE on this draw." | tee -a $LOG
     echo "   Honest, and recorded: it emitted no exchange long enough to score." | tee -a $LOG
     echo "   ⚠️ Sampling is stochastic; see sampling_stream_seeded in the lag report." | tee -a $LOG ;;
  *) echo "⛔ STOP row — see the verdict artifact" | tee -a $LOG ;;
esac

# ── THE GATE ON ~/DONE ──────────────────────────────────────────────────────
# ⛔⛔ NOT `tlon_gate_done`. It verifies CELLS, and `unpersisted()` checks THIS
# RUN'S OWN persist ledger -- so a run that deliberately persists no cell can
# never satisfy it. The first version called it with $CELL on the theory that it
# would re-verify the object on the hub; it does not, and I asserted that from
# the function's NAME instead of reading it. It refused, correctly, after the
# verdict had already been computed and pushed.
#
# ⭐ `tlon_mark_done` is factored out from the verification precisely because
# THE CHECK VARIES AND THE MARKER'S MEANING MUST NOT. A read-only run's
# certifiable output is its READ ARTIFACTS, so that is what is verified here.
tlon_persist_run_files "$PY" "$ROOT" "$HF_REPO" \
    "$ROOT/model_lag_${CELL}_reread.json" \
    "$ROOT/verdict_${CELL}_reread.json" \
    "$ROOT/vocab_coverage.json"

step verify_reads
RBASE=$(basename $ROOT)
$PY - <<PYVER 2>&1 | tee -a $LOG
import sys
sys.path.insert(0, "tools")
from huggingface_hub import HfApi
import act2_provision as P
api = HfApi(token=P._hf_token())
have = set(api.list_repo_files("$HF_REPO"))
want = ["$RBASE/model_lag_${CELL}_reread.json",
        "$RBASE/verdict_${CELL}_reread.json",
        "$RBASE/vocab_coverage.json",
        "$RBASE/pipeline_fullft_read.log"]
missing = [w for w in want if w not in have]
for w in want:
    print("  %s %s" % ("MISSING" if w in missing else "OK     ", w))
if missing:
    raise SystemExit("REFUSING to mark done: %d read artifact(s) are not in "
                     "durable storage. Until they are, ~/DONE would be a lie "
                     "and the watchdog terminates on it." % len(missing))
print("  all %d read artifact(s) verified in durable storage" % len(want))
PYVER

TLON_SUMMARY="⭐ RE-READ COMPLETE — $CELL re-read from the hub, verdict exit $EV, WEIGHTS UNTOUCHED"
tlon_mark_done "$HF_REPO" "the read artifacts for $CELL (weights not written)"
