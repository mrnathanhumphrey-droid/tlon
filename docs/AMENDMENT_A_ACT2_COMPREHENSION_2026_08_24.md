# AMENDMENT A to PREREG `20620b7c` — the comprehension observable, rebuilt

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `8c010702` (sha256[:8] of draft body at lock, 2026-08-25T00:50Z)
- **Date:** 2026-08-24
- **Amends:** PREREG `20620b7c` §1 (the two halves), §3.3 (the comprehension
  probe), §8 (the battery-difficulty check). ⛔ **The locked prereg body is NOT
  rewritten.** This document supersedes those three sections and nothing else.
- **Triggered by:** `docs/FINDINGS_ACT2_F1_2026_08_24.md` — §8 fired, measured.
- **Depends on:** `docs/SCOPE_LOCAL_FINETUNE.md`

---

## 0 · Why an amendment and not an edit

§8 fired on the first pre-flight: comprehension **16/16, at ceiling**. §1 locks
the two halves at equal weight and forbids the obvious dodge — *"no post-hoc
reweighting, no dropping a half that disagrees with the other"* — so the
observable cannot be quietly adjusted. §8's own registered response is that it
*"needs rebuilding, not patching"*. This is that rebuild.

⭐ **AND THE RULING THAT MAKES IT DRAFTABLE.** Act 2 is now ruled **`D_ctx`** —
in-context convention between models that already know the language. That fixes
what comprehension drift *means*: not "does the model learn to decode over the
conversation" but **"does a fluent speaker's interpretation of a fixed utterance
move as a shared convention forms around it."**

## 1 · What broke, stated exactly

The old probe put the **lexicon card in context**. With the card, and a grammar
that is exactly invertible, decoding a surface is a **LOOKUP** — and:

> ⛔⛔ **A LOOKUP CANNOT DRIFT.** The old probe was not a hard measurement that
> happened to saturate; it was structurally incapable of moving. Harder
> distractors cannot fix it, because the answer is derivable from the table
> either way.

And the mirror failure is equally structural: **remove the card from a prompted
model and epoch-0 accuracy falls to chance (1/4)**, which is §8's *floor*. The
noise floor rises to meet the headroom and the gate closes from the other side.

⇒ **While the model is PROMPTED, the comprehension half is uninformative in both
configurations.** That is not a tuning problem. It is why this amendment is
blocked on native weights.

## 2 · The rebuilt observable

**Precondition, and it is a hard gate:** this observable may only be measured on
a model that has cleared **F-LOCAL** — native, **cardless**, first-attempt legal
render ≥ 0.90 and speak ≥ 0.90 (`SCOPE_LOCAL_FINETUNE` §3). Below that bar the
model is not a fluent speaker and "what does it take this to mean" is not yet a
question about the model.

**The probe.** Unchanged in shape — a fixed validated Tlön surface and four
forced-choice austere glosses, one true and three π-distinct near misses drawn
from the single-denoting-part mutation set. **No judge model**, for the reason
already registered: a judge is a second confabulation engine.

**The one change, and it is the whole amendment:**

> ⛔⛔ **THE LEXICON CARD IS NOT IN CONTEXT. THE CONVERSATION IS.**
> The model decodes from its weights; the only thing that varies across epochs
> is the shared history. Comprehension drift is then exactly what it claims to
> be: a **context effect on a weight-grounded interpretation**.

`D_comp` and `C_comp` are computed as before — mismatch against epoch 0, and
agreement between the two models — and enter `D` and `C` at equal weight with
the production half, exactly as §1 fixes. **Nothing about the weighting changes.**

## 3 · The calibration gate — §8, re-run against the new configuration

§8's check is not weakened; it is re-pointed at the configuration that can
actually pass it. Measured **at epoch 0 of the first native run, before any
conversation exists**:

| epoch-0 comprehension accuracy | verdict |
|---|---|
| ≥ **0.95** | ⛔ AT CEILING — still a lookup. The fine-tune has made decoding trivial and drift cannot be observed. **UNINFORMATIVE.** |
| ≤ **0.35** | ⛔ AT FLOOR — barely above the 0.25 chance line. Choices are noise; `D` measures resampling and the headroom gate closes. **UNINFORMATIVE.** |
| **0.35 – 0.95** | clear — comprehension has room to move in both directions. |

⭐ **THE FLOOR IS RAISED FROM CHANCE (0.25) TO 0.35 ON PURPOSE.** A model at
0.26 is indistinguishable from guessing at n = 32, and "indistinguishable from
guessing" is not a baseline a departure can be measured from. Registered now, at
a number, so it cannot be relaxed by whatever the first run happens to return.

⛔ **AND THE UNINFORMATIVE-CELL RULE STILL BINDS (§5.2).** If this gate closes,
the comprehension half is **UNINFORMATIVE, NOT A NULL**, it may not contribute to
a boundary result, and the honest report is that Act 2 measured the production
half only — stated as a limitation, never by silently dropping the half.

## 4 · The falsifier this amendment must survive

> **Fires if:** epoch-0 comprehension is outside 0.35–0.95 on a model that has
> cleared F-LOCAL.

Then the probe design is wrong *even for a fluent speaker*, and the registered
recovery set is bounded and fixed here:

1. **Widen the distractor set** beyond single-part mutations — two-part
   mutations are further away and easier; **one-part-plus-decoration** is nearer
   and harder. (Nearer, not further: the failure mode is ceiling.)
2. **Longer / deeper probe surfaces** — more slots to misread.
3. **Reduce the option count** 4 → 3, raising chance to 0.33 and compressing the
   usable band deliberately, so a small real effect is not hidden under a wide
   floor.

Persistent firing across all three ⇒ **BOUNDARY: comprehension drift is not
observable in this grammar**, reported as a finding about the language — an
exactly-invertible grammar may simply not admit interpretive drift — and not as
a failed measurement.

## 5 · What is NOT changed

- §1's **equal weighting** of the two halves. Unchanged.
- The **production half** in every respect.
- `D`, `C`, the **yoked control**, the MDE, the headroom gate, F2–F5, the
  no-transcript rule, the four axes and the stopping rule. All unchanged.
- The **primary estimator** — π-impression identity — and the secondary graded
  estimator's EXPLORATORY status. Unchanged.

## 6 · Sequencing

This amendment **cannot be exercised until a model has cleared F-LOCAL**. It is
locked now so that the observable is fixed *before* anyone sees a native model's
comprehension number — which is the entire point of pre-registration and the
reason it is being written at the moment the shape was decided rather than at the
moment the data arrives.

⛔ **NOTHING IN THIS AMENDMENT AUTHORISES A FINE-TUNE, A BACKBONE, OR A SPEND.**
Those remain open calls in `SCOPE_LOCAL_FINETUNE.md`.
