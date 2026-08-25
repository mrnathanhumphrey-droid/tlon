# VERDICT — Phase 5, denotation projection + listener population

**PREREG:** `docs/PREREG_5_DENOTATION_2026_08_22.md`, LOCK `c09d0fb3`
**Date:** 2026-08-22 · **Spend:** $0.00, all local
**Runs:** `runs/pi_controls.json` · `runs/phase5.json` · `runs/phase5_v6.log`
**Superseded logs:** v1–v5 — see deviations. **Do not quote them.**

---

## Headline

**KILL E FIRED.** The interventions did not remove the private code. They removed
the part of it the scramble probe can see.

Against the correct baseline, `aspect_root` excess falls to **−2.82, −7.00,
−0.48, −5.20, +0.48** in five of eight arms — the probe reads clean — while the
**naive-listener gap holds at 8–13 points in every arm**. That is precisely the
condition KILL E names: *the code moved into meaning-bearing structure where
scrambling cannot see it — worse than phase 4, because it looks like success.*

I pre-registered this as the outcome I was most likely to misreport. It is the
outcome.

## The two measurements, side by side

`CODE` = naive gap minus the frozen arm's gap. `vs FROZEN` = `aspect_root` drop
on the ambiguous stratum minus the same drop in the frozen arm.

| arm | λ | `aspect_root` vs FROZEN | CODE gap | KILL A | KILL E |
|---|---|---|---|---|---|
| phase-4 replication | 0 | **+10.61** | +8.00 | fired | — |
| phase-4 replication | 2 | **+15.42** | +12.20 | fired | — |
| π only | 0 | **+20.71** | +8.40 | fired | — |
| π only | 2 | −2.82 | +9.07 | clean | **FIRED** |
| population only | 0 | −7.00 | **+13.33** | clean | **FIRED** |
| population only | 2 | −0.48 | +8.84 | *(coda +3.08)* | — |
| BOTH | 0 | −5.20 | +11.68 | clean | **FIRED** |
| BOTH | 2 | +0.48 | +10.19 | clean | **FIRED** |

**The probe improves. The gap does not.** Every intervention that quiets the
scramble probe leaves the naive gap untouched — and `BOTH`, the arm designed to
fix the problem, fires KILL E at **both** λ.

⛔ The KILL A / KILL E columns printed by `run_phase5.py` used the RANDOM
baseline and are superseded by this table. See deviation D5.

## Why the earlier baseline was wrong

The frozen arms — listener never updates, so **co-adaptation is impossible and no
code can exist** — still show `aspect_root` drops of **+24.89, +11.95, +26.21,
+18.82** on the ambiguous stratum. Against the random-policy baseline that reads
as KILL A firing in an arm where a code is structurally impossible.

So a large `aspect_root` drop does **not** indicate a code. A generator that
merely *concentrates its aspect choices* produces one, because scrambling then
destroys information the listener legitimately relies on. The honest reference is
not a random policy but **an optimising policy that cannot negotiate**. Once that
is subtracted, most of the apparent cipher signal disappears — and what remains
is carried by the gap, not the probe.

## What each intervention actually did

**π worked, exactly as designed, and did not help.** `pi_controls.json`: a 2-bit
code in a stripped channel buys **−0.30 pts** under π versus **+6.67** without
it, with the same code and the same size. The receptor is gone, not discouraged.
Every stripped channel is correctly reported as *probe undefined* rather than
measured. And the gap is unchanged — at λ=0 it is slightly **worse** (+8.40 vs
+8.00).

**Population squeezed the visible channels.** `aspect_root` excess drops hardest
under population. But at λ=2 without π the decorative channels light up instead
(`coda` +3.08 over frozen), which is **relocation for the third time in this
project**: phase 4 blocked two channels and the code moved to `coda`; here
population squeezes `aspect_root` and it moves to the decoration; add π to close
that and the gap simply stops being visible anywhere.

**Nothing reduced the code at λ=0**, the pre-registered primary read. Baseline
+8.00; π +8.40; population +13.33; both +11.68.

## The picture this supports

Interventions relocate private information; they do not remove it. The naive gap
sits at 8–13 points regardless of which channels exist, which is consistent with
a roughly conserved quantity that finds whatever carrier is available. The
scramble probe measures *where*; only a judge that never entered the loop
measures *whether*.

⚠️ **One seed per cell, no confidence intervals.** The between-arm differences
(+8.00 vs +13.33) are **not** interpretable and I am not claiming population made
λ=0 worse. What is robust is the sign and rough magnitude: every arm, both λ,
8–13 points, none near zero.

## KILL results

- **KILL A** — fired in 3 of 8 against the frozen baseline (phase-4 replication
  both λ, π-only λ=0), plus `coda` in population-only λ=2.
- **KILL E** — **FIRED in 4 of 8**, including `BOTH` at both λ. The headline.
- **KILL F** — did not fire. π is sound: the schema guard passes with red-proofs
  on both branches, and per-sample equality of `matches` **and** `consistent`
  holds over ~7,200 (scene, referent) pairs, so ambiguity is provably unchanged.
- **KILL C** — did not fire. Decidedness 0.77–0.88 against 0.50 at init.
- **KILL D** — did not fire. Every arm sits above its own uniform floor.
- **KILL B** — **still not measured.** The gloss auditor has not been
  re-baselined on partial glosses. **No interpretability claim is made.**

## Priors: I lost the ones I registered, and that is the point

- ✅ Predicted π alone would not fix it — correct.
- ✅ Predicted population alone would not fix it — correct.
- ✅ Predicted migration into meaning-bearing structure — correct, and KILL E is
  the measurement of it.
- ✅ Predicted M would rise under π and that a rise means nothing — M is
  98–99.8 % everywhere including arms with the largest codes.

## What this licenses next — ⛔ NEEDS A CALL

1. **Seeds before any between-arm claim.** 5 seeds per cell; the current table
   supports "8–13 points everywhere", nothing finer.
2. **The counter still cannot be published.** B2 holds; a live cipher pathway is
   demonstrated and `auditor_state` ≠ `MEASURED`.
3. **The naive gap is now the primary detector**, and the frozen arm is its
   baseline. The scramble probe is demoted to locating *where*.
4. **Mitigation has to attack the incentive, not the channel.** Three relocation
   results say channel-level intervention cannot work. The remaining candidates
   are penalising mutual information between free channels and referent identity
   directly, or the deferred clarification bound — an honest listener cannot ask
   for help less often than the world is ambiguous.

## Do not quote

- `runs/phase5_v1..v5.log` — see `DEVIATIONS_5_2026_08_22.md`. v1 crashed (OOM);
  v2–v3 probed π-constant channels; v4 had the `co` shadowing bug; v3–v5 measured
  every gap against a judge that was **byte-identical** to the arm's own listener.
- Any `aspect_root` figure referenced to the **random** baseline.
- The KILL A / KILL E columns printed by the tool (random baseline).
