"""Tests for the `ForceMap` object and the stipulation guard.

⛔⛔ THE FAILURE THIS FILE EXISTS TO PREVENT IS NOT A CRASH. It is a STIPULATED
cell quietly becoming "the map" three sessions from now because it sat in a
corpus once and nobody re-read the label. [caveat_in_name]: the caveat is a
FIELD with a guard that RAISES, never a comment beside a value.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.discourse import force_map as FM                         # noqa: E402
from tlon.discourse.force_map import (                             # noqa: E402
    ForceMap, ForceMapError, StipulationLeak)


# ── the object is valid by construction ───────────────────────────────────────
def test_rejects_unknown_source_and_target():
    with pytest.raises(ForceMapError, match="not in class F"):
        ForceMap({"zz": "ka"}, label="x")
    with pytest.raises(ForceMapError, match="not in class F"):
        ForceMap({"ka": "zz"}, label="x")


def test_rejects_self_loop():
    with pytest.raises(ForceMapError, match="self-loop"):
        ForceMap({"ka": "ka"}, label="x")


def test_rejects_the_two_cycle_the_probe_had_to_avoid():
    """⛔ `ki`→`ka` + `ka`→`ki`. Unconstructible, not merely un-chosen."""
    with pytest.raises(ForceMapError, match="FORCED CYCLE"):
        ForceMap({"ki": "ka", "ka": "ki"}, label="x")


def test_rejects_a_longer_forced_cycle():
    with pytest.raises(ForceMapError, match="FORCED CYCLE"):
        ForceMap({"ka": "ki", "ki": "ko", "ko": "ka"}, label="x")


def test_accepts_a_forced_chain_that_is_not_a_cycle():
    """A legitimate no-op must not be red: ko→ki→ka terminates in a uniform row."""
    m = ForceMap({"ko": "ki", "ki": "ka"}, label="chain")
    assert m.verdict("ka") == FM.UNIFORM


def test_rejects_a_stipulation_label_with_nothing_under_it():
    with pytest.raises(ForceMapError, match="no forced cell"):
        ForceMap({"ki": "ka"}, label="x", stipulated=frozenset({"ko"}))


# ── the stipulation guard ─────────────────────────────────────────────────────
def test_derived_map_is_not_stipulated_and_passes_the_guard():
    assert FM.DERIVED_v1.is_stipulated is False
    assert FM.DERIVED_v1.stipulated == frozenset()
    FM.DERIVED_v1.assert_derived("the arena")          # must not raise


def test_stipulated_map_raises_at_every_non_probe_site():
    assert FM.STIPULATED_KI_TARGET_v1.is_stipulated is True
    with pytest.raises(StipulationLeak, match="STIPULATED"):
        FM.STIPULATED_KI_TARGET_v1.assert_derived("the arena")


def test_stipulated_map_names_itself_in_describe():
    """A human reading the log must not have to know which map this is."""
    d = FM.STIPULATED_KI_TARGET_v1.describe()
    assert "STIPULATED" in d and "ko→ki" in d
    assert "STIPULATED" not in FM.DERIVED_v1.describe()


def test_the_stipulated_source_is_neither_ka_nor_ki():
    """⛔ `ka` closes a 2-cycle; `ki` already has a forced target."""
    assert FM.STIPULATED_SOURCE not in ("ka", "ki")
    assert FM.REPLICATION_SOURCE_HELD not in ("ka", "ki")
    assert FM.REPLICATION_SOURCE_HELD != FM.STIPULATED_SOURCE


# ── the primary measure's stratum ─────────────────────────────────────────────
def test_common_stratum_is_uniform_in_both_maps():
    for f in FM.COMMON_UNIFORM_ROWS:
        assert FM.DERIVED_v1.verdict(f) == FM.UNIFORM
        assert FM.STIPULATED_KI_TARGET_v1.verdict(f) == FM.UNIFORM


def test_common_stratum_EXCLUDES_the_stipulated_source():
    """⛔⛔ THE CONFOUND. `ko` emits `ki` 100 % by construction in the treatment
    arm; including it would measure the stipulation and read as clean relief."""
    assert FM.STIPULATED_SOURCE not in FM.COMMON_UNIFORM_ROWS


def test_common_stratum_expectation_is_identical_in_both_arms():
    for f in FM.COMMON_UNIFORM_ROWS:
        assert FM.DERIVED_v1.row(f)["ki"] == pytest.approx(
            FM.COMMON_UNIFORM_EXPECTATION)
        assert FM.STIPULATED_KI_TARGET_v1.row(f)["ki"] == pytest.approx(
            FM.COMMON_UNIFORM_EXPECTATION)


def test_treatment_really_does_make_ki_a_target():
    """The probe's entire premise, asserted rather than assumed."""
    assert "ki" not in FM.DERIVED_v1.forced_cells.values()
    assert "ki" in FM.STIPULATED_KI_TARGET_v1.forced_cells.values()


# ── the maps behave ───────────────────────────────────────────────────────────
def test_rows_sum_to_one_in_both_maps():
    for m in (FM.DERIVED_v1, FM.STIPULATED_KI_TARGET_v1):
        for f in FM.ORDER:
            assert sum(m.row(f).values()) == pytest.approx(1.0)


def test_stationary_sums_to_one_and_treatment_lifts_ki():
    st_b = FM.DERIVED_v1.stationary()
    st_t = FM.STIPULATED_KI_TARGET_v1.stationary()
    assert sum(st_b.values()) == pytest.approx(1.0)
    assert sum(st_t.values()) == pytest.approx(1.0)
    assert st_t["ki"] > st_b["ki"]


def test_treatment_separation_is_higher_and_that_is_DECLARED_NEUTRAL():
    """⚠️ The treatment map is more learnable BY GEOMETRY. A fidelity gain in the
    treatment arm is predicted by this number and is NOT evidence of relief."""
    assert FM.STIPULATED_KI_TARGET_v1.separation() > FM.DERIVED_v1.separation()


# ── backwards compatibility: the module still speaks for the DERIVED map ──────
def test_module_level_functions_delegate_to_the_derived_map():
    for f in FM.ORDER:
        assert FM.row(f) == FM.DERIVED_v1.row(f)
        assert FM.verdict(f) == FM.DERIVED_v1.verdict(f)
    assert FM.separation() == pytest.approx(FM.DERIVED_v1.separation())
    assert FM.stationary() == FM.DERIVED_v1.stationary()
    assert FM.matrix() == FM.DERIVED_v1.matrix()


def test_module_forced_cells_constant_still_matches_the_derived_map():
    assert dict(FM.FORCED_CELLS) == dict(FM.DERIVED_v1.forced_cells)
