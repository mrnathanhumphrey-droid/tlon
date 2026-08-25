# DECISIONS — the literary render, 2026-08-24

**DECISION · EVIDENCE · REJECTED · sha.** One file for one arc.

**Scope:** B2's second surface. A new, separate Scene→English function producing
the surface a visitor experiences. `grammar/gloss.py` is untouched — it is the
measurement instrument and the honest surface. Same Scene, two surfaces,
inviolable wall.

**Gates at close:** 738 tests (was 676) · 10/10 preregs VERIFIED · literary
red-proof **8/8 mutations CAUGHT** · B2 hardening red-proof still **7/7** ·
live corpus audit 5/5 clean · `tools/chat.py --offline` at **$0.00**.

| file | sha256 |
|---|---|
| `tlon/product/literary.py` | `2f9797b49211519e` |
| `tlon/product/chat.py` | `1473c1b2f67e4faf` |
| `tools/chat.py` | `587bd0778dbdba4b` |
| `tests/test_literary_render.py` | `37c911699499e4e4` |
| `tlon/grammar/gloss.py` **(UNCHANGED — the instrument)** | `b06bdf4d7bcee5e4` |

---

## D1 — the reveal opens onto the LITERARY render, and it stays NOUNLESS

**DECISION.** `/reveal` (behind *"are you sure you want to ruin the puzzle?"*)
shows the literary render. `/austere` goes one level deeper to the gloss.

**EVIDENCE — Nate, verbatim.** *"the reveal is the literal english translation of
what it said. it still isn't normal english. it is the high gloss nounless
english instead of the cypher. at first all they get is the cypher. nonsense. a
puzzle. something pronounable without being comprehensible — but it could be
solvable if someone thought about it right."*

⛔⛔ **THE CORRECTION THAT MATTERED MORE THAN THE WIRING.** The brief's own
example — *"a pressing that rises again, from one who looms above"* — contains an
AGENT. "One who looms" is a doer, and a doer is exactly the permanence Tlön
refuses. The puzzle must not resolve into ordinary speech; it resolves into a
language with no objects in it. `test_the_render_NEVER_supplies_an_agent` bans
"one who", "someone", "a person", he/she/they/him/her/them, "that which",
"whoever" across the whole scene set.

## D2 — the register is BORGES' OWN, and the lexicon already encodes it

**DECISION.** Embedded happenings nominalise to gerunds; the head happening stays
an impersonal verb and comes last; orientations lead as bare adverbs.

**EVIDENCE.** `Hlör u fang axaxaxas mlö` — and the frozen lexicon has `hlör` =
upward, `u` = BEYOND, `fang` = it streams, `mlö` = it moons. Borges renders it
*"upward, behind the onstreaming, it mooned."* Ours, from the same Scene:

> **"Upward, beyond a streaming and flowing on, it moons and lunates."**

A gerund is not a thing — it refers to a happening without positing anything that
has it — which is the only kind of reference this language permits.

## D3 — faithfulness is PROVED as partition equality against the gloss

**DECISION.** The certificate is: `partition(literary) == partition(gloss)` over a
deterministic 260-scene set covering **every item of every lexicon class**.

**EVIDENCE.** Left-to-right failure would mean the render collapses a distinction
the gloss keeps (two impressions, one pretty sentence). Right-to-left would mean
it asserts a distinction the gloss does not make (meaning invented by
arrangement). Ground truth is `gloss()` — a function this module does not
implement and cannot influence, which is the fix carried over from the B2
retraction. A second guard asserts the scene set really exercises every class, so
the partition claim cannot go quietly narrow.

**REJECTED.** *A "reads faithfully" review.* Craft is not auditable by reading;
the partition is.

## D4 — the latitude clause, pre-registered

**DECISION.** The render **may** vary in HOW it says an impression — arrangement,
rhythm, which coda voices the force. It **may never** vary in WHICH impression it
says. D3 is the line, and it is mechanical.

## D5 — every phrase of a root gloss is rendered, because of a collision

**DECISION.** `_verbs()` emits all comma-separated phrases, not just the head.

**EVIDENCE.** 156 roots, **155 distinct head verbs**. `nöl` = "it stills,
silences" and `hläx` = "it stills, goes unbreathing". Head-only rendering fuses
two π-DISTINCT scenes into one identical sentence — the reveal claiming Tlön
hears one impression where it hears two.

## D6 — embedded scope is bounded by em-dashes, because of a second collision

**DECISION.** A child with modifiers renders as `a streaming — beneath, toward a
gladdening —`; a bare child renders bare.

**EVIDENCE.** Found while designing the tests, before writing them. The gloss
marks embedding with `⟨...⟩`; prose has no brackets, and without a boundary these
two different scenes are the same sentence:

| scene | without a boundary |
|---|---|
| `X ← AT(Y ← TOWARD(Z))` — Z hangs off Y | "at a Y-ing, toward a Z-ing, it Xs." |
| `X ← AT(Y), TOWARD(Z)` — both hang off X | "at a Y-ing, toward a Z-ing, it Xs." |

**REJECTED.** *Tight attachment by omitting commas.* Reads as a run-on the moment
a child has more than one modifier, and the ambiguity returns for aspect and
frames. **Cost accepted:** a single short modifier reads a little stiff
("— across —"). Unambiguity beats it.

## D7 — force becomes a sentence-final CODA, not a parenthetical

**DECISION.** ASSERT `.` · ASK `— is it so?` · WONDER `— a wondering.` ·
URGE `— an urging.` · DENY `— and it is denied.`

**EVIDENCE.** Tlön puts the force morpheme **last**, so the shape of the English
mirrors the shape of the utterance. Every content word in a coda is the gloss's
own force word, so voicing the force names nothing new. ⭐ This is the seed of
**stance-without-speaker** the conversant will be built on: an illocution with no
one performing it.

## D8 — aspect repetition is ICONIC

**DECISION.** reps *n* → the aspect phrase plus *n*−1 echoes drawn from that
aspect's own gloss words.

**EVIDENCE.** Tlön repeats the morpheme (`tes` → `testesas`), so the English
repeats the word: *"it dims, guttering out, and guttering, and guttering."* A
guttering thing fades in the prose. It also keeps reps recoverable from the
render, which is required for D3 — the gloss shows `(×n)`, so the literary
surface must distinguish them too.

## D9 — no model call, asserted rather than assumed

**DECISION.** `literary.py` imports only from `tlon.grammar`. A test greps the
module for `anthropic`, `requests`, `urllib`, `http`, `socket`, `openai`,
`Proposer`, `api_key`.

**EVIDENCE.** A model call would make this **ungated text** — the
`note`/`refused_objects` category, the one surface the parser cannot vouch for —
and it could drift from the Scene. Faithfulness here is *inherited* from being a
pure function of the Scene; a model call severs the inheritance.

## D10 — no added meaning, as a mechanical claim

**DECISION.** Every content word must appear in the gloss **of the same scene**,
up to inflection. The renderer's own vocabulary is a 30-word closed set of
function words.

**EVIDENCE.** `_REL` and `_ASP` are **imported from `gloss.py`**, not re-spelt —
one source of truth, and every relator and aspect word is gloss-justified for
free. The one inflection the literary surface performs that the gloss does not is
the gerund, and a separate test proves `gerund()` is inflection and not
invention: `g[:-3]` must be the stem under one of four documented transformations.

⛔ **THAT SECOND TEST CLOSES A HOLE IN THE FIRST.** The justified-words test
admits whatever `gerund()` produces, so a `gerund()` that returned a different
word entirely would license that word. Red-proofed by making `"rains"` return
`"snowing"`.

## D11 — the instrument is pinned by BEHAVIOUR, not by a file hash

**DECISION.** Five hand-written golden `(scene → exact gloss)` pairs, plus a
sha256 over the gloss of the whole 260-scene set.

**EVIDENCE.** A file hash would fail on a comment edit and pass on a behavioural
change made elsewhere. What must not drift is what `gloss()` SAYS. Red-proofed by
changing `_ASP["punctual_iterated"]` to "over and over" — both guards fired.

---

# ACCEPTED IMPERFECTION

**"it extremely rains."** Degree adverbs sit pre-verbally ("it strongly warms",
"it markedly stills", "it faintly gleams"), which is the more literary position
and correct for five of six degrees. `extreme` → `extremely` is the outlier,
since it wants an adjective. Moving all degrees post-verbally would fix that one
case and strand the adverb far from the verb on the 31 roots whose gloss has two
phrases. Kept pre-verbal: wrong in fewer places, and a marked adverb in a
deliberately strange register is not a defect.

---

# STILL PARKED — correctly

- **The conversant** — its own phase, entered with **stance-without-speaker** as
  the design centre, not "chat but in Tlön". `docs/SCOPE_CHATBOT_FRONTEND.md` §8.
  D7 is now its first working part.
- **Route B** — starts at 2,000 distinct English AND 100/156 roots.
