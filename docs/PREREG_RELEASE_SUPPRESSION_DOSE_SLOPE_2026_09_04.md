# PREREG — is the model's lag-2 persistence ENDOGENOUS, or driven by the corpus?

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `765b6787` (sha256[:8] of draft body at lock, 2026-09-04T18:47Z)
- **Date:** 2026-09-04
- **Fires on:** two adapters, `cp-s20624` and `ctw1-s20624`, read against the
  already-measured `ct-s20624` (the gate).
- **Written before either adapter exists.** No dose-arm model has been trained
  and no model-side lag number for any dose but 0 has been observed.
- **Gates:** the twelve-adapter batch and the conversational chatbot. Both remain
  blocked until this reads.

---

## 1 · What the gate left open, stated as the thing that could be false

`PREREG_CONTENT_TRANSIENT_MODEL_GATE_2026_09_03` (LOCK `abde6124`) returned
**REFUSED**, reading (c): perceive transmitted (model lag-1 z **+22.86** against
a floor of 6.0) and release did not (model lag-2 z **+6.56** against a ceiling
of 3.0) while its corpus suppressed lag 2 to z **−8.57**.

⭐⭐ **THE OBSERVATION THAT MOTIVATES THIS RUN.** At dose 0 the model's lag-2 mean
shared roots is **0.385** while its corpus's is **0.027** — the model is
**≈14× its own training data**. It is therefore not echoing residual corpus
content. It is *generating* persistence that the corpus does not contain.

Two mechanisms produce that observation and they demand opposite responses:

  a. **Transmission with gain < 1.** The corpus signal does move the model, but
     not far enough. Then more corpus signal is the lever, and the question is
     whether the reachable maximum suffices.
  b. **Endogenous persistence.** The base model's self-consistency prior
     manufactures the lag-2 coherence irrespective of the corpus. Then no
     corpus-signal strength is a lever at all, and the obstacle is the frozen
     base weights under a LoRA.

⛔ **ONE DOSE CANNOT SEPARATE THESE.** If dose +1 still reads above the ceiling,
"insufficient gain" and "no channel" produce the identical observation. That is
why this run measures a **slope across a controlled span**, not another point.

## 2 · The knob, and why the span is what it is

One knob: `suppression_window` in `tlon.discourse.transient`. LoRA rank, training
config, base model, seed, force map and pool are held fixed.

  * `window = 0` bars the single root the previous turn echoed — **the gate
    recipe, and the default.** A dose-0 rebuild reproduces train sha
    `dd40e22f85b0b6e4` byte-identically (red-proofed).
  * `window = k ≥ 1` additionally bars **every** root of the speaker's own
    preceding `k` turns, at positions −2, −4, … ⛔ Never −1: `offerable` is
    `provocation_roots − barred`, so barring the partner's turn would empty the
    echo set and collapse perceive.
  * `window = −1` bars nothing. **This is not a valid content-transient recipe**
    and `check_transience` refuses it; it is a labelled dose arm whose only job
    is to anchor the low end.

**Measured corpus-side before any GPU** (1445 chains, seed 20624,
`runs/act2/dose_curve_corpus.json`):

| dose | bar (roots) | echo_rate | self-overlap | lag-1 z | lag-2 z |
|---|---|---|---|---|---|
| −1 | 0.00 | 1.000 | 0.4245 | +423.85 | **+162.43** |
| 0 (gate) | 0.82 | 0.952 | 0.0269 | +427.63 | **−8.57** |
| +1 | 2.36 | 0.951 | **0.0000** | +392.15 | **−19.73** |
| +2 | 3.93 | 0.955 | 0.0000 | +385.65 | −20.86 |

⭐ **THE SPAN IS 182 z-UNITS** (+162.43 → −19.73) and **+1 IS THE CEILING**:
window 1 already drives self-overlap to 0.0000 and windows 2+ are numerically
identical to it. There is no ladder above +1 to climb, which is why the span was
extended downward instead.

## 3 · ⛔ ENTANGLED IS RULED OUT CORPUS-SIDE AND IS NOT TESTED HERE

The gate's design anticipated that cranking suppression might damage perceive —
release and perceive being adjacent lags in one corpus. **Measured across the
entire 182-z span, perceive is invariant**: echo_rate 1.000 → 0.949, lag-1 z
+385 to +428. The two are separable in the generator because they read different
slots — the echo is drawn from the partner's turn, the bar is applied to the
speaker's own.

⭐ Recorded as **eliminated in the corpus data**, not as untested and not as
forgotten. A future reader is entitled to know it was a candidate and why it is
absent from §4. ⛔ It is guarded, not merely observed: a test asserts the bar can
never reach the partner's turn, because a generator that over-barred would
produce a **false ENTANGLED verdict caused by tooling rather than by substrate**.

## 4 · The pre-declared readings

Run at each dose: `tools/act2_model_lag.py`, 12 chains × 10 turns, temperature
0.70, `max_new_tokens` 256, cardless, unconstrained — identical to the gate's
§4 so the three points are commensurable. **Chain accounting is reported first
and any dose with dropped chains is read as suspect before its z is quoted.**

Let `Δ_model = z_lag2(dose −1) − z_lag2(dose +1)` across a corpus-side span of
182 z. Both lags are measured at every dose.

| outcome | reading |
|---|---|
| **model lag-2 TRACKS the corpus** — Δ_model large, ordered `−1 > 0 > +1` | **TRANSMISSION WORKS, gain < 1.** There is a channel. The gain and the fact that +1 is the axis ceiling say whether the ceiling is reachable by corpus signal at all. If +1 clears 3.0 → recipe-strength fork, buy the batch at window 1. If +1 does not clear, the floor is measured **with a slope behind it** and the extrapolation is quantitative. |
| **model lag-2 is FLAT across the span** — Δ_model small, no ordering | ⭐⭐ **ARCHITECTURAL FLOOR, DECISIVE.** 182 z of corpus signal moved the model ~nothing, so the persistence is endogenous to the base weights. **The flatness IS the evidence** — not "we could not push hard enough" but "pushing the whole available range changed nothing." No LoRA-on-frozen-weights recipe fixes it; the next question is rank or a heavier intervention, and that is a separate decision. |
| **UNDERPOWERED** | The two points cannot resolve a slope — e.g. the model-side movement is within the noise of a 12-chain read. Report and refine (more chains, pre-declared) **before** concluding either of the above. |
| ~~ENTANGLED~~ | **Eliminated corpus-side** (§3). Not tested model-side. |

⛔⛔ **NO THRESHOLD CHANGE IS AUTHORISED BY ANY OUTCOME.** `Z_LAG1_MIN = 6.0` and
`Z_LAGN_MAX = 3.0` are imported from `tlon.discourse.transient` — the constants
the corpus was gated on — and are hashed into this body.

⛔ **A slope is not a GO.** Only dose +1 clearing the ceiling *while* lag 1 holds
above the floor unblocks the batch. A measurable gain that still leaves lag 2
above 3.0 is a STOP with a mechanism attached, which is more useful than a bare
STOP and is still a STOP.

⚠️ **POWER IS NOT CLAIMED.** 12 chains is sized against a corpus-scale effect,
as at the gate. This run distinguishes *large* movement from *none*; it does not
resolve a small gain, and a small gain must be read as UNDERPOWERED rather than
as flatness.

## 5 · What is deliberately NOT claimed

- **Nothing about LoRA rank.** Rank is held fixed on purpose: this asks whether
  the SIGNAL is strong enough before asking whether the CAPACITY is. A dose sweep
  that also moved rank would confound signal strength with capacity.
- **Nothing about the twelve-adapter batch**, which stays gated.
- **Nothing cross-recipe.** `cp-s20624` is a **dose arm, not a factorial cell**.
  Its corpus persists by construction (lag-2 z +162.43), so it must never enter
  the content-transient population — the same discipline as the drift run's
  self-pair arm: control, not data, tagged so it is structurally un-poolable.
- **Nothing about whether a human finds the result satisfying.**

## 6 · Provenance

- dose knob + corpus-side curve: `3bcd8b3`
- the gate this follows: `PREREG_CONTENT_TRANSIENT_MODEL_GATE_2026_09_03`,
  LOCK `abde6124`, verdict REFUSED, `runs/act2/retrain12_ct/model_lag_ct-s20624.json`
- instrument: `tools/act2_model_lag.py`, importing `lag_profile`,
  `permutation_null` and `check_transience` from `tlon.discourse.transient`
