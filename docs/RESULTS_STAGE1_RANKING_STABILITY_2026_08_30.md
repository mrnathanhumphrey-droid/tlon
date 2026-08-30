# RESULTS — Stage 1: is the contamination ranking stable?

**Spec:** `SPEC_TWO_SPEAKER_DRIFT_2026_08_30.md` §2, admission rule fixed before
this ran. `$0`, no box, re-analysis of 122 window-1 exchanges across 7 same-code
same-map builds. Tool: `tools/act2_ranking_stability.py`, bootstrap seed 20260830.

## VERDICT — ⭐ PANEL ADMITTED (3)

```
root TTR · force:ka · nodes/scene
```

The arc does not halt. These three, and only these, may become distance axes in
Stage 2.

## THE TABLE

Admission required **both**: jackknife rank range ≤ 2 **and** bootstrap 95 % CI
upper bound < 0.50.

| observable | k=7 | jack rank | jack contam | boot 95 % CI | |
|---|---|---|---|---|---|
| root TTR | 0.13 | **1–1** | 0.08–0.14 | 0.05–0.16 | ⭐ ADMIT |
| force:ku | 0.26 | 2–5 | 0.16–0.29 | 0.08–0.38 | ⛔ rank |
| force:ka | 0.27 | 2–4 | 0.22–0.30 | 0.12–0.34 | ⭐ ADMIT |
| root repertoire | 0.29 | 2–6 | 0.22–0.32 | 0.12–0.38 | ⛔ rank |
| tokens/surface | 0.30 | 2–5 | 0.21–0.33 | 0.14–0.39 | ⛔ rank |
| nodes/scene | 0.35 | 6–7 | 0.28–0.39 | 0.17–0.42 | ⭐ ADMIT |
| modifier density | 0.35 | 5–8 | 0.31–0.38 | 0.17–0.42 | ⛔ rank |
| force:ki | 0.53 | **3–9** | 0.22–0.60 | 0.12–0.74 | ⛔ rank |
| force:kä | 0.82 | 8–10 | 0.58–0.95 | 0.31–1.27 | ⛔ CI |
| force:ko | 0.96 | 9–10 | 0.79–1.09 | 0.40–1.27 | ⛔ CI |
| distinct-surface | inf | 11–11 | inf | — | ⛔ CI |

9 of 2000 bootstrap resamples had < 3 distinct builds and were discarded.

## WHAT THE GATE CAUGHT THAT A POINT ESTIMATE WOULD NOT

⭐ **Four observables fail on rank stability alone while looking perfectly
respectable on contamination.** `force:ku` (0.26), `root repertoire` (0.29) and
`tokens/surface` (0.30) all sit under 0.35 and would have been picked by a
top-N rule — and each moves 3–4 places when a single build is dropped. **The
"take the top 3" heuristic that Screen A licensed would have selected two axes
whose rank is an artefact of which builds happened to be on disk.**

⭐ **`root TTR` is genuinely solid**: rank 1 in every one of the 7 leave-one-out
recomputations, CI 0.05–0.16 entirely below the threshold. It earns its place
rather than inheriting it from the exploratory screen.

⛔ **`force:ki` is dead as an axis.** Jackknife rank 3–9 — it moves six places on
a single dropped build — and CI 0.12–0.74 straddling the threshold. The
observable the entire arc was built on cannot define a distance.

## ⛔ CORRECTION TO `RESULTS_VARIANCE_DECOMPOSE_2026_08_29.md` §2

That document said Screen A was "recomputed over 7 builds instead of 4." **It was
not.** `act2_variance_decompose.py` builds its `arms` from B-fresh plus the three
new adapters — 4 builds, *a different 4*; `s20621/22/23` were never included.

| build set | n | root TTR | force:ki | gap |
|---|---|---|---|---|
| exploratory screen (s20620–23) | 4 | 0.07 | 0.65 | 9.8× |
| Screen A (s20620 + t30001–3) | 4 | 0.13 | 0.28 | 2.2× |
| **all same-code** | **7** | 0.13 | **0.53** | 4.2× |

Verified by recomputing both sets; the Screen A set reproduces 0.13 / 0.28 /
2.2× exactly. **`force:ki` reads 0.65, 0.28 or 0.53 depending on which builds you
hold.** The direction of the original caveat stands and is strengthened; the
"7 builds" label was wrong and the 2.2× gap was a 4-build number.

## ⛔⛔ THE LIMIT THAT MUST TRAVEL TO STAGE 2

**Contamination has only ever been measured on window-1 transcripts, and the
drift run will not use window-1.** Between-build `ka` spread is 0.037 at window-1
and 0.687 under accumulation (18×, `RESULTS_VARIANCE_DECOMPOSE_2026_08_29.md`
§4.3). Contamination is a ratio of two regime-dependent quantities, so **this
panel is certified for a regime the experiment will not run in.**

⇒ Two consequences, both binding:

1. **The cold-distance table in Stage 2 must be computed in the same regime the
   drift is measured in** — asymmetric self-accumulation — not from the window-1
   transcripts that produced this ranking.
2. **The panel is provisional.** Once asymmetric transcripts exist, contamination
   is recomputed on them and the admission rule re-applied. An axis that fails
   there is dropped, whatever it did here.

This is the same error class as Screen B (a measurement taken in a regime the
question does not live in), caught before it was built on rather than after.

## WHAT THIS DOES NOT DO

Defines no distance, runs no exchange, produces no drift number. It says only
which axes are stable enough to build one from, in one regime, provisionally.
