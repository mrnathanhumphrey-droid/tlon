# RESULTS — the epochs lever: repetition does not install release

- **Prereg:** `docs/PREREG_EPOCHS_LEVER_2026_09_14.md`, lock **`c01a2b89`** (verified)
- **Cells:** `epochlevB2-s20624` (control), `epochlevA-s20624` (repeat)
- **Code pin:** `8acdaf0` · both boxes `gpu_1x_h100_pcie`, us-west-3, ~$70 the pair
- **Status:** both arms complete, both audits clean, both boxes self-terminated.

⛔ **Read §1 before §3.** An earlier run of this arm produced a release curve that
was **void**, and the reason changes how to read several prior campaign numbers.

---

## 1 · The instrument was wrong, and this is the correction

The first arm B (`epochlevB-s20624`, 2026-09-15) trained cleanly and produced a
five-point release curve. That curve measured the wrong quantity.

Every **in-training** lag read in this campaign was taken through a backend built
by `LocalBackend.adopt()`, whose decode defaults are F-LOCAL's: 220 tokens and
**temperature 0.0 — greedy**. A deterministic speaker repeats content across
turns *because the same context yields the same continuation*, so it inflates
apparent persistence at every lag. Same weights, same step, two decoders:

```
in-training (T=0.0)   prof 2.213 1.823 1.595 1.417   lag2 z = 23.858
standalone  (T=0.7)   prof 0.915 0.266 0.085 0.014   lag2 z =  4.343
```

Consequences worth carrying into any framing discussion:

- ⛔⛔ **`miscurve`'s epoch-2 signal — the campaign's only evidence pointing at
  release *installing* — was an in-training read.** It is under the same
  suspicion and should not be cited as support for anything.
- ⛔ **Standalone CLI lag reads are unaffected.** Every `model_lag_*.json` in the
  campaign was taken at T=0.7/256, so cross-run comparisons of *endpoint*
  readings remain valid.
- ⛔ The void curve **could not be recovered by re-reading**: dose-curve
  checkpoints are never written to disk (that is why `adopt()` exists — five
  checkpoints would be ~72 GB). Only a re-run regenerates it, which is why
  **both** arms were re-run rather than arm A alone.

The instrument now owns its decoder (`read_lag` installs T=0.7/256, restores what
it found, and records both in every row), and a post-run gate refuses any run
whose readings do not carry the decoder they were taken with. Five wiring bugs
were found and closed in the process; they are in the git log, not here.

---

## 2 · Design, in one paragraph

Both arms train Mistral-7B-Instruct-v0.3, layer rung top-half (16 of 32), LR
1e-5, identical optimizer steps. The **only** difference is repetition: the
control sees 60,148 distinct rows once; the repeat arm sees a derived 15,040-row
subsample four times. Step match came out **exact**:

```
s_a 3760   s_b 3760   Δsteps 0   Δfrac 0.00000%   (declared tolerance 0.2%)
```

⛔ The cost, pre-declared in §1 of the prereg: repetition is confounded with
**diversity**, because `epochs = steps ÷ distinct` and you cannot hold steps,
dose and diversity fixed at once. The prereg therefore declared in advance that
this design can *confirm* the lever or *confirm the dose story*, but **cannot
cleanly refute** the lever.

---

## 3 · The control arm's curve — the first valid release-vs-dose measurement

```
step   rms          speak  render   lag1   lag2   lag3   lag4   lag1/lag2
 235   1.2973e-04   0.969  0.969   1.000  0.507  0.322  0.286     1.97
 470   1.6514e-04   0.984  0.891   0.975  0.551  0.373  0.204     1.77
 940   2.0590e-04   1.000  0.969   0.975  0.500  0.333  0.315     1.95
1880   2.6790e-04   1.000  0.719   1.057  0.398  0.185  0.072     2.66
3759   3.0915e-04   1.000  0.938   0.778  0.250  0.095  0.097     3.11
```

Lag-2 falls 0.507 → 0.250 and lag-3 0.322 → 0.095 while lag-1 holds: **locality
sharpens as dose rises.** §0 of the prereg noted that release had never been
measured at more than one dose at any scope; this is that measurement, and it is
the first one taken with an instrument that measures persistence rather than
decoder determinism.

⚠️ **Not established as a trend.** n = 1 read per rung, and see §5 for the noise
floor. The direction is consistent across five points; the magnitude is not
bounded by anything here.

---

## 4 · The comparison, at matched dose

⛔ **The endpoints are not a matched pair and were not compared.** Arm A finished
at rms 3.3390e-04 against the control's 3.0915e-04 — **8% apart**. §3 of the
prereg requires reporting that as unmatched rather than comparing it. The
comparison below pairs each control rung with the nearest arm-A read; all five
land within 1%.

```
rms (ctrl)   rms (repeat)   Δ       lag2 ctrl   lag2 repeat   z2 ctrl   z2 repeat
1.2973e-04   1.3032e-04   0.46%      0.507        0.634        4.047      3.653
1.6514e-04   1.6502e-04   0.07%      0.551        0.598        4.571      7.397
2.0590e-04   2.0743e-04   0.74%      0.500        0.313        7.262      4.501
2.6790e-04   2.7056e-04   0.99%      0.398        0.561        7.656      8.960
3.0915e-04   3.1050e-04   0.44%      0.250        0.637        3.999     10.841
```

Endpoint verdicts (standalone reads, T=0.7/256, both `STOP — floored`):

```
              release z2   z3       z4      perceive z1   F-LOCAL
control          5.911    -0.170   0.276      20.866       PASS
repeat           9.472     5.810   3.270      27.711       PASS
```

The control clears lags 3 and 4 below the 3.0 ceiling; the repeat arm does not.
On four of five matched rungs the repeat arm holds **more** content.

---

## 5 · ⭐ The noise floor, measured by accident — read §4 through this

The run contains an unplanned same-object control. The end-of-run verdict and the
final curve point read the **same weights** (one optimizer step apart) with
identical decoder, seed, `chains_used` (12), `chains_dropped` (0) and `n_pairs`
(108/96/84/72). They disagree:

```
        standalone   in-run
lag1 z    20.866     18.371        prof 0.880 vs 0.778
lag2 z     5.911      3.999        prof 0.323 vs 0.250
```

`torch.manual_seed` pins the sampling stream's start, not the realised
generations across two model/process contexts. So **a lag-2 z moves ~1.9, and a
lag-2 profile ~0.073, between two reads of one fixed object.**

Against that floor, three of the four "repeat arm higher" deltas in §4 (0.127,
0.047, 0.163) sit within ~2×. Only the top-dose rung (0.387, ~5×) is clearly
beyond it. ⚠️ **This is a single paired observation, not a variance estimate** —
it bounds nothing formally and no interval is computed from it. It is enough to
say that single-rung differences of order 2 in z2 are not interpretable.

⭐ A confound proposed and then refuted by the artefacts: the repeat arm saw ¼ the
distinct examples, so its chains might be less varied, narrowing the permutation
null and inflating z mechanically. Null sd at the five matched rungs went
wider / narrower / narrower / wider / wider — no consistent direction. The z
differences track the raw profile, not a narrowed null.

---

## 6 · What this settles, and what it does not

**Settled — repetition did not help.** The repeat arm holds more content on four
of five matched rungs, clearest at the top dose; the control's curve sharpens
with dose and the repeat arm's does not. Combined with §1, the strong hypothesis
(*repetition installs release*) has no support left: the signal that motivated
this arm was itself a decoder artefact, and the clean test of it points the other
way.

**Not settled — the lever is not refuted, and §1 of the prereg said so in
advance.** "Repeat arm worse" cannot separate *repetition hurts* from *the repeat
arm saw less diverse data*. The design cannot resolve that, which was declared
before firing. This is an **ambiguous-by-construction** outcome, not a muddy one:
the reason it is ambiguous is known and was written down first.

**Held loosely — the size.** Consistent direction across four rungs, one point
clearly beyond the §5 noise floor.

⚠️ **Where this leaves the wider question — not established, stated as an open
reading.** Every lever the campaign has pulled (dose, layers, mapping locus,
LR-path, and now epochs) has failed to move release toward the ceiling. That is a
consistent picture across arms, not a demonstration; no lever has been shown
*incapable* of installing release, and the escalation ladder in
`PREREG_FULL_FINETUNE_RELEASE §7.1` is not exhausted.

---

## 7 · Open, for the direction discussion

- The diversity confound is structural to this design. Separating repetition from
  diversity needs a different arm (e.g. matched *distinct-example count* with
  varied epochs, which trades a different variable), not a re-run of this one.
- n = 1 read per rung is the binding limit on every rung-level comparison here.
  Repeated reads per checkpoint would cost generations, not training.
- ⛔ The `choose` axis remains **0/256 unscoreable** — an emission failure, not a
  comprehension reading. Unchanged by this run and still open.
- ⛔ `FINDINGS_*.md` is not covered by `tools/lint_settled_claims.py`
  (`LIVE_GLOBS` lists `RESULTS_*`, `AUDIT_*`, `SPEC_*`, `PREREG_*`, `PRICING_*`,
  `PREFLIGHT_*`). Two findings docs in `docs/` are therefore unlinted. Noted, not
  fixed here.

**Artefacts:** `runs/act2/fullft_epochlevB2-s20624/` and
`runs/act2/fullft_epochlevA-s20624/` locally; both cells complete on
`hf://keyzersoze04/tlon-act2-adapters`. Weights were not persisted, by
PREREG §2.2 — the readings are the record.
