# PREREG — is the build-variance in the DATA DRAW or the TRAINING DRAW?

**Locked 2026-08-28, before any new adapter is trained.** Descriptive
decomposition plus two screens. Fixed at this commit; later edits are amendments
and say so.

---

## 1 · WHAT IS ALREADY MEASURED

`RESULTS_RECIPE_VARIANCE_2026_08_28.md`: four adapters differing in `--seed`,
which drives **both** the corpus draw and the trainer, gave

```
S_combined = 0.1549      between-adapter sd 0.0700
```

That is the **total** build-variance. It does not say where it comes from, and
the answer governs every future measurement on this pipeline — not just `ki`.

## 2 · THE DECOMPOSITION

**Hold the corpus BYTE-IDENTICAL; vary only the trainer seed.**

| adapter | corpus | trainer seed | status |
|---|---|---|---|
| **s20620 (B-fresh)** | `corpus_bfresh` sha `263fe3c8…` | 20620 | ✅ already trained, 38 exchanges |
| **t30001** | **the same corpus** | 30001 | to train |
| **t30002** | **the same corpus** | 30002 | to train |
| **t30003** | **the same corpus** | 30003 | to train |

`act2_finetune.py --seed` drives the trainer only: LoRA init, data-shuffle order,
dropout. The corpus directory is passed unchanged and its sha is re-pinned on the
box. **Everything else is held**: map, hyperparameters, seq/batch/accum, epochs,
provocation, 40-turn window-1 exchanges.

⇒ `S_training` = spread across those four. Compared against the already-measured
`S_combined = 0.1549`.

### Pre-declared readings

Let `R = S_training / S_combined`.

- **R ≥ 0.7** → ⭐ **the variance is in the TRAINING DRAW** (init / shuffle /
  bf16 non-determinism). The corpus draw contributes little. ⇒ Fixes are
  averaging over trainer seeds, or making training deterministic.
- **R ≤ 0.3** → ⭐ **the variance is in the DATA DRAW** — *which particular
  surfaces the corpus sampled*. ⇒ Fixes are a larger corpus, or pinning the draw
  across arms so both maps see the same surfaces.
- **0.3 < R < 0.7** → both contribute; report the split, claim neither.
- ⛔ **`S_training` > `S_combined`** → the estimate is unstable at k=4 and neither
  number should be quoted as a decomposition. Say so; do not pick the flattering
  reading.

⚠️ `S_combined` was measured over 14–38 exchanges per adapter and `S_training`
will be measured over 14. Within-adapter se was 0.0189 against a between-adapter
sd of 0.0700, so this is not the limiting term — but the comparison is
sd-of-4-means against sd-of-4-means either way, and both carry k=4's wide
uncertainty. **R is a ratio of two noisy quantities and is read as a direction,
not a coefficient.**

## 3 · SCREEN A — does the observable ranking survive fresh builds?

The `$0` screen (`runs/act2/observable_screen.json`) ranked 11 observables by
`contamination = between-build sd / within-conversation movement` on four
adapters. **It has never been tested on builds it did not see.**

Re-run the identical screen including the three new adapters. Pre-declared:

- **`root TTR` stays in the top 3 and `force:ki` stays outside it** → the ranking
  is a property of the observables, not of those four draws. ⇒ The arena
  observable is chosen from the top of that list, pre-registered separately.
- **The ranking reorders materially** → contamination is itself unstable at k=4
  and no observable may be selected on it yet.

⛔ Exploratory-turned-confirmatory **only because the prediction is written here
first**. The original screen was exploratory and stays labelled as such.

## 4 · SCREEN B — coupling, in the only regime where it can exist

⛔⛔ Every transcript to date was `--history-window 1`: each speaker sees only the
previous turn, so convention formation over 40 turns is **architecturally
impossible**. The observed ~0 coupling excess is expected by construction and
rules nothing out.

⇒ **8 additional exchanges per new adapter with ACCUMULATING context** (window
omitted). Each probe run already emits a yoked pair — interacting, and a control
against a pre-recorded partner that never adapts back — so every exchange yields
its own paired live-vs-frozen delta. n = 24 pairs.

Pre-declared, per observable:

- **coupling excess > 0, paired, across adapters** → that observable responds to
  an interlocutor and is a live arena candidate.
- **coupling excess ≈ 0 for ALL observables even with accumulation** → ⛔⛔ a
  foundation finding much larger than any map question: **these models do not
  adapt to each other at all**, and "emergent convention" is not measurable with
  this apparatus regardless of observable. Report it as the headline.
- ⛔ **accumulating exchanges DEGENERATE** → the coupling screen is void for those
  adapters (a degenerate transcript's movement describes the loop). Degeneracy is
  a **reported statistic, never a silent exclusion** — the amendment carried
  forward from the ki-as-target run.

⚠️ 8 exchanges × 3 adapters is small. If coupling excess is positive but the
paired CI includes zero, the verdict is **UNDERPOWERED**, not "no coupling."

## 5 · CARRIED DISCIPLINE

Corpus sha re-pinned on the box (**the same sha as B-fresh's**, which is the whole
point); token gate against run 3; VRAM at the worst observed correction;
`compileall` under the box's Python 3.10 first; raw dump on failure, no `tail` on
attribution-relevant output; **pull the pipeline log before killing the box**;
pull-and-kill at DONE.

⛔ **No throughput branch.** Dropping adapters destroys the estimate, so the cost
is accepted up front. *(Carried from the run where "budget" was a switch, not a
cap.)*

## 6 · WHAT THIS DOES NOT DO

No treatment arm, no map comparison, no stipulation. It does not choose the arena
observable — it tests whether the ranking that would choose one is stable. **It
produces no drift number.** σ_cp remains unmeasured.
