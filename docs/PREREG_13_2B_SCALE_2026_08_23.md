# PREREG 13.2B — the scale-confound fix, and the re-run it licenses

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `d70b3a4f` (sha256[:8] of draft body at lock, 2026-08-24T02:31Z)
- **Date:** 2026-08-23
- **Supersedes nothing.** PREREG `4ad552d4` stands unedited; this adds the one
  change its Part A could not have anticipated, and re-specifies the read.
- **Read with:** `docs/VERDICT_13_2_PART_A_2026_08_23.md`,
  `docs/DEVIATIONS_13_2_2026_08_23.md` (D16–D19),
  `docs/PROPOSAL_13_2_CONSISTENCY_INVARIANT.md` (the gate, approved).

---

## 0 · Why this exists — two measured facts, neither of them a hypothesis

**(1) Entropy is not the mechanism.** The Fix-1 sweep found metric-arm headroom
of **exactly 0.00 at every coefficient from 0.01 to 1.00** — a 100× range — with
M pinned at chance (~34.5 %). On the *same architecture* with one-hot
coordinates, headroom runs **40.23 → 61.24 pts** across that grid. Entropy is a
*per-referent* regulariser: it flattens each referent's distribution without
making distributions **differ between** referents, and between-referent
separation is the whole problem.

⛔ The pre-registered criterion also selected the **incumbent 0.01, i.e. no
change**, because it calibrates on the control arm and *the control arm was
never broken*. Firing the 2×2 on it would have reproduced Part A exactly.

**(2) The arms were unmatched in input scale, on the axis the 2×2 measures.**

| arm | dim | mean inter-referent L2 (raw) |
|---|---|---|
| lyric (metric) | 3 | **2.91** |
| random (categorical) | 24 | **24.04** |

**8.3×.** The one-hot scale (17) was chosen to match *mean normalised residue
distance for R* (D7) — a quantity that at λ=0 **is not in the reward at all** —
while the same number silently set the trunk's input magnitude, which is doing
all the work in the head arm. The arms were matched on something irrelevant and
left unmatched on the one thing that mattered. **That is Code's error, and it
sits directly on the treatment axis**, so even a passing gate would not have
made the metric-vs-categorical contrast attributable.

---

## 1 · The fix — global standardisation of the head's coordinate input

Centre, then divide by the RMS inter-referent distance:

```
X ← X − mean(X);   X ← X / rms_pairwise(X)
```

Both arms then present clouds **centred at the origin with RMS pairwise distance
1**, differing only in **shape**.

**Realised (`tests/test_residue_head.py`):**

| arm | raw RMS | after: mean pairwise | min | max |
|---|---|---|---|---|
| lyric | 3.10 | **0.937** | 0.322 | 1.735 |
| random | 24.04 | **1.000** | 1.000 | 1.000 |

⇒ metric = a **graded** cloud; categorical = a **mutually equidistant simplex**.
That is the contrast the phase is about. Location and scale are not.

⛔ **A GLOBAL SCALAR, NOT PER-DIMENSION Z-SCORING.** Per-dimension
standardisation does *not* equalise inter-referent distance when the arms differ
in dimensionality — distance grows like √dim, so a 24-dim one-hot would still
sit ≈3.4× further apart than a 3-dim lattice after z-scoring. Only a global
scale on the pairwise distance closes the measured confound.

⛔ **Deterministic and derived from the referent set, never learned.** An
adaptive input scale would reintroduce the embedding-distance failure
`novelty/distance.py` exists to prevent, in a new place.

⭐ **Shape is preserved:** relative distances within an arm are unchanged up to
the single global factor (tested). The fix removes scale, not geometry.

---

## 2 · ⛔⛔ THE STOPPING CLAUSE — Wilson's condition, and it is binding

> **If the metric arm still collapses after standardisation, THAT IS THE
> FINDING. It is not a cue for another fix.**

No third fix is pre-approved. If post-standardisation `metric×head` is refused
by the ceiling gate, the result is recorded as:

> *the metric residue does not become conventionable through a generalising head
> in this architecture, and the failure is not attributable to input scale or to
> exploration pressure, both of which were tested and excluded.*

⛔ **Naming the next candidate fix in the verdict is itself a violation of this
clause.** Two fixes have now been tried; a third would make the sequence a
search for a configuration that produces the wanted answer, which is the failure
mode every guard in this project exists to prevent. Any further change requires
a new decision by Nate, made *after* the finding is written down, not instead of
writing it.

---

## 3 · The re-run

**Sweep first, both arms, seeds 101/202/303 (disjoint from Part A's 11–88).**
The control arm selects; the metric arm is diagnostic and selects nothing.
Criterion unchanged: minimum coefficient with mean headroom > **5.92 pts**
(2 × MDE) and M-rate ≥ 0.9 × the incumbent's.

⛔ **The grid is NOT widened.** `[0.01, 0.03, 0.10, 0.30, 1.00]`, as before.
Widening it after seeing a null is tuning to taste.

**Then the 2×2**: {metric, categorical} × {table, head}, **n = 8**, **λ = 0**
(R absent from the reward; `W_RESIDUE` stays nonzero so the landmine does not
re-arm), at the frozen coefficient, applied **identically** to both arms.

**The gate is the per-cell Bayes ceiling** (approved): a cell is readable iff
`headroom > MDE (2.96 pts)`; metric cells additionally require
`categorical×head` to pass. It reads what the policy *does* and encodes no
architectural assumption, so the D16 class of failure cannot recur.

**Carried confirmations, recorded before any read:** scenes-per-form 3.000 both
arms · RepetitionLog landmine (one medoid per mate; exact repeat folds at
hits=3) · unknown-as-ignorance (0 scenes without a residue) · residue log from
turn one · λ=0 table-identity bit-identical across arms.

---

## 4 · The locked read

1. **Gate passes; `metric×head` gaps AND exceeds `categorical×head`** → metric
   structure conventions better than categorical noise. The lever is live and
   **structure matters**.
2. **Gate passes; both head cells gap, equally** → the pact forms around **any
   readable residue**; metric structure adds nothing. **H2 confirmed again, H3
   falsified — a real, clean result.** ⭐ This is the outcome the whole
   discipline exists to let win if it is true: it would mean the lyric geometry
   is beautiful and *not* the thing doing the work.
3. **Gate passes on categorical; `metric×head` refused or flat** → **the
   stopping clause fires (§2).** Recorded as the finding. No third fix.
4. **`categorical×head` refused** → the head cannot read *any* residue; the 2×2
   is not measuring what it claims; stop and diagnose, interpret no metric cell.

Below-MDE anywhere ⇒ **sized, not absent**; record the effect size.

---

## 5 · Named misreport risks

1. **Reading a post-fix metric result without confirming the coefficient was
   chosen on the control and frozen.** It is; sweep seeds are disjoint.
2. **Entropy large enough to manufacture diversity read as the metric working.**
   The ceiling gate refuses it: uniform ⇒ every mate shares one distribution ⇒
   headroom 0. Collapse and over-entropy fail identically.
3. **Treating a post-standardisation collapse as "needs another fix."** §2.
4. **Reading a `metric×head` gap as evidence evocation is intersubjective.**
   Mantel's job. **D11 stands: one human geometry + one mechanical embedding,
   not two distillations.** Nobody writes "two distillers agreed."
5. **Quoting `metric×head ≈ 0` from Part A (the pre-fix run) as a result.** It
   was a collapsed optimiser and a scale confound; the cell was never readable.
6. **Part-1's 3.000 read as the lever working.** True by construction.
7. **The isolation claim quoted without its containment clause** — the 13.1
   ledger wording is the one on record.
8. **Head-vs-table difference read as a validity failure.** It is a finding: the
   architectural route costs something. The old check over-gated it; the ceiling
   gate correctly reclassifies it as data.

---

## 6 · Deliverables

Sweep artefacts for both arms + the frozen coefficient · `VERDICT_13_2_PART_A_RERUN`
with the 2×2 per cell, gate outcome per cell, the four-way classification,
**per-cell Bayes ceiling and policy classification** (the tell), and the
seed-paired co-adaptation share reported side by side, never subtracted ·
`DEVIATIONS_13_2` updated (D20 the scale confound, D21 the sweep's
calibrate-on-unbroken-control flaw) · this prereg locked before firing.

⏸ **STOP after the read.** Part B remains a separate trigger and only becomes
meaningful if the metric cells are readable and non-collapsed.
