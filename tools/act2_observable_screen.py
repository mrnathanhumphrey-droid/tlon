"""OBSERVABLE SCREEN — which quantity is stable across BUILDS but moves WITHIN a
conversation? $0, no box, pure re-analysis of transcripts already on disk.

⭐⭐ THE SELECTION CRITERION IS INVERTED FROM THE ONE THAT GOT US HERE.
`ki`-emission was chosen because it MOVED — it was the force whose marginal
deviated from the corpus. That is the right instinct for finding a phenomenon and
the WRONG one for choosing an arena observable, because a quantity selected for
movement is selected for variance, and build-variance is variance.

For the arena the requirement is the opposite: **movement inside a conversation
must be unambiguously coupling, not an accident of which build you grabbed.**

⛔ BUT "LOWEST BUILD-VARIANCE" ALONE IS THE WRONG TARGET TOO. A constant has zero
build-variance and cannot register drift at all. The criterion is a RATIO:

      contamination = between-build sd  /  within-conversation movement

    LOW  → build noise is small against the signal drift would produce  ⭐ usable
    HIGH → any within-conversation movement could be build noise         ⛔ unusable

⛔⛔ THE COUPLING COLUMN IS MEASURED IN A REGIME WHERE COUPLING IS IMPOSSIBLE.
Every transcript on disk was generated at `--history-window 1`: each speaker sees
ONLY the previous turn. Convention formation over 40 turns cannot occur when
neither party can remember turn 3 at turn 30 — the locality architecture removed
accumulation deliberately. So a coupling excess of ~0 here is EXPECTED BY
CONSTRUCTION and rules nothing out. ⇒ **The build-stability column is valid and
usable. The coupling column is not yet evidence about any observable**, and must
be re-measured on ACCUMULATING-context exchanges before it can kill a candidate.
(Exactly one such transcript exists: `runs/act2/logs/mt_run/arm1_new_accum.json`.)

⚠️ EXPLORATORY AND NOT PRE-REGISTERED. This ranks candidates to inform a design
decision; it establishes nothing about Tlön. Any observable it favours must still
be pre-registered before it is used to make a claim.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.discourse import force_map as FM                        # noqa: E402
from tlon.grammar.parse import parse, render                      # noqa: E402

#: The builds, and which are the same code. adapter_mt predates the 08-27
#: refactor, so it is reported but kept OUT of the primary between-build number.
BUILDS = [
    ("s20620", "runs/act2/ki_target/logs", "bfresh_*.json", True),
    ("s20621", "runs/act2/recipe_var/logs", "s20621_*.json", True),
    ("s20622", "runs/act2/recipe_var/logs", "s20622_*.json", True),
    ("s20623", "runs/act2/recipe_var/logs", "s20623_*.json", True),
    ("adapter_mt", "runs/act2/logs/mt_run", "arm2_new_w1_*.json", False),
]


def _nodes(n):
    out, stack = [], [n]
    while stack:
        x = stack.pop()
        out.append(x)
        stack.extend(c for _, c in x.edges)
    return out


def scenes_of(transcript):
    out = []
    for s in transcript:
        try:
            sc = parse(s)
        except Exception:                                          # noqa: BLE001
            continue
        if render(sc) == s:
            out.append((sc, s))
    return out


#: ⭐ Each observable maps a LIST of (scene, surface) to one float. Keeping them
#: in one table means the screen cannot quietly favour the one it was written for.
def _rate(scs, force):
    f = [sc.force for sc, _ in scs]
    return f.count(force) / len(f) if f else None


def _ttr_roots(scs):
    r = [n.root for sc, _ in scs for n in _nodes(sc.node)]
    return len(set(r)) / len(r) if r else None


def _distinct_surface(scs):
    s = [x for _, x in scs]
    return len(set(s)) / len(s) if s else None


def _mean_nodes(scs):
    v = [len(_nodes(sc.node)) for sc, _ in scs]
    return sum(v) / len(v) if v else None


def _mean_depth(scs):
    def d(n):
        return 1 + max((d(c) for _, c in n.edges), default=0)
    v = [d(sc.node) for sc, _ in scs]
    return sum(v) / len(v) if v else None


def _mod_density(scs):
    ns = [n for sc, _ in scs for n in _nodes(sc.node)]
    if not ns:
        return None
    filled = sum(bool(n.aspect) + bool(n.degree) + bool(n.modal)
                 + bool(n.tense) + bool(n.quant) + bool(n.orient) for n in ns)
    return filled / (6 * len(ns))


def _mean_tokens(scs):
    v = [len(x.split()) for _, x in scs]
    return sum(v) / len(v) if v else None


def _root_repertoire(scs):
    r = {n.root for sc, _ in scs for n in _nodes(sc.node)}
    return len(r)


OBSERVABLES = {
    "force:ki": lambda s: _rate(s, "ki"),
    "force:ka": lambda s: _rate(s, "ka"),
    "force:ko": lambda s: _rate(s, "ko"),
    "force:ku": lambda s: _rate(s, "ku"),
    "force:kä": lambda s: _rate(s, "kä"),
    "root TTR": _ttr_roots,
    "distinct-surface": _distinct_surface,
    # ⛔ `tree depth` REMOVED: verified 40/40 scenes have node-count == depth —
    # the parse trees are LINEAR CHAINS, so it was the same observable twice and
    # would have double-counted a candidate in the ranking.
    "nodes/scene": _mean_nodes,
    "modifier density": _mod_density,
    "tokens/surface": _mean_tokens,
    "root repertoire": _root_repertoire,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/act2/observable_screen.json")
    a = ap.parse_args()

    print("OBSERVABLE SCREEN — stable across BUILDS, moving WITHIN a conversation")
    print("=" * 78)
    print("⚠️ EXPLORATORY, NOT PRE-REGISTERED. Ranks candidates for the arena; "
          "establishes\n   nothing. Anything it favours must be pre-registered "
          "before it carries a claim.\n")

    per_build = {}
    for name, d, pat, same_code in BUILDS:
        files = sorted(pathlib.Path(d).glob(pat))
        if not files:
            continue
        ex = []
        for f in files:
            t = json.loads(f.read_text(encoding="utf-8"))["transcript_interacting"]
            scs = scenes_of(t)
            if len(scs) < 8:
                continue
            half = len(scs) // 2
            ct = json.loads(f.read_text(encoding="utf-8")).get(
                "transcript_control") or []
            cs = scenes_of(ct)
            ch = len(cs) // 2
            ex.append({"all": scs, "first": scs[:half], "second": scs[half:],
                       "cfirst": cs[:ch], "csecond": cs[ch:]})
        per_build[name] = {"ex": ex, "same_code": same_code}
        print(f"  {name:11s} {len(ex):3d} exchanges")

    rows = []
    for oname, fn in OBSERVABLES.items():
        build_means, within_sds, moves, cmoves = {}, [], [], []
        for bname, b in per_build.items():
            vals = [v for e in b["ex"] if (v := fn(e["all"])) is not None]
            if len(vals) < 2:
                continue
            build_means[bname] = sum(vals) / len(vals)
            within_sds.append(statistics.stdev(vals))
            for e in b["ex"]:
                f1, f2 = fn(e["first"]), fn(e["second"])
                if f1 is not None and f2 is not None:
                    moves.append(abs(f2 - f1))
                # ⭐⭐ THE YOKED CONTROL — movement is not coupling.
                # First-half vs second-half movement can be a pure LENGTH
                # artifact (root TTR mechanically falls as any monologue grows).
                # The control arm talks to a FROZEN partner, so anything that
                # moves equally there is not responding to an interlocutor.
                c1, c2 = fn(e["cfirst"]), fn(e["csecond"])
                if c1 is not None and c2 is not None:
                    cmoves.append(abs(c2 - c1))
        same = [v for k, v in build_means.items() if per_build[k]["same_code"]]
        if len(same) < 3 or not moves:
            continue
        bsd = statistics.stdev(same)
        move = sum(moves) / len(moves)
        wsd = sum(within_sds) / len(within_sds)
        cmove = (sum(cmoves) / len(cmoves)) if cmoves else None
        rows.append({"observable": oname, "between_build_sd": bsd,
                     "within_build_sd": wsd, "within_conv_move": move,
                     "control_move": cmove,
                     # ⭐ coupling excess: how much MORE it moves against a live
                     # partner than a frozen one. <= 0 means the movement is a
                     # length artifact and drift could never be attributed.
                     "coupling_excess": (move - cmove) if cmove is not None else None,
                     "contamination": bsd / move if move else float("inf"),
                     "build_means": build_means})

    rows.sort(key=lambda r: r["contamination"])
    print(f"\n  {'observable':18s} {'build sd':>10s} {'conv move':>10s} "
          f"{'CONTAM':>8s}  {'within sd':>10s}")
    print("  " + "-" * 62)
    for r in rows:
        flag = "  ⭐" if r["contamination"] < 0.5 else (
            "  ⛔" if r["contamination"] > 1.0 else "")
        print(f"  {r['observable']:18s} {r['between_build_sd']:10.4f} "
              f"{r['within_conv_move']:10.4f} {r['contamination']:8.2f} "
              f"{r['within_build_sd']:10.4f}{flag}")

    print("\n  CONTAM = between-build sd / mean within-conversation movement.")
    print("  ⭐ < 0.5  build noise is small against what drift would move")
    print("  ⛔ > 1.0  any within-conversation movement could be build noise")
    print("  COUPLING = live movement − frozen-partner movement. ⛔ ≤ 0 means the")
    print("  movement is a LENGTH ARTIFACT and drift could never be attributed.")
    # ⛔ Ranked on BUILD-STABILITY only. The coupling column cannot filter yet:
    # see the module docstring — it was measured at window=1.
    best = [r for r in rows if r["contamination"] < 0.5]
    if best:
        print(f"\n  ⭐ CANDIDATES FOR THE ARENA: "
              f"{[r['observable'] for r in best]}")
    ki = next((r for r in rows if r["observable"] == "force:ki"), None)
    if ki:
        print(f"  ⛔ force:ki — the observable the whole arc was built on — "
              f"contamination {ki['contamination']:.2f}")

    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(rows, indent=2, ensure_ascii=False),
                                   encoding="utf-8", newline="")
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
