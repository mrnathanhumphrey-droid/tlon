# Tlön — brief for Wilson

**2026-08-22 · `D:\Tlon` · $0.00 spent, everything local on one 5070 Ti · 492 tests**

Every figure below is copied out of the artefact named beside it, not recalled.
Where a number is superseded, the superseded value is shown too, because in this
project the retractions have been more informative than the results.

---

## 1. What it is

A system that describes the world in **Tlönian** — Borges' southern hemisphere:
impersonal verbs plus monosyllabic adverbial particles, **no nouns**. The public
artefact is a **"days since repetition" counter**.

The constraint that makes it more than a toy came out of phase 0.

**Q3 = 1, Q4 = 3.63e41.** A fixed *scene* has exactly one canonical surface form.
There is no paraphrase — no "the cat sat on the mat" / "on the mat sat the cat".
So the only way to not repeat yourself is to have **noticed something different
about the world**. The counter measures days since the same *impression*, not
days since the same string.

⛔ Q4 bounds the grammar's capacity, **not** the entropy of lived experience. The
correct phrasing is "the grammar will never be the bottleneck", never "the
counter cannot expire".

## 2. The question the project is actually asking

Two demands that fight:

- **never repeat yourself**
- **be understood**

Satisfy only the first and you emit noise. Satisfy only the second and you say
one reliable thing forever. Sustained honest novelty requires perceiving
differently, over and over, without leaving comprehension.

**Can a system be endlessly novel and still genuinely understood — or does
"never repeat yourself" always collapse into nonsense or into a private code?**

## 3. Where it stands: it collapses into a private code, and we cannot stop it

Five phases. The headline in one line: **the generator and its listener invent a
private cipher, and every mitigation we have tried relocates it rather than
removing it.**

### Phase 3 — the null that meant nothing

KILL A did not fire; worst no-information scramble drop **+0.30 pts** over 11
conditions. Worthless, and *not* because the probe was blind — the same runs
report **+3.01 to +4.59 pts** on `aspect_root`, inside a 5-seed null band of
**+4.01 ± 0.52**.

It was worthless because **M was never scarce**. The listener sat at 99.2–100 %
from step one — the signature core handed it the referent. A code solves a
communication problem the generator never had. Honest scope of that null: *no
cipher forms when there is no reason to build one.*

Also from phase 3, and it invalidated our own published direction: **λ multiplies
a reward term, so sweeping it also sweeps advantage variance (2.17×).** REINFORCE
collapses faster under bigger steps. Normalise the advantage and both metrics
**reverse** — concentration 0.825→0.733, R 0.384→0.258. The raw λ axis reads
backwards. *(`runs/lambda_purchase.json`, `runs/variance_confound.json`)*

### Phase 4 — make M scarce, and the code appears

Fix: **impression-selection.** The generator utters only a *subset* of the
scene's dependents, so reference becomes underdetermined. This is the project's
own thesis, not an imposed impairment.

Licensed by a pre-check (`runs/confusability.json`): uniform-posterior floor
**0.8930**, **0 mutually indistinguishable pairs**, 8 asymmetric containments,
mean consistent referents **1.133 → 1.322 → 1.469** at 0/1/2 dependents dropped,
**26/60** referents with a head root unique to them.

**KILL A fired** (`runs/phase4.json`, ambiguous stratum):

| arm | M | `aspect_reps` | `degree` | `coda` |
|---|---|---|---|---|
| random | 0.7740 | 0.0000 | −0.0091 | 0.0000 |
| learned λ=0 | 0.9947 | **+0.0214** | +0.0056 | +0.0050 |
| learned λ=2 | 0.9967 | **+0.0741** | **+0.0595** | +0.0090 |
| λ=2 **codeless ctrl** | 0.9887 | **−0.0124** | +0.0040 | **+0.0315** |

Three things in that table.

**It fires at λ=0**, where the reward is M alone and there is no novelty term at
all. **The cipher is driven by M scarcity, not by novelty pressure.** The
flag-⑦ framing this project was built on — that λR is the dangerous term — is
wrong. λ=0 is not a safe configuration.

**The codeless control decides it.** Forbid the policy to steer
`aspect_reps`/`degree` (uniform, no gradient) and the probe goes to **−0.0124 /
+0.0040** with overfitting held constant (M 0.9887, decidedness 0.807). The
"overfit listener is brittle to any perturbation" explanation is refuted.

**The code relocates.** In that same control `coda`, left free, goes
+0.0090 → **+0.0315**. A cipher attaches to the *existence of a free channel*,
not to a channel.

Honest selection happened too, separately: ambiguity 25.1 % → 14.7 % while the
policy uttered **less** than random. The thesis works; the cipher rides on top.

### Phase 5 — remove the channel class and the private partner

Two moves. **π**, a denotation projection: the listener sees only what can bear
on reference, and R is computed on the same object. The strip-list is *derived*
from the schema — a `NodePattern` can constrain only
`root_any · orient_any · aspect_root_any · edge_relator_any · via · at_depth`, so
`degree`, `force`, aspect-reps, `modal`, `tense`, `quant` are provably
non-denoting. **The derivation found three fields (`modal`, `tense`, `quant`)
that my hand-written list had missed.** And **population**: K=6 listeners, one
reset to fresh every 500 steps.

π does exactly what it claims (`runs/pi_controls.json`) — same 2-bit code:

| | accuracy | vs baseline |
|---|---|---|
| π, no code | 0.9269 | — |
| π, code in **stripped** channel | 0.9239 | **−0.30 pts** |
| π, code in **surviving** channel | 0.9902 | +6.32 pts |
| **no π**, code in stripped channel | 0.9936 | **+6.67 pts** |

Receptor gone, not discouraged. And it did not help.

**`runs/phase5.json`.** `code` = naive-listener gap minus the frozen arm's gap.
`ar vs frozen` = `aspect_root` drop minus the same in the frozen arm.

| arm | λ | M | `ar` vs frozen | **code gap** |
|---|---|---|---|---|
| phase-4 replication | 0 | 0.9967 | +0.1061 | **+0.0800** |
| phase-4 replication | 2 | 0.9980 | +0.1542 | **+0.1220** |
| π only | 0 | 0.9980 | +0.2071 | **+0.0840** |
| π only | 2 | 0.9913 | **−0.0282** | **+0.0907** |
| population only | 0 | 0.9967 | **−0.0700** | **+0.1333** |
| population only | 2 | 0.9771 | −0.0048 | **+0.0884** |
| **BOTH** | 0 | 0.9948 | **−0.0520** | **+0.1168** |
| **BOTH** | 2 | 0.9806 | +0.0048 | **+0.1019** |

**KILL E fired in 4 of 8, including BOTH at both λ.** The scramble probe goes
clean in five arms. The naive gap never moves — **8 to 13 points in every arm**.

> KILL E was written into the locked prereg (`c09d0fb3`) *before the run* as "the
> outcome I am most likely to misreport, because it looks like success."

⚠️ **One seed per cell.** This supports "8–13 points everywhere". It does **not**
support any between-arm comparison, and I am not claiming population made λ=0
worse.

## 4. The three findings we would defend

**1. The cipher is caused by an information deficit plus a co-adapting listener.
Not by novelty pressure.** It forms at λ=0.

**2. Channel-level mitigation cannot work — relocation, three times.** Block two
channels → moves to `coda`. Squeeze `aspect_root` with population → moves to the
decoration. Close that with π → stops being visible anywhere while the gap holds.

**3. Concentration is not a cipher detector, and the scramble probe only locates.**
Phase 4: concentration 0.752 with every no-info channel ≤0.009 is a fixed
*idiolect*, not a code; the codeless control sits at 0.519 while its `aspect_reps`
reads −0.0124. The only measure that tracked the code across every intervention
is the **naive-listener gap** — a judge trained solely on honest random-generator
data that never enters the loop.

## 5. Where we want your eye

**(a) The naive gap's baseline.** Its reference is a **frozen-listener** arm — the
generator optimises but the listener never updates, so co-adaptation is
impossible and a code cannot exist. Frozen gaps: **−1.27, −1.27, +1.60, +3.73**.
Is that the right null? It still permits *one-sided* adaptation — the generator
tailoring to a fixed partner's quirks — which is arguably a weak form of the
thing we are measuring.

**(b) Is 8–13 points actually conserved, or are we fooling ourselves?** It is
suspiciously flat across four very different configurations. Needs 5 seeds per
cell before anyone says "conserved".

**(c) What attacks the incentive rather than the channel?** Our two candidates:
penalise mutual information between free channels and referent identity
directly; or the clarification bound below.

**(d) Deferred, and we think it is the strongest public-facing detector.**
Conversational repair — let the listener ask "what do you mean?". It does *not*
fix the leak (it is a wider back-channel and a better training signal for
building a code). But: we have measured how often a partial utterance is
genuinely ambiguous, and **an honest listener cannot ask for help less often than
the world is ambiguous.** That is a bound, not a heuristic, and unlike scramble
probes it is legible to an outsider.

**(e) KILL B is unmeasured.** The gloss auditor (frozen Qwen2.5-1.5B) was
baselined at **43.8 % vs 25 % chance** on complete scenes; under selection it
sees partial glosses and would fall for honest reasons. **No interpretability
claim is made anywhere in phases 4 or 5.**

## 6. Method, and the failure mode worth knowing about

**PREREG → run → VERDICT, locked by sha256 of the draft body** (`tools/lock_prereg.py`,
adopted from Nate's `D:\IC_experiments`). Hypothesis, falsifier, KILL conditions,
priors to lose, must-beat baselines. Corrections are recorded as **deviations**,
never edited into a locked body.

That machinery earned its keep. Phase 5 produced **five** deviations, and every
one is the same mistake:

> **Treating zero as the default for a quantity nobody measured.**

- The "89.3 % ceiling" was a *floor* — `E[1/|consistent set|]`, uniform picking.
  A real listener hit 92.1 %, above the "ceiling".
- `aspect_root` carried a 1.0 pt threshold with no baseline. The honest drop is
  large: frozen arms, where a code is **structurally impossible**, still read
  **+0.2489 / +0.1195 / +0.2621 / +0.1882**.
- Under π, `aspect_reps` is constant, so scrambling it is a distribution shift,
  not information removal. It read +0.00 at λ=0 and +7.84 at λ=2 with the channel
  constant in both — what scaled was overfitting.
- A control that read **0.00 by construction**: `tr.train` seeds from a fixed
  default, so the "independent" naive judge was **byte-identical** to the
  listener it was judging. It could not have come back positive.
- A variable-shadowing bug (`co` the flag vs `co` the accuracy) silently
  un-froze half the control arms. Caught **only** because the numbers were
  byte-identical to another arm's — had they been merely plausible, phase 5
  would have been written up as a partial success.

The question that caught all five: **what result would have made this fire?**

## 7. Reading order

1. `STATE.md`
2. `docs/VERDICT_5_DENOTATION_2026_08_22.md` + `docs/DEVIATIONS_5_2026_08_22.md`
3. `docs/VERDICT_4_SELECTION_2026_08_20.md` + `docs/DEVIATIONS_4_2026_08_20.md`
4. `docs/GRAMMAR_SOUTHERN_v0.1.md` for the language itself
5. Controls, which is where most of the work went: `tools/pi_controls.py`,
   `planted_cipher_control.py`, `confusability.py`, `variance_confound_control.py`

⛔ **Do not quote:** `runs/phase3.log` (phase 3 v1, invalid) ·
`runs/phase5_v2..v5.log` (superseded, four different reasons) · the raw λ arm of
`phase3_sweep.json` as novelty pressure · any `aspect_root` figure referenced to
the random baseline · "89.3 % ceiling". Each verdict carries its own do-not-quote
list.

**Not a git repo.** No history behind any of this; the deviations files are the
only record of what was corrected.
