"""FORCE-FIDELITY — THE GATE. A random painter fails it; extent cannot. $0 local.

⛔⛔ WHY THIS EXISTS. `degeneracy_guard` (extent) is **maxed by noise** under the
locality architecture — measured 0/200 fires at depths 8/20/40 on a painter that
ignores the prior turn entirely. Extent has no discriminating power, so it is a
tripwire. The only structure the corpus carries is force→force, so the only test
that can show the training took is whether the realised force-transition matrix
reproduces the map.

⭐⭐ THREE BRANCHES, NOT TWO — and this is the part a two-way test would get
wrong. The pre-declared reading has "matches the map" and "at chance". There is a
**third** outcome and it is the LIKELY one: an LLM asked to be uniform in four of
five rows will not be uniform, it will mode-collapse. That model has real
structure that is NOT the map, and a χ²-against-chance alone would score it as a
SUCCESS. So both distances are always reported:

    d(observed, MAP)            — did it learn the intended structure?
    d(observed, INDEPENDENCE)   — did it learn ANY structure?

    near MAP, far from INDEP   → FIDELITY          (the training took)
    far from MAP, near INDEP   → CHANCE            (learned nothing)
    far from MAP, far from INDEP → ⚠️ THIRD THING   (structure, but not ours)
    near both                  → ⛔ DEGENERATE TEST (map ≈ independence here)

⚠️ AND IT REFUSES TO REPORT AN UNDERPOWERED NULL. With one forced cell, a
40-turn exchange yields ~6.7 `ki` priors — enough in aggregate, **not** enough
stratified by depth (~2.2 per bucket, best-case p ≈ 0.087, unreachable even with
perfect learning). A null from that is a statement about the instrument.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.discourse import force_map as FM                     # noqa: E402

#: Below this many observations in a forced row, a null is uninterpretable.
MIN_FORCED_OBSERVATIONS = 20

#: ⛔⛔ THERE ARE NO ABSOLUTE THRESHOLDS HERE, AND THE FIRST VERSION HAD TWO.
#: Hand-picked bands (near 0.15 / far 0.30) read ⚠️UNRESOLVED on a corpus
#: generated FROM THE MAP, whose forced row scored a literal 0.000. Two separate
#: causes, both invisible to a picked constant:
#:
#:   1. **the ceiling** — the map is mostly uniform, so it sits close to
#:      independence by construction. `force_map.separation()` computes the max
#:      achievable distance: **0.222**, not 1.0. A `far` of 0.30 was unreachable.
#:   2. **the floor** — a PERFECT model cannot score d_map = 0 on a finite
#:      sample. At ~100 observations per row the multinomial noise alone puts
#:      d_map near 0.08.
#:
#: ⇒ Both bands are SIMULATED from the map and from independence at the OBSERVED
#: row sizes. The verdict asks "is this consistent with X?", never "is this below
#: a number someone chose".
NULL_TRIALS = 600
NULL_PERCENTILE = 95


def _tv(observed_row: dict, expected_row: dict) -> float:
    n = sum(observed_row.values())
    if not n:
        return float("nan")
    return 0.5 * sum(abs(observed_row[f] / n - expected_row[f])
                     for f in FM.ORDER)


def distances(counts: dict) -> dict:
    """Row-mass-weighted total variation from the MAP and from INDEPENDENCE."""
    total = sum(counts.values())
    if not total:
        raise SystemExit("⛔ no transitions")
    marg = {f: sum(counts.get((p, f), 0) for p in FM.ORDER) / total
            for f in FM.ORDER}
    d_map = d_ind = 0.0
    rows = {}
    for p in FM.ORDER:
        obs = {f: counts.get((p, f), 0) for f in FM.ORDER}
        n = sum(obs.values())
        if not n:
            continue
        dm, di = _tv(obs, FM.row(p)), _tv(obs, marg)
        rows[p] = {"n": n, "d_map": dm, "d_independence": di,
                   "verdict": FM.verdict(p),
                   "observed": {f: obs[f] / n for f in FM.ORDER}}
        d_map += (n / total) * dm
        d_ind += (n / total) * di
    return {"d_map": d_map, "d_independence": d_ind, "rows": rows,
            "marginal": marg, "total": total}


def _simulate(row_ns: dict, source, *, trials: int, seed: int) -> dict:
    """Draw synthetic matrices from `source` at the OBSERVED row sizes and return
    the null distributions of both distances. ⭐ Calibration, not assumption."""
    import random as _r
    rng = _r.Random(seed)
    dm, di = [], []
    for _ in range(trials):
        counts = {}
        for p, n in row_ns.items():
            probs = source(p)
            draw = rng.choices(FM.ORDER, weights=[probs[f] for f in FM.ORDER],
                               k=n)
            for f in draw:
                counts[(p, f)] = counts.get((p, f), 0) + 1
        d = distances(counts)
        dm.append(d["d_map"])
        di.append(d["d_independence"])
    q = lambda xs: sorted(xs)[min(len(xs) - 1,                     # noqa: E731
                                 int(len(xs) * NULL_PERCENTILE / 100))]
    return {"d_map_p": q(dm), "d_independence_p": q(di)}


def verdict(d: dict, *, seed: int = 0) -> tuple[str, str]:
    """⭐ A BRANCH PER OUTCOME, THE LOUD FALLBACK WRITTEN FIRST, AND BOTH BANDS
    SIMULATED AT THIS SAMPLE SIZE RATHER THAN CHOSEN."""
    dm, di = d["d_map"], d["d_independence"]
    row_ns = {p: r["n"] for p, r in d["rows"].items()}
    forced_n = sum(r["n"] for r in d["rows"].values()
                   if r["verdict"] == FM.FORCED)
    if forced_n < MIN_FORCED_OBSERVATIONS:
        return ("UNDERPOWERED",
                f"only {forced_n} observations in forced row(s); "
                f"{MIN_FORCED_OBSERVATIONS} needed. A null here is a statement "
                "about the instrument, not the model. Run more exchanges.")

    sep = FM.separation()
    under_map = _simulate(row_ns, FM.row, trials=NULL_TRIALS, seed=seed)
    marg = d["marginal"]
    under_ind = _simulate(row_ns, lambda _p: marg, trials=NULL_TRIALS,
                          seed=seed + 1)
    ok_map = dm <= under_map["d_map_p"]
    ok_ind = di <= under_ind["d_independence_p"]
    band = (f"[sample-calibrated: consistent-with-map iff d_map ≤ "
            f"{under_map['d_map_p']:.3f}; consistent-with-independence iff "
            f"d_indep ≤ {under_ind['d_independence_p']:.3f}; "
            f"max achievable separation {sep:.3f}]")

    if ok_map and not ok_ind:
        return ("FIDELITY",
                f"consistent with the map (d_map={dm:.3f}) and NOT with "
                f"independence (d_indep={di:.3f}). The force-handoff was "
                f"learned. {band}")
    if ok_ind and not ok_map:
        return ("CHANCE",
                f"consistent with independence (d_indep={di:.3f}) and not with "
                f"the map (d_map={dm:.3f}). No coupling — what a random painter "
                "scores. Per the locked reading this is the real 'flat space is "
                "flat' result: the connection carries nothing, and the next work "
                f"is a substrate/connection fix. {band}")
    if not ok_map and not ok_ind:
        return ("⚠️ THIRD THING",
                f"consistent with NEITHER the map (d_map={dm:.3f}) nor "
                f"independence (d_indep={di:.3f}). The model has real structure "
                "that is not the map — most likely mode-collapse on the uniform "
                f"rows. A chance-only test would have scored this a SUCCESS. {band}")
    return ("⛔ DEGENERATE TEST",
            f"consistent with BOTH the map and independence at this sample size "
            f"— the test cannot separate them and decides nothing. Run more "
            f"exchanges. {band}")


def by_depth(chains, buckets: int = 3) -> list[dict]:
    """Fidelity vs turn index — does the massless connection hold with depth?"""
    n = max(len(c) for c in chains)
    edges = [round(n * i / buckets) for i in range(buckets + 1)]
    out = []
    for b in range(buckets):
        lo, hi = edges[b], edges[b + 1]
        counts: dict = {}
        for ch in chains:
            for i, t in enumerate(ch):
                if lo <= i < hi and t.get("prior_force"):
                    k = (t["prior_force"], t["force"])
                    counts[k] = counts.get(k, 0) + 1
        if not counts:
            continue
        d = distances(counts)
        v, why = verdict(d)
        out.append({"turns": f"{lo}-{hi - 1}", "d_map": d["d_map"],
                    "d_independence": d["d_independence"],
                    "verdict": v, "why": why})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chains", required=True,
                    help="JSON: [[{surface, force, prior_force}, ...], ...]")
    ap.add_argument("--buckets", type=int, default=3)
    a = ap.parse_args()

    chains = json.loads(pathlib.Path(a.chains).read_text(encoding="utf-8"))
    counts: dict = {}
    for ch in chains:
        for t in ch:
            if t.get("prior_force"):
                k = (t["prior_force"], t["force"])
                counts[k] = counts.get(k, 0) + 1

    d = distances(counts)
    v, why = verdict(d)
    print(FM.describe())
    print(f"\nFORCE-FIDELITY · {len(chains)} chains · {d['total']} transitions")
    print(f"  d(observed, MAP)          = {d['d_map']:.4f}")
    print(f"  d(observed, INDEPENDENCE) = {d['d_independence']:.4f}")
    print(f"\n  VERDICT: {v}\n  {why}\n")
    print(f"  {'prior':>6} {'n':>6} {'d_map':>8} {'d_indep':>8}  verdict")
    for p, r in d["rows"].items():
        print(f"  {p:>6} {r['n']:>6} {r['d_map']:>8.3f} "
              f"{r['d_independence']:>8.3f}  {r['verdict']}")

    print("\n  ── fidelity vs depth ──")
    for b in by_depth(chains, a.buckets):
        print(f"    turns {b['turns']:>8}: d_map {b['d_map']:.3f}  "
              f"d_indep {b['d_independence']:.3f}  {b['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ══ Q1 / Q2 — THE COUPLING, INSTRUMENTED RATHER THAN ANNOTATED ═══════════
def _row_band(n: int, source: dict, reference: dict, *, trials: int,
              seed: int) -> float:
    """p95 of TV(draw-from-`source`, `reference`) at row size `n`."""
    import random as _r
    rng = _r.Random(seed)
    out = []
    for _ in range(trials):
        draw = rng.choices(FM.ORDER, weights=[source[f] for f in FM.ORDER], k=n)
        obs = {f: 0 for f in FM.ORDER}
        for f in draw:
            obs[f] += 1
        out.append(_tv(obs, reference))
    return sorted(out)[min(len(out) - 1, int(len(out) * NULL_PERCENTILE / 100))]


def q1_two_null(counts: dict, *, prior: str = "ki", seed: int = 0) -> dict:
    """⛔⛔ Q1 IS COUPLED TO Q2 THROUGH THE SHARED MARGINAL, SO IT IS TESTED
    AGAINST BOTH.

    Reading the `ki` row per-row protects its OBSERVED distribution from
    aggregate contamination — but the NULL it is judged against is built from the
    marginal, and **mode-collapse in the 24 uniform rows moves that marginal.**
    So the row is tested twice:

      DESIGN null   — the stationary marginal the map implies if the model holds
                      uniform (ka 1/3, rest 1/6).
      REALIZED null — the marginal the model actually produced, collapse and all.

    A clean Q1 positive requires beating **both**. Beating design but not
    realized means the apparent fidelity is partly an artifact of a collapsed
    marginal — Q1 CONFOUNDED BY Q2, named before the run so it cannot be quietly
    read as a win.

    ⚠️ THE VERDICT KEYS ON BEATING THE NULLS, NOT ON MATCHING THE MAP. The forced
    row is deterministic, so `d(observed, map)` has ZERO tolerance — a model at
    95 % `ka` would read as "not the map" and be thrown to THIRD THING despite
    obviously transmitting. Map-distance is reported as a DIAGNOSTIC number, not
    a branch condition.
    """
    obs = {f: counts.get((prior, f), 0) for f in FM.ORDER}
    n = sum(obs.values())
    if n < MIN_FORCED_OBSERVATIONS:
        return {"verdict": "UNDERPOWERED", "n": n,
                "why": f"{n} observations in the {prior!r} row; "
                       f"{MIN_FORCED_OBSERVATIONS} needed. A null here is a "
                       "statement about the instrument. Run more exchanges."}

    design = FM.stationary()
    total = sum(counts.values())
    realized = {f: sum(counts.get((p, f), 0) for p in FM.ORDER) / total
                for f in FM.ORDER}

    tv_d, tv_r = _tv(obs, design), _tv(obs, realized)
    band_d = _row_band(n, design, design, trials=NULL_TRIALS, seed=seed)
    band_r = _row_band(n, realized, realized, trials=NULL_TRIALS, seed=seed + 1)
    beats_d, beats_r = tv_d > band_d, tv_r > band_r

    out = {"n": n, "observed": {f: obs[f] / n for f in FM.ORDER},
           "d_design": tv_d, "band_design": band_d, "beats_design": beats_d,
           "d_realized": tv_r, "band_realized": band_r, "beats_realized": beats_r,
           "d_map_diagnostic": _tv(obs, FM.row(prior)),
           "design_marginal": design, "realized_marginal": realized}

    if beats_d and beats_r:
        out.update(verdict="Q1 CLEAN POSITIVE",
                   why=f"{prior}→ beats BOTH nulls (design {tv_d:.3f}>{band_d:.3f}, "
                       f"realized {tv_r:.3f}>{band_r:.3f}). Force transmits, and "
                       "the result is robust to whatever the uniform rows did.")
    elif beats_d and not beats_r:
        out.update(verdict="⚠️ Q1 CONFOUNDED BY Q2",
                   why=f"{prior}→ beats the DESIGN null ({tv_d:.3f}>{band_d:.3f}) "
                       f"but NOT the REALIZED one ({tv_r:.3f}≤{band_r:.3f}). The "
                       "apparent fidelity is partly an artifact of a marginal "
                       "that mode-collapse moved. NOT a force-transmission "
                       "result — read Q2 first.")
    elif not beats_d:
        out.update(verdict="Q1 NULL",
                   why=f"{prior}→ does not beat the design null "
                       f"({tv_d:.3f}≤{band_d:.3f}). Force does not transmit even "
                       "where forced and learnable. This is the real "
                       "'flat space is flat' result.")
    else:
        out.update(verdict="⚠️⚠️ Q1 UNRESOLVED",
                   why=f"beats the realized null but not the design one "
                       f"(d_design={tv_d:.3f}≤{band_d:.3f}, "
                       f"d_realized={tv_r:.3f}>{band_r:.3f}) — not a shape either "
                       "branch anticipated. Report the numbers, not a verdict.")
    return out


def q2_rows(counts: dict, *, seed: int = 0) -> dict:
    """Q2 — can the substrate hold a flat prior? Each UNIFORM row on its own.

    ⭐ A THIRD THING here is a FOUNDATION FINDING, not a run failure: RULING 12's
    emergent-convention design assumes the model starts uniform on undetermined
    rows. If it cannot, there is no flat prior for emergence to be measured
    against, and the next work is a substrate fix — not an abandonment of the
    uniform target, which is what RULING 12 requires be trainable.
    """
    total = sum(counts.values())
    realized = {f: sum(counts.get((p, f), 0) for p in FM.ORDER) / total
                for f in FM.ORDER}
    out = {}
    for prior in FM.ORDER:
        if FM.verdict(prior) != FM.UNIFORM:
            continue
        obs = {f: counts.get((prior, f), 0) for f in FM.ORDER}
        n = sum(obs.values())
        uni = FM.row(prior)
        if n < MIN_FORCED_OBSERVATIONS:
            out[prior] = {"n": n, "verdict": "UNDERPOWERED"}
            continue
        tv_u, tv_i = _tv(obs, uni), _tv(obs, realized)
        band_u = _row_band(n, uni, uni, trials=NULL_TRIALS, seed=seed)
        band_i = _row_band(n, realized, realized, trials=NULL_TRIALS,
                           seed=seed + 1)
        ok_u, ok_i = tv_u <= band_u, tv_i <= band_i
        # ⛔⛔ THE UNIFORM TEST DECIDES FIRST, AND THIS ORDERING IS THE FIX.
        # An earlier version branched on the realized-marginal comparison and
        # reported a model 75 % collapsed onto `ka` as CHANCE — "✅ the uniform
        # rows hold flat". **Mode-collapse had moved the very baseline Q2
        # measures against**, so the collapsed rows matched the collapsed
        # marginal and made themselves invisible. That is Nate's Q1 bleed
        # exactly, one question over, built in after being warned about it.
        # Q2 asks ONE thing — can this row hold uniform — and not-uniform is the
        # finding however it fails.
        if ok_u:
            v = "HOLDS FLAT"
        elif ok_i:
            v = "⚠️ COLLAPSED TO A GLOBAL PRIOR"
        else:
            v = "⚠️ THIRD THING"
        out[prior] = {"n": n, "d_uniform": tv_u, "band_uniform": band_u,
                      "d_independence": tv_i, "band_independence": band_i,
                      "verdict": v, "holds_flat": ok_u,
                      "observed": {f: obs[f] / n for f in FM.ORDER}}
    # ⭐ BOTH non-uniform branches are foundation findings. Counting only
    # THIRD THING was the false green.
    failed = [p for p, r in out.items() if r.get("holds_flat") is False]
    global_prior = [p for p, r in out.items()
                    if r["verdict"] == "⚠️ COLLAPSED TO A GLOBAL PRIOR"]
    invented = [p for p, r in out.items() if r["verdict"] == "⚠️ THIRD THING"]
    return {"rows": out, "n_failed": len(failed),
            "collapsed_to_global_prior": global_prior, "invented": invented,
            "foundation": (
                "⚠️ FOUNDATION FINDING — the substrate cannot hold a flat prior "
                f"on {len(failed)} of {len(out)} uniform rows "
                f"({len(global_prior)} collapsed onto one global distribution, "
                f"{len(invented)} invented per-row structure). RULING 12's "
                "emergent-convention measurement is NOT well-posed until this "
                "is fixed: there is no flat prior for emergence to be measured "
                "against. Next work is a substrate fix, NOT abandoning the "
                "uniform target."
                if failed else
                "✅ every uniform row holds flat — RULING 12's foundation is "
                "sound and emergent convention is measurable.")}
