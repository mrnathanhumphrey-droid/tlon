"""⛔⛔ THE MISSING ADMISSION CRITERION — does the axis SEPARATE THE SPEAKERS?

`$0`. The panel was admitted on two requirements: low **contamination**
(between-build sd / within-conversation movement) and a stable jackknife rank.
Neither asks whether builds are DISTINGUISHABLE on the axis at all.

⭐ ICC = the share of conversation-level variance attributable to BUILD IDENTITY,
with the between-build term corrected for sampling error:

    sd_between* = sqrt(max(0, sd(centroids)^2 − sd_within^2 / n))
    ICC         = sd_between*^2 / (sd_between*^2 + sd_within^2)

⛔⛔ AND THE TWO CRITERIA POINT OPPOSITE WAYS. Contamination has between-build
spread in its NUMERATOR, so ranking observables by ASCENDING contamination is
close to ranking them by ASCENDING build-separability. Selecting the arena
observable and selecting the distance axis are therefore in direct tension, and
the Stage-1 rule only ever asked for one of them.
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

from act2_observable_screen import OBSERVABLES, scenes_of                # noqa: E402
from act2_ranking_stability import (ASYM_BUILDS, _transcript,            # noqa: E402
                                    contamination, load_builds)

#: A distance axis must attribute at least this much conversation-level variance
#: to build identity. Below it, two speakers are not meaningfully apart and no
#: amount of `n` makes the gap worth resolving — you would be measuring a
#: statistically significant, substantively empty separation.
MIN_ICC = 0.30


def per_conversation():
    out = {}
    for name, d, pat in ASYM_BUILDS:
        for p in sorted(pathlib.Path(d).glob(pat)):
            sc = scenes_of(_transcript(json.loads(p.read_text(encoding="utf-8"))))
            for o, fn in OBSERVABLES.items():
                v = fn(sc)
                if v is not None:
                    out.setdefault(o, {}).setdefault(name, []).append(v)
    return out


def icc_of(groups):
    g = [np.asarray(v) for v in groups.values() if len(v) > 2]
    if len(g) < 3:
        return None
    n = float(np.mean([len(x) for x in g]))
    within2 = float(np.mean([x.var(ddof=1) for x in g]))
    obs2 = float(np.stack([x.mean() for x in g]).var(ddof=1))
    between2 = max(obs2 - within2 / n, 0.0)
    denom = between2 + within2
    return {"icc": (between2 / denom) if denom else float("nan"),
            "sd_between_corrected": float(np.sqrt(between2)),
            "sd_within": float(np.sqrt(within2)),
            "F": (obs2 / (within2 / n)) if within2 else float("nan")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/act2/separability.json")
    a = ap.parse_args()

    per = per_conversation()
    pb = load_builds(ASYM_BUILDS)
    names = list(pb)

    rows = []
    for o, fn in OBSERVABLES.items():
        if o not in per:
            continue
        r = icc_of(per[o])
        if r is None:
            continue
        r.update(observable=o, contamination=contamination(pb, names, fn))
        r["separates"] = bool(r["icc"] >= MIN_ICC)
        rows.append(r)

    print("SEPARABILITY — does the axis distinguish the speakers at all?")
    print("=" * 78)
    print("  %-18s %7s %11s %10s %8s %8s"
          % ("observable", "ICC", "sd_betw*", "sd_within", "F", "contam"))
    for r in sorted(rows, key=lambda z: -z["icc"]):
        c = r["contamination"]
        print("  %-18s %7.3f %11.4f %10.4f %8.2f %8s%s"
              % (r["observable"], r["icc"], r["sd_between_corrected"],
                 r["sd_within"], r["F"],
                 ("%.2f" % c) if c is not None and np.isfinite(c) else "inf",
                 "" if r["separates"] else "   ⛔"))

    good = [r for r in rows
            if r["contamination"] is not None and np.isfinite(r["contamination"])]
    ic = np.array([r["icc"] for r in good])
    ct = np.array([r["contamination"] for r in good])
    ri = ic.argsort().argsort().astype(float)
    rc = ct.argsort().argsort().astype(float)
    rho = float(np.corrcoef(ri, rc)[0, 1])

    print("\n  ⛔⛔ Spearman(ICC, contamination) = %+.3f over %d observables."
          % (rho, len(good)))
    print("     Contamination has between-build spread in its NUMERATOR, so "
          "admitting the\n     LOWEST-contamination axes admits the axes on which "
          "the builds are LEAST\n     distinguishable. The Stage-1 rule selected "
          "against separability.")

    panel = ("tokens/surface", "nodes/scene")
    print("\n  ── the admitted panel, scored on the criterion nobody applied ──")
    for o in panel:
        r = next(x for x in rows if x["observable"] == o)
        print("  %-18s ICC %.3f%s" % (o, r["icc"],
                                      "" if r["separates"] else "   ⛔ BELOW %.2f"
                                      % MIN_ICC))
    print("\n  ⇒ MORE CONVERSATIONS CANNOT FIX THIS. `n` shrinks the standard "
          "error; it does\n     not enlarge a separation that is not there.")

    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(
        json.dumps({"min_icc": MIN_ICC, "spearman_icc_contamination": rho,
                    "rows": rows}, indent=1, ensure_ascii=False),
        encoding="utf-8", newline="")
    print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ═══ THREE-WAY ADMISSION, SEPARABILITY-FIRST ════════════════════════════════
#
# ⛔⛔ THE PRIORITY ORDER IS ARGUED, NOT TUNED. Separability is HARD because it is
# about the measurement EXISTING: below it there is no distance to shrink and
# nothing to detect. Contamination is SOFT — a noisier signal is still a signal.
#
# ⭐ AND RANK-STABILITY IS NOT SOFTENED, IT IS REPLACED. Jackknife RANK range
# answers "does this axis keep its POSITION when the build set changes" — a
# question about which axis generalises as best-in-class. A distance axis needs a
# different property: does it SEPARATE, reliably. The direct test of that is
# whether the ICC ITSELF survives dropping a build. Substituting the direct
# measurement for a proxy is not the same move as relaxing a threshold.
#
# ⛔ THE CORRUPTION TEST, APPLIED: would this ordering hold if `root TTR` had
# passed rank-stability and failed separability instead? Yes — separability would
# still be the hard floor, because a rank-stable axis that cannot tell two
# speakers apart still yields no measurement. The argument does not reference
# which observable passes.
#
# ⚠️ PROVENANCE, STATED: `MIN_ICC = 0.30` was set AFTER the ICC table was
# computed. Its justification is that below 0.30 more than 70 % of what a
# conversation shows is not about which build produced it, so a "distance between
# speakers" would mostly not be about the speakers. Read the ICC column directly
# rather than leaning on the threshold.

MIN_JACK_ICC = 0.25         #: separability must survive dropping any one build


def jackknife_icc(per_obs):
    """Leave-one-BUILD-out ICC. The direct analogue of the rank jackknife, on
    the quantity a distance axis actually needs."""
    builds = list(per_obs)
    out = []
    for drop in builds:
        sub = {b: v for b, v in per_obs.items() if b != drop}
        r = icc_of(sub)
        if r:
            out.append(r["icc"])
    return out
