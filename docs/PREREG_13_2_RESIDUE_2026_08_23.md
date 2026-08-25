# PREREG 13.2 — is the residue conventionable, through which route, and does it build over time?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `4ad552d4` (sha256[:8] of draft body at lock, 2026-08-23T21:53Z)
- **Date:** 2026-08-23
- **Depends on:** `docs/ISOLATION_LEDGER_13_1_2026_08_23.md` (the wording to
  quote), `docs/SCOPE_13_RESIDUE_BANKED.md` + Amendment A,
  `docs/PREMISE_13_2_2026_08_23.md` (why the design is a 2×2 and not the
  original metric-vs-categorical contrast)

---

## 0 · What changed since the scope, and why this design

The original metric-vs-categorical contrast had **no differentiating mechanism**
under the existing policy class. Measured, not argued
(`tools/premise_13_2.py`): the speaker is a per-referent lookup table with one
independent row and *"nothing forcing generalisation"*; the surface is
residue-invariant so the listener never perceives residue proximity; M is hard
identity; and the free channel holds **24,500** codes, so an exact **arbitrary**
code exists in both arms with no capacity pressure. The metric's only route into
the loop was **R**, a novelty-pressure term — a confound. Held-out
generalisation could not rescue it either: an untrained referent's policy row is
all-zero and a table cannot interpolate between rows.

⇒ **The original Part-A rule 3 is void** and is not carried into this prereg.
The redesign adds a **residue-conditioned head** so the architectural claim
becomes a measured result rather than an assumption.

---

## 1 · Hypotheses, in the order they can fail

**H1 (build).** Scenes-per-form > 1 on every arm. *True by construction; a build
check, never a result.*

**H2 (core).** Inside a residue cluster the naive-vs-trained gap on the
**residue component** is nonzero — a pact forms around a distinction the
grammar structurally cannot express.

**H3 (architectural).** The metric arm gaps under **head** and the categorical
arm does not, and the difference survives R-isolation.

**H4 (temporal, Part B).** The residue gap **grows** over interaction length,
residue-specifically, and **collapses on reset** (convention) rather than
surviving it (a slowly-learned static code).

---

## 2 · Design

**Arms.** `referents_residue_lyric.yaml` (metric: lyric-derived evocative
geometry, coordinates in a 2-D integer lattice 0..4, distilled by a human, words
left at the door) and `referents_residue_random.yaml` (categorical: one-hot, so
every pair of distinct residues is exactly equidistant).

**Parameterisations.** `table` = the existing per-referent `ChannelPolicy`,
unchanged. `head` = a shared MLP trunk over the residue coordinate, so nearby
residues get nearby channel distributions.

**Inventory.** 8 clusters × 3 mates = 24 referents. Both arms are emitted from
**one in-memory inventory in a single run**, so the expressible scaffold is
shared byte-for-byte and cannot drift. Within a cluster the expressible
signature is byte-identical; across clusters the (head, dependent) root pair is
distinct. Listener ceiling inside a cluster is **1/3**.

**Seeds.** n = 8 (Nate's ruling). MDE **2.96 pts** on the prior sd 3.54.
⛔ The prior came from a regime where M sat at ceiling; **2.96 is a floor, not
an estimate.**

### The two anti-vacuity requirements

**(a) The falsifying cell must be able to win.** The head's trunk is an **MLP,
not a linear map**, so it retains the capacity to memorise an arbitrary
per-residue code. If the pair trains to an arbitrary code anyway, metric and
categorical gap identically **under head** and H3 is **false**. That outcome is
a result, not a bug to debug until the difference appears. Certified by
`test_the_head_CAN_memorise_an_arbitrary_code` — a linear trunk would have made
the falsifier unreachable and the 2×2 self-confirming.

**(b) R-isolation is λ = 0, and it is exact.** `reward = M + λ·(1 − novelty_cost)`,
so at λ=0 R is not in the reward and the confound route is closed by
construction. λ=1 cells then **measure** R's contribution.
⛔ **Setting `W_RESIDUE = 0` would NOT have worked:** it re-arms the
RepetitionLog landmine (`nd == 0.0` folds cluster-mates into one medoid), so the
isolation would have manufactured the very null it was meant to exclude.

### Measurement

Every eval utterance yields two accuracies **over identical items**:
*expressible* = argmax over the 8 cluster scores; *residue* = argmax over the 3
mates **of the true cluster**. Restricting to the true cluster (rather than
conditioning on the cluster having been predicted correctly) is what keeps the
item sets identical — conditioning would make the item set depend on the
listener being compared, which is the unpaired comparison in its phase-7
costume. Gap = co-adapted − naive judge, through `paired_delta`.

⛔ **Cross-cell comparisons are NOT paired and will not be pretended to be.**
Different arms and parameterisations emit different utterances, so no item-level
pairing exists; they go through `side_by_side()` plus a seed-level Welch
contrast.

---

## 3 · ⛔ The expressible control is at CEILING, measured before locking

`co_expressible == naive_expressible == 1.0000` on **8/8** dry-run cells. The
signature core is always fully uttered and exactly parseable, so cluster
identification is at ceiling for both listeners from step 0.

⇒ **The specified residue-vs-expressible paired growth control is a comparison
against a flat line and cannot adjudicate.** "Residue grows faster than
expressible" would be trivially true. A control that cannot come back positive
is not a control.

**The frozen-listener arm carries that role instead.** `train_listener=False`
makes co-adaptation impossible while the generator still shifts its distribution
to be understood, so it separates *a pact formed* from *the policy concentrated
and the listener does better on a narrower distribution*. It is run for every
cell, not as a baseline for show. The expressible component is still reported,
with a per-run ceiling flag, because its degeneracy is itself a finding about
the architecture.

---

## 4 · The locked read

**Part A, four-way:**

1. **Metric×head gaps, categorical×head does not, difference survives
   R-isolation** → H3 holds: the metric is conventionable through the
   generalising head, net of novelty pressure. → Part B.
2. **Metric×head and categorical×head gap identically** → **H3 FALSIFIED.** The
   head permits the metric but does not use it; conventionable metric residue
   needs a generalisation pressure the head alone does not supply. A real,
   named-in-advance result.
3. **Difference appears at λ=1 but vanishes at λ=0** → it was R. Honest null on
   the architectural claim, exactly as the premise check predicted.
4. **Any arm below the (floor) MDE** → **SIZED, NOT ABSENT.** Record the
   effect-size estimate; triggers Part B. Not a null.

**Internal consistency check, and it gates the metric cells:** one-hot into a
linear layer *is* a row lookup, so **categorical×head should land on
categorical×table**. If those two cells disagree, the 2×2 is not measuring what
it claims and no metric cell may be read.

**Part B** (triggered by a live or sized Part-A result): growth curve of the
residue gap over interaction length — shape, rate, asymptote — against the
**frozen arm** as the growth control. Then the reset discriminator: collapse on
reset → convention; survives → static code. Phase 8's five-branch classifier
applies, **none of them the default branch**, per-run trajectory visible not
averaged. Part-B n is set from Part A's *realised* sd and reported to Nate
before spending.

---

## 5 · Carried confirmations — no Part-2 number is readable without them

Re-run **per arm**, inside `tools/run_13_2.py`, not trusted from the unit tests:
a hand-built object cannot certify the pipeline that builds the real ones (that
is the build-gap lesson, banked).

- **RepetitionLog landmine, both clauses** — one medoid per mate on every
  cluster; exact repeat still folds.
- **unknown-as-ignorance** — every generated scene carries a residue; zero
  `residue=None` from the generator.
- **Residue selection logged from turn one** (`P3Stats.residues`).

---

## 6 · Named misreport risks

1. **A metric×head difference read as architectural when it vanishes under
   R-isolation.** λ=0 is primary; λ=1 measures R.
2. **Gap-identically-under-head read as a build failure rather than the
   falsifying result it is.** H3 is allowed to lose.
3. **A below-MDE Part-A gap read as absence.** Sized, triggers Part B.
4. **Residue growth read as real when the frozen arm grows too.** The frozen arm
   adjudicates; the expressible control cannot (§3).
5. **A rising curve read as a pact when it is a slowly-learned static code.**
   Only collapse-on-reset licenses "convention".
6. **Rebuild-to-same-level read as conservation without per-run trajectory.**
7. **Part 1's by-construction frontier read as the lever working.** Part 2 is
   the test.
8. **The isolation claim quoted without its containment clause.** The 13.1
   ledger wording is the one on record.
9. **A metric gap reported as evidence that evocation is intersubjective.** That
   is the Mantel test's job and is uninferable from the agent run at any effect
   size — both agents are handed the same metric.
10. **Scenes-per-form quoted from surface collisions.** The first estimator
    counted sampled surface collisions and read 1.016 because the free channel
    holds 24,500 codes; the frontier quantity is `consistent()`-based and reads
    3.000.

---

## 7 · Mantel test — headline gate, non-blocking, human, no compute

≥2 independent distillers produce the evocative geometry over the **same**
referent inventory; rank-correlate the distance matrices against a permutation
null. **Agree** → the metric is licensed as more than one person's taste and the
"evocation is shared" headline is available. **Disagree** → the agent run is
still entirely valid (it measures conventionability, route and temporal shape),
the metric is one distiller's, and the headline scopes down. Gates the
**headline**, not the phase.

---

## 8 · Deliverables

`VERDICT_13_2` (scenes-per-form; the four-way Part-A read with the R-isolated
head contribution and the effect-size estimate; Part B if triggered);
`DEVIATIONS_13_2`; the two arm YAMLs; this prereg locked before firing.

⛔ **The lyric arm ships with EMPTY SLOTS.** Its coordinates are the human
distiller's and the loader **refuses** an unfilled set — an empty `residue_any`
parses fine and simply means "no constraint", which would make `build_scene`
emit `residue=None`, fold every cluster-mate into one medoid, and manufacture a
null while the arm looked healthy. **Part A's metric cells cannot run until the
distillation lands.**
