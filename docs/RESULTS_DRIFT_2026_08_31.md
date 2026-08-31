# THE DRIFT RUN — verdict: UNDERPOWERED, and the control is what proves it

Run: 105 transcripts (12 pairs × 7 replicates + 7 self-pairs × 3), 80 turns,
`force:ka`, injections OFF, against frozen cold table `84c2a1b5…`.
Analysis: `tools/act2_drift.py` · red-proof `tests/test_drift_estimand.py`
Raw: `runs/act2/drift/drift_results.json`

## The number

```
mean delta = W2(LIVE) − W2(YOKED) = +0.0803
95% CI (clustered on ADAPTER, 7 adapters, 12 pairs) = [−0.2856, +0.4637]
pairs converging: 6 of 12
```

Six converge, six diverge, the interval covers zero comfortably, and the sign of
the mean is *positive* — nominally away from coupling.

## ⛔⛔ This is NOT the Borges anti-inevitability answer

The pre-registration said `LIVE ≈ YOKED` may be read as a null **only** if the
interval also excludes an effect worth having. It does not:

- CI half-width **0.375** = **32% of the median cold-table separation** between
  two speakers (median W2 1.1878). A coupling effect a third the size of the
  typical distance between two Tlön speakers would sit comfortably inside this
  interval, undetected.

So σ_cp remains **unmeasured**. The run did not find "no coupling"; it found
that this apparatus cannot yet see coupling.

## ⭐⭐ The self-pair control is the finding

Identical speakers **cannot** converge — that is a fact about the world, not a
hypothesis. So every non-zero delta in the control arm is manufactured by
estimation noise, and the control tells us how big that manufacturing gets:

| | sd of pair deltas | min | max |
|---|---|---|---|
| **self-pair control** (cannot converge) | 0.4412 | **−0.8266** | +0.5364 |
| real pairs | 0.3988 | −0.6114 | +0.7999 |

**`s20621` talking to itself produced delta = −0.827** — a larger apparent
convergence than any real pair achieved (best: `s20620|s20621` at −0.611).

⭐ Had this run shipped without the control arm, `s20620|s20621` at −0.611 with
five other converging pairs would have looked like a coupling finding. The
control proves that magnitude is reachable by pure noise from a source where
convergence is impossible. **The control is the reason no claim is being made,
and it cost 21 of the 105 transcripts.**

⚠️ CAVEAT, stated because it cuts against the comparison above: the control ran
at **3** replicates and the real pairs at **7**, so the two sds are not
like-for-like. Matched at n=3 by subsampling the real pairs 200 times, real sd
is **0.5389** against the control's 0.4412, exceeding it in 82% of subsamples.
Real pairs are genuinely somewhat more variable than the impossible-convergence
control — but that is pair-to-pair *heterogeneity*, which the cold table already
established, not evidence of coupling.

## Why it is underpowered, and what would fix it

Fitting `sd(n)² = h² + k²/n` on the observed pair-delta sds
(n=3 → 0.5426, n=5 → 0.4480, n=7 → 0.3988; two-point solve, indicative only):

```
genuine pair-to-pair heterogeneity   h        = 0.2397
W2 estimation noise at n=7           k/√7     = 0.3187      ← LARGER
```

**At 7 replicates the estimation noise exceeds the real between-pair signal.**
Projected sd: n=14 → 0.3290, n=28 → 0.2878, n=56 → 0.2648, asymptote 0.2397.

⛔ But replicates alone will not rescue it. The unit of independence is the
**adapter**, and there are only 7, capping the design at 21 distinct pairs.
Quadrupling replicates to 28 shrinks the CI half-width only to roughly 0.27 —
still ~23% of the median speaker separation. **The experiment is
adapter-limited, not replicate-limited.** Any serious next attempt needs more
independently-trained speakers first, and more replicates second.

⭐ Per [unit_of_independence]: this is the sixth time the unit has moved in this
arc, and it moved for the same reason as always — sizing was done against what
the run re-rolls (sampling noise) rather than what the estimand generalises over
(the speakers).

## What is nevertheless established

1. The harness is sound and proven so at run time: **0 of 105** transcripts
   failed the both-adapters-spoke-and-alternated guard; all three arms balanced
   to within 1 turn of 8400.
2. The estimand is red-proofed. The sign convention is asserted in both
   directions and mutation-tested (flipping the subtraction fails 2 tests).
3. The frozen ruler held: cold table content sha recomputes to `84c2a1b5…`.
4. Location vs spread: the mean shift decomposes as location **+0.3957**,
   spread **−0.0600** — what movement there is sits in the speakers' locations,
   not in their fuzz.

## ⛔ A guard that was not a guard

`pipeline_drift.sh` step `cold_pin` printed the file sha (`51e50026…`) beside
the frozen reference (`84c2a1b5…`) and **never compared them**. They differ by
construction — the stored sha is of the content *before* the sha field is
embedded — so it printed an apparent mismatch and continued. The fact it was
meant to establish is true (verified independently post-hoc), but the check was
decorative and was wrongly reported as a gate that passed.
Fix: compare the *content* sha, and `exit 1` on mismatch.
