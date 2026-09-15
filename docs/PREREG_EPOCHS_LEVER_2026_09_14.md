# PREREG — the epochs lever: does REPETITION install release beyond dose, at matched steps?

- **Cell:** `epochlev-s20624` (arm B `epochlevB-s20624`, arm A `epochlevA-s20624`)
- **LOCK:** `3c56054e` (sha256[:8] of draft body at lock, 2026-09-15T17:08Z)
- **Status:** LOCKED — pre-registered. Not fired.
- **Fires on:** two full-weight fine-tunes, layer rung top-half,
  `mistralai/Mistral-7B-Instruct-v0.3`, LR 1e-5, **step counts matched to within
  a pre-declared 0.2 %** (§2.1), differing **only** in corpus repetition. F-LOCAL
  + release read at checkpoints matched to arm B's rms ladder.
- **Cost:** **$19.4 (quote $18–23)** — priced against two recorded anchors
  agreeing within 2.5 % (`miscurve75` $7.70/2.40 h = $3.21/h; `mis16d`
  $5.53/6,049 s = $3.29/h). ⛔ Not estimated: cost was guessed low twice in this
  campaign ($6 vs $12.07; $6 vs $7.70).

---

## 0 · The question, and why this design separates what the last one could not

`miscurve`'s **unregistered** epoch 2 improved lag2 `8.87 → 7.53` and dropped
lag3 under the 3.00 ceiling — the campaign's **only** signal pointing toward
release *installing*. Unregistered, therefore unusable. This run registers it, at
the layer rung where the clean n=2 floor lives.

⛔ **The trajectory design is impossible and was killed.** Within one fixed-LR
run, *"release vs rms"* and *"release vs epochs"* are the same curve relabelled:
rms is a deterministic monotone function of steps (`rms ∝ steps^0.144`) and
steps = epochs × steps_per_epoch, so there is **no residual to read**. And there
is **no release-vs-dose reference curve anywhere** — verified against the
artefacts: both `dose_curve_*.jsonl` carry `speak`/`render`/`rms` and **no lag
field at all**. Release has never been measured at more than one dose, at any
scope. Every curve "explains" the single trajectory you have. **Self-prediction,
third instance in this campaign.**

⛔ **Cross-LR matched-rms is also killed** — by our own measurement. `miscurve`
vs `miscurve75` put render at **51.6 % vs 14.1 % at matched rms**, so LR-path is
a *measured, large* confound. Using LR as the lever trades an unmeasured confound
for a severe measured one.

⭐ **The design that works — hold LR, steps and dose fixed; vary ONLY repetition.**

```
arm B (control)   full corpus,     1 epoch    <- max diversity, single pass
arm A (repeat)    1/4 of it,       4 epochs   <- 4x repetition, matched steps
```

Identical LR, identical optimizer steps, matched rms by construction. The only
difference is **N distinct examples seen once vs N/4 seen four times** — which is
what "epochs" *mechanically means*. Arm B runs first and records its rms ladder;
arm A fires its reads at arm B's **measured** rms values via `TargetLadder` — the
proven `miscurve → miscurve75` matched-by-construction pattern. No extrapolation,
no fitted exponent, no self-prediction.

---

## 1 · ⛔⛔ THE PRE-DECLARED ASYMMETRY — this run can confirm the lever, not refute it

`epochs = steps ÷ distinct`, so steps, dose **and** diversity cannot all be held
fixed while epochs varies. Here **diversity gives**: the repeat arm sees fewer
distinct examples. Declared in the reading, not discovered afterwards:

| finding | reading |
|---|---|
| arm A **better** on release, F-LOCAL holds | ⭐ **STRONG** — repetition helped *despite* a diversity headwind, so the effect overcame a penalty. Epochs is a lever; miscurve's contrary signal confirmed. Would change the art-piece calculus. |
| arms **equal** | ⭐ **CLEAN** — dose is what matters; repetition neutral. The dose story, confirmed. |
| arm A **worse** | ⚠️ **AMBIGUOUS** — repetition hurting **or** diversity loss. The design cannot separate them. **NOT a refutation of the lever.** |
| F-LOCAL craters in either arm | release unreadable there; read release only at faithful checkpoints |

⛔ **Do not read "arm A worse" as "epochs does not help."** Acceptable only
because the run exists to test whether the contrary signal is *real*, and it
confirms that direction cleanly if true.

---

## 2 · Configuration

| field | value | why |
|---|---|---|
| base | `mistralai/Mistral-7B-Instruct-v0.3` | closest to the ceiling (**+3.972**, gap 0.972 vs Qwen's 2.785 — if the effect ≈ miscurve's −1.34, Mistral clears and Qwen would not); faithful speaker (speak 100 %, render 93.8 %) so F-LOCAL is least likely to gate the read. ⭐ Qwen's dose-fit advantage is **moot**: this design separates by construction, not by a fit. |
| scope | layer rung, top-half (16 of 32), verified against the real header | matches the n=2 floor this compares to |
| LR | 1e-5 | the layer-rung standard, matched to the floors |
| corpus | `content-transient`, sha **`dd40e22f85b0b6e4`**, rebuilt and sha-verified on the box before training | the pinned corpus; a mismatch means every downstream number is about a different language |
| arm B | **full** corpus × 1 epoch, `EPOCH_BUDGET=1` | control |
| arm A | **derived 1/4 subsample** × 4 epochs, `EPOCH_BUDGET=4` | repeat |
| `EPOCH_BUDGET` | **4 (arm A) / 1 (arm B) — ONE PAIRED STATEMENT, declared = enforced** | `8905a45`: a run may not buy an epoch its prereg did not declare. Here the budget **is** the repeat factor. |
| steps | **matched across arms to within `STEP_MATCH_TOL = 0.002`** (0.2 %), derived from the sha-verified corpus and asserted before training; both exact counts recorded (§2.1) | the variable held fixed — the whole point. ⛔ Bounded, not exact: arm A can only land on multiples of 4, so exactness is not available on demand. Over the bound the run **refuses**. |
| batch / accum / seq | 4 / 4 (effective 16) / 384 | the gate's shape, unchanged |
| card | `h100_pcie` | matches the layer-rung hardware; no gratuitous variable |
| attention | eager, resolved kernel printed | demonstrated clean on Mistral |
| optimizer | `adamw_bnb_8bit`, fp32 master | unchanged |

### 2.1 · ⛔⛔ THE SUBSAMPLE SIZE IS DERIVED AND ASSERTED, NEVER HARDCODED

The draft of this prereg hardcoded *"60,158 rows → 15,039 × 4 = 3,759 steps
both arms."* **Both numbers were wrong, and the second was wrong in the one
variable this design holds fixed:**

- ⛔ **60,158 rows came from the wrong corpus.** It is the row count of
  `runs/act2/retrain12_ct/corpus_ct-s20624/train.jsonl`, whose sha is
  **`16abeb8d27e4ccd3`** — *not* the pinned `dd40e22f85b0b6e4`. **No corpus on
  disk matches the pinned sha**; the pipeline rebuilds it on the box. A row count
  was taken from one artefact and labelled with another's identity.
- ⛔ **3,759 is the curve's own `_total`, not the trainer's `state.max_steps`.**
  The curve computes `len(dataloader) // accum` (**floor**); the trainer computes
  `ceil(len(dataloader) / accum)`. On the pinned corpus those differ by one —
  `miscurve` recorded `of: 3759` while its `state.max_steps` was **3,760**. The
  same off-by-one already corrected once in this campaign: deriving a total the
  system already knows.
  ⛔ **And my first correction of this repeated the original sin.** I justified
  "3,760" by recomputing it from **60,158 rows — the wrong corpus again**.
  3,760 happens to be right for the pinned corpus, but the derivation offered
  for it was not. **Neither number is knowable from anything on this disk**; both
  come from the trainer at runtime, which is what §2.1 now enforces.

⭐ **So the size is computed from the corpus that was actually sha-verified.**
After `corpus_pin` passes:

```
S_B = ceil(ceil(N / batch) / accum)                    # arm B, 1 epoch
M   = the subsample size MINIMISING | steps(M, 4 epochs) - S_B |
S_A = ceil(ceil(M / batch) / accum) * 4                # arm A, 4 epochs
```

### ⭐⭐ `STEP_MATCH_TOL = 0.002` — the bound, declared HERE, before the corpus rebuilds

**The match criterion is BOUNDED, not exact:** proceed iff
`|S_A − S_B| / S_B ≤ 0.002` (0.2 % of arm B's step count).

⛔ **Why bounded and not exact.** Arm A's total is `4 ×` an integer, so it can
only land on multiples of 4. If `S_B` is not such a multiple, **no subsample
reaches it exactly** — and `N` is whatever the generator emits against the pinned
sha, not a dial. "Exact or refuse" would make the run **un-fireable on an unlucky
row count**, treating a two-step difference as fatal.

⭐ **Why 0.2 % is negligible, stated before the number is seen.** The effect under
test is miscurve's epoch-2 movement of **lag2 by 1.34**. 0.2 % of ~3,760 steps is
~8 steps of dose difference, which moves release by orders less than that — far
below the resolution the comparison needs. ⛔ **The bound is registered here so it
cannot become a post-hoc "close enough" once the mismatch is visible.** This is
the `resolution_match` discipline: *"matched to ±0.2 %"* is a declared quantity
with stated reasoning, not a judgement made after the measurement.

⛔ **Above the bound the run REFUSES.** A mismatch past 0.2 % means a difference
between the arms could be a step-count difference rather than repetition — the
confound the whole design exists to exclude. An awkward row count must block a
**confounded run**, not be waved through. The refusal is itself recorded.

⭐ **What the bound actually costs, measured across corpus sizes:** because arm A
lands only on multiples of 4, **`|S_A − S_B|` is structurally ≤ 2**. So the bound
is satisfied for every `S_B ≥ 1,000` and binds only on a small corpus. At this
run's scale it is **insurance, not a constraint** — at `N ≈ 60,150` the match
comes out **exact (Δ = 0)**.

### The held-fixed variable, precisely

Not "steps are equal" but **"steps matched to within a pre-declared 0.2 %"**, and
**both arms' exact counts are recorded** — `S_A`, `S_B`, `Δsteps`, `Δfrac`, `M`,
its seed and its sha all land in the run manifest before the first optimizer
step. ⛔ The manifest never says *"matched"*: a boolean hides the match quality a
reader needs to judge. §1's asymmetry and reading are unchanged — the arms still
differ only in repetition-vs-diversity, now with a declared tolerance rather than
an unreachable exactness.

⛔⛔ **AND THE DERIVED NUMBERS ARE PREDICTIONS, NOT THE RECORD.** They mirror the
trainer's own step formula so the run can refuse **before** GPU time is bought;
authoritative totals are `state.max_steps` on each arm, and the same criterion is
re-run on those. Re-deriving a total the system already knows is exactly how
`3,759` (the curve's floor) got mistaken for `3,760` (the trainer's ceil).

---

## 3 · The read

At each checkpoint (arm B's rms ladder; arm A matched via `TargetLadder`):

1. **F-LOCAL** (`render` + `speak`) — gates the checkpoint: a cratered speaker
   makes release unreadable there.
2. **release**, via the **one shared `read_lag` fold** (`65f4eae`) — the
   checkpoint and the end verdict are the same instrument, not two.
3. **rms** — confirms the arms are matched. ⛔ If arm A's rms at a read diverges
   from arm B's ladder value, **the match failed at that rung** and the pair is
   reported UNDERPOWERED, not compared.

In-process, inside `isolated_read` (proven to restore module mode, RNG and grads
and to *assert* it did). Readings-only persisted — checkpoints are 14.5 GB.

---

## 4 · Carried guards — all proven, including the one that nearly manufactured a confirmation

- ⛔⛔ **Scoreability per checkpoint on the lag read.** A small cell yields a small
  z **no matter what the speaker did**; at lag ≥ 2 that is a **vacuous release
  pass**, and early checkpoints are exactly where cells are small. `read_lag`
  compares `resolving_power` against `threshold_for_lag` and records
  `z: null` beside `n_pairs` — never a number.
  ⭐⭐ **PROVEN BY RUNNING THE MUTANT, AND IT FAILED THE FIRST TIME.** The guard
  asserted `"resolving_power" in ast.dump(fn)`; a mutant replacing the whole call
  with `power = float('inf')` **passed**, because the string survives as a dict
  *key*. That is the mutation that would have **manufactured a confirmation of
  the hypothesis under test**. Rewritten to assert the AST `Call`, plus a test
  that *calling is not using* — the value must gate the z. **Five mutants, all
  caught** (`65f4eae`).
- **Shared `read_lag` fold** (`65f4eae`) — checkpoint and verdict cannot drift.
- **Isolated eval RNG** — validated live on `miscurve75`: the endpoint reproduced
  `mismap` at 17/64 and rms to five figures after six in-process reads.
- **Pinned-statistic guard** — a gate statistic read once per run can never reveal
  it is constant. This run reads repeatedly, so a pinned statistic shows
  (the `0.51220703125` lesson).
- **In-trainer §4.1 defers to per-leaf** (`d8cfaef`) — the $7.70 false halt; plus
  the call-site **signature scan** that finds gates instead of checking a list.
- **Flush covers the readings on every exit** (`fb7962f`) — validated on an rc=3
  pre-persist exit, which is the shape that lost `miscurve`'s curve.
- `EPOCH_BUDGET` declared = enforced (`8905a45`).
- Watchdog armed **first**; corpus sha-verified **both arms**; `base_audit` clean;
  deduplicated capacity floor; provenance carries the verified prereg id;
  throughput pulled **before** terminate.

---

## 5 · What this run does NOT do

- Does **not** test the mapping locus (parked).
- Does **not** change any threshold — `Z_LAGN_MAX` 3.0, `Z_LAG1_MIN` 6.0,
  imported.
- Does **not** cleanly refute the lever (§1) — "arm A worse" is ambiguous.
- Does **not** read release where F-LOCAL cratered.
- Does **not** separate epochs from dose by trajectory or by cross-LR — both
  killed in §0. Only by matched-steps repetition-vs-diversity.
- Does **not** hardcode a subsample size or a step count (§2.1).

---

## 6 · Fallback

| condition | reading |
|---|---|
| no `M` satisfies §2.1 | ⛔ **REFUSE TO TRAIN.** The held-fixed variable cannot be held fixed on this corpus. |
| arm A's rms misses arm B's ladder value at a rung | that pair is **UNDERPOWERED**; report per-arm curves, not a matched comparison |
| corpus sha ≠ `dd40e22f85b0b6e4` | ⛔ refuse — the deterministic rebuild is broken and every number is about a different language |
| incoherent / `DIVERGED` / pinned statistic | **VOID** per the standing guards |
| F-LOCAL craters in **both** arms | no readable release; the run reports **the crater**, not the lever |
