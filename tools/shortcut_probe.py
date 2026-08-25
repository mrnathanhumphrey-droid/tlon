"""Can a single cheap feature solve a pair set without reading structure?

Bag-of-roots is not the only shortcut. Two more, both trivial:

  MATRIX-ROOT-ONLY  -- the last root before the coda. Sur is head-final, so the
                       matrix is always in a fixed position. Perspective pairs
                       flip which happening is the matrix, so this ONE feature
                       may solve all ten without the model learning anything
                       beyond "look at the end".
  FIRST-MORPHEME    -- the leading orientation particle, same idea from the front.

If either sweeps a set, that set does not test what it claims to test.
"""
from __future__ import annotations
import collections
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar import classes as C                  # noqa: E402
from tlon.grammar.parse import render                  # noqa: E402
from tlon.referents import schema                      # noqa: E402
from tlon.selfplay import scenes as gen                # noqa: E402

N = 240
REF = pathlib.Path(__file__).resolve().parents[1] / "tlon" / "referents"


def matrix_root(surface: str) -> str:
    """Head-final: the matrix root is the last R token before the coda."""
    lex = C.load()["classes"]
    for tok in reversed(surface.split()):
        if tok in lex["R"]:
            return tok
    return "?"


def first_morph(surface: str) -> str:
    return surface.split()[0]


def probe(path: pathlib.Path, label: str) -> None:
    rs = schema.load(path, allow_unreviewed=True)
    pairs: dict[str, list] = collections.defaultdict(list)
    for r in rs.referents:
        pairs[r.minimal_pair].append(r)
    rng = random.Random(5150)

    print(f"\n{'=' * 72}\n{label}\n{'=' * 72}")
    print(f"{'pair':6} {'contrast':13} {'matrix-root':>12} {'first-morph':>12}")
    tot_m, tot_f, n = 0.0, 0.0, 0
    for pid in sorted(pairs, key=lambda k: int(k[1:])):
        a, b = pairs[pid]
        feats = {"m": collections.defaultdict(collections.Counter),
                 "f": collections.defaultdict(collections.Counter)}
        rows = []
        for lab, r in enumerate((a, b)):
            for _ in range(N):
                s = render(gen.sample(r, rng, blend_pool=[a, b], blend_p=0.0))
                rows.append((lab, matrix_root(s), first_morph(s)))
        for lab, m, f in rows:
            feats["m"][m][lab] += 1
            feats["f"][f][lab] += 1
        # accuracy of "predict the majority label for this feature value"
        def acc(table):
            right = sum(max(c.values()) for c in table.values())
            return right / len(rows)
        am, af = acc(feats["m"]), acc(feats["f"])
        tot_m += am; tot_f += af; n += 1
        flag_m = "  ← SOLVES IT" if am > 0.9 else ""
        print(f"{pid:6} {a.contrast:13} {100 * am:11.1f}% {100 * af:11.1f}%{flag_m}")
    print(f"{'mean':6} {'':13} {100 * tot_m / n:11.1f}% {100 * tot_f / n:11.1f}%")


def main() -> int:
    probe(REF / "imagery_pairs.draft.yaml", "PERSPECTIVE PAIRS (J1–J10)")
    probe(REF / "minimal_pairs.draft.yaml", "CHANNEL DIAGNOSTICS (P1–P10)")
    print("\nA feature at ~100% means that set is solvable without reading")
    print("structure. A set is only a real test if EVERY cheap feature is near")
    print("chance on it, or if the set mixes contrasts so no single one sweeps.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
