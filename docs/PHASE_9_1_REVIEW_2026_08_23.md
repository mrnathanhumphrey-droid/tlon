# 9.1 — REVIEW PACKET: referent set v2, The Distance of the Moon

**Date:** 2026-08-23 · **Spend:** $0.00, all local · **No prereg** — content.
**Status:** `review_status: UNREVIEWED`. ⛔ Nothing runs until Nate sets it.

⭐ **UPDATED after Nate's pass: *"ya apply the fix. the referents are solid asf
tbh."*** Roster content approved, no vetoes. **The matrix rule is applied** —
see *The matrix rule, applied* below. All numbers in this file are post-fix.

**Read the page, not this file:** `docs/signature_review_v2.html` — generated
from the YAML, so it cannot drift from what it reviews. Each referent shows the
**minimal legal utterance** its signature accepts plus the gloss. *If the
minimum already reads as the referent the signature holds; if it reads as
anything at all it is too loose.*

| | |
|---|---|
| File | `tlon/referents/referents_v2.yaml` — **50 declared, 46 live, 4 held back** |
| Coverage | `tools/coverage_v2.py` → `runs/coverage_v2.json`, **exit 0** |
| Review page | `tools/build_review_v2.py` → `docs/signature_review_v2.html` |
| Tests | `tests/test_referents_v2.py`, +9. **512 → 521, all passing** |
| Lexicon | `e2b8527010231a81fd31b6eeb9de3d8c`, **unchanged** — 156 roots, 55 used |

**Nate's ruling reversed the standing rule for v2:** Code compiles, Nate reviews
and vetoes. Every entry below is a proposal.

---

## Coverage: the language can say all fifty

✅ **All 50 referents are sayable.** Every root, orientation, relator and aspect
validated by `schema.load()` against the current lexicon — *not* the stale
151-root audit from 2026-08-17.

✅ **211/222 selection subsets buildable (95.0 %).** The 11 holes are exactly
one per nesting referent and they are **structural, not accidental**: a depth-2
pattern hangs off a depth-1 node, so the subset that keeps the deep dependent
and drops the shallow one cannot build. Predicted from reading the builder
before writing a signature, then measured. Pinned by a test so a future
signature cannot reintroduce the worse version (a signature whose *only*
dependent is deep can never build at all).

✅ **`forbid` 0/50, `matrix` 0/50** ⇒ **9.3 carries Phase 6's isolation claim
over unchanged.** Its honest scope was *"impossible for signature families
without forbid/matrix"*, and v2 is such a family. No re-run owed.

## What moved, against the old set

| | archive 60 | **v2 50, post-fix** |
|---|---|---|
| mean patterns per signature | 2.50 | **3.10** |
| max patterns | 3 | **4** (6 referents) |
| `at_depth > 1` (nesting) | 2 | **11** |
| `aspect_root_any` | 2 | **11** |
| head root **unique** to one referent | 26/60 = **43 %** | **11/50 = 22 %** |
| `forbid` / `matrix` | 0 | **0** |

⛔ **Reported side by side, never subtracted.** Different referents, no pairing
exists — this is exactly the case `side_by_side()` was built for in 9.0.

---

## ⭐⭐ The matrix rule, applied

**The matrix predication is the world's persisting event; the distinguishing
happening is a dependent.** In this story there are exactly two persisting
events — the mooning and the sea — and Calvino narrates every human action as
subordinate to the cosmological one. So *"the moon's underside, scaled and
pored"* is not a roughening that happens to involve the moon; it is **a mooning,
part of which ⟨a roughening, under, at which a hollowing⟩.**

The linguistic reason came first: the matrix verb is *what is happening* and
everything else is *how*. The measurement reason follows from it: the head is
never dropped by impression-selection, so a unique head root means that referent
can never be made ambiguous.

**Applied to 11** — M03 M04 M06 M07 M08 M09 M12 M23 M31 M32 M43.

⭐ **Two came out better as images, not just as structure.** M06's pores used to
nest inside the mooning; they now nest inside the roughened underside, which is
where they are. M07's curd now sits in the pore, in the moon — three levels, and
each one true.

### ⛔ Where it was refused, and why

Each refusal is a reason, not an oversight:

- **M10** — the nesting *is* the image. The referent is that the moon is at
  depth 2, inside the water. Promoting `mlö` to matrix puts it at depth 0 and
  the reflection is gone.
- **M45** — **the causation would invert.** `kra` is CAUS in one direction only.
  *"A weighing because of a mooning"* is true; matrix-`mlö` forces *"a mooning
  because of a weighing"*, which is false. The rule would have reversed a causal
  claim to gain a shared head.
- **M17, M29, M40** — no cosmological body is in the impression. The
  unburdening, the bending and the recalling *are* the events.
- **M41** — deliberately the shallowest referent, kept as a control on whether
  depth is what moves consistency-set size. Restructuring it destroys the
  control.
- **M37, M38, M49** — held back; not in any live measurement.

### ⛔ 11, not the 9 I predicted — and the difference matters

Moving `säx` off M12's head and `kron` off M23's made **M26 and M46 — which were
shared — newly unique.** The count is a property of the whole set, not of the
referents changed, and my before-the-run prediction of 9 was wrong.

**M26 and M46 are not chased.** Neither has a cosmological body in its
impression, so the rule does not cover them, and applying a rule where it does
not hold in order to move a number is the exact thing this phase ordering exists
to prevent. **11/50 = 22 %, down from 43 %.**

### Breadth moved as a side effect, not as a target

Three of the eleven (M08, M31, M32) needed a fourth pattern to keep their
content once the head moved, so 4-pattern referents went **4 → 6** and mean
breadth **3.06 → 3.10**. That fell out of faithfulness. It was not chosen to
move the omission ceiling — and it is still small, so **Phase 7's complaint
stands: nesting does not add a dependent, it moves one deeper, and the omission
ceiling may not move much.** That remains open and is 9.2's to answer.

---

## ⭐⭐ A trade-off in the depth-by-nesting ruling, found by doing it

**The schema cannot constrain the relator of a nested pattern.** `via` is
hardwired to depth 1 — `NodePattern.parse` raises *"via implies at_depth 1"* —
so a depth-2 pattern's edge relator is chosen at random by the builder.

| | archive 60 | **v2 50** |
|---|---|---|
| dependents | 90 | 103 |
| **relator unconstrained** (no `via`) | **2** | **11** |

⛔ **Those relators live in `edges`, and `edges` DENOTES — π keeps them.**

⭐⭐ **CORRECTION, 2026-08-23.** I first wrote that this is *"a place a code
could sit that π cannot strip."* **That is wrong as stated.** `FREE =
("aspect_root", "aspect_reps", "degree", "coda", "orient")` — the policy has
**no relator handle**, no log-prob and no gradient there, so it **cannot
currently carry a code**. It is **denoting noise, not a channel.** It would
become a channel the moment anyone adds a relator head to the policy.

**Why it still matters, and what was done about it:** it is noise the listener
must see through and v2 has **5.5× more of it**, so a lower listener accuracy on
v2 is partly this rather than underdetermination. Pre-registered as **confound
C1** in `PREREG_9_REFERENTS_2026_08_23.md`, with a paired control — deep-edge
relators pinned to a constant, `contrast="deep_relator"`, through the guard.

This is not an argument against the ruling — nesting is the more Tlönian axis and
M10 is unsayable without it. It is a consequence that should be on the record
**before** 9.2 rather than discovered in its verdict. Three ways out, none taken
unilaterally:

1. **Accept it** and note that v2's free-channel landscape differs from the old
   set's in a way π does not cover.
2. **Schema change:** allow `via` on `at_depth > 1` patterns. Touches
   `NodePattern.parse` and both builders. Does **not** touch `lexicon.yaml`, so
   no prereg hash moves.
3. **Fewer nesting referents.** Cheapest, and it gives back the thing the ruling
   was for.

## ⭐ Two near-misses where the meaning would have evaporated at π

Caught while writing, recorded because both are the shape of a silent leak:

- **M32** *"the tide going out and not returning"* wanted `pän` (never, QUANT).
  **π strips quant.** It would have projected to a plain ebbing.
- **M45** *"the moon's pull felt in the arms"* wanted the modal `ten` (felt).
  **π strips modal.** It would have projected to a plain weighing.

Both now carry the meaning in a relator or a root, which denote. ⭐ The general
rule this suggests: **anything a referent means must be sayable in root, orient,
aspect-root or edge — the four things π keeps.** Everything else is decoration
by definition, and a signature that leans on decoration is not a signature.

## What I ruled on myself

- **Three negations as CONC `xom`, not `forbid`** — the deaf cousin (M18), the
  tide (M32), the pole that bends anyway (M29). `forbid` was the obvious
  encoding and does not denote; using it would have narrowed Phase 6's isolation
  claim for the whole set. `xom` denotes and is truer: he does not *lack* the
  senses, he does not *need* them.
- **`aspect_root_any` on 11** (old: 2), only where the aspect *is* the image —
  `ax` unceasing (M23, M36, M46), `mel` terminative (M26, M28, M33, M39), `nim`
  momentary (M14, M47), `sor` habitual (M25), `tes` iterated (M41). ⛔ **Not
  free:** fixing a head's aspect removes that referent's free `aspect_root`
  channel, which is where phases 4–5 found the code living.
- **No `minimal_pair` fields.** Members must share an identical root multiset or
  bag-of-roots tells them apart; half-correct pairs would be worse than none.
  The 2b.2 pair history lives in the archive. **Flagged, not silently omitted.**
- **M38 and M50 held back** — they state Calvino's engine flat, *the relation
  surviving its objects*, which is the conservation claim **Phase 8 retracted**.
  A referent saying the thesis out loud inside the live set while we measure the
  thesis is a compositional pressure toward believing it. Declared so the world
  is complete, withheld so they cannot whisper into a measurement. Pinned by a
  test: flipping `seed_2a` on either fails the suite and owes a DEVIATIONS entry.
- **M05 / M22, the ladder, is the weakest thing here.** Tlön has no way to say
  "carrying" that does not imply a carried thing; M22 uses the instrumental
  `fro` and the strain is real. If the gloss reads as mush, cut that one first.

## Replace for live, archive for history — implemented safely

`schema.load_live()` returns v2; `schema.load_archive()` returns the frozen 60.
⛔ **`load_all()` is deliberately unchanged** and still returns the 60 — every
phase 3–8 tool calls it, and silently repointing it at v2 would change what those
tools reproduce while their preregs still claim 60 referents. That is the same
class of failure as editing a locked prereg body. The switch is **explicit**: new
work asks for `load_live()`, old work keeps getting exactly what it got.

## On approval

1. Apply any vetoes; regenerate the review page and the coverage pass.
2. **Lock the 9.2 / 9.3 prereg** — named outcomes, three-way gap-vs-
   underdetermination branch, and the misreport risk stated: *"reporting v2
   consistency-set size or gap as evidence for conservation, or letting the
   Cosmicomics theme's conservation-whisper stand in for the unexecuted dynamic
   reset test."*
3. Run 9.2 / 9.3, every comparison through the 9.0 guard.

⛔ **Phase 9 still does not re-run the 8.2 dynamic reset test or re-attempt
conservation.** The theme makes conservation *more* tempting and therefore that
test *more* necessary — executed, five-branch-classified, on a confirmed-deep
set. Once, on solid ground. Slow is smooth.
