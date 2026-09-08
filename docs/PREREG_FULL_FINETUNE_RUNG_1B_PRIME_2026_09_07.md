# PREREG — rung 1b′: does 19 layers help at rung 1a's PER-PARAMETER dose, or was rung 1b's lag-2 drop just under-dosing?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `bd435b37` (sha256[:8] of draft body at lock, 2026-09-08T00:58Z)
- **Date:** 2026-09-07
- **Fires on:** one full-weight fine-tune, 19 layers, LR **1e-5**, content-transient
  corpus (`dd40e22f85b0b6e4`), then the model-lag read + F-LOCAL + perceive.
- **Predecessors:**
  - rung 1a — `a0450b36`, 14L @ 1e-5. Floored clean at epoch 1: release FAIL
    (lag2 **+5.785**), perceive PASS (+24.046), f_local PASS. `delta_norm` **17.81**.
  - rung 1b — `9ccf98d6`, 19L @ 5e-6. Floored clean at epoch 1: release FAIL
    (lag2 **+4.844**), perceive PASS (+21.192), f_local PASS. `delta_norm`
    **10.884** — **UNDER-DOSED**, so its lag-2 drop is uninterpretable as capacity.
- **This is the pre-declared response** to rung 1b's under-dosed result
  (`9ccf98d6` §2.1: *"re-run 19 layers at 1e-5, a NEW prereg"*).

---

## 0 · The single question

⭐ **Does 19 layers move lag-2 toward the ceiling at rung 1a's per-parameter dose?**

Rung 1b was supposed to be a one-variable capacity test and under-dosed itself
out of being one. This run holds the dose constant and varies **only layer
count** against rung 1a.

⛔ Why rung 1b cannot answer it: rung 1a's own trajectory established that **less
weight movement gives lower lag-2** (its epochs ran dose 17.81 → 26.80 while
lag-2 ran 5.785 → 8.422, a slope of **+0.293 lag-2 per unit `delta_norm`**).
Rung 1b moved the weights *less* and got a lower lag-2. The 0.94 drop is exactly
what dose alone predicts, so it cannot be attributed to capacity.

---

## 1 · ⭐⭐ THE DOSE UNIT — and a defect in `9ccf98d6` that this corrects

`delta_norm_estimated` is `‖θ_final − θ_init‖` estimated over **all** trainable
parameters. **It grows with parameter count.** The same per-parameter movement
gives a larger total norm at 19 layers (4.428 B) than at 14 (3.263 B), purely
because more terms enter the sum.

⛔⛔ **So matching raw `delta_norm` across a layer-count change UNDER-DOSES the
larger run per parameter** — it would reintroduce the very confound this run
exists to remove, one level down.

⭐ **The comparable invariant is per-parameter RMS displacement:**

    rms = delta_norm_estimated / sqrt(n_trainable_params)

| run | `delta_norm` | n_trainable | **rms** | LR |
|---|---|---|---|---|
| rung 1a, epoch 1 | 17.810 | 3,262,809,088 | **3.118e-4** | 1e-5 |
| rung 1b, epoch 1 | 10.884 | 4,428,098,048 | **1.636e-4** | 5e-6 |

**rms ratio 0.525 against an LR ratio of 0.500**, and the "sublinear 0.611" seen
in raw `delta_norm` decomposes as `0.525` (LR) × `1.165` (√param-count).

⚠️ **That is ONE ratio from TWO runs, and it is not established.** It is
*consistent with* per-parameter displacement tracking LR rather than layer count
— which is what one would expect if an Adam step has magnitude on the order of
`lr` irrespective of gradient scale — but two points do not measure a slope, and
no interval is available for it. **The §4 dose gate exists precisely because
this prediction may be wrong**; nothing downstream may treat linearity as
demonstrated.

⛔ **RECORDED, NOT SMOOTHED — `9ccf98d6` §2.1 banded the dose in the wrong unit.**
Its band `12.5–23.2` was built from rung 1a's 14-layer `delta_norm` and applied
to a 19-layer run. Layer-corrected, that band at 19L is **14.5–27.0**. Rung 1b's
10.884 is under **either** band, so **its UNDER-DOSED verdict stands and its
result is unaffected** — but the gate was right by direction, not by
construction. Had rung 1b landed near 24 the locked gate would have called it
over-dosed while per-parameter it was fine. `9ccf98d6` stays locked; this
document supersedes its dose unit for all later runs.

---

## 2 · §5 — the configuration

| field | value | why |
|---|---|---|
| **unfrozen** | top **19** of 28 = **4.428 B** | Identical to rung 1b, so layer count is held against rung 1a and nothing else moves. |
| **frozen** | `embed_tokens` + `lm_head` | Rung 2 of the ladder. Not skipped. |
| **LR** | **1e-5 PRIMARY**; **5e-6** as the (c) dial-back (a new prereg) | Chosen to land the **per-parameter dose** on rung 1a's, not for its own sake. |
| **card** | `gpu_1x_h100_sxm5`, 80 GiB (D-7-ext); PCIe if stable | Planner **60.7**, ×1.28 = **77.7**, **+2.3 GiB margin**. Sized against 1.28, not the observed 1.238 — the lower bound validated itself and stays. |
| **attention** | `eager` from step 0 (D-8), both legs | The fused SDPA backward makes non-finite gradients on this config. |
| **optimizer** | `adamw_bnb_8bit`, fp32 master, 8-bit moments | fp32 master is load-bearing (§4.1). |
| **seq / batch / accum** | 384 / 4 / 4 | Unchanged from both predecessors. |
| **corpus** | content-transient, sha `dd40e22f85b0b6e4` | Byte-identical. Mismatch aborts. |
| **epochs** | ≤ 2, halted by §3 | The stopping rule decides. |

**Dose prediction:** at 19 L and 1e-5, rms should land on rung 1a's **3.118e-4**,
i.e. `delta_norm` ≈ **20.75**. ⚠️ That is an extrapolation from two dose points
across an LR change, which is why §4 is a **gate** and not an assumption.

---

## 3 · The stopping rule — carried unchanged, it worked

Halt at end of epoch 1 and take it as the verdict if epoch 1 is **GO across all
three** *or* **floored-but-fluent** (release FAIL, perceive PASS, f_local PASS).
Epoch 2 runs only if epoch 1 is itself unreadable.

⭐ Rung 1b fired this correctly — *"EPOCH 1 IS READABLE — stopping here"* — halted
at one epoch, protected the readable floor, and cost **$6.50** instead of
$15–20. Unchanged here.

---

## 4 · ⭐⭐ THE DOSE GATE — read FIRST, and it can DEFER the capacity read

`rms = delta_norm_estimated / sqrt(n_trainable_params)` after epoch 1, against
rung 1a's **3.118e-4**:

| rms | reading |
|---|---|
| **within ±30 %** — **2.18e-4 … 4.05e-4** | **DOSE-MATCHED.** Same per-parameter movement, more layers. Proceed to §5. |
| **outside that band** | ⛔ **This run is itself mis-dosed. The capacity comparison is DEFERRED, not forced.** Record the dose, do **not** read capacity, choose the next LR before concluding anything. |

⛔ **The gate keys on `rms`.** `delta_norm` is printed beside it as the
human-readable companion (compare against ≈20.75) and is **not** what the gate
tests — it is not comparable across the layer-count change this run makes.

⛔ `fraction_changed` is the §4.1 **precondition only**. It saturated to
`0.9999629153481012` at *both* of rung 1a's epochs (the same 21 of 566,272
sampled values unmoved). **The field that maxes out is not the field that
measures.**

⭐ This branch exists because a second confounded run being read as a capacity
result is exactly the trap rung 1b fell into. Deferring is the declared
behaviour, not a failure.

---

## 5 · The capacity read — pre-declared, all three outcomes

**Only if §4 passes.** Compare this run's lag-2 against rung 1a's **5.785** at
matched per-parameter dose:

| lag-2 at 19 L, rms-matched | reading |
|---|---|
| **materially below 5.785** (toward the 3.0 ceiling) | **Capacity helps at matched dose.** 14→19 moved release toward installing with dose held. **all-28 via FSDP is a justified investment.** |
| **≈ 5.785** (within noise) | **Capacity does not help at matched dose.** More layers, same dose, same floor. **Do not buy FSDP on capacity grounds** — it would purchase a more expensive floor. |
| **materially above 5.785** | **Capacity hurts at matched dose** — consistent with rung 1a's more-training-goes-the-wrong-way finding, and with rung 1b sitting **+1.09 worse** than its own dose-only prediction of 3.754. Strong evidence against FSDP-for-capacity. |

⛔ The full three-axis GO/STOP verdict still applies independently — a GO on all
three would be the module working regardless of the capacity comparison. The
expected outcome given 1a and 1b is another floored-but-fluent STOP; **the
capacity read is what this run adds over "it floored again."**

⛔⛔ **NO THRESHOLD CHANGE IS AUTHORISED BY ANY STOP.** Thresholds imported
(`Z_LAG1_MIN` 6.0, `Z_LAGN_MAX` 3.0). A floor is a floor; the capacity
comparison informs the next lever, never the ceiling.

---

## 6 · Ladder position

    rung 1a    14L @ 1e-5, dose 3.118e-4    FLOORED
    rung 1b    19L @ 5e-6, dose 1.636e-4    FLOORED, UNDER-DOSED — capacity unreadable
    rung 1b′   19L @ 1e-5, dose-matched     THIS RUN
    rung 1-full  all 28, FSDP               only if 1b′ shows capacity helps
    rung 2     unfreeze embed_tokens + lm_head
    rung 3     "the substrate is the wall" — terminal, publishable

⛔ **A dose-matched floor at 19 L does NOT discharge §7.1 rung one.** Only all-28
does. But per §5 it **undercuts the case for paying for FSDP on capacity
grounds** — buying more of a lever that did not move at 14→19.

---

## 7 · §Fallback — carried

If this run returns **STOP — incoherent**, do not interpret and do not climb:
re-validate rung 1a under the fixed stopping rule, as a new pre-registered run
at the rung-1a config with only the stop changed.

---

## 8 · Provenance — fixed before this run, and this is the first run it protects

`act2_fullft_verdict.py` hardcoded `"PREREG": "a0450b36"`, so **rung 1b's verdict
shipped claiming the wrong pre-registration.** Fixed: the tool now takes
`--prereg <path>`, reads the LOCK id from the locked file, and **re-hashes the
body**, refusing to emit if it has moved since the lock. An id copied from a
stamp line proves only that someone typed it.

⭐ **So this prereg's LOCK will be verified at verdict time** — the first run
whose attribution cannot rot.

⚠️ **Six of this repo's 22 preregs carry no hash at all** and are locked by prose
assertion: `ASPECT_ROOT_MECHANISM`, `ASYMMETRIC_RECERT`, `KI_AS_TARGET`,
`LOCALITY_ISOLATION`, `RECIPE_VARIANCE`, `VARIANCE_DECOMPOSE`. ⛔ **They are NOT
retroactively hashed.** Stamping one now would hash *today's* body and prove
nothing about what was locked then — a false provenance claim is worse than an
absent one. They are marked as prose-locked-unverifiable, left alone, and any
current decision resting on one carries that weaker provenance explicitly.

---

## 9 · Operational

Watchdog armed before the floors. Corpus sha-verified. `weight_delta` `DIVERGED`
branch live (non-finite voids the whole table). `delta_norm_estimated` **and**
`rms` recorded per epoch. `eager` pinned on both legs with the resolved kernel
printed. `_w` quarantine raises. Persist-before-`~/DONE` with manifest.
Throughput pulled before terminate. VRAM confirmed at +2.3 GiB before launch.
Every number `_w`-labelled.

---

## 10 · What this run does NOT do

- ⛔ Does not discharge §7.1 rung one (all-28).
- ⛔ Does not change any GO threshold.
- ⛔ Does not read capacity if §4 defers.
- ⛔ Does not interpret an incoherent result.
- ⛔ Does not retroactively hash any prereg.
- ⛔ Does not measure two-speaker drift.
- ⛔ Does not read a floor as the substrate wall.
