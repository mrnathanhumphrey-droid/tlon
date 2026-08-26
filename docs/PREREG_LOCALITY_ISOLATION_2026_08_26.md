# PREREG — the locality isolation test

**Locked 2026-08-26, BEFORE reading Nate's context-issue framework, and before
any corpus exists.** Tests the locality architecture's *architectural* claim on
weights we already have. Design is fixed at this commit; changes after this point
are amendments and are labelled as such.

---

## THE CLAIM UNDER TEST

Locality asserts two separable things. **Only the second costs money.**

1. **ARCHITECTURAL** — accumulating context is the collapse mechanism. Remove the
   accumulation and the exchange sustains.
2. **TRAINING** — a model trained to paint fresh, force-connected, content-free
   scenes does this well.

**This test is claim 1 only, on run 3, untrained.** If claim 1 is false there is
nothing for the corpus to exploit and the architecture is refuted for ~$1 instead
of ~$15 plus a week.

## ⛔⛔ WHAT WE ALREADY MEASURED, WRITTEN DOWN BEFORE THE RUN

Three numbers exist already and the design must answer to them, not discover them
afterwards:

| fact | source | consequence |
|---|---|---|
| at history-depth 1 run 3 **deterministically ECHOES** `parse(history)` — **8/10, 1/8 distinct** | `tools/act2_exchange_probe.py:158` | depth-1 is a **known-degenerate regime**, not neutral ground. 1/8 distinct ⇒ ~0.125, far below `DEGENERACY_TTR_FLOOR` 0.50 |
| `act2_temp_sweep.py` **refuses `--depth < 3`** | spec line 328 | the codebase already treats depth-1 as a measurement artifact |
| a painter ignoring the prior turn scores **0/200 guard-fires** at depths 8/20/40, mean TTR 0.937/0.856/0.738 | measured 2026-08-26, this session | **the existing gate cannot fail on noise.** A second, failable measure is mandatory |

⭐ **The first fact predicts the naïve version of this test FAILS FOR THE WRONG
REASON.** A window-1 arm on the current prompt would reproduce the echo, and the
echo is a *prompting* effect (a depth-1 history reads as "continue this") — not
evidence about accumulation. **Locality's actual condition is a painter PROVOKED
to paint fresh, which the current prompt never asks for.** So the design needs an
arm that separates them, and that arm is the real test.

## ARMS — one rental, one model, four arms

Subject: **run 3** (`keyzersoze04/tlon-7b-lora`, frozen, published). The only
uncontaminated adapter.

| arm | history window | prompt | purpose |
|---|---|---|---|
| **A** | ∞ (accumulate) | current | **reproduce the measured null.** Must degenerate |
| **B** | 3 | current | the middle; is collapse graded in window? |
| **C** | 1 | current | ⛔ **the known-artifact arm.** Expected to ECHO |
| **D** | 1 | **fresh-painting provocation** | ⭐ **THE TEST.** Locality's actual condition |

**Held identical across arms:** weights · temperature · `seed_history` · turns=40
· battery · decoding params · the frozen-partner control · seeds. **The only
variables are window and (for D) the prompt**, and D differs from C in prompt
alone, so C↔D isolates the prompting effect and A↔D isolates accumulation.

⚠️ **D changes two things vs A (window AND prompt) and is therefore NOT a clean
single-variable arm on its own.** It is read only through C and B. Stated here so
it is not claimed as one later.

## MEASURES — the gate, its components, and one that can fail

1. `falsify.degeneracy_guard` verdict — the existing gate (boolean).
2. Its **components** — TTR and near-repetition share, reported separately. A
   boolean hides which limb fired, and the two limbs mean different failures.
3. ⭐ **FORCE-FIDELITY** — the realized 5×5 (prior-force → response-force)
   transition matrix, tested against **independence** (marginal product) by χ².
   **This is the measure that can come back negative on a model that learned
   nothing**, and it establishes the pre-training chance baseline the corpus's
   paired gate will need.
4. **Echo rate** — token overlap between turn *n* and turn *n−1* specifically,
   distinct from the windowed near-repetition share. Echo is the depth-1 failure
   and it needs its own number.
5. Cycle detection (`_find_cycle`) — the existing measure.
6. **Well-formedness rate by turn index** — the one-place oracle. Does local
   coherence decay with turn number, or hold flat? Locality predicts **flat**.

## PRE-DECLARED READINGS — locked, all branches, including the ones that hurt

- **A degenerates, D does not** → accumulation is the mechanism. **Locality
  survives its first real test.** Proceed to the corpus.
- **A degenerates, D degenerates too** → ⛔ **accumulation was never the
  mechanism, and locality is refuted before a corpus exists.** Pre-named
  candidates: the collapse is an attractor in the weights, not the context; or
  depth-1 echo is inherent rather than prompt-driven (read C vs D); or 40 turns
  of anything from this adapter degenerates.
- **C echoes and D does not** → the echo is a **prompting artifact**, the
  depth-1 regime is usable, and `temp_sweep`'s `--depth ≥ 3` refusal should be
  revisited (it would be guarding a prompt, not a depth).
- **C and D both echo** → depth-1 echo is **inherent**. Locality's mechanism is
  compromised before training, and the force map would have to carry the entire
  burden of preventing a mirror. Strong early warning, not a refutation — but the
  corpus spec would need to say how force alone prevents echo.
- **B (window 3) sits between A and D** → collapse is **graded in window**, which
  is itself the most informative outcome available: it would make context length
  a *dial* rather than a switch, and the product could be tuned on it.
- ⛔⛔ **A does NOT degenerate** → **we cannot reproduce our own null.** Everything
  downstream is suspect and nothing else in this run may be read. Halt, diagnose
  the instrument, do not interpret B/C/D.
- **Force-fidelity at chance in every arm** → run 3 has no force-responsiveness
  to build on. Not a refutation (that is what training is for) but it fixes the
  chance baseline and means the corpus must *create* the connection, not sharpen
  one.

## WHAT THIS TEST CANNOT SAY

It cannot say the **corpus** works — claim 2 is untested and untestable without
training. It cannot say two *trained* models sustain. It cannot measure σ_cp or
anything about the pact. **A pass here licenses building the corpus. It does not
license any statement about drift.**

## COST AND LOGISTICS

One rental. Four 40-turn exchanges plus the frozen-partner control ≈ 1 box-hour.
⭐ **Fold in the depth-3 arena-temperature re-derivation (RULING 15) on the same
box** — one rental, both jobs. Pull-and-kill at DONE; zero analysis on a live box.

**Harness work required first ($0, local):** a `--history-window` argument on
`tools/act2_exchange_probe.py` (`exchange()` currently accumulates unconditionally
at line 89), the fresh-painting prompt for arm D, and measures 3/4/6 which do not
exist yet. Red-proof the window knob by asserting window=1 actually truncates —
a knob that silently no-ops would return "locality works" for the worst reason.

---

**Locked before reading the context framework.** The design depends on no part of
it, which is precisely why the blindness was available here after being burned on
RULING 14 — and why it is spent if this file is edited after that framework
arrives.

---

# ⭐⭐ AMENDMENT 1 — 2026-08-26, AFTER the context framework and the (b) ruling

⛔⛔ **THE BLINDNESS CLAIMED ABOVE IS NOW SPENT, AND THIS FILE SAYS SO RATHER THAN
QUIETLY ABSORBING THE CHANGE.** The original text closes: *"the design depends on
no part of it, which is precisely why the blindness was available here after
being burned on RULING 14 — and why it is spent if this file is edited after that
framework arrives."* It has been edited. **Everything above the amendment line is
verbatim as locked; everything below is post-hoc and must be read as such.**

## What changed, and why it is not absorbable

RULING (b) makes the trainer and the arena share ONE prompt
(`tlon/discourse/provocation.py`). That is not a tweak to the arms — it changes
what the arms *mean*.

**The old arm C/D question was PROMPT PREFERENCE:** which wording does the model
respond to better. **That question is RETIRED.** It was never the interesting one
and it is not what the arms now measure.

**The new arm C/D question is TRAIN/SERVE CONTRACT-MATCHING:** arm C is
trained-`write`/`read`, served-`CONVERSE` — *the mismatch*. Arm D is trained and
served on the unified provocation — *the match*. The comparison now asks **"does
matching the training and serving contract eliminate the depth-1 echo"**, which
is more fundamental than the question it replaces and bears directly on the
motivation for the whole corpus.

⛔ **RECORDED SO IT IS NOT MISREAD LATER.** If this amendment were absorbed
silently, a future reader would score the arm C/D result against the *original*
prereg's prompt-preference question and reach a wrong conclusion. The arms are
the same shape; the question underneath them is different.

## ⛔⛔ AMENDMENT 2 — the Q1 baseline was going to conflate THREE things

RULING 4 as first stated was a labelling fix: run 3 is trained-mismatched and
served-mismatched, so beating it measures training **plus** contract-matching,
not training alone. **That understated it.** Run 3's adapter was trained before
the `provoke` direction existed at all, so `run-3-as-published` differs from the
new model in **three** ways at once:

1. multi-turn training — absent
2. serve-time contract matching — absent
3. the `provoke` direction present in training — absent

⇒ A CLEAN POSITIVE against that single baseline is **a three-way confound in the
headline result**, not a caveat.

**FIX — a FOURTH ARM: run 3 RE-SERVED under the unified provocation.** Same
published weights, new serving prompt. That arm is *"provoke contract present at
serve, absent at train, multi-turn absent"*, which isolates serve-time matching
on its own. The headline then splits into three clean pairwise comparisons:

| comparison | isolates |
|---|---|
| new model **vs** run-3-published | the full combined effect (all three) |
| new model **vs** run-3-**re-served** | multi-turn training + train-time `provoke`, **net of** serve-time matching |
| run-3-re-served **vs** run-3-published | ⭐ **serve-time contract-matching alone** |

⭐ **The third row is the one that tests the hypothesis this whole corpus rests
on** — that some of the raw-arena degeneration was train/serve mismatch rather
than model incapacity. Without this arm that assumption stays untested and the
degeneration-motivation for the corpus stays partly confounded.

⚠️ **ON RECORD: the "no" was nearly the assumed default and would have been
wrong.** It costs one extra inference pass on a box that is already up — no
second rental — and it converts a three-way confound in the headline into three
clean comparisons, one of which tests a load-bearing premise.

## The box plan, amended

Four arms, one rental: **new model interacting** · **new model vs frozen partner**
(the yoked control, truncated identically) · **run 3 re-served** under the
provocation · and **run-3-published**, read from prior results rather than re-run.
Plus the RULING 15 depth-3 temperature re-derivation on the same box.

`Q1` takes `baseline_counts` from **run-3-re-served**, not run-3-published, so the
CLEAN POSITIVE branch attributes to *training + train-time contract* and never to
serve-time matching. Run-3-published stays in the report as the combined-effect
figure, labelled as such.
