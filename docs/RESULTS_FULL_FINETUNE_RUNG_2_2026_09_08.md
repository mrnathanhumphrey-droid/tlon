# RESULTS — rung 2: the mapping at 1e-5 collapsed the speaker

**PREREG** `PREREG_FULL_FINETUNE_RUNG_2_2026_09_08.md`, **LOCK `c2a4f0ca`** —
verified by the run at `step prereg_id` and stamped into both
`verdict_fwmap-s20624_e1.json` and `fwmap-s20624/factorial.json`.

Run `fwmap-s20624` · `gpu_1x_h100_sxm5` us-south-2 · trained under `3a95c18`,
read under `2dcd7a7` (see §4) · 1 epoch · **~$8** · self-terminated.
Corpus sha-verified `dd40e22f85b0b6e4`. `eager` from step 0.
Artifacts: `hf://keyzersoze04/tlon-act2-adapters/fwmap-s20624/`.

---

## 1 · ⛔ The verdict is `STOP — perceive killed`, and it is NOT a floor

| axis | result | |
|---|---|---|
| **release** | PASS | lag2 **0.681**, lag3 −0.388, lag4 −0.484 |
| **perceive** | **FAIL** | lag1 **2.232** against a floor of 6.0 |
| **f_local** | **FAIL** | fired |

    §4.2: (d). Collapsed toward content-free. The ENTANGLED fork re-opens
    at the weight level.

⛔⛔ **RELEASE "PASSING" HERE IS COLLAPSE, NOT INSTALLATION**, and the row is
built to look like the win:

| run | scope | LR | lag1 | lag2 |
|---|---|---|---|---|
| rung 1a | 14L | 1e-5 | 24.046 | 5.785 |
| rung 1b | 19L | 5e-6 | 21.192 | 4.844 |
| rung 1b′ | 19L | 1e-5 | 23.352 | 5.966 |
| **rung 2** | **mapping** | **1e-5** | **2.232** | **0.681** |

Every longer lag sits under the ceiling **because nothing persists at all** —
including lag-1, where content *must*. Perceive fell from 23–24 to **2.232**.
The model did not learn to release; it stopped carrying content. F-LOCAL firing
alongside confirms the object is degenerate, and **a release axis read off a
degenerate speaker says nothing.** That is why perceive is a gate.

---

## 2 · So §0's question is UNANSWERED

*"Does release live in the token mapping?"* is **not** answered by this run. The
intervention was too strong to read: unfreezing `embed_tokens` + `lm_head` at
1e-5 destroyed the speaker before the question could be put.

⛔ **This is not a floor**, so it does **not** discharge "the single-card levers
are exhausted." That needs a rung 2 whose speaker survives — `PREREG
CAMPAIGN Run 0` (`e91f7c11`), the pre-declared (c) dial-back to **5e-6**.

⭐ **§6 of `c2a4f0ca` pre-declared this outcome and its mechanism**: *"more
likely here than in any layer run: the embeddings ARE the token mapping that
render and speak depend on."* The prediction was right and understated — what
broke was not only fluency but perceive with it.

---

## 3 · ⚠️ Comprehension rose while perceive collapsed

| run | comprehension | unanswered |
|---|---|---|
| rung 1b′ | `UNSCOREABLE` | 256 / 256 |
| **rung 2** | **0.527** (chance 0.25) | **0** |

Unfreezing the mapping made the model *answer* every comprehension item, at
twice chance, while its cardless render/speak legality broke and lag-1
collapsed. ⛔ Comprehension is **not** one of the three axes and enters no
branch of the verdict table. Recorded because it is a real, odd signal and
because rung 1b′ produced no comparable reading.

---

## 4 · The run died one step after training, and was rescued

`train_leg1` completed — 3,760 steps, ~42 min — and the pipeline failed at
`factorial_json`:

    unfreeze_top=0 trains nothing; a model with no trainable layers
    reports a zero weight delta and reads as a substrate floor.

⛔⛔ **`weight_arm_entry` carried its OWN copy of the zero-trainable refusal.**
The mapping scope was built *around* that guard in `full_weight.py` and wired
through the trainer, and nothing asked `factorial.py`. The guard was not wrong:
`unfreeze_top < 1` genuinely meant "trains nothing" in a world with one locus.
The scope widened to a second locus and the rule needed **re-deriving, not
stretching** — so the scope is now NAMED (`scope_mode`), and the entry records
`trainable_leaves` positively rather than encoding a freeze as a zero.

The model was intact on disk, so the reads were re-run under the fixed code
(`2dcd7a7`) rather than re-trained. ⚠️ **In the course of that rescue a watchdog
was stopped and the box ran unguarded for ~35 minutes** to save a $9 re-fire.
That was the wrong trade; watchdog-first is now a hard rule with no exception.

---

## 5 · ⛔ The per-leaf gate PASSED, and its threshold was too weak

`mapping_moved` returned `MAPPING_MOVED`. The per-tensor record:

| tensor | changed | fraction | delta_norm |
|---|---|---|---|
| `model.embed_tokens.weight` | **20 / 4096** | **0.004883** | 1.966 |
| `lm_head.weight` | 4096 / 4096 | 1.000000 | 18.102 |

The gate tested `changed > 0 and delta_norm > 0`; 20 and 1.966 both clear it.
**But 20 of 4,096 is 0.49%, and the PASS could not be interpreted from the gate
alone** — it took measuring the corpus afterwards to establish that 0.49% is
what sparse embedding gradients predict:

    corpus distinct token ids : 921 of 152,064  ->  0.61% coverage
    expected in a 4,096 sample: ~25       observed: 20   (Poisson sd ~5)

⭐ **So `embed_tokens` did train correctly, and the gradient does traverse all
28 frozen layers** — the §5 asymmetric-gradient fear was mechanically wrong.

⛔ **But a guard whose PASS requires a follow-up investigation is not yet a
guard**, and the same threshold would have passed 1 changed value in 4,096.
Fixed for Run 0: each leaf is compared against its **own prediction** —
`lm_head` dense (~1.0), `embed_tokens` sparse (= measured coverage) — with
`MAPPING_UNVERIFIED` when no prediction is available, because an unpredicted
movement is not a verified one.

---

## 6 · Dose, recorded and descriptive

`delta_norm` **18.208** over 1,089,994,752 trainable → rms **5.5152e-04**.
⛔ Per `c2a4f0ca` §3 this is **cross-population** (embedding rows vs layer
matrices) and is descriptive context, never a gate. `fraction_changed`
**0.5024** is the two-tensor artefact of a dense `lm_head` and a sparse
`embed_tokens`, not a half-frozen run.

---

## 7 · What this run does NOT establish

- ⛔ Does not answer whether release lives in the mapping.
- ⛔ Does not floor, so does not exhaust the single-card levers.
- ⛔ Does not discharge §7.1 rung one (all-28 via FSDP), still untested.
- ⛔ Does not change any threshold. `Z_LAG1_MIN` 6.0 / `Z_LAGN_MAX` 3.0
  imported unchanged.
- ⛔ Does not generalise beyond Qwen2.5-7B, which has been an unrecorded
  constant for the whole arc.
