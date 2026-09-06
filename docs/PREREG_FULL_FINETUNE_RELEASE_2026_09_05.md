# PREREG — does a FULL FINE-TUNE install release (lag-2 suppression) that a LoRA on frozen weights provably cannot?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `a0450b36` (sha256[:8] of draft body at lock, 2026-09-05T23:10Z)
- **Date:** 2026-09-05
- **Fires on:** one full-weight fine-tune of the base model on the
  content-transient corpus (`dd40e22f85b0b6e4`), then the model-lag read +
  F-LOCAL + perceive, all three.
- **Written before that fine-tune exists.** No full-fine-tuned Tlön model has
  been trained.
- **Gates:** the conversational chatbot deliverable AND the two-speaker drift
  measurement — which D6/D5 established are the *same* deliverable (a bot that
  holds its own context = a speaker at lag-2 = the release brick F2/F3). Both
  downstream of this.

---

## 0 · This is the first weight-level measurement in Act 2 — `D_w` is now live

Every prior arm was inference-only, so every number was `_ctx` by construction
and the subscript partitioned nothing. **This fine-tune changes weights.** Per
`PREREG_ACT2_DRIFT` §0.2 (unamended) and MEASUREMENTS C8: `D_w` becomes a live
category, the subscript discipline returns, and `_ctx`/`_w` must never be
reported under one word. Every number this run produces is `_w` and is labelled
so. It is not comparable to the frozen inference-only ruler (C1) — see §6.

---

## 1 · The assumption, stated as the thing that could be false

D6 established, decisively: the lag-2 persistence is **endogenous to the base
weights** — corpus signal swung 230 z (0.443 → 0.000 shared roots) and the model
held ≈0.35, flat, unordered. The frozen-base LoRA approach is exhausted as a
lever (measured, not suspected).

The **untested** claim: a fine-tune that *unfreezes base weights* can move the
endogenous persistence a LoRA-on-frozen-weights cannot reach. It might:

  a. **install release** — lag-2 drops to ceiling, perceive holds, F-LOCAL
     survives (the working module);
  b. **fail to move it** — lag-2 stays ≈0.35 even with base weights unfrozen
     (the persistence is deeper than fine-tuning reaches; the substrate itself
     is the wall);
  c. **install release but crater fluency** — lag-2 drops but F-LOCAL fails
     (too aggressive; the fine-tune broke the native speaker);
  d. **install release but kill perceive** — lag-2 drops but lag-1 falls below
     floor (collapsed toward content-free; traded one failure for the other).

---

## 2 · Why the rank sweep is skipped, logged not silent

A LoRA-rank sweep is the cheaper next lever and is being **deliberately
skipped**, with reason: D6 established the persistence is endogenous to the base
weights, and a LoRA at any rank is a low-rank perturbation *on top of frozen
base weights* — more capacity to fight the base prior, still fighting a frozen
base. The mechanism D6 measured predicts rank floors for the same reason corpus
signal floored. Skipping it is a logged decision (this section), not an
unexamined leap.

⛔ If this run returns (b) — fails to move it — the rank sweep is retroactively
moot (a weaker lever could not do what the stronger one did not), **subject to
the escalation ladder in §7**, which must be exhausted before "substrate" is
said out loud.

---

## 3 · The instrument — the same one, both sides (imported, identity-asserted)

`act2_model_lag.py` imports `lag_profile`, `permutation_null`,
`check_transience`, and the thresholds `Z_LAG1_MIN` / `Z_LAGN_MAX` from
`tlon.discourse.transient` — the exact functions and constants the corpus and
the LoRA gate (`abde6124`) were read against. Function-identity asserted (`is`,
not equality). A model-side statistic or threshold invented here would let the
gate be tuned after seeing the model — post-hoc.

Chain construction identical to `abde6124` §2: trained shape, bare-surface
provocation, refusal ends a chain (never spliced), chains < 3 turns dropped and
the drop count reported. 12 chains × 10 turns, temp 0.70, max_new_tokens 256 —
the gate's pinned parameters, unchanged. Chain accounting reported first: a
truncated instrument is not a finding.

---

## 4 · The thresholds — imported, three axes, all three required for GO

This run differs from the LoRA gate in one structural way: **weights change, so
F-LOCAL and perceive can break, and both must be measured.** GO requires all
three:

    RELEASE:  lag-2 z <= 3.0  (Z_LAGN_MAX, imported) AND every longer lag <= 3.0
    PERCEIVE: lag-1 z >= 6.0  (Z_LAG1_MIN, imported)
    F-LOCAL:  render AND speak clear their standing gate (cardless,
              unconstrained, n=64)

### 4.1 · ⛔⛔ THE WEIGHT-DELTA PRECONDITION — ON THE WHOLE TABLE, NOT A FOOTNOTE

**No row below may be read until the fine-tune is shown to have moved the
weights.** The run records, per trainable module, `||theta_final - theta_init||`
and the **fraction of trainable parameters whose stored value actually
changed**, both into the run manifest.

⛔⛔ A near-zero delta is **INSTRUMENT FAULT — never (b)**. This is
`assert_the_mutation` at the weight level, and it is load-bearing here for a
specific, quantified reason recorded before the run:

An Adam step has magnitude ≈ `lr` irrespective of gradient scale. Under a
**bf16 master copy**, the representable increment at a typical Qwen weight
(`initializer_range` = 0.02, from the model's own `config.json`) is
`ulp = 1.22e-4`, so a 1e-5 step is **0.08 ulp and rounds to zero every step**;
the largest weight that can absorb one step is `|theta| <= 2.56e-3`, an order of
magnitude below typical. A bf16-master run would therefore have produced weight
movement indistinguishable from zero across most of the model — **observationally
identical to (b), the terminal substrate finding.** §5 selects an fp32 master
copy for exactly this reason (`ulp = 1.86e-9` at `|theta|` = 0.02; a 1e-5 step is
5,369 ulps and lands cleanly), and this precondition is the guard that a wiring
bug, a mis-set `requires_grad`, or any future config change cannot slip past.

A silent no-op and a silent success are the same observation. This precondition
is what separates them.

### 4.2 · The verdict table

| outcome | release (lag>=2) | perceive (lag1) | F-LOCAL | verdict |
|---|---|---|---|---|
| **GO** | all z <= 3.0 | z >= 6.0 | clears | fine-tune installs release without breaking the speaker. **The module is buildable; the drift measurement is un-blocked.** |
| **STOP — floored** | any z > 3.0 | z >= 6.0 | clears | (b). Persistence survives the unfreezing declared in §5. ⛔ **Not yet a substrate finding** — the §7 escalation ladder must be exhausted first. |
| **STOP — fluency cratered** | all z <= 3.0 | z >= 6.0 | **fails** | (c). Release installed at the cost of the native speaker. Pre-declared dial-back: LR → 5e-6, as a **new** pre-registered run. |
| **STOP — perceive killed** | all z <= 3.0 | **z < 6.0** | any | (d). Collapsed toward content-free. The ENTANGLED fork (eliminated corpus-side, D6 §3) re-opens at the weight level. |
| **STOP — incoherent** | mixed | mixed | mixed | instrument or training fault before interpretation. |
| **INSTRUMENT FAULT** | — | — | — | §4.1 precondition failed: weights did not move. **No row above may be read.** |

⛔⛔ **NO THRESHOLD CHANGE IS AUTHORISED BY ANY STOP.** The thresholds are hashed
into this body and imported from the corpus's own constants. A lag-2 landing at
z = 4 is a STOP-floored, and the response is to ask why the fine-tune
under-installs — not to discover 5.0 was always sensible.

⛔ A GO is not "the transcripts read well." The verdict is the three-axis
profile; the transcript is colour.

---

## 5 · The fine-tune configuration — pre-declared so it cannot be tuned toward the result

Base model `Qwen/Qwen2.5-7B-Instruct`. Corpus `dd40e22f85b0b6e4`
(content-transient, dose 0), rebuilt deterministically and sha-verified before
training. **One configuration is read against this document; a second attempt
after a (c) result is a new pre-registered run, not a re-read.**

| field | value | why it is here and not in a runbook |
|---|---|---|
| **card** | `gpu_1x_h100_pcie` — 1× H100 80 GB PCIe, $3.29/hr, us-west-3 | The 40 GB A100 default is over by 3.2–3.4×. No A100-80GB exists on Lambda. GH200 (96 GB, $2.29) is cheaper and larger but aarch64 — a `bitsandbytes` install-time failure on a self-terminating box is the failure mode that burns a rental. The card sets batch/accum, so it is config, not deployment. |
| **master copy** | **fp32** | The load-bearing choice. See §4.1: a bf16 master rounds a 1e-5 Adam step to zero for the bulk of the model and would fake (b). |
| **optimizer moments** | **AdamW, 8-bit (`adamw_bnb_8bit`)** | ⚠️ **FORCED, not preferred.** fp32 moments do not fit at any split: 90.8 GiB at 4×4 and 86.8 GiB at 2×8 against 80. 8-bit quantises `m`/`v` only; parameters stay fp32, so the update still lands in fp32 and **the §4.1 dead-zone does not return**. The cost is noise in the direction/scale estimate, not a rounding floor. |
| **frozen** | `embed_tokens` + `lm_head` — 2 × 544,997,376 = **1.090 B, 14.3%** | `tie_word_embeddings: false`, so these are two separate matrices (checked against the model's own `config.json`, not assumed). Release is representational, not tokenization: it lives in the layers. Freezing them also holds the token↔vector mapping fixed, which **protects F-LOCAL**, a GO axis. |
| **trainable** | **top 14 of 28 transformer layers — 3.263 B** | What makes an fp32 master affordable. ⚠️ This is a real scope reduction and it is what a (b) would be about — see §7. |
| **dtype layout** | frozen params bf16, trainable params fp32 | 65.7 GiB worst-case vs 76.9 for all-fp32; keeps the gate's 4×4 shape with margin. |
| **LR** | **1e-5** primary; **5e-6** pre-declared dial-back for a (c) crater | Genuinely ordered under an fp32 master. ⚠️ Under a bf16 master they are *not* ordered — 5e-6 halves the absorbable-weight ceiling to 1.28e-3 and is *deeper* into the dead zone. The fp32 choice is what makes "gentler" mean gentler. |
| **seq** | **384** | The gate's actual value (`pipeline_retrain.sh:98`), not 256. Declaring 256 would move a second knob against the LoRA arms. |
| **batch × accum** | **4 × 4**, effective 16 | Byte-identical in shape to the gate. Fit: 51.4 GiB planner, **65.7 GiB** with the planner's own 28% worst-observed miss applied — **14.3 GiB margin on 80**. |
| **grad checkpointing** | on | As shipped. |
| **epochs** | **2 declared**, with a **mandatory read at end of epoch 1** | The epoch-1 read measures F-LOCAL **and** lag-2. Pre-declared early-stop: if epoch 1 is GO on all three axes, **stop there**. Stopping on a pre-declared success condition is not threshold-fudging; it protects against an epoch-2 over-fit cratering fluency. If epoch 1 is not GO-on-all-three, epoch 2 runs and epoch 2 is the verdict. Both branches are declared here, so neither is a choice made after seeing the number. |

⚠️ **The VRAM figures above are LOWER BOUNDS.** `PLANNER_IS_A_LOWER_BOUND = True`
in `act2_finetune.py`; the planner under-predicted its closest anchor
(bf16 / seq 256, 36.1 GiB measured) by 28%, and every figure quoted here has
that 28% applied. They are still floors, not measurements.

⚠️ **F-LOCAL is a GO axis here because a weight change can break it.** The LoRA
arms kept F-LOCAL unordered across doses (D6) — but that was frozen-base.

---

## 6 · The ruler — a NEW `D_w` baseline, NOT the frozen inference ruler

The frozen 7-build between-build sd (C1, `84c2a1b5`) is a `_ctx` ruler over
inference-only LoRA adapters. This fine-tune produces a `_w` object; measuring
it against the `_ctx` ruler compares two categories under one scale (the C8
prohibition). ⛔ The frozen ruler stays frozen and authoritative for prior
inference-only results and is NOT touched.

Any distance/convergence read on the fine-tuned model needs its own `_w`
baseline, computed over `_w` objects, recorded separately. This run's *lag* read
(release/perceive) does not need the ruler — lag is a within-model profile
against a permutation null — so the ruler question is deferred to the point a
two-speaker `_w` drift measurement is actually run, and flagged here so it is
not silently pooled.

⛔ Structurally enforced, not remembered: the `_w` object enters the ledger
through the dose-arm quarantine path (no `cell`, no `factorial_pair_key`, no
`pairing_capability_side`), so no pooling routine can take it into a `_ctx`
contrast whether or not anyone recalls that it must not.

---

## 7 · What is deliberately NOT claimed, and the escalation ladder

- **Not that a GO is the finished chatbot.** GO means release transmits without
  breaking the speaker — the *precondition* for the module and for a
  Tlön-faithful two-speaker drift measurement. Product-satisfying conversation
  is a further question.
- **No two-speaker claim.** This is a single-model release read.
- **No power claim beyond the corpus-scale effect** the lag instrument is sized
  for (`abde6124` §5): a lag-1 z between 3 and 6 is UNDERPOWERED, not a STOP by
  magnitude; more chains, pre-declared, before revisiting.

### 7.1 · ⛔⛔ A STOP-FLOORED DOES NOT SAY "SUBSTRATE" UNTIL THIS LADDER IS SPENT

A (b) from *this* configuration means **the top 14 layers, with embeddings
frozen, trained properly, could not install release.** It does not mean the
substrate is the wall. In pre-declared order, each rung a separate
pre-registered run:

1. **STOP-floored with the top half unfrozen** → next attempt unfreezes more
   layers (all 28, fp32 master, which requires multi-GPU FSDP or a larger card).
2. **STOP-floored with all layers unfrozen** → next attempt unfreezes
   `embed_tokens` + `lm_head`, testing the §5 claim that release is
   representational rather than tokenization.
3. **Only when rung 2 also floors** is "the substrate is the wall" the finding —
   and it is then a real, terminal, publishable result about this base model.

Writing the ladder here is the point: a floor at rung 0 is the *cheapest* place
to mistake a scope limit for a law.

---

## 8 · Operational (carried, all red-proofed in the record)

- Watchdog armed **first**, before floors (R5): the safety net deploys before
  the risk. A broken tree failing floors-after-arming triggers the watchdog,
  which is its job; floors-first leaves the un-guarded idle window that leaked
  $0.75 twice.
- `~/DONE` = persisted-and-verified, per-artifact pipeline stage (D1). Persist
  set **includes the corpus manifest** (R6).
- ⚠️ The persist chain is adapter-shaped today (`CELL_FILES` names
  `adapter_model.safetensors`). A `_w` object is ~13 GiB of sharded safetensors
  plus an index: different filenames, different count, and a 13 GiB verified
  round-trip. **The `_w` persist shape is a build item and a launch blocker.**
- Provisioner: verified upload, verified download (local md5 == box md5),
  persist-before-terminate (refused if any artifact unpersisted), `HF_TOKEN`
  write-probed at provision time.
- Corpus rebuilt deterministically and sha-verified `dd40e22f85b0b6e4` before
  training (`sorted()` / `PYTHONHASHSEED` fix applies).
- Pull the throughput log before terminating (it costs the next run).
- `lint_settled_claims` clean; every number carries its interval and its `_w`
  label.

---

## 9 · Provenance / cost

⛔ **The LoRA per-adapter figure does not carry.** The gate's LoRA train stage
measured `train_runtime` = 1.326e+04 s (3.68 h) at 9.071 samples/s over 60,158
rows × 2 epochs on a $1.99/hr A100-40. This run changes the optimizer, the
trainable parameter count, and the card at once; quoting that figure as an
estimate here would be exactly the borrowed-number error.

The card is $3.29/hr. Per-step cost is **measured, not predicted**: the epoch-1
checkpoint (§5) exists to establish it, and to catch a (c) crater before the
full spend. Price the second epoch against the measured throughput at that
checkpoint, not against anything in this document.

---

**The frame:** D6 proved the release-persistence is endogenous to the base
weights and unreachable by any frozen-base LoRA. This tests the one lever that
reaches base weights, with GO requiring release-transmits AND perceive-survives
AND F-LOCAL-survives, all three, thresholds imported not invented, config
pre-declared so a fluency-crater leads to a pre-registered dial-back, an fp32
master so the optimizer can actually write the update, a weight-delta
precondition so a run that wrote nothing can never be read as a substrate floor,
and the `_w` ruler kept separate from the frozen `_ctx` one. GO un-blocks the
module and the drift measurement together. A floor is a scope finding until the
§7 ladder is spent. Rank sweep skipped with D6's endogenous-to-base reason
logged.
