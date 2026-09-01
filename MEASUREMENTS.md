<!-- settled-claim-ok: this file exists to attach an interval and a status to every
     measurement; where a status is "not established" that is stated explicitly. -->
# MEASUREMENTS — the canonical dictionary

**One authoritative definition per measurement.** Where a doc disagrees with this
file, **this file governs** and the doc is listed as stale in its entry.

Built by the audit of 2026-09-01. Inventory + the 14 collisions it resolves:
[`docs/AUDIT_INVENTORY_2026_09_01.md`](docs/AUDIT_INVENTORY_2026_09_01.md).
Removals: [`RETIRED.md`](RETIRED.md).

**Status vocabulary:** `LIVE` in use · `SUPERSEDED` replaced, by what and why ·
`RETRACTED` was wrong, with the correction · `PARKED` valid, not in current use.

---

## CONTENTS

**A · Convergence & coupling estimands** — [A1 W2 drift delta](#a1) · [A2 pairing gain](#a2) · [A3 trajectory partner-vs-stranger](#a3) · [A4 co-movement](#a4) · [A5 D / C probe-battery pair](#a5) · [A6 σ_cp](#a6)
**B · Observable selection** — [B1 contamination](#b1) · [B2 separability / ICC](#b2) · [B3 drift capacity](#b3) · [B4 locatability](#b4)
**C · Variance structure** — [C1 between-build sd](#c1) · [C2 h and k](#c2) · [C3 σ_a²](#c3)
**D · Decision quantities** — [D1 Δ\*](#d1) · [D2 MDE](#d2) · [D3 LOO stability](#d3) · [D4 unit of independence](#d4)
**E · Controls & nulls** — [E1 YOKED](#e1) · [E2 COLD](#e2) · [E3 self-pair](#e3) · [E4 unrelated-pair](#e4)
**F · Foreign metrics** — [F1 ROUGE](#f1) · [F2 TwoNN Id](#f2)
**G · The measured axis** — [G1 force:ka](#g1) · [G2 the force simplex](#g2)
**H · The F1–F5 falsifier scheme** — [remapped to its current estimators](#h), not retired

⛔ **Three words that mean several things. Always disambiguate:**
| word | see |
|---|---|
| **drift** | [A1](#a1) (current estimand) · [A5](#a5) (departure, probe battery) · [B3](#b3) (capacity) — three different objects |
| **`D`** | [A5](#a5) departure, *within*-speaker · vs `D(A,B)` distance, *between*-speaker in `SPEC_TWO_SPEAKER` §3 |
| **MDE** | [D2](#d2) — two incompatible estimators in the record |

---

# A · CONVERGENCE & COUPLING ESTIMANDS

<a name="a1"></a>
## A1 · W2 drift delta — `W2(LIVE) − W2(YOKED)`

**Aliases:** "the drift estimand", "delta", "the coupling estimand".
⛔ **Not to be confused with** [A5](#a5) `D` (departure) or [B3](#b3) drift
capacity. ⛔ **Not σ_cp** — see [A6](#a6).

**Measures:** whether two speakers' `force:ka` **marginal distributions** are
closer when the partner can respond than when the partner is a recording.

**Does NOT measure:** conversation-specific convention ([A2](#a2)); movement of
both speakers together ([A4](#a4)); anything about the *trajectory* within a
conversation ([A3](#a3)). ⛔⛔ **It is MARGINAL-BLIND**: two speakers whose
marginals coincide register zero however far their individual trajectories
diverge.

**Computed:** 2-Wasserstein, Gaussian (Fréchet) form, between each speaker's
cloud of per-replicate `force:ka` values, axis standardised by the **frozen**
between-build sd ([C1](#c1)); LIVE minus YOKED, per pair.
**Unit of independence: the ADAPTER.** `tools/act2_drift.py`, red-proof
`tests/test_drift_estimand.py` (sign mutation-tested in both directions).
**Sign convention: negative = coupling.**

**Status: `LIVE`** — the current primary estimand.

**Current value:** `+0.0803`, 95% CI clustered on adapter **[−0.2856, +0.4637]**,
6 of 12 pairs converging. Detection floor ≈ **32% of the median cold-table
separation (1.1878)**.

**Authoritative:** `docs/RESULTS_DRIFT_2026_08_31.md`.
**Stale elsewhere:** `SPEC_TWO_SPEAKER_DRIFT_2026_08_30.md` §5 states the intent
("`D(A,B)` shrinking in LIVE relative to YOKED") with a different symbol and no
estimator.

**Reading (three-way, pre-declared):**
- `LIVE < YOKED` **and** self-pair ≈ 0 → coupling. **Both required.**
- `LIVE ≈ YOKED` → **UNDERPOWERED**, *not* a null, unless the CI also excludes an
  effect worth having ([D1](#d1)). **This is the current outcome.**
- `LIVE > YOKED` → check for a sign error before interpreting.

<a name="a2"></a>
## A2 · Pairing gain — conversation-specific convention

**Measures:** whether partners **from the same conversation** are more alike than
partners drawn from different ones — i.e. whether each conversation forms its own
shared groove. This is the channel [A1](#a1) is structurally blind to.

**Does NOT measure:** a common shift (both speakers moving together leaves every
difference unchanged — that is [A4](#a4)); the speakers' starting gap.

**Computed:** `gain = mean_{i≠j}|A_i − B_j| − mean_i|A_i − B_i|`, then
LIVE − YOKED. **Unit: the ADAPTER.** `act2_drift.pairing_gain`, red-proof
`tests/test_pairing_statistic.py` — proven to fire on a planted convention, to be
graded in its size, and to stay silent on a common shift and on the gap.

**Status: `LIVE`**, validated-but-underpowered.

**Current value:** real pairs Δgain `+0.0024`, CI **[−0.0075, +0.0130]**.
⛔⛔ **That CI is on the GAIN, not on the convention.** Gain compresses its input
(a convention of sd 0.10 ka yields gain 0.0233), so the run's true detection
floor is a convention of **sd ≥ ≈0.10 ka = 41% of a between-build sd** — *worse*
than [A1](#a1)'s 32%. An earlier reading of "±4% of a between-build sd" is
**RETRACTED** (units error).

**Authoritative:** `docs/RESULTS_DRIFT_2026_08_31.md` §"THE CHANNEL W2 CANNOT SEE".

<a name="a3"></a>
## A3 · Trajectory partner-vs-stranger

**Measures:** whether the gap between two speakers *narrows over the course of a
conversation* relative to what two strangers do — the closest native analogue of
Parfenova's convergence-over-rounds.

**Does NOT measure:** marginal distance ([A1](#a1)). ⭐ Its stranger control
automatically removes "each speaker drifts to its own attractor", which
contaminates the raw quarter-by-quarter numbers.

**Computed:** `|ka_A − ka_B|` per quarter of each speaker's turns; Q4−Q1; then
partners minus strangers (strangers = cross-paired speakers from different
transcripts). Currently **descriptive** — bootstrapped over transcripts, not
clustered on adapter.

**Status: `LIVE`, provisional** — built 2026-09-01, not yet clustered on the
correct unit ([D4](#d4)), not yet in a tool or test.

**Current value:** partners widen `+0.0989`, strangers widen `+0.0960`,
**partner − stranger `+0.0030`, CI [−0.0607, +0.0679]**. Detection floor by
transcript count: 0.204 (n=6) · 0.138 (n=12) · 0.087 (n=24) · 0.064 (n=84).

⚠️ The raw self-drift figure (`|ka(Q4) − ka(Q1)|` = 0.1952 for one speaker) is
**≈84% estimation noise** — the within-quarter noise floor is 0.1636 at matched
window size, leaving an excess of **+0.0316 ≈ 13% of a between-build sd**.

<a name="a4"></a>
## A4 · Co-movement

**Measures:** both speakers moving in the *same* direction, which leaves their
gap unchanged and is therefore invisible to **both** [A1](#a1) and [A2](#a2).

**Computed:** mean of `(shift_A + shift_B)/2` from each speaker's cold centroid,
LIVE minus YOKED. The cold terms cancel in the difference, so the contrast is
clean despite the cold-baseline problems in [E2](#e2).

**Status: `PARKED` — a LEAD, not a result.**

**Current value:** `−0.0172`, CI **[−0.0335, +0.0004]** — grazes zero. ⛔ Found
post-hoc among several tests. **Re-analysing the existing data cannot upgrade it;
it needs its own pre-registered run.**

<a name="a5"></a>
## A5 · `D` (departure) and `C` (convergence) — the probe-battery pair

⛔⛔ **`D` HERE IS NOT THE `D(A,B)` OF `SPEC_TWO_SPEAKER` §3.** This `D` is
*within*-speaker; that one is *between*-speaker distance. Collision C1.

**Measures:** on a **fixed held-out 64-probe battery** (32 production / 32
comprehension, forced-choice against mutation distractors, administered in a
branched context that is then discarded):
- `D(M,t)` — fraction of probes where M's mapping at epoch t differs from **its own** at epoch 0
- `C(t)` — fraction of probes where A and B agree **with each other** at epoch t

**Status: `PARKED` — and parked as the UPGRADE PATH, decided 2026-09-01.** The
apparatus exists (`probes.build`) but the entire `force:ka` line measures
free-running transcripts with no battery. **The two approaches have never been
reconciled** (collision C11). Parked, not superseded — nothing has replaced what
it does.

⭐ **WHY IT IS HELD RATHER THAN RETIRED.** It measures the **meaning↔form
mapping** in impression space, which is a strictly stronger convergence claim
than a free-transcript `force:ka` rate: a shared force rate is two speakers
*sounding* alike, a shared mapping is two speakers *meaning* alike. It is also
the only instrument in the project that has ever fired on a constructed pact
(`ΔD` −5.08, `ΔC` +85.94, p=0.0078, n=8 seed-paired — synthetic).
⇒ Held pending the positive control ([E4](#e4) must pass first). **If `force:ka`
moves, this is the apparatus that upgrades "the force rate converged" to "the
mapping converged."** Flagged item `RETIRED.md` A4.

**Validation on record:** synthetic speakers with drift known by construction,
n=8 seed-paired, MDE by exact sign-flip permutation — a pact-by-construction gave
`ΔD` **−5.08** and `ΔC` **+85.94** (p=0.0078). ⛔ **This is a *synthetic*
validation, the same class as a planted-effect red-proof — not a demonstrated
positive on real adapters.**

⭐ Recorded finding that still binds: **`D` up with `C` flat has the registered
name WANDERING, NOT CONVENTION**, and a pair that provably built a shared codebook
showed `ΔD ≈ 0`. **Drift alone is not a pact.**

**Authoritative:** `docs/PREREG_ACT2_DRIFT_2026_08_24.md` (relocked 2026-09-01
after a cost redaction; prior lock `20620b7c` — see C8 below).

### C8 · the `D_ctx` / `D_w` subscript discipline — `RETIRED` 2026-09-01

The prereg §0.2 mandates *"Every number, table and filename carries its
subscript"*, separating `D_ctx` (in-context, prompted) from `D_w` (weight-level,
post-fine-tune). No document since 2026-08-24 uses either subscript (collision
C8).

**Retired as TRIVIALLY SATISFIED — not abandoned, and not out of compliance.**
Every Act-2 measurement to date is **inference-only**: no weights change in any
arm of any run, so **every number in the arc is `_ctx` by construction** and the
subscript partitions nothing. A marker that takes the same value on every row is
not a caveat, and carrying it teaches readers to skip a marker that is meant to
be load-bearing.

⛔ **THE DISTINCTION §0.2 DRAWS IS NOT RETIRED — only the notation is.** The
moment a fine-tune enters an Act-2 measurement, `D_w` becomes a live category,
§0.2 is back in force unamended, and the subscripts return. §0.2's actual
prohibition — *the two must never be reported under one word* — stands
unconditionally.

Logged with reasoning: [`RETIRED.md`](RETIRED.md) R2. A note is appended to the
prereg and **this retirement did not edit the body.**

⚠️ **The prereg's lock changed on 2026-09-01.** Private research costs were
removed from the public repository (`7420a11`, 2026-08-28, §0.2 and §7) and the
document was then relocked; no hypothesis, estimator, threshold or falsifier
changed. Older text citing `20620b7c` refers to the pre-redaction lock.
Record: [`RETIRED.md`](RETIRED.md) **R3**.

<a name="a6"></a>
## A6 · σ_cp — coupling power

⛔⛔ **σ_cp IS NOT WHAT THE DRIFT RUN MEASURED, AND NEVER WAS.** It is a
**stochastic-thermodynamics** object — `σ_cp ∝ dᵀKd`, diffusion matrix, Sylvester
gradient projection, integral fluctuation theorem, entropy production. It is
mathematically unrelated to [A1](#a1).

**Status: `PARKED`, and the naive form is `RETRACTED`** — `σ_cp ∝ dᵀKd` was
**sign-indefinite in 5000/5000** on-shell 2-DOF draws, and a coupling power that
can go negative cannot be an entropy production. The corrected object
`σ_ex^MN − σ_ex^HS` passed **0/1500 negative**.

**Current value: never measured on any real system.**

⛔ Four documents close with *"σ_cp remains unmeasured"* in a drift context —
`RESULTS_VARIANCE_DECOMPOSE`, `RESULTS_ASYMMETRIC_RECERT`, `RESULTS_STAGE2_DISTANCE`,
`STATE`. **True, but it reads as though the drift run were attempting σ_cp. It
was not.** Collision C12.

**Authoritative:** `docs/SPEC_DISCOURSE_LAYER_v0.1_2026_08_25.md`.

---

# B · OBSERVABLE SELECTION

<a name="b1"></a>
## B1 · Contamination

**Measures:** between-build sd ÷ within-conversation movement — how much of an
observable's variation is *build identity* rather than *conversational churn*.
Low = good arena axis.

**Status: `SUPERSEDED` by [B2](#b2)+[B3](#b3)+[B4](#b4).**
**Why:** contamination and separability are near-inverses, so ranking by
ascending contamination ranks approximately by ascending *separability* — it
selects **against** the property a distance needs (collision C4).

**Values on record for `force:ka`:** window-1 **0.27** (jackknife rank 2–4) →
in-regime **1.59** (jackknife rank 7–9). ⚠️ Contamination is a ratio of two
regime-dependent quantities and **changes by ~6× between regimes**; a panel
certified in one regime is not certified in another.

**Authoritative (as history):** `RESULTS_STAGE1_RANKING_STABILITY_2026_08_30.md`,
`RESULTS_ASYMMETRIC_RECERT_2026_08_30.md`.

<a name="b2"></a>
## B2 · Separability (ICC)

**Measures:** the share of conversation-level variance attributable to build
identity — *do the speakers differ at all*.

**Does NOT measure:** ⛔⛔ **whether they CONVERGE.** An axis can separate
speakers perfectly and be entirely unable to show coupling. This boundary is the
one most often crossed in the older docs.

**Status: `LIVE`** — one of the three current admission floors.

**Current values** (LIVE arm, 84 real-pair transcripts, 2026-09-01):
`force:ka` **0.856** · `force:ki` 0.826 · `force:kä` 0.774 · `force:ko` 0.709 ·
`force:ku` 0.600 · modifier density 0.312 · root repertoire 0.310 · root TTR
0.298 · tokens/surface 0.211 · nodes/scene 0.128 · distinct-surface **0.000**.
Earlier jackknife range for `force:ka`: **0.559–0.906**.

⇒ **Only the force family separates speakers.** Everything else sits below 0.32
and moves more *within* a speaker than *between* speakers.

<a name="b3"></a>
## B3 · Drift capacity

⛔ **Not "drift"** ([A1](#a1)) — this is *can the axis move at all*.

**Measures:** observed half-to-half movement ÷ movement expected under a frozen
rate, `sqrt(2·σ²_turn/n_half)·sqrt(2/π)`. Ratio ≈ 1 means frozen.

**Status: `LIVE`** — second admission floor.
**Current value:** `force:ka` **1.45 ± 0.10** vs frozen. `force:ki` **0.92** —
separates robustly (ICC 0.749–0.826) and **does not move**; admitted on
separability alone it would have frozen a baseline on an inert axis.

<a name="b4"></a>
## B4 · Locatability

**Measures:** whether a speaker's centroid is precise enough to place against the
population: `centroid se ≤ 0.5 × between-build sd` on every axis. Equivalently
`sqrt((1−ICC)/ICC)/√n`.

**Status: `LIVE`** — third admission floor.

**Current values — and they differ by panel, which is collision C5:**
| panel | verdict |
|---|---|
| 2-axis (`tokens/surface`+`nodes/scene`), n=14 | ⛔ **all 7 builds FAIL**, need 23–29 conversations; cold table `frozen: false`, sha `ca1ab5e9…` |
| `force:ka`, n=14 | ⭐ **all 7 locatable**, `unlocatable: []`, `frozen: true`, sha `84c2a1b5…` |

⭐ Both are correct for their own panel. **Locatability is a property of the
AXIS, not of the sample size** — an earlier "all builds fail, the fix is more n"
reading was corrected on exactly this point.

**`runs/act2/cold_table.json` (the 2-axis table, sha `ca1ab5e9…`): `SUPERSEDED`,
and KEPT ON PURPOSE.** Superseded by `runs/act2/cold_table_ka.json` (sha
`84c2a1b5…`, [C1](#c1)) — ⛔ **never use it as a current baseline.** It is
retained for two reasons, either of which alone would be sufficient:

1. It is the baseline `docs/RESULTS_STAGE2_DISTANCE_2026_08_30.md` was written
   against. Deleting it orphans that document's numbers.
2. Its HALT **is the evidence for the panel switch.** All 7 builds unlocatable at
   n=14 (needing 23–29) on the 2-axis panel, while all 7 are locatable at the
   same n=14 on `force:ka`, is what showed locatability tracks the axis rather
   than the sample size — the finding that re-admitted `force:ka` ([G1](#g1))
   after contamination had excluded it ([B1](#b1)).

Flagged item `RETIRED.md` A5, decided 2026-09-01: keep, mark, forward-point.

---

# C · VARIANCE STRUCTURE

<a name="c1"></a>
## C1 · Between-build sd — the frozen ruler

**Measures:** sd of per-build `force:ka` centroids; **one unit of [A1](#a1)
distance = one build-to-build sd**.

**Status: `LIVE` and FROZEN.** `runs/act2/cold_table_ka.json`, content sha
`84c2a1b5…`. ⛔ Never recompute it per condition — a ruler that moves with the
measurement.

**Current value: `0.2454`** (7 builds, n=14 each).
⚠️ **Numerically adjacent to h = 0.2519 ([C2](#c2)) and they are DIFFERENT
QUANTITIES IN DIFFERENT UNITS** — this one is a `force:ka` proportion, that one
is a standardised-W2 sd computed *after* dividing by this one.

<a name="c2"></a>
## C2 · `h` and `k` — the variance split

**Measures:** in `sd(n)² = h² + k²/n` over pair-level deltas, `h` is the
irreducible pair-to-pair heterogeneity and `k²/n` the W2 estimation noise at n
replicates.

**Status: `LIVE`, NOT ESTABLISHED.**

**Current value:** `h = 0.2519`, adapter-bootstrap 95% CI **[0.0000, 0.4033]**.
⛔⛔ **The lower bound is zero**, so h = 0 (replicate-limited, no new adapters
needed) cannot be ruled out. Independent split-half estimator: `h² = +0.0358`
(h = 0.189), CI **[−0.0624, +0.1398]**, 24% of draws ≤ 0 — agrees in direction,
also not established. `k² = 0.67111`; noise at n=7 = 0.3096.

⛔ **"The experiment is adapter-limited" is RETRACTED** — it was this point
estimate reported without its interval.
⛔ **The brief that called `0.2397` "h²" was wrong: that is `h`** (h² = 0.0575),
a factor of 4 in variance.

<a name="c3"></a>
## C3 · σ_a² — the adapter variance component

**Status: `RETRACTED` — NOT IDENTIFIABLE at this design.**
Method-of-moments over one-shared-adapter cross-products returned **−0.0268**
(negative), and a fitted-component model **undershot the observed se by 44%**.
⇒ N is bracketed between two bounding laws anchored on the *observed* se, never
extrapolated from fitted components.

---

# D · DECISION QUANTITIES

<a name="d1"></a>
## D1 · Δ\* — the worth-having threshold

**Measures:** the smallest coupling effect that would be scientifically
meaningful. Pre-declared **before any power curve was computed**, on grounds
independent of the data: *an effect must close at least half the distance that
ordinarily separates two Tlön speakers.*

**Status: `LIVE`.** **Value: `Δ* = 0.5939`** = 0.5 × median cold-table separation
1.1878, in W2 units.

⛔ **Lowering Δ\* after a null result is retrofitting the threshold to the
outcome.** If it should be lower, that case must stand on independent grounds.

<a name="d2"></a>
## D2 · MDE — ⛔ two incompatible estimators in the record

| | definition | where |
|---|---|---|
| **MDE-perm** | 95th percentile of \|ΔD\| under seed-label permutation **within the control arm**, computed before unblinding | `PREREG_ACT2_DRIFT` §5.1 |
| **MDE-power** *(current)* | **2.802 × se** — minimum detectable effect, 80% power, two-sided α=0.05 | `PRICING`, `PREFLIGHT`, `STATE` |

**Status:** MDE-power `LIVE`; MDE-perm `PARKED` with [A5](#a5).
**Current value (MDE-power):** `0.5365` at se 0.1915 — **below Δ\* = 0.5939**, so
the completed run is *nominally powered* for a worth-having effect. ⚠️ But see
[D3](#d3): leave-one-out it ranges **0.472–0.725** and straddles Δ\*.

<a name="d3"></a>
## D3 · LOO stability

**Measures:** how much the estimate and its se move when one adapter is dropped.

⛔⛔ **Use ABSOLUTE units. The relative form is broken:** the drift mean is
+0.0803, near zero, so any ratio to it explodes regardless of N. Both the
"swing ≈ 1.65/N" law **and its refutation** ("plateaus at ~41%") were artifacts
of that near-zero denominator. **Both retracted.**

**Status: `LIVE`** in absolute form.

**Current value:** LOO means `+0.1909 +0.1370 +0.0545 −0.0056 +0.0914 +0.0260
+0.0754` → **sd 0.0666, range 0.1965**, against Δ\* = 0.5939 (**11.2%** of the
threshold). ⇒ **the verdict does not flip; only the quoted MDE does.**

<a name="d4"></a>
## D4 · Unit of independence

**Canonical: the independently-trained ADAPTER.** 21 pairs from 7 adapters are
not 21 observations. Clustering is on the adapter; intervals come from a dyadic
cluster bootstrap resampling adapters, pairs entering with multiplicity
`count[x]·count[y]`.

**Status: `LIVE`, standing check.**
⛔ The record disagrees about how many times this has moved — "third", "fourth"
and "sixth" all appear (collision C7). **The count is decorative; the rule is
not.** Lineage: transition → exchange → training run → adapter →
conversation-within-adapter → adapter-count.

---

# E · CONTROLS & NULLS

<a name="e1"></a>
## E1 · YOKED — the primary null

Each speaker faces a **recording** of the other's LIVE turns: input held,
mutuality removed. **`LIVE − YOKED` is the only clean contrast** — same n, same
estimator, same run. **Status: `LIVE`.**
⚠️ Known limit, stated before the run: once a speaker's own outputs diverge from
its LIVE trajectory, "identical input" holds for the **partner stream only**.

<a name="e2"></a>
## E2 · COLD — the baseline, ⛔ NOT the null

Each speaker alone, own chain only — *where they start*.
**Status: `LIVE` as a baseline; ⛔⛔ BANNED as a contrast.**

**Standing rule: never compare LIVE to COLD.** Two would-be headline false
positives came from it: **Jensen** (`mean|A−B|` vs `|mean A − mean B|`;
`E|X| ≥ |EX|`, worst at small gaps — `gap(LIVE)−gap(COLD) = +0.0736` "excluded
zero" and was bias), and **n-mismatch** (live n=7 vs cold n=14 inflates the
absolute difference even with matched estimators).

<a name="e3"></a>
## E3 · Self-pair control

One adapter as **both** speakers. **Status: `LIVE`** — the precondition for any
coupling claim.

⛔⛔ **What it is:** a **marginal-distance noise floor**. Identical weights make
the two marginals coincide (exchangeability: `law(A) = law(B)`), and [A1](#a1)
reads marginals — so this arm could **never** show coupling however far the two
trajectories diverged.
⛔ **What it is NOT:** proof that coupling is impossible. It was used as that, and
that was a category error. Two identical adapters are **two individuated
trajectories**, because neither holds the other's words.
⚠️ Roles are not perfectly symmetric (in LIVE A moves first; in YOKED both are
first-movers). The asymmetry is **common-mode** — every LIVE arm carries it — so
it **cancels in the self-vs-real comparison**. The self-pair is a matched
baseline *carrying that offset*, not a pure zero.

**Current value:** mean `+0.0445`, CI **[−0.4949, +0.3665]** — the predicted
sign. ⭐ **`s20621` against itself read −0.827**, a *larger* apparent convergence
than any real pair achieved (best −0.611). **Without this arm, six converging
pairs led by −0.611 would have read as a coupling result.**

<a name="e4"></a>
## E4 · Unrelated-pair test — the saturation screen

**Measures:** whether a candidate metric separates partners from **strangers** at
all. ⭐ **Any new convergence metric must pass this before use** — it is the
cheapest way to catch a saturated or inert instrument.
**Status: `LIVE`, standing gate.**

---

# F · FOREIGN METRICS (Parfenova et al., arXiv 2512.00047v1)

<a name="f1"></a>
## F1 · ROUGE — ⛔ DEAD on this substrate

**Status: `RETRACTED` for Tlön use.**
Partners score **0.6610**; **unrelated** speakers score **0.6669**; total
vocabulary across 84 transcripts is **244 tokens**. LIVE−YOKED `−0.0044`, CI
**[−0.0147, +0.0057]**.
⇒ **Saturated, not suppressed** — and those have opposite implications. A
saturated metric can show neither convergence nor its absence.

<a name="f2"></a>
## F2 · TwoNN intrinsic dimensionality

Their headline convergence measure (Table 4): 2-Model ΔId **−0.44**, 3-Model
**−7.30**, 5-Model **−7.24**.
**Status: `PARKED` for Tlön — validity unestablished.** Computed on 384-d MiniLM
embeddings; MiniLM is English-trained and its embeddings of Tlön surfaces have
not been shown to carry Tlön structure.
⛔ **A sample-size confound was hypothesised and REJECTED:** TwoNN bias is ~2% at
these cloud sizes and runs the **wrong way**. Do not raise it.

---

# G · THE MEASURED AXIS

<a name="g1"></a>
## G1 · `force:ka`

Fraction of scenes whose force is `ka`; a proportion in [0,1].
**Status: `LIVE` — the sole current axis**, on separability ([B2](#b2) 0.856),
capacity ([B3](#b3) 1.45 ± 0.10) and locatability ([B4](#b4), all 7 pass).

⛔⛔ **Its admission history is collision C3 and must not be read from `docs/`
alone.** It was admitted at window-1 (contamination 0.27), then **excluded
in-regime** as *"the single worst-behaved force in the set"* (contamination
1.59), then **re-admitted** on the three floors above when contamination was
found to select backwards ([B1](#b1)). **The re-admission has no RESULTS doc** —
it lives in `STATE.md`, in `runs/act2/cold_table_ka.json`, and in this entry.

<a name="g2"></a>
## G2 · The force simplex — why there is only one axis

**Status: `LIVE`** — a structural property of the observable set, measured
2026-09-01 on 336 speaker×arm×replicate records.

The five force rates **sum to exactly 1** (observed sd `3.9e-17`): compositional
data, **4 degrees of freedom**, fifth eigenvalue `4.3e-19`.
**PC1 carries 76%** of the variance; effective rank **1.67 of 5**. `force:ka`
correlates −0.83 / −0.71 / −0.50 with `ku` / `ki` / `kä` — it *is* "ka vs the
rest".

⇒ **A CLR-transformed 4-vector of the full profile narrows the [A1](#a1) CI by
4.4%** (0.9716 vs 1.0162, self-standardised). ⭐ **There is no second native axis
to add.** `force:ka` is sufficient because the substrate has ≈ one structured
dimension and `force:ka` is approximately it.

---

<a name="h"></a>
# H · THE F1–F5 FALSIFIER SCHEME — REMAPPED, NOT RETIRED

**Decided 2026-09-01.** The prereg's five falsifiers (`PREREG_ACT2_DRIFT` §2) are
**live**. What changed is not the scheme but the *estimator* each falsifier is
computed from: the arc moved off the held-out probe battery ([A5](#a5)) and onto
free-running transcripts on `force:ka` ([G1](#g1)), and no document connected the
two — which is collision C10, and why the scheme read as abandoned.

⛔⛔ **THIS TABLE RE-POINTS EACH FALSIFIER AT ITS CURRENT ESTIMATOR AND CHANGES
NO FALSIFIER'S MEANING.** The firing condition column is the prereg's, unaltered.
Where nothing currently estimates a falsifier, that is stated — **not** filled in
with the nearest available number.

| | fires if (prereg §2, unchanged) | current estimator | status |
|---|---|---|---|
| **F1** internalizability | native valid-emission rate **< 0.90** on held-out prompts | **F-LOCAL** — `falsify.f_local`, measured cardless and **unconstrained** (constrained decoding makes validity 100% and the falsifier unable to fire) | ⭐ **CLEARED** 2026-08-26. All 7 adapters on disk are recorded F-LOCAL-clear (`STATE.md` :299, :363). Standing gate for any new adapter. |
| **F2** drift-is-noise ⛔ *the load-bearing brick* | `ΔD = D(interacting) − D(control) ≤ MDE`, seed-paired | the LIVE−YOKED contrast ([E1](#e1)), read against the [E3](#e3) self-pair floor and [A5](#a5)'s synthetic-validation floor | ⚠️ **NOT ADJUDICATED.** [A1](#a1) reads `+0.0803`, CI **[−0.2856, +0.4637]**, which covers zero — but prereg §5.2 binds: an underpowered cell is **UNINFORMATIVE, NOT A FIRING.** F2 is neither cleared nor fired. |
| **F3** pact | `ΔC = C(interacting) − C(control) ≤ MDE`, seed-paired | [A1](#a1) for the shared-marginal reading; [A2](#a2) for conversation-specific convention | ⚠️ **NOT ADJUDICATED**, same headroom reason. [A2](#a2) Δgain `+0.0024`, CI **[−0.0075, +0.0130]**. ⛔ **The estimator changed OBJECT:** `C` is probe *agreement*, [A1](#a1) is marginal *distance* and is marginal-blind. Reconnected **by intent, not by identity** — see the caveat below. |
| **F4** degeneration | drift explained by degradation rather than convention: root-diversity decline **> 25 %** in the interacting arm while the control's holds, **or** `ΔD` losing significance under a pre-committed covariate | `falsify.f4_degeneration` — the two relative branches plus the absolute third, `degeneracy_guard` (root-TTR floor **0.50**, near-repetition ceiling **0.75**) | ⭐ **ACTIVE and PASSING.** Fired and was fixed (**D15**, `STATE.md` :599): both relative branches read **+0.0 %** on a real collapse because both arms sat on the floor, which under a yoked design is the *likely* case. Current regime: **0 of 98** in-regime solo transcripts degenerated (`tools/pipeline_drift.sh` :14). |
| **F5** leakage | a probe's impression appears in the conversation **before** that probe is administered | ⛔ **none — there is no current estimator** | ⏸ **PARKED with [A5](#a5).** F5 is defined over a probe battery; the free-transcript line administers no probes, so there is nothing that can leak into anything. It returns to force **with the battery**, and not before. |

⚠️ **F4's absolute branch is a tripwire, not a discriminator — do not read a
PASS as evidence for the claim.** A depth-1 Markov painter that ignores the prior
turn entirely scores **0/200 guard-fires** at depths 8/20/40 (mean root-TTR
**0.937 / 0.856 / 0.738** against the 0.50 floor —
`tlon/discourse/multiturn.py`). It separates *degenerate* from *healthy* and has
**no power** to separate *noise* from *convention*. The gate a random painter
fails is force-fidelity (`tools/act2_force_fidelity.py`).

⚠️ **F3's remap is the one place a reader could be misled, so it is stated
twice.** `C` asks whether A and B give the **same answer to the same probe**;
[A1](#a1) asks whether their **`force:ka` marginals are close**. Two speakers can
match on the second while disagreeing on every probe. The F3 row records what
currently stands in for the falsifier — it does **not** claim the two quantities
are the same, and a future `C` measurement supersedes the substitution rather
than agreeing with it. [A5](#a5) is the apparatus that would restore the original
estimator.

⭐ **WHAT THE REMAP EXPOSES.** F1 and F4 — the two falsifiers asking whether the
speakers are *fit to be measured* — are cleared and passing. F2 and F3 — the two
that carry the actual scientific claim — are **undetermined for want of power**,
not answered. That is the same verdict [A1](#a1) and [A2](#a2) already report,
reached independently through the prereg's own vocabulary. **Nothing in the F
scheme has been retired, and nothing in it has been cleared that the dictionary
does not also clear.**

Flagged item `RETIRED.md` A3, decided 2026-09-01: **remap, do not retire.**
