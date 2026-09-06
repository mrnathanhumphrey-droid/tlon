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
