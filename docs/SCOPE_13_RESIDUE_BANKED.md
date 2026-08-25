# SCOPE — Phase 13: the ineffable component. **BANKED, NOT STARTED.**

**Date:** 2026-08-23 · **Amended 2026-08-23** (residue source + control meaning;
see *Amendment A* at the end — read it, it changes what the control tests and
flags one claim the design cannot reach).
**Status:** ⏸ scoped, not scheduled. Nate calls it.
⛔ **No prereg is locked** — locking implies firing, and 13.2 has not been
approved to run. ⛔ **No code written.** This document is the bank.

Behind the spring courseload and six other projects. Written so a cold session
can pick it up without re-deriving anything.

---

## Why this lever and no other

Every dead lever pointed here. **Exact invertibility recovers all *expressible*
ambiguity** — that is Lever 2's death (LL(1) + exact decoder ⇒ attachment always
recoverable at any depth) and the phase-2 M-gate vacuity, the same fact twice.
So the only surviving ambiguity is the **never-expressible**: a scene component
the grammar carries meaning about but structurally cannot say.

**The governing requirement is that the residue be a metric space, not a free
categorical dimension**, and it does double duty:

- **Conventionable** (Pictionary): nearby residues get gestured at similarly, so
  a co-adapting pair can build shared convention. A free categorical residue has
  no "nearby" and is predicted empty.
- **Auditable** (the counter fix): residue-proximity is measurable, so R
  penalises residue-*distance*, not residue-*identity*.

**Conventionable and auditable are the same property from two sides.** That is
what resolves the Phase 12 fork and makes the phase buildable.

---

# ⭐ Premise checks run before banking (this is the new work)

## ✅ The auditable half is real, and cheaper than stated

`tlon/novelty/distance.py` is **already a weighted tree edit distance**, not an
exact-match counter:

```
W_ROOT 1.0 · W_ASPECT_KIND 0.40 · W_ASPECT_STEP 0.10 · W_FIELD 0.25
W_ORIENT 0.35 · W_RELATOR 0.45 · W_MISSING 1.20 · W_FORCE 0.30
```

So "R penalises residue-distance, same shape as the expressible-channel measure"
is **true as written**. It is one weight plus one term in the node cost.

⭐⭐ **And the template already exists in the same file.** `W_ASPECT_STEP = 0.10
per reduplication step` is already a **graded, ordered** term — every other field
is flat-categorical (0.25 if different). Aspect-steps is the architecture's one
existing metric-valued dimension and it is already treated as a metric.
`W_RESIDUE` is that pattern again, not a new kind of thing.

## ⛔ NEW CONSTRAINT the brief does not state: the residue metric must be IMMOVABLE

`distance.py`'s own docstring:

> *"deliberately NOT an embedding distance … scoring novelty in a learned space
> the generator is simultaneously being trained to move through would let it buy
> novelty by shifting the space rather than by having a new impression. Tree edit
> distance is exact, cheap, auditable, and immovable."*

⇒ **"A space with a metric" must mean a pre-specified, exact, immovable metric**
— integers under `|a−b|`, a fixed lattice, a fixed ring — **never a learned
embedding.** A learned residue metric reintroduces precisely the failure
`distance.py` was built to prevent, and it would do so inside the one dimension
nobody can read. **This is a hard constraint on the 13.2 build, not a preference.**

## ⛔⛔ LANDMINE — the current log would MANUFACTURE a false "empty" verdict

`RepetitionLog.observe()`:

```python
uid = utterance_id(scene)                      # blake2b over canon_json(scene)
...
if nearest is not None and (nearest.uid == uid or nd == 0.0):
    nearest.weight = ...; nearest.hits += 1; return      # folded as a repeat
```

Two scenes differing **only** in residue would collapse in **two independent
places**:

1. `utterance_id` hashes `canon_json(scene)` — which will not include a new
   residue field unless extended ⇒ **same uid**.
2. `D.normalized(scene, m.scene)` — without a residue term ⇒ **`nd == 0.0`**.

Either clause folds the second scene into the first as *"an exact canonical
repeat."* **It would not crash. It would silently erase the residue
distinction** — so the metric-residue arm would behave exactly like a no-residue
arm and 13.2 Part 2 would come back **empty for a reason that has nothing to do
with conventionability.**

⭐ **This is the highest-value thing in this document.** It is a null-manufacturing
bug of the D1 class (a dead measurement reading perfect), it sits in the arm that
is *supposed* to show the effect, and the predicted-empty control arm would look
correct — so the pair of results would look internally consistent and be wrong.

> **Both clauses must carry the residue, and a red-proof must assert that two
> residue-differing scenes produce two medoids, before 13.2 is believed.**

---

# Build order, when it is called

### 13.0 — the third category, guard-gated

- `EventNode`/`Scene` gains `residue`.
- `NodePattern` gains `residue_any`; `_PATTERN_TO_PART` gains its mapping —
  **the `ProjectionUnsound` guard forces this**, verified in Phase 12 by firing
  it. The residue must be *explicitly declared inexpressible-by-design*, never
  merely omitted.
- π's two-way split becomes three-way. **Residue is not stripped** —
  structurally unsayable is a different thing from stripped-for-measurement.
- `match.node_matches()` checks residue.
- `canon_json` **and** `distance.py` must both see it (see the landmine).

**Two red-proofs, both required:**
1. **Renders-never** — mutating residue leaves the surface byte-identical.
   Proves inexpressibility is real, not assumed. *(Phase 12 established the
   method: mutate each field and watch the surface; 7/7 currently change it.)*
2. **Guard-on-unmapped-field** — already exists and already fires.

### 13.1 — record the three restated claims BEFORE 13.2 runs

1. **Q3 = 1 → "one form per denotation-class."** Original meaning preserved
   *within* a class. **Scenes-per-form becomes the new frontier-relevant
   quantity** — the thing every previous set measured as zero.
2. **Phase 6 semantic drift → "the denotation-set contains the target."**
   Weaker, still exact as set-membership. **The isolation claim gains a
   containment clause:** structural and semantic drift remain impossible on the
   *expressible* component; the residue is the designated, contained exception,
   and 13.0's renders-never red-proof is what certifies the containment.
3. **R spans expressible-channel distance and residue-metric distance.** The
   metric requirement is what makes this coherent; a categorical residue in R
   would be free noise.

### 13.2 — two arms, prereg-locked

`referents_residue_metric.yaml` (live hypothesis) and
`referents_residue_random.yaml` (**predicted-empty control — this is what proves
the metric is the mechanism rather than the mere presence of a residue**).

- **Part 1 — frontier nonzero.** True *by construction*; a **build-correctness
  check, not a discovery.** Zero ⇒ the residue is not actually contained and the
  build is wrong. Report scenes-per-form.
- **Part 2 — conventionable or empty. THE REAL MEASUREMENT.** Naive-vs-trained
  gap on residue-distinguished pairs, against the **frozen-arm** baseline
  (Phase 5: the reference is an optimising policy that *cannot negotiate*, never
  a random one).
- **Readings:** metric gap + random none ⇒ **LEVER LIVE.** Both empty ⇒ pivot.
  **Both show a gap ⇒ the residue is not the mechanism — stop and diagnose.**
- 5-seed floor · guard on every comparison · banner on every count ·
  **selection log on, extended to log residue selection** (the Phase 10 standing
  output applied to the new dimension).

⛔ **Power note, carried from 10.0:** MDE at n=5 on the archive variance prior is
**4.40 pts**. A Part-2 gap smaller than that is UNDERPOWERED, not absent. Decide
the seed count against that number *before* running, not after.

### 13.3 — pivot, pre-named

From empty, move toward **coarser, lower-dimensional residue metrics** (easier to
build convention on) before abandoning the lever. Not built now.

---

## Named misreport risks, for the 13.2 prereg body

1. **"Part 1's nonzero frontier means the lever works."** Part 1 is true by
   construction. Part 2 is the test. *A nonzero-but-empty residue is a failure
   wearing success's numbers* — the Cosmicomics/CR lesson, where a beautiful
   property was not evidence the pact forms.
2. **Quoting the isolation claim without the residue-containment clause.**
3. **Reading the metric arm without the random control.** Uncontrolled, a gap is
   unattributable — the 8.3a paired-control lesson applied to the residue design.
4. ⭐ **NEW, from the landmine:** *"reporting Part 2 empty without first
   red-proving that two residue-differing scenes produce two medoids."* An empty
   result is uninterpretable until the log is shown to be able to tell them
   apart.

## What this unblocks if it lands

The dynamic reset test — written in Phase 8 and never run, and correctly
kill-only at n=5 — would finally have **a set with irreducible full-utterance
ambiguity**, which is the set it always needed. Conservation becomes reachable
for the first time since it was retracted.

**And if both arms come back empty, that is a strong finding, not a failure:**
*inexpressibility does not convention in this architecture* would say the pact
requires expressible carriers — which bears directly on where private
information can and cannot live in emergent communication.

---

# AMENDMENT A — residue source, and what the control actually tests

**2026-08-23.** Everything above stands. This names the residue source and
sharpens the control. Two premise checks were run before folding it in.

## The source: lyric-derived evocative geometry

Not philosophy-distillation — **that was the expressible-worldview lever and it
died at frontier zero** (CR/TAO), because worldview is sayable and the exact
decoder recovers it. The residue lever needs the opposite: **denotationally
identical, evocatively distinct.**

The mechanistic reason lyric is the register, and it is not a poetic one: in
conversational prose **denotation ≈ meaning**, so residue ≈ 0 (which is why the
garlic-bread demo is a good door and dead substrate). **In lyric, denotation
underdetermines meaning by design** — the art form is words meaning more than
they denote — so two lyrics with matching denotations gesture at different
things, and *that difference is the residue*. ⛔ **Lyric is not the source
because it feels ineffable.** That is the thematic-fit trap, named below.

**Copyright line, reaffirmed unchanged:** the metric is built from the
**geometry of what lyrics gesture at** — which evocations cluster near, which
fall far — **never from any lyric's words**. The words are the denotation:
sayable, parser-recoverable, the part we neither want nor may take. Human
doorman distills; words stay at the door. Lawful source + human distillation
both still required. The residue YAML carries no source text and the red-check
extends to the residue dimension.

⛔ **NEW SAFETY CONSTRAINT, from that:** the residue field must be **numeric or
structural — a coordinate — never free text.** A string-valued residue is a side
door through which expression could enter while every other check passes.
`expression_check.py` must assert the residue field's type, not only scan names
and notes.

## ✅ Premise check: the construction is schema-legal

Two referents **can** share a byte-identical expressible signature —
`Signature` is a frozen dataclass and equality holds; only **ids** are checked
for duplicates, never signatures. So the build shape the amendment implies is
available today: **denotationally-identical clusters differing only in residue.**
`consistent()` returns the same for both members, which *is* the irreducible
full-utterance ambiguity the lever needs. Nothing blocks it.

## ⛔⛔ Premise check: the control cannot test what the amendment says it tests

The amendment restates the random arm as testing **"is evocation
intersubjectively shared, or private-per-reader?"** — and the agent experiment
**cannot reach that question.**

**Why.** The residue metric lives in the referent YAML. Both agents face the same
environment; the speaker's residue and the listener's target come from **the same
file**. Intersubjectivity between *humans* is not a variable in the experiment —
it is **baked in by construction the moment Nate authors the metric.**

Concretely: **if evocation were 100 % private-per-reader, Nate's lyric-derived
metric would still be *a* metric** — still structured, still conventionable — and
the metric arm would still show a gap. The experiment would read *lever lives*
while the intersubjectivity claim was false.

> **What metric-vs-random actually measures: is METRIC STRUCTURE conventionable,
> versus categorical noise. That is Phase 13's real question and it is a good
> one. It is not the same proposition as "evocation is shared."**

⭐ This is the mirror of *a null is evidence only if the test could have come
back positive*: **a positive supports the stated claim only if the claim could
have been falsified**, and by this design it cannot. Same family as
`[wrong_subject]` — a gate cannot ask whether the evidence is about the question.

⭐⭐ **And it is the FOURTH instance of the pattern the amendment itself names.**
Cosmicomics (10.5 %), CR/TAO (frontier zero), lyric-felt-ineffability — and now
**the felt strength of a claim outrunning what the measurement can address.**
The amendment spotted three; this is the one it was standing inside.

> **Logged plainly, in Wilson's words, because it is the argument for the whole
> method: *"the person who names the pattern is not immune to the pattern …
> vigilance failed in the very act of preaching vigilance."***

⭐⭐⭐ **THAT IS WHY EVERY GUARD HERE IS STRUCTURAL RATHER THAN ATTENTIONAL** —
the comparison guard that refuses to subtract, the banner that raises on a wrong
count, the red-proof that must fire against a decorative stand-in, and now the
residue type assertion. **A lesson in a verdict does not hold; a lesson in the
harness does.** This is the cleanest demonstration the project has: its most
careful reader made its signature error about his own claim, inside the document
warning about that error.

### ⭐⭐ THE SHAPE, IN WILSON'S FRAMING (better than mine, adopted verbatim)

> **Intersubjectivity gates the HEADLINE, not the PHASE.**

The phase runs regardless. The Mantel result decides **which of two true things
you have earned:**

| Mantel outcome | the sentence you get |
|---|---|
| **agree above chance** | *"The private language forms around a **shared** unsayable evocative structure"* — the big claim, evocation-is-intersubjective made measurable. |
| **disagree** | *"The private language forms around a **structured** unsayable residue, here authored by one distiller"* — still real, still novel, scoped honestly. |

**Both publishable. The Mantel test tells you which sentence you have earned,
for zero compute, before the agent run spends a seed.**

⭐ **This is separation-of-instruments, one level up** — the same discipline as
the exact-invertible channel isolating pragmatic drift, and the frozen auditor
being a different family from the trained pair. **The agent run tests
conventionability; the Mantel test tests intersubjectivity; neither pretends to
test the other.**

### The fix is cheap and it protects the bigger claim rather than blocking it

**Intersubjectivity is a prior, human-level question with its own cheap
measurement, and it is not compute:**

> **Two or more people independently produce the evocative geometry over the
> same referent inventory. Measure agreement between their distance matrices
> (Mantel-shaped: rank-correlate the two, permutation null).**

- **Independent distillations agree above chance** ⇒ evocation is shared, and
  the lyric-derived metric is licensed as more than one person's taste. **Then
  the agent result carries the bigger claim.**
- **They don't agree** ⇒ the agent experiment is **still entirely valid** — it
  measures "structured residue is conventionable" — but the metric is *Nate's*,
  not humanity's, and the intersubjectivity headline is not available.

⭐ Wilson is the obvious second distiller. Two humans is a weak but real n; the
point is that it can come back negative, which the agent design cannot.

## Restated control, for the locked prereg

| arm | residue | tests |
|---|---|---|
| `referents_residue_lyric.yaml` | lyric-derived evocative geometry | is **metric structure** conventionable? |
| `referents_residue_random.yaml` | free categorical, no structure | the unstructured null |
| *(separate, human, no compute)* | two independent distillations | is **evocation shared**? |

**Named misreport risks — the amendment's, plus the one it revealed:**

5. **"Treating lyric-derived residue as conventionable because lyric feels
   ineffable."** The test is structure, not feeling. A metric arm that conventions
   no better than random means the felt-ineffability was thematic fit again.
6. ⭐ **NEW: "Reporting a metric-arm gap as evidence that evocation is
   intersubjective."** It is not — both agents were handed the same metric. That
   claim needs the two-distiller agreement measurement and cannot be inferred
   from the agent run at any effect size.

## Value in both directions, held loosely

If lyric conventions and random doesn't: **the private language forms around a
shared-but-unsayable evocative structure** — bigger than the pact alone, *and
only fully earned with the agreement measurement above.* If both are empty:
**evocation is private, or the pact requires sayable carriers** — also real, also
publishable. High-value in both directions is exactly when to hold it loosest.
