"""Tree edit distance must actually discriminate.

Identity and symmetry are cheap: a function returning 0 for everything passes
both. The tests that matter are the ones asserting it SEPARATES things -- that
it orders differences the way the semantics say it should.
"""
from __future__ import annotations
import itertools
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tlon.grammar.parse import parse                 # noqa: E402
from tlon.novelty import distance as D               # noqa: E402

P = parse

# Sur is HEAD-FINAL: satellites and clauses precede the matrix root.
CORPUS = [
    "mlö ka",
    "fang ka",
    "hlör mlö ka",
    "u fang mlö ka",
    "xom rän kön ka",
    "mlö axaxas ka",
    "nar tris melas ka",
    "u fang sen tris mlö ka",
    "sim nu ten hlör u fang axaxaxas mlö tos ka",
]


def test_corpus_is_parseable_and_varied():
    """If these fixtures did not parse, every test below would error rather
    than fail, and the file would look broken instead of red."""
    scenes = [P(t) for t in CORPUS]
    assert len({D.size(s.node) for s in scenes}) >= 3


def test_identity():
    for t in CORPUS:
        assert D.distance(P(t), P(t)) == 0.0


def test_canonically_equal_scenes_are_zero_apart():
    """Permuted surface, same meaning — novelty must see no distance at all."""
    assert D.distance(P("hlör nar mlö ka"), P("nar hlör mlö ka")) == 0.0
    assert D.distance(P("u fang sen tris mlö ka"),
                      P("sen tris u fang mlö ka")) == 0.0


def test_symmetry():
    for a, b in itertools.combinations(CORPUS, 2):
        assert D.distance(P(a), P(b)) == pytest.approx(D.distance(P(b), P(a)))


# ── discrimination: the orderings the semantics demand ─────────────────────
def test_root_change_outweighs_a_modifier_change():
    base, other_root, modified = P("mlö ka"), P("fang ka"), P("hlör mlö ka")
    assert D.distance(base, other_root) > D.distance(base, modified)


def test_aspect_steps_are_graded_not_binary():
    a, b, c = P("mlö axas ka"), P("mlö axaxas ka"), P("mlö axaxaxas ka")
    assert 0 < D.distance(a, b) < D.distance(a, c)


def test_different_aspect_root_costs_more_than_one_step():
    step = D.distance(P("mlö axas ka"), P("mlö axaxas ka"))
    kind = D.distance(P("mlö axas ka"), P("mlö melas ka"))
    assert kind > step


def test_missing_subtree_costs_by_its_size():
    bare, one, two = P("mlö ka"), P("u fang mlö ka"), P("u fang sen tris mlö ka")
    assert D.distance(bare, two) > D.distance(bare, one) > 0


def test_relator_change_is_visible():
    """Peg 20 hinges on `kra` versus anything else — the metric must feel it."""
    assert D.distance(P("kra fang mlö ka"), P("mil fang mlö ka")) > 0


def test_orientation_overlap_is_partial_credit():
    none_shared = D.distance(P("hlör mlö ka"), P("nar mlö ka"))
    half_shared = D.distance(P("hlör nar mlö ka"), P("hlör tex mlö ka"))
    assert 0 < half_shared < none_shared


def test_illocution_matters():
    assert D.distance(P("mlö ka"), P("mlö ki")) > 0


# ── normalization ──────────────────────────────────────────────────────────
def test_normalized_is_bounded_and_not_constant():
    seen = set()
    for a, b in itertools.combinations(CORPUS, 2):
        v = D.normalized(P(a), P(b))
        assert 0.0 <= v <= 1.0
        seen.add(round(v, 4))
    assert len(seen) > 1, "normalized distance collapsed to a constant"


def test_the_metric_is_not_constant():
    """Red-proof for every ordering test above: a constant function would
    satisfy identity and symmetry and nothing else."""
    vals = {D.distance(P("mlö ka"), P(t))
            for t in ("mlö ka", "fang ka", "hlör mlö ka", "u fang mlö ka")}
    assert len(vals) == 4


def test_triangle_inequality_holds_on_this_corpus():
    """NOT guaranteed by construction — optimal-alignment tree edit distance
    with these weights is not proven metric. Checked empirically so that a
    violation would be a known fact rather than a surprise during Phase 3."""
    scenes = [P(t) for t in CORPUS]
    bad = []
    for a, b, c in itertools.permutations(scenes, 3):
        ab, bc, ac = D.distance(a, b), D.distance(b, c), D.distance(a, c)
        if ac > ab + bc + 1e-9:
            bad.append((round(ac, 3), round(ab + bc, 3)))
    assert not bad, f"{len(bad)} triangle violations, e.g. {bad[:3]}"
