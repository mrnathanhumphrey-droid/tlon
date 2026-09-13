# PREREG — the mapping dose curve: does touching the mapping crater the speaker, or did every mapping run simply get too much dose?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `ac255dce` (sha256[:8] of draft body at lock, 2026-09-13T21:18Z)
- **Date:** 2026-09-13
- **Cell:** `miscurve-s20624`
- **Fires on:** one full-weight fine-tune of **`mistralai/Mistral-7B-Instruct-v0.3`**,
  `embed_tokens` + `lm_head` trainable and all 32 layers frozen
  (`--scope-mode mapping`, **268,435,456** trainable), LR **1e-5**, content-transient
  corpus `dd40e22f85b0b6e4`, **a full epoch, changing nothing about the training
  itself** — with **F-LOCAL read at five points along the way**.
- **Predecessors:** `mis16d-s20624` (`5f4a554c`, layer rung, floored +3.972,
  faithful speaker) · `mismap-s20624` (`afe75eca`, mapping rung, no verdict) ·
  `fwmap-s20624` / `fwmap6-s20624` (`c2a4f0ca` / Run 0, Qwen mapping, both cratered).

---

## 0 · The one question this run exists to answer

⛔⛔ **EVERY MAPPING RUN EVER FIRED CRATERED DIRECTED PRODUCTION, AND EVERY ONE
OF THEM WAS OVER-DOSED.** On the identical F-LOCAL battery `a2b318d6d2e6b98a`:

| run | base | LR | dose (rms) | % of layer rung | **render** |
|---|---|---|---|---|---|
| `fwmap` | Qwen | 1e-5 | 5.5152e-04 | 176.9 % | **0.0 %** |
| `fwmap6` | Qwen | 5e-6 | 4.4869e-04 | 143.9 % | **0.0 %** |
| `mismap` | Mistral | 1e-5 | 5.1900e-04 | 166.5 % | **26.6 %** |

So *"the mapping touch breaks the speaker"* and *"every mapping run was
over-dosed"* predict the same three rows. **No mapping run has ever been
dose-matched to the layer rungs (3.1180e-04).**

⭐ **One piece of evidence already runs against the dose explanation**: between
`fwmap` and `fwmap6` the dose fell **33 points** and render **did not move** —
0.0 % both times, same probes. Over-dose predicts render improves as dose falls.
⚠️ Recorded as a direction, not a result: those two runs differ in more than
dose, and the local `fwmap` log is its *rescue* log, so its step count cannot be
verified. **Nothing here is claimed from that pair beyond the direction.**

### ⛔⛔ 0.1 · Why this is NOT done by matching the dose

The obvious design — halt when rms reaches 3.1180e-04 — lands at roughly **60 %
of the epoch, about 40 % fewer examples than any layer rung saw.** The fine-tune
is what *installs* Tlön: the layer rung's render 93.8 % was **learned**, not
native. So a crater in that run would be explained equally well by *"the mapping
touch breaks render"* and by *"we showed it 40 % less data."*

⛔ **The mechanism used to control the variable would become a rival cause of the
measured outcome.** That is not a comparability caveat to record. It is a
confound that invalidates the read.

### ⭐⭐ 0.2 · So measure the curve, not the point

Train the full epoch and read F-LOCAL **while it runs**. Every point shares one
base, one corpus, one battery, one seed — the comparison is **within-run**, and
there is no cross-run difference left to defend. The dose-matched reading is
simply one point on the curve, **observed in passing while the epoch completes**,
so nothing is traded away to reach it.

⭐ It also yields this base's **own rms-versus-steps points** — the second dose
point that made the learning-rate question answerable. That question is
currently *unanswerable*: one measurement fixes an intercept, never a slope, so
every exponent reproduces Mistral's single point exactly while implying
dose-matched LRs from **6e-8 to 6e-6, a 98× spread**.

### 0.3 · How it bears on §0's (A)/(B) split

⛔ **This run does not produce a mapping-rung verdict** (§6.3). It decides
whether one is *reachable*. But the answer is not neutral between the campaign's
two hypotheses:

- **render already destroyed at the lowest dose** → the mapping cannot be touched
  without breaking the speaker, at any dose this method reaches. That is
  **(B)-supporting for the mapping locus** — release and speakerhood in tension
  exactly where release was thought to live — and it is then a *cross-family*
  statement, since Qwen shows the same at two doses.
- **render intact at low dose and falling with dose** → the craters were
  **over-dose**, the mapping rung is readable after all, and the curve says at
  what dose to read it.

---

## 1 · SCOPE — unchanged from `afe75eca`

`embed_tokens` + `lm_head` trainable, all 32 transformer layers frozen.
**268,435,456** params, measured off the real safetensors, `tie_word_embeddings:
false`, one stack of 32 — re-asserted at run time against the model, never read
from this file. The tied-checkpoint refusal stays armed although it cannot fire
on this base.

⛔ **Nothing about the training is changed from `mismap-s20624`** — same base,
scope, LR, corpus, seed, card, kernel. That is deliberate: the curve's endpoint
must be comparable to the run it explains, and a training change would make this
a different experiment rather than a reading of that one.

---

## 2 · Configuration

| field | value | why |
|---|---|---|
| **base** | `mistralai/Mistral-7B-Instruct-v0.3` | As `mismap-s20624`. |
| **LR** | **1e-5** | ⭐ **Held, not chosen.** Every run in this arm except `fwmap6` is at 1e-5, and §0.2 shows the dose-matched LR cannot be derived from existing data. Holding it keeps LR the constant it has been and makes *dose* the thing that varies — along the curve, by training longer. |
| **epochs** | **1, run to completion** | ⛔ The epoch must finish. A halt is the confound §0.1 rejects. |
| **card** | `gpu_1x_h100_pcie`, us-west-3 | Matched to `mis16d` and `mismap`. SXM5 only if capacity forces, reason recorded. |
| **attention** | `eager`, pinned both legs | Demonstrated clean on Mistral. |
| **corpus** | content-transient, `dd40e22f85b0b6e4`, sha-verified | Byte-identical. |
| **curve reads** | **5**, geometric: steps **235 · 470 · 940 · 1880 · 3760** | ⭐ Halving back from the end puts **half the reads in the first quarter**, where "destroyed immediately" and "decays with dose" make different predictions. Even spacing would spend the budget where they agree. |
| **extra read** | when rms first crosses **3.1180e-04** | The layer-rung dose, observed in passing. ⛔ **Training continues through it** — `tests/test_dose_curve_wiring.py` asserts the callback never returns a stop. |
| **probes per read** | 64, cardless, unconstrained, greedy | The gate's own n and the gate's own configuration. |

---

## 3 · ⛔⛔ THE READS MUST NOT PERTURB THE RUN THEY MEASURE

A curve measured by disturbing the run it measures is a curve of a **different
run**, and nothing downstream could tell. Three things a mid-training generation
touches, all restored and all **asserted** rather than trusted
(`tlon/act2/dose_curve.py`, `isolated_read`):

1. **Module mode** — `generate` needs `eval()`; left there, dropout is disabled
   for the rest of training. The run would finish, report a clean loss, and be a
   different experiment.
2. **RNG state** — F-LOCAL decodes greedily (`temperature=0.0`, so
   `do_sample=False`) and *should* draw nothing. ⛔ "Should draw nothing" is
   precisely the assumption this project keeps paying for, so the state is saved
   and restored anyway, and `test_the_draw_after_a_read_is_the_draw_that_would_have_come_next`
   asserts the training stream continues exactly where it would have.
3. **Gradients** — cleared, because a grad left by a read would be added to the
   next optimizer step and move the weights by an amount no dose accounts for.

⭐ On failure it raises `EvalContaminatedTraining` rather than warning: the
failure mode is a silent restore-that-did-not.

⛔ **No intermediate weights are written.** Five checkpoints would be
5 × 14.5 GB = **72 GB against 46.8 GB of headroom**. The curve *is* the
readings. `LocalBackend.adopt` reads the model where it already sits, and
deliberately does **not** touch its training mode.

---

## 4 · What each reading records

`step · of · why (schedule|target) · examples_seen · rms · delta_verdict ·
fraction_changed · speak · render · battery · lr`, one JSON object per line.

⭐ **`examples_seen` sits beside `rms` on every row, by construction.** The
design this replaces would have conflated them under the single word "dose";
here they are two named columns and cannot be silently substituted for one
another. Every row also stamps the **battery digest**, so the curve can make the
same cross-run claim about itself that §0's table makes.

---

## 5 · The gates that still apply

`base_audit` · `eos_guard` · corpus sha · `verified_prereg_id` ·
per-leaf `mapping_moved` against `act2_vocab_coverage.py`'s per-base coverage ·
the **§4.1 precondition carried by the per-leaf test** (`757c157`), because the
pooled fraction test is invalid for mapping scope — it predicts 1.0 where a
healthy mapping run is structurally ≈ `(1.0 + coverage) / 2`. ❓ UNKNOWN is not
PASS.

---

## 6 · How the curve is read — PRE-DECLARED

### 6.1 · The primary reading

Let `render_low` be render at the **first** checkpoint (step 235) and
`render_end` render at the last (step 3760, the full-epoch endpoint, which must
reproduce `mismap-s20624`'s **26.6 %** within sampling error or §7 applies).

| pattern | reading |
|---|---|
| **`render_low` < 0.90** | ⭐⭐ **THE MAPPING TOUCH CRATERS DIRECTED PRODUCTION.** Render is already gone at ~6 % of the epoch, long before the dose reaches the layer rung's. Over-dose is excluded as the cause. **(B)-supporting for the mapping locus**, and cross-family given Qwen's two doses. |
| **`render_low` ≥ 0.90 and render falls below 0.90 later** | **DOSE.** The craters were over-dose; the curve locates the largest dose at which render still clears the gate, and the mapping rung is readable there. |
| **render ≥ 0.90 at every checkpoint** | ⛔ Then the endpoint contradicts `mismap-s20624` at the same configuration → **instrument fault**, §7. Not a result. |
| **render non-monotone across checkpoints** | Record the whole curve and claim nothing about a trend. n=1 per point. |

⛔ **0.90 is `NATIVE_THRESHOLD`, imported from `tlon/act2/falsify.py`, not
retyped here.** No threshold moves in this prereg.

### ⛔⛔ 6.1.1 · A COARSE POINT AT THE THRESHOLD IS NOT A VERDICT

`render_low` is **one** reading at **n=64**, and the first row of §6.1 asks it to
decide between two hypotheses by which side of 0.90 it falls on. ⛔ Near the
threshold it cannot do that: the binomial standard error of a proportion at 0.90
with n=64 is **0.0375**, so a 1.96-SE band around the threshold spans

    0.8265  <=  render_low  <=  0.9735          (53 to 62 valid of 64)

⭐ **DERIVED, NOT PICKED** — it is `1.96 * sqrt(p*(1-p)/n)` at this prereg's own
`p = NATIVE_THRESHOLD` and `n = 64`, computed rather than chosen, so it cannot be
widened after seeing the number.

**If `render_low` lands inside that band, the low-end answer is UNDERPOWERED**,
and §6.1's first two rows **do not fire**. The read then falls to the **shape of
the curve across the remaining four checkpoints** — which has more points and is
not a single threshold crossing. An UNDERPOWERED low end is reported as such,
counted separately, and is **not** evidence for either hypothesis.

⛔ This is the same rule the rest of the arm runs on: an under-resolved
measurement is its own state, never a verdict. A coarse point sitting on a
threshold is exactly how `resolving_power` got built, and letting one
masquerade as a sharp call here would be that lesson unlearned.

⚠️ **Expected to be moot, and pre-declared anyway.** `mismap-s20624`'s endpoint
was render **26.6 %** and the crater evidence points at the mapping touch, so
`render_low` is *expected* far below the band, where n=64 resolves it fine. The
branch exists because the unlikely case is the one that would otherwise be
read too strongly.

### 6.2 · The dose-matched point

The reading taken at the `3.1180e-04` crossing is the **first F-LOCAL ever
measured on a mapping run at the layer rungs' dose**, and it is taken while the
epoch completes, so it carries no early-halt confound. Its `examples_seen` is
recorded beside it and must be quoted with it.

### 6.3 · ⛔ What this run does NOT decide

**There is no release/perceive verdict at any intermediate dose.** The lag
profile is not read along the curve — it costs a 12-chain, 10-turn read per
point, and F-LOCAL is the *gating* axis: if render is cratered, a release number
at that dose is unreadable anyway (the confound the gate exists to prevent).

⭐ So the sequencing is deliberate: this run says whether a readable dose exists.
If one does, the mapping rung is fired **at that dose** under its own prereg,
and *that* run reads release. If none does, there is nothing for a release
reading to be measured on, and the §0 (B)-reading is what the campaign has.

---

## 7 · Fallback

Endpoint disagrees with `mismap-s20624` beyond sampling error → **instrument
fault**: something about the curve reads perturbed the run, and `isolated_read`
failed to catch it. Do not interpret any point. `EvalContaminatedTraining`,
`MAPPING_FROZEN`, `MAPPING_UNVERIFIED`, `DIVERGED` → the run is not evidence,
and no row of §6 may be read.

---

## 8 · Provenance

Cell `miscurve-s20624`, asserted by `cell_guard` to collide with no fired run.
Verdict and `factorial.json` read the one `verified_prereg_id()`, re-hashed.
Machinery red-proofed before firing: `tests/test_dose_curve.py` (20),
`tests/test_backend_adopt.py` (7), `tests/test_dose_curve_wiring.py` (9).

---

## 9 · Operational

Watchdog armed **first**. Deduplicated capacity floor before `train_leg1`
(one object, ~15.18 GB; readings are kilobytes). `persist_reads` after the
reads, so the curve survives a halt — `mismap-s20624`'s entire measurement
existed only in its log and survived only because the watchdog flushed it.
Corpus sha-verified. Curve JSONL persisted under the run root. Every number
`_w`-labelled. ⛔ `pipeline_fullft_read.sh` is Qwen-hardcoded — not on this
run's path, but de-Qwen it before any re-read of this cell.

**Cost:** ~1.35 h training + ~35 min of reads ≈ **$6** at $3.29/h.

---

## 10 · What this run does NOT do

- ⛔ Does not change LR, scope, corpus, seed, card or kernel from `mismap-s20624`.
- ⛔ Does not halt early, and does not stop at the dose-matched crossing.
- ⛔ Does not write intermediate weights.
- ⛔ Does not produce a release or perceive verdict at any dose (§6.3).
- ⛔ Does not move any threshold; 0.90 is imported.
- ⛔ Does not claim a trend from non-monotone points.
- ⛔ Does not let a `render_low` inside the 0.8265–0.9735 band decide between the
  hypotheses — that is UNDERPOWERED and defers to the curve's shape (§6.1.1).
- ⛔ Does not rest anything on the `fwmap`/`fwmap6` pair beyond a direction (§0).

---

## 11 · Watch, do not gate

- **`speak` along the curve.** It was 100 % at the endpoint on Mistral while
  render was 26.6 % — free generation intact, directed production gone. If that
  split holds across the curve it is the OLMo 2a shape appearing again, on a
  second base and at the mapping locus. Record it; no branch reads it.
- **`rms` versus `steps`.** This is the by-product that makes the LR question
  answerable. ⛔ It is not read as a dose-response *law* from one run.
- **`fraction_changed` along the curve** — whether the structural ≈0.512 holds
  from early training, which is the direct evidence for §5's claim about the
  pooled test.
