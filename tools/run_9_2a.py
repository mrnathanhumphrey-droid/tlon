"""PHASE 9.2a — consistency-set size on v2. PREREG 10757ac4.

THE SINGLE NUMBER THIS PHASE EXISTS FOR. Phase 8.1's RSA frontier was identically
zero because mean L0 consistency-set size on the old 60 was 1.26 -- a
near-deterministic utterance space with no room for a pact to live in.

⛔ REPORTING THE MEAN ALONE IS A PRE-REGISTERED MISREPORT. A mean of 1.26 with a
long tail is a different world from a flat 1.26. Primary statistic is

    f2 = fraction of DISTINCT utterances with |consistent| >= 2

with mean / median / p90 / max / full histogram, and mean H(r|u) in bits as the
literature-legible companion (Wilson: f2 is ours and defensible but is nobody's
convention; entropy is what a pragmatics referee expects to see).

⛔⛔ THE YARDSTICK IS CHECKED AGAINST THE BANKED RECORD BEFORE IT IS USED.
This script recomputes the ARCHIVE set first and asserts it reproduces the
banked 1.26. If a fresh derivation of a banked number disagrees, the pipeline is
wrong and the v2 number means nothing -- that collision is exactly what caught
the gate2b scheme error. Never derive the yardstick from the artefact under
audit, and never trust a pipeline that has not reproduced something known.

⛔ OLD vs NEW IS NEVER SUBTRACTED. Different referents, no pairing exists; it
goes through side_by_side() and the guard refuses the delta.
"""
from __future__ import annotations

import itertools
import json
import math
import pathlib
import random
import statistics as S
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar.parse import render                        # noqa: E402
from tlon.harness.paired import ItemSet, Measurement, side_by_side  # noqa: E402
from tlon.referents import schema                            # noqa: E402
from tlon.referents.match import consistent                  # noqa: E402
from pi_controls import build                                # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
BANKED_ARCHIVE_MEAN = 1.26        # VERDICT_8_FRONTIER, runs/rsa_frontier.json
DRAWS = 12                        # robustness: v2 has 19 disjunctive roots
F2_GATE = 0.25                    # PREREG: outcome A below this
MEDIAN_GATE = 8                   # PREREG: outcome C above this


def space_one_draw(refs):
    """EXACTLY how phase 8.1 built it: one deterministic scene per (ref, keep).

    Kept identical so the 1.26 comparison stays legible. Its weakness on v2 --
    one draw cannot represent 19 disjunctive roots and 11 randomly-relatored
    deep edges -- is why space_multi_draw exists alongside it.
    """
    scenes = {}
    for ri, ref in enumerate(refs):
        deps = len(ref.signature.contains) - 1
        for k in range(deps + 1):
            for keep in itertools.combinations(range(deps), k):
                sc = build(ref, keep, random.Random(1000 + ri), None, 0, True)
                if sc is not None:
                    scenes[(ri, keep, 0)] = sc
    return scenes


def space_multi_draw(refs, draws=DRAWS, seed=515):
    """R independent realisations per (ref, keep).

    The disjunctive root and the unconstrained deep-edge relator are things the
    GENERATOR actually varies, so one draw understates the reachable space.
    """
    scenes = {}
    for ri, ref in enumerate(refs):
        deps = len(ref.signature.contains) - 1
        for k in range(deps + 1):
            for keep in itertools.combinations(range(deps), k):
                for d in range(draws):
                    sc = build(ref, keep, random.Random(seed + 9973 * ri + d),
                               None, 0, True)
                    if sc is not None:
                        scenes[(ri, keep, d)] = sc
    return scenes


def literal(refs, scenes):
    """L0(r|u) = uniform over referents the utterance is CONSISTENT with.

    Distinct (ref, keep, draw) triples may render the SAME surface -- that
    collision IS the ambiguity, so surfaces are deduped first.
    """
    by_surface = {}
    for key, sc in scenes.items():
        by_surface.setdefault(render(sc), sc)
    out = {}
    for surf, sc in by_surface.items():
        cons = [i for i, r in enumerate(refs) if consistent(sc, r.signature)]
        out[surf] = cons
    return out


def stats(L0):
    sizes = sorted(len(c) for c in L0.values())
    n = len(sizes)
    f2 = sum(1 for s in sizes if s >= 2) / n
    # H(r|u) for a UNIFORM posterior over the consistent set = log2|consistent|
    H = S.fmean(math.log2(s) if s > 0 else 0.0 for s in sizes)
    floor = S.fmean(1.0 / s if s > 0 else 0.0 for s in sizes)
    hist = {}
    for s in sizes:
        hist[s] = hist.get(s, 0) + 1
    return {"n_utterances": n, "f2": f2, "mean": S.fmean(sizes),
            "median": S.median(sizes), "p90": sizes[int(0.9 * (n - 1))],
            "max": sizes[-1], "H_bits": H, "m_uniform_floor": floor,
            "histogram": {str(k): v for k, v in sorted(hist.items())},
            "empty": sum(1 for s in sizes if s == 0)}


def show(label, st):
    print(f"  {label}")
    print(f"    utterances {st['n_utterances']:>5}   "
          f"f2 = {100*st['f2']:.1f} %   H(r|u) = {st['H_bits']:.3f} bits")
    print(f"    |consistent|  mean {st['mean']:.2f}  median {st['median']:.1f}  "
          f"p90 {st['p90']}  max {st['max']}   "
          f"m_uniform_floor {st['m_uniform_floor']:.3f}")
    h = st["histogram"]
    top = sorted(((int(k), v) for k, v in h.items()))[:9]
    bar = "  ".join(f"{k}:{v}" for k, v in top)
    print(f"    histogram  {bar}{'  ...' if len(h) > 9 else ''}")
    if st["empty"]:
        print(f"    ⛔ {st['empty']} utterances consistent with NOTHING")


def main() -> int:
    print("=" * 78)
    print("PHASE 9.2a -- CONSISTENCY-SET SIZE ON v2. PREREG 10757ac4")
    print("=" * 78)

    # ---- 0. reproduce the banked archive number BEFORE trusting anything ----
    arch = schema.load_archive().referents
    a_st = stats(literal(arch, space_one_draw(arch)))
    print("\n  0. YARDSTICK CHECK -- reproduce the banked archive number first\n")
    show(f"archive 60, one draw (phase 8.1's method)", a_st)
    delta = abs(a_st["mean"] - BANKED_ARCHIVE_MEAN)
    if delta > 0.02:
        print(f"\n  ⛔⛔ PIPELINE DISAGREES WITH THE BANKED RECORD: "
              f"{a_st['mean']:.3f} vs {BANKED_ARCHIVE_MEAN}. "
              "The v2 number below would be meaningless. STOP.")
        return 1
    print(f"    ✅ reproduces banked {BANKED_ARCHIVE_MEAN} "
          f"(got {a_st['mean']:.2f}) -- pipeline trusted")

    # ---- 1. v2 -------------------------------------------------------------
    live = schema.load_live().referents
    print(f"\n  1. v2 LIVE SET -- {len(live)} referents\n")
    v_one = stats(literal(live, space_one_draw(live)))
    show("v2, one draw (SAME METHOD as 8.1 -- the legible comparison)", v_one)
    v_many = stats(literal(live, space_multi_draw(live)))
    print()
    show(f"v2, {DRAWS} draws (robustness: 19 disjunctive roots, 11 free "
         "deep relators)", v_many)

    # ---- 2. old vs new: side by side, NEVER subtracted ---------------------
    print("\n  2. OLD vs NEW -- unpairable, so reported side by side\n")
    m_old = Measurement("archive 60, mean |consistent|", a_st["mean"],
                        ItemSet.of("referent", [r.id for r in arch],
                                   referent_set="archive"))
    m_new = Measurement("v2 46, mean |consistent|", v_one["mean"],
                        ItemSet.of("referent", [r.id for r in live],
                                   referent_set="v2"))
    sbs = side_by_side(m_old, m_new,
                       reason="different referents entirely; no pairing exists")
    print("    " + sbs.describe().replace("\n", "\n    "))
    try:
        _ = sbs.delta
        print("    ⛔ GUARD FAILED -- a delta was computed")
        return 1
    except Exception:
        print("    ✅ guard refuses the subtraction, as designed")

    # ---- 3. the pre-registered verdict -------------------------------------
    f2, med = v_one["f2"], v_one["median"]
    print("\n" + "=" * 78)
    print(f"  PRE-REGISTERED THRESHOLDS: f2 >= {F2_GATE:.0%} and median "
          f"<= {MEDIAN_GATE}\n")
    if med > MEDIAN_GATE:
        outcome = "C"
        text = ("OVER-COLLIDED -- the opposite failure. Pre-object vocabulary "
                "so uniform\n  that discrimination may be impossible. ⛔ NOT "
                "automatically fatal: report\n  m_uniform_floor and the honest "
                "listener's accuracy; C is fatal ONLY if the\n  honest listener "
                "cannot beat its own uniform floor (D1).")
    elif f2 < F2_GATE:
        outcome = "A"
        text = ("STILL SCATTERED -- v2 rebuilt the shallow set with prettier "
                "names.\n  Detectors stay degenerate. THE PHASE HAS FAILED ITS "
                "OWN BET AND SAYS SO.")
    else:
        outcome = "B"
        text = ("USABLE MIDDLE -- the set delivered the underdetermination the "
                "instrument\n  needs. Phase 8's open questions become "
                "answerable on a set with range.")
    print(f"  OUTCOME {outcome}: {text}")
    print(f"\n  f2 = {100*f2:.1f} %   median = {med:.1f}   "
          f"mean = {v_one['mean']:.2f}   H = {v_one['H_bits']:.3f} bits")

    OUT.mkdir(exist_ok=True)
    (OUT / "phase9_2a.json").write_text(json.dumps(
        {"prereg": "10757ac4", "outcome": outcome,
         "gates": {"f2": F2_GATE, "median": MEDIAN_GATE},
         "archive_one_draw": a_st, "banked_archive_mean": BANKED_ARCHIVE_MEAN,
         "v2_one_draw": v_one, "v2_multi_draw": v_many, "draws": DRAWS},
        indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'phase9_2a.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
