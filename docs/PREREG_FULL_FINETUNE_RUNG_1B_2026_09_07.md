# PREREG — rung 1b: does MORE capacity (14 → 19 layers), at a comparable dose, move lag-2 at all?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `9ccf98d6` (sha256[:8] of draft body at lock, 2026-09-07T18:34Z)
- **Date:** 2026-09-07
- **Fires on:** one full-weight fine-tune, content-transient corpus
  (`dd40e22f85b0b6e4`), then the model-lag read + F-LOCAL + perceive, all three.
- **Predecessor:** `PREREG_FULL_FINETUNE_RELEASE_2026_09_05` (**LOCK
  `a0450b36`**), fired 2026-09-07. Results:
  `RESULTS_FULL_FINETUNE_2026_09_07.md`.
- **Gates:** whether **all-28-on-FSDP is worth buying.** This run does not
  discharge §7.1's rung one; it decides whether paying for it is justified.

---

## 0 · What rung 1a taught, and how each lesson is spent here

Rung 1a (top 14 of 28, LR 1e-5) returned a clean epoch-1 **(b) STOP — floored**
— release FAIL (lag2 z=+5.79), perceive PASS (+24.05), f_local PASS, §4.1 OK —
and then **over-fit past that floor at epoch 2** (every lag rose, lag3 −0.87 →
+4.35, f_local cratered). The epoch-2 incoherence was **procedural**, not a
substrate finding.

| lesson from 1a | how this run spends it |
|---|---|
| **More training made release WORSE**, not better | The direction is suspect, so the *gating* question here is whether more **capacity** moves lag-2 **at all** (§1). |
| The early stop was gated on **GO-across-all-three**, so a floored-but-fluent epoch 1 could not trigger it, and the run over-shot its own readable floor | **The stopping rule is fixed** (§3) — it halts on *any readable state*, not only GO. |
| **`fraction_changed` saturates** (0.9999629 at both epochs) and is useless as a dose measure | **`delta_norm_estimated` is the dose measure**, recorded per epoch, and carries a pre-declared comparability check (§2.1). |
| A fused-kernel fault *looked exactly like* a substrate fault and cost two days | ⛔ **No unproven machinery on this run** (§1.2). Eager from step 0 (D-8), single GPU, the loop that just ran clean end-to-end. |

---

## 1 · The question, and why it is prior to all-28

⭐ **Does unfreezing 14 → 19 layers, at a comparable weight-movement dose, move
lag-2 toward the ceiling at all?**

§7.1's rung one is **all 28 layers**, and the locked body itself notes it
*"requires multi-GPU FSDP or a larger card."* Measured against the planner, that
is right: all 28 = **6.526 B** trainable, planner **77.5 GiB**, ×1.28 lower bound
**99.2 GiB** — **19 GiB over a single 80 GiB card**, and no §5-preserving change
closes it (batch 4→2 buys ~1.6 GiB; the fp32 master and fp32 grads at 26.1 GiB
each are exactly what §4.1 forbids shrinking).

⛔⛔ **So this run is diagnostically prior, not merely cheaper.** Rung 1a showed
training harder pushes *toward* persistence. If that direction also holds for
capacity, then more trainable layers is more capacity to push the wrong way — and
all-28 would buy a **more expensive floor**. This run answers the gating
question on **proven machinery** for ~$15–20 before ~$25–35 and an untested
distributed layer are committed.

### 1.1 · ⛔ THIS IS AN INTERPOLATED RUNG AND DOES NOT DISCHARGE §7.1 RUNG ONE

The ladder now reads:

    rung 1a   top 14 of 28, LR 1e-5      FLOORED (single reading)
    rung 1b   19 of 28, LR 5e-6          THIS RUN — interpolated
    rung 1-full  all 28, FSDP            only if 1b moves lag-2
    rung 2    unfreeze embed_tokens + lm_head
    rung 3    "the substrate is the wall" — terminal, publishable

**A floor at 19 establishes:** capacity in the 14→19 range, at a dose comparable
to rung 1a's, did not move lag-2.
**A floor at 19 does NOT establish:** that §7.1 rung one is discharged, or that
capacity is exhausted as a lever, or anything about the substrate. Only all-28
discharges rung one.

### 1.2 · ⛔ No unproven machinery, and this is a hard constraint

Nothing in this repository has ever run FSDP. Introducing it immediately after
two days spent separating a **fused-kernel fault** from a **substrate fault**
would reintroduce exactly that ambiguity on the run whose result most needs to be
trusted: a NaN or a floor on first-run FSDP is indistinguishable from a model
result without another diagnosis. **A floor at 19 is interpretable because the
loop is proven.** FSDP is earned only if 1b shows movement.

---

## 2 · §5 — the configuration, pre-declared

| field | value | why this value |
|---|---|---|
| **card** | `gpu_1x_h100_sxm5`, 80 GiB (D-7-extended) | Proven across five runs. PCIe if capacity is stable at launch; both are 80 GiB. |
| **unfrozen** | **top 19 of 28 layers** = **4.428 B** trainable | The largest count that fits fp32-master on one 80 GiB card: planner **60.7**, ×1.28 = **77.7**, **+2.3 GiB margin**. L=20 is 80.1 — over. |
| **frozen** | `embed_tokens` + `lm_head` (1.090 B) | Unfreezing them is rung 2. Not skipped. |
| **LR** | **5e-6 PRIMARY**; **2.5e-6** as the (c) dial-back, a *new* prereg | Half of rung 1a's, chosen to keep the **dose** comparable (§2.1) — not gentler for its own sake. |
| **optimizer** | `adamw_bnb_8bit`, fp32 master, 8-bit moments | As `a0450b36` §5. fp32 master is load-bearing (§4.1's dead zone). |
| **attention** | **`eager` from step 0** (D-8) | The fused SDPA backward makes non-finite gradients on this config. Pinned on **every** leg. |
| **seq / batch / accum** | 384 / 4 / 4 (effective 16) | Unchanged from `a0450b36`, so shape is not a second moving knob. |
| **corpus** | content-transient, sha **`dd40e22f85b0b6e4`** | Byte-identical to rung 1a's. Verified before training; mismatch aborts. |
| **epochs** | ≤ 2, halted by §3 | The stopping rule, not the epoch count, decides. |

⚠️ **VRAM is sized against ×1.28, not the friendlier measured ratio.** Rung 1a
predicted 51.4 and measured **63.6** — a ratio of **1.238**. The lower-bound
factor validated itself, so it stays 1.28. `PLANNER_IS_A_LOWER_BOUND` remains
true.

### 2.1 · ⭐⭐ THE DOSE-COMPARABILITY CHECK — pre-declared, so "under-dosed" is answerable

Two things change from rung 1a: **more layers** and **a lower LR**. That is two
changes against one question, and without a dose readout a floor here could not
distinguish *capacity did not help* from *we under-dosed it*.

⭐ **`delta_norm_estimated` after epoch 1 is the dose measure. Rung 1a's was
17.81.** This run records its own and the comparison is declared **now**:

- **`delta_norm` within ±30 % of 17.81** → the run is **dose-controlled**: same
  weight movement, more layers. A floor then means **capacity did not help**.
- **`delta_norm` materially below** (< 12.5) → **UNDER-DOSED.** A floor is
  **not** readable as a capacity result, and the response is a re-run at 1e-5
  with the same 19 layers — a new prereg, not a threshold change here.
- **`delta_norm` materially above** (> 23.2) → over-dosed relative to 1a; a (c)
  crater would be read as dose, not capacity.

⛔ `fraction_changed` is recorded as the §4.1 **precondition only**. It saturated
identically at both of rung 1a's epochs (0.9999629153481012, the same 21 of
566,272 sampled values unmoved) and **cannot** be used as a dose or trajectory
measure. **The field that maxes out is not the field that measures.**

---

## 3 · ⭐⭐ THE FIXED STOPPING RULE — the procedural fix from rung 1a

Rung 1a over-shot its own clean floor because the early stop fired only on GO.
Verified in code: `pipeline_fullft.sh` halts on `if [ $E1 -eq 0 ]`, and
`act2_fullft_verdict.py` returns **0 for GO alone** — every STOP row returns 1.

**This run halts at the end of epoch 1 if epoch 1 is in ANY readable state:**

    HALT and take epoch 1 as the verdict if EITHER
        GO across all three axes
      OR floored-but-fluent:  release FAIL, perceive PASS, f_local PASS
    RUN epoch 2 only if epoch 1 is itself unreadable
        (perceive fails, or f_local already fails at epoch 1)

**Rationale:** the epoch-1 read always existed to protect against an epoch-2
over-fit. Rung 1a proved a floored-but-fluent epoch 1 is *precisely* the readable
state over-fitting destroys. So the stop must fire on it.

⛔ **This changes the stopping PROCEDURE, not any threshold.** `Z_LAG1_MIN` and
`Z_LAGN_MAX` are unchanged and still imported from `tlon.discourse.transient`.
Only *when the run halts* moves, and it moves toward protecting a readable state
**sooner**, which is strictly conservative. It is declared here **before** the
run, not applied after.

---

## 4 · The reading

### 4.1 · Precondition (unchanged, and it is a precondition on the whole table)

`weight_delta.py`: `OK` / `DIVERGED` (any non-finite value) / `UNDISCRIMINATING`
/ `INSTRUMENT_FAULT`. ⛔ **Anything but `OK` voids every row below.** The
`DIVERGED` branch exists because `NaN != NaN` is True, so a destroyed weight
counts as "changed" — it returned `OK` on a NaN model once already.

### 4.2 · Three-axis GO — thresholds imported, not invented

    RELEASE:  lag-2 z <= 3.0 AND every longer lag <= 3.0
    PERCEIVE: lag-1 z >= 6.0
    F-LOCAL:  render AND speak clear (cardless, unconstrained, n=64)

| outcome | release | perceive | f_local | verdict |
|---|---|---|---|---|
| **GO** | ≤3.0 | ≥6.0 | clears | Capacity is the lever. Release installs without breaking the speaker; module and drift read un-blocked. |
| **STOP — floored** | any >3.0 | ≥6.0 | clears | 19 layers at a comparable dose did not install release. ⛔ **Not substrate, and rung one is NOT discharged.** → §5. |
| **STOP — fluency cratered** | ≤3.0 | ≥6.0 | fails | (c). Dial-back 2.5e-6, a **new** prereg. |
| **STOP — perceive killed** | ≤3.0 | <6.0 | any | ENTANGLED at the weight level; more layers could not separate hold-own from respond-to-partner. |
| **STOP — incoherent** | mixed | mixed | mixed | Instrument or training fault. **Do not interpret.** → §6 Fallback. |
| **INSTRUMENT FAULT / DIVERGED / UNDISCRIMINATING** | — | — | — | §4.1 failed. No row readable. |

⛔⛔ **NO THRESHOLD CHANGE IS AUTHORISED BY ANY STOP.** The thresholds are hashed
into this body and imported from the corpus's own constants. A lag-2 landing at
z = 3.4 is a STOP-floored, and the response is §5 — not a discovery that 4.0 was
always sensible.

---

## 5 · What a floor at 19 decides — declared before the number exists

A **STOP — floored** here is read against rung 1a's **lag2 z = +5.79** (epoch 1,
the protected reading), at a dose confirmed comparable by §2.1:

- **lag-2 moved materially DOWN toward 3.0** → capacity is the right lever and
  is under-supplied. **all-28-on-FSDP is justified**, and the FSDP-introduction
  risk is worth carrying.
- **lag-2 flat, or UP** → capacity in this range is not the lever, and the same
  answer at all-28 would cost ~2× plus an unproven distributed layer. **FSDP is
  not justified on this evidence**; the next lever is rung 2 (embeddings), or a
  re-examination of whether the corpus can train release at all at the weight
  level.

⛔ Neither branch is "the substrate is the wall." That remains rung 3.

---

## 6 · §Fallback — pre-declared response to incoherence

If this run returns **STOP — incoherent**, the response is **not** to interpret
it and **not** to climb. It is to **re-validate rung 1a under the fixed stopping
rule**: re-run the rung-1a config (top 14, LR 1e-5) with §3's stop, to obtain a
*protected* rung-1a reading and confirm the floor is real. A new pre-registered
run at the rung-1a config with **only the stop changed**.

⭐ Declared here so "wonky numbers" leads to a declared validation rather than an
improvisation.

---

## 7 · Ruler and category

This is a **`_w`** object (C8; `PREREG_ACT2_DRIFT` §0.2 in force — weights
change). The frozen `_ctx` ruler (`84c2a1b5`) is untouched and **not pooled**.
The `_w` quarantine in `tlon/act2/factorial.py` raises rather than filters. The
lag read needs no ruler (within-model against a permutation null); a two-speaker
`_w` drift read, if GO, needs its own `_w` baseline and is **deferred**.

---

## 8 · Operational

Watchdog armed **before** the floors, deadline sized to the priced run (7,520
steps at ≤1.90 s/step measured ⇒ ~4 h; deadline **14 h**, $60, under the $70/run
alert). Corpus sha-verified before training. `eager` pinned on every leg and the
resolved kernel printed. `DIVERGED` branch live. Persist-before-`~/DONE` with
manifest. `delta_norm_estimated` recorded per epoch. Throughput pulled before
terminate. Every number `_w`-labelled.

---

## 9 · What this run does NOT do

- ⛔ Does **not** discharge §7.1 rung one. Only all-28 does.
- ⛔ Does **not** re-run rung 1a as the primary — 1a is a single-reading floor,
  sufficient to proceed; re-validation is the **fallback** for incoherence.
- ⛔ Does **not** skip to rung 2 — embeddings stay frozen.
- ⛔ Does **not** change any GO threshold.
- ⛔ Does **not** interpret an incoherent result.
- ⛔ Does **not** measure two-speaker drift.
- ⛔ Does **not** read a floor as the substrate wall.
