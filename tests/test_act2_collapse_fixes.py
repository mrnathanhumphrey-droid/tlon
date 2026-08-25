"""THE THREE FIXES FROM THE COLLAPSE DIAGNOSIS, RED-PROOFED. $0.00, offline.

The Tier-A gate read `speak 100 % (64/64)` and `render 31.2 %`. Neither number
meant what it said, and the $0 diagnoses on the pulled artifacts said why:

  A — the corpus is NOT collapsed: 37,410/40,000 distinct scenes, all 156 roots
      (min 658 / max 718), forces exactly 8,000 each, 85 % carrying edges. The
      model's constant output appears **6 times in 40,000**, so it collapsed AWAY
      from its data, not toward it.
  B — output IS input-dependent: **12/12 distinct** on 12 different inputs.
  D — ⭐⭐ IT WAS THE DECODER. Same prompt greedy = **1/12**; same prompt at
      temperature 0.8 = **11/12**. The weights were never collapsed; greedy took
      the mode of a diverse distribution, and F-LOCAL's speak probe issues a
      BYTE-IDENTICAL prompt 64 times. **Effective sample size 1, reported as 64.**
"""
from __future__ import annotations

import json

import pytest

from tlon.act2 import diversity as DV
from tlon.act2 import schema_bridge as SB
from tlon.grammar.canon import canon_json
from tlon.product import schema as PS

SIMPLE = {"node": {"root": "klung"}, "force": "ka"}


# ══ FIX 1 — THE CORPUS IS SERIALIZED IN THE PROPOSAL SCHEMA ══════════════
def _sample_scenes(n=40):
    from tlon.act2 import corpus
    return [p.scene for p in corpus.build(n, balanced=True)]


def test_every_sampled_scene_round_trips_through_the_GATE():
    """⭐⭐ THE RED-PROOF THAT MATTERS. Serialize with the new writer, validate
    with the gate the fine-tune is scored by. If this passes, the trainer and the
    gate speak one dialect — which is the whole defect."""
    for scene in _sample_scenes():
        proposal = SB.scene_to_proposal(scene)
        PS.validate(proposal)                      # raises if the dialects differ


def test_the_round_trip_PRESERVES_MEANING_not_merely_validity():
    """⛔ Validity is not enough — a serializer that silently dropped `aspect`
    would still validate. The IMPRESSION is the identity of the utterance, so it
    must survive the trip."""
    from tlon.product.compat import impression
    for scene in _sample_scenes(30):
        back, _, _ = PS.validate(SB.scene_to_proposal(scene))
        assert impression(back) == impression(scene)


def test_the_OLD_serializer_FAILS_the_same_round_trip():
    """⛔⛔ THE MUTATION, AS A TEST. `canon_json` is what shipped. If this ever
    stops failing, the two shapes have converged and Fix 1 is moot — but while
    they differ, this is the 39-of-44 defect reproduced on demand."""
    failures = 0
    for scene in _sample_scenes(30):
        try:
            PS.validate(json.loads(canon_json(scene)))
        except PS.ProposalError:
            failures += 1
    assert failures > 0, (
        "the canonical hashing form must NOT validate as a proposal; if it "
        "does, this test no longer proves anything")


def test_a_scene_WITH_EDGES_is_where_the_two_shapes_diverge():
    """⭐ The two spellings agree on a bare scene, which is exactly why the bug
    stayed invisible until edges appeared."""
    from tlon.act2 import corpus
    with_edges = next(p.scene for p in corpus.build(60, balanced=True)
                      if p.scene.node.edges)
    prop = SB.scene_to_proposal(with_edges)
    assert isinstance(prop["node"]["edges"][0], dict)
    assert "relator" in prop["node"]["edges"][0]
    canon = json.loads(canon_json(with_edges))
    assert isinstance(canon["node"]["edges"][0], list)      # the old shape
    PS.validate(prop)
    with pytest.raises(PS.ProposalError):
        PS.validate(canon)


# ══ FIX 2 — REFUSE, NEVER SILENTLY DROP ══════════════════════════════════
def test_a_canon_shape_ASPECT_is_REFUSED_not_silently_dropped():
    """⛔⛔ THE SILENT FAILURE, CLOSED. `validate` read `aspect_root`, so a
    canon-shape `aspect` key simply vanished and the proposal VALIDATED —
    scoring as an F-LOCAL success while having lost meaning."""
    bad = {"node": {"root": "klung", "aspect": ["pal", 2]}, "force": "ka"}
    with pytest.raises(PS.ProposalError, match="aspect_root"):
        PS.validate(bad)


@pytest.mark.parametrize("field", ["aspect", "relator", "residue", "note", "xyz"])
def test_ANY_unrecognised_field_is_refused(field):
    """The general rule, not the one observed case: a field the validator cannot
    read is a loss of meaning, and it must be loud."""
    bad = {"node": {"root": "klung", field: "whatever"}, "force": "ka"}
    with pytest.raises(PS.ProposalError, match="unrecognised"):
        PS.validate(bad)


def test_the_legitimate_fields_all_still_pass():
    """⛔ The floor. Over-strict refusal would break the product, so every field
    the schema actually declares must survive."""
    # ⛔ Forms taken from the frozen lexicon by CLASS, not from memory — the
    # first draft of this test used `pal` as an aspect root and `pal` is an
    # R-form. That is the exact R→A confusion the hosted pre-flight measured,
    # committed in a test fixture.
    full = {"force": "ka", "node": {
        "root": "klung", "aspect_root": "sor", "aspect_reps": 2,
        "orient": ["fen"], "degree": "les", "modal": "hrix", "tense": "nu",
        "quant": "tren",
        "edges": [{"relator": "kra", "node": {"root": "frem"}}]}}
    PS.validate(full)


# ══ FIX 3 — THE TWO-SIDED DIVERSITY GUARD ════════════════════════════════
def _const(n):  return [dict(SIMPLE) for _ in range(n)]
def _uniq(n):   return [{"node": {"root": f"r{i}"}, "force": "ka"} for i in range(n)]


def test_the_guard_REFUSES_the_exact_collapse_that_motivated_it():
    """⛔⛔ THE VACUITY TRAP, CLOSED. A diversity guard that does not catch the
    collapse it was written for is theatre. This is the measured `san` x12."""
    with pytest.raises(DV.DegenerateSpeaker, match="COLLAPSE"):
        DV.measure(repeated=_const(12), varied=_const(12))


def test_the_guard_REFUSES_the_NOISE_end_too():
    """⛔⛔ THE OTHER DEGENERATE END. Uniform-random legal output maxes any naive
    distinctness check. Here the SAME input gives 12 different answers, so the
    output is not tracking meaning at all."""
    with pytest.raises(DV.DegenerateSpeaker, match="NOISE"):
        DV.measure(repeated=_uniq(12), varied=_uniq(12))


def test_a_native_shaped_speaker_SCORES_and_is_not_refused():
    """Consistent on the same input, diverse across different ones."""
    d = DV.measure(repeated=_const(12), varied=_uniq(12))
    assert d.repeat_rate == 1.0 and d.response_rate == 1.0
    assert d.dependence == 1.0 and d.verdict == "input-dependent"


def test_the_guard_REPORTS_A_NUMBER_so_it_can_be_driven():
    """⭐ A binary pass/fail cannot be tracked against training step; the retrain
    plots THIS against checkpoints (Diagnosis C)."""
    d = DV.measure(repeated=_const(12), varied=_uniq(12))
    for f in ("distinct", "repeat_rate", "response_rate", "dependence"):
        assert isinstance(getattr(d, f), (int, float))
    assert 0.0 <= d.ratio <= 1.0


def test_UNEQUAL_samples_are_refused_because_they_measure_the_sample_size():
    with pytest.raises(ValueError, match="same size"):
        DV.measure(repeated=_const(12), varied=_uniq(6))


def test_a_sample_too_small_to_separate_the_two_ends_is_refused():
    with pytest.raises(ValueError, match="too small"):
        DV.measure(repeated=_const(2), varied=_uniq(2))


def test_the_MEASURED_greedy_and_sampled_readings_land_on_opposite_verdicts():
    """⭐⭐ THE DIAGNOSIS ITSELF, AS A REGRESSION TEST. Greedy on a constant
    prompt gave 1/12; the same prompt at temperature 0.8 gave 11/12. The guard
    must call the first degenerate and the second not — otherwise it would have
    reported the decoder's behaviour as the model's."""
    with pytest.raises(DV.DegenerateSpeaker, match="COLLAPSE"):
        DV.measure(repeated=_const(12), varied=_const(12))     # greedy, 1/12
    sampled = _uniq(11) + [dict(SIMPLE)]                        # 11/12 distinct
    d = DV.measure(repeated=_const(12), varied=sampled)
    assert d.distinct == 12 or d.distinct == 11
    assert d.dependence > 0.5
