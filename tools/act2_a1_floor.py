"""⛔⛔ THE FLOOR A1 NEVER HAD — `FLOOR_ka`, for PREREG_POSITIVE_CONTROL_KA.

A1 (`W2(LIVE) − W2(YOKED)`) is red-proofed for SIGN, asymmetry, axis-scale use,
label hygiene, that one distribution gives a CI covering zero, and that the
bootstrap CAN exclude zero. ⛔ **None of those plants a convergence of KNOWN SIZE
and confirms A1 recovers it.** A2 has that calibration (planted convention of sd
0.10 ka ⇒ gain 0.0233); A5 has it (ΔD −5.08, ΔC +85.94). A1 does not — so the
positive control's decision rule ("above the demonstrated floor, not above zero")
had no number to lock.

⭐ This also separates two readings the project has never separated: the drift run
returned `+0.0803`, CI [−0.2856, +0.4637] — that is either *nothing moved* or
*A1 could not have seen it*, and those have opposite implications.

⛔ FIDELITY RULE: this calls the REAL `pair_delta` and the REAL
`cluster_bootstrap` from `act2_drift`, and the REAL `w2` underneath them. A
calibration that re-implements the estimator calibrates the re-implementation.

⛔ THE CLUSTER STRUCTURE IS SIMULATED, NOT ASSUMED AWAY. A centroid is drawn ONCE
PER ADAPTER and shared by every pair that adapter appears in — which is the whole
reason the unit of independence is the adapter. Drawing per-pair would make the
pairs independent by construction and report a floor that is too good.

    python tools/act2_a1_floor.py --sims 400 --boot 1000
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from act2_drift import cluster_bootstrap, load_pairs, pair_delta  # noqa: E402

PANEL = ("force:ka",)
COLD = pathlib.Path("runs/act2/cold_table_ka.json")
REAL_LOGS = pathlib.Path("runs/act2/drift/logs")

#: The registered design of PREREG_POSITIVE_CONTROL_KA §4.1: 6 pairs over 6
#: adapters as a BALANCED 6-CYCLE — every adapter has degree exactly 2, and the
#: cycle alternates the two adapter families so no pair is within-family only.
#: ⛔ Balance matters: a design where one adapter carries five pairs has fewer
#: effective clusters than its pair count suggests.
FAMILY_A = ("s20621", "s20622", "s20623")      # recipe_var
FAMILY_B = ("t30001", "t30002", "t30003")      # var_decomp
RING = (FAMILY_A[0], FAMILY_B[0], FAMILY_A[1],
        FAMILY_B[1], FAMILY_A[2], FAMILY_B[2])
DESIGN = tuple((RING[i], RING[(i + 1) % len(RING)]) for i in range(len(RING)))

#: ⛔ Finer near the bottom than the first pass. At 28 replicates the floor sits
#: lower than the 6/6/7 grid could resolve, and a coarse grid reports the
#: smallest GRID POINT that clears, not the floor — which would round the locked
#: threshold upward and make the gate harder than it needs to be.
DELTAS = (0.0, 0.0125, 0.025, 0.0375, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30, 0.40)
TARGET_POWER = 0.80

#: ⛔⛔ THE CEILING PROBE, AND IT IS THE POINT. Planted closure is capped by the
#: pair's own gap — two speakers cannot close by more than the distance between
#: them — so power does NOT rise without bound in delta. `float("inf")` plants
#: COMPLETE convergence: the LIVE gap goes to exactly zero. If the design cannot
#: reach the target power *there*, no achievable effect will reach it either, and
#: the floor does not exist at that design. A power curve read without its
#: ceiling invites "just plant a bigger effect", which is unavailable.
FULL = float("inf")

#: How many independently-trained adapters the ring design would need. Only 7
#: exist on disk; everything above that is a TRAINING COST, quoted so the
#: adapters-vs-abandon decision has a number rather than a feeling.
ADAPTER_SWEEP = (6, 8, 10, 12, 14, 18, 24)


def ring(n, names=None):
    """n adapters, n pairs, every adapter of degree exactly 2."""
    names = list(names or ["a%02d" % i for i in range(n)])[:n]
    return tuple((names[i], names[(i + 1) % n]) for i in range(n))


def real_ring(n):
    """A ring over the ACTUAL builds in the frozen cold table, families
    interleaved so no pair is within-family only.

    ⛔ The build names come from `cold_table_ka.json`, not from a list typed
    here — the cold table is the authority on which speakers exist.
    """
    cold = json.loads(COLD.read_text(encoding="utf-8"))
    builds = sorted(cold["locatability"].keys())
    fam_s = [b for b in builds if b.startswith("s")]
    fam_t = [b for b in builds if not b.startswith("s")]
    inter = [b for pair in zip(fam_s, fam_t + [None] * len(fam_s))
             for b in pair if b is not None]
    inter += [b for b in builds if b not in inter]
    if n > len(inter):
        raise SystemExit("asked for %d adapters; cold table has %d: %s"
                         % (n, len(inter), builds))
    return ring(n, inter)


def measure_real_structure():
    """⭐ The simulation's parameters are MEASURED off the real run, not chosen.

    Returns the within-speaker replicate sd (the noise a cloud carries) and the
    grand mean of `force:ka`. The BETWEEN-adapter sd is taken from the frozen
    cold table, never recomputed — it is the ruler ([C1]).
    """
    pairs, _skipped = load_pairs(REAL_LOGS, PANEL, self_pair=False)
    if not pairs:
        raise SystemExit("no real clouds found under %s" % REAL_LOGS)
    within, allvals, reps = [], [], []
    for cloud in pairs.values():
        for arr in cloud.values():
            a = np.asarray(arr, dtype=float).ravel()
            allvals.extend(a.tolist())
            reps.append(len(a))
            if len(a) > 1:
                within.append(a.std(ddof=1))
    cold = json.loads(COLD.read_text(encoding="utf-8"))
    # ⛔ Both are per-axis LISTS in the cold table (one entry per panel axis).
    # The panel is 1-wide here; `scale` stays a vector because that is what the
    # real `w2` is handed, and `sd_between` is its scalar for generating
    # centroids. Collapsing the vector would silently change the estimator.
    return {"sd_within": float(np.mean(within)),
            "mu0": float(np.mean(allvals)),
            "n_reps": int(round(float(np.mean(reps)))),
            "sd_between": float(np.asarray(cold["between_build_sd"]).ravel()[0]),
            "scale": np.asarray(cold["axis_scale"], dtype=float),
            "cold_sha": cold["sha256"][:8],
            "n_pairs_real": len(pairs)}


def one_run(rng, s, delta, design, propensity_sd=0.0):
    """Simulate ONE positive-control run at planted convergence `delta` (ka).

    ⛔ `delta` is the amount the two speakers' MARGINAL CENTROIDS close by in the
    LIVE arm. Each speaker moves delta/2 toward the other and they are not
    allowed to cross — a planted convergence that overshoots into a crossing is
    a divergence wearing the wrong label.
    """
    names = sorted({n for ab in design for n in ab})
    mu = {n: rng.normal(s["mu0"], s["sd_between"]) for n in names}   # ONCE per adapter

    def cloud(centre):
        # ⛔ Shape (n_reps, 1): the real clouds are one panel-vector per
        # replicate, and `w2` takes its mean/cov over axis 0.
        v = rng.normal(centre, s["sd_within"], s["n_reps"])
        return np.clip(v, 0.0, 1.0).reshape(-1, 1)

    deltas, adapters = [], []
    for x, y in design:
        # ⛔⛔ THE `h` TERM THE SIMULATION ORIGINALLY OMITTED. Every pair closing
        # by the SAME delta is the assumption that made this model optimistic:
        # real adapters may differ in HOW MUCH they converge, not only in where
        # they start. `propensity_sd` gives each pair its own closure, drawn
        # log-normally so it stays positive, with the same mean.
        d_pair = delta
        if propensity_sd > 0 and delta != FULL:
            d_pair = delta * float(rng.lognormal(-0.5 * propensity_sd ** 2,
                                                 propensity_sd))
        gap = mu[y] - mu[x]
        # ⛔ Closure is capped at |gap|/2 per speaker: they meet, they do not
        # cross. `delta=inf` is therefore COMPLETE convergence, not an infinite
        # effect — it is this design's ceiling.
        step = min(d_pair / 2.0, abs(gap) / 2.0) * np.sign(gap)
        d = pair_delta(cloud(mu[x] + step), cloud(mu[y] - step),   # LIVE: closed
                       cloud(mu[x]), cloud(mu[y]),                 # YOKED: as-is
                       s["scale"])
        deltas.append(d["delta"])
        adapters.append((x, y))
    return deltas, adapters


def power_at(delta, s, *, sims, boot, seed, design, propensity_sd=0.0):
    """Fraction of runs whose clustered CI excludes zero ON THE COUPLING SIDE.

    ⛔ Sign matters: an interval excluding zero from ABOVE is a divergence
    result, and counting it as detection would inflate power on a two-sided
    interval. Only `ci_upper < 0` counts.
    """
    rng = np.random.default_rng(seed)
    hits = wrong_side = 0
    for i in range(sims):
        deltas, adapters = one_run(rng, s, delta, design, propensity_sd)
        cb = cluster_bootstrap(deltas, adapters, n_boot=boot, seed=int(rng.integers(1 << 31)))
        lo, hi = cb["ci"]
        if hi < 0:
            hits += 1
        elif lo > 0:
            wrong_side += 1
    return hits / sims, wrong_side / sims


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20260901)
    ap.add_argument("--out", default="runs/act2/a1_floor.json")
    ap.add_argument("--adapters", type=int, default=None,
                    help="run the delta curve on a ring over N REAL builds")
    ap.add_argument("--reps", type=int, default=None,
                    help="replicates per cloud (default: as measured, 7)")
    ap.add_argument("--propensity-sd", type=float, default=0.0,
                    help="per-pair convergence-propensity heterogeneity (the h "
                         "term the first version of this model omitted)")
    ap.add_argument("--no-sweeps", action="store_true",
                    help="delta curve + ceiling only")
    a = ap.parse_args()

    s = measure_real_structure()
    design = DESIGN
    if a.adapters:
        design = real_ring(a.adapters)
    if a.reps:
        # ⛔ Override AFTER measuring, and print both, so the run states
        # plainly that its replicate count is a design choice and not the
        # number observed on disk.
        print("  ⚠ replicates overridden: measured %d -> design %d"
              % (s["n_reps"], a.reps))
        s = dict(s, n_reps=a.reps)
    print("A1 DETECTION FLOOR -- planted convergence, real estimator")
    print("  measured off the real run (%d pairs):" % s["n_pairs_real"])
    print("    within-speaker replicate sd : %.4f ka" % s["sd_within"])
    print("    grand mean force:ka         : %.4f" % s["mu0"])
    print("    replicates per cloud        : %d" % s["n_reps"])
    print("  frozen ruler (cold table):")
    print("    between-build sd            : %.4f ka" % s["sd_between"])
    print("  design: %d pairs / %d adapters, balanced ring, families alternating"
          % (len(design), len({n for ab in design for n in ab})))
    print("    %s" % " ".join("%s|%s" % p for p in design))
    print("  %d sims x %d bootstrap per delta\n" % (a.sims, a.boot))

    print("  %-10s %-14s %8s %10s" % ("delta ka", "in sd units", "power", "wrong-side"))
    rows = []
    floor = None
    for d in DELTAS:
        p, w = power_at(d, s, sims=a.sims, boot=a.boot, seed=a.seed, design=design)
        rows.append({"delta_ka": d, "delta_sd": d / s["sd_between"],
                     "power": p, "wrong_side": w})
        print("  %-10.3f %-14.3f %8.3f %10.3f" % (d, d / s["sd_between"], p, w))
        if floor is None and d > 0 and p >= TARGET_POWER:
            floor = d

    # ── the ceiling ────────────────────────────────────────────────────────
    ceil_p, ceil_w = power_at(FULL, s, sims=a.sims, boot=a.boot,
                              seed=a.seed, design=design,
                              propensity_sd=a.propensity_sd)
    print("  %-10s %-14s %8.3f %10.3f" % ("COMPLETE", "(gap -> 0)", ceil_p, ceil_w))

    print()
    if floor is None:
        print("  FLOOR_ka: DOES NOT EXIST AT THIS DESIGN.")
        print("  Power CEILING at complete convergence = %.3f, below the %.2f "
              "target." % (ceil_p, TARGET_POWER))
        print("  => the registered 6-pair/6-adapter design cannot clear its own")
        print("     gate even if the two speakers converge COMPLETELY.")
    else:
        print("  FLOOR_ka = %.3f ka  (= %.2f between-build sd), ceiling %.3f"
              % (floor, floor / s["sd_between"], ceil_p))
    print("  false-positive rate at delta=0: %.3f (nominal 0.025 one-sided)"
          % rows[0]["power"])

    sweep, reps_sweep, need = [], [], None
    if not a.no_sweeps:
        # ── what design WOULD clear it ─────────────────────────────────────
        print("\n  ADAPTERS NEEDED -- power at COMPLETE convergence, ring design")
        print("  ⛔ clusters = ADAPTERS. More pairs from the same adapters do not"
              " buy power.")
        print("  %-10s %-8s %8s" % ("adapters", "pairs", "power"))
        for n in ADAPTER_SWEEP:
            p, _w = power_at(FULL, s, sims=a.sims, boot=a.boot,
                             seed=a.seed + n, design=ring(n),
                             propensity_sd=a.propensity_sd)
            sweep.append({"n_adapters": n, "n_pairs": n, "power_complete": p})
            flag = ""
            if p >= TARGET_POWER and need is None:
                need, flag = n, "  <= first to clear"
            print("  %-10d %-8d %8.3f%s" % (n, n, p, flag))
        print("\n  ON DISK: 7 adapters. NEEDED for %d%% power at COMPLETE "
              "convergence: %s" % (int(TARGET_POWER * 100),
                                   ("%d" % need) if need
                                   else ">%d" % ADAPTER_SWEEP[-1]))

        # ── REPLICATES: the cheap lever, or not a lever at all ─────────────
        # ⛔⛔ THIS IS THE DECISION-RELEVANT SWEEP. More ADAPTERS is a TRAINING
        # spend; more REPLICATES is only more inference on the adapters already
        # on disk. Which one buys power is exactly the unresolved `h` question
        # (h = 0.2519, CI [0.0000, 0.4033] — lower bound zero, so
        # replicate-limited is not excluded). If power is flat in replicates,
        # the limit is adapter heterogeneity and no extra inference reaches it.
        print("\n  REPLICATES PER CLOUD -- power at COMPLETE convergence")
        print("  %-10s %-10s %8s" % ("adapters", "reps", "power"))
        for n_ad in (6, 7):
            for r in (7, 14, 28, 56):
                s_r = dict(s, n_reps=r)
                p, _w = power_at(FULL, s_r, sims=a.sims, boot=a.boot,
                                 seed=a.seed + 1000 * n_ad + r,
                                 design=ring(n_ad),
                                 propensity_sd=a.propensity_sd)
                reps_sweep.append({"n_adapters": n_ad, "n_reps": r,
                                   "power_complete": p})
                print("  %-10d %-10d %8.3f" % (n_ad, r, p))

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    struct = {k: (v.tolist() if isinstance(v, np.ndarray) else v)
              for k, v in s.items()}
    out.write_text(json.dumps(
        {"structure": struct, "design": [list(p) for p in design], "n_reps_design": s["n_reps"],
         "sims": a.sims, "n_boot": a.boot, "seed": a.seed,
         "target_power": TARGET_POWER, "curve": rows,
         "power_ceiling_complete_convergence": ceil_p,
         "adapter_sweep_at_complete_convergence": sweep,
         "replicate_sweep_at_complete_convergence": reps_sweep,
         "propensity_sd": a.propensity_sd,
         "monte_carlo_se_note": "power se = sqrt(p(1-p)/sims); ~0.02 at p=0.8, sims=400",
         "adapters_on_disk": 7,
         "adapters_needed_for_target": need,
         "floor_ka": floor,
         "floor_sd": (floor / s["sd_between"]) if floor else None,
         "estimand": "delta = W2(LIVE) - W2(YOKED); negative = coupling",
         "note": "centroid drawn once per ADAPTER; detection requires ci_upper<0"},
        indent=2), encoding="utf-8")
    print("\n  wrote %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
