"""Tests for `tools/act2_ki_attribution.py`.

⛔⛔ THE POINT OF THIS FILE IS THAT THE INSTRUMENT CAN COME BACK NEGATIVE. A
re-analysis tool that only ever agrees with the hypothesis that motivated it is
the self-confirming-counter shape again. So the permutation test is exercised on
BOTH synthetic worlds — global-flat and ka-coupled — and is required to separate
them.

⭐ AND THE DEGENERACY GATE IS WITNESSED BY THE REAL TRANSCRIPT IT VOIDED. Run 3's
probe reads force `ki` 100 % of the time (18/18, 25/25) because it is echoing a
`ki`-final seed seven surfaces wide. That file is the regression witness: if the
gate ever stops firing on it, a 7-surface echo loop becomes a substrate baseline.
"""
from __future__ import annotations

import json
import pathlib
import random
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from act2_ki_attribution import (                                  # noqa: E402
    MIN_DISTINCT_RATIO, TARGET, Void, assert_not_degenerate, contrast,
    forces_from, mde, permutation_p)
from tlon.discourse import force_map as FM                         # noqa: E402

UNIFORM = [f for f in FM.ORDER if FM.verdict(f) == FM.UNIFORM]


# ── the degeneracy gate ───────────────────────────────────────────────────────
def test_gate_fires_on_the_real_run3_transcript():
    """⛔ THE REGRESSION WITNESS. This exact file would have supplied a false
    substrate baseline of 'run 3 asks 100 % of the time'."""
    p = ROOT / "runs/act2/harden/exchange_probe.json"
    if not p.exists():
        pytest.skip("run-3 probe not on this checkout")
    d = json.loads(p.read_text(encoding="utf-8"))
    for key in ("transcript_interacting", "transcript_control"):
        with pytest.raises(Void, match="DEGENERATE"):
            assert_not_degenerate(d[key], key)


def test_gate_passes_a_healthy_transcript():
    """A legitimate no-op must not be red."""
    assert_not_degenerate([f"s{i}" for i in range(40)], "healthy")


def test_gate_boundary_is_the_declared_constant_not_a_vibe():
    n = 100
    below = [f"s{i}" for i in range(int(n * MIN_DISTINCT_RATIO) - 1)]
    below += ["s0"] * (n - len(below))
    with pytest.raises(Void):
        assert_not_degenerate(below, "below")
    at = [f"s{i}" for i in range(int(n * MIN_DISTINCT_RATIO) + 1)]
    at += ["s0"] * (n - len(at))
    assert_not_degenerate(at, "at")


def test_gate_refuses_empty():
    with pytest.raises(Void):
        assert_not_degenerate([], "empty")


# ── the oracle is enforced in the force extraction ────────────────────────────
def test_forces_from_drops_non_round_tripping():
    assert forces_from(["definitely not a tlon surface"]) == []


def test_forces_from_keeps_only_legal_forces():
    """⭐ arm3 emitted force `"u"`. Nothing outside FM.ORDER may enter a count."""
    for f in forces_from(["har kra sul mläng plon fäm ka"]):
        assert f in FM.ORDER


# ── the contrast ──────────────────────────────────────────────────────────────
def test_contrast_excludes_the_forced_row():
    """⛔ `ki->ka` is deterministic BY DESIGN. Letting a design zero into the
    contrast would let the map's own construction masquerade as evidence."""
    trans = [("ki", "ka")] * 100 + [("ka", "ki")] * 10 + [("ko", "ki")] * 10
    c = contrast(trans)
    assert c["pivot_n"] == 10 and c["other_n"] == 10
    assert "ki" not in c["others"]


def test_contrast_refuses_a_non_uniform_pivot():
    with pytest.raises(Void, match="not a uniform row"):
        contrast([("ka", "ki")], pivot="ki")


def test_contrast_rates_are_conditional_not_marginal():
    trans = [("ka", "ki")] * 5 + [("ka", "ko")] * 5 + [("ko", "ko")] * 10
    c = contrast(trans)
    assert c["pivot_rate"] == pytest.approx(0.5)
    assert c["other_rate"] == pytest.approx(0.0)


# ── ⛔⛔ THE INSTRUMENT MUST BE ABLE TO SAY 'NO' ───────────────────────────────
def _synth(rate_by_prior: dict, n_per: int, seed: int) -> list[tuple]:
    rng = random.Random(seed)
    out = []
    for prior, rate in rate_by_prior.items():
        for _ in range(n_per):
            other = [f for f in FM.ORDER if f != TARGET]
            out.append((prior, TARGET if rng.random() < rate
                        else rng.choice(other)))
    return out


def test_permutation_does_NOT_refute_a_genuinely_flat_world():
    """⭐ THE NEGATIVE CONTROL. Equal rates on every prior ⇒ must not fire."""
    flat = _synth({f: 0.10 for f in UNIFORM}, 200, seed=5)
    p = permutation_p(flat, contrast(flat), trials=2000, seed=5)
    assert p > 0.05, f"fired on a flat world (p={p})"


def test_permutation_DOES_refute_a_ka_coupled_world():
    """And the positive control, so the negative one is not just a dead test."""
    coupled = _synth({"ka": 0.35, "ko": 0.05, "ku": 0.05, "kä": 0.05},
                     200, seed=5)
    p = permutation_p(coupled, contrast(coupled), trials=2000, seed=5)
    assert p < 0.05, f"missed a real coupling (p={p})"


def test_permutation_is_two_sided():
    """A coupling in the OTHER direction must fire too — arm1 pointed that way."""
    rev = _synth({"ka": 0.05, "ko": 0.35, "ku": 0.35, "kä": 0.35}, 200, seed=7)
    p = permutation_p(rev, contrast(rev), trials=2000, seed=7)
    assert p < 0.05


# ── the MDE, which is the guard against reading an underpowered null ──────────
def test_mde_shrinks_as_n_grows():
    """⛔⛔ THE `kä` MISTAKE, MADE MECHANICAL. A small sample must DECLARE a large
    minimum detectable effect so its null cannot be read as flatness."""
    small = mde(9, 16, 0.066, trials=600, seed=2)
    large = mde(181, 319, 0.066, trials=600, seed=2)
    assert small > large, f"small n declared a smaller MDE ({small} vs {large})"


def test_mde_at_the_real_heldout_size_exceeds_the_real_effect():
    """The held-out arm genuinely cannot see the effect. Asserted, not asserted-to."""
    assert mde(9, 16, 0.066, trials=600, seed=2) > 0.0723
