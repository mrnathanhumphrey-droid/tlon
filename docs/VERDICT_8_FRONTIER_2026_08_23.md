# VERDICT — Phase 8: Hole 1's RSA horn closed; conservation's evidence is gone

**PREREG:** `docs/PREREG_8_FRONTIER_2026_08_23.md`, LOCK `269f78d7`
**Date:** 2026-08-23 · **Spend:** $0.00, all local
**Runs:** `runs/rsa_frontier.json` · `runs/reset_dynamics.json`

**Gate outcome: SCOPED DOWN.** One horn of Hole 1 is closed analytically.
Conservation's supporting evidence is dead. 8.2's dynamic test was not run.

---

## 8.1 — The honest RSA frontier is identically ZERO. Hole 1's RSA horn is closed.

| α | L_adapted | L_naive | honest gap |
|---|---|---|---|
| 0 | 97.1 % | 97.1 % | **0.00** |
| 1 | 98.4 % | 98.4 % | **0.00** |
| 8 | 100.0 % | 100.0 % | **0.00** |
| **→ ∞** | 100.0 % | 100.0 % | **0.00** |

Not small — zero, at every α including the limit.

**Why, and this is the general result rather than a fact about our data:** an RSA
speaker concentrates on utterances where `L₀(r|u)` is *higher*, i.e. where fewer
competitors are consistent. **Those are exactly the utterances a naive listener
also resolves well.** Concentration toward informativeness helps both listeners
equally. A gap would require the speaker to concentrate on *less* informative
utterances, which honest RSA never does.

### It took three red-proofs, and the first two failed on the test, not the code

1. Hand-built synthetic space → 0.00. **Bad test case.**
2. Anti-RSA speaker (negative α) on the real space → 0.00. **Also uninformative** —
   the real space is too unambiguous for any speaker policy to matter.
3. Hand-built space where the gap is derivable by hand → **+48.11 pts at α=8,
   +0.00 at α=0**, both matching the prediction written before running.

Only after (3) is the zero trustworthy. Working out *why* (1) and (2) failed is
what produced the mechanism above.

### KILL condition, evaluated on 5 seeds

Measured gaps: **+4.56, +5.39, +9.04, +10.15, +13.19**. Every seed exceeds the
frontier maximum of 0.00 at every α.

> **Hole 1's RSA horn is CLOSED. Our gap cannot be honest pragmatic
> specialisation, because honest pragmatic specialisation produces nothing here.**

⭐ **Methodological contribution:** `L₀` is exact — LL(1) parse, lossless
denotation, `consistent()` — where every prior RSA application approximates it
with a neural net. The frontier is **computed**, and the comparison carries no
model-slop term.

### ⛔ The horn that is NOT closed

The frontier assumes **Bayes-optimal listeners**. Ours are neural. The surviving
alternative explanation is **listener suboptimality and train/test distribution
mismatch**, which the frozen arm addresses separately (≤3.73 pts, subtracted) and
which 8.1 does not touch. Hole 1 had two horns; one is closed cleanly and the
other is where it was.

---

## 8.2 — NOT ANSWERED. The classifier was written and never called.

**No trajectory was measured.** `reset_dynamics.py` records only the end-state
gap, so there is no collapse-and-re-climb evidence. The five-branch classifier —
with "same level" deliberately kept off the default path, per the locked prereg —
**exists in the file and is never invoked.** I built the guard and did not wire
it up. None of the five outcomes can be reported.

### But the static conservation evidence is now dead, and that is a real result

| | range |
|---|---|
| Phase 5 across four different interventions | **+8.00 to +13.33** |
| **Phase 8, one configuration, five seeds** | **+4.56 to +13.19** |

**Within-arm seed spread equals the across-arm spread that suggested
conservation.** Mean +8.46, sd 3.17. The apparent invariance of the gap across π,
population, both, and neither is **fully accounted for by seed noise in a single
configuration.**

This does not prove conservation false — the dynamic test is what could do that,
and it was not run. It removes the evidence that motivated the claim.

⛔ **Conservation stays quarantined, now with a stronger reason than before.**
Per the locked prereg it required outcome 1 on ≥5 seeds; it has instead lost its
static support on the first properly-seeded measurement in the project's history.
**The 5-seed floor did its job on first application.**

---

## 8.3a — No entropy spike, and the measurement is confounded

Entropy **fell** in every seed on simultaneous whole-pool reset: −6.8, −11.4,
−8.2, −3.1, −5.4 % (mean −7.0 %).

⛔ **Not interpretable.** Policy entropy declines monotonically as training
converges, and I compared windows before/after the reset **within a single run**,
so the convergence trend swamps any transient spike. **This is the unpaired-
comparison error for the third time in this project** (phase-3 contaminated
cipher control; phase-7 floor curve; here).

**The fix is a paired no-reset control** at the same seeds: spike = entropy(reset
run) − entropy(no-reset run) at matched step. Until that runs, Li & Bowling's
teachability pressure is **untested in our setup**, and outcome 3 ("config still
wrong") cannot be distinguished from "measurement still wrong".

## 8.3b — Population's effect on the gap

Mean gap after simultaneous reset and reconvergence: **+8.46 ± 3.17**. Phase 5's
staggered-reset population arms sat at +7.07 / +10.44. **Indistinguishable given
the seed spread.** No evidence that simultaneous reset changes the gap; also no
power to detect a change smaller than ~3 pts.

---

## What survives, stated conservatively

1. **A conceptual pact forms at λ=0** — under pure comprehension pressure, no
   incentive to hide. *(Phase 4; unchanged.)*
2. **An exact, provably meaning-preserving paraphraser does not stop it.**
   *(Phase 5; unchanged.)*
3. **Relocation, measured three times.** *(Phases 4–5; unchanged.)*
4. **The first exactly-invertible testbed isolating pragmatic drift by
   construction** — structural and semantic drift pinned at 0.0000 % over 7,240
   utterances per arm, both measures red-proofed. *(Phase 6; unchanged, and this
   is the novel-instrument claim that stands regardless of everything above.)*
5. **NEW: no honest RSA speaker at any α can produce our gap** — the frontier is
   identically zero, computed against an exact `L₀`. *(Phase 8.1.)*
6. ~~Conservation~~ — **retracted to unproven.** Static evidence is seed noise;
   dynamic test unrun.

## The convergent finding nobody planned

**Three independent measurements now say the referent set is too shallow:**

- Phase 7: strongest constructible omission-pact = **0.8 pts** against a 7.9 pt
  detector ceiling, because ≤2 dependents leaves no room to withhold adversarially.
- Phase 8.1: RSA frontier **identically 0**, because mean `L₀` consistency-set
  size is **1.26** — the utterance space is nearly unambiguous.
- Phase 8.3b: no power to detect a <3 pt population effect at 5 seeds.

Each arrived from a different direction and none was looking for it. **The
referent set is now the binding constraint on what this instrument can measure**,
which makes the deferred referent-set decision a measurement question as well as
an artistic one.

## ⛔ Next — needs a call

1. **Wire and run 8.2 properly**: per-window gap trajectory across the reset,
   five-branch classifier actually invoked. Cheap; the run already exists in
   skeleton.
2. **Paired no-reset control for 8.3a.** Same seeds, no reset, subtract.
3. **The referent-set decision** is now three-way load-bearing (Phase 7 ceiling,
   8.1 frontier, 8.3b power) and still, correctly, an artistic call.

## Do not quote

- Conservation. Any form. Quarantined.
- Any 8.2 outcome — none was measured.
- "No teachability spike" — confounded by the convergence trend.
- Phase-5's "8–13 pts everywhere" as evidence of invariance; it is seed noise.
