# SCOPE 2.1 — the English→Scene front end. **DECISION DOCUMENT. NOTHING BUILT.**

**Date:** 2026-08-24 · first open-world component in the project's history ·
first real model spend · **needs Nate's ruling before any build.**

---

## 1 · What exists, verified

| | |
|---|---|
| grammar, parser, renderer | ✅ LL(1), **exactly invertible** |
| denotation + `consistent()` | ✅ exact, exhaustive |
| Scene algebra | `Scene(node, force)`; `EventNode(root, aspect, degree, modal, tense, quant, orient, edges, residue)` |
| listener | ✅ 4.8 M from-scratch |
| **gloss** (`Scene → English`) | ✅ deterministic, and see §4 — it is an asset |
| constraints | MAX_DEPTH 3 · ≤3 clauses/pred · ≤2 orient/pred |
| lexicon | **`e2b8527010231a81fd31b6eeb9de3d8c`**, unchanged — 156 R · 24 O · 12 L · 6 A · 10 M · 6 D · 6 Q · 8 T · 5 F |

## 2 · What is missing

**The map from arbitrary English to a Scene.** The research never needed it —
every phase ran on closed rosters with hand-authored signatures. The chatbot
cannot exist without it.

---

## 3 · ⛔⛔ THE CRUX, AND IT IS NOT THE PARSER

I expected the hard part to be English→structure. It is not; AMR parsers exist
and AMR→Scene is a definable projection. **The hard part is that there is
nothing to project *onto*.**

**The lexicon is 156 impersonal verbs and zero nouns.** Measured semantic fields:

| field | roots |
|---|---|
| unclassified / elemental | 58 |
| body & mind | 29 |
| motion & shape | 23 |
| light & dark | 20 |
| water & weather | 17 |
| life & growth | 9 |

⛔ **Roots plausibly usable for human or social content: 14 of 156** — *speaks,
sings, sees, hears, touches, weeps, laughs, dreams, recalls, forgets, hunts,
flees, crowds, shades.*

So: *"my landlord raised the rent"*, *"what's a good pasta recipe"*, *"the Knicks
lost"* have **no denotation in this language.** An AMR→Scene projection would
faithfully deliver `landlord / rent / raise` and there would be nothing to map
them to. **The coverage bound is the lexicon, not the translator** — and any
plan that scopes the translator without confronting this will build a correct
component that still cannot answer *"can it talk about anything."*

⭐ **This is not a defect. It is the conceit, working.** Tlön has no nouns
because Tlönians cannot refer to objects. A front end that faithfully declines to
denote a landlord, and instead renders something about pressing and enduring, is
**the artifact behaving correctly.** That reframes §6 completely: the coverage
edge is not a failure mode to hide, it is the product.

⛔ **Expanding the lexicon is not a free fix.** Every prereg cites
`e2b8527010231a81fd31b6eeb9de3d8c`; adding roots re-mints it and detaches the
product's language from the research record. If we ever do it, the research
lexicon stays frozen and the product forks — a decision, not a patch.

---

## 4 · ⭐ The asset nobody has used: the gloss is a free parallel corpus

`gloss.py` is a **deterministic `Scene → English`** map, and Scenes are cheap to
sample. So `(English, Scene)` pairs are **free and unlimited**, with a perfectly
clean target:

```
TLON : har nar mil krun sen fox mlö sorsoras tos kä
GLOSS: amid, downward, while ⟨it approaches⟩, at ⟨it pools, lies still and
       level⟩, it moons, lunates, habitually (×2), strongly (denied)
```

⛔ **What it does and does not buy.** It teaches the *inverse of the gloss* — a
supervised, verifiable task with infinite data and an exact correctness check
(round-trip: `Scene → gloss → model → Scene′`, assert `Scene == Scene′`). It
does **not** teach arbitrary English. The remaining gap is
**gloss-English → arbitrary-English**, i.e. paraphrase robustness — a much
smaller and better-posed problem than "English → Scene" from scratch.

---

## 5 · Three routes

| | route | training spend | per-message | ships in | honest coverage |
|---|---|---|---|---|---|
| **A** | **LLM-as-translator** — a hosted model emits a Scene against a JSON schema; we validate with the real parser and reject anything illegal | **none** | ~cents | days | widest; limited only by §3 |
| **B** | **Small local model**, trained on the gloss corpus (§4), paraphrase-augmented | one-off local, ~hours on the 5070 Ti; augmentation is the only API cost | **$0** | weeks | narrower; strongest on gloss-shaped input |
| **C** | **Constrained/templated** — a fixed set of input frames, no model at all | none | $0 | ~2 days | narrow and *stated* |

**Notes that matter for the choice:**

- **A is not "Claude with a markdown."** The grammar, parser, denotation,
  renderer, listener and the invertibility guarantee are all ours; the model does
  one bounded job — propose a Scene — and **every output is validated by our own
  parser**, so it cannot emit anything illegal. But it *is* a hosted dependency
  in the loop, and the project has been $0.00 and fully local to date. That is a
  real change of character and it is Nate's call, not mine.
- **B is the specified plan and it is now cheaper than when it was specified**,
  because §4 removes the data-collection problem entirely.
- **A and B compose:** A ships the door now; its accepted (English, Scene) pairs
  become the training corpus that makes B viable later. **A is not a detour from
  B; it is B's data collection.**

⛔ **The backbone model is Nate's call, every time** (standing rule). I am not
choosing one, and nothing is trained or called until he does.

---

## 6 · The coverage-edge decision — flagged, not decided

An open-world front end will meet input it cannot map. Four behaviours:

1. **Refuse** — *"there is no way to say that in Tlön."* Honest, brittle, and it
   makes the language look poor rather than strange.
2. **Approximate silently** — always render something. Feels smooth; **lies**
   about what was understood, and would quietly wreck the compatibility-set
   reveal (2.2), whose whole point is showing what the utterance *actually*
   left open.
3. ⭐ **Approximate, and say so** — render the nearest expressible impression
   *and* show what was dropped: *"'landlord' has no denotation here; rendered as
   an enduring pressure."* Honest, and it **teaches the visitor the conceit** —
   the reason it can't say landlord is the interesting thing about the language.
4. **Refuse with a redirect** — decline and offer what the language *can* say.

**My recommendation is 3.** It is the only option where the coverage limit
becomes the exhibit rather than an apology for it, and it is the one that keeps
the compatibility-set reveal truthful. **But it is an aesthetic-and-product call
and it is Nate's.**

---

## 7 · What I need before building

1. **Route A, B, or C** — and if A, the **backbone**, with explicit sign-off that
   the project stops being $0.00 and fully local.
2. **Coverage-edge behaviour** — 1/2/3/4 above.
3. **Ship order** — my recommendation: **C or A first as an honest
   limited-coverage door**, with the round-trip validator from §4 as the
   correctness gate, then B once real (English, Scene) pairs have accumulated.

⭐ **What I would do with a free hand, stated so it can be overruled:** ship a
walk-up door on route A with behaviour 3, gate every output through the existing
parser, prioritise the compatibility-set reveal (it is nearly free — `consistent()`
plus the listener — and it is the moment underdetermination becomes visible),
and let the accepted pairs accumulate into B's corpus.

⛔ **Nothing in §2.2 (the encounter) is designed here**, per the sequence: the
front end is the load-bearing unknown and it gets ruled on first. And nothing
from the research scaffolding — residue, arms, ceiling gate, pact measurement,
reset test — goes anywhere near the product.


---

# 8 · ⭐⭐ THE EVENTUAL GOAL — **CONVERSE**, not translate. Banked 2026-08-24.

**Nate, verbatim:** *"my eventual goal is for it to intake english from the user
and then RESPOND in Tlonian. try to converse. a bot that can read english and
tlonian but only responds in the tlonian cypher."*

⏸ **BANKED, NOT SCHEDULED. Nothing here is built and B2 is unchanged.**

## What B1 actually is, stated plainly

**B1 is a TRANSLATOR. It echoes.** English in → the *same content* rendered in
Tlön. `render_english()` produces a Scene that MEANS the user's sentence.

**The goal is a CONVERSANT.** English in → understand → **form a reply** →
render *the reply* in Tlön. The Scene it emits is a **response**, not a
translation of the input. That is a different system, and the difference is a
whole pipeline stage:

```
B1  today :  english --> Scene(english)      --> Tlön
goal      :  english --> understanding --> Scene(REPLY) --> Tlön
             (and: tlön --> parse --> Scene --> gloss --> understanding)
```

## What carries over UNCHANGED — most of it

- ⭐ **The parser gate is untouched and still correct.** It validates *whatever*
  Scene is proposed; it neither knows nor cares whether that Scene translates
  the input or answers it. `parse(render(s)) == s` is the same guarantee.
- The renderer, the frozen lexicon card, the austere gloss, the refusal
  presentation, the retry-on-parser-complaint loop.
- ⭐ **Reading Tlön input is nearly free**: `parse()` → Scene → `gloss()` already
  exists. "Reads Tlönian" is a wiring job, not a research one.

## ⛔⛔ THE ONE HAZARD, AND IT MUST BE HANDLED BEFORE THE FIRST REPLY

**`runs/corpus/accepted.jsonl` currently holds TRANSLATION pairs** —
`(English, Scene that means that English)` — which is exactly and only what
Route B needs to learn. **A conversant emits `(English, Scene that REPLIES to
that English)`.** Those are different relations under identical field names.

> **Mixing them silently corrupts B's training set**, and it corrupts it in the
> way that is hardest to see: every row still validates, still round-trips,
> still looks like a clean pair. B would train on a blend of "say this" and
> "answer this" and learn neither.

**Required before the first conversational reply is logged:** a `mode` field on
every corpus row (`"translate"` / `"reply"`), with existing rows back-filled as
`translate`, and `corpus.status()` counting the B milestone on `translate` rows
only. ⛔ **One field, and it has to go in BEFORE the mode exists, not after** —
this is the caveat-in-the-key rule, and the same class of error as the residue
log that had to be built before the arms.

## What the language CAN and CANNOT do in conversation

**It has the moves.** 5 illocutionary forces — `ka` ASSERT · `ki` ASK ·
`ko` WONDER · `ku` URGE · `kä` DENY — and **10 evidentials** marking how a thing
is known: *seen, heard, felt, remembered, inferred, doubted, feared, wished,
denied, dreamt*. That is an unusually rich stance inventory; a Tlön reply can
assert, question, urge, refuse, and mark its own epistemic footing.

⛔ **It has no deixis.** There is **no root for a person, a self, or an
addressee** — 0 of 156. So the bot structurally cannot say *"I think you are
wrong."* It can only say something like *it is doubted; it errs* — the stance
without the speaker.

⭐ **That is the same conceit as the noun refusal, one level up, and it should be
framed the same way:** the bot cannot address you as a person because Tlön has
no persons, only happenings. A conversation with no *I* and no *you*, carried
entirely on force and evidential, is the strangest and most faithful thing this
system could do — and it is reachable with the lexicon frozen.

## Open questions for when it is scheduled

1. Where does the reply *content* come from — the hosted proposer forming a
   reply directly in Scene, or a two-stage understand-then-render?
2. Does it hold conversational state (prior Scenes as context), and if so does
   that state live in Tlön or in English?
3. The coverage edge on the OUTPUT side: what happens when the reply it wants to
   give has no denotation? (Ruling 2 covers the input side only.)
