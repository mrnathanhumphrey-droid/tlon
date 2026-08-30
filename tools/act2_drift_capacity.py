"""⛔⛔ DRIFT-CAPACITY — can the separable axes MOVE, or are they locked?

`$0`, on the 98 in-regime transcripts.

⭐ THE SECOND FLOOR, WHICH WAS HIDING IN CONTAMINATION'S DENOMINATOR. Selecting a
distance axis on separability alone is the same one-criterion mistake as
selecting on contamination alone, in the other direction:

    contamination-only  ->  axes where the builds are IDENTICAL   (nothing to measure)
    separability-only   ->  axes where the builds may be LOCKED   (nothing to move)

An axis usable for DRIFT needs both: speakers distinguishable at baseline, AND
capable of moving within an interaction. The forces separate robustly — but the
solo-COLD result showed each build settles into its own force attractor and
STAYS there, which is a live warning that force may be separable-but-inert.

⛔⛔ AND RAW HALF-TO-HALF MOVEMENT CANNOT ANSWER THIS. A perfectly FROZEN rate
still shows movement between two halves, purely from sampling: 20 turns at
p = 0.5 give a half-difference of ≈ 0.13 on average with nothing changing at all.
So the test is observed movement AGAINST THE MOVEMENT A FROZEN AXIS WOULD
PRODUCE:

    expected |Δ| under a frozen rate  =  sqrt(2·σ²_turn / n_half) · sqrt(2/π)
    capacity ratio                    =  observed |Δ| / expected |Δ|

    ratio ≈ 1  ->  ⛔ FROZEN. The "movement" is sampling noise. Drift is
                   unmeasurable on this axis by construction.
    ratio >> 1 ->  ⭐ the axis genuinely moves within a conversation.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from act2_observable_screen import _nodes, scenes_of                     # noqa: E402
from act2_ranking_stability import ASYM_BUILDS, _transcript              # noqa: E402

FORCES = ("ka", "ki", "ko", "ku", "kä")

#: An axis must move more than this multiple of what a frozen axis produces by
#: sampling alone. 1.0 is exactly "indistinguishable from frozen", so the floor
#: has to sit meaningfully above it.
MIN_CAPACITY_RATIO = 1.25


def per_turn_series(sc):
    """Per-turn values, so the frozen-null can be computed from turn variance."""
    out = {"tokens/surface": np.array([len(s.split()) for _, s in sc], float),
           "nodes/scene": np.array([len(_nodes(x.node)) for x, _ in sc], float)}
    f = [x.force for x, _ in sc]
    for k in FORCES:
        out["force:%s" % k] = np.array([1.0 if y == k else 0.0 for y in f])
    roots = [{n.root for n in _nodes(x.node)} for x, _ in sc]
    out["root TTR"] = np.array([len(r) for r in roots], float)   # proxy series
    return out


def capacity(series):
    """observed half-to-half movement vs what a FROZEN axis would produce."""
    n = len(series)
    if n < 8:
        return None
    h = n // 2
    a, b = series[:h], series[h:]
    obs = abs(float(b.mean() - a.mean()))
    var = float(series.var(ddof=1))
    if var <= 0:
        return {"observed": obs, "expected_frozen": 0.0, "ratio": float("nan")}
    exp = float(np.sqrt(2.0 * var / h) * np.sqrt(2.0 / np.pi))
    return {"observed": obs, "expected_frozen": exp,
            "ratio": obs / exp if exp > 0 else float("nan")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/act2/drift_capacity.json")
    a = ap.parse_args()

    acc = {}
    for name, d, pat in ASYM_BUILDS:
        for p in sorted(pathlib.Path(d).glob(pat)):
            sc = scenes_of(_transcript(json.loads(p.read_text(encoding="utf-8"))))
            if len(sc) < 8:
                continue
            for o, s in per_turn_series(sc).items():
                c = capacity(s)
                if c and np.isfinite(c["ratio"]):
                    acc.setdefault(o, []).append(c)

    print("DRIFT-CAPACITY — do the separable axes MOVE, or are they locked?")
    print("=" * 78)
    print("  null: the axis is FROZEN within a conversation and only sampling")
    print("        moves the halves. ratio = observed / expected-under-frozen.")
    print("  ⛔ ratio ~ 1.0 = indistinguishable from frozen · floor %.2f\n"
          % MIN_CAPACITY_RATIO)
    print("  %-18s %5s %10s %10s %8s" % ("observable", "n", "observed",
                                         "if frozen", "ratio"))
    rows = []
    for o, v in acc.items():
        obs = float(np.mean([x["observed"] for x in v]))
        exp = float(np.mean([x["expected_frozen"] for x in v]))
        r = float(np.mean([x["ratio"] for x in v]))
        se = float(np.std([x["ratio"] for x in v], ddof=1) / np.sqrt(len(v)))
        rows.append({"observable": o, "n": len(v), "observed": obs,
                     "expected_frozen": exp, "ratio": r, "ratio_se": se,
                     "moves": bool(r >= MIN_CAPACITY_RATIO)})
    for r in sorted(rows, key=lambda z: -z["ratio"]):
        print("  %-18s %5d %10.4f %10.4f %6.2f±%.2f%s"
              % (r["observable"], r["n"], r["observed"], r["expected_frozen"],
                 r["ratio"], r["ratio_se"],
                 "  ⭐ moves" if r["moves"] else "   ⛔ frozen"))

    sep = ("force:ki", "force:ka")
    print("\n  ── the robustly SEPARABLE axes, on the second floor ──")
    for o in sep:
        r = next(x for x in rows if x["observable"] == o)
        print("  %-18s capacity ratio %.2f ± %.2f  %s"
              % (o, r["ratio"], r["ratio_se"],
                 "⭐ MOVES" if r["moves"] else "⛔ FROZEN — separable but inert"))

    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(
        json.dumps({"min_capacity_ratio": MIN_CAPACITY_RATIO, "rows": rows},
                   indent=1, ensure_ascii=False), encoding="utf-8", newline="")
    print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
