"""⭐ RED-PROOF FOR THE STAGE-2 DISTANCE.

⛔⛔ THE THREAT: a speaker's own conversational fuzz masquerading as drift. If
inflating a speaker's spread moved the part of the metric that reports LOCATION,
then a high-variance build would look like it had converged (or diverged) without
its speakers going anywhere.

⭐ The decomposition is what defends against it, so the decomposition is what is
tested: fuzz must land ENTIRELY in the spread term and leave the mean term
untouched.
"""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

from act2_distance import (MAX_CENTROID_SE_FRACTION, PANEL,  # noqa: E402
                           axis_scale, locatability, w2)

SCALE = np.array([1.0, 1.0])
RNG = np.random.default_rng(20260830)


def cloud(mu, sd, n=14):
    return RNG.normal(mu, sd, size=(n, 2))


def test_the_panel_is_two_axes_and_excludes_the_dropped_ones():
    assert PANEL == ("tokens/surface", "nodes/scene")
    assert "root TTR" not in PANEL and "force:ka" not in PANEL


# ── the s20621 threat ───────────────────────────────────────────────────────
def test_INFLATING_a_speakers_own_spread_does_NOT_move_the_mean_term():
    """⛔⛔ THE LOAD-BEARING ONE. A fuzzy speaker must not appear to have moved."""
    a = cloud([0.0, 0.0], 0.05)
    b = cloud([1.0, 0.0], 0.05)
    tight = w2(a, b, SCALE)
    fuzzy = np.concatenate([a, a * 8.0 - a.mean(axis=0) * 7.0])  # same centroid
    fuzzy = fuzzy - fuzzy.mean(axis=0) + a.mean(axis=0)
    blown = w2(fuzzy, b, SCALE)
    assert blown["spread_term"] > tight["spread_term"] * 2, "fuzz must show up"
    assert abs(blown["mean_term"] - tight["mean_term"]) < 1e-9, (
        "own-variance leaked into the LOCATION term")


def test_a_synthetic_high_variance_speaker_produces_no_spurious_LOCATION_change():
    """Its distance-to-everyone in the mean term must be unchanged."""
    others = {k: cloud([float(k), 0.0], 0.05) for k in range(3)}
    base = cloud([0.5, 0.0], 0.05)
    wide = base * 10.0
    wide = wide - wide.mean(axis=0) + base.mean(axis=0)
    for k, o in others.items():
        assert abs(w2(base, o, SCALE)["mean_term"]
                   - w2(wide, o, SCALE)["mean_term"]) < 1e-9


def test_MOVING_a_speaker_moves_the_mean_term_by_exactly_the_displacement():
    a = cloud([0.0, 0.0], 0.05)
    b = cloud([1.0, 0.0], 0.05)
    moved = a + np.array([0.3, 0.0])
    d0 = np.linalg.norm(a.mean(axis=0) - b.mean(axis=0))
    d1 = np.linalg.norm(moved.mean(axis=0) - b.mean(axis=0))
    assert abs(w2(a, b, SCALE)["mean_term"] - d0 ** 2) < 1e-9
    assert abs(w2(moved, b, SCALE)["mean_term"] - d1 ** 2) < 1e-9


# ── metric sanity ───────────────────────────────────────────────────────────
def test_a_cloud_against_itself_is_zero():
    a = cloud([1.0, 2.0], 0.1)
    r = w2(a, a, SCALE)
    assert r["w2"] < 1e-6 and r["spread_term"] < 1e-9


def test_the_metric_is_symmetric():
    a, b = cloud([0.0, 0.0], 0.1), cloud([1.0, 0.5], 0.2)
    assert abs(w2(a, b, SCALE)["w2"] - w2(b, a, SCALE)["w2"]) < 1e-9


def test_the_spread_term_is_never_negative():
    """A numerical floor, asserted — a negative 'distance' component would make
    the total unreadable."""
    for _ in range(20):
        a, b = cloud([0, 0], RNG.uniform(0.01, 1)), cloud([0, 0], RNG.uniform(0.01, 1))
        assert w2(a, b, SCALE)["spread_term"] >= 0.0


def test_the_scale_makes_axes_commensurate():
    """Without it, tokens/surface (~7.0) would swamp nodes/scene (~2.7)."""
    cl = {"a": cloud([7.0, 2.7], 0.2), "b": cloud([7.2, 2.9], 0.2),
          "c": cloud([6.8, 2.5], 0.2), "d": cloud([7.1, 2.8], 0.2)}
    s = axis_scale(cl)
    assert s.shape == (2,) and (s > 0).all()
    raw = w2(cl["a"], cl["b"], np.array([1.0, 1.0]))["mean_term"]
    scaled = w2(cl["a"], cl["b"], s)["mean_term"]
    assert scaled != raw


# ── locatability, and its halt ──────────────────────────────────────────────
def test_a_tight_population_is_locatable():
    # ⛔ both axes must separate: a fixture flat on one axis makes that axis's
    # "between-build sd" pure centroid noise, and nothing is ever locatable.
    cl = {n: cloud([float(i), float(i) * 0.5], 0.02) for i, n in enumerate("abcd")}
    rows, _ = locatability(cl, axis_scale(cl))
    assert all(r["locatable"] for r in rows.values())


def test_a_speaker_too_fuzzy_to_PLACE_is_refused():
    """⛔ The gate must be able to fail, or it has been consulted not passed."""
    cl = {n: cloud([float(i), float(i) * 0.5], 0.02) for i, n in enumerate("abc")}
    cl["fuzzy"] = cloud([1.5, 0.75], 5.0)
    rows, _ = locatability(cl, axis_scale(cl))
    assert rows["fuzzy"]["locatable"] is False
    assert any(r["locatable"] for k, r in rows.items() if k != "fuzzy")


def test_locatability_improves_with_MORE_CONVERSATIONS_not_more_speakers():
    """⭐ se falls as 1/sqrt(n), so the fix for an unlocatable build is more
    conversations from it — the thing the halt message must say."""
    cl_small = {n: cloud([float(i), float(i) * 0.5], 0.5, n=6)
                for i, n in enumerate("abcd")}
    scale = axis_scale(cl_small)          # one frozen ruler for both
    small, _ = locatability(cl_small, scale)
    cl_big = {n: cloud([float(i), float(i) * 0.5], 0.5, n=200)
              for i, n in enumerate("abcd")}
    big, _ = locatability(cl_big, scale)
    assert (statistics_mean(big) < statistics_mean(small)), "more n must help"


def statistics_mean(rows):
    return sum(r["worst"] for r in rows.values()) / len(rows)


def test_the_threshold_is_the_declared_one():
    assert MAX_CENTROID_SE_FRACTION == 0.5


# (sd=0.5, n=4) is deliberately NOT here: se=0.25 against a population
# spread of ~0.82 is genuinely locatable, and asserting otherwise would
# have been a test demanding the wrong answer.
@pytest.mark.parametrize("sd,n", [(1.5, 4), (2.0, 14)])
def test_a_wide_speaker_with_few_conversations_is_not_locatable(sd, n):
    cl = {k: cloud([float(i), float(i) * 0.5], 0.02) for i, k in enumerate("abc")}
    cl["w"] = cloud([1.0, 0.5], sd, n=n)
    rows, _ = locatability(cl, axis_scale(cl))
    assert rows["w"]["locatable"] is False
