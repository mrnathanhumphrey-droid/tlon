"""Diagnosis of the 9.2a OUTCOME A result. Not a pre-registered measurement.

9.2a came back f2 = 9.3 % against a 25 % gate -- OUTCOME A, the bet failed, and
WORSE than the archive's 15.9 % despite the matrix rule. A verdict needs a
mechanism, so this asks where the ambiguity actually went.

⛔ THIS IS DIAGNOSIS, NOT A SECOND ATTEMPT. It changes no threshold, re-runs no
gate, and its numbers do not replace 9.2a's. If anything here suggests an edit to
the referent set, that edit is a NEW phase with its own prereg -- editing
signatures until f2 clears 25 % is the exact tuning loop the phase ordering
exists to prevent.

Three questions:
  1. WHERE does ambiguity live -- by keep-size (how much was withheld)?
  2. Did the matrix rule work AT ALL, i.e. is bare-head ambiguity up?
  3. Is the free aspect_root decoration ARTIFICIALLY disambiguating? v2 has 11
     referents with aspect_root_any vs the archive's 2, and a random decorated
     aspect mismatches those patterns, so the free channel may be doing the
     disambiguating rather than the signatures.
"""
from __future__ import annotations

import itertools
import json
import pathlib
import random
import statistics as S
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar.denote import project                      # noqa: E402
from tlon.grammar.parse import EventNode, Scene, render      # noqa: E402
from tlon.referents import schema                            # noqa: E402
from tlon.referents.match import consistent                  # noqa: E402
from pi_controls import build                                # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"


def by_keepsize(refs, label):
    """|consistent| bucketed by HOW MANY dependents were uttered."""
    rows = {}
    for ri, ref in enumerate(refs):
        deps = len(ref.signature.contains) - 1
        for k in range(deps + 1):
            for keep in itertools.combinations(range(deps), k):
                sc = build(ref, keep, random.Random(1000 + ri), None, 0, True)
                if sc is None:
                    continue
                cons = sum(1 for r in refs if consistent(sc, r.signature))
                rows.setdefault(k, []).append(cons)
    print(f"\n  {label}")
    print(f"    {'kept':>4} {'n':>5} {'mean':>7} {'max':>5} {'f2':>7}")
    out = {}
    for k in sorted(rows):
        v = rows[k]
        f2 = sum(1 for x in v if x >= 2) / len(v)
        out[str(k)] = {"n": len(v), "mean": S.fmean(v), "max": max(v), "f2": f2}
        print(f"    {k:>4} {len(v):>5} {S.fmean(v):>7.2f} {max(v):>5} "
              f"{100*f2:>6.1f}%")
    return out


def bare_head(refs, label):
    """Ambiguity of the UNDECORATED head alone -- the matrix rule's own target.

    Built by hand rather than via build(), so no free-channel decoration can
    disambiguate it. This is the cleanest read on whether making the head shared
    did what it was supposed to do.
    """
    sizes = []
    for ref in refs:
        p = ref.signature.contains[0]
        for root in p.root_any:
            n = EventNode(root=root,
                          orient=[p.orient_any[0]] if p.orient_any else [],
                          aspect=(p.aspect_root_any[0], 1)
                          if p.aspect_root_any else None)
            sc = project(Scene(node=n, force="ka"))
            sizes.append(sum(1 for r in refs if consistent(sc, r.signature)))
    f2 = sum(1 for s in sizes if s >= 2) / len(sizes)
    print(f"\n  {label}")
    print(f"    n {len(sizes)}   mean {S.fmean(sizes):.2f}   "
          f"median {S.median(sizes):.1f}   max {max(sizes)}   "
          f"f2 {100*f2:.1f}%")
    return {"n": len(sizes), "mean": S.fmean(sizes), "max": max(sizes),
            "f2": f2, "median": S.median(sizes)}


def aspect_effect(refs, label):
    """Does the FREE aspect_root decoration artificially disambiguate?

    Same scenes, head aspect stripped. If ambiguity jumps, the free channel was
    doing the discriminating -- which would mean f2 measures decoration, not the
    referent set.
    """
    dec, bare = [], []
    for ri, ref in enumerate(refs):
        deps = len(ref.signature.contains) - 1
        for k in range(deps + 1):
            for keep in itertools.combinations(range(deps), k):
                sc = build(ref, keep, random.Random(1000 + ri), None, 0, True)
                if sc is None:
                    continue
                dec.append(sum(1 for r in refs if consistent(sc, r.signature)))
                # strip a head aspect the SIGNATURE did not ask for
                sig_asp = ref.signature.contains[0].aspect_root_any
                n = sc.node
                keep_asp = n.aspect if sig_asp else None
                stripped = Scene(node=EventNode(
                    root=n.root, orient=list(n.orient), aspect=keep_asp,
                    edges=list(n.edges)), force=sc.force)
                bare.append(sum(1 for r in refs
                                if consistent(stripped, r.signature)))
    f2d = sum(1 for x in dec if x >= 2) / len(dec)
    f2b = sum(1 for x in bare if x >= 2) / len(bare)
    print(f"\n  {label}")
    print(f"    with free aspect decoration : mean {S.fmean(dec):.2f}   "
          f"f2 {100*f2d:>5.1f}%")
    print(f"    head aspect STRIPPED        : mean {S.fmean(bare):.2f}   "
          f"f2 {100*f2b:>5.1f}%")
    return {"decorated": {"mean": S.fmean(dec), "f2": f2d},
            "stripped": {"mean": S.fmean(bare), "f2": f2b}}


def main() -> int:
    arch = schema.load_archive().referents
    live = schema.load_live().referents
    print("=" * 78)
    print("DIAGNOSIS of 9.2a OUTCOME A -- where did the ambiguity go?")
    print("=" * 78)
    print("  ⛔ Diagnosis only. No gate is re-run and no threshold moves.")

    print("\n  1. AMBIGUITY BY KEEP-SIZE (how many dependents were uttered)")
    a_k = by_keepsize(arch, "archive 60")
    v_k = by_keepsize(live, "v2 46")

    print("\n  2. THE MATRIX RULE'S OWN TARGET -- undecorated head alone")
    a_b = bare_head(arch, "archive 60, bare head")
    v_b = bare_head(live, "v2 46, bare head")

    print("\n  3. IS THE FREE aspect_root DECORATION DISAMBIGUATING?")
    print("     v2 has 11 referents with aspect_root_any vs the archive's 2.")
    a_a = aspect_effect(arch, "archive 60")
    v_a = aspect_effect(live, "v2 46")

    OUT.mkdir(exist_ok=True)
    (OUT / "phase9_2a_diag.json").write_text(json.dumps(
        {"note": "diagnosis of OUTCOME A; not a pre-registered measurement",
         "by_keepsize": {"archive": a_k, "v2": v_k},
         "bare_head": {"archive": a_b, "v2": v_b},
         "aspect_effect": {"archive": a_a, "v2": v_a}},
        indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'phase9_2a_diag.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
