# FINDINGS — why the full-weight run produced a NaN model

**Run:** `fwtrace-s20624`, box `0978c1cbe062499d8f32bbae70a86b96`, H100 PCIe /
us-west-3, code `1eb466e`, 300 steps, `total wall: 1081 s`, ~$2.
**Artifacts:** `hf://keyzersoze04/tlon-act2-adapters/fwtrace-s20624/step_trace.jsonl`
(+ `weight_delta.json`, + the pipeline log under `fullft_trace_fwtrace-s20624/`).

⛔ **This is about the instrument, not about Tlön.** D6's architectural-floor
finding is untouched. The full-weight arm has still never produced a readable
result, because the training loop has not yet run clean.

---

## 1 · What the trace shows

The configuration is the one that failed (LOCK `a0450b36`), unchanged. Only
`--max-steps 300` and `--trace-out` differ.

| step | loss | grad non-finite | weight non-finite | moment non-finite | top module ‖grad‖ |
|---|---|---|---|---|---|
| 10 | 0.6242 | 0 / 168 | 0 | 0 | `L27.mlp.down_proj` 0.447 |
| 11 | 0.6274 | 0 / 168 | 0 | 0 | `L27.mlp.down_proj` 0.575 |
| 12 | 0.6651 | 0 / 168 | 0 | 0 | `L27.mlp.down_proj` 0.609 |
| **13** | 0.6404 | **168 / 168** | **70** | **70** | — |

Loss over the first eight steps: **4.4853 · 3.5786 · 2.4876 · 2.1744 · 1.2992 ·
1.1468 · 0.9577 · 0.9084**. Total gradient norm sat at **1.0000** every step,
which is exactly `max_grad_norm`, so the clip was active and the raw gradients
were ordinary.

**The model was training normally, with no precursor of any kind, and then every
gradient in it went non-finite in a single step.**

---

## 2 · The causal chain, in order

1. Forward/backward produces **non-finite gradients on all 168 trainable
   tensors** at step 13. Nothing upstream of it is anomalous.
2. The optimizer receives them and writes NaN into **exactly 70** — every tensor
   below `min_8bit_size` (4096), which in this model is every 1-D tensor: 42
   biases and 28 layernorms. The 98 weight matrices, which use the 8-bit
   blockwise state path, are **not** poisoned by the same non-finite gradient.
3. The model now has NaN layernorms and biases in layers 14–27. Everything
   afterwards — the flat loss, the ~3.25e-3 residual movement in the surviving
   matrices — is wreckage, not signal.
4. `weight_delta.py` read `fraction_changed = 0.9999982` and returned **OK**,
   because `NaN != NaN` is True. (Closed in `bbfff69`: verdict `DIVERGED`.)

---

## 3 · ⛔⛔ THREE HYPOTHESES DIED HERE, AND ONE OF THEM WAS A SYMPTOM I HAD BEEN
## USING AS A LOCALIZER

**Degenerate objective — refuted.** The loss descended 4.49 → 0.62 over twelve
steps. The `loss → 0` that defined the original failure is *downstream of the
NaN*, not its cause. Every diagnosis that started from "why is the loss zero"
started one link too late.

**Optimizer path — refuted.** The gradients were already non-finite when the
optimizer received them.

**⛔⛔ THE 1-D / 2-D FINGERPRINT WAS NOT EVIDENCE ABOUT WHERE THE FAULT STARTED.**
The finished model had NaN in all 70 1-D tensors and none of the 98 matrices,
and four successive hypotheses were built on that split as though it localised
the fault to something that treats 1-D parameters differently. The trace shows
gradients broke on **all 168 at once** — 2-D included. The split describes
**which optimizer state path tolerates a non-finite gradient**, not which
computation produced one.

⭐ The lesson is not "that hypothesis was wrong". It is that **a symptom observed
only at the end of a run cannot say where in the run it originated**, and four
component tests could not detect the error because each was asking a question
the fingerprint had already mis-framed. Only ordering — gradients captured
BEFORE the optimizer step, weights and moments AFTER — separated them, and that
required two hooks in the same step.

---

## 4 · What is still open

**Why the forward/backward produces a non-finite gradient at step 13.**
Localised to the mixed-dtype (frozen bf16 / trainable fp32) + bf16-autocast +
gradient-checkpointing assembly at real scale, after ~12 healthy steps. Not
named.

⚠️ Note against the temptation to blame bf16 overflow: **bf16 has the same
exponent range as fp32**, so plain magnitude overflow is not the obvious
mechanism and should not be assumed. The next instrumented run needs
finiteness *inside* the forward — per-layer activations and per-layer grad
outputs — to find the first tensor in the graph that goes non-finite, rather
than the first parameter.

⚠️ A second, cheaper question worth asking first: the assembly ablation
(`tools/act2_repro_assembly.py`) established that **mixed-dtype cannot run
without autocast at all** (`float != BFloat16` at `lm_head`). The mixed-dtype
layout exists only to fit fp32 master weights in 80 GiB. If the fault is in that
layout, the alternative is fewer trainable layers with a uniform dtype — which
changes what a STOP-floored would mean (§7.1) and is therefore a prereg
decision, not a bug fix.

---

## 5 · What the run also proved works

- **`--flush-cmd` glob fix**: this run's pipeline log reached the hub. The
  previous box's did not.
- **`bitsandbytes` in the pinned venv** (D-6): installed automatically, no hand
  step, so this box carries no undocumented package.
- **The optimizer write probe**: `fp32 256/256 changed · bf16 0/256` on the H100
  itself — §4.1's arithmetic confirmed on the hardware for the third time.
- **Watchdog-first with a 4 h deadline**: the run finished, marked `~/DONE`
  after persisting, and the box terminated itself.

---

## 6 · The clip is a spreader, and its post-clip signature says WHICH kind of bad value started it

Added 2026-09-06, after reading the installed transformers source.

`Trainer._inner_training_loop` calls `self._clip_grad_norm(...)` at
**trainer.py:1759** and fires `on_pre_optimizer_step` at **trainer.py:1762**
(transformers 5.8.1, read off the box's own installed file). Its docstring is
explicit that the value it returns -- the one logged as `grad_norm` -- is the
**pre-clip** norm.
Every gradient this investigation has measured was therefore read **after** the
clip. And `clip_grad_norm_` computes **one global norm across all parameters**,
so it is a spreader by construction: one tensor's bad value makes the total norm
bad, the clip coefficient bad, and multiplies every gradient by it.

⭐⭐ **So "all 168 at once" was never 168 events. It was one event and a global
coefficient** — and the instrument was sitting downstream of the transformation
that erased the distinction. This is the same structural error as
`logging_nan_inf_filter`: both times the probe read a value the framework had
already processed, and both times the processing destroyed exactly the signal
being looked for.

### ⭐⭐ The free discrimination, measured on this laptop (`tests/test_preclip_probe.py`)

The two ways a gradient can be non-finite do **not** produce the same aftermath:

| pre-clip origin | total_norm | clip_coef | post-clip result |
|---|---|---|---|
| one tensor **inf** | `inf` | `1/inf` = **0** | that tensor `inf*0` = NaN; **every other tensor exactly 0, still finite** |
| one tensor **NaN** | `nan` | **nan** | **every tensor NaN** |

Both rows are asserted against the real `torch.nn.utils.clip_grad_norm_`.

⛔⛔ **The failing run reported 168 of 168 non-finite after the clip. That is the
NaN row, not the inf row.** So the originating value was a **NaN**, not a
magnitude that grew too large — which agrees with the standing warning that bf16
carries fp32's exponent range, and points at `inf - inf`, `0 * inf` or `0 / 0`
inside the backward rather than at simple overflow.

This was bought for nothing: the prediction was wrong on the first write of the
test, the assertion failed, and the failure was the finding.

### The instrument

`PreClipGradProbe` (`tlon/act2/step_trace.py`) registers
`register_post_accumulate_grad_hook` on every trainable parameter. The hook
fires as each gradient is finalised **inside the backward**, before any clip
exists. It records, without a single device synchronisation inside the backward:

- per-parameter **finiteness** and **L2 norm** → the pre-clip global norm,
  computed independently of HF's
- per-parameter **absmax**, so the trajectory across 11 → 12 → 13 says whether
  the fault **compounded** (growing step over step) or was **triggered** (flat,
  then a jump) — which selects the fix class
- **arrival order within the backward**, because gradients finalise in reverse
  topological order, so the earliest-arriving offender is nearest the origin

Alongside it, HF's own logged `grad_norm` is captured — it is the value
`clip_grad_norm_` returns, i.e. the **pre-clip** total — and stored *with the
global step it was logged for*, so alignment is checked rather than assumed.
Two instruments, different routes, one quantity.

### ⛔ A third instrument bug, found while fixing the second

`ForwardProbe.snapshot()` returned its record dict unconditionally, while
`arm()` only cleared it *inside* the window. So every step after the window
re-emitted the last armed step's numbers under the current step's number. In the
raw-loss trace, **rows 15–19 are five identical copies of step 14** wearing later
step numbers — they read as a stable post-break plateau and were not
measurements. Fixed to return nothing when not armed, and pinned by a test.

⭐ **The pattern, three for three: an instrument that keeps answering after it
stops looking reports its own memory as data.**

### Field names changed

`grad_*` in a trace row is now `grad_POSTCLIP_*`; the pre-clip scan is
`grad_PRECLIP_*`; `grad_norm_total` is now `grad_norm_total_POSTCLIP` beside
`grad_norm_total_PRECLIP_ours`. The un-suffixed name is asserted absent — the
last reading was built on a quantity whose name did not say which side of the
clip it came from.

---

## 7 · NAMED: the NaN enters at grad-w.r.t.-Q in layer 27's attention

Run `fwpreclip-s20624`, box `de358aee14e340ddb2a5125583b0dcf0`
(`gpu_1x_h100_sxm5`, D-7), pinned at `51b32a3`, 20 steps, 460 s wall, ~$0.55.
Corpus sha-verified identical (`dd40e22f85b0b6e4`). Self-terminated after
persisting.

### ⛔⛔ First: the hypothesis this run was built on is REFUTED by its own instrument

"One tensor's gradient overflows and the global clip spreads it to all 168" is
**wrong**. At step 13:

| | count |
|---|---|
| non-finite **pre-clip** (inside the backward) | **159** of 168 |
| non-finite **post-clip** | 168 of 168 |

The clip added **9**, not 167. It is a spreader, but it was never doing the
work the hypothesis gave it. ⭐ The instrument built to confirm a story
disconfirmed it in its first row — which is the only reason it was worth
building.

### ⭐⭐ And what it found instead is far better localised

The probe records **arrival order inside the backward**. At step 13, of 168
tensors finalising in micro-batch 0:

```
  0  L27.mlp.down_proj.weight              0.038948
  1  L27.mlp.up_proj.weight                0.072735
  2  L27.mlp.gate_proj.weight              0.026688
  3  L27.post_attention_layernorm.weight   0.002623
  4  L27.self_attn.o_proj.weight           0.001135
  5  L27.self_attn.v_proj.weight           0.036560
  6  L27.self_attn.v_proj.bias             0.000516
  7  L27.self_attn.k_proj.weight           0.092133
  8  L27.self_attn.k_proj.bias             0.000270
  9  L27.self_attn.q_proj.weight           NaN   <== ENTERS HERE
 10  L27.self_attn.q_proj.bias             NaN
 11  L27.input_layernorm.weight            NaN
 12+ every remaining tensor, layers 26..14  NaN
```

**Everything before position 9 is finite. Everything from position 9 on is
NaN. Zero exceptions.** Per layer: layer 27 is 3/12 NaN, every layer 26 down to
14 is 12/12.

⭐ The asymmetry is the mechanism. `grad_k_proj.weight` and `grad_v_proj.weight`
are finite; `grad_q_proj.weight` is NaN. All three are `grad_<X>_activation^T @
hidden` off the **same attention backward**, so `grad_K` and `grad_V` are clean
while `grad_Q` is not. The NaN is not inherited from a shared upstream value —
it is **produced inside the attention backward, on the Q output specifically**.

`attn_implementation` is never passed at `from_pretrained`, so this ran on the
transformers default fused **SDPA** kernel (`_supports_sdpa = True` for Qwen2).

### ⭐⭐ TRIGGERED, not compounding — and this closes a whole fix class

Pre-clip gradient absmax on the tensor the NaN enters at:

| step | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|
| `L27.q_proj.weight` | 0.0109 | 0.0104 | 0.0137 | 0.0134 | 0.0138 | 0.0085 | 0.0074 | **NaN** |
| max over all 168 | 0.181 | 0.081 | 0.182 | 0.065 | 0.086 | 0.151 | 0.043 | — |

**The gradient was declining, and no tensor in the model ever exceeded 0.19.**
There is no runway. A value at 0.0074 does not become infinite on the next step:
this is a NaN generated by a single operation, not a magnitude that grew.

⛔ So the compounding-feedback fix class — per-layer LR, per-tensor clipping
ahead of the global norm, LR reduction — is **closed**. None of it addresses an
operation that produces a NaN from small finite inputs.

### The independent confirmation held

HF's own `grad_norm` (its docstring: *"Returns the pre-clip gradient norm"*)
went `nan` at exactly the break, and matched our independently-summed pre-clip
norm at every step before it — **offset by one step**, which is visible in the
output only because the value was stored with the global step it was logged for
rather than as a bare scalar:

```
  step 12  ours=2.442   HF=2.909  (HF step 12)
  step 13  ours=1.557   HF=2.442  (HF step 13)   <- HF's row 13 is our step 12
  step 14  ours=None    HF=nan    (HF step 14)   <- HF's row 14 is our step 13
```

⭐ Two instruments, different routes, same quantity, agreeing — with the
misalignment surfaced instead of silently absorbed.

### The next test costs nothing

The asymmetric signature (grad_Q NaN, grad_K/grad_V finite, from a fused
attention backward, triggered on one specific step) is the known shape of a
**fully-masked query row**: a softmax row with no unmasked keys has a zero
denominator, and the fused backward's grad_q reduction divides by it while the
grad_k/grad_v reductions weight that row by zero and stay finite.

⛔⛔ **This is a HYPOTHESIS, not a finding.** What is measured is the location
and the asymmetry; the masked-row story is a candidate that fits it.

⭐ And it is testable for **$0, with no GPU and no model weights** — the
attention mask depends only on the tokenizer, the collator and the seed. Run the
free version before renting anything.

### ⚠️ Two instrument caveats found in this run's own output

- **`loss_raw` is the LAST MICRO-BATCH's loss, not the step's mean.** The
  `compute_loss` wrapper overwrites its holder once per micro-batch, so with
  accumulation 4 it keeps the fourth. That is why `loss_raw` (1.2196 at step 0)
  and `loss_LOGGED_FILTERED` (4.4853) disagree in level — they are different
  quantities, and only the finite/NaN distinction is comparable between them.
  The name should carry it.
- **A backtick pair inside the reader's Python comment was expanded by the
  unquoted heredoc**, producing `line 129: loss_raw: command not found` in the
  log. Harmless here, and exactly the banked shell-payload hazard.

---

## 8 · The eager ablation: clean for 60 steps — and a confound that must be closed before it is believed

Run `fwattn-eager-s20624`, box `3fee311a48ce405eaa42b6f635b1d343`, same card as
the baseline (`gpu_1x_h100_sxm5`, us-south-3), pinned at `c0d2847`, 60 steps,
310 s wall, ~$0.55. Corpus sha-verified identical. `attention implementation
RESOLVED TO: 'eager' (requested: 'eager')` — the flag is confirmed applied, not
assumed.

### The result

| | SDPA (`fwpreclip`) | eager (`fwattn-eager`) |
|---|---|---|
| steps run | 20 | **60** |
| first non-finite gradient | **step 13** | **never** |
| total non-finite gradient observations | 159 pre-clip + 168 post-clip at 13 | **0, across all 60 steps** |
| loss_raw, mean of steps 0–9 | — | 0.4904 |
| loss_raw, mean of steps 50–59 | — | **0.0984** |
| pre-clip grad norm at step 59 | — | 2.08 (healthy, not collapsing) |

Eager passes step 13 — where three separate SDPA assemblies broke — and keeps
descending for another 46 steps.

### ⛔⛔ BUT THE FORWARD IS NOT THE SAME, AND THAT IS A CONFOUND OF THE BANKED SHAPE

The two runs' losses **diverge from step 0**:

```
 step |   SDPA    |   EAGER   |   delta
   0  | 1.2196    | 1.2341    | +0.014571
   4  | 0.2600    | 0.2536    | -0.006417
   8  | 0.2161    | 0.1971    | -0.018977
  12  | 0.1806    | 0.1729    | -0.007741
  13  | 0.1109    | 0.1114    | +0.000491
```

So eager did not merely swap the backward on a fixed trajectory — it put the run
on a **different numerical trajectory**, ~1 % off, from the first step. Two
explanations now predict the identical observation:

- **(a) the kernel** — the fused SDPA backward manufactures a NaN the unfused
  path does not, and
- **(b) the trajectory** — a ~1 % perturbation moved the run off whatever
  condition fired at step 13, and the kernel is incidental.

⛔ **This is [[same_prediction]]: when the confound and the hypothesis predict
the same association, the measurement does not discriminate them at any effect
size.** The three prior SDPA runs do not settle it either — checkpointing on vs
off leaves the forward numerics essentially unchanged, so none of them ever
tested perturbation-sensitivity.

⚠️ Two things lean toward (a) without settling it, and are recorded as
arguments, not evidence: the failure signature is **asymmetric** (`grad_Q` NaN
while `grad_K`/`grad_V` from the same op are finite), which is structural rather
than trajectory-like; and there is **no knife-edge visible** in the approach —
gradients were small and declining in both runs, with no quantity climbing
toward a threshold.

### ⏭ THE CONTROL, AND WHY IT IS BOUGHT BEFORE THE BIG RUN

**SDPA again, with a different TRAINER seed and the corpus pinned** — perturbing
the trajectory *without* touching the kernel. It is the same-condition control
arm: the cheapest arm, and the only one that can say the eager reading is void.

- SDPA breaks again under a perturbed trajectory → perturbation does not save
  it → eager's cleanliness is attributable to the kernel.
- SDPA runs clean → the break is trajectory-specific and **the eager result
  proves nothing about the kernel**.

⭐ **It is insurance on a much larger spend.** The pre-declared next step after
"eager is clean" is the real 2-epoch full-weight run. If the break is
trajectory-specific rather than kernel-specific, that run can fail at step 400
instead of step 13 and burn the whole budget to learn what ~$0.85 answers now.

⛔ The pipeline currently drives the corpus build and the trainer from one
`SEED`, so the trainer seed has to be decoupled first — otherwise the control
changes the corpus too and tests two things at once.
