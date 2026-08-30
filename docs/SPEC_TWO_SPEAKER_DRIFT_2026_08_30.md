# SPEC — the first two-speaker experiment

**Status: SPEC, not yet a prereg.** It becomes `PREREG_TWO_SPEAKER_DRIFT_*.md`
with a sha once Stages 1–2 have run and their outputs have filled in the
bracketed parameters. Nothing is generated before that hash exists.

---

## 0 · STANDING — why this needs an unusually clean pre-registration

⛔⛔ **This is the first two-speaker experiment in the project.** Everything prior
was one adapter wearing two labels (`RESULTS_VARIANCE_DECOMPOSE_2026_08_29.md`
§4.1): one `LocalBackend`, `A` and `B` pointing at it, so the coupling column was
mechanically zero — not by regime, not by observable, but because there was one
speaker. **There is therefore no prior run to compare against and no result to
reproduce.** Nothing here can be sanity-checked against history, which is exactly
why the readings must be fixed in advance.

Second standing fault it must not inherit: **full accumulation retains the
partner's past turns, which is object-persistence and the ontology forbids it**
(discourse spec, twice; grammar §8, *"There is no persisting moon"*). Window-1 is
also wrong — it denies a speaker its own memory. The regime below is the only one
that satisfies both, and `exchange()` cannot currently express it.

## 1 · INVENTORY — corrected, and larger than assumed

⭐ **The asset is 7 builds, not 3.** Prior messages said "three adapters"; that
was wrong — it counted only this run's. Weights verified present on disk:

| group | builds | corpus | pairs |
|---|---|---|---|
| fixed-corpus | s20620, t30001, t30002, t30003 | all `263fe3c8…` | 6 |
| varied-corpus | s20621, s20622, s20623 | own draw per seed | — |
| **same-code, same-map (derived) total** | **7** | | **21** |
| excluded | `adapter_mt` (pre-08-27 code), `adapter_treat` (STIPULATED map) | | |

136 window-1 exchanges exist across 8 builds; 25 accumulating transcripts exist,
24 of them from the forbidden symmetric regime.

⭐ **The two groups are a designed contrast, free.** Fixed-corpus pairs differ
only in trainer seed; cross-group pairs differ in corpus too. That gives a
built-in test of whether drift depends on **how far apart the speakers start** —
which is the question "baseline distance" was reaching for.

## 2 · STAGE 1 — recompute the ranking, and measure whether it has stopped moving

⛔⛔ **The instrument built to escape build-variance had build-variance.** At k=4
the contamination ranking gave root TTR 0.07 and `force:ki` 0.65 — a 9.8× gap. At
k=7: 0.13 and 0.28, a 2.2× gap. The prediction passed by its letter and the
magnitude that made it compelling did not survive. **Recomputing at k=7 and
trusting it repeats the k=4 mistake with a bigger number.**

⇒ Stage 1 is not "recompute." It is **recompute WITH a stability estimate**:

1. Contamination over all 7 same-code builds (`adapter_mt` reported separately,
   never pooled — different code).
2. **Leave-one-build-out jackknife**: recompute the full ranking 7 times, each
   omitting one build. Report, per observable, the range of its contamination
   and the range of its rank.
3. **Bootstrap over builds** (resample builds with replacement, B = 2000) for a
   CI on each contamination value and on each pairwise rank ordering.

### Pre-declared admission rule for the distance panel

An observable may enter the panel iff **its jackknife rank range is ≤ 2
positions AND its bootstrap contamination CI upper bound is < 0.5.** Rank alone
is not enough — that is the criterion that just failed.

- **≥ 3 observables qualify** → the panel is those observables; proceed to §3.
- **1–2 qualify** → proceed with a reduced panel and record that the distance is
  built on a narrow basis.
- **0 qualify** → ⛔ **STOP. The ranking is not stable enough at k=7 to define a
  distance**, and the honest next move is more builds, not a metric built on
  sand. Do not proceed to §3 on the strength of a point estimate.

Cost: `$0`, no box, existing transcripts.

## 3 · STAGE 2 — define the distance

⛔ `S = 0.155` is the **range of one scalar across builds. It is not a distance**
and must never be quoted as one. Convergence is undefined until a metric exists.

- **Axes:** the Stage-1 panel, nothing else. No observable enters because it is
  interesting.
- **Scaling:** each axis standardised by its **between-build sd measured in
  Stage 1** — so one unit of distance is one build-to-build sd on that axis, and
  no axis dominates by having larger raw units.
- **Geometry:** Euclidean over the standardised panel. Stated here so it cannot
  be chosen after seeing the drift.
- **Estimand:** `D(A, B)` between two speakers' transcripts, computed over
  matched turn counts.

⚠️ Pre-declare the **cold distances for all 21 pairs before any exchange is
run**, from existing window-1 transcripts. That table is the baseline and is
frozen.

## 4 · STAGE 3 — the harness

Three changes to `act2_exchange_probe.py`, each red-proofed:

1. **Two adapters.** `--adapter-a` / `--adapter-b`, two `LocalBackend`s.
   ⛔ A test must assert the two speakers do **not** share a backend object —
   the current fault is invisible precisely because it looks correct.
2. **Speaker-attributed history.** `hist` becomes a list of `(speaker, surface)`.
   Each speaker is conditioned on **its own chain, accumulated, plus the
   partner's single most recent turn.** The partner's older turns are never
   stored and never reachable — provoke and release.
   ⭐ Red-proof with the existing spy speaker: assert that at turn 40 speaker A
   receives exactly its own 20 turns plus B's turn 39, and that B's turn 1 is
   **absent**. A knob that silently no-ops returns "the metaphysics holds" for
   the worst possible reason.
3. **Seeded injections**, at pseudo-random turns from a stated seed, to break the
   self-reinforcing groove that symmetric accumulation produced.
   - ⛔ **Content must be neutral with respect to the Stage-1 panel.** Injections
     drawn from the corpus drag every distribution toward the corpus baseline and
     would manufacture apparent convergence. Pre-declare the source and
     **verify neutrality on the panel axes before use** — an injection stream
     whose own panel values differ from both speakers' is a third speaker.
   - ⛔ **Yoked identically into every condition**: same seed, same turn indices,
     same content. An injection that lands in LIVE but not in the null *is* the
     difference being measured.

## 5 · STAGE 4 — conditions, and the null

| condition | A hears | B hears | isolates |
|---|---|---|---|
| **COLD** | own chain only | own chain only | starting distance |
| **LIVE** | own chain + B's latest | own chain + A's latest | mutual adaptation |
| **YOKED** | own chain + a **recording** of B's LIVE turns | own chain + recording of A's LIVE turns | the same input, minus mutuality |

⭐ **YOKED is the primary null, not "two adapters that never interact."** A
never-interact pair receives *different input* from the live pair, so a distance
change confounds mutuality with what each speaker was given. YOKED replays the
identical partner turns while removing the partner's ability to respond — input
held, mutuality removed. COLD is retained as the baseline, not as the null.

⚠️ **Known and unavoidable limitation of yoking:** once A's own outputs diverge
from its LIVE run, its accumulated self-chain differs, so "identical input" holds
for the partner stream only. Stated here rather than discovered later.

**Drift** = `D(A,B)` shrinking in LIVE relative to YOKED, paired by pair.

## 6 · STAGE 5 — pairs, and the unit of independence

⛔⛔ **21 pairs are not 21 independent observations.** Seven adapters, each
appearing in six pairs; the unit that the experiment re-rolls is the **adapter**,
not the pair. Significance must be computed with the adapter as the clustering
unit — a paired test over 21 correlated pairs would overstate power exactly the
way transitions-within-exchange did, and the way exchanges-within-training-run
did after that. *(Third time this unit has moved; it is now a standing check.)*

**Fingerprint test, carried from the last run:** each build held its own `ka`
attractor across 8 conversations (0.119 / 0.806 / 0.278, ranges largely
non-overlapping), but the frozen partner mirrored it — self-reinforcement, not
mutual adaptation. With 7 builds, ask whether a per-build attractor is a **law**
or a **small-sample coincidence**, and whether it survives the asymmetric regime
at all. If injections dissolve the attractor, that is itself the headline.

## 7 · WHAT THIS CAN AND CANNOT CONCLUDE

⛔ **No MDE can be computed.** The drift effect size is unknown — no prior run
measured it, because no prior run had two speakers. This is a **feasibility and
existence probe**, and it is labelled one.

Pre-declared readings:

- **LIVE distance shrinks vs YOKED, clustered by adapter, CI excluding 0** →
  ⭐ two Tlön speakers adapt to each other. The first drift number.
- **No difference, CI narrow enough to exclude `[minimum meaningful
  convergence]`** → a real negative about mutual adaptation at this scale.
- **No difference, CI wide** → ⛔ **UNDERPOWERED. Not "no drift."** Given n = 7
  clustered units this is the likely outcome and saying so now prevents a tidy
  false null later.
- ⛔ **A collapse gate that watches the FORCE axis, not only surface repetition.**
  Last run passed a transcript that was 80.6 % one force with distinct-surface
  1.00 and `degenerates: false`. Any transcript exceeding `[force-share
  ceiling]` is **reported and flagged**, never silently dropped.

## 8 · CARRIED DISCIPLINE

Prereg hashed and committed before generation; `compileall` under the box's
Python 3.10 first; corpus/adapter shas re-pinned on the box; **md5-verify every
adapter before the box dies**; pull the pipeline log **first**; analyse locally
only; pull-and-kill at DONE; raw dump on failure, never `tail` on
attribution-relevant output. **Corpus pinning is now the standing recipe for any
future adapter comparison** (between-adapter sd 0.0700 → 0.0284 for one flag) —
it does not help this run, which is inference-only on existing builds.

## 9 · ORDER, AND WHY IT IS THE ORDER

```
1  recompute + stabilise the ranking      $0   → gates 2; may STOP the arc
2  define the distance on stable axes     $0   → frozen cold table, 21 pairs
3  build + red-proof the harness          $0   → tests must fail before they pass
4  hash the prereg with 1–3's outputs      —
5  run LIVE + YOKED, three-way, on a box
```

Stages 1–3 are free and none of them needs a GPU. **The distance must not
inherit an unstable ranking**, which is why §2 can halt everything before a
single dollar is spent.
