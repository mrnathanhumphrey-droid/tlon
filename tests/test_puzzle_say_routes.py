"""⛔⛔ THE ROUTES, END TO END THROUGH `/say`.

`tests/test_puzzle_router.py` proves the DECISION. This proves the WIRING: that
the decision reaches the right half of the speaker, that the reader is shown
what they typed, that the route is written to the log, and that the aligned
pair is withheld on every route — including the two new ones that never call
the write step and so never went through the path `_public` was built for.

⛔ No model. `speaker.turn` and `speaker.speak_from` are both replaced, and the
test asserts WHICH ONE was called — the bug being fixed is a line reaching the
wrong door, so "it returned something" is not evidence.
"""
from __future__ import annotations

import pathlib
import sqlite3
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SECRET = "proxy-secret-for-tests"
READER_IP = "198.51.100.9"

#: A real reply from the production log — legal under the served lexicon.
REPLY = "hlim hlux les nang axas les ka"


@pytest.fixture(autouse=True)
def expanded_lexicon(monkeypatch):
    """⛔⛔ Set PER TEST, never at module import — see the same fixture in
    `test_puzzle_router.py` for why, and `classes.reset_caches` for why the env
    var alone would leave `form_class` classifying against the old language."""
    from tlon.grammar import classes as C
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.reset_caches()
    yield
    monkeypatch.undo()
    C.reset_caches()


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("TLON_PRELOAD", "0")
    monkeypatch.setenv("TLON_HTTPS", "0")
    monkeypatch.setenv("TLON_DB", str(tmp_path / "bench.sqlite3"))
    monkeypatch.setenv("TLON_TRUST_PROXY", "1")
    monkeypatch.setenv("TLON_PROXY_SECRET", SECRET)
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    monkeypatch.delenv("TURNSTILE_SECRET_KEY", raising=False)
    monkeypatch.delenv("TLON_ADMIN_TOKEN", raising=False)
    for mod in [m for m in list(sys.modules) if m.startswith("puzzle")]:
        del sys.modules[mod]

    from puzzle import server

    calls = []

    def fake_turn(english, write_pairs, provoke_pairs, force=None):
        calls.append(("turn", english, force))
        return {"you": {"english": english, "surface": "mil prax ka",
                        "gloss": "g", "literary": "l", "let_go": [],
                        "refused": None, "seconds": 0.1},
                "tlon": {"english": None, "surface": REPLY, "gloss": "g",
                         "literary": "l", "let_go": [], "refused": None,
                         "seconds": 0.1},
                "seconds": 0.2, "shape": "trained"}

    def fake_speak_from(surface, provoke_pairs, *, english):
        calls.append(("speak_from", surface, english))
        return {"you": {"english": english, "surface": surface, "gloss": "g",
                        "literary": "l", "let_go": [], "refused": None,
                        "seconds": 0.0},
                "tlon": {"english": None, "surface": REPLY, "gloss": "g",
                         "literary": "l", "let_go": [], "refused": None,
                         "seconds": 0.1},
                "seconds": 0.1, "shape": "trained"}

    monkeypatch.setattr(server.speaker, "turn", fake_turn)
    monkeypatch.setattr(server.speaker, "speak_from", fake_speak_from)
    monkeypatch.setattr(type(server.speaker), "ready", property(lambda s: True))
    server._calls = calls
    return server


def _client(server):
    from fastapi.testclient import TestClient
    return TestClient(server.app)


def signed() -> dict:
    return {"X-Tlon-Proxy-Secret": SECRET, "X-Tlon-Client-IP": READER_IP}


def _routes(server):
    con = sqlite3.connect(server.LOG_PATH)
    try:
        return [r[0] for r in con.execute(
            "SELECT route FROM turns ORDER BY id")]
    finally:
        con.close()


# ── (d) the ordinary path is untouched ─────────────────────────────────────

def test_plain_english_still_goes_to_the_write_step(app):
    c = _client(app)
    r = c.post("/say", json={"english": "what is happiness?"},
               headers=signed())
    assert r.status_code == 200
    assert app._calls == [("turn", "what is happiness?", None)]
    assert _routes(app) == ["english"]


# ── (c) the line that broke production ─────────────────────────────────────

def test_are_you_there_ka_reaches_the_write_step_stripped(app):
    """⛔ REFUSED THREE TIMES ON THE LIVE BENCH. The write model has never seen
    `ka` in its English; the router hands it the line that already worked."""
    c = _client(app)
    r = c.post("/say", json={"english": "Are you there ka"}, headers=signed())
    assert r.status_code == 200
    assert app._calls == [("turn", "Are you there", "ka")]
    assert _routes(app) == ["tagged"]


def test_the_reader_is_shown_what_they_typed_not_what_we_sent(app):
    """⛔ The bubble is the reader's own sentence. They never wrote the
    stripped string and must not be shown it back as theirs."""
    c = _client(app)
    r = c.post("/say", json={"english": "Are you there ka"}, headers=signed())
    you = [m for m in r.json()["messages"] if m["role"] == "you"][0]
    assert you["english"] == "Are you there ka"


# ── (a) a pasted surface ───────────────────────────────────────────────────

def test_a_pasted_reply_skips_the_write_step_entirely(app):
    c = _client(app)
    r = c.post("/say", json={"english": REPLY}, headers=signed())
    assert r.status_code == 200
    assert app._calls == [("speak_from", REPLY, REPLY)]
    assert _routes(app) == ["tlon"]


# ── (b) a bare force word ──────────────────────────────────────────────────

def test_a_bare_force_on_the_first_line_is_answered_truthfully(app):
    """⛔⛔ NOT "The language would not hold that". It holds it fine. There is
    simply nothing yet for the speech act to be aimed at, and saying otherwise
    is the bench blaming Tlön for its own plumbing."""
    c = _client(app)
    r = c.post("/say", json={"english": "ka"}, headers=signed())
    assert r.status_code == 400
    assert r.json()["error"] != app._REFUSAL_LANGUAGE
    assert r.json()["error"] == app._NOTHING_TO_ANSWER
    assert app._calls == [], "no model was asked, and none should have been"
    assert _routes(app) == ["nothing"]


def test_a_bare_force_after_a_reply_aims_at_that_reply(app):
    """`ki` means "is it so?" OF THE TLÖNIAN'S LAST LINE — same scene, new
    speech act."""
    from tlon.grammar.parse import parse
    c = _client(app)
    c.post("/say", json={"english": "tell me of the sky"}, headers=signed())
    app._calls.clear()
    r = c.post("/say", json={"english": "ki"}, headers=signed())
    assert r.status_code == 200
    assert len(app._calls) == 1 and app._calls[0][0] == "speak_from"
    sent = app._calls[0][1]
    assert parse(sent).force == "ki"
    assert parse(sent).node == parse(REPLY).node, "it answered a different line"
    assert _routes(app)[-1] == "force"


def test_the_reader_bubble_on_a_force_route_is_the_word_they_typed(app):
    c = _client(app)
    c.post("/say", json={"english": "tell me of the sky"}, headers=signed())
    r = c.post("/say", json={"english": "ki"}, headers=signed())
    you = [m for m in r.json()["messages"] if m["role"] == "you"][0]
    assert you["english"] == "ki"


# ── the withholding holds on every route ───────────────────────────────────

@pytest.mark.parametrize("line", ["what is happiness?", "Are you there ka",
                                  REPLY])
def test_no_route_ships_the_aligned_pair(app, line):
    """⛔⛔ THE PUZZLE'S ONE SECRET. `_public` strips the reader's own line
    rendered into Tlön. Two of these routes never pass through the write step,
    so they never took the path that guarantee was written for — this is what
    says it still holds."""
    c = _client(app)
    r = c.post("/say", json={"english": line}, headers=signed())
    assert r.status_code == 200
    for m in r.json()["messages"]:
        if m["role"] == "you":
            assert "gloss" not in m and "literary" not in m, (
                "the reader's own line came back translated — that is the "
                "answer key")


def test_english_carrying_a_root_is_recorded_apart(app):
    """⭐ Routed identically to plain English — roots are never stripped — but
    findable afterwards, because these are the rows a future write corpus
    needs."""
    from tlon.grammar import classes as C
    root = sorted(C.load()["classes"]["R"])[0]
    c = _client(app)
    r = c.post("/say", json={"english": "is %s a word" % root},
               headers=signed())
    assert r.status_code == 200
    assert app._calls[0][0] == "turn"
    assert _routes(app) == ["english.roots"]


# ── the migration ──────────────────────────────────────────────────────────

def test_the_route_column_is_added_to_a_database_that_predates_it(tmp_path):
    """⛔⛔ `CREATE TABLE IF NOT EXISTS` DOES NOTHING TO AN EXISTING TABLE. The
    production log is live and already holds turns; without the migration every
    insert naming `route` would fail there and nowhere else."""
    from puzzle import logbook as LB
    path = tmp_path / "old.sqlite3"
    con = sqlite3.connect(path)
    con.executescript(
        "CREATE TABLE turns (id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL "
        "NOT NULL, request_id TEXT, reader TEXT NOT NULL, ip_trusted INTEGER "
        "NOT NULL, conversation_id TEXT, turn INTEGER, english TEXT, surface "
        "TEXT, refused TEXT, seconds REAL, flags TEXT NOT NULL DEFAULT '', "
        "severity INTEGER NOT NULL DEFAULT 0);")
    con.execute("INSERT INTO turns (at, reader, ip_trusted, english) "
                "VALUES (1.0, 'r', 1, 'an older turn')")
    con.commit()
    con.close()

    book = LB.Logbook(path)
    book.record_turn(reader="r", ip_trusted=True, english="a newer turn",
                     route="tlon")
    assert book.failures == 0, book.last_failure

    con = sqlite3.connect(path)
    try:
        rows = list(con.execute(
            "SELECT english, route FROM turns ORDER BY id"))
    finally:
        con.close()
    assert rows == [("an older turn", ""), ("a newer turn", "tlon")], (
        "the pre-existing row must survive and default, not vanish")
