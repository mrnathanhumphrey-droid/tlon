# PREREG — rung 2: does release live in the token mapping, where the layer-capacity rungs could not reach it?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `c2a4f0ca` (sha256[:8] of draft body at lock, 2026-09-08T21:44Z)
- **Date:** 2026-09-08
- **Fires on:** one full-weight fine-tune, **`embed_tokens` + `lm_head` trainable
  and ALL 28 transformer layers frozen** (`--scope-mode mapping`,
  **1,089,994,752** trainable — verified against the model's real 339 tensors,
  not a spec figure), content-transient corpus (`dd40e22f85b0b6e4`), then the
  three-axis read.
- **Predecessors:** `a0450b36` (rung 1a, 14L), `9ccf98d6` (rung 1b, 19L
  under-dosed), `bd435b37` (rung 1b′, 19L dose-matched).

---

## 0 · Why this rung, and what the capacity result established

| run | scope | LR | rms | **lag2** |
|---|---|---|---|---|
| rung 1a | 14L | 1e-5 | 3.1182e-04 | **5.785** |
| rung 1b′ | 19L | 1e-5 | 3.0032e-04 | **5.966** |

**Layer capacity in the 14→19 range does not install release, and trends the
wrong way** — robust to the dose confound, because 1b′ landed at 96.3 % dose and
still came in higher, while rung 1a's own within-run trend was more-dose →
higher-lag-2. So the favourable dose gap should have flattered 1b′ and did not.

⛔ **That does not discharge §7.1 rung one (all 28 via FSDP).** It is *untested*,
not floored. It is not bought because more of a lever that trends wrong is
negative-EV — a different statement, and §6 keeps it separate.

⭐ **This rung tests a DIFFERENT LOCUS.** `embed_tokens` and `lm_head` have been
frozen in every run of this arm, on the reasoning that release lives in the
layers. The capacity result makes that reasoning *testable*: if more layers
cannot install release, perhaps release is not a layer property at all, and the
token↔vector mapping — frozen throughout — is where it lives.

**Both outcomes are informative.** GO: release lives in the mapping, a real
finding, and the brick installs. Floor: the last cheap single-card lever is
exhausted and the substrate reading hardens (§6, with its caveat).

---

## 1 · SCOPE — Option A, and why not B

**Option A, chosen: `embed_tokens` + `lm_head` ONLY; all 28 layers frozen.**
The clean single-variable test of the mapping's role, at **1.090 B** trainable —
far under rung 1a's 3.263 B, so VRAM is not a constraint.

⛔ **Option B (mapping + top-half layers) is rejected.** The layer-capacity
question is answered flat-to-wrong; adding layers back re-confounds a settled
variable, costs more, and would make a floor ambiguous between the two loci.

---

## 2 · Configuration

| field | value | why |
|---|---|---|
| **trainable** | `embed_tokens` + `lm_head`, **1,089,994,752** | Verified against the real safetensors header. `tie_word_embeddings: false`, so the two are separate 545,003,776-param matrices. |
| **frozen** | all 28 transformer layers + `model.norm` | The inversion of §5's freeze. |
| **LR** | **1e-5** | As rung 1a/1b′. See §3 — the dose comparison is weaker here and is not the gate. |
| **card** | `gpu_1x_h100_sxm5` 80 GiB | 1.090 B trainable is far under the fitted scopes; VRAM sized and asserted at run time regardless. |
| **attention** | `eager` from step 0 (D-8), both legs | The fused SDPA backward makes non-finite gradients on this config. |
| **optimizer** | `adamw_bnb_8bit`, fp32 master | fp32 master is load-bearing (§4.1). |
| **seq / batch / accum** | 384 / 4 / 4 | Unchanged. |
| **corpus** | content-transient, `dd40e22f85b0b6e4` | Byte-identical. Mismatch aborts. |
| **epochs** | ≤ 2, halted by §4 | The stopping rule decides. |

---

## 3 · ⛔⛔ THE DOSE COMPARISON IS WEAKER HERE, AND IS **NOT** THE GATE

Rung 1a's baseline rms (`3.1182e-04`) was measured over **transformer-layer**
parameters. This run trains **embedding rows** — a *structurally different
parameter population*, with different initialisation scales and different
gradient magnitudes.

⛔ **So rms-matching does not transfer.** Rung 1b′ was layers-vs-layers
(comparable populations) and the dose match was load-bearing. This is
mapping-vs-layers, and a "dose-matched to 3.118e-4" claim here would be the
`resolution_match` error: two real quantities sharing one name, differing in
what they are denominated over.

⭐ **THE PRIMARY READ IS THEREFORE THE ABSOLUTE VERDICT** — does release install
at all (lag-2 ≤ 3.0) — **not** a dose-matched comparison against rung 1a. That
is a cleaner question than the capacity comparison and does not need the
cross-population match.

`rms` and `delta_norm` are still recorded per epoch, for the trajectory and the
over-fit check the stopping rule needs. ⛔ **Their comparison to rung 1a is
DESCRIPTIVE CONTEXT, not a gate.** No branch below reads them.

---

## 4 · The stopping rule — carried unchanged, it has worked twice

Halt at end of epoch 1 and take it as the verdict if epoch 1 is **GO across all
three** *or* **floored-but-fluent** (release FAIL, perceive PASS, f_local PASS).
Epoch 2 runs only if epoch 1 is itself unreadable.

---

## 5 · ⛔⛔ THE PRE-DECLARED RISK: `embed_tokens` MAY RECEIVE NO GRADIENT

**This rung inverts the gradient geometry of every previous run, and the
inversion has a specific, plausible failure that would FAKE THE FINDING.**

The layer rungs carried the opposite hazard, recorded in `act2_finetune.py`:
frozen embeddings + reentrant gradient checkpointing means the input to the
first checkpointed block does not require grad, the backward skips the segment,
and *every trainable layer gets no gradient while training appears to succeed.*

Here `embed_tokens` is **trainable**, so that door is shut — but a new one
opens. `lm_head` sits **one step from the loss**; `embed_tokens` is reached only
after the gradient traverses **all 28 frozen layers**. So the plausible failure
is **asymmetric**:

> `lm_head` trains normally, `embed_tokens` receives nothing.

⛔⛔ **And that state PASSES the global §4.1 precondition**, because the global
delta is non-zero — carried entirely by the half that worked — while the *input*
half of the mapping never trained. A floor read off that run would say *"the
mapping did not install release"* when the truth is *"half the mapping never
trained."* **The false floor and the finding are the same observation.**

⭐ **THE GATE: `mapping_moved()` — PER DECLARED LEAF.** A floor verdict is
**not readable** unless **BOTH** `embed_tokens` **and** `lm_head` show non-zero
`changed` *and* non-zero `delta_norm_estimated` in `per_module`. Either leaf
still → `MAPPING_FROZEN` → the run is an **instrument fault, not a floor**, and
no row of §6's table may be read. A missing `per_module` record refuses rather
than certifying: an unmeasured mapping is not a moved one.

⛔ This gate runs **before** the verdict is interpreted, alongside §4.1, and is
red-proofed in both directions (`tests/test_mapping_scope.py`).

**The scope itself is positively selected and asserted**, because a selector
matching nothing trains a frozen model and reads as a substrate floor: both
leaves must match by name (a **tied** checkpoint is *refused*, not silently
halved to 545 M), no layer tensor may leak into the trainable set (that is
Option B by accident), and the layer freeze is asserted on the model, not
merely on the name list.

---

## 6 · The verdict table

    RELEASE:  lag-2 z <= 3.0 AND every longer lag <= 3.0
    PERCEIVE: lag-1 z >= 6.0
    F-LOCAL:  render AND speak clear

| outcome | reading |
|---|---|
| **GO** | ⭐ **Release lives in the token mapping.** Unfreezing the mapping installed what more layers could not. A real finding: the locus is the mapping, not the layers. Drift measurement un-blocked. |
| **STOP — floored** (release FAIL, perceive PASS, f_local PASS) | The mapping alone did not install release. With the capacity floors, **the single-card fine-tune levers — layers AND mapping — are exhausted.** See the caveat below. |
| **STOP — fluency cratered** (release OK, f_local FAILS) | (c). ⚠️ **More likely here than in any layer run**: the embeddings *are* the token mapping that render and speak depend on, so training them directly risks F-LOCAL. Pre-declared dial-back: **LR 5e-6, a NEW prereg.** Storage for that run is reserved before this one fires. |
| **STOP — perceive killed** | Unfreezing the mapping broke the comprehension path. ENTANGLED at the mapping level. |
| **incoherent / DIVERGED / MAPPING_FROZEN** | → §7. Non-finite voids the table; a frozen leaf voids it too (§5). |

⛔⛔ **NO THRESHOLD CHANGE IS AUTHORISED BY ANY STOP.** `Z_LAG1_MIN` 6.0 and
`Z_LAGN_MAX` 3.0 imported from `tlon.discourse.transient`. A floor is a floor.

**⛔ What a floor here does and does not establish.** It would mean: *release
does not install via full fine-tuning across the layer-capacity range OR the
token mapping, on a single 80 GiB card.* Combined with D6 that is a **strong**
reading — **not a proven substrate wall**. §7.1 rung one (all 28 via FSDP)
remains **untested**, and the honest statement is *"not pursued because capacity
trended wrong,"* never *"tested and floored."* ⛔ Pre-declared so a floor here
cannot be over-read as terminal.

---

## 7 · §Fallback

`incoherent` → do not interpret and do not climb. `MAPPING_FROZEN` → an
instrument fault: fix the gradient path and re-run under a new prereg; it is
**not** evidence about the mapping.

---

## 8 · Provenance

The verdict and `factorial.json` both read the one `verified_prereg_id()` — the
LOCK id read from this file and **re-hashed**, refusing on mismatch. Rung 1b′
was the first run this protected; this is the second.

⛔ Rung 1a's and 1b's artifacts stamp `a0450b36` including where that is wrong
(rung 1b ran under `9ccf98d6`). **Not retroactively re-stamped** — a stamp
applied today proves nothing about what ran then. They stay as historical
artifacts of the pre-fix defect.

---

## 9 · Operational

Persist-capacity floor before `train_leg1` (measured `usedStorage` against the
measured ceiling bracket, low end, refuses on insufficient). **Space for the §6
(c) dial-back is confirmed free before this run fires**, since that outcome is
the more likely one here. Watchdog armed first. `eager` pinned both legs with
the resolved kernel printed. Corpus sha-verified. `weight_delta` `DIVERGED`
branch live. Readings persisted under **epoch-distinct names**
(`weight_delta_EPOCH1.json`), so no later epoch can overwrite a reading.
Persist-before-`~/DONE` with manifest. Every number `_w`-labelled.

---

## 10 · What this run does NOT do

- ⛔ Does not discharge §7.1 rung one (all-28 via FSDP), which is untested.
- ⛔ Does not change any threshold.
- ⛔ Does not read a floor as a proven substrate wall.
- ⛔ Does not read a floor at all unless **both** mapping leaves moved.
- ⛔ Does not treat the rung-1a rms comparison as a gate.
- ⛔ Does not measure two-speaker drift.

---

## 11 · Watch, do not gate

lag-3 rose across the three fired runs: **−0.874 → 0.674 → 2.266**, under the
3.0 ceiling, confounded with every other thing that differs. If rung 2 pushes
lag-3 over 3.0 that is a second release lag failing — **record it**; it would be
consistent with training in this direction broadening persistence. ⛔ It is not
a gate and no branch reads it.
