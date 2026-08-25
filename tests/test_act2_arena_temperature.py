"""HARDEN 3 — THE ARENA TEMPERATURE FLOOR, RED-PROOFED AT BOTH ENDS. $0, offline.

⛔⛔ GREEDY DECODING MAKES DRIFT IMPOSSIBLE BY CONSTRUCTION, AND THE FAILURE LOOKS
LIKE THE MOST HONEST RESULT AVAILABLE. Two deterministic speakers each emit
exactly one continuation for a given history: they can be identical or not, but
there is no distribution for a convention to move within. A drift run at
temperature 0 therefore returns **a clean null** — ΔD ≈ 0, ΔC ≈ 0, no pact —
which is **indistinguishable from the pre-registered BOUNDARY FINDING**.

⭐ That is why this is a structural refusal and not a note in a runbook: the
artefact and the discovery are the same number, and a null that came from the
sampler would be written up as a result.

Measured, and the reason the floor exists at all: the same prompt read **1/12**
distinct at temperature 0 and **11/12** at temperature 0.8.

⛔ THE TEMPERATURE NUMBER ALONE IS NOT ENOUGH, which is the half that is easy to
miss — a correctly-configured temperature on a degenerate speaker still cannot
drift. So the guard also measures actual variability.
"""
from __future__ import annotations

import pytest

from tlon.act2 import falsify as F

SCENE = {"node": {"root": "klung"}, "force": "ka"}


def _same(n):     return [dict(SCENE) for _ in range(n)]
def _varied(n):   return [{"node": {"root": f"r{i}"}, "force": "ka"} for i in range(n)]


# ══ END 1 — THE COLD END REFUSES ═════════════════════════════════════════
@pytest.mark.parametrize("temp", [0.0, 0.1, 0.3, 0.5, 0.69])
def test_below_the_floor_RAISES_rather_than_returning_a_null(temp):
    """⛔⛔ THE WHOLE POINT. It must RAISE. Returning "no drift" here would be
    reporting the sampler's determinism as a finding about language."""
    with pytest.raises(F.VacuousFalsifier, match="below the pre-registered floor"):
        F.arena_preconditions(temperature=temp)


def test_the_refusal_SAYS_the_null_would_be_indistinguishable_from_the_finding():
    """The message has to carry the reason, or the next person raises the floor
    to make the error go away."""
    with pytest.raises(F.VacuousFalsifier) as e:
        F.arena_preconditions(temperature=0.0)
    msg = str(e.value)
    assert "VACUOUS" in msg and "boundary finding" in msg


def test_an_UNRECORDED_temperature_is_refused_too():
    """⛔ A parameter that was never written down cannot be checked, and "we
    probably used the default" is not a record."""
    with pytest.raises(F.VacuousFalsifier, match="pre-registered parameter"):
        F.arena_preconditions(temperature=None)


# ══ END 2 — THE WARM END PASSES, SO THE GUARD IS NOT MERELY A WALL ═══════
@pytest.mark.parametrize("temp", [0.7, 0.8, 1.0, 1.2])
def test_at_or_above_the_floor_the_measurement_is_ALLOWED(temp):
    """⛔⛔ THE OTHER END OF THE RED-PROOF. A guard that refuses everything is as
    useless as one that refuses nothing — and would quietly block the arena
    forever while looking rigorous."""
    F.arena_preconditions(temperature=temp)                 # must not raise


def test_a_VARYING_speaker_at_the_floor_passes_the_variability_check():
    F.arena_preconditions(temperature=0.8, same_history_samples=_varied(12))


# ══ THE HALF THE TEMPERATURE NUMBER WOULD HAVE MISSED ════════════════════
def test_a_DEGENERATE_speaker_is_refused_even_at_a_LEGAL_temperature():
    """⛔⛔ THE MEASURED FAILURE, GENERALISED. The `san`x12 collapse passed every
    setting-level check: the config was fine and the speaker still could not
    vary. A precondition that trusts the setting instead of measuring the
    behaviour would wave this straight through."""
    with pytest.raises(F.VacuousFalsifier, match="cannot vary"):
        F.arena_preconditions(temperature=0.9, same_history_samples=_same(12))


def test_the_degenerate_refusal_NAMES_the_setting_as_innocent():
    """So the reader fixes the speaker, not the temperature."""
    with pytest.raises(F.VacuousFalsifier) as e:
        F.arena_preconditions(temperature=0.9, same_history_samples=_same(12))
    assert "setting was right" in str(e.value)


def test_too_few_variability_samples_is_refused_not_assumed_fine():
    with pytest.raises(F.VacuousFalsifier, match="Too few"):
        F.arena_preconditions(temperature=0.8, same_history_samples=_same(3))


@pytest.mark.parametrize("distinct,ok", [(1, False), (2, False), (3, True), (12, True)])
def test_the_variability_threshold_is_exactly_where_it_says_it_is(distinct, ok):
    """⛔ An off-by-one in a refusal threshold silently changes what is
    measurable, so the boundary is pinned rather than described."""
    # exactly `distinct` unique continuations spread over 12 samples
    samples = [{"node": {"root": f"r{i % distinct}"}, "force": "ka"}
               for i in range(12)]
    assert len({s["node"]["root"] for s in samples}) == distinct
    if ok:
        F.arena_preconditions(temperature=0.8, same_history_samples=samples)
    else:
        with pytest.raises(F.VacuousFalsifier):
            F.arena_preconditions(temperature=0.8, same_history_samples=samples)


# ══ THE FLOOR IS A LOCKED PARAMETER ══════════════════════════════════════
def test_the_floor_is_declared_as_pre_registered_and_not_a_default():
    """⚠️ It is locked BEFORE the arena runs and must not be tuned after seeing
    arena results. If this constant ever moves, it should be a visible decision."""
    import inspect
    src = inspect.getsource(F)
    assert "MIN_ARENA_TEMPERATURE" in src
    assert "PRE-REGISTERED PARAMETER, NOT A KNOB" in src
    assert F.MIN_ARENA_TEMPERATURE > 0.0


def test_greedy_is_below_the_floor_by_construction():
    """The configuration that produced the original artefact must be excluded."""
    assert 0.0 < F.MIN_ARENA_TEMPERATURE
