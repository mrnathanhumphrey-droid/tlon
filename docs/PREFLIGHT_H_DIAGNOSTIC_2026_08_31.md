<!-- settled-claim-ok: this document exists to put intervals ON the
     adapter-limited/replicate-limited dichotomy and names both hypotheses
     throughout precisely because neither is established. -->
# PRE-FLIGHT ON THE h-DIAGNOSTIC — recommend NOT running it

$0. No box was started. Four checks, each of which alone would have changed the
run; together they say the diagnostic costs more than the decision it gates.

## ⛔⛔ 1. THE RUN AS SPECIFIED TARGETS THE WRONG `n`

The brief proposes *"additional **solo** transcripts … extending each build from
n = 14 to n ≈ 28"*. But the `n` in `sd(n)² = h² + k²/n` is **replicates per
pair** in the drift run, not solo conversations per build:

| | what `n` counts |
|---|---|
| cold table / recert arm | 14 **solo** conversations per **build** |
| **the sd(n) fit** | **7 replicates per PAIR**, each = one two-speaker probe |

`pair_delta()` consumes `live_a, live_b, yoked_a, yoked_b`. A solo transcript has
none of those, so **98 new solo transcripts would add zero points to this
curve.** The intended run is 12 pairs × 21 extra replicates = **252 two-speaker
probes = 43 GPU-h** at the measured 615 s/replicate — not the 36 h quoted.

## 2. A $0 ESTIMATOR OF h² ALREADY EXISTS, AND IT AGREES

Split each pair's 7 replicates into disjoint halves and take the covariance of
the two half-deltas across pairs. The halves' noise is independent, so it
cancels, and the covariance estimates `Var(systematic pair effect) = h²`
directly — no curve fit, no new data:

```
h² = +0.0358   (h = 0.189)   adapter-bootstrap 95% CI [−0.0624, +0.1398]
24% of bootstrap draws ≤ 0        curve-fit comparison: h = 0.2519, h² = 0.0634
```

An independent estimator lands in the same place: h is **probably** positive,
around 0.19–0.25, and **not established** — the CI still contains zero.

## ⛔⛔ 3. n = 28 WOULD MOST LIKELY RETURN "UNDETERMINED"

Simulating the proposed design (12 pairs, 7 adapters, adapter-bootstrapped),
truth h = 0.19:

| n | power to establish h > 0 | if h = 0, median CI upper bound |
|---|---|---|
| 7 (current) | 6% | +0.107 |
| **28 (the brief)** | **34%** | +0.023 |
| 56 | 57% | +0.012 |
| ∞ | 100% | 0 |

**At n = 28 the run has ~34% power for the branch that matters.** Two thirds of
the time it lands in the pre-declared third branch, "still underdetermined,"
after 43 GPU-h. The design is asymmetric — decent at *collapsing* h toward zero,
poor at *pinning* it away.

Reaching ~80% power needs n ≈ 100+, i.e. **200+ GPU-h.** ⇒ **The diagnostic
costs more than the ~98 GPU-h adapter design it was meant to gate.** A gate that
costs more than the decision is not a gate.

## ⭐ 4. AND THE TWO PROBLEMS HAVE DIFFERENT LEVERS

Power to establish h > 0 (truth 0.19) and leave-one-adapter-out se swing:

| design | power on h | LOO swing | infer h | train h |
|---|---|---|---|---|
| current: 7 ad, 12 pairs, n=7 | 10% | 65% | 14 | 0 |
| 7 ad, 12 pairs, **n=28** | 32% | **65%** | 57 | 0 |
| 7 ad, all 21 pairs, n=28 | 29% | — | 100 | 0 |
| **15 ad, 45 pairs, n=7** | 26% | **40%** | 54 | 10 |
| 20 ad, 60 pairs, n=7 | 11% | **38%** | 72 | 16 |
| 20 ad, 60 pairs, n=14 | 38% | — | 144 | 16 |

Two facts, and they are not the same decision:

- **More replicates pin h; more adapters do not.** At 20 adapters and 60 pairs
  with n=7 the power on h is 11% — barely above the current 10%. h is
  **noise-limited**: until `k²/n` falls below h², the systematic component is
  invisible no matter how many pairs you have.
- **More adapters buy stability; more replicates do not.** The LOO swing is 65%
  now and **still 65% at n=28**, but falls to 38–40% with 15–20 adapters.

## ⭐⭐ THE CONSEQUENCE: THE ADAPTER DECISION NEVER RESTED ON h

`h` governs whether more **replicates** would help. The **leave-one-adapter-out
instability** governs whether more **adapters** are needed — and that instability
is a *direct observation*, not a model parameter with a CI containing zero:
dropping one speaker moves the MDE 0.472 → 0.725 and the point estimate −0.006 →
+0.191. Nothing about that reading depends on h.

So the sequencing in `PRICING_ADAPTER_COUNT_2026_08_31.md` §7 — *"replicates
first, adapters only if h survives"* — was **wrong, and wrong because I let one
parameter stand in for two separate questions.** Pinning h is neither necessary
nor sufficient for the adapter decision.

## RECOMMENDATION

**Do not run the h-diagnostic.** It targets a parameter that does not gate the
adapter decision, at 34% power, for more than the decision costs.

Two coherent options remain, and they are a *scope* choice, not a technical one:

1. **Stop here.** The drift result stands as published: no coupling detected,
   MDE 0.5365 against a pre-declared Δ\* of 0.5939, unstable at 7 adapters, both
   channels' limits stated. σ_cp unmeasured and honestly characterised.
2. **Go to ~15–20 adapters** (~54–72 GPU-h inference + 10–16 GPU-h training) on
   **stability** grounds — the observed LOO swing, not h. That roughly halves the
   swing (65% → ~40%) and makes the interval mean what it says. It also, as a
   by-product, improves h's estimate — but that is not why you would do it.

⛔ What is *not* on the table is running 43 GPU-h to learn, most likely, that h
is still undetermined.
