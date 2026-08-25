# PRE-REG — 4: when saying less costs something, does the generator select or cipher?

- **Date:** 2026-08-20
- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `c1f7d06c` (sha256[:8] of draft body at lock, 2026-08-21T01:31Z)
- **Arc:** Tlön phase 4. Supersedes the scope of `PREREG_3_CIPHER_2026_08_20.md`
  (LOCK `3c49ad47`), whose verdict is `VERDICT_3_CIPHER_2026_08_20.md`.
- **Lexicon:** `e2b8527010231a81fd31b6eeb9de3d8c` · **Referents:** 60, REVIEWED,
  **unchanged by Nate's call of 2026-08-20 — no referent edits.**

## Why phase 3 has to be redone at all

Phase 3's KILL A did not fire, and the null is worthless. Not because the probe
was blind — it reported **+3.01 to +4.59 pts on `aspect_root`** throughout, so it
was demonstrably live — but because **M was never scarce.** The signature core
handed the listener the referent, M sat at 99.2–100 % from step one, and a code
is a solution to a communication problem the generator never had. The honest
scope of that null is *no cipher forms when there is no reason to build one.*

Phase 4 gives it a reason.

## What changes

The generator utters only a **subset** of `sig.contains[]`: the head predication
always, plus a learned choice over the dependents. This is not an impairment
bolted on to force a result — **it is the project's thesis.** Q3=1 / Q4=3.63e41
says novelty cannot come from paraphrase and must come from impression
*selection*, and selection means choosing what to leave out. Until now the
generator selected nothing; it dumped the full signature and decorated the edges.

M becoming scarce is a **consequence** of doing the thing we claimed to be doing,
not an imposition.

## The pre-check that licenses this (already run)

`tools/confusability.py` → `runs/confusability.json`. **Run before any policy
code, precisely because it could have killed the phase.**

- **M ceiling under selection: 89.3 %.** A perfect listener, uniform over the
  referents still consistent with what it heard, cannot do better. Phase 3 ran at
  99.2–100 %.
- **Mutual indistinguishable pairs: 0.** All 8 confusions are **asymmetric**
  containments — A's full scene fits inside B's larger signature. So the ~11
  points are **recoverable in principle**; had there been mutual pairs, part of
  the gap would have been a wall no code could climb and we would have been
  measuring the wall.
- Ambiguity is monotone in how much is withheld: mean consistent referents
  **1.13 → 1.32 → 1.47** at 0/1/2 dependents dropped.
- **26/60 referents have a head root unique to them.** See the stratification
  requirement below — this is the thing most likely to manufacture a false null.

## One-line hypothesis

When withholding information costs M, the generator recovers it by **selecting
more informative impressions** — not by agreeing with the listener on a code. M
rises toward the 89.3 % ceiling, R falls, and every channel carrying no referent
information stays inside the null band, **measured on the stratum where the
pressure actually exists.**

I pre-register the expectation that **this fails**, and that phase 4 is where the
cipher finally appears. Phase 3 could not produce one. This one can.

## Falsifier (pre-registered kill conditions)

- **KILL A — CIPHER FORMED.** Any no-information channel (`orient_order`,
  `coda`, `degree`, `aspect_reps`) shows a scramble-drop **> 1.0 pt** ON THE
  AMBIGUOUS STRATUM (defined below). Report the channel and the selection rate.
- **KILL A′ — PROBE ARTEFACT (negative control).** The same channels on the
  **unambiguous stratum** must stay **≤ 0.5 pt**. Those 26 referents never need a
  code. If they show a drop, the probe is reading something other than a cipher
  and KILL A's number is uninterpretable. **A′ is checked before A is believed.**
- **KILL B — INTERPRETABILITY COLLAPSE.** Deferred: threshold cannot be set until
  the auditor is re-baselined (see deviations).
- **KILL C — SELECTION INERT.** The policy's mean selection rate stays within
  5 % of its initialisation, i.e. it never learns to withhold anything. Then M is
  not actually scarce in practice and phase 4 has reproduced phase 3.
- **KILL D — M COLLAPSE.** Listener accuracy falls below **70 %**, i.e. well
  under the 89.3 % ceiling rather than under 100 %.

## ⛔ Thresholds are stated against 89.3 %, never 100 %

A listener at 89 % is **at ceiling**, not failing. Every M figure in this phase
is reported as a fraction of the measured ceiling as well as in absolute terms.
Carrying "M = 89 %" as a bare number into a later summary would read as a large
regression from phase 3's 99 % when it is in fact a perfect score.
See [[feedback_put_the_caveat_in_the_name_not_the_prose]] — the field is named
`m_vs_ceiling`, not `m` with a footnote.

## The stratification requirement (the most likely false null)

26 of 60 referents have a head root unique to them. Selection never makes them
ambiguous, so they **never need a code**. A scramble drop averaged over all 60 is
diluted by roughly 2×, which could push a real cipher under the 1.0 pt threshold
and produce exactly the clean-looking null phase 3 produced.

**The probe is stratified by whether the referent was ambiguous under the subset
the generator actually chose** — not by a static per-referent label, because the
policy decides per utterance how much to withhold. Both strata are reported. The
unambiguous stratum is KILL A′, a built-in negative control that comes free.

This is the same error as the contaminated cipher control, which compared a
scrambled subset against a full-set baseline and produced a spurious 1.35 pt drop
on a provable no-op.

## Must-beat baselines / controls

1. **PLANTED-CIPHER POSITIVE CONTROL — mandatory, runs before the experiment.**
   Force `aspect_reps = f(referent index)` and confirm the scramble probe reports
   a large drop on that channel. The probe's sensitivity is established only in
   the regime where M is free; a long green record in one regime says nothing
   about a regime the code has never run in. **If the planted cipher is not
   detected, phase 4 does not run.**
2. **Selection-off control** — the phase 3 configuration, full signature always
   uttered, same seed and budget. All deltas paired against it.
3. **The 5-seed null band** — `runs/null_band_seeds.json`: no-information
   channels worst 0.09 pts, `aspect_root` +4.01 ± 0.52.
4. **Frozen listener** as held-out judge, never trained in this loop.
5. **Gloss auditor** — audit only, never in the accept loop.

## Method

1. `ChannelPolicy` gains a **selection head**: a Bernoulli per dependent slot,
   conditioned on referent, alongside the existing channel logits.
   `contains[0]` is always realised — the grammar requires a head predication.
2. **Advantage normalised by default.** Phase 3 established that λ multiplies a
   reward term and therefore scales advantage variance (2.17×) as well as novelty
   weight, so a raw λ sweep confounds the two and reads backwards. Any sweep in
   this phase runs on normalised advantage.
   See [[feedback_a_weight_sweep_also_sweeps_step_size]].
3. Reward `M + λ(1 − R)`, M scored by margin. Selection makes M genuinely
   variable for the first time, so the margin now has real gradient.
4. Probe every channel, paired on identical rows, **stratified**.
5. Report the order the detectors fire in.

## Priors to lose (pre-register against)

- **That a cipher will form here.** I expect one. If phase 4 also comes back
  clean *with a passing positive control and a live ambiguous stratum*, that is a
  real result and much stronger than phase 3's.
- **That concentration will indicate it.** Phase 3 showed concentration measures
  *determinism*, not ciphering: 0.774 concentration with every no-info channel
  ≤0.20 pts was a fixed **idiolect**, not a code. It is carried as a diversity
  metric only. If it turns out to track a real cipher here, my model is wrong.
- **That selection will be used.** The policy may simply learn to always say
  everything, since that maximises M. KILL C exists because that is the likeliest
  boring outcome.

## Deviations from LOCK `3c49ad47` (recorded, not edited)

1. **KILL B's threshold was never usable.** "Auditor falls > 10 pts" is over half
   its usable 43.8 → 25 band. It must be expressed as a fraction of the
   honest-to-chance band with seed variance.
2. **KILL B is additionally confounded under selection.** The 43.8 % baseline was
   measured on *complete* scenes. Under selection the auditor sees partial
   glosses and will likely fall for entirely honest reasons. **It must be
   re-baselined in the new regime before any threshold means anything** —
   otherwise the yardstick inherits the very change it is meant to detect.
3. **KILL A is now stratified.** Unstratified, it is measured on a population
   half of which cannot produce the effect.

## Standing floor (reportable regardless)

- **Cipher forms:** we located the boundary, with a passing positive control, a
  calibrated null band, and a built-in negative control. This is what the
  instrument was built to catch.
- **No cipher, positive control passes, ambiguous stratum live:** the framework
  survived real pressure with a demonstrated detection floor. Unlike phase 3,
  this null would mean something.
- **KILL C:** selection is never used; M scarcity does not translate into
  behaviour at this scale.

## Cost / lane

Local, $0. Same ~5 M-param models. Sweep is minutes. Ledger row regardless.

## ⛔ BLOCKED — needs Nate's call

- **Lock this prereg** (body hash → `tools/lock_prereg.py`).
- **KILL B's restated threshold**, once the auditor re-baseline lands. I am not
  setting it from the artefact under audit.
