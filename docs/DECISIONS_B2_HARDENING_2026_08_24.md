# DECISIONS — B2 hardening pass, 2026-08-24

One file for one arc. Every entry: **DECISION · EVIDENCE · REJECTED · sha**.
The retractions are in here too, at the bottom, because a trace that only
records the things that worked is a highlight reel.

**Scope:** harden the two claims the product makes to a stranger — the refusal
and the compatibility reveal — so both are provably true, and sweep the input
boundary now that the door is open. **Not a feature pass.** The literary render
and the conversant stayed parked.

**Gates at close:** 676 tests (was 627) · 10/10 preregs VERIFIED · red-proof
**7/7 mutations CAUGHT** · live corpus audit 5/5 rows clean · `tools/chat.py
--offline` renders at **$0.00**.

| file | sha256 |
|---|---|
| `tlon/product/schema.py` | `96caf184ad8b72d6` |
| `tlon/product/chat.py` | `86a0503da1138d19` |
| `tlon/product/corpus.py` | `6b9d7c6280a7da30` |
| `tlon/product/compat.py` | `6cec97a7790b6f10` |
| `tools/chat.py` | `4d24dbbced285ef9` |
| `tools/writefile.py` | `917c3d8c2176011d` |
| `tests/test_product_hardening.py` | `c834b50d20944fbf` |
| `tests/test_product_frontend.py` | `924918a467b2c3b5` |

---

## D1 — π-exactness is certified by TWO independent instruments, not one

**DECISION.** Certify "Tlön cannot tell them apart" with (a) a per-part mutation
sweep derived from `denote._ALL_PARTS`, and (b) a partition test asserting
`compatible_with` returns *exactly* the π-class.

**EVIDENCE.** (a) covers `impression()` being π; (b) covers the grouping being
the class *induced by* `impression()`. They are different claims and neither
implies the other. Sweep result, one part mutated at a time against a base scene
exercising every part: `root`, `orient`, `aspect.root`, `edges` → **separate**;
`aspect.reps`, `degree`, `modal`, `tense`, `quant`, `force` → **collapse**.
Matches `denote.denoting_parts()` / `nondenoting_parts()` exactly.

**REJECTED.**
- *Two hand-picked cases (one equivalent pair, one distinct pair).* Passes on a
  fuzzy grouping as long as the distinct pair happens to be far apart. The
  interesting failure is the **near miss**, and only a per-part sweep guarantees
  one of those exists for every part.
- *Reading the code and asserting no `abs()`/`isclose()` appears.* A source
  search is satisfied by absence of a spelling, not absence of the behaviour.
  The real argument is structural: an impression id is a 128-bit blake2b digest,
  **a digest admits equality and no other comparison**, so a threshold cannot be
  written here even by someone trying.

## D2 — `residue` is EXEMPTED from the sweep, and the exemption is asserted

**DECISION.** The sweep covers `_ALL_PARTS` minus `residue`; a separate test
asserts product Scenes never carry one, and the coverage guard asserts the
difference is **exactly** `{"residue"}`.

**EVIDENCE.** `schema._node` hard-sets `residue=None`; `render()` structurally
cannot emit one, so a product Scene carrying one would not be reproducible from
its own surface.

**REJECTED.** *Silently skipping it.* A skip is indistinguishable from an
oversight six months later — and this project has already been bitten by a test
that **silently skipped** rather than failing.

## D3 — over-long input is REFUSED, never truncated

**DECISION.** `MAX_ENGLISH_CHARS = 2000`. Above it, refuse with an in-voice line
and log `stage="input"`. No truncation anywhere.

**EVIDENCE.** A clipped input logged beside a Scene that was never a rendering of
the whole of it is a row that validates, round-trips, and misrepresents its own
relation — the `mode`-field hazard, in the field that carries the meaning.
Refusing costs a visitor one retype; truncating costs Route B a poisoned pair
nobody can find later.

**REJECTED.** *Truncate-and-say-so* (offered in the brief). Saying so protects
the visitor, who can see the message; it does nothing for the corpus row, which
is the thing that outlives the session.

## D4 — input is normalised ONCE, at the door

**DECISION.** `PS.flatten()` at the top of `render_english`; that one string goes
to the proposer, the corpus row and the display.

**EVIDENCE.** The pair is then true **by construction** — there is no second
version of the input for the three to disagree about. `flatten` and `clip` are
deliberately separate functions: model-written display text may be clipped, a
user's input never may.

**REJECTED.** *Store raw, clean at display.* Two representations, and the corpus
row would then be a pair the proposer never saw.

## D5 — order-insensitive slots are canonicalised in `_node`

**DECISION.** Sort `orient`, and sort `edges` on render's own key, before the
round-trip gate.

**EVIDENCE.** Demonstrated on the machine: `orient: [fen, nar]` rendered while
`orient: [nar, fen]` was **REFUSED**, with `canon_node` equal for both. Same for
sibling clauses. `render` sorts both slots, `canon_node` sorts both slots,
`fiber_size` counts the permutations as one scene (Q3 = 1).

**⛔ NOT ATTRIBUTED.** The known "2 of 3 first live renders took a retry" is a
tempting match, and it is **not evidence**: those renders predate refusal
logging and **no `refused.jsonl` exists on the machine**. The defect stands on
its own demonstration; the attribution does not, and is not claimed.

**REJECTED.**
- *Leaving it.* Each occurrence burns a hosted retry, and two unlucky proposals
  show a visitor "Tlön could not hold that" for input Tlön holds fine.
- *Weakening the gate to `canon_node(back) == canon_node(scene)`.* That would
  make the runtime check strictly weaker than `parse(render(s)) == s` in order
  to fix an input-side problem. Canonicalising the input keeps the gate an exact
  identity.

**Guard against "this is a silent repair":** repair changes what the model
*meant*; this picks the canonical representative of an equivalence class the
grammar already defined, and
`test_canonicalising_the_slots_is_MEANING_PRESERVING_not_a_repair` asserts
`canon_node` is unchanged by it.

## D6 — unreadable corpus rows are counted and disclosed

**DECISION.** `Compatibility.unreadable`, surfaced in `reveal()`.

**EVIDENCE.** The previous `except Exception: continue` made the reveal state a
smaller set as if it were the whole one. An under-report is a lie too, just a
quieter one than an over-report.

## D7 — the empty case is ARRIVAL, not emptiness

**DECISION.** "The first saying to land on this impression." `0` and `1` are
structurally unreachable — the count renders only past the early return.

**EVIDENCE.** At 5 corpus rows the empty case is what **most** visitors will
hit. "Compatible with 0 things" reads as a broken feature; being first is both
true and the more interesting fact.

## D8 — `stage` on refusals; `proposal_acceptance_rate` renamed

**DECISION.** `REFUSAL_STAGES = ("input", "parser")`, required, no default.
Acceptance rate computed on parser-stage only and **renamed to say what it is**.

**EVIDENCE.** Pooled, the rate drifts with how much junk gets typed at the door
— a fact about visitors, not about the translator. And it was always
per-proposal, not per-message (a rescued message contributes one acceptance AND
one refusal): **put the caveat in the name, not in prose beside it.**

## D9 — `corpus.audit()` reads the FILE

**DECISION.** Re-read every accepted row and require the three views to agree:
`parse(surface) == scene_from_canon(row.scene)`, matching `utterance_id`, known
mode, frozen lexicon. Wired into `/corpus`.

**EVIDENCE.** The dangerous row is the one that is well-formed AND
misrepresents itself; no schema catches that. Red-proofed with a planted liar
(legal mode, parseable surface, decodable scene, surface **not** a rendering of
that scene) — caught — and with a clean sweep — not flagged. Live corpus: 5
rows, all pass.

**REJECTED.** *Asserting the writer is correct.* That restates the code that
wrote the rows instead of checking the rows.

## D10 — `tools/writefile.py` is the VERIFY half, and says so

**DECISION.** Ship `check` (sha256, byte count, LF/CRLF/lone-CR census, BOM,
stray controls) and `write` (stdin **bytes** → file, `--force` to overwrite,
prints the old sha first).

**EVIDENCE.** Both recurring failures — heredoc `\n` mangling and
`Get-Content | Set-Content` destroying a source file — share one shape: content
passed through a text layer that felt entitled to rewrite it. Run on all 8
touched files this pass: all clean UTF-8, LF-only, no BOM, no stray controls.

**⛔ HONEST LIMIT, STATED IN THE MODULE DOCSTRING.** It **does not make heredocs
safe** — content is already mangled before it reaches stdin. What actually kills
that papercut is authoring files with the editor tool (no shell in the loop) and
running `check`. Claiming otherwise would be the same mistake in a new costume.

---

# RETRACTIONS

## R1 — my own certificate was self-confirming, and the red-proof caught it

`test_the_group_is_EXACTLY_the_equivalence_class` originally computed its ground
truth by calling `compat.impression()` — **the function under test**. Under the
coarse-π mutation (impression → top root only) it **passed**, because expectation
and result moved together. Ground truth now comes from
`utterance_id(project(...))` directly; the mutation then fails 5 tests instead
of 4.

**A verifier that reimplements the same fold is not a verifier.** This is the
Ohtani-61 shape, in a test I had just written and would have reported as the
certificate for the product's central claim.

## R2 — a vacuous assertion shipped into the first draft of the sweep

`assert r.english == "..." or True` — trailing `or True` makes the line
unconditionally true. Caught on re-read before the suite ran; replaced with
assertions on what the normalisation actually guarantees (no ESC, no newline, no
NUL, no tab, no doubled space).

---

# STILL PARKED — correctly

- **The literary render** (B2's second surface, where the craft lives).
  ⛔ **The austere gloss stays frozen — it was the measurement instrument.**
- **The conversant** — its own phase, entered with **stance-without-speaker** as
  the design centre, not "chat but in Tlön". `docs/SCOPE_CHATBOT_FRONTEND.md` §8.
