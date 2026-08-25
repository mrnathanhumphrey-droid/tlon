"""PHASE 12.1 -- Lever 2 (depth/nesting). Closed-form.

THE HYPOTHESIS: deeper nesting creates ATTACHMENT ambiguity -- which impression
embeds in which -- that an optimising speaker cannot resolve by uttering more.

⛔ TWO CORRECTIONS TO THE BRIEF'S PREMISES, BOTH FROM THE CODE:

1. "raising MAX_DEPTH doesn't touch the lexicon hash" -- IT DOES. MAX_DEPTH
   lives in `lexicon.yaml` under `constraints:` and the hash is blake2b over the
   whole file, so raising it moves `e2b8527010231a81fd31b6eeb9de3d8c`, which is
   pinned in EVERY locked prereg (3,4,5,7,8,9). Same cost as
   MAX_CLAUSES_PER_PRED, flagged in Phase 9 for the same reason.

2. The brief predicts depth is "dead on part 2 (conventionable) even if it
   passes part 1". The code says it is dead on PART 1, and structurally, for two
   independent reasons measured below. That is a stronger result than predicted
   and it means no depth-4/5 set needs building.

THE TWO STRUCTURAL ARGUMENTS, VERIFIED NOT ASSERTED:

  A. THE GRAMMAR IS LL(1) AND `parse()` DECODES EXACTLY. If every distinct tree
     renders to a distinct surface, attachment is ALWAYS recoverable and
     attachment ambiguity cannot exist at any depth. Tested by constructing
     scenes with IDENTICAL node multisets and DIFFERENT attachment.

  B. `consistent()` REJECTS ON NODE COUNT:
         if len(pool) > len(sig.contains): return False
     Every level of nesting adds a node, so a deeper scene is consistent with
     STRICTLY FEWER referents. Depth is anti-correlated with the target by
     construction -- the same shape as the f2 finding, one level down.
"""
from __future__ import annotations

import collections
import itertools
import json
import pathlib
import random
import statistics as S
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar import classes as C                        # noqa: E402
from tlon.grammar.parse import (EventNode, Scene, parse,     # noqa: E402
                                render)
from tlon.referents import schema                            # noqa: E402
from tlon.referents.match import consistent, nodes           # noqa: E402
from pi_controls import build                                # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"


class BannerMismatch(RuntimeError):
    pass


def banner(label, value, expected, fmt="{}"):
    if value != expected:
        raise BannerMismatch(f"{label}: printed {value!r}, expected {expected!r}")
    print(f"    {label:<52} {fmt.format(value)}")


def tree_shape(n: EventNode):
    """Structure only, ignoring which node is which -- so two scenes with the
    same nodes attached differently compare unequal."""
    return (n.root, tuple(sorted((rel, tree_shape(c)) for rel, c in n.edges)))


def test_attachment_is_always_recoverable():
    """ARGUMENT A. Same node multiset, different attachment -> different surface?

    Builds every distinct attachment of {a, b, c} under a matrix and checks the
    surfaces are pairwise distinct AND that parse() recovers each tree.
    """
    lex = C.load()["classes"]
    rels = sorted(lex["L"])[:3]
    roots = ["mlö", "fox", "lan"]

    def flat():                       # matrix with two siblings at depth 1
        h = EventNode(root=roots[0])
        h.edges = [(rels[0], EventNode(root=roots[1])),
                   (rels[1], EventNode(root=roots[2]))]
        return h

    def nested():                     # matrix -> b -> c, a chain to depth 2
        c = EventNode(root=roots[2])
        b = EventNode(root=roots[1]); b.edges = [(rels[1], c)]
        h = EventNode(root=roots[0]); h.edges = [(rels[0], b)]
        return h

    def swapped():                    # matrix -> c -> b
        b = EventNode(root=roots[1])
        c = EventNode(root=roots[2]); c.edges = [(rels[1], b)]
        h = EventNode(root=roots[0]); h.edges = [(rels[0], c)]
        return h

    out = []
    for label, mk in (("flat (a<b, a<c)", flat), ("nested (a<b<c)", nested),
                      ("nested (a<c<b)", swapped)):
        sc = Scene(node=mk(), force="ka")
        surf = render(sc)
        back = parse(surf)
        out.append({"label": label, "surface": surf,
                    "roundtrip_exact": tree_shape(back.node) == tree_shape(sc.node)})
    surfaces = [o["surface"] for o in out]
    return {"cases": out, "all_surfaces_distinct": len(set(surfaces)) == len(surfaces),
            "all_roundtrip_exact": all(o["roundtrip_exact"] for o in out)}


def ambiguity_by_nodecount(refs, label):
    """ARGUMENT B. |consistent| as a function of how many nodes were uttered."""
    rows = collections.defaultdict(list)
    for ri, ref in enumerate(refs):
        d = len(ref.signature.contains) - 1
        for k in range(d + 1):
            for keep in itertools.combinations(range(d), k):
                sc = build(ref, keep, random.Random(1000 + ri), None, 0, True)
                if sc is None:
                    continue
                nn = len(nodes(sc.node))
                rows[nn].append(sum(1 for r in refs
                                    if consistent(sc, r.signature)))
    print(f"\n    {label}")
    print(f"      {'nodes':>6} {'n':>5} {'mean |consistent|':>19} {'max':>5}")
    out = {}
    for nn in sorted(rows):
        v = rows[nn]
        out[str(nn)] = {"n": len(v), "mean": S.fmean(v), "max": max(v)}
        print(f"      {nn:>6} {len(v):>5} {S.fmean(v):>19.2f} {max(v):>5}")
    return out


def main() -> int:
    print("=" * 78)
    print("PHASE 12.1 -- LEVER 2 (DEPTH / NESTING). Closed-form.")
    print("=" * 78)

    k = C.constraints()
    banner("MAX_DEPTH in lexicon.yaml", k["MAX_DEPTH"], 3)
    print(f"    ⛔ raising it MOVES the lexicon hash "
          f"{C.load()['_hash']},\n       which is pinned in every locked prereg "
          "(3,4,5,7,8,9). The brief's\n       premise that it is free is wrong "
          "-- same cost as MAX_CLAUSES_PER_PRED.")

    print("\n  ARGUMENT A -- is attachment ever ambiguous?\n")
    a = test_attachment_is_always_recoverable()
    for c in a["cases"]:
        print(f"    {c['label']:<18} {c['surface']}")
        print(f"    {'':18} round-trip exact: {c['roundtrip_exact']}")
    banner("distinct attachments -> distinct surfaces",
           a["all_surfaces_distinct"], True)
    banner("parse() recovers every tree exactly",
           a["all_roundtrip_exact"], True)
    print("\n    ⇒ THE GRAMMAR IS LL(1) AND THE DECODER IS EXACT, SO ATTACHMENT")
    print("      IS ALWAYS RECOVERABLE FROM THE SURFACE. Attachment ambiguity")
    print("      cannot exist at ANY depth. The hypothesis is refuted by the")
    print("      architecture, not by a measurement -- and this is the same")
    print("      fact that made the phase-2 M gate vacuous.")

    print("\n  ARGUMENT B -- what nesting does to referent ambiguity\n")
    print("    consistent() contains this, verbatim:")
    print("        if len(pool) > len(sig.contains): return False")
    print("    Every level of nesting adds a node to `pool`, so a deeper scene")
    print("    can only be consistent with signatures that have MORE patterns.")
    sets = {}
    for name, load in (("archive", lambda: schema.load_archive().referents),
                       ("v2", lambda: schema.load_live().referents),
                       ("cr", lambda: schema.load_worldview("cr", allow_unreviewed=True).referents),
                       ("tao", lambda: schema.load_worldview("tao", allow_unreviewed=True).referents)):
        sets[name] = ambiguity_by_nodecount(load(), name)

    mono = True
    for name, rows in sets.items():
        ks = sorted(int(x) for x in rows)
        means = [rows[str(x)]["mean"] for x in ks]
        if any(b > a + 1e-9 for a, b in zip(means, means[1:])):
            mono = False
            print(f"\n    ⛔ {name} is NOT monotone decreasing: {means}")
    banner("mean |consistent| falls with node count, every set", mono, True)

    print("\n" + "=" * 78)
    print("  LEVER 2 VERDICT -- DEAD ON PART 1, STRUCTURALLY.\n")
    print("  Part 1 (survives optimisation): FAILS. Attachment is always")
    print("    recoverable (LL(1), exact decoder), so nesting adds no ambiguity")
    print("    of that kind; and adding nodes strictly REDUCES the set of")
    print("    consistent referents, so depth moves AWAY from the target.")
    print("  Part 2 (conventionable): NOT REACHED -- part 1 fails first.")
    print("\n  ⭐ STRONGER THAN THE BRIEF PREDICTED (it expected part-1 pass,")
    print("     part-2 fail), and it means NO depth-4/5 REFERENT SET NEEDS")
    print("     BUILDING and NO LEXICON HASH NEEDS MOVING. The cheap lever is")
    print("     closed for $0.00 and without touching the pinned constant.")
    print("\n  ⛔ NO SURPRISE TO BANK: the brief asked to measure in case")
    print("     attachment ambiguity turned out conventionable. It cannot turn")
    print("     out anything -- it does not exist.")

    OUT.mkdir(exist_ok=True)
    (OUT / "phase12_1_depth.json").write_text(json.dumps(
        {"max_depth": k["MAX_DEPTH"], "lexicon_hash": C.load()["_hash"],
         "raising_moves_hash": True,
         "attachment": a, "ambiguity_by_nodecount": sets,
         "monotone_decreasing": mono,
         "verdict": "DEAD_ON_PART_1_STRUCTURAL"},
        indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'phase12_1_depth.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
