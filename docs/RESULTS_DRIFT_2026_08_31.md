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

## ⛔⛔ CORRECTION (2026-08-31, after Nate's challenge): "identical cannot converge" is NOT arithmetic

This document originally said identical speakers cannot converge because it is
"a fact about the world, not a hypothesis." **That was wrong as stated, and the
architecture is the reason.** Speakers do not hold each other's words: A's
context is `own_chain + B's latest`, B's is `own_chain + A's latest`. Those are
different token streams from turn 1 at temperature 0.70, so two identical
adapters are **two individuated trajectories**, not one process mirrored. The
"identical ⇒ zero difference by construction" argument comes from a
shared-history system; this is a self-accumulation system.

⭐ **THE NULL SURVIVES ON A DIFFERENT ARGUMENT: EXCHANGEABILITY.** Identical
weights plus symmetric roles give `law(A) = law(B)`, and W2 compares MARGINAL
distributions. Two samples from the same law have true W2 = 0 **however wildly
the individual trajectories wander** — trajectory divergence is invisible to a
statistic that only sees marginals.

⚠️ **And the roles are NOT perfectly symmetric, which the wrong argument hid.**
In LIVE, A moves first and sees the seed while B responds to A. In YOKED, A and
B are *both* first-movers in their own arms. So LIVE carries a first-mover
asymmetry YOKED lacks. ⭐ This does **not** need to be waved through as "small":
the asymmetry is **COMMON-MODE** — every LIVE arm has it, self-pairs and real
pairs alike — so it **cancels in the self-vs-real comparison**. The self-pair is
therefore the correct *matched baseline including the first-mover offset*, not a
pure zero. Observed self-pair mean **+0.0445**, the sign the asymmetry predicts.

⛔⛔ **AND THE BIGGER CONSEQUENCE: THE SHIPPED ESTIMAND IS MARGINAL-BLIND.**
Because self-pair marginals coincide by construction, the self-pair arm could
**never** have shown coupling under W2, however strongly the two trajectories
actually converged. So the self-pair is a **marginal-distance noise floor**, NOT
a proof that coupling is impossible. This document originally used it as the
latter. That is a category error, and it means the headline answers a narrower
question than claimed: *do the marginal `force:ka` distributions converge* — not
*do the speakers form a convention*.

## ⭐⭐ The self-pair control is still the finding

Every non-zero delta in the control arm is manufactured by estimation noise
(true delta = 0 by exchangeability, plus the common-mode first-mover offset),
and the control tells us how big that manufacturing gets:

| | sd of pair deltas | min | max |
|---|---|---|---|
| **self-pair control** (marginals coincide) | 0.4412 | **−0.8266** | +0.5364 |
| real pairs | 0.3988 | −0.6114 | +0.7999 |

**`s20621` talking to itself produced delta = −0.827** — a larger apparent
convergence than any real pair achieved (best: `s20620|s20621` at −0.611).

⭐ Had this run shipped without the control arm, `s20620|s20621` at −0.611 with
five other converging pairs would have looked like a coupling finding. The
control proves that magnitude is reachable by pure noise from a source whose
true W2 is zero. **The control is the reason no claim is being made,
and it cost 21 of the 105 transcripts.**

⚠️ CAVEAT, stated because it cuts against the comparison above: the control ran
at **3** replicates and the real pairs at **7**, so the two sds are not
like-for-like. Matched at n=3 by subsampling the real pairs 200 times, real sd
is **0.5389** against the control's 0.4412, exceeding it in 82% of subsamples.
Real pairs are genuinely somewhat more variable than the zero-true-distance
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

## THE CHANNEL W2 CANNOT SEE — and it is underpowered too

Two speakers can agree *inside each shared conversation* while neither marginal
moves; W2 is blind to that, and self-accumulation is exactly the architecture
where it could happen. Statistic (`act2_drift.pairing_gain`):

    gain = mean_{i≠j} |A_i − B_j|  −  mean_i |A_i − B_i|

| | Δ gain (LIVE − YOKED) | 95% CI |
|---|---|---|
| self-pairs (n=3) | +0.0167 | [−0.0250, +0.0655] |
| real pairs (n=7) | +0.0024 | [−0.0075, +0.0130] |

⛔⛔ **DO NOT READ THAT CI AS A BOUND ON THE CONVENTION.** I first reported it as
"±0.010 in ka units ≈ 4% of a between-build sd." **Retracted — units error.**
The CI is on the *gain*, and gain is a heavily compressed function of the
convention producing it: a planted convention of sd 0.10 ka yields a gain of
only 0.0233. Calibrated at the real design (12 pairs × 7 reps, noise 0.10):

| planted convention (ka sd) | 0.04 | 0.06 | 0.08 | **0.10** |
|---|---|---|---|---|
| mean gain | 0.0036 | 0.0075 | 0.0142 | **0.0233** |
| detected? | no | no | no | **yes** |

⇒ the run could only have caught a conversation-specific convention of
**sd ≥ ~0.10 ka = 41% of a between-build sd** — *worse* than the shipped
estimand's 32%. **Both channels are underpowered.** The pairing statistic is
nonetheless validated, not inert: `tests/test_pairing_statistic.py` proves it
fires on a planted convention, responds monotonically to its size, and stays
silent on a common shift and on the speakers' starting gap.

⭐ **Temporal check** (does convergence build, as coupling should?): it does
not. Self-pair Δgain **+0.0143 → +0.0000** first half to second — it *decays*.
Real pairs +0.0026 → +0.0077. The "−0.827 is the coupling ceiling, not the
artifact floor" hypothesis was testable, tested, and is not supported.

## A LEAD, NOT A RESULT: co-movement

Both speakers moving *together* leaves the gap unchanged, so **neither** W2 nor
pairing gain sees it. Cold cancels in the LIVE−YOKED contrast, so it is clean:
**−0.0172, CI [−0.0335, +0.0004]**. It grazes zero. ⛔ It was found post-hoc
among several tests, so re-analysing this data cannot upgrade it — **it needs
its own pre-registered run.**

## ⛔⛔ STANDING RULE: COMPARE LIVE TO YOKED, NEVER TO COLD

Two false positives were caught mid-analysis, both of which read as findings:

1. **Jensen.** `gap(LIVE) − gap(COLD) = +0.0736`, CI excluding zero — computed
   as `mean|A−B|` against `|mean A − mean B|`. `E|X| ≥ |EX|` always, and the
   inflation is worst at small gaps (`s20620|t30001`: cold 0.029 → live 0.157,
   essentially all bias). Matched estimators drop it to +0.0516, and even that
   is inflated because live means use n=7 against cold's n=14.
2. **A module default.** `clouds()` fell back to the 2-D Stage-1 panel while the
   caller believed it had `force:ka`, returning "proportions" of ~4.86. Now
   raises without an explicit `panel=`.

⇒ **Only LIVE-vs-YOKED is a valid contrast** — same n, same estimator, same run.
It reads **+0.0191, CI [−0.0338, +0.0753]**, covering zero, consistent with the
shipped W2 result. No divergence-from-cold claim is licensed.

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
