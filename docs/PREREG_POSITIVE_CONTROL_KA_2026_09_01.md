# PREREG — POSITIVE CONTROL: does `force:ka` move on real data, at all?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `c0de41c7` (sha256[:8] of draft body at lock, 2026-09-01T22:06Z)
- **Date:** 2026-09-01
- **Deliverable:** a GO/STOP gate. **Not a study.**
- **Depends on:** `MEASUREMENTS.md` [A1](../MEASUREMENTS.md#a1) (the instrument),
  [E1](../MEASUREMENTS.md#e1) (YOKED), [E4](../MEASUREMENTS.md#e4) (the
  saturation screen), [D4](../MEASUREMENTS.md#d4) (unit of independence),
  `docs/PARFENOVA_READ_2026_09_01.md` (Algorithm 1, the memory model)
- **Supersedes nothing.** Does not amend `PREREG_ACT2_DRIFT` `b96902b3`.

---

## 1 · Purpose, stated as the problem it solves

Every convergence instrument in this project is validated to fire on **planted
synthetic** convergence and **has never fired on real data**. A1 returned
`+0.0803`, CI **[−0.2856, +0.4637]**; A2 returned Δgain `+0.0024`, CI
**[−0.0075, +0.0130]**. Both are UNDERPOWERED, neither is a null.

⛔ **A memory CONTRAST run at this point risks two nulls, and two nulls are
uninterpretable.** Before shared-vs-self-accumulation is worth paying for, the
instrument needs one demonstrated positive on real data.

**The question, and it is the whole question:** does `force:ka` move on real data
under a memory model already known to produce strong convergence in natural
language (Parfenova's shared append-only memory)?

## 2 · Estimand

`force:ka` convergence under shared memory, measured by the **A1 W2-delta**
instrument — the one already red-proofed for sign in both directions
(`tests/test_drift_estimand.py`, mutation-tested: flipping the subtraction fails
2 tests).

**Convergence means signal above the instrument's demonstrated detection floor
(§3), NOT above zero.** A CI excluding zero on an instrument whose real-data
sensitivity is unmeasured is not a positive control.

**Sign convention, carried unchanged from A1: negative = coupling.**

## 3 · ✅ THE FLOOR — MEASURED 2026-09-01, AND IT FIRED ONCE BEFORE IT PASSED

> ## ⭐⭐ `FLOOR_ka` = **0.100 ka** = **0.41 between-build sd** = **−0.311 in W2 units**
>
> Power at the floor **0.848**; ceiling at complete convergence **0.902**;
> false-positive rate at δ=0 **0.018** against a nominal 0.025.
> Design: **7 pairs / 7 adapters / 28 replicates.**
> Tool `tools/act2_a1_floor.py` · result `runs/act2/a1_floor_7x28.json`
> · 400 sims × 1000 bootstrap per δ, MC se ≈ 0.02.

**⛔ THE FIRST DESIGN THIS PREREG REGISTERED IS DEAD, AND THAT IS WHAT §3 WAS
FOR.** At 6 pairs / 6 adapters / 7 replicates, power **saturated at 0.637** and
stopped: no δ cleared 80%, **including complete convergence**, so no floor
existed and the run would have been uninformative before it started. Recorded in
`runs/act2/a1_floor.json`.

⭐ **The calibration red-proofs itself.** At δ=0 the detection rate was 0.020
(6/6/7) and 0.018 (7/7/28) against a nominal 0.025 one-sided, with wrong-side
rates 0.022 and 0.000. **The interval is correctly calibrated, not conservatively
over-wide** — so the 6/6/7 failure was the design, not a timid bootstrap.

### 3.1 The curve at the registered design

| planted δ (ka) | in sd | mean W2 delta produced | power |
|---|---|---|---|
| 0 | 0 | — | **0.018** ← nominal 0.025 |
| 0.0125 | 0.05 | — | 0.062 |
| 0.025 | 0.10 | — | 0.180 |
| 0.0375 | 0.15 | — | 0.333 |
| 0.050 | 0.20 | −0.168 | 0.502 |
| 0.075 | 0.31 | −0.243 | 0.728 |
| **0.100** | **0.41** | **−0.311** | **0.848** ⇐ `FLOOR_ka` |
| 0.150 | 0.61 | −0.440 | 0.892 |
| 0.200 | 0.82 | −0.545 | 0.902 |
| complete | — | −0.988 | 0.902 |

### 3.2 ⭐ The floor sits BELOW Δ\*, which is the condition that matters

[Δ\*](../MEASUREMENTS.md#d1) = **0.5939** W2 units (half the median cold-table
separation 1.1878). `FLOOR_ka` produces **−0.311** — a little over **half** of
Δ\*, and **power at Δ\* is ≈0.90** (δ≈0.20 ka gives −0.545 at power 0.902).

⇒ **The design detects effects well below the pre-declared worth-having
threshold.** A null from this run is therefore interpretable in a way the drift
run's was not — that one had a detection floor of ~32% of median separation and
a CI half-width of 0.375, and could not exclude a worth-having effect.

### 3.3 Three caveats carried into the lock

1. ⚠️ **`FLOOR_ka` is the smallest GRID POINT that clears, not the crossing.**
   Power is 0.728 at δ=0.075 and 0.848 at δ=0.100, so the true 80% crossing is
   near **0.085**. Locking 0.100 is the **conservative** direction — a harder
   gate than strictly required. Deliberate: a floor rounded *down* would be a
   threshold flattered by grid resolution.
2. ⛔⛔ **THE SIMULATION IS OPTIMISTIC BY AN UNKNOWN AMOUNT, IN THE DIRECTION
   THAT MATTERS.** It generates pair-to-pair heterogeneity from **starting-gap
   spread only** — every pair closes by the same δ. Real adapters may differ in
   *how much* they converge, not only in where they start, and that extra
   heterogeneity is the `h` term the simulation does not carry
   ([C2](../MEASUREMENTS.md#c2): h = 0.2519, CI [0.0000, 0.4033]). Extra `h`
   ⇒ replicates buy **less** power than §3.1 shows. **This is why the design
   takes 28 replicates rather than the 14 that nominally clears at 0.805** —
   sizing against known model error rather than against the model.
3. ⛔ **NUMERAL COLLISION, NAMED BEFORE IT PROPAGATES.**
   `FLOOR_ka` = 0.100 ka and [A2](../MEASUREMENTS.md#a2)'s convention floor
   "sd ≥ ≈0.10 ka" are **the same numeral for different quantities** — this one
   is a **centroid closure between two speakers**, that one is the **sd of a
   planted within-conversation convention**. They are not comparable and must
   never be quoted as agreeing.

<details><summary>What §3 was written to do, before it did it</summary>

**The decision rule in §5 needed a number that this project did not have.**

A1's red-proofs establish direction, asymmetry, axis-scale use, label hygiene,
that one distribution gives a CI covering zero, and that the bootstrap **can**
exclude zero. ⛔ **None of them plants a convergence of known size and confirms
A1 recovers it.** [A2](../MEASUREMENTS.md#a2) has that calibration (a planted
convention of sd 0.10 ka yields gain 0.0233).
[A5](../MEASUREMENTS.md#a5) has it (`ΔD` −5.08, `ΔC` +85.94, p=0.0078).
**A1 does not.**

⇒ Before this prereg locks: plant convergence of known magnitude
`δ ∈ {0.05, 0.10, 0.20, 0.40}` ka into synthetic clouds matched to the real run's
cloud size and axis scale ([C1](../MEASUREMENTS.md#c1), between-build sd
**0.2454**), at the pair count §4 will actually use, and record the smallest δ
A1 recovers at 80% power.

> **`FLOOR_ka` := that δ.** It is written into this document and hashed **before
> any box comes up.** A floor chosen after seeing the run is a threshold
> retrofitted to its outcome.

⭐ This is $0, local, and it is also the honest answer to *"why has the
instrument never fired"* — it may be that nothing moved, or that A1 could not
have seen it. **Those have opposite implications and the project has never
separated them.**

</details>

## 4 · Arms, and the unit

**Arm 1 — SHARED MEMORY.** Two speakers per conversation under Parfenova
Algorithm 1: shared, append-only history; **both read everything**; fixed turn
order; each turn appends to the shared store.

> ⛔ **THE ONE FORCED DEVIATION, NAMED NOT GLOSSED.** Their memory holds
> **one-sentence summaries**; Tlön has no summarization operator, so the **full
> surface** is appended instead.
>
> ⚠️ **And this is a larger deviation than "no summarizer."** Summarisation is
> *lossy compression*, and convergence onto a compressed shared representation is
> a live candidate for what drives their result. Substituting full surfaces
> removes the compression. ⇒ **This arm tests shared append-only ACCESS, not
> shared SUMMARISATION.** §6 binds what a STOP may therefore claim.

**Arm 2 — YOKED.** Partner replayed, cannot respond. Identical to
[E1](../MEASUREMENTS.md#e1) so the contrast is the project's existing one:
**LIVE-shared < YOKED, by more than `FLOOR_ka`.**

⛔ **COLD is not an arm.** Standing ban ([E2](../MEASUREMENTS.md#e2)) — Jensen
inflation and n-mismatch produced two would-be headline false positives.

### 4.1 The unit, and the one place the brief needs pinning

**Unit of independence: the ADAPTER** ([D4](../MEASUREMENTS.md#d4)), dyadic
cluster bootstrap, pairs entering with multiplicity `count[x]·count[y]`.

⛔⛔ **"Two speakers" means two PER CONVERSATION, drawn from the seven builds on
disk — NOT two adapters total.** A run with two adapters has **two clusters**;
the dyadic bootstrap is undefined there and §5 could not be applied to its
output. Verified present: `adapter_s20621` `s20622` `s20623` (recipe_var),
`adapter_t30001` `t30002` `t30003` (var_decomp), plus `adapter_mt` — **7 builds,
matching the 7 in `cold_table_ka.json`.** No new training.

**Registered n: 7 pairs × 7 adapters × 28 replicates × 2 arms.**

⛔ **REVISED 2026-09-01 from 6 pairs × 6 adapters × 7 replicates, which §3 killed**
(power ceiling 0.637, no floor). The revision was chosen by measurement, not
preference:

- **Replicates are the lever here, not adapters.** Power at complete convergence
  on the seven builds already on disk: **7 reps 0.698 · 14 reps 0.805 · 28 reps
  0.873 · 56 reps 0.948**. ⇒ **No training is required.** (At 6 adapters:
  0.615 / 0.700 / 0.823 / 0.850.)
- ⭐ **This is a second, independent route to a number already on record.**
  `PRICING_ADAPTER_COUNT` §7 recommended *"extend replicates on the existing 7
  adapters to n≈28"* from the **variance decomposition** on 2026-08-31. §3
  reaches n≈28 from the **power** side, in simulation, against the real
  estimator. Two arguments, same n.
- **28 and not 14** for the reason in §3.3.2: 14 nominally clears at 0.805, which
  is borderline *and* resting on a simulation known to be optimistic.
- The adapter branch is quantified and **not taken**: at 7 replicates it would
  need **8 adapters (0.782, straddles) or 10 (0.877)** — a training spend the
  replicate lever makes unnecessary.

**The ring**, over the seven builds named in `cold_table_ka.json`:
`s20620|t30001 · t30001|s20621 · s20621|t30002 · t30002|s20622 · s20622|t30003 ·
t30003|s20623 · s20623|s20620`.
⚠️ Seven builds split 4 `s` / 3 `t`, so an odd ring **cannot** alternate families
throughout — the closing pair `s20623|s20620` is within-family. Recorded because
it is a small asymmetry in the design, not a defect to be discovered later.

This is a go/no-go — enough to see whether `force:ka` moves at all, **not** to
resolve an effect size.

### 4.2 ⛔ RECORDED, NOT DEFERRED — the shared-attractor quantity

Shared memory **reintroduces the shared-attractor confound by design**: both
agents read one growing store, so both can be pulled toward it without any
coupling between them.

The spec correctly makes this the first post-positive check. ⛔ **But a check
that needs data the run did not record is not a check, it is a second spend.**
⇒ Per-speaker shift from cold centroid is **recorded on both arms and computed
with the primary**, giving [A4](../MEASUREMENTS.md#a4) co-movement. Registered
here so computing it later is not a post-hoc choice.

**Pre-declared:** a negative A1 delta accompanied by large same-direction
co-movement is **REGRESSION TO SHARED CONTEXT, NOT COUPLING** — a named outcome,
not a weakened GO.

## 5 · The reading, locked before the run

| outcome | verdict |
|---|---|
| **mean delta ≤ −0.311 W2 units** (`FLOOR_ka`), CI upper bound < 0 | ⭐ **GO.** The instrument is demonstrated on real data. §4.2 must clear first — a positive that is co-movement is not coupling. Only then does the memory contrast become interpretable. |
| **no movement beyond `FLOOR_ka`** | ⛔ **STOP**, and it is a **finding**: Tlön shows no measurable `force:ka` convergence even under shared memory, **at a design with 0.848 power to see a −0.311 effect and ≈0.90 to see Δ\***. Bounded by §6. **No memory contrast** — two nulls are uninterpretable. |
| **ambiguous / underpowered at this n** | ⚠️ Report **as** an underpowered go/no-go. Decide whether a modest n increase resolves it. ⛔ **A weak signal is not read as GO and not read as STOP.** |

⛔ `FLOOR_ka` may not be lowered after the run. If it should be lower, that case
stands on §3's calibration, on independent grounds, or not at all.

## 6 · Scope — what a STOP does and does not license

**Answers exactly one question:** does `force:ka` move on real data under shared
append-only access, above a demonstrated floor.

⛔ **A STOP does NOT establish** that Tlön admits no convergence: it is silent
about summarisation-mediated memory (§4, the forced deviation), about the
[A5](../MEASUREMENTS.md#a5) mapping channel, and about any observable other than
`force:ka`. It **is** evidence that their result may be substrate-dependent, and
that is publishable as a contribution to their open question — their group-size
effect is confounded with model composition, and seven same-recipe adapters
remove exactly that confound.

**Does NOT:** run the memory contrast (gated on GO) · train adapters · measure
σ_cp ([A6](../MEASUREMENTS.md#a6) — unrelated object) · use ROUGE
([F1](../MEASUREMENTS.md#f1) — saturated: partners 0.6610 vs strangers 0.6669 on
a 244-token vocabulary).

## 7 · Cost, from measured wall — not estimated

From `runs/act2/drift/pipeline_drift.log`, the drift run's **marginal** wall
(the log records marginal separately from the 70 s one-time setup, which is
correct and is reused here):

- **~4,300 s per pair** for 7 replicates across **3** arms (range 4,180–4,435 s
  over 12 pairs).
- This run has **2** arms and **28** replicates ⇒ ~11,500 s/pair **if wall scales
  linearly in arms and replicates** — an assumption, checked on the box rather
  than assumed into the budget.

⇒ **7 pairs ≈ 80,000 s ≈ 22 GPU-hours**, plus setup. Single box, inference only,
**no training.**

⚠️ **`PRICING_ADAPTER_COUNT` §7 put the comparable replicate extension at ~36
GPU-h.** The two estimates are not reconciled and **the cheaper one is not
adopted**: the registered range is **22–36 GPU-h**, and the first pair on the box
settles which end it sits at.

⛔ **HARD CHECKPOINT: after pair 1, compare measured wall against ~11,500 s.
Beyond the 36 GPU-h end, STOP and re-price before committing the remaining six.**
⛔ **Pull the throughput log BEFORE terminating** — it has been lost to a kill
once already.

## 8 · Guards, all carried

1. **This document hashed and committed before the run**, with `FLOOR_ka` and the
   §5 reading in the hashed body.
2. ⛔⛔ **ON-INSTANCE SELF-TERMINATING WATCHDOG, RED-PROOFED AGAINST A FABRICATED
   RUNAWAY BEFORE ARMING.** A laptop-side poll is for progress only and **is not
   a safety watchdog**. Process identity by **PID + `/proc/<pid>/cmdline`** —
   ⛔ never `pgrep -f`, which matches the SSH shell's own command line and makes
   the process-died branch unreachable.
3. **Two backends proven distinct** — the same-adapter guard stays armed; a
   self-pair reads as [E3](../MEASUREMENTS.md#e3), not as a result.
4. **Both raw arms committed.** No summary without its run behind it; every
   quoted figure grepped from its artefact.
5. `lint_settled_claims` clean — the verdict carries its interval.
6. **Cold ruler frozen and content-sha compared with `exit 1`** on mismatch
   (`84c2a1b5…`). The old `cold_pin` printed two hashes and compared nothing.
7. **Spend figures go in the gitignored ledger, never in committed prose.**

## 9 · What would make me wrong about this design

- ✅ *Was:* if `FLOOR_ka` comes back larger than the movement shared memory could
  plausibly produce, this run is uninformative before it starts and must not be
  bought. **§3 is a genuine gate and it FIRED** — it killed the first design
  outright, and the replacement passes with the floor at roughly half Δ\*.
- ⛔ If the run's **observed** pair-to-pair spread exceeds what §3 simulated, the
  0.848 power figure is optimistic by §3.3.2 and the achieved power must be
  **recomputed from the observed spread before any verdict is written** — not
  quoted from this document.
- If shared memory drives `force:ka` mostly through **co-movement** (§4.2), the
  instrument still has not been demonstrated on *coupling*, and a GO would be
  misread. That is why §4.2 is recorded rather than deferred.
- If the full-surface substitution turns out to change the memory model's
  character rather than only its fidelity, the arm is not Parfenova's mechanism
  and neither verdict transfers to their result.
