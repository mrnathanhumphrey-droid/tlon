"""Phase 8.1 -- the RSA alpha-frontier. PREREG 269f78d7.

WHAT THIS ANSWERS. Our naive-listener gap (8-13 pts) is the primary pact
detector, but a gap on its own is unremarkable: an HONEST RSA pragmatic speaker
produces one too. It specialises its utterance choice toward what a listener
adapted to IT will resolve, and a listener adapted to a UNIFORM speaker then does
worse. That is honest pragmatic specialisation, and until now nothing ruled it out.

So: compute the largest gap an honest speaker could possibly produce, as a
function of rationality alpha, and check whether ours exceeds it EVERYWHERE --
including alpha -> infinity, where the honest gap is maximal.

    L0(r | u)         = uniform over { r : consistent(u, sig_r) }        EXACT
    S1^a(s | r)       ∝ L0(r | u(r,s))^a
    L_adapted(r | u)  ∝ P_{S1^a}(u | r) P(r)     Bayes listener for THIS speaker
    L_naive(r | u)    ∝ P_uniform(u | r) P(r)    Bayes listener for a uniform one
    gap_RSA(a)        = acc(L_adapted) - acc(L_naive) on S1^a's own output

⭐ L0 IS EXACT HERE. Every prior RSA application approximates the literal
listener with a neural net; ours is an LL(1) parse plus a lossless denotation
plus consistent(). So this frontier is COMPUTED, not estimated, and the
comparison carries no model-slop term. That is the methodological contribution.

XX MISREPORT RISK NAMED IN THE LOCKED PREREG: "comparing against a single
convenient alpha and calling it closed." Exceeding at alpha=1 is NOT sufficient.
Only exceeding at alpha->infinity closes Hole 1.
"""
from __future__ import annotations
import itertools
import json
import math
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar.parse import render                 # noqa: E402
from tlon.referents import schema                     # noqa: E402
from tlon.referents.match import consistent           # noqa: E402
from pi_controls import build                         # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
ALPHAS = [0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0]
SEED = 8080


def utterance_space(refs, rng):
    """u(r,s) for every referent and every selection subset, under pi.

    The scene is built deterministically per (r, s) so the utterance is a
    well-defined function of the speaker's choice. Distinct (r,s) pairs may map
    to the SAME surface -- that collision IS the ambiguity, and it is what L0
    has to resolve.
    """
    space, scenes = {}, {}
    for ri, ref in enumerate(refs):
        deps = len(ref.signature.contains) - 1
        subs = []
        for k in range(deps + 1):
            for keep in itertools.combinations(range(deps), k):
                sc = build(ref, keep, random.Random(1000 + ri), None, 0, True)
                if sc is None:
                    continue
                subs.append((keep, render(sc)))
                scenes[(ri, keep)] = sc
        if subs:
            space[ri] = subs
    return space, scenes


def literal_listener(refs, space, scenes):
    """L0(r | u): uniform over referents the utterance is CONSISTENT with.

    Note this is semantic, not policy-derived -- a literal listener knows the
    language, not the speaker's habits. That is what makes it the honest
    baseline rather than a second adapted listener.
    """
    surfaces = {}
    for ri, subs in space.items():
        for keep, surf in subs:
            surfaces.setdefault(surf, scenes[(ri, keep)])
    L0 = {}
    for surf, sc in surfaces.items():
        cons = [i for i, r in enumerate(refs) if consistent(sc, r.signature)]
        L0[surf] = {i: 1.0 / len(cons) for i in cons} if cons else {}
    return L0


def speaker(space, L0, ri, alpha):
    """S1^a(s | r). alpha=inf -> deterministic argmax, ties split evenly."""
    subs = space[ri]
    util = [L0[surf].get(ri, 0.0) for _, surf in subs]
    if math.isinf(alpha):
        best = max(util)
        w = [1.0 if u >= best - 1e-12 else 0.0 for u in util]
    else:
        w = [u ** alpha if u > 0 else 0.0 for u in util]
    tot = sum(w)
    if tot <= 0:
        w = [1.0] * len(subs)
        tot = float(len(subs))
    return [x / tot for x in w]


def frontier_point(refs, space, L0, alpha):
    n = len(space)
    prior = 1.0 / n

    # P(u | r) under S1^a and under the uniform speaker
    p_s1, p_un = {}, {}
    for ri in space:
        s1 = speaker(space, L0, ri, alpha)
        for (keep, surf), w in zip(space[ri], s1):
            p_s1.setdefault(ri, {}).setdefault(surf, 0.0)
            p_s1[ri][surf] += w
        u = 1.0 / len(space[ri])
        for keep, surf in space[ri]:
            p_un.setdefault(ri, {}).setdefault(surf, 0.0)
            p_un[ri][surf] += u

    def posterior(pmodel, surf):
        post = {ri: pmodel[ri].get(surf, 0.0) * prior for ri in space}
        tot = sum(post.values())
        return {k: v / tot for k, v in post.items()} if tot > 0 else {}

    acc_ad = acc_na = 0.0
    for ri in space:
        s1 = speaker(space, L0, ri, alpha)
        for (keep, surf), w in zip(space[ri], s1):
            if w <= 0:
                continue
            for pmodel, which in ((p_s1, "ad"), (p_un, "na")):
                post = posterior(pmodel, surf)
                if not post:
                    continue
                best = max(post.values())
                winners = [k for k, v in post.items() if v >= best - 1e-12]
                hit = (1.0 / len(winners)) if ri in winners else 0.0
                if which == "ad":
                    acc_ad += prior * w * hit
                else:
                    acc_na += prior * w * hit
    return acc_ad, acc_na, acc_ad - acc_na


def red_proof(refs, space, L0):
    """Can this frontier compute a NON-zero gap AT ALL?

    Two earlier attempts at this red-proof returned 0.00 and BOTH were bad test
    cases, not bugs -- which is itself the finding. An RSA speaker concentrates
    on utterances where L0(r|u) is HIGHER (fewer competitors), and those are
    exactly the ones a naive listener also resolves well, so concentration
    toward informativeness helps both listeners. Even an ANTI-RSA speaker on our
    real space gave 0.00, because that space is nearly unambiguous
    (mean consistency 1.26) and both listeners are already near-perfect.

    So here is a space where a gap is provable BY HAND:

      ref0 : {uX (shared), uA (unique)}          -> best option is uA
      ref1 : {uX (shared), uB1..uB9 (each 4-way ambiguous)}  -> best is uX

    At high alpha ref0 says uA and ref1 says uX. On uX the ADAPTED listener
    knows only ref1 goes there and is right; the NAIVE listener assumes uniform,
    where P(uX|ref0)=1/2 beats P(uX|ref1)=1/10, and is WRONG. Expected gap ~50pts.

    If the code reports ~+50 here, the computation is sound and every 0.00 above
    is a property of OUR utterance space, not of the estimator.
    """
    fake_L0 = {"uX": {0: 0.5, 1: 0.5}, "uA": {0: 1.0}}
    opts1 = [((0,), "uX")]
    for i in range(1, 10):
        fake_L0[f"uB{i}"] = {1: 0.25}
        opts1.append(((i,), f"uB{i}"))
    fake_space = {0: [((0,), "uX"), ((1,), "uA")], 1: opts1}
    _, _, g = frontier_point(refs, fake_space, fake_L0, 8.0)
    _, _, g_uni = frontier_point(refs, fake_space, fake_L0, 0.0)
    return {"handbuilt_gap_pts": 100 * g,
            "handbuilt_at_alpha0_pts": 100 * g_uni,
            "fires": g > 0.01}


def main() -> int:
    rng = random.Random(SEED)
    refs = schema.load_all().referents
    print("=" * 78)
    print("RSA ALPHA-FRONTIER -- PREREG 269f78d7. Exact L0, no estimation.")
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
        print(f"  {label:>8}  {100*ad:>9.1f}%  {100*na:>8.1f}%  {100*g:>10.2f} pts")

    rp = red_proof(refs, space, L0)
    print("")
    print("  RED-PROOF -- a hand-built space where a gap is provable by hand")
    print("  (expected ~+50 pts at alpha=8, ~0 at alpha=0):")
    print(f"    hand-built space, alpha=8   {rp['handbuilt_gap_pts']:+.2f} pts")
    print(f"    hand-built space, alpha=0   {rp['handbuilt_at_alpha0_pts']:+.2f} pts"
          f"   (must be ~0: uniform speaker = uniform listener)")
    if not rp["fires"]:
        print("  XX RED-PROOF FAILED -- frontier cannot report a positive.")
        print("  The zero above means nothing. Fix the computation.")
        return 1

    gmax = max(r["gap"] for r in rows)
    amax = next(r["alpha"] for r in rows if r["gap"] == gmax)
    ginf = next(r["gap"] for r in rows if r["alpha"] == "inf")
    print(f"\n  frontier maximum: {100*gmax:.2f} pts at alpha={amax}")
    print(f"  at alpha->inf:    {100*ginf:.2f} pts")

    # Our measured gap, one seed, from phase 5. NOT yet the 5 seeds the KILL
    # condition requires -- that comes from the 8.2/8.3 run.
    p5 = json.loads((OUT / "phase5.json").read_text())
    frozen = {(r["pi"], r["lam"]): r["gap"] for r in p5["results"]
              if not r["co_adapting"]}
    meas = [100 * (r["gap"] - frozen[(r["pi"], r["lam"])])
            for r in p5["results"] if r["co_adapting"]]
    print(f"\n  measured gap (phase 5, ONE SEED -- direction only): "
          f"{min(meas):+.2f} to {max(meas):+.2f} pts")
    print(f"  frontier max over ALL alpha:                        "
          f"{100*gmax:+.2f} pts")
    if min(meas) > 100 * gmax:
        print("\n  DIRECTION: every measured arm exceeds the honest frontier at "
              "EVERY alpha.\n  XX NOT YET A CLOSURE -- the KILL condition needs "
              "5 seeds. One seed is direction only.")
    elif max(meas) <= 100 * gmax:
        print("\n  DIRECTION: the frontier covers our measured gap. An honest "
              "RSA speaker at\n  some alpha could produce it => Hole 1 would NOT "
              "close; the pact reduces to\n  honest pragmatic specialisation.")
    else:
        print("\n  DIRECTION: MIXED -- some arms above the frontier, some below. "
              "Per-arm, per-seed\n  comparison required; no aggregate statement "
              "is legitimate.")

    (OUT / "rsa_frontier.json").write_text(json.dumps(
        {"prereg": "269f78d7", "n_referents": len(space),
         "n_utterances": n_u, "frontier": rows,
         "red_proof": rp, "frontier_max_pts": 100 * gmax, "frontier_at_inf_pts": 100 * ginf,
         "measured_phase5_one_seed_pts": meas},
        indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'rsa_frontier.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
