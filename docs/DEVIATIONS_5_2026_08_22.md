# DEVIATIONS from PREREG 5 — LOCK `c09d0fb3`

Recorded, never edited into the locked body.

**All five are the same mistake: treating ZERO as the default for a quantity
nobody measured.** A baseline not measured, a threshold not calibrated, a
control not checked for whether it could move. Every one produced a
plausible-looking number.

---

## D3 — π-constant channels cannot be probed at all

**Locked text:** KILL A applies to no-information channels at > 1.0 pt.

**Actual:** π pins `aspect_reps`, `degree`, `coda`, `orient_order` to constants.
Scrambling a constant does not remove information — it manufactures an utterance
that never occurs in training, so any drop measures **brittleness**. The tell in
v2: `aspect_reps` read **+0.00 at λ=0 and +7.84 at λ=2** with the channel
constant in both. What scaled was overfitting.

**Replacement:** the exclusion set is *derived* by asking
`denote.nondenoting_parts()` which parts π pins, so it tracks π automatically
instead of going stale. Those channels print *probe undefined*. Blindness is
tested by the accuracy route in `pi_controls.py`, never by scrambling.

## D4 — `co` shadowing silently un-froze half the control arms

**Actual:** the arms tuple unpacked the co-adaptation flag as `co`; thirty lines
later `co = mean_acc(...)` overwrote it with an accuracy. The first λ used the
boolean, the second inherited the previous iteration's **truthy float**, so
`train_listener=0.963` and the listener trained anyway.

**Caught because the numbers were BYTE-IDENTICAL** to the co-adapting twin —
M 99.8 %, gap +12.33, R 0.181, decidedness 0.803, four channel drops. Had it
produced plausibly *different* numbers, the frozen control would have read as
"distribution shift explains most of the gap", I would have subtracted it, and
phase 5 would have looked like a partial success.

**Replacement:** flag renamed `co_adapt`.

## D5 — the random-policy baseline was wrong for channels that denote

**Locked text:** KILL A at > 1.0 pt on surviving channels, later amended to
excess over a random-policy baseline.

**Actual:** the **frozen** arms — where co-adaptation is impossible and a code
therefore cannot exist — still show `aspect_root` drops of **+24.89, +11.95,
+26.21, +18.82**. Against a random baseline that reads as KILL A firing where a
code is structurally impossible. A generator that merely concentrates its aspect
choices produces a large drop, because scrambling then destroys information the
listener legitimately uses.

**Replacement:** the reference is an **optimising policy that cannot negotiate**
(frozen listener), not a random one. Under it, five of eight arms show
`aspect_root` excess at or below zero — and KILL E becomes visible.

## D6 — the naive judge was the same model as the arm's listener

**Actual:** `tr.train` calls `torch.manual_seed(cfg.seed)` from a fixed default,
so training twice on the same rows with the same cfg returns **byte-identical
weights**. The seed listener and the naive judge were one model. In the frozen
arms that made the gap **0.00 by construction** — the control compared a model
to itself and **could not have come back positive**.

**Replacement:** the naive judge gets a different init seed *and* a disjoint
honest draw, plus an assertion that the two models differ, which raises rather
than reporting a silent zero. Frozen gaps then move to −1.27 / −1.27 / +1.60 /
+3.73.

⛔ Every gap in v3, v4 and v5 is void.

## D7 — KILL A/E as printed by the tool are superseded

The tool's columns were computed against the random baseline (D5) and understate
KILL E: an arm whose `aspect_root` fired against random had KILL E suppressed
even when the probe was clean against frozen. The verdict recomputes both from
`runs/phase5.json`.

---

## Carried forward, still open

- **KILL B** unset and unmeasured — the gloss auditor needs re-baselining on
  partial glosses. ⛔ Nate's call. No interpretability claim in phase 5.
- **Seeds.** One per cell. The table supports "8–13 points in every arm";
  between-arm differences are not interpretable.
