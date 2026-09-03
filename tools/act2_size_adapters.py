"""⛔⛔ HOW MANY ADAPTERS — power AT THE FLOOR, not at the ceiling.

    python tools/act2_size_adapters.py --sims 400 --boot 1000

⛔ THE CEILING TABLE CANNOT ANSWER THIS. Power at COMPLETE convergence is
unaffected by convergence-propensity heterogeneity by construction — if every
pair closes fully there is no propensity left to vary. So a sweep at the ceiling
reports the same numbers with and without `h`, and sizing off it silently drops
the very term the sizing is supposed to protect against.

⭐ The decision quantity is **power at `FLOOR_ka`** — the smallest effect the
design is required to detect — computed WITH per-pair propensity heterogeneity,
because the first version of this model assumed every pair closes by the same
delta and was therefore optimistic in the direction that matters.

⛔ THE POPULATION IS THE SURVIVING ONE. `s20620` is gone (it existed only on a
terminated box), so the ring is built from the adapters that actually exist plus
however many are to be trained. A ring labelled with a build nobody has is a
design that cannot be run.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from act2_a1_floor import (measure_real_structure, power_at,  # noqa: E402
                           ring)

#: ⛔ The six that are verified present on disk, by md5. `s20620` is NOT here.
ON_DISK = ("s20621", "s20622", "s20623", "t30001", "t30002", "t30003")

FLOOR_KA = 0.100          #: the locked floor, PREREG c0de41c7 §3
TARGET = 0.90             #: the brief's bar — margin, not the bare 0.80


def population(n_total):
    """`n_total` adapters: the six on disk, then newly-trained ones.

    ⭐ New builds get NEW NAMES (`s20624`…). ⛔ Never a retrained adapter wearing
    `s20620`'s name — a substitute under the lost build's label is the
    caveat-in-the-name failure, and GPU training is not bit-deterministic so it
    would not be that build in any case.
    """
    names = list(ON_DISK) + ["s2062%d" % (4 + i) for i in range(max(0, n_total - len(ON_DISK)))]
    return names[:n_total]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--reps", type=int, default=28)
    ap.add_argument("--seed", type=int, default=20260902)
    ap.add_argument("--delta", type=float, default=FLOOR_KA)
    ap.add_argument("--counts", default="6,7,8,9,10,12,14")
    ap.add_argument("--propensity", default="0.0,0.5")
    ap.add_argument("--out", default="runs/act2/adapter_sizing.json")
    a = ap.parse_args()

    s = dict(measure_real_structure(), n_reps=a.reps)
    counts = [int(x) for x in a.counts.split(",")]
    props = [float(x) for x in a.propensity.split(",")]

    print("ADAPTER SIZING — power at delta = %.3f ka (the locked FLOOR_ka)"
          % a.delta)
    print("  %d replicates/cloud · %d sims x %d bootstrap · MC se ~%.3f"
          % (a.reps, a.sims, a.boot, (0.25 / a.sims) ** 0.5))
    print("  ⛔ s20620 is LOST; the population is the 6 on disk + new builds")
    print("  target: power >= %.2f at the floor\n" % TARGET)

    hdr = "  %-9s %-7s" % ("adapters", "pairs")
    for pr in props:
        hdr += " %14s" % ("h=%.2f" % pr)
    print(hdr)

    rows, need = [], {pr: None for pr in props}
    for n in counts:
        line = "  %-9d %-7d" % (n, n)
        row = {"n_adapters": n, "n_pairs": n,
               "population": population(n), "power": {}}
        for pr in props:
            p, _w = power_at(a.delta, s, sims=a.sims, boot=a.boot,
                             seed=a.seed + 97 * n + int(pr * 100),
                             design=ring(n, population(n)), propensity_sd=pr)
            row["power"]["%.2f" % pr] = p
            flag = ""
            if p >= TARGET and need[pr] is None:
                need[pr], flag = n, " *"
            line += " %13.3f%s" % (p, flag)
        rows.append(row)
        print(line)

    print("\n  first count to reach %.2f:" % TARGET)
    for pr in props:
        k = need[pr]
        print("    h=%.2f -> %s adapters%s"
              % (pr, k if k else ">%d" % counts[-1],
                 "" if k is None else "  (train %d new)" % max(0, k - len(ON_DISK))))
    print("\n  ⛔ Size on the h>0 column. The h=0 column is the optimistic model "
          "whose assumption — every pair closes by the same delta — is the one\n"
          "     known to be wrong.")

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"delta": a.delta, "reps": a.reps, "sims": a.sims, "n_boot": a.boot,
         "target_power": TARGET, "on_disk": list(ON_DISK),
         "lost": ["s20620"], "rows": rows,
         "first_count_reaching_target": {("h=%.2f" % k): v
                                         for k, v in need.items()}},
        indent=2), encoding="utf-8")
    print("\n  wrote %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
