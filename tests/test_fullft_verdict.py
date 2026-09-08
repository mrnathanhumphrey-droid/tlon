"""THE §4.2 VERDICT TABLE — and the precondition that voids it.

PREREG `PREREG_FULL_FINETUNE_RELEASE_2026_09_05` (LOCK `a0450b36`). The tests
that matter are the ones where a row must NOT be read: a delta that did not
pass, an F-LOCAL that could not be scored, a lag profile taken against the wrong
kind of object.
"""
import importlib.util
import json
import pathlib

import pytest

from tlon.discourse.transient import Z_LAG1_MIN, Z_LAGN_MAX


def _v():
    p = (pathlib.Path(__file__).resolve().parents[1] / "tools"
         / "act2_fullft_verdict.py")
    spec = importlib.util.spec_from_file_location("_v", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


#: ⭐ Any 8-hex id; these tests exercise the TABLE, not provenance —
#: `tests/test_verdict_provenance.py` owns the id's correctness.
PREREG_ID = "0" * 8


def _delta(verdict="OK"):
    return {"verdict": verdict, "fraction_changed": 0.99, "why": "..."}


def _lag(z1=20.0, z2=1.0, z3=0.5):
    return {"z": {"1": z1, "2": z2, "3": z3}, "object_kind": "full_weight"}


def _fl(fired=False):
    return {"fired": fired}


def test_thresholds_are_the_corpus_own_constants_not_retyped():
    """⛔⛔ §3: a number typed in the verdict tool would let the gate be tuned
    after seeing the model."""
    v = _v()
    assert v.Z_LAG1_MIN is Z_LAG1_MIN
    assert v.Z_LAGN_MAX is Z_LAGN_MAX


def test_go_requires_all_three_axes():
    v = _v()
    out = v.decide(_delta(), _lag(), _fl(), prereg=PREREG_ID)
    assert out["verdict"] == v.GO


@pytest.mark.parametrize("bad_delta", ["INSTRUMENT_FAULT", "UNDISCRIMINATING",
                                      "DIVERGED"])
def test_a_delta_that_did_not_pass_voids_the_whole_table(bad_delta):
    """⛔⛔ THE CENTRAL GUARD. Not just INSTRUMENT_FAULT — UNDISCRIMINATING too.
    A test that could not distinguish the hypotheses has not certified anything,
    and reading a GO off it would be a pass the measurement could not confer.
    Note the axes would otherwise all PASS here: the void is the point."""
    v = _v()
    out = v.decide(_delta(bad_delta), _lag(), _fl(), prereg=PREREG_ID)
    assert out["verdict"] == v.FAULT
    assert out["axes_not_computed"] is True
    assert "axes" not in out


def test_release_failing_is_floored_and_is_not_yet_a_substrate_finding():
    """⛔⛔ §7.1. A floor at this rung is 'the top 14 layers could not', not
    'the substrate is the wall'. The verdict text must say so, because the
    sentence is what someone reads six weeks later."""
    v = _v()
    out = v.decide(_delta(), _lag(z2=Z_LAGN_MAX + 1.0), _fl(), prereg=PREREG_ID)
    assert out["verdict"] == v.STOP_FLOORED
    assert "NOT YET A SUBSTRATE FINDING" in out["why"]


def test_a_longer_lag_over_the_ceiling_also_floors_it():
    """⛔ §4: 'lag-2 z <= 3.0 AND every longer lag <= 3.0'. Checking lag-2 alone
    would pass a model that holds its turn from three back."""
    v = _v()
    out = v.decide(_delta(), _lag(z2=1.0, z3=Z_LAGN_MAX + 2.0), _fl(), prereg=PREREG_ID)
    assert out["verdict"] == v.STOP_FLOORED


def test_f_local_failing_is_the_cratered_row_with_the_declared_dial_back():
    v = _v()
    out = v.decide(_delta(), _lag(), _fl(fired=True), prereg=PREREG_ID)
    assert out["verdict"] == v.STOP_CRATERED
    assert "5e-6" in out["why"]


def test_an_unscoreable_f_local_is_not_a_pass():
    """⛔⛔ `fired=None` means the speaker was degenerate and F-LOCAL could not
    be scored. Treating an unmeasured axis as clear is the vacuous pass this
    project keeps finding."""
    v = _v()
    out = v.decide(_delta(), _lag(), _fl(fired=None), prereg=PREREG_ID)
    assert out["verdict"] != v.GO
    assert out["axes"]["f_local"]["unscoreable"] is True


def test_perceive_below_the_floor_reopens_the_entangled_fork():
    v = _v()
    out = v.decide(_delta(), _lag(z1=Z_LAG1_MIN - 1.0), _fl(), prereg=PREREG_ID)
    assert out["verdict"] == v.STOP_PERCEIVE
    assert "ENTANGLED" in out["why"]


def test_a_lag_profile_missing_lag2_is_incoherent_not_a_pass():
    v = _v()
    out = v.decide(_delta(), {"z": {"1": 20.0}, "object_kind": "full_weight"},
                   _fl(), prereg=PREREG_ID)
    assert out["verdict"] == v.STOP_INCOHERENT


def test_the_boundary_values_are_inclusive_as_written():
    """⭐ §4 is `<= 3.0` and `>= 6.0`. A strict comparison here would refuse a
    model landing exactly on the pre-registered threshold."""
    v = _v()
    out = v.decide(_delta(), _lag(z1=Z_LAG1_MIN, z2=Z_LAGN_MAX,
                                  z3=Z_LAGN_MAX), _fl(), prereg=PREREG_ID)
    assert out["verdict"] == v.GO


def test_the_last_f_local_row_is_the_one_read(tmp_path):
    """⛔ The ledger is append-only. Reading the first `f_local` row would score
    a previous build against this run's weights."""
    v = _v()
    p = tmp_path / "ledger.jsonl"
    p.write_text("\n".join([
        json.dumps({"event": "f_local", "fired": True}),
        json.dumps({"event": "other", "fired": False}),
        json.dumps({"event": "f_local", "fired": False}),
    ]), encoding="utf-8")
    assert v.last_f_local(p)["fired"] is False


def test_a_missing_ledger_refuses_rather_than_defaulting(tmp_path):
    v = _v()
    with pytest.raises(SystemExit):
        v.last_f_local(tmp_path / "nope.jsonl")
