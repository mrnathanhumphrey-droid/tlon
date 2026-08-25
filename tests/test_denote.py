"""Soundness of the denotation projection π. PREREG c09d0fb3, KILL F.

Everything phase 5 measures is computed under π, so if π is unsound every number
rots silently. These are the guards that make the soundness argument a TEST
rather than a comment in a docstring.
"""
from __future__ import annotations
import random

import pytest

from tlon.grammar import denote
from tlon.grammar.denote import ProjectionUnsound, project, project_node
from tlon.grammar.parse import EventNode, Scene, parse, render
from tlon.listener import tokenizer as tk
from tlon.referents import schema
from tlon.referents.match import compat, consistent
from tlon.selfplay import phase3
from tlon.selfplay.policy import ChannelPolicy


def _scenes(n=120):
    refs = schema.load_all().referents
    pol = ChannelPolicy(len(refs), deps=[len(r.signature.contains) - 1
                                         for r in refs])
    rng = random.Random(11)
    out = []
    guard = 0
    while len(out) < n and guard < n * 10:
        guard += 1
        ri = rng.randrange(len(refs))
        sc = phase3.build_scene(refs[ri], pol(ri), rng)
        if sc is not None:
            out.append((refs[ri], sc))
    return refs, out


# ── the schema guard, with a red-proof on BOTH branches ────────────────────
def test_derived_parts_are_what_we_think():
    """PHASE 13.0: the split is now THREE-way, not two.

    π's original construction assumed DENOTING ⊆ EXPRESSIBLE. `residue` breaks
    that on purpose: it denotes (a signature constrains it, π keeps it) and the
    surface structurally cannot carry it.
    """
    assert denote.denoting_parts() == frozenset(
        {"root", "orient", "aspect.root", "edges", "residue"})
    assert denote.nondenoting_parts() == frozenset(
        {"aspect.reps", "degree", "modal", "tense", "quant", "force"})
    assert denote.inexpressible_parts() == frozenset({"residue"})
    assert denote.expressible_denoting_parts() == frozenset(
        {"root", "orient", "aspect.root", "edges"})


def test_the_three_categories_partition_cleanly():
    """No part may be in two categories, and stripped ≠ unsayable."""
    den, non = denote.denoting_parts(), denote.nondenoting_parts()
    inx = denote.inexpressible_parts()
    assert not (den & non), "a part cannot both denote and be normalised away"
    assert inx <= den, "an inexpressible non-denoting part is unreachable state"
    assert not (inx & non), \
        "STRIPPED (reaches the surface, removed for measurement) and UNSAYABLE " \
        "(never reaches the surface) are different things"
    assert den | non == frozenset(denote._ALL_PARTS)


def test_inexpressible_must_be_denoting_or_the_guard_fires(monkeypatch):
    """RED-PROOF: an inexpressible part no signature can constrain must raise."""
    monkeypatch.setattr(denote, "_INEXPRESSIBLE", frozenset({"degree"}))
    with pytest.raises(ProjectionUnsound, match="not denoting"):
        denote.inexpressible_parts()


def test_guard_fires_when_nodepattern_gains_a_field(monkeypatch):
    """RED-PROOF: a NodePattern field π cannot interpret must fail LOUDLY."""
    trimmed = dict(denote._PATTERN_TO_PART)
    trimmed.pop("orient_any")          # simulate a field π does not know
    monkeypatch.setattr(denote, "_PATTERN_TO_PART", trimmed)
    with pytest.raises(ProjectionUnsound, match="orient_any"):
        denote.denoting_parts()


def test_guard_fires_when_mapping_goes_stale(monkeypatch):
    """RED-PROOF: the other direction -- mapping a field that no longer exists."""
    extra = dict(denote._PATTERN_TO_PART)
    extra["degree_any"] = ("degree",)
    monkeypatch.setattr(denote, "_PATTERN_TO_PART", extra)
    with pytest.raises(ProjectionUnsound, match="degree_any"):
        denote.denoting_parts()


# ── π strips exactly the non-denoting parts ───────────────────────────────
def test_projection_normalises_nondenoting_fields():
    n = EventNode(root="hrun", aspect=("mel", 4), degree="kral", modal="tos",
                  tense="les", quant="ron", orient=["u"])
    p = project_node(n)
    assert p.root == "hrun"
    assert p.aspect == ("mel", 1)      # root kept, repetition count collapsed
    assert (p.degree, p.modal, p.tense, p.quant) == (None, None, None, None)
    assert p.orient == ["u"]


def test_projection_normalises_force():
    sc = Scene(node=EventNode(root="hrun"), force="ku")
    assert project(sc).force == denote.CANON_FORCE


def test_projection_is_idempotent():
    _, pairs = _scenes(40)
    for _, sc in pairs:
        once = project(sc)
        assert render(project(once)) == render(once)


# ── KILL F: π must not change WHICH REFERENTS ARE POSSIBLE ────────────────
def test_projection_preserves_compatibility_exactly():
    """Per-sample equality, not a distribution comparison.

    The prereg says the confusability numbers must carry over intact under π.
    Comparing summary distributions would pass even if individual scenes
    flipped in compensating directions; equality per (scene, referent) cannot.
    """
    refs, pairs = _scenes(120)
    checked = 0
    for _, sc in pairs:
        p = project(sc)
        for r in refs:
            assert compat(sc, r) == compat(p, r), (
                f"π changed compatibility with {r.id}: {render(sc)!r}")
            checked += 1
    assert checked > 5000


def test_projection_preserves_consistency_exactly():
    """Same equality check for the DUAL, which is the relation phase 5 uses.

    Under selection the utterance is partial, so it does not `match` its own
    referent -- it has not said enough. `consistent` is the relation that
    decides the ambiguity stratum, so it is the one KILL F actually rides on.
    """
    refs, pairs = _scenes(120)
    for _, sc in pairs:
        p = project(sc)
        for r in refs:
            assert consistent(sc, r.signature) == consistent(p, r.signature)


def test_projection_keeps_the_scene_possible_for_its_own_referent():
    """A partial utterance must stay CONSISTENT with what it describes."""
    _, pairs = _scenes(80)
    hits = sum(1 for ref, sc in pairs if consistent(project(sc), ref.signature))
    assert hits == len(pairs)


# ── projected scenes are still legal utterances ───────────────────────────
def test_projected_scenes_render_parse_and_encode():
    _, pairs = _scenes(80)
    for _, sc in pairs:
        surf = render(project(sc))
        parse(surf)
        assert tk.encode(surf)
