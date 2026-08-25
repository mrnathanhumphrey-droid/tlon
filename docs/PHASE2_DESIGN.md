# Phase 2 — the listener, designed around impression-selection

**Status:** DESIGN FOR REVIEW. Nothing built. No model chosen, downloaded, or trained.
**Supersedes:** Phase 1 (cancelled — see §1) and the M-gate definition in the original brief (§2).

---

## 1. Phase 1 is cancelled, and why that is not a shortcut

Phase 1 was: SFT a model on a fixed, reversible English→Tlönist transform, to be
demolished in Phase 3 once novelty pressure arrives. That plan assumed
*determinism-per-scene was the problem*.

Q3 = 1 says the assumption was inverted. A fixed scene canonicalising to exactly
one form is not a fixed point to escape — it is **correct, permanent behaviour**,
the same way `2+2` should always canonicalise to `4`. `parse.py` / `canon.py` /
`render()` already implement it exactly, deterministically, and with a passing
golden test. There is nothing for a neural model to approximate here, and
training one to approximate it would only introduce error into a layer that
currently has none.

**DECISION: the deterministic layer is permanent ground truth, not a scaffold.**

---

## 2. The M gate as originally specified is now VACUOUS

This needs stating before any listener is built, because the original brief's
central mechanism no longer does anything.

> Original M: *"a second listener model must be able to decode the Tlönist
> utterance back to the correct referent/scene. If it can't, reject."*

`parse()` decodes any legal utterance to its exact scene, always, with **zero
error**, at zero inference cost. The grammar is LL(1) and the denotation is
lossless. A listener asked to do this **cannot fail**, so the gate can never
reject, so `M` never fires.

The gate was implicitly testing *syntax + semantics*, which we have since made
free. What it was **meant** to test survives, and is genuinely hard:

| Layer | Question | Cost | Who does it |
|---|---|---|---|
| Syntax | is this a legal string? | free | `fsm.py` — FSM, O(1)/token |
| Semantics | what scene is this? | free | `parse.py` → `denote` — exact, lossless |
| **Pragmatics** | **what is this scene ABOUT?** | **the only real cost** | **the listener model** |

**The model's entire job is reference resolution.** The generator picks a
momentary impression `s` compatible with referent `r`; the listener sees `s`
recovered perfectly and must infer `r`. *"Upward beyond the onstreaming it moons"*
→ **which** thing is being talked about? That is inference under genuine
uncertainty, and it is the only place a neural model belongs in this system.

**RESTATED M:** `M(s, r, context) = can the listener recover r from s?`
A retrieval / ranking task over a candidate referent set — **one forward pass, no
generation**, yielding a calibrated score with a usable margin. This is what
flag ④ asked for (gate on margin, not a binary boundary), except now the
architecture forces it rather than us choosing it.

---

## 3. Generation is scene selection, and the mask is a serialization

The FSM work is not wasted. Because the grammar is LL(1) and the slot order is
fixed, **a masked morpheme sequence is exactly a serialization of the scene
graph** — the token stream and the AST are isomorphic. Emitting tokens under the
mask and emitting a structured `EventNode` are the same act in two notations.

So the generator is a **scene selector**: given `(r, context, history)` it picks a
point in the Q4 space (2.80 × 10⁴¹ scenes compatible with `r`), and `render()`
does the rest. It is not a text generator that we constrain after the fact.

---

## 4. ⚠️ FLAG ⑦ — the cipher problem, which is now the dominant risk

The channel is lossless, the decoder is exact, and the listener is co-trained.
That combination has a known degenerate solution, and the new architecture makes
it *more* attractive, not less:

> The generator can encode `r` in a way the listener reliably reads, without the
> scene **describing** `r` at all. "Aspect reps = 3 means moon." Passes M
> perfectly (the listener learns the code), maximises R (everything else varies
> freely), and is not language.

This is the emergent-communication degenerate-code failure, sharpened. It will
not be caught by rising rejection rates — a cipher has an *excellent* M score.
More listeners do not fix it either: a population co-trained on the same rollouts
learns the same cipher.

**The fix must be a listener the generator cannot move.**

### The gloss-grounded frozen auditor

Render the scene to its **English gloss** via the lexicon —
*"upward, beyond ⟨streaming, unceasingly⟩, it moons"* — and ask a **frozen,
general-purpose model, never trained in this loop**: *what is being described?*

The generator cannot retrain that model and cannot shift what English words mean.
A cipher that says nothing descriptive fails it. A genuine impression passes it.

Consequences:
- **The lexicon glosses become load-bearing grounding**, not documentation. This
  retroactively justifies the "if the gloss can be pluralized, it is wrong"
  review rule in spec §3.1.
- The auditor is **never** in the accept/regenerate loop (that would make it a
  yardstick derived from the artefact under audit — the exact anti-pattern). It
  scores a held-out sample and raises an alarm. Audit only.
- **Cipher alarm = M-gate pass rate high while gloss-auditor agreement falls.**
  That divergence is the signal. Track the gap, not either number alone.

---

## 5. Phase 2a needs no model at all — start here

`compat(s, r)` can be defined **structurally**: referent `r` pins a signature (a
required root, optionally required edges); any scene containing that signature is
compatible. This is exactly the relation used to compute Q4, so it is already
implemented and already counted.

That gives a curriculum where the loop is proven before any GPU is touched:

| Stage | `M` implemented by | Model needed | Proves |
|---|---|---|---|
| **2a** | structural signature match — exact, free | **none** | the self-play loop, the orbit budget, the audit log, and the R metric are stable |
| **2b** | learned listener, calibrated against 2a | small | that a model can do reference resolution at all, with 2a as a *reference*, not as its training target |
| **2c** | + frozen gloss-grounded auditor (§4) | frozen general model | that 2b is describing rather than ciphering |

**Recommendation: build 2a first.** Every mechanism that can break for
non-neural reasons — bucket keying, decay weights, orbit-budget arithmetic, the
audit schema, tree-edit distance, the collision counter — breaks in 2a, where
failures are legible and free. Phase 3's reward hacking is much easier to see
against a loop already known to be sound.

**Caveat that must not decay:** 2a's structural `compat` is a *stand-in*. It
cannot distinguish a vivid impression from a barely-relevant one, and a system
that scores well under it has not been shown to communicate. 2a proves plumbing,
never pragmatics.

---

## 6. R — repetition, restated on the graph

Weighted tree edit distance over canonical `EventNode`s. Exact, cheap, auditable,
and **not gameable by moving through an embedding space the generator is also
being trained to move in** (flag ③). Embeddings may bucket; they must not score.

Buckets key on the **ground-truth referent** during training — in self-play we
generated `r`, so we have it. Listener-inferred buckets are for serve time only,
where no ground truth exists.

---

## 6b. BOUND CONSTRAINTS (Wilson, 2026-08-17) — ordering, not TODOs

### B1. Auditor ordering is a hard dependency

2a's `compat` is pure structural matching, so no cipher can form and the frozen
gloss auditor may stay out. **Binding:** the instant any *trainable* component
enters the listener, the gloss auditor ships **in the same commit**. Not a
follow-up, not a TODO. A trainable listener without a grounded auditor is the
exact configuration flag ⑦ describes, and it is the one configuration where the
failure is invisible to every other alarm we have.

### B2. The counter may never be logged or served alone

The collision counter is vacuous without its conditioning pass rates — the
birthday-problem objection is correct, and a counter drawn from a 2.8 × 10⁴¹
space proves nothing on its own. **Binding:** counter, M-gate pass rate, and
gloss-agreement rate are **one record**. The schema must make an unaccompanied
counter unrepresentable, not merely discouraged.

> ⚠️ **The null trap, which B2 as stated walks into.** In 2a there *is* no
> gloss-agreement rate — no auditor, no model. A nullable column would sit empty
> through 2a and then be indistinguishable from a *measured* pass later. That is
> a plausible default being quoted as a measurement.
>
> **Therefore:** `auditor_state` is a REQUIRED enum, never null —
> `ABSENT_BY_PHASE` | `MEASURED` | `FAILED_TO_RUN`. Any consumer (audit log
> view, public endpoint, site copy) **must refuse to render a counter whose
> `auditor_state != MEASURED` as a public number.** 2a can log freely; it simply
> cannot publish. The refusal is in the serving layer, tested.

### B3. Grammar-family agnosticism — and what it actually requires

Northern hemisphere is a planned controlled ablation: same referent set, two
grammar families. **Binding:** bucket / compat / audit layers key on `Scene` and
`EventNode`, never on southern surface forms or southern morpheme classes.

> The real constraint this implies, worth stating before northern is designed:
> **both grammars must denote into the SAME `Scene` algebra.** If northern
> denotes into a different structure, the comparison is not controlled and the
> ablation measures the structure change rather than the grammar family. This
> is a constraint on the *northern grammar spec*, not on the 2a plumbing, and
> it is much cheaper to honour now than to retrofit.

### B4. The 2a caveat, carried unchanged

**2a proves plumbing, never pragmatics.** Structural compat cannot tell a vivid
impression from a barely-relevant one. Scoring well under it is evidence the
pipes do not leak — nothing more.

---

## 6c. BLOCKER — the lexicon predates the referent set

The 151 roots were minted before any referent existed. Nothing guaranteed
coverage, and coverage is **not** complete. See `docs/REFERENT_COVERAGE.md`.

Two Tier-1 pegs have genuine semantic gaps, and they are not marginal ones:

| Peg | Gap |
|---|---|
| **01 a mirror** | no root for reflection / doubling / returning-the-look |
| **12 a map the size of its territory** | no root for representation / standing-for / correspondence |

Both are *representation* concepts. The root inventory was built around physical
happenings, so the whole representational family is absent — and these are the
two most Borgesian images on the roster. **Resolve before 2a seeds, or drop them
from the 20.**

---

## 6d. Signature design — single-root signatures are degenerate

If referent `r`'s signature is "matrix root = X", then reference resolution is a
lookup on one token: 2a's ranking task is trivially solvable and stresses
nothing. Worse, Tier 1 has heavy root overlap by design — 03, 06, 08, 15 and 20
all involve water roots — so single-root signatures would *collide*, reporting
compat for the wrong referent.

**A signature must be a partial graph pattern, not a root:** a disjunction of
required roots, plus required edges with their relators, plus orientation
constraints. That keeps the compatible set large (Q4-scale), makes overlap
informative rather than fatal, and leaves 2b a task worth learning.

Schema for `referents.yaml` is in §7.1. **Nate/Wilson author the content; this
document defines only the shape.**

---

## 7. Open — needs Nate

1. **The referent set.** Nothing above works without one. How many referents,
   and where do they come from? This is the single largest unspecified input, and
   it is a content decision, not an engineering one.
2. **Where do seed (scene, referent) pairs come from for 2b?** Hand-authored, or
   proposed by a general LM and reviewed? If an LM is in the data loop, the
   §4 auditor must be a *different* model from the one that authored the data.
3. **Backbone.** Deliberately still unchosen — see §8.

---

## 8. Backbone status: NONE. Nothing downloaded, nothing trained.

The earlier recommendation (Qwen3-8B-Base generator + different-family listener)
was made when the model was expected to carry syntax, semantics, and pragmatics.
**It no longer is.** Syntax and semantics are deterministic Python. The model
does reference resolution over a candidate set — a ranking task on short inputs.

That is a much smaller job, and the sizing should be redone against it rather
than inherited. Provisional read, to be settled after §7.1 fixes the referent set
size:

- **Listener (2b):** small. A ranking/retrieval head over a few hundred
  referents on ≤24-morpheme inputs does not need 8B. Something in the
  0.5–1.5B range is the honest starting point, and there are already
  Qwen2.5-0.5B / 1.5B and Pythia checkpoints in the local HF cache.
- **Generator:** open. Depends whether scene selection is a learned policy over
  a structured space or a masked LM. Do not pick before 2a runs.
- **Frozen gloss auditor (2c):** the one place a genuinely strong general model
  earns its cost, because ungameability is the whole point. Must be a different
  family from anything trained in the loop.

**No backbone should be chosen until 2a has run**, because 2a is what tells us
what the model actually has to do.
