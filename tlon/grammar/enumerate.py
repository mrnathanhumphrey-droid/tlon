"""Exact counting of the Sur utterance space -- the Phase 0 gate (spec §7).

METHOD NOTE. Exhaustive enumeration is infeasible: a single leaf predication
already admits ~1e10 forms, so no amount of CPU enumerates |U|. Instead we
count EXACTLY with generating functions over morpheme length, which is
instant and gives big-integer answers rather than estimates.

Each class contributes a polynomial in x where the coefficient of x^n is the
number of choices of length n morphemes. Sets of distinct sub-objects (sibling
clauses, orientation particles) are counted with Newton's identities for the
elementary symmetric functions, so duplicates are excluded exactly rather than
approximated away.
"""
from __future__ import annotations
import math

from . import classes as C

Poly = list[int]


# ── polynomial helpers (truncated at MAXM) ─────────────────────────────────
def _trim(p: Poly, n: int) -> Poly:
    return (p + [0] * n)[:n + 1]


def mul(a: Poly, b: Poly, n: int) -> Poly:
    out = [0] * (n + 1)
    for i, ai in enumerate(a):
        if not ai or i > n:
            continue
        for j, bj in enumerate(b):
            if not bj or i + j > n:
                continue
            out[i + j] += ai * bj
    return out


def add(a: Poly, b: Poly, n: int) -> Poly:
    a, b = _trim(a, n), _trim(b, n)
    return [x + y for x, y in zip(a, b)]


def scale(a: Poly, k: int) -> Poly:
    return [x * k for x in a]


def shift(a: Poly, d: int, n: int) -> Poly:
    return _trim([0] * d + a, n)


def subst_pow(a: Poly, m: int, n: int) -> Poly:
    """c(x) -> c(x^m)."""
    out = [0] * (n + 1)
    for i, ai in enumerate(a):
        if ai and i * m <= n:
            out[i * m] += ai
    return out


def _exact_div(p: Poly, k: int) -> Poly:
    out = []
    for c in p:
        q, r = divmod(c, k)
        assert r == 0, "elementary symmetric function was not integral"
        out.append(q)
    return out


def subsets_upto(c: Poly, kmax: int, n: int, ordered: bool) -> Poly:
    """GF for choosing 0..kmax DISTINCT items from the graded set with GF c.

    ordered=False -> unordered subsets (canonical form)
    ordered=True  -> ordered sequences of distinct items (surface form)
    """
    p1 = _trim(c, n)
    p2 = subst_pow(c, 2, n)
    p3 = subst_pow(c, 3, n)
    e = [[1] + [0] * n]                                        # e0
    if kmax >= 1:
        e.append(p1)
    if kmax >= 2:
        e.append(_exact_div(add(mul(p1, p1, n), scale(p2, -1), n), 2))
    if kmax >= 3:
        t = add(mul(mul(p1, p1, n), p1, n),
                scale(mul(p1, p2, n), -3), n)
        e.append(_exact_div(add(t, scale(p3, 2), n), 6))
    total = [0] * (n + 1)
    for k, ek in enumerate(e):
        total = add(total, scale(ek, math.factorial(k) if ordered else 1), n)
    return total


# ── the language ───────────────────────────────────────────────────────────
def build(ordered: bool, pin_matrix_root: bool = False,
          sizes: dict | None = None, caps: dict | None = None) -> dict:
    """Return counting results. ordered=True counts surface strings;
    ordered=False counts canonical (order-insensitive) structures.

    `sizes`/`caps` override the lexicon, so the same code path can be checked
    against brute-force enumeration on a toy grammar (tests/test_counting.py).
    """
    lex = C.load()
    k = dict(lex["constraints"])
    if caps:
        k.update(caps)
    n = k["MAX_MORPHS"]
    sz = dict(C.class_sizes())
    if sizes:
        sz.update(sizes)

    gR = [0, sz["R"]]
    gR_pinned = [0, 1]
    # aspect: 6 roots x reps 1..4, cost = reps + 1
    gA = [1] + [0] * n
    for reps in range(1, k["MAX_ASPECT_REPS"] + 1):
        gA = add(gA, shift([sz["A"]], reps + 1, n), n)
    gD = [1, sz["D"]]
    gQ = [1, sz["Q"]]
    gT = [1, sz["T"]]
    gM = [1, sz["M"]]
    gF = [0, sz["F"]]

    nucleus = mul(mul(gR, gA, n), gD, n)
    nucleus_pinned = mul(mul(gR_pinned, gA, n), gD, n)
    orient = subsets_upto([0, sz["O"]], k["MAX_ORIENT_PER_PRED"], n, ordered)
    prefix = mul(mul(gQ, gT, n), gM, n)

    # P_d: predication with d further levels of clause nesting available.
    P = [None] * (k["MAX_DEPTH"] + 1)
    P[0] = mul(mul(prefix, orient, n), nucleus, n)
    for d in range(1, k["MAX_DEPTH"] + 1):
        clause = shift(scale(P[d - 1], sz["L"]), 1, n)     # L + Predication
        clauses = subsets_upto(clause, k["MAX_CLAUSES_PER_PRED"], n, ordered)
        P[d] = mul(mul(mul(prefix, orient, n), clauses, n), nucleus, n)

    top = P[k["MAX_DEPTH"]]
    if pin_matrix_root:
        clause = shift(scale(P[k["MAX_DEPTH"] - 1], sz["L"]), 1, n)
        clauses = subsets_upto(clause, k["MAX_CLAUSES_PER_PRED"], n, ordered)
        top = mul(mul(mul(prefix, orient, n), clauses, n), nucleus_pinned, n)

    utt = mul(top, gF, n)
    by_depth = {d: sum(mul(mul(P[d], gF, n), [1], n)) for d in range(len(P))}
    return {"by_length": utt, "total": sum(utt), "by_depth": by_depth}


def max_fiber_bound() -> int:
    """Upper bound on |{u : canon(parse(u)) == canon(s)}| over all legal s.

    Maximises  prod over nodes of (|orient|! * |edges|!)  subject to the depth
    and morpheme caps. Upper bound because it ignores sibling-distinctness.
    """
    k = C.constraints()
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def F(d: int, m: int) -> int:
        if m < 1:
            return 0
        best = 1                                   # bare nucleus, fiber 1
        for o in range(0, k["MAX_ORIENT_PER_PRED"] + 1):
            kmax = k["MAX_CLAUSES_PER_PRED"] if d > 0 else 0
            for kc in range(0, kmax + 1):
                spent = o + kc + 1                 # orients + relators + root
                left = m - spent
                if left < kc:                      # each child needs >= 1
                    continue
                g = G(d - 1, left, kc)
                if g:
                    best = max(best, math.factorial(o) * math.factorial(kc) * g)
        return best

    @lru_cache(maxsize=None)
    def G(d: int, budget: int, kc: int) -> int:
        if kc == 0:
            return 1 if budget >= 0 else 0
        best = 0
        for m1 in range(1, budget - (kc - 1) + 1):
            a, b = F(d, m1), G(d, budget - m1, kc - 1)
            if a and b:
                best = max(best, a * b)
        return best

    return F(k["MAX_DEPTH"], k["MAX_MORPHS"] - 1)
