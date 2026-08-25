# PRE-REG — 5: take away the free channels and the private partner. Does the code die, or move?

- **Date:** 2026-08-22
- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `c09d0fb3` (sha256[:8] of draft body at lock, 2026-08-22T17:01Z)
- **Arc:** Tlön phase 5. Follows `VERDICT_4_SELECTION_2026_08_20.md`
  (PREREG `c1f7d06c`, KILL A **FIRED**).
- **Lexicon:** `e2b8527010231a81fd31b6eeb9de3d8c` · **Referents:** 60, REVIEWED,
  unchanged.

## The crux this phase is built on

Phase 4 produced a code, and channel-blocking relocated it (`coda` +0.90 →
+3.15). The reason blocking fails is now clear, and it is not "we picked the
wrong channels":

**A code is only pathological when it lives somewhere novelty is free.**

Decoration costs nothing to vary. So a code in decoration buys perfect
comprehension *and* endless novelty without ever perceiving anything — both
constraints satisfied, neither honoured. If a code is forced into
meaning-bearing structure, then reusing it **is** repeating yourself, and R
punishes it. The two constraints finally bite the same surface.

So phase 5 does not block channels. It removes the *class*.

## What changes

### 1. The denotation projection π (new — this is NOT the existing `canon`)

`canon()` sorts order-insensitive slots: same meaning, different word order.
π is strictly stronger. **The listener never sees anything else, and R is
computed on π(scene) too.**

π strips exactly the fields **no signature can reference**. From
`referents/schema.py`, a `NodePattern` may constrain only:

    root_any · orient_any · aspect_root_any · edge_relator_any · via · at_depth

It has no field for **`degree`**, **`force`/coda**, or **aspect repetition
count**. Those three are therefore *unconditionally non-denoting*: no referent
can ever be picked out by them. π normalises them away. `orient` and
`aspect_root` **stay** — signatures do constrain those, so stripping them would
destroy real meaning.

Those three are precisely where the code went: `aspect_reps` +7.41, `degree`
+5.95, `coda` +3.15.

⛔ **This soundness argument must be a TEST, not a comment.** A CI check asserts
`NodePattern` has no field naming degree/force/aspect-reps. If someone later adds
one, π becomes unsound and every phase-5 number silently rots. The guard must
fail loudly on the schema, not on a string search of it
([[feedback_guard_that_searches_a_report]]).

### 2. R moves onto π as well — and this is not a convenience

If only the listener's view is projected and R is not, we trade the cipher
failure for the **noise failure**: the generator earns free novelty wiggling
decoration nobody can read.

Projecting R is also the position phase 0 already forces. **Q3 = 1: a fixed
scene has exactly one form.** Two utterances that differ only in non-denoting
decoration are *the same impression* and must not count as novel. We proved that
and then never enforced it in the novelty metric. This is making the code match
the result, not a patch.

### 3. Listener population with resets

The generator faces a **randomly drawn listener from a pool of K**, with one
member reset to fresh initialisation every T steps. A private code must be
re-agreed with everyone; honest description transfers for free.

## Predicted ambiguity is UNCHANGED — and that is checkable

`consistent()` matches on root, orient, aspect_root, edge_relator, via, depth —
none of the projected fields. **So π cannot change the confusability numbers**
(14–25 % ambiguous, `runs/confusability.json`) and they carry over intact. If a
re-run disagrees, π is stripping something denoting and the phase is void.

## One-line hypothesis

With the non-denoting channel class removed and the partner no longer private,
the scramble probe goes quiet, the naive-listener gap closes, and R still falls.

**I pre-register that this is NOT what happens.** I expect the code to **migrate
into selection and `aspect_root`** rather than vanish. That is the interesting
outcome and the one the kills below are shaped to catch.

## Falsifier (pre-registered kill conditions)

- **KILL A — CIPHER SURVIVED.** Scramble drop **> 1.0 pt** on any channel
  surviving π (`aspect_root`, `orient`), ambiguous stratum.
- **KILL E — THE CODE WENT UNDERGROUND.** ⛔⛔ **The naive-listener gap stays
  > 5 pts while the scramble probe reads clean.** The code moved into
  meaning-bearing structure where the probe cannot see it — *worse than phase 4,
  because it looks like success.* **This is the outcome I am most likely to
  misreport, so it is named before the run.**
- **KILL F — π IS UNSOUND.** The schema guard fails, or re-running
  `confusability.py` under π changes the ambiguity distribution. Everything else
  is void if this fires.
- **KILL C — NOVELTY INERT.** R under π does not fall relative to λ=0, or
  selection decidedness stays ≤ 0.55.
- **KILL D — M COLLAPSE.** Accuracy below each arm's **own** uniform floor by
  more than 5 pts (D1: never against a cross-regime constant).

## The detector this phase turns on: the naive-listener gap

Phase 3 pre-registered a held-out judge and never ran it. Phase 5 does.

**gap = acc(co-trained listener) − acc(naive listener), both on the learned
generator's output**, where the *naive* listener is trained **only on honest
random-generator data** and never enters the loop.

⛔ It must be trained on honest data, **not** on the generator's output. A
listener trained on coded data learns the code — the gap would read zero and the
test could not come back positive ([[feedback_verify_a_test_could_have_detected_before_trusting_its_null]]).

## Positive controls — TWO-SIDED, mandatory, before the experiment

Phase 4's floor was measured on a listener that could see decoration. π changes
what the probe is looking at, so the floor must be re-established
([[feedback_green_history_in_one_regime_is_not_evidence]]).

1. **Blindness (new).** Plant a code in a **stripped** channel (`aspect_reps`).
   Listener accuracy must be **unchanged** — proving π removed the receptor, not
   merely discouraged its use. A drop here means π leaks.
2. **Sensitivity.** Plant a code in a **surviving** channel (`aspect_root`).
   The probe must fire **> 1.0 pt** — proving it still detects a code that is
   actually there.

**If either fails, phase 5 does not run.**

## Arms (ablated, so we learn which move did the work)

| arm | π | population |
|---|---|---|
| phase-4 replication | no | no |
| π only | yes | no |
| population only | no | yes |
| **both** | yes | yes |

At **λ = 0 and λ = 2**. λ=0 is the primary test — phase 4 showed the code forms
with zero novelty pressure, so λ=0 is the cleanest read on whether the fix works,
with no novelty confound. Advantage normalised throughout.

## Priors to lose (pre-register against)

- That π alone fixes it. I expect migration into selection.
- That population alone fixes it. I expect it to reduce, not remove.
- That a quiet scramble probe means success. See KILL E — that is exactly what
  the dangerous outcome looks like.
- That M will fall. I expect M to **rise** under π: less surface variety, same
  ambiguity, easier classification. A rise is not evidence of anything good.

## Standing floor (reportable regardless)

- **Code dies:** first honest configuration in the project; the counter becomes
  conditionally publishable once KILL B is also settled.
- **Code migrates (expected):** we have shown the failure is structural rather
  than channel-specific, with a detector that sees it where scrambling cannot.
  Publishable and more interesting than a fix.
- **KILL F:** π was unsound; the schema told us so before any number was quoted.

## Cost / lane

Local, $0. 8 configurations × ~50 s, plus two positive controls and the naive
listener. Ledger row regardless.

## ⛔ BLOCKED — needs Nate's call

- **Lock this prereg.**
- **K and T** (pool size, reset interval). Proposing K=6, T=500 — cheap at our
  scale. Not a backbone decision, but it changes what "the partner" means, so
  flagging it.
- **KILL B** still unset and still deferred: the gloss auditor needs
  re-baselining on partial glosses. **No interpretability claim in this phase
  either.**

## Deferred, explicitly

**Conversational repair / clarification** — Nate's call 2026-08-22. It does not
fix the leak (it is a wider back-channel), but it yields a *bound*-based
detector: an honest listener cannot ask for help less often than the world is
ambiguous. See STATE.md. Not started while the leak is open.
