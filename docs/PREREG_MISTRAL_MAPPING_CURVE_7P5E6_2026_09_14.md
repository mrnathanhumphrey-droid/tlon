# PREREG — the second mapping curve at 7.5e-6: break the collinearity and attribute the inverted U

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `09d4d9df` (sha256[:8] of draft body at lock, 2026-09-14T22:50Z)
- **Date:** 2026-09-14
- **Cell:** `miscurve75-s20624`
- **Fires on:** one full-weight fine-tune of **`mistralai/Mistral-7B-Instruct-v0.3`**,
  `--scope-mode mapping` (**268,435,456** trainable, re-asserted against the real
  header at run time), content-transient corpus `dd40e22f85b0b6e4`, LR **7.5e-6**,
  **one epoch**, with F-LOCAL read in-process **at `miscurve-s20624`'s own
  measured rms values**.
- **Predecessor:** `miscurve-s20624` (`ac255dce`, LR 1e-5) — render inverted U
  `0 → 0 → 6.2 → 51.6 → 34.4 → 26.6 %`, peak 51.6 % at step 940, never clearing
  the 0.90 gate. Valid by its own control (endpoint reproduced `mismap` at 17/64
  and rms to five figures).

---

## 0 · The one question

`miscurve` established the inverted U but **could not attribute it**: within a
fixed-LR run, `rms` and `examples_seen` are **perfectly collinear** — every point
moves both together. So "render peaks at 51.6 % and falls" is a statement about
*that LR's trajectory*, not about the mapping locus.

⭐ **A lower LR reaches any given rms at more examples.** Overlaying the two
curves **at matched rms** separates the hypotheses:

⭐ The two labels below are **names for outcomes this run has not had yet**, not
claims. `settled-claim-ok: pre-declared outcome labels in an unfired prereg — §5
sets the evidence bar each must clear, and §4 names the bias the control cannot
catch.`

| at matched rms | reading |
|---|---|
| render **higher** at 7.5e-6 (more examples) | `settled-claim-ok: outcome label, unfired` **DURATION-LIMITED** — the mapping locus *can* install render; 1e-5's trajectory saturated rms before it had seen enough. The locus is reachable, and a release read there becomes conceivable. |
| render **the same** regardless of examples | **DOSE-BOUNDED** — mapping-only cannot install faithful render past ~51 %. Insufficiency **established** rather than over-read. (B)-supporting for the mapping locus, by *insufficiency*, not destruction. |
| render **lower** at 7.5e-6 | Unexpected — more examples, worse render. Check for a schedule or instrument fault before interpreting anything. |

⛔ **No release verdict.** Render gates, and it clears 0.90 nowhere on
`miscurve`. This run decides whether the locus is *reachable*, which is what
gates whether a release read is ever possible there.

---

## 1 · ⛔⛔ WHY 7.5e-6 AND NOT LOWER — THE OBVIOUS CHOICE CANNOT CONCLUDE

The instinct is "lower LR ⇒ more examples-contrast ⇒ better." **It is wrong, and
computing it before locking is what caught it.** Lower LR buys contrast and
loses *coverage*, and coverage is what decides whether the comparison lands
where the hypotheses differ.

Using `miscurve`'s own fits (`rms ∝ steps^0.144` within a run, `rms ∝ LR^0.298`
across the Qwen pair):

```
LR        rms @ 1 epoch   miscurve render in the reachable band   contrast
3.0e-06   3.6253e-04      0.0 - 0.0 %   (1 matched point)          12.08x
5.0e-06   4.2214e-04      0.0 - 6.2 %   (3)                         4.20x
6.9e-06   4.6467e-04      0.0 - 6.2 %   (3)                         2.16x
8.0e-06   4.8561e-04      0.0 - 51.6 %  (4)                         1.59x
```

⛔⛔ **AT 3e-6 THE COMPARATOR IS PINNED AT ZERO.** One epoch tops out at
`3.63e-4`, and `miscurve`'s render across that whole band is **0.0 % at both
measured points**. Every matched pair would compare against a floor, so
**"dose-bounded" could not fire by construction** — both-zero is uninformative,
not evidence of a bound. A design in which one arm is structurally unreachable
is not a test; it is a run that can only return one answer.

⭐ **7.5e-6 reaches `miscurve`'s peak rms (`4.65e-4`) inside one epoch** — the band
where render is **51.6 %**, i.e. where the two hypotheses actually make
different predictions — with a **1.81× examples contrast** at matched rms. It is
also *shorter and cheaper* than the design it replaces (§8).

⛔ The 12× contrast at 3e-6 is purchasable at **5.64 epochs / ~$16**, and it
would confound LR with the **epochs-lever hypothesis** that §6 deliberately
holds separate. Rejected on both counts.

### ⚠️ 1.1 · THE WHOLE RUN TURNS ON REACHING ONE RUNG, AND THE MARGIN IS THIN

§5 needs **two non-floor matched pairs**, and the second of them is the
`4.6505e-4` rung — `miscurve`'s peak, where render is 51.6 %. Whether one epoch
reaches it is a near-run thing:

```
LR        rms @ 1 epoch   vs the 4.6505e-4 rung   contrast   non-floor pairs
6.9e-06   4.6467e-04      MISSED                   2.16x      1   <- unreadable
7.0e-06   4.6667e-04      +0.3 %                   2.09x      2
7.5e-06   4.7636e-04      +2.4 %                   1.81x      2
8.0e-06   4.8561e-04      +4.4 %                   1.59x      2
```

⛔⛔ **7e-6 WOULD CLEAR THE DECISIVE RUNG BY 0.3 %, AND THAT IS WHY IT IS
REJECTED.** That margin is computed from the very exponent §2 exists because it
cannot be pinned — the same exponent whose plausible range spanned
overlap-to-no-overlap. Betting the run's ability to conclude on a 0.3 % margin
from an unpinnable fit would smuggle the extrapolation-dependence back in at the
single most load-bearing rung, which is precisely what the rms ladder was built
to remove. A 6.9e-6 run misses the rung outright and is UNDERPOWERED by §5.

⭐ **So the LR is chosen for MARGIN, not for contrast: 7.5e-6**, which clears the
decisive rung by **+2.4 %** — an 8× larger margin for a 13 % smaller contrast
(1.81× vs 2.09×). ⛔ Contrast at a rung you miss is worth nothing; slightly less
contrast at a rung you reliably reach is worth everything. The table is recorded
so a MISSED rung would still read as *a known risk*, never as a surprise.

---

## 2 · ⛔⛔ THE READS ARE AT `miscurve`'s OWN rms VALUES, NOT AT A STEP SCHEDULE

**`--dose-curve-targets 3.1205e-4,3.7173e-4,4.1686e-4,4.6505e-4,5.0033e-4,5.1900e-4`**
— **all six** rms values `miscurve` actually measured, not a subset. The top two
are not expected to be reached in one epoch at this LR; they are declared anyway
because an unreached rung simply stays unfired, and choosing which of another
run's measurements to compare against *after* seeing where this one lands is how
a ladder quietly becomes a selection.

⭐⭐ **This makes every reading a matched pair BY CONSTRUCTION.** A *step*
schedule can only reach the comparison by **predicting** where rms will land,
and that prediction rests on an exponent fitted from a two-point Qwen pair whose
one member's step count could not be verified. Across plausible values of it:

```
B=0.144 -> 3e-6 at one epoch tops out at 4.36e-04   overlaps
B=0.298 -> 3e-6 at one epoch tops out at 3.63e-04   overlaps the DEAD band
B=0.500 -> 3e-6 at one epoch tops out at 2.84e-04   NO OVERLAP AT ALL
```

⛔ So a step schedule left the outcome spanning *good comparison* to *no
comparison exists*, decided by a number nobody can pin — and a "degrades
gracefully to UNDERPOWERED" clause would have dressed that up as an acceptable
result. It is not acceptable; it is the run possibly being pointless.

⭐ **With an rms ladder the fit decides only HOW MANY rungs this run reaches,
never WHETHER the comparison exists.** A short run simply reports fewer matched
pairs, each one still exactly matched. `TargetLadder` latches each rung once,
fires every rung a single step crosses, and fires none when the dose is
unmeasurable (`tests/test_dose_curve.py`, 9 assertions). Each reading records
`matched_rms_targets`, so the pair is joinable in the artifact rather than by
eye.

---

## 3 · Configuration

**Epochs: one leg, and `EPOCH_BUDGET=1`. These are one statement, not two
facts.** The run trains exactly one epoch and the pipeline enforces exactly one
— the defect-3 lesson (`8905a45`, *"a run may not buy an epoch its
pre-registration did not declare"*), which arose precisely because a declared
count and an executed count were two separate statements that drifted.

| field | value | why |
|---|---|---|
| **base** | `mistralai/Mistral-7B-Instruct-v0.3` | as `miscurve` |
| **LR** | **7.5e-6** | §1 — reaches the informative band in one epoch |
| **EPOCH_BUDGET** | **1** *(declared here = enforced there)* | §3 above |
| **scope** | `mapping`, 268,435,456, untied | re-asserted at run time |
| **rms ladder** | `3.1205e-4, 3.7173e-4, 4.1686e-4, 4.6505e-4, 5.0033e-4, 5.1900e-4` | §2 — `miscurve`'s own measured values |
| **step reads** | 5, geometric | kept as trajectory context; the ladder carries the comparison |
| **corpus** | `dd40e22f85b0b6e4`, sha-verified | mismatch aborts |
| **card** | `gpu_1x_h100_pcie`, us-west-3 | matched to `mismap`/`miscurve`; SXM5 only if capacity forces, reason recorded |
| **attention** | `eager`, resolved kernel printed | demonstrated clean on Mistral twice |
| **seq / batch / accum** | 384 / 4 / 4 | unchanged, so **LR is the only intended difference from `miscurve`** |

---

## 4 · ⛔ THE CONTROL IS WEAKER THAN `miscurve`'s, AND HERE IS EXACTLY HOW

`miscurve`'s endpoint had a **known prior point to reproduce** (`mismap`'s
17/64), so a run that was subtly wrong would have missed it. **There is no prior
7.5e-6 mapping run**, so this run's control is **internal trajectory
consistency**: the endpoint must sit on its own curve, and achieved rms must
track the ladder crossings coherently.

⛔⛔ **WHAT THAT CONTROL DOES NOT COVER: a systematic bias.** A fault shifting
*every* reading by the same amount would sit **perfectly on its own trajectory**
and pass. `miscurve`'s control could catch that; this one cannot. So a
`DOSE-BOUNDED` reading here — "render is the same at matched rms" — is exactly
the pattern a uniform downward bias would also produce, and it is the arm this
control is least able to defend.

⭐ Two partial mitigations, neither a substitute: the machinery is byte-identical
to the run that *did* reproduce a known point, and `isolated_read` is
demonstrated empirically rather than assumed. ⛔ Recorded as a named limitation
of this run, to be quoted with any DOSE-BOUNDED conclusion.

---

## 5 · Pre-declared reading

Join the two curves on `matched_rms_targets`. **≥2 matched pairs at rms ≥
4.1686e-4** (where `miscurve`'s render is non-zero) are required for §0's table
to be read at all; below that the comparison sits against a floor and §1's
objection applies to *this* run too.

⛔ **UNDERPOWERED** — fewer than two non-floor pairs → report the 7.5e-6 curve
alone, locus-versus-trajectory unresolved. Declared so a thin overlap is never
read as a null.
⛔ **VOID** — endpoint off its own trajectory (§4), non-finite, `DIVERGED`,
`MAPPING_FROZEN`, `MAPPING_UNVERIFIED`, or `EvalContaminatedTraining`.
⛔ **No threshold moves.** `0.90` is `NATIVE_THRESHOLD`, imported.

---

## 6 · Carried, not re-litigated

- **Dose is nearly pinned** (`steps^0.144`, `LR^0.298`) — which is *why* varying
  examples-at-matched-rms requires changing LR at all, and why the reachable
  band moves so much for so little LR.
- **rms is not cross-scope comparable in examples-terms** (the layer-rung dose
  landed at 2.8 % of an epoch on mapping scope). ⭐ This run compares **within
  mapping scope, across LR**, so that caveat does not bite here — it still
  stands on any mapping-versus-layer claim.
- **The epochs-lever hypothesis** (`miscurve`'s unregistered epoch 2 moved lag2
  8.87 → 7.53 and lag3 under the ceiling) is **not tested here** — single epoch
  by §3. ⭐ If this run reads DURATION-LIMITED (an outcome label, §0;
  `settled-claim-ok: conditional reference to an unfired outcome, not a claim
  that it obtained`), that hypothesis gains force and needs its own prereg.

---

## 7 · Provenance and operational

`verified_prereg_id()` re-hashed, refusing on mismatch. Cell `miscurve75-s20624`
asserted unused. `base_audit` and `eos_guard` before training. Watchdog armed
first. Deduplicated capacity floor. Corpus sha-verified.

⭐ **The curve reaches durable storage by design, not by accident** — `flush`
now sweeps `dose_curve_*.jsonl` and runs from a `trap` on every exit path
(`fb7962f`), which is the fix for `miscurve`'s curve reaching no hub at all.
Call-site coverage and `EPOCH_BUDGET` are in the same commits.

**Cost: ~0.9 h training plus ~35 min of reads ≈ $6**, at $3.29/h. ⭐ The
rejected 3e-6 design cost the same and could not conclude; the 5.64-epoch
version cost ~$16 and would have confounded the epochs lever.

---

## 8 · What this run does NOT do

- ⛔ Does not produce a mapping-rung release verdict (§0).
- ⛔ Does not change any threshold.
- ⛔ Does not test the epochs-lever hypothesis (§6).
- ⛔ Does not claim a control by reproduction — internal consistency only, blind
  to systematic bias (§4).
- ⛔ Does not read §0's table on fewer than two non-floor matched pairs (§5).
- ⛔ Does not vary anything but LR from `miscurve`.
