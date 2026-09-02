# AMENDMENT A to PREREG `c0de41c7` — the null must run the treatment's memory model

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `8f3024fb` (sha256[:8] of draft body at lock, 2026-09-02T17:26Z)
- **Date:** 2026-09-02
- **Amends:** `PREREG_POSITIVE_CONTROL_KA_2026_09_01.md` §4 **arm 2 only**, and
  §4.2's decomposition consequently. ⛔ **The locked prereg body is NOT
  rewritten** — `c0de41c7` stands and still verifies. This document supersedes
  that one arm and nothing else.
- **Found:** while building §4.2, before any box came up. **No data exists under
  the superseded design**, so nothing is being reinterpreted after the fact.

---

## 1 · What was registered, and why it does not work

| | partner | memory model |
|---|---|---|
| **Arm 1 SHARED** | adaptive | full chronological store, both read everything |
| **Arm 2 YOKED** *(as registered)* | recording | **own chain + the partner's single most recent turn** |

⛔⛔ **THE CONTRAST VARIED TWO THINGS AT ONCE.** `W2(SHARED) − W2(YOKED)` mixes
**partner-adaptivity** with **memory model**. The shared arm's speakers read a
long full transcript; the yoked arm's read their own chain plus one turn.
`force:ka` is a rate over generated scenes and context length changes
generation, so a negative delta could have been produced entirely by the second
factor. **A GO would not have distinguished *they coupled* from *long context
shifts the force distribution*.**

⭐ **THIS IS THE PROJECT'S OWN ARGUMENT, TURNED ON ITSELF.**
`PREREG_ACT2_DRIFT` §4 rejects a solo control in these words:

> *"A solo/monologue control varies two things at once — partner-adaptation
> **and** whether the context is conversation-shaped. Any difference would be
> unattributable, which is the exact defect this control exists to prevent."*

The YOKED null was imported because it was *"the project's existing one"*. It
was existing **because it was matched to the asymmetric treatment arm.** Against
a shared-memory treatment it is not matched, and *"we already use it"* is not a
reason — it is the shape of the mistake.

## 2 · The amended arm 2 — SHARED-YOKED

**Arm 2 is now:** each speaker reads a **shared append-only store** whose partner
contributions are a **recording**. Same memory model, same context length and
shape, same content. **Only adaptivity differs** — which is the whole and only
thing the estimand is supposed to be about.

This is the H2 frozen-control move applied correctly: *co-adaptation-specific
share = interacting − frozen*, **within one memory model**.

⭐ **The change is one line per call site** (`mode=YOKED` → `mode=null_mode`).
`Replay` is deliberately deaf to `history`, so it is mode-agnostic by
construction and its output still enters the store.

### 2.1 It is verified from the transcript, not from the flag

⛔⛔ A flag that is passed and ignored leaves no trace in a result. So the probe
**refuses to write a shared run whose arms did not actually share**:
`store_was_shared()` reads the per-turn `n_shown` already recorded in every log —
under a shared store that reaches the full history, under the asymmetric rule it
reaches roughly the speaker's own half plus one. All three arms are checked and
a failure is a `SystemExit`, not a warning.

Red-proof: `tests/test_shared_memory_arm.py` §7 — the check is shown to return
**True** on a shared transcript and **False** on an asymmetric one. A check that
passed on both would be decoration.

## 3 · What this does to §4.2, and why the decomposition alone could not have worked

§4.2 registered a post-positive check: is a GO coupling, or both speakers
regressing toward the shared store?

⛔⛔ **IN ONE DIMENSION THAT CHECK CANNOT BE DONE FROM ENDPOINTS.** If each
speaker moves a fraction `λ` toward the store value `S`, then
`A' = A + λ(S−A)` and `B' = B + λ(S−B)`, so the gap becomes
**`|A'−B'| = (1−λ)|A−B|`** — *independent* store-tracking closes the gap by
exactly `(1−λ)`, with no coupling whatsoever. `force:ka` is a single axis, so
there is no direction orthogonal to the store to project the residual onto.
**Coupling and common-attractor regression are observationally equivalent from
endpoint positions alone.**

⇒ **The matched null is not a nicety, it is the only thing that separates them.**
With store content matched across arms, both speakers' tracking of the store
differences out, and a surviving `SHARED − SHARED-YOKED` gap is attributable to
mutual adaptation.

**§4.2's recording is retained as a CONFIRMATORY check, not the primary control:**
per-speaker `force:ka` per quarter, and the store's own running `force:ka` per
quarter, are computed from the existing transcripts (no harness change — the log
already carries every turn and its speaker). A GO accompanied by large
same-direction co-movement toward the store is reported as
**[A4](../MEASUREMENTS.md#a4) CO-MOVEMENT**, a named outcome, not a weakened GO.

## 4 · What does NOT change

- **`FLOOR_ka` = 0.100 ka = −0.311 W2 units, power 0.848.** The calibration
  models cloud sizes, the frozen ruler and planted closure; none of it depends
  on which null is used. §3 of the prereg stands unamended.
- **Δ\* = 0.5939**, the §5 three-way reading, §6's scope limits, §7's 22–36 GPU-h
  and the pair-1 checkpoint, §8's guards. All unchanged.
- **Cost.** Identical — the same number of exchanges, one of them in a different
  mode.
- The **forced summarisation deviation** (§4) and everything it bounds.

## 5 · What would make me wrong about this amendment

- If the shared store makes the **replayed** partner's turns unreachable in
  practice (e.g. context truncation at 80 turns), the two arms stop being
  matched for a different reason, and `store_was_shared` would pass while the
  model silently drops the head of the store. ⛔ **Not currently checked** — the
  transcript records how much context was *handed*, not how much was *attended*.
  Stated here rather than discovered in the result.
- If `Replay` running under SHARED changes its own emission (it should not — it
  ignores `history` — but that is an argument, not a measurement), then the
  recording is no longer identical across arms and the yoke is broken.
