"""Validate the generating-function counts against brute-force enumeration.

The Phase 0 verdict rests on numbers with 45 digits produced by a closed form.
A closed form is a claim, not a measurement. This test shrinks the grammar to
a size where EVERY legal string can actually be enumerated, and demands the
two methods agree exactly -- for surface counts and for canonical counts, at
every nesting depth.

If this test can't fail, it isn't evidence: test_counting_detects_an_error()
mutates the closed form and asserts the comparison goes red.
"""
from __future__ import annotations
import itertools
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tlon.grammar import enumerate as E   # noqa: E402


# ── reference enumerator: builds strings straight from the BNF ─────────────
def ref_enumerate(sizes: dict, caps: dict):
    """Yield (surface_tuple, canon_key) for every legal utterance.

    Deliberately written from the BNF in spec §4.1 rather than from
    enumerate.py, so a shared bug cannot hide in both.
    """
    Q = [None] + [("Q", i) for i in range(sizes["Q"])]
    T = [None] + [("T", i) for i in range(sizes["T"])]
    M = [None] + [("M", i) for i in range(sizes["M"])]
    O = [("O", i) for i in range(sizes["O"])]
    L = [("L", i) for i in range(sizes["L"])]
    R = [("R", i) for i in range(sizes["R"])]
    D = [None] + [("D", i) for i in range(sizes["D"])]
    A = [None] + [("A", i, r) for i in range(sizes["A"])
                  for r in range(1, caps["MAX_ASPECT_REPS"] + 1)]
    F = [("F", i) for i in range(sizes["F"])]

    def nuclei(budget):
        for r, a, d in itertools.product(R, A, D):
            cost = 1 + (0 if a is None else a[2] + 1) + (0 if d is None else 1)
            if cost <= budget:
                toks = [r] + ([a] if a else []) + ([d] if d else [])
                yield toks, cost, (r, a, d)

    def preds(depth, budget):
        for q, t, m in itertools.product(Q, T, M):
            pre = [x for x in (q, t, m) if x]
            if len(pre) > budget:
                continue
            for no in range(caps["MAX_ORIENT_PER_PRED"] + 1):
                for osq in itertools.permutations(O, no):
                    b1 = budget - len(pre) - no
                    if b1 < 1:
                        continue
                    maxc = caps["MAX_CLAUSES_PER_PRED"] if depth > 0 else 0
                    for nc in range(maxc + 1):
                        for csq, ccost, ckeys in clause_seqs(depth, b1, nc):
                            b2 = b1 - ccost
                            if b2 < 1:
                                continue
                            for ntoks, ncost, nkey in nuclei(b2):
                                toks = pre + list(osq) + csq + ntoks
                                key = (nkey, q, t, m,
                                       tuple(sorted(osq)),
                                       tuple(sorted(ckeys, key=repr)))
                                yield toks, len(pre) + no + ccost + ncost, key

    def clause_seqs(depth, budget, nc):
        if nc == 0:
            yield [], 0, ()
            return
        pool = []
        for rel in L:
            for ptoks, pcost, pkey in preds(depth - 1, budget - 1):
                pool.append(([rel] + ptoks, pcost + 1, (rel, pkey)))
        for combo in itertools.permutations(pool, nc):
            keys = [c[2] for c in combo]
            if len(set(map(repr, keys))) != nc:      # duplicate siblings
                continue
            cost = sum(c[1] for c in combo)
            if cost <= budget:
                toks = [tok for c in combo for tok in c[0]]
                yield toks, cost, tuple(keys)

    for f in F:
        for toks, cost, key in preds(caps["MAX_DEPTH"], caps["MAX_MORPHS"] - 1):
            if cost + 1 <= caps["MAX_MORPHS"]:
                yield tuple(toks + [f]), (key, f)


TOY_SIZES = {"R": 2, "O": 2, "L": 2, "A": 1, "M": 1, "D": 1,
             "Q": 1, "T": 1, "F": 2}
TOY_CAPS = {"MAX_DEPTH": 1, "MAX_MORPHS": 6, "MIN_MORPHS": 2,
            "MAX_CLAUSES_PER_PRED": 2, "MAX_ORIENT_PER_PRED": 2,
            "MAX_ASPECT_REPS": 2}


@pytest.mark.parametrize("depth,morphs", [(0, 5), (1, 5), (1, 6), (2, 6)])
def test_gf_matches_bruteforce(depth, morphs):
    caps = dict(TOY_CAPS, MAX_DEPTH=depth, MAX_MORPHS=morphs)
    rows = list(ref_enumerate(TOY_SIZES, caps))

    brute_surface = len({r[0] for r in rows})
    brute_canon = len({repr(r[1]) for r in rows})

    gf_surface = E.build(ordered=True, sizes=TOY_SIZES, caps=caps)["total"]
    gf_canon = E.build(ordered=False, sizes=TOY_SIZES, caps=caps)["total"]

    assert brute_surface > 0, "toy grammar produced nothing -- test is vacuous"
    assert gf_surface == brute_surface, (
        f"surface: closed form {gf_surface} vs enumeration {brute_surface}")
    assert gf_canon == brute_canon, (
        f"canon: closed form {gf_canon} vs enumeration {brute_canon}")


def test_toy_is_big_enough_to_exercise_every_feature():
    """A toy that never nests, never doubles an orientation, or never uses
    aspect would pass while the interesting code is untested."""
    caps = dict(TOY_CAPS)
    rows = list(ref_enumerate(TOY_SIZES, caps))
    kinds = {t[0] for toks, _ in rows for t in toks}
    assert kinds == {"Q", "T", "M", "O", "L", "R", "A", "D", "F"}, kinds
    assert any(sum(1 for t in toks if t[0] == "O") == 2 for toks, _ in rows)
    assert any(sum(1 for t in toks if t[0] == "L") == 2 for toks, _ in rows)
    assert any(t[0] == "A" and t[2] == 2 for toks, _ in rows for t in toks)


def test_counting_detects_an_error():
    """Red-proof: if the ordered/unordered distinction were dropped, the
    comparison MUST fail. Otherwise the test above proves nothing."""
    caps = dict(TOY_CAPS)
    rows = list(ref_enumerate(TOY_SIZES, caps))
    brute_surface = len({r[0] for r in rows})
    wrong = E.build(ordered=False, sizes=TOY_SIZES, caps=caps)["total"]
    assert wrong != brute_surface, (
        "canonical count coincidentally equals the surface count; the toy "
        "grammar cannot distinguish ordered from unordered -- widen it")
