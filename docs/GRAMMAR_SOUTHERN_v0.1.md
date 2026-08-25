# Tlönian — Southern Hemisphere Grammar ("Sur")

**Spec version:** 0.2 — Phase 0 gate PASSED, 2026-08-17
**Status:** this document defines the *classes, phonotactics, syntax, semantics, and
canonical form*. The **normative inventory is `tlon/grammar/lexicon.yaml`**
(hash `d55c3e0fc7085becc34632371441eea6`), minted by `tools/mint_lexicon.py`.
Where a surface form in §3 below differs from the lexicon, **the lexicon wins** —
see `deviations_from_spec_v0_1` in that file for every change and its reason.
Changing this document is a versioned event — the decoder pins the lexicon hash.

---

## 0. Design contract

Four properties the grammar must have, in priority order. Everything below is
downstream of these:

| # | Property | Why it matters |
|---|---|---|
| C1 | **Finite, enumerable morpheme inventory** | The mask decoder must be exact, not heuristic. |
| C2 | **Deterministic parse** (LL(1) over morpheme tokens) | Decode must be a function, not a model, at the syntax layer. |
| C3 | **Compositional denotation into an event graph** | Round-trip verification is graph comparison, not string comparison. |
| C4 | **Canonical form under semantic equivalence** | The "never repeated" claim is only auditable if you dedupe on the AST, not the surface string. |

Non-goal: naturalness. Sur is a *constructed* language for a machine to be held to.
It should be *sayable* and Borges-consistent, but the spec optimizes for C1–C4.

---

## 1. Ontology: there are no things, only happenings

Borges, Southern hemisphere: *"no nouns... the world is not a concurrence of objects
in space, but a heterogeneous series of independent acts."* The base unit is the
**impersonal verb**, modified by monosyllabic adverbial particles.

The engineering consequence — and this is the load-bearing decision of the whole spec:

> **Participants are not arguments. Participants are subordinate happenings,
> attached to the matrix happening by a relational particle.**

"The moon rose above the river" is not `rise(moon, above(river))`. It is:

```
[ upward ] [ beyond ⟨ it-streams, unceasingly ⟩ ] it-moons
```

There is no moon and no river. There is a mooning, and beyond-and-below it,
a streaming. This is what makes the grammar recursive without ever needing a
nominal category — and it is why Sur can express arbitrary scenes with zero nouns.

---

## 2. Phonotactics

### 2.1 Syllable template

```
σ  :=  Onset? Nucleus Coda?
```

**Onsets** (26 including null)

| Type | Members | n |
|---|---|---|
| null | — | 1 |
| simple | `p t k f s x h m n l r` | 11 |
| obstruent + liquid | `{p t k f x h m} × {l r}` — the full series | 14 |

**Nuclei** (7): `a e i o u ö ä`

**Codas** (8 including null): `— n ng m r s l x`

**Legal syllable space: 26 × 7 × 8 = 1456.** The lexicon claims **229**;
1227 syllables remain free. Headroom is deliberate: new roots may be minted by
spec revision, never by the model at inference time.

Two changes from v0.1, both forced by validation and both principled:

- **`m` admitted as a coda**, completing the nasal natural class `n ng m`.
  Rescues `tim` `sim` `hom` `fim`. **Stop codas `p t k` remain illegal** — no
  attested Borges form has one.
- **Clusters made the full `{p t k f x h m} × {l r}` series** rather than the ad
  hoc list of nine. Rescues `plas` `plun` `frax` `fro` `fral` `pral`.
- **Voiced obstruents `d` `v` were REFUSED.** They appear in no attested form;
  the inventory is deliberately voiceless. `dul` `dur` `ver` were changed instead
  of the table.

### 2.2 Orthography

`x` = /ʃ/. `ö` = /ø/. `ä` = /æ/. `ng` = /ŋ/ (coda only). Everything else IPA-obvious.
ASCII fallback for logs/URLs: `ö → oe`, `ä → ae`. The canonical form uses the
diacritic spelling; the ASCII form is display-only and never hashed.

### 2.3 Borges conformance

Every attested form must parse under this spec. Non-negotiable acceptance test:

| Attested | Parse | Class |
|---|---|---|
| `hlör` | `hl` + `ö` + `r` | ORIENT (upward) |
| `u` | ∅ + `u` + ∅ | RELATOR (beyond/behind) |
| `fang` | `f` + `a` + `ng` | ROOT (to stream, to flow-on) |
| `axaxaxas` | `ax`·`ax`·`ax` + `as` | ASPECT (see §3.4) |
| `mlö` | `ml` + `ö` + ∅ | ROOT (to moon, to lunate) |

`Hlör u fang axaxaxas mlö` ⇒ *upward, beyond ⟨streaming-unceasingly⟩, it moons.*
This is the spec's golden test case. `tests/test_borges_conformance.py` must
never be allowed to fail.

---

## 3. Morpheme classes

> ⚠️ **The tables in this section are illustrative.** 24 of the forms shown below
> were phonotactically illegal or collided across classes, and were corrected
> during minting. `tlon/grammar/lexicon.yaml` is normative and carries the full
> 151-root inventory; every correction is listed there with its reason. The class
> *structure* below is unchanged and remains normative.

All morphemes are monosyllabic. **The single exception is ASPECT**, which is built
by productive reduplication of a monosyllabic aspect root (§3.4) — this is how
`axaxaxas` is derived, and it is the only unbounded morphological process in Sur.

### 3.1 `R` — Verbal roots (impersonal)

The event kernel. Always clause-final within its predication. Target inventory
**128**. Representative slice:

| Form | Gloss | Form | Gloss |
|---|---|---|---|
| `mlö` | it moons, lunates | `fang` | it streams, flows on |
| `hrun` | it stones, is-mineral | `xel` | it greens, vegetates |
| `pök` | it darkens | `lir` | it lightens, dawns |
| `tlan` | it winds, blows | `kris` | it cracks, fissures |
| `mun` | it warms | `fes` | it chills |
| `hlax` | it sounds, resonates | `nöl` | it stills, silences |
| `tris` | it burns | `mör` | it wets, damps |
| `klung` | it hollows, voids | `fral` | it crowds, teems |
| `säx` | it edges, is-bounded | `hom` | it rounds, curves |
| `pel` | it rises (generic) | `nur` | it falls (generic) |
| `xir` | it moves, displaces | `tang` | it rests, holds |
| `mel` | it sweetens | `krax` | it sharpens, is-acute |

Roots are **impressions, not objects**. `mlö` is not "moon"; it is *the mooning*,
the momentary lunar event. `hrun` is not "stone"; it is *stone-ing*. This is what
prevents a noun lexicon from re-entering through the back door, and the lexicon
review must police it: **if a gloss can be pluralized, it is wrong.**

### 3.2 `O` — Orientation particles

Spatial-deictic. Zero to two per predication. Target **24**.

| Form | Gloss | Form | Gloss | Form | Gloss |
|---|---|---|---|---|---|
| `hlör` | upward | `nar` | downward | `tim` | inward |
| `pox` | outward | `krel` | across | `sung` | around |
| `flar` | under | `tex` | over | `hren` | before (space) |
| `u` † | behind / beyond | `mix` | within | `lang` | along |
| `kon` | against | `zir` | between | `hlan` | hither |
| `xun` | thither | `tro` | atop | `fen` | beneath |
| `plas`| through | `nok` | past | `har` | amid |
| `sil` | apart | `dul` | together | `wex` | askew |

† `u` is dual-class (ORIENT and RELATOR). Disambiguated positionally: as ORIENT it
takes no complement; as RELATOR it must be followed by a Predication. The LL(1)
property is preserved because the parser knows whether a Nucleus has been consumed.
**If this dual class causes any grief in implementation, split it — Borges is not
owed the ambiguity.**

### 3.3 `L` — Relators (subordinators)

Binds a subordinate Predication into the matrix. **This class is the argument
system.** Target **12**.

| Form | Relation | Semantics |
|---|---|---|
| `u` | `BEYOND` | matrix happens beyond / behind the subordinate |
| `sen` | `AT` | co-located with |
| `tan` | `ERE` | matrix precedes subordinate |
| `pos` | `POST` | matrix follows subordinate |
| `kra` | `CAUS` | subordinate occasions the matrix |
| `xom` | `CONC` | matrix despite subordinate |
| `mil` | `SIM` | matrix while subordinate |
| `hlin` | `CMP` | matrix as / in the manner of subordinate |
| `fro` | `INSTR` | matrix by means of subordinate |
| `nix` | `PART` | matrix out of / from subordinate |
| `zul` | `TOWARD` | matrix directed at subordinate |
| `hom̈` | `AMID` | matrix interspersed with subordinate |

### 3.4 `A` — Aspect (the reduplicative scale)

The only productive morphology. An aspect word is:

```
Aspect := AspRoot{1,4} "as"
```

The aspect root is repeated 1–4 times; the terminal `-as` closes the word. The
repetition count encodes **intensity/duration on an ordinal scale**, not a distinct
lexeme.

| AspRoot | Base sense | ×1 | ×2 | ×3 | ×4 |
|---|---|---|---|---|---|
| `ax` | continuous flow | `axas` | `axaxas` | `axaxaxas` | `axaxaxaxas` |
| `tek` | punctual, iterated | `tekas` | `tektekas` | … | … |
| `hun` | inceptive, welling | `hunas` | `hunhunas` | … | … |
| `mel` | terminative, guttering | `melas` | `melmelas` | … | … |
| `zor` | habitual | `zoras` | `zorzoras` | … | … |
| `nif` | momentary, flickering | `nifas` | `nifnifas` | … | … |

`axaxaxas` = `ax` ×3 + `as` = *streaming, unceasingly*. Attested. ✓

6 roots × 4 counts + ∅ = **25 aspect values.**

### 3.5 `M` — Modality / evidentiality

How the speaker came by the impression. This is metaphysically load-bearing in Tlön
— an unperceived happening is a different happening. Target **10**.

`sköl` seen · `hrix` heard · `ten` felt · `plun` inferred · `mar` remembered ·
`xoth` dreamt · `nek` denied · `dul̈` doubted · `wir` wished · `frax` feared

### 3.6 `D` — Degree

`fim` faint · `lek` slight · ∅ neutral · `ron` marked · `tosk` strong ·
`kral` extreme · `xarr` overwhelming — **7 values incl. ∅.**

### 3.7 `Q` — Occasion quantifier

Counts *occasions*, never objects. `sim` once · `dur` twice · `tref` thrice ·
`nol` oft · `ver` ever · `pän` never — **6.**

### 3.8 `T` — Temporal deixis

`nu` now · `hlan̈` then-past · `xun̈` then-future · `tar` ere · `sim̈` since ·
`brek` until · `ol` always · `kip` momentarily — **8.**

### 3.9 `F` — Illocutionary coda

Exactly one, utterance-final. `.` is not written; the coda *is* the punctuation.

`ka` assert · `ki` interrogate · `ko` wonder/dubitate · `ku` urge · `kä` negate

---

## 4. Syntax

### 4.1 Grammar (BNF)

```bnf
<Utterance>    ::= <Predication> <F>

<Predication>  ::= <SatSeq> <Nucleus>

<SatSeq>       ::= <Q>? <T>? <M>? <O>{0,2} <Clause>{0,3}

<Clause>       ::= <L> <Predication>

<Nucleus>      ::= <R> <A>? <D>?

<A>            ::= <AspRoot>{1,4} "as"
```

**Head-final.** The matrix root is the last morpheme before the coda. All
modification precedes its head. This is what makes the Borges line parse in
its attested order.

### 4.2 Hard structural constraints

| Constraint | Value | Rationale |
|---|---|---|
| `MAX_DEPTH` | 3 | Clause nesting. Beyond 3 the listener's decode accuracy is not worth the branching factor. |
| `MAX_MORPHS` | 24 | Whole utterance, incl. coda. Reduplicated aspect counts as its syllable count. |
| `MAX_CLAUSES_PER_PRED` | 3 | Breadth cap. |
| `MIN_MORPHS` | 2 | `<R> <F>` is the shortest legal utterance. |
| Slot order | `Q T M O* Clause*` | **Fixed.** Non-negotiable — it is what buys LL(1). |

The fixed slot order means the mask decoder's legal-next-token set is a pure
function of `(slots_filled, depth, morphs_used)`. It is a **finite state machine
with a bounded stack** — implementable as a table, no parser generator needed,
no per-token model call. Mask cost is O(1) per token.

### 4.3 Why LL(1) matters here

Every class is disjoint in surface form except `u` (§3.2). Given the fixed slot
order and the disjointness, one morpheme of lookahead determines the production.
So `decode` is a *deterministic function*, and any decode failure is a **generator
bug, not a listener disagreement**. That separation is the entire point: it
guarantees the M gate is testing semantics, never syntax.

---

## 5. Semantics — denotation into an event graph

### 5.1 Target structure

```python
EventNode = {
  "root":    RootID,              # from R
  "aspect":  (AspRootID, count)   | None,
  "degree":  DegreeID             | None,     # neutral == None
  "modal":   ModalID              | None,
  "tense":   TenseID              | None,
  "quant":   QuantID              | None,
  "orient":  [OrientID, ...],     # 0..2, order-insensitive
  "edges":   [(RelatorID, EventNode), ...],   # 0..3, order-insensitive
}
Scene = { "node": EventNode, "force": IllocID }
```

### 5.2 Composition rules

Purely bottom-up, no context, no defaults-from-elsewhere:

1. `⟦<R> <A>? <D>?⟧` → `EventNode(root=R, aspect=A, degree=D)`, all other fields empty.
2. `⟦<L> P⟧` → an edge `(L, ⟦P⟧)`.
3. `⟦<SatSeq> N⟧` → `⟦N⟧` with `quant/tense/modal` set from `Q/T/M`, `orient`
   set to the multiset of `O`, and `edges` set to the multiset of `⟦Clause⟧`.
4. `⟦P <F>⟧` → `Scene(node=⟦P⟧, force=F)`.

**Absence is not neutrality.** An empty `modal` means *the impression's provenance
was not asserted*, which is distinct from `plun` (inferred). The decoder must not
fill defaults. This distinction is what lets §7 measure real information content.

### 5.3 The golden decode

```
hlör        u      fang  axaxaxas   mlö     ka
ORIENT(up) REL(BEYOND) [ ROOT(stream) ASP(ax,3) ]  ROOT(moon)  ASSERT
```
```json
{"force":"ASSERT","node":{
  "root":"mlö","aspect":null,"degree":null,"modal":null,"tense":null,
  "quant":null,"orient":["hlör"],
  "edges":[["u",{"root":"fang","aspect":["ax",3],"orient":[],"edges":[]}]]}}
```

---

## 6. Canonical form

**The repetition counter is only as honest as this section.** Surface-string
dedupe is trivially defeated by permuting order-insensitive slots.

```
canon(Scene):
  1. recursively canon() every child EventNode
  2. sort `orient` by OrientID
  3. sort `edges` by (RelatorID, blake2b(canon(child)))
  4. drop all None-valued fields (absence is structural, not a value)
  5. serialize as canonical JSON (sorted keys, no whitespace)
  6. utterance_id = blake2b(that, digest_size=16)
```

- Collision check, audit log, and the public "days without a repeat" counter key
  on `utterance_id`. **Never on the surface string.**
- Two utterances with different surface forms and the same `utterance_id` are
  **the same utterance**. Emitting the second one is a repeat and must be
  counted as one. No exceptions, no "well it *sounded* different."

---

## 7. Phase-0 gate — RESULTS

### Method correction

The gate was specified as *exhaustive enumeration*. **Enumeration is infeasible**:
a single non-nesting predication already admits **5.28 × 10¹⁰** surface forms, so
no CPU budget enumerates `|U|`. It was instead computed **exactly** by generating
functions over morpheme length, with sibling-distinctness handled by Newton's
identities for the elementary symmetric functions. Big-integer exact, instant.

That closed form is a claim, not a measurement, so it is cross-checked against
brute-force enumeration on a shrunken grammar at four `(depth, max_morphs)`
settings — surface counts **and** canonical counts — with a red-proof asserting
the comparison goes red if the ordered/unordered distinction is dropped
(`tests/test_counting.py`, 6 passed).

### Answers

Figures below are at lexicon `49475a61a308a2beeb7434693eff5c44` (**156 roots**,
after the pattern/marking family was minted 2026-08-18). Re-run
`tools/count_paraphrases.py` after any lexicon revision — these move with class
sizes.

| | Question | Result |
|---|---|---|
| **Q1** | `\|U\|` surface strings | **1.3674 × 10⁴⁵** (46 digits) |
| **Q2** | `\|U/≡canon\|` distinct meanings | **5.6564 × 10⁴³** (44 digits) |
| **Q3** | paraphrases of one fixed scene | **1** for the Borges scene; **1152** max over all legal scenes (upper bound) |
| **Q4** | scenes compatible with one referent | **3.6259 × 10⁴¹** (0.641 % of all meanings) |

Surface/canonical inflation is **24.17×** — i.e. ~96 % of legal strings are
duplicate meanings of another string. A surface-string repeat counter would
therefore read green while the system repeated itself constantly. §6 is not
optional.

### The Q3 result, stated plainly

**Q3 = 1.** Under a compositional, deterministic, lossless semantics, a fixed
scene has exactly one canonical form. Every morpheme carries meaning; there is no
synonymy; the only surface freedom is in order-insensitive slots, which §6
collapses by construction. Even the most favourable legal scene reaches only 1152,
and only by spending its entire morpheme budget on permutable slots.

So: *"never reuse the same construction for the same referent"* is **not merely
hard under this spec — it is impossible by construction**, if "same referent"
means "same scene." This is now measured, not argued.

This is not a defect in the spec. It is the spec surfacing an ambiguity in the
product requirement at the cheapest possible moment. See §8.

---

## 8. The resolution: novelty lives in impression-selection, not paraphrase

Tlön's own metaphysics supplies the fix, which is a good sign we are on the right
track. There is no persisting moon. There are only successive *momentary
impressions* which happen to be moon-compatible. Novelty is therefore **not**
"a new way to say the same scene." It is **a new scene, drawn from the set of
scenes compatible with the referent.**

That changes three things downstream, and each is cheaper to change now than in
Phase 3:

1. **M becomes a compatibility check, not an equality check.**
   `decode(u) ⊨ compat(r)` — the decoded scene must be *consistent with* the
   referent, not identical to a stored one. This is an entailment/NLI-shaped task,
   and it is what the listener is actually for. Syntactic decode is free (§4.3);
   the model is only ever needed for compatibility.

2. **`R` is measured over scene-graph distance, not embedding distance.**
   We have the graph. Use it: weighted tree edit distance over canonical
   `EventNode`s, which is exact, cheap, auditable, and cannot be gamed by moving
   through an embedding space the generator is also being trained to move in.
   Embeddings become a *bucketing* convenience, not the metric.

3. **Phase 1's fixed point is off the path.** A deterministic 1:1 English→Sur
   transform teaches the grammar and validates the mask. It does **not** teach
   impression-selection, which is the actual task. Phase 1 is a scaffold, and
   should be named as one so nobody is surprised when Phase 3 has to demolish it.

**Headroom — and exactly what it does and does not claim.** Q4 = 3.63 × 10⁴¹
compatible scenes for a single referent; at 1,000 utterances per day about that
same referent, exhaustion is 9.93 × 10³⁵ years away.

> ⚠️ **Q4 bounds the grammar's combinatorial capacity. It says nothing about the
> entropy of lived experience.** The correct claim is *"the grammar has more
> capacity than any realistic usage could exhaust — it will never be the
> bottleneck."* The claim **"the counter cannot expire"** is NOT established:
> that would require a result about how many genuinely distinct moments a real
> user supplies, which we have not measured and this spec cannot measure.
>
> **This scoping is normative for site copy and for the public counter's own
> description.** If the system ever does repeat, the cause will be upstream —
> impression-selection collapsing onto a few favoured scenes — not the grammar
> running out. Novelty drawn from Q3 instead of Q4 expires on day one.

---

## 9. Open questions for review

1. **Split `u`?** (§3.2) Dual-class ORIENT/RELATOR is Borges-faithful and mildly
   annoying. Recommend splitting to `u` (RELATOR) / `ung` (ORIENT) unless you
   want the attested line to be literally byte-exact.
2. **Is `MAX_DEPTH = 3` right?** It is the single biggest lever on `|U|`. Should
   be set *after* Q1–Q4 are computed, not before.
3. **Should ROOT be open-class under spec revision?** Currently 128 fixed. Minting
   roots is how you get unbounded expressivity, and also how you get an
   uninterpretable private language. Recommend: fixed, versioned, human-reviewed.
4. **Degree and aspect overlap.** `tosk` (strong) vs `axaxaxas` (unceasing) both
   intensify. Keep both — one is intensity, one is duration — but the lexicon
   review must keep the glosses from drifting into each other.

---

## 10. Change log

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-08-17 | Initial draft. Southern hemisphere only. Northern deferred. |
| 0.2 | 2026-08-17 | Phase 0 gate run and passed. Phonotactics corrected (`m` coda, full cluster series, `d`/`v` refused). 24 forms fixed during minting; lexicon.yaml became normative. §7 replaced with measured results. Q3 = 1 confirmed by construction. |

## 11. Open questions §9 — status after the gate

1. **Split `u`?** — **RESOLVED, split.** `u` stays RELATOR (attested); ORIENT
   behind/beyond became `ung`. LL(1) requires surface-disjoint classes and
   `classes.load()` now enforces it.
2. **Is `MAX_DEPTH = 3` right?** — **still open**, but now quantified: depth 0
   gives 2.85 × 10¹⁰ meanings, depth 1 gives 8.05 × 10³³, depth 2 gives
   1.80 × 10⁴², depth 3 gives 5.66 × 10⁴³. Almost all expressivity arrives by
   depth 2. Depth 3 buys ~31× more meanings for a listener-accuracy cost not yet
   measured. **Decide after the first listener is calibrated, not before.**
3. **Open-class roots?** — unchanged recommendation: fixed, versioned, reviewed.
4. **Degree/aspect overlap** — unchanged; a lexicon-review concern.
