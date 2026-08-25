# VERDICT — Phase 7: KILL B is measurable, and has almost no power here

**PREREG:** `docs/PREREG_7_AUDITOR_2026_08_22.md`, LOCK `a260481e`
**Deviations:** `docs/DEVIATIONS_7_2026_08_22.md` (D8, D9, D10, D11)
**Date:** 2026-08-22 · **Spend:** $0.00, all local
**Runs:** `runs/auditor_anchors.json` · `runs/auditor_anchors_v2.json`

---

## Headline

**No KILL B verdict. `auditor_state` = `FAILED_TO_RUN`. B2 still blocks the
counter.**

Not because the auditor failed — it works, and we now have a number for how well.
**Because the strongest omission-pact this referent set can express is roughly
0.8 pts, against a detector ceiling of 7.9 pts.** KILL B is measurable in
principle and has essentially no dynamic range in practice.

## The two anchors, corrected

| keep | floor auditor | ceiling auditor (code + adversarial selection) | drop | ceiling listener |
|---|---|---|---|---|
| 0 | 43.6 % | 42.8 % | **+0.8** | 100.0 % |
| 1 | 46.0 % | 46.0 % | **+0.0** | 100.0 % |

The ceiling arm is a genuine pact — its listener resolves at 100 % via the
planted code. It simply is not much of an *omission*, and the reason is visible
in the ambiguity it induces: **1.77 → 1.80** at keep=0 and **1.10 → 1.13** at
keep=1. The adversarial subset is barely more ambiguous than a random one.

**Because the selection space is too small to be adversarial in.** Referents
carry at most 2 dependents, so at a fixed keep-size the "choice" is between two
options at best — and at keep=0 there is exactly one subset, making *adversarial*
and *random* the same object. There is no room to withhold the informative part.

## The detector's power, measured directly — and it refutes my own diagnosis

I claimed in D10 that the auditor "reads the head predication and little else",
inferred from a floor that stayed flat (46.4 / 42.8 / 48.0 %) while ambiguity
moved 15.1 % → 32.9 %. **That was wrong.**

Paired test on **identical items**, full gloss versus head-only gloss:

| gloss | all items | items that have dependents |
|---|---|---|
| FULL | 44.0 % | **42.8 %** |
| HEAD-ONLY | 39.2 % | **34.9 %** |
| shuffled (liveness) | 25.6 % | — |

**Removing the dependents costs 7.9 pts on the items that have them.** The
auditor reads selection content, and reads it substantially.

⛔ **Why I got it wrong: the floor curve was UNPAIRED.** Each withholding rate
produced a different item set with different referents and different ambiguity,
so the comparison absorbed the effect. Paired on identical items it is **3×
larger** than the unpaired curve suggested. This is the same error as the
contaminated cipher control in phase 3, which compared a scrambled subset against
a full-set baseline and produced a spurious 1.35 pt drop on a provable no-op.

## So the verdict is about the referent set, not the instrument

- **Detector ceiling (total omission of all dependents): 7.9 pts, paired.**
- **Strongest constructible omission-pact on this referent set: 0.8 pts.**
- Chance 25 %, honest ~44 %, shuffled 25.6 % — the auditor is live and immovable.

X was to be placed between floor and ceiling. The honest range is **0 to 7.9**,
and every pact we can actually build sits at the bottom of it. **Placing X is
premature: there is nothing yet to place it against.** No threshold is set, and
none should be, because a threshold chosen now would be tuned to a construction
we already know is too weak.

## What this says about flag ⑦'s designed mitigation

The gloss auditor was **B1** — the anti-pact device, the one judge the generator
cannot move. Phase 7's result is that in this system it is:

- **live** (25.6 % shuffled, ~44 % honest),
- **sensitive to omission** (7.9 pts paired),
- and **structurally unable to see the pact we actually have** (D11:
  superposition rides alongside intact description; nothing is removed to miss),
- with **too little dynamic range** to catch even the omission-pacts this
  referent set permits (0.8 of 7.9).

That is a real negative result about our own mitigation, arrived at with the
device demonstrably working. It is worth more than a KILL B verdict would have
been, because it bounds the instrument rather than reporting through it.

## D11 stands, and now dominates the read

A gloss-grounded frozen auditor detects **pacts-of-omission** only. Our natural
λ=0 pact is **superposition** — it sits in `aspect_root` beside a working
description, which is why the phase-4 planted code scored 44.4 %, inside the
honest band. The auditor answered correctly; it was asked the wrong question.

**A fired KILL B proves a pact. A clean KILL B on the natural arms proves
nothing.** Sufficient, not necessary.

## Two paths out — ⛔ BOTH NEED A CALL

**A. Deepen the referent signatures.** More dependents per referent enlarges the
selection space and gives an omission-pact room to exist. Nate ruled "no edit" on
the referent set on 2026-08-22 for a different reason (the fascination-driven set
question). This is now a second, independent reason to revisit it — and note the
lit-hunt observation that Coleridge/Calvino/Borges/Burroughs imagery is *harder*
to say without nouns, which likely means deeper signatures naturally.

**B. Accept that KILL B cannot answer the superposition question and hand it to
Phase 8**, which is where the instruments that can live:
- **RSA α-frontier** — does the listener resolve better than an RSA-optimal
  speaker's gloss should permit, at every α including α→∞?
- **Dynamic reset test** — does resolution collapse and re-climb on whole-pool
  reset, proving the capability lived in the co-adaptation rather than in the
  description?

I favour **B now, A later**: B answers the question we actually have with
instruments already specified, and A is entangled with a referent-set decision
that deserves to be made on artistic grounds rather than forced by a detector's
dynamic range.

## Corrections carried

- **D10 is retracted and replaced** by the paired measurement above. The auditor
  is *not* head-only; the unpaired floor curve misled me.
- The "floor is a curve" refinement (prereg §7.1) was correct in principle and
  **the wrong tool** — a curve across *different item sets* cannot measure a
  within-item effect. Pairing was the missing discipline, not more points.

## Do not quote

- Any KILL B result. **There isn't one.**
- The v1 anchors (`runs/auditor_anchors.json`) — listener saturated at 100 %,
  gap pinned, ceiling below floor. See D8.
- "The auditor reads only the head predication" — retracted, see above.
