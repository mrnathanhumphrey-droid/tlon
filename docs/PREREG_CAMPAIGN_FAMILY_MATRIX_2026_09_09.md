# PREREG — CAMPAIGN family matrix: is the mapping untouchable across families?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `5f4a554c` (sha256[:8] of draft body at lock, 2026-09-10T20:31Z)
- **Date:** 2026-09-09
- **Fires on:** four full-weight fine-tunes — **two bases × two rungs** —
  `allenai/Olmo-3-7B-Instruct` and
  `mistralai/Mistral-7B-Instruct-v0.3` (AMENDMENT A), each at the **layer rung**
  (speakerhood gate) and then the **mapping rung** (the question), on the
  content-transient corpus `dd40e22f85b0b6e4`.
- **Predecessors:** `a0450b36` / `9ccf98d6` / `bd435b37` (Qwen layer rungs),
  `c2a4f0ca` (Qwen mapping @1e-5), `e91f7c11` (Qwen mapping @5e-6).

---

## 0 · The question, and why it is now worth four runs

The Qwen arc closed both single-card levers:

| locus | Qwen result |
|---|---|
| layers | **release does not install** — 19L at matched dose gave lag2 **5.966** vs 14L's **5.785**, up not down |
| mapping | **untouchable** — collapsed at 1e-5 (lag1 23→2.232) and worse at 5e-6 (2 chains / 7 turns, unscoreable) |

⛔⛔ **The base model was an unrecorded CONSTANT for that entire arc.** Every
one of those findings is, strictly, a fact about Qwen2.5-7B-Instruct. This
matrix asks whether the mapping's untouchability is **a Qwen fact or an LLM
fact**.

⭐ **The mapping row is the row that matters.** If the mapping collapses on
three unrelated families, "the mapping cannot be trained without destroying the
speaker" starts to be a property of instruction-tuned transformer LMs rather
than of one checkpoint. Two clean datapoints beat three noisy ones, which is why
this is two bases and not four.

---

## 1 · The matrix

| run | base | rung | purpose |
|---|---|---|---|
| **2a** | Olmo-3-7B-Instruct | layer, top-half | speakerhood gate |
| **2b** | Olmo-3-7B-Instruct | mapping | THE QUESTION |
| **3a** | Mistral-7B-Instruct-v0.3 | layer, top-half | speakerhood gate |
| **3b** | Mistral-7B-Instruct-v0.3 | mapping | THE QUESTION |

⛔ **Gemma 4 is deliberately EXCLUDED from this matrix.** It is Apache-2.0 and
ungated (verified at decision time, 2026-09-09), but
`tie_word_embeddings = True` on every variant, which `mapping_scope` refuses by
design — a tied checkpoint would train a silently halved scope. **Gemma cannot
occupy a cell in the mapping row at all.** It is available only as an off-locus
capacity-row datapoint, and that is a different question requiring its own
prereg.

---

## 2 · ⛔⛔ ORDER IS LOAD-BEARING: speakerhood is established at the LAYER rung

**The layer rung fires first for each base, and its F-LOCAL result gates the
mapping rung.**

⛔ The first draft of this gate read *"fails F-LOCAL → not a speaker → out"*,
and **it would have excluded Qwen**, which clears F-LOCAL at 14L/19L@1e-5 and
fails it at mapping@1e-5. **One run cannot separate "this base cannot speak
Tlön" from "this configuration breaks this base."** So speakerhood is tested at
the FORGIVING configuration, never the fragile one.

- Layer rung **F-LOCAL PASS** → the base speaks Tlön → the mapping rung is
  interpretable and fires.
- Layer rung **F-LOCAL FAIL** → ⛔ **the base is not a speaker under any
  configuration tested**, its mapping rung is NOT fired, and its cell in the
  mapping row is recorded as **NOT ESTABLISHED** — never as a collapse.

⭐ That asymmetry is the point: a mapping collapse only means something on a
base that demonstrably spoke first.

---

## 3 · Thresholds — IMPORTED, UNCHANGED, NOT RE-SPELT

`Z_LAG1_MIN = 6.0` and `Z_LAGN_MAX = 3.0`, imported from
`tlon.discourse.transient`. No threshold in this campaign is new, and the
verdict tool asserts identity at the point of use.

⭐ **Cross-base reading is VERDICT-vs-VERDICT and ruler-free.** The lag z comes
from a per-run `permutation_null`, so no ruler transfers between bases.
⛔ **Magnitudes do NOT compare across bases.** Only verdicts do.

⭐ **Scoreability is derived, not picked** (`b16ed80`): a lag is readable only
if `resolving_power` — the z of the maximum attainable profile — reaches the
locked threshold it is judged against. A cell too small to reach its bar is
`UNSCOREABLE`, never a pass and never a fail.

---

## 4 · Scope: the INVARIANT is frozen, the VALUES are computed and recorded

⛔⛔ **THE INVARIANT, which is what this prereg freezes:**

> **Layer rung** — the **top HALF** of the base's text-stack transformer layers
> are trainable; `embed_tokens` and `lm_head` and every other module are frozen.
>
> **Mapping rung** — `embed_tokens` and `lm_head` ONLY; every transformer layer
> frozen.

⛔ **NOT "top 14".** 14 is half of Qwen's 28 and only 41% of Ministral's 34;
freezing the literal would silently vary the fraction of depth across the very
axis this campaign holds constant. The invariant is the fraction; the count is
derived per base.

**VALUES, measured from each base's real tensors on 2026-09-09** (not
predicted — read from the downloaded safetensors headers):

| base | total | text layers | top-half | layer-rung trainable | mapping trainable |
|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct *(incumbent)* | 7.616 B | 28 | 14 | 3.263 B | 1.090 B |
| **Olmo-3-7B-Instruct** | 7.298 B | 32 | **16** | **3,238,264,832** | **821,477,376** |
| **Mistral-7B-Instruct-v0.3** | 7.248 B | 32 | **16** | **3,489,792,000** | **268,435,456** |

⭐ OLMo's layer rung lands within **0.8 %** of Qwen's incumbent by coincidence,
Ministral's is +13.6 %. Recorded as context; the read is verdict-vs-verdict, so
neither is a dose match and neither is required to be.

### 4.1 ⛔⛔ AMENDMENT A: the Mistral base is TEXT-ONLY, and that is the point

**Both bases in this matrix are single-stack causal LMs, so no `stack` argument
is used.** Verified against each base's real tensors on 2026-09-10:

- **Olmo-3-7B-Instruct** — one stack (`model`), Qwen/Llama naming
  byte-for-byte. 0 vision tensors.
- **Mistral-7B-Instruct-v0.3** — one stack (`model`), `MistralForCausalLM`,
  untied. 32 layers, 3,489,792,000 trainable at top-16.

⛔ **THE BASE WAS SWAPPED FROM `Ministral-3-8B-Instruct-2512-BF16`, AND THE
REASON IS THE AXIS, NOT THE EFFORT.** Ministral-3 is
`Mistral3ForConditionalGeneration`: a multimodal model carrying TWO
transformer-layer stacks (`language_model.model.layers.0..33` and
`vision_tower.transformer.layers.0..23`). Two things followed.

1. **It could not be loaded.** `AutoModelForCausalLM` refuses a
   `Mistral3Config`, so run 3a died at the training leg with
   *"Unrecognized configuration class ... for this kind of AutoModel"*.
   Supporting it means a different AutoClass, the trainer's loss path, the
   `LocalBackend` read path and a chat template carrying image tokens — a
   modality port across train AND read.
2. ⭐ **And the port would have WEAKENED the axis it was meant to serve.** This
   matrix exists to vary FAMILY while holding architecture constant. A
   multimodal base varies family AND modality, so a Ministral result differing
   from Qwen's could not distinguish "different training lineage" from
   "different architecture". The effort would have bought a CONFOUNDED arm.

⭐ `Mistral-7B-Instruct-v0.3` holds architecture constant (text-only causal LM,
same tensor naming as Qwen and OLMo) and varies only family — a different lab,
a different pretraining corpus, a different instruction-tuning recipe. It is
therefore the BETTER object for this axis, not a fallback.

⚠️ **Recorded honestly: it is the 2024 v0.3 line, not the 2025 Mistral-3 line.**
The axis is LINEAGE, not recency — "is this a Qwen-recipe artifact or an LLM
property" is answered by any capable different-lineage 7B. Recency would matter
only for a claim about frontier models specifically, which this campaign does
not make.

⚠️ **THE MAPPING LOCUS IS NOT THE SAME SIZE ACROSS THE MATRIX, AND THAT IS
RECORDED BEFORE THE RUN, NOT DISCOVERED AFTER IT.** Vocabulary drives it:

```
Qwen2.5-7B        vocab 152,064  hidden 3584  ->  1,089,994,752
Olmo-3-7B         vocab 100,278  hidden 4096  ->    821,477,376
Mistral-7B-v0.3   vocab  32,768  hidden 4096  ->    268,435,456
```

Mistral's mapping rung is **4.1x smaller than Qwen's**. The read stays valid —
it is verdict-vs-verdict and ruler-free (§3) — but "the mapping" is a materially
different fraction of each model, so a cross-family mapping result is a claim
about the LOCUS, never about a matched parameter budget. ⛔ Do not read a
magnitude difference between these runs as a dose effect.

⛔ `Ministral-3-3B` is also excluded, and for the Gemma reason as well as the
modality one: `tie_word_embeddings = True`, so `mapping_scope` refuses it and it
could not occupy the mapping row either.

⛔ **A GAP THIS EXPOSED, recorded for the preflight suite:** every preflight
passed before run 3a died — because NONE OF THEM LOAD THE MODEL. VRAM plans
from parameter counts, `cell_guard` and `hub_capacity` query the hub, `corpus`
is CPU-only. The first thing that touches the architecture is the training leg,
so an unloadable base is not caught until GPU time is being spent. Cheap here
(~$0.45, 8 min) and loud, but the check belongs at minute zero.

---

## 5 · Configuration

LR **1e-5** at the layer rung — the configuration Qwen's speakerhood was
established at, and the forgiving one. LR **1e-5** at the mapping rung, matching
rung 2 (`c2a4f0ca`), which is the Qwen mapping run that produced a READABLE
collapse rather than an unscoreable one.

⛔ **No 5e-6 mapping arm is pre-declared.** On Qwen the dial-back made the
speaker *more* degenerate, not less (2 chains / 7 turns vs 6 / 30). A gentler LR
is not a rescue and will not be spent as one without a new prereg saying what a
third point would establish.

Everything else is inherited unchanged: content-transient corpus
`dd40e22f85b0b6e4` sha-pinned before training, fp32 master weights with the
optimizer write probe at minute zero, 1 epoch with the mandatory read, persist
BEFORE reads, watchdog armed before any GPU time.

### 5.1 ⛔ Attention implementation is a PER-BASE CHECK, not an inherited setting

`eager` was a **Qwen + SDPA** finding. It is NOT assumed to transfer. Each
base's first run doubles as its own attention check: the optimizer/delta probe
runs before training, and a NaN or zero delta at step 0 is an INSTRUMENT FAULT
for that base, not a finding about it.

---

## 6 · Pre-declared risks

1. **A base may fail F-LOCAL at the layer rung.** Then §2 applies: NOT
   ESTABLISHED, mapping rung not fired, no collapse claimed. This is a real
   possible outcome and it costs one run to discover.
2. **Ministral's frozen vision tower is dead weight**, adding VRAM and
   parameters that never receive gradient. It is a recorded architectural
   difference between the two bases, not a controlled variable.
3. **A mapping run may be UNSCOREABLE** rather than collapsed, as Qwen's was at
   5e-6. §3's derived scoreability bar makes that an honest recorded state; it
   is NOT evidence of untouchability on its own, because nothing was measured.
4. **Tokenizer and vocab differ across bases** (152064 / 100278 / 131072), so
   `vocab_coverage` is measured PER BASE and the `mapping_moved` prediction is
   rebuilt from it. A constant here would be a lie about a different language.
5. **The chains are not persisted**, so a fired run's cells cannot be
   re-analysed exactly. Known, carried forward, not fixed by this prereg.

---

## 7 · What each outcome establishes

| mapping row | reading |
|---|---|
| **both bases collapse** | ⭐ "The mapping cannot be trained without destroying the speaker" holds on **three unrelated families**. That is an LLM-level claim about instruction-tuned transformer LMs, not a Qwen fact. |
| **one collapses, one does not** | ⛔ **Untouchability is NOT general.** The base that survived becomes the interesting object, and the question moves to what distinguishes it. Strictly stronger information than the unanimous case. |
| **neither collapses** | ⛔ Qwen is the outlier and the whole mapping finding is a Qwen fact. The arc's conclusion is re-scoped, not discarded. |
| **a base is NOT ESTABLISHED** | Its cell is empty. ⛔ NOT evidence either way, and it must not be pooled with a collapse. |

---

## 8 · ⛔ What this campaign does NOT establish

- It does **not** revisit the layer/capacity result on any base. The layer rung
  here is a speakerhood GATE, and reading a capacity floor off it would be
  reading an axis the run was not designed to measure.
- It does **not** test scale. Both bases are 7–9 B; the scale axis is a separate
  question with its own prereg.
- It does **not** include Gemma 4, which cannot run the mapping rung.
- It does **not** touch D6's architectural floor.
- ⛔ It does **not** change a single threshold.
