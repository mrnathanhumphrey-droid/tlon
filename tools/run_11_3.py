"""PHASE 11.3 -- RSA frontier on the gate-B sets. AND THE HONESTY TEST.

⛔⛔ READ THIS BEFORE THE NUMBERS. CR and TAO were built with d=1 on purpose,
and that choice came straight out of Phase 9's combinatorial finding -- with d
dependents only 1 of 2^d subsets is strongly ambiguous, so d=1 puts HALF the
space at keep=0. That is designing to the detector's mechanism. It is the thing
this project keeps warning against, and pretending otherwise would be worse than
doing it.

SO THE QUESTION IS WHETHER THE UNDERDETERMINATION IS REAL OR METRIC-SPECIFIC,
and the RSA frontier is the test that can tell them apart:

  * f2 up AND frontier still identically 0  ->  the "ambiguity" is not the kind
    an optimising speaker can act on. f2 was gamed. The gate measured something
    the phenomenon cannot use.
  * f2 up AND frontier goes POSITIVE       ->  the ambiguity is real: an honest
    RSA speaker now has something to produce. ⛔ AND THAT REOPENS HOLE 1 -- our
    measured gap must then exceed the frontier's SUPREMUM over alpha, not its
    endpoint. A cost of a usable set, never evidence of "range".

Either way the answer is informative and neither is good news by default.

BAR (Wilson's fix, Phase 9): sup over ALL alpha, reporting alpha* and the margin
there. The endpoint rule was an artefact of the zero-frontier case.
"""
from __future__ import annotations

import json
import math
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.referents import schema                            # noqa: E402
from rsa_frontier import (ALPHAS, frontier_point,            # noqa: E402
                          literal_listener, red_proof, utterance_space)

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"


def run(setname: str) -> dict:
    refs = schema.load_worldview(setname, allow_unreviewed=True).referents
    rng = random.Random(8080)
    space, scenes = utterance_space(refs, rng)
    n_u = len({s for subs in space.values() for _, s in subs})
    L0 = literal_listener(refs, space, scenes)
    amb = [len(v) for v in L0.values()]

    print(f"\n  {setname.upper()} -- {len(space)} referents, "
          f"{sum(len(v) for v in space.values())} (ref, subset) pairs, "
          f"{n_u} distinct utterances")
    print(f"    L0 consistency-set size: mean {sum(amb)/len(amb):.2f}, "
          f"max {max(amb)}")
    print(f"\n    {'alpha':>8}  {'L_adapted':>10}  {'L_naive':>9}  {'GAP':>10}")
    rows = []
    for a in ALPHAS + [math.inf]:
        ad, na, g = frontier_point(refs, space, L0, a)
        rows.append({"alpha": ("inf" if math.isinf(a) else a),
                     "acc_adapted": ad, "acc_naive": na, "gap": g})
        lab = "inf" if math.isinf(a) else f"{a:g}"
        print(f"    {lab:>8}  {100*ad:>9.1f}%  {100*na:>8.1f}%  "
              f"{100*g:>9.2f} pts")

    sup = max(r["gap"] for r in rows)
    astar = next(r["alpha"] for r in rows if r["gap"] == sup)
    ginf = next(r["gap"] for r in rows if r["alpha"] == "inf")
    return {"set": setname, "n_referents": len(space), "n_utterances": n_u,
            "l0_mean": sum(amb) / len(amb), "l0_max": max(amb),
            "frontier": rows, "sup_pts": 100 * sup, "alpha_star": astar,
            "at_inf_pts": 100 * ginf}


def main() -> int:
    print("=" * 78)
    print("PHASE 11.3 -- RSA FRONTIER ON THE GATE-B SETS")
    print("  bar = sup over ALL alpha. Also: the test of whether f2 was gamed.")
    print("=" * 78)

    out = {}
    for name in ("cr", "tao"):
        out[name] = run(name)

    # red-proof once: can the estimator report a positive at all?
    refs = schema.load_worldview("cr", allow_unreviewed=True).referents
    space, scenes = utterance_space(refs, random.Random(8080))
    rp = red_proof(refs, space, literal_listener(refs, space, scenes))
    print(f"\n  RED-PROOF: hand-built space {rp['handbuilt_gap_pts']:+.2f} pts "
          f"at alpha=8, {rp['handbuilt_at_alpha0_pts']:+.2f} at alpha=0")
    if not rp["fires"]:
        print("  XX RED-PROOF FAILED -- every zero above is meaningless.")
        return 1
    print("    ✅ the estimator CAN report a positive")

    print("\n" + "=" * 78)
    for name, r in out.items():
        sup, astar, ginf = r["sup_pts"], r["alpha_star"], r["at_inf_pts"]
        print(f"\n  {name.upper()}: sup = {sup:.2f} pts at alpha* = {astar}   "
              f"(endpoint {ginf:.2f})")
        if abs(sup) < 1e-9:
            r["verdict"] = "ZERO_F2_WAS_METRIC_SPECIFIC"
            print("    ⛔⛔ FRONTIER IDENTICALLY ZERO DESPITE f2 CLEARING THE")
            print("       GATE. The added ambiguity is NOT the kind an")
            print("       optimising speaker can act on ⇒ f2 was gamed by the")
            print("       d=1 construction and the gate measured something the")
            print("       phenomenon cannot use. Hole 1 stays closed for free,")
            print("       and that is the bad news, not the good news.")
        else:
            r["verdict"] = "POSITIVE_REAL_UNDERDETERMINATION_HOLE1_REOPENS"
            print("    ⭐ FRONTIER IS POSITIVE ⇒ the underdetermination is REAL:")
            print("       an honest RSA speaker now has something to produce.")
            print("    ⛔⛔ AND SO HOLE 1 REOPENS. Any closure claim must exceed")
            print(f"       {sup:.2f} pts, the SUPREMUM at alpha*={astar} -- not")
            print(f"       the {ginf:.2f} at the endpoint. This is a COST of a")
            print("       usable set and must NEVER be reported as 'range'.")
            if abs(ginf - sup) > 1e-9:
                print("    ⭐ THE ENDPOINT IS NOT THE MAXIMUM -- Phase 8's")
                print("       alpha->inf rule would have UNDERSTATED the bar.")
                print("       Wilson's fix earns its keep on first use.")

    (OUT / "phase11_3_rsa.json").write_text(
        json.dumps({"sets": out, "red_proof": rp}, indent=2, default=float),
        encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'phase11_3_rsa.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
