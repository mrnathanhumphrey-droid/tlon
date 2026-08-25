"""SEED PLAN for 13.2 -- the one open decision, costed instead of asked blind.

Reuses 10.0's estimator and its variance prior (phase-8's within-arm seed spread
on the archive) so the two numbers are commensurable and nobody has to trust a
second implementation.

⛔⛔ THE PRIOR IS WEAKER HERE THAN IT WAS AT 10.0, AND THE RISK RUNS ONE WAY.
10.0 already flagged it as optimistic because v2's f2 is lower than the
archive's. 13.2 is further out still: inside a residue cluster M is NON-VACUOUS
for the first time in the project -- phase-8's spread was measured in a regime
where "accuracy saturates at 100% immediately". A statistic that was pinned at
ceiling has less room to vary than one that is not, so 13.2's true sd could be
LARGER than the prior and every MDE below correspondingly optimistic. Treat the
table as a floor on the seed count, never a ceiling.
"""
from __future__ import annotations

import json
import pathlib
import statistics as S
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from run_10_0_mde import banner, mde, n_for                      # noqa: E402

RUNS = pathlib.Path(__file__).resolve().parents[1] / "runs"


def main() -> int:
    rd = json.loads((RUNS / "reset_dynamics.json").read_text())
    gaps = [100 * r["gap_final"] for r in rd["runs"]]
    banner("phase-8 seeds in the variance prior", len(gaps), 5)
    sd = S.stdev(gaps)
    print(f"    {'sample sd of the prior (pts, HUMAN-READ)':<54} {sd:.2f}")

    print("\n  MDE vs SEED COUNT  (two-sided 95%, unpaired, per arm)")
    print(f"    {'n':>4}  {'MDE (pts)':>10}   cost = n x arms x steps")
    for n in (5, 8, 10, 12, 16, 20, 24):
        star = "   <- 10.0's quoted figure" if n == 5 else ""
        print(f"    {n:>4}  {mde(sd, n):>9.2f}  {star}")

    print("\n  SEEDS NEEDED TO REACH A GIVEN MDE")
    for target in (4.40, 4.0, 3.0, 2.5, 2.0):
        print(f"    MDE {target:>5.2f} pts  ->  n = {n_for(sd, target)}")

    print("""
  ⭐ THE PAIRED DESIGN IS THE CHEAPEST POWER AVAILABLE AND IT IS NOT IN THIS
  TABLE. Part B's primary contrast -- residue-gap growth vs expressible-gap
  growth -- is measured on the SAME pair, SAME seeds, SAME interaction length,
  so it is a PAIRED comparison and its variance is sd(difference), not sd(gap).
  Wherever the two curves are positively correlated across seeds, sd(difference)
  is strictly smaller and the effective MDE is better than every row above.

  ⛔ BY HOW MUCH IS UNKNOWN AND MUST NOT BE ASSUMED. No run has ever produced
  the two curves together, so their correlation has never been observed. Quoting
  a paired MDE now would be a number recalled rather than measured. The honest
  move: SIZE THE RUN OFF THE UNPAIRED TABLE, then report the realised paired sd
  from Part A and re-power Part B against it -- which is exactly what the spec
  already requires ("Part A's effect estimate feeds Part B's power calc").""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
