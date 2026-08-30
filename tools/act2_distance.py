"""STAGE 2 — the distance between two speakers, and the frozen cold table.

Spec: docs/SPEC_TWO_SPEAKER_DRIFT_2026_08_30.md §3
Panel: docs/RESULTS_ASYMMETRIC_RECERT_2026_08_30.md — `tokens/surface` +
`nodes/scene`, the ONLY two admitted in-regime. ⛔ `root TTR` and `force:ka` are
OUT and must not be reintroduced; the geometry is 2-D.

⛔⛔ A SPEAKER IS A DISTRIBUTION, NOT A POINT. `s20621` produced conversations
spanning `ka` 0.15–0.925 and a mean (0.462) that describes none of them. A
distance computed from one conversation per speaker would measure a build's own
fuzz and call it drift.

⭐ THE METRIC: 2-Wasserstein between the two speakers' conversation clouds, in
the Gaussian (Fréchet) form, on axes standardised by the FROZEN between-build sd
so one unit is one build-to-build sd:

    W2² = ‖μ₁−μ₂‖²  +  tr(Σ₁) + tr(Σ₂) − 2·tr((Σ₂^½ Σ₁ Σ₂^½)^½)
          └── MEAN TERM ──┘  └────────── SPREAD TERM ──────────┘

⭐⭐ THE DECOMPOSITION IS MANDATORY, NOT DECORATIVE. It is what makes the metric
robust to the s20621 threat: a speaker's own fuzz lives ENTIRELY in the spread
term, so a drift driven by shape change is visibly distinguishable from a drift
driven by the speakers' locations approaching. Chosen over own-spread-normalised
centroid distance because normalising DIVIDES by a quantity that itself moves
between conditions — a change in fuzz would then rescale the whole metric and
manufacture drift multiplicatively. Here it only adds.

⛔ Empirical (matching) W2 was rejected at n=14: the assignment is dominated by
sampling noise at that size, and the Gaussian form has a closed decomposition.

⛔ NO INJECTED MATERIAL. Distances are computed from `conditions.cold_a.surfaces`
of the `--no-injections` arm, which `measurable_turns()` already filtered.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import statistics
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
from act2_ranking_stability import ASYM_BUILDS, _transcript              # noqa: E402

#: ⛔ The in-regime admitted panel. Two axes. Do not add a third.
PANEL = ("tokens/surface", "nodes/scene")

#: ⭐ SAME CORPUS (263fe3c8…) — these differ by TRAINER SEED ONLY, so their pairs
#: are the NEAR pairs and the rest are FAR. That contrast is free and is the
#: built-in test of whether drift depends on how far apart the speakers start.
FIXED_CORPUS = frozenset({"s20620", "t30001", "t30002", "t30003"})

#: ⭐ LOCATABILITY, pre-declared as a rule about the ESTIMATE, not the raw spread.
#: A speaker can be placed relative to the population iff the standard error of
#: its centroid is small against the spread it must be resolved within. `0.5`
#: means "the centroid estimate is at least twice as precise as the distance it
#: has to measure". ⚠️ Declared AFTER seeing per-build sds (they were needed to
#: build the metric) but BEFORE any distance was computed, and set from that
#: principle rather than from what lets builds pass.
MAX_CENTROID_SE_FRACTION = 0.5


def clouds(spec=None):
    """build -> (n_conversations, 2) array of per-conversation panel points."""
    out = {}
    for name, d, pat in (spec or ASYM_BUILDS):
        pts = []
        for f in sorted(pathlib.Path(d).glob(pat)):
            data = json.loads(f.read_text(encoding="utf-8"))
            sc = scenes_of(_transcript(data))
            if len(sc) < 8:
                continue
            v = [OBSERVABLES[o](sc) for o in PANEL]
            if all(x is not None for x in v):
                pts.append(v)
        if len(pts) >= 3:
            out[name] = np.asarray(pts, dtype=float)
    return out


def axis_scale(cl):
    """⭐ FROZEN between-build sd per axis — one distance unit = one build-to-build
    sd. It is computed ONCE from the cold table and reused for the drift run; a
    scale recomputed per condition would move the ruler with the measurement."""
    cent = np.stack([c.mean(axis=0) for c in cl.values()])
    return cent.std(axis=0, ddof=1)


def _sqrtm_psd(A):
    w, V = np.linalg.eigh(A)
    return (V * np.sqrt(np.clip(w, 0.0, None))) @ V.T


def w2(a, b, scale):
    """2-Wasserstein (Gaussian form) with its decomposition. Symmetric."""
    A, B = np.asarray(a) / scale, np.asarray(b) / scale
    dmu = A.mean(axis=0) - B.mean(axis=0)
    mean_term = float(dmu @ dmu)
    S1 = np.cov(A, rowvar=False)
    S2 = np.cov(B, rowvar=False)
    r2 = _sqrtm_psd(S2)
    cross = _sqrtm_psd(r2 @ S1 @ r2)
    spread_term = float(np.trace(S1) + np.trace(S2) - 2.0 * np.trace(cross))
    spread_term = max(spread_term, 0.0)          # numerical floor, not a fudge
    total = mean_term + spread_term
    return {"w2_sq": total, "w2": float(np.sqrt(max(total, 0.0))),
            "mean_term": mean_term, "spread_term": spread_term,
            "mean_frac": (mean_term / total) if total > 0 else float("nan")}


def locatability(cl, scale):
    """Can each speaker be PLACED in the population at all?

    ⛔ `scale` IS the between-build sd (`axis_scale`). An earlier draft recomputed
    it here and ignored the argument — two sources for one number, and the
    silent kind of duplication that drifts apart later.
    """
    between = np.asarray(scale, dtype=float)
    rows = {}
    for name, c in cl.items():
        se = c.std(axis=0, ddof=1) / np.sqrt(len(c))
        frac = se / between
        rows[name] = {"n": int(len(c)),
                      "own_sd": c.std(axis=0, ddof=1).tolist(),
                      "centroid_se": se.tolist(),
                      "se_over_between": frac.tolist(),
                      "worst": float(frac.max()),
                      "locatable": bool(frac.max() <= MAX_CENTROID_SE_FRACTION)}
    return rows, between.tolist()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/act2/cold_table.json")
    a = ap.parse_args()

    cl = clouds()
    scale = axis_scale(cl)
    print("STAGE 2 — DISTANCE, AND THE FROZEN COLD TABLE")
    print("=" * 78)
    print("  panel %s   (2-D; root TTR and force:ka are OUT)" % (PANEL,))
    print("  builds %d · conversations each %s"
          % (len(cl), sorted({len(c) for c in cl.values()})))
    print("  frozen axis scale (between-build sd): %s"
          % np.array2string(scale, precision=4))

    loc, between = locatability(cl, scale)
    print("\n── LOCATABILITY · is a speaker's centroid precise enough to place? ──")
    print("  rule: centroid se <= %.2f x between-build sd on EVERY axis"
          % MAX_CENTROID_SE_FRACTION)
    print("  %-8s %20s %20s %8s" % ("build", "own sd", "centroid se",
                                    "se/between"))
    for n, r in loc.items():
        print("  %-8s %20s %20s %8.2f%s"
              % (n,
                 np.array2string(np.array(r["own_sd"]), precision=4),
                 np.array2string(np.array(r["centroid_se"]), precision=4),
                 r["worst"], "" if r["locatable"] else "   ⛔"))
    unlocatable = [n for n, r in loc.items() if not r["locatable"]]

    rows = []
    names = sorted(cl)
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            d = w2(cl[x], cl[y], scale)
            grp = ("fixed-corpus" if {x, y} <= FIXED_CORPUS else "cross-corpus")
            rows.append({"pair": "%s|%s" % (x, y), "group": grp, **d})

    print("\n── COLD TABLE · 21 pairs, W2 with its decomposition ──")
    print("  %-16s %-13s %7s %9s %9s %7s"
          % ("pair", "group", "W2", "mean term", "spread", "mean%"))
    for r in sorted(rows, key=lambda z: z["w2"]):
        print("  %-16s %-13s %7.3f %9.3f %9.3f %6.0f%%"
              % (r["pair"], r["group"], r["w2"], r["mean_term"],
                 r["spread_term"], 100 * r["mean_frac"]))

    fx = [r for r in rows if r["group"] == "fixed-corpus"]
    cx = [r for r in rows if r["group"] == "cross-corpus"]
    mf = [r["mean_frac"] for r in rows]
    print("\n  fixed-corpus (n=%d) mean W2 %.3f · cross-corpus (n=%d) mean W2 %.3f"
          % (len(fx), statistics.mean(r["w2"] for r in fx),
             len(cx), statistics.mean(r["w2"] for r in cx)))
    print("  share of W2² carried by the MEAN term: median %.0f%%, max %.0f%%"
          % (100 * statistics.median(mf), 100 * max(mf)))

    print("\n" + "=" * 78)
    if unlocatable:
        print("  ⛔⛔ %d of %d BUILDS ARE NOT LOCATABLE: %s"
              % (len(unlocatable), len(cl), unlocatable))
        print("     Their centroids are too imprecise to place against the "
              "between-build\n     spread, so a pairwise distance involving them "
              "is dominated by centroid\n     estimation error rather than by "
              "where the speakers actually are.")
        if len(unlocatable) == len(cl):
            print("\n  ⛔⛔ EVERY BUILD FAILS. This is not an exclusion, it is a "
                  "HALT: the distance\n     is not estimable at 14 conversations "
                  "per speaker. The fix is MORE\n     CONVERSATIONS PER SPEAKER "
                  "(se falls as 1/sqrt(n)), not more speakers.")
    else:
        print("  ⭐ all builds locatable")

    out = {"panel": list(PANEL), "axis_scale": scale.tolist(),
           "between_build_sd": between,
           "max_centroid_se_fraction": MAX_CENTROID_SE_FRACTION,
           "locatability": loc, "unlocatable": unlocatable,
           # ⛔⛔ THE TABLE IS ONLY FROZEN IF EVERY SPEAKER CAN BE PLACED.
           # Freezing a baseline whose centroids are dominated by estimation
           # error would pre-register noise and give the drift run something
           # authoritative-looking to measure against.
           "frozen": not unlocatable,
           "estimand": "drift = W2(LIVE) - W2(YOKED), paired per pair, "
                       "clustered on ADAPTER; COLD is the baseline, not the null",
           "cold_pairs": rows}
    blob = json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True)
    out["sha256"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                   encoding="utf-8", newline="")
    print("\n  COLD TABLE %s · sha256 %s"
          % ("FROZEN" if out["frozen"] else "⛔ NOT FROZEN (provisional)",
             out["sha256"]))
    print("  wrote %s" % a.out)
    print("\n⛔ No drift number. This freezes the baseline the drift run is "
          "measured against.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
