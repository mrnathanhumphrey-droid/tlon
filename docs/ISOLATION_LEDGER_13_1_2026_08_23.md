# 13.1 — THE ISOLATION LEDGER: three claims restated, recorded BEFORE 13.2 runs

**Date:** 2026-08-23 · **Status:** RECORDED. 13.0 is built and green
(**530 → 557 tests**); 13.2 has not run and no arm exists yet.

⛔ **This file exists because the change touches the crown jewel.** The rule is
*record the restatement before anything leans on it* — so this is written while
13.2 is still unbuilt, and it is the version that must be quoted on any
residue-bearing set. **The pre-13.0 wordings are superseded, not amended.**

---

## What 13.0 actually changed

π's construction assumed **denoting ⊆ expressible**. It no longer holds. The
split is now three-way, derived from the schema and asserted in
`tests/test_denote.py`:

| category | parts |
|---|---|
| denoting ∧ **expressible** | `root`, `orient`, `aspect.root`, `edges` |
| denoting ∧ **inexpressible** | **`residue`** |
| non-denoting (stripped) | `aspect.reps`, `degree`, `modal`, `tense`, `quant`, `force` |

⭐ **`stripped` and `unsayable` are different and the code now says so.**
Stripped = reaches the surface, removed for measurement. Unsayable = never
reaches the surface at all. **π does not strip the residue** — `project_node`
carries it through, because π removes decoration, not meaning.

---

## CLAIM 1 — Q3

**Was:** *Q3 = 1. A fixed scene has exactly one canonical surface form.*

**Now:** *Q3 = 1 **per denotation-class**. A fixed scene still has exactly one
canonical form; but many scenes — all those agreeing on every expressible part
and differing only in residue — share that one form.*

The original meaning is **preserved within a class**, not weakened. What is new
is the reciprocal count:

> ⭐ **SCENES-PER-FORM is now a first-class measured quantity, and it is the
> frontier-relevant one.** Every previous referent set measured it as exactly 1,
> which is why the RSA frontier came back identically zero on all four.

⛔ **Consequence, tested:** for a residue-bearing scene,
`utterance_id(scene) != id_of(render(scene))`. The surface→id direction can no
longer round-trip. **That asymmetry is the source-lossiness; it is not a defect
to repair.**

## CLAIM 2 — Phase 6 isolation

**Was:** *Structural and semantic drift are impossible by construction.
Structural: the parser accepts or it does not. Semantic: the scene denotes its
referent or it does not.*

**Now, and this is the wording to quote on any residue-bearing set:**

> **Structural and semantic drift remain impossible on the EXPRESSIBLE
> component. Semantic grounding is restated as SET MEMBERSHIP: the utterance's
> denotation-set CONTAINS the target. The residue is inexpressible by
> construction, and its ambiguity is the designated, CONTAINED exception.**

Weaker than exact denotation. **Still exact as a set-membership claim** — the
denotation-set is computed by `consistent()`, which is exhaustive and exact, not
estimated.

⭐ **"Contained" is the operative word and it is certified, not asserted.**
`tests/test_residue.py` red-proofs that mutating the residue leaves the surface
**byte-identical**, at depth as well as at the matrix. If the residue ever
leaked into the surface, containment would fail and this clause would be void —
so the red-proof is what holds the claim up.

⛔ **Do not quote the pre-13.0 wording on a residue-bearing set.** Named as a
misreport risk in the 13.2 prereg.

## CLAIM 3 — the novelty counter

**Was:** *R is computed on π(scene). Two utterances differing only in
non-denoting decoration are the same impression and must not count as novel.*

**Now:** *R spans **expressible-channel distance and residue-metric distance**.
Repeating a residue IS repeating yourself, so R must see it.*

⭐⭐ **The fork Phase 12 found is resolved by the metric, not chosen between.**
Phase 12 showed a free categorical residue is either invisible to R (a blind
counter) or free uncheatable novelty (the noise failure π exists to prevent).
**A metric residue is neither: it enters R as a DISTANCE.**

⛔ **The metric must be fixed and immovable, never learned.** `distance.py`'s own
docstring: an embedding distance *"would let it buy novelty by shifting the
space rather than by having a new impression."* A learned residue metric
reintroduces exactly that failure **inside the one dimension nobody can read.**
L1 on an integer lattice, `W_RESIDUE = 0.50`, tested to scale with distance.

⭐ **Conventionable and auditable are the same property from two sides** — the
finding that made this phase buildable. Both come from the metric, and neither
is available without it.

---

## ⛔ The landmine, and why it is in a ledger rather than a commit message

`RepetitionLog.observe` folds a scene into an existing medoid when
`nearest.uid == uid OR nd == 0.0`. **Both clauses would have collapsed
residue-differing scenes** — `utterance_id` hashed a `canon_json` that omitted
the residue, and `D.normalized` had no residue term.

It would not have crashed. **It would have silently erased the distinction, made
the metric-residue arm behave exactly like a no-residue arm, and manufactured an
empty Part-2 result — while the predicted-empty control looked correct, so the
pair would have read as internally consistent and been wrong.**

Both clauses are fixed and both are separately red-proofed
(`test_both_collapse_clauses_are_actually_fixed`). ⛔ **No Part-2 null is
interpretable until that test passes** — it is the fourth named misreport risk.

## One design question 13.0 answered, that the scope had not

**`residue = None` means UNKNOWN, not "the null residue".** It surfaced as a
failing red-proof: a heard utterance carries no residue, and treating that as a
*value* made it consistent with **neither** of two residue-distinct referents —
when the entire point is that it is consistent with **both**.

The two subsystems must therefore treat unknown differently, and now do:

- **`match`** — unknown is **benign**. It is the listener's epistemic position
  and cannot violate a constraint. *This is what creates the ambiguity.*
- **the metric** — unknown **raises**. Either convention is exploitable:
  maximally-distant buys free novelty for dropping the residue, zero makes
  dropping it read as a repeat. Safe to raise because the generator's own scenes
  always carry one; a known-vs-unknown comparison means something upstream
  dropped it.

---

## Status

| | |
|---|---|
| 13.0 architecture | ✅ built, **557 tests** |
| red-proof: renders-never | ✅ incl. at depth |
| red-proof: guard on unmapped field | ✅ pre-existing, fires |
| red-proof: two medoids, both clauses | ✅ |
| type assertion (no text residue) | ✅ 7 rejected types + the str side door |
| 13.1 ledger | ✅ this file |
| **13.2 arms + prereg + training** | ⏸ **not started** |
| pre-phase Mantel (≥2 distillers) | ⏸ needs a second human |

⛔ **13.2 still needs a seed decision before it locks.** MDE at n=5 on the
archive variance prior is **4.40 pts**; a Part-2 gap below that is UNDERPOWERED,
not absent.
