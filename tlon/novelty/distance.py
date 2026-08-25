"""Weighted tree edit distance over canonical EventNodes.

This is R's metric, and it is deliberately NOT an embedding distance
(PHASE2_DESIGN §6, flag ③). We have the graph exactly; scoring novelty in a
learned space the generator is simultaneously being trained to move through
would let it buy novelty by shifting the space rather than by having a new
impression. Tree edit distance is exact, cheap, auditable, and immovable.

Trees here are tiny -- MAX_DEPTH 3, MAX_CLAUSES_PER_PRED 3, so at most 40 nodes
and at most 3 children each. That means the optimal child alignment can be found
by brute force over permutations rather than by Zhang-Shasha.
"""
from __future__ import annotations
import itertools
from dataclasses import dataclass

from ..grammar import residue as _res
from ..grammar.parse import EventNode, Scene

# The root is the impression's kernel; disagreeing on it is the largest single
# difference two happenings can have short of structure.
W_ROOT = 1.0
W_ASPECT_KIND = 0.40      # different aspect root
W_ASPECT_STEP = 0.10      # per reduplication step, same root
W_FIELD = 0.25            # degree / modal / tense / quant
W_ORIENT = 0.35           # scaled by symmetric difference
W_RELATOR = 0.45          # a matched child reached by a different relation
W_MISSING = 1.20          # per node of an unmatched subtree
W_FORCE = 0.30
# PHASE 13.0. The residue is DENOTING, so repeating one IS repeating yourself
# and R must see it. ⭐ IT ENTERS AS A DISTANCE, NEVER AS IDENTITY -- that is
# what makes the residue auditable rather than free novelty, and it is only
# possible because the residue lives in a metric space. A categorical residue
# in R would be uncheatable noise, the exact failure π exists to prevent.
# ⛔ Scaled by the fixed lattice metric (residue.normalized), never a learned
# one: an embedding here would let the generator buy novelty by moving a space
# no auditor can read.
W_RESIDUE = 0.50


@dataclass(frozen=True)
class Weights:
    root: float = W_ROOT
    aspect_kind: float = W_ASPECT_KIND
    aspect_step: float = W_ASPECT_STEP
    field: float = W_FIELD
    orient: float = W_ORIENT
    relator: float = W_RELATOR
    missing: float = W_MISSING
    force: float = W_FORCE
    residue: float = W_RESIDUE


DEFAULT = Weights()


def size(n: EventNode) -> int:
    return 1 + sum(size(c) for _, c in n.edges)


def _aspect_cost(a, b, w: Weights) -> float:
    if a == b:
        return 0.0
    if a is None or b is None:
        return w.aspect_kind
    if a[0] != b[0]:
        return w.aspect_kind
    return w.aspect_step * abs(a[1] - b[1])


def _label_cost(a: EventNode, b: EventNode, w: Weights) -> float:
    c = 0.0
    if a.root != b.root:
        c += w.root
    c += _aspect_cost(a.aspect, b.aspect, w)
    for f in ("degree", "modal", "tense", "quant"):
        if getattr(a, f) != getattr(b, f):
            c += w.field
    sa, sb = set(a.orient), set(b.orient)
    if sa or sb:
        c += w.orient * len(sa ^ sb) / max(1, len(sa | sb))
    # ⛔⛔ THE OTHER HALF OF THE LANDMINE. RepetitionLog also folds a scene into
    # a medoid when `nd == 0.0`, so without this term two residue-differing
    # scenes are distance-0, collapse as a repeat, and Part 2 reads empty for
    # reasons unrelated to conventionability. BOTH clauses had to be fixed.
    c += w.residue * _res.normalized(a.residue, b.residue)
    return c


def node_distance(a: EventNode, b: EventNode, w: Weights = DEFAULT) -> float:
    """Optimal-alignment edit distance between two event subtrees."""
    cost = _label_cost(a, b, w)
    ea, eb = list(a.edges), list(b.edges)
    if not ea and not eb:
        return cost
    # brute force: at most 3 children a side
    long_, short_ = (ea, eb) if len(ea) >= len(eb) else (eb, ea)
    best = None
    for pick in itertools.permutations(range(len(long_)), len(short_)):
        c = 0.0
        for si, li in enumerate(pick):
            rel_s, ch_s = short_[si]
            rel_l, ch_l = long_[li]
            if rel_s != rel_l:
                c += w.relator
            c += node_distance(ch_s, ch_l, w)
        for li in range(len(long_)):
            if li not in pick:
                c += w.missing * size(long_[li][1])
        best = c if best is None else min(best, c)
    return cost + (best or 0.0)


def distance(a: Scene, b: Scene, w: Weights = DEFAULT) -> float:
    d = node_distance(a.node, b.node, w)
    if a.force != b.force:
        d += w.force
    return d


def normalized(a: Scene, b: Scene, w: Weights = DEFAULT) -> float:
    """Distance scaled to roughly [0, 1] by the larger tree, so that lambda is
    interpretable across scenes of different sizes."""
    denom = w.missing * max(size(a.node), size(b.node))
    return min(1.0, distance(a, b, w) / denom) if denom else 0.0
