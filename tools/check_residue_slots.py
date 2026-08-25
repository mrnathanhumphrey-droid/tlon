"""Report which 13.2 lyric slots the distiller has filled, and audit the filled
ones against the brief.

⛔ THE BRIEF IS A CONSTRAINT, NOT ADVICE. `residue.normalized` has span 4, so a
coordinate outside 0..4 silently saturates at 1.0 and destroys exactly the
gradation the metric arm exists to provide -- a violation would not raise
anywhere, it would just quietly flatten the metric arm into a categorical one
and hand back a manufactured null. So the bound is checked here, out loud.
"""
from __future__ import annotations

import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

import yaml                                                      # noqa: E402

from tlon.grammar import residue as R                            # noqa: E402
from tlon.referents import schema                                # noqa: E402

AXIS, SPAN, DIM = 5, 4, 3


def gradation(pts: list[tuple[int, ...]]) -> None:
    """⛔⛔ IS THIS A METRIC RESIDUE, OR A CATEGORICAL ONE WEARING METRIC CLOTHES?

    Nate's catch, and it is the one that decides whether the metric arm is worth
    running at all: if every pair is either ~0 apart or at the far corner, the
    set has no 'nearby' and it has quietly re-made the categorical arm. The head
    would then have nothing to generalise ACROSS, and metric-vs-categorical
    would come back null for a reason that has nothing to do with evocation.

    The categorical arm is the reference point and it is exact: one-hot
    coordinates have ZERO distance variance (every pair equidistant). So the
    diagnostic is how far this set sits from that degenerate case, plus whether
    the middle of the range is actually populated.
    """
    import itertools as it
    ds = [R.normalized(a, b, span=SPAN) for a, b in it.combinations(pts, 2)]
    lo, hi = min(ds), max(ds)
    mid_lo, mid_hi = lo + 0.25 * (hi - lo), lo + 0.75 * (hi - lo)
    mid = sum(1 for d in ds if mid_lo <= d <= mid_hi) / len(ds)
    levels = len(set(round(d, 6) for d in ds))
    cv = (statistics.pstdev(ds) / statistics.fmean(ds)) if statistics.fmean(ds) else 0.0
    print(f"\n  GRADATION AUDIT — is the metric arm actually metric?")
    print(f"    {'pairwise normalised distance':<34} "
          f"min {lo:.3f}  mean {statistics.fmean(ds):.3f}  max {hi:.3f}")
    print(f"    {'distinct distance levels used':<34} {levels}")
    print(f"    {'coefficient of variation':<34} {cv:.3f}"
          "   (one-hot categorical = 0.000)")
    print(f"    {'share of pairs in the middle half':<34} {100*mid:.1f}%")
    # crude histogram so the SHAPE is visible, not just the summary
    nb = 10
    hist = [0] * nb
    for d in ds:
        hist[min(nb - 1, int(nb * (d - lo) / (hi - lo)) if hi > lo else 0)] += 1
    w = max(hist) or 1
    for i, c in enumerate(hist):
        band = lo + (hi - lo) * (i + 0.5) / nb
        print(f"      {band:.2f} {'█' * int(28 * c / w):<28} {c}")
    # ⛔⛔ THE VERDICT MUST BE ABLE TO SEE THE SHAPE IT EXISTS TO CATCH. The
    # first version tested `levels < 4 or mid < 0.15` and PASSED a set built
    # as three tight clumps at far corners -- the exact trap -- because 6
    # levels and 36% mid-mass clear those bars while the distribution has a
    # hard hole through its middle. The histogram showed it; the verdict did
    # not. A verdict can only report outcomes it was written to recognise.
    #
    # Bimodality is a GAP, not a low average, so the statistic is the largest
    # CONTIGUOUS empty stretch of the range.
    run = best = 0
    for c in hist:
        run = run + 1 if c == 0 else 0
        best = max(best, run)
    gap = best / nb
    print(f"    {'largest contiguous empty band':<34} {100*gap:.0f}% of the range")
    if levels < 4 or gap >= 0.20:
        print("    ⛔⛔ CATEGORICAL WEARING METRIC CLOTHES — the distribution "
              "has a hole through it,\n         so pairs are either 'near' or "
              "'far' with nothing in between. The head has no\n         "
              "gradient to generalise across and the metric arm would differ "
              "from the\n         categorical arm in name only. Spread the "
              "intermediate judgments.")
    else:
        print("    ✅ graded: intermediate distances are populated, so nearby "
              "and far are\n       distinguishable and the head has something "
              "to interpolate.")


def main() -> int:
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else schema.LYRIC_PATH
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    rows = raw["referents"]
    filled, empty, bad = [], [], []
    for row in rows:
        got = [p.get("residue_any") or []
               for p in row["signature"]["contains"]]
        coords = [tuple(c) for cs in got for c in cs]
        if not coords:
            empty.append(row["id"])
            continue
        for c in coords:
            try:
                R.validate(c)
            except R.ResidueTypeError as e:
                bad.append((row["id"], f"not a coordinate: {e}"))
                continue
            if len(c) != DIM:
                bad.append((row["id"], f"dim {len(c)}, brief says {DIM}"))
            if any(not (0 <= v < AXIS) for v in c):
                bad.append((row["id"],
                            f"{c} outside 0..{AXIS - 1} — normalized() would "
                            f"saturate at 1.0 and flatten the metric"))
        filled.append((row["id"], coords[0]))

    print(f"\n  {path.name}")
    print(f"    {'referents':<34} {len(rows)}")
    print(f"    {'slots FILLED':<34} {len(filled)}")
    print(f"    {'slots EMPTY':<34} {len(empty)}"
          + (f"   ({', '.join(empty[:6])}{' …' if len(empty) > 6 else ''})"
             if empty else ""))
    if bad:
        print(f"\n  ⛔ {len(bad)} COORDINATE(S) VIOLATE THE BRIEF:")
        for rid, why in bad:
            print(f"     · {rid}: {why}")
    if filled and not empty and not bad:
        pts = [c for _, c in filled]
        print(f"    {'distinct coordinates':<34} {len(set(pts))}/{len(pts)}")
        print(f"    {'lattice occupancy':<34} "
              f"{len(set(pts))}/{AXIS ** DIM} points")
        gradation(pts)
        try:
            schema.load_residue_arm("lyric", allow_unreviewed=True)
            print("\n  ✅ complete and loadable — the metric arm can run once "
                  "Nate marks it REVIEWED.")
        except schema.ReferentError as e:
            print(f"\n  ⛔ still refused by the loader: {e}")
            return 1
    else:
        print("\n  ⏸ INCOMPLETE — the metric arm cannot run. Part A's metric "
              "cells wait on the distillation.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
