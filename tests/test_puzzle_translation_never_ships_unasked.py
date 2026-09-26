"""⛔⛔ THE PUZZLE'S ONE LOAD-BEARING INVARIANT.

The whole mechanic is that pressing translate is a CHOICE. If the gloss rides
along with the reply, it sits in the network tab and in the page source of every
reader who never pressed it, and the button becomes decoration. That failure is
invisible from the screen — the page looks identical either way — so it can only
be caught here.

⭐ AND IT IS TESTED AT THE ENDPOINT, NOT AT THE HELPER. The five instrument bugs
of 2026-09-16 all had the same shape: a test exercised the helper and the
pipeline shipped the caller. `_public()` being correct proves nothing if `/say`
stops calling it, so every assertion below goes through the real route.
"""
from __future__ import annotations

import os
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

#: ⛔⛔⛔ THE LIST WAS THE WRONG SHAPE AND THE LEAK WALKED PAST IT FOR MONTHS.
#:
#: This used to be a flat set of forbidden KEYS, with `english` on it, and every
#: assertion below asked "does the payload contain English?". Meanwhile
#: `_public()` returned `surface` for BOTH roles — and the surface of the
#: READER'S OWN TURN is their sentence rendered into Tlön. They typed the
#: English. They were shown the Tlön. **That is an aligned pair on every single
#: turn**, and not one test here could see it, because the leaking field was
#: called `surface` and looked like Tlön rather than like a translation.
#:
#: ⭐⭐ A LEAK TEST ENUMERATES WHAT THE AUTHOR ALREADY THINKS IS SECRET, SO IT IS
#: BLIND TO ANYTHING THE AUTHOR CHOSE TO EXPOSE. That lesson was already written
#: in this very file, about `english`. It was then reproduced one field over.
#:
#: ⭐ THE INVARIANT IS ABOUT PAIRING, NOT ABOUT ENGLISH. Returning readers their
#: own sentence tells them nothing they did not type; what must never happen is
#: a row carrying BOTH an English line and its Tlön:
#:     role "you"  -> `english`, and NEVER `surface`
#:     role "tlon" -> `surface`, and NEVER `english`
#: `gloss`, `literary` and `let_go` remain forbidden outright — those are the
#: translation proper, and the translate button is the only thing that hands
#: them over.
ALWAYS_FORBIDDEN = ("gloss", "literary", "let_go")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """The real app, with the model replaced and nothing else."""
    monkeypatch.setenv("TLON_PRELOAD", "0")
    monkeypatch.setenv("TLON_HTTPS", "0")
    monkeypatch.setenv("TLON_DB", str(tmp_path / "bench.sqlite3"))
    for mod in [m for m in list(sys.modules) if m.startswith("puzzle")]:
        del sys.modules[mod]

    from fastapi.testclient import TestClient

    from puzzle import server

    def fake_turn(english, write_pairs, provoke_pairs, force=None):
        # ⛔ The fake returns gloss and literary EXACTLY as the real speaker
        # does. A stub that omitted them would make this test pass by having
        # nothing to leak — the mutant that rubber-stamps itself.
        return {
            "you": {"english": english, "surface": "mil pläng prax ka",
                    "gloss": "while ⟨it closes⟩, it points.",
                    "literary": "While a closing, it points.",
                    "let_go": ["toast"], "refused": None, "seconds": 0.1},
            "tlon": {"english": None, "surface": "sen sir hlin pläng tlux fäm kä",
                     "gloss": "at ⟨between⟩, it drains (denied)",
                     "literary": "At a dappling — it drains — and it is denied.",
                     "let_go": [], "refused": None, "seconds": 0.1},
            "seconds": 0.2, "shape": "trained"}

    monkeypatch.setattr(server.speaker, "turn", fake_turn)
    monkeypatch.setattr(type(server.speaker), "ready",
                        property(lambda self: True))
    return TestClient(server.app)


def _leaks(blob, keys=ALWAYS_FORBIDDEN) -> list[str]:
    """Every place a forbidden key appears, at any depth."""
    found = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in keys:
                    found.append("%s.%s" % (path, k))
                walk(v, "%s.%s" % (path, k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, "%s[%d]" % (path, i))

    walk(blob, "$")
    return found


def test_say_does_not_return_the_translation(client):
    r = client.post("/say", json={"english": "I burnt the toast."})
    assert r.status_code == 200, r.text
    assert _leaks(r.json()) == [], (
        "⛔⛔ /say shipped the translation unasked — the puzzle is solved in "
        "the payload before the reader chooses")


def test_the_raw_body_does_not_contain_the_gloss_text(client):
    """⭐ A SECOND INSTRUMENT, FAILING BY A DIFFERENT PATH. The key-walk above
    would miss a gloss smuggled under a differently-named field; this reads the
    bytes on the wire for the text itself. Two checks that can fail
    independently, which is the only kind of corroboration worth having."""
    r = client.post("/say", json={"english": "I burnt the toast."})
    body = r.content.decode("utf-8")
    assert "While a closing" not in body
    assert "it drains" not in body
    # ⛔⛤ THIS USED TO ALSO ASSERT THE READER'S OWN SENTENCE NEVER CAME BACK,
    # AND THAT WAS GUARDING THE WRONG THING. The sentence is theirs — they
    # typed it — so returning it teaches them nothing. What was actually
    # leaking, past this very assertion, was `mil pläng prax ka`: THEIR LINE
    # RENDERED INTO TLÖN, in their own bubble, every turn. The aligned pair was
    # being assembled out of the field called `surface`, which nobody was
    # watching because it looked like Tlön.
    # ⭐ So the byte-level check is now for the TLÖN OF THE READER'S TURN.
    assert "mil pläng prax ka" not in body, (
        "⛔⛔⛔ the reader's own line came back rendered into Tlön — they typed "
        "the English, so that is a free aligned pair on every single turn")


def test_no_row_ever_carries_both_a_line_and_its_translation(client):
    """⛔⛔⛔ THE INVARIANT, STATED IN THE SHAPE THAT CAN ACTUALLY FAIL.

    Every earlier guard asked "is English present?" — a question about a field
    name. The leak was never a field name: it was PAIRING. A row that carries a
    reader's English AND the Tlön it became is an answer key, and after a
    handful of turns it is a dictionary.

    ⭐ Checked over both doors and over every row, because a rule enforced at
    one endpoint is not a rule."""
    client.post("/say", json={"english": "I burnt the toast."})
    for where, blob in (("/say", client.post(
                            "/say", json={"english": "The kettle is loud."}).json()),
                        ("/conversation", client.get("/conversation").json())):
        for row in blob["messages"]:
            has_en = bool(row.get("english"))
            has_tlon = bool(row.get("surface"))
            assert not (has_en and has_tlon), (
                "⛔⛔⛔ %s returned a row holding BOTH an English line and its "
                "Tlön — that is the parallel text: %r" % (where, row))
            if row["role"] == "you":
                assert "surface" not in row, (
                    "⛔⛔⛔ %s sent the Tlön of the READER'S OWN LINE. They "
                    "typed the English; this hands them the other half: %r"
                    % (where, row))
            else:
                assert "english" not in row, (
                    "⛔⛔ %s attached English to a Tlönian line: %r"
                    % (where, row))


def test_conversation_replay_does_not_return_the_translation(client):
    """⛔ THE SECOND DOOR. A reader who reloads gets their bench back from
    /conversation — if THAT route forgot to strip, the leak returns on every
    refresh and /say would still look clean."""
    client.post("/say", json={"english": "I burnt the toast."})
    r = client.get("/conversation")
    assert r.status_code == 200
    assert _leaks(r.json()) == [], "⛔⛔ /conversation shipped the translation"


def test_reveal_is_what_hands_it_over(client):
    """The button must actually work — a leak-free app that cannot translate
    passes every assertion above and is broken."""
    said = client.post("/say", json={"english": "I burnt the toast."}).json()
    row = [m for m in said["messages"] if m["role"] == "tlon"][0]
    r = client.post("/reveal", json={"turn": row["turn"], "role": "tlon"})
    assert r.status_code == 200, r.text
    assert r.json()["literary"]
    assert r.json()["gloss"]


def test_reveal_refuses_to_translate_the_user(client):
    """⛔⛔ WE NEVER TRANSLATE THE USER. They wrote the line; handing back its
    English makes an aligned English/Tlön pair, which is the parallel-text leak
    arriving by request instead of by accident.

    ⭐ ASSERTED AT THE ENDPOINT, NOT AT THE BUTTON. app.js only draws the
    button on the Tlönian's lines, but a UI-only rule is one fetch away from
    being no rule at all — and the reader of a puzzle is exactly the person
    curious enough to open the console.
    """
    said = client.post("/say", json={"english": "I burnt the toast."}).json()
    row = [m for m in said["messages"] if m["role"] == "you"][0]
    r = client.post("/reveal", json={"turn": row["turn"], "role": "you"})
    assert r.status_code == 422, (
        "⛔⛔ /reveal translated the reader's own line — status %s, body %s"
        % (r.status_code, r.text))
    assert "I burnt the toast" not in r.content.decode("utf-8")


def test_reveal_refuses_a_line_from_another_bench(client, tmp_path):
    """⛔ /reveal reads from the caller's OWN conversation. Without a cookie
    there is no bench, and it must not fall through to some other reader's."""
    client.post("/say", json={"english": "I burnt the toast."})
    client.cookies.clear()
    r = client.post("/reveal", json={"turn": 0, "role": "tlon"})
    assert r.status_code == 404
