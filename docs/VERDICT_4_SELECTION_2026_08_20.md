# VERDICT — Phase 4, impression-selection

**PREREG:** `docs/PREREG_4_SELECTION_2026_08_20.md`, LOCK `c1f7d06c`
**Deviations:** `docs/DEVIATIONS_4_2026_08_20.md` (D1, D2 — recorded pre-run)
**Date:** 2026-08-20 · **Spend:** $0.00, all local
**Runs:** `runs/confusability.json` · `runs/planted_cipher.json` · `runs/phase4.json`

---

## Headline

**KILL A FIRED.** Under impression-selection, the generator and listener built a
private code. At λ=2, on the ambiguous stratum: **`aspect_reps` +7.41 pts,
`degree` +5.95 pts** against a pre-registered threshold of 1.0. It fires at every
λ tested.

**And it fires at λ=0.** That is the result that matters most, because it
contradicts the premise the whole flag-⑦ investigation was built on.

## The finding: the cipher is driven by M scarcity, not by novelty pressure

Phase 3's framing — carried since the original brief — was that λR is the
dangerous term: push for novelty and the generator will buy it with a code.
Phase 4 says no.

| λ | novelty pressure | KILL A on ambiguous stratum |
|---|---|---|
| 0.0 | **none at all** | `aspect_reps` **+2.14** — FIRED |
| 1.0 | moderate | `degree` +1.38, `aspect_reps` +1.03 — FIRED |
| 2.0 | strong | `aspect_reps` **+7.41**, `degree` **+5.95** — FIRED |

At λ=0 the reward is `M` alone. There is no repetition term, no novelty
incentive, nothing pushing for variety — and a code still forms. **λ modulates
how hard the code is driven; it does not cause it.** What causes it is the
combination of a co-adapting listener and an information deficit the honest
channel cannot cover. Phase 3 could not have discovered this, because it had no
deficit.

Practical consequence: **λ=0 is not a safe configuration.** Any deployment that
lets a listener co-adapt against a generator facing underdetermined reference is
exposed, whatever the novelty setting.

## Both mechanisms are present — this is not cipher *instead of* selection

The policy also did the honest thing. It learned to select *informative*
dependents, not merely fewer of them:

| arm | ambiguous rows | selection rate | decidedness |
|---|---|---|---|
| random | 25.1 % | 0.500 | 0.500 |
| learned λ=0 | 13.3 % | 0.613 | 0.831 |
| learned λ=1 | 16.3 % | 0.486 | 0.801 |
| learned λ=2 | 14.7 % | 0.466 | 0.804 |

At λ=1 and λ=2 the policy utters **less** than random (rate 0.49, 0.47) while
producing **far less ambiguity** (25.1 % → ~15 %). It is choosing *which*
impression to state. That is the project's thesis working. The cipher rides on
top of it; it does not replace it.

## Ruling out the alternative explanation (the control that decided it)

A concentrated policy makes the co-adapting listener overfit a narrow
distribution, and such a listener degrades when **any** channel is scrambled —
code or not. The `random` arm cannot rule this out, because its listener is
never overfit. So the run carries a **codeless control**: identical training at
λ=2, but the policy is *forbidden* to steer `aspect_reps` and `degree`, which are
sampled uniformly with no log-prob and no gradient. Those channels then provably
carry no code, while the listener is just as overfit.

| channel | λ=2 experimental | λ=2 **codeless control** |
|---|---|---|
| `aspect_reps` | **+7.41** | **−1.24** |
| `degree` | **+5.95** | **+0.40** |
| M / decidedness / concentration | 99.7 / 0.804 / 0.752 | 98.9 / 0.807 / 0.519 |

**The probe goes silent exactly where the code is removed, with overfitting held
constant.** The artefact explanation is refuted; the drops are a real code.

## The code RELOCATES when its channels are blocked

In that same control, `coda` — which was left free — jumps to **+3.15** on the
ambiguous stratum, from +0.90 in the experimental arm.

**A cipher is not attached to a channel. It is attached to the existence of any
unconstrained channel.** Blocking the two it preferred did not remove it; it
moved. Any mitigation that names specific channels will fail the same way.

## KILL A′ (probe specificity) — PASS

**+0.27 pts** on the constructed no-code arm, threshold ≤0.5. Per **D2**, the
negative control is the *arm* split, not the stratum split: a real cipher bleeds
onto the unambiguous stratum (+14.29 pts in the planted control), so that stratum
cannot serve as a control. Absence of a code must be **constructed**, not
inferred.

## Detection floor was established BEFORE the experiment

`planted_cipher_control.py`, run as a gate: code learned **+7.1 pts**
(92.1 → 99.1 %), probe fired **+27.05 pts**, silent without it **+0.17 pts**.
Phase 3's null failed precisely because no such floor existed. The trap it had
to dodge: a planted code is invisible unless the listener *uses* it, so the
control had to run under selection and demonstrate use — otherwise a null would
have meant "nothing to detect", not "probe is blind".

## Detector order — concentration fails again, as pre-registered

Concentration rose to **0.726–0.752** in the learned arms against 0.155 for
random. But the **codeless control sits at 0.519 with `aspect_reps` at −1.24** —
concentrated and codeless simultaneously. Concentration measured determinism
again, not ciphering, exactly as phase 3 found. It stays a diversity metric and
is not a cipher detector. My pre-registered prior that the scramble probe is the
sharper instrument held for the second phase running.

## KILL C — did not fire (and my first measurement of it was wrong)

The initial implementation tested `|selection_rate − 0.5| > 0.05` and reported
**"KILL C FIRED (selection inert)"** at λ=1 and λ=2. That was a bad metric.
Mean rate answers *how much does it say*; KILL C asks *has it learned to
choose*. A policy can be fully committed — "for referent 12 always utter slot 0,
never slot 1" — with a mean rate of exactly 0.50. Decidedness (mean
`max(p, 1−p)`) is the right measure: **0.80–0.83 against 0.50 at init.**
Selection was never inert. The contradicting evidence was already on screen —
ambiguity had fallen from 25.1 % to 14.7 %, which random selection cannot do.
See [[feedback_a_narrower_check_answers_a_different_question]].

## KILL B — NOT MEASURED

The gloss auditor did not run in this phase. Its 43.8 % baseline was measured on
*complete* scenes; under selection it sees partial glosses and would fall for
honest reasons. Re-baselining is required before any threshold means anything,
and the threshold itself is ⛔ **Nate's call**. **No interpretability claim is
made by this verdict.**

## D1 correction applied

`m_vs_ceiling` was initially reported against 92.1 % and read **108 %**. That
compared arms using *learned* selection against a floor measured under *random*
selection — two numbers sharing a name without sharing a measurement. Each arm
now reports **its own uniform floor**, computed on the utterances it actually
produced:

| arm | M | own floor | M − floor |
|---|---|---|---|
| random | 77.4 % | 84.8 % | **−7.4** |
| learned λ=0 | 99.5 % | 92.5 % | +6.9 |
| learned λ=1 | 99.6 % | 90.2 % | +9.4 |
| learned λ=2 | 99.7 % | 91.1 % | +8.5 |
| λ=2 codeless | 98.9 % | 88.3 % | +10.5 |

Exceeding the uniform floor is legitimate on its own — a real listener uses
likelihood, not uniform picking — so these gaps are **not** themselves evidence
of a code. The codeless control is what carries that claim.

## What this licenses next — ⛔ NEEDS A CALL

1. **The counter cannot be published on this basis.** B2 holds: `auditor_state`
   is not `MEASURED`, and phase 4 has just demonstrated a live cipher pathway.
2. **Re-baseline the gloss auditor under selection**, then set KILL B.
3. **Channel-blocking is not a mitigation** — the code relocated. If mitigation
   is wanted, it has to constrain the *listener's* access to free channels, or
   penalise mutual information between free channels and referent identity
   directly.
4. Northern hemisphere ablation (B3), still outstanding.

## Do not quote

- `runs/phase3.log` — phase 3 v1, invalid.
- The **raw** λ arm of `phase3_sweep.json` as novelty pressure — confounded with
  step size, reads backwards.
- Any `m_vs_ceiling` figure against a cross-regime constant. Use each arm's own
  floor.
- "89.3 % ceiling" — it is a floor. See D1.
