# VERDICT — Phase 12: Lever 2 dead structurally. Lever 4 architecture-blocked, and the block is a design assumption.

**Date:** 2026-08-23 · **Spend:** $0.00, closed-form and paper-only, no training
**Runs:** `runs/phase12_1_depth.json` · `runs/phase12_2a_arch.json`
No prereg — 12.1 is closed-form, 12.2a is a determination. **12.2b was never
reached, so nothing was locked.** Research mode, no exhibit dependency.

> **Lever 2 fails part 1 of the filter, structurally — stronger than predicted,
> and no lexicon hash needs moving. Lever 4 requires an architecture change, and
> the change is small in code and expensive in restated claims. The blocking
> decision is named.**

---

## ⛔ Two premises in the brief that the code contradicts

1. **"Raising `MAX_DEPTH` doesn't touch the lexicon hash."** It does.
   `MAX_DEPTH` lives in `lexicon.yaml` under `constraints:` and the hash is
   blake2b over the whole file, so raising it moves
   `e2b8527010231a81fd31b6eeb9de3d8c` — pinned in **every** locked prereg
   (3, 4, 5, 7, 8, 9). Same cost as `MAX_CLAUSES_PER_PRED`, flagged in Phase 9
   for the same reason. **Not fatal to the brief, but it is not free.**
2. **"Depth is predicted dead on part 2 even if it passes part 1."** It is dead
   on **part 1**, for two independent structural reasons. That is a stronger
   result and it means **no depth-4/5 referent set needs building at all.**

---

# 12.1 — Lever 2 (depth/nesting): DEAD ON PART 1

## Argument A — attachment ambiguity cannot exist

Three scenes with the **identical node multiset** `{mlö, fox, lan}` and
different attachment:

| attachment | surface |
|---|---|
| flat, both at depth 1 | `fro fox hlim lan mlö ka` |
| nested `a<b<c` | `fro hlim lan fox mlö ka` |
| nested `a<c<b` | `fro hlim fox lan mlö ka` |

**All surfaces distinct. `parse()` recovers every tree exactly.**

> **The grammar is LL(1) and the decoder is exact, so attachment is always
> recoverable from the surface. Attachment ambiguity cannot exist at any depth.**

⭐ This is the same fact that made the phase-2 M gate vacuous — *"`parse()`
decodes exactly, so a listener asked to decode cannot fail"* — reappearing one
level up. The hypothesis is refuted by the architecture, not by a measurement.

## Argument B — depth moves *away* from the target

`consistent()` contains, verbatim:

```python
if len(pool) > len(sig.contains): return False
```

Every level of nesting adds a node to `pool`, so a deeper scene can only be
consistent with signatures having **more** patterns. Measured, and **monotone
decreasing on all four sets**:

| nodes uttered | archive | v2 | CR | TAO |
|---|---|---|---|---|
| 1 | 1.78 | 2.70 | **4.28** | **4.03** |
| 2 | 1.08 | 1.02 | 1.00 | 1.00 |
| 3 | 1.00 | 1.00 | — | — |
| 4 | — | 1.00 | — | — |

⭐ **The same shape as the f₂ finding, one level down.** More structure uttered ⇒
less ambiguity. Depth is anti-correlated with the target by construction.

**Part 2 (conventionable) is not reached — part 1 fails first.** The brief asked
to measure in case attachment ambiguity turned out conventionable; it cannot
turn out anything, because it does not exist.

---

# 12.2a — Lever 4: architecture change required, and the crux is a design assumption

## What the architecture has now, derived from the schema

| category | parts |
|---|---|
| **denoting ∧ expressible** | `root`, `orient`, `aspect.root`, `edges` |
| **non-denoting ∧ expressible** | `aspect.reps`, `degree`, `modal`, `tense`, `quant`, `force` |

**Two categories. There is no third.** Verified rather than read: mutating each
of the seven `EventNode` fields changes the surface in **7/7** cases, so
**0 fields are invisible to `render()`** — no inexpressible slot already exists.

## ⭐⭐ The crux

> **π's whole construction assumes DENOTING ⊆ EXPRESSIBLE.** The strip-list is
> *derived* from `NodePattern`'s fields, and every one maps to a scene part that
> renders. **Lever 4 needs a third category — denoting *and* inexpressible —
> which the two-way split has no room for.**

That is a design assumption, not an oversight, and naming it is most of the
answer to 12.2a.

⭐ **The guard already knows.** Firing it deliberately: adding a `NodePattern`
field π has no mapping for raises `ProjectionUnsound` at import. So the change
**cannot be made silently** — which is exactly what that guard was built for.

## The change, specified (~20 lines)

1. `EventNode`/`Scene` gains a `residue` field.
2. `render()` must **not** emit it — **and a test must assert the surface is
   invariant to it**, or it leaks silently.
3. `NodePattern` gains `residue_any`.
4. `denote.py`'s two-way split becomes **three-way**; `_PATTERN_TO_PART` gains
   the mapping (the guard forces this).
5. `match.node_matches()` checks residue.

**Sub-question (2) — speaker holds the residue, utterance cannot carry it — is
trivially YES once (1) exists.** That is source-lossiness, and it makes the
frontier nonzero by construction.

## ⛔⛔ The cost is not the lines. It is three restated claims.

**(a) Q3 = 1 changes meaning.** *"A fixed scene has exactly one canonical form"*
becomes *"one form per denotation-class"*, and scenes-per-form becomes a new
quantity — which **is** the ambiguity Lever 4 wants. Not a bug, but Q3=1 is
quoted as a headline and would need restating everywhere.

**(b) Phase 6's semantic-drift measure needs restating.** *"The message stops
being grounded to its target"* presumes the utterance determines the target.
With a residue it never does — it denotes a **set** — so *grounded* becomes
*"the denotation-set contains the target"*. Weaker, still exact, still
checkable. ⛔ **The isolation claim survives in modified form, and the
modification must be recorded before anything leans on it.**

**(c) ⭐⭐ THE NOVELTY COUNTER FORKS, AND THIS IS THE BLOCKING DECISION.**
R is computed on π(scene). Two scenes differing only in residue project to the
same view, so:

- **residue OUT of R** → the counter is blind to a distinction the speaker can
  actually perceive. It under-counts novelty.
- **residue IN R** → free novelty from wiggling something nobody can read. **That
  is precisely the noise failure π was built to prevent** — `denote.py` says so
  in its own docstring: *"projecting only the listener's view would trade the
  cipher failure for the noise failure."*

**Neither branch is free.** 12.2b is not blocked forever; it is blocked on this
decision, and the decision is the specified next phase.

## 12.2c — pivot axes, named regardless

- **Random residue** → predicted **empty**. Nothing to convention on; a listener
  can only learn to ignore it.
- **Structured residue** → the Pictionary case, and the live hypothesis. The
  inexpressible component has internal regularities the grammar cannot name but
  a listener could learn.
  ⭐ **Concretely, "structured" means the residue is drawn from a space with its
  own metric** — so nearby residues get gestured at similarly — **rather than
  from a free categorical dimension.** That is the difference between a code and
  a gesture, and it is why Pictionary works.

---

## Where the lever hunt stands

| lever | status |
|---|---|
| 1 — selection | dead on mechanism *(prior)* |
| **2 — depth/nesting** | **DEAD ON PART 1, structurally. $0.00, no hash moved.** |
| 3 — grammar lossiness | not standalone; substrate for 4 |
| **4 — source-lossiness** | **architecture-blocked on a named decision, not on feasibility** |

⭐ **This is the "specified next phase, banked" gate outcome, not a terminus.**
Lever 4 is architecturally real — the change is five small edits — and what
stops it today is a genuine design fork about the novelty counter that nobody
had to face before, because until now denoting and expressible were the same
thing.

## Do not quote

- **"Depth was measured and found weak."** It was refuted structurally; no
  depth-4/5 set was built and none needs to be.
- **"Lever 4 works."** Nothing was built or trained. Part 1 would be true *by
  construction* and part 2 — conventionable vs empty — is **unmeasured**.
- **Any claim that the residue is conventionable.** That is the whole open
  question and the Pictionary framing is a hypothesis, not a result.
- Conservation, in any form. Phase 12 measures none of it.
