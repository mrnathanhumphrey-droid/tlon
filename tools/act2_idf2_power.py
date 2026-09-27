"""IDF-2 §3A — the power check's arithmetic, on disk as a committed tool.

`docs/PREREG_IDF2_2026_09_26.md`, LOCK `37363296`.

    python tools/act2_idf2_power.py --root runs/act2/idf2/stepP \
        --cell ct-s20624 --step0 runs/act2/idf2/step0.json --out power.json

⛔⛔ THIS DECIDES WHETHER THE READING TABLE CAN SEPARATE ITS OWN CELLS. If
`2 × between-seed SD > 15 points`, §6's bands did not resolve and the reading
is **no verdict** regardless of where any point estimate lands — so the run
stops here, before three adapters are bought, and the choice between more
chains, more seeds and wider bands is a RE-LOCK rather than a mid-run
adjustment.

⭐ Widening the bands after seeing this number, but before any treatment
exists, is legitimate. Widening them after M has read is retrofitting. That
distinction is the only reason this step runs first, and it is why the tool
refuses to read any M-arm file.
"""
from __future__ import annotations

import argparse
import glob
import json
import pathlib
import statistics
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

#: §6's band boundaries, inherited verbatim from `PREREG_IDF1B` §4 in IDF-1b's
#: own role. ⛔ Not redefined here — if these ever need to move it is a re-lock.
FLOORS_POINTS = 15.0
INSTALLS_POINTS = 35.0

#: §3A's trip. ⛔ `2 ×` the SD, not the SD: the question is whether the bands
#: separate, and a boundary one SD wide is a coin flip.
TRIP_MULTIPLE = 2.0


def closes(lag2: float, *, blind: float, corpus: float) -> float:
    """§6's ONE denominator: `(blind₀c − x) / (blind₀c − corpus₀a)`, in points.

    ⛔ THE DENOMINATOR IS THE CORPUS, NOT THE 0b ORACLE. They agree to 0.0008
    — that agreement IS 0b's red-proof — but the oracle is the proof that the
    marker is sufficient, not the scale's endpoint, and a locked formula is
    not approximated.
    """
    return 100.0 * (blind - lag2) / (blind - corpus)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True)
    ap.add_argument("--cell", default="ct-s20624")
    ap.add_argument("--step0", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    s0 = json.loads(pathlib.Path(a.step0).read_text(encoding="utf-8"))
    blind, corpus = s0["blind_lag2"], s0["corpus_lag2"]
    gap = blind - corpus

    files = sorted(glob.glob("%s/lag_%s_s*.json" % (a.root, a.cell)))
    if not files:
        raise SystemExit("⛔ no lag files under %s" % a.root)

    rows, bad = [], []
    for f in files:
        d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        # ⛔⛔ EVERY READ MUST SAY HOW IT WAS TAKEN, AND STEP P IS THE UNMARKED
        # ARM. A marked read pooled in here would measure the marker's spread
        # and call it C0's noise — the gate would then be calibrated on the
        # treatment it exists to protect.
        if d.get("marker_fn") is not None:
            bad.append((f, "marker_fn=%r — this is not a C0 read"
                        % d["marker_fn"]))
            continue
        if not d.get("decoder_sampled") or d.get("temperature") != 0.7:
            bad.append((f, "decoder %r — a lag read is T=0.7"
                        % d.get("temperature")))
            continue
        prof = d.get("lag_profile") or {}
        lag2 = prof.get("2", prof.get(2))
        if lag2 is None:
            bad.append((f, "no lag-2 cell: %s" % d.get("refusal_reason")))
            continue
        rows.append({"file": pathlib.Path(f).name, "seed": d.get("seed"),
                     "lag1": prof.get("1", prof.get(1)), "lag2": lag2,
                     "closes": closes(lag2, blind=blind, corpus=corpus),
                     "n_pairs": (d.get("n_pairs") or {}).get("2"),
                     "chains_used": d.get("chains_used"),
                     "dropped": d.get("chains_dropped_too_short")})

    print("=" * 70)
    print("IDF-2 STEP P — the power check · prereg LOCK 37363296")
    print("=" * 70)
    print("  gap  %.4f   (blind %.4f − corpus %.4f)" % (gap, blind, corpus))
    print()
    print("  %-6s %8s %8s %9s %7s %8s" % ("seed", "lag1", "lag2", "closes",
                                          "pairs", "dropped"))
    for r in rows:
        print("  %-6s %8.4f %8.4f %8.1f%% %7s %8s"
              % (r["seed"], r["lag1"], r["lag2"], r["closes"],
                 r["n_pairs"], r["dropped"]))
    for f, why in bad:
        print("  ⛔ EXCLUDED %s — %s" % (pathlib.Path(f).name, why))

    if len(rows) < 2:
        raise SystemExit("\n⛔ %d usable read(s) — an SD needs at least 2"
                         % len(rows))

    vals = [r["closes"] for r in rows]
    sd = statistics.stdev(vals)
    df = len(vals) - 1
    trip = TRIP_MULTIPLE * sd
    ok = trip <= FLOORS_POINTS

    print("\n  reads        %d   (%d df)" % (len(vals), df))
    print("  mean closes  %.2f points" % statistics.mean(vals))
    print("  between-seed SD  %.2f points" % sd)
    print("  2 × SD       %.2f points   vs the %.0f-point boundary"
          % (trip, FLOORS_POINTS))
    print("\n  %s" % ("✅ PASS — the table resolves its own boundaries"
                      if ok else
                      "⛔ FAIL — the bands did not resolve"))
    if not ok:
        print("     STOP BEFORE TRAINING. More chains, more seeds or wider "
              "bands is a RE-LOCK, not a mid-run adjustment (§3A).")

    rep = {"prereg": "docs/PREREG_IDF2_2026_09_26.md", "LOCK": "37363296",
           "arm": "C0", "marker_fn": None,
           "gap": gap, "blind_lag2": blind, "corpus_lag2": corpus,
           "reads": rows, "excluded": [{"file": f, "why": w} for f, w in bad],
           "n": len(vals), "df": df,
           "mean_closes_points": statistics.mean(vals),
           "between_seed_sd_points": sd,
           "trip_multiple": TRIP_MULTIPLE, "two_sd_points": trip,
           "floors_boundary_points": FLOORS_POINTS,
           "installs_boundary_points": INSTALLS_POINTS,
           "verdict": "PASS" if ok else "FAIL",
           "bands_raw_lag2": {
               "15_points": blind - 0.15 * gap,
               "35_points": blind - 0.35 * gap}}
    pathlib.Path(a.out).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print("\n  wrote %s" % a.out)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
