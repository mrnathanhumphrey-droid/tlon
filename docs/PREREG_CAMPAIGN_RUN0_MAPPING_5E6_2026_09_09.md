# PREREG — CAMPAIGN Run 0: a READABLE mapping verdict on Qwen, at 5e-6

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `e91f7c11` (sha256[:8] of draft body at lock, 2026-09-09T01:36Z)
- **Date:** 2026-09-09
- **Fires on:** one full-weight fine-tune of `Qwen2.5-7B-Instruct`,
  `--scope-mode mapping` (**1,089,994,752** trainable — `embed_tokens` +
  `lm_head`, all 28 layers frozen), **LR 5e-6**, content-transient corpus
  `dd40e22f85b0b6e4`, then the three-axis read.
- **Predecessor:** `c2a4f0ca` (rung 2, the same scope at **1e-5**), which
  returned `STOP — perceive killed`.

---

## 0 · Why this run exists, and what it is NOT

⛔ **Rung 2 did not floor. It collapsed.** At 1e-5 the mapping run destroyed the
speaker:

| run | scope | LR | lag1 | lag2 | f_local | verdict |
|---|---|---|---|---|---|---|
| rung 1a | 14L | 1e-5 | 24.046 | 5.785 | PASS | floored |
| rung 1b′ | 19L | 1e-5 | 23.352 | 5.966 | PASS | floored |
| **rung 2** | **mapping** | **1e-5** | **2.232** | 0.681 | **FAIL** | **perceive killed** |

Every lag fell under the ceiling **because nothing persisted at all**, including
lag-1, where content *must* persist. Perceive went 23–24 → **2.232**. F-LOCAL
fired. A release axis read off a degenerate speaker says nothing.

⭐ **So §0's question is UNANSWERED, not answered negatively.** *"Does release
live in the token mapping?"* needs a run whose speaker survives. This run buys
**readability**, not hope: 5e-6 is the pre-declared (c) dial-back from
`c2a4f0ca` §6, taken because the intervention was too strong, not because a
gentler one is expected to succeed.

⛔ **It is the ANCHOR of the generalisation campaign.** A 14B mapping run has
nothing to compare against without a *readable* 7B mapping verdict, so this
fires first and the scale run locks against its result.

---

## 1 · Configuration — identical to `c2a4f0ca` except the LR

| field | value | why |
|---|---|---|
| **scope** | `mapping`: `embed_tokens` + `lm_head`, **1,089,994,752** | Verified against the model's real 339 tensors. `tie_word_embeddings: false`. |
| **frozen** | all 28 transformer layers + `model.norm` | Unchanged. |
| **LR** | **5e-6** | `c2a4f0ca` §6's pre-declared (c) dial-back, now primary. |
| **cell** | `fwmap6-s20624` | ⛔ Distinct from `fwmap-s20624`; rung 2's artifacts are the comparison. |
| **attention** | `eager` from step 0 (D-8) | Unchanged. |
| **optimizer** | `adamw_bnb_8bit`, fp32 master | §4.1. |
| **seq / batch / accum** | 384 / 4 / 4 | Unchanged. |
| **corpus** | content-transient `dd40e22f85b0b6e4` | Byte-identical. Mismatch aborts. |
| **epochs** | ≤ 2, halted by §4 | The stopping rule decides. |

---

## 2 · ⛔⛔ THE PER-LEAF GATE, NOW COMPARED AGAINST A PREDICTION

`c2a4f0ca` §5 required both mapping leaves to move, and the implementation
tested `changed > 0 and delta_norm > 0`. **That threshold was too weak, and the
run proved it.** Rung 2's `embed_tokens` moved **20 of 4,096 sampled values
(0.49 %)** and the gate returned `MAPPING_MOVED` — a PASS that could not be
interpreted until the corpus was measured *afterwards* to show 0.49 % is exactly
what sparse embedding gradients predict.

⛔ **A guard whose PASS requires a follow-up investigation is not a guard**, and
the same threshold would have passed 1 changed value in 4,096.

⭐ **The gate now compares each leaf against its OWN prediction:**

    lm_head       dense  — logits over the whole vocabulary every step  → expect ~1.0
    embed_tokens  sparse — gradient only on rows for tokens that appear → expect COVERAGE

`COVERAGE` is **measured per run** by `act2_vocab_coverage.py`, before the gate,
from this corpus under this tokenizer — never a constant, because a different
base's tokenizer gives a different number. A leaf must reach **half** its
prediction (Poisson slack: at ~0.6 % coverage the expected count in 4,096
samples is ~25, sd ≈ 5).

⛔ **Three outcomes, and only one permits a floor reading:**

| gate | meaning |
|---|---|
| `MAPPING_MOVED` | both leaves moved as predicted — the verdict below is readable |
| `MAPPING_FROZEN` | a leaf under-moved — **instrument fault, not a floor** |
| `MAPPING_UNVERIFIED` | no coverage measured — **an unpredicted movement is not a verified one** |

⚠️ **Rung 2's own numbers still pass** this gate (0.49 % against a predicted
0.61 %), so the fix does not retroactively invalidate it — it makes the same
PASS *self-interpreting*.

---

## 3 · The dose comparison is DESCRIPTIVE, not a gate

Carried from `c2a4f0ca` §3: rung 1a's rms was measured over transformer-layer
parameters; this trains embedding rows. **Cross-population, so rms-matching does
not transfer.** `rms` and `delta_norm` are recorded per epoch for the trajectory
and the over-fit check; ⛔ no branch below reads them.

**The primary read is the ABSOLUTE verdict.**

---

## 4 · The stopping rule — carried, worked three times

Halt at end of epoch 1 and take it as the verdict if epoch 1 is **GO across all
three** *or* **floored-but-fluent**. Epoch 2 runs only if epoch 1 is unreadable.

---

## 5 · The verdict table

    RELEASE:  lag-2 z <= 3.0 AND every longer lag <= 3.0
    PERCEIVE: lag-1 z >= 6.0
    F-LOCAL:  render AND speak clear

| outcome | reading |
|---|---|
| **GO** | ⭐ **Release lives in the token mapping.** Unfreezing the mapping installed what more layers could not. The locus is the mapping; the brick installs. |
| **STOP — floored** (release FAIL, perceive PASS, f_local PASS) | ⭐ **THE READABLE MAPPING FLOOR — what this run is for.** The mapping was tested, the speaker survived, release did not install. Completes the Qwen single-card ladder with no unread cells, and becomes the 7B anchor the campaign's scale run compares against. |
| **STOP — perceive killed / fluency cratered** | ⛔ **5e-6 is STILL too much for the mapping.** Then the finding is *"the mapping cannot be touched without collapse at either tested LR"* — itself a completing result for the Qwen ladder, and it means the mapping locus is unreachable by this method rather than tested-and-floored. ⛔ Do **not** dial back a third time without a new prereg saying what a third point would establish. |
| **incoherent / DIVERGED / MAPPING_FROZEN / MAPPING_UNVERIFIED** | → §7. Not a floor. |

⛔⛔ **NO THRESHOLD CHANGE IS AUTHORISED BY ANY STOP.** `Z_LAG1_MIN` 6.0 and
`Z_LAGN_MAX` 3.0 imported from `tlon.discourse.transient`.

---

## 6 · What a floor here does and does not establish

- ⭐ It completes the **Qwen single-card ladder**: layers (14/19, dose-matched,
  flat-to-wrong) and mapping (tested, floored) both spent.
- ⛔ It does **not** discharge §7.1 rung one (all 28 via FSDP), which is
  **untested** — not pursued because capacity trended wrong, never
  tested-and-floored. That distinction is pre-declared so a floor here cannot be
  written up as a proven substrate wall.
- ⛔ It does **not** generalise beyond Qwen. Base model has been an unrecorded
  constant for the entire arc; the campaign's Runs 2 and 3 are what vary it.

---

## 7 · §Fallback

`incoherent` → do not interpret, do not climb. `MAPPING_FROZEN` /
`MAPPING_UNVERIFIED` → instrument fault: fix the gradient path or the
measurement and re-run under a new prereg. **Neither is evidence about the
mapping.**

---

## 8 · Operational

Watchdog armed **first, no exception** — a hard rule as of 2026-09-08, when a
box was left unguarded for 35 minutes to save $9. Persist-capacity floor before
`train_leg1`. `verified_prereg_id` re-hashed, and both the verdict and
`factorial.json` carry that one id. Corpus sha-verified. `eager` pinned both
legs with the resolved kernel printed. Scope verified against the base's real
tensors. `weight_delta` `DIVERGED` branch live. Readings persisted under
epoch-distinct names. Persist-before-`~/DONE`. Every number `_w`-labelled.

---

## 9 · What this run does NOT do

- ⛔ Does not vary the base model — that is Runs 2 and 3.
- ⛔ Does not discharge all-28-via-FSDP.
- ⛔ Does not change a threshold.
- ⛔ Does not read a floor unless both mapping leaves moved **as predicted**.
- ⛔ Does not treat the rung-1a rms comparison as a gate.
- ⛔ Does not dial back a third time on its own authority.
