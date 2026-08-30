"""⭐⭐ RED-PROOF FOR THE ASYMMETRIC TWO-SPEAKER HARNESS.

Spec: docs/SPEC_TWO_SPEAKER_DRIFT_2026_08_30.md §4

⛔⛔ THE FAULT THIS GUARDS IS THE WORST FALSE POSITIVE AVAILABLE. A harness that
CLAIMS self-accumulation but leaks the partner's older turns would report drift
that is really SHARED CONTENT — two speakers looking at the same text and
therefore resembling each other. That reads as convergence and is not.

⛔⛔ AND THE FAULT IT REPLACES IS ALREADY IN THE RECORD: every "interacting"
exchange in Act 2 gave speaker A and speaker B THE SAME ADAPTER — one backend,
two labels — so the coupling column was mechanically zero. The two-backend test
below asserts distinctness rather than assuming it, because that fault looked
correct for months.

⭐ Written BEFORE the module, and each test names the specific way the harness
could silently be the old one wearing a new name.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

from act2_two_speaker import (COLD, LIVE, SEED_SPEAKER, InjectionPlan,  # noqa: E402
                              exchange_two, plan_injections, visible_history)


# ── fixtures ────────────────────────────────────────────────────────────────
SEED = ("s1", "s2", "s3", "s4", "s5")


def hist_of(pairs):
    return list(pairs)


class Spy:
    """⭐ RECORDS WHAT IT ACTUALLY RECEIVED. A knob that silently no-ops returns
    'the metaphysics holds' for the worst possible reason."""

    def __init__(self, label, emit):
        self.label, self._emit, self.seen = label, emit, []

    def speak(self, history, turn):
        self.seen.append(tuple(history))
        return self._emit(self.label, turn)


def _emit(label, turn):
    return "%s%d" % (label, turn)


# ── 1 · the partner's past must NOT be reachable ────────────────────────────
def test_a_speaker_sees_its_OWN_chain_accumulated():
    h = hist_of([("A", "a0"), ("B", "b0"), ("A", "a1"), ("B", "b1")])
    shown = visible_history(h, "A", mode=LIVE)
    assert "a0" in shown and "a1" in shown


def test_a_speaker_sees_ONLY_THE_LATEST_partner_turn():
    h = hist_of([("A", "a0"), ("B", "b0"), ("A", "a1"), ("B", "b1")])
    shown = visible_history(h, "A", mode=LIVE)
    assert "b1" in shown, "the present provocation must be there"
    assert "b0" not in shown, "⛔ THE COINS CEASED TO EXIST WHEN THEY WERE LOST"


def test_the_partners_ENTIRE_past_is_unreachable_at_depth():
    """The load-bearing one: at turn 40, B's turn 1 must be gone."""
    h = []
    for t in range(40):
        h.append(("A" if t % 2 == 0 else "B", "t%d" % t))
    shown = visible_history(h, "A", mode=LIVE)
    partner_visible = [s for s in shown if s in {"t%d" % t for t in range(1, 40, 2)}]
    assert partner_visible == ["t39"], (
        "exactly one partner surface may be visible, the most recent; got %r"
        % partner_visible)
    assert all("t%d" % t in shown for t in range(0, 40, 2)), "own chain intact"


def test_the_provocation_is_LAST_so_it_sits_in_the_present():
    h = hist_of([("A", "a0"), ("B", "b0")])
    assert visible_history(h, "A", mode=LIVE)[-1] == "b0"


# ── 2 · guard on the guard ──────────────────────────────────────────────────
def _leaky_visible_history(hist, me, **kw):
    """The OLD behaviour: one shared list, everyone sees everything.

    ⭐ This is not a strawman — it is `act2_exchange_probe.exchange()` with
    `history_window=None`, which generated all 24 accumulating transcripts.
    """
    return tuple(s for _, s in hist)


def _assert_self_only_plus_one(fn):
    """The exact assertion the real tests make, applied to any implementation."""
    hist = [("A" if t % 2 == 0 else "B", "t%d" % t) for t in range(40)]
    shown = fn(hist, "A", mode=LIVE)
    partner = [s for s in shown if s in {"t%d" % t for t in range(1, 40, 2)}]
    assert partner == ["t39"], "leaked %d partner surfaces" % len(partner)


def test_the_spy_assertion_CATCHES_the_real_leaky_implementation():
    """⛔⛔ GUARD ON THE GUARD. If the assertion passed against full
    accumulation, every test above would be decorative — and a harness that
    leaks the partner reports drift that is really SHARED CONTENT, the worst
    false positive available."""
    _assert_self_only_plus_one(visible_history)          # the real one passes
    with pytest.raises(AssertionError, match="leaked 20 partner surfaces"):
        _assert_self_only_plus_one(_leaky_visible_history)


def test_the_spy_assertion_also_catches_a_WINDOW_1_implementation():
    """The other wrong regime: it denies the speaker its own memory."""
    def window_1(hist, me, **kw):
        return tuple(s for _, s in hist[-1:])

    hist = [("A" if t % 2 == 0 else "B", "t%d" % t) for t in range(40)]
    own = [s for s in window_1(hist, "A") if s in {"t%d" % t for t in range(0, 40, 2)}]
    assert own == [], "window-1 keeps no self-chain, which is the fault"
    assert len([s for s in visible_history(hist, "A", mode=LIVE)
                if s in {"t%d" % t for t in range(0, 40, 2)}]) == 20


def test_seed_history_is_PARTNER_material_not_own_memory():
    """A speaker cannot have remembered what it never said."""
    h = [(SEED_SPEAKER, s) for s in SEED]
    shown = visible_history(h, "A", mode=LIVE)
    assert shown == ("s5",), (
        "at turn 0 a speaker has no own chain and exactly one provocation")


def test_truncation_applies_FROM_TURN_ZERO_including_into_the_seed():
    """Carried from the window-1 guard: a version that truncated only after the
    seed accumulated would silently give early turns full context."""
    h = [(SEED_SPEAKER, s) for s in SEED] + [("A", "a0")]
    shown = visible_history(h, "B", mode=LIVE)
    assert "s1" not in shown and "s4" not in shown
    assert shown[-1] == "a0"


# ── 3 · COLD ────────────────────────────────────────────────────────────────
def test_cold_has_NO_partner_material_once_the_self_chain_exists():
    h = [(SEED_SPEAKER, s) for s in SEED] + [("A", "a0"), ("A", "a1")]
    shown = visible_history(h, "A", mode=COLD)
    assert shown == ("a0", "a1")
    assert not any(s.startswith("s") for s in shown)


def test_cold_is_provoked_once_so_it_is_not_a_cold_start():
    h = [(SEED_SPEAKER, s) for s in SEED]
    assert visible_history(h, "A", mode=COLD) == ("s5",)


# ── 4 · injections, and their yoking ────────────────────────────────────────
def test_the_injection_plan_is_DETERMINISTIC_from_its_seed():
    p1 = plan_injections(seed=11, turns=40, n=4, pool=("x", "y", "z"))
    p2 = plan_injections(seed=11, turns=40, n=4, pool=("x", "y", "z"))
    assert p1 == p2


def test_a_different_seed_gives_a_different_plan():
    p1 = plan_injections(seed=11, turns=40, n=4, pool=("x", "y", "z"))
    p2 = plan_injections(seed=12, turns=40, n=4, pool=("x", "y", "z"))
    assert p1 != p2


def test_the_SAME_plan_object_is_what_yokes_the_conditions():
    """⛔ An injection that lands in LIVE but not in the null IS the difference
    being measured."""
    p = plan_injections(seed=11, turns=40, n=4, pool=("x", "y", "z"))
    a = [p.at(t) for t in range(40)]
    b = [p.at(t) for t in range(40)]
    assert a == b and any(v is not None for v in a)


def test_an_injected_surface_is_VISIBLE_at_its_turn():
    h = hist_of([("A", "a0"), ("B", "b0")])
    shown = visible_history(h, "A", mode=LIVE, injected="INJ")
    assert "INJ" in shown


def test_injections_are_requested_at_exactly_n_turns():
    p = plan_injections(seed=5, turns=40, n=6, pool=("x",))
    assert sum(p.at(t) is not None for t in range(40)) == 6


def test_an_injection_plan_cannot_exceed_the_turns_available():
    with pytest.raises(ValueError):
        plan_injections(seed=5, turns=4, n=9, pool=("x",))


def test_an_empty_pool_is_refused_rather_than_silently_injecting_nothing():
    with pytest.raises(ValueError):
        plan_injections(seed=5, turns=40, n=2, pool=())


# ── 5 · two speakers, actually two ──────────────────────────────────────────
def test_exchange_two_REFUSES_the_same_speaker_object_twice():
    """⛔⛔ THE FAULT THAT MADE EVERY PRIOR RESULT ONE IMPRESSION AND A MIRROR."""
    s = Spy("A", _emit)
    with pytest.raises(ValueError, match="(?i)same|distinct|one speaker"):
        exchange_two(s, s, turns=4, seed_history=SEED)


def test_exchange_two_REFUSES_two_speakers_sharing_one_backend():
    class Shared:
        pass

    back = Shared()
    a, b = Spy("A", _emit), Spy("B", _emit)
    a.backend = b.backend = back
    with pytest.raises(ValueError, match="(?i)backend"):
        exchange_two(a, b, turns=4, seed_history=SEED)


def test_two_distinct_speakers_with_distinct_backends_are_accepted():
    a, b = Spy("A", _emit), Spy("B", _emit)
    a.backend, b.backend = object(), object()
    log = exchange_two(a, b, turns=4, seed_history=SEED)
    assert len(log) == 4


# ── 6 · end to end: what the spy actually received ──────────────────────────
def test_at_depth_the_spy_confirms_self_only_plus_one():
    a, b = Spy("A", _emit), Spy("B", _emit)
    a.backend, b.backend = object(), object()
    exchange_two(a, b, turns=20, seed_history=SEED)
    last = a.seen[-1]                       # A's context on its final turn
    own = [s for s in last if s.startswith("A")]
    partner = [s for s in last if s.startswith("B")]
    assert len(own) >= 8, "the self-chain must actually accumulate"
    assert len(partner) == 1, "exactly one partner surface, the latest"


def test_the_history_REALLY_GROWS_or_every_test_above_is_vacuous():
    a, b = Spy("A", _emit), Spy("B", _emit)
    a.backend, b.backend = object(), object()
    exchange_two(a, b, turns=20, seed_history=SEED)
    assert len(a.seen[-1]) > len(a.seen[0])
