# RESULTS — the path to a dose matters: render depends on the learning rate beyond dose and examples

**Cell `miscurve75-s20624`** · `mistralai/Mistral-7B-Instruct-v0.3` · mapping scope
**PREREG `09d4d9df`** · pinned `4a40107` · H100 PCIe / us-west-3 · ~2.4 h · **~$7.70**

⭐⭐ **A THIRD MECHANISM, UNANTICIPATED BY THE DESIGN.** The collinearity broke as
intended — and a new variable appeared behind it.

---

## 1 · The curve, and the matched-rms pairs

The reads fired at `miscurve`'s own measured rms values, so every pair is matched
**by construction** rather than by prediction. Matching held to five decimals
(target `4.6505e-04`, achieved `4.65082e-04`).

```
  step examples          rms    speak   render
   151     2416   3.1243e-04    15.6%     0.0%
   235     3760   3.4769e-04    28.1%     0.0%
   341     5456   3.7182e-04    28.1%     0.0%
   470     7520   3.9226e-04    62.5%     0.0%
   669    10704   4.1689e-04    81.2%    14.1%
   940    15040   4.4056e-04    87.5%    12.5%
  1439    23024   4.6508e-04    96.9%    14.1%
  1880    30080   4.7766e-04    98.4%    26.6%   <- peak
  3759    60144   4.9610e-04   100.0%    17.2%
```

| rms rung | `miscurve` 1e-5 | `miscurve75` 7.5e-6 | direction |
|---|---|---|---|
| 3.1205e-04 | 1,712 ex · 0.0 % | 2,416 ex · 0.0 % | ⛔ floor, uninformative |
| 3.7173e-04 | 3,760 ex · 0.0 % | 5,456 ex · 0.0 % | ⛔ floor, uninformative |
| **4.1686e-04** | 7,520 ex · **6.2 %** | 10,704 ex · **14.1 %** | **HIGHER** |
| **4.6505e-04** | 15,040 ex · **51.6 %** | 23,024 ex · **14.1 %** | **LOWER** |

§5's bar of two non-floor pairs was met. ⛔ **They point opposite ways.**

## 2 · ⭐⭐ The finding — POST-HOC, no row pre-declared it

Both curves are inverted U. **The lower-LR run peaked at 26.6 % against the
higher-LR run's 51.6 %**, despite ~1.5× more examples at matched dose.

That is **neither** pre-declared outcome:

- **not DURATION-LIMITED** (one pair; its interval is below) — more examples did
  not help at the decisive rung, it hurt;
- **not DOSE-BOUNDED** — render was not *the same* at matched rms, it was *lower*.

⛔ Both rest on **one** matched pair, so the interval belongs on it: at the
decisive rung `4.6505e-04`, render is **51.6 % ± 12.2 pp** against **14.1 % ±
8.5 pp** (95 %, n=64 each). Non-overlapping — the *difference* is established.
**The two-mechanism reading of it is not**: three mechanisms are now in play and
this design separates none of them.

⭐ So: **the same weight displacement, reached in smaller steps, produced a
materially worse speaker.** The *path* to a dose matters, not only the dose or
the example count. Three mechanisms are now in play — dose, duration, and
LR-path — and the two-curve design cannot separate all three.

⛔⛔ **LOCUS-VERSUS-TRAJECTORY REMAINS UNRESOLVED.** The collinearity broke and a
third variable surfaced behind it. Nothing here establishes whether the mapping
locus is reachable; "at what LR" is now a free parameter nobody has mapped.

⛔ Held as post-hoc. §0's third row governed (*"more examples, worse render —
check for an instrument fault before interpreting"*), and that check was done: §3.

## 3 · ⛔ The §4.1 fault that halted this run is FALSE, and the curve proves it

The run exited **rc=3 inside `train_leg1`** on `§4.1 WEIGHT DELTA:
INSTRUMENT_FAULT — the weights did not move`, before F-LOCAL, lag or verdict ran.

⭐ **The run's own curve refutes it**: rms climbed monotonically
`3.1243e-04 → 4.9610e-04` and speak went `15.6 % → 100.0 %`. **A model whose
weights did not move cannot do that.**

⭐⭐ **And the pooled statistic is a CONSTANT OF THE SCOPE.** `fraction_changed`
came back **0.51220703125 = 1049/2048 leaves at every one of the fifteen reads
across both runs** — two learning rates, rms `3.12e-04 → 5.19e-04`, speak
`15.6 % → 100 %`. It never moved once. ⛔ The number the §4.1 test reads is fixed
by which leaves the mapping scope touches; it carries **no information about
whether training happened**. The two runs drew different verdicts
(`UNDISCRIMINATING` at 1e-5, `INSTRUMENT_FAULT` at 7.5e-6) only because the
LR-derived *threshold* swept past a number that was standing still.

It is the invalid pooled test again, now in its worse form. At 7.5e-6 the
absorbable ceiling falls to `1.92e-3`, the dead-zone prediction drops under 0.5,
the pooled test starts *discriminating* — and lands on FAULT for a healthy
mapping run. This is the false positive that was predicted before the 5e-6
dial-back was rejected — and it is now **observed** rather than derived: the
statistic sat at `0.51220703125` while the threshold moved beneath it.

## 4 · ⛔⛔ The fourth instance of one wiring class

The §4.1 fix went into `act2_fullft_verdict.py` (`757c157`), and
`tests/test_call_site_coverage.py` was written to stop this class recurring — by
**enumerating the verdict call sites** (`fb7962f`). The identical gate in
`act2_finetune.py` was never touched, so the false FAULT fired *in the trainer*
and halted the run before any verdict could apply the fix.

⭐⭐ **The lesson is about the test, not the bug.** An author-maintained list of
call sites catches partial wiring *only among the sites the author already
remembered*, and the bug is always the site they did not. **The list and the
wiring share one blind spot** — which is why the list caught three instances and
missed the fourth.

**Fixed structurally** (uncommitted at time of writing):

- `POOLED_INVALID_FOR_MAPPING` defined **once** in `weight_delta.py`; the trainer
  and the verdict both import it, so they cannot drift again. `DIVERGED` is
  excluded, because `NaN != NaN` makes a destroyed leaf count as *changed*.
- The trainer **defers** rather than halts in mapping scope — recorded as
  `pooled_deferred_to_per_leaf`, and explicitly *not* a pass.
- `tests/test_gate_sites_are_found_not_listed.py` **AST-scans every module** for
  any `if` branching on a delta-verdict constant, under every import alias, and
  requires each to consult the shared exemption. ⭐ Mutation-tested two ways:
  reverting the trainer fix is caught, **and so is a gate added in a file named
  in no list anywhere** — the property the old test could not have at any length
  of list.

## 5 · ⭐⭐ Two fixes validated on a live failure

**The flush trap.** The run died on a branch that exits before any persist —
precisely the shape that lost `miscurve`'s curve entirely. This time:

```
=== [flush_measurement] 01:24:51 · exit rc=3 ===
  flushed dose_curve_miscurve75-s20624.jsonl -> hf://...
```

**All 9 readings reached the hub from the failure path, by design.** `fb7962f`
is proven on the failure it was built for, not only in tests.

**The margin call.** 7.5e-6 over 7e-6 was chosen so the decisive rung cleared by
+2.4 % rather than +0.3 %. The fit turned out **4.1 % low** (endpoint
`4.9610e-04` against a predicted `4.7636e-04`), so 7e-6 would have cleared too —
unknowable pre-run, and choosing margin against an unpinnable exponent was right
on the information available.

## 6 · ⚠️ The strategic observation, standing on five runs

**The mapping locus has produced zero verdicts and four confounds** — over-dose,
then collinearity, then LR-path, with the pooled §4.1 test invalid throughout.
Every control surfaced a new variable. The **layer** rung produced a clean
verdict on the *first* attempt per base once the harness was right.

⭐ That asymmetry is itself a datum: the mapping locus behaves like a genuinely
multivariable system where the layer locus behaved like a one-dimensional one.
⛔ Whether that is a fact about the locus or about our instruments is **not
established**.

Resolving reachability now needs an (LR × dose × examples) sweep — plausibly
6–10 runs at ~$8, so **$50–80** — against a layer-rung n=2 already in hand
(Qwen and Mistral, both floored, both faithful, both dose-matched). ⛔ A
recommendation, not a decision: bank the layer result and the
confound-proneness observation, and hold the mapping locus unless the art-piece
decision turns on it specifically.

## 7 · ⏭ Open

1. The (LR × dose) sweep, if the mapping locus is worth it (§6).
2. **The epochs-lever hypothesis** — still untested, still the only signal
   pointing toward release *installing* (`RESULTS_MAPPING_DOSE_CURVE_2026_09_14.md` §5).
3. `pipeline_fullft_read.sh` remains Qwen-hardcoded.
4. Two results docs from consecutive days both read as entry points; the
   `START=` chain needs one door.
