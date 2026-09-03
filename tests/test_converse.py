"""⛔⛔ RED-PROOF FOR THE CONVERSANT'S PROMPT SHAPES.

`tools/tlon_converse.py` is the first thing that puts the fine-tune in front of
a human, and the only way it can be silently wrong is by prompting under a shape
the model was never trained on. That is not hypothetical: run 3 was trained on
write/read and prompted at arena time under `CONVERSE`, a string in another
module that had never been a training direction, and **27/27 green said nothing
because no test crossed the boundary**. `tlon/discourse/provocation.py` exists
because of it.

⭐ SO THESE TESTS CROSS THE BOUNDARY. They assert against the TRAINER's own
constants and the CORPUS BUILDER's own row shape -- not against a re-spelling of
either. If the trainer moves, these fail.

⛔⛔ AND THE DIVERGENCE THEY PIN. `provocation.py` fixed the SYSTEM string and
left the USER message alone. Every corpus row's user message is a BARE string;
`LLMSpeaker` wraps all three directions in `"The conversation so far: ..."`. That
is the same defect one level down from where it was fixed, and it is now a test
rather than a note.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

from act2_finetune import SYSTEM as TRAINED_SYSTEM, row_messages  # noqa: E402
from tlon.act2.llm import ScriptedBackend                         # noqa: E402
from tlon.discourse.provocation import DIRECTION as PROVOKE       # noqa: E402
from tlon_converse import (ARENA, TRAINED, WRITE, exchange,       # noqa: E402
                           generate, user_message)

#: A legal Scene, in the PROPOSAL schema the gate accepts.
SCENE = {"node": {"root": "klung", "orient": ["nar"], "aspect_root": "tes",
                  "aspect_reps": 2,
                  "edges": [{"relator": "sen", "node": {"root": "lan"}}]},
         "force": "ka"}
OTHER = {"node": {"root": "flux"}, "force": "ki"}


# ── 1 · the trained shape is what the corpus actually contains ──────────────

def test_the_trained_user_message_is_the_BARE_payload():
    """⛔⛔ THE WHOLE CONTRACT. `row_messages` puts `row["prompt"]` in the user
    slot with nothing around it. Any preamble here is a shape the model has
    never served under."""
    assert user_message(WRITE, "my rent went up", [], shape=TRAINED) == \
        "my rent went up"
    assert user_message(PROVOKE, "pral sen lan ka", [], shape=TRAINED) == \
        "pral sen lan ka"


def test_the_trained_shape_MATCHES_THE_TRAINERS_OWN_FOLD():
    """⛔⛔ CROSSES THE BOUNDARY THAT WAS NEVER CROSSED. Asserted against
    `act2_finetune.row_messages` itself, so a change to the trainer's fold
    fails here instead of silently making the arena off-distribution."""
    for direction, payload in ((WRITE, "the bread was warm"),
                               (PROVOKE, "pral sen lan ka")):
        row = {"direction": direction, "prompt": payload, "scene": SCENE}
        msgs = row_messages(row)
        assert msgs[1]["role"] == "user"
        assert user_message(direction, payload, [], shape=TRAINED) == \
            msgs[1]["content"]
        assert msgs[0]["content"] == TRAINED_SYSTEM[direction]


def test_history_CANNOT_leak_into_the_trained_shape():
    """⭐ The trained provoke row is depth-1 Markov: one surface in, one scene
    out. A history that reached the prompt would be a different direction."""
    long_history = ["a" * 50, "b" * 50, "c" * 50]
    assert user_message(PROVOKE, "pral ka", long_history, shape=TRAINED) == \
        "pral ka"


# ── 2 · the arena shape is DIFFERENT, or the comparison is vacuous ──────────

def test_the_two_shapes_ACTUALLY_DIFFER():
    """⛔ Non-vacuity. If these were equal the tool's whole comparison would be
    two names for one experiment, and a null would mean nothing."""
    t = user_message(PROVOKE, "pral ka", ["lan ki"], shape=TRAINED)
    a = user_message(PROVOKE, "pral ka", ["lan ki"], shape=ARENA)
    assert t != a
    assert "The conversation so far" in a and "The conversation so far" not in t


def test_the_arena_shape_reproduces_LLMSpeaker_not_an_approximation_of_it():
    """⛔ It must be the real scaffolding, or `--shape arena` measures a third
    thing that is neither trained nor what the arena runs."""
    from tlon.act2.llm import transcript_block
    hist = ["lan ki", "pral ka"]
    got = user_message(PROVOKE, "ignored", hist, shape=ARENA)
    want = (f"The conversation so far:\n{transcript_block(hist, 60)}"
            f"\n\nSay the next thing.")
    assert got == want


def test_an_UNKNOWN_shape_RAISES_rather_than_defaulting():
    """⛔⛔ An unrecognised value silently taking the trained branch would
    report an arena run as a trained one -- the `visible_history` lesson."""
    with pytest.raises(ValueError, match="unknown shape"):
        user_message(WRITE, "x", [], shape="loose")


# ── 3 · ⛔⛔ THE PROVOCATION IS THE SURFACE, NEVER THE ENGLISH ──────────────

def test_the_provoke_step_is_handed_the_TLON_SURFACE_not_the_english():
    """⛔⛔ THE DEFECT THIS TOOL EXISTS TO AVOID. Every provoke row in the
    corpus is `prev.surface` (`act2_build_multiturn.py:54`). Handing it the
    user's English would be a direction the model has never served under, and
    it would look like it worked."""
    back = ScriptedBackend([SCENE, OTHER])
    english = "my landlord raised the rent again"
    yours, reply = exchange(back, english, [], shape=TRAINED)
    assert yours.ok and reply.ok
    write_call, provoke_call = back.calls
    assert write_call["kind"] == WRITE and write_call["user"] == english
    assert provoke_call["kind"] == PROVOKE
    assert provoke_call["user"] == yours.surface
    assert english not in provoke_call["user"]


def test_each_step_carries_ITS_OWN_trained_system_prompt():
    back = ScriptedBackend([SCENE, OTHER])
    exchange(back, "the bread was warm", [], shape=TRAINED)
    assert back.calls[0]["system"] == TRAINED_SYSTEM[WRITE]
    assert back.calls[1]["system"] == TRAINED_SYSTEM[PROVOKE]


def test_NO_LEXICON_CARD_reaches_either_prompt():
    """⛔⛔ `card` IS THE SUCCESS CRITERION, NOT A SETTING. The bar is cardless
    emission; a 233-form table in context measures a card-reader and reports it
    as a native speaker."""
    back = ScriptedBackend([SCENE, OTHER])
    exchange(back, "it rained", [], shape=TRAINED)
    for call in back.calls:
        assert "LEXICON" not in call["system"]
        assert "ROOTS (" not in call["system"]


# ── 4 · refusals are outcomes, and they keep their evidence ────────────────

def test_a_refused_first_step_does_NOT_invent_a_provocation():
    """⛔ A provocation built from a line the gate rejected would put the model
    in front of input the corpus never had. `reply` is None, and the session
    records the refusal instead."""
    back = ScriptedBackend([{"node": {"root": "NOT_A_ROOT"}, "force": "ka"}])
    yours, reply = exchange(back, "unrenderable", [], shape=TRAINED)
    assert not yours.ok and reply is None
    assert len(back.calls) == 1, "the provoke step must not have run"


def test_a_gate_refusal_KEEPS_the_proposal_it_refused():
    """⛔⛔ Run 4 lost its largest result to `proposal: null` with no text. A
    failure is the most information-dense event in a run."""
    bad = {"node": {"root": "NOT_A_ROOT"}, "force": "ka"}
    t = generate(ScriptedBackend([bad]), WRITE, "x", [], shape=TRAINED)
    assert not t.ok and t.raw and "NOT_A_ROOT" in t.raw
    assert "gate refused" in t.error


def test_a_backend_failure_keeps_its_RAW_generation_in_full():
    from tlon.act2.llm import BackendError

    class Broken:
        name = "broken"

        def call(self, **_kw):
            raise BackendError("no JSON object", raw="x" * 5000, kind=WRITE)

        def cost_report(self):
            return {}

    t = generate(Broken(), WRITE, "x", [], shape=TRAINED)
    assert not t.ok and t.raw is not None
    assert len(t.raw) == 5000, "the raw generation was truncated"


# ── 5 · the row a session writes is complete enough to read afterwards ─────

def test_a_successful_turn_records_surface_gloss_and_literary():
    """⭐ The transcript is the deliverable. A row without the gloss cannot be
    read by a human later, which is the entire question being asked."""
    back = ScriptedBackend([SCENE, OTHER])
    _yours, reply = exchange(back, "it rained", [], shape=TRAINED)
    row = reply.as_row()
    assert row["surface"] and row["gloss"] and row["literary"]
    assert row["shape"] == TRAINED and row["direction"] == PROVOKE
    assert row["seconds"] >= 0.0


def test_the_recorded_shape_is_the_shape_that_RAN():
    """⛔ A transcript that mislabels its own shape is worse than none — the
    two arms of the comparison become unreadable."""
    for shape in (TRAINED, ARENA):
        back = ScriptedBackend([SCENE, OTHER])
        yours, reply = exchange(back, "it rained", [], shape=shape)
        assert yours.as_row()["shape"] == shape
        assert reply.as_row()["shape"] == shape
