# AMENDMENT B to PREREG `c0de41c7` — the self-pair lockstep floor

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `115fe1d3` (sha256[:8] of draft body at lock, 2026-09-02T20:05Z)
- **Date:** 2026-09-02
- **Amends:** `PREREG_POSITIVE_CONTROL_KA_2026_09_01.md` §4 (adds an arm), §5
  (the reading), §7 (cost). ⛔ **The locked prereg body is NOT rewritten** —
  `c0de41c7` stands and still verifies, as does
  [`AMENDMENT A`](AMENDMENT_A_POSITIVE_CONTROL_MATCHED_NULL_2026_09_02.md)
  `8f3024fb`, which this does not disturb.
- **Written before any box fired.** No data exists under the un-amended design.

---

## 1 · What the matched null does NOT subtract

[Amendment A](AMENDMENT_A_POSITIVE_CONTROL_MATCHED_NULL_2026_09_02.md) matched
the null to the treatment's memory model, so both arms carry the same
store-tracking and it differences out. **That closes the store-regression
confound and only that one.**

⛔⛔ **IT DOES NOT SUBTRACT IDENTICAL-SPEAKER LOCKSTEP.** Two copies of the same
weights are maximally legible to each other. They can fall into step in
`SHARED-LIVE` in a way they cannot in `SHARED-YOKED` — not because a convention
formed between two individuals, but because each is the most predictable
possible interlocutor for the other. `SHARED-YOKED` removes **responsiveness
entirely**; it does not remove **identical-responsiveness specifically**. So
lockstep survives into `LIVE − YOKED` and arrives wearing the signature of
coupling.

⭐⭐ **AND THIS OBSERVABLE HAS ALREADY BEEN FOOLED BY IT ONCE.** In the drift run
([E3](../MEASUREMENTS.md#e3)), `s20621` paired against **itself** read
**−0.827** — a *larger* apparent convergence than any real pair achieved (best
−0.611). Without that arm, six converging pairs led by −0.611 would have been
the headline. The self-pair arm did not confirm the result; **it inverted it.**

⇒ A positive control with no self-pair floor can produce exactly that inversion
again, and this time it would be certified by a run whose every other guard
passed.

## 2 · The added arm

**Arm 3 — SELF-PAIR.** One adapter as **both** speakers, run through the same
two arms as a real pair: `SHARED-LIVE` and `SHARED-YOKED`, estimand
`LIVE − YOKED`, identical settings.

- **7 self-pairs, one per adapter, 28 replicates each** — the same replicate
  count as the real pairs. ⛔ **Deliberately not fewer.** A floor measured worse
  than the effect it bounds cannot bound it; an arm at 3 replicates would give a
  floor whose interval swallows the very region the decision lives in.
- **Unit of independence: still the ADAPTER.** Seven self-pairs are seven
  clusters; the dyadic bootstrap applies unchanged.

### 2.1 The aliasing guard is bypassed LOUDLY, or not at all

Pairing an adapter with itself is the arrangement `_assert_two()` exists to
refuse — it is how every pre-2026-08-31 Act-2 "interaction" was one impression
talking to itself. The bypass is therefore:

- **`--allow-self-pair`, off by default**, and the probe **`SystemExit`s** on a
  same-adapter pair without it. Not a warning.
- **Announced at run time** on the arm that uses it, naming what is being
  suspended and why.
- **`self_pair: true` written into every such transcript**, and
  `act2_drift.load_pairs(self_pair=...)` partitions on that field — so a
  self-pair transcript is **structurally unable to enter the real-pair
  analysis**. The separation is in the loader, not in a convention about
  filenames.
- **Logged**, so the bypass appears in the run record rather than only in the
  invocation.

⛔ The self-pair arm is **CONTROL, NEVER DATA.** It never contributes to the
real-pair estimate; it only sets the floor that estimate must clear.

## 3 · The pre-declared floor, and the margin

> **The self-pair floor is the self-pair arm's own `mean(LIVE − YOKED)`.**
>
> **A real-pair effect clears it only if
> `mean(real) − mean(self) ≤ −0.311` W2 units** — i.e. by at least `FLOOR_ka`,
> [§3](PREREG_POSITIVE_CONTROL_KA_2026_09_01.md) of the locked prereg.

⭐ **The margin reuses the calibrated floor rather than inventing a second
threshold.** `FLOOR_ka` is the smallest effect this design recovers at 80 %
power; requiring the real-pair effect to beat the artifact floor *by that same
amount* asks for a separation the instrument has been shown able to see. A
freshly chosen margin here would be a number with no calibration behind it,
picked with the outcome already imaginable.

⛔ Neither the floor nor the margin may be moved after the run.

## 4 · The reading — four outcomes, all pre-declared

| outcome | condition | verdict |
|---|---|---|
| ⭐ **GO** | real pairs `SHARED-LIVE < SHARED-YOKED` beyond `FLOOR_ka`, **AND** the effect clears the self-pair floor by the §3 margin | Coupling. The instrument is demonstrated on real data. The [A4](../MEASUREMENTS.md#a4) regression check still applies. **Both conditions required.** |
| ⛔ **STOP** | no real-pair movement beyond `FLOOR_ka` | Tlön shows no measurable `force:ka` convergence **even under the shared memory that produces strong convergence in natural language.** A finding, bounded by prereg §6. |
| ⚠️ **GO-BUT-LOCKSTEP** | real pairs move **and** the self-pair moves comparably (margin not cleared) | ⛔⛔ **NOT COUPLING.** The movement is identical-speaker lockstep — the [E3](../MEASUREMENTS.md#e3) inversion, pre-named so that a real-pair movement cannot be read as coupling while the self-pair shows the same thing. Reported as **artifact floor**, never as a weakened GO. |
| ⚠️ **UNDERPOWERED** | the CI cannot place the real-pair effect against either floor | An underpowered go/no-go. Decide on `n` before concluding anything. ⛔ Not read as GO and not read as STOP. |

⛔⛔ **A GO MUST SURVIVE BOTH FLOORS AND THE REGRESSION CHECK.** Amendment A's
algebra stands: on a single axis, independent store-tracking closes the gap by
`(1−λ)` with zero coupling, so only the matched null separates coupling from
regression. Adding the self-pair floor separates coupling from lockstep. **They
are different confounds and neither substitutes for the other.**

## 5 · Cost, restated honestly

The arm **roughly doubles the run**: 7 real pairs + 7 self-pairs = **14 pairs**
at 28 replicates × 2 arms.

⇒ **44–72 GPU-h**, from the same measured marginal that gave prereg §7 its
22–36 for seven pairs. ⛔ **The cheaper end is still not adopted.**

⭐ **The pair-1 checkpoint threshold does not change.** It is a *per-pair* bound
(11,314–18,514 s), and both the budget and the pair count doubled, so the
per-pair arithmetic is identical. The early-abort fires on exactly the same
condition it did before.

## 6 · What does NOT change

`FLOOR_ka` = 0.100 ka = −0.311 W2 units at power 0.848 · Δ\* = 0.5939 · the
`SHARED-YOKED` matched null and its transcript-level verification · the
`store_was_shared` attended check and the raised window · prereg §6 scope · §8
guards · the forced summarisation deviation · **no training, 7 existing
adapters, `force:ka` the only live axis.**

## 7 · What would make me wrong about this amendment

- **A self-pair floor near zero does not prove lockstep is absent** — it proves
  it is absent **for this statistic**. [E3](../MEASUREMENTS.md#e3) is a
  *marginal-distance* floor, and two identical adapters have coinciding
  marginals by exchangeability, so the arm is structurally weak at detecting
  trajectory-level lockstep. ⛔ It bounds what `W2` can be fooled by, not what
  lockstep can be.
- If the self-pair arm's own interval is wide, the margin test is
  **UNDERPOWERED rather than passed** — a floor that cannot be placed cannot be
  cleared. That is the fourth outcome, and it must be read, not rounded past.
- If lockstep and coupling are themselves entangled — two identical speakers
  *are* the easiest case for a genuine convention to form in — then subtracting
  the self-pair floor removes real signal along with the artifact. **This
  amendment chooses the conservative direction knowingly**, and a STOP under it
  is bounded accordingly.
