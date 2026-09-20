"""⛔⛔ THE WINDOW MUST REACH THE MODEL, OR THERE IS NO PUZZLE.

A Tlönian sits down next to you on the bench. That moment and that interaction
ARE the context. If every reply is an unrelated scene then no root ever recurs,
and a reader has nothing to work with — the puzzle IS the language, and a
language is solvable only because it repeats.

⭐ SO THIS FILE ASSERTS THE PROMPT, NOT THE PLUMBING. `store.threads()` being
correct proves nothing if `/say` does not hand the result to the model, and
`speaker.turn()` accepting the pairs proves nothing if they never reach the
text the model is tokenized on. Every test below reads the STRING the backend
would generate from.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from puzzle.window import TLON, YOU, ConversationStore        # noqa: E402


class FakeTok:
    """A chat template that is trivially readable, so a test can assert the
    MESSAGE SEQUENCE rather than a vendor's formatting."""

    chat_template = "yes"

    def apply_chat_template(self, msgs, tokenize=False,
                            add_generation_prompt=False):
        out = "".join("<%s>%s</%s>" % (m["role"], m["content"], m["role"])
                      for m in msgs)
        return out + ("<assistant>" if add_generation_prompt else "")


def _backend():
    """A BenchBackend with no model behind it. ⛔ `LocalBackend.__init__` loads
    14 GB of weights, so the instance is built without it — `_prompt` touches
    nothing but `self.tok` and `self.conversation`."""
    from puzzle.speaker import _bench_backend_class

    cls = _bench_backend_class()
    b = cls.__new__(cls)
    b.tok = FakeTok()
    b.conversation = []
    return b


# ── the empty bench ─────────────────────────────────────────────────────────

def test_an_empty_bench_is_byte_identical_to_the_single_turn_path():
    """⛔⛔ THE FIRST TURN OF EVERY CONVERSATION GOES THROUGH THIS BRANCH.

    If it differed even by a newline, every opening turn would be read under a
    prompt no measurement in this project has ever used — and the difference
    would be invisible, permanent, and impossible to attribute later. The
    trainer/reader fold exists precisely because those two drifted apart once
    before on Mistral.
    """
    from tlon.act2.chat_shape import read_prompt

    b = _backend()
    b.conversation = []
    assert b._prompt("SYS", "USER") == read_prompt(b.tok, "SYS", "USER")


def test_an_empty_conversation_attribute_is_treated_as_empty():
    """⭐ None, missing and [] must all take the single-turn branch. A backend
    that had never been handed a bench would otherwise build a one-message
    prompt down the multi-turn path."""
    from tlon.act2.chat_shape import read_prompt

    b = _backend()
    expected = read_prompt(b.tok, "SYS", "USER")
    for value in ([], None):
        b.conversation = value
        assert b._prompt("SYS", "USER") == expected
    del b.conversation
    assert b._prompt("SYS", "USER") == expected


# ── the bench ───────────────────────────────────────────────────────────────

def test_prior_turns_arrive_as_alternating_chat_messages():
    """⛔ NOT A TRANSCRIPT FLATTENED INTO ONE USER MESSAGE. That is the `arena`
    shape, and no training row ever had it. Each message keeps the bare shape a
    corpus row contains; the alternation is what the instruct base expects."""
    b = _backend()
    b.conversation = [("mil prax ka", "sen fes kä"),
                      ("hul nix ka", "krin tan ki")]
    got = b._prompt("SYS", "hren u ka")
    assert got == (
        "<system>SYS</system>"
        "<user>mil prax ka</user><assistant>sen fes kä</assistant>"
        "<user>hul nix ka</user><assistant>krin tan ki</assistant>"
        "<user>hren u ka</user>"
        "<assistant>")


def test_the_live_payload_is_the_last_user_message_and_is_bare():
    """⭐ The thing being answered must sit last and unadorned — that is the
    byte-for-byte shape of a training row's user message."""
    b = _backend()
    b.conversation = [("a", "b")]
    got = b._prompt("SYS", "PAYLOAD")
    assert got.endswith("<user>PAYLOAD</user><assistant>")


def test_there_is_exactly_one_system_message():
    """⛔ A chat template carries ONE system message, which is why the bench is
    split into two direction-homogeneous threads. If both directions were mixed
    into one thread, half the exchanges would sit under a framing that does not
    govern them."""
    b = _backend()
    b.conversation = [("a", "b"), ("c", "d")]
    assert b._prompt("SYS", "x").count("<system>") == 1


# ── the shape of a prior exchange ───────────────────────────────────────────

def test_a_prior_assistant_turn_is_a_json_scene_not_a_bare_surface():
    """⛔⛔ THE BUG THIS FILE EXISTS FOR, AND IT COULD NOT SHOW UP ON TURN ONE.

    The first bench put bare Tlön surfaces in the assistant slots. Turn one was
    fine — an empty bench never takes that branch — and every turn after it
    failed in under a second with no JSON object in the generation: shown
    "assistant" turns that were plain text, the model stopped producing the
    object the gate parses. A defect invisible until the second message is one
    that reaches a stranger on a public URL, not a developer.

    ⭐ The assertion is against the TRAINER'S OWN serialisation, obtained the
    same way the trainer obtains it.
    """
    import json

    from act2_finetune import row_messages
    from tlon.act2 import schema_bridge as SB
    from tlon.grammar.parse import parse

    from puzzle.speaker import trained_pair

    surface = "mil pläng prax ka"
    user, assistant = trained_pair("write", "I burnt the toast.", surface)

    assert user == "I burnt the toast.", "the user payload stays bare"
    decoded = json.loads(assistant)          # ⛔ raises if it is not JSON
    assert decoded == SB.scene_to_proposal(parse(surface))

    expected = row_messages({"direction": "write",
                             "prompt": "I burnt the toast.",
                             "scene": SB.scene_to_proposal(parse(surface))})
    assert assistant == expected[2]["content"], (
        "⛔⛔ the bench's assistant turn drifted from the trainer's")


def test_a_provoke_pair_keeps_the_bare_surface_as_the_user_payload():
    """⛔ Every provoke row in the corpus is `prompt = prev.surface` — one bare
    Tlön line. The user half must stay exactly that."""
    import json

    from puzzle.speaker import trained_pair

    # ⭐ Both surfaces are REAL generations from a live bench, not invented.
    # An invented one failed to parse here, which is the gate doing its job —
    # but a test fixture that is not a legal utterance tests the fixture.
    user, assistant = trained_pair("provoke", "pral lang säx ka",
                                   "lang fro säx krun ka")
    assert user == "pral lang säx ka"
    json.loads(assistant)


# ── the two threads ─────────────────────────────────────────────────────────

@pytest.fixture()
def store(tmp_path):
    return ConversationStore(tmp_path / "bench.sqlite3")


def _bench(store, n):
    cid = store.new_conversation()
    for t in range(n):
        store.append(cid, t, YOU, english="english %d" % t,
                     surface="you%d" % t)
        store.append(cid, t, TLON, surface="it%d" % t)
    return cid


def test_the_threads_are_homogeneous_in_direction(store):
    cid = _bench(store, 3)
    write, provoke = store.threads(cid)
    assert write == [("english 0", "you0"), ("english 1", "you1"),
                     ("english 2", "you2")]
    assert provoke == [("you0", "it0"), ("you1", "it1"), ("you2", "it2")]


def test_an_incomplete_turn_is_dropped_from_both_threads(store):
    """⛔ A pair with no assistant half enters the prompt as a question the
    model never answered, and its next move is to notice the gap rather than
    continue the bench."""
    cid = store.new_conversation()
    store.append(cid, 0, YOU, english="e0", surface="you0")
    store.append(cid, 0, TLON, surface="it0")
    store.append(cid, 1, YOU, english="e1", surface="you1")   # no reply row
    store.append(cid, 2, YOU, english="e2", surface=None,
                 refused="gate refused")                      # refused
    store.append(cid, 2, TLON, surface="it2")
    write, provoke = store.threads(cid)
    assert provoke == [("you0", "it0")]
    assert write == [("e0", "you0"), ("e1", "you1")]


def test_the_context_timeout_bounds_how_far_back_the_model_sees(store):
    """⭐ The time-out, in turns. Too few and convention never forms; too many
    and the oldest exchanges dominate a prompt that keeps growing."""
    cid = _bench(store, 12)
    _write, provoke = store.threads(cid, max_turns=4)
    assert len(provoke) == 4
    assert provoke[-1] == ("you11", "it11")
    assert provoke[0] == ("you8", "it8")


def test_a_cold_bench_reports_its_idle_time(store):
    import time as _t

    cid = _bench(store, 1)
    idle = store.idle_seconds(cid)
    assert idle is not None and idle < 5
    assert store.idle_seconds("nope") is None
    del _t


# ── the wiring ──────────────────────────────────────────────────────────────

def test_say_hands_the_window_to_the_speaker(tmp_path, monkeypatch):
    """⛔⛔ THE CALLER, NOT THE HELPER. Every instrument bug in this project's
    2026-09-16 arc had the same shape: the helper was exercised and the
    pipeline shipped the caller. `threads()` being right is worth nothing if
    `/say` keeps passing a flat surface list."""
    monkeypatch.setenv("TLON_PRELOAD", "0")
    monkeypatch.setenv("TLON_HTTPS", "0")
    monkeypatch.setenv("TLON_DB", str(tmp_path / "bench.sqlite3"))
    for mod in [m for m in list(sys.modules) if m.startswith("puzzle")]:
        del sys.modules[mod]

    from fastapi.testclient import TestClient

    from puzzle import server

    seen = []

    def fake_turn(english, write_pairs, provoke_pairs):
        seen.append((english, list(write_pairs), list(provoke_pairs)))
        n = len(seen)
        return {"you": {"english": english, "surface": "you%d" % n,
                        "gloss": "g", "literary": "l", "let_go": [],
                        "refused": None, "seconds": 0.1},
                "tlon": {"english": None, "surface": "it%d" % n,
                         "gloss": "g", "literary": "l", "let_go": [],
                         "refused": None, "seconds": 0.1},
                "seconds": 0.2, "shape": "trained", "context_turns": n - 1}

    monkeypatch.setattr(server.speaker, "turn", fake_turn)
    c = TestClient(server.app)

    c.post("/say", json={"english": "first"})
    c.post("/say", json={"english": "second"})
    c.post("/say", json={"english": "third"})

    assert seen[0][2] == [], "the first turn has no bench yet"
    assert seen[1][2] == [("you1", "it1")], (
        "⛔⛔ the second turn did not receive the first exchange — the model is "
        "answering with no context and nothing will ever recur")
    assert seen[2][2] == [("you1", "it1"), ("you2", "it2")]
    assert seen[2][1] == [("first", "you1"), ("second", "you2")]
