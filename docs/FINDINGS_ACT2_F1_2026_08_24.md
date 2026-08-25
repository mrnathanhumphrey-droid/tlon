# ACT 2 — F1 + §8 pre-flight. PREREG `20620b7c`

**Ran:** 2026-08-24 · `claude-sonnet-5` · 48 calls · **$0.1043 of a $1.00 hard
ceiling** · battery `d6f1ae1040d6910d` · lexicon `e2b85270…` · ledgered to
`runs/act2/ledger.jsonl`.

**This is Act 2's first spend.** It bought three answers and one of them stops
the design where it stands.

---

## 1 · A prompted model CAN speak legal Tlön — 16/16

Cold, no conversation, lexicon card only: **100 % first-attempt legal turns.**
The conversation half of step 2 works without a single retry.

## 2 · Translation is 50 % legal, and every failure is a CLASS CONFUSION

`render` (English → Tlön, the product's own task): **8/16 first-attempt legal.**

⭐⭐ **NOT ONE HALLUCINATED FORM.** Every refusal used a *real* lexicon word in
the wrong class:

| form | what it is | what it was used as |
|---|---|---|
| `pal` | ROOT — "it thins" | `aspect_root` |
| `rän` | ROOT — "it repeats" | `aspect_root` |
| `plas` | ORIENT — "through" | `root` |
| `hul` | ORIENT — "together" | `relator` |

**The model has the vocabulary and not the class system.** It is not inventing
Tlön; it is misassigning slots. That is exactly the failure a fine-tune fixes and
a longer prompt does not — the lexicon is 156 roots plus 66 other forms in eight
classes, and class membership is structural, not semantic.

⛔ F1 as a native gate would FIRE at 0.500 vs the 0.90 threshold. In the prompted
pass F1 is **fired by construction** anyway, so this changes no verdict — but it
sizes the problem: **half of all production probes reach the gate illegal**, so
the retry loop is doing heavy work and `D_ctx` on the production half carries the
gate's fingerprints, not only the model's.

## 3 · ⛔⛔ §8 FIRED: THE COMPREHENSION HALF CANNOT SHOW DRIFT AT ALL

**16/16 correct. Accuracy 100 %. At ceiling.**

§8, pre-registered, checked "at epoch 0 of the very first run, before any
conversation is generated":

> *"If the probe battery proves too easy (epoch-0 comprehension accuracy at
> ceiling) … the headroom gate closes every cell and the whole design is
> uninformative regardless of what the models do."*

**And the reason is structural, not a matter of harder distractors.** The
comprehension prompt carries the lexicon card. With the card, decoding a Tlön
surface is a *lookup* — the grammar is exactly invertible and every form is in
the table. A lookup cannot drift. So:

> **THE COMPREHENSION HALF IS PINNED BY THE CARD, AND A PINNED MAPPING HAS NO
> DRIFT TO MEASURE. Making the distractors harder cannot fix this; the answer is
> derivable either way.**

And removing the card does not rescue it: with no card and no conversation,
epoch-0 accuracy falls to chance (1/4), which is §8's *floor* — the noise floor
rises to meet the headroom and the gate closes from the other side.

⇒ **While the model is PROMPTED, the comprehension half is uninformative in both
configurations.** §1 forbids the obvious dodge — *"no post-hoc reweighting, no
dropping a half that disagrees with the other"* — so this is not something to
work around. §8 says the observable "needs rebuilding, not patching", and that
rebuild is a decision, not a patch to make quietly.

---

# WHAT THIS SAYS ABOUT THE ROUTE

⭐⭐ **THE PRE-FLIGHT ARGUES FOR LOCAL, AND IT ARGUES ON EVIDENCE RATHER THAN
PREFERENCE.** Nate's read — *"the goal/dream is to get local ASAP, because that's
where the real axes are"* — is what these three numbers independently say:

| finding | what it implies |
|---|---|
| speak 100 % legal | the conversation loop is not the bottleneck |
| render 50 %, all class confusion | the class system is **learnable and not prompted-in**; a fine-tune targets exactly this |
| comprehension pinned at ceiling by the card | **the card is a crutch that exists only because we are prompting.** A model with the mapping in its WEIGHTS needs no card, and only then is "what does it take this to mean?" a question about the model |

⛔ **AND THE AXES WERE ALREADY LOCAL-ONLY.** Of the four pre-committed
re-decomposition axes, a hosted API can run at most two:

- **axis 3 — validity-enforcement mode.** `soft_penalty` and `curriculum` are
  *training-time* controls. There is no way to express them through an inference
  API. Only `hard_retry` is reachable.
- **axis 4 — lexicon tightness.** Needs a re-fine-tune per minted lexicon.
- **`D_w` at all.** Weight-level drift requires owned weights, by definition;
  §7 step 3 already says so.

So the hosted pass was never going to reach the axes. It was going to validate
the instrument and hand over. **It has now done that, for ten cents.**

---

# WHAT IS DECIDED, AND WHAT IS NOT

**Decided by evidence, no sign-off needed:** the prompted pass cannot produce a
`D_w` claim (already pre-registered), and cannot measure comprehension drift
(§8, just fired).

**NOT decided — Nate's calls, and the standing rule is that they always are:**

1. **The comprehension observable needs rebuilding.** §1's halves are locked at
   equal weight, so this is a change to a pre-registered observable: it needs a
   new prereg or a formal amendment, not an edit. My reading is that it should be
   rebuilt *after* the model holds the mapping in weights, because that is the
   first configuration in which the question is even well-posed.
2. **The local backbone.** `LocalBackend` is a shaped hole with a raise in it;
   the `Speaker` protocol, the gate, the arena, the falsifiers and the ledger all
   run unchanged behind it.
3. **Whether any more hosted spend is wanted at all.** On this evidence I would
   spend nothing further hosted: the production half would measure the retry
   loop as much as the model, and the comprehension half cannot move.

⭐ **THE DREAM, RECORDED VERBATIM (Nate):** *"two models who THINK and SPEAK in
tlonian talking to each other and drifting in public through voice and text."*
**THINK is the operative word and it is the whole argument for local** — a model
reading a lexicon card is looking the language up, not thinking in it. The
comprehension ceiling is that distinction showing up as a number.
