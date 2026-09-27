#!/usr/bin/env bash
# ═══ IDF-2 — TRAIN M AND C1, THEN READ FOUR ARMS ═══════════════════════════
#
# `docs/PREREG_IDF2_2026_09_26.md`, LOCK `37363296`. Step 0 and Step P have both
# passed; this is the treatment.
#
# ⭐⭐ THE ESTIMAND IS `closes(M) − closes(C1)`. Both adapters train on the SAME
# corpus under the SAME bar (`held`) at the SAME dose, and differ in exactly one
# thing: whether each provoke row's input carries the annotation line. That is
# what makes the difference the marker's effect rather than a corpus rebuild —
# §2, and the reason C1 exists at all.
#
# ⛔ W2 IS NOT IN THIS RUN. Its input is `t−2` and `t−1` as real chat turns,
# which needs a row shape and a reader history that do not exist yet. Nathan
# chose (b): the two primary arms now, W2 on a later box. `tests/…` asserts W2
# is absent here rather than half-present.
#
#   bash tools/pipeline_idf2_train.sh
#
set -uo pipefail
source "$(dirname "$0")/pipeline_lib.sh"
tlon_trap_init
set -e

ROOT=${ROOT:-runs/act2/idf2/train}
tlon_log_init "$ROOT" pipeline_idf2_train.log

PY=${PY:-$HOME/venv/bin/python}
MODEL=Qwen/Qwen2.5-7B-Instruct
HF_REPO=${HF_REPO:-keyzersoze04/tlon-act2-adapters}
SEED=${SEED:-20624}

# ⛔ Matched to `16abeb8d…`'s manifest, field by field, not by memory:
# chains 1445, turns 12, responsiveness 1.0, multiturn fraction 0.5 BY COMPUTE.
CHAINS=${CHAINS:-1445}
TURNS=${TURNS:-12}
MTFRAC=${MTFRAC:-0.5}
RESP=${RESP:-1.0}

# Training config, same as the `retrain12_ct` cell.
SEQ=${SEQ:-256}
BATCH=${BATCH:-4}
ACCUM=${ACCUM:-4}

# ⛔ §5 read geometry, and the seed counts RE-LOCKED on Step P's measured SD
# (DEVIATIONS D4). The gating arms get five; M-shuffle is descriptive and keeps
# three. Distinct from Step P's seeds so no read is reused across steps.
RCHAINS=${RCHAINS:-48}
RTURNS=${RTURNS:-10}
GATING_SEEDS=${GATING_SEEDS:-"30624 30625 30626 30627 30628"}
DESC_SEEDS=${DESC_SEEDS:-"30624 30625 30626"}

step watchdog
# ⛔⛔ FIRST, BEFORE ANY GPU TIME. 2 trains (~4.5 h each) + 18 reads (~28 min
# each) ≈ 17.5 h, so a 26 h deadline is ~1.5× headroom. The stall window is
# 90 min because a training leg's log gaps are longer than a read's.
tlon_arm_watchdog "$PY" "$ROOT" "$HF_REPO" pipeline_idf2_train.sh 26 90 $$

step prereg_lock
$PY tools/lock_prereg.py docs/PREREG_IDF2_2026_09_26.md | tee -a "$LOG"

# ── the two corpora ────────────────────────────────────────────────────────
# ⛔⛔ SAME SEED, SAME CHAINS, SAME BAR. `--marker` is the ONLY difference, and
# `act2_build_multiturn` REFUSES `--marker` unless the recipe is
# content-transient-held — a marker naming `held` on a corpus barred by
# `inherited` would train the model that the line is noise.
# ⛔⛔ C1 IS DERIVED FROM M, NOT BUILT BESIDE IT, AND THE GATE IS WHY.
# Two separate builds are NOT the same corpus: `--multiturn-fraction` is by
# COMPUTE and rows are solved for, so a marked provoke row costs more tokens,
# so the marked build needs FEWER singleturn rows to reach the same split.
# Measured at 80 chains before any GPU time: 2,190 rows marked vs 2,168
# unmarked. M and C1 would have differed in how much write/read training they
# saw, and `closes(M) − closes(C1)` would have carried that difference.
# ⭐ Stripping the annotation from M's rows makes the row set, the targets, the
# scenes and the forces identical BY CONSTRUCTION. What differs is total token
# count — exactly what adding a marker unavoidably does. The removable confound
# is removed; the unremovable one is named. (DEVIATIONS D6.)
CM=$ROOT/corpus_heldM-s$SEED
CC=$ROOT/corpus_heldC1-s$SEED
if [ ! -f "$CM/train.jsonl" ]; then
  step corpus_M
  $PY tools/act2_build_multiturn.py \
      --recipe content-transient-held --marker \
      --chains "$CHAINS" --turns "$TURNS" --multiturn-fraction "$MTFRAC" \
      --responsiveness "$RESP" --seed "$SEED" --map derived \
      --out "$CM" 2>&1 | tee -a "$LOG"
fi
if [ ! -f "$CC/train.jsonl" ]; then
  step corpus_C1_derived
  $PY tools/act2_idf2.py unmark --marked "$CM" --out "$CC" 2>&1 | tee -a "$LOG"
fi

step corpus_diff
# ⛔⛔ THE ONE DIFFERENCE, PROVED. If M's and C1's corpora differed anywhere but
# the marker line, `M − C1` would not be the marker's effect — and the two
# builds are separate invocations of a generator with its own RNG, so "same
# seed" is a claim, not a guarantee. This asserts it on the FILES.
$PY tools/act2_idf2_corpus_diff.py --marked "$CM" --unmarked "$CC" \
    --out "$ROOT/corpus_diff.json" 2>&1 | tee -a "$LOG"

# ── train, gate, read ──────────────────────────────────────────────────────
for ARM in M C1; do
  CELL=held$ARM-s$SEED
  A=$ROOT/adapter_$CELL
  C=$ROOT/corpus_$CELL

  if [ ! -f "$A/adapter_model.safetensors" ]; then
    step train_$CELL
    $PY tools/act2_finetune.py --model $MODEL --out "$A" \
        --corpus "$C" --seq $SEQ --batch $BATCH --accum $ACCUM \
        --seed $SEED 2>&1 | tee -a "$LOG"
  fi

  step flocal_$CELL
  # ⛔ F-LOCAL is the fluency gate. §4: it must clear before any lag read of
  # this adapter is INTERPRETED. A build that does not speak is not a release
  # result, it is a broken build.
  $PY tools/act2_flocal.py --model $MODEL --adapter "$A" \
      --n 64 --n-comp 64 2>&1 | tee -a "$LOG"

  step dose_$CELL
  # ⛔ §4's gate, against ct-s20624's RECOMPUTED rms (0f). Non-zero exits here,
  # so the pipeline halts rather than reading an arm whose dose is a confound.
  $PY tools/act2_idf2.py dose --adapter "$A" \
      --out "$ROOT/dose_$CELL.json" 2>&1 | tee -a "$LOG"
done

step reads
# ⛔⛔ FOUR ARMS, AND THREE OF THEM ARE THE SAME WEIGHTS. M, M-strip and
# M-shuffle all read `adapter_heldM`; only the marker differs, and `--marker`
# is recorded in every result as `marker_fn` so no two rows can differ by
# filename alone. C1 is read BARE, because C1 never trained with a marker.
read_arm() {  # $1 label  $2 adapter  $3 marker  $4 seeds
  for S in $4; do
    O=$ROOT/lag_$1_s$S.json
    [ -f "$O" ] && { echo "  $1 seed $S done — skipping" | tee -a "$LOG"; continue; }
    echo "  ── $1 · marker=$3 · seed $S ──" | tee -a "$LOG"
    $PY tools/act2_model_lag.py --model $MODEL --adapter "$2" \
        --object-kind adapter --marker "$3" \
        --chains $RCHAINS --turns $RTURNS --seed "$S" \
        --temperature 0.7 --max-new-tokens 256 --out "$O" 2>&1 | tee -a "$LOG"
  done
}
read_arm M        "$ROOT/adapter_heldM-s$SEED"  held    "$GATING_SEEDS"
read_arm C1       "$ROOT/adapter_heldC1-s$SEED" none    "$GATING_SEEDS"
read_arm M-strip  "$ROOT/adapter_heldM-s$SEED"  strip   "$GATING_SEEDS"
read_arm M-shuffle "$ROOT/adapter_heldM-s$SEED" shuffle "$DESC_SEEDS"

step persist_cells
# ⛔⛔ THE WEIGHTS GO UP BEFORE THE ANALYSIS RUNS. `s20620` was lost because
# persistence waited for the end of a run. Two adapters at ~4.5 GPU-h each are
# not re-derivable from anything on this box.
$PY tools/act2_box_persist.py --root "$ROOT" --repo "$HF_REPO" \
    persist --cells "heldM-s$SEED heldC1-s$SEED" 2>&1 | tee -a "$LOG"

step persist
tlon_persist_run_files "$PY" "$ROOT" "$HF_REPO" \
    "$ROOT/corpus_diff.json" $ROOT/dose_*.json $ROOT/lag_*.json

tlon_mark_done "$HF_REPO" "IDF-2 M + C1 adapters, 18 reads, dose + corpus-diff gates"
