"""PHASE 9.2b -- the RSA alpha-frontier on v2. PREREG 10757ac4.

⭐ THE BAR CHANGED SINCE PHASE 8, and this is the first run under the new one.
Phase 8 used "measured gap must exceed the frontier at alpha -> infinity". That
was only sufficient BY ACCIDENT OF THE VALUE: the frontier was identically zero,
so any positive gap cleared it everywhere at once and a single endpoint check
happened to be enough.

A POSITIVE frontier is a CURVE, and RSA gaps are generally non-monotonic in
alpha -- they rise, then can fall as the speaker saturates toward deterministic
informativeness. So the largest honest gap may sit at a FINITE alpha, and a
measured gap could clear the endpoint while sitting UNDER an interior peak. Hole
1 would be open while the verdict said closed.

    PREREG BAR:  measured gap  >  sup over all alpha of frontier(alpha)
                 report alpha* where the supremum occurs, and the margin there.

⛔ 9.2a came back OUTCOME A (f2 = 9.3 % vs a 25 % gate). The prereg says a
frontier that is still identically zero is EVIDENCE FOR OUTCOME A -- a
degenerate frontier means a near-deterministic space. So a zero here is a
CONSISTENCY CHECK on a failed gate, not a free win. It is reported that way.
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


def main() -> int:
    rng = random.Random(8080)
    refs = schema.load_live().referents
    print("=" * 78)
    print("PHASE 9.2b -- RSA ALPHA-FRONTIER ON v2. PREREG 10757ac4")
    print("  bar = sup over ALL alpha, not the endpoint")
    print("=" * 78)

    space, scenes = utterance_space(refs, rng)
    n_u = len({s for subs in space.values() for _, s in subs})
    print(f"  {len(space)} referents, "
          f"{sum(len(v) for v in space.values())} (referent, subset) pairs, "
          f"{n_u} distinct utterances")
    L0 = literal_listener(refs, space, scenes)
    amb = [len(v) for v in L0.values()]
    print(f"  L0 consistency-set size: mean {sum(amb)/len(amb):.2f}, "
          f"max {max(amb)}\n")

    print(f"  {'alpha':>8}  {'L_adapted':>10}  {'L_naive':>9}  {'HONEST GAP':>11}")
    rows = []
    for a in ALPHAS + [math.inf]:
        ad, na, g = frontier_point(refs, space, L0, a)
        rows.append({"alpha": ("inf" if math.isinf(a) else a),
                     "acc_adapted": ad, "acc_naive": na, "gap": g})
        label = "inf" if math.isinf(a) else f"{a:g}"
        print(f"  {label:>8}  {100*ad:>9.1f}%  {100*na:>8.1f}%  "
              f"{100*g:>10.2f} pts")

    rp = red_proof(refs, space, L0)
    print("\n  RED-PROOF -- hand-built space where a gap is provable by hand")
    print(f"    alpha=8 {rp['handbuilt_gap_pts']:+.2f} pts   "
          f"alpha=0 {rp['handbuilt_at_alpha0_pts']:+.2f} pts (must be ~0)")
    if not rp["fires"]:
        print("  XX RED-PROOF FAILED -- the frontier cannot report a positive.")
        print("  Every zero above means nothing. Fix the computation.")
        return 1
    print("    ✅ the computation CAN report a positive, so a zero is a fact")
    print("       about v2's utterance space, not about the estimator")

    sup = max(r["gap"] for r in rows)
    astar = next(r["alpha"] for r in rows if r["gap"] == sup)
    ginf = next(r["gap"] for r in rows if r["alpha"] == "inf")

    print("\n" + "=" * 78)
    print(f"  sup over all alpha : {100*sup:.2f} pts   at alpha* = {astar}")
    print(f"  at alpha -> inf    : {100*ginf:.2f} pts")
    if abs(sup) < 1e-9:
        print("\n  FRONTIER IS IDENTICALLY ZERO ON v2, at every alpha.")
        print("  ⇒ Hole 1's RSA horn stays closed for free -- AND, per the")
        print("     prereg, this is EVIDENCE FOR OUTCOME A: a degenerate")
        print("     frontier means a near-deterministic utterance space.")
        print("  ⛔ Not a win. It is the same reading as f2 = 9.3 %, arrived")
        print("     at independently.")
        verdict = "ZERO_CONSISTENT_WITH_OUTCOME_A"
    else:
        print("\n  ⛔⛔ FRONTIER IS POSITIVE -- HOLE 1 REOPENS.")
        print(f"  Any closure claim must now exceed {100*sup:.2f} pts, the")
        print(f"  SUPREMUM at alpha*={astar} -- NOT the {100*ginf:.2f} pts at")
        print("  the endpoint. This is a COST of a deeper set and must never")
        print("  be reported as 'the set has range'.")
        verdict = "POSITIVE_HOLE1_REOPENS"
        if abs(ginf - sup) > 1e-9:
            print(f"  ⭐ AND THE ENDPOINT IS NOT THE MAXIMUM: {100*ginf:.2f} at")
            print(f"     alpha->inf vs {100*sup:.2f} at alpha*={astar}. Phase")
            print("     8's endpoint rule would have understated the bar.")

    (OUT / "phase9_2b_rsa.json").write_text(json.dumps(
        {"prereg": "10757ac4", "set": "v2", "verdict": verdict,
         "n_referents": len(space), "n_utterances": n_u,
         "l0_mean": sum(amb) / len(amb), "l0_max": max(amb),
         "frontier": rows, "sup_pts": 100 * sup, "alpha_star": astar,
         "at_inf_pts": 100 * ginf, "red_proof": rp},
        indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'phase9_2b_rsa.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
