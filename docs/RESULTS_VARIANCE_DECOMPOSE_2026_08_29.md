# RESULTS — variance decomposition, observable screen, coupling

**Prereg:** `PREREG_VARIANCE_DECOMPOSE_2026_08_28.md`, sha `9bd4a629…`, locked before
any adapter was trained and verified on the box.
**Run:** A100-SXM4-40GB, 2026-08-28 12:28 → 2026-08-29 04:58 UTC. All stages passed.
Three adapters trained on a corpus held **byte-identical** to B-fresh's
(`263fe3c8…`, sha-gated — the run aborts if it does not match).

⭐ **The two most important things in this document were not what it was
designed to measure.** They are in §4, and they invalidate the regime §3 was run
in. The pre-registered results are reported first and unchanged.

---

## 1 · DECOMPOSITION — R = 0.42, BOTH CONTRIBUTE

| adapter | corpus | trainer seed | k | mean `ki` | sd | degenerate |
|---|---|---|---|---|---|---|
| s20620 (B-fresh) | `263fe3c8…` | 20620 | 38 | 0.2520 | 0.0702 | 0 |
| t30001 | **same** | 30001 | 14 | 0.1865 | 0.0931 | 0 |
| t30002 | **same** | 30002 | 14 | 0.2252 | 0.0707 | 0 |
| t30003 | **same** | 30003 | 14 | 0.2397 | 0.1033 | 0 |

```
S_training  (corpus FIXED)   0.0655     between-adapter sd 0.0284
S_combined  (corpus varied)  0.1549     between-adapter sd 0.0700
R = 0.42                     → pre-declared band: BOTH CONTRIBUTE
```

Pre-declared reading, taken as written: **report the split, claim neither
source.** R is a ratio of two noisy k=4 quantities and is a direction, not a
coefficient.

⭐ **The actionable part:** holding the corpus byte-identical cut the
between-adapter sd from **0.0700 to 0.0284 — a 59 % reduction — for the price of
one flag.** Against the pricing in `RESULTS_RECIPE_VARIANCE_2026_08_28.md`, that
moves detecting a 0.10 effect from ~9 adapters/arm toward ~4. Corpus pinning is
now mandatory in any arm-to-arm contrast.

⛔ **But the training draw is real and irreducible without changing the trainer.**
Three models trained on identical bytes still separate by 0.0655. No corpus
discipline touches that. Loss was blind to it as usual: 0.21041 / 0.20528 /
0.20604. F-LOCAL likewise: render 0.953 / 0.938 / 0.953, speak 1.000 throughout.

**56 window-1 exchanges, 0 degenerate.** Nothing here rests on a compromised arm.

## 2 · SCREEN A — the ranking HELD, the magnitude did not

Pre-declared: *root TTR stays in the top 3 and `force:ki` stays outside it.*

```
 1. root TTR         0.13        7. modifier density  0.33
 2. force:ka         0.22        8. root repertoire   0.38
 3. force:ku         0.22        9. force:kä          0.67
 4. tokens/surface   0.23       10. force:ko          1.10
 5. nodes/scene      0.28       11. distinct-surface   inf
 6. force:ki         0.28
```

⭐ **HELD — observables may now be selected on contamination.** top3 =
`[root TTR, force:ka, force:ku]`, `force:ki` at rank 6.

⚠️ **And a caveat that must travel with it.** Re-computed over 7 builds instead
of 4, the values moved substantially:

| | k=4 | k=7 |
|---|---|---|
| root TTR | 0.07 | 0.13 |
| force:ki | 0.65 | **0.28** |
| **gap** | **9.8×** | **2.2×** |

The prediction passed by its letter, but the 10× gap that made the original
screen compelling is a 2.2× gap. **The k=4 contamination estimates were
themselves unstable** — the same lesson this whole arc keeps teaching, now
applied to the instrument that was supposed to escape it. Root TTR is still the
best available choice; it is not the landslide the exploratory screen suggested.

## 3 · SCREEN B — UNDERPOWERED, and in a regime that should not have been run

24 accumulating exchanges, 0 degenerate by the pre-declared criterion. Paired
live-minus-frozen, per observable, largest first:

```
nodes/scene      +0.0296   t +1.64        force:kä   -0.0208   t -1.27
force:ku         +0.0208   t +0.90        tokens/surface -0.0325 t -0.42
force:ki         +0.0146   t +0.66        force:ka   -0.0022   t -0.08
```

Nothing reaches |t| > 2. Pre-declared verdict: **UNDERPOWERED — positive coupling
excess but no paired significance at this n. This is NOT "no coupling."**

⛔⛔ **It is also not evidence about coupling at all**, for the reason in §4.1.

## 4 · WHAT THE RUN DISCOVERED THAT IT WAS NOT LOOKING FOR

### 4.1 ⛔⛔ A and B are the same adapter. There has never been a two-speaker exchange.

```python
back = LocalBackend(a.model, adapter=a.adapter, temperature=...)
A = LLMSpeaker("A", back, card=False)
B = LLMSpeaker("B", back, card=False)
```

One backend, one adapter, two labels. Every "interacting" exchange in Act 2 —
including all 24 here — is **one impression talking to itself.** The code comment
reads *"A and B, each adapting to the other."* There is no other.

⇒ Convergence between two speakers is **unmeasurable by construction** in this
harness: identical things cannot converge, they are already one point. The
coupling column was always going to read zero, whatever the observable and
whatever the regime. `--adapter` must become two adapters before any drift number
can exist.

### 4.2 ⛔⛔ Full accumulation is object-persistence, which the ontology forbids

The discourse spec says it twice — *"the exact object-persistence the ontology
forbids"* — and the grammar says *"There is no persisting moon. There are only
successive momentary impressions."* Holding the partner's past turns in context
is the heresiarch's position on the nine coins, implemented: a thing that endures
unperceived and can be pointed at again. That is a noun, and Tlön is nounless
**because** nothing persists that way.

⇒ Both regimes run to date are wrong. `window-1` denies a speaker its own memory
(and the spec already flags depth-1 as artifact-producing — the arena temperature
sweep was void for exactly this). Full accumulation retains the partner. **The
correct regime — self accumulates, partner present-only — has never been run**,
and `exchange()` cannot express it: `hist` is a single shared list with no
speaker attribution.

### 4.3 ⭐ Individuality is LATENT at depth 1 and expresses only at depth

`ka` share, mean and per-conversation range:

| adapter | window-1 | accumulating |
|---|---|---|
| t30001 | 0.423 [0.300–0.575] | **0.119** [0.000–0.200] |
| t30002 | 0.395 [0.300–0.475] | **0.806** [0.700–0.875] |
| t30003 | 0.386 [0.300–0.450] | **0.278** [0.175–0.375] |
| **between-build spread** | **0.037** | **0.687** |

At window-1 the three builds are indistinguishable. Under accumulation they
separate by **18×** more. Each settles into its own attractor reproducibly across
8 independent conversations — t30002 never below 0.700, t30001 never above 0.200.
Structure, not scatter. (t30001 and t30003 touch at the extreme edge, 0.175 vs
0.200; their means are separated at t ≈ 4.4.)

⇒ **Window-1 cannot see individual differences at all.** It was never going to
show drift regardless of observable. The regime where individuals appear is the
one that reifies the partner. Only the asymmetric regime satisfies both.

⇒ And the yoked control **mirrors the interacting arm in all three** (0.084 /
0.841 / 0.281 against 0.119 / 0.806 / 0.278). The attractor is a speaker
reinforcing its own accumulated output — **self-reinforcement, not mutual
adaptation.** Consistent with the ontology's prediction, and also with generic
long-context LLM behaviour; this data cannot separate those two stories. The
test that would: run the asymmetric regime on these same adapters and compare
rut severity.

### 4.4 ⛔ The degeneracy gate is blind to the collapse that matters

All 24 accumulating exchanges scored distinct-surface 1.00, 40/40 turns,
`degenerates: false`. A transcript that is **80.6 % one force** is collapsed in
the dimension under study while passing a gate that only watches surface
repetition. The gate was not amended mid-run and t30002's exchanges are included
as pre-declared; it is recorded here as a measured limitation of the instrument.

## 5 · ARTEFACTS

66 exchange logs, `decompose.json`, the full pipeline log, and three adapters
(`adapter_t30001/2/3`, md5-verified against the box before termination) are
local. Instance `13364f3e…` terminated 2026-08-29 05:0x UTC; fleet confirmed
empty by polling to an empty list, not by the terminate call's return.

⭐ **The three adapters are the asset.** Same corpus, three seeds — three
measurably distinct individuals of one language, already paid for. The
asymmetric-history experiment is inference-only on them.

## 6 · WHAT THIS DOES NOT DO

No treatment arm, no map comparison, no stipulation. **No drift number. σ_cp
remains unmeasured** — and §4.1 explains why it was never obtainable here.
