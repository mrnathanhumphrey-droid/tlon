# RESULTS — the `ki`-as-target mechanism probe. **HALTED.**

Prereg `docs/PREREG_KI_AS_TARGET_2026_08_26.md`, sha256 `9b21976c…`, locked before
any treatment corpus existed and hash-verified on the box at runtime.
Commitment `61059a06…`. Box `42269df0…`, **15h31m, ≈$30.90**, terminated.

---

## THE VERDICT

**HALTED at check 3 of 5. The treatment arm was not scored, by pre-declaration.**

The probe cannot answer the mechanism question, because **its own control failed**
— and the reason it failed is the most important thing this run produced.

## THE ORDERED CHECKS, AS LOCKED

| # | check | result |
|---|---|---|
| 1 | **COMMITMENT** — every scored arm carries the commitment sha; count == committed N | ✅ 90/90 arms carry `61059a06…`; 3 timing exchanges carry `None` and are rejected by the same mechanism |
| 2 | **HARNESS** — `adapter_mt` re-served reproduces its stored 14 | ✅ Δ +0.0162, **t +0.62** |
| 3 | **REPRODUCTION** — B-fresh reproduces the known suppression | ⛔⛔ Δ **+0.1492**, **t +6.89** → **HALT** |
| 4 | VARIANCE | same-map \|Δ\| **0.1330** vs map effect \|Δ\| **0.0309** |
| 5 | RELIEF | **NOT READ** |

## THE NUMBERS

Primary measure `P(ki | prior ∈ {ka, ku, kä})` — rows uniform in **both** maps,
corpus expectation **0.20** in both arms, stipulated row `ko` excluded.

```
B-fresh    38 exch   mean 0.2520  sd 0.0702   pooled  273/1097 = 0.2489
T          38 exch   mean 0.2829  sd 0.1027   pooled   228/829 = 0.2750
B-prior    14 exch   mean 0.1190  sd 0.0700   pooled    47/409 = 0.1149
stored-14  14 exch   mean 0.1027  sd 0.0689   pooled    41/408 = 0.1005
```

## ⭐⭐ WHAT ACTUALLY HAPPENED — AND WHY IT MATTERS MORE THAN THE RELIEF NUMBER

**The measurement is stable. The training is not.**

- `adapter_mt` re-served today reproduces its own stored result to **t +0.62**. The
  harness, the prompt, the window, the scoring — all reproduce.
- A **fresh training on the same map, the same hyperparameters, and a corpus
  matched to 0.19 % on tokens** produces **0.2520** where the stored model produces
  **0.1005**. That is **t +6.89**.

⇒ **`ki`-suppression is not a stable property of the map and corpus. It is
substantially a property of a particular training run.** One run suppressed `ki`
hard; another, built the same way, did not suppress it at all — B-fresh sits
*above* the 0.20 expectation.

⛔⛔ **THIS RETROACTIVELY UNDERCUTS THE PREMISE THE PROBE WAS BUILT ON.** The
2026-08-26 attribution said *"the model will not ask"* and treated `ki`-suppression
as a property of the architecture. It was measured entirely within **one adapter**.
Tests B, C and E remain internally valid *for `adapter_mt`* — the ka-coupling
(p .00945, 12/14 exchanges) and the window dependence (+4.1 SD) are real facts
about that model. **What is now unsupported is that they generalise beyond it.**

## ⭐⭐ THE ARM THAT CAUGHT IT WAS THE ONE ADDED TO THE SPEC, AND IT WAS NEARLY FREE

`B-prior` — `adapter_mt` re-served as a run-to-run variance control — was **not in
Nate's spec**. It was added because "two trainings are never identical" was
otherwise an *assumption*, and inference-only made it cost ~1 h of a 15 h box.

**Without it this run would have reported:** *"relief +0.0309, below the committed
MDE 0.060 ⇒ UNDERPOWERED."* Tidy, defensible, and **wrong-headed** — it would have
filed a broken baseline under "we needed more exchanges," and the next move would
have been to buy more of the same. Nate's ratification named the exact failure
mode: *"if the relief signal is small, run-to-run variance could swamp or
manufacture it."* It swamped it, by **4.3×**.

## THE TREATMENT DID TAKE — THE NULL IS NOT "TRAINING FAILED"

Stratified by prior force:

```
 prior │  B-fresh        T        Δ
    ka │   0.2210   0.2737   +0.0527
    ki │   0.0000   0.0000   +0.0000   (forced, both maps)
    ko │   0.2116   1.0000   +0.7884   ⛔ STIPULATED — excluded from the measure
    ku │   0.2907   0.1859   −0.1048   ⚠️ moved the WRONG way
    kä │   0.3072   0.3300   +0.0229
```

`ko → ki` at **1.0000** is the stipulation reproducing perfectly: the corpus and
the training took, exactly as designed. ⭐ And it is a clean demonstration of why
that row is excluded — including it would have shown "relief" of +0.79 that is
**pure construction**.

⚠️ Within the treatment arm the common rows **disagree in direction** (`ku` moves
−0.105 while `ka` moves +0.053), which is what a noise-dominated contrast looks
like.

## ⛔⛔ A SECOND UNSPECIFIED-CASE HOLE, IN THE SAME RUN

`treat_23` came back **degenerate** (18/40 distinct). The degeneracy gate said
*refuse it*; the count lock said *the arm must have exactly the committed 38*. Two
guards, each correct alone, with **no specified behaviour for a legitimately
generated exchange that degenerates**. The analyser refused the whole run.

Same class as the budget-vs-cap hole earlier the same day: **an unspecified case in
a branch clause, filled by whatever was written literally.** Twice in one run.

**Resolution (post-hoc, labelled):** degeneracy became a *reported statistic and a
sensitivity arm*, never a silent exclusion — the committed N is what the primary
analysis reports, because "it looked degenerate" is not a distinction the lock can
verify, and dropping to taste is the optional stopping the lock exists to prevent.

⚠️ And the threshold was **knife-edge on this data** — the treatment tail runs
`0.450, 0.450, 0.500, 0.825, 0.850, 0.975`, so a hard cut at 0.50 decides 36 vs 37
vs 38 by a rounding. Sensitivity, all three ways:

```
PRIMARY  all 38 (committed)   relief +0.0309   t +1.53   BELOW MDE
sens     excl. dr < 0.50      relief +0.0263   t +1.27   BELOW MDE
sens     excl. ANY repeat     relief +0.0174   t +0.82   BELOW MDE
```

The exclusion choice does not change any verdict. The hole was real; on this data
it was **moot**.

## ⭐ A SEPARATE FINDING, NOT IN THE PRIMARY MEASURE: THE TREATMENT ARM DEGENERATES

```
B-fresh   38/38 at distinct-ratio 1.000   (zero repeats, ever)
B-prior   14/14 at 1.000
T         6 of 38 below 1.000: 0.450, 0.450, 0.500, 0.825, 0.850, 0.975
```

**The stipulated map degenerates and the derived map never does.** Mechanistically
plausible: `STIPULATED_KI_TARGET_v1` makes two of five rows deterministic, so
`ko → ki → ka` is forced for two steps and the reachable trajectory space
contracts (stationary ka .375 / ki .250 / ko .125 / ku .125 / kä .125 against the
derived map's .333 / .167 / .167 / .167 / .167).

⚠️ **Reported as an observation, not a result.** It was not pre-registered, n is
small, and it is confounded with the same training-run variance that halted the
probe. But it is a concrete cost of adding forced cells, and it bears on map
design directly.

## WHAT HELD

- Corpora rebuilt **byte-identical** to the local build (both SHAs pinned).
- Token gate: baseline +0.19 %, treatment +0.04 % against run 3; **arms within
  0.1557 % of each other** — the map effect cannot be confounded with a
  training-budget effect.
- VRAM 26.2 raw × 1.253 worst factor = **32.8 GiB against a 40 GiB wall**.
- Both trainings clean and near-identical: 3h37m each, train_loss 0.2369 / 0.2348,
  eval_loss 0.2083 / 0.2064.
- F-LOCAL both clear, and the **pre-declared neutrality held** this time:
  B-fresh 97.3 / 100.0 / 55.9, T 97.7 / 100.0 / 57.8.
- The **ordering lock worked on live data**: 90 scored arms carrying the
  commitment sha, 3 timing exchanges carrying `None`.

## OPEN

1. ⛔⛔ **The mechanism question is unanswered and cannot be answered by this
   design.** With same-map training variance at 0.133 and the expected map effect
   near 0.10, a two-adapter contrast is underpowered *in principle*, not for want
   of exchanges. **Any future version needs multiple training seeds per arm**, and
   the power calculation must be over *training runs*, not exchanges — the unit of
   independence moved again, one level up. This is the same lesson as
   transitions-vs-exchanges, and I got it wrong at the next level up.
2. **Re-open whether `ki`-suppression is real at all.** It reproduces within
   `adapter_mt` and vanishes in a fresh build. Cheapest honest test: train k ≥ 3
   adapters on the *derived* map alone and measure the spread of
   `P(ki | common)`. No treatment arm, no stipulation — just: **is the baseline a
   property of the recipe or of the run?**
3. **The stipulation is discarded**, as pre-declared, regardless of outcome.
   `STIPULATED_KI_TARGET_v1` was a probe instrument and remains one. `ku → ki`
   stays pre-named as the replication and is **not** worth spending until (2)
   resolves.
4. **Still no drift number.** σ_cp remains downstream and unmeasured.
