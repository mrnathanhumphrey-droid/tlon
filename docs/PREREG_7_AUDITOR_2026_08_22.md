# PRE-REG — 7: is it a conceptual pact, or an idiolect?

- **Date:** 2026-08-22
- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `a260481e` (sha256[:8] of draft body at lock, 2026-08-23T02:45Z)
- **Arc:** Tlön phase 7. Follows `VERDICT_6_TAXONOMY_2026_08_22.md` (gate passed)
  and `VERDICT_5_DENOTATION_2026_08_22.md` (PREREG `c09d0fb3`, KILL E fired).
- **Lexicon:** `e2b8527010231a81fd31b6eeb9de3d8c` · **Referents:** 60, REVIEWED.

## The question, and why only the auditor can answer it

Phases 4–5 measured that private information exists and relocates. They never
measured **what kind** of information it is. Two readings fit every number so far:

- **Conceptual pact** — the listener resolves using information the gloss does
  not contain. Arbitrary, uninterpretable, the thing flag ⑦ warned about.
- **Idiolect** — the listener is merely deterministic, but everything it uses is
  genuinely present in the description. A style, not a code.

The frozen gloss auditor is the **only judge that never entered the loop**, so it
is the only instrument that can separate them. Every verdict since phase 3 has
deferred this with "no interpretability claim is made."

## Why it is only now well-posed

**KILL B MUST RUN UNDER π.** In phases 3–4 the gloss rendered decoration —
`gloss.py` emits `×3` for aspect repetitions and `-ly` for degree — which is
exactly where the pact lived. The auditor was being handed glosses with the
answer smuggled into them. Under π that decoration is gone and the pact has moved
into **selection**, which is precisely what a gloss reflects, since selection
changes which happenings get mentioned. **Running KILL B without π re-pollutes
the input and voids the measurement.**

## ⛔ The outcome I am most likely to misreport

**Setting the floor against the complete-scene baseline (43.8 %) and reading
honest underdetermination as a pact.**

An honest partial gloss genuinely underdetermines its referent. A perfect frozen
outsider *cannot* always resolve it and will score lower than on complete scenes
— for entirely honest reasons. Using 43.8 % as the reference would fire a false
KILL B and it would look like the project's headline result. **This is the
zero-is-the-default mistake in a new costume — the fifth instance if it happens.**

**The 7.1 floor is the guard. If the floor is not measured on honest partial
glosses under π, the entire phase is void.**

## Method

### The two judges must perform the SAME task

⛔ **A raw comparison of "listener 60-way accuracy" against "auditor 4-way
accuracy" is not a gap, it is a task-difficulty artefact.** So both judges answer
an identical forced choice on identical items: **target + 3 root-disjoint
distractors**. The auditor scores candidate names by log-prob given the gloss;
the listener's logits are **restricted to the same four referents** and argmaxed.
Same item, same choice set, two different inputs — gloss versus surface.

The gap then means one thing: **how much better does the co-trained listener do
from the surface than an outsider does from the description?**

### 7.1 — THE FLOOR (gates everything)

Honest random-selection generator: no co-adaptation, uniform selection, **no pact
possible by construction**. Under π, frozen Qwen2.5-1.5B, log-prob forced choice,
root-disjoint distractors.

    floor_gap(w) = listener_4way(honest, w) − auditor_4way(honest, w)

⭐ **The floor is a CURVE, not a point.** It moves with the withholding rate *w*,
because withholding more makes the gloss less determining. Phase-5 arms sit at
12–18 % ambiguity while an honest p=0.5 generator sits near 24 %. Comparing an
arm against a floor measured at *higher* ambiguity biases toward **not** firing —
safe, but it can manufacture a false "idiolect". So the floor is measured at
**w ∈ {0.25, 0.5, 0.75}** and each arm is compared against the floor **matched to
its own ambiguity**.

**Required control:** shuffled glosses — gloss paired with another item's
candidate set. The auditor must fall to ~25 %. A live auditor is proven, not
assumed.

### 7.2 — THE CEILING (known positive)

The planted-cipher arm: a deliberate code the gloss cannot contain, hence a
guaranteed pact. Code planted in `aspect_root` (survives π; a code in a stripped
channel would be erased and prove nothing). Same auditor, same π, same
distractors.

    ceiling_gap = listener_4way(planted) − auditor_4way(planted)

⛔ **If the planted cipher does not open a gap clearly above the floor, the
auditor cannot detect pacts at all and KILL B is UNREADABLE. Stop and surface
it** — the instrument has failed, not the hypothesis. A null would then mean
"blind", not "clean". This is the trap the phase-4 positive control was built to
dodge, and it applies here unchanged.

### 7.3 — Place X, then fire

**X is not set in advance. It is placed between two measured anchors, and only
after both exist.** Nearer the floor than the ceiling, so KILL B is sensitive
rather than conservative. **Nate places it once 7.1 and 7.2 report.** Published
with both anchors so a hostile referee can see it was not tuned to the answer.

**KILL B fires** on a phase-4/5 arm when

    (listener_4way − auditor_4way) − floor_gap(matched w)  >  X

**with M-gate pass rate simultaneously high.** The **gap**, never either number
alone — B2 discipline. High listener + matching auditor = **idiolect**. High
listener + collapsed auditor = **pact**.

## Falsifier / KILL conditions

- **KILL B — PACT CONFIRMED.** Gap exceeds matched floor by more than X with M
  high.
- **KILL B′ — INSTRUMENT FAILURE.** The planted ceiling does not clear the floor.
  Everything else in this phase is void.
- **KILL B″ — AUDITOR DEAD.** Shuffled control is not at chance, or the honest
  auditor rate is at chance. The auditor is not reading the gloss at all.
- **IDIOLECT** (not a kill, a result): gap stays within X of the matched floor.
  The λ=0 pact headline weakens sharply and the counter-publishing blocker
  partially lifts.

## Priors to lose

- **I expect a pact**, i.e. KILL B fires. Phase 5 showed the gap survives every
  channel intervention, which reads more like information the gloss lacks than
  like determinism. If it comes back idiolect, my reading of phases 4–5 was wrong
  and the headline must be rewritten, not softened.
- I expect the floor to be **well below** 43.8 %, and the difference between
  those two numbers to be the largest single quantity in this phase.
- I expect the auditor to be weak in absolute terms. **A weak auditor is
  acceptable; it must be better than chance and immovable, not accurate.**

## Schema requirement (B2, enforced — not documentation)

The audit record couples, inseparably:

    {m_gate_rate, listener_rate, auditor_rate, gap, floor, ceiling, X,
     auditor_state}

No consumer may render a KILL B result — or any counter conditioned on it —
unless every field is present and `auditor_state = MEASURED`. **An unaccompanied
gap number must be unrepresentable, not merely discouraged.** `auditor_state`
moves to `MEASURED` for the first time in the project's history, and only then
does any counter depending on it become publishable.

## Standing floor (reportable regardless)

- **Pact confirmed:** first measured interpretability result; the λ=0 conceptual-
  pact headline is real; phase 8 proceeds.
- **Idiolect:** the headline weakens, the product path widens, and we learned it
  from the one judge that could not be co-opted. A good failure.
- **KILL B′:** the auditor is not up to the job — which is itself the finding
  that the anti-pact device we designed does not work, and it needs saying.

## Cost / lane

Local, $0. Qwen2.5-1.5B forced choice over short glosses; listener training is
minutes. Ledger row regardless.

## ⛔ BLOCKED — needs Nate's call

- **Lock this prereg.**
- **X**, after 7.1 and 7.2 report. Not before.
