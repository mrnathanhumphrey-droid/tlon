"""TRUNCATION RED-PROOF — the knob must actually truncate, or the run lies. $0.

⛔⛔ WITHOUT THIS TEST PASSING, A POSITIVE LOCALITY RESULT IS UNINTERPRETABLE.
`--history-window 1` is the whole architecture: it is the claim that turn 40 is
structurally identical to turn 1. If the knob silently no-ops, the exchange runs
on FULL history, and "it did not collapse" would mean *the model saw everything
and happened to hold together* — which says nothing whatsoever about depth-1, in
exactly the direction that flatters the hypothesis.

⭐ SO THE PROOF IS A SPY, NOT AN INSPECTION. A speaker that RECORDS what it was
handed, asserted against what the architecture requires. And the mutation is
asserted too: with the knob off, the same spy must see MORE — a test that passes
whether or not the knob does anything is not a red-proof, it is a decoration.
"""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "xp", pathlib.Path(__file__).parents[1] / "tools" / "act2_exchange_probe.py")
xp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(xp)

#: A five-deep seed, so "truncates into the seed" is testable at turn 0.
SEED = ("kra mil ka", "song tris ki", "fim hen ko", "hom nal ku", "vel dor kä")


class Spy:
    """Records every history it is handed. Emits nothing valid, so the exchange
    never appends — which keeps the *seed* the thing under test."""

    def __init__(self):
        self.seen: list[tuple] = []

    def speak(self, history, turn):
        self.seen.append(tuple(history))
        return None


class Painter:
    """Emits a REAL, schema-valid proposal each turn so history GROWS — needed
    to prove the window stays fixed as depth increases.

    ⛔ AN EARLIER VERSION OF THIS SPY FAKED THE PROPOSAL (`{force, surface}`) AND
    `PS.validate` SILENTLY REJECTED EVERY ONE, so nothing was ever appended and
    history never grew. The truncation assertions all still passed — because a
    window of 1 over a history that never grows is trivially 1. **The fake spy
    made the hardest test vacuous**, which is the same shape as a probe that
    cannot come back positive. Real proposals, from the real corpus.
    """

    def __init__(self, surfaces):
        self.seen: list[tuple] = []
        self._s = list(surfaces)
        self._i = 0

    def speak(self, history, turn):
        from tlon.act2 import schema_bridge as SB
        from tlon.grammar.parse import parse
        self.seen.append(tuple(history))
        s = self._s[self._i % len(self._s)]
        self._i += 1
        return SB.scene_to_proposal(parse(s))


@pytest.fixture(scope="module")
def real_surfaces():
    """Distinct, well-formed surfaces straight from the corpus builder."""
    from tlon.act2 import corpus
    seen, out = set(), []
    for p in corpus.build(400, seed=17):
        if p.surface and p.surface not in seen:
            seen.add(p.surface)
            out.append(p.surface)
        if len(out) == 6:
            break
    assert len(out) == 6
    return out


# ══ THE KNOB TRUNCATES ═══════════════════════════════════════════════════
def test_window_1_hands_over_exactly_one_surface_from_turn_zero():
    """⛔ INCLUDING INTO THE SEED. A version that truncated only once the seed
    had been consumed would give early turns full context, silently."""
    a, b = Spy(), Spy()
    xp.exchange(a, b, turns=6, seed_history=SEED, history_window=1)
    for got in a.seen + b.seen:
        assert len(got) == 1, got


def test_window_1_hands_over_THE_LAST_surface_not_just_one():
    """⭐ LENGTH IS NOT ENOUGH. `hist[:1]` also has length 1 and is the FIRST
    turn — a painter provoked by the oldest thing in the room."""
    a, b = Spy(), Spy()
    xp.exchange(a, b, turns=4, seed_history=SEED, history_window=1)
    for got in a.seen + b.seen:
        assert got == (SEED[-1],), got


@pytest.mark.parametrize("window", [1, 2, 3])
def test_the_window_is_exact_at_every_size(window):
    a, b = Spy(), Spy()
    xp.exchange(a, b, turns=5, seed_history=SEED, history_window=window)
    for got in a.seen + b.seen:
        assert got == tuple(SEED[-window:]), got


# ══ THE MUTATION IS ASSERTED ═════════════════════════════════════════════
def test_WITHOUT_the_knob_the_spy_sees_MORE():
    """⛔⛔ THE HALF THAT MAKES IT A RED-PROOF. If this were also 1, the knob
    would be doing nothing and every test above would pass anyway."""
    a, b = Spy(), Spy()
    xp.exchange(a, b, turns=4, seed_history=SEED, history_window=None)
    assert all(len(g) == len(SEED) for g in a.seen + b.seen)
    assert len(SEED) > 1, "the seed must be deeper than the window to prove it"


def test_the_two_configurations_actually_DIFFER():
    """The comparison the run rests on, made explicit rather than implied."""
    trunc, full = Spy(), Spy()
    xp.exchange(trunc, Spy(), turns=3, seed_history=SEED, history_window=1)
    xp.exchange(full, Spy(), turns=3, seed_history=SEED, history_window=None)
    assert trunc.seen != full.seen
    assert len(trunc.seen[0]) < len(full.seen[0])


# ══ DEPTH-1 IS STABLE AS THE EXCHANGE GROWS ══════════════════════════════
def test_the_history_REALLY_GROWS_or_every_test_below_is_vacuous(real_surfaces):
    """⛔⛔ THE GUARD ON THE GUARD. A window of 1 over a history that never grows
    is trivially 1. This asserts the painter's emissions are actually being
    accepted and appended, so the accumulation tests have something to bite on."""
    a, b = Painter(real_surfaces), Painter(real_surfaces)
    xp.exchange(a, b, turns=12, seed_history=SEED, history_window=None)
    lens = [len(g) for g in a.seen]
    assert lens[-1] > lens[0] + 4, lens


def test_the_window_stays_1_while_history_ACCUMULATES_underneath(real_surfaces):
    """⭐⭐ THE ARCHITECTURE'S CENTRAL CLAIM, MEASURED: turn 40 is structurally
    identical to turn 1. The painter emits and `hist` really does grow (asserted
    above) — the window must not grow with it."""
    a, b = Painter(real_surfaces), Painter(real_surfaces)
    xp.exchange(a, b, turns=40, seed_history=SEED, history_window=1)
    seen = a.seen + b.seen
    assert len(seen) == 40
    assert {len(g) for g in seen} == {1}, sorted({len(g) for g in seen})


def test_the_window_shows_the_MOST_RECENT_emission_not_a_stale_one(real_surfaces):
    """⭐ The window must track the front of the exchange, not sit on the seed."""
    a, b = Painter(real_surfaces), Painter(real_surfaces)
    xp.exchange(a, b, turns=10, seed_history=SEED, history_window=1)
    assert b.seen[0] == (real_surfaces[0],), b.seen[0]
    assert a.seen[1] == (real_surfaces[0],), a.seen[1]
    assert b.seen[1] == (real_surfaces[1],), b.seen[1]


# ══ REFUSALS ═════════════════════════════════════════════════════════════
@pytest.mark.parametrize("bad", [0, -1])
def test_a_window_below_one_is_refused(bad):
    """A speaker provoked by nothing is a cold start, not a depth-1 painter."""
    with pytest.raises(ValueError, match="history_window must be >= 1"):
        xp.exchange(Spy(), Spy(), turns=2, seed_history=SEED, history_window=bad)


def test_the_cli_exposes_the_knob_and_defaults_to_ACCUMULATE():
    """⚠️ The default must be the MEASURED NULL, not the hypothesis. A default of
    1 would silently make every future run a locality run."""
    src = (pathlib.Path(__file__).parents[1] / "tools"
           / "act2_exchange_probe.py").read_text(encoding="utf-8")
    assert '"--history-window"' in src
    assert src.count("history_window=a.history_window") == 2, (
        "both the interacting arm AND the frozen-partner control must be "
        "truncated, or the control is not yoked")
