"""⭐ RED-PROOF FOR THE INJECTION-POOL GATE.

⛔⛔ THIS IS THE LAST HIDING PLACE FOR A FALSE POSITIVE, and it is the one that
would look most like success: a pool that pulls both speakers toward itself makes
them more alike, the distance shrinks, and on the metric that is
indistinguishable from mutual convergence.

⛔ The condition-level guards do NOT catch it. The spy proves no partner content
leaks; the two-backend test proves two distinct speakers; the yoke proves input
is held. A biased pool passes all three, because the pool is SUPPOSED to be
shared — the yoking makes it identical across conditions by design.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

from act2_injection_gate import (OUTSIDE_SEGMENT_FRACTION, PANEL,  # noqa: E402
                                 Z_MAX, asymmetry, centrality, verdict_of)
from act2_two_speaker import measurable_turns                        # noqa: E402


def mk(vals):
    return {o: v for o, v in zip(PANEL, vals)}


BUILDS = {"b1": mk([0.90, 0.40, 3.0]), "b2": mk([0.92, 0.42, 3.1]),
          "b3": mk([0.88, 0.38, 2.9]), "b4": mk([0.91, 0.41, 3.05])}


# ── centrality ──────────────────────────────────────────────────────────────
def test_a_central_pool_passes_centrality():
    c = centrality(mk([0.9025, 0.4025, 3.0125]), BUILDS)
    assert all(v["ok"] for v in c.values())


def test_an_OFF_CENTRE_pool_is_caught_on_the_offending_axis():
    """⛔ The third-speaker case: far away on one axis, fine on the others."""
    c = centrality(mk([0.50, 0.4025, 3.0125]), BUILDS)
    assert c["root TTR"]["ok"] is False
    assert c["force:ka"]["ok"] is True


def test_off_centre_on_ANY_axis_halts_the_whole_gate():
    c = centrality(mk([0.50, 0.4025, 3.0125]), BUILDS)
    assert verdict_of(c, []) == "HALT_CENTRALITY"


def test_a_zero_variance_axis_gives_infinite_z_and_REFUSES():
    """⛔ A degenerate build set must not read as 'perfectly central'."""
    flat = {"b1": mk([0.9, 0.4, 3.0]), "b2": mk([0.9, 0.4, 3.0])}
    c = centrality(mk([0.9, 0.4, 3.0]), flat)
    assert c["root TTR"]["z"] == float("inf")
    assert c["root TTR"]["ok"] is False


# ── projection: a DIAGNOSTIC, halting only when the pool is off to one side ─
def test_a_central_pool_projects_BETWEEN_the_speakers_for_most_pairs():
    rows = asymmetry(mk([0.9025, 0.4025, 3.0125]), BUILDS)
    assert len(rows) == 6                       # 4 builds -> 6 pairs
    assert sum(r["outside"] for r in rows) / len(rows) <= OUTSIDE_SEGMENT_FRACTION


def test_a_pool_BEYOND_the_population_is_caught_as_not_between():
    """⛔ The third-speaker-off-to-one-side case."""
    rows = asymmetry(mk([0.60, 0.10, 1.0]), BUILDS)
    assert sum(r["outside"] for r in rows) / len(rows) > OUTSIDE_SEGMENT_FRACTION


def test_a_pool_beyond_the_population_HALTS():
    ok_cent = centrality(mk([0.9025, 0.4025, 3.0125]), BUILDS)
    rows = [{"outside": True} for _ in range(6)]
    assert verdict_of(ok_cent, rows) == "HALT_NOT_BETWEEN"


def test_a_pool_between_the_speakers_PASSES():
    ok_cent = centrality(mk([0.9025, 0.4025, 3.0125]), BUILDS)
    assert verdict_of(ok_cent, [{"outside": False}]) == "PASS"


def test_asymmetry_alone_does_NOT_halt_a_central_pool():
    """⭐ THE DEMOTION, ASSERTED: a lopsided-but-interior pool is reported, not
    halted, because a yoked pool's differential pull cancels in LIVE - YOKED."""
    ok_cent = centrality(mk([0.9025, 0.4025, 3.0125]), BUILDS)
    lopsided = [{"outside": False}] * 5 + [{"outside": True}]
    assert verdict_of(ok_cent, lopsided) == "PASS"


# ── guard on the guard ──────────────────────────────────────────────────────
def test_the_gate_can_return_every_verdict_it_defines():
    """⛔ A gate that can only PASS has not been passed, it has been consulted."""
    bad_cent = centrality(mk([0.50, 0.4025, 3.0125]), BUILDS)
    good_cent = centrality(mk([0.9025, 0.4025, 3.0125]), BUILDS)
    seen = {verdict_of(bad_cent, []),
            verdict_of(good_cent, [{"outside": True}] * 6),
            verdict_of(good_cent, [{"outside": False}])}
    assert seen == {"HALT_CENTRALITY", "HALT_NOT_BETWEEN", "PASS"}


# ── the STRUCTURAL defence, which does not depend on the gate at all ────────
def test_injected_turns_are_excluded_from_measurement():
    log = [{"valid": True, "injected": False, "surface": "a"},
           {"valid": True, "injected": True, "surface": "POOL"},
           {"valid": True, "injected": False, "surface": "b"}]
    assert [e["surface"] for e in measurable_turns(log)] == ["a", "b"]


def test_invalid_turns_are_excluded_too():
    log = [{"valid": False, "injected": False, "surface": None},
           {"valid": True, "injected": False, "surface": "a"}]
    assert [e["surface"] for e in measurable_turns(log)] == ["a"]


def test_exclusion_is_not_vacuous_it_actually_drops_something():
    log = [{"valid": True, "injected": True, "surface": "P"}] * 3
    assert measurable_turns(log) == []
