# 9.1 — HANDOFF TO NATE: the referent roster

**Date:** 2026-08-23 · **9.0 is done, the gate is open** — see
`docs/GUARD_9_0_COMPARISON_2026_08_23.md`. Nothing else in Phase 9 runs until
this roster exists.

**Standing rule, unchanged:** *Nate authors the roster. Code consumes it and does
not author it.* Signatures are **proposed by Code for review, veto reserved by
Nate** (the propose-for-review ruling from the mirror/map decision).

⭐ **The measurement in 9.2 checks the artistic choice. It does not make it.** A
referent set chosen for the instrument's convenience is how this project got
sixty pegs engineered for measurement instead of a cast that makes the piece
yours. Everything below is *constraint and translation* — what the grammar can
hold, and what "deeper signature" means in imagery terms — so the choice is
informed. **Not a shortlist.**

---

## 1. What you author

`tlon/referents/referents_v2.yaml`, same shape as the three current files. A
worked entry, copied from `referents.draft.yaml`:

```yaml
review_status: UNREVIEWED   # nothing runs until you set this to REVIEWED
schema_version: 2
grammar_family: southern

referents:
  - id: "14"
    name: a lit window seen from outside at night
    tier: 1
    notes: >
      Why this is the impression and not the object.
    signature:
      contains:
        - {root_any: [flex]}                       # it darkens to night
        - {root_any: [hräx], via: [sir]}           # it glows, amid
        - {root_any: [lan], via: [hlin]}           # it is seen, against
```

**All you have to supply is `name` + `notes`.** I propose the `signature`
blocks, you veto. If you want to sketch roots, `tlon/grammar/lexicon.yaml` has
all 156 with glosses.

## 2. The hard constraints — these bound what you can ask for

From `lexicon.yaml` (hash `e2b8527010231a81fd31b6eeb9de3d8c`):

| | value | meaning |
|---|---|---|
| `MAX_CLAUSES_PER_PRED` | **3** | a signature holds **at most 4 `contains` patterns** |
| `MAX_DEPTH` | 3 | nesting depth below the matrix |
| `MAX_ORIENT_PER_PRED` | 2 | orientation particles per predication |
| `MAX_ASPECT_REPS` | 4 | |

⛔⛔ **Where the current set sits: max 3 patterns, mean 2.50.** So on the
"how many happenings" axis there is **exactly one step of headroom** before the
cap.

⛔ **Raising the cap is a grammar change and it is your call.** The constraints
live inside `lexicon.yaml`, so editing one changes the lexicon hash, which is
pinned in **every locked prereg**. Not forbidden — but it is a real cost and it
is not a thing I do quietly.

## 3. The capacity that is sitting unused

Current usage across all 60:

| feature | used | what it buys |
|---|---|---|
| `via` (relator to matrix) | 88 | how two happenings relate |
| `orient_any` | 31 | orientation constraint |
| disjunctive `root_any` | 16 | "either of these roots" |
| `aspect_root_any` | **2 / 60** | aspect as part of the signature |
| `at_depth` (**scope**) | **2 / 60** | *"a glow beyond ⟨a raining that is seen⟩"* vs *"a glow beyond a raining, and a seeing"* |
| `forbid` | **0 / 60** | what must NOT be present |
| `matrix` | **0 / 60** | what the head happening must be |

⭐ **`at_depth` is the axis with real room.** Depth-by-nesting is capped at 3 and
used twice. It is the one contrast the grammar's recursion buys and nothing else
can express — and it does not touch the clause cap.

⛔⛔ **If any new signature uses `forbid` or `matrix`, 9.3 must re-run the
Phase 6.2 taxonomy placement.** Those two are the *only* features that can make
a signature-built scene stop denoting, and Phase 6's honest scope was
*"impossible for signature families without `forbid`/`matrix`, and detectable
when present."* Not a reason to avoid them — a reason it is written down here.

## 4. What "deeper" actually means, in imagery terms

The translation, so the artistic pick can be made in artistic language:

⭐ **Depth = how many distinct happenings the impression is composed of** — not
how abstract it is. Compare, from the current set:

- *a flickering light* → **1 pattern.** One happening. Nothing to withhold.
- *a river at night* → **2.** It streams · it darkens.
- *a lit window seen from outside at night* → **3.** It darkens · it glows ·
  it is seen.

An impression that bundles three or four simultaneous happenings has something
to leave out. One that bundles one does not — and *having something to leave
out* is the whole of what impression-selection operates on.

⭐ **A cast that shares a world collides; a cast of unrelated one-offs does
not.** Underdetermination is a property of the *set*, not of any member. Right
now **26 of 60 referents have a head root unique to them**, so selection can
never make them ambiguous and they never need a pact. Xanadu is one world —
sacred river, caverns measureless, sunless sea, caves of ice — and a single
world naturally shares vocabulary. Calvino's cities likewise.

⛔ **And the honest counter-pressure, so this is not a prediction dressed as
advice:** deeper signatures also give the listener *more* to read, which pushes
resolution the other way. A valid mechanism does not entitle anyone to the sign.
**That is precisely why 9.2 enumerates three outcomes** — gap grows with
underdetermination, gap flat, gap shrinks — and none of them is the default
branch.

## 5. The brief, restated from your spec

The Coleridge / Calvino / Borges / Burroughs constellation, per the senior-paper
lineage. **Concrete-weighted first for legibility** — the sacred river, caves of
ice, the mirror, the tiger, the coin, the invisible city, the labyrinth —
abstractions folded in only after the listener is calibrated, same discipline as
`MAX_DEPTH`.

⭐ **Precedent for gaps (option C, the mirror/map ruling):** when the language
cannot say a referent, it is expressed as **encounter-impressions**. We never
mint representational roots — that smuggles object-permanence back in and Tlön
denies the object. `01 a mirror` and `12 a map the size of its territory` both
still stand `validated: false` under that ruling.

**Open question that is yours, not mine:** whether the v2 cast *replaces* the
current 60 or *extends* them. Replacing gives a clean measurement and loses the
diagnostic pairs (31–50) that 2b.2 was built on. Extending keeps the instrument
history and dilutes the new set's effect on the aggregate. Either is defensible;
say which.

## 6. What happens the moment the roster lands

1. **Coverage pass** — rerun `REFERENT_COVERAGE` against the **current** lexicon
   (156 roots, hash `e2b8527010231a81fd31b6eeb9de3d8c`), *not* the stale
   151-root audit from 2026-08-17. Can the language say each one? Gaps logged
   with the option-C resolution.
2. **I propose signatures** — graph patterns, disjunctive roots, `via` relators,
   orientation constraints. Never single-root. You veto.
3. **Lock the 9.2 / 9.3 prereg** — named outcomes, misreport risk stated
   ("reporting the new consistency-set size or gap without confirming, via the
   guard, that any old-vs-new comparison was reported **side by side rather than
   subtracted**").
4. **Run 9.2 / 9.3**, every comparison through the guard.

⛔ **Phase 9 does not re-run the 8.2 dynamic reset test or re-attempt
conservation.** They wait for a confirmed-deep set so they run **once**, on
solid ground, through the guard. Slow is smooth.
