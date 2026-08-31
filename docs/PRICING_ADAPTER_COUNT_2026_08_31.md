# PRICING THE DRIFT MEASUREMENT — how many speakers buy an answer

$0 calculation on data already on disk. No box, no training, no inference, and
**no claim about whether drift exists.** It prices the experiment that would
measure it.

## VERDICT: FEASIBLE — but the headline is that the diagnosis it was meant to price is NOT ESTABLISHED

**N ≈ 15–25 independently-trained adapters**, ~71–98 GPU-h total. But see §1
first: the "adapter-limited" claim this pricing exists to cost out **does not
survive its own uncertainty**, and the cheapest next move is not training
adapters at all.

## §1 ⛔⛔ h's 95% CI INCLUDES ZERO — "ADAPTER-LIMITED" IS NOT ESTABLISHED

Everything downstream rests on `h`, the irreducible speaker-to-speaker floor in
`sd(n)² = h² + k²/n`. Refitting it inside an adapter-level bootstrap:

```
h = 0.2519      95% CI [0.0000, 0.4033]
```

**The lower bound is zero.** If h = 0 there is no irreducible heterogeneity, the
sd keeps falling as `k/√n`, and the design is **replicate-limited** — more
conversations per pair would fix it and no new adapters are needed. If h = 0.40
it is strongly adapter-limited. *The data cannot tell these apart.*

⛔ So "the experiment is adapter-limited, not replicate-limited", asserted in
`RESULTS_DRIFT_2026_08_31.md` and STATE and repeated through review, is a **point
estimate reported without its interval**. It may be right. It is not established.

⭐ **CHEAPEST NEXT MOVE, and it is not more adapters:** more replicates on the
*existing 7* separates the hypotheses. h is identified by the *curvature* of
sd(n) vs 1/n, and the current fit spans only n=3…7. Extending the same 12 pairs
to n=28 costs ~36 GPU-h — a third of the N=20 design — and either pins h away
from zero (⇒ train adapters, §4 prices it) or collapses it toward zero (⇒ the
whole adapter programme is unnecessary). **Buy the diagnosis before buying the
cure.**

## §2 PRE-DECLARED THRESHOLD

Fixed before any curve was computed:

> **Δ\* = half the median cold-table separation between two speakers**
> = 0.5 × 1.1878 = **0.5939** in W2 units.

Ground: if conversation closes less than half the distance that ordinarily
separates two Tlön speakers, the effect is smaller than routine between-speaker
variation and cannot support a claim about convention formation.

## §3 ⭐ AT THAT THRESHOLD THE EXISTING RUN IS NOMINALLY POWERED — AND UNSTABLE

Observed se (cluster-bootstrap on adapters) = **0.1915** ⇒ MDE = 2.802 × se =
**0.5365 < Δ\* = 0.5939**. On its face the completed run *already had* 80% power
for a worth-having effect, which qualifies the blanket "underpowered" verdict:
it is underpowered for effects **below** Δ\*, not at it.

⛔ But that se comes from **7 clusters**. Leave-one-adapter-out:

| dropped | s20620 | s20621 | s20622 | s20623 | t30001 | t30002 | t30003 |
|---|---|---|---|---|---|---|---|
| MDE | 0.634 | 0.472 | 0.629 | 0.705 | **0.725** | 0.514 | 0.505 |
| mean δ | +0.191 | +0.137 | +0.055 | −0.006 | +0.091 | +0.026 | +0.075 |

**MDE ranges 0.472–0.725 — it straddles Δ\*.** Whether the run was powered
depends on which speaker you remove, and the point estimate swings −0.006 to
+0.191. ⇒ **The binding constraint is inference stability, not point power.**

## §4 N REQUIRED

⚠️ The variance model would not fit: the method-of-moments σ_a² came out
**negative** (−0.0268) and a fitted-component model undershot the observed se by
44%. The adapter component is **not identifiable** at 12 pairs / 7 adapters, so
N is bracketed between two bounding laws anchored on the *observed* se rather
than extrapolated from components I cannot estimate.

**MDE by N** (`*` = at or below Δ\*):

| N | pairs | adapter-limited, n=7 | n→∞ | pair-limited, n=7 | n→∞ |
|---|---|---|---|---|---|
| 7 | 21 | 0.536\* | 0.339\* | 0.405\* | 0.256\* |
| 12 | 66 | 0.410\* | 0.259\* | 0.229\* | 0.144\* |
| 15 | 105 | 0.366\* | 0.231\* | 0.181\* | 0.115\* |
| 20 | 190 | 0.317\* | 0.200\* | 0.135\* | 0.085\* |
| 30 | 435 | 0.259\* | 0.164\* | 0.089\* | 0.056\* |

Every row clears Δ\*, so **point power does not set N.** Stability does. The
leave-one-out se swing is ±23.6% at N=7 and falls as ≈1.65/N:

| tolerance on se | ±20% | ±15% | **±10%** | ±5% |
|---|---|---|---|---|
| **N required** | 9 | 11 | **17** | 33 |

⇒ **N ≈ 15–25.** Below 15 the interval still moves materially on one speaker;
beyond 25 the return is small and the cost is not.

**Replicate-limited floor** (n→∞ at fixed N): MDE 0.339 at N=7, 0.231 at N=15,
0.200 at N=20 — all below Δ\*, which is why replicates alone are not the
obstacle *if* h > 0. If h = 0 there is no floor at all.

## §5 THE CONVENTION CHANNEL SCALES BADLY

Smallest detectable conversation-specific convention (80% power; simulation):

| N | 7 | 12 | 15 | 20 | 30 | 40 |
|---|---|---|---|---|---|---|
| convention sd (ka) | 0.07 | 0.05 | 0.04 | 0.04 | 0.03 | 0.03 |
| as % of between-build sd | 29% | 20% | 16% | 16% | 12% | 12% |

It **plateaus around 0.03–0.04** because gain grows roughly as convention², so
halving the detectable gain only reduces the detectable convention by √2.
Quadrupling adapters buys about a factor of two. ⚠️ These use an 80%-power
criterion; the 0.10 figure in `RESULTS_DRIFT` used a stricter one (95% against
the observed CI half-width) — different criteria, not a changed result.

## §6 COST (measured unit costs, both from disk)

- training **1.24 GPU-h/adapter** (4,477 s, 5,000 steps, A100-40GB, from
  `DEVIATIONS_ACT2_2026_08_24.md`). ⚠️ The only training-time datapoint in the
  repo, and it is a 5,000-step run — **not verified** to be the recipe the
  s2062x/t3000x adapters used.
- inference **615 s/replicate** (51,631 s ÷ 84 real replicates, drift run).

Pairs set to ~3N, because se is adapter-driven and the complete N(N−1)/2 design
buys little for a great deal:

| N | new adapters | pairs | train h | infer h | **total h** | all-pairs h |
|---|---|---|---|---|---|---|
| 15 | 8 | 45 | 9.9 | 61.5 | **71.4** | 143 |
| 20 | 13 | 60 | 16.2 | 82.0 | **98.1** | 253 |
| 25 | 18 | 75 | 22.4 | 102.4 | **124.8** | 394 |

Single A100-40GB; divide wall-clock by boxes run in parallel. Rates are in the
gitignored ledger, deliberately not here.

## §7 RECOMMENDED ORDER

1. **Extend replicates on the existing 7 adapters to n≈28** (~36 GPU-h). Pins h
   away from zero or collapses it. **This decides whether §4 is needed at all.**
2. If h > 0: **train to N = 20**, run ~60 pairs at n=7 (~98 GPU-h total).
3. If h ≈ 0: no new adapters — buy replicates, and the "adapter-limited"
   framing is retired.

⛔ Do not train adapters before step 1. The entire adapter programme is
justified by a parameter whose confidence interval currently contains zero.
