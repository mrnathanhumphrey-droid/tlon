# VERDICT — Phase 6: landing the reads into the record

**Date:** 2026-08-22 · **No prereg lock** — this phase makes no falsifiable
experimental claim. 6.2 is a confirmatory measurement whose only failure mode is
"the isolation claim doesn't hold", which is itself the gate.
**Runs:** `runs/drift_taxonomy.json` · **Spend:** $0.00, no training.

---

## 6.1 — Terminology migration: "cipher" retires outward

**Adopted.** The field's name for our phenomenon is **pragmatic drift**
(Lazaridou et al. 2020); the mechanism is a **conceptual pact** (Brennan & Clark
1996, cited via Lazaridou).

"Cipher" imports *deliberate hiding*, which our λ=0 result specifically
disproves, and it files us under steganography (Motwani; Roger & Greenblatt)
where "collusion when hiding pays" is the known result and ours reads as a weaker
restatement. Stated correctly it is the opposite and stronger: **a conceptual
pact forming with no incentive to hide.**

**One scope distinction retained, because it is load-bearing rather than
sentimental:** *cipher* remains the correct word for the **planted control** —
an arbitrary code we install to calibrate detectors. It is literally a cipher.
Keeping both words precisely scoped lets us say the thing that matters: *the
planted cipher is detected at +27.05 pts; the pact that forms on its own is a
different object, and here is how it differs.* Collapsing them would erase that
contrast.

⛔ **Locked prereg bodies are NOT rewritten.** `3c49ad47`, `c1f7d06c`, `c09d0fb3`
all contain "cipher" inside hashed bodies. This is a forward-going terminology
deviation plus the glossary below — not a tidy-up pass. Editing them to be
consistent would break the one guarantee the lock exists to provide.

| internal / historical | outward-facing |
|---|---|
| "the cipher", KILL A "CIPHER FORMED" | pragmatic drift |
| "the code", "private code" | conceptual pact |
| planted-cipher control | *unchanged* — it is a cipher |
| `cipher_control.py`, `planted_cipher_control.py` | *unchanged* — calibration tooling |

## 6.2 — Taxonomy placement, verified in code ✅ **GATE PASSED**

`tools/drift_taxonomy.py` → `runs/drift_taxonomy.json`.

**Quantified over the reachable action space, not one trajectory.** Sampling a
trained policy's utterances and checking they parse is a test that cannot fail —
`build_scene` already filters on `parse()` before returning, so it would confirm
its own filter. The claim is about the *construction*, so the quantifier has to
range over everything a policy could ever pick: **60 referents × every selection
subset × 40 free-channel settings = 7,240 utterances built per arm**, both raw
and under π.

| | raw | π |
|---|---|---|
| built | 7,240 | 7,240 |
| rejected by the mask | 40 (0.5 %) | 40 (0.5 %) |
| **structural drift** | **0.0000 %** | **0.0000 %** |
| **semantic drift** | **0.0000 %** | **0.0000 %** |
| canonical round-trip mismatches | 0 | 0 |

**Pragmatic drift, from `runs/phase5.json`: +8.00 to +13.33 pts across 8
co-adapting arms — the only mover.**

### Both measures are red-proofed, and the red-proof caught a bad test

A rate of 0.0000 % is worthless unless the measure could have reported otherwise.

- **Structural** — battery of five corruptions, all caught: drop the
  illocutionary coda · reverse morpheme order · two codas · bare root · empty.
- **Semantic** — swap the head root for one outside `root_any` (`fal` for a
  signature admitting only `lan`). Caught. **And the mutant is still perfectly
  grammatical**, which proves the two measures are independent rather than one
  detector wearing two hats. This is the exact analogue of Lazaridou's "tree"
  coming to mean "ground": well-formed, wrongly grounded.

⭐ **The red-proof's first version failed, and it was the test that was wrong.**
My initial corruption duplicated the leading morpheme — which turns out to
produce a **legal** utterance. The structural measure correctly reported "not a
corruption", the red-proof failed loudly, and the tool refused to print a drift
rate. Had it not been there, `0.0000 %` would have gone into this verdict backed
by a check that never checked anything.

### The rejection rate is live, which is what makes "enforced" non-empty

40 of 7,280 attempts (0.5 %) are refused by the construction. Low, but non-zero —
so the guard is active rather than decorative. They are deterministic
(dropped-anchor `at_depth` patterns), which is why both arms reject identically.

### ⛔ The caveat a referee will find first

**`forbid` is used by 0/60 referents. `matrix` is used by 0/60.**

Those are the two schema features that could make a well-formed, signature-built
scene *stop* denoting its referent. They are unused, so part of "semantic drift
is impossible" is a property of **our current referent set**, not of the
architecture alone. Adding forbid patterns would reintroduce a leak path that
this measurement would then have to catch — and it demonstrably can, per the
red-proof.

State the claim as: *semantic drift is impossible for signature families without
`forbid`/`matrix` constraints, and detectable by an exact measure when they are
present.* That is still much stronger than Lazaridou's contrivance, and it does
not overclaim.

### The spine, stated for the eventual paper

> Lazaridou et al. (2020) identify pragmatic drift as a distinct and uniquely
> hard-to-isolate failure mode, reaching it in isolation only through a
> hand-constructed gold-caption reranking special case. We present a setup in
> which structural and semantic drift are eliminated **by construction** — via an
> exactly-invertible grammar and a frozen lossless denotation — making pragmatic
> drift the sole possible failure mode, continuously and by proof rather than by
> experimental contrivance.

**Anticipated attack, and the answer.** Signatures use disjunctive `root_any`, so
a hostile reader can call "the generator always picks root A for referent 12"
semantic drift. It is not: the denotation of A is unchanged and machine-checked
(the red-proof above is exactly this mutation, and it *fires* when the root
leaves `root_any`). What varies is **which of several true things the speaker
elects to say** — selection among true descriptions, which is pragmatics by
definition. Note this is the same object as the RSA test in 6.3.

## 6.3 — RSA α-frontier: correction to the Hole-1 null

The lit hunt claimed RSA hands us the Hole-1 null "for free". **It does not.**

The RSA S₁ speaker is *softmax*-optimal with rationality parameter **α**, so the
predicted honest naive-gap is a **function of α**, not a number. Closing Hole 1
requires showing our measured gap exceeds the RSA-predicted gap at **every α**,
including **α→∞** — the most-optimal honest speaker, which produces the
*largest* honest gap. A single-α comparison (e.g. the conventional α=1) leaves
"why that α?" open to a hostile reader.

⭐ **Our advantage is real and worth stating.** In all prior RSA work the literal
listener L₀ is approximated. Here L₀ is **exact** — LL(1) parse plus lossless
denotation plus `consistent()` — so the S₁ predictions are a computation, not an
estimate, and the α-frontier is exactly computable.

Spec note for **P2/P3**. Built in Phase 8, not now.

## 6.4 — Conservation prior-art search: NEGATIVE, and it stays quarantined

Searched: emergent communication, steganography and covert channels,
information-bottleneck multi-agent communication, side-channel mitigation, and
conceptual pacts. Terms per the brief — conserved/invariant private information,
carrier-independent covert-channel capacity, total correlation between free
channels and referent identity under mitigation.

**No paper found stating that private information is conserved across carriers.**
What exists nearby, and is *not* the same claim:

- Covert-channel work trades capacity against covertness, and pursues
  carrier-independent *detection* — but reports no conserved total.
- Information-bottleneck emergent-comm work **bounds** I(message; referent) as a
  design knob. That is imposing a budget, not observing an invariant.

**The structural precedent is in control theory, not ML.** Bode's sensitivity
integral — the **waterbed effect** — is a theorem that suppressing sensitivity in
one frequency band forces it up in another, because the integral is conserved.
That is the exact shape of our claim, rigorously formalised in another field.

⛔ **Which cuts both ways, and mostly against us.** The waterbed effect is a
*theorem with stated conditions*. Ours is an empirical pattern at **one seed per
cell** with Hole 1 open. Having a compelling mechanism (Lazaridou's conceptual
pacts: the pact belongs to the co-adapting *pair*, so its magnitude could be
conserved while its carrier is free) and now a compelling analogy makes the
claim **more** attractive to state and therefore **more** dangerous. A wrong
claim with a mechanism and a precedent attached does far more damage than an
obviously tentative one.

**Conservation stays quarantined.** Not in the brief, not in a draft, not in
exhibit copy, until it has seeds and a dynamic test.

⭐ **The dynamic test the mechanism implies.** If the pact belongs to the pair,
replacing the partner should destroy it and continued training should rebuild it
**to the same magnitude**. Reset the entire pool mid-run and watch the naive gap
as a time series: collapse toward zero, then re-climb. Re-climbs to 8–13 →
conservation shown *within a single run*, far stronger than eight arms at n=1.
Re-climbs elsewhere → conservation is false and we never said it. This is the
same experiment as **P1** (abrupt whole-pool reset, per Li & Bowling), read a
second way.

## Gate to Phase 7

**6.2 came back clean.** Structural and semantic drift pinned at zero across the
entire reachable action space, both measures red-proofed, mask demonstrably
live. The isolation spine holds.

**Phase 7 = KILL B**, and the threshold is ⛔ **Nate's call**. It has been
deferred through phases 3, 4 and 5, and it is newly better-posed: under π the
gloss is decoration-free, while the pact now lives in *selection* — which is
exactly what a gloss reflects, since selection changes which happenings get
mentioned. In phases 3–4 the auditor's input was polluted by the very channels
the pact occupied.

**Carried, unchanged:** seeds (5/cell) remain a confirmation cost, after
Phases 7–8.
