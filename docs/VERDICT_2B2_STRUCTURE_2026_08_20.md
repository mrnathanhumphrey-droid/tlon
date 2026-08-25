# VERDICT — 2b.2: structure IS read; the per-channel half of the hypothesis is dead (KILL C)

- **Date:** 2026-08-20 · **Pre-reg:** `PREREG_2B2_STRUCTURE_2026_08_20.md` (LOCK `080bc40f`)
- **Artifacts:** `runs/2b2_results.json`; `tlon/listener/{model,train,evaluate}.py`, `tools/run_2b2.py`
- **Compute:** local RTX 5070 Ti, **60 s**, **$0.00**. 4,824,902 params, random init.
- **Lexicon:** `e2b8527010231a81fd31b6eeb9de3d8c`

## Result (novel-decoration split — the honest one)

| | |
|---|---|
| within **perspective** pairs | **99.5 %** [99.3, 99.7] n=7452 |
| within **diagnostic** pairs | **99.8 %** [99.7, 99.9] n=7244 |
| predicted outside the pair | 0.0 % |
| bag-of-roots, same items | 68.5 % |
| **model − bag-of-roots, paired** | **+31.3 pts** [30.7, 31.9] |
| shuffled-label null | 0.5 % (chance = 1.4 %) |

Per channel: aspect 100.0 · relator 99.9 · direction 99.9 · nesting 99.7 ·
orientation 99.6. **Spread 0.4 points.**

## Kill checks

| | | |
|---|---|---|
| A no structure read | diag 99.8 % | not fired |
| B shortcut only | persp 99.5 / diag 99.8 | not fired |
| **C flat channel profile** | spread **0.4 pts** | **FIRED** |
| D leakage | random−novel −0.2 pts | not fired |

## Verdict

**First half CONFIRMED.** A 4.8 M-parameter model trained from random init reads
relational structure in a nounless impression language. The diagnostic pairs are
root-identical, so 99.8 % cannot come from lexical identity, and KILL B did not
fire — the model is not merely reading the matrix position, since 8 of the 10
diagnostic pairs are immune to that shortcut.

**Second half FALSE — KILL C fired.** The per-channel profile is flat.

**My pre-registered priors were both wrong, and that is the point of writing
them down:**
- I predicted **nesting would fail**. It scored **99.7 %**.
- I predicted **aspect would be hardest**. It scored **100.0 %** — the best channel.

## ⚠️ What KILL C actually means here

The pre-reg said a flat profile means "channels are uniformly legible … the
per-channel framing is wrong and should be dropped." That reading is too
generous to itself. **At 99.6–100 % every channel is at ceiling, and relative
difficulty is not measurable at ceiling.** The per-channel question is not
answered; it is unasked. The honest statement is *the task is too easy to
separate the channels*, not *the channels are equally easy*.

## Deviation from the locked method (recorded, not hidden)

The pre-reg says 60 referents. `schema.load_all()` merges **70** — the 10 Tier-2
and Tier-3 pegs in `referents.draft.yaml` are not `seed_2a`, but `load_all` does
not filter on that. They carry no `minimal_pair`, so they enter training and
appear in the overall figure while being excluded from every headline number by
construction. The within-pair results are unaffected. Fix `load_all` or amend
the method before this figure is quoted anywhere.

## Next instrument — learning curves, not final accuracy

At ceiling, sample efficiency is the discriminating measurement: a harder
channel is acquired **later**, not less well. Re-run the per-channel breakdown
across a data-budget sweep (e.g. 50 / 150 / 500 / 1500 examples per referent)
and report the budget at which each channel crosses 90 %. That is a new
hypothesis and needs its own lock.

## Scope

- Overall accuracy (99.7 %) is context only and should never be quoted as the
  result; the 20 original pegs are root-solvable.
- The cipher-control null band specified in the pre-reg has **not yet been run**.
  Owed before phase 3.
- Nesting rests on a single pair (P5) and its CI is correspondingly wide.
