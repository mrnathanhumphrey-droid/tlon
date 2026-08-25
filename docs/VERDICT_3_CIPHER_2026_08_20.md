# VERDICT — Phase 3, the cipher question

**PREREG:** `docs/PREREG_3_CIPHER_2026_08_20.md`, LOCK `3c49ad47`
**Date:** 2026-08-20 · **Spend:** $0.00, all local (RTX 5070 Ti)
**Runs:** `runs/phase3_v2.log` · `runs/phase3_sweep.json` ·
`runs/lambda_purchase.json` · `runs/baseline_scope.json` ·
`runs/variance_confound.json`

---

## Headline

**KILL A did not fire. No cipher formed at any lambda.** The worst
no-information scramble drop anywhere across eleven trained conditions is
**+0.30 pts**, against a pre-registered threshold of 1.0 and a defensible
threshold of 0.50.

**That null is worth something, but much less than it looks, and not for the
reason I pre-registered.** The prereg's own hedge was "pressure never got high
enough". The real answer is sharper and worse: **M was never scarce.** The
listener sat at 99.2-100 % from the first step, because the signature core
already determines the referent. A code is a solution to a communication
problem, and the generator never had one. The channels a cipher would have to
live in were redundant, so nothing pushed the listener to read them.

So the honest scope of the null is: *no cipher forms when the generator has no
reason to build one.* It is not evidence that the framework resists ciphering
under pressure. Making the failure reachable is a phase-4 design change and
needs a call (see **What this licenses next**).

## KILL A, stated against the locked criteria

| condition | worst no-info scramble | KILL A (1.0) |
|---|---|---|
| v2 sweep, lambda 0 / 0.25 / 0.5 / 1 / 2 | +0.00 / +0.20 / +0.10 / +0.09 / +0.00 | no |
| variance control, raw, lambda 0 / 1 / 2 | +0.12 / +0.15 / +0.00 | no |
| variance control, normalised, lambda 0 / 1 / 2 | +0.12 / +0.30 / +0.00 | no |

**Could this test have come back positive?** Yes, and that is load-bearing.
The same probe, on the same runs, reports **+3.01 to +4.59 pts on
`aspect_root`** — a channel the signature genuinely uses. It sits inside the
null band's honest figure of **+4.01 ± 0.52** measured over five seeds.
`orient_order` returns **+0.00 on every seed and every cell**, which is the
canonicalisation proof. The probe was live throughout; the null is a real null,
within its scope.

## The sign anomaly, and what it cost to resolve

The v2 sweep reported repetition cost R **rising** with lambda: 0.193 -> 0.237.
Novelty pressure producing more repetition is the wrong sign, and it was the
only thing in an otherwise clean sweep that could not be explained by the
framework working. Three controls, in order:

**1. `lambda_purchase.py` — does lambda have any grip on the action space?**
Refuted the easy explanation. R *is* action-steerable: within-state sd
**0.1129** across 64 distinct free-channel actions at fixed state, signal-to-noise
**1.284**, and only 6 of 120 states returned an identical R for every action.
The novelty term genuinely takes over the reward, from 0 % of felt magnitude at
lambda=0 to **76.4 %** at lambda=2. Total advantage magnitude grows only
**2.17x**. Lambda was turning a real knob.

**2. `baseline_scope_control.py` — is the global advantage baseline the driver?**
Hypothesis: R varies strongly by referent (across-state sd 0.0880, ~78 % of the
within-state signal), and a single global EMA leaves all of that in the
advantage, so actions get reinforced for *which referent came up*.
**FALSIFIED.** Per-referent baselining left lambda=2 concentration essentially
unchanged (0.774 -> 0.748) and merely degraded lambda=0 (0.356 -> 0.652).

> This control's verdict function printed **PREDICTION HELD**. It was wrong. It
> keyed on two endpoint comparisons — "did concentration fall vs global" and
> "did R fall vs lambda=0" — both of which passed because the *lambda=0*
> endpoint got worse, not because lambda=2 improved. A verdict can only report
> outcomes it was written to recognise. See
> [[feedback_verdict_functions_need_a_branch_per_outcome]].

**3. `variance_confound_control.py` — is it step size?** Lambda multiplies a
reward term, so it raises advantage *variance* as well as novelty *weight*, and
REINFORCE collapses faster under larger steps. Normalising the advantage by its
running sd holds step magnitude fixed while lambda still sets the weight.

| advantage | lambda=0 | lambda=1 | lambda=2 |
|---|---|---|---|
| raw — concentration | 0.356 | 0.703 | **0.774** |
| raw — R | 0.193 | 0.213 | **0.237** |
| normalised — concentration | **0.825** | 0.758 | 0.733 |
| normalised — R | **0.384** | 0.239 | 0.258 |

**Both metrics reverse direction.** With step magnitude fixed, higher lambda
*lowers* concentration and *lowers* repetition — the designed behaviour.

**Therefore the raw sweep's lambda axis is not interpretable as novelty
pressure, and reads backwards.** Any statement of the form "at lambda=X the
system did Y" from `runs/phase3.log` or the raw arm of `phase3_sweep.json` is
confounded with step size. This does not change KILL A, which is flat across
every cell in both arms.

> This control's verdict function fell through to its loud fallback:
> *UNRECOGNISED PATTERN*. Correct behaviour — I had enumerated "flat" and
> "rises" but not "falls", because I did not believe lambda could reduce
> concentration. The fallback is the only reason the result was read by hand
> instead of forced into a branch. The branch has since been added.

## Two claims that were being conflated

**Concentration is not a cipher detector.** It measures how *deterministic* the
generator became. A cipher additionally requires the listener to *read* the
concentrated channels. The v2 sweep separates them cleanly: concentration
**0.774** with every no-information channel at **<= 0.20 pts** is a fixed
**idiolect**, not a code — the generator settled on a house style that carries
nothing.

Under every condition tested, concentration lands at **0.73-0.83** against a
uniform baseline near 0.15. **The policy collapses to an idiolect regardless.**
What lambda controls is how much, not whether. Within 4 000 steps, this
table-of-logits parameterisation is going to become deterministic; that is a
property of the optimiser and the horizon, not a finding about novelty.

## Auditor (KILL B)

**Did not fire, and could not have as specified.** Coarse 4-way against
root-disjoint distractors: **48.5 / 48.5 / 46.5 / 48.0 / 49.5 %** across the
lambda sweep, flat, and *above* the 43.8 % validated honest baseline (chance
25 %). No fall to detect.

KILL B's threshold still needs restating and remains an open deviation: "falls
> 10 pts" is over half the usable 43.8 -> 25 band. Express as a fraction of the
honest-to-chance band with seed variance. **Record as a deviation from
`3c49ad47`, not an edit.**

## Detector order

Pre-registered prior: concentration moves first (cheapest), scramble probe is
sharpest, gloss auditor is the coarsest. **Partly wrong.** Concentration did
move first and hardest — but it moved on a confound, and moved identically in
conditions with and without any cipher, so it turned out to carry no
information about the question it was deployed to answer. The scramble probe
was the only detector that discriminated at all, and it discriminated in the
honest direction (`aspect_root` +3 to +4.6, everything else ~0).

## What this licenses next — NEEDS A CALL

⛔ Backbone model and phase progression are Nate's call, every time.

1. **Make M scarce.** The cipher failure is unreachable while the signature core
   hands the listener the answer for free. Mask or corrupt part of the core so
   the listener genuinely needs the free channels, then re-run. Until then
   phase 3's null is scoped to "no reason to cipher".
2. **Normalise the advantage by default**, or drop lambda-sweeping REINFORCE for
   something whose step size does not scale with the objective's weights.
3. **Retire concentration as a cipher detector**, or keep it explicitly labelled
   as a diversity metric. It answered a different question than the one it was
   assigned. See [[feedback_a_narrower_check_answers_a_different_question]].
4. Restate KILL B's threshold as a deviation.
5. Northern hemisphere ablation (B3: must denote into the same `Scene` algebra).

## Do not quote

- `runs/phase3.log` — phase 3 **v1**, invalid. REINFORCE with no baseline; the
  tell is concentration 0.92 at lambda=0. Includes a `degree +0.55` figure that
  reads like a hit and is not.
- The **raw** arm of the v2 lambda trend, as novelty pressure. Confounded with
  step size; reads backwards.
