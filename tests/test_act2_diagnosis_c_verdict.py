"""HARDEN 2 — THE DIAGNOSIS-C VERDICT READ A SATURATED METRIC. $0.00, offline.

⛔⛔ IT KEYED ON `dependence`, WHICH IS +1.00 FOR ANY FUNCTIONING MODEL UNDER
GREEDY DECODING. With no variance to read, the verdict printed **"NEVER ROSE"**
on every run regardless of what happened — including run 3, where the real curve
(`valid`) moved **0–1/12 → 12/12 by step 1,000**.

⭐ A verdict keyed to a pinned metric is the vacuity trap one level up: not a test
that cannot fail, but a *report* that cannot say anything else. The fix is not
"pick a better metric once" — it is "notice when the metric cannot vary", which
is why `_saturated` exists and why the saturated metric is still mentioned in the
output instead of quietly dropped.

Both curves below are the REAL measured ones.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

import act2_diagnose_c as C                                     # noqa: E402


def _rows(valids, deps=None, n=12, start=1000, step=1000):
    deps = deps if deps is not None else [1.0] * len(valids)
    return [{"step": start + i * step, "valid": v, "n": n, "dependence": d}
            for i, (v, d) in enumerate(zip(valids, deps))]


# ══ THE TWO MEASURED CURVES ══════════════════════════════════════════════
def test_RUN_3_the_rise_the_old_verdict_MISSED():
    """⛔⛔ THE RED-PROOF. Run 3's measured speak validity: 12/12 at every
    checkpoint, `dependence` pinned at +1.00 throughout. The old verdict called
    this 'NEVER ROSE'. It must now report that the task was learned before the
    first save — which is the actual finding."""
    reading = C.read_curve(_rows([12, 11, 12, 12, 12, 12]))
    assert "NEVER ROSE" not in reading
    assert "CEILING" in reading and "step 1000" in reading


def test_RUN_2_the_floor_that_really_DID_never_rise():
    """⭐ The contrast case, also measured: run 2's speak validity was 0,0,0,1,1,1
    out of 12. Here 'never rose' is the TRUE reading, and it must still be given —
    a fix that turns every verdict positive is no better than one stuck negative."""
    reading = C.read_curve(_rows([0, 0, 0, 1, 1, 1]))
    assert "NEVER ROSE" in reading and "FLOOR" in reading
    assert "not in the training data" in reading


# ══ THE VERDICT DETECTS ITS OWN SATURATION ═══════════════════════════════
def test_a_saturated_metric_is_NAMED_not_silently_dropped():
    """⛔ The old metric's uselessness must stay visible. Dropping it silently
    would leave the next reader wondering why `dependence` is in the table."""
    reading = C.read_curve(_rows([12] * 6, deps=[1.0] * 6))
    assert "SATURATED" in reading and "dependence" in reading


def test_an_UNsaturated_dependence_is_not_flagged():
    """The warning must be conditional on the measurement, not hardcoded — or it
    is itself a line that can only say one thing."""
    reading = C.read_curve(_rows([2, 5, 9, 12, 12, 12],
                                 deps=[0.2, 0.5, 0.8, 1.0, 1.0, 1.0]))
    assert "SATURATED" not in reading


# ══ EVERY OUTCOME HAS A BRANCH ═══════════════════════════════════════════
@pytest.mark.parametrize("valids,expect", [
    ([0, 2, 6, 10, 12, 12], "ROSE AND HELD"),
    ([0, 4, 11, 12, 6, 2], "OVERTRAINED"),
    ([0, 0, 0, 1, 1, 1], "NEVER ROSE"),
    ([12, 12, 12, 12, 12, 12], "CEILING"),
    ([6, 6, 6, 6, 6, 6], "NEVER ROSE"),
])
def test_each_shape_of_curve_gets_its_own_reading(valids, expect):
    assert expect in C.read_curve(_rows(valids))


def test_too_few_checkpoints_says_so_rather_than_guessing():
    """⛔ Two points cannot distinguish 'rose then fell' from 'rose and held'.
    That is exactly why --save-steps exists, and the verdict must not pretend."""
    assert "too few" in C.read_curve(_rows([12]))


def test_the_overtrained_reading_NAMES_the_peak_step():
    """A verdict that says 'stop earlier' without saying where is not actionable."""
    r = C.read_curve(_rows([0, 4, 11, 12, 6, 2]))
    assert "step 4000" in r


def test_the_reading_is_computed_from_valid_NOT_dependence():
    """⛔⛔ THE ROOT CAUSE, pinned. Identical `valid` curves must give identical
    readings no matter what `dependence` does — otherwise the saturated metric is
    still steering the verdict."""
    a = C.read_curve(_rows([0, 2, 6, 10, 12, 12], deps=[1.0] * 6))
    b = C.read_curve(_rows([0, 2, 6, 10, 12, 12], deps=[0.1, 0.9, 0.2, 1.0, 0.3, 1.0]))
    assert a.split("·")[0].strip() == b.split("·")[0].strip()
