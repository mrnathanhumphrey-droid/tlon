# DEVIATIONS from PREREG 4 — LOCK `c1f7d06c`

Recorded, never edited into the locked body. Each entry: what the prereg says,
what is actually true, the evidence, and what replaces it.

Discovered by `tools/planted_cipher_control.py` → `runs/planted_cipher.json`,
run as the mandatory gate **before** the experiment — which is the whole reason
these were caught before a headline number existed to protect.

---

## D1 — "M ceiling under selection: 89.3 %" is NOT a ceiling. It is a floor.

**Prereg says:** "M CEILING UNDER SELECTION = 89.3 %. A perfect listener,
uniform over the referents still consistent with what it heard, cannot do
better." Thresholds are then stated against it, and KILL D was moved to 70 %
on that basis.

**What is actually true:** 89.3 % is `E[1 / |consistent set|]` — the accuracy of
a listener that recovers the consistency set and then picks **uniformly** inside
it. A Bayes-optimal listener does not pick uniformly. It uses the likelihood:
`P(ref | surface) ∝ P(surface | ref) P(ref)`. If referent A emits a given partial
scene far more often than B does, the posterior favours A even though both remain
consistent. So the uniform-posterior figure is a **lower bound on what a perfect
listener achieves**, not an upper bound.

**Evidence, two independent routes:**
1. **Empirical.** Arm A of the planted-cipher control — no code, partial
   utterances — reaches **92.1 %**, above the "ceiling". A number that a real
   listener exceeds was never a ceiling.
2. **Arithmetic.** Arm A's test rows: 23.7 % ambiguous, mean consistency-set size
   1.38. Uniform-posterior accuracy for that mix is ≈ 85.4 %. The listener beat
   it by ~7 pts, exactly the gap likelihood information buys.

**What replaces it.** The quantity is renamed in every artefact from here on:

    m_uniform_floor = 0.893     # NOT a ceiling
    m_honest_observed = 0.921   # measured, no-code arm, this subset distribution

The true Bayes ceiling is unmeasured and sits somewhere above 92.1 %. **The
headline claim is unaffected**: M is no longer pinned near 100 % (phase 3 ran at
99.2–100 %), which is the only property phase 4 needed. What changes is that
`m_honest_observed = 92.1 %` is the honest comparison point, not 89.3 %.

**KILL D stays at 70 %.** It was set for headroom below a non-100 % ceiling and
70 % is still comfortably below 92.1 %.

⛔ This is exactly [[feedback_put_the_caveat_in_the_name_not_the_prose]]: I wrote
"ceiling" in prose and it was already being used as one three documents later.
The fix is the variable name, not a footnote. And
[[feedback_plausibility_check_the_rules_output_before_any_statistics]] — the
first listener to run under selection immediately produced an impossible number,
and that was cheaper than any statistic.

---

## D2 — KILL A′ as written would flag a REAL cipher as a probe artefact.

**Prereg says:** "KILL A′ — the same channels on the **unambiguous stratum** must
stay ≤ 0.5 pt. Those 26 referents never need a code. If they show a drop, the
probe is reading something other than a cipher and KILL A's number is
uninterpretable. A′ is checked before A is believed."

**What is actually true:** a planted code that is genuinely a cipher drops
**+14.29 pts on the unambiguous stratum** (arm B). A′ as locked would fire, and
its stated consequence — "KILL A's number is uninterpretable" — would discard a
true positive.

**Why.** A′ assumed a code forms only where it is needed. It does not. The policy
is a per-referent lookup table, so a code is set for *every* referent including
the ones whose head root already identifies them; and the listener will **use a
free shortcut even where it has sufficient honest signal.** Phase 3 already
showed the generator concentrates across all referents regardless of pressure
(0.73–0.83 in every condition). Spillover is the expected case, not the exotic
one.

**Sub-finding worth keeping:** a cipher does not merely *add* a channel, it
**cannibalises the honest one.** Arm B leans on the code even on rows where
structure alone suffices — which is why the unambiguous stratum bleeds 14 pts.
That is the interpretability damage the phase exists to detect, showing up as a
measurement.

**What replaces it.** The negative control moves off the stratum split, which is
contaminated by construction, and onto the arm split, which is not:

- **A′-new (probe specificity):** the probe must stay **≤ 0.5 pt** on a
  **no-code control arm** — a run with the same selection regime and no coded
  channel. Measured: **+0.17 pt overall, +0.00 on the unambiguous stratum.**
  This is a real negative control because the absence of a code is *constructed*,
  not inferred.
- **Stratified drops are still reported**, but as *description*, not as a kill
  condition. The informative form is the **ratio**: arm B hits the ambiguous
  stratum ~4.7× harder than the unambiguous one (66.67 / 14.29). A probe artefact
  would show no such asymmetry. This ratio is **not** given a threshold here — it
  has one observation and deriving a threshold from it would make the yardstick a
  product of the artefact under audit ([[yardstick]]).

---

## Still open from LOCK `3c49ad47` (carried forward, unchanged)

- **KILL B's threshold** — "auditor falls > 10 pts" is over half its usable
  43.8 → 25 band, and the 43.8 % baseline was measured on *complete* scenes. It
  needs re-baselining under selection before any threshold means anything.
  ⛔ Nate's call, after the re-baseline lands.
