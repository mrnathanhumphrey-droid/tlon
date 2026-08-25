# 9.0 — The comparison guard is live. Phase 9's gate is OPEN.

**Date:** 2026-08-23 · **Spend:** $0.00, all local · **No prereg** — this is
build, not a measurement claim. The gate is the red-proof's exit code.

**Code:** `tlon/harness/paired.py` (new package `tlon/harness/`)
**Red-proof:** `tools/guard_redproof.py` → **exit 0**
**Suite:** `tests/test_paired.py`, 20 tests. **492 → 512 tests, all passing.**

---

## Why this is code and not another lesson

The unpaired comparison is the project's recurring error — **five instances**,
three costumes:

| # | Where | What it did |
|---|---|---|
| 1 | Phase 3 | Contaminated cipher control: a **scrambled subset** vs a **full-set** baseline. Manufactured a **−1.35 pt** drop on a channel that is provably a no-op. |
| 2 | Phase 7 (D10) | Auditor "floor curve": one point per withholding rate, **each a different item set**. Read flat → I concluded the auditor ignored withheld content. Paired: **42.8 % vs 34.9 % = 7.9 pts, 3×**. Conclusion **RETRACTED**. |
| 3 | Phase 8.3a | Teachability "spike": windows **before/after within one run**. Entropy declines monotonically as training converges, so the trend swamped the transient. Read **−7.0 %**. Uninterpretable. |
| 4 | Phase 7 (pre-pairing) | The same error upstream of D10, in how the floor was constructed. |
| 5 | Phase 8.2 | Sibling failure — the classifier that would have caught the trajectory was written and never called. |

It was **written into two verdicts as a lesson and committed again after both.**
A lesson in a verdict does not hold. This is the same move as root allocation
going from hand-typed to deterministically generated: the goal is that the error
becomes **unexpressable**, not that it is remembered against.

## The mechanism

A bare float carries no record of what it covers, so `a - b` can always be
typed. So measurements are not bare floats.

- **`ItemSet`** — the identity of what was measured over. `digest` is
  `sha256` over the **actual sorted item keys**, never a label the caller types,
  so two genuinely different sets cannot be declared paired by naming them the
  same thing. Refuses an **empty** set (two empties compare equal, silently
  pairing two vacuous numbers) and **duplicate keys** (a repeated key does not
  identify an item, so "the same items" cannot be established).
- **`Measurement`** — value + its `ItemSet`. **`__sub__` refuses**, in both
  directions, and points at `paired_delta`.
- **`paired_delta(a, b, contrast=...)`** — the only way to get a difference.
  `contrast` is **required**: the caller must name the one thing allowed to
  differ. Five conditions, each with its own error:
  1. item **kinds** identical
  2. item **digests** identical *(error prints the symmetric difference)*
  3. both sides declare the **same facet names** — a facet on one side only is a
     condition nobody checked
  4. the named **contrast is a declared facet**
  5. **every other facet identical** → else `ConfoundedContrast`
  6. the **contrast actually differs** → else `DegenerateContrast`
- **`measure(name, kind, items, fn, ...)`** — iterates the item list itself and
  hands *that same list* to the scoring function, so the recorded identity
  **cannot drift from what was actually scored**. Anything built by hand can.
- **`side_by_side(a, b, reason=...)`** — for comparisons that are unpairable by
  construction (9.2's old-set vs new-set: different referents, no pairing
  exists). Holds both, demands a written reason, and **`.delta` raises**.
  It also **refuses an actually-pairable comparison** — if a pairing exists you
  do not get to opt out of the check.

⭐ **`DegenerateContrast` is not decoration.** It catches the shape that produced
Phase 5's frozen-arm shift of **0.00 BY CONSTRUCTION** — the naive judge was
byte-identical to the arm's listener, so a difference between a thing and itself
went into a table as a measured null.

## The red-proof, and why it is not "assert it raises"

A guard that raises on the cases you wrote for it is not evidence — the cases
might raise for reasons unrelated to the guard, and then the guard is decorative
and the battery is theatre. So the battery runs **twice**:

| | requirement | result |
|---|---|---|
| **A** 8 unpaired cases vs the **real** guard | every one RAISES | ✅ 8/8 |
| **B** same 8 vs a **decorative** guard that only subtracts | every one **computes a number** | ✅ 8/8 |
| **C** 2 legitimate pairings vs the real guard | must NOT raise | ✅ 2/2 |
| **D** empty / duplicate item keys | refused | ✅ |
| **E** `SideBySide.delta` | raises; refuses a pairable comparison | ✅ |

**B is the mutation** and it is what proves the battery is sensitive to the
guard rather than to an accident of its own construction. The decorative guard
reproduces the historical numbers exactly — **−1.35 pts** on the phase-3 case,
**+12.90** on the phase-8.3a case. If a case had also raised under the
decorative stand-in it would be reported **UNINFORMATIVE**, not as a pass.

⭐⭐ **The gate was then broken on purpose and the exit code watched**
(`[report≠gate]`: a report becomes a gate the moment it enters CI, and six
suites once *saw* a failure, *printed* it, and exited **0**). With
`paired_delta` monkeypatched to the decorative version — mutation asserted
applied, per `[redproof_assert]` — `guard_redproof.py` **exits 1** and names all
eight cases. It is a gate, not a report.

## ⛔ Scope — what is NOT guarded

**Phases 3–8 tools were not retrofitted.** The guard is live for Phase 9 code.
No number in any existing verdict passed through it, and none should be
described as if it had. Retrofitting is not free and Phase 9 explicitly does not
re-run 8.2 or 8.3a — those re-runs, when they happen, go through the guard.

**Python cannot forbid `a.value - b.value`.** The enforcement is that Phase 9's
measurement functions **return `Measurement`, never `float`**, so a raw
subtraction at the comparison site raises rather than computing. That is a
strong default, not a proof.

**The guard checks identity, not provenance.** `measure()` ties the keyed list
to the scored list; an `ItemSet` built by hand asserts a claim the guard takes
on trust. Prefer `measure()`.
