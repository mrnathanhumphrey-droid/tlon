"""Review aid for referent signatures.

For each referent: construct the MINIMAL legal scene satisfying its signature,
render it, gloss it. A signature nobody can satisfy is dead on arrival, and a
witness is the cheapest way to see whether a pattern is too loose.

Then: the pairwise collision matrix -- which referents a single scene can
satisfy at once. Collisions are not automatically bugs (the water cluster
overlaps by design) but every one needs adjudicating.
"""
from __future__ import annotations
import itertools
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar.canon import utterance_id                    # noqa: E402
from tlon.grammar.gloss import gloss                           # noqa: E402
from tlon.grammar.parse import EventNode, Scene, parse, render  # noqa: E402
from tlon.referents import schema, match                       # noqa: E402

# Fallback only, for patterns that decline to name a relator. NOT 'u' first:
# BEYOND is spatially loaded, and defaulting to it made every peg read alike.
RELATORS = ["mil", "sen", "hlim"]


def witness(sig: schema.Signature) -> Scene | None:
    """Smallest scene satisfying `contains`: pattern 0 is the matrix, the rest
    hang off it as clauses, through the relator the signature asks for."""
    def mk(p: schema.NodePattern) -> EventNode:
        return EventNode(root=p.root_any[0],
                         orient=[p.orient_any[0]] if p.orient_any else [],
                         aspect=(p.aspect_root_any[0], 1) if p.aspect_root_any else None)
    head = mk(sig.contains[0])
    deep = []
    for i, p in enumerate(sig.contains[1:]):
        rel = p.via[0] if p.via else RELATORS[i % len(RELATORS)]
        if (p.at_depth or 1) > 1:
            deep.append((p.at_depth, rel, mk(p)))
            continue
        head.edges.append((rel, mk(p)))
    for want, rel, child in deep:        # scope patterns nest below depth 1
        cur, d = head, 0
        while d + 1 < want and cur.edges:
            cur = cur.edges[0][1]
            d += 1
        if d + 1 != want:
            return None
        cur.edges.append((rel, child))
    sc = Scene(node=head, force="ka")
    try:
        parse(render(sc))
    except Exception:
        return None
    return sc if match.matches(sc, sig) else None


def main() -> int:
    rs = schema.load(allow_unreviewed=True)
    print("=" * 78)
    print(f"SIGNATURE REVIEW — review_status={rs.review_status} "
          f"family={rs.grammar_family}")
    print("=" * 78)

    seeds = rs.seeds()
    print(f"\n2a seed: {len(seeds)} referents (tier 1). "
          f"Declared but excluded: {len(rs.referents) - len(seeds)}\n")

    wit: dict[str, Scene] = {}
    dead: list[str] = []
    for r in rs.referents:
        w = witness(r.signature)
        flag = "" if r.validated else "  ⚠ UNVALIDATED"
        if w is None:
            dead.append(r.id)
            print(f"[{r.id}] {r.name}{flag}\n      ✗ NO WITNESS — signature is unsatisfiable\n")
            continue
        wit[r.id] = w
        surf = render(w)
        print(f"[{r.id}] {r.name}{flag}")
        print(f"      {surf}")
        print(f"      \"{gloss(w)}\"")
        print(f"      {len(surf.split())} morphs · id {utterance_id(w)[:12]}\n")

    print("=" * 78)
    print("COLLISIONS — a witness matching more than its own referent")
    print("=" * 78)
    seed_ids = {r.id for r in seeds}
    collisions = 0
    for r in rs.referents:
        if r.id not in wit:
            continue
        also = [o.id for o in rs.referents
                if o.id != r.id and match.compat(wit[r.id], o)]
        if also:
            collisions += 1
            mark = "SEED" if r.id in seed_ids else "excl"
            print(f"  [{r.id}] ({mark}) {r.name}")
            print(f"        witness also matches: {', '.join(also)}")

    print(f"\n  witnesses colliding: {collisions}/{len(wit)}")

    print("\n" + "=" * 78)
    print("PAIRWISE CO-SATISFIABILITY (2a seed only) — can ONE scene match both?")
    print("=" * 78)
    pairs = 0
    for a, b in itertools.combinations(seeds, 2):
        merged = schema.Signature(contains=a.signature.contains + b.signature.contains,
                                  forbid=a.signature.forbid + b.signature.forbid)
        if len(merged.contains) - 1 > 3:      # clause cap; deeper nesting not tried
            continue
        w = witness(merged)
        if w is not None:
            pairs += 1
            print(f"  {a.id}+{b.id}  {a.name}  ×  {b.name}")
            print(f"        {render(w)}")
    print(f"\n  co-satisfiable seed pairs (flat witnesses only): {pairs}")

    if dead:
        print(f"\n⛔ UNSATISFIABLE SIGNATURES: {', '.join(dead)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
