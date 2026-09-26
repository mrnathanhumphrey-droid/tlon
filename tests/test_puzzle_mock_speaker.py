"""⛔⛔ THE SKELETON'S SPEAKER — real shape, no model, and never a stranger's.

The mock exists so the page can be reacted to before anything is spent. That
makes it dangerous in exactly one way: what it emits is LEGAL TLÖN, so a mock
left switched on in production would answer every visitor plausibly and nothing
on the page would look wrong. The refusal to start in a deployed environment is
therefore the most important thing in this file.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from puzzle import mock_speaker as M                       # noqa: E402
from puzzle.speaker import SpeakerError                    # noqa: E402


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in M._DEPLOYED + ("TLON_MOCK_SPEAKER",):
        monkeypatch.delenv(k, raising=False)
    yield


# ── 1 · it must never serve a stranger ──────────────────────────────────────

def test_off_by_default():
    assert M.enabled() is False


def test_on_when_asked(monkeypatch):
    monkeypatch.setenv("TLON_MOCK_SPEAKER", "1")
    assert M.enabled() is True


@pytest.mark.parametrize("marker", M._DEPLOYED)
def test_REFUSES_on_a_deployed_environment(monkeypatch, marker):
    """⛔⛔ THE ONE THAT MATTERS. Not `return False` — a REFUSAL, naming the
    marker, so the process does not come up quietly serving fake Tlön."""
    monkeypatch.setenv("TLON_MOCK_SPEAKER", "1")
    monkeypatch.setenv(marker, "something")
    with pytest.raises(SpeakerError) as exc:
        M.enabled()
    assert marker in str(exc.value)


def test_a_deployed_marker_without_the_flag_is_fine(monkeypatch):
    """⛔ Non-vacuity: the guard must fire on the MOCK being on, not on being
    deployed. Otherwise it would block the real server."""
    monkeypatch.setenv("FLY_APP_NAME", "tlon")
    assert M.enabled() is False


# ── 2 · the shape is the real shape ─────────────────────────────────────────

@pytest.fixture
def spoke():
    s = M.MockSpeaker()
    return s, s.turn("I sat with the quiet for a while.", [], [])


def test_the_turn_has_the_speakers_contract(spoke):
    _, out = spoke
    assert set(out) == {"you", "tlon", "seconds", "shape", "context_turns"}
    assert set(out["you"]) >= {"english", "surface", "gloss", "literary",
                               "let_go", "refused", "seconds"}


def test_every_surface_it_emits_RE_PARSES(spoke):
    """⛔⛔ THE ROUND TRIP THE WHOLE PROJECT RESTS ON. A mock emitting
    placeholder text would leave `parse`, `gloss` and the translate button
    untested while the page looked finished."""
    from puzzle.speaker import translate
    s = M.MockSpeaker()
    for i in range(25):
        out = s.turn("line %d" % i, [], [])
        for key in ("you", "tlon"):
            row = out[key]
            if row and row.get("surface"):
                t = translate(row["surface"])      # raises if it will not parse
                assert t["gloss"] and t["literary"]


def test_a_refusal_is_an_OUTCOME_not_an_error():
    """⛔ The gate refuses real English too, and a skeleton that never refuses
    hides the refusal copy from review entirely."""
    s = M.MockSpeaker(refusal_rate=1.0)
    out = s.turn("anything", [], [])
    assert out["you"]["refused"]
    assert out["you"]["surface"] is None
    # ⛔ and NO reply: a provocation built from a refused line is not a turn
    assert out["tlon"] is None


def test_it_is_deterministic_for_a_seed():
    a = M.MockSpeaker(seed=5).turn("x", [], [])
    b = M.MockSpeaker(seed=5).turn("x", [], [])
    assert a["you"]["surface"] == b["you"]["surface"]
    assert a["tlon"]["surface"] == b["tlon"]["surface"]


# ── 3 · the crib density is v1's, not a wish ────────────────────────────────

def _carry_rate(speaker, n=400):
    from tlon.grammar import classes as C
    roots = frozenset(C.load()["classes"]["R"])
    def sr(surface):
        return frozenset(w for w in surface.split() if w in roots)
    seen = carried = 0
    for i in range(n):
        out = speaker.turn("line %d" % i, [], [])
        if not out["tlon"] or not out["you"].get("surface"):
            continue
        seen += 1
        a = sr(out["you"]["surface"])
        b = sr(out["tlon"]["surface"])
        carried += bool(a & b)
    return carried / seen if seen else 0.0


def test_the_mock_carries_at_v1s_MEASURED_rate():
    """⭐⭐ THE WHOLE VALUE OF THE SKELETON. The served adapter
    `force-s20624` carries 33.6% [28.1, 39.6] at n=256 (v1 `dosed-s20624` was
    27.5% [22.3, 33.2]). A mock that carried every turn would make the puzzle
    look solvable when it is not, and the first person to find out otherwise
    would be a stranger on the public URL.
    """
    rate = _carry_rate(M.MockSpeaker(seed=11))
    assert abs(rate - M.V1_CARRY_RATE) < 0.08, rate


def test_the_carry_dial_is_NOT_VACUOUS_at_either_end():
    """⛔ If the dial did nothing, the test above would pass on any mock."""
    assert _carry_rate(M.MockSpeaker(seed=3, carry_rate=1.0, refusal_rate=0.0),
                       n=120) > 0.85
    assert _carry_rate(M.MockSpeaker(seed=3, carry_rate=0.0, refusal_rate=0.0),
                       n=120) < 0.15


def test_the_rate_constant_matches_the_measured_number():
    """⛔ Pinned to the run that produced it: `act2_model_carry` 2026-09-26,
    battery 9b4d4e19b14244e5, **force-s20624 = 86/256**.

    ⛔⛤ Was `70/255` — v1 `dosed-s20624`, carrysweep 2026-09-23. This test is
    the reason the constant could not be left behind when the served cell moved:
    the rate is a property of the WEIGHTS, and a mock still generating v1's crib
    density under v2 would be a UI built against a puzzle that no longer exists.
    """
    assert M.V1_CARRY_RATE == pytest.approx(86 / 256, abs=0.005)
