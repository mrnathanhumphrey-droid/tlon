# PRE-REG — 2b: can a small from-scratch listener resolve reference in a nounless impression language?

- **Date:** 2026-08-19
- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `612f37ba` (sha256[:8] of draft body at lock, 2026-08-19T22:08Z)
- **Arc:** Tlön phase 2b (extends `docs/VERDICT_2A_PLUMBING_2026_08_18.md`)
- **Lexicon:** `49475a61a308a2beeb7434693eff5c44` · **Referents:** 20 Tier-1, REVIEWED

## One-line hypothesis

A **from-scratch** transformer encoder (~5 M params, morpheme-per-token vocab)
trained on 2a's sampler output can resolve **scene → referent** over the 20
Tier-1 pegs, and — the load-bearing half — **its errors concentrate on exactly
the pairs that targeted structural reachability predicts** (01+12 39 %, 06+08
53 %, 14+15 46 %, 05+11 43 %).

The second clause is what makes this a test rather than a demo. An accuracy
number alone is uninterpretable here; a **predicted error structure** is not.

## Falsifier (pre-registered kill conditions)

- **KILL — TASK IS TRIVIAL.** If a **bag-of-roots** classifier (multiset of root
  morphemes only; no order, no structure, no relators, no aspect) reaches within
  **2 points** of the transformer, then the task is solved by root identity
  alone and the model has demonstrated nothing about reference resolution.
  **This is the live risk**, pre-flagged in the 2a verdict: signatures are
  nearly disjoint under natural generation (0.38 % ambiguity), so the decision
  boundary may be clean enough that structure is irrelevant.
  → Report as "the 20-peg set is root-identity-solvable"; the referent set needs
  harder pegs before any listener result means anything.
- **KILL — NO PREDICTED ERROR STRUCTURE.** If Spearman ρ between per-pair
  confusion rate and per-pair targeted reachability is **≤ 0.3** or its
  permutation-null p **> 0.05**, the "errors land where signatures overlap"
  claim is falsified. Accuracy would then be a bare number with no mechanism
  behind it, and must be reported that way.
- **KILL — LEAKAGE.** If test accuracy drops by **> 10 points** when the split
  is deduplicated by canonical `utterance_id`, the headline number was
  memorisation of near-duplicates, not resolution.

## Priors to lose (pre-register against)

- **My own prior:** that the model will beat bag-of-roots. It may not, and 2a
  already gave a reason to doubt it. Writing it down so a tie cannot be
  retrospectively reframed as expected.
- **That accuracy implies communication.** It does not. A high number under a
  near-disjoint compat relation is closer to a lookup than to pragmatics.
- **That 01/12 confusion would be a model failure.** It is *predicted*. If the
  model separates them cleanly, that is evidence the pegs are more individuated
  than structure suggests — an interesting result in the opposite direction, not
  a better one.

## Must-beat baselines

1. **Majority class** — 5.0 % (20 balanced classes). Floor.
2. **Bag-of-roots logistic regression** — the real baseline. See KILL 1.
3. **Shuffled-label null** — must land at chance; if it does not, the pipeline
   leaks.
4. **Structural compat (2a's matcher)** — ~100 % by construction. This is the
   **CEILING, not a baseline**: it reads the signature the data was generated
   from. Reported for scale only; beating it is impossible and matching it is
   not impressive.

## Method

1. **Data.** Sample per referent with `blend_p=0.6` so overlap regions are
   represented — the whole reason section A widened the sampler. Balanced,
   N = 4 000/referent, 80 000 total. Deduplicate by canonical `utterance_id`
   **before** splitting.
2. **Tokenizer.** Morpheme-per-token: ~234 atomic tokens + `[PAD] [CLS]`.
   Aspect words tokenize as `(root, reps)` pairs, not as one symbol per
   reduplication count, so the ordinal scale stays learnable.
   ⚠️ **Provisional** — Nate has prior tokenization studies not yet located;
   this choice is revisable and the prereg must be re-locked if it changes.
3. **Model.** Transformer encoder, d_model 256, 6 layers, 8 heads, max 26
   tokens, `[CLS]` → 20-way head. ≈ 5 M params. Random init, **no pretraining**.
4. **Train.** Local, RTX 5070 Ti. AdamW, cosine schedule, early stop on val.
5. **Evaluate.** Accuracy + per-pair confusion; correlate confusion against the
   reachability matrix from `tools/ambiguity_report.py`.

## Confound controls (pre-registered)

- **Dedupe by `utterance_id` across splits.** Canonical, not surface — permuted
  orientations are the same utterance (spec §6) and would otherwise leak.
- **Two splits, both reported.** (a) random; (b) **novel-decoration**: test
  scenes carry aspect/degree/modal combinations unseen in train. (b) is the
  honest one; a gap between them measures memorisation of decoration.
- **Balanced classes**, so accuracy is not carried by a frequent peg.
- **⭐ CIPHER-CONTROL BASELINE — run it now, while we know there is no cipher.**
  2b's generator is the *random sampler*, not a learned policy, so nothing is
  optimising against the listener and **no cipher can form by construction.**
  That makes 2b the only clean opportunity to measure what channel-scrambling
  does to a system known to be honest. Scramble each non-semantic channel in
  turn (aspect reps, illocutionary coda, orientation order) and record the
  accuracy drop. Those numbers become the **null band** against which phase 3's
  drops are judged. Without measuring it here we would have no idea what a
  clean system looks like under the test.
  Method adopted from `COSINE_GEOMETRY_OF_INTERFERENCE_2026_07_11.md:308`,
  where equalising label tokens collapsed an apparent cosine structure.

## Stats

Bootstrap 95 % CI over the test set for every accuracy. Spearman ρ for the
confusion/reachability correlation with a **permutation null** over pair labels.
Paired comparison against bag-of-roots on the **same** test items, reported as a
difference with CI — not two independent numbers.

## Cost / lane

**Local, ≈ $0.** ~5 M params on ≤ 26-token sequences; minutes on the 5070 Ti.
No Lambda. If it needs Lambda, that is itself a finding worth stopping on.
Ledger row required regardless: `date,instance_id,type,rate_c_per_hr,minutes,cost_usd,note`.

## Standing floor (reportable regardless)

- **Hypothesis holds:** reference resolution in a nounless impression language
  is learnable from scratch at ~5 M params, with an error structure predicted in
  advance by the grammar's own overlap geometry. Plus a measured null band for
  the cipher control.
- **KILL 1 fires (bag-of-roots ties):** the 20-peg set is root-identity-solvable.
  That is a **direct, actionable finding about the referent set** — it says the
  pegs need to share more roots before a listener test is meaningful, and it
  arrives for $0 before any backbone is chosen.
- **KILL 2 fires (no error structure):** the reachability matrix does not
  predict behaviour, so structural overlap is not the mechanism behind
  confusion. Worth knowing before phase 3 leans on it.

Every outcome yields a result. None of them requires the model to be good.

## Not in scope

- The gloss auditor (**B1**: ships in the same commit as any *trainable*
  listener that faces a *learned* generator — 2b's generator is random, so the
  cipher risk is absent and the auditor's absence is safe **only here**).
- Backbone selection for later phases. ⛔ Nate's call, every time.
- `MAX_DEPTH` revisit — needs a calibrated listener, which is this phase's output.
