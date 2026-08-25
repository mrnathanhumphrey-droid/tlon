"""Verify the property that makes the minimal pairs a test rather than a hope.

Asserts, rather than trusting the YAML comment, that:
  1. every pair has exactly two members;
  2. their root multisets are IDENTICAL, so bag-of-roots is pinned at 50 %
     within the pair BY CONSTRUCTION;
  3. each pair is separable by SOMETHING -- witnesses exist and do not
     cross-match, so the contrast is real and not merely asserted;
  4. an actual bag-of-roots feature vector cannot separate them, measured on
     generated scenes rather than argued from the schema.

(4) is the one that could come back negative even if (2) passes -- decoration
and blended nodes add roots the signature never mentions.
"""
from __future__ import annotations
import collections
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar import classes as C                     # noqa: E402
from tlon.grammar.gloss import gloss                      # noqa: E402
from tlon.grammar.parse import render                     # noqa: E402
from tlon.referents import match, schema                  # noqa: E402
from tlon.selfplay import scenes as gen                   # noqa: E402
from signature_report import witness                      # noqa: E402

PATH = pathlib.Path(__file__).resolve().parents[1] / "tlon" / "referents" / "imagery_pairs.draft.yaml"
N = 300


def _bag_of_roots_on_pair(a, b, rng) -> float:
    """Fit the pre-registered baseline on just this pair. Held-out accuracy
    should sit at chance if the pair is genuinely minimal."""
    from tlon.grammar.canon import utterance_id
    from tlon.grammar.parse import render as _render
    from tlon.listener import baselines, tokenizer as tk
    from tlon.listener.data import Example

    rows, seen = [], set()
    for label, r in enumerate((a, b)):
        made = 0
        while made < N:
            sc = gen.sample(r, rng, blend_pool=[a, b], blend_p=0.3)
            uid = utterance_id(sc)
            if uid in seen:
                continue
            seen.add(uid)
            surf = _render(sc)
            try:
                ids = tk.encode(surf)
            except ValueError:
                continue
            rows.append(Example(label=label, ref_id=r.id, surface=surf,
                                uid=uid, ids=ids, dec_key=""))
            made += 1
    rng.shuffle(rows)
    cut = int(len(rows) * 0.3)
    te, tr = rows[:cut], rows[cut:]
    return baselines.bag_of_roots(tr, {"t": te}, 2)["t"]


def main() -> int:
    rs = schema.load(PATH, allow_unreviewed=True)
    refs = rs.referents
    pairs: dict[str, list] = collections.defaultdict(list)
    for r in refs:
        pairs[r.minimal_pair].append(r)

    print("=" * 78)
    print(f"MINIMAL PAIRS — {len(pairs)} pairs, {len(refs)} referents "
          f"(status {rs.review_status})")
    print("=" * 78)

    fails = 0
    measured: dict[str, float] = {}
    rng = random.Random(31337)
    lex = C.load()["classes"]

    for pid in sorted(pairs, key=lambda k: int(k[1:])):
        a, b = pairs[pid]
        wa, wb = witness(a.signature), witness(b.signature)
        same_roots = a.roots() == b.roots()

        print(f"\n[{pid}] {a.contrast.upper()}   {a.id}/{b.id}")
        print(f"  {a.id} {a.name}")
        print(f"     {render(wa) if wa else '— UNSATISFIABLE —'}")
        if wa:
            print(f"     \"{gloss(wa)}\"")
        print(f"  {b.id} {b.name}")
        print(f"     {render(wb) if wb else '— UNSATISFIABLE —'}")
        if wb:
            print(f"     \"{gloss(wb)}\"")

        roots_str = " ".join(f"{r}({lex['R'][r]})" for r in dict.fromkeys(a.roots()))
        print(f"  roots: {roots_str}")

        if len(pairs[pid]) != 2:
            print("  ✗ not exactly two members"); fails += 1
        if not same_roots:
            print(f"  ✗ ROOT MULTISETS DIFFER — {a.roots()} vs {b.roots()}")
            print("     bag-of-roots could separate these; not a minimal pair")
            fails += 1
        else:
            print("  ✓ identical root multisets — bag-of-roots pinned at 50%")
        if wa is None or wb is None:
            print("  ✗ unsatisfiable"); fails += 1
            continue
        if match.compat(wa, b) or match.compat(wb, a):
            print("  ✗ witnesses cross-match — the contrast does not separate them")
            fails += 1
        else:
            print("  ✓ witnesses separate")

        # (4) MEASURED, not argued: actually fit bag-of-roots on the pair.
        # An earlier version compared which roots APPEARED in each sample --
        # that just measured random decoration differing between two draws and
        # flagged noise as leakage. Fit the classifier instead; it is the thing
        # the claim is about.
        acc = _bag_of_roots_on_pair(a, b, rng)
        measured[pid] = round(100 * acc, 1)
        if acc > 0.60:
            print(f"  ✗ bag-of-roots scores {100 * acc:.1f}% on this pair — "
                  "root evidence separates them")
            fails += 1
        else:
            print(f"  ✓ bag-of-roots {100 * acc:.1f}% (chance = 50%)")

    import json as _json
    dump = pathlib.Path(__file__).resolve().parents[1] / "runs" / "imagery_pairs_bor.json"
    dump.parent.mkdir(exist_ok=True)
    dump.write_text(_json.dumps(measured, indent=2), encoding="utf-8", newline="")
    print(f"\n  wrote {dump}")

    print("\n" + "=" * 78)
    if fails:
        print(f"⛔ {fails} PROBLEM(S) — not ready for review")
        return 1
    print("✓ ALL PAIRS VALID — bag-of-roots is at chance within every pair,")
    print("  by construction and by measurement. The listener must read")
    print("  structure or score 50%.")
    contrasts = collections.Counter(r.contrast for r in refs)
    print("\n  contrast coverage: " +
          "  ".join(f"{k}×{v // 2}" for k, v in sorted(contrasts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

