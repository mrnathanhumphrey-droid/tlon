# SPEC — Tlönian Discourse Layer ("The Unfolding") v0.1

**Received 2026-08-25.** Defines what coheres one utterance to the next, the
multi-turn oracle, and the drift observable. Downstream of
`GRAMMAR_SOUTHERN_v0.1.md` and `tlon/grammar/classes.py`. **Revises neither the
sentence grammar nor the frozen lexicon `e2b8527010231a81fd31b6eeb9de3d8c`.**

---

# ⭐⭐ RULINGS — 2026-08-25. THESE SUPERSEDE THE BODY. READ THEM FIRST.

Nate's rulings on the verification pass below. **The spec body stays verbatim;
these amend it.** Where a ruling and the body disagree, the ruling governs.

| # | ruling | status |
|---|---|---|
| 1 | §8.1's table keys on the **lexicon** M-column; ontology unchanged | ✅ `tlon/discourse/evidential.py`, 22 tests |
| 2 | **§3's region gate is WITHDRAWN.** ρ_wide is deleted as a parameter | ✅ below |
| 3 | §5's oracle drops to **two** conditions; BREAK is redefined | ✅ below |
| 4 | §7-F2 pre-declares the peak's **shape**, never its **location** | ✅ below |
| 5 | σ_cp gets an **absolute floor + near-repetition guard** | ✅ `falsify.degeneracy_guard`, 21 tests |
| 6 | `MIN_ARENA_TEMPERATURE = 0.7` is flagged **unvalidated** | ✅ provenance in the identifier; sweep fixed |
| 7 | **§8.2 (render → ≥0.90) starts now** — no open design question | ⏳ in flight |

## ⛔⛔ RULING 2 — §3's REGION GATE WAS A CATEGORY ERROR AGAINST THE SOURCE TEXT

The measurement (finding 3 below) showed no ρ_wide is both wide-by-design and
able to fail: at 4.0 it rejects most random pairs (proximity-coherence, forbidden
by C-D2); at 6.0 it admits 98 % (criterion 1 cannot fire). **That contradiction
is itself the information.** It is not a bad parameter — it is the wrong kind of
criterion, and the tell was in the text the whole time:

> *"not a concurrence of objects **in space**, but a heterogeneous series of
> independent acts. It is successive, **temporal, not spatial**."* — CF p.73,
> quoted in §1 of this very spec.

§3 put a **spatial distance gate on a world the source explicitly says is not
spatial.** And C-D2 finishes the argument: Tlönian criticism attributes unrelated
works to one author and prizes contradiction, so *unrelated-held-as-one* is the
**prized** case, not the edge case. If any two impressions can be held as one
unfolding, then **there is no out-of-region by content-distance**. The wideness
was never "very wide" — it is **total**, and a total region is not a gate.

⇒ **The residue-distance region criterion is WITHDRAWN.** ρ_wide is deleted; it
is not re-tuned, re-based, or moved to another substrate. The residue geometry is
**demoted to description** — it still distinguishes a *wide* abiding from a *deep*
one, which is a real and useful thing to say about a pair, and it says nothing
about legality.

⭐ **This removes a parameter, a failure mode, and a category error at once**, and
the oracle gets more Tlön-faithful, not less. It also means §3's near-vacuity was
never a defect in the measurement — **the ethos makes criterion 1 vacuous**, and
the measurement is what surfaced that.

## ⭐ RULING 3 — THE ORACLE SIMPLIFIES, AND BREAK IS REDEFINED

Two conditions, both on axes that are **not content** and therefore **can** fail:

A continuation `u_{n+1}` given `u_1…u_n` is **default-coherent** iff

1. its evidential is a **smooth morph** of `u_n`'s (adjacency in the M-flow, §4)
   — the *temporal/successive* axis, which is the one the ontology endorses —
   **and**
2. its move is **ABIDE** (§2).

**No content-region test at all.** Evidential smoothness can be discontinuous (a
shock: *seen* → *dreamt*). Force can be marked. Those gate. Content does not,
because the ethos forbids content from gating.

⛔ **BREAK IS NOT "DISTANT CONTENT" — THAT WAS THE ERROR.** §2 and §3 define BREAK
as `d > ρ_wide`. Corrected: **BREAK is refusing the *flow*** — an evidential
discontinuity, or a force that drives at closure. You do not step out of an
unfolding by saying something unrelated; **that is prized.** You step out by
breaking the epistemic continuity.

⚠️ Consequence for §2's table: the "Region relation" column is withdrawn along
with §3. ABIDE/CLOSE/BREAK are distinguished by **force and evidential
continuity** alone.

## ⛔ RULING 4 — §7-F2 PRE-DECLARES THE SHAPE, NEVER THE LOCATION

As the verification pass found: the Turbulence toy locks σ_cpl = 0 at both ends
with a single interior peak (theorem-backed, 0/1500 negative), and **explicitly
holds the peak's location** — the swept `s* = 0.45` was the geometric peak of a
placeholder, since only `d(s)` varied while A/D/Ω were held fixed.

§7-F2 as written says *"pre-declare the σ_cp(coupling-strength) slope"*. Amended:
**pre-declare that a peak EXISTS and its SHAPE — zero at both ends, positive
interior, single maximum. Leave the location open, because it is open upstream.**

⭐ Declaring a location we do not have would be **the fourth vacuous falsifier in
this project, this one wearing a physics costume** — a pre-registered number that
could only ever be checked against itself.

## ⭐ RULING 5 — σ_cp MUST NOT INHERIT F4's DECLINE-BASED SHAPE

Built, because the defect was demonstrable rather than hypothetical: **F4 read
"no degeneration signature" on the 40-turn probe.** Both its branches are
relative and both read **+0.0 %** — the within-arm decline because TTR was
already 0.125 at the *first* window, the level-vs-control branch because the
control was equally degenerate (0.125 vs 0.125).

⛔⛔ **A RELATIVE MEASURE HAS NO OPINION WHEN BOTH ARMS ARE ON THE FLOOR** — and
both-arms-degenerate is the case actually measured. A σ_cp defined as a *change*
reads 0 on a pair stuck from turn zero, and **0 there means "independent, no
pact", the exact opposite of the truth.**

`falsify.degeneracy_guard` is the absolute reading, and both thresholds come from
the **corpus null alone** so neither was fitted to the event it catches:

| | threshold | derived from | margin on the measured event |
|---|---|---|---|
| root-TTR floor | **0.50** | corpus min **0.700** over 2,500 8-scene windows | event at 0.056 — **0/2,500** corpus windows come near it |
| near-repetition | **0.75** | random corpus pairs max **0.500** over 20,000 | **153/153** transcript pairs above the corpus max |

⚠️ The near-repetition ceiling is calibrated against the **single-turn** null —
utterances that genuinely abide should be *more* similar than random, so the
healthy multi-turn band is unmeasured. **The caveat is in the identifier**
(`NEAR_REPETITION_CEILING_SINGLE_TURN_NULL`) and must be recalibrated the moment
an abiding-chain corpus exists.

## ⭐ RULING 6 — THE TEMPERATURE FLOOR IS FLAGGED, AND THE SWEEP IS FIXED

`MIN_ARENA_TEMPERATURE = 0.7` is a placeholder. `MIN_ARENA_TEMPERATURE_PROVENANCE`
and `MIN_ARENA_TEMPERATURE_IS_MEASURED = False` now sit beside it and are stamped
into every refusal, so the caveat cannot decay into a bare number.

`tools/act2_temp_sweep.py` **refuses `--depth < 3`** — its original depth-1 probe
measured the deterministic-echo regime, where no temperature can produce
variation, and reported "NO USABLE TEMPERATURE ON THIS GRID" as a fact about the
model. It also now separates the two causes of that verdict: *varies nowhere*
(a real sampler finding) from *legal nowhere* (**a depth-competence finding that
belongs to the multi-turn corpus, and no temperature can close it**).

---

# ⛔ VERIFICATION PASS — RUN BEFORE ANY BUILD, RECORDED HERE

The spec asserts things about code and about other projects. Every assertion was
checked against the machine. **The spec body below is preserved verbatim; nothing
is silently patched.**

## ⛔⛔ CORRECTION 1 — five M-class form-names do not exist

§4 lists the evidential inventory as *"normative in classes.py"*. **The ten
ways-of-holding are exactly right and map one-for-one. Five of the ten SURFACE
FORMS are wrong** and would be refused by `PS.validate` as "not in lexicon class
M" — which is the hardened path, so a convention table built on the spec's names
would fail loudly rather than silently, but it would fail.

| gloss | spec says | **frozen lexicon (authoritative)** |
|---|---|---|
| seen | `sköl` | **`xöl`** |
| dreamt | `xoth` | **`xos`** |
| denied | `nek` | **`nem`** |
| doubted | `dul̈` | **`hrin`** |
| wished | `wir` | **`mir`** |
| heard | `hrix` | `hrix` ✅ |
| felt | `ten` | `ten` ✅ |
| inferred | `plun` | `plun` ✅ |
| remembered | `mar` | `mar` ✅ |
| feared | `frax` | `frax` ✅ |

⭐ **THE ONTOLOGY IS INTACT** — direct / mediated / irreal / withdrawn survives
unchanged. Only the spelling of half the forms is off. **§8.1's convention table
must be keyed on the right-hand column.**

## ✅ VERIFIED — everything else the spec leans on exists

| claim | status |
|---|---|
| §3 residue/impression geometry | ✅ `tlon/grammar/residue.py:distance`, `tlon/novelty/distance.py:distance(Scene, Scene)` |
| §4 M-class is 10 values, metaphysically load-bearing | ✅ 10 forms in the frozen lexicon |
| §6 `D:\Turbulence\STOCHASTIC_THERMO` | ✅ exists — EXPLORE_01–03, PREREG_01/02 LOCKED, TOY_01–05 |
| §6 discrete-KM estimator | ✅ `D:\Turbulence\code\plan_A_kramers_moyal.py` + `calib_km_beta_firstknife.py` (calibrated) |
| §7 F1 analytic-toy 3-way closure | ⭐ **LARGELY ALREADY PAID — see below** |

## ⭐ §8.3 IS SUBSTANTIALLY BANKED, WITH ONE CAVEAT THAT MUST CARRY OVER

The Turbulence lane already ran the toy closure the spec asks for, **and its
first answer was wrong in a way that matters here**:

- **TOY_03 — the heuristic closed form FAILED its own correctness gate.**
  `σ_cp ∝ dᵀKd` was sign-indefinite in **5000/5000** on-shell 2-DOF draws. It is
  a *signed coupling power*, **not** DSI's σ_cpl — and a σ_cp that can go
  negative cannot be an entropy production. The closed form, the explicit `g(s)`
  and every peak-location claim built on it were **DISCARDED**.
- **TOY_05 — the CORRECT object passed.** `σ_cpl = σ_ex^MN − σ_ex^HS` (DSI
  definition, MN gradient-projection via Sylvester): **0/1500 draws negative**,
  min `7.2e-32` (machine zero).
- **LOCKED:** σ_cpl = 0 at both ends (s=1 forced/hard; s=0 isotropic-exact/soft),
  single interior peak in the overparameterized regime — theorem-backed.
- ⛔ **HELD, NOT LOCKED: the peak LOCATION.** The swept `s*=0.45` was an
  **ARTIFACT** — only `d(s)` varied while A/D/Ω were held fixed, so it is the
  geometric peak of a placeholder, not physical. Location depends on the
  curl-suppression `Ω∝[D,H]`, deliberately not guessed.

⛔ **CONSEQUENCE FOR §7 F2 (slope-not-endpoint).** We may pre-declare the
**SHAPE** — zero at both ends, positive interior, single peak — because that is
theorem-backed and empirically confirmed. **We may NOT pre-declare where the peak
sits**, because that is explicitly open upstream. Declaring a location we do not
have would be the fourth vacuous falsifier wearing a physics costume.

## ⛔ WHAT THIS SPEC DOES NOT YET RESOLVE

- **§8.1 the base convention table is unbuilt** — and it is the load-bearing
  derivation. The spec itself flags the test: *"is it forced by the ontology or
  picked? (The picked ones are duct tape.)"*
- **ρ_wide has no value.** §3 says wide-by-design and red-team anything that
  rejects a Borges-consistent "unrelated-yet-held-as-one" pair. **Until it has a
  measured value the abiding oracle cannot be evaluated**, and picking it by
  taste would make Tlön discourse into topic-tracking — the exact
  object-persistence the ontology forbids.
- **The arena minimum temperature (§7 F4) is still an unvalidated placeholder**
  (`falsify.MIN_ARENA_TEMPERATURE = 0.7`). The measured sweep that was meant to
  derive it probed at history-depth 1, where the model is a deterministic echo,
  so it produced "no usable temperature" — an artifact of the probe, not a fact
  about the model. **Must be re-derived at realistic depth.**

## ⭐ WHAT THE EXCHANGE PROBE ALREADY CONFIRMS ABOUT §0

The spec's premise is measured, not assumed. 40 turns, temperature 0.9, criteria
pre-specified before the data:

| | interacting | control (frozen partner) |
|---|---|---|
| validity overall | 45 % | 62 % |
| validity last quarter | **40 %** | **50 %** |
| root TTR | 0.12 → 0.12 | 0.12 → 0.12 |

**Both arms degenerate**, so it is the model and not the exchange — which is
exactly the spec's §0 claim, and it is why an intrusive-thought generator is the
wrong fix. The transcript is a near-fixed point: **6 distinct utterances in 18
legal turns**, mean 2.9 differing tokens of 14, most of that aspect-reduplication
jitter.

⛔ **AND A WARNING THE DISCOURSE METRICS MUST HEED.** Of three pre-specified
criteria, **two failed to fire on this textbook degeneration**: TTR *decline*
read **+0 %** because TTR was already 0.12 at the first window, and the *exact*
cycle check missed near-repetition. Only validity caught it. **A decline-based or
exact-match-based measure cannot see a speaker that starts degenerate and jitters
— F4 has the same shape, and σ_cp must not inherit it.**

---
---

# THE SPEC AS RECEIVED (verbatim)

## 0. Why this layer exists

The sentence grammar produces one impression at a time. The raw 7B-vs-7B arena
proved a model trained only on single-turn pairs degenerates at depth in both
arms (interacting and frozen-partner) — the corpus contains no notion of one
utterance cohering with the next, so at turn 40 the model conditions on 40
accumulated surfaces it never saw in training, and retreats to its simplest
attractor. This is the same gap that reading was before it was trained: a task
absent from the corpus. The fix is not a shortcut (context-bounding hides the
depth the drift lives in; an intrusive-thought generator papers over a speaker
that can't sustain generation alone). The fix is to build the discourse structure
the corpus is missing, so multi-turn continuation has an oracle the way reading
did (`parse(render(s))==s`).

This document is that structure. It is derived, not invented — every rule is
forced by Tlön's ontology as Borges states it, and the drift observable is a
formalism already built and validated in another Resolve project, not a bespoke
metric.

## 1. The ethos — from the text, not from taste

Borges states the ontology (CF p.73): the world is "not a concurrence of objects
in space, but a heterogeneous series of independent acts. It is successive,
temporal, not spatial." Three consequences from the philosophy and literature
sections govern discourse:

- **C-D1 — No causality between acts.** The Tlönians deny that one act causes the
  next; succession is association, not consequence. There is no "because." → A
  later utterance does not follow from an earlier one; it succeeds and associates
  with it.
- **C-D2 — Coherence is attributed unity across difference.** Tlönian literary
  criticism attributes unrelated works to one timeless author and prizes
  self-contradiction within a work. → Two utterances cohere not by matching,
  agreeing, or resolving, but by being holdable as one unfolding. Difference is
  embraced; contradiction is not a defect.
- **C-D3 — No resolution.** With no persistent fact beneath the succession,
  nothing closes. The default relation between successive impressions is to abide
  together — to sit in a shared open region — not to complete, answer, or
  resolve.

These three are the whole ethos: acausal succession, associative unity, no
resolution. Everything below is downstream.

## 2. The three moves

Every turn is exactly one of three moves, and the move is structurally checkable
(no persistent fact required — which is what solves the no-oracle problem):

| Move | Definition | Force (F) signature | Region relation |
|---|---|---|---|
| **ABIDE** (default) | Offer an impression that belongs to the current unfolding — in-region, holds the region open, accompanies without closing. | `ka` assert used non-insistently, `ki`, `ko` | in-region (§3) |
| **CLOSE** (marked) | Force resolution — insist on a point, try to make the series conclude or cause. Against the acausal grain. | `ka` assert used insistently, `ku` urge | in-region but resolution-seeking |
| **BREAK** (marked) | Refuse the unfolding — step out of the shared region entirely. | `kä` negate; any force with an out-of-region node | out-of-region |

ABIDE is convention (shared by all speakers — the language's accepting default).
CLOSE and BREAK are personality — marked departures a speaker chooses, and the
thing a pair negotiates. In a society of independent acts, acceptance is the norm
and insistence/defiance are character (§4).

A legal (default) turn ABIDES. CLOSE and BREAK are legal Tlön but marked — they
carry stance-cost. This is the multi-turn oracle: a continuation is
default-coherent iff it abides; marked moves are legal-but-characterful, and
their rate is a measured quantity, not a violation.

## 3. The region — what "in-region" means (the operationalization)

"In-region" = associatively holdable in the same unfolding. Per C-D2 this is wide
(difference-embracing), and per C-D1 it is not logical consistency
(compat-as-agreement is the wrong tool — contradiction is prized). It is a wide
associative reach in impression-space, using the residue geometry the project
already built:

- Let `d(u_n, u_{n+1})` be the residue/impression-space distance between
  successive scenes (the same evocative geometry used in Act 1,
  `referents_residue_*`).
- **In-region** iff `d ≤ ρ_wide`, where ρ_wide is a generous radius —
  far-but-reachable is in; only the utterly unassociable is out. ρ_wide is a
  pre-registered parameter, and its default value defines the language's baseline
  "width of the holding."
- **Out-of-region (BREAK)** iff `d > ρ_wide` — the response has stepped out of
  the unfolding.

⚠️ ρ_wide is wide by design. The failure mode to avoid is setting it tight
(proximity-coherence), which would make Tlön discourse topic-tracking — the exact
object-persistence the ontology forbids. Per C-D2, the region embraces the
different and the contradictory; only the unassociable is out. Red-team any
ρ_wide that rejects a Borges-consistent "unrelated-yet-held-as-one" pair.

Two utterances at large `d` but ≤ ρ_wide are a **wide abiding**
(associated-across-difference — the prized case). Small `d` is a **deep abiding**
(sitting close). Both abide.

## 4. The evidential flow (the M-spine) — coherence's substance

Coherence's spine is the evidential (M-class: *seen · heard · felt · inferred ·
remembered · dreamt · denied · doubted · wished · feared* — normative in
`classes.py`, CLASSES includes M). The spec's own §3.5 designates M
metaphysically load-bearing: an unperceived happening is a different happening.
Therefore changing the evidential is changing the happening — an evidential
progression across turns is the happening continuously becoming a different
happening, not a fixed fact re-perceived.

This is why discourse is a turbulent evidential flow: successive impressions
morph through ways-of-holding, no persistent object carried through, coherence =
local continuity of the flow (each turn a smooth morph of the prior), not
identity of a thing moving through it. Long-range coherence is emergent from
local, which is exactly why context-bounding is the wrong fix (it would sever the
flow) and why local continuity is the right oracle (turn N+1 need only smoothly
continue turn N, dissolving the OOD-at-depth problem).

**Two flows, coupled by forcing (not diffusion).** A conversation is two
evidential flows (one per model), and each utterance is a forcing term on the
other's flow — A-utters-under-*seen* perturbs B's state; B responds according to
B's own dynamics, staying distinct (not copying A). This is the load-bearing
structural fact: a single flow with no forcing relaxes to its attractor (the
observed degeneration); the phenomenon requires two, because it is the coupling.
This is why the frozen-partner control is not an add-on but the definition of the
null (§6).

The coupling is **biased (conventional)**, because language is a societal
structure and society has convention regardless of grammatical rule. A's *seen*
tends toward evoking a region of B's response — a shared default of "what *seen*
calls for" — and this bias is a convention: shared, learnable, and negotiable
between a specific pair. The bias is the mean; the turbulence is the spread; the
pair renegotiating the bias is the drift (§6). Convention is what can drift (it
could have been otherwise); pure dynamics cannot. This is where the pact lives.

The base convention table (what each evidential conventionally calls for as an
in-region abiding response) is derived per-M from what each way-of-holding makes
associable, following the direct/mediated/irreal/withdrawn grouping. [Deriving
the full 10-value base table is the first build task under this spec — §8.] The
default is always abide in-region; the table biases *where* in the region.

## 5. The multi-turn oracle (solves the no-oracle problem)

Reading had `parse(render(s))==s`. Multi-turn has no "correct next scene" — but
it does not need one, because coherence was never correctness; it is abiding. The
oracle is structural:

A continuation `u_{n+1}` given history `u_1…u_n` is **default-coherent** iff:

1. it is **in-region** relative to `u_n` (`d(u_n,u_{n+1}) ≤ ρ_wide`, §3), **and**
2. its evidential is a **smooth morph** of `u_n`'s evidential (adjacency in the
   M-flow, §4), **and**
3. its move is **ABIDE** (§2).

CLOSE and BREAK are legal but marked; their occurrence is recorded, not rejected.

This is checkable with no persistent fact — it keys on residue-distance,
evidential-adjacency, and force. It is the training oracle for the multi-turn
corpus: sample discourse-legal sequences (abiding chains with a controlled,
pre-registered rate of marked moves), and the corpus gains the missing task.
Because it is generative-with-ground-truth, it does not reintroduce the
invented-continuation-policy trap (history→next-scene was correctly refused
precisely because that had no oracle; this has one — abiding-legality).

This same oracle unblocks the conversant (Path C): "respond appropriately" =
"abide (or knowingly CLOSE/BREAK) in-region with a smooth evidential morph." The
parked conversant's missing oracle was the discourse layer.

## 6. The drift observable — σ_cp (coupling entropy production)

The drift is not a bespoke metric. It is the coupling term of the three-way
entropy-production decomposition (Dechant–Sasa–Ito 2202.04331; discrete/
no-steady-state instrument: Yoshimura–Ito 2205.15227 App. C), the same formalism
the Turbulence project's `STOCHASTIC_THERMO` lane built for catastrophic
forgetting. Two coupled Tlön flows are a discrete, non-stationary, double-driven
system — exactly Yoshimura's domain (discrete state space, no steady-state
requirement, valid for multistability/limit-cycles/chaos), which is why it
survives here where an SDE/Fokker–Planck framing would not.

The decomposition splits each model's turn-to-turn entropy production into three
positive, IFT-obeying parts, and each maps to a derived Tlön layer:

| Term | Stochastic-thermo meaning | Tlön meaning |
|---|---|---|
| **σ_ex** (excess) | time-dependent drive; Lyapunov toward instantaneous steady state | **being-moved-by-the-other** — the incoming utterance as forcing (§4) |
| **σ_hk** (housekeeping) | nonconservative/solenoidal force; the standing bias | **personality** — the model's own standing character (CLOSE/BREAK tendencies, §2/§4) |
| **σ_cp** (coupling) | interplay; = 0 iff the two drivings act on independent DOF | **THE PACT** — shared negotiated structure; > 0 iff the flows genuinely couple in shared impression/evidential DOF |

σ_cp is the drift observable. It is the thermodynamic measure of how entangled
the two flows are in shared structure, and it is zero exactly when they are
independent — i.e. σ_cp > 0 is communication-driven drift; σ_cp = 0 is two flows
forcing each other on independent DOF (no real pact).

**The frozen-partner control is the σ_cp = 0 baseline, built into the
formalism.** A frozen partner forces (σ_ex ≠ 0) but cannot couple back (no live
responsive character to share DOF), so σ_cp = 0 by construction. Thus
interacting-pair σ_cp > 0 vs frozen-pair σ_cp = 0 is the pact, measured, with the
control intrinsic — the H2 co-adaptation-specific share, re-derived at LLM scale
in a validated physical formalism.

**Built-in vacuity guard (IFT):** the decomposition is only clean if
`⟨e^{−Δs_cp}⟩ = 1` holds empirically. This is the σ_cp analog of every
falsifier-must-be-able-to-fire guard in the project: if the coupling IFT fails,
the decomposition is not clean in this system and no σ_cp claim is licensed.
Pre-register the IFT check as the precondition for reading σ_cp.

**The coupling law (response kernel) is measured, not invented** — by discrete
Kramers–Moyal. How B's evidential/impression state morphs under A's forcing is
extracted from observed arena transitions via the discrete-KM estimator already
built and calibrated in Turbulence (`plan_A_kramers_moyal`,
`KM_beta_estimator_calibration_firstknife`). Discrete KM, not the SDE limit — a
token-emitting model is discrete (the Yaida SGD≠SDE caution transfers directly).

## 7. Carried red-team flags (from STOCHASTIC_THERMO EXPLORE_03 — they transfer)

- **F1 — convergence/sample floor.** σ_cp needs the non-stationary density
  gradient in the flow's state space; high-D is brutal. Mitigation (transfers):
  compute in a low-D collective-variable projection — here, the
  residue/impression coordinates + the M-flow coordinate, which are already the
  natural low-D substrate. Run the analytic-toy 3-way closure (σ = σ_ex + σ_hk +
  σ_cp on a 2-DOF system where it's analytic) before instrumenting the arena.
- **F2 — the overlap AXIS, not one pair.** "σ_cp rises with coupling" needs a
  sweep, not a single interacting-vs-frozen point. Pre-declare the
  σ_cp(coupling-strength) slope (slope-not-endpoint discipline) — e.g. vary
  decoding temperature or the base-convention sharpness — or monotonicity is
  unfalsifiable.
- **F3 — is σ_cp additive beyond a simpler measure?** The Turbulence lane must
  show σ_cp adds explanatory power beyond rank-contraction; here, show σ_cp adds
  beyond a naive ΔC/convergence count — i.e. σ_cp catches pacts that
  surface-convergence misses (the ΔD-blind-to-pacts lesson, one level up).
- **F4 — vacuity precondition (arena temperature).** Greedy decoding makes drift
  impossible by construction (deterministic flows cannot couple-and-drift).
  Pre-register a minimum arena temperature; below it σ_cp is declared vacuous and
  raises, never reports a null (a false σ_cp = 0 from temp-0 is indistinguishable
  from a real independence null — the most dangerous confound).

## 8. Build order (derived work → corpus → arena)

1. **Derive the base convention table** (§4) — the 10-value evidential
   response-bias, per-M, from the direct/mediated/irreal/withdrawn grouping +
   C-D1/2/3. Metaphysics work, $0, on paper. Red-team each entry: is it forced by
   the ontology or picked? (The picked ones are duct tape.)
2. **Fix F4/F-LOCAL first** (render →≥0.90; the small-class targeted positives) —
   a model that can't cleanly emit isn't ready to abide.
3. **Analytic-toy 3-way closure** (§7 F1) — prove σ = σ_ex+σ_hk+σ_cp closes on a
   2-DOF Langevin with an overlap knob, and σ_cp(overlap) is monotone with a
   derivable slope, before any arena instrumentation.
4. **Multi-turn corpus via the §5 oracle** (abiding chains, pre-registered
   marked-move rate). Trains both 7B and 32B (shared corpus).
5. **Arena** — two native-Tlön models, discrete-KM coupling-law extraction, σ_cp
   with the IFT guard, frozen-partner (σ_cp=0) control, temperature ≥ the F4
   floor, σ_cp(coupling) slope pre-declared.

## 9. What this does and does not claim

- **Claims:** discourse coherence in Sur is acausal associative abiding
  (Borges-derived); the multi-turn oracle is abiding-legality (structural, no
  persistent fact); the drift is σ_cp (coupling entropy, IFT-guarded,
  frozen-partner = σ_cp=0 baseline); the coupling law is discrete-KM-measured.
- **Does NOT claim:** that σ_cp > 0 will be found (that is the arena's question,
  gated on the IFT and the slope); that the base convention table is complete
  (§8.1 is unbuilt); that "shared/experienced" are evidentials (they are
  directions the flow moves, expressed via existing M-values, not new lexicon —
  the frozen lexicon is untouched).
