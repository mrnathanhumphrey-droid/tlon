# RESULTS — asymmetric solo pass: the panel re-certified in-regime

**Prereg:** `PREREG_ASYMMETRIC_RECERT_2026_08_30.md`, sha `a7bc2a7f…`, pinned on
the box before generation. **Run:** A100-SXM4-40GB, 2026-08-30 13:03 → 17:15 UTC,
all stages passed. 7 builds × 14 solo asymmetric transcripts (own chain
accumulates, no partner), 40 turns, `--no-injections`. Instance terminated;
fleet confirmed empty by polling to an empty list.

⭐ **The first right-regime transcripts in the project's history.** Every prior
transcript was window-1 (no self-memory) or symmetric full-accumulation (the
partner's past retained, which the ontology forbids).

---

## 1 · ⛔⛔ THE PANEL WAS 2/3 WRONG, AND ONLY THE IN-REGIME RUN COULD SHOW IT

| observable | window-1 | in-regime | jack rank (in-regime) | |
|---|---|---|---|---|
| **tokens/surface** | 0.30 (rank 2–5 ⛔) | **0.24** | **1–3** | ⭐ ADMIT |
| **nodes/scene** | 0.35 (rank 6–7 ⭐) | **0.31** | **2–3** | ⭐ ADMIT |
| root TTR | **0.13 (rank 1–1 ⭐)** | 0.32 | **1–4** | ⛔ rank |
| modifier density | 0.35 | 0.33 | 1–4 | ⛔ rank |
| root repertoire | 0.29 | 0.58 | 5–6 | ⛔ CI |
| force:ku | 0.26 | 0.72 | 5–6 | ⛔ CI |
| force:ko | 0.96 | 1.17 | 7–8 | ⛔ CI |
| **force:ka** | **0.27 (rank 2–4 ⭐)** | **1.59** | 7–9 | ⛔ CI |
| force:ki | 0.53 | 1.61 | 8–10 | ⛔ CI |
| force:kä | 0.82 | 1.85 | 8–10 | ⛔ CI |

**VERDICT: ⚠️ NARROW PANEL — `tokens/surface` + `nodes/scene`.** The distance
rests on a two-axis basis and that is recorded, per the pre-declared reading.

⛔⛔ **`root TTR` was rank 1 in all seven window-1 leave-one-out recomputations —
and it does not survive the regime change.** Its contamination goes 0.13 → 0.32
and its jackknife rank range 1–1 → 1–4. The most convincingly stable observable
in the window-1 screen is not admissible in the regime the experiment will
actually run in.

⭐ **`force:ka` crossed, exactly as pre-declared** — 0.27 → **1.59**, more than
three times the threshold, jackknife up to 1.78 and CI up to 2.07. §3 of the
prereg named this in advance as a **valid outcome, not a failure**.

⭐ **`tokens/surface` was REJECTED at window-1 (rank range 2–5) and is admitted
in-regime (1–3).** The re-certification did not merely prune the old panel — it
promoted an observable the old regime had disqualified. **Only `nodes/scene`
survives both regimes.**

⇒ Had Stage 2 been built on the window-1 panel, the distance metric would have
rested on two axes that are not build-stable where it counts, and one of them
(`force:ka`) is now the single worst-behaved force in the set.

## 2 · POOL GATE, RE-RUN IN-REGIME ON THE RE-CERTIFIED PANEL — PASS

```
axis              pool    build mean   build sd      z
tokens/surface  7.1083      7.0173      0.1012     0.90
nodes/scene     2.7500      2.7423      0.0350     0.22
8 of 21 pairs project outside the segment (halt at >50%)
```

The native pool (140 surfaces, 20 per build) is central on both surviving axes.
The `force:ka` z = 1.30 watch is moot: `force:ka` is no longer an axis.

## 3 · THE ATTRACTOR REPRODUCES WITHOUT A PARTNER

| build | ka | sd | range | >0.60 | symmetric regime |
|---|---|---|---|---|---|
| s20620 | 0.263 | 0.059 | 0.200–0.400 | 0/14 | — |
| s20621 | 0.462 | **0.271** | 0.150–0.925 | 4/14 | — |
| s20622 | 0.350 | 0.081 | 0.200–0.525 | 0/14 | — |
| s20623 | 0.905 | 0.094 | 0.700–0.975 | 14/14 | — |
| t30001 | 0.234 | 0.058 | 0.100–0.325 | 0/14 | 0.119 |
| t30002 | 0.650 | 0.128 | 0.400–0.825 | 9/14 | 0.806 |
| t30003 | 0.302 | 0.078 | 0.200–0.425 | 0/14 | 0.278 |

```
between-build sd 0.2454 · mean within-build sd 0.1098 · ratio 2.24
```

⭐ **Build identity dominates conversation noise, and the ordering is preserved.**
For the three builds with symmetric-regime values, the rank order is identical
(t30001 < t30003 < t30002 in both), with magnitudes compressed. **The attractors
survive removing the partner entirely** — they are not an artefact of the
forbidden symmetric regime.

⭐ **s20621 is the interesting build:** sd 0.271 against ~0.06–0.13 for its
siblings, with 4 of 14 conversations in the high band and 10 in the low. Its mean
of 0.462 describes no conversation it produced. **Conversational stability is
itself a per-build property** — same recipe, different seed.

⛔⛔ **THE PRE-DECLARED READING, BINDING: THIS MEANS "SELF-ACCUMULATION-
INTRINSIC". IT DOES NOT MEAN THE METAPHYSICS PREDICTED IT.** Any autoregressive
model accumulating its own context tends toward self-reinforcing grooves, and
that alternative predicts this observation exactly. Separating *Tlön-specific*
from *generic-transformer* requires a **control language** — same recipe,
non-Tlön corpus — which does not exist and is **DEFERRED**.

⚠️ **A retraction, recorded.** At n=56 (4 builds) the pooled histogram had **zero**
conversations between 0.55 and 0.70 and I described a clean bimodal gap. At n=98
that band holds **6** conversations. The distribution is heavy-tailed toward a
high mode, not cleanly bimodal. Interim reporting of an unstable statistic
produced one reversal earlier in this run (between/within 0.73 at n=3 → 2.26 at
n=4) and this is a second.

## 4 · WHAT DID NOT MOVE

Zero degenerate transcripts in 98. Validity 40.0 of 40 turns on average. Per-build
marginal wall time 2,090–2,186 s (mean 2,146), setup 70 s one-time and **not**
divisible into the per-build rate.

## 5 · CARRIED TO STAGE 2

- **The panel is `tokens/surface` + `nodes/scene`, two axes, narrow basis.**
- ⚠️ **Certified SOLO, applied LIVE** (prereg §2). Contamination is a per-build
  property so solo is the right arm, but the drift run measures interaction. An
  observable build-stable solo and ill-behaved under interaction would pass this
  gate and still hurt the distance.
- ⛔ **s20621's within-build spread is a live threat to the 21-pair design.** A
  distance measured from one conversation per speaker inherits conversation-level
  noise that, for that build, is comparable to the between-build signal.

## 6 · WHAT THIS DOES NOT DO

No LIVE arm, no YOKED arm, no pairs, no distance, **no drift number.** σ_cp
remains unmeasured.
