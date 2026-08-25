# VERDICT — Phase 9: OUTCOME A. The bet failed, and the mechanism is interesting.

**PREREG:** `docs/PREREG_9_REFERENTS_2026_08_23.md`, LOCK `10757ac4`, VERIFIED
**Date:** 2026-08-23 · **Spend:** $0.00, all local, no training yet
**Runs:** `runs/phase9_2a.json` · `runs/phase9_2b_rsa.json` ·
`runs/drift_taxonomy_v2.json` · `runs/phase9_2a_diag.json`
⛔ **Read with `docs/DEVIATIONS_9_2026_08_23.md` — four entries, D1 is serious.**

**Gate outcome: OUTCOME A — STILL SCATTERED.** `f₂ = 10.5 %` against a
pre-registered 25 % gate. **v2 did not deliver the underdetermination the
instrument needs, and the phase says so.**

⭐ **This is the designed good outcome of a failed bet: the decision arrived
here, for $0.00 and before any training, instead of three phases downstream.**

---

## 9.2a — `f₂ = 10.5 %`. Gate is 25 %. OUTCOME A.

⛔ **The yardstick was checked against the banked record before it was used.**
The pipeline recomputes the archive set first and reproduced the banked
**1.26** exactly. Only then was v2 computed. A fresh derivation colliding with a
banked number is what caught the gate2b scheme error; here it agreed, so the v2
number is trustworthy.

| | archive 60 | **v2 46** |
|---|---|---|
| distinct utterances | 176 | 191 |
| **f₂ (\|consistent\| ≥ 2)** | **15.9 %** | **10.5 %** |
| mean \|consistent\| | 1.26 | **1.31** |
| median · p90 · **max** | 1.0 · 2 · **5** | 1.0 · 2 · **8** |
| H(r\|u) | 0.214 bits | 0.186 bits |
| `m_uniform_floor` | 0.906 | 0.930 |
| histogram | 1:148 2:15 3:9 4:3 5:1 | 1:171 2:8 3:4 4:2 **7:4 8:2** |

⛔ **Side by side, never subtracted** — different referents, no pairing exists,
and the 9.0 guard refuses the delta (verified in the run).

**Robustness, 12 draws per (referent, subset)** — v2 has 19 disjunctive roots and
11 randomly-relatored deep edges, so one draw understates the space: 1,088
utterances, **f₂ 7.9 %**, mean 1.19. **Lower, not higher.** The one-draw figure
is the generous one.

## 9.2b — the RSA frontier is STILL identically zero, and that is not a win

**0.00 pts at every α: 0, 0.25, 0.5, 1, 2, 4, 8, 16, 32, and α→∞.**
`sup` over all α = **0.00**. Red-proof fires at **+48.11 pts** on the hand-built
space and **+0.00 at α=0**, so the estimator *can* report a positive — the zero
is a fact about v2's utterance space, not about the computation.

⭐ **First run under the new bar** (Wilson's fix): `sup` over all α, not the
endpoint. It made no difference *here* because the frontier is flat at zero — but
that is the accident-of-the-value case the fix exists to stop relying on.

⛔ **Per the prereg this is EVIDENCE FOR OUTCOME A, not a free closure.** A
degenerate frontier means a near-deterministic space. **Two independent
measurements — `f₂` and the frontier — return the same reading.**
Hole 1's RSA horn stays closed on v2, and it stays closed for the same reason it
was closed before: there is nothing for an honest RSA speaker to produce.

## 9.3 — isolation RE-CONFIRMED on v2, and the guard got *more* live

`forbid` 0/50, `matrix` 0/50, so the claim carried over logically. It was
re-measured anyway, because the demonstration should be on the set the claim will
be made about.

| | archive | **v2** |
|---|---|---|
| utterances per arm | 7,240 | **8,440** |
| structural drift | 0.0000 % | **0.0000 %** |
| semantic drift | 0.0000 % | **0.0000 %** |
| mask rejects | 40 (**0.5 %**) | **440 (5.0 %)** |

⭐ **The rejection rate went up 10×**, which matters: a 0.0000 % drift reading
next to a dead guard is not evidence. On v2 the guard demonstrably bites.
Both measures red-proofed again (5 structural corruptions all caught; semantic
fires on a wrongly-grounded root).

⛔ **Scope, per D2:** *pragmatic drift is the sole possible mover on v2* holds as
a **structural** claim. Its **magnitude on v2 is unmeasured** — that is 9.2c.

---

# ⭐⭐ Why it failed: the matrix rule worked, and the combinatorics ate it

This is the real finding of Phase 9 and it was not anticipated by anyone.

### The rule hit its own target, cleanly

| bare head, undecorated | archive | **v2** |
|---|---|---|
| mean \|consistent\| | 1.73 | **2.61** |
| median | 1.0 | **2.0** |
| max | 4 | **8** |
| f₂ | 41.9 % | **50.9 %** |

**When the head is all you say, v2 is substantially more ambiguous than the
archive.** The matrix rule did exactly what it was for.

### But ambiguity by keep-size shows where it went

| dependents uttered | archive n / mean / f₂ | **v2 n / mean / f₂** |
|---|---|---|
| 0 | 60 / 1.78 / 43.3 % | **46 / 2.70 / 47.8 %** |
| 1 | 89 / 1.08 / 7.9 % | **86 / 1.02 / 2.3 %** |
| 2 | 32 / 1.00 / 0.0 % | **57 / 1.00 / 0.0 %** |
| 3 | — | **6 / 1.00 / 0.0 %** |

⭐⭐ **MOVING THE DISTINGUISHING MATERIAL OUT OF THE HEAD AND INTO THE
DEPENDENTS RAISES AMBIGUITY WHEN DEPENDENTS ARE WITHHELD AND LOWERS IT WHEN THEY
ARE UTTERED.** v2 beats the archive at keep=0 (47.8 % vs 43.3 %) and is *worse*
at keep=1 (2.3 % vs 7.9 %), because the dependents now carry everything that
tells referents apart.

⭐⭐ **AND DEEPER SIGNATURES SHIFT THE UTTERANCE SPACE TOWARD HIGH KEEP-SIZES,
WHERE THERE IS NO AMBIGUITY AT ALL.** More dependents ⇒ more subsets ⇒ most of
them keep ≥ 1. Archive: 60/176 = **34 %** of utterances at keep=0. v2:
46/191 = **24 %**. The two effects fight and **the second one won.**

> **DEPTH IS SELF-DEFEATING FOR UNDERDETERMINATION UNDER UNIFORM ENUMERATION OF
> SUBSETS.** Every dependent added makes the withheld case more ambiguous *and*
> makes the withheld case rarer, and the second effect is combinatorial.

⛔ **Honest scope on that statement.** `f₂` is computed over the **uniform
enumeration** of subsets, which is how Phase 8.1 computed it and is what the
prereg specified. **A trained policy does not sample subsets uniformly** —
Phase 4 found it learns to utter *less* (rate 0.47 vs 0.50) and to pick
informative dependents. So the `f₂` the trained system experiences may differ.
**This is a scope statement on the measurement, not a rescue of the result**: the
gate was pre-registered on this statistic and this statistic failed it.

### One confound cleanly killed

v2 has 11 referents with `aspect_root_any` vs the archive's 2, so a free
`aspect_root` decoration could have been doing the disambiguating. **It is not:**
stripping the head aspect moves v2 from mean 1.41 / f₂ 12.3 % to **1.41 /
12.3 %** — no effect at all. (Archive: 1.30 → 1.29, f₂ 18.2 % → 18.2 %.)
*These are per-(referent, subset) figures, not the deduped-utterance `f₂` of
9.2a; do not mix the two.*

---

## 9.2c — NOT RUN. It can still fire, but with reduced power.

Before spending a 5-seed training cell, the x-axis was checked: **a correlation
whose predictor has no variance cannot come back positive.**

`mean|consistent|_r` across the 46 live referents: **min 1.00, median 1.00, max
3.00, sd 0.632**, **24/46 (52 %) pinned at exactly 1.00**, only **10 distinct
values**. So the test is **not** dead on arrival — 22 referents do vary — but
half the sample contributes no rank information and the effective n is well
below 46. Combined with 5 seeds, **UNDERPOWERED (branch 4) is the likely
outcome**, which the prereg already names as honourable.

⭐⭐ **AND THE VARIANCE THAT EXISTS IS THE MATRIX RULE'S DOING.** The eight most
ambiguous referents are **M06, M07, M23, M01, M25, M09, M12, M43** — and seven of
those eight are referents the rule changed. **The rule failed to move `f₂` and
succeeded at creating the only x-axis 9.2c has.**

**Needs a call: spend the cell or not.** Also unrun: the **omission ceiling**
half of 9.2b, which needs the frozen auditor.

---

## What survives, stated conservatively

1. A conceptual pact forms at λ=0. *(Phase 4; unchanged.)*
2. An exact meaning-preserving paraphraser does not stop it. *(Phase 5.)*
3. Relocation, measured three times. *(Phases 4–5.)*
4. **The first exactly-invertible testbed isolating pragmatic drift by
   construction** — and as of today, **re-confirmed on a second, independently
   built referent set**, with the mask guard 10× more live. *(Phases 6 and 9.3.
   This is the novel-instrument claim and Phase 9 strengthened it.)*
5. No honest RSA speaker at any α can produce our gap — now on two sets.
6. ~~Conservation~~ — retracted, untouched by Phase 9.
7. **NEW, negative:** depth-by-nesting and a shared-matrix rule **do not** buy
   underdetermination under uniform subset enumeration, and the combinatorial
   reason is stated above.

## Do not quote

- **Any claim that v2 is "deeper" in a way that helped.** `f₂` fell, 15.9 % → 10.5 %.
- **The RSA zero as a Phase 9 win.** It is evidence for OUTCOME A.
- **Any 9.2c result** — not run. **Any omission-ceiling figure** — not run.
- **v2's pragmatic-drift magnitude.** Unmeasured; `phase5.json` is the archive's.
- Any first-run (50-referent) number — superseded, see D1.
- Conservation, in any form.
