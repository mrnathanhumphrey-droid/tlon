"""ACT 2 DRY RUN — the whole decision path, end to end, on SYNTHETIC speakers.

⛔ $0.00. No hosted model, no network. This is not a result about language models;
it is a demonstration that the instrument reads correctly on speakers whose drift
and convergence are known BY CONSTRUCTION, which PREREG `20620b7c` step 1 requires
before step 2 spends anything.

    python tools/act2_dryrun.py            # all four synthetic pairs
    python tools/act2_dryrun.py imitating  # one of them
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.act2 import arena, falsify, observe, probes        # noqa: E402
from tlon.act2.speaker import (DegeneratingSpeaker,          # noqa: E402
                               ImitatingSpeaker, MutualCollapseSpeaker,
                               StableSpeaker, WanderingSpeaker)

SEEDS = range(8)                     # PREREG §4: n = 8 seed-paired runs
TURNS, EVERY = 40, 10

PAIRS = {
    "stable":       (StableSpeaker, {}, "no drift at all"),
    "wandering":    (WanderingSpeaker, {"rate": 0.30},
                     "drifts, converges with nobody"),
    "imitating":    (ImitatingSpeaker, {"adopt": 0.90},
                     "builds a SHARED codebook — a pact, by construction"),
    "degenerating": (DegeneratingSpeaker, {"rate": 0.50},
                     "collapses on its own — NOT communication-driven"),
    "collapse":     (MutualCollapseSpeaker, {"rate": 0.90},
                     "falls silent TOGETHER — confabulated drift, F4's target"),
}


def _speakers(cls, seed, kw):
    return cls("A", seed, **kw), cls("B", seed + 1000, **kw)


def run_cell(name: str, battery, frozen) -> None:
    cls, kw, blurb = PAIRS[name]
    print(f"\n── {name.upper()} — {blurb}")

    dd, dc, control_reps = [], [], []
    cov_i, cov_y = [], []
    for seed in SEEDS:
        a, b = _speakers(cls, seed, kw)
        inter = arena.run("interacting", speaker_a=a, speaker_b=b,
                          battery=battery, seed=seed, turns=TURNS,
                          epoch_every=EVERY)
        a, b = _speakers(cls, seed, kw)
        yoked = arena.run("yoked", speaker_a=a, speaker_b=b, battery=battery,
                          seed=seed, turns=TURNS, epoch_every=EVERY,
                          frozen_a=frozen[0], frozen_b=frozen[1])
        # ⛔ A SECOND, INDEPENDENT CONTROL REPLICATE. The MDE is a sign-flip
        # permutation over WITHIN-CONTROL differences (§5.1) and needs one.
        a, b = _speakers(cls, seed + 500, kw)
        yoked2 = arena.run("yoked", speaker_a=a, speaker_b=b, battery=battery,
                           seed=seed, turns=TURNS, epoch_every=EVERY,
                           frozen_a=frozen[1], frozen_b=frozen[0], replicate=1)

        e = len(inter.epochs) - 1
        dd.append(observe.delta(observe.departure(inter, e),
                                observe.departure(yoked, e)))
        dc.append(observe.delta(observe.convergence(inter, e),
                                observe.convergence(yoked, e)))
        control_reps.append(
            falsify.paired_delta(observe.departure(yoked, e),
                                 observe.departure(yoked2, e),
                                 contrast="replicate"))
        cov_i += [r.covariates for r in inter.epochs[1:]]
        cov_y += [r.covariates for r in yoked.epochs[1:]]

    # ⛔⛔ THE MDE IS COMPUTED FROM THE CONTROL ARM ALONE, BEFORE THE
    # INTERACTING ARM IS LOOKED AT (§5.1).
    band = falsify.null_band(control_reps)
    mean_dd = sum(d.value for d in dd) / len(dd)
    mean_dc = sum(d.value for d in dc) / len(dc)

    print(f"   {band.describe()}")
    print(f"   ΔD {100 * mean_dd:+6.2f} pts   ΔC {100 * mean_dc:+6.2f} pts   "
          f"(p_D={falsify.permutation_p(dd):.4f}, p_C={falsify.permutation_p(dc):.4f})")

    for firing in (falsify.f2_drift_is_noise(dd[0].__class__(
                       mean_dd, "arm", dd[0].left, dd[0].right), band.mde),
                   falsify.f3_pact(dc[0].__class__(
                       mean_dc, "arm", dc[0].left, dc[0].right), band.mde),
                   falsify.f4_degeneration(cov_i, cov_y),
                   falsify.f5_leakage(probes.leakage(battery, ()))):
        mark = "FIRED  " if firing.fired else "clear  "
        print(f"   {firing.name} {mark} {firing.detail}")

    if not falsify.f2_drift_is_noise(dd[0].__class__(
            mean_dd, "arm", dd[0].left, dd[0].right), band.mde).fired:
        reading = "drift exceeds control"
    elif not falsify.f3_pact(dc[0].__class__(
            mean_dc, "arm", dc[0].left, dc[0].right), band.mde).fired:
        reading = ("⭐ A PACT THAT ΔD CANNOT SEE — F2 fires, F3 does not. "
                   "Without C this reads as 'drift is noise'.")
    else:
        reading = "no departure and no convergence beyond control"
    print(f"   ⇒ {reading}")


def main() -> int:
    which = sys.argv[1:] or list(PAIRS)
    battery = probes.build(seed=7, n_prod=8, n_comp=8)
    frozen = (arena.record_frozen_transcript(StableSpeaker("f1", 900), turns=TURNS),
              arena.record_frozen_transcript(StableSpeaker("f2", 901), turns=TURNS))
    print(f"PREREG {falsify.PREREG} · battery {battery.digest} "
          f"({len(battery)} probes, lexicon {battery.lexicon[:8]}) · "
          f"n={len(list(SEEDS))} seed-paired · {TURNS} turns")
    print("⛔ synthetic speakers — an instrument check, NOT a result about models")
    for name in which:
        run_cell(name, battery, frozen)
    print("\n⛔ no transcript was read: every number above is from the probe "
          "battery, and the transcripts are still sealed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
