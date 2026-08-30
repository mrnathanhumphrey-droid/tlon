# RESULTS — Stage 2: the distance is defined; the cold table is NOT frozen

`$0`, on the 98 in-regime transcripts. Tool `tools/act2_distance.py`, red-proof
`tests/test_distance_metric.py` (14 tests). Suite 1272.

## VERDICT

⛔⛔ **THE COLD TABLE IS NOT FROZEN. All 7 builds fail the pre-declared
locatability rule at 14 conversations per speaker.** The metric is built and
red-proofed; the data underneath it is too imprecise to pre-register as a
baseline. **The fix is more conversations per speaker, not more speakers.**

## 1 · THE METRIC

2-Wasserstein between the speakers' conversation clouds, Gaussian (Fréchet) form,
on the two admitted axes standardised by the frozen between-build sd
(`tokens/surface` 0.1012, `nodes/scene` 0.0350) so one unit is one build-to-build
sd:

```
W2² = ‖μ₁−μ₂‖²  +  tr(Σ₁) + tr(Σ₂) − 2·tr((Σ₂^½ Σ₁ Σ₂^½)^½)
      └ MEAN TERM ┘  └─────────── SPREAD TERM ───────────┘
```

⭐ **Chosen over own-spread-normalised centroid distance** because normalising
*divides* by a quantity that itself moves between conditions — a change in a
speaker's fuzz would then rescale the whole metric and manufacture drift
multiplicatively. Here fuzz only *adds*, and it adds to a term reported
separately.

⭐ **The decomposition is the defence, so the decomposition is what is tested.**
`test_INFLATING_a_speakers_own_spread_does_NOT_move_the_mean_term` blows a
speaker's variance up 8× at a fixed centroid: the spread term more than doubles,
the mean term moves by < 1e-9. A fuzzy speaker cannot appear to have relocated.

⛔ Empirical matching W2 was rejected at n=14 — the assignment is dominated by
sampling noise at that size and has no closed decomposition.

### ⭐ The s20621 threat was on an axis that is no longer in the panel

`s20621`'s notorious spread (own-conversation sd 0.271 vs siblings' 0.06–0.13)
was measured on **`force:ka`**, which the in-regime re-certification excluded
(contamination 1.59). On the two admitted axes `s20621` is unremarkable:

```
own-conversation sd     tokens/surface        nodes/scene
s20621                      0.2490               0.0746
range across all 7      0.2387 – 0.2680      0.0578 – 0.0751
```

⇒ The exclusion rule was written for a build that does not need excluding. What
the check found instead is worse and general.

## 2 · ⛔⛔ NOBODY IS LOCATABLE

Pre-declared rule: a speaker can be placed iff its **centroid standard error ≤
0.5 × between-build sd** on every axis — the estimate must be at least twice as
precise as the distance it has to resolve.

| build | n | worst se/between | n needed |
|---|---|---|---|
| s20620 | 14 | 0.70 | 28 |
| s20621 | 14 | 0.66 | 25 |
| s20622 | 14 | 0.64 | 24 |
| s20623 | 14 | **0.71** | **29** |
| t30001 | 14 | 0.70 | 28 |
| t30002 | 14 | 0.63 | 23 |
| t30003 | 14 | 0.63 | 23 |

**Every build fails.** This is not an exclusion — an exclusion removes a bad
speaker from a good population — it is a **HALT on the whole table**.

⭐ **An independent check agrees with the declared threshold.** Comparing each
pair's centroid separation against that pair's own uncertainty:

```
15 of 21 pairs are separated by < 2σ
closest:  s20620|s20622  0.16 ± 1.21  →  0.1σ
best:     s20623|t30003  3.17 ± 1.18  →  2.7σ
```

The rule and the per-pair analysis were derived differently and reach the same
place, so `0.5` was not an arbitrarily strict bar.

## 3 · THE COLD TABLE (provisional, `frozen: false`, sha `ca1ab5e9…`)

Computed and recorded so the next pass can be compared against it, **explicitly
not frozen**. Freezing a baseline whose centroids are dominated by estimation
error would pre-register noise and hand the drift run something
authoritative-looking to measure against.

```
fixed-corpus (n=6)  mean W2 1.201
cross-corpus (n=15) mean W2 2.114
share of W2² carried by the MEAN term: median 95%, max 100%
```

⭐ **The mean term carries ~95 % of the distance**, so this is a metric about
*where speakers are*, not about the shape of their clouds — which is what makes
the decomposition a diagnostic rather than a crutch.

⚠️ **The near/far gradient is in the right direction but does not hold pair by
pair.** Same-corpus pairs average closer, yet the single closest pair in the
table (`s20620|s20622`, 0.387) is **cross**-corpus. With 15 of 21 pairs under 2σ
the gradient is suggestive and nothing more; it is a drift-run reading regardless.

## 4 · PRE-DECLARED FOR THE DRIFT RUN

- **Estimand: `drift = W2(LIVE) − W2(YOKED)`, paired per pair.** COLD is the
  baseline where they start, **not** the null; YOKED is the null because it
  replays the identical partner turns with mutuality removed.
- **Unit of independence: the ADAPTER.** 21 pairs over 7 adapters are not 21
  observations — each adapter sits in 6 pairs. Clustering is on the adapter.
  ⭐ The conversation-within-adapter is the finer unit and the distribution
  metric absorbs it **by construction**, since a speaker is a cloud, not a point.
  *(Fourth move of this unit: transition → exchange → training run → adapter →
  conversation-within-adapter.)*
- **No injected material.** Distances come from the `--no-injections` arm via
  `conditions.cold_a.surfaces`, already filtered by `measurable_turns()`.
- **Two axes. `root TTR` and `force:ka` are not reintroduced.**

## 5 · WHAT IT WOULD COST TO PASS

```
29 conversations per build (worst case)  →  15 more per build
7 × 15 = 105 transcripts × 153 s          ≈  4.5 h on an A100
```

Roughly the same as the pass that generated the first 98, and it makes the
existing 98 count — se falls as 1/√n over the combined set.

## 6 · WHAT THIS DOES NOT DO

No drift number. No frozen baseline. σ_cp remains unmeasured.
