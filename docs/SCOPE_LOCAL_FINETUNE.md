# SCOPE — the local fine-tune that installs the class system

- **Status:** SCOPE ONLY. **Nothing trained, no backbone chosen, $0 spent.**
- **Date:** 2026-08-24
- **Carries forward:** `docs/FINDINGS_ACT2_F1_2026_08_24.md` (established)
- **Touches:** nothing in PREREG `20620b7c`, which stays VERIFIED unchanged. The
  one prereg change this implies (§6 below) is an **amendment blocked on the
  fine-tune existing**, and is not drafted here.

---

## 1 · The target, made precise from the failure

The hosted pre-flight said exactly what is missing, and it is not vocabulary.

**Measured on the machine:** the lexicon is **233 distinct surface forms across 9
classes**, and the partition is **surface-disjoint — 0 forms belong to more than
one class**. That is what makes the target well-posed: class membership is a
*function* of the form, learnable exactly, with no ambiguous cases to hedge.

| class | forms | | class | forms |
|---|---|---|---|---|
| R roots | 156 | | D degrees | 6 |
| O orientations | 24 | | Q quants | 6 |
| L relators | 12 | | A aspects | 6 |
| M evidentials | 10 | | F forces | 5 |
| T tenses | 8 | | **total** | **233** |

⭐ **R IS 67 % OF THE FORMS AND CAUSED NONE OF THE FAILURES.** All four recorded
render failures were misassignments *involving the small classes* — `pal` and
`rän` (both R) shoved into **A** (6 forms), `plas` and `hul` (both O) used as
**root** and **relator**. The model reaches for a form it knows and puts it in
the wrong box, and it does so where the boxes are smallest.

**What the fine-tune installs — two things, both structural:**

1. **The class partition.** Which of the 9 boxes each of the 233 forms lives in.
2. **The slot-order discipline**, read off the parser (`grammar/parse.py`), which
   is the real generative rule and is not stated anywhere in the card:

       predication := Q? T? M? O{0,2} (L predication){0,3} R A? D?
       utterance   := predication F

   Bounds, from `C.constraints()`: `MAX_DEPTH 3` · `MAX_CLAUSES_PER_PRED 3` ·
   `MAX_ORIENT_PER_PRED 2` · `MAX_ASPECT_REPS 4` · morphs in `[2, 24]`.

### ⛔⛔ THE SUCCESS BAR: ≥ 0.90 FIRST-ATTEMPT LEGAL RENDER, **WITHOUT THE CARD**

The no-card condition is the whole point and is not negotiable. Measured: the
card is **4,922 chars ≈ 1,230 tokens**, and removing it takes the system prompt
to **9 %** of its current size. A model that still needs it has internalised
nothing — it is looking the language up.

⭐ Two secondary bars, recorded now so they are not invented later:
`speak` ≥ 0.90 no-card (it is already 1.00 *with* the card, so this is a
retention check, not a stretch), and **comprehension no-card above chance**, which
is what makes §6's rebuilt observable possible at all.

---

## 2 · The corpus, and its free correctness oracle

### The oracle is exact and already built
`Scene → gloss()` is deterministic; `parse`/`render`/π give an exact equality
test. So every training pair carries its own ground truth:

    sample Scene s → gloss(s) → model → Scene′ → assert impression(s′) == impression(s)

No judge, no human labelling, no approximation.

### Generation is effectively free — **measured, 33,711 pairs/sec, 100 % accept**
A 100,000-pair corpus takes **≈ 3 seconds** to generate. Corpus size is not a
constraint on this project; corpus *composition* is the only real decision.

### Composition — three sources
1. **Sampled gloss pairs** (unbounded). The structural backbone.
2. **The accepted-pairs log** (`runs/corpus/accepted.jsonl`, currently **5
   rows**) — real arbitrary-English → Scene pairs. Tiny, but it is the only
   source of the *paraphrase* distribution; the gloss corpus covers structure
   only. ⚠ This is also Route B's milestone corpus (2,000 distinct English);
   the two uses do not conflict.
3. ⭐⭐ **THE FAILURE LOG AS HARD NEGATIVES.** Every class confusion is a labelled
   contrastive example — *"`pal` is class R, not A"* — targeting exactly the
   partition the model gets wrong rather than adding more of what it already
   does. **This is the highest-value and smallest part of the corpus.**

   ⛔ **PREREQUISITE, AND IT IS A REAL GAP:** `tools/act2_f1.py` currently stores
   only the **top 4** refusal reasons (`reasons` is truncated in `_validity`).
   Four of eight failures were recorded. **Widen it to log every failure with the
   offending form, the slot it was put in, and its true class, before any corpus
   is built** — otherwise the negatives are a sample of a sample.

### Per-class coverage — **requirement already met, measured**
The hazard named was a corpus concentrated in the easy classes. Checked on 5,000
naively sampled pairs: **9/9 classes at 100 % form coverage** (R 156/156,
O 24/24, L 12/12, M 10/10, T 8/8, A 6/6, D 6/6, Q 6/6, F 5/5).

⛔ **BUT COVERAGE IS NOT BALANCE, AND BALANCE IS THE ONE THAT MATTERS HERE.**

### ⛔⛔ CORRECTION — THE MEASUREMENT REFUTED THE DIRECTION, AND I BUILT ON IT FIRST

The exposure gap is real and was correctly sized (**~30×**). The *direction* was
inverted, in the brief and in my first sampler, and the first sampler made things
**worse** (spread 26.8× → 28×) before the measurement caught it.

The worry was that free sampling starves the **small** classes. Measured, 5,000
freely sampled pairs, **per-form exposure**:

| class | forms | per-form exposure |
|---|---|---|
| **R** | 156 | **39** ← the starved class |
| O | 24 | 291 |
| A | 6 | 685 |
| F | 5 | 930 |

**A class with FEW forms concentrates its exposure; a class with MANY spreads it
thin.** R holds 67 % of the lexicon in one slot per node, so each root is seen
~39 times while each force is seen ~930. **The starvation runs WITH class size,
not against it** — so weighting toward the small classes spends the fine-tune on
what is already over-learned.

⭐ The failures stay consistent with this and in fact *explain* better under it:
`pal`/`rän` are **R**-forms (39 exposures each) misfiled into A, and `plas`/`hul`
are **O**-forms put in R and L slots. The confusions are about the **thinly-seen**
forms, which are the R and O ones.

**Implemented** (`act2/corpus.py`): round-robin over the least-exposed forms of
each class, with edge-heavy trees so R gets more slots per pair. Measured on
5,000 pairs:

| | worst-form exposure | spread | within-class variance |
|---|---|---|---|
| naive | 39 | 26.8× | up to 38 |
| **balanced** | **79** | **12.7×** | **≤ 2** |

⛔ The residual 12.7× is a **structural floor, not a sampler defect**: `F` must
appear exactly once per utterance (5 forms ⇒ ~1,000 each) and `L` once per edge.
Neither can go lower without removing the slot. **The number that binds is
`worst_form_exposure`, and it doubled.** `exposure_report()` prints it, and it is
printed before training.

---

## 3 · The internalizability falsifier — GATES the drift measurement

Pre-registered here, before the fine-tune exists, so it cannot be softened after
seeing a number.

> **F-LOCAL fires if:** post-fine-tune, no-card, first-attempt legal **render**
> < **0.90**, or legal **speak** < **0.90**.

**Why it gates everything:** F1 already established that at 50 % validity the
retry loop is doing heavy work, so `D_ctx` on the production half "carries the
gate's fingerprints, not only the model's". Drift measured under heavy retry is
confounded with validity-failure and is not a measurement of the model.

**Bounded, pre-committed recovery set, in order:**
1. **More contrastive negatives** from the widened failure log (cheapest; targets
   the measured defect directly).
2. **Curriculum fine-tune** — class discipline before composition: single-class
   slot-filling → bare predications → nested clauses at depth 2–3.
3. **Bigger backbone** (Tier B in §4).

**Recover** ⇒ validity clears and drift becomes measurable.
**Boundary** ⇒ *the constraint is not internalizable at this scale* — a real
finding about the grammar's learnability, reported as one, per §6's boundary
logic. Not a failure and not a wall: a falsifier with a recovery set.

### ⛔⛔ ONE TRAP THAT WOULD MAKE F-LOCAL VACUOUS
A local backend can do **grammar-constrained decoding** (GBNF / guided
generation), which would make invalid emission *structurally impossible* and
drive validity to 100 % **by construction**. F-LOCAL could then never fire and
would be measuring the sampler, not the model.

⇒ **F-LOCAL MUST BE MEASURED WITH UNCONSTRAINED DECODING.** Constrained decoding
may be used for arena runs *after* F-LOCAL is measured, and if it is, that must
be recorded on every affected run — it changes what the retry covariates mean and
therefore what F4 is reading.

---

## 4 · Backbone options, costed against **measured** hardware

**Owned hardware, read from the machine:** `NVIDIA GeForce RTX 5070 Ti,
15.9 GiB`, CUDA available, torch 2.11.0+cu128.

⭐ **The task is unusually cheap for three measured reasons:** training sequences
are *short* (a gloss ≈ 100 tokens + a Scene JSON ≈ 80 ⇒ **~200 tokens/example**,
where VRAM is dominated by sequence length); the card comes *out* of inference
prompts (**9 %** of the old system prompt); and both arena speakers are the
**same weights with different contexts**, so one served instance covers both.

| tier | size | QLoRA fine-tune | serve 2 contexts | verdict |
|---|---|---|---|---|
| **A** | 7–8B instruct | ~8–10 GiB | ~6–7 GiB | **fits with headroom on owned hardware** |
| **B** | 12–14B instruct | ~13–15 GiB | ~9–10 GiB | **tight but feasible** at short seq + grad checkpointing; the "bigger backbone" rung of §3's recovery ladder |
| **C** | > 14B | does not fit 15.9 GiB | — | **needs Lambda**; only if A and B both fire F-LOCAL |

**Selection criteria, in priority order:**
1. **Permissive licence (Apache-2.0 / MIT).** This is destined for a *public
   installation* — a research-only or non-commercial licence is disqualifying,
   and that is a harder constraint than any benchmark.
2. Reliable **structured/JSON output** at 7–14B — the model emits a Scene object.
3. Instruction-following at short context.

⛔ **NO SPECIFIC CHECKPOINT IS NAMED HERE, DELIBERATELY.** Backbone is Nate's
call, every time, and current licence terms and checkpoint quality need checking
at decision time rather than recalled from training data.

### The budget, corrected
Wilson predicted "hundreds of dollars, not thousands". **The measured evidence
says lower still: Tier A is very likely $0 — an overnight QLoRA on owned
hardware.** Order-of-magnitude, to be replaced by a measured pilot: a 50,000-pair
corpus at ~200 tokens is ~10M tokens per epoch; at plausible 5070 Ti QLoRA
throughput that is **hours per epoch, not days**.

⛔ **THOSE THROUGHPUT FIGURES ARE ESTIMATES AND ARE NOT LOAD-BEARING.** The
honest next action is a **$0 measured pilot**: one short QLoRA run on owned
hardware to record real tokens/sec and real peak VRAM. **The $1,500 Lambda budget
appears over-provisioned for this step** and should be held for Tier C or for
running axis settings in parallel — not spent because it exists.

---

## 5 · What runs unchanged behind `LocalBackend`

**Verified by reading the imports:** `tlon/act2/*` imports only from
`tlon.grammar`, `tlon.product` (`schema`, `compat`, `proposer.lexicon_card`),
`tlon.harness.paired`, and the standard library. **No network library is
reachable from the package, and a test enforces it.**

**Backend-agnostic — swap and go, nothing to touch:**

- `Speaker` protocol (`speak` / `render` / `choose`)
- the validity gate — `product/schema.py`, `parse(render(s)) == s`
- `arena.py` — three arms, epoch loop, covariates, the yoked control
- `observe.py` — `D`, `C`, both estimators
- `falsify.py` — F1–F5, MDE, headroom gate, Holm, verdict
- `ledger.py` — the sealed transcript
- `harness/paired.py` — the comparison guard
- `probes.py` — the battery

### ⛔ NOT backend-agnostic — three things that need touching, all small
1. **`llm.py` hardcodes the card into every prompt** (`self._card or
   lexicon_card()`). The no-card condition is the *success criterion*, so
   `LLMSpeaker` needs an explicit `card: bool` and the F-LOCAL harness must run
   with `card=False`. **Leaving this un-parameterised would silently measure the
   card-reading model and report it as internalised.**
2. **The local backend must support schema-constrained generation** to return a
   Scene object at all — subject to §3's trap: unconstrained for F-LOCAL.
3. **`history_limit = 60`** was chosen when the card ate the context. With the
   card gone there is room for a longer window; **changing it changes what
   `D_ctx` can see** (see `llm.py`'s own note), so it is a pre-registration-
   adjacent decision, not a tuning knob.

---

## 6 · The comprehension observable — amendment PENDING WEIGHTS, not drafted

§8 fired: comprehension is at ceiling because with the card, decoding is a
lookup, and **a lookup cannot drift**. §1 locks the two halves at equal weight
and forbids dropping one, so this is a change to a pre-registered observable and
needs a **formal amendment**, not an edit.

⛔ **NOT DRAFTED HERE, AND THAT IS THE POINT: IT IS BLOCKED ON THE FINE-TUNE
EXISTING.** Comprehension drift is only well-posed once comprehension is a
weight-property. Writing the amendment now would be specifying an observable for
a model that does not exist.

**What the rebuilt observable must satisfy, sketched only:**
- the model decodes **from weights, not from a card in context** — otherwise the
  ceiling returns unchanged;
- epoch-0 accuracy lands **between chance (25 %) and ceiling (95 %)**, or §8
  closes the gate from one side or the other;
- it measures *"what does this model take this surface to mean"* as a property of
  the model, and it must be able to move.

---

## ⚠ ONE FINDING THAT CHANGES WHAT THE FINE-TUNE DELIVERS

**A fine-tune-once-then-run-the-arena design still measures `D_ctx`, not `D_w`.**

PREREG §0.2 defines `D_w` as "weight-level, post-fine-tune". Those are two
different readings and the difference matters:

- **"drift of a post-fine-tune model"** — fine-tune once, freeze, run the arena.
  The weights do not change during the conversation, so whatever drifts is still
  the *context*. This is what §4 above scopes.
- **"drift IN the weights"** — the models updating on their own exchanges, which
  needs **online/continual fine-tuning inside the arena loop**. That is a
  different and materially larger build than anything scoped here.

⇒ **The fine-tune's real deliverable is not `D_w`.** It is that the mapping moves
into the weights, which (a) removes the gate's fingerprints from the production
half and (b) **makes the comprehension half well-posed for the first time**. Both
are necessary before any drift number means what it says — and neither is
weight-level drift.

**This needs Nate's ruling before the amendment is drafted**, because it decides
whether Act 2's headline claim is about in-context convention formation in models
that *know* the language, or about weights changing under conversation. The first
is scoped and cheap. The second is a different project.

---

# RULED 2026-08-24 — and what is built

⭐⭐ **ACT 2 IS `D_ctx`** — in-context convention between native-Tlön models, the
LLM-scale replication of H2. `D_w` is **parked as a separate project, named not
buried**, with its reopening condition: an arena that can take gradient steps
between turns without the run becoming a study of training instability.

**Built and red-proofed since this scope was written (12/12 mutations caught):**

| ruling | mechanised as |
|---|---|
| F-LOCAL measured **unconstrained** | `falsify.f_local` **RAISES** `VacuousFalsifier` on `constrained_decoding=True` **or** `card=True`. Refused, not warned. |
| card **parameterised out** | `LLMSpeaker(card=False)`, wired through all three tasks; `act2_f1.py --no-card` |
| refusal log **widened** | `negatives.class_errors` walks the PROPOSAL — every error, with form, slot and true class. Not a top-N of prose messages. |
| **failure-weighted / balanced** corpus | `corpus.build(balanced=True)`; worst-form exposure **39 → 79** |
| comprehension **amendment** | `docs/AMENDMENT_A_ACT2_COMPREHENSION_2026_08_24.md`, LOCKED `8c010702` |

**Still open, all Nate's:**
1. **Backbone tier** (A: 7–8B, likely $0 on owned hardware · B: 12–14B · C: Lambda).
2. Whether to run the **$0 measured pilot** — one short QLoRA on the 5070 Ti for
   real tokens/sec and peak VRAM — before ruling on tier.
3. **Hold the $1,500** unless Tier C is reached. It is not to be spent because it
   exists.
