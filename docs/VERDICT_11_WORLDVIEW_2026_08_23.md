# VERDICT — Phase 11: both sets clear the gate. **The gate is wrong.**

**Date:** 2026-08-23 · **Spend:** $0.00, closed-form, no training
**Runs:** `runs/phase11_2.json` · `runs/phase11_3_rsa.json` ·
`runs/phase11_expression_check.json` · **530 tests**
No prereg for 11.1–11.2 (closed-form, named outcomes, no between-arm claim).

> **CR f₂ = 36.8 %, TAO f₂ = 39.7 %, both against a 25 % gate — OUTCOME B on
> both. And the RSA frontier on both is STILL identically zero at every α.**
>
> **The collision hypothesis is confirmed and it does not matter. `f₂` can be
> raised without raising the thing the phenomenon needs, so `f₂` is the wrong
> gate — and it has been steering the referent-set lever for two phases.**

---

## Provenance and expression-strip

**No source text was consulted, recalled or reconstructed at any compilation
step.** Both sets were built only from the distilled positions Nate wrote in the
brief. There was no expression to strip because none was ingested — a stronger
position than stripping after.

⭐ **Standing architectural commitment (Nate, 2026-08-23): if source text is ever
needed it lives in a separate lane that never touches this pipeline.** No loader
reads anything but a distilled referent file, so the separation is structural.

`tools/expression_check.py` — **clean, and red-proofed on 4 probes.** Every
referent in both sets traces to a position the brief declared; no quoted spans;
no name reads as a line (longest 8 words, cap 12). ⛔ It audits the **artefact**;
what a human read before writing the brief is Nate's to confirm, and nothing
downstream ever saw it.

⛔ **One real catch, from the red-proof:** my first citation regex was `P([1-5])`
— **narrower than the thing it had to match.** An invented `P9` failed to match
at all and was reported as *"cites no position"*: right verdict, wrong reason,
and `"P1. P9."` would have cited P1 and hidden the P9 entirely. Fixed to
`P(\d+)` + validate. It also caught a genuine quoted span in my own note for
T29, which I rewrote rather than loosening the check.

## 11.2 — the gate, four sets, measured identically

Yardstick checked first: the pipeline reproduces the banked archive **1.26**.

| set | utts | **f₂** | mean | med | p90 | max | H bits | outcome |
|---|---|---|---|---|---|---|---|---|
| archive 60 | 176 | 15.9 % | 1.26 | 1.0 | 2 | 5 | 0.214 | **A** |
| v2 46 | 191 | 10.5 % | 1.31 | 1.0 | 2 | 8 | 0.186 | **A** |
| **CR 36** | 68 | **36.8 %** | 2.49 | 1.0 | 6 | 6 | 0.846 | **B** |
| **TAO 36** | 68 | **39.7 %** | 2.37 | 1.0 | 5 | 6 | 0.832 | **B** |

⛔ Side by side, never subtracted — different referents, guard verified.
All 36 referents in both sets sayable; **72/72 subsets buildable, 100 %**.

### The mechanism check passed exactly as predicted

| set | mean deps | unique head | top head share | keep=0 share |
|---|---|---|---|---|
| archive | 1.50 | 43 % | 8 | 33.1 % |
| v2 | 2.11 | 17 % | 9 | 23.6 % |
| **CR** | **1.00** | 19 % | 6 | **50.0 %** |
| **TAO** | **1.00** | 14 % | 6 | **50.0 %** |

**Low depth + high sharing + high keep=0 share ⇒ high f₂.** The prediction was
written before the run and it held on both sets. The collision-from-cohort-
vocabulary hypothesis is **confirmed as stated.**

---

# ⛔⛔ 11.3 — and then the frontier came back zero on both

**CR: sup over all α = 0.00. TAO: sup over all α = 0.00.** Identically zero at
every α including α→∞, on sets whose mean |consistent| is 2.49 and 2.37.
Red-proof fires at **+48.11 pts**, so the estimator can report a positive.

⭐⭐ **I designed CR and TAO with d=1 on purpose, and that choice came straight
out of Phase 9's combinatorial finding. That is designing to the detector's
mechanism.** I said so in the tool before running it, and 11.3 was written as the
test of whether the resulting ambiguity was real or metric-specific. **It was
metric-specific.**

## Why — and this is the finding

| set | ambiguity at **full** utterance | frac ambiguous at full |
|---|---|---|
| archive | mean 1.13, max 3 | **10.0 %** |
| v2 | mean 1.00, max 1 | **0.0 %** |
| CR | mean 1.00, max 1 | **0.0 %** |
| TAO | mean 1.00, max 1 | **0.0 %** |

CR is **80.6 % ambiguous at keep=0 and 0.0 % at keep=1.** TAO: **86.1 % and
0.0 %.** All of the ambiguity sits in the one subset an optimising speaker will
never choose.

> ⭐⭐⭐ **`f₂` COUNTS AMBIGUITY THAT EXISTS. THE FRONTIER NEEDS AMBIGUITY THAT
> SURVIVES SAYING EVERYTHING.** With d=1 the speaker has exactly one escape and
> it always works, so an RSA speaker at any α > 0 takes the informative option,
> the naive listener follows it perfectly, and the gap is zero by construction.

⭐ **The two statistics are anti-correlated across these four sets.** The archive
has the **lowest f₂** (15.9 %) and is the **only** set with any irreducible
ambiguity (10.0 %). Raising f₂ moved the sets *away* from what the frontier
needs. Two measurements that agreed on two sets and disagree maximally on two
others — that is exactly when you learn which one measures the thing.

⛔ **And even the archive's 10 % was not enough** — its frontier was zero too
(Phase 8.1). So the frontier's requirement is *stronger* than any of the four
constructions meets, and it is not approached by raising f₂. What it appears to
need is referents where the speaker has **≥2 options and none fully resolves**;
we have never built one, and I do not claim to have derived the sufficient
condition — only that four sets fail it and one lever demonstrably does not
reach it.

---

## Where this leaves the fork

**Both worldview sets "cleared" the gate, and it is a false pass.** The gate
outcome and the frontier disagree, and **the frontier is the decision-relevant
one** — it is what Hole 1 is stated against.

> **THE REFERENT-SET LEVER IS EXHAUSTED, NOW MECHANISTICALLY AND NOT JUST
> EMPIRICALLY.** Four constructions — scatter (archive), depth+matrix-rule (v2),
> and two flat high-sharing worldviews (CR, TAO) — and the statistic used to
> steer the lever for two phases does not track the quantity that matters.
> The honest terminus holds. **Bank the instrument claim; Track B proceeds.**

⭐ **What Phase 11 bought, which is not nothing:** the terminus is now *explained*
rather than observed. "We tried four sets and they failed" is weak; **"raising
the steering statistic provably moves you away from the target"** is a result,
and it is the kind a referee can check.

⛔ **`f₂` is retired as a gate.** Any future set-design work targets ambiguity at
full utterance, or the frontier directly. Phase 9's Outcome A stands as recorded
— it was honest on its own statistic — but the *conclusion* drawn from it is now
supported by a better argument than the one it was drawn from.

## Do not quote

- **"CR and TAO cleared the gate"** without the frontier result. It is a false
  pass and quoting it alone inverts the finding.
- **Any f₂ as evidence of usable underdetermination.** That is the retired claim.
- **The thematic fit of either worldview as evidence.** CR's P5 — *identity as
  operation, not noun* — is literally this grammar's central rule, and Cosmicomics
  was also a perfect thematic fit at 10.5 %. Fit is why a world was chosen; it is
  never evidence that its set collides.
- Conservation, in any form. Phase 11 measures none of it.
- Any claim that a non-zero frontier is reachable — we have not built one.
