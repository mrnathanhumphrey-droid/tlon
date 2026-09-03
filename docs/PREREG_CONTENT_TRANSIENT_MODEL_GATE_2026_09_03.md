# PREREG — does corpus lag-1 responsiveness survive into MODEL behaviour?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `abde6124` (sha256[:8] of draft body at lock, 2026-09-03T22:18Z)
- **Date:** 2026-09-03
- **Fires on:** one adapter, `ct-s20624`, trained on the content-transient
  corpus at corpus seed 20624.
- **Written before that adapter exists.** No content-transient model has been
  trained, and no model-side lag number has been observed.
- **Gates:** the remaining eleven adapters of the factorial (~26–52 GPU-h) and
  the conversational chatbot deliverable. Both are downstream of this one
  measurement.

---

## 1 · The assumption, stated as the thing that could be false

The content-transient **corpus** is responsive at lag 1 and silent at lag 2.
Measured, before any training:

    lag1 0.9685 (z = +120.36)   lag2 0.0396 (z = -1.41)
    lag3 0.0236 (z =  -1.06)    lag4 0.0238 (z = -1.35)

⛔⛔ **That is a property of the DATA, not of a model.** The content-free arm is
the standing proof that the transmission is real in the other direction: its
corpus carried no content connection (measured across six independent corpora,
z between −0.68 and +2.03) and the model faithfully learned to have none —
0.00 shared roots across 13 human-in-the-loop exchanges, in both prompt shapes.

The inverse has never been tested. A corpus **with** lag-1 responsiveness might
produce a model that:

  a. **reproduces the profile** — perceives, responds, releases;
  b. **washes it out** — the fine-tune averages the responsiveness away and the
     model behaves content-free anyway;
  c. **over-holds it** — the model learns "echo recent content" and carries it
     past the turn, which is content PERSISTENCE and is the thing Tlön denies;
  d. **learns something adjacent** — e.g. lexical repetition of the seed rather
     than responsiveness to whatever provoked the current turn.

⭐ **One adapter distinguishes these. Twelve assume (a).** So one is trained and
read before the other eleven are bought.

## 2 · The instrument — the same one, both sides

`tools/act2_model_lag.py` **imports** `lag_profile`, `permutation_null` and
`check_transience` from `tlon.discourse.transient` — the exact functions the
corpus was gated on. It defines no statistic of its own, and
`tests/test_model_lag.py` asserts function identity (`is`, not equality) so a
re-implementation fails the suite.

⛔ Without that, "the model matches the corpus" would be a claim about two
implementations agreeing rather than about the model.

**The chain is built in the trained shape.** Seed surface, then each turn
provoked by the one before it under the `provoke` direction with a **bare
surface** as the user message — byte-for-byte the shape of `prev.surface` in
every provoke row of the corpus. A refused turn **ends** its chain rather than
being skipped: splicing across a refusal would report an adjacency the model
never produced, manufacturing lag-1 evidence out of a gap, in the direction that
flatters the hypothesis. Chains with fewer than 3 usable turns are dropped
(they have no lag-2 cell), and the count of dropped chains is reported.

## 3 · The thresholds — the corpus's own, not new ones

    Z_LAG1_MIN = 6.0     lag 1 must be responsive
    Z_LAGN_MAX = 3.0     every longer lag must be indistinguishable from chance

⛔⛔ These are `tlon.discourse.transient.Z_LAG1_MIN` / `Z_LAGN_MAX` — the
constants the corpus was gated on, imported. A model-side threshold invented
here would let the gate be tuned after seeing the model, which is the definition
of post-hoc. The test suite asserts they are the same objects.

⭐ The acceptance criterion is stated against a **permutation null**, never
against zero: chance overlap between two short utterances drawn from 156 roots
is ≈0.042 shared roots, so a target of "> 0" is passed by a model that does
nothing.

## 4 · The pre-declared readings

Run: 12 chains × 10 turns, temperature 0.70, `max_new_tokens` 256, cardless
(`card=False` — the project's standing success criterion), unconstrained
decoding. Adapter `ct-s20624`, bf16 unless otherwise recorded.

| outcome | lag 1 | lag ≥2 | verdict |
|---|---|---|---|
| **GO** | z ≥ 6.0 | all z ≤ 3.0 | the recipe transmits. Train the remaining eleven; the chatbot is unblocked. |
| **STOP — washed out** | z < 6.0 | all z ≤ 3.0 | (b). The model is content-free despite a responsive corpus. The eleven are the wrong purchase; the fine-tune, not the corpus, is the obstacle. |
| **STOP — persists** | z ≥ 6.0 | any z > 3.0 | (c). The model holds content past its turn. This is object permanence and it is **worse than the control**, not better: the recipe produced the un-Tlön failure mode. |
| **STOP — both** | z < 6.0 | any z > 3.0 | incoherent; instrument or training fault before interpretation. |

⛔ **A GO is not "the transcripts read well."** Eyeballing a conversation and
calling it conversation is exactly the read this gate exists to replace. The
verdict is the lag profile, produced by `check_transience`, and the transcript
is colour.

⛔⛔ **A STOP DOES NOT AUTHORISE A THRESHOLD CHANGE.** If lag-1 lands at, say,
z = 4.5, that is a STOP under this document and the response is to ask why the
fine-tune attenuates the signal — not to discover that 4.0 was always the
sensible floor. The thresholds are hashed into this body.

## 5 · What is deliberately NOT claimed

- **Nothing about convergence, coupling or force:ka.** This gate reads content
  transmission only. The positive control (`c0de41c7` + Amendments A and B) is a
  separate question on a separate arm and is not touched here.
- **Nothing cross-recipe.** A content-free adapter is not run through this
  instrument as a comparison, because the two arms' rulers are per-recipe
  (see §6) and a cross-recipe z here would be a between-recipe difference
  wearing a within-recipe name.
- **Nothing about whether a human finds it satisfying.** "Holds a conversation"
  in the product sense is a further question. This gate answers only whether the
  measured corpus property reached the model.
- **No power claim.** 12 chains is sized to detect a corpus-scale effect
  (z ≈ +120 in the data), not to resolve a small one. A lag-1 z between 3 and 6
  is therefore **UNDERPOWERED, not a STOP by magnitude** — it is a STOP by this
  document's rule, and the honest follow-up is more chains, pre-declared, before
  any threshold is revisited.

## 6 · The pairing consequence, recorded here because it constrains the read

`ct-s20624` will pair with the cooking `s20624` (legacy single-stream path) by
**seed only, not by force sequence** — unbiased (same map, same stationary
distribution) but unpaired, therefore higher variance. That is acceptable for
this first-order question and is not acceptable for the second-order
cross-recipe convergence contrast, which requires per-recipe rulers and matched
pairs. **Rulers are never pooled across recipes.**

## 7 · Provenance

- corpus recipe + one-knob guarantee: `d6a1372`
- factorial bookkeeping, recipes measured off their own rows: `3fd3aff`
- one pipeline both arms, failure handler hardened in all eight: `6cc614f`
- instrument: `tools/act2_model_lag.py`, red-proofed by `tests/test_model_lag.py`
