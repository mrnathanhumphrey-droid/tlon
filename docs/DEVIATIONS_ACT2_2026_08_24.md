# DEVIATIONS — ACT 2 harness against PREREG `20620b7c`

⛔ **THE LOCKED PREREG BODY IS NEVER REWRITTEN.** Every under-specification found
while building, and every place the harness does something the prereg's literal
text does not say, is recorded here with its reason. Nothing below weakens a
falsifier; D2 supplements one and says so.

**Status at close of step 1 (harness):** 780 tests · red-proof **12/12 mutations
CAUGHT** · prereg `20620b7c` VERIFIED unchanged · **$0.00** (synthetic speakers,
no network).

---

## D1 — the two frozen partners must be DIFFERENT transcripts

**§4 says** "a pre-recorded, non-adaptive partner transcript" and does not say
whether A and B get the same one.

**They must not.** Yoked to a single shared transcript, both speakers adapt
toward one attractor and therefore toward each other. `C(control)` would rise,
`ΔC` would be biased toward zero, and the control would contain a synthetic copy
of the very convergence the interacting arm is supposed to have exclusively.
**A control that contains the treatment attributes nothing.**

**Enforced, not documented:** `arena.run` raises on identical frozen transcripts.
Red-proofed.

## D2 — F4 gets a second, paired test beside the pre-registered one

**§2 says** F4 fires if "the interacting arm's root-diversity declines by more
than 25 % from epoch 0 while the control's does not."

**Measured on a pair that falls silent together, that rule reads +0.0 % and F4
stays clear.** Epoch 0 has no emitted turns to count, so the first measurable
window is already the collapsed one and there is no decline left to see. The
rule as written can only catch a **slow** collapse; the **fast** one walks past
it — and the fast one is the dangerous one, because it produces **ΔC = +100.00
pts** and would be reported as the strongest pact in the study.

**So the pre-registered test is kept exactly as written**, and a level
comparison against the control at the same epoch is added beside it. Either
signature fires. The supplement is the paired form the rest of the design
already uses. Verified on the dry run: F4 now fires on the mutual-collapse pair
(TTR **0.200** vs control **1.000**) and stays clear on the genuine pact and on
the no-drift pair.

## D3 — the covariate is type/token over LIVE speakers only

Not a deviation but a **defect in my first implementation**, recorded because it
produced a wrong reading that looked plausible.

`distinct_roots` was stored as a **raw count** and pooled **frozen-partner
replays**. The yoked arm runs two lanes, so it pooled twice as many turns and the
control always looked twice as diverse — **F4 fired on every cell, including
STABLE, which has no drift at all.** That is the unpaired-comparison failure this
project has been bitten by five times, committed inside a covariate.

§2 already specifies "type/token over `R`". Now counted live-only and
ratio-valued, which makes the token counts match across arms exactly.

## D4 — `D_ctx` for synthetic speakers is codebook drift, not context drift

The synthetic speakers hold an explicit codebook and mutate it. A prompted LLM
has no codebook; its equivalent drift is whatever the growing context does to its
mapping. **The synthetic pass validates the INSTRUMENT, not the phenomenon**, and
no number from `tools/act2_dryrun.py` is a result about language models. Stated
here so a later reader cannot mistake the dry-run table for a finding.

## D5 — axis 4 cannot run yet, and `contrast_pair` raises rather than faking it

`lexicon_tightness` needs a separate minted, frozen, hashed lexicon per setting.
`axes.contrast_pair("lexicon_tightness")` raises instead of substituting the
product's lexicon. Until it is minted, a boundary claim across "all four axes"
is not available — §6's stopping rule requires all four, and three is not four.

## D6 — `impression` is imported from the product, not re-spelt

`tlon/act2` imports `product.compat.impression` rather than re-deriving
`utterance_id(project(s))`. Two spellings of one rule is the Ohtani-61 shape.
⛔ **Known limit:** it reads the loaded lexicon, so **axis 4 will need this
parameterised** before it can run. Recorded now rather than discovered then.

## D7 — ⛔⛔ THE COMPREHENSION READING WAS AN ARTEFACT, AND IT IS RETRACTED

**Not a deviation. A defect in the instrument, found on the first local run, and
recorded because two already-ledgered numbers are wrong.**

The 7B before-baseline printed `choose 0.0 % (0/64), 64 unanswered`. **Chance on
a four-way forced choice is 25 %, so 0 % is BELOW chance** — and a below-chance
reading is not a weak result, it is a broken one. The raw generations settle it:

```
  surface : flar ung xom fer flix soras mring kä      RAW: '[0]'
  surface : nol sil pröx ki                            RAW: '[1]'
  surface : har xun u tar kril soras mrung tesas ko    RAW: '[0]'
  surface : nol tim ung xom sim kim hul hlang ...      RAW: '[1]'
```

**The model answered every probe.** `CHOOSE` told it to "answer with the index of
the correct reading" and — alone among the three prompts — never asked for JSON.
`LocalBackend` required a `{...}` object, found none, raised, and scored all 64
as `NO_ANSWER`. **The model obeyed the instruction it was given; the harness
discarded the answer.**

**Three things this cost, in ascending order of seriousness:**

1. **A ledgered number that is not a measurement.** Ledger entries 2 and 3
   (`Qwen2.5-1.5B` and `Qwen2.5-7B-Instruct`, both `comprehension = 0.0`) are
   **RETRACTED**. Entries are never edited; the corrected 7B reading is a new
   entry and this section is what makes the old ones readable.
2. **A verdict with no branch for what happened.** The gate printed *"AT FLOOR —
   indistinguishable from guessing"*, a claim about the **model**, when the truth
   was a claim about the **harness**. Guessing would have scored higher.
3. ⛔⛔ **AMENDMENT A's gate could not come back clear.** The band is 0.35–0.95
   and the harness could only ever read 0.0. **A falsifier that cannot fire** —
   the third instance in this project, and the first one to reach a locked
   document's gate.

⛔ **THE HOSTED PRE-FLIGHT COULD NOT HAVE CAUGHT IT.** There, tool use *forced*
the schema, so the missing sentence was invisible and comprehension read 16/16 —
the ceiling result that motivated going local. **One prompt, two backends, and
only one of them could express the defect.** A pre-flight on a different backend
is not a rehearsal of the run.

**Fixed at the cause and at the symptom, both:** `CHOOSE` now states its format
like `CONVERSE` and `RENDER` always did, and `LocalBackend` reads a bare index —
**anchored at both ends, so prose is still refused**, because a tolerant parser
here would manufacture comprehension out of hedging and inflate the exact number
the amendment gates on. `unanswered` is now ledgered beside `comprehension`; it
was printed but never recorded, so the record could not distinguish a real zero
from a harness reading nothing.

**Red-proofed, 3/3 mutations applied and CAUGHT:** unanchor the index parser ⇒
prose scores; delete the format sentence ⇒ the root cause returns; remove the
unanswered branch ⇒ 0 %/64-unanswered is reported as a floor again.

⛔ **What is NOT retracted:** `speak 0.0 %` and `render 0.0 %` are real. The raw
generations are invented forms and wrong structure (`{"lexeme":"beginning",
"form":"Śart"}`, `{"impression":"thinning_crawling_wondering"}`), which fail
validation on content, not on parsing. **F-LOCAL's firing on the baseline stands.**

## D8 — ⛔⛔ THE TIER-A RUN IS **UNINFORMATIVE**, NOT A BOUNDARY FINDING

**TLON (A100 40 GB), 2026-08-25. The fine-tune completed cleanly** — 5,000 steps,
`train_loss 0.2756`, `eval_loss 0.2579`, 4,477 s at 1.117 steps/s. **The gate that
followed does not measure what it claims**, for two independent reasons. Neither
is a fact about whether Tlön's class system is learnable.

| | baseline (bf16) | after |
|---|---|---|
| speak | 0.0 % | **100.0 %** ⛔ see (2) |
| render | 0.0 % | **31.2 %** ⛔ see (1) |
| comprehension | 39.1 % | **64.1 %** ✅ the one clean number |

### (1) THE CORPUS TAUGHT A DIFFERENT SCHEMA THAN THE GATE VALIDATES

**39 of 44 render failures are one shape error.** Three spellings of "a Scene"
exist in this codebase and the corpus builder picked the wrong one:

| | edges | aspect |
|---|---|---|
| **corpus** (`canon_json`, via `act2_build_corpus.py`) | `[["nix", {…}]]` | `["sor", 2]` |
| **`PS.validate`** (the gate) | `[{"relator":…,"node":…}]` | `aspect_root` + `aspect_reps` |
| **`schema_bridge.scene_schema()`** (advertised to the model) | `relator`/`node` | `aspect_root`/`aspect_reps` |

⛔⛔ **`canon_json` IS THE CANONICAL HASHING FORM** — the representation behind the
impression digest. It was never the proposal schema. **The model reproduced its
training data faithfully and the validator rejected it.**

⛔ **AND THE ASPECT CASE FAILS SILENTLY, WHICH IS WORSE.** `validate` reads
`aspect_root`; canon-shape `aspect` is simply absent, so the aspect is **dropped
without an error**. Scenes carrying aspect but no edges therefore VALIDATE while
having lost meaning — **the 20 "successes" are contaminated too**, not merely the
44 failures. ⭐ This is the two-spellings-of-one-rule failure again ([[one_rule_all_folds]]),
committed between the trainer and the gate.

### (2) ⛔⛔ `speak = 100.0 %` IS A COLLAPSE, AND F-LOCAL CANNOT SEE IT

Twelve independent samples came back **byte-identical**:

```
{"force": "ki", "node": {"root": "san"}}      ← ×12, zero variation
```

The model found the simplest legal scene and emits it forever. It scores **64/64
because validity alone cannot distinguish a native speaker from a model saying
one legal thing on repeat.**

⭐⭐ **THIS IS A HOLE IN THE PRE-REGISTERED INSTRUMENT, NOT JUST IN THIS RUN.** The
prereg already knows this failure mode — **F4 exists precisely because
mutual collapse produces `ΔC = +100.00`, the strongest apparent pact in the dry
run, from a pair that has stopped speaking.** F-LOCAL has **no diversity guard at
all**, so a constant output attains the maximum score. The same collapse the
arena is armed against walks straight through the gate in front of it.

### VERDICT

⛔ **By the prereg's own rule — a cell that cannot show an effect is
UNINFORMATIVE, NOT A NULL — this run does not enter the record as evidence about
learnability.** F-LOCAL "fired", but on a render number produced by a
serialization mismatch and against a speak number produced by a degenerate
constant. **The recovery set is NOT triggered**: nothing here shows the class
system is hard to internalise.

**The one result that survives:** comprehension **39.1 % → 64.1 %**, cardless and
unconstrained, inside AMENDMENT A's band at both ends.

### WHAT MUST CHANGE BEFORE A RERUN IS WORTH BUYING

1. **Serialize the corpus through the proposal schema**, not `canon_json` — one
   spelling, derived from `schema_bridge`, so trainer and gate cannot diverge.
2. **Give F-LOCAL a diversity guard.** A validity rate with no distinctness term
   is satisfiable by a constant. ⛔ Write it so a constant output scores ZERO,
   not so it is merely warned about.
3. **Make the silent aspect drop an error.** A field the validator does not
   recognise must refuse, never be ignored.

## D8-CORRECTION — ⛔⛔ "COLLAPSE" WAS THE WRONG DIAGNOSIS. RETRACTED.

**D8 §(2) above called `speak 100 %` a collapse. That is WITHDRAWN.** The three
$0 diagnoses, run on the already-pulled adapter, refute it:

| diagnosis | measurement | reading |
|---|---|---|
| **A** corpus diversity | 37,410/40,000 distinct scenes · all 156 roots (min 658 / max 718) · forces exactly 8,000 each · 85 % carry edges · the "collapsed" scene appears **6 times in 40,000** | ⛔ **NOT the corpus.** The model collapsed *away* from its data, not toward it |
| **B** input-dependence | **12/12 distinct** outputs on 12 different inputs | ⛔ **NOT input-ignoring.** Output tracks input completely |
| **D** decoding | same prompt greedy **1/12** · same prompt at temp 0.8 **11/12** · different inputs greedy **12/12** | ⭐⭐ **IT WAS THE DECODER** |

⭐⭐ **THE WEIGHTS WERE NEVER COLLAPSED.** The distribution is diverse; **greedy
decoding was taking its mode.** And the probe made that inevitable:
`_rate(speaker, [None] * 64, "speak")` calls `speaker.speak((), 1)` sixty-four
times, and `speak()` builds its prompt from an empty history and a fixed string —
**a byte-identical prompt every call.** A deterministic function of a constant
input returns a constant.

⛔ **So the real defect is worse than collapse and duller: `speak 100 % (64/64)`
had an EFFECTIVE SAMPLE SIZE OF 1.** One sample, reported as 64. No retraining
would have fixed it, and a retrain launched on the collapse hypothesis would have
spent 75 minutes confirming nothing.

⚠️ **Caveat on the diagnostic run:** training was bf16 on an A100; these
diagnoses ran **4-bit** on a 16 GiB local card. At 4-bit the greedy output is
`{"force": "denied", …}` — `denied` is the *English gloss* of a force, not a
lexicon form — and validity falls to 4/12 where the bf16 run scored legally.
**Quantization degraded the model materially, so the validity rates above are NOT
comparable to the A100 run.** The distinctness counts are robust: they measure
variation, and variation is not a precision artefact.

⭐ **What this makes of the arena:** decoding temperature is now a live
pre-registration-adjacent parameter. **Greedy makes drift impossible by
construction** — a `D_ctx` measured under temperature 0 would read zero for the
same reason `speak` read 1/12. Flagged here, **not decided**.

## D11 — F-LOCAL gets a TWO-SIDED diversity guard (`tlon/act2/diversity.py`)

**§2's threshold is untouched.** The guard decides whether a sample is
**scoreable at all**, exactly as `VacuousFalsifier` does for card/constrained
runs — it does not move the pre-registered 0.90 bar.

It **reports numbers** (`distinct`, `repeat_rate`, `response_rate`,
`dependence`), because a binary pass/fail cannot be tracked against training step
and cannot distinguish the three situations above. All are **ledgered**, not
merely printed.

⛔⛔ **AND IT IS TWO-SIDED, BECAUSE BOTH ENDS ARE DEGENERATE:**

    a CONSTANT speaker       -> 1 distinct   REFUSED (collapse)
    a UNIFORM-RANDOM speaker -> N distinct   REFUSED (noise)
    a NATIVE speaker         -> diverse AND INPUT-DEPENDENT

**Raw diversity is not the target.** A model emitting uniformly random legal
scenes maxes any naive distinctness check while being no more native than the
broken record. The signal is **input-dependence** — different meanings give
different scenes, the same meaning gives the same scene — which is why the guard
takes *two* samples (`repeated` and `varied`) and scores their difference.

**Red-proofed at both ends:** the measured `san`×12 is refused as COLLAPSE; 12
uniform-random legal scenes are refused as NOISE; a consistent-yet-diverse
speaker scores `dependence 1.00` and passes. **The speak probe now varies its
history**, which is what the arena does anyway.

## D12 — RUN 3: the read direction added. **Speak 9.4 % → 98.4 %.**

**The corpus trained a writer and the gate tested a reader.** Run 3 adds the
missing half: `Tlön surface → Scene`, which is trainable because
`parse(render(s)) == s` is an exact identity, so every scene yields a read pair
with free ground truth. Verified exact on 2,000/2,000 sampled rows.

⛔ **WHAT WAS DELIBERATELY NOT ADDED: "given a history, what comes NEXT".** Any
legal scene may follow any other — there is no oracle, and inventing one would
teach an arbitrary continuation policy and score it as competence. F-LOCAL
measures VALIDITY, not appropriateness, so read + write is what the gate needs.

| | baseline | run 2 (write only) | **run 3 (write + read)** |
|---|---|---|---|
| speak | 0.0 % | 9.4 % | **98.4 %** (63/64) |
| render | 0.0 % | 81.2 % | **84.4 %** (54/64) |
| comprehension | 46.9 % | — | **68.0 %** (174/256) |

**Two controls make these attributable.** The **write half was byte-identical**
to run 2 (content-hash `c4194a13bc750e37`), so render's 81.2 → 84.4 (a 2-item
change on n=64, inside noise) says the read data caused **no interference**. And
**compute was unchanged** — 80,000 rows × 1 epoch is the same 5,000 steps and the
same tokens as 40,000 × 2 — so nothing here is bought with extra training.

⭐ **Diagnosis C: speak validity was 12/12 at step 1,000** and held across all six
checkpoints, against 0–1/12 everywhere in run 2. The read task is learned almost
immediately once it is present at all.

⛔ **F-LOCAL STILL FIRES, BUT THE BLOCKER HAS SWAPPED.** It is now **render at
84.4 %**, 5.6 points under the 0.90 bar, with speak clearing at 98.4 %. The 11
remaining render errors are small-class slot confusions (`L→M` ×3, `Q→A` ×2) —
the exact family the targeted-positives mechanism exists for.

## D13 — ⭐⭐ COMPREHENSION IS ESTABLISHED. The pairing was the whole story.

**Per-item outcomes are now ledgered, so McNemar is available.** The result:

| comparison | test | result |
|---|---|---|
| full battery n=256 | McNemar | 88 discordant for tuned vs 34 against, **p = 1.1 × 10⁻⁶** |
| the original 64 items | McNemar | 24 vs 3, **p = 4.9 × 10⁻⁵** |
| *the same 64 items, unpaired* | *Fisher* | *p = 0.21* |

⭐⭐ **THE SAME SIXTY-FOUR ITEMS READ p = 0.21 UNPAIRED AND p = 0.000049 PAIRED.**
The effect was there the whole time; the ledger was discarding the pairing at
**write time**, and no amount of re-analysis could recover it. **You cannot
recover pairing you did not record.**

⭐ A free reproducibility check fell out of it: the recovered 64-item subset gives
baseline **25/64 = 39.1 %**, byte-matching the historical baseline exactly.

⛔ **A RETRACTION STANDS AND IS NOW RESOLVED.** Comprehension was called "the one
clean result" after run 1, which was an over-claim — run 2 did not replicate the
significance (p=0.21), and I recorded it as *suggestive, not established*. It is
**now established**, by the correct test at adequate n. The direction was right
throughout; the confidence was not, and only the replication and the paired test
could tell those apart.

## D14 — Diagnosis C's own verdict is saturated and near-vacuous

`act2_diagnose_c.py` computes its automatic READING from `dependence`, which
**saturates at +1.00 under greedy decoding for any functioning model** — so it
prints "NEVER ROSE" regardless of what the run did. In run 3 the informative
curve was the **`valid` column** (0–1/12 → 12/12 at step 1,000), which the
verdict does not look at.

⛔ Technically true and practically useless: a metric pinned at its ceiling cannot
show a curve, which is the same shape as every other saturated-instrument failure
in this file. Recorded rather than silently relied on.

## D9 — the validator CRASHED instead of refusing, and took the run with it

`_node` guarded its own argument and `validate` guarded the proposal, but the
**edge element** was assumed to be a dict:
`(e or {}).get("relator")` → `AttributeError: 'list' object has no attribute
'get'`. **The whole 64-probe measurement died after `speak` had already scored.**

⛔ A malformed emission is a **FAILED** emission — it must be counted, not thrown.
Fixed at three sites (edge element type, non-string/unhashable forms,
non-numeric `aspect_reps`, non-string `force`), plus a catch-all in
`act2_flocal._rate` that scores an unanticipated crash as a failure **and shouts
that it is a bug rather than a model result**. 32 new tests; the property test
("no deformed proposal escapes as a non-`ProposalError`") found two crash paths
beyond the one observed.

## D10 — two of MY OWN instruments were wrong, recorded so they are not trusted

- ⛔ **The VRAM planner was wrong by 3.4×** — predicted 4.6 GiB, measured 15.5 on
  a 16 GiB card. The omitted term does not scale with parameters: it is the LM
  head, which scales with **vocabulary** (152,064 for Qwen). Now reproduces both
  measured runs to ±2.5 %; the slack factor is **labelled as fitted to two
  points**, because that is what it is.
- ⛔ **The completion watcher could never fire.** `until ls DONE FAILED` requires
  **both** sentinels to exist, and they are mutually exclusive by design —
  `ls A B` exits 2 when only one is present. A guard whose success condition is
  unreachable, in the same family as the vacuous falsifier it was watching for.
- ⛔ **The pipeline wrote `DONE` unconditionally**, so a run in which all four
  stages failed still reported "PIPELINE DONE".

---

# WHAT THE DRY RUN ESTABLISHED (instrument check, $0.00, synthetic)

`python tools/act2_dryrun.py` · battery `161b124c39d6c24d` · n=8 seed-paired ·
40 turns · MDE by exact sign-flip permutation over within-control replicates.

| synthetic pair | ΔD | ΔC | reading |
|---|---|---|---|
| stable — no drift | +0.00 | +0.00 | F2 fires, F3 fires. Correct. |
| wandering — drifts, converges with nobody | +0.00 | +0.00 | F2 fires. **Not communication-driven** — the control wandered just as far. |
| **imitating — a pact by construction** | **−5.08** | **+85.94** (p=0.0078) | ⭐⭐ **F2 FIRES. F3 DOES NOT.** |
| degenerating — collapses alone | +0.00 | +0.00 | F4 correctly silent: the control collapsed too. |
| mutual collapse — falls silent together | −13.67 | **+100.00** | **F4 FIRES.** Confabulated drift caught. |

⭐⭐ **THE IMITATING ROW IS THE FINDING ABOUT THE DESIGN.** A pair that provably
built a shared codebook shows **ΔD ≈ 0** — *negative*, in fact. Two speakers
adapting toward two different frozen partners depart from epoch 0 just as far as
two adapting toward each other; they simply depart toward different places.

**On F2 alone — the prereg's load-bearing falsifier — Act 2's cheap pass would
have reported "drift is noise" and closed the arc on a pair that had
demonstrably built a private language.** Only `C` sees it. That is PREREG §0.1,
measured rather than argued.

⛔ And the mutual-collapse row is the mirror: **ΔC = +100.00 pts**, the largest
convergence in the table, from a pair that has stopped saying anything. Without
F4 it would be the headline.

---

## D15 — ⛔⛔ D2 WAS STILL NOT ENOUGH. F4 READ CLEAR ON A TEXTBOOK COLLAPSE.

**2026-08-25.** D2 added a level-vs-control branch to F4 because the
pre-registered decline branch reads +0.0 % on a *fast* collapse. Both branches
were then run against the 40-turn exchange probe — the first real degeneration
this project has measured rather than synthesised — and **both read +0.0 %.**

```
F4 on the measured degeneration:  fired = False
  "root diversity — decline: interacting +0.0%, control +0.0%;
   final TTR: 0.125 vs control 0.125 (+0.0% shortfall) — no degeneration signature"
```

The transcript it called clear: **6 distinct utterances in 18 legal turns**, all
six sharing a byte-identical 8-token prefix.

| branch | why it could not fire |
|---|---|
| within-arm decline (pre-registered) | TTR was **already 0.125 at the FIRST window**. There was no decline left to see. |
| level vs control (D2) | the control was **equally degenerate** — 0.125 vs 0.125, shortfall +0.0 %. |

⭐⭐ **THE GENERAL LESSON, AND IT IS THE POINT OF THE ENTRY: BOTH BRANCHES ARE
RELATIVE, AND A RELATIVE MEASURE HAS NO OPINION WHEN BOTH ARMS ARE ON THE
FLOOR.** "Both arms degenerate" is not a corner case — it is the case the probe
actually returned, and it is the one the yoked design makes *most* likely, since
both arms are the same weights.

⛔ **THE SAME SHAPE ATE TWO OF THE EXCHANGE PROBE'S OWN THREE CRITERIA.** Its TTR
*decline* test read +0 % for the same reason, and its *exact*-cycle test missed
near-repetition: the six utterances differ only in reduplication counts
(`nimnimnimas` → `nimnimnimnimas`) and sibling order, so no equality check fires
and no positional check fires. **Only validity caught it — 1 of 3.**

### The supplement

`falsify.degeneracy_guard`, a third branch, passed via `interacting_surfaces`.
Optional, so no existing caller changes meaning silently — but a caller that has
the surfaces and does not pass them is choosing the blind version, and F4 now
**says so in its own detail string** rather than reporting a clean null.

⛔ **THE PRE-REGISTERED BRANCH IS UNTOUCHED.** The supplement may only ADD
firings; a test asserts a slow within-arm collapse still fires with and without
surfaces.

**Both thresholds come from the corpus null alone and never saw the
degeneration**, so neither is a threshold fitted to clear the case it catches:

| | threshold | derived from | margin on the measured event |
|---|---|---|---|
| root-TTR floor | **0.50** | corpus min **0.700** over 2,500 8-scene windows | event 0.056; **0/2,500** windows come near it |
| near-repetition | **0.75** | random corpus pairs max **0.500** over 20,000 | **153/153** transcript pairs above the corpus max |

Red-proofed both ways: fires on the real transcript (both arms), **0/200 healthy
corpus windows fire**, and fewer than 2 utterances is REFUSED rather than scored
clean. 21 tests.

⚠️ **CARRIED CAVEAT, IN THE IDENTIFIER NOT THE PROSE.**
`NEAR_REPETITION_CEILING_SINGLE_TURN_NULL` is calibrated against the single-turn
null. Utterances that genuinely *abide* should be more similar than random, so
the healthy multi-turn band is **unmeasured**. Recalibrate the moment an
abiding-chain corpus exists.

⛔⛔ **AND THE REASON THIS MATTERS BEYOND F4: σ_cp MUST NOT INHERIT THE SHAPE.**
A coupling term defined as a *change* reads 0 on a pair stuck from turn zero —
and σ_cp = 0 is defined to mean *"the two flows act on independent DOF, no
pact"*. A degenerate pair would be reported as an independent one. That is why
the guard is a standalone function and not an `if` inside F4.

---

## D16 — §8.2's named instrument was the wrong one, and the corpus said so

**2026-08-25.** §8.2 asks for *"the small-class targeted positives"*. Measured on
the corpus that trained run 3:

- per-form exposure is **already flat** — A 663 · M 663 · Q 662 · T 649 · D 670
- the four forms targeted after the hosted pre-flight (`pal` `rän` `plas` `hul`)
  account for **1 of 48** confusions at n=256; three are gone entirely

⭐⭐ **ERRORS TRACK SLOT RARITY, NOT FORM RARITY.**

| slot | occupancy | missed-slot errors |
|---|---|---|
| `root` | 100.0 % | 8 — *156 forms, fewest errors per fill* |
| `relator` | 61.1 % | 0 |
| `orient` | 30.9 % | 2 |
| `modal` | 6.4 % | 11 |
| `tense` | 5.1 % | 3 |
| **`aspect_root`** | **3.9 %** | **16** — the biggest hole |
| `quant` | 3.9 % | 5 |
| `degree` | 3.9 % | 2 |

**The model has seen every A-form 663 times and still has not learned which slot
is an A-slot**, because it has only seen one filled once every 26 nodes. And the
rarity is not accidental: `_decoration_p` sets a class's occupancy to
`len(class)/len(R)` *precisely so that per-form exposure evens out*. The
balancing worked, and it optimised away the thing that was missing.

⇒ **`slot_floor`** (0.30, taken from `orient`'s 30.9 %-and-2-errors and
`relator`'s 61.1 %-and-0) decouples the two: the round-robin keeps per-form
exposure balanced, the slot gets exercised often enough to be learnable.

⇒ **`contrastive_pairs`** — the claim that targeted positives are *"the only form
a contrastive signal can take in supervised fine-tuning"* is true of a *negative*
and false of a **pair**. Two legal scenes differing in exactly one slot put the
competing readings side by side:

```
nol mlang ko        oft, it dreams (wondering)
mlang testesas ko   it dreams, again and again (×2) (wondering)
```

Same root, same force; the only difference is whether repetition is a **Q** or an
**A** — which is exactly the `nol`-in-the-aspect-slot error, taught as two
correct sentences rather than as an error string.

⛔ **THE HAND-KEPT LIST ROTTED AND NOTHING NOTICED.** `CONFUSED = {pal, rän,
plas, hul}` was mined from the hosted pre-flight and was still being boosted
three runs later, spending itself on solved problems while `nol` `nem` `xom`
`sen` went untargeted. `--from-ledger` mines the newest run instead; the frozen
list survives only as `--stale-list`, an ablation that reproduces run 3's corpus
exactly (verified: 102,842 nodes and all five per-form min/max pairs identical).

⚠️ **OPEN, NOT RESOLVED:** `aspect_root` is an outlier *even among* the rare
slots — 16 errors against `quant`'s 5 at identical occupancy. Two candidates and
no measurement separating them: aspect is the only two-field slot
(`aspect_root` + `aspect_reps`) and the only one whose surface is a
reduplication rather than the bare morpheme; and Q/A collide semantically in
English (*oft* vs *habitual*).

⛔ **"HOLD COMPUTE CONSTANT" MEANS TOKENS, NOT ROWS**, and the two come apart
here: flooring occupancy lengthens every scene and contrastive pairs add rows.
The builder now prints the token total so `--n` can be trimmed to match run 3's
budget — otherwise a render improvement is confounded with a longer run.

---

## D17 — ⛔⛔ RUN 4: THE FIX WORKED ON ITS TARGET AND THE ERRORS MOVED

**2026-08-25.** The §8.2 corrected corpus (slot_floor 0.30 + contrastive minimal
pairs), tokens held to **−0.13 %**, battery `8d21aa635d5729fd` identical, greedy,
same hardware, baseline re-verified at **25/64 = 39.1 %** three times on the box.

| | run 3 | run 4 | Δ |
|---|---|---|---|
| render | 82.0 % (210/256) | **81.6 %** (209/256) | **−1 item** |
| speak | 97.3 % (249/256) | **76.2 %** (195/256) | **−54 items** |
| comprehension | 71.1 % (182/256) | **60.2 %** (154/256) | **−28 items** |

**F-LOCAL FIRED.** The gate is not cleared and the model is not arena-ready.

### ⭐⭐ THE FINDING: THE ERRORS DID NOT DISAPPEAR, THEY RELOCATED

| slot group | run 3 | run 4 | Δ |
|---|---|---|---|
| **FLOORED** (aspect/modal/quant/tense/degree) | 37 | **26** | **−11** |
| **UNFLOORED** (root/orient/relator/force) | 11 | **24** | **+13** |
| total | 48 | 50 | +2 |

The intervention did **exactly what it was designed to do** on the slots it
treated, and the displaced probability mass landed in the one slot it did not:

| confusion | run 3 | run 4 | |
|---|---|---|---|
| `Q→A` | 5 | **0** | ⭐ the contrastive pairs' own target — eliminated |
| `L→M` | 6 | **1** | ⭐ the second targeted boundary |
| **`M→R`** | 7 | **19** | ⛔ |
| **`R→M`** | 1 | **6** | ⛔ |

⇒ **Raising modifier occupancy 3.9 % → 29.9 % raised the model's PRIOR on
modifier forms, and it now spends that prior in the ROOT slot** — the one slot
that is 100 % occupied, was never floored, and therefore always available to be
wrong in. The M/R boundary went **8 → 25**. Net render change: **one item.**

### ⭐ THE PRE-REGISTERED aspect_root TEST — `PREREG_ASPECT_ROOT_MECHANISM`

**Count test: UNDERPOWERED, exactly as pre-declared.** `k` = 0.286 from the
held-out fit slots ⇒ predicted 11.4, observed **11**, z = **−0.09**. This is the
instrument declining to answer, **not** "the mechanisms are the same".

**Composition test — the observable the prereg named as informative at low N —
FIRED:**

| | run 3 | run 4 | |
|---|---|---|---|
| non-Q real sources into A | 10 | 7 | **−30.0 %** (dose-response predicted −28.6 %) |
| **`Q→A`** | 5 | **0** | **−100 %**, Poisson p = **0.028** |

Everything except Q fell at exactly the occupancy dose-response; **Q→A vanished.**
That is the H-COLLIDE signature, pre-declared before the data, and the
preferential-targeting confound was ruled out in advance (modal received **21**
units of contrastive attention to aspect's **16**).
⛔ **One pre-declared cell at small n. SUGGESTIVE, NOT ESTABLISHED.**
⚠️ H-REDUP is **not** refuted: invented forms in the aspect slot went **1 → 4**,
and they are reduplication fragments (`xas`, `un`, `sas`, `melmel`).

### ⛔⛔ THE SPEAK COLLAPSE IS UNDIAGNOSED, AND THE HARNESS IS WHY

**60 of 61 speak failures are `no parseable JSON`** — only 1 is a class error.
This is not a class-discipline failure at all.

Two hypotheses were formed and **both refuted against the data**:

1. *"denser output ⇒ conjunctive validity penalty"* — **REFUTED.** Modifier slots
   per node in failed render proposals: **1.38 (run 3) vs 1.39 (run 4)**.
2. *"targets outgrew `max_new_tokens=220`"* — **REFUTED.** Longest target is
   **163** tokens; **0.00 %** of either corpus exceeds the cap.

⛔⛔ **AND THE THIRD ATTEMPT HIT AN INSTRUMENT WALL: `act2_flocal._rate` STORES
`proposal: null` AND DISCARDS THE RAW GENERATION WHEN PARSING FAILS.** The
failure mode that accounts for **98 % of the speak regression** is the one the
ledger records the least about. ⭐ This is the project's own rule —
*dump the raw output before believing a number* — violated by the harness at
exactly the point it matters. **Fix before any re-run: record the raw text on
parse failure.** Until then the speak collapse has no diagnosis, and none should
be invented.

### ⚠️ DIAGNOSTIC C's VERDICT IS OVER-READING NOISE AT n=12

Curve (valid/12): **9, 12, 12, 9, 12, 7, 10, 10**. The tool reports
*"OVERTRAINED — rose to 100 % at step 1000, fell to 83 %."*

⛔ **NOT SUPPORTED.** Binomial sd at p≈0.84, n=12 is **1.27**; the observed
scatter is 1.81. The series is consistent with noise around a flat ~84 % and is
not monotone in either direction. This is the SAME shape HARDEN 2 fixed one level
up — a verdict keyed to a metric that cannot resolve the difference it reports.

### ⛔ MY OWN ERRORS THIS RUN, RECORDED

- **I did not pull the checkpoints.** Diagnostic C exists to identify a better
  checkpoint; I then discarded the 7.4 GB of checkpoints it evaluates to save
  ~$0.25 of meter, and terminated. If an earlier checkpoint is better, **that is
  now unrecoverable without retraining.** Running the diagnostic and throwing
  away its subject was a mistake, not a trade-off.
- **I claimed invented forms were "a new category not in run 3 at all."** Wrong:
  run 3 had **3**, run 4 has **10**. I read run 4's printed summary against my
  memory of run 3's instead of against run 3's ledger.
- **I asserted numpy 1.21.5 "worked"** in `requirements-lambda.txt` when it had
  merely never been exercised — the gate path never imports the collator.

### COST

**~3.05 h × $1.99 = ≈ $6.1**, of which ~45 min was four environment failures
(Pillow, jinja2, numpy, plus a relaunch). Act 2 total **≈ $29**.
**The $1,500 contingency is still untouched.** Instance TERMINATED, verified.
