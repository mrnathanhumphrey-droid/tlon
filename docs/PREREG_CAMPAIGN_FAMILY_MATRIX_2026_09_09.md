# PREREG — CAMPAIGN family matrix: is the mapping untouchable across families?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `91956dbe` (sha256[:8] of draft body at lock, 2026-09-10T01:24Z)
- **Date:** 2026-09-09
- **Fires on:** four full-weight fine-tunes — **two bases × two rungs** —
  `allenai/Olmo-3-7B-Instruct` and
  `mistralai/Ministral-3-8B-Instruct-2512-BF16`, each at the **layer rung**
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
| **3a** | Ministral-3-8B-BF16 | layer, top-half | speakerhood gate |
| **3b** | Ministral-3-8B-BF16 | mapping | THE QUESTION |

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
| **Ministral-3-8B-BF16** | 8.918 B | 34 | **17** | **3,707,904,000** | **1,073,741,824** |

⭐ OLMo's layer rung lands within **0.8 %** of Qwen's incumbent by coincidence,
Ministral's is +13.6 %. Recorded as context; the read is verdict-vs-verdict, so
neither is a dose match and neither is required to be.

### 4.1 ⛔⛔ The layer STACK must be named for Ministral

`Ministral-3-8B` is **multimodal** and carries two transformer-layer stacks:

```
language_model.model.layers.0..33       the text model
vision_tower.transformer.layers.0..23   an image encoder
```

The pooled index set is `0..33` — **contiguous**, so every pre-existing scope
guard passed and `unfreeze_top=14` put **36 vision-tower tensors** in the
trainable set. Fixed in `de1d846`/`563b5a6`: the scope refuses a multi-stack
base unless the stack is named, and naming it restricts the SELECTION, not only
the layer count.

- **Olmo-3-7B** — one stack (`model`), Qwen/Llama naming byte-for-byte. **No
  stack argument.** Verified: 0 vision tensors, trainable set is exactly the
  text layers.
- **Ministral-3-8B** — `stack="language_model.model"`, RECORDED IN THE RUN.
  Verified: 126 tensors at top-14, **0 vision**, and the mapping leaves resolve
  to `language_model.model.embed_tokens.weight` +
  `language_model.lm_head.weight` (different depths — the leaves are
  deliberately not filtered by the stack prefix, and the per-leaf positive
  assertion is what makes that safe).

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
