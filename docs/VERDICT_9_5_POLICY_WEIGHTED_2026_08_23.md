# VERDICT — 9.5: OUTCOME 3. Inconclusive from banked data, twice over.

**Scope-check on `VERDICT_9_REFERENTS_2026_08_23.md` (Outcome A).** No prereg —
this locks no body, but it is decision-bearing, so it is recorded with the same
misreport discipline. **Date:** 2026-08-23 · **Spend:** $0.00 · **Run:**
`runs/phase9_5.json` · **Tool:** `tools/run_9_5.py`

⛔ **Outcome A is untouched.** It was locked on the uniform statistic and failed
on its own terms. This asked only whether the *conclusion* drawn from it
generalises. **It could not be answered from banked data**, so the conclusion's
scope is unresolved and stays stated as scoped.

---

## The precondition failed. The data is ABSENT, not sparse.

| checked | value |
|---|---|
| policy checkpoints anywhere on disk (`*.pt`/`*.pth`/`*.ckpt`) | **0** |
| phase-8 rollout keys carrying a subset selection | **0** of 9 |
| phase-5 result keys carrying a subset selection | **0** |
| **effective sample size per referent** | **0** |

Phase 8 banked `entropy · entropy_pre · entropy_rise_pct · entropy_spike ·
gap_final · m · naive · seed · steps`. Aggregates only. **No run in the project
has ever recorded which subset the policy chose**, and no policy weights were
saved, so `P_policy(subset | referent)` cannot be estimated at any resolution.

⛔ **This is not outcome 3-by-sparsity, where a wider estimate might still
inform.** There is no sample at all. Computing a re-weighting anyway would be a
vacuous number of exactly the D1 class — a dead measurement reading perfect — so
none was computed.

## ⛔⛔ And a second blocker that banking selections would NOT have fixed

| | |
|---|---|
| referents the phase-8 policy was trained on | archive, **60** |
| referents Outcome A was measured on | v2, **46** |
| ids in common | **0** |

`ChannelPolicy` is a **per-referent lookup table** — logits indexed by referent,
plus a selection head with per-referent Bernoullis. **A policy trained on the
archive has no parameters for a v2 referent.** So `P_policy(subset | v2
referent)` does not exist in Phase 8 data *even in principle*.

⭐ **Only a policy trained on v2 could answer this, and that is training.** Per
the standing instruction, that is a separate decision and it goes back to Nate
rather than being taken here.

---

## ⭐ What IS banked, and it bears on the question — on the archive

Phase 4 already ran the comparison this check was asking for, on the old set.
⭐⭐ **The `random` arm IS uniform enumeration**: `selection_rate` 0.500 and
`decidedness` 0.500 is Bernoulli(0.5) per slot, which is exactly uniform over
subsets — and it was measured with the same estimator as the learned arms.

| arm | sel_rate | decidedness | frac_ambiguous |
|---|---|---|---|
| **random (= UNIFORM)** | 0.500 | 0.500 | **25.1 %** |
| learned λ=0 | 0.613 | 0.831 | **13.3 %** |
| learned λ=1 | 0.486 | 0.801 | **16.3 %** |
| learned λ=2 | 0.466 | 0.804 | **14.7 %** |
| codeless ctrl λ=2 | 0.378 | 0.807 | **19.1 %** |

> **Policy-weighting drove ambiguity DOWN in every arm, by 6–12 points.**

That is **Outcome 1's direction — Outcome A robust** — and it matches the naive
prior the spec flagged as the one to pre-empt: a policy trained to succeed at
reference preferentially selects informative, low-ambiguity subsets. **The
surprising result did not happen, so no mechanism is owed.**

⛔⛔ **THREE REASONS THIS DOES NOT DECIDE v2, and it may not be quoted as a
policy-weighted f₂:**
1. **Wrong set.** Archive, not v2 — and the two are unpairable.
2. **One seed per arm.** Phase 4 predates the 5-seed floor. Direction only.
3. **Different estimator granularity.** `frac_ambiguous` is per *sampled scene*;
   `f₂` is per *distinct utterance*. Same notion, different denominator.

⭐ **Guard adjudication, and it is a genuine category call:** a re-weighting
comparison **cannot be item-paired against the thing it re-weights** — the two
weightings draw different scenes *by construction*, which is what a weighting
is. So `side_by_side`, not `paired_delta`. Verified in the run: `.delta` raises.

---

## ⭐ Rule zero, mechanised — the eighth instance got a fix, not a reminder

Every set-size, share and count this tool prints goes through `banner(label,
value, expected)`, which **raises `BannerMismatch` if the printed value is not
the expected one.** The number is now checked by the code, not by me remembering
to read it. Nine banners are asserted, including the two that would have caught
D1 (`referents ... (v2) = 46`, `ids in common = 0`).

This was cheap here because the quantities are small integers known in advance.
⛔ It does **not** generalise for free to a measured statistic, where there is no
expectation to assert — for those the discipline is still human.

---

## Where this leaves the fork

**Outcome 3: the fork is decided without this input.** Separately:

> **Needs a call — does a policy-weighted measurement earn a dedicated run?**
> It requires training a policy on v2 (5 seeds, local, ~Phase 8 shape). It would
> also be the natural moment to **bank per-referent subset selections**, which no
> run has ever done and whose absence is what stalled this check.

⭐ **Cheap and worth doing regardless of that call: make the selection log a
standing output.** It costs nothing at write time, and its absence has now cost
one whole check.

## Do not quote

- **Any policy-weighted f₂.** None was computed, for v2 or the archive.
- **"Outcome A is robust"** as a finding — the archive evidence points that way
  and is direction-only on the wrong set with one seed.
- **"Outcome A is an enumeration artifact."** Nothing here supports that either.
- Phase 4's `frac_ambiguous` figures as `f₂` — different denominator.
