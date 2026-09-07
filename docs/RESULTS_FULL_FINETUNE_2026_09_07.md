# RESULTS — the full-weight release run

**PREREG** `PREREG_FULL_FINETUNE_RELEASE_2026_09_05.md`, **LOCK `a0450b36`**
(verifies, body unchanged). **DEVIATIONS** D-7-extended (card) and D-8 (attention
implementation), both declared *before* the run fired.

Run `fw-s20624` · box `5854a39f977e47f89bb738a0ecfd2561` · `gpu_1x_h100_sxm5`
us-south-3 · pinned `6ddc16d` · 2 epochs · ~2.5 h · **~$10.70** · self-terminated
after persisting. Corpus sha-verified `dd40e22f85b0b6e4`.
Artifacts: `hf://keyzersoze04/tlon-act2-adapters/fw-s20624/` and
`.../fullft_fw-s20624/`.

⭐ **This is the first readable verdict table the full-weight arm has produced.**
Four earlier attempts produced NaN models; see
`FINDINGS_FULLFT_TRACE_2026_09_06.md`.

---

## 1 · The tables

| axis | epoch 1 | epoch 2 |
|---|---|---|
| **release** (all lags ≤ z 3.0) | **FAIL** — lag2 z=+5.79 | **FAIL** — lag2 +8.42, lag3 +4.35, lag4 +2.07 |
| **perceive** (lag1 ≥ z 6.0) | PASS — z=+24.05 | PASS — z=+23.26 |
| **f_local** | PASS | **FAIL — fired** |
| §4.1 delta | OK · `fraction_nonfinite` 0.0 | OK · `fraction_nonfinite` 0.0 |
| §4.2 verdict | **`STOP — floored`** (b) | **`STOP — incoherent`** |

Lag profiles: epoch 1 `1.0093 / 0.3542 / 0.0833 / 0.0556`; epoch 2
`1.0093 / 0.4271 / 0.2738 / 0.1944`.

---

## 2 · The verdict of record is EPOCH 2, and it is `STOP — incoherent`

§5 declares: *"If epoch 1 is not GO-on-all-three, epoch 2 runs and epoch 2 is the
verdict."* Epoch 1 was not GO, so **the verdict of record is epoch 2's**, and the
prereg's pre-declared reading of that row is:

> *"mixed profile: instrument or training fault before interpretation."*

⛔⛔ **So the verdict of record is not interpreted, and nothing in this document
reads it as a substrate result.**

⛔ **The 5e-6 dial-back is NOT authorised by this run.** It is pre-declared for
row **(c)** only — *release passes*, perceive passes, f_local fails. Release
**fails** here, so this is not (c). Applying it would be borrowing a response
declared for a different row, and §4.2 states plainly: **"NO THRESHOLD CHANGE IS
AUTHORISED BY ANY STOP."** The dial-back is also declared as *"a **new**
pre-registered run"*, not a continuation of this one.

---

## 3 · Epoch 1 is a separately readable measurement — and reading it as *the result* is a POST-HOC step, labelled

Epoch 1's table is **coherent**: release fails while perceive and f_local both
pass, with the §4.1 precondition satisfied and zero non-finite values. It is a
clean **(b) STOP — floored**, and the epoch-1 read was **pre-declared** — §5
makes it mandatory precisely so this measurement exists.

⚠️⚠️ **What is NOT pre-declared is a rule that says "if epoch 2 is incoherent,
fall back to epoch 1 as the substrate-relevant reading."** That rule is being
applied here for the first time, *after* seeing both tables. It is defensible —
epoch 1 is a complete, coherent, precondition-satisfied measurement, and it was
always going to be taken — but it is a **post-hoc selection rule and is recorded
as one**. A future reader must be able to see that the elevation of epoch 1 from
*"mandatory read"* to *"the reading"* happened after the numbers were in.

⭐ With that label attached, the substantive reading of epoch 1 is:

> **At rung one — top 14 of 28 layers, LR 1e-5, read at the end of epoch 1 — a
> full fine-tune did NOT install release, while perceive and local fluency both
> held.**

⛔ **A (b) floor is NOT a substrate finding.** §7.1's ladder — more layers, then
unfreeze embeddings, then the wall — must be exhausted first. This is rung one.

---

## 4 · The epoch-2 incoherence is a PROCEDURAL finding: the run over-fit past its own clean floor

Every lag rose between epoch 1 and epoch 2, and one crossed from chance into
significance:

| lag | e1 z | e2 z | |
|---|---|---|---|
| 2 | +5.79 | **+8.42** | already over ceiling, got worse |
| 3 | −0.87 | **+4.35** | **chance → significant** |
| 4 | −1.30 | **+2.07** | chance → approaching ceiling |

…while f_local broke and perceive held. **A second epoch of training on a
release-suppression corpus increased content persistence and degraded the
speaker.**

⭐ **And the stopping rule could not catch it — verified in code, not inferred.**
`pipeline_fullft.sh` runs the early stop as `if [ $E1 -eq 0 ]`, and
`act2_fullft_verdict.py` returns **exit 0 only for GO**; every STOP row returns
1. So a **floored-but-fluent epoch 1 cannot trigger the early stop**, and the run
proceeds into an epoch that can only be read if it stays coherent. The prereg
names this hazard exactly — *"it protects against an epoch-2 over-fit cratering
the fluency that just passed"* — but gates the protection on a condition a
floored run cannot meet.

⛔ **This is a design gap in the stopping rule, not a fact about the substrate.**

### On "training fault" vs "instrument fault", with the confidence it earns

The prereg's row says *"instrument or training fault."* The evidence points at a
**training fault (over-fit)**: the degradation is **directional and coherent** —
three lags all moving the same way, fluency breaking, perceive holding — where an
instrument fault would be expected to produce scattered or non-monotone
incoherence.

⚠️ **But this is one run, one seed, two points.** "Monotone across two
measurements" is a two-point trend, and this project's own rule is that a
small-n trajectory is read for structure, not treated as established
([[wait_for_n]]). **Over-fit is the leading explanation, not a demonstrated
one.** Nothing downstream should treat it as measured.

---

## 5 · An instrument observation worth carrying

⛔ **`fraction_changed` SATURATES.** It read **`0.9999629153481012` at both
epochs** — identical to sixteen digits, the same **21 of 566,272** sampled values
unmoved. It answers *"did the optimizer write anything?"* and nothing else; it
cannot distinguish one epoch of training from two.

⭐ **`delta_norm_estimated` is the dose measure: 17.81 → 26.80.** It is also what
proved epoch 2's delta file was genuinely rewritten rather than a stale read of
epoch 1's — the identical `fraction_changed` looked exactly like a stale-file bug
and was not one.

**The field that maxes out is not the field that measures.**

---

## 6 · What this run does NOT establish

- ⛔ Not a substrate finding. Not a wall. Rung one of §7.1.
- ⛔ No threshold is revisited. The thresholds are hashed into the locked body
  and imported from `tlon.discourse.transient`.
- ⛔ No comparison to the LoRA arm is made. `_w` and `_ctx` are separate
  measurement categories by construction, kept apart so a shared-looking z-score
  cannot be read across them.
- ⛔ The verdict of record was **not** measured on §5's declared card (D-7-ext),
  and was measured under an attention implementation §5 did not name (D-8). A
  STOP here is about eager's numerics as much as the model's — as every earlier
  run was silently about SDPA's, with the difference that this one is written
  down.

---

## 7 · What the next run has to carry

Not a continuation and not a threshold change on this one — **a new
pre-registered run**, which is what §5 requires for any of this.

1. **A stopping rule that protects a floored-but-fluent epoch-1 state**, so a run
   cannot over-shoot a readable floor into an unreadable crater. The current gate
   fires only on GO.
2. **The next §7.1 rung**, with the epoch-2 result informing it: more layers adds
   *capacity to over-fit*, and this run showed more training in this direction
   makes release **worse**. So "more layers" may need a gentler LR alongside it
   rather than after it.
3. ⚠️ **Or first: re-confirm rung one.** There is exactly **one** epoch-1 reading
   of this cell. One reading is not a result, and every lever question downstream
   rests on it.

⛔ Which of 2 or 3 comes first is a decision for the next prereg, not a
consequence of this document.
