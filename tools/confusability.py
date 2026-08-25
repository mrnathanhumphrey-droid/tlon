"""Phase 4 pre-check: does impression-SELECTION actually induce ambiguity?

WHY THIS RUNS BEFORE ANY POLICY CODE. Phase 3's null was unfalsifiable because
M was never scarce -- the signature core handed the listener the answer, so the
generator had no reason to build a code and KILL A could not fire. Phase 4's fix
is to let the generator utter only a SUBSET of the scene (impression-selection,
which is the project's thesis anyway) so reference resolution becomes genuinely
underdetermined.

That fix is conditional on a fact nobody has checked: the referent set must
actually OVERLAP. If every signature's head root is unique, a bare head
predication still names the referent, dropping dependents changes nothing, M
stays pinned, and phase 4 is phase 3's vacuous null in a new costume.

So: measure the induced ambiguity BEFORE building anything. What result would
have made this fire? Ambiguity > 1 under partial utterance. If it comes back at
1.0 everywhere, the referent set is the thing to fix, not the policy.

CONSISTENCY IS THE DUAL OF `matches`, NOT `matches`.
  matches(scene, sig)    -- every PATTERN finds a distinct node ("fully stated")
  consistent(scene, sig) -- every NODE finds a distinct pattern ("still possible")
A partial utterance of A does not `match` A -- it has not said enough. It is
still CONSISTENT with A, and with every other referent whose signature could be
completed the same way. That set is what a listener has to choose from, so that
set is the ambiguity.

Read-only. Trains nothing. Touches no module.
"""
from __future__ import annotations
import itertools
import json
import pathlib
import random
import statistics as S
import sys
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar import classes as C                          # noqa: E402
from tlon.grammar.parse import EventNode, ParseError, Scene, parse, render  # noqa: E402
from tlon.referents import schema                              # noqa: E402
from tlon.referents.match import consistent as _consistent    # noqa: E402
from tlon.referents.schema import Referent, Signature          # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
SAMPLES = 6          # scenes sampled per (referent, subset) -- free channels vary
SEED = 4242


# consistency now lives in the package (tlon/referents/match.py) as the dual
# of `matches`; re-exported here so existing tools keep importing it.
consistent = _consistent


# ── build a scene realising only a subset of the dependents ────────────────
def build_partial(ref: Referent, keep: tuple[int, ...],
                  rng: random.Random) -> Scene | None:
    """keep = indices into signature.contains[1:] that get uttered."""
    lex = C.load()["classes"]
    sig = ref.signature

    def node(pat) -> EventNode:
        n = EventNode(
            root=rng.choice(list(pat.root_any)),
            orient=[rng.choice(list(pat.orient_any))] if pat.orient_any else [])
        if pat.aspect_root_any:
            n.aspect = (rng.choice(list(pat.aspect_root_any)), 1)
        return n

    head = node(sig.contains[0])
    deep, used = [], set()
    for i in keep:
        pat = sig.contains[1 + i]
        child = node(pat)
        rel = rng.choice(list(pat.via)) if pat.via else rng.choice(list(lex["L"]))
        if (pat.at_depth or 1) > 1:
            deep.append((pat.at_depth, rel, child))
            continue
        if (rel, child.root) in used:
            return None
        used.add((rel, child.root))
        head.edges.append((rel, child))
    for want, rel, child in deep:
        cur, d = head, 0
        while d + 1 < want and cur.edges:
            cur = cur.edges[0][1]
            d += 1
        if d + 1 != want:
            return None      # its anchor was dropped; this subset is unbuildable
        cur.edges.append((rel, child))
    sc = Scene(node=head, force=rng.choice(sorted(lex["F"])))
    try:
        parse(render(sc))
    except (ParseError, ValueError):
        return None
    return sc


def verdict(ceiling: float, bare: float, frac_amb: float, mutual: int) -> str:
    """Branch on the CEILING, not on mean ambiguity.

    The first version of this branched on full-utterance ambiguity and called
    any of it "confounded". That conflates two different things. A full scene of
    A sitting inside B's larger signature is not a broken signature -- B is
    merely not finished being described, and a listener with a prior over
    omission can still prefer A. Only MUTUAL consistency is irreducible.
    """
    v = ("UNRECOGNISED -- none of the enumerated branches matched. Read the "
         "tables by hand before concluding anything.")
    if bare <= 1.05 and frac_amb < 0.02:
        v = ("DEAD. Selection induces NO ambiguity: even a bare head predication "
             "names the referent. Phase 4 as designed would reproduce phase 3's "
             "vacuous null. FIX THE REFERENT SET FIRST -- do not build the "
             "selection policy.")
    elif ceiling >= 0.97:
        v = (f"THIN. A perfect listener still reaches {100 * ceiling:.1f}%, so "
             "selection barely costs M. The generator would have almost no "
             "incentive to recover information through the free channels and "
             "KILL A stays hard to reach. Widen the overlap first.")
    elif ceiling < 0.97 and mutual == 0:
        v = (f"LIVE. Ceiling {100 * ceiling:.1f}% -- selection costs real M, and "
             "every ambiguity is ASYMMETRIC (no two referents are mutually "
             "indistinguishable). That is recoverable information, which is "
             "exactly the incentive a cipher would exploit. KILL A becomes "
             "reachable and the listener's target is well defined.")
    elif ceiling < 0.97 and mutual > 0:
        v = (f"LIVE WITH A FLOOR. Ceiling {100 * ceiling:.1f}%, but {mutual} "
             "MUTUALLY indistinguishable referent pairs exist -- no listener "
             "can ever separate those, so part of the gap is irreducible. "
             "Usable, but the M target must be stated against this ceiling, "
             "never against 100%.")
    return v


def main() -> int:
    rng = random.Random(SEED)
    refs = schema.load_all().referents
    n = len(refs)
    print("=" * 78)
    print("CONFUSABILITY -- does impression-selection make reference underdetermined?")
    print("=" * 78)
    print(f"\n  {n} referents")

    # ── 1. the cheapest, most decisive number: head-root collisions ────────
    head_roots: dict[str, list[str]] = defaultdict(list)
    for r in refs:
        for form in r.signature.contains[0].root_any:
            head_roots[form].append(r.id)
    shared = {k: v for k, v in head_roots.items() if len(v) > 1}
    reach = Counter()
    for r in refs:
        hits = set()
        for form in r.signature.contains[0].root_any:
            hits |= set(head_roots[form])
        reach[r.id] = len(hits)
    solo = sum(1 for r in refs if reach[r.id] == 1)
    print(f"\n  HEAD-ROOT COLLISIONS")
    print(f"    distinct head roots in use : {len(head_roots)}")
    print(f"    head roots shared by >1 ref: {len(shared)}")
    print(f"    referents whose head root is UNIQUE to them: {solo}/{n}"
          f"   {'<-- these can never be confused by a bare head' if solo else ''}")
    print(f"    mean referents reachable from a head root: {S.fmean(reach.values()):.2f}")

    # ── 2. ambiguity vs how much was dropped ──────────────────────────────
    by_dropped: dict[int, list[int]] = defaultdict(list)
    ceiling_cases: list[float] = []
    full_amb, bare_amb, all_amb = [], [], []
    unbuildable = 0
    per_ref = {}
    for r in refs:
        deps = len(r.signature.contains) - 1
        idx = list(range(deps))
        ref_rows = []
        for k in range(deps + 1):
            for keep in itertools.combinations(idx, k):
                counts = []
                for _ in range(SAMPLES):
                    sc = build_partial(r, keep, rng)
                    if sc is None:
                        unbuildable += 1
                        continue
                    counts.append(sum(1 for b in refs if consistent(sc, b.signature)))
                if not counts:
                    continue
                mean_c = S.fmean(counts)
                # Bayes-optimal accuracy on this case: a perfect listener knows
                # only which referents remain possible, so it can do no better
                # than a uniform pick among them. THIS is the M ceiling under
                # selection, and the number that decides whether phase 4 has
                # any pressure to apply.
                ceiling_cases.append(S.fmean([1.0 / c for c in counts]))
                dropped = deps - k
                by_dropped[dropped].append(mean_c)
                all_amb.append(mean_c)
                if dropped == 0:
                    full_amb.append(mean_c)
                if k == 0:
                    bare_amb.append(mean_c)
                ref_rows.append({"keep": list(keep), "dropped": dropped,
                                 "mean_consistent": mean_c})
        per_ref[r.id] = {"name": r.name, "deps": deps, "rows": ref_rows}

    print(f"\n  AMBIGUITY BY HOW MANY DEPENDENTS WERE DROPPED")
    print(f"    {'dropped':>8} {'cases':>7} {'mean':>7} {'median':>7} {'max':>6}"
          f"  {'% ambiguous':>12}")
    for d in sorted(by_dropped):
        v = by_dropped[d]
        amb = sum(1 for x in v if x > 1.0) / len(v)
        print(f"    {d:>8} {len(v):>7} {S.fmean(v):>7.2f} {S.median(v):>7.2f} "
              f"{max(v):>6.1f}  {100 * amb:>11.1f}%")

    full = S.fmean(full_amb) if full_amb else float("nan")
    bare = S.fmean(bare_amb) if bare_amb else float("nan")
    frac_amb = sum(1 for x in all_amb if x > 1.0) / len(all_amb) if all_amb else 0.0

    print(f"\n    fully stated  : {full:.3f} consistent referents on average")
    print(f"    bare head only: {bare:.3f}")
    print(f"    share of all (referent, subset) cases that are ambiguous: "
          f"{100 * frac_amb:.1f}%")
    if unbuildable:
        print(f"    unbuildable subsets skipped (dropped anchor / dup edge): {unbuildable}")

    # ── 3. worst offenders, the pairs a listener will actually fight ──────
    ceiling = S.fmean(ceiling_cases) if ceiling_cases else float("nan")
    print(f"\n  M CEILING UNDER SELECTION")
    print(f"    a PERFECT listener, uniform over the possible referents, reaches"
          f" {100 * ceiling:.1f}%")
    print(f"    (phase 3 ran at 99.2-100%, i.e. no pressure at all)")

    # ── 4. mutual vs asymmetric: which ambiguity is irreducible? ──────────
    full_scene = {}
    for r in refs:
        deps = len(r.signature.contains) - 1
        sc = build_partial(r, tuple(range(deps)), rng)
        if sc is not None:
            full_scene[r.id] = sc
    fits = {a: {b.id for b in refs
                if b.id != a and consistent(full_scene[a], b.signature)}
            for a in full_scene}
    mutual_pairs = sorted({tuple(sorted((a, b))) for a, bs in fits.items()
                           for b in bs if a in fits.get(b, set())})
    asym = sum(len(bs) for bs in fits.values()) - 2 * len(mutual_pairs)
    print(f"\n  IS THE FULL-UTTERANCE AMBIGUITY IRREDUCIBLE?")
    print(f"    MUTUAL pairs (neither can ever be told from the other): "
          f"{len(mutual_pairs)}")
    for a, b in mutual_pairs[:8]:
        na = next(r.name for r in refs if r.id == a)
        nb = next(r.name for r in refs if r.id == b)
        print(f"      {a} {na[:30]:<30} <-> {b} {nb[:30]}")
    print(f"    ASYMMETRIC containments (A's full scene fits inside B's larger "
          f"signature): {asym}")
    print(f"      -> recoverable: a listener with a prior over omission can "
          f"still prefer A")

    print(f"\n  MOST CONFUSABLE REFERENTS (highest mean over all subsets)")
    worst = sorted(((S.fmean([x["mean_consistent"] for x in v["rows"]]), k, v)
                    for k, v in per_ref.items() if v["rows"]), reverse=True)[:8]
    for m, k, v in worst:
        print(f"    {k:>4} {v['name'][:44]:<44} {m:>5.2f}")

    print(f"\n  VERDICT: {verdict(ceiling, bare, frac_amb, len(mutual_pairs))}")

    (OUT / "confusability.json").write_text(json.dumps({
        "n_referents": n, "head_roots": len(head_roots),
        "shared_head_roots": {k: v for k, v in shared.items()},
        "unique_head_referents": solo,
        "full": full, "bare": bare, "frac_ambiguous": frac_amb,
        "by_dropped": {str(k): S.fmean(v) for k, v in by_dropped.items()},
        "per_referent": per_ref,
        "ceiling": ceiling, "mutual_pairs": [list(x) for x in mutual_pairs],
        "asymmetric": asym,
        "verdict": verdict(ceiling, bare, frac_amb, len(mutual_pairs)),
    }, indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'confusability.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
