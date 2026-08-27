# RESULTS — the multi-turn locality run

**Box `6eccef0e` terminated. ≈$16, ~7h15m wall. Corpus sha `5e796d5a`, adapter
`runs/act2/adapter_mt`, artifacts `runs/act2/logs/mt_run/` (31 files).**

## ⭐⭐ F-LOCAL CLEARS — first time in the project

    render   82.0 → 96.1 %      speak  97.3 → 100.0 %     comprehension 57.0 %
    F-LOCAL CLEAR (threshold 0.90 on the WORST limb). "A NATIVE SPEAKER."

⚠️ **AND THIS BREAKS MY OWN PRE-DECLARATION.** `RENDER_SPEAK_STABILITY_IS_NEUTRAL`
locked the claim that render/speak would *barely move* and that such stability
would prove nothing. **+14.1 points is not barely moving.** The prediction failed,
in the flattering direction, which is the direction I do not get to re-interpret.
Recorded as a failed prediction, not retro-fitted into a success.

## Q1 — force transmission: ⚠️ POSITIVE (UNATTRIBUTED)

    ki→ka hit rate 1.000 over 546 transitions (14 exchanges, window=1)
    beats chance ✅   beats realized marginal ✅   beats run-3 baseline: NO BASELINE

Capped at UNATTRIBUTED **by design**: arm 3 yielded **0 usable transitions**, so
the attribution null is missing and the structure cannot be credited to this
training. The three-null check did exactly what it was built to do.

## Q2 — can the substrate hold a flat prior? ⚠️ FOUNDATION FINDING

    ka  ⚠️ THIRD THING (invented per-row structure)
    ko  ⚠️ COLLAPSED TO A GLOBAL PRIOR
    ku  ⚠️ COLLAPSED TO A GLOBAL PRIOR
    kä  ✅ HOLDS FLAT

**3 of 4 uniform rows fail.** The substrate largely cannot hold the flat prior
RULING 12's emergent-convention design assumes. This is the pre-declared
foundation finding: emergence is not well-posed against a prior the model cannot
represent. **Next work is a substrate fix, NOT abandoning the uniform target.**

## ⛔⛔ ACCUMULATION WAS NOT THE COLLAPSE MECHANISM

| arm | degenerates | last-qtr validity |
|---|---|---|
| 1 · new model, **accumulating** | 0/1 | 1.000 (TTR *rose* 0.864→0.913) |
| 2 · new model, window=1 | 0/14 | 1.000 |
| 3 · run 3 re-served, window=1 | 14/14 | 0.000 |

The new model sustains 40 turns **with full accumulating context** — the exact
condition locality was designed to avoid. **The depth-1 blindfold is not what
fixed this.** Locality's architectural premise is unsupported by its own run.

## ⛔ ARM 3 — DIAGNOSED, AND BOTH MY HYPOTHESES WERE WRONG

Validity 0.000 with all-null transcripts looked like either (a) contract mismatch
is catastrophic, or (b) plumbing. Nate insisted the discriminator is *what the
model emitted*, not that it was null. Reproduced directly:

    seed shown : "fen xun tan sim krax hrem nimnimnimnimas ki"
    run 3 turn1: {"force":"u","node":{orient["fen","xun"],relator"tan",
                  quant"sim",root"krax",root"hrem",aspect_root"nim",reps 4}}
    run 3 turn2: IDENTICAL
    new model  : force "ka", then "ko" — fresh, varied, valid

**Run 3 emitted schema-shaped JSON with an ILLEGAL force (`u` ∉ {ka,ki,ko,ku,kä})
that near-verbatim ECHOES the seed.** `PS.validate` correctly refused it. The
null was a *correct refusal of real output* — not silence, not plumbing.

⇒ **Arm 3 measures the known depth-1 ECHO** (on record at 8/10, 1/8 distinct),
not the train/serve mismatch. The seductive hypothesis — that the mismatch is
catastrophic and vindicates the unified-string decision — is **NOT supported**.
The temp sweep generating fine on the same adapter at the same moment (13/16 at
t=1.2) was the evidence that should have pulled hardest, and it was right.

⭐ **The real contrast stands:** same prompt, same window — run 3 echoes with an
illegal force, the new model paints fresh valid scenes. **Multi-turn training
fixed the depth-1 echo.**

## ⛔ WHAT THIS RUN DOES NOT MEASURE

**No drift. No σ_cp. No pact.** Those are the arena proper and are downstream of
a model that sustains. This run says a model sustains; it says nothing about
whether two of them drift.

## OPEN

1. **Arm 3 must be re-run to attribute Q1** — needs a run-3 baseline with usable
   transitions. Its forces are illegal, so force-fidelity cannot be computed from
   it at all; a different baseline design is required.
2. **Q2's foundation finding blocks the arena** — fix the substrate's ability to
   hold uniform before emergent convention means anything.
3. **Locality's premise is unsupported** — accumulation was not the mechanism;
   what fixed it (training vs contract) is unseparated.
4. Model card for run 3 says it "does not clear its own gate" — still true of
   run 3, but the new adapter does. Publish decision pending.
