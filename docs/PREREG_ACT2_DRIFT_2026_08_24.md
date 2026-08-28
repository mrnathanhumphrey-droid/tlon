# PREREG ACT 2 — does constrained LLM-to-LLM communication drift, and is the drift a pact?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `20620b7c` (sha256[:8] of draft body at lock, 2026-08-24T22:30Z)
- **Date:** 2026-08-24
- **Deliverable:** Act 2, **Deliverable 0**. Framework only. **$0.** No harness
  line exists yet and none may be written until this is LOCKED.
- **Depends on:** `docs/VERDICT_13_2_FINAL_2026_08_24.md` (H2, the frozen-control
  move this borrows), `docs/DECISIONS_B2_HARDENING_2026_08_24.md` (π-exactness,
  the near-miss mutation set reused as distractors), `tlon/grammar/denote.py` (π),
  `tlon/product/schema.py` (the validity gate)

---

## 0 · Three things the brief leaves underspecified, and what this prereg does about them

Stated up front because each one changes what gets built, and none of them is an
objection to the design.

**0.1 — DRIFT ALONE IS NOT A PACT, AND THE HEADLINE CLAIM IS ABOUT A PACT.**
Two models each wandering independently inside a tight constraint will both
depart from where they started. That is drift, and it is *not* a private
language. A private convention requires the pair to depart from epoch 0 **and to
arrive at the same place as each other**. The sealed research already says this
in its own headline — H2 is *a pact forms*, and its estimand is a co-adaptation
share, not a wander rate. ⇒ This prereg registers **two** observables, `D` and
`C`, and the private-language claim requires **both**. A result with `D` up and
`C` flat is registered in advance as **wandering, not convention** — a distinct
outcome with its own name, not a weakened success.

**0.2 — IN AN INFERENCE-ONLY PASS, NOTHING DRIFTS THAT COULD DRIFT.** No weights
change. Whatever moves, moves because the conversation history conditions the
model differently as it grows. That is a real phenomenon and it is the cheap
phenomenon the brief correctly wants measured first — but it is **not** the same
object as post-fine-tune drift, and the two must never be reported under one
word. ⇒ Caveat in the name, never in prose beside it:
`D_ctx` (in-context, prompted, cheap) and `D_w` (weight-level, post-fine-tune,
the the contingency class). Every number, table and filename carries its subscript.

**0.3 — A PROBE ADMINISTERED WITHOUT THE CONVERSATION IN CONTEXT MEASURES THE
BASE MODEL.** In the prompted pass the model at epoch t and the model at epoch 0
are byte-identical weights; the *only* thing that can differ is what is in the
context window. A probe run in a clean context therefore returns epoch-0
behaviour by construction, `D_ctx ≡ 0`, and the falsifier fires for a reason that
has nothing to do with the claim. ⇒ Probe administration **must** carry the
conversation history, and the probe transcript must be discarded afterwards so
probing never becomes conversation (§3.4).

---

## 1 · The claim, and the two observables

**The claim under discipline.** *Two language models constrained to communicate
only in valid Tlön develop a private convention — a meaning↔form mapping that
departs from where they started and that they come to share.*

⛔⛔ **THE OBSERVABLE IS PRE-COMMITTED HERE AND MAY NOT BE REDEFINED AFTER ANY
RUN.** Drift is **not** "the transcripts look different over time." That is the
confabulation trap: surface novelty is free under this grammar, and a human
watching two models chatter will see a private language whether or not one
exists. Drift is a departure in the **mapping between meaning and form**,
measured **in impression space** (π), against a **fixed held-out probe battery**.

Let `P` be the probe battery (§3), `A` and `B` the two models, `t` an epoch.

| symbol | name | definition |
|---|---|---|
| `D(M,t)` | **departure** | fraction of probes whose mapping under model `M` at epoch `t` differs from the same model's mapping at epoch 0 |
| `C(t)` | **convergence** | fraction of probes on which `A` and `B` agree with **each other** at epoch `t` |

Both are computed over two probe halves — **production** and **comprehension**
(§3.2, §3.3) — and averaged with **equal weight, fixed now**. No post-hoc
reweighting, no dropping a half that disagrees with the other.

**Primary estimator (coarse, and primary precisely because it cannot be tuned):**
π-impression identity. Two renderings either share an impression or they do not;
an impression id is a 128-bit digest, so there is no threshold to move later.

**Secondary estimator (declared EXPLORATORY, cannot enter a verdict):** graded
π-slot disagreement — normalised count of disagreeing denoting slots, structural
mismatch scoring maximal, slot list derived from `denote.denoting_parts()`.
Registered now so that computing it later is not a post-hoc choice.

---

## 2 · The falsifiers, in the order they can fire

### F1 — THE INTERNALIZABILITY GATE (fires first; gates everything below)

> **Fires if:** native valid-emission rate < **0.90** on held-out prompts.

Below that, the retry loop dominates and every measured mapping is partly the
*gate's* mapping rather than the model's. ⛔ In the prompted pass F1 is **fired
by construction** — a prompted model reaches validity only through
reject-and-retry. That is why the prompted pass measures `D_ctx` and is barred
from making any `D_w` claim. Retry rate is logged per epoch per arm as a
covariate and checked for arm-imbalance (§5.3).

**Re-decomposition set (pre-committed):** {bigger model, curriculum fine-tuning,
looser-but-still-exact validation}. Recovery ⇒ `D_w` becomes measurable.
Persistent firing ⇒ **boundary result: the constraint is not internalizable at
size N** — a real finding about the grammar's learnability, not a failure.

### F2 — THE DRIFT-IS-NOISE FALSIFIER ⛔⛔ **THE LOAD-BEARING BRICK**

> **Fires if:** `ΔD = D(interacting) − D(control) ≤ MDE`, seed-paired.

The measured drift is then indistinguishable from what the same models produce
under the same constraint **without a partner adapting to them** — it is the
constraint's own generation variance, and the claim is unattributable.

⛔⛔ **THE CONTROL IS BUILT AND RUN FIRST, BEFORE ANY TRANSCRIPT IS READ.** This
is not sequencing preference; it is the whole integrity of Act 2. Two models
talking will look alive. The human pattern-matcher is the confabulation engine,
and a paired control is the only thing that overrides it.

### F3 — THE PACT FALSIFIER (new; see §0.1)

> **Fires if:** `ΔC = C(interacting) − C(control) ≤ MDE`, seed-paired.

The pair departed but did not converge. Registered outcome name: **WANDERING,
NOT CONVENTION.** F2 clearing while F3 fires is a *publishable, honest, distinct*
result and must be reported under that name, never as a qualified success.

### F4 — THE DEGENERATION FALSIFIER (anti-confabulated-drift)

> **Fires if:** measured drift is explained by degradation rather than convention.

⭐ **THIS IS THE FALSIFIER THAT FIRES ON CONFABULATED DRIFT.** A pair that
collapses into repetition, lexical impoverishment or validity failure will show a
large `D` for reasons that are the opposite of a private language. Pre-committed
covariates, logged per epoch per arm: valid-emission rate, retry rate, distinct
roots per epoch (type/token over `R`), mean nodes per Scene, mean edges per node.
**Fires if** `ΔD` loses significance when any covariate is entered, **or** if the
interacting arm's root-diversity declines by more than 25 % from epoch 0 while
the control's does not.

### F5 — THE LEAKAGE FALSIFIER

> **Fires if:** a probe's impression appears in the conversation before that probe
> is administered.

Then agreement on that probe is recall, not convention. Checked mechanically per
probe per run; leaked probes are **excluded before unblinding**, and a run losing
> 20 % of its battery to leakage is void and re-run with a fresh battery.

---

## 3 · The probe battery (fixed, held out, generated before any run)

### 3.1 Construction
`|P| = 64` probes, split 32 production / 32 comprehension. Generated from the
frozen lexicon by a seeded, recorded procedure, then **frozen and hashed**. The
battery hash is recorded in this prereg's run ledger before epoch 0.

⛔ Probes are **held out of the conversation seed material** and never shown to a
model except during probe administration.

### 3.2 Production probes — "how does this model say X?"
Fixed English stimulus `e_i`. The model, **with conversation history in context**
(§0.3), renders `e_i` through the existing validated pipeline. Output → Scene.

- `D_prod(M,t) = mean_i [ impression(s_i^{M,t}) ≠ impression(s_i^{M,0}) ]`
- `C_prod(t)  = mean_i [ impression(s_i^{A,t}) = impression(s_i^{B,t}) ]`

### 3.3 Comprehension probes — "what does this model take Y to mean?"
Fixed **validated Tlön surface** `u_i` plus **4 forced-choice** austere glosses:
one true, three **π-distinct near-misses**.

⭐ **THE DISTRACTORS ARE THE HARDENING PASS'S OWN MUTATION SET** — single
denoting-part mutations (root / orient / aspect-root / edge-relator), already
proven to be π-distinct and already proven to be near misses a threshold would
merge. This makes comprehension a *discrimination test in the same coordinate as
everything else*, and it needs **no judge model** — which is the point, since a
judge is a second confabulation engine.

- `D_comp(M,t) = mean_i [ choice_i^{M,t} ≠ choice_i^{M,0} ]`
- `C_comp(t)  = mean_i [ choice_i^{A,t} = choice_i^{B,t} ]`

### 3.4 Administration hygiene
Probes are administered in a **branched context**: conversation history in
context, probe appended, response taken, **branch discarded**. Probe exchanges
never enter the conversation history of either model. Probe order is randomised
per administration with a recorded seed. Epochs: every 25 turns, to a
pre-committed horizon of 200 turns (9 epochs including 0).

---

## 4 · The control ⛔⛔ BUILT FIRST

**PRIMARY — the yoked frozen-partner control.** Each model converses with a
**pre-recorded, non-adaptive** partner transcript. Identical constraint,
identical turn count, identical probe schedule, identical decoding parameters,
identical seeds. The **only** thing varied is whether the partner is *adapting to
you*.

⭐ **WHY YOKED AND NOT SOLO.** A solo/monologue control varies two things at once
— partner-adaptation *and* whether the context is conversation-shaped. Any
difference would be unattributable, which is the exact defect this control exists
to prevent. This is the H2 frozen-control move: **co-adaptation-specific share =
interacting − frozen.**

**SECONDARY — the solo control.** Registered, run, reported; used only to
interpret a yoked result, never to establish one.

**Pairing.** Runs are seed-paired across arms and analysed as paired differences.
`n = 8` seed-paired runs (the project's standing convention). ⛔ Measurements
carry their arm and seed; an unpaired comparison is a build error, not a result.

---

## 5 · Decision rules, fixed before any run

### 5.1 MDE — computed from the control, before unblinding
`MDE` = the 95th percentile of `|ΔD|` under **seed-label permutation within the
control arm alone**. Computed and **recorded before the interacting arm is
unblinded**. Same procedure for `ΔC`.

### 5.2 ⛔⛔ THE HEADROOM GATE — an underpowered cell is UNINFORMATIVE, NOT A NULL
Before any cell may report a firing, it must be shown capable of showing an
effect. Measure epoch-0 **replicate** variance (same model, same probe,
re-sampled) to get the noise floor, and epoch-0 `D` to get the ceiling.

> If a cell's available headroom ≤ MDE, that cell **CANNOT show an effect** and
> its result is **UNINFORMATIVE ABOUT THE CLAIM. It is not a null.**

This is the project's own hardest-won rule and it is binding here: an
uninformative cell **may not contribute to a boundary result** (§6).

### 5.3 Covariate balance
Retry rate, valid-emission rate and turn length must not differ between arms
beyond MDE. If they do, `ΔD` is reported **CONFOUNDED** and the axis is re-run
with the imbalance corrected, not interpreted.

### 5.4 Recovery requires all three — strictness is deliberate
A firing **clears** on an axis only if:
1. `ΔD > MDE`, seed-paired, **and**
2. the axis's headroom gate is open (§5.2), **and**
3. it **replicates on a pre-registered held-out seed block** (seeds 9–16,
   generated now, not looked at until a recovery is claimed).

⭐ Condition 3 exists because the falsifier is built to fire on **confabulated**
drift as much as on absent drift. A single-block recovery is a candidate, not a
result.

### 5.5 Multiplicity
Four axes ⇒ **Holm–Bonferroni** at family α = 0.05 across the four axis tests,
plus §5.4.3. Registered now so the correction cannot be chosen after seeing which
axis moved.

### 5.6 ⛔⛔ THE NO-TRANSCRIPT RULE (procedural, binding)
**No conversation transcript is read by any human or model analyst until `ΔD`,
`ΔC`, the covariates and the ledger entry are computed and written.** Transcripts
are for post-hoc interpretation only. Anything noticed in a transcript is stamped
**EXPLORATORY** and can never enter a verdict or a re-decomposition decision.

---

## 6 · The re-decomposition axes and the stopping rule

On a firing, do **not** declare a terminal negative. Re-decompose in this order,
which is fixed now:

| # | axis | hypothesis | operationalisation | cost |
|---|---|---|---|---|
| 1 | **Force / evidential richness** | drift lives in stance-deployment first | restrict vs. full: {1 force, 0 evidentials} → {5 forces, 10 evidentials} | cheap |
| 2 | **Residue on/off** | the private dialect forms in the **unsayable** (H2) | product residue OFF (current) vs. ON, `W_RESIDUE = 0.50` | cheap |
| 3 | **Validity-enforcement mode** | retry dynamics enable or mask drift | hard-reject-and-retry vs. soft-penalty vs. curriculum | cheap |
| 4 | **Lexicon tightness** | constraint-tightness has a sweet spot | pre-committed smaller / larger lexicon, **each separately frozen and hashed** | expensive — re-fine-tune per setting |

⛔ **AXIS 4 FORKS THE LEXICON AND THEREFORE FORKS RESEARCH FROM PRODUCT.** Each
setting gets its own frozen, hashed lexicon; the product's
`e2b8527010231a81fd31b6eeb9de3d8c` is never touched, and no Act-2 lexicon may
reach `tlon/product/`.

⭐ **Axis 2 is where the sealed research says to look.** H2's headline is that a
pact formed around a distinction the grammar **structurally could not express**.
Axis 2 is that finding, re-asked of two language models.

**Stopping rule.**
- **Cleared on an axis** (§5.4) ⇒ **RECOVERED RESULT:** *constrained LLM
  communication drifts, and the drift lives in [axis]*. Stop; that axis is the
  one the installation rides on.
- **Fired on all four, every cell informative** (§5.2) ⇒ **BOUNDARY RESULT:**
  *constrained LLM-to-LLM communication does not drift beyond the constraint's
  own generation variance, across every pre-committed decomposition.* This is a
  real finding about the constraint's expressive geometry and is reported as one.
- **Fired on all four, any cell uninformative** ⇒ **NEITHER.** The uninformative
  cells are named and the boundary claim is **withheld**. A boundary result built
  partly on cells that could not have shown an effect is a false negative wearing
  a verdict's clothes.

Every outcome is ledgered: axis, `ΔD`, `ΔC`, MDE, headroom, covariates, seed
block, and the retractions.

---

## 7 · The wallet, gated

| step | what | cost | gate |
|---|---|---|---|
| 0 | **this document** | **$0** | — |
| 1 | harness: probe battery, drift observable, **control first**, axis toggles | $0 (local) | this doc LOCKED |
| 2 | **inference-only pass** — prompted + validated, `D_ctx` only | cheap, local hardware | harness green, control runs first |
| 3 | fine-tune for `D_w` | **the contingency class** | ⛔ **ONLY IF step 2 RECOVERS** (§5.4) |
| 4 | installation | — | rides on **the axis that recovered**, never the one hoped for |

⛔ **NO FINE-TUNING SPEND UNTIL THE CHEAP PROMPTED PASS SHOWS DRIFT EXCEEDING
CONTROL.** Framework before compute, applied to the wallet: do not pay to make a
phenomenon native before establishing the phenomenon is there.

---

## 8 · What would make me wrong about the design itself

Registered so it cannot be rationalised later:

- If `D_ctx` and `D_w` turn out to be **uncorrelated** across the axes, the cheap
  pass does not license the expensive one and step 3's gate is invalid. Test on
  the first axis that recovers, before committing the rest of the budget.
- If the probe battery proves **too easy** (epoch-0 comprehension accuracy at
  ceiling) or **too hard** (at floor), the headroom gate closes every cell and
  the whole design is uninformative regardless of what the models do. Checked at
  epoch 0 of the very first run, before any conversation is generated.
- If **leakage** exceeds 20 % routinely, held-out probes are not achievable at
  this lexicon size and the observable needs rebuilding, not patching.
