# PRE-REG — 9.2 / 9.3: what the Cosmicomics set bought

- **Date:** 2026-08-23
- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `10757ac4` (sha256[:8] of draft body at lock, 2026-08-23T15:15Z)
- **Arc:** Tlön phase 9. Follows `VERDICT_8_FRONTIER_2026_08_23.md` (scoped
  down; conservation retracted) and `GUARD_9_0_COMPARISON_2026_08_23.md`.
- **Lexicon:** `e2b8527010231a81fd31b6eeb9de3d8c` — **unchanged**, 156 roots.
- **Referents:** v2, `referents_v2.yaml`, **50 declared / 46 live**, matrix rule
  applied. ⛔ Must be `REVIEWED` before anything below runs.
- **9.1 measured facts this prereg is built on** (`runs/coverage_v2.json`):
  all 50 sayable · **211/222 subsets buildable** · `forbid` 0/50 · `matrix` 0/50
  · nesting 11 · unique head root **11/50**.

## Review pin and revision history

**Draft 1** hashed `99d53fe8`. **Wilson reviewed it and returned DO NOT LOCK
YET, three fixes.** All three were the same kind of error — *matching the
inference to the actual unit of independence*, which is the lesson Phase 8
already taught at the cost of the conservation claim. This is **draft 2**:

| | change | why |
|---|---|---|
| **9.2c** | primary inference is now **per-seed estimates aggregated across seeds**; within-seed permutation **demoted to descriptive** | as drafted it was an **anticonservative** test — see 9.2c |
| **9.2b** | RSA bar is now **`sup` over all α**, not α→∞ | a positive frontier is a curve and **α→∞ need not be its maximum** |
| **C2** | split is a **screen**, with **contingent promotion** to a paired arm | the split is confounded; the arm only matters in one branch |
| 9.2a | **H(r\|u)** in bits added as a reported companion to `f₂` | literature-legible; no threshold change |

`tools/lock_prereg.py` hashes the body (everything but the Status and LOCK
lines), so **any edit changes the hash** and a reviewer's comments stay pinned to
a version rather than to "the prereg". ⭐ **The hash mechanism did its job here:
three substantive changes force a re-review rather than sliding in under an
existing sign-off.** Stamp with `--lock` only after Wilson's confirming pass and
Nate's go. ⛔ **A locked body is never rewritten afterwards** — corrections go to
`DEVIATIONS_9`.

## Standing constraints for the whole phase

⛔⛔ **5 SEEDS PER CELL IS THE HARD FLOOR ON ANY BETWEEN-ARM CLAIM.** A one-seed
result is *"direction only, not interpretable"* and may never be compared to
another cell. It killed the conservation claim on first application in Phase 8;
it is not relaxed here.

⛔⛔ **EVERY COMPARISON GOES THROUGH THE 9.0 GUARD** (`tlon/harness/paired.py`).
Measurements are `Measurement`, not float. Differences come only from
`paired_delta(a, b, contrast=…)`. **Old-set vs new-set is unpairable by
construction — different referents — and goes to `side_by_side(reason=…)`,
reported next to each other, never subtracted.**

⭐⭐ **THE GUARD ALREADY CHANGED THIS DESIGN, BEFORE ANY RUN.** The obvious way
to test "does the gap scale with underdetermination" is to compare a
high-ambiguity stratum against a low-ambiguity one — and those are **different
items**, so it is the unpaired comparison in a fifth costume and the guard
refuses it. **9.2c is therefore specified as a CORRELATION ACROSS REFERENTS, not
a difference between strata.** That is a better design and it was forced, not
chosen.

---

# 9.2 — What the choice bought

## The bet, stated so it can fail

Cosmicomics' collision structure delivers the underdetermination the instrument
needs. ⛔ **A valid mechanism does not entitle anyone to the sign** — deeper
signatures also give the listener *more* to read, which pushes resolution the
other way. Every outcome below is a named branch; none is the fallthrough.

## 9.2a — Consistency-set size, and the saturation guard

Phase 8.1's frontier was identically zero because mean L₀ consistency-set size
was **1.26** — a near-deterministic utterance space with no room for a pact.

⛔ **REPORTING THE MEAN ALONE IS PRE-REGISTERED AS A MISREPORT.** A mean of 1.26
with a long tail is a different world from a flat 1.26. Report **mean, median,
p90, max, and the full histogram**, plus the primary statistic:

> **f₂ = the fraction of distinct utterances with |consistent| ≥ 2.**

⭐ **Reported alongside it, as a companion and NOT as a second gate: mean
`H(r|u)` in bits**, the literal listener's posterior entropy over referents given
an utterance. It is computable from our exact `L₀` for free, and it is the
quantity a pragmatics referee will expect to see — `f₂` is ours and defensible
but it is not anyone's convention. **The two are reported together so a reader
can see whether they agree.** The gate stays `f₂`, because "what fraction of
utterances are even ambiguous at all" is interpretable and its 25 % line rests
on a mechanistic argument, where an entropy gate would need a threshold nobody
has intuition for.

### Three named outcomes, thresholds fixed now

| | condition | reading |
|---|---|---|
| **A — still scattered** | **f₂ < 25 %** | v2 rebuilt the shallow set with prettier names. Detectors stay degenerate. **The phase has failed its own bet and says so.** |
| **B — usable middle** | **f₂ ≥ 25 % and median ≤ 8** | The set delivered. Phase 8's open questions become answerable. |
| **C — over-collided** | **median > 8** (>17 % of the live set) | The opposite failure: pre-object vocabulary so uniform that nothing discriminates. |

**Why 25 %:** below that the frontier computation is dominated by unambiguous
utterances and will round to ~0 again for the same reason it did on the old set.
**Why median > 8:** a median utterance consistent with more than a sixth of the
live set means selection is no longer choosing between candidates.

⛔ **Outcome C is not automatically fatal and must not be reported as if it
were.** A Bayes listener beats the uniform floor — that is D1, where the
"89.3 % ceiling" turned out to be `m_uniform_floor` and the honest arm hit
92.1 %. Under C, additionally report `m_uniform_floor` and the honest listener's
observed accuracy. **C is fatal only if the honest listener cannot beat its own
uniform floor**, which is the operational meaning of "no discrimination
possible".

## 9.2b — Per-detector dynamic range

Each computed **the same way it was computed before**, or the comparison is not
legible.

### Omission ceiling — Phase 7's paired FULL vs HEAD-ONLY

Old set: detector ceiling **7.9 pts**, strongest constructible omission-pact
**0.8 pts**. Paired on identical items (the unpaired version of this curve is
what produced retracted D10).

> **KILL: if v2's strongest constructible omission-pact is < 3.0 pts, the
> omission detector still has no usable range and KILL B stays unmeasurable.**

**Why 3.0:** Phase 8.3b established there is no power to detect an effect below
~3 pts at the 5-seed floor. It is the smallest effect this instrument can
resolve, so it is the honest bar — **not** a number derived from v2.

⛔ **I expect this one to be tight and I am saying so before running.** The
matrix rule raised collision, but **nesting does not add a dependent, it moves
one deeper**, and Phase 7's complaint was specifically about dependent count.
v2 has 43 referents at 2 dependents and 6 at 3. If the omission ceiling does not
move, that is the predicted failure, not a surprise.

### RSA frontier — recomputed with the exact L₀ on v2

⛔⛔ **THE OUTCOME MOST LIKELY TO BE MISREPORTED, NAMED HERE.**

1. **Still identically 0 at every α including α→∞** ⇒ Hole 1's RSA horn stays
   closed for free — *and* it is evidence for outcome **A**, because a
   degenerate frontier means a near-deterministic space.
2. **Non-zero at some α** ⇒ ⛔ **HOLE 1 REOPENS.** **This is a COST of a deeper
   set.** Reporting a non-zero frontier as "the set has range" while quietly
   keeping Phase 8's closure is the misreport this clause exists to forbid.

### ⛔⛔ The bar on a positive frontier is the SUPREMUM, not the endpoint

> **Closure requires: measured gap > sup over all α of frontier(α).
> Report α\* where that supremum occurs, and the margin AT α\*.**

**Why the α→∞ rule cannot be carried over.** When the frontier was *identically
zero*, α→∞ was the whole story — zero at every α means any positive gap clears
it everywhere at once, so a single endpoint check was sufficient by accident of
the value, not by argument. **A positive frontier is a curve, and RSA gaps are
generally non-monotonic in α**: they rise, then can fall as the speaker
saturates toward deterministic informativeness. So the largest honest gap may
sit at some **finite α**, and a measured gap could clear the endpoint while
sitting *below the interior peak* — an honest speaker at that intermediate
rationality could have produced it, and Hole 1 would **not** be closed while the
verdict said it was.

Cheap, since the whole frontier is computed anyway. ⛔ **Phase 8's "exceed at
α→∞" wording is an artefact of the zero-frontier case and is retired here.**

## 9.2c — Does the gap scale with underdetermination?

**Correlation across referents, not a difference between strata** (see the
standing constraint). But the *correlation's* unit and the *inference's* unit are
not the same thing, and conflating them is what draft 1 got wrong.

### ⛔⛔ Why draft 1's permutation null was anticonservative

Draft 1 said "Spearman ρ across 46 referents with a permutation null". **The 46
`gap_r` values are not independent** — within a seed, one listener produces all
of them, so they share that training run's idiosyncrasies through shared weights.
Permuting referents within a seed therefore tests *"is this ρ above chance among
one listener's outputs"*, which is a **weaker and different claim** than "does
the gap scale with underdetermination". Permutation of correlated points
**understates the null's spread**, so it goes significant far too easily. That is
the standard cluster confound and it manufactures false positives.

⛔ **And the obvious fix — cluster = seed — is worse, not better.** Five clusters
is uninterpretable; no cluster-robust method is trustworthy at n=5. It trades a
false-positive risk for a test with no power at all. **Neither drafted option is
correct**, so the estimator changes instead of the null.

⭐⭐ **This is D10's cousin: there, the wrong thing was the items; here, the wrong
thing is what counts as independent.** In this project **the seed is the unit of
independence** — established in Phase 8, at the cost of the conservation claim.

### The estimator, and it models the dependence instead of permuting around it

`mean|consistent|_r` is **seed-invariant** — computed from the exact `L₀`, no
training — so only `gap_{r,s}` varies across seeds.

1. **Within each seed `s` separately**, Spearman ρ_s across the 46 live
   referents: `gap_{r,s}` against `mean|consistent|_r`.
   → **5 independent per-seed estimates.**
2. Fisher z-transform each ρ_s, take the mean z̄ and a **95 % t-interval on 5
   values (df = 4)**, back-transform to ρ.
3. ⛔ **Report all five raw ρ_s, always.** The aggregate alone would repeat the
   error that let a mean of 1.26 hide a distribution.

**The across-seed spread of those five estimates IS the legitimate uncertainty,
because seeds are the actual independent replications.** The estimand is *"the
per-seed within-listener rank association, aggregated across 5 independent
seeds."*

⭐ **The within-seed permutation survives as a DESCRIPTIVE line only** —
labelled *"within-listener association"* — and **may never be the inferential
test.** Stated here so it cannot quietly be promoted in the verdict.

⭐ **Baseline is the FROZEN arm, never a random policy.** Phase 5: frozen arms
with no co-adaptation — so no code is *possible* — still showed `aspect_root`
+24.89/+11.95/+26.21/+18.82, because a policy that merely concentrates produces
a big drop. The reference is *an optimising policy that cannot negotiate.*

### Four named branches, and UNDERPOWERED is honourable

1. **Interval excludes 0, ρ̄ > 0** — the phenomenon **scales with
   underdetermination**. The interesting result: it was regime-*limited* on the
   shallow set, not merely unmeasurable there.
2. **Interval excludes |ρ| = 0.4 and includes 0** — the phenomenon is **real and
   set-independent**. A genuine null, because the test could have found an
   effect worth acting on and did not.
3. **Interval excludes 0, ρ̄ < 0** — the phenomenon was **partly a shallow-set
   artefact**.
4. ⭐ **UNDERPOWERED — interval includes BOTH 0 and |ρ| = 0.4.** No claim. **With
   5 seeds this is a likely outcome and it is the CORRECT answer when it
   happens, not a failure of the design.** It may not be reported as branch 2.

**Why 0.4:** it is the smallest rank association that would change what we do
next — below it, "the phenomenon scales" is not something to build on. A
decision-relevant threshold, not one derived from v2.

⛔ A null is evidence only if the test could have come back positive. Branch 2
requires the interval to *exclude* 0.4; an interval that contains both 0 and 0.4
is branch 4 and says nothing.

---

# ⛔ Named confounds specific to v2, all pre-registered

### C1 — 5.5× more denoting relator NOISE

Depth-2 patterns cannot carry `via` (`NodePattern.parse` raises *"via implies
at_depth 1"*), so their edge relator is drawn **uniformly at random** by the
builder. Unconstrained relator slots: **2/90 on the old set → 11/103 on v2.**
`edges` denotes, so **π keeps it.**

⭐ **CORRECTION TO WHAT I FIRST TOLD NATE:** I described this as "a place a code
could sit that π cannot strip." **That is wrong as stated.** `FREE =
("aspect_root", "aspect_reps", "degree", "coda", "orient")` — the policy has
**no relator handle**, no logprob and no gradient there, so it cannot currently
carry a code. It is **denoting noise**, not a channel. It would become a channel
the moment anyone adds a relator head to the policy.

**Why it still matters:** it is noise the listener must see through, and v2 has
5.5× more of it, so **a lower listener accuracy on v2 is partly this and not
underdetermination.**

> **Control C1:** re-run with deep-edge relators pinned to a constant. Paired on
> identical (referent, subset) items, `contrast="deep_relator"` (random vs
> fixed), through the guard.

### C2 — v2 removes free capacity from the historically code-bearing channel

`aspect_root_any` is used by **11** referents (old set: 2), and fixing a head's
aspect **removes that referent's free `aspect_root` channel** — the channel
phases 4 and 5 found the code living in. So v2 has *less* free capacity exactly
where a pact has previously formed. **A smaller gap on v2 could be this, not the
referent set.**

⛔ **The split is a SCREEN, not the answer.** Reporting the gap by whether the
referent has a free `aspect_root` is observational and **confounded**: on a set
built by a structural rule the 11 are not a random 11 — they are the referents
whose head aspect the matrix rule fixed, which correlates with their depth and
their collision structure and probably much else. The split will show *a*
difference and will not attribute it.

> **Contingent escalation, pre-registered:** the split runs first because it is
> free. **If v2's gap comes in materially below the old set's, C2 is promoted to
> a paired arm** — same referents, free `aspect_root` toggled on/off,
> `contrast="free_aspect"`, through the guard — **before any part of that
> reduction is attributed to the referent set.**
>
> **Trigger, fixed now:** v2 mean gap **< 5.29 pts**, i.e. more than one old-set
> seed-sd (3.17) below the old-set mean (8.46), both from
> `runs/reset_dynamics.json`.
>
> ⛔ **The trigger is read off two side-by-side numbers. It is NOT a delta** —
> the sets are unpairable and the guard refuses the subtraction. It is a
> decision rule for whether to spend a cell, and it is never reported as an
> effect size.

**Why not spend the arm now:** C2 only becomes load-bearing in the branch where
the v2 gap is *smaller*. If the gap holds or grows, removed free capacity did not
suppress it and C2 explains nothing that needs defending. Observational screen
first because it is free; the causal arm only in the branch where its answer
changes a conclusion — the same shape as parking KILL B until the set can
express an omission-pact.

### C3 — different set size, different chance level

46 live vs 60. Chance is 1/46 vs 1/60 and the label-space difficulty differs.
⛔ **This is why old-vs-new is `side_by_side` and never a delta.**

### C4 — 11 unreachable selection subsets (5.0 %)

Structural: a depth-2 pattern needs a depth-1 sibling. It shrinks the space
impression-selection can search — the very quantity Phase 7 found too small —
so it is reported alongside the omission ceiling, not buried.

---

# 9.3 — Isolation, re-confirmed rather than assumed

Phase 6: structural drift **0.0000 %**, semantic drift **0.0000 %** over 7,240
utterances per arm, both red-proofed, mask rejects 40 (0.5 %, so the guard is
live and not vacuous). Honest scope: *"impossible for signature families without
`forbid`/`matrix`, and detectable when present."*

**v2 uses neither (0/50, measured).** So the claim **carries over logically.**

⛔ **It is re-run anyway.** The logical carry-over is about the *scope
condition*; the *demonstration* was on the old set, and v2's reachable action
space is different — nesting ×11, `aspect_root_any` ×11, 46 referents. Re-running
6.2 is enumeration, no training, and converts an inherited claim into a measured
one. Cheap enough that not doing it would be a choice to keep the weaker version.

- **Expected:** 0.0000 % / 0.0000 % on v2.
- **Any non-zero** ⇒ the isolation scope **narrows**, and that is recorded
  **before** any exhibit or paper leans on it.
- ⭐ **Re-report the mask-reject rate on v2.** A guard that rejects nothing is
  vacuous, and a 0.0000 % drift reading next to a 0 % reject rate is not
  evidence — it is a dead measurement reading perfect.

---

# ⛔⛔ Misreport risks, named

1. **THE ONE THE SPEC REQUIRED:** *"reporting v2 consistency-set size or gap as
   evidence for conservation, or letting the Cosmicomics theme's
   conservation-whisper stand in for the unexecuted dynamic reset test."*
   **Calvino's engine is conservation-to-absurdity — the relation surviving its
   objects — which is exactly the claim Phase 8 RETRACTED.** The referent set now
   thematically whispers it. **The content embodying the thesis is not evidence
   for the thesis.**

   ⭐⭐ **THE DEFENCE IS PHASE SEPARATION OF EVIDENCE, NOT WITHHOLDING** (Wilson,
   2026-08-23). Holding back M38 and M50 is **hygiene, not a defence** — those
   two literally state the claim as an image and do not belong in a live
   measurement, but withholding *two* referents concedes that the set's content
   is entangled with the claim while treating only the most flagrant cases, which
   reads as knowing-and-under-treating. The real answer is stronger and it is
   simply true:

   > **The referent set cannot argue for conservation, because Phase 9 does not
   > measure conservation at all.** The only thing that could earn it back is the
   > dynamic reset test, which Phase 9 explicitly does not run. The whisper and
   > the evidence are in **different phases**, and the phase open to the
   > theme-loading charge is precisely the phase that measures **none** of what
   > the theme is about.

   **Wording for the write-up, and this replaces "we held back two referents" as
   the answer to a referee:** *the referent set was chosen for collision
   structure, verified by `f₂`; the conservation claim it thematically resembles
   is retracted and is not tested here; the test that could restore it — the
   dynamic reset — is theme-independent and pending.*

   ⛔ The hold-back stays as hygiene and stays pinned by a test. It is just not
   the argument.
2. **Reporting a non-zero RSA frontier as "the set has range"** when it
   **reopens Hole 1**. See 9.2b.
3. **Quoting the mean consistency-set size alone.** See 9.2a.
4. **Subtracting anything across the old and new sets.** The guard raises; a
   number that appears anyway came from outside it and is not a result.
5. **Reading outcome C as fatal without checking the honest listener against its
   own uniform floor.** D1, again.

# Standing floor — reportable whichever way this goes

- **Solid:** outcome B, detectors have range, isolation holds ⇒ the referent set
  stops being the binding constraint, and Phase 8's open questions (8.2 executed
  and five-branch-classified, 8.1's neural horn, 8.3 with a paired control)
  become answerable on a set that can measure them.
- **Scoped down:** outcome A or C, or the omission KILL fires, or isolation
  narrows. ⛔ **This is a good outcome, not a failure** — the decision arrives
  here, cheaply, instead of three phases downstream. Tlön remains **the first
  exactly-invertible testbed isolating pragmatic drift by construction**, which
  is the novel-instrument claim and **stands regardless of what 9.2 does.**
- Either branch, the record gains **the first referent set built to a stated
  structural rule** and a **guarded** measurement of what that rule bought.

# ⛔ What Phase 9 still does not do

**No dynamic reset test. No conservation re-attempt.** They wait for a
confirmed-deep set so they run **once**, executed and five-branch-classified,
through the guard. ⭐ **The Cosmicomics theme makes conservation more tempting
and therefore that test more necessary — executed rather than whispered.**

# Cost / lane

Local, $0. 9.2a and the RSA frontier are closed-form, no training. 9.2c needs
5 seeds × training runs on the RTX 5070 Ti, same shape as Phase 8. The omission
ceiling uses the frozen Qwen2.5-1.5B auditor. 9.3 is enumeration.

# ⛔ BLOCKED — needs Nate's call

- **Lock this prereg.**
- **Set `review_status: REVIEWED` on `referents_v2.yaml`.** Nothing runs until
  both are done.
