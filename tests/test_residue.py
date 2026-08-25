"""PHASE 13.0 -- the third category. Both required red-proofs live here.

  1. RENDERS-NEVER  -- mutating the residue leaves the surface byte-identical.
     This is what CERTIFIES the inexpressibility, and it is what the restated
     Phase 6 isolation claim leans on ("the residue is the designated,
     CONTAINED exception"). Contained is only true if it never leaks.

  2. THE LANDMINE   -- two residue-differing scenes must produce TWO medoids.
     RepetitionLog folds a scene into an existing medoid when
     `nearest.uid == uid OR nd == 0.0`, and BOTH clauses would have collapsed
     residue-differing scenes: `utterance_id` hashes canon_json (which omitted
     residue) and `D.normalized` had no residue term. It would not have
     crashed -- it would have silently erased the distinction, made a
     metric-residue arm behave like a no-residue arm, and MANUFACTURED an empty
     Part-2 result while the predicted-empty control looked correct.

⛔ Until (2) passes, no Part-2 null is interpretable.
"""
from __future__ import annotations

import pytest

from tlon.grammar import residue as R
from tlon.grammar.canon import utterance_id
from tlon.grammar.denote import project
from tlon.grammar.parse import EventNode, Scene, parse, render
from tlon.novelty import distance as D
from tlon.novelty.centroids import RepetitionLog
from tlon.referents.match import consistent, node_matches
from tlon.referents.schema import NodePattern, ReferentError, Signature


def scene(res, root="mlö"):
    return Scene(node=EventNode(root=root, residue=res), force="ka")


# ── RED-PROOF 1: the residue never reaches the surface ────────────────────
@pytest.mark.parametrize("res", [None, (0, 0), (1, 0), (3, 2), (-4, 7)])
def test_render_is_invariant_to_the_residue(res):
    assert render(scene(res)) == render(scene(None))


def test_render_is_invariant_at_depth_too():
    def build(res):
        child = EventNode(root="fox", residue=res)
        head = EventNode(root="mlö", residue=res, edges=[("mil", child)])
        return Scene(node=head, force="ka")
    assert render(build((2, 5))) == render(build(None))


def test_parse_cannot_recover_it_and_that_is_the_point():
    """Source-lossiness, stated as a test rather than a comment.

    The speaker holds the residue; the utterance cannot carry it; so a
    maximally informative speaker still cannot close the gap. That asymmetry
    is the mechanism, not a defect.
    """
    s = scene((3, 1))
    assert parse(render(s)).node.residue is None
    assert utterance_id(s) != utterance_id(parse(render(s)))


def test_pi_KEEPS_the_residue_stripped_is_not_unsayable():
    s = scene((3, 1))
    assert project(s).node.residue == (3, 1)


# ── RED-PROOF 2: the landmine. Two medoids, not one. ──────────────────────
def test_two_residue_differing_scenes_produce_two_medoids():
    log = RepetitionLog()
    a, b = scene((0, 0)), scene((3, 3))
    assert render(a) == render(b)                 # same surface, by design
    log.observe("ref", a, render(a))
    log.observe("ref", b, render(b))
    assert len(log.buckets["ref"].medoids) == 2, (
        "residue-differing scenes collapsed into one medoid — the log cannot "
        "tell them apart, so any Part-2 null would be manufactured")


def test_both_collapse_clauses_are_actually_fixed():
    """The fold triggers on `uid == uid OR nd == 0.0`. Check BOTH separately."""
    a, b = scene((0, 0)), scene((3, 3))
    assert utterance_id(a) != utterance_id(b), "clause 1 (uid) still collapses"
    assert D.normalized(a, b) > 0.0, "clause 2 (distance) still collapses"


def test_an_exact_repeat_still_folds():
    """The fix must not break the thing the fold is FOR."""
    log = RepetitionLog()
    for _ in range(3):
        log.observe("ref", scene((2, 2)), render(scene((2, 2))))
    assert len(log.buckets["ref"].medoids) == 1
    assert log.buckets["ref"].medoids[0].hits == 3


# ── R sees it as a DISTANCE, not an identity ──────────────────────────────
def test_r_scales_with_residue_distance_not_identity():
    """⭐ This is what makes the residue auditable instead of free novelty."""
    base = scene((0, 0))
    near, far = scene((1, 0)), scene((4, 0))
    d_near = D.normalized(base, near)
    d_far = D.normalized(base, far)
    assert 0.0 < d_near < d_far, (d_near, d_far)


def test_a_categorical_residue_could_not_do_this():
    """The metric is the whole reason R can hold the residue at all.

    Under identity-only scoring every distinct residue is equidistant, so R
    could not distinguish 'a nearby impression' from 'a wholly other one' and
    the generator would get uncheatable novelty for any change at all.
    """
    assert R.distance((0, 0), (1, 0)) < R.distance((0, 0), (4, 0))


# ── the type assertion: the copyright line, made mechanical ───────────────
def test_unknown_is_benign_in_match_and_an_error_in_the_metric():
    """`None` means UNKNOWN, and the two subsystems must treat it differently.

    In `match` it is the listener's epistemic position and cannot violate a
    constraint. In the metric either convention is exploitable — maximally
    distant buys free novelty for dropping the residue, zero makes dropping it
    read as a repeat — so it raises instead of absorbing.
    """
    p = NodePattern.parse({"root_any": ["mlö"], "residue_any": [[0, 0]]})
    assert node_matches(EventNode(root="mlö"), p)              # unknown: benign
    assert not node_matches(EventNode(root="mlö", residue=(9, 9)), p)
    assert R.distance(None, None) == 0.0                       # legacy case
    with pytest.raises(R.ResidueTypeError, match="unknown"):
        R.distance((0, 0), None)


@pytest.mark.parametrize("bad", ["a lyric fragment", b"bytes", 3, 3.5,
                                 ("a", "b"), (1.5, 2), (True, 1)])
def test_a_non_coordinate_residue_raises(bad):
    with pytest.raises(R.ResidueTypeError):
        R.validate(bad)


def test_a_string_residue_is_refused_in_a_signature():
    """⛔ THE SIDE DOOR. A str is iterable, so `tuple(r)` would silently accept
    it as a tuple of characters — text in a field no name-and-notes scanner
    reads. The type assertion is what closes it."""
    with pytest.raises((ReferentError, R.ResidueTypeError)):
        NodePattern.parse({"root_any": ["mlö"],
                           "residue_any": ["ancestral voices"]})


def test_mixed_lattice_dimensions_are_refused():
    with pytest.raises(ReferentError, match="dimensions"):
        NodePattern.parse({"root_any": ["mlö"],
                           "residue_any": [[0, 0], [1, 1, 1]]})


def test_a_valid_coordinate_signature_parses():
    p = NodePattern.parse({"root_any": ["mlö"], "residue_any": [[0, 0], [3, 1]]})
    assert p.residue_any == ((0, 0), (3, 1))


# ── the construction the lever needs: same signature, different residue ───
def test_denotationally_identical_residue_distinct_referents_are_ambiguous():
    """Two referents identical on every EXPRESSIBLE part, differing only in
    residue. Their shared surface is consistent with BOTH — which is
    irreducible full-utterance ambiguity, the thing no previous set produced."""
    sig_a = Signature.parse({"contains": [{"root_any": ["mlö"],
                                           "residue_any": [[0, 0]]}]})
    sig_b = Signature.parse({"contains": [{"root_any": ["mlö"],
                                           "residue_any": [[3, 3]]}]})
    heard = Scene(node=EventNode(root="mlö"), force="ka")   # residue not carried
    assert consistent(heard, sig_a) and consistent(heard, sig_b)
    # and the speaker's own scene still picks out exactly one
    spoken = scene((0, 0))
    assert node_matches(spoken.node, sig_a.contains[0])
    assert not node_matches(spoken.node, sig_b.contains[0])
