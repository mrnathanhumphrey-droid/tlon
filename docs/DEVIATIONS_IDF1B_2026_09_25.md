# DEVIATIONS — IDF-1b (`docs/PREREG_IDF1B_2026_09_25.md`, LOCK `904b85df`)

The prereg is not rewritten. Every walk-back is recorded here, in the order it
was found, with the state of knowledge at the time it was written.

---

## D1 · Instrument 3 as first run measured the vocabulary swap, not held-out provenance

**Written before the corrected number exists.** The corrected instrument has not
been run at the time of writing, and no reading is made below.

### What the prereg says

> **3 · O-E-heldout.** Build the kernel from rebuild seed A; seed and score O-E
> chains from rebuild seed B's surfaces — the situation `read_lag` is actually
> in. Report the exact-hit rate and the lag profile.

### What was run

`I.rebuild(SEED_B)` resamples **both** the pair pool and the chain draw from
seed 90210, following A4′'s precedent in IDF-1. A4′ is a classifier over
**roots**, which the two pools share, so there a resampled pool is harmless and
is the stronger test. O-E is keyed on **exact surfaces**, and there it is not.

Measured:

| | |
|---|---|
| pool A (seed 20624) surfaces | 5,890 |
| pool B (seed 90210) surfaces | 5,871 |
| **shared** | **185 (3.2 % of B)** |
| draw B corpus surfaces also in draw A | **118 of 5,376 = 2.2 %** |
| draw B seed surfaces also in draw A | 37 of 1,268 = 2.9 % |

So the kernel was asked to continue surfaces it had essentially never seen —
not because the draw was held out, but because the **vocabulary was swapped**.
The arm's own fallback log says the same thing: **exact 47.2 % · root-set 7.5 %
· blind 45.3 %**. Nearly half its steps were blind reseeds.

### Why this matters to the reading table, and why nothing is read off it

The run produced lag-2 **0.1424**, which closes **72.7 %** of the blind-to-true
gap, and the locked READABLE branch fires on *either* arm closing ≥ 35 %. So by
the letter of the table, **READABLE fires on this arm alone.**

⛔ It is not read, for two reasons stated together:

1. **The arm is fidelity-collapsed.** Its lag-1 is **0.4961** against the D6
   model's **1.0278** and O-A's **1.0357**. A speaker that carries less than
   half as much forward has less to suppress at lag-2, so its low lag-2 is not
   evidence of release. This is the exact confound instrument 5 exists to
   remove, and instrument 5 is declared descriptive and non-gating.
2. **The locked vacuous-pass guard does not catch it.** §5 flags an arm whose
   lag-1 **z** falls below 6.0. This arm's lag-1 z is **+439.273**, because z
   scales with n = 5,000. The guard was calibrated on IDF-1's O-B F1-threshold
   arm, whose lag-1 went to literally 0.0000. ⭐ **A z-floor does not detect a
   half-collapsed speaker at large n; only the raw profile does.** That is a
   hole in a locked guard, found by data, and it is recorded here rather than
   patched into the prereg.

### The correction

Instrument 3 is re-run with the **pool held at seed 20624** and only the chain
draw varying (`pool_seed` in `act2_idf1.rebuild`, exposed as the default for
`act2_idf1b.py i3`). That is the instrument the prereg describes: a held-out
**draw**, not a held-out **vocabulary**.

⭐ The confounded form stays runnable as `i3 --free-pool`, so this entry can be
reproduced rather than taken on trust.

**This is a correction to a construction fault, not a threshold chosen after
seeing a result.** No number in the reading table moved, and the corrected
value was unknown when this was written.

### ⛔ Not resolved here

Whether READABLE may be read off the *corrected* instrument 3, and what to do
about the z-floor hole in a locked guard, are decisions for Nate and Wilson.
Resolving either unilaterally would be retrofitting.

---

## D2 · Instrument 5's knob, and what a matched read is not

**Written while instrument 5 was running; the knob findings below are from the
tuning stage, not from the read distribution.**

### The knob is bar-rate, not `responsiveness`, for the barring arms

The prereg says "with `responsiveness` tuned so their lag-1 matches the model's
measured lag-1 per dose". `responsiveness` cannot reach the target, and the
reason is a measured fact about the campaign's speakers:

| | lag-1 |
|---|---|
| O-A blind | 1.0357 |
| **D6 model, dose 0** | **1.0278** |
| O-C true | 0.9651 |
| O-E | 0.9580 |
| O-B top-1 | 0.9350 |
| O-E-noreplay | 0.8973 |

⭐ **The model carries more forward than every suppressing oracle, and less than
the one that suppresses nothing.** Barring is what removes carry, so the dial
that spans the model's fidelity runs from "bar nothing" — which is exactly O-A —
to "bar always", which is exactly the arm. That dial is the **bar rate**, and it
brackets the target where `responsiveness` does not.

Applied: at dose 0, O-B(4) matches the model's lag-1 at **bar-rate 0.127**.

⛔ `tune` reports a `bracketed` flag and refuses to present an endpoint as a
match. A bisection always returns something; returning a limit and calling it
"matched" is how an unreachable target becomes a silent falsehood in a table.
Two cases are reported as unreachable rather than papered over:
- **dose −1**, whose model lag-1 of 1.0495 is above even O-A's maximum;
- **O-E-noreplay at every dose**, whose ceiling of ~0.90 is below the model's,
  and whose blind-mix knob only lowers lag-1 further.

That second one is itself worth stating: **the noreplay speaker cannot reach the
model's lag-1 at all**, so its lower lag-2 can never be cleanly attributed to
better release rather than to carrying less.

### A matched read is not a corpus, and is not gated like one

The first 500-rep run died with `FORCE-PAIR STARVATION in cell ('kä','ki')`.
`build_transient` runs `check_force_pair_fairness` unconditionally — correctly,
and its source says so: a generated corpus that starves a force pair cannot
measure that transition.

⛔ **The guard was not loosened.** A matched read is 12 chains of 10 turns — 120
turns — and at that size some force pair is routinely unrepresented by chance.
The model's own read was 12 chains and was taken off a trained speaker, never
gated this way. Applying a corpus invariant to a read would have silently
discarded exactly the unlucky draws that make a distribution a distribution.

Instrument 5 therefore calls `chain_transient` directly through
`act2_idf1b.read_chains`, reproducing `build_transient`'s rng derivation byte
for byte — same seeds, same two streams, same pool and index — and omitting only
the corpus-level gate. The chains are the same chains.

⭐ A 5-rep smoke passed before this fired at 500. **A sample small enough to miss
an unlucky draw is a sample small enough to miss the bug.**
