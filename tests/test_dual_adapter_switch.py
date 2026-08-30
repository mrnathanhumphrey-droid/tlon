"""⭐⭐ RED-PROOF FOR THE ADAPTER SWITCH — the arc's original bug, third disguise.

⛔⛔ If `set_adapter` silently no-ops, ONE set of weights generates both sides of
the conversation while every surface check still passes: two adapter paths on the
command line, two labels, two distinct backend objects, `_assert_two` satisfied.
That is one impression talking to itself, which is exactly what made every prior
Act 2 "interaction" mechanically incapable of showing coupling.

⭐ The switch is therefore READ BACK, not trusted, and the tests below prove the
read-back bites against a model that lies.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

from act2_dual_backend import (AdapterSwitchError,  # noqa: E402
                               DualAdapterCore)


class FakeModel:
    """Honest: set_adapter actually changes active_adapter."""

    def __init__(self):
        self.active_adapter = None

    def set_adapter(self, name):
        self.active_adapter = name


class StuckModel(FakeModel):
    """⛔ THE FAULT. `set_adapter` runs, returns None, and changes nothing —
    so every generation comes from whichever adapter loaded first."""

    def set_adapter(self, name):
        if self.active_adapter is None:
            self.active_adapter = name          # first call appears to work


class ListActiveModel(FakeModel):
    """PEFT has reported `active_adapter` as a list in places."""

    def set_adapter(self, name):
        self.active_adapter = [name]


# ── the core contract ───────────────────────────────────────────────────────
def test_two_distinct_adapters_are_required():
    with pytest.raises(ValueError, match="(?i)distinct|identical"):
        DualAdapterCore(FakeModel(), ("A", "A"))


def test_an_honest_switch_is_recorded():
    c = DualAdapterCore(FakeModel(), ("A", "B"))
    c.activate("A")
    c.activate("B")
    assert c.switches == ["A", "B"]
    assert c.usage() == {"A": 1, "B": 1}


def test_an_unknown_adapter_is_refused():
    c = DualAdapterCore(FakeModel(), ("A", "B"))
    with pytest.raises(ValueError, match="unknown adapter"):
        c.activate("C")


def test_a_list_valued_active_adapter_is_accepted():
    c = DualAdapterCore(ListActiveModel(), ("A", "B"))
    c.activate("A")
    assert c.switches == ["A"]


# ── ⛔⛔ THE ONE THAT MATTERS ────────────────────────────────────────────────
def test_a_SILENTLY_STUCK_switch_RAISES_instead_of_generating_from_one_model():
    """The whole point: `set_adapter` that does nothing must not pass."""
    c = DualAdapterCore(StuckModel(), ("A", "B"))
    c.activate("A")                                  # fine — A really is active
    with pytest.raises(AdapterSwitchError, match="one set of weights"):
        c.activate("B")


def test_the_readback_is_what_catches_it_not_the_call_returning():
    """A model whose set_adapter returns cleanly but lies must still fail."""
    class Liar(FakeModel):
        def set_adapter(self, name):
            self.active_adapter = "A"                # always A, silently

    c = DualAdapterCore(Liar(), ("A", "B"))
    c.activate("A")
    with pytest.raises(AdapterSwitchError):
        c.activate("B")


# ── run-time guards on the finished transcript ──────────────────────────────
def test_a_transcript_where_one_adapter_NEVER_SPOKE_is_refused():
    c = DualAdapterCore(FakeModel(), ("A", "B"))
    for _ in range(6):
        c.activate("A")
    with pytest.raises(AdapterSwitchError, match="never generated"):
        c.assert_two_speakers_spoke()


def test_non_alternating_turns_are_refused():
    c = DualAdapterCore(FakeModel(), ("A", "B"))
    for n in ("A", "A", "B", "B"):
        c.activate(n)
    with pytest.raises(AdapterSwitchError, match="did not alternate"):
        c.assert_two_speakers_spoke()


def test_a_properly_alternating_exchange_passes():
    c = DualAdapterCore(FakeModel(), ("A", "B"))
    for i in range(40):
        c.activate("A" if i % 2 == 0 else "B")
    c.assert_two_speakers_spoke()
    assert c.usage() == {"A": 20, "B": 20}


def test_the_guard_can_FAIL_so_it_has_not_merely_been_consulted():
    """⛔ Guard on the guard: the same assertion must reject the one-speaker
    transcript and accept the two-speaker one."""
    ok = DualAdapterCore(FakeModel(), ("A", "B"))
    for i in range(10):
        ok.activate("A" if i % 2 == 0 else "B")
    ok.assert_two_speakers_spoke()

    bad = DualAdapterCore(FakeModel(), ("A", "B"))
    for _ in range(10):
        bad.activate("A")
    with pytest.raises(AdapterSwitchError):
        bad.assert_two_speakers_spoke()


# ── the guard must be SCOPED to one arm ─────────────────────────────────────
def test_the_guard_scoped_to_the_LIVE_arm_ignores_one_sided_arms():
    """⛔⛔ CAUGHT ON THE FIRST REAL RUN. COLD is one speaker alone and each
    YOKED arm is one live speaker against a recording, so a cumulative
    alternation check fails on arms that are CORRECTLY one-sided."""
    c = DualAdapterCore(FakeModel(), ("A", "B"))
    for _ in range(8):                      # COLD: A alone — legitimately
        c.activate("A")
    mark = c.mark()
    for i in range(8):                      # LIVE: alternating
        c.activate("A" if i % 2 == 0 else "B")
    c.assert_two_speakers_spoke(since=mark)          # passes, scoped
    with pytest.raises(AdapterSwitchError, match="did not alternate"):
        c.assert_two_speakers_spoke()                # fails, cumulative
    assert c.usage_since(mark) == {"A": 4, "B": 4}
    assert c.usage() == {"A": 12, "B": 4}            # the observed failure


def test_a_one_sided_LIVE_arm_still_fails_when_scoped():
    """Scoping must not become a way of not looking."""
    c = DualAdapterCore(FakeModel(), ("A", "B"))
    c.activate("B")
    mark = c.mark()
    for _ in range(6):
        c.activate("A")
    with pytest.raises(AdapterSwitchError, match="never generated"):
        c.assert_two_speakers_spoke(since=mark)
