"""DIAGNOSTIC C MUST NOT REPORT A MOVE IT CANNOT RESOLVE. $0, offline.

⛔⛔ RUN 4's CURVE WAS 9, 12, 12, 9, 12, 7, 10, 10 OF 12 AND THE TOOL CALLED IT
"OVERTRAINED — rose to 100 % at step 1000, fell to 83 %." It is not overtrained.
It is not monotone in either direction. Observed scatter is **1.81 items**
against a binomial **1.27** at p≈0.84 — entirely consistent with a flat ~84 %.

⛔ THE CAUSE WAS A THRESHOLD BELOW ITS OWN NOISE: `rose`/`fell` compared against
a fixed **0.1**, and the binomial sd at n=12 near p=0.85 is **0.106**. The bar
sat UNDER one standard deviation, so the verdict fired on sampling noise BY
CONSTRUCTION — a check that cannot help but find something.

⭐ AND "NEVER ROSE" WOULD HAVE BEEN JUST AS WRONG, IN THE OTHER DIRECTION. That
is a claim about the MODEL, and run 4's adapter went 0 % → 82 % render. The
12-sample curve simply cannot see the shape. A statement about the instrument
must not be dressed as a statement about the model.

Same lesson as HARDEN 2 one level up: do not key a verdict to a metric that
cannot express the thing the verdict claims.
"""
from __future__ import annotations

import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import act2_diagnose_c as D                                    # noqa: E402

#: Verbatim from `runs/act2/tlon_run4/logs/diagnosis_c.json`.
RUN4 = [9, 12, 12, 9, 12, 7, 10, 10]


def curve(vals, n=12):
    return [{"step": 500 * (i + 1), "valid": v, "n": n, "dependence": 1.0}
            for i, v in enumerate(vals)]


# ══ THE MEASURED MISREAD ═════════════════════════════════════════════════
def test_run4s_real_curve_is_NOT_called_overtrained():
    """⛔⛔ THE REGRESSION PIN, ON THE ACTUAL DATA."""
    assert "OVERTRAINED" not in D.read_curve(curve(RUN4))


def test_run4s_real_curve_is_NOT_called_never_rose_either():
    """⛔ The opposite error. That adapter reached 82 % render; 'never rose'
    would be a false claim about the model."""
    reading = D.read_curve(curve(RUN4))
    assert "NEVER ROSE" not in reading


def test_run4s_real_curve_is_reported_as_an_INSTRUMENT_limit():
    reading = D.read_curve(curve(RUN4))
    assert "NO RESOLVED TREND" in reading
    assert "instrument" in reading
    assert "n=12" in reading


# ══ THE GUARD IS NOT MERELY A WALL — REAL SHAPES STILL FIRE ══════════════
def test_a_REAL_rise_is_still_called():
    assert "ROSE AND HELD" in D.read_curve(curve([1, 4, 8, 11, 12, 12]))


def test_a_REAL_overtrain_is_still_called():
    assert "OVERTRAINED" in D.read_curve(curve([2, 12, 12, 9, 5, 3]))


def test_a_genuine_floor_is_still_called():
    r = D.read_curve(curve([0, 0, 0, 1, 0, 0]))
    assert "STAYED ON THE FLOOR" in r


def test_a_tiny_wobble_is_called_UNRESOLVED_not_flat():
    r = D.read_curve(curve([10, 11, 10, 11, 10, 11]))
    assert "WITHIN NOISE" in r and "UNRESOLVED" in r


# ══ THE BAR IS TIED TO n, WHICH IS THE WHOLE FIX ═════════════════════════
def test_the_same_curve_becomes_readable_at_larger_n():
    """⭐ THE POINT: the shape did not change, the RESOLUTION did. A verdict
    that ignores n gives the same answer to a 12-sample and a 1200-sample
    curve, which is how run 4's reading happened."""
    shape = [0.75, 1.0, 1.0, 0.75, 1.0, 0.58, 0.83, 0.83]
    small = curve([round(v * 12) for v in shape], n=12)
    large = curve([round(v * 600) for v in shape], n=600)
    assert "NO RESOLVED TREND" in D.read_curve(small)
    # at n=600 the same swings are far outside noise and must be readable
    assert "NO RESOLVED TREND" not in D.read_curve(large)


def test_the_resolution_is_REPORTED_not_just_applied():
    """A reader must be able to see what the run could and could not have
    shown, without re-deriving it."""
    assert "resolution at n=" in D.read_curve(curve([1, 4, 8, 11, 12, 12]))


@pytest.mark.parametrize("n", [4, 12, 64])
def test_the_bar_never_drops_below_the_floor(n):
    """⛔ Near p=0 or p=1 the standard error itself collapses, and a one-item
    move must never become a 'trend'. MIN_REAL_MOVE is the backstop."""
    assert D.MIN_REAL_MOVE >= 0.15
    r = D.read_curve(curve([n - 1, n, n, n - 1, n], n=n))
    assert "OVERTRAINED" not in r


def test_the_multiplier_and_floor_are_declared_constants():
    """⚠️ Fixed before use; if either moves it should be a visible decision."""
    assert D.NOISE_SD_MULT == 2.0
    assert 0.0 < D.MIN_REAL_MOVE < 1.0
