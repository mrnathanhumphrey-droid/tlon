# PREREG — Mistral rung 2: does the wall hold past the layer rung on the second family, and can release install WITHOUT killing the speaker?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `afe75eca` (sha256[:8] of draft body at lock, 2026-09-13T15:26Z)
- **Date:** 2026-09-13
- **Cell:** `mismap-s20624`
- **Fires on:** one full-weight fine-tune of **`mistralai/Mistral-7B-Instruct-v0.3`**,
  `embed_tokens` + `lm_head` trainable and **all 32 transformer layers frozen**
  (`--scope-mode mapping`), **268,435,456** trainable — measured off the real
  safetensors header on 2026-09-13 (`lm_head.weight` +
  `model.embed_tokens.weight`, `tie_word_embeddings: false`, one stack of 32) and
  **re-verified at run time, never carried from this file** — content-transient
  corpus `dd40e22f85b0b6e4`, then the three-axis read.
- **Predecessors:**
  - **Mistral layer rung**, cell `mis16d-s20624`, PREREG `5f4a554c` — **floored
    at lag-2 +3.972** with a faithful speaker (F-LOCAL clear, speak 100.0 %,
    render 93.8 %) at 99.1 % dose match.
  - **Qwen mapping rung**, PREREG `c2a4f0ca`, cell `fwmap-s20624` — **STOP,
    perceive killed**: `release ok=TRUE, lag2 0.681`, `perceive ok=false,
    z_lag1 2.232`, `f_local fired`.

---

## 0 · Why this rung, and the sharper thing it is actually for

**The layer rung floored on a second faithful family.** Mistral **+3.972**, Qwen
**+5.785**, both above the 3.0 ceiling, both dose-matched, both through the
speakerhood gate. Installation-resistance *replicates at the layer rung*, n=2.
This rung asks whether it **holds past the layer rung** on the second family, at
the **mapping locus** — frozen in every Mistral run so far.

⭐ **Mistral is the right base for it, twice over.** It floored *closest to the
ceiling*, so it is **the base nearest to clearing** and the one most likely to
surprise. And a floor here extends the cross-family claim from one locus to two.

### ⛔⛔ 0.1 · THE CAMPAIGN'S ONE "RELEASE PASSED" IS WHERE THE SPEAKER DIED

Read off Qwen's own mapping verdict, `fullft_fwmap-s20624/verdict_fwmap-s20624_e1.json`:

```
verdict    STOP — perceive killed
release    ok: TRUE    lag2 z = 0.681   (ceiling 3.0)
perceive   ok: false   z_lag1 = 2.232   (floor 6.0)
f_local    ok: false   fired: true
```

**That is the only `release ok=TRUE` anywhere in this campaign, and it happened
exactly where the model stopped being a speaker.** Every layer rung floored with
the speaker intact; the one place release "passed", the speaker was gone.

⛔⛔ **So the campaign cannot currently separate two hypotheses:**

| | claim | what the evidence so far says |
|---|---|---|
| **(A)** | **Release does not install.** | Supported by every layer rung: release fails, speaker survives. |
| **(B)** | **Release and speakerhood are in tension** — you get one or the other, and Qwen's mapping "release pass" is really *the speaker collapsed, so there is no content left to persist, which reads as release*. | Equally consistent with the same rows. Not yet excluded by anything. |

⭐⭐ **THIS RUN IS THE FIRST CHANCE TO SEPARATE THEM**, because it is the mapping
locus on the base nearest to clearing, matched to Qwen's one collapse:

- **Floored but survives** (release FAIL, perceive PASS, f_local PASS) → supports
  **(A)**. Release does not install; the speaker is fine; no tension.
- **"Release passes" by collapsing** (release OK, perceive killed and/or f_local
  fired) → supports **(B)**, the nastier reading — a second family reproduces
  Qwen's trade.
- **Release installs *while* the speaker survives** → **breaks both (A) and (B).**
  This is the only real GO.

⛔ **THEREFORE THE BAR IS `release WITHOUT collapse`, AND IT IS WRITTEN INTO §6
AS THE GO CONDITION**: lag-2 ≤ 3.0 **while** lag-1 ≥ 6.0 **and** F-LOCAL clear.
Stated here so that a GO row can never be claimed by a repeat of Qwen's collapse.

### ⭐ 0.2 · Why this matters beyond the matrix

If **(B)** is true, the art piece does not merely need release *installed* — it
needs **release and speakerhood coexisting**, which is a strictly harder bar, and
one the ground-up build would have to demonstrate is *possible at all*, not just
reachable. That raises the stakes on the ground-up cost decision
(`docs/DIRECTION_ELASTICITY_AND_GROUNDUP_2026_09_13.md`), and this is the first
look at it. ⛔ It is a reason to run; it is **not** a branch, and nothing in §6
reads it.

---

## 1 · SCOPE — Option A (mapping only), same as Qwen rung 2

**`embed_tokens` + `lm_head` ONLY; all 32 Mistral layers frozen.** The clean
single-variable test of the mapping's role. Option B (mapping + layers) is
rejected for the same reason as Qwen rung 2: the Mistral layer rung is answered
(floored), and adding layers back re-confounds a settled variable and would make
a floor ambiguous between two loci.

⚠️ **Mistral's mapping is SMALL, and vocabulary is why.** Mistral's vocab is
**32,768** against Qwen's **152,064**, so the mapping is **268,435,456** params
against Qwen's **1,089,994,752** — **4.06× smaller**, measured on both sides, not
estimated. ⛔ This is *why the cross-family read is verdict-vs-verdict and
ruler-free* (§3), and it means VRAM is even less of a constraint than Qwen's
mapping rung was.

⭐ **The tied-checkpoint refusal cannot fire here** — `tie_word_embeddings:
false` is measured on this base, two separate 134,217,728-param matrices. The
refusal stays armed anyway, because a guard that is switched off for a base is a
guard that is not there for the next one.

---

## 2 · Configuration

| field | value | why |
|---|---|---|
| **base** | `mistralai/Mistral-7B-Instruct-v0.3` | The second faithful family. |
| **trainable** | `embed_tokens` + `lm_head`, **268,435,456** | Measured off the real header; **re-asserted at run time against the model**, never read from this file. Tied → REFUSED (armed, cannot fire on this base). |
| **frozen** | all 32 transformer layers + `model.norm` | The inversion of the layer freeze. |
| **LR** | **1e-5** | Matched to Qwen rung 2, so the cross-family mapping comparison is at one LR. §3: dose is not the gate. |
| **card** | **`gpu_1x_h100_pcie`, us-west-3** | ⭐ **Matched to `mis16d`, the datapoint this reads against.** Changing card or region mid-family introduces a variable for no stated gain. ⛔ If capacity forces `gpu_1x_h100_sxm5`, that is permitted **only with the reason recorded in `INSTANCE.json`** — a stated deviation, never a silent one. |
| **attention** | `eager`, pinned both legs (`tools/pipeline_fullft.sh:84`) | ⭐ **Demonstrated clean on Mistral, not assumed**: `mis16d` ran under this same pin with `delta` OK, `fraction_changed` 0.9999457 and zero non-finite gradients. The remaining obligation is a **sanity check, not an open question** — confirm the resolved kernel prints and the early steps are clean. |
| **optimizer** | `adamw_bnb_8bit`, fp32 master | fp32 master is load-bearing. |
| **seq / batch / accum** | 384 / 4 / 4 | Unchanged. |
| **corpus** | content-transient, `dd40e22f85b0b6e4`, sha-verified | Byte-identical. Mismatch aborts. |
| **epochs** | ≤ 2, halted by §4 | The stopping rule decides. |

**Pre-run gates, all structural and all already in the pipeline:** `base_audit`
(step before `train_leg1`) passes for Mistral across loader / tokenizer /
chat-template train-vs-read shape survival / scope — the four Mistral instrument
faults are fixed and witnessed; `eos_guard` confirms a genuine eos survives
label masking; the `chat_shape` fold makes the read prompt a literal prefix of
the training text by construction; `verified_prereg_id` re-hashes this file.
❓ **UNKNOWN is not PASS** — an audit path that cannot run reports UNKNOWN and is
counted separately.

---

## 3 · THE DOSE COMPARISON IS CROSS-FAMILY *AND* CROSS-POPULATION — NOT THE GATE

Two independent reasons rms-matching does not transfer: (1) mapping trains
**embedding rows**, a structurally different parameter population from layer
matrices, with different init scales and gradient magnitudes — Qwen rung 2's §3
weakness, unchanged; (2) this is a **different base** with a 4.06× different
mapping and a different tokenizer. A "dose-matched" claim here would be the
`resolution_match` error twice over.

⭐ **The primary read is the ABSOLUTE VERDICT** — does release install (lag-2 ≤
3.0) without collapse (§0.1) — and the **cross-family comparison is
verdict-vs-verdict**, never magnitude-vs-magnitude across bases. `rms` and
`delta_norm` are still recorded per epoch for the trajectory and the over-fit
check the stopping rule needs. ⛔ **Descriptive context, not a gate. No branch
below reads them.**

---

## 4 · The stopping rule — carried unchanged, it has fired correctly three times

Halt at end of epoch 1 and take it as the verdict if epoch 1 is **GO across all
three** *or* **floored-but-fluent** (release FAIL, perceive PASS, f_local PASS).
Epoch 2 runs only if epoch 1 is itself unreadable. (Rung 1b′, rung 2, and the
Mistral layer rung.)

---

## 5 · THE PER-LEAF `mapping_moved` GATE — carried, and it matters MORE here

Same asymmetric-gradient risk as Qwen rung 2: `lm_head` sits one step from the
loss, `embed_tokens` is reached only after the gradient traverses **all 32**
frozen layers. So the plausible failure is **`lm_head` trains, `embed_tokens`
gets nothing** — a state that **passes** the global §4.1 precondition, because
the global delta is non-zero, carried entirely by the half that worked, and
therefore **fakes a floor**. ⛔⛔ The false floor and the finding are the same
observation.

⭐ **A floor verdict is NOT readable unless BOTH `embed_tokens` AND `lm_head`
show non-zero `changed` and non-zero `delta_norm_estimated` in `per_module`.**
Either leaf still → `MAPPING_FROZEN` → **instrument fault, not a floor**, and no
row of §6 may be read. A missing `per_module` record refuses rather than
certifying: an unmeasured mapping is not a moved one.

**Per leaf, against that leaf's own prediction** — `lm_head` dense (≈1.0),
`embed_tokens` sparse, because the gradient only reaches rows for tokens that
actually appear. ⭐ **THAT PREDICTION IS COMPUTED, NOT REMEMBERED.**
`tools/act2_vocab_coverage.py` runs as `step vocab_coverage` (SCOPE: mapping)
**before** `step mapping_moved`, scans the corpus **as the trainer sees it**
under **this run's own tokenizer**, and its `coverage` is passed into
`mapping_moved(d, vocab_coverage=...)`. No prediction → `MAPPING_UNVERIFIED`,
which is not a pass.

⛔ **So "recompute coverage for Mistral" is not an instruction anyone has to
remember — it is what the step does by construction**, and a per-base figure
cannot be carried in from another base even by accident. ⛔ **No Qwen coverage
number appears in this prereg**, because a figure quoted here that is not in the
record is exactly the 182-z failure: the draft of this document carried one, and
it could not be sourced.

Scope is positively selected and asserted — both leaves matched by name, no
layer tensor in the trainable set, the layer freeze asserted on the model and
not merely on the name list — because a selector matching nothing trains a
frozen model and reads as a substrate floor.

---

## 6 · The verdict table

    RELEASE:  lag-2 z <= 3.0 AND every longer lag <= 3.0
    PERCEIVE: lag-1 z >= 6.0
    F-LOCAL:  render AND speak clear

⛔⛔ **A GO REQUIRES ALL THREE, AND §0.1 IS WHY THAT IS NOT PEDANTRY.** Release
alone is not a GO; the one release-pass in this campaign came with a dead
speaker. **The GO condition is release WITHOUT collapse.**

| outcome | reading |
|---|---|
| **GO** — release OK **and** perceive OK **and** f_local clear | ⭐⭐ **Release installs in Mistral's mapping while the speaker survives.** Breaks **both** (A) and (B): release is installable, and not only by destroying the speaker. The biggest surprise available in the campaign, on the base nearest clearing. The drift/art substrate exists on this base and the ground-up question changes shape. |
| **STOP — floored** (release FAIL, perceive PASS, f_local PASS) | Mapping alone does not install release on Mistral. **A second faithful family fails at TWO loci** (layer + mapping). ⭐ Supports **(A)** over **(B)**: resistance without a speakerhood trade. Strong cross-family reading with the caveat below — not a proven wall. |
| **STOP — fluency cratered** (release OK, f_local FAILS) | (c). ⚠️ Likely: the embeddings *are* the mapping that render and speak depend on. ⛔⛔ **This is Qwen's collapse reproduced on a second family — it supports (B), the nastier reading, and it is NOT a release result.** Records "mapping untouchable on Mistral too". Pre-declared dial-back **LR 5e-6, a NEW prereg**; its storage is reserved before this run fires. |
| **STOP — perceive killed** (release OK or not, perceive FAIL) | Unfreezing the mapping broke the comprehension path. ENTANGLED at the mapping level, second family. ⛔ If release also reads OK here, that is **exactly Qwen's row** and must be written up as **(B)-supporting, not as release installing**. |
| **incoherent / DIVERGED / MAPPING_FROZEN / MAPPING_UNVERIFIED** | → §7. Non-finite voids the table; an unmoved or unverified leaf voids it too (§5). |

### ⛔ 6.1 · `choose` is PRE-DECLARED LIKELY-UNSCOREABLE AND DOES NOT GATE

`mis16d` returned **0.0 %, 256/256 unanswered** on `choose`, and the harness
correctly refused to read it as comprehension — *"an EMISSION failure, not a
comprehension reading; the band does not apply and the number is not a result."*
⚠️ It was **unchanged by the chat-template repair**, so it has a separate,
**undiagnosed** cause and is OPEN.

⭐ **The F-LOCAL gate reads `render` and `speak` only** — structurally:
`f_local(*, render_rate, speak_rate, ...)` takes `worst = min(render_rate,
speak_rate)` in `tlon/act2/falsify.py`. `choose` is not an input to it.

⛔ **So a repeat of 0/256 on this run is the KNOWN OPEN ISSUE, not a new
failure**, and it is written here in advance so that it cannot be read
post-hoc as a fresh Mistral mapping symptom. It gates nothing.

---

⛔⛔ **NO THRESHOLD CHANGE IS AUTHORISED BY ANY STOP.** `Z_LAG1_MIN` 6.0 and
`Z_LAGN_MAX` 3.0 imported unchanged from `tlon.discourse.transient`. A floor is
a floor.

**What a floor here establishes:** *a second faithful family fails to install
release across BOTH the layer rung and the token mapping.* With Qwen (layers
floored, mapping untouchable) and D6, that is a **strong cross-family resistance
reading — n=2 at two loci.** ⛔ **NOT a proven substrate wall:** §7.1 rung one
(all-28/all-32 via FSDP) is **untested on either base**, and Mistral's ladder
still stops where this run stops. The honest statement is *"not pursued,"* never
*"tested and floored."*

---

## 7 · Fallback

`incoherent` → do not interpret and do not climb. `MAPPING_FROZEN` /
`MAPPING_UNVERIFIED` → an instrument fault (the `embed_tokens`-got-no-gradient
case, or a missing coverage prediction): fix the gradient path or the
measurement and re-run under a new prereg. ⛔ It is **not** evidence about the
mapping.

---

## 8 · Provenance

Cell **`mismap-s20624`** — asserted by `cell_guard` to collide with no fired run
(`fwmap-s20624`, `mis16`/`b`/`c`/`d-s20624`, and every prior cell). The verdict
and `factorial.json` both read the one `verified_prereg_id()` — the LOCK id read
from **this file** and re-hashed, refusing on mismatch.

⛔ This file is **not yet locked**. Lock it before any weights change; a body
edited after the lock fails the re-hash and refuses the run, which is the point.

---

## 9 · Operational

- **Persist-capacity floor before `train_leg1`** — `max(usedStorage,
  **deduplicated** live-file-sum)` against the measured ceiling bracket, low
  end (`PROVEN_ACCEPTED_BYTES` = 94,214,989,055 B), refusing on insufficient.
  ⛔⛔ **The dedup is load-bearing and was paid for**: the un-deduplicated sum
  double-counted a shared LFS blob and read **90.43 GB** against `usedStorage`'s
  **68.88 GB**, which would have refused a run that fits. LFS is
  content-addressed; summing filenames counts one blob twice.
- **Headroom, measured 2026-09-13 after the archive/delete/squash:** live
  **47.44 GB** + this run's mapping artifacts **~15.18 GB** + the §6 (c)
  dial-back **~15 GB** ≈ **78 GB**, under the 94.21 GB low bracket. ⭐ **Space
  for the dial-back is confirmed free before this fires**, because collapse is a
  likely outcome here. ⛔ These are context; the floor re-measures at run time
  and it, not this paragraph, decides.
- **Watchdog armed FIRST** — hard rule, self-terminating, before any training.
- `eager` pinned both legs with the resolved kernel printed; early steps
  confirmed clean before any verdict is trusted.
- Corpus sha-verified against `dd40e22f85b0b6e4`; mismatch aborts.
- `weight_delta` `DIVERGED` branch live. Readings persisted under
  **epoch-distinct** names (`weight_delta_EPOCH1.json`) so no later epoch can
  overwrite a reading. Persist-before-`~/DONE` with manifest. Throughput pulled
  before terminate. Every number `_w`-labelled.
- ⛔ **`pipeline_fullft_read.sh` is Qwen-hardcoded** (`MODEL=Qwen/Qwen2.5-7B-Instruct`)
  with unguarded mapping steps. It is **not** on this run's path, but it must be
  de-Qwened before any re-read of this cell.

---

## 10 · What this run does NOT do

- ⛔ Does not discharge §7.1 rung one (all-28/all-32 via FSDP), untested on either base.
- ⛔ Does not change any threshold.
- ⛔ Does not read a floor as a proven substrate wall — n=2 at two loci is strong, not terminal.
- ⛔ Does not read a floor at all unless **both** mapping leaves moved and a coverage prediction exists (§5).
- ⛔ **Does not count a collapsed-speaker "release pass" as a GO** (§0.1, §6).
- ⛔ Does not treat any cross-base or cross-population rms as a gate.
- ⛔ Does not carry a coverage figure from another base — the step recomputes it per base and per corpus (§5).
- ⛔ Does not gate on `choose`, and does not read a repeat of 0/256 as a new failure (§6.1).
- ⛔ Does not change card or region from `mis16d` without recording the reason (§2).
- ⛔ Does not measure two-speaker drift.

---

## 11 · Watch, do not gate

- **Where lag-2 lands against Mistral's own layer rung (+3.972).** Does the
  mapping move it toward or away from the 3.0 ceiling? Record it; no branch
  reads it. ⚠️ One run against one run — a difference, not a trend.
- **lag-3.** It rose across the Qwen rungs (−0.874 → 0.674 → 2.266) under the
  3.0 ceiling, confounded with everything else that differed. If it crosses 3.0
  here that is a second release lag failing — **record it**. Not a gate.
- **`choose` raws.** If it returns 0/256 again, the ledger raws from *two* bases
  at *two* loci are then available to diagnose it from. Diagnosis is its own
  task, not this run's.
