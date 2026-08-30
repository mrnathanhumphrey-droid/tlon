"""INJECTION-POOL GATE — is the pool a THIRD SPEAKER? $0, pre-declared, halting.

Spec: docs/SPEC_TWO_SPEAKER_DRIFT_2026_08_30.md §4.3

⛔⛔ THE CONFOUND. Injections are provocations both speakers receive. If the pool
sits away from the speakers on a panel axis, BOTH are pulled toward it, they end
up more alike, and the distance shrinks. That is **co-tropism toward a common
stimulus**, not coupling, and on the distance metric it is indistinguishable
from mutual convergence.

⭐ BUT THE MECHANISM IS NARROWER THAN "ANY BIASED POOL POISONS THE RUN", AND
GETTING IT RIGHT CHANGES THE DEFENCE:

  · The drift estimand is **LIVE − YOKED, paired**. A pull that acts equally in
    both conditions SUBTRACTS OUT — that is what the yoked design is for. The
    yoked partner is a recording of the LIVE partner, so it carries the same
    injection influence through the same channel.
  · What does NOT cancel, and is the real exposure:
      1. ⛔⛔ **PANEL RE-CERTIFICATION.** Contamination is between-build sd over
         within-conversation movement. Every build sees the SAME injections, so
         a biased pool compresses between-build sd and contamination looks
         better than it is. **The panel would be certified on poisoned data.**
      2. **The COLD baseline.** A pool that drags both builds toward itself
         compresses the starting distance and shrinks the dynamic range of the
         whole measurement.
      3. A pool that is not BETWEEN the speakers at all but off to one side —
         a third speaker sitting outside the population.

⚠️ WHAT WAS DROPPED, AND WHY, BECAUSE IT LOOKS LIKE A WEAKENED GUARD: the first
draft ALSO halted on per-pair asymmetry, on the reasoning that a pool nearer to
A drags B toward A. **That threat largely cancels.** Injections are yoked, so the
pool pulls A and B identically in LIVE and in YOKED, and the estimand is their
difference. The criterion was also ill-behaved — no single pool can sit at the
midpoint of all 21 pairs, so its "PASS" was unreachable by construction. It is
demoted to a reported diagnostic (see `OUTSIDE_SEGMENT_FRACTION`). ⛔ This is a
demotion by argument, not a threshold relaxed until the data passed.

⇒ THREE DEFENCES, IN ORDER OF STRENGTH:
   1. **EXCLUSION** — never measure an injected turn (`measurable_turns()`).
      Structural, and independent of whether the bias is visible on the axes.
   2. **A NO-INJECTION ARM** for panel re-certification, so contamination is
      never computed on injected material at all.
   3. **THIS GATE** — bound the bias that survives, on the panel axes, with a
      pre-declared halt.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from act2_observable_screen import OBSERVABLES, scenes_of                # noqa: E402
from act2_ranking_stability import BUILDS                                # noqa: E402

#: ⭐ The Stage-1 admitted panel. Drift is measured on these axes, so these are
#: the axes on which an injection pool can do damage.
PANEL = ("root TTR", "force:ka", "nodes/scene")

#: The pool must sit within this many BETWEEN-BUILD sds of the build mean on
#: every panel axis. Between-build sd is the right yardstick because it is the
#: scale of the distance the experiment is trying to resolve.
Z_MAX = 1.5

#: ⭐ ASYMMETRY IS A REPORTED DIAGNOSTIC, NOT A HALT — and the demotion is
#: reasoned, not a threshold tuned until the data passed.
#:
#: The first draft halted on |d(pool,A) − d(pool,B)| / d(A,B). Two things are
#: wrong with that. It is ill-behaved: for a pair lying in the same direction
#: from the pool the ratio approaches 1 however central the pool is, and no
#: single pool can sit at the midpoint of all 21 pairs, so "PASS" was
#: unreachable by construction. More importantly the threat is weaker than it
#: looks: **injections are yoked, so the pool pulls A and B identically in LIVE
#: and in YOKED, and its differential pull largely cancels in LIVE − YOKED**,
#: which is the estimand. What does NOT cancel is compression of the COLD
#: baseline and of the between-build sd used for re-certification — and those
#: are what CENTRALITY guards.
#:
#: What survives as a halt is only the pathological case: a pool that is not
#: BETWEEN the speakers at all but off to one side, measured by the projection
#: t of the pool onto the A→B axis. `t ∈ [0,1]` means the pool projects between
#: them; outside means it sits beyond one of them.
OUTSIDE_SEGMENT_FRACTION = 0.50


def build_values():
    """Per build, the mean of each panel observable over its exchanges."""
    out = {}
    for name, d, pat in BUILDS:
        scs = []
        for f in sorted(pathlib.Path(d).glob(pat)):
            data = json.loads(f.read_text(encoding="utf-8"))
            s = scenes_of(data.get("transcript_interacting") or [])
            if len(s) >= 8:
                scs.append(s)
        if not scs:
            continue
        vals = {}
        for o in PANEL:
            v = [x for s in scs if (x := OBSERVABLES[o](s)) is not None]
            if v:
                vals[o] = sum(v) / len(v)
        if len(vals) == len(PANEL):
            out[name] = vals
    return out


def pool_values(pool_surfaces, chunk: int = 40, seed: int = 20260830):
    """⛔⛔ THE POOL MUST BE CHARACTERISED AT THE SAME SAMPLE SIZE AS THE BUILDS.

    `root TTR` is distinct-roots / total-roots, and TTR FALLS MECHANICALLY AS n
    GROWS. Scoring a 140-surface pool against builds scored on ~40-surface
    exchanges made the pool look 43.8 sds off-centre — an artefact of the sample
    size, not a property of the pool. So the pool is cut into chunks the size of
    an exchange and the per-chunk values averaged, exactly as `build_values()`
    averages over exchanges.
    """
    scs = scenes_of(list(pool_surfaces))
    if len(scs) < chunk:
        raise ValueError(
            "pool has %d parseable scenes, fewer than the %d-scene chunk the "
            "builds are characterised at; a pool that cannot be scored "
            "like-for-like cannot be gated" % (len(scs), chunk))
    rng = random.Random(seed)
    idx = list(range(len(scs)))
    rng.shuffle(idx)
    chunks = [[scs[i] for i in idx[s:s + chunk]]
              for s in range(0, len(idx) - chunk + 1, chunk)]
    out = {}
    for o in PANEL:
        vals = [v for c in chunks if (v := OBSERVABLES[o](c)) is not None]
        out[o] = sum(vals) / len(vals)
    return out


def centrality(pool, builds):
    """z of the pool against the build distribution, per axis."""
    rows = {}
    for o in PANEL:
        vals = [b[o] for b in builds.values()]
        mu = sum(vals) / len(vals)
        sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
        z = float("inf") if not sd else abs(pool[o] - mu) / sd
        rows[o] = {"pool": pool[o], "build_mean": mu, "build_sd": sd, "z": z,
                   "ok": bool(z <= Z_MAX)}
    return rows


def _d(x, y, scale):
    return (sum(((x[o] - y[o]) / scale[o]) ** 2 for o in PANEL)) ** 0.5


def asymmetry(pool, builds):
    """Where the pool projects onto each A→B axis.

    `t = ((pool−A)·(B−A)) / |B−A|²`, in between-build-sd units.
    `t ≈ 0.5` sits at the midpoint; `t ∈ [0,1]` is between the two speakers;
    outside means the pool is beyond one of them, which is the pathological
    case a single central pool should not produce.
    """
    scale = {}
    for o in PANEL:
        vals = [b[o] for b in builds.values()]
        sd = statistics.stdev(vals) if len(vals) > 1 else 1.0
        scale[o] = sd or 1.0
    names = sorted(builds)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            A, B = builds[a], builds[b]
            num = sum(((pool[o] - A[o]) / scale[o]) * ((B[o] - A[o]) / scale[o])
                      for o in PANEL)
            den = sum(((B[o] - A[o]) / scale[o]) ** 2 for o in PANEL)
            t = float("inf") if not den else num / den
            rows.append({"pair": "%s|%s" % (a, b),
                         "d_ab": _d(A, B, scale), "t": t,
                         "outside": bool(not (0.0 <= t <= 1.0))})
    return rows


def verdict_of(cent, asym) -> str:
    """⛔ CENTRALITY HALTS. Asymmetry halts only in the pathological case."""
    if not all(v["ok"] for v in cent.values()):
        return "HALT_CENTRALITY"
    if asym:
        out = sum(r["outside"] for r in asym) / len(asym)
        if out > OUTSIDE_SEGMENT_FRACTION:
            return "HALT_NOT_BETWEEN"
    return "PASS"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True,
                    help="JSON file: a list of Tlön surfaces")
    ap.add_argument("--out", default="runs/act2/injection_gate.json")
    a = ap.parse_args()

    surfaces = json.loads(pathlib.Path(a.pool).read_text(encoding="utf-8"))
    builds = build_values()
    pool = pool_values(surfaces)

    print("INJECTION-POOL GATE — is the pool a third speaker?")
    print("=" * 78)
    print("  panel %s" % (PANEL,))
    print("  %d builds · Z_MAX %.2f · outside-fraction halt %.2f"
          % (len(builds), Z_MAX, OUTSIDE_SEGMENT_FRACTION))
    print("  ⚠️ RUN ON WINDOW-1 TRANSCRIPTS. Must be RE-RUN in the asymmetric "
          "regime\n     before it licenses anything — a pool neutral at depth 1 "
          "may not be at depth.")

    cent = centrality(pool, builds)
    print("\n── centrality (pool vs the build distribution) ──")
    print("  %-14s %9s %11s %9s %7s" % ("axis", "pool", "build mean",
                                        "build sd", "z"))
    for o, r in cent.items():
        print("  %-14s %9.4f %11.4f %9.4f %7.2f%s"
              % (o, r["pool"], r["build_mean"], r["build_sd"], r["z"],
                 "" if r["ok"] else "   ⛔"))

    asym = asymmetry(pool, builds)
    out_n = sum(r["outside"] for r in asym)
    print("\n── projection onto each A→B axis (DIAGNOSTIC — see the constant) ──")
    print("  %d pairs · %d project OUTSIDE the segment" % (len(asym), out_n))
    for r in sorted(asym, key=lambda x: -abs(x["t"] - 0.5))[:5]:
        print("  %-18s d(A,B) %5.2f · t %+.2f%s"
              % (r["pair"], r["d_ab"], r["t"],
                 "   ⛔ not between" if r["outside"] else ""))

    verdict = verdict_of(cent, asym)
    print("\n" + "=" * 78)
    if verdict == "HALT_CENTRALITY":
        print("  ⛔⛔ HALT — the pool is off-centre on a panel axis. It is a "
              "third speaker and\n     would pull both builds toward it. "
              "Pre-declared: find a native pool or\n     run without "
              "injections. Do NOT proceed and 'watch for it'.")
    elif verdict == "HALT_NOT_BETWEEN":
        print("  ⛔⛔ HALT — the pool is not BETWEEN the speakers; for most pairs "
              "it sits\n     beyond one of them. That is a third speaker off to "
              "one side.")
    else:
        print("  ⭐ PASS — central on every panel axis (%d/%d pairs project "
              "outside, under the\n     %.0f%% halt). The projection spread is a "
              "DIAGNOSTIC, not a gate: injections\n     are yoked, so the pool's "
              "pull is present in LIVE and YOKED alike and largely\n     cancels "
              "in their difference."
              % (out_n, len(asym), 100 * OUTSIDE_SEGMENT_FRACTION))

    print("\n⛔ THIS GATE IS THE WEAKEST OF THE THREE DEFENCES. It bounds only "
          "the bias\n   visible on the panel axes. The structural ones are: "
          "measure NO injected turn\n   (`measurable_turns()`), and re-certify "
          "the panel on a NO-INJECTION arm.")

    out = {"panel": list(PANEL), "z_max": Z_MAX, "outside_fraction": OUTSIDE_SEGMENT_FRACTION,
           "pool": pool, "builds": builds, "centrality": cent,
           "asymmetry": asym, "verdict": verdict,
           "regime": "window-1 (PROVISIONAL — re-run asymmetric)"}
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                   encoding="utf-8", newline="")
    print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
