"""⭐ RED-PROOF FOR THE STAGE-1 GATE.

⛔⛔ A gate that cannot return a negative has not been passed, it has been
consulted. Stage 1 is the first gate in the arc that can honestly END it on a
$0 re-analysis, so the halt must be demonstrated to FIRE — not assumed.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

from act2_ranking_stability import (MAX_CI_UPPER, MAX_RANK_RANGE, admit,  # noqa: E402
                                    contamination, verdict_of)


# ── the gate refuses ────────────────────────────────────────────────────────
def test_a_stable_cheap_observable_is_admitted():
    assert admit(0, 0.10) is True
    assert admit(MAX_RANK_RANGE, MAX_CI_UPPER - 0.01) is True


def test_an_unstable_RANK_is_refused_even_with_a_tiny_CI():
    """The k=4 failure mode: looked great, moved when builds were added."""
    assert admit(MAX_RANK_RANGE + 1, 0.01) is False


def test_a_wide_CI_is_refused_even_with_a_perfectly_stable_rank():
    assert admit(0, MAX_CI_UPPER + 0.01) is False


def test_the_boundary_is_exclusive_on_the_CI_and_inclusive_on_the_rank():
    assert admit(MAX_RANK_RANGE, MAX_CI_UPPER) is False       # < , not <=
    assert admit(MAX_RANK_RANGE, MAX_CI_UPPER - 1e-9) is True


def test_a_NaN_CI_is_refused_not_admitted():
    """An empty bootstrap must never read as admissible."""
    assert admit(0, float("nan")) is False


def test_an_infinite_contamination_is_refused():
    assert admit(0, float("inf")) is False


# ── the verdict, including the halt ─────────────────────────────────────────
def test_zero_qualifiers_HALTS():
    assert verdict_of([]) == "HALT"


@pytest.mark.parametrize("n", [1, 2])
def test_one_or_two_qualifiers_is_NARROW_not_a_full_panel(n):
    assert verdict_of(["o%d" % i for i in range(n)]) == "NARROW"


def test_three_qualifiers_is_a_PANEL():
    assert verdict_of(["a", "b", "c"]) == "PANEL"


def test_the_halt_is_reachable_from_real_shaped_input():
    """⭐ GUARD ON THE GUARD — the whole pipeline must be able to reach HALT.

    If every synthetic build set produced a panel, the halt would be decorative.
    """
    rows = [{"admitted": admit(5, 0.9)}, {"admitted": admit(4, 2.0)}]
    assert verdict_of([r for r in rows if r["admitted"]]) == "HALT"


# ── contamination itself ────────────────────────────────────────────────────
def _mk(vals):
    """A build whose observable reads `v` everywhere -> zero movement."""
    return [{"all": v, "first": v, "second": v} for v in vals]


def _mk_moving(pairs):
    """A build that MOVES within each conversation: (first, second) per exchange.

    `all` is the first half so the build mean is well defined and independent of
    the movement, which is what the two terms of contamination need.
    """
    return [{"all": [f], "first": [f], "second": [s]} for f, s in pairs]


def test_contamination_needs_at_least_two_builds():
    pb = {"a": _mk([[1.0]])}
    assert contamination(pb, ["a"], lambda s: s[0]) is None


def test_zero_movement_is_infinite_contamination_not_zero():
    """⛔ A CONSTANT HAS NO BUILD-VARIANCE AND CANNOT REGISTER DRIFT.

    It must come out UNUSABLE (inf), never as the best candidate — the exact
    trap `distinct-surface` fell into in the exploratory screen.
    """
    pb = {"a": _mk([[1.0], [2.0]]), "b": _mk([[3.0], [4.0]])}
    assert contamination(pb, ["a", "b"], lambda s: s[0]) == float("inf")


def test_contamination_recomputes_BOTH_terms_from_the_given_builds():
    """Dropping a build must be able to change the value; a denominator held
    fixed across resamples would describe a quantity never actually computed."""
    pb = {"a": _mk_moving([(1.0, 1.5), (1.0, 1.5)]),
          "b": _mk_moving([(1.2, 1.7), (1.2, 1.7)]),
          "c": _mk_moving([(9.0, 9.5), (9.0, 9.5)])}   # far-out build
    fn = lambda s: s[0]                                            # noqa: E731
    with_c = contamination(pb, ["a", "b", "c"], fn)
    without = contamination(pb, ["a", "b"], fn)
    assert with_c not in (None, float("inf"))
    assert without not in (None, float("inf"))
    # `c` sits far from a and b, so including it must widen the spread.
    assert with_c > without
