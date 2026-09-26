# ⛔ Closed avenues — read before proposing anything

Each item below was tried, or proposed and killed, with a reason on record. This
file exists because a fresh context re-proposes exactly these. Reasons are given
so a genuinely new argument can still reopen one — the bar is a **new argument**,
not a fresh memory.

---

## Comparisons and contrasts

**LIVE vs COLD — BANNED as a contrast.** Standing rule. It produced two
would-be headline false positives:
- **Jensen**: `mean|A−B|` vs `|mean A − mean B|`; `E|X| ≥ |EX|`, worst at small
  gaps. `gap(LIVE) − gap(COLD) = +0.0736` "excluded zero" and was bias.
- **n-mismatch**: live n=7 vs cold n=14 inflates the absolute difference even
  with matched estimators.

COLD is a **baseline** — where speakers start. The null is **YOKED**.

**Pooling arms.** `assert_arm` refuses to read one arm as another. A
shared-memory transcript loaded as `live` would silently pool the positive
control with the drift run — two different memory models under one estimand,
and the number would look entirely normal.

**Pooling a NOT-ESTABLISHED cell with a collapse.** OLMo's cell is empty
(F-LOCAL fired). It is not evidence either way.

---

## Metrics that are dead here

**ROUGE — RETRACTED for Tlön.** Partners **0.6610**; *unrelated* speakers
**0.6669**; total vocabulary across 84 transcripts is **244 tokens**. LIVE−YOKED
**−0.0044**, CI [−0.0147, +0.0057].
⇒ **Saturated, not suppressed** — and those have opposite implications. A
saturated metric can show neither convergence nor its absence.

**TwoNN sample-size confound — hypothesised and REJECTED.** Bias is ~2% at these
cloud sizes and runs the **wrong way**. ⛔ Do not raise it again. (TwoNN itself is
PARKED for a different reason: it is computed on 384-d MiniLM embeddings, and
MiniLM is English-trained — its embeddings of Tlön surfaces have not been shown
to carry Tlön structure.)

**Contamination ranking — SUPERSEDED, and it selects backwards.** Contamination
and separability are near-inverses, so ranking by ascending contamination ranks
approximately by ascending *separability* — it selects **against** the property a
distance needs. Also: it is a ratio of two regime-dependent quantities and
changes by **~6× between regimes**, so a panel certified in one regime is not
certified in another.

**`force:ki` as an axis — dead.** Jackknife rank **3–9**; reads 0.65, 0.28 or
0.53 depending which builds you hold. It separates robustly (ICC 0.749–0.826)
and **does not move** (capacity 0.92 ≈ frozen). Admitted on separability alone it
would have frozen a baseline on an inert axis.

**Adding a second native axis — there isn't one.** The force simplex has
effective rank **1.67 of 5**; PC1 carries 76%; a CLR 4-vector buys **4.4%** on
the CI. `force:ka` is approximately the substrate's one structured dimension.

---

## Statistical objects that were wrong

**σ_cp naive form — RETRACTED.** `σ_cp ∝ dᵀKd` was sign-indefinite in
**5000/5000** on-shell 2-DOF draws; a coupling power that can go negative cannot
be an entropy production. The corrected object `σ_ex^MN − σ_ex^HS` passed
**0/1500 negative**. ⛔ And σ_cp is **not what the drift run measured** and never
was — it is a stochastic-thermodynamics object, mathematically unrelated to A1.
Four documents close with "σ_cp remains unmeasured" in a drift context; true, but
it reads as though the drift run were attempting it. It was not.

**σ_a² — RETRACTED, not identifiable at this design.** Method-of-moments returned
**−0.0268** (negative); a fitted-component model **undershot the observed se by
44%**. N is bracketed between two bounding laws anchored on the *observed* se,
never extrapolated from fitted components.

**"The experiment is adapter-limited" — RETRACTED.** It was the `h` point
estimate reported without its interval. The CI is **[0.0000, 0.4033]**.

**Relative LOO — RETRACTED, both directions.** The drift mean is +0.0803, near
zero, so any ratio to it explodes regardless of N. The "swing ≈ 1.65/N" law
**and** its refutation ("plateaus at ~41%") were both artifacts of that
denominator. Use **absolute** units.

**Lowering Δ\*** (0.5939) after a null — retrofitting the threshold to the
outcome. If it should be lower, that case must stand on **independent grounds**.

---

## Readings that are void

**In-training lag reads.** Taken at **T = 0.0, greedy**. A deterministic speaker
repeats content because the same context yields the same continuation, so it
inflates persistence at every lag (lag2 z **23.858** greedy vs **4.343** at
T=0.7). ⛔ **`miscurve`'s epoch-2 signal — the campaign's only evidence that
release ever installs — is one of these. Do not cite it for anything.**
⭐ Standalone CLI reads (T=0.7/256) are unaffected; cross-run endpoint
comparisons remain valid.

**Single-rung z differences of order ~2.** The measured same-object noise floor
is a lag-2 z moving **~1.9** and a lag-2 profile **~0.073** between two reads of
one fixed object. Three of the four "repeat arm higher" deltas sit within ~2× of
that floor.

---

## Designs that cannot answer what they were pointed at

**Re-running the epochs arm.** The diversity confound is **structural**:
`epochs = steps ÷ distinct`, and you cannot hold steps, dose and diversity fixed
at once. The prereg declared *in advance* that the design can confirm the lever
or confirm the dose story but **cannot cleanly refute** the lever. It is
ambiguous-by-construction, not muddy. Separating repetition from diversity needs
a **different arm** (e.g. matched distinct-example count with varied epochs),
not a re-run.

**Re-analysing existing data to upgrade A4 co-movement.** It was found post-hoc
among several tests. It needs its own pre-registered run.

**A LoRA-on-frozen-weights recipe for release, at this rank.** Corpus-signal
strength is **exhausted as a lever** — measured, not suspected (D6). ⚠️ Rank was
held fixed on purpose, so D6 says nothing about *capacity*; a rank sweep is a
separate decision, and it was skipped with D6's endogenous-to-base reason logged.

> ⭕ **REOPENED for IDF-2 on 2026-09-26 — Wilson, on the input-axis argument.**
> See `docs/PREREG_IDF2_2026_09_26.md` §0. The entry closed the **corpus**
> axis. IDF-1/1b then showed D6's target was **not a function of the model's
> input**: the rule depended on bookkeeping no row carried, so D6 closed that
> axis **under a confound it could not see**. IDF-2 removes the confound and
> moves a different lever — the information in the input — at the same rank and
> recipe.
> ⛔ **The entry is NOT deleted and is NOT closed-in-general.** It stands for
> every other use, and the rank caveat above applies **unchanged** to IDF-2's
> FLOORS branch, which is scoped in that prereg's §6 to *"at this rank and this
> recipe"* for exactly this reason.

**F4's absolute branch as evidence FOR the claim.** It is a tripwire, not a
discriminator. A depth-1 Markov painter that ignores the prior turn entirely
scores **0/200 guard-fires**. It separates degenerate from healthy and has **no
power** to separate noise from convention.

---

## Notation

**`D_ctx` / `D_w` subscripts — RETIRED as trivially satisfied, NOT abandoned.**
Every Act-2 measurement to date is inference-only, so every number is `_ctx` by
construction and the subscript partitions nothing. ⛔ **The moment a fine-tune
enters an Act-2 measurement, `D_w` is live, the subscripts return, and the
prohibition — the two must never be reported under one word — is back in force
unamended.** Rung 1 would trigger exactly this.
