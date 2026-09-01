<!-- settled-claim-ok: this document reports intervals and measured levels for
     every claim it makes; the two "-limited" mentions are quoted retractions. -->
# PRE-FLIGHT: stability spend + Parfenova replication — recommend NOT spending yet

$0. No box started. Gate 1 of the brief was "is there a $0 version?" — there
was, and it undermines three of the design's premises. One gate is **blocked**
on something I cannot supply.

## ⛔⛔ 1. THE `1.65/N` LAW IS FALSE — AND THE ERROR WAS MINE, TWICE OVER

The adapter target came from "LOO se swing ≈ 1.65/N ⇒ N=17 for ±10%". That was
extrapolated from **one observation at N=7** plus an assumed 1/N law. Simulated
across N (12 pairs→3N pairs, n=7):

| N | 7 | 12 | 20 | 30 | 60 |
|---|---|---|---|---|---|
| simulated swing | 56% | 46% | 41% | 41% | **42%** |
| `1.65/N` predicts | 24% | 14% | 8% | 6% | 3% |

**It plateaus at ~41%.** No achievable N reaches ±10%, so the pre-declared
tolerance was unreachable at any price.

⭐ **But the plateau is my METRIC, not the design.** "Swing" was a ratio —
range ÷ mean — and the drift mean is **+0.0803**, near zero. A ratio to a
near-zero denominator explodes regardless of N. Both the original 1.65/N law and
its refutation were artifacts of dividing by something close to zero.

## ⭐⭐ 2. MEASURED PROPERLY, THE VERDICT IS ALREADY STABLE

The scale-free quantity is the **absolute sd of the leave-one-out estimates**,
which does fall with N (simulated: 0.0531 at N=7 → 0.0161 at N=20 → 0.0051 at
N=60). On the real data:

```
LOO means: +0.1909 +0.1370 +0.0545 −0.0056 +0.0914 +0.0260 +0.0754
sd 0.0666    range 0.1965    full-sample mean +0.0803
pre-declared Δ* = 0.5939   ⇒ LOO sd = 11.2% of Δ*, range = 33.1% of Δ*
```

**Dropping a speaker moves the estimate by ~0.067 against a threshold of
0.594.** The estimate never approaches Δ\*, so the verdict — *no effect at or
above Δ\** — does not flip. What flips is the **quoted MDE** (0.472–0.725), via
the se, not the conclusion.

⇒ **There is no established methodological need for more adapters.** Adapters
would buy sensitivity to effects *below* Δ\*, and lowering Δ\* after a null
result is retrofitting the threshold to the outcome. If Δ\* should be lower,
that case has to be made on grounds independent of this run.

## ⛔⛔ 3. ROUGE IS SATURATED ON THIS SUBSTRATE — "SUPPRESSED" IS THE WRONG WORD

The brief asks the content channel be shown suppressed *to a measured level*.
Measured on the 84 existing real-pair transcripts:

| | ROUGE-1 | ROUGE-2 |
|---|---|---|
| LIVE | 0.6610 | 0.0923 |
| YOKED | 0.6654 | 0.0940 |
| LIVE − YOKED | −0.0044 (CI [−0.0147, +0.0057]) | −0.0017 (CI [−0.0066, +0.0034]) |

Near zero — but the discriminating test says why:

```
ROUGE-1, partners in the SAME conversation : 0.6610
ROUGE-1, speakers from UNRELATED transcripts: 0.6669
difference interaction could explain        : −0.0059
total distinct tokens across 84 transcripts : 244
```

**Unrelated speakers already share ~67% of unigrams.** The channel is not
suppressed by nounlessness — it is **saturated by a 244-token closed
vocabulary**, and those are different facts with opposite implications. A
saturated metric cannot show convergence *and cannot show its absence*.

⇒ **A "faithful replication on their lexical metrics" would run a metric that
cannot move on this substrate.** That is a design fault independent of every
other question here, and it is itself a reportable finding: *Tlön's closed
vocabulary saturates lexical-overlap measures, so group-size convergence cannot
be assessed on ROUGE here.* Embedding-convergence may escape saturation, but it
needs an encoder — **not on disk, not $0** — and would have to be shown
unsaturated by the same unrelated-pair test before use.

## ⛔⛔ 4. BLOCKED: I CANNOT VERIFY THE PARFENOVA PAPER

The brief specifies "their Algorithm 1" and "their Table 4: 2-agent barely
converges, 3/5-agent collapse". **I cannot verify any of that** — the paper is
not in this repo, and I will not reconstruct another group's algorithm or
results from recall in order to call the reconstruction faithful.

⛔ This is the exact failure the brief itself names: *"A replication that fails
because we built it differently is not a replication."* Designing the
shared-memory arm from my recollection would guarantee that failure while
looking like diligence. Per the standing rule that recency-sensitive facts come
from project data and never from training, **gate 3 cannot be cleared without
the paper**.

**What I need:** the PDF or the text of Algorithm 1 and Table 4 in the repo.
Then the shared-memory arm can be built against the source and the reproduction
verified before any contrast is claimed.

## WHAT SURVIVES, AND WHAT IT WOULD COST

Goal 2's group-size axis (2/3/5 agents) needs ≥5 adapters and we have 7, so **no
adapter purchase is required for the group-size design at all.** The adapter
spend was justified only by Goal 1, whose premise §2 removes.

| | status |
|---|---|
| Goal 1 — adapters for LOO stability | **not justified**; verdict already stable at Δ\* |
| Goal 2 — group-size axis 2/3/5 | **already possible** on the existing 7 adapters |
| Goal 2 — lexical metrics | **blocked**: saturated (0.667 unrelated baseline) |
| Goal 2 — faithful shared-memory arm | **blocked**: paper not available |
| confound demo: shared-pull | already spy-proven, citable |
| confound demo: architecture | per-adapter attractor result, citable |
| confound demo: content channel | **measured, and it says saturated, not suppressed** |

## RECOMMENDATION

**Do not spend.** Two things unblock most of this and cost nothing:

1. **Put the Parfenova paper in the repo.** Until then the replication cannot be
   designed, only guessed at.
2. **Decide whether an unsaturated convergence metric exists for Tlön.** The
   force:ka channel is ours and works; the lexical channel is saturated. If the
   replication must be on their metrics, it needs a metric shown unsaturated by
   the unrelated-pair test *first* — that is the same "prove the instrument
   before trusting it" arm the brief asks for, and it currently fails.

If both clear, the run is **inference-only on the existing 7 adapters** and far
cheaper than the adapter design it was framed around.
