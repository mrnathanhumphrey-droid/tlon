# DEVIATIONS from PREREG 7 — LOCK `a260481e`

Recorded, never edited into the locked body.
**Status: phase 7 HALTED at the anchor stage, per the prereg's own instruction
("stop and surface it"). No KILL B verdict exists and none may be quoted.**

Run: `runs/auditor_anchors.json`, `runs/auditor_anchors.log`.

---

# FINDINGS

## D8 — the gap cannot discriminate, because the listener saturates

**Measured.** Listener 4-way accuracy is **100.0 % in every condition** — honest
at p_utter 0.25 / 0.50 / 0.75, and the planted cipher. The gap is therefore
`100 − auditor` everywhere, one term pinned, and the "ceiling" landed **1.6 pts
below** the floor.

**Cause, and it is mine.** Root-disjoint distractors were chosen so the *auditor*
had a feasible task — phase 2b.2 established it sits at chance on near-synonyms
(48.3 %). But the listener reads roots directly off the surface, so root-disjoint
candidates are eliminated trivially. **The distractor choice removed exactly the
part of the listener's job that is hard.**

**The tension may be structural, and that matters more than the bug.**
Distractors easy enough for a frozen 1.5B outsider appear to be *too* easy for a
trained listener. If that holds under test, no auditor-vs-listener gap on a
shared forced choice can work, and KILL B needs a different statistic — not a
tuned one.

**Proposed replacement (needs a call, it changes a locked method).**
Compare the **auditor rate across arms at matched withholding**, rather than
auditor-vs-listener within an arm. Both judges already see identical items, so
comparing the same judge across conditions is already controlled; the
cross-judge subtraction was only ever there to normalise task difficulty, and it
introduced a saturating term to do it. The listener rate stays in the record as
a **condition check** (M must be high) per B2 — it is required for the result to
mean anything, it is just not the discriminating statistic.

## D9 — the planted cipher is not a valid ceiling for THIS detector

The auditor's job, per `tlon/listener/auditor.py`, is to notice **a gloss that
says nothing descriptive**. The planted code sits in `aspect_root`, alongside a
fully intact description — and `gloss.py` renders the aspect adverb regardless.
**Nothing was removed, so there was nothing for the auditor to fail to see.**
Its rate on the planted arm (44.4 %) sits inside the honest range (42.8–48.0 %),
exactly as it should.

**A pact's function is that it lets the speaker say LESS and still be
understood.** A ceiling that leaves the description intact does not exercise
that, and cannot bound what the detector can see.

**Proposed replacement.** The ceiling must be **code plus aggressive
withholding**: plant the code in a surviving channel *and* drive p_utter low, so
the gloss is genuinely sparse while the listener still resolves via the code.
That is the pathology KILL B exists to catch, and only then is the ceiling a
ceiling.

## D10 — ⛔ RETRACTED. See VERDICT_7. The inference below was WRONG.

**Retraction:** the reading "the auditor was never using the withheld content /
reads the head predication and little else" is **false**. A PAIRED test on
identical items (full gloss vs head-only) shows removing dependents costs
**7.9 pts** on items that have them (42.8 % → 34.9 %). The auditor reads
selection content substantially.

**Why the inference failed:** the floor curve below is **UNPAIRED** — each
withholding rate is a different item set with different referents and different
ambiguity, so the effect was absorbed by between-set variation. Paired, it is 3×
larger. Same error as the phase-3 contaminated cipher control.

The original text is kept below because the retraction is the point.

### (superseded) a prior I registered came back wrong, in a useful direction

The prereg predicted the floor would sit **well below** the 43.8 % complete-scene
baseline, and that this difference would be the largest quantity in the phase.

**It is not.** Auditor accuracy on honest *partial* glosses is **46.4 / 42.8 /
48.0 %** at p_utter 0.25 / 0.50 / 0.75 — indistinguishable from the complete-scene
43.8 %, and **flat across withholding** despite ambiguity moving 15.1 % → 32.9 %.

**Reading:** honest underdetermination does not hurt the frozen auditor, which
implies **it was never using the withheld content.** It appears to resolve from
the head predication and little else. That is worth knowing independently of
KILL B: it bounds what this auditor can ever detect, and it means the
"floor is a curve" refinement — correct in principle — was unnecessary in
practice. The curve is flat.

⭐ Note this cuts *for* the instrument in one way: a judge insensitive to how much
is withheld is exactly the stable yardstick B1 asks for. It is only a problem if
it is also insensitive to a pact — which D9 means we have not yet tested.

## What did NOT fail

- **KILL B″ does not fire.** The auditor is live: 42.8–48.0 % honest against
  **25.6 % shuffled** (chance 25 %). It is reading the gloss.
- π, the four-way item construction, and the identical-choice-set discipline all
  worked as specified.

---

# RULINGS (Wilson, 2026-08-22)

## D8 — APPROVED. Direction locked before the run.

Cross-judge subtraction is dropped. **Discriminating statistic = auditor rate
across arms at matched withholding.** Both judges already see identical items, so
comparing one judge across conditions is already controlled; the subtraction only
existed to normalise task difficulty and it imported the saturating term to do it.

⛔ **The expected direction is locked now, so neither outcome can be read as
confirmation after the fact:**

> **Does the auditor score LOWER on pact-arm glosses than on honest-arm glosses
> at the same withholding level?** I.e. does the pact make the gloss less
> recoverable to an outsider than honest selection at equal sparsity.

Listener rate remains in the record as a **B2 condition check** — "the listener
actually resolves" must be true for an arm to be a pact candidate at all — but is
no longer the discriminating statistic.

## D9 — APPROVED, with a correction Wilson's version does not yet capture

Approved: the ceiling must be an **omission-pact**, and it calibrates the
detector **for omission-pacts only**.

⛔ **But "code + low p_utter" alone still yields no ceiling, for the same reason
D8 failed one level down.** At *matched* withholding, the honest arm and the
coded arm produce **equally sparse** glosses. The auditor sees the same quantity
of description in both and scores the same. Sparsity degrades the gloss on *both
sides of the comparison* and therefore cancels.

**What differentiates a pact is not HOW MUCH is dropped but WHICH content.** An
honest speaker withholding at rate *w* drops at random. A pact-driven speaker can
drop precisely the *informative* parts, because the code covers for them. At
matched *w*, those glosses are genuinely less recoverable.

**So the ceiling is code + ADVERSARIAL selection:** plant the code in a surviving
channel *and* choose the **ambiguity-maximising** subset at each size, computed
exactly with `consistent()` — the same machinery as the RSA test (P2). Maximum
description withheld per unit of withholding, listener still resolving via the
code. That is an omission-pact, and it is the shape this instrument can see.

## D11 — SCOPE: KILL B is sufficient, not necessary

**A gloss-grounded frozen auditor can only detect pacts-of-OMISSION — where the
gloss goes sparse or uninformative. It is structurally blind to
pacts-of-SUPERPOSITION, where the pact rides alongside a fully intact
description**, because nothing descriptive was removed for it to miss.

Established, not assumed: the floor is **flat at 46.4 / 42.8 / 48.0 %** across
withholding while ambiguity moves 15.1 % → 32.9 %, so this auditor was never
using withheld content; and the phase-4 planted code — which sits in
`aspect_root` beside an intact description — scored **44.4 %, inside the honest
band**. The auditor answered correctly. It was asked the wrong question.

**Our natural λ=0 pact is the superposition kind.** Therefore:

- **A fired KILL B proves a pact.**
- **A clean KILL B, on the arms where the natural pact lives, is UNINFORMATIVE.**
  It neither confirms nor rules out superposition.

⛔ **If D9's omission-ceiling fires and the natural arms come back clean, the
honest conclusion is NOT "no pact."** It is: *the natural pact is not an
omission-pact; whether it is a superposition-pact is beyond this instrument.*
The D9 ceiling proves the detector works for the pacts it can see. **It cannot
extend the detector's reach to the pacts it cannot.**

**Hand-off:** the superposition question — where our actual finding lives —
needs a different instrument, and both candidates are already Phase 8. The
**RSA α-frontier** (does the listener resolve better than an RSA-optimal
speaker's gloss should permit?) and the **dynamic reset test** (does resolution
collapse and re-climb on whole-pool reset, proving it lived in the co-adaptation
rather than in the description?). Phase 7 hands off rather than completing
itself. That is the correct decomposition; it just has to be stated so nobody
expects KILL B to answer a question it structurally cannot.

## Status

`auditor_state` remains **FAILED_TO_RUN**, not `MEASURED`. Under B2 no counter
conditioned on it may be served, and no KILL B result exists to report. Phase 8
does not proceed on a KILL B verdict, because there isn't one.

**Two proposed method changes (D8, D9) need a call before re-running, because
both alter a locked prereg.**
