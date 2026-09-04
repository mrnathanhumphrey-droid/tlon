# DECISIONS — 2026-09-03 · the content-transient arc

One file per arc: the decision, the evidence, what was rejected, and the sha.
⛔ **Retractions are recorded, not quietly dropped.** A trace that only holds the
claims that survived is a trace of what was believed at the end, which is the
one thing nobody needs.

Entry point: `STATE.md`. Dictionary: `MEASUREMENTS.md`.

---

## D1 · The corpus was content-FREE, and that was the wrong ontology

**Decision.** Add a second corpus recipe, `content-transient`: the response is
provoked by its provocation's content, and that content dies at the end of the
turn.

**Evidence.** `act2_build_multiturn.py`'s own first line said "content-free", and
the measurement agreed — 15,573 provoke rows in `runs/act2/corpus_mt`, within-pair
shared roots 0.0457 against a permutation null of 0.0424.

**The reasoning (Wilson's, and it is the pivot of the arc).** Tlön denies that
content *persists* — no objects, the coins were lost. It does not deny that
content is *apprehended*. An impression is had, in the moment, and released. The
corpus conflated *content-free* with *content-transient* and trained the first:
a mind that never perceives its input at all, which is not Tlönian, it is deaf.

**Rejected.** (a) Ship force-only as art — not what was asked for. (b) A
topical-carry corpus — that is content *persisting*, the object permanence the
language denies. (c) Reason the reply in English and render it through the LoRA
— works, but the mind is not Tlönian and the language becomes a skin.

**sha** `d6a1372`

## D2 · The army is a factorial, not a pile

**Decision.** Keep the content-free adapters as the **control arm** rather than
discarding them. Same seeds across recipes, per-recipe rulers, recipe label on
every adapter.

**Evidence.** The contrast "does adding within-turn responsiveness produce
conversation, holding everything else fixed" is unavailable from either arm
alone.

**Rejected.** Pooling rulers across recipes — a between-recipe sd wearing a
within-recipe name, the same shape as the ruler that the lost-s20620
substitution would have corrupted.

**sha** `3fd3aff`

## D3 · One pipeline serves both arms

**Decision.** Parameterise `pipeline_retrain.sh` by `RECIPE=${RECIPE:?}` rather
than copying it for the transient arm.

**Evidence.** Two copies of one procedure drift, and then a difference between
the arms could be the procedure rather than the recipe.

**sha** `6cc614f`

## D4 · One adapter gates twelve

**Decision.** Train **one** `ct-s20624` and read the model-side lag profile
before buying the other eleven (~26–52 GPU-h).

**Evidence.** Corpus responsiveness is a property of the DATA. The content-free
arm proves transmission is real in the other direction — no connection in the
corpus, none in the model (0.00 shared roots over 13 human exchanges). The
inverse is untested, and the factorial *and* the chatbot are downstream of it.

**Rejected.** Seed-matched fresh builds of both arms (~52 GPU-h) — that buys
lower variance on a *second-order* contrast which cannot even be asked until the
first-order question is answered.

**sha** `dd403ed`, prereg LOCK `abde6124`

---

# ⛔⛔ RETRACTIONS AND CORRECTIONS

## R1 · "One-knob contrast" — verified against the wrong pair

**Claimed.** The two recipes differ in exactly one variable.

**Actually.** Checked by comparing `chain_transient(1.0)` against
`chain_transient(0.0)` — *both on the new path* — while the builder's control arm
ran `multiturn.build`, the legacy coupled-stream generator. The real comparison
returned **False**: the force-transition multisets did not match.

**Fixed structurally, not vigilantly.** Both arms now run one generator with the
control as `responsiveness=0`, so one-knob is enforced by shape rather than by
remembering to check the right pair. Re-verified: multiset identical across 1080
transitions, provocation surfaces differ.

## R2 · The transitivity break was insufficient

**Claimed.** Barring the inherited root from the echo slot prevents content
persisting.

**Actually.** Failed its own gate at **lag-2 z = 29.65**. Roots co-occur in
clusters, so a surface chosen for containing `W` very often also contains `X` —
the root rides along regardless of what was nominally echoed. The bar had to be
on **containment**, not the echo slot.

## R3 · "Chance plus a hair" — reading signal into an expected tail

**Claimed.** `corpus_mt`'s within-pair z = +2.22 was "chance plus a hair".

**Actually.** Across six independent corpora, one reading +2 is exactly the
expected tail. It is chance. "Plus a hair" gave a noise value a word that implies
signal.

## R4 · The corpus did not reproduce from its seed

**Claimed, implicitly.** A corpus built from a seed can be sha-pinned, as this
project pins every other corpus.

**Actually.** `responsive_choice` iterated a **frozenset**, and set iteration
order follows randomised string hashing. Same seed, different process, different
corpus — measured at PYTHONHASHSEED 1 / 2 / 1.

**Why it hid.** Every draw is *valid*: they pass the recipe gate identically
(+518 local, +545 on the box). Nothing was wrong with the corpus, only with the
ability to rebuild it — and that voids the sha-pinning discipline silently.

**Caught by** comparing the box's corpus to the local one, not by a test.
Fixed with `sorted()`; guarded by a test that spawns child processes, because
hash randomisation is fixed per interpreter and an in-process assertion passes
against the broken code. **sha** `2405a27`

## R5 · Four defects found by running things, not by reading them

- **7 of 8 pipelines** had a failure handler that dereferenced `$STAGE` before
  it existed, so under `set -u` the handler died on early exit — erasing the
  diagnosis exactly when there was one. Included `pipeline_positive_control.sh`,
  which has not run yet. `6cc614f`
- **A literal `\n`** written where a line continuation belonged. `bash -n`
  *passes* — the shell reads it as an argument `n` — so it is valid syntax that
  fails at run time on a rented box. `6cc614f`
- **The token baseline was destroyed** by the obvious invocation: `--out`
  defaults to the same path as the natural `--baseline`. Silent and compounding —
  every later corpus would still print a delta, against the wrong reference.
  `92dbf3a`
- **`provision` crashed on a `print`** (Windows cp1252 vs `✅`) *after* the clone
  and SHA check had run. On a path where `collect` and `persist` do irreversible
  work, a crash between an action and its record is the shape that lost s20620.
  `2c81a6b`

---

## Open, and what closes it

| open | closes on |
|---|---|
| Does corpus lag-1 responsiveness reach the model? | `ct-s20624` gate read, prereg `abde6124` |
| Are the eleven other adapters worth buying? | the same read |
| Does the chatbot have a Tlönian mind or a skin? | the same read |
| Per-recipe rulers + `FLOOR_ka` recompute | after the control batch persists |
| Amendment C (design → factorial) | after the rulers |

⚠️ **`ct-s20624`'s corpus is pre-determinism-fix and is NOT a pinnable
population member.** It answers the gate — which asks whether the property
transmits at all, not which draw. If the gate returns GO, the batch is rebuilt
deterministically, `ct-s20624` included.
