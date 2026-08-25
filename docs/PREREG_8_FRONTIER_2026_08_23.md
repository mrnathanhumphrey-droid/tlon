# PRE-REG — 8: the α-frontier, conservation, and population done right

- **Date:** 2026-08-23
- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `269f78d7` (sha256[:8] of draft body at lock, 2026-08-23T04:14Z)
- **Arc:** Tlön phase 8. Follows `VERDICT_7_AUDITOR_2026_08_22.md` (no KILL B
  verdict; superposition handed here) and `VERDICT_5_DENOTATION_2026_08_22.md`.
- **Lexicon:** `e2b8527010231a81fd31b6eeb9de3d8c` · **Referents:** 60, REVIEWED.

## Standing constraint for the entire phase

⛔⛔ **5 SEEDS PER CELL IS THE HARD FLOOR ON ANY BETWEEN-ARM CLAIM.** A one-seed
result may be recorded as *"direction only, not interpretable"* and may never be
compared to another cell. This applies to every table Phase 8 produces. Non-negotiable.

This is the first phase that can produce headline claims, so it is the phase most
exposed to the project's signature error: **treating a seductive result as
confirmation because the alternatives were never enumerated.** Each sub-phase
below states its falsifier before its hypothesis, and names the outcome most
likely to be misreported as success.

---

# 8.1 — Hole 1, via the RSA α-frontier

## Falsifier, stated first

**If our measured naive-listener gap sits at or below the RSA frontier at ANY
α ≤ α→∞, Hole 1 is NOT closed.** An honest speaker at that rationality could
produce our gap, and the pact claim reduces to **honest pragmatic
specialisation, RSA-explicable**. This is a real, enumerated outcome, not a
formality.

## Hypothesis

Our gap exceeds the frontier everywhere, including at α→∞ — the most-optimal
honest speaker, which produces the **largest** honest gap.

## Why a gap alone proves nothing

Chaabouni's partner-specific protocols produce a gap with no pact. An honest RSA
pragmatic speaker produces one too: it specialises its utterance choice toward
what a listener adapted to *it* will resolve, and a listener adapted to a
*uniform* speaker then does worse. That is honest specialisation and it is
exactly what our detector currently cannot rule out.

## Method — exact, not estimated

The RSA S₁ speaker is softmax-optimal in α, so the honest predicted gap is a
**function of α, not a number**.

    L₀(r | u)        = uniform over { r : consistent(u, sig_r) }      [EXACT]
    S₁^α(s | r)      ∝ L₀(r | u(r,s))^α
    L_adapted(r | u) ∝ S₁^α(s | r) · P(r)      Bayes listener for THIS speaker
    L_naive(r | u)   ∝ P_uniform(s | r) · P(r) Bayes listener for a uniform speaker
    gap_RSA(α)       = acc(L_adapted) − acc(L_naive),  both on S₁^α output

⭐ **L₀ is EXACT here** — LL(1) parse plus lossless denotation plus
`consistent()` — where every prior RSA application approximates it with a neural
net. **The frontier is computed, not estimated; the comparison carries no
model-slop term.** State this in the verdict; it is the methodological
contribution of 8.1.

α swept over a wide range plus the α→∞ limit (deterministic argmax-informative
selection), which is where the honest gap is maximal.

## KILL condition

**Hole 1 closed iff measured gap > frontier at α→∞, on ≥5 seeds, with the margin
reported.**

## ⛔ Misreport risk, named

**"Comparing against a single convenient α and calling it closed."** The
conventional α=1 comparison leaves *why that α?* wide open to a hostile reader.
Exceeding at α=1 is **not** sufficient and must not be reported as if it were.

---

# 8.2 — Conservation, falsifier-first

## Falsifier, stated first — all five outcomes enumerated BEFORE the run

Static conservation ("8–13 pts flat across arms") is fragile: one seed per cell
straddling a common mean is indistinguishable from a real invariant. The dynamic
test is strictly stronger — reset the whole pool mid-run and watch the gap
collapse and re-climb **within a single run**.

**Every re-climb pattern is a named branch the analysis code must explicitly test
for and be able to print. "Same level" is NOT the default branch.**

1. **Re-climbs to 8–13 pts (same level)** → consistent with conservation.
2. **Re-climbs to a different stable level** → conservation **FALSE**; the level
   is regime-dependent, not invariant.
3. **Re-climbs into a different carrier** (gap returns but the channel it
   occupies has moved) → **relocation**, not conservation of magnitude.
4. **Does not re-climb** → the gap was not a conserved pact but an artefact of
   the particular converged state.
5. **Re-climbs partially or unstably** → **inconclusive**; more seeds, no claim.

⛔ The `variance_confound` lesson: a verdict function that enumerated "flat" and
"rises" but not "falls" fell through to a loud default, and that default is the
only reason the result was read by hand. Here, **outcome 1 must not be the
fallthrough** — it must be one branch among five, so a re-climb to 8–13 cannot be
confirmed by a check that never considered the other four.

## Bode caveat — in the locked body on purpose

The waterbed effect (Bode's sensitivity integral) is the nearest formal
precedent, and it is a **theorem with stated conditions**. Ours would be
n-per-cell empirics. The analogy sharpens what a conservation claim would have to
look like — a stated invariant with conditions — and **does not lower the bar for
making it.**

⛔ **Conservation stays quarantined from every outward-facing artefact** until
this test returns outcome 1 on ≥5 seeds **and** the prior-art search remains
negative. A wrong conservation claim with a Bode analogy attached does more
damage than an obviously tentative one.

## ⛔ Misreport risk, named

**"Reading re-climb-to-same-level as conservation when the run count cannot
distinguish it from noise around a common mean."** The within-run dynamic signal
is what is supposed to beat that — **but only if collapse-and-re-climb is visible
per-run.** Averaging runs into a mean hides the dynamics and reinstates exactly
the weakness the dynamic test exists to remove. Per-run trajectories are reported.

---

# 8.3 — Population, done right

## Falsifier, stated first — three named outcomes

Population-only underperformed because rolling 1-of-6-every-500-steps is Li &
Bowling's **staggered** regime: each reset abrupt, but the pool average smooth,
which they identify as the regime that kills ease-of-teaching pressure. Their
mechanism is the **speaker's entropy spike** when its listener cannot understand
it; with a large pool the majority keeps reward high and the spike never fires.

Fix: reset the **whole pool at once, less often** — simultaneous reset.

1. **Entropy spike fires AND gap falls** → population is genuine pact mitigation.
2. **Entropy spike fires AND gap does NOT fall** → population raises
   compositionality **without** suppressing the pact. Population is the wrong
   tool for our purpose, and we say so.
3. **Neither fires** → the config is still wrong; no conclusion about population.

## ⛔ The conflation this sub-phase exists to avoid

Li & Bowling validate that abruptness increases **compositionality**. That is
**not** pact-suppression, and it could pull *against* it — a more structured
channel may offer more predictable free capacity to hide in. **The two effects
are measured separately:** (a) speaker entropy spike on reset — their Figure 13
reproduced in our setup; (b) naive gap before/after. Conflating them is the error
this sub-phase is designed not to make.

## Shared instrumentation

**The whole-pool reset IS the 8.2 dynamic-conservation reset.** One reset event,
three measurements: entropy spike (8.3a), gap re-climb pattern (8.2), gap level
change (8.3b). Instrumented off the same event, so they cannot disagree about
what happened.

---

## Standing floor (reportable regardless)

- **Solid:** Hole 1 closed, conservation shown dynamically on 5 seeds,
  population characterised. Claims 1–4 hold and claim 5 is earned.
- **Scoped down:** any of — gap ≤ RSA frontier at some α; conservation false or
  inconclusive; population uninterpretable. **This is a good outcome, not a
  failure.** A scoped-down Tlön remains *the first exactly-invertible testbed
  isolating pragmatic drift by construction* (Phase 6, confirmed in code), which
  is the novel-instrument claim and **stands regardless of what Phase 8 does to
  the conservation and λ=0 claims.**
- Either branch, the record gains the **α-frontier** — the exact-L₀ computation
  nobody else can do — and the **first properly-seeded measurements in the
  project's history.**

## Cost / lane

Local, $0. 8.1 is closed-form, no training. 8.2/8.3 share one seeded run.

## ⛔ BLOCKED — needs Nate's call

- **Lock this prereg.**
- Any decision to promote conservation out of quarantine, after the fact.
