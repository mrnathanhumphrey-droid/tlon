"""Assemble the Wilson review packet for PREREG 9.

⛔ WHY THIS IS GENERATED. The Wilson brief is the only document written to leave
the room, and STATE has carried "keep it in sync with the verdicts" as a manual
chore since 2026-08-22. A manual sync chore on the one document an outside
reader sees is how an outside reader gets a stale number. So the packet embeds
the prereg BODY VERBATIM and prints its hash: the thing Wilson reviews is
byte-identical to the thing that gets locked, and if the prereg moves, the
packet moves with it.

⛔ NOT AN ARTIFACT LINK. Anything leaving Nate is a local markdown file under
D:\\Resolve Research — the leak vector is sharing, not publishing.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from lock_prereg import body_hash                            # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREREG = ROOT / "docs" / "PREREG_9_REFERENTS_2026_08_23.md"
COV = ROOT / "runs" / "coverage_v2.json"
OUT = pathlib.Path(r"D:\Resolve Research") / "TLON_PREREG_9_REVIEW_2026_08_23.md"

DELTA = """\
# Tlön — PREREG 9 for review

**For:** Wilson · **From:** Nate · **Date:** 2026-08-23
**Prereg body hash:** `{hash}` — your comments are pinned to this exact text.
Any edit to the prereg changes the hash, so there is no ambiguity about which
version you read.

⭐ **THIS IS THE CONFIRMING PASS, NOT THE FIRST READ.** You reviewed draft 1
(`99d53fe8`) and returned **DO NOT LOCK YET** with three fixes. All three are
applied. This packet is the delta bring-up (unchanged, for self-containedness),
the **revised** prereg verbatim, and a short checklist of *did the fixes land as
you meant* — plus **two numbers I had to choose that you did not specify**, which
are the places this could still be wrong.

---

## What happened since the brief

### Phase 8 — scoped down. One real result, one retraction.

⭐ **The honest RSA α-frontier is identically 0.00 at every α including α→∞.**
Measured gaps on 5 seeds: +4.56 / +5.39 / +9.04 / +10.15 / +13.19. **Hole 1's
RSA horn is closed** — our gap cannot be honest pragmatic specialisation.

The mechanism is general, not a fact about our data: an RSA speaker concentrates
on utterances where `L₀(r|u)` is *higher* — fewer competitors — and those are
exactly the utterances a naive listener also resolves well. Informativeness helps
both listeners. A gap would need the speaker to prefer *less* informative
options, which honest RSA never does.

⭐ Our `L₀` is **exact** — LL(1) parse, lossless denotation, `consistent()` —
where every prior RSA application approximates it with a neural net. The
frontier is *computed*, and the comparison carries no model-slop term.

⛔ **The other horn is still open.** The frontier assumes Bayes-optimal
listeners; ours are neural, so listener suboptimality and train/test mismatch
survive (the frozen arm bounds it separately at ≤3.73 pts).

⛔⛔ **Conservation is RETRACTED to unproven.** Within-arm seed spread
(4.56–13.19) equals the across-arm spread (8.00–13.33) that suggested it. Phase
5's apparent invariance across four interventions is **seed noise**. The 5-seed
floor killed our best claim on its first application.

⛔ **8.2's dynamic reset test was NOT RUN** — I wrote the five-branch classifier
and never called it. No trajectory exists. And 8.3a's entropy measurement is
confounded (before/after windows *within one run*, so the convergence trend
swamps the transient).

⭐⭐ **The convergent finding nobody planned:** three independent measurements
said the referent set was the binding constraint — Phase 7's omission ceiling
(strongest constructible pact 0.8 pts against a 7.9 pt detector ceiling), 8.1's
frontier being identically 0 *because* mean consistency-set size was 1.26, and
8.3b having no power below ~3 pts. Each arrived from a different direction and
none was looking for it.

### 9.0 — the unpaired comparison is now a tool, not a lesson

That error had happened **five times** and been written into two verdicts as a
lesson, then committed again after both. So it moved into the harness.
Measurements are no longer floats: a `Measurement` carries its `ItemSet`
(digest over the *actual* item keys, never a caller-typed label), `__sub__`
**refuses**, and the only route to a difference is
`paired_delta(a, b, contrast=…)` — the caller must name the one thing allowed to
differ. Unpairable comparisons go to `side_by_side(reason=…)`, whose `.delta`
raises.

The red-proof runs the battery **twice** — 8 unpaired cases must raise against
the real guard *and compute a number against a decorative one* — which is what
proves the battery is sensitive to the guard rather than to its own
construction. Then the guard was broken on purpose and the exit code watched: it
exits 1 and names all eight.

⭐ It has already changed a design decision before any run — see the standing
constraint about 9.2c in the prereg.

### 9.1 — the referent set is Calvino, *The Distance of the Moon*

Coherence is the technical requirement, not the flavour. Underdetermination is a
property of the *set*: 26 of the old 60 had a head root unique to them, and the
head is never dropped by impression-selection, so those referents could never be
made ambiguous. That scatter is the mechanism behind 1.26.

**{n_declared} referents from one story, {n_live} live.** A structural rule was
applied — *the matrix predication is the world's persisting event; the
distinguishing happening is a dependent* — which is both truer to Tlön (the
matrix verb is what is happening, everything else is how) and the thing that
kills unique heads. Unique head roots **26/60 = 43 % → {n_uniq}/{n_declared} =
{pct_uniq:.0f} %**.

Measured: all {n_declared} sayable · **{reach}/{subs} selection subsets
buildable** · `forbid` 0/{n_declared} · `matrix` 0/{n_declared} · nesting on 11.

⛔⛔ **The theme embodies the retracted thesis.** Calvino's engine is
conservation-to-absurdity — the relation surviving its objects — which is
*exactly* the claim Phase 8 retracted. The set will thematically whisper
conservation. That raises the discipline bar rather than lowering it, and it is
named as a misreport risk in the prereg.

---

## The prereg, verbatim

"""

QUESTIONS = """

---

# Confirming pass — did the three fixes land as you meant?

**1. 9.2c — the estimator.** Per-seed Spearman ρ_s across the 46 live referents
(`mean|consistent|_r` is seed-invariant, so only `gap_{r,s}` moves), giving 5
independent estimates; the across-seed spread is the uncertainty. Within-seed
permutation demoted to a line explicitly labelled *"within-listener
association"* and forbidden from being the inferential test. UNDERPOWERED is a
named fourth branch and cannot be reported as branch 2.

⛔ **Four specifics you did not specify and I chose:** Fisher z-transform each
ρ_s before averaging, back-transform at the end · **95 % t-interval on 5 values,
df = 4** · all five raw ρ_s always reported, never the aggregate alone · and the
threshold below.

**2. ⛔ NUMBER I CHOSE #1 — the 0.4 in the branch definitions.** Branch 2 (real
and set-independent) requires the interval to *exclude* |ρ| = 0.4; an interval
containing both 0 and 0.4 is branch 4, UNDERPOWERED. I justified 0.4 as *the
smallest rank association that would change what we do next*, so it is
decision-relevant rather than derived from v2. **But it is my number and it
decides whether a null is a null.** If you would put it elsewhere, now is when.

**3. 9.2b — the RSA bar.** Now *"measured gap > sup over all α of frontier(α),
report α\\* and the margin at α\\*"*, with the reasoning written in: a positive
frontier is a curve, RSA gaps are non-monotonic in α, so the endpoint need not
be the maximum and clearing it while sitting below an interior peak would leave
Hole 1 open while the verdict said closed. Phase 8's α→∞ wording is explicitly
retired as an artefact of the zero-frontier case.

**4. C2 — screen plus contingent arm.** Split runs first because it is free and
is labelled confounded (the 11 are not a random 11 — they are the ones the matrix
rule touched). Promotion to a paired arm (`contrast="free_aspect"`) is triggered
before any reduction is attributed to the referent set.

⛔ **NUMBER I CHOSE #2 — the trigger, at v2 mean gap < 5.29 pts**, i.e. more
than one old-set seed-sd (3.17) below the old-set mean (8.46), both from
`runs/reset_dynamics.json`. You said "materially below" and did not give a
figure. I also wrote in that **this trigger is read off two side-by-side numbers
and is NOT a delta** — the sets are unpairable and the guard refuses the
subtraction — so it is a decision rule about spending a cell and is never
reported as an effect size. **Is one seed-sd the right line, and is using the
old set's own spread to set it acceptable given it is a historical baseline
rather than the artefact under audit?**

**5. f₂ keeps the gate, H(r|u) added as companion.** Mean posterior entropy in
bits, computed from the exact L₀, reported next to f₂ with a note that the two
are reported together so a reader can see whether they agree. No entropy
threshold.

**6. #5 — the reframe, in your words, as the argument.** Misreport risk 1 now
carries phase separation of evidence as the *defence* and demotes the hold-back
to hygiene, with this as the write-up wording: *the referent set was chosen for
collision structure, verified by f₂; the conservation claim it thematically
resembles is retracted and is not tested here; the test that could restore it —
the dynamic reset — is theme-independent and pending.* Is that the argument you
meant, and does it belong in the prereg (where it is now) as well as the paper?

---

# For the record — the original five and your answers

Kept so the packet stays self-contained for a later reader.

**1. Is `f₂ ≥ 25 %` the right operationalisation of "enough
underdetermination", or is there a standard measure I should be using?**
I chose the *fraction of distinct utterances with |consistent| ≥ 2* over the
mean because a mean of 1.26 with a long tail is a different world from a flat
1.26 — and the mean is what hid it last time. But 25 % is my number, argued from
"below this the frontier is dominated by unambiguous cases", not from any
literature. If emergent-communication or formal-pragmatics work has a
conventional referential-ambiguity statistic, I would rather use theirs.

**2. Is the referent the right unit for 9.2c, and is a permutation null over
referents legitimate here?**
This is the one I am least sure of. `gap_r` values are **not independent across
referents** — one listener produces all of them, so they share a training run.
Permuting referents within a seed may be the right null, or the cluster may need
to be the seed with only 5 of them, which would leave the test badly
underpowered. It is a correlation of 46 non-independent points and I do not want
to discover that after locking.

**3. When the frontier is positive, is "exceed it at α→∞" still the right bar?**
Phase 8 closed the RSA horn against a frontier that was identically zero, so the
bar was trivial to state. If v2's frontier is non-zero the comparison becomes a
margin, and I have pre-registered that the margin must be reported at α→∞ rather
than at a convenient α. Is that sufficient, or does a positive frontier need a
different treatment — a per-α comparison, or a distributional one?

**4. Is confound C2 handled well enough by a split, or does it need an arm?**
v2 fixes the head aspect on 11 referents, which *removes their free
`aspect_root` channel* — the exact channel phases 4 and 5 found the pact living
in. So a smaller gap on v2 could be reduced free capacity rather than anything
about the referent set. I plan to report the gap split by whether the referent
has a free `aspect_root`. A split is observational; an arm would be causal but
costs a full 5-seed cell.

**5. Is holding back two referents enough mitigation for the theme, or is the
Cosmicomics choice a problem for the paper?**
M38 (*the distance persisting after the bodies*) and M50 (*two things holding a
distance between them*) state the retracted conservation claim as an image, so
they are declared and withheld from every live measurement, pinned by a test.
The named misreport risk covers the rest. But a referee could reasonably say the
whole set is a thematic argument for a claim we retracted. **Is that a real
problem, or am I over-correcting?** I would rather hear it now than in review.

---

## Standing constraints, so nothing gets proposed that we cannot do

- **Backbone model and phase progression are Nate's call, every time.**
- **5 seeds per cell** is the hard floor on any between-arm claim.
- **A locked prereg body is never rewritten** — corrections go to a DEVIATIONS
  file, which is how D1–D11 exist.
- Local compute only so far: RTX 5070 Ti, **$0.00 spent to date.**
- ⛔ The counter cannot be published while `auditor_state ≠ MEASURED` (B2),
  enforced in SQL, and Phase 7 left it at `FAILED_TO_RUN`.
"""


def main() -> int:
    text = PREREG.read_text(encoding="utf-8")
    cov = json.loads(COV.read_text(encoding="utf-8"))
    n_uniq = len(cov["unique_head_root"])
    head = DELTA.format(
        hash=body_hash(text),
        n_declared=cov["n_declared"], n_live=cov["n_live"],
        n_uniq=n_uniq, pct_uniq=100 * n_uniq / cov["n_declared"],
        reach=cov["subsets_reachable"], subs=cov["subsets_total"])
    quoted = "\n".join("> " + ln if ln.strip() else ">"
                       for ln in text.splitlines())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(head + quoted + QUESTIONS, encoding="utf-8", newline="")
    print(f"wrote {OUT}")
    print(f"  prereg body hash embedded: {body_hash(text)}")
    print(f"  {len(head.splitlines())} lines delta + "
          f"{len(text.splitlines())} lines prereg (verbatim) + "
          f"{len(QUESTIONS.splitlines())} lines questions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
