# PREREG — is the `ki` baseline a property of the RECIPE or of the RUN?

**Locked 2026-08-27, before any new adapter is trained.** Descriptive, not a
hypothesis test: it estimates a spread. Everything below is fixed at this commit;
later changes are amendments and say so.

---

## 1 · WHY THIS EXISTS

`RESULTS_KI_AS_TARGET_2026_08_27.md` halted because the control failed:

```
adapter_mt re-served today  0.1190   reproduces its own stored 0.1027 at t +0.62
B-fresh (same map)          0.2520   vs stored              t +6.89   -> HALT
```

⇒ **The measurement is stable; the pipeline's OUTPUT is not.** Everything the
2026-08-26 attribution claimed about `ki`-suppression was measured inside **one
adapter**. This probe asks the prior question: **run the recipe again and what do
you get?**

## 2 · ⭐⭐ THE ATTRIBUTION, MEASURED BEFORE DESIGNING (and it moved the design)

Two facts found at $0, both of which change what "run it again" means:

1. **The trainer seed was HARDCODED** (`seed=20620` inside `TrainingArguments`)
   and the corpus seed defaults to the same value. **B-fresh and `adapter_mt`
   therefore shared a seed.** Their 0.133 gap is *not* seed variance — the seed
   never varied. Now wired to `--seed`.
2. **They nonetheless trained on substantially different corpora.** Same map, same
   generator, same seed, same 1,445 chains, same 15,895 multi-turn rows — but as
   sets the multi-turn rows overlap by only **3,229 of 15,895 (~20 %)**. Code
   changes between 08-26 and 08-27 re-rolled the draw.

⭐ And the current generator **is** deterministic: the box rebuilt
`corpus_bfresh` byte-identical to the local build (sha `263fe3c8…` pinned and
matched). So the corpus is reproducible *given fixed code*, and the observed
divergence was a **re-draw from the same distribution** — which is exactly what
varying `--seed` produces on purpose.

⇒ **Varying the seed reproduces the mechanism that actually differed.** The
originally-requested design survives contact with the attribution.

## 3 · DESIGN

**One map only — `DERIVED_v1`. No treatment arm, no stipulation.** Nothing is
being compared to anything; a spread is being estimated.

| adapter | seed | status |
|---|---|---|
| **B-fresh** | 20620 | ✅ already trained and measured (0.2520, 38 exch) |
| **R1** | 20621 | to train |
| **R2** | 20622 | to train |
| **R3** | 20623 | to train |

`--seed` drives **both** the corpus draw and the trainer, so each run re-rolls what
the recipe re-rolls. Everything else is held: map, chains 1445, turns 12,
multiturn-fraction 0.5 by compute, seq 384, batch 4, accum 4, 2 epochs, lr 1e-4,
rank 32, the same provocation string, 40-turn exchanges at window 1.

⚠️ **`adapter_mt` is NOT in the estimate.** It was built with different code, so it
is not a draw from the same recipe. It is reported alongside as historical context
and labelled as such.

### Exchanges per adapter: **14**, and why fewer than last time

The unit of independence is the **adapter**, so exchanges buy within-adapter
precision, not between-adapter precision — the thing being estimated. At 38
exchanges the within-adapter SE was 0.0702/√38 = **0.0114**; at 14 it is
0.0700/√14 = **0.0187**. Against a spread the size of the observed 0.133, both are
negligible. **Spending the budget on more adapters instead of more exchanges is
the whole lesson of the last run.**

⛔ 40 turns, window 1, unchanged — the protocol must match B-fresh's or the new
adapters cannot be placed on the same scale.

### Measured before the box: the four corpora and their compute

Token gate run locally against run 3 (the tokenizer is the arbiter, not chars):

```
s20620 (B-fresh)  +0.19 %      s20622   -1.34 %
s20621            -0.11 %      s20623   -1.39 %      max spread 1.58 %
```

All four HELD within +/-2 %, no truncation at seq 384 (longest row 330).

⚠️ **The 1.58 % compute spread is IN SCOPE, not a confound.** Re-rolling the seed
re-draws the corpus, and the draw's size is part of what the recipe produces. It
is recorded here so it cannot later be presented as a discovered flaw — but if the
spread S turns out large, compute is one of the named candidates to check against.

## 4 · PRE-DECLARED READINGS

Primary: `P(ki | prior ∈ {ka, ku, kä})` per adapter — the same stratum, so the
numbers are comparable to everything already measured. Expectation 0.20.

Let **S** = the spread (max − min) across the four same-recipe adapters.

- **S < 0.04** → ⭐ the recipe is stable. Then B-fresh vs `adapter_mt` was caused by
  the *code change* between them, not by re-drawing, and `ki`-suppression is a
  real property of a corpus generator that has since changed. Diagnose the code
  delta.
- **0.04 ≤ S < 0.10** → the recipe is moderately unstable. Map experiments remain
  possible but need k ≥ 3 adapters per arm and must be powered over adapters.
- **S ≥ 0.10** → ⛔⛔ **the recipe does not determine `ki`-emission.** The
  2026-08-26 `ki`-suppression finding is a property of one draw, the asymmetry
  mechanism is unfalsifiable by this apparatus, and **no map-level experiment on
  this measure is worth running until the variance source is fixed.**
- ⭐ **Any adapter landing near 0.20** is independently informative: it means
  "suppression" is not the recipe's typical behaviour at all.

### Declared in advance, so it cannot be read as a finding later

- **This probe cannot say the asymmetry mechanism is right or wrong.** It has no
  treatment arm. A stable recipe would *re-enable* the mechanism question; it does
  not answer it.
- **F-LOCAL is neutral**, as before, and is run only to catch a broken adapter
  before exchanges are spent on it.
- **Degeneracy is a reported statistic**, never a silent exclusion — the
  amendment from the last run, carried forward. Every adapter reports its
  distinct-ratio distribution.

## 5 · CARRIED DISCIPLINE

Corpus sha pinned **per seed** and rebuilt on the box; token gate against run 3
**and** across all four corpora at 2 % (a compute difference between adapters
would confound the spread with a budget effect); VRAM at the worst observed
correction; `compileall` under the box's Python 3.10 before anything else; raw
dump on failure, no `tail` on attribution-relevant output; **pull the pipeline log
first**; pull-and-kill at DONE.

⛔ **No throughput branch this time.** The design is 3 trainings + 42 exchanges and
there is no fallback that preserves the estimate — dropping adapters is the one
thing that would destroy it. Cost is accepted up front instead of branched on.
*(Last run's "budget" clause was a switch, not a cap, and the missing third arm
cost ~$13.)*

## 6 · WHAT THIS DOES NOT DO

No treatment arm. No stipulation — `STIPULATED_KI_TARGET_v1` stays discarded.
No `ku→ki` replication. No drift number, no σ_cp. It answers exactly one
question: **does building this model twice give you the same speaker?**
