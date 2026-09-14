# RESULTS — the mapping crater is the tail of an inverted U, not a collapse

**Cell `miscurve-s20624`** · `mistralai/Mistral-7B-Instruct-v0.3` · mapping scope
**PREREG `ac255dce`** · pinned `6238502` · H100 PCIe / us-west-3 · 3.84 h · **$12.07**

⭐⭐ **RENDER RISES, PEAKS, AND FALLS.** Every previous mapping run read only the
endpoint and called it a crater. The endpoint is the tail.

---

## 1 · The curve

Six F-LOCAL readings taken **during** training, same base, corpus, battery
(`a2b318d6d2e6b98a`), seed — a within-run comparison with no cross-run
difference to defend.

```
  step  examples         rms   %layer    speak   render
   107      1712  3.1205e-04   100.1%    17.2%     0.0%   <- the dose-match crossing
   235      3760  3.7173e-04   119.2%    34.4%     0.0%
   470      7520  4.1686e-04   133.7%    75.0%     6.2%
   940     15040  4.6505e-04   149.2%    93.8%    51.6%   <- peak
  1880     30080  5.0033e-04   160.5%   100.0%    34.4%
  3759     60144  5.1900e-04   166.5%   100.0%    26.6%   <- endpoint = control
```

⭐⭐ **THE CONTROL PASSED EXACTLY.** The endpoint had to reproduce
`mismap-s20624`'s render or §7 voided every point. It came back **17/64 on both
runs** and **rms 5.1900e-04 on both**, to five figures — after six in-process
generation reads. So `isolated_read` is demonstrated empirically, not only in
unit tests, and this arm is bit-reproducible again.

## 2 · What it settles

⭐ **The crater reading is dead.** Render is not destroyed by touching the
mapping; it is *installed* (0 → 51.6 %) and then *lost* (51.6 → 26.6 %). Every
prior mapping run sampled only the far end of that curve.

⭐ **Over-dose is real AND insufficient.** Past step 940 more training makes
directed production worse — so the craters were partly over-dose. But the peak
is **51.6 %** against the **0.90** gate and the layer rung's **93.8 %**, so dose
alone does not explain the gap.

⭐ **Dose is nearly a pinned variable.** From this run's six points and Qwen's
two-LR pair:

    rms ∝ steps^0.144        (within this run, LR fixed)
    rms ∝ LR^0.298           (Qwen fwmap vs fwmap6)
    to halve the dose: 124x fewer steps, or 10.2x less LR

⛔⛔ **So "dose-matched, therefore comparable" rests on a quantity that barely
responds to the levers available.** This reaches back through every cross-scope
dose claim in the arm.

⛔⛔ **AND rms IS NOT COMPARABLE ACROSS SCOPES IN EXAMPLES-TERMS.** The
layer-rung dose (3.1180e-04) is reached at **step 107 — 1,712 examples against
the layer rung's 60,144.** Matching rms between scopes equates 2.8 % of an epoch
with a whole one.

## 3 · ⛔ What it does NOT settle

⛔ **`render` and `examples_seen` are perfectly collinear within a single-LR
run.** Every point moves both together, so the inverted U cannot be attributed
to dose rather than to training duration. **"Mapping-only cannot install
faithful render at any dose" is NOT established** — only *"not along this LR's
trajectory."* A lower-LR curve breaks the collinearity by giving render at
matched rms with different examples; that is the experiment, and it has not run.

⛔ No release or perceive verdict at any intermediate dose — the curve reads
F-LOCAL only (`ac255dce` §6.3). Render is the gating axis, and it never cleared
0.90 anywhere on the curve.

⛔ The peak is five coarse points; the true maximum could sit between steps 470
and 1880.

## 4 · ⛔ The pre-declared rule was mis-specified, and the curve is what showed it

§6.1 row 1 read `render_low < 0.90` as *"the mapping touch craters directed
production."* ⛔ **The premise is false.** Render does not start high and get
destroyed — it starts at 0.0 % because Tlön is not installed yet. So
`render_low < 0.90` cannot distinguish *destroyed* from *not yet learned*, which
is the whole distinction the row claimed to draw.

⭐ **Row 4 governs** (render non-monotone → record the curve, claim no trend),
and the prereg held *by having a branch for its own primary rule being wrong.*
The "peak never reaches 0.90" reading is **post-hoc** and is labelled so.

⭐⭐ **AND THE DESIGN THIS REPLACED WOULD HAVE BEEN CATASTROPHICALLY WRONG.** The
rejected halt-at-matched-dose design stops at step 107, measures render 0.0 %,
and reports *"at matched dose the mapping craters render"* — about a model that
had seen 2.8 % of an epoch. The confound was estimated at "~40 % fewer
examples"; it is **~97 %**. What makes the point legible rather than a trap is
§4's requirement that `examples_seen` sit beside `rms` on every row: read alone
`rms 3.1205e-04 · render 0.0%` looks like a matched-dose crater, and with
`examples_seen 1712` next to it the model obviously has not learned yet.

## 5 · ⚠️ FLAGGED HYPOTHESIS — NOT A RESULT

The run spent a second epoch its prereg did not declare (§6). Those readings are
**unregistered and may not be cited as evidence.** They are recorded here
because losing them would be worse than holding them honestly:

```
            render      lag1     lag2     lag3     lag4
epoch 1     26.6%      +22.97   +8.87    +3.08    +0.84
epoch 2     32.8%      +25.75   +7.53    +1.23    -1.33
```

⭐ **Every axis moved the good way, and lag3 dropped under the 3.0 ceiling.**
(render 17/64 → 21/64 is z = 0.78 — *not worse*, not better.)

⛔⛔ **THIS IS THE ONLY SIGNAL THIS CAMPAIGN HAS PRODUCED THAT POINTS TOWARD
RELEASE INSTALLING**, and it points at a lever nobody has tested: **epochs.**
The stopping rule exists precisely to *avoid* epoch 2, so the arm has never
looked there.

⛔ n=1, unregistered, and confounded — this was a curve run at 1e-5, so the
improvement could be more-training or could be that run's own dynamics.
**Pre-register an epochs-as-lever test before citing any of this.** It does not
jump the queue ahead of the lower-LR curve, and it must not be lost.

## 6 · Three defects, one cause — all fixed (`fb7962f`, `8905a45`)

Every one was a fix applied to **one of two call sites**:

| | defect | fix |
|---|---|---|
| 1 | `--mapping` reached `verdict_epoch1` only → epoch 2 fell back to the pooled §4.1 test and reported a **false** INSTRUMENT FAULT | every verdict call site asserted to carry it |
| 2 | `persist_reads` sat after `verdict_epoch1` only → **the curve JSONL reached no hub at all** | `FLUSH_PATTERNS` + `trap _flush_measurement EXIT` |
| 3 | the §4.1 fix changed `decide()`'s exit code, unblocking the epoch-2 branch | `EPOCH_BUDGET`, default 2 |

⛔⛔ **Existing tests could not have caught any of them** — they exercise
`decide()`, `mapping_moved`, `isolated_read`, the *definitions*. A function can
be correct at every definition and wired into half the places it is needed.
`tests/test_call_site_coverage.py` enumerates **call sites** instead.

⛔⛔ **AND `cmd_flush` NEVER SWEPT THE MEASUREMENT.** It covered
`pipeline_*.log`, `manifest.json`, `watchdog.log` — and nothing a run measured.
`mismap` and `miscurve` were both recovered *only* because their numbers had
been printed into a log that happened to match a pattern. Twice is not luck, it
is a dependency on an accident; the function's own docstring already recorded
this as the **fourth** instance of the hardcoded-name class, and this was the
fifth.

⛔ On defect 3, making `STOP — incoherent` terminal was **rejected**: the
evidence for "epoch 2 degrades" is rung 1a's epoch 2 destroying a
*floored-but-fluent* epoch 1 — a readable state the rule already halts on — and
the only case that governs (§5) points the other way. The defect is
**unregistered** spending, not **harmful** spending.

## 7 · ⏭ Next

1. **The lower-LR curve (≈3e-6)** — breaks the rms/examples collinearity and
   decides locus-versus-trajectory. ⛔ Its prereg must declare **`EPOCH_BUDGET=1`
   in §2 beside the epoch count**, so the declaration and the enforcement are one
   statement — the whole lesson of defect 3.
2. **The epochs-as-lever prereg** (§5), held as hypothesis.
3. `pipeline_fullft_read.sh` is still Qwen-hardcoded — de-Qwen before any re-read.
