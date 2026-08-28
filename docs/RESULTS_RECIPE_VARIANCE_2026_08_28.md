# RESULTS — the recipe does not determine `ki`-emission. **S = 0.1549.**

Prereg `docs/PREREG_RECIPE_VARIANCE_2026_08_27.md`, sha256 `76de343c…`, locked
before any new adapter existed and hash-verified on the box at clone time.
Box `4153e748…`, ~14h30m, terminated. All artifacts pulled and md5-verified.

---

## THE VERDICT

**⛔⛔ THE RECIPE DOES NOT DETERMINE `ki`-EMISSION.** `S = 0.1549`, against a
pre-declared unstable band of `≥ 0.10`.

Four adapters, **one map**, same hyperparameters, same generator, differing only
in `--seed` (which drives both the corpus draw and the trainer):

| adapter | k | mean | sd | se | pooled | global `ki` | degenerate |
|---|---|---|---|---|---|---|---|
| s20620 (B-fresh) | 38 | **0.2520** | 0.0702 | 0.0114 | 0.2489 | 0.1984 | 0 |
| s20621 | 14 | **0.0971** | 0.0542 | 0.0145 | 0.0990 | 0.0952 | 0 |
| s20622 | 14 | **0.2368** | 0.0994 | 0.0266 | 0.2344 | 0.1886 | 0 |
| s20623 | 14 | **0.2071** | 0.0867 | 0.0232 | 0.2033 | 0.1758 | 0 |

```
SPREAD S = 0.1549      min 0.0971 · max 0.2520 · k = 4 adapters
between-adapter sd 0.0700   ·   mean within-adapter se 0.0189   ·   ratio 3.7×
```

⭐ **The 3.7× ratio is what makes this a result rather than noise.** The variation
*between* adapters is nearly four times the sampling error *within* one. More
exchanges per adapter would not have shrunk it — it is not a precision problem.

## ⛔⛔ SUPPRESSION IS A MINORITY OUTCOME, NOT THE RECIPE'S BEHAVIOUR

Ordered, with the historical adapter alongside:

```
s20621        0.0971   ⟵ "suppressed"
adapter_mt    0.1027   ⟵ "suppressed"   (HISTORICAL, different code, not in S)
s20623        0.2071   ⟵ at expectation
s20622        0.2368
s20620        0.2520
                0.20  = the corpus expectation on these rows
```

**Two of five builds suppress `ki`. Three sit at or above the 0.20 expectation.**
The 2026-08-26 headline — *"the model will not ask"* — described one of the two.
Had the first multi-turn adapter drawn a different seed, the entire `ki`
investigation would never have been opened.

⇒ The pre-declared side-reading fired: `s20623` lands within 0.03 of expectation,
which the prereg named in advance as meaning *"suppression is not the recipe's
typical behaviour."*

## WHAT THIS DOES TO THE PRIOR WORK

- ⛔ **`docs/KI_ATTRIBUTION_2026_08_26.md` is now a description of `adapter_mt`,
  not of Tlön.** Its internal findings stand *for that adapter* — the ka-coupling
  (p .00945, 12/14 exchanges) and the window dependence (+4.1 SD) were measured
  correctly. **They are not properties of the architecture, the map, or the
  corpus design.**
- ⛔ **The asymmetry mechanism is UNFALSIFIABLE by this apparatus.** Not refuted —
  *untestable*, because the noise floor exceeds the effect any single-adapter
  contrast could show.
- ✅ The `ki`-as-target HALT was **correct and for the right reason**. Its
  reproduction check caught exactly this, one run earlier, for the price of one
  extra inference-only arm.

## THE NAMED CONFOUND, CHECKED

The prereg recorded the corpora's 1.58 % compute spread as *in scope* and named
it as the thing to check if `S` came back large. It does **not** explain the
result:

```
s20620  compute +0.19 %   ki 0.2520
s20621  compute −0.11 %   ki 0.0971     ⟵ nearly identical compute to s20620,
s20622  compute −1.34 %   ki 0.2368         wildly different ki
s20623  compute −1.39 %   ki 0.2071
```

The two adapters closest in compute are the two furthest apart in `ki`. No
monotone relationship. **Corpus size is not the variance source.**

## ⭐⭐ WHAT ANY FUTURE MAP EXPERIMENT NOW COSTS

Given between-adapter sd **0.0700**, to detect a map effect at 80 % power:

| effect to detect | adapters/arm | trainings | GPU-hours |
|---|---|---|---|
| 0.15 | 4 | 8 | ~29 |
| **0.10** | **9** | **18** | **~65** |
| 0.08 | 13 | 26 | ~94 |
| 0.05 | 32 | 64 | ~230 |

⛔ **The `ki`-as-target probe used ONE adapter per arm.** It would have needed
**nine** to resolve the effect it was looking for. It was never going to work,
and no amount of exchanges could have saved it — which is precisely what
"the unit of independence is the training run" means in money.

## WHAT HELD

- Three corpora rebuilt **byte-identical** to the local build (all SHAs pinned).
- Token gate: all four within ±2 % of run 3, verified **locally before the box**.
- All three trainings clean: 3h36m / 3h33m / ~3h33m; train_loss **0.2369 /
  0.2375 / —**, against B-fresh's 0.2369. ⭐ **Near-identical loss across four
  draws that differ by 0.155 in behaviour** — loss is blind to this entirely.
- F-LOCAL tripwire cleared on all three (render 0.938 / 0.953 / 0.922 at n=64,
  speak 1.000). Grammatical competence is *stable* even where force-emission is
  not.
- **0 degenerate exchanges in 80/80 derived-map exchanges ever run.** Only the
  stipulated map has ever degenerated (6 of 38).

## OPEN

1. ⛔⛔ **Find the variance source before any further map work.** Named
   candidates, none tested: LoRA init draw; data order (the shuffle differs when
   the row count differs); which specific surfaces the corpus drew; bf16
   non-determinism. The cheapest discriminator is **same corpus, different
   trainer seed** — one knob, and it separates data-draw from training-draw.
2. **Or change the measure.** `ki`-emission may simply be a high-variance
   statistic. A quantity that is stable across builds would let map experiments
   proceed at 1 adapter/arm. Nothing says the force marginal is the right
   observable — it was chosen because it was the one that moved.
3. ⛔ **`ku→ki` stays unspent.** It is the pre-named replication and there is
   nothing yet to replicate.
4. **The arena is still gated.** Two models "developing a convention" is
   indistinguishable from two models that were built differently — which is now
   measured, not feared. **Still no drift number. σ_cp has never been measured.**
