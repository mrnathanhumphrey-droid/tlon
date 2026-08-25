"""Natural ambiguity: how often does a scene generated FOR A also match B?

Replaces the junked "45 co-satisfiable pairs" number, which measured the clause
cap rather than the signatures and could not have come back negative. This one
can: if the signatures were perfectly disjoint under natural generation, every
figure below would be zero.

Reported at two blend rates so the effect of the sampler is separable from the
effect of the signatures -- the whole reason the first 2a run read 0%.
"""
from __future__ import annotations
import collections
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.referents import match, schema          # noqa: E402
from tlon.selfplay import scenes                  # noqa: E402

N = 400


def measure(seeds, blend_p: float, seed: int = 4242) -> dict:
    rng = random.Random(seed)
    pair = collections.Counter()
    amb = collections.Counter()
    per_ref = collections.Counter()
    total = 0
    for ref in seeds:
        for _ in range(N):
            sc = scenes.sample(ref, rng, blend_pool=seeds, blend_p=blend_p)
            hits = sorted(r.id for r in match.resolve(sc, seeds))
            assert ref.id in hits, "a scene must always match its own referent"
            total += 1
            amb[len(hits)] += 1
            if len(hits) > 1:
                per_ref[ref.id] += 1
                for other in hits:
                    if other != ref.id:
                        pair[tuple(sorted((ref.id, other)))] += 1
    return {"total": total, "amb": amb, "pair": pair, "per_ref": per_ref}


def show(tag: str, r: dict) -> None:
    total = r["total"]
    multi = total - r["amb"][1]
    print(f"\n--- {tag} ---")
    print(f"  scenes                {total}")
    print(f"  matching >1 referent  {multi}  ({100 * multi / total:.2f}%)")
    if r["amb"]:
        dist = "  ".join(f"{k}:{v}" for k, v in sorted(r["amb"].items()))
        print(f"  ambiguity spread      {dist}")
    if r["pair"]:
        print("  top colliding pairs:")
        for (a, b), n in r["pair"].most_common(8):
            print(f"      {a}+{b}   {n:5d}  ({100 * n / total:.2f}% of all scenes)")
    if r["per_ref"]:
        print("  referents that most often bleed:")
        for rid, n in r["per_ref"].most_common(5):
            print(f"      {rid}   {n}/{N}  ({100 * n / N:.1f}%)")


def reachability(seeds, k: int = 120, seed: int = 909) -> dict:
    """For each ordered pair (A, B): generate scenes FOR A while forcing the
    blended clause to come from B, and count how many also match B.

    Separates two things the natural rate confounds -- whether a pair CAN
    collide at all, and whether an untargeted sampler happens to try. A pair
    unreachable even under a targeted attempt is genuinely disjoint.
    """
    rng = random.Random(seed)
    out: dict[tuple[str, str], int] = {}
    for a in seeds:
        for b in seeds:
            if a.id == b.id:
                continue
            hits = 0
            for _ in range(k):
                sc = scenes.sample(a, rng, decorate_p=1.0, blend_pool=seeds,
                                   blend_p=1.0, blend_donor=b)
                if b.id in {r.id for r in match.resolve(sc, seeds)}:
                    hits += 1
            out[(a.id, b.id)] = hits
    return out


def main() -> int:
    rs = schema.load()
    seeds = rs.seeds()
    print("=" * 74)
    print("NATURAL AMBIGUITY — scenes generated for A that also match B")
    print("=" * 74)

    off = measure(seeds, blend_p=0.0)
    on = measure(seeds, blend_p=0.6)
    show("blend OFF (what the first 2a run actually sampled)", off)
    show("blend ON  (extra clause drawn from another peg's signature)", on)

    off_multi = off["total"] - off["amb"][1]
    on_multi = on["total"] - on["amb"][1]
    print("\n" + "=" * 74)
    print("READ")
    print("=" * 74)
    print(f"  blend off  {100 * off_multi / off['total']:.2f}%   "
          f"blend on  {100 * on_multi / on['total']:.2f}%")
    if off_multi == 0 and on_multi > 0:
        print("  CONFIRMED: the first run's 0% ambiguity measured the SAMPLER,")
        print("  not the signatures. The overlap regions were unreachable, not absent.")
    elif on_multi <= off_multi:
        print("  blending did not open the overlap regions — sampler still too narrow.")
    hit = on["pair"].get(("03", "15"), 0)
    print(f"\n  03+15 (the overlap Nate ruled in): {hit} scenes "
          f"({100 * hit / on['total']:.2f}%) under untargeted blending")

    print("\n" + "=" * 74)
    print("TARGETED REACHABILITY — can A and B collide when we actually try?")
    print("=" * 74)
    K = 120
    reach = reachability(seeds, k=K)
    pairs = {}
    for (a, b), n in reach.items():
        key = tuple(sorted((a, b)))
        pairs[key] = max(pairs.get(key, 0), n)
    live = {k: v for k, v in pairs.items() if v}
    print(f"  unordered pairs tested        {len(pairs)}")
    print(f"  pairs reachable                {len(live)}  "
          f"({100 * len(live) / len(pairs):.0f}%)")
    print(f"  pairs NOT reached             {len(pairs) - len(live)}")
    print("  ⚠ 'not reached' is NOT 'disjoint'. This probe blends exactly ONE")
    print("    donor node, so a pair needing two would read as unreachable here.")
    print("    The check is narrower than the claim — treat it as a lower bound.")
    print(f"\n  most reachable (of {K} targeted attempts):")
    for (a, b), n in sorted(live.items(), key=lambda x: -x[1])[:10]:
        print(f"      {a}+{b}   {n:3d}/{K}  ({100 * n / K:.0f}%)")
    r0315 = pairs.get(("03", "15"), 0)
    print(f"\n  03+15 targeted: {r0315}/{K} ({100 * r0315 / K:.0f}%)")
    if r0315 == 0:
        print("  ⛔ the ruled-in overlap is UNREACHABLE by generation, only by hand.")
    else:
        print("  Reachable by generation, and rare when untargeted — which is what")
        print("  a ruled-in-but-uncommon overlap should look like.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
