#!/usr/bin/env bash
# ═══ THE PUZZLE SPEAKER — retrain on natural English + bench context ═════════
#
# ⛔⛔ THIS IS A PRODUCT BUILD, NOT A RESEARCH RUN. No release read, no lag
# curve, no dose curve, no drift, no two-speaker probe, no readings audit gate.
# Those answer "does release install", which is a different question with a
# different prereg. Adding one here would make a chat app depend on an
# instrument and make its numbers ambiguous between the two.
#
# WHAT IT FIXES, both measured, both in the corpus rather than the weights:
#
#   1. `corpus.py:282` built every write pair as `english = gloss(scene)`, the
#      austere machine gloss. The speaker had NEVER seen a sentence a person
#      would type, and collapsed to two words from turn two.
#   2. `multiturn.py` carries "ONLY the prior turn's force ... no content
#      relation" — measured at 27.1% content overlap, which is chance. The
#      speaker was trained that context is noise, so feeding it context made
#      replies connect LESS (0 of 3, against 3 of 4 with context off).
#
# ⛔⛤ THE FIRST FIX FOR (2) DID NOT WORK AND THIS HEADER ONCE SAID IT DID.
# It claimed "599 bench conversations at 68% content carry". RETRACTED: that
# 68% was WORD overlap and three quarters of it was degree, tense and relator
# particles — forms every utterance needs, so they collide by necessity. At
# ROOT level, which is what a player decodes against, it was 9%; WITHIN a
# conversation it ran BELOW chance (5.3% vs a 7.5% shuffled null, p=0.000).
# The retrain bought on that number moved nothing, and the cause was one word
# in the dialogue prompt asking for a "FRESH impression" — a different
# happening every turn, in a language whose roots ARE happenings.
#
# The corpus now runs 8,181 natural-English pairs, 679 bench conversations at
# **97.1% ROOT-carry [96.3, 97.7], root-led (R 57.7% of what carries)**, and
# 2,466 contrastive pairs for the class boundaries the gate actually refused.
# Carry is FORCED at build time: the reply's proposal is given the prior
# turn's roots and must reuse one and add one.
#
# ⛔⛔ THAT FORCED CARRY IS PUZZLE-ONLY. It is the crib that makes the cipher
# solvable and it is exactly the persistence the research's drift measurement
# must not contain. Every conversation row is stamped `forced_root_carry`.
# Never point a research pipeline at this corpus.
#
# ⛔⛔ THE SAFETY SCAFFOLDING IS SOURCED, NEVER COPIED. The trap, the log
# rotation, the watchdog arming and the `~/DONE` gate were the site of both
# losses on 2026-09-04. Copied into each script, the next fix lands in one copy
# and not the others — and the box running the most expensive job is the one
# holding the stale copy.
source "$(dirname "$0")/pipeline_lib.sh"
tlon_trap_init
set -euo pipefail

# ⛔⛔ THE VENV, NOT `python`. `pipeline_retrain.sh` and `pipeline_fullft.sh`
# both spell it this way and this file did not — so the preflight ran under the
# box's system interpreter and died on `No module named 'transformers'` after
# the clone, the credential write and the corpus pull had all succeeded. It
# failed in the right place (before the watchdog, before any GPU) but for a
# reason that had nothing to do with the run. Copy the convention that works.
PY="${PY:-$HOME/venv/bin/python}"
ROOT="${ROOT:-runs/act2/puzzle}"
HF_REPO="${HF_REPO:-keyzersoze04/tlon-act2-adapters}"
# ⛔⛔ EXPORTED, BECAUSE THE PREFLIGHT IS A CHILD PROCESS. The preflight below
# reads these through `os.environ`, and a shell variable that is merely assigned
# is not in a child's environment — python would `KeyError` on the FIRST line of
# the one check standing between a mis-lexiconed corpus and eight hours of GPU.
export MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"
# ⛔⛔ THE STEERED BUILD. Pointed at the old path, a run would train the
# 9.3%-carry speaker and every number downstream would look healthy.
# ⭐ As of 2026-09-21 the directory name is no longer the only thing that says
# which build this is: every conversation row carries `forced_root_carry` and
# `recipe`, and `meta.json` — which ships as `--corpus-manifest` — carries the
# counts. Until then the two builds were schema-identical, `source:
# conversation` and nothing else. `corpus_bench` is the pre-steer build, kept
# as the control the seq figures below reproduce.
export CORPUS="${CORPUS:-runs/act2/corpus_bench_steered}"
export CELL="${CELL:-bench-s20624}"
export SEED="${SEED:-20624}"
export ROOT

# ⛔⛔ THE LEXICON IS AN ARGUMENT AND IT IS NOT THE FROZEN ONE. Every research
# number was measured against e2b8527…; the puzzle speaks the 218-root expanded
# language. A run that silently used the frozen file would train a speaker that
# cannot say 62 of the words its corpus contains.
export TLON_LEXICON="${TLON_LEXICON:-lexicon_expanded.yaml}"
export EXPECT_LEXICON="${EXPECT_LEXICON:-08c03b0a81330e4ba42883fa8b08c873}"

# ⛔⛔ seq 1024 IS A REQUIREMENT, NOT A PREFERENCE, AND THE DEFAULT WOULD VOID
# THE RUN. Truncation lands at the END, where the answer is, and the loss looks
# healthy throughout.
#
# ⛔⛤ RE-MEASURED 2026-09-21 ON THE STEERED CORPUS, BECAUSE THE FIGURES THAT
# STOOD HERE WERE TAKEN ON THE PRE-STEER BUILD — 3,926 context rows against
# this corpus's 3,149. Reading a number measured on one distribution against
# another is the mistake this arc made four separate times. (The old line also
# divided a train-only numerator, 3,698, by a train+eval denominator, 4,010.)
# Measured through `act2_finetune.row_to_text` — the trainer's own composer, so
# the string counted is the string tokenized — over train.jsonl, 14,921 rows of
# which 3,149 carry context:
#
#   seq  256 -> 3,550 truncated (23.8%) · 2,878 of 3,149 context rows (91.4%)
#   seq  512 -> 1,183 truncated ( 7.9%) · 1,183 of 3,149 context rows (37.6%)
#   seq 1024 ->     4 truncated ( 0.0%) ·     4 of 3,149 context rows ( 0.1%)
#
# ⭐ The same script re-read the pre-steer corpus and reproduced its published
# 4,292 / 27.6% / 3,698 exactly — the instrument is certified, not assumed.
# ⚠️ The longest row is 1,081 tokens, so 4 rows still clip at 1024. seq 1536
# clears them and costs memory the 40 GiB card does not have.
export SEQ="${SEQ:-1024}"

# ⛔ batch 2, NOT 4, ON A 40 GiB CARD. `act2_finetune.MEASURED` records run 4 as
# "PLANNER UNDER-PREDICTED BY 28%". batch 4 plans 36.6 GiB -> 46.9 with that
# miss and OOMs; batch 2 plans 28.3 -> 36.2 and fits. bf16 throughout because
# every measured number in this project is bf16 and 4-bit changes the model.
BATCH="${BATCH:-2}"
ACCUM="${ACCUM:-8}"
EPOCHS="${EPOCHS:-3}"
RANK="${RANK:-32}"          # alpha = rank*2 = 64, matching ct-s20624 exactly

DEADLINE_H="${DEADLINE_H:-8}"
STALL_MIN="${STALL_MIN:-45}"

A="$ROOT/adapter_$CELL"
mkdir -p "$ROOT/logs"
tlon_log_init "$ROOT" "pipeline_puzzle.log"

echo "  cell     $CELL"            | tee -a "$LOG"
echo "  model    $MODEL"           | tee -a "$LOG"
echo "  corpus   $CORPUS"          | tee -a "$LOG"
echo "  lexicon  $TLON_LEXICON"    | tee -a "$LOG"
echo "  shape    seq $SEQ · batch $BATCH x $ACCUM · $EPOCHS epochs · rank $RANK" \
     | tee -a "$LOG"

# ── 1 · WATCHDOG, BEFORE ANYTHING THAT CAN FAIL ─────────────────────────────
# ⛔⛔ HARD RULE, NO EXCEPTION. A box billing unguarded cost ~$16 of idle time
# once and 35 minutes of unguarded billing another time to save a $9 re-fire.
#
# ⛔⛤ IT USED TO ARM *AFTER* THE PREFLIGHT, AND THAT WAS A HOLE. The preflight's
# whole job is to REFUSE — wrong lexicon, unrenderable rows — and `set -e` means
# a refusal exits the script. Exiting before this line left a freshly
# provisioned box running with nothing watching it, so the stricter the
# preflight got, the likelier it was to strand a box on the meter. Armed first,
# the watchdog sees the watched pid die and terminates within one 300 s poll:
# `decide()` returns KILL for "process is gone and the run did not complete".
# A guard that only covers the paths that succeed is not a guard.
step watchdog
tlon_arm_watchdog "$PY" "$ROOT" "$HF_REPO" pipeline_puzzle.sh \
    "$DEADLINE_H" "$STALL_MIN" $$

# ── 2 · THE CORPUS, REBUILT HERE FROM COMMITTED INPUTS ──────────────────────
# ⛔⛔ THE ROWS WERE NEVER IN THE CLONE, AND NOBODY WROTE THAT DOWN. Provisioning
# does `rm -rf ~/tlon && git clone`, and `corpus_bench_steered/` was untracked —
# so every previous run of this pipeline trained on a corpus put on the box by
# hand, by a step that existed only in somebody's scrollback. The run log opens
# at the preflight with the data already present and no record of where it came
# from. A pipeline that cannot say where its training data came from is not
# reproducible, whatever its logs say.
#
# ⭐ THE INPUTS ARE COMMITTED, THE ROWS ARE NOT, AND THE SPLIT IS THE EXISTING
# RULE. `.gitignore` excludes what is regenerable and keeps what is not:
# `corpus_conv_steered` cost $62.97 of hosted sampling at temperature 1.0 and
# `corpus_natural` is part of the ~$130 Route-A build, so no seed reproduces
# either and both are in the repo. These rows ARE an exact function of those
# inputs at a fixed seed — verified byte-identical on a clean rebuild — so the
# builder plus the pin below is the stronger artifact.
step corpus
$PY tools/act2_build_multiturn_rows.py \
    --conversations runs/act2/corpus_conv_steered/conversations.jsonl \
    --natural runs/act2/corpus_natural/pairs.jsonl \
    --contrastive runs/act2/corpus_contrastive/pairs.jsonl \
    --out "$CORPUS" --seed "$SEED" 2>&1 | tee -a "$LOG"
CORPUS_RC=${PIPESTATUS[0]}
[ "$CORPUS_RC" -eq 0 ] || { echo "⛔ corpus build rc=$CORPUS_RC" | tee -a "$LOG"; exit 1; }

# ⛔⛔ PINNED, BECAUSE "DETERMINISTIC" IS A CLAIM UNTIL SOMETHING CHECKS IT.
# This is the sha of the rows whose 97.1% root-carry and whose seq-1024
# truncation figures are published in the header above. If the box builds
# anything else — a changed input, a changed builder, a changed seed — those
# numbers stop being about the thing being trained, which is the failure this
# whole arc is a record of. Refuse rather than train.
# ⛔ The builder writes `newline="\n"` explicitly. Without that the bytes differ
# between a Windows laptop and this box and no pin can exist at all.
EXPECT_TRAIN_SHA="${EXPECT_TRAIN_SHA:-62170ac2d87d0ea2251ca009d59aa041302cb09913d7d96ab5f18f1ab1296cb5}"
GOT_TRAIN_SHA=$(sha256sum < "$CORPUS/train.jsonl" | cut -d' ' -f1)
if [ "$GOT_TRAIN_SHA" != "$EXPECT_TRAIN_SHA" ]; then
  echo "⛔⛔ CORPUS SHA MISMATCH — refusing to train on rows nobody measured" \
       | tee -a "$LOG"
  echo "   expected $EXPECT_TRAIN_SHA" | tee -a "$LOG"
  echo "   got      $GOT_TRAIN_SHA" | tee -a "$LOG"
  exit 1
fi
echo "  ✅ corpus rebuilt on the box and sha-verified" | tee -a "$LOG"

# ── 3 · PREFLIGHT, BEFORE ANY GPU TIME ──────────────────────────────────────
# ⛔⛔ EVERY PREFLIGHT THIS PROJECT HAS WRITTEN PASSED BEFORE RUN 3a DIED,
# BECAUSE NONE OF THEM LOADED ANYTHING. These check the two inputs that would
# each silently void the run: the wrong lexicon, and a corpus whose rows do not
# render. Both are cheap and neither needs the GPU.
step preflight
$PY - <<'PYEOF' 2>&1 | tee -a "$LOG"
import json, os, pathlib, sys
sys.path.insert(0, "."); sys.path.insert(0, "tools")
from tlon.grammar import classes as C
lex = C.load()
want = os.environ["EXPECT_LEXICON"]
got = lex["_hash"]
print("  lexicon %s  %d roots" % (got, len(lex["classes"]["R"])))
if got != want:
    raise SystemExit("⛔⛔ LEXICON HASH %s != expected %s. Refusing: a "
                     "speaker trained against a different language than its "
                     "corpus would look healthy and be wrong." % (got, want))
corpus = pathlib.Path(os.environ["CORPUS"])
rows = []
with (corpus / "train.jsonl").open(encoding="utf-8") as fh:
    for i, line in enumerate(fh):
        if i >= 200: break
        rows.append(json.loads(line))
if not rows:
    raise SystemExit("⛔ corpus train.jsonl is empty")
from transformers import AutoTokenizer
import act2_finetune as F
tok = AutoTokenizer.from_pretrained(os.environ["MODEL"])
seq = int(os.environ["SEQ"])
over = 0
ctx = 0
for r in rows:
    n = len(tok(F.row_to_text(r, tok))["input_ids"])
    over += n > seq
    ctx += bool(r.get("context"))
print("  sampled %d rows · %d carry context · %d exceed seq %d"
      % (len(rows), ctx, over, seq))
if ctx == 0:
    raise SystemExit("⛔⛔ NO CONTEXT ROWS in the sample. The whole "
                     "point of this retrain is context; training without it "
                     "would produce a speaker indistinguishable from the old "
                     "one and nothing would say so.")
if over > len(rows) * 0.02:
    raise SystemExit("⛔⛔ %d/%d rows exceed seq %d. Truncation lands "
                     "at the END, where the answer is." % (over, len(rows), seq))
PYEOF

# ── 4 · TRAIN ───────────────────────────────────────────────────────────────
step train
$PY tools/act2_finetune.py --model "$MODEL" --out "$A" \
    --corpus "$CORPUS" --seq "$SEQ" --batch "$BATCH" --accum "$ACCUM" \
    --epochs "$EPOCHS" --rank "$RANK" --seed "$SEED" 2>&1 | tee -a "$LOG"
# ⛔ `$?` AFTER A PIPE IS `tee`'s STATUS AND IS ALWAYS 0.
TRAIN_RC=${PIPESTATUS[0]}
[ "$TRAIN_RC" -eq 0 ] || { echo "⛔ train rc=$TRAIN_RC" | tee -a "$LOG"; exit 1; }

# ── 5 · IS IT STILL A SPEAKER? ──────────────────────────────────────────────
# ⛔ F-LOCAL is the only read here, and it is a HEALTH CHECK, not a verdict:
# cardless and unconstrained, it asks whether the thing still produces legal
# Tlön on demand. Expanding the lexicon and adding context should not break
# fluency — but "should not" is why it is measured.
step f_local
$PY tools/act2_flocal.py --model "$MODEL" --adapter "$A" \
    --n 64 --n-comp 64 2>&1 | tee -a "$LOG"
FLOCAL_RC=${PIPESTATUS[0]}
[ "$FLOCAL_RC" -eq 0 ] || echo "⚠ f_local rc=$FLOCAL_RC (recorded, not fatal — \
the adapter is still persisted below; a read that failed must not destroy the \
thing it was reading)" | tee -a "$LOG"

# ── 6 · PERSIST BEFORE THE BOX CAN END ITSELF ───────────────────────────────
# ⛔⛔ THE ADAPTER IS THE ONE ARTIFACT RE-RUNNING CANNOT REGENERATE CHEAPLY, and
# a Lambda box takes its disk with it on terminate.
# ⛔⛔ `CELL_FILES` DEMANDS `factorial.json` AND `persist_cell` REFUSES AN
# INCOMPLETE CELL — after the training has already been paid for. It is written
# here rather than discovered there.
#
# ⛔⛔ AND IT CARRIES NO `factorial_pair_key` AND NO `pairing_capability_side`.
# Those are the fields every pooling and pairing routine reads, and this build
# is NOT a member of the factorial: different lexicon (218 roots, not the frozen
# 156), different corpus, different question. Omitting them makes the adapter
# STRUCTURALLY un-poolable rather than merely labelled — the same discipline
# `dose_arm_entry` applies, so a later analysis that forgets what this was
# cannot quietly fold it in.
step factorial
$PY - <<'PYEOF' 2>&1 | tee -a "$LOG"
import json, os, pathlib, sys
sys.path.insert(0, ".")
from tlon.grammar import classes as C
cell = os.environ["CELL"]
out = pathlib.Path(os.environ["ROOT"]) / ("adapter_%s" % cell) / "factorial.json"
out.parent.mkdir(parents=True, exist_ok=True)
body = {
    "name": cell,
    "recipe": "puzzle-bench",
    "seed": int(os.environ["SEED"]),
    "cell": cell,
    "generator": "act2_build_multiturn_rows/natural+conversation+contrastive/v1",
    "lexicon": C.load()["_hash"],
    "lexicon_file": os.environ["TLON_LEXICON"],
    "corpus": os.environ["CORPUS"],
    "product": "puzzle",
    "NOT_A_FACTORIAL_MEMBER": (
        "no factorial_pair_key and no pairing_capability_side: this build "
        "speaks the 218-root expanded lexicon and cannot be compared against "
        "the frozen-lexicon population."),
}
tmp = out.with_suffix(".json.tmp")
tmp.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
tmp.replace(out)
print("  wrote %s (lexicon %s)" % (out, body["lexicon"]))
PYEOF

step persist
# ⭐ `cell`, NOT a bare file push, and the difference is the verify. For THIS
# run the deliverable is the weights, so `verify --cells` — which asks whether
# the cell's adapter files arrived — is the correct gate, the same one the
# epochs arms had to be repointed AWAY from because their deliverable was the
# readings. Guard the thing the config actually produces.
#
# ⛔ `--solo-n 0` is honest, not a bypass: this pipeline generates no solo
# transcripts, and `persist_cell` refuses any mismatch between the count it is
# told and the count it finds.
#
# ⛔ The corpus manifest is a keyword with no default because the gate run once
# persisted everything EXCEPT it, and noticed with the box already terminating.
# `meta.json` is this corpus's own recipe record — row counts by source, context
# depth, seed.
$PY tools/act2_box_persist.py --root "$ROOT" --repo "$HF_REPO" \
    cell --cell "$CELL" --solo-n 0 \
    --corpus-manifest "$CORPUS/meta.json" 2>&1 | tee -a "$LOG"

tlon_gate_done "$PY" "$ROOT" "$HF_REPO" "$CELL" 2>&1 | tee -a "$LOG"
