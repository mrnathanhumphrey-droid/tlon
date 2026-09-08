# RESULTS — rung 1b′: the dose-matched capacity test

**PREREG** `PREREG_FULL_FINETUNE_RUNG_1B_PRIME_2026_09_07.md`, **LOCK
`bd435b37`** — re-hashed and verified *by the run itself*, at
`step prereg_id`, before training. ⭐ **The first run in this arm whose
attribution is verifiable end to end**: the same verified id is stamped into
both `verdict_fw19b-s20624_e1.json` and `fw19b-s20624/factorial.json`.

Run `fw19b-s20624` · box `1a7b5c7db932432daacf46fa64151374` ·
`gpu_1x_h100_sxm5` us-south-2 · pinned `3f4ffb3` · **1 epoch, halted by the
stopping rule** · ~1.3 h · **~$9** · self-terminated after persisting.
Corpus sha-verified `dd40e22f85b0b6e4`. `eager` from step 0 (D-8), resolved
kernel printed.
Artifacts: `hf://keyzersoze04/tlon-act2-adapters/fw19b-s20624/` and
`.../fullft_fw19b-s20624/`.

---

## 1 · The question, and the answer

> **`bd435b37` §0:** *"Does 19 layers move lag-2 toward the ceiling at rung 1a's
> per-parameter dose?"*

**No.** At a matched per-parameter dose, lag-2 came in **above** rung 1a's, not
below.

| run | scope | LR | `delta_norm` | **rms** | lag1 | **lag2** | lag3 | f_local | verdict |
|---|---|---|---|---|---|---|---|---|---|
| rung 1a | 14L | 1e-5 | 17.812 | 3.1182e-04 | 24.046 | **5.785** | −0.874 | PASS | `STOP — floored` |
| rung 1b | 19L | 5e-6 | 10.884 | 1.6356e-04 | 21.192 | 4.844 | 0.674 | PASS | `STOP — floored` |
| **rung 1b′** | **19L** | **1e-5** | 19.985 | **3.0032e-04** | 23.352 | **5.966** | 2.266 | PASS | `STOP — floored` |

Every figure above is copied from its artifact
(`weight_delta*.json`, `verdict_*_e1.json`), not from prose.

**§4 dose gate: MATCHED** — rms `3.0032e-04` is **96.3 %** of rung 1a's
`3.1182e-04`, inside the pre-declared band `2.18e-04 … 4.05e-04`. So §5's
capacity read is licensed rather than deferred. §4.1 precondition OK,
`fraction_nonfinite` **0.0**.

⭐ **The §2 dose prediction survived a test that could have refuted it.** It
predicted `delta_norm ≈ 20.75` at this scope and LR; the run produced
**19.985**, 3.7 % under. That is a third point consistent with per-parameter
displacement tracking LR rather than layer count. ⚠️ It is still not a measured
slope and carries no interval.

---

## 2 · The FSDP decision, and the limit of what licenses it

§5 pre-declared three branches. **"Materially below 5.785" — the only branch
that justifies FSDP — is not satisfied.**

⛔ **Whether this row is "≈ 5.785 (within noise)" or "materially above" cannot be
resolved, because `bd435b37` §5 never operationalised "materially".** That is a
**defect in the pre-declaration**, recorded as one — the same class as the
control-fork defect in `FINDINGS_FULLFT_TRACE_2026_09_06.md` §8, where a
pre-declared fork stopped the choosing without making the inference sound.

⭐ **The decision is determined anyway: both surviving branches prescribe the
same action.** "Capacity does not help" and "capacity hurts" both say *do not
buy FSDP on capacity grounds*. The ambiguity is real and it is not
load-bearing here.

**The residual dose gap cuts against capacity, not for it.** This run moved the
weights **less** than rung 1a (96.3 %). Rung 1a's own within-run trend was more
dose → *higher* lag-2 (dose 17.81 → 26.80 as lag-2 went 5.785 → 8.422). So the
lower dose should have flattered this run, and lag-2 still came in higher.

⛔ **No dose-corrected point estimate is quoted.** Rung 1a's `+0.293 lag-2 per
unit delta_norm` slope is a within-run, 14-layer quantity, and extrapolating it
across a layer-count change is exactly the move flagged as suggestive-not-
measured. The *direction* is legible without the arithmetic; the magnitude is
not available.

---

## 3 · What this does NOT establish

- ⛔ **It does not discharge §7.1 rung one.** Only all-28 does. What changed is
  that the case for *paying* for FSDP is now evidence-backed against rather
  than unexamined.
- ⛔ **n = 1 per configuration.** No repeat seeds, no error bars, no measured
  effect size. One dose-matched comparison.
- ⛔ **It is not a substrate finding.** A floor is a floor; §7.1's ladder is not
  exhausted.
- ⛔ **No threshold moved.** `Z_LAG1_MIN` 6.0 and `Z_LAGN_MAX` 3.0 imported
  unchanged from `tlon.discourse.transient`.

---

## 4 · Three floored runs, and the thing that does not move

Across three scopes and three doses the shape is identical: **perceive passes
enormously** (21.2 – 24.0 against a floor of 6.0), **f_local passes**, and
**release fails on lag-2 alone**. Rung 1b′'s lag-3 (2.266) is under the 3.0
ceiling, so release fails on one lag.

⚠️ **lag-3 has risen across the three runs: −0.874 → 0.674 → 2.266.** It
breaches nothing and it is confounded with every other thing that differs
between these runs (scope, LR, dose). Written down because it is trending
toward the ceiling, **not** because it is a result.

---

## 5 · The instrument, which is now the part that works

- **The stopping rule fired correctly for the second time.** Epoch 1 was
  floored-but-fluent → `readable_stop()` → exit 4 → halted. Rung 1a trained
  past exactly this state and destroyed it; that has not recurred.
- **The verdict names and re-hashes its own prereg.** The stamps across the
  three runs read `a0450b36`, `a0450b36`, **`bd435b37`** — rung 1b's verdict
  still claims a pre-registration it did not answer, preserved as the record of
  the defect. 1b′ is the first that cannot rot.
- **The run reproduced bit-identically after the failed attempt**:
  `delta_norm` **19.984646** on both boxes, same seed, same corpus sha, same
  code sha. So nothing about the rebuild changed the measurement.
- **The persist-capacity floor was live and passed** (`✅ FITS`, 19.18 GiB
  spare) ten seconds before the prereg check and 35 seconds before training.

---

## 6 · What the next run has to carry

1. ⛔ **Operationalise "materially" before any fork that compares two lag-2
   values.** A branch whose trigger is a word is a branch that gets argued
   after the fact.
2. ⛔ **The ledger is not persisted.** `f_local` is an input to the verdict and
   its row — render/speak rates, comprehension — dies with the box. The
   conclusion survives in the verdict JSON; the evidence for it does not. Same
   shape as the `weight_delta.json` path-reuse, one level over.
3. ⚠️ **Comprehension read `UNSCOREABLE — 256/256 unanswered`** on this run.
   It is **not** one of the three axes and enters no branch of the verdict
   table, and F-LOCAL is `min(render_rate, speak_rate)` — emission legality —
   so the axis is not vacuous. But there is no comparable reading from rung 1a
   or 1b (see 2), so whether this is normal for the arm is **unknown**.
