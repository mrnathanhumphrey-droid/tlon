# The unscoreable speaker — Run 0's crash, diagnosed and guarded

**What broke.** Run 0 (`e91f7c11`, mapping @5e-6) trained cleanly, persisted
17.42 GB to the hub, and then died inside the instrument:

    tlon/discourse/transient.py  permutation_null
    means.append(sum(len(x & y) for x, y in zip(a, b)) / len(a))
    ZeroDivisionError            # len(a) == 0

**Why.** A chain of *n* turns holds *n − lag* pairs. `act2_model_lag.py` drops
chains with fewer than 3 usable turns, so lag 1 and lag 2 are always safe — but
**lag 3 needs a 4-turn chain and lag 4 needs a 5-turn one**, and nothing
guaranteed those. The 5e-6 mapping object was degenerate enough that no chain
reached the length its longer lags required. The cell was empty; the null
divided by its size.

⛔ **The traceback said INSTRUMENT. The truth was SPEAKER.** *"It produced no
exchange long enough to score"* is a **diagnosable state, not a code fault** —
and on a rented box it cost the entire read of a run whose weights were fine.

---

## ⛔⛔ The crash was the cheap half of the bug

The obvious fix is to return `nan` instead of dividing. That would not crash —
it would **fabricate a finding**:

| value | `>= Z_LAG1_MIN` (6.0) | `<= Z_LAGN_MAX` (3.0) | what the verdict table then says |
|---|---|---|---|
| `nan` | False | False | perceive collapsed **and** release persists |
| `None` | TypeError | TypeError | crash, one step later |

An unmeasured lag would render as **"(d) collapsed toward content-free"** or as
**"content persists"** — substantive rows of §4.2, with a threshold attached,
about a number nobody ever measured. ⭐ Same family as the F-LOCAL rule already
in the verdict tool: `fired is None` means UNSCOREABLE and is **not** a pass.

**An unmeasured axis is not a failed one and is certainly not a passed one.**

---

## What was built

**1 · `lag_pairs(chains, lag)`** — the scoreability question asked in ONE place.
`lag_profile` returned `nan` for an empty cell while `permutation_null` divided
by that cell's zero length; the two disagreed about which cells exist. Both now
count through this function, and `lag_profile` **asserts** the agreement rather
than restating it in a comment.

**2 · `UnscoreableLag(MultiturnError)`** — raised, not returned, and carrying
`lag`, `n_pairs`, `n_chains`, `n_turns`, `lengths`. ⭐ **Raised deliberately**: a
sentinel return has to be checked at all five call sites and one would be
missed — the exact shape of the zero-scope guard that had a third call site and
cost a trained model. An exception cannot be ignored into a pass. Subclassing
`MultiturnError` means the corpus-side callers that already catch it keep
refusing rather than silently accepting an empty cell.

**3 · `act2_model_lag.py` scores per-lag.** Run 0 lost lag 1 and lag 2 — which
*were* scoreable — to the lag that was not. Now each lag is attempted
separately, `z` is `null` where the cell is empty, and the run writes a report
with `verdict: UNSCOREABLE`. ⛔ Not `REFUSED`: a refusal is the gate saying the
speaker **failed a criterion it could measure**, and filing "emitted nothing"
under the same name as "emitted the wrong thing" loses which one happened.
⛔ The RNG stream is unharmed by a skip — `permutation_null` refuses *before* it
draws, so the scoreable lags consume exactly what they would have consumed.

**4 · `act2_fullft_verdict.py` refuses to read an axis off a blind lag.** A new
verdict `NO VERDICT — speaker unscoreable`, distinct from `INSTRUMENT FAULT`
(§4.1 = *the weights did not move*; here the weights moved and the resulting
speaker said nothing). It catches `None` **and** `nan` — the second closes a
pre-existing hole where a permutation null with zero spread produced `nan` and
read as an axis failure. §4.1 still runs first.

**5 · The pipeline halts on exit 5.** ⛔⛔ Without its own branch, exit 5 falls
into the `else` whose rule is *"epoch 1 left no readable state to protect, so
run epoch 2"* — true of a FAILED axis, **false of an UNMEASURED one**. A
degenerate speaker does not become scoreable by training it further; the default
path would have bought a second epoch to reproduce the same non-result.

---

## ⭐⭐ `n_pairs` now travels with every `z`

A z is only as good as the cell it came from, and **nothing in any artifact
recorded the cell size.** Measured from the two reports on disk:

| run | chains used | dropped | turns | lag-4 pairs |
|---|---|---|---|---|
| rung 1b′ | 12 | 0 | 120 | **72** |
| rung 2 | 6 | **6** | 30 | **between 6 and 10** |

⛔ Rung 2's lag-3 (−0.388) and lag-4 (−0.484) came off a handful of pairs
carried by whichever chains happened to run long, and the exact split **is not
recoverable** — the report stored only the totals. Run 0 degraded one step past
that cliff.

⭐ **No fired verdict is affected.** Rung 1b′'s floor rests on full-length
chains, and rung 2's `STOP — perceive killed` was decided at lag 1, whose cell
was never thin. Verified by re-running `decide()` on both runs' own artifacts:
both reproduce their recorded verdict exactly.

---

## Red-proof

Every guard was seen to fail. Each defect injected alone, suite run, file
restored and verified byte-identical by sha256:

| injected defect | result |
|---|---|
| no guard at all — the literal Run 0 crash | RED (4 failed) |
| the tempting fix: return `nan` instead of raising | RED (4 failed) |
| verdict tool stops detecting a blind lag | RED (9 failed) |
| pipeline loses its exit-5 branch | RED (1 failed) |
| `lag_pairs` miscounts — profile and null disagree again | RED (2 failed) |
| the lag tool drops `n_pairs` from the report | RED (1 failed) |

Suite **1720 → 1739**. Both linters clean. `bash -n` clean.

---

## Why this mattered more for the campaign than for Qwen

⛔ A non-Qwen base is **more** likely to produce a degenerate speaker on its
first run, and a crash there would have read as a broken harness — sending the
next hours into debugging the instrument instead of recording a fact about the
base. The campaign now gets a written report from a base that cannot speak Tlön,
which is a *result*, and the F-LOCAL-at-the-layer-rung rule is what keeps that
result from being mistaken for "this base is disqualified".
