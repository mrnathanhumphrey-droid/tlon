# MUTATION TEST — the M-adjacency relation (RULING 9)

**Run 2026-08-26. $0, paper, no box.** Executes RULING 14 against the block table
derived in RULING 9 of `SPEC_DISCOURSE_LAYER_v0.1_2026_08_25.md`.

---

## ⛔⛔ PREREG INTEGRITY — THE BLINDNESS WAS NOT ACHIEVED. SAID FIRST.

RULING 14 requires the mutation test be pre-registered **against the EMPTY
table**, because *"a plausible adjacency table looks exactly like a forced one."*

**That did not happen.** The derivation (RULING 9) and the assignment (RULING 14)
arrived in the same message, so the verifier read all twelve cross-block cells
and their forcing reasons before writing any prereg. **This review is not blind
and must not be described as one.**

⭐ **WHY IT IS STILL WORTH SOMETHING.** The failure mode of a contaminated
verifier is *agreeing with what it was shown*. The mutation test is the one
protocol that is adversarial by construction: it does not ask "is this cell
plausible?", it asks **"can the same four-way grouping justify the OPPOSITE
cell?"** A verifier biased toward the given answer makes that test HARDER to
pass, not easier — every inversion it manages to write is a finding it was
predisposed against. The test can therefore still come back negative, and below
it does, on six of twelve cells.

⛔ **WHAT IS PERMANENTLY LOST:** the count. A blind prereg would have let us say
"N cells were predicted before reading." That number does not exist and cannot be
reconstructed. Any future adjacency derivation gets a blind pass or none.

## THE TEST

For each cross-block cell, write the **strongest** forcing story for the
inversion, using **only** the four-way grouping (Direct · Mediated · Withdrawn ·
Irreal) and the source ontology. Then:

- **FORCED** — the inverted story is materially weaker; the grouping picks a side.
- **PICKED** — both stories stand; the grouping does not decide, and the cell is
  taste. Per RULING 14: re-derive or mark undetermined.

Blocks (frozen lexicon, RULING 1 spellings):
Direct `xöl` `hrix` `ten` · Mediated `plun` `mar` ·
Withdrawn `nem` `hrin` · Irreal `xos` `mir` `frax`

---

## RESULTS — 6 FORCED, 6 PICKED

| cell | given | inversion story | verdict |
|---|---|---|---|
| D→M | S | *"Perception becoming memory is the arrow; nothing about the grouping resists it."* Inversion has no material. | **FORCED** |
| D→W | S | *"You asserted contact; withdrawing it is a reversal of your own act, not a continuation."* Real, but doubt-after-perception is the ordinary case. Weaker. | **FORCED** (weakly) |
| D→I | ✗ | *"`xöl`→`frax` — seeing then fearing — is entirely ordinary. So is seeing then wishing."* As strong as the original. Original is true of `xos` only. | ⛔ **PICKED** |
| M→D | ✗ | *"Recall, then look. `mar`→`xöl` is the structure of recognition and one of the commonest epistemic sequences there is."* Stronger than the original. | ⛔ **PICKED** |
| M→W | S | Inversion has no material — inference softening into doubt is the paradigm case. | **FORCED** |
| M→I | ✗ | *"`plun`→`frax` is the structure of anxiety; `mar`→`mir` is nostalgia."* As strong. Original true of `xos` only. | ⛔ **PICKED** |
| W→D | ✗ | *"Doubt resolved by looking is how doubt ends."* And see finding 2 — W→M is granted on reasoning that equally grants this. | ⛔ **PICKED** |
| W→M | S | *"Doubt hardening into a reasoned account runs back up the contact scale."* Weaker; but the cell is inconsistent with W→D (finding 2). | **FORCED**, inconsistently |
| W→I | S | *"Withdrawn is contact HELD IN SUSPENSION — `nem`/`hrin` are stances toward a happening that presented itself. Irreal never had contact. This is the D→I shock arriving one band later."* As strong. **Nate's own flagged priority target.** | ⛔ **PICKED** |
| I→D | S | *"The largest jump in contact there is, skipping two bands. If M→D is against the arrow, I→D is more so."* As strong. The waking story is `xos`-only — `mir` and `frax` do not wake. | ⛔ **PICKED** |
| I→M | ✗ | *"The dream remembered AS a dream is `xos`→`mar` and is ordinary."* Comparable. | **FORCED** (weakly) |
| I→W | S | *"Was that real?" is the canonical exit from the irreal and the only one that does not assert contact.* Inversion has no material. | **FORCED** |

---

## ⭐⭐ FINDING 1 — THE IRREAL BLOCK IS NOT A BLOCK. IT IS THE CAUSE OF FIVE OF THE SIX FAILURES.

Every one of the six Irreal-touching cells is justified by reasoning that holds
for **`xos` (dreamt)** and does not hold for **`mir` (wished)** or **`frax`
(feared)**:

| cell | stated reason | true of `xos`? | true of `mir` / `frax`? |
|---|---|---|---|
| D→I ✗ | "un-anchored generated" | yes | **no** — seeing then fearing is ordinary |
| M→I ✗ | "contact-derived → un-anchored" | yes | **no** — inferring then fearing is anxiety |
| I→D S | "the dream yielding — the waking arrow" | yes | **no** — a wish does not wake |
| I→M ✗ | "dream→memory-as-fact skips withdrawal" | yes | **no** |
| I→W S | "'was that real?'" | yes | partly |
| W→I S | "suspended-contact → absent-contact" | yes | **no** — a fear is not absent contact |

**Six of twelve cross-block cells — half the derivation — rest on one of ten
forms.** `xos` is *un-anchored generation*: a happening with no contact at all.
`mir` and `frax` are **affective/prospective stances toward a happening**, and a
stance attaches to any level of contact — you can fear what you saw, what you
inferred, and what you doubt.

⇒ **The grouping is what needs the mutation test, not the cells.** RULING 9's
block-level discipline is correct precisely *because* a bad block propagates to
every cell in its row and column, and that is what happened here. The 4-way
grouping is inherited from v0.1 §4, and v0.1 has now produced five wrong
spellings, one category error (ρ_wide), and a codomain over a deleted space. **It
has never itself been red-teamed.**

**Shape of the fix (Nate's derivation, not the verifier's):** split Irreal into
**Generated** (`xos` — no contact, genuinely a band on the contact axis) and
**Affective** (`mir`, `frax` — a stance orthogonal to contact, plausibly
adjacent to everything in both directions). That gives 5 blocks / 25 block
decisions, and it dissolves five of the six PICKED cells by construction rather
than by re-argument.

## ⭐ FINDING 2 — W→M AND W→D ARE INCONSISTENT WITH EACH OTHER

- **W→M is S**: *"doubt resolving toward a reasoned account."*
- **W→D is ✗**: *"doubt → fresh perception, against the arrow."*

Both are Withdrawn resolving upward in contact. The reason granted to one is
denied to the other with no principle separating them. **A forcing story that
defeats its own neighbour is not forcing.** Either doubt can resolve upward (both
S) or it cannot (both ✗).

## ⭐ FINDING 3 — THE "ARROW OF CONTACT" DOES NOT ORDER WITHDRAWN, YET FIVE ✗ CELLS INVOKE IT

Read the table's own S-pattern:

- **everything → Withdrawn is S** (D→W, M→W, I→W) — universal sink
- **Withdrawn → M and → I are both S** — and M↔W and W↔I are the **only two
  bidirectional cross-block pairs in the table**, both involving Withdrawn

Withdrawn behaves as an **orthogonal hub**, not a band on a linear contact scale.
But the ✗ cells (M→D, W→D, D→I, M→I, I→M) are justified by *"against the arrow"* —
an ordering that the table's own structure shows does not place Withdrawn on it.
**The principle that forbids five cells is not the principle that generates the
other seven.**

## ⭐ FINDING 4 — `S†` IS A BLANKET, NOT A DERIVATION (16 CELLS)

The within-block diagonal is declared `S†` = *"non-self morphs smooth"* for all
four blocks. That is **16 ordered cells** (Direct 6 · Mediated 2 · Withdrawn 2 ·
Irreal 6) set by a default that was never argued — and RULING 9's own named
exceptions attack it from two directions:

- exception 1: `hrin`→`nem` (hardening) vs `nem`→`hrin` (softening) — **within-block
  may itself be directed**, which `S†` forbids by fiat
- exception 2: `frax`→`mir` reverses affective valence — may be a shock within-block

If either exception holds, `S†` is false as stated. **16 of 90 live cells are
currently duct tape**, and it is the quiet kind: a blanket default reads as
structure because it is uniform.

## ⭐ FINDING 5 — THE JOINT-CELL COUNT IS 204, NOT ~300 (RULING 11 ARITHMETIC)

With the diagonal excluded (RULING 8), **90** ordered pairs remain live. Under the
RULING 9 table: **57 smooth** (41 cross-block + 16 within-block) and **33 shock**.

RULING 10 checks morph **before** force, so:

- a **smooth** pair carries three moves — ABIDE (`ka`/`ki`/`ko`), CLOSE (`ku`),
  BREAK (`kä`) → 57 × 3 = **171** cells
- a **shock** pair collapses to BREAK regardless of force → **33** cells

⇒ **204 joint (m→m′, move) cells to floor**, not the ~300 estimated from
10 × 10 × 3.

⚠️ **The floor is not uniform and RULING 11 should know the shape before the
fraction is set.** With an abide-dominant marked-move ratio (say 80/10/10), the
57 CLOSE cells and the 90 BREAK cells each share a tenth of the transitions while
57 ABIDE cells share four fifths — **the marked-move cells run ~4× thinner than
the abide cells before any floor is applied.** The floor binds on CLOSE and
BREAK, and setting it from an average would starve exactly the cells the marked
moves exist to teach.

---

## ⛔ WHAT WAS DELIBERATELY NOT DONE

**No `tlon/discourse/adjacency.py` was written.** Encoding a table that just
failed its mutation test on half its cells would be the identical failure
`base_convention`'s refusal was written to prevent: a plausible default that gets
measured downstream and reported as a result. The refusal held for §8.1 for eight
days. It applies to the verifier's own hands.

## VERDICT

**6 FORCED · 6 PICKED · 16 cells undetermined (`S†`) · 1 internal inconsistency ·
1 principle that does not order its own hub.**

The derivation is not ready to be an oracle, and the reason is upstream of every
individual cell: **the 4-way grouping puts un-anchored generation (`xos`) in the
same block as two affective stances (`mir`, `frax`), and half the table is
`xos`'s reasoning applied to all three.**

⇒ **Blocks first, then cells.** Red-team the grouping — which has never been
tested and has carried three defects already — and the block table gets re-derived
over whatever survives. Build order item 1 is not complete.
