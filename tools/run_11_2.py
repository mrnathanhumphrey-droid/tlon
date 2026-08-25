"""PHASE 11.2 -- four sets against the Phase 9 gate, measured identically.

THE HYPOTHESIS. v2 (Cosmicomics) failed at f2 = 10.5 % because DEPTH BACKFIRES
COMBINATORIALLY: d dependents give 2^d subsets, only keep=0 is strongly
ambiguous, so each dependent added makes the ambiguous case rarer faster than it
makes it more ambiguous. CR and TAO invert that -- every signature has ONE
dependent, and collision is supposed to come from a cohort sharing one dense
image-world.

THE MECHANISM CHECK IS THE POINT, NOT THE GATE. A set could clear the gate for
the wrong reason. The prediction is specific and falsifiable: high f2 should
arrive with LOW mean depth and HIGH head-root sharing -- the inverse of v2's
profile. If a set clears with high depth, the hypothesis is not what carried it.

⛔ ALL FOUR SETS ARE SIDE BY SIDE, NEVER SUBTRACTED. Different referents,
unpairable by construction; the guard refuses the delta.

⛔ RULE ZERO: every count printed carries an asserted expected value.
   Measured statistics are flagged human-read-required.
"""
from __future__ import annotations

import collections
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
F2_GATE = 0.25
MEDIAN_GATE = 8
TRIES = 60
BANKED = {"archive": 1.26}          # VERDICT_8 / phase9_2a yardstick


class BannerMismatch(RuntimeError):
    pass


def banner(label, value, expected, fmt="{}"):
    if value != expected:
        raise BannerMismatch(f"{label}: printed {value!r}, expected {expected!r}")
    print(f"    {label:<50} {fmt.format(value)}")


def space(refs):
    """One deterministic scene per (referent, subset) -- 8.1's method exactly,
    so every number here is legible against 1.26 / 10.5 %."""
    out = {}
    for ri, ref in enumerate(refs):
        deps = len(ref.signature.contains) - 1
        for k in range(deps + 1):
            for keep in itertools.combinations(range(deps), k):
                sc = build(ref, keep, random.Random(1000 + ri), None, 0, True)
                if sc is not None:
                    out[(ri, keep)] = sc
    return out


def stats(refs, scenes):
    by_surface = {}
    for sc in scenes.values():
        by_surface.setdefault(render(sc), sc)
    sizes = sorted(sum(1 for r in refs if consistent(sc, r.signature))
                   for sc in by_surface.values())
    n = len(sizes)
    hist = collections.Counter(sizes)
    return {"n_utterances": n,
            "f2": sum(1 for s in sizes if s >= 2) / n,
            "mean": S.fmean(sizes), "median": S.median(sizes),
            "p90": sizes[int(0.9 * (n - 1))], "max": sizes[-1],
            "H_bits": S.fmean(math.log2(s) if s else 0.0 for s in sizes),
            "m_uniform_floor": S.fmean(1.0 / s if s else 0.0 for s in sizes),
            "histogram": {str(k): v for k, v in sorted(hist.items())}}


def structure(refs, scenes):
    """The mechanism: depth, head-root sharing, dependent sharing."""
    breadth = [len(r.signature.contains) for r in refs]
    heads = collections.Counter()
    deps = collections.Counter()
    for r in refs:
        for f in r.signature.contains[0].root_any:
            heads[f] += 1
        for p in r.signature.contains[1:]:
            for f in p.root_any:
                deps[f] += 1
    uniq_head = sum(1 for r in refs
                    if all(heads[f] == 1 for f in r.signature.contains[0].root_any))
    # share of the utterance space sitting at keep=0, where ambiguity lives
    k0 = sum(1 for (_, keep) in scenes if len(keep) == 0)
    return {"mean_patterns": S.fmean(breadth), "max_patterns": max(breadth),
            "mean_dependents": S.fmean(b - 1 for b in breadth),
            "unique_head_frac": uniq_head / len(refs),
            "head_root_max_share": max(heads.values()),
            "dep_root_max_share": max(deps.values()) if deps else 0,
            "keep0_share": k0 / len(scenes),
            "n_referents": len(refs)}


def verdict(st):
    if st["median"] > MEDIAN_GATE:
        return "C", "OVER-COLLIDED"
    if st["f2"] < F2_GATE:
        return "A", "STILL SCATTERED"
    return "B", "USABLE MIDDLE"


def main() -> int:
    print("=" * 78)
    print("PHASE 11.2 -- WORLDVIEW SETS vs THE PHASE 9 GATE")
    print("=" * 78)

    sets = {}
    loaders = [("archive", lambda: schema.load_archive().referents),
               ("v2", lambda: schema.load_live().referents),
               ("cr", lambda: schema.load_worldview("cr", allow_unreviewed=True).referents),
               ("tao", lambda: schema.load_worldview("tao", allow_unreviewed=True).referents)]
    expected_n = {"archive": 60, "v2": 46, "cr": 36, "tao": 36}

    print("\n  0. SET SIZES (asserted, not just printed)\n")
    for name, load in loaders:
        refs = load()
        banner(f"{name} referents", len(refs), expected_n[name])
        sets[name] = refs

    print("\n  1. SATISFIABILITY -- can the generator build every referent?\n")
    for name, refs in sets.items():
        sc = space(refs)
        total = sum(2 ** (len(r.signature.contains) - 1) for r in refs)
        built = {ri for ri, _ in sc}
        print(f"    {name:<9} {len(sc):>4}/{total:<4} subsets buildable "
              f"({100*len(sc)/total:5.1f} %)   referents with >=1 scene "
              f"{len(built)}/{len(refs)}")
        if len(built) != len(refs):
            missing = sorted({i for i in range(len(refs))} - built)
            print(f"      ⛔ UNSAYABLE: {[refs[i].id for i in missing]}")
            return 1
        sets[name] = (refs, sc)

    # yardstick against the banked record before any new number is trusted
    a_st = stats(*sets["archive"])
    print(f"\n  2. YARDSTICK -- archive mean |consistent| = {a_st['mean']:.2f} "
          f"(banked {BANKED['archive']})")
    if abs(a_st["mean"] - BANKED["archive"]) > 0.02:
        print("    ⛔⛔ PIPELINE DISAGREES WITH THE BANKED RECORD. STOP.")
        return 1
    print("    ✅ reproduces -- pipeline trusted")

    print("\n  3. THE GATE  (f2 >= 25 % and median <= 8)   [HUMAN-READ]\n")
    print(f"    {'set':<9} {'utts':>5} {'f2':>7} {'mean':>6} {'med':>5} "
          f"{'p90':>4} {'max':>4} {'H bits':>7}  outcome")
    res = {}
    for name in ("archive", "v2", "cr", "tao"):
        st = stats(*sets[name])
        code, label = verdict(st)
        res[name] = {**st, "outcome": code}
        print(f"    {name:<9} {st['n_utterances']:>5} {100*st['f2']:>6.1f}% "
              f"{st['mean']:>6.2f} {st['median']:>5.1f} {st['p90']:>4} "
              f"{st['max']:>4} {st['H_bits']:>7.3f}  {code} {label}")

    print("\n  4. THE MECHANISM CHECK -- collision from SHARING, not DEPTH\n")
    print(f"    {'set':<9} {'mean deps':>10} {'uniq head':>10} "
          f"{'top head':>9} {'top dep':>8} {'keep0 share':>12}")
    for name in ("archive", "v2", "cr", "tao"):
        s = structure(*sets[name])
        res[name]["structure"] = s
        print(f"    {name:<9} {s['mean_dependents']:>10.2f} "
              f"{100*s['unique_head_frac']:>9.0f}% {s['head_root_max_share']:>9} "
              f"{s['dep_root_max_share']:>8} {100*s['keep0_share']:>11.1f}%")
    print("\n    PREDICTION MADE BEFORE RUNNING: a set clearing the gate should")
    print("    show LOW mean deps + HIGH sharing + HIGH keep0 share. If a set")
    print("    clears with high depth, the hypothesis is not what carried it.")

    print("\n  5. GUARD -- four sets, side by side, never subtracted\n")
    ms = {n: Measurement(f"{n} f2", res[n]["f2"],
                         ItemSet.of("referent", [r.id for r in sets[n][0]],
                                    referent_set=n))
          for n in res}
    sbs = side_by_side(ms["v2"], ms["cr"], reason=(
        "different referents entirely -- no pairing exists between referent "
        "sets, so no delta is defined"))
    print("    " + sbs.describe().replace("\n", "\n    "))
    try:
        _ = sbs.delta
        print("    ⛔ GUARD FAILED"); return 1
    except Exception:
        print("    ✅ .delta raises; the four f2 values are reported, not differenced")

    print("\n" + "=" * 78)
    for name in ("cr", "tao"):
        st = res[name]
        code = st["outcome"]
        print(f"  {name.upper()}: OUTCOME {code}   f2 {100*st['f2']:.1f} %   "
              f"median {st['median']:.1f}   mean {st['mean']:.2f}")
        if code == "C":
            print(f"    ⛔ C is NOT automatically fatal (D1). m_uniform_floor = "
                  f"{st['m_uniform_floor']:.3f}; C is fatal only if an honest")
            print("       listener cannot beat that -- which needs a trained run.")
        if code == "B":
            print("    ⇒ RSA frontier owed on this set (11.3): a usable set may")
            print("       give an honest speaker something to produce, which")
            print("       REOPENS Hole 1. Non-zero frontier is a COST, not range.")

    (OUT / "phase11_2.json").write_text(json.dumps(
        {"gate": {"f2": F2_GATE, "median": MEDIAN_GATE}, "sets": res},
        indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'phase11_2.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
