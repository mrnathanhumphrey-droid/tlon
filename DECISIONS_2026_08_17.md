# Tlön — decision trace, arc opened 2026-08-17

One file per arc. DECISION + EVIDENCE + REJECTED + artefact. Retractions get
recorded, not quietly overwritten.

---

## 0. Where things stand

Phase 0 gate **PASSED**. Grammar spec, lexicon, parser, denotation,
canonicalisation, mask FSM, and exact counting are built and tested.
**421 tests pass** (`python -m pytest tests/ -q` from `D:\Tlon`).

Nothing has been trained. No model has been downloaded. No Lambda spend.

---

## 1. Hardware / stack context

| | |
|---|---|
| Local | RTX 5070 Ti 16.3 GB sm_120, 63.4 GB RAM, 32 threads |
| Stack | torch 2.11.0+cu128 (CUDA live), transformers 5.8.1, peft 0.19.1, datasets 4.8.5 |
| Absent | vLLM, TRL, bitsandbytes, flash-attn (no sm_120 Windows wheels) |
| Remote | Lambda, **with persistent storage** (confirmed by Nate 2026-08-17) |

**DECISION** — Phase 0 and Phase 1 run local. Syntax costs zero inference (§4.3
of the spec: the mask is an FSM, not a model), so the GPU is not the constraint
until listener self-play in Phase 2.

---

## 2. Phase 0 gate — the numbers

Artefact: `tools/count_paraphrases.py`, lexicon hash `61ad847f450e0c48c6cabff076b41421`.

| | | |
|---|---|---|
| Q1 | surface strings | 1.0164e45 |
| Q2 | distinct meanings | 4.2315e43 |
| Q3 | paraphrases of a fixed scene | **1** (Borges); 1152 max, upper bound |
| Q4 | scenes compatible with one referent | 2.8023e41 |
| — | surface/canon inflation | **24.02×** |

**DECISION — novelty is drawn from Q4, never Q3.** "Never reuse the same
construction for the same referent" is impossible if "referent" means "scene":
Q3 = 1 by construction. It is trivially satisfiable if "referent" means a set of
compatible momentary impressions: Q4 = 2.8e41, i.e. 7.7e35 years at 1,000
utterances/day about the same referent.

**SCOPE CORRECTION (Nate, same day) — retained deliberately, not overwritten.**
An earlier draft of §8 and of `count_paraphrases.py` said "the counter cannot
expire." That overclaims. **Q4 bounds the grammar's combinatorial capacity, not
the entropy of lived experience.** The defensible claim is *"the grammar will
never be the bottleneck."* Whether a real user supplies enough genuinely distinct
moments is unmeasured and unmeasurable by this spec. Normative for site copy.
Corrected in spec §8 and in the gate's own printed output, so the caveat lives in
the artefacts rather than in a conversation nobody will re-read.

**Q3 = 1 is CORRECT BEHAVIOUR, not a degeneracy.** A fixed scene canonicalising
to exactly one form is the same property as `2+2` always canonicalising to `4`.
This matters for §6 below: it is the reason Phase 1 was cancelled.

Consequences already written into the spec (§8):
- **M becomes a compatibility check, not an equality check.**
- **R is scene-graph tree-edit distance, not embedding distance.** We have the
  graph; an embedding proxy is gameable by a generator being trained to move
  through that same space.
- **Phase 1 is a scaffold, not a foundation.** A 1:1 English→Sur transform
  validates the mask and teaches the grammar; it does not teach
  impression-selection. Phase 3 demolishes it. Say so up front.

**REJECTED** — running the gate by exhaustive enumeration as originally
specified. A single non-nesting predication has 5.28e10 forms. Replaced with
exact generating-function counting.

---

## 3. Rule-zero: the counts are cross-checked, not asserted

A 45-digit number from a hand-derived closed form is exactly the kind of value
that is quietly wrong and flattering.

**EVIDENCE** — `tests/test_counting.py` shrinks the grammar until every legal
string can actually be enumerated, then demands the closed form and the
enumeration agree exactly, for **both** surface and canonical counts, at four
`(depth, max_morphs)` settings. The reference enumerator is written from the BNF
independently of `enumerate.py` so a shared bug cannot hide in both.

Guards against a vacuous null:
- `test_toy_is_big_enough_to_exercise_every_feature` — fails if the toy grammar
  never nests, never doubles an orientation, or never uses reduplicated aspect.
- `test_counting_detects_an_error` — red-proof; asserts the comparison goes red
  if the ordered/unordered distinction is dropped.

---

## 4. Phonotactics — corrected under validation

The mint script refused 24 hand-authored forms. **Do not read this as tidying:**
the published v0.1 tables contained forms the published v0.1 phonotactics made
illegal. The validator caught every one.

**DECISION — two principled table changes:**
- `m` admitted as a coda, completing the nasal class `n ng m`.
- Clusters made the full `{p t k f x h m} × {l r}` series instead of an ad hoc
  list of nine.

Syllable space 1029 → **1456**; 229 claimed, 1227 free.

**REJECTED — admitting `d` and `v` as onsets.** They would have rescued
`dul`/`dur`/`ver` for free. No attested Borges form contains a voiced obstruent;
the inventory is deliberately voiceless. The forms were changed instead of the
table. Same reasoning refuses stop codas `p t k`.

**DECISION — surface forms are never hand-typed for roots.** Glosses are
hand-authored (semantics needs judgement); forms are allocated deterministically
from the legal syllable space, so collisions and phonotactic violations are
impossible by construction rather than caught by review.

**DECISION — `u` split.** RELATOR keeps the attested `u`; ORIENT behind/beyond
becomes `ung`. LL(1) requires surface-disjoint classes; `classes.load()` enforces
it on every load.

---

## 5. Canonicalisation is load-bearing, and now measured

24.02× surface inflation means **~96 % of legal strings are duplicate meanings**.
A surface-string repeat counter would read green while the system repeated itself
constantly.

`tests/test_grammar.py` asserts permuted orientations and permuted sibling
clauses collide on `utterance_id`, with a red-proof
(`test_different_meanings_do_not_collide`) so those cannot pass vacuously, plus
`test_absence_is_not_neutrality` for spec §5.2.

---

## 6. The mask is tested in both directions

**DECISION** — soundness alone is not acceptance. A mask that only guarantees
"nothing illegal escapes" can silently shrink the language to a fraction of it
and every test still passes.

- SOUND — 300 random FSM walks to completion, each must parse. No dead-ends.
- COMPLETE — 200 legal utterances from an *independent* random generator that
  bypasses the FSM; the mask must accept every token of each.

Budget and depth guards verified to bite for the right reason, not incidentally:
at `used=22` the mask offers only `R`; after three nested clauses it stops
offering `L`; a 4-repetition aspect is withdrawn when the budget cannot hold it;
the depth-cap parse error names the depth cap.

---

## 6b. Phase 1 CANCELLED; M gate found vacuous (Nate's call, 2026-08-17)

**DECISION — Phase 1 cancelled.** It was designed to teach a fixed scene→form
transform for Phase 3 to demolish, on the assumption that determinism-per-scene
was the problem. Q3 = 1 inverts that: the deterministic mapping is correct and
permanent, and `parse.py`/`canon.py`/`render()` already implement it exactly.
Training a model to approximate a function we have exactly would only add error
to a layer that currently has none.

**FINDING — the M gate as originally briefed is VACUOUS.** "Listener decodes the
utterance back to the scene" is something `parse()` does with zero error at zero
cost. A listener asked to do it cannot fail, so the gate can never reject.

**DECISION — M restated as reference resolution.** The three layers separate
cleanly: syntax free (FSM), semantics free (parse/denote), **pragmatics = the
only place a model belongs**. The listener's job is *what is this scene ABOUT*,
a ranking task over a candidate referent set: one forward pass, no generation,
calibrated score with a margin. This satisfies flag ④ by construction rather
than by choice.

**DECISION — Phase 2a needs no model at all.** `compat` starts as structural
signature matching (already implemented; it is what computed Q4). Every
mechanism that can fail for non-neural reasons — bucket keying, decay weights,
orbit arithmetic, audit schema, tree-edit distance, collision counter — fails in
2a where it is legible and free. **Caveat that must not decay: 2a proves
plumbing, never pragmatics.** A system scoring well under structural compat has
not been shown to communicate anything.

**DECISION — no backbone chosen, nothing downloaded.** The earlier Qwen3-8B-Base
recommendation was sized for a model carrying syntax + semantics + pragmatics.
It now carries only pragmatics. Re-sizing is deferred until 2a shows what the
model actually has to do. See `docs/PHASE2_DESIGN.md` §8.

Design: `docs/PHASE2_DESIGN.md`.

---

## 7. Known loose ends (not yet addressed)

1. **`lexicon_hash` differs between mint (`e63a7d…`) and load (`61ad84…`)** —
   mint hashes the pre-write string, `classes.load()` hashes the file bytes.
   Harmless today, but reproducibility claims will pin a hash, so make them agree
   before anything pins it. **Load's value is the real one.**
2. **Max-fiber 1152 is an upper bound**, not attained — it ignores
   sibling-distinctness. Only matters if Q3 is ever revisited.
3. **`MAX_DEPTH = 3` unresolved.** Now quantified (depth 2 → 1.38e42, depth 3 →
   4.23e43; 30× more meanings). Costs listener accuracy by an unmeasured amount.
   Decide after the first listener is calibrated.
4. **Northern hemisphere grammar not started.**

---

## 8. Framework flags raised before build, still standing

Raised 2026-08-17 against the M/λR/O spec; ① is now settled by measurement, ②–⑥
are not.

| | Flag | Status |
|---|---|---|
| ① | Paraphrase space ≈ 1 ⇒ novelty must come from impression-selection | **SETTLED** — Q3 = 1, measured |
| ② | Best-of-N against a noisy verifier is adversarial search on that verifier; a co-trained listener is a yardstick derived from the artefact under audit | open — needs listener population, frozen auditor, rejection-rate alarm |
| ⑦ | **NEW.** Lossless channel + exact decoder + co-trained listener ⇒ the generator's best move is an arbitrary CIPHER, not a description. A cipher scores *excellently* on M, so rejection-rate alarms cannot see it. | open — **now the dominant risk.** Fix = gloss-grounded frozen auditor, audit-only, never in the accept loop. Alarm is M-pass-rate high **while** gloss agreement falls: track the gap, not either number. See `docs/PHASE2_DESIGN.md` §4 |
| ③ | Listener-inferred bucket keys are circular and gameable | open — key on ground-truth referent during training |
| ④ | A binary gate puts the optimum on the listener's decision boundary | open — gate on margin, not pass/fail |
| ⑤ | `R > ŵ·M_budget` does not typecheck; a binary M has no budget | open — restate O in units of accumulated repetition cost |
| ⑥ | Surface-string dedupe is a lie | **CLOSED in the grammar layer** — 24.02× measured, canon enforced and tested |
