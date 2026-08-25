"""THE COMPREHENSION READING THAT WAS THROWN AWAY. $0.00, offline.

⛔⛔ MEASURED, NOT HYPOTHETICAL. The 7B baseline read `choose 0.0 % (0/64), 64
unanswered`. Chance on a 4-way forced choice is 25 %, so 0 % is BELOW chance --
and the raw generations showed the model answering `[0]`, `[1]`, `[0]`, `[1]`.
It obeyed the CHOOSE prompt, which said "answer with the index" and -- unlike
CONVERSE and RENDER -- never asked for JSON. `LocalBackend` demanded a JSON
object, found none, and scored every answer as NO_ANSWER.

⛔ THE HOSTED PRE-FLIGHT COULD NOT HAVE CAUGHT IT. Tool use forced the schema
there, so comprehension read 16/16 and the missing sentence was invisible. One
prompt, two backends, and only one of them could express the defect.

⛔ AND IT MADE A LOCKED GATE UNREACHABLE. AMENDMENT A bands comprehension at
0.35-0.95; while the harness could only ever read 0.0, "clear" was unreachable
by construction -- a falsifier that cannot fire.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

import act2_backends as B                                        # noqa: E402
import act2_flocal as F                                          # noqa: E402
from tlon.act2.llm import CHOOSE, BackendError                   # noqa: E402


# ══ 1. THE PROMPT NOW STATES ITS FORMAT ══════════════════════════════════
def test_the_CHOOSE_prompt_asks_for_the_format_it_is_parsed_for():
    """⛔ THE ROOT CAUSE. Every prompt whose reply is parsed as JSON must say so;
    this one asked for "the index" and was parsed for an object."""
    assert '{"choice"' in CHOOSE
    assert "Emit ONLY the JSON object" in CHOOSE


def test_every_json_parsed_prompt_states_the_format():
    """The general form of the bug, so a fourth prompt cannot reintroduce it."""
    from tlon.act2 import llm
    for name in ("CONVERSE", "RENDER", "CHOOSE"):
        assert "JSON" in getattr(llm, name), name


# ══ 2. THE ANSWER THE MODEL ACTUALLY GAVE IS READ ════════════════════════
@pytest.mark.parametrize("raw,want", [
    ("[0]", 0), ("[1]", 1), ("2", 2), (" [3] ", 3), ("3.", 3), ("1)", 1),
    ("\n[2]\n", 2)])
def test_a_bare_index_is_read_as_the_answer_it_is(raw, want):
    """⭐ THE FOUR MEASURED REPLIES ARE IN HERE (`[0]`, `[1]`). Reading the answer
    the model gave is a repair to the instrument, not a loosening of the bar."""
    assert B._bare_index(raw, "choose") == want


@pytest.mark.parametrize("raw", [
    "I think [2] is right",
    "between [1] and [3]",
    "The correct reading is index 2 because it preserves the aspect.",
    "none of these",
    "",
    "  ",
    "[1] [2]",
    "it thuds",
    "choice: 2 (but [3] is close)"])
def test_prose_is_STILL_REFUSED_so_the_parser_cannot_launder_a_score(raw):
    """⛔⛔ THE DIRECTION THAT MATTERS. A tolerant parser here would manufacture
    comprehension out of hedging and inflate the exact number AMENDMENT A gates
    on. The whole generation must BE the answer, anchored at both ends."""
    with pytest.raises(BackendError):
        B._bare_index(raw, "choose")


def test_the_fallback_is_CHOOSE_ONLY_and_cannot_rescue_a_scene():
    """⛔ A Scene is a structured object; an index could never be one. If the
    fallback ever applied to speak/render it would turn a failed emission into a
    parse success and F-LOCAL would read high for the wrong reason."""
    import inspect
    src = inspect.getsource(B.LocalBackend.call)
    assert 'kind == "choose"' in src, "the fallback must be gated on choose"


# ══ 3. THE VERDICT HAS A BRANCH FOR WHAT HAPPENED ════════════════════════
def test_the_measured_baseline_is_reported_as_UNSCOREABLE_not_as_a_floor():
    """⛔⛔ THE EXACT NUMBERS FROM THE RUN: 0.0 %, 64/64 unanswered. The old
    verdict called this "indistinguishable from guessing" — a claim about the
    model, when the truth was a claim about the harness."""
    v = F.comprehension_verdict(0.0, 64, 64, 0.25)
    assert "UNSCOREABLE" in v and "64/64" in v
    assert "guessing" not in v


def test_below_chance_with_answers_given_still_points_at_the_harness():
    """Answered but worse than a coin: not a comprehension floor either."""
    v = F.comprehension_verdict(0.05, 0, 64, 0.25)
    assert "BELOW CHANCE" in v


@pytest.mark.parametrize("acc,unans,expect", [
    (0.00, 64, "UNSCOREABLE"),      # the measured baseline
    (0.98, 0, "CEILING"),           # the hosted pre-flight's failure mode
    (0.30, 0, "FLOOR"),
    (0.60, 0, "clear"),
    (0.60, 20, "UNSCOREABLE"),      # a third mute ⇒ the band does not apply
    (0.60, 5, "clear")])            # a few refusals is still a reading
def test_every_outcome_has_its_own_branch(acc, unans, expect):
    """⭐ WRITE THE LOUD FALLBACK FIRST, THEN ENUMERATE. Each row is an outcome
    the run can actually produce; the muted one is the row that was missing."""
    assert expect in F.comprehension_verdict(acc, unans, 64, 0.25)


def test_the_band_still_matches_the_LOCKED_amendment():
    """⛔ The fix adds branches; it must not move the locked band."""
    assert F.BAND == (0.35, 0.95)
