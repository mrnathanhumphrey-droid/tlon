"""⛔⛔ THE LOG IS EVERY READER'S BENCH AT ONCE. NOTHING MAY SERVE IT.

⛔⛤ AND THE FIRST VERSION OF THIS FILE OVERSTATED WHY, WHICH ITS OWN TEST CAUGHT.
I wrote that the log was the answer key. It is not: a turn row holds the reader's
English and the reply it DREW, which is the same two things `/conversation`
already shows that reader. The aligned pair is their own line rendered into Tlön,
and `logbook.py` deliberately keeps no copy of it.

⭐ THE REAL REASON IS THE AGGREGATE. All of it together is everybody's
conversation beside a stable pseudonymous id for each — a privacy artifact
outright, and in a puzzle whose difficulty is how much Tlön one person has seen,
a large shortcut. So the log has no route, the admin door only WRITES, and
reading happens offline after `modal volume get`.

⭐⭐ THE SPLIT IS THE SECURITY DESIGN. Banning has to be online: an ops manual
cannot say "redeploy to block someone". Reading does not have to be, so the half
that could publish the file never gets a URL at all.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TOKEN = "admin-token-for-tests"
#: Distinctive enough that finding it anywhere is proof, not coincidence.
SAID = "zarquon the landlord hollows"
TLON = "nar sen lan klung testesas ka"


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("TLON_PRELOAD", "0")
    monkeypatch.setenv("TLON_HTTPS", "0")
    monkeypatch.setenv("TLON_DB", str(tmp_path / "bench.sqlite3"))
    monkeypatch.setenv("TLON_ADMIN_TOKEN", TOKEN)
    monkeypatch.delenv("TURNSTILE_SECRET_KEY", raising=False)
    for mod in [m for m in list(sys.modules) if m.startswith("puzzle")]:
        del sys.modules[mod]

    from puzzle import server

    def fake_turn(english, write_pairs, provoke_pairs):
        return {"you": {"english": english, "surface": "mil prax ka",
                        "gloss": "g", "literary": "l", "let_go": [],
                        "refused": None, "seconds": 0.1},
                "tlon": {"english": None, "surface": TLON, "gloss": "g",
                         "literary": "l", "let_go": [], "refused": None,
                         "seconds": 0.1},
                "seconds": 0.2, "shape": "trained"}

    monkeypatch.setattr(server.speaker, "turn", fake_turn)
    monkeypatch.setattr(type(server.speaker), "ready", property(lambda s: True))
    return server


def _client(server):
    from fastapi.testclient import TestClient
    return TestClient(server.app)


def test_the_log_does_not_live_under_static(app):
    """⛔⛔⛔ `/static` IS MOUNTED. A log file dropped in there is published to
    the internet by a line of code written months earlier for another reason."""
    log = pathlib.Path(app.LOG_PATH).resolve()
    static = pathlib.Path(app.STATIC).resolve()
    assert static not in log.parents, (
        "⛔⛔⛔ the log is inside the served static directory — the answer key "
        "is downloadable")
    assert log.name not in [p.name for p in static.rglob("*")]


def _sweep(c):
    """Every endpoint a stranger can reach, plus the admin door with its key."""
    auth = {"Authorization": "Bearer " + TOKEN}
    return [c.get("/"), c.get("/healthz"), c.get("/conversation"),
            c.get("/static/app.js"), c.get("/static/log.sqlite3"),
            c.get("/log.sqlite3"), c.get("/log-snapshot.sqlite3"),
            c.get("/admin/stats"), c.get("/admin/stats", headers=auth),
            c.post("/admin/snapshot", headers=auth),
            c.post("/reveal", json={"turn": 0, "role": "tlon"})]


def test_nothing_from_the_log_reaches_a_url(app):
    """⛔⛔ SWEPT, NOT REVIEWED. A reader can be persuaded that a handler is
    safe; a sweep for a string that exists only in the log cannot be.

    ⭐ The marker is the READER ID. It appears nowhere else in the system —
    not in a cookie, not in a response, not in the bench store — so finding it
    in any body is proof that log contents escaped."""
    from puzzle import logbook as LB
    c = _client(app)
    c.post("/say", json={"english": SAID})
    c.get("/wp-login.php")                       # leaves a `probe` event

    conn = app.logbook._conn()
    try:
        reader = conn.execute("SELECT reader FROM turns").fetchone()["reader"]
    finally:
        conn.close()
    assert reader and reader != "None"

    for r in _sweep(c):
        assert reader not in r.text, (
            "⛔⛔⛔ %s returned a reader id — that string exists only in the "
            "log, so log contents are escaping" % r.url)
        assert "wp-login" not in r.text, (
            "⛔⛔ %s returned a logged event" % r.url)


def test_no_single_message_is_an_aligned_pair(app):
    """⛔⛔⛔ THE CARDINAL RULE, CHECKED PER MESSAGE RATHER THAN PER BODY.

    ⛔⛤ MY FIRST VERSION CHECKED THE WHOLE RESPONSE AND FAILED ON A CORRECT ONE.
    `/conversation` legitimately carries the reader's English on one row and the
    Tlönian's REPLY on another; those are two different utterances, not a
    translation. The leak is one ROW carrying both — which is exactly the shape
    of the bug that shipped for months, so testing it at the wrong granularity
    would have been the same mistake twice."""
    c = _client(app)
    c.post("/say", json={"english": SAID})
    for message in c.get("/conversation").json()["messages"]:
        assert not (message.get("english") and message.get("surface")), (
            "⛔⛔⛔ one message carries an English line AND its Tlön: %r"
            % message)


def test_the_admin_door_does_not_announce_itself(app):
    """⛔ 404, NOT 403. A 403 tells a scanner the endpoint is real and that the
    only missing piece is the token."""
    c = _client(app)
    for r in (c.post("/admin/ban", json={"reader": "a" * 16}),
              c.post("/admin/unban", json={"reader": "a" * 16}),
              c.post("/admin/snapshot"),
              c.get("/admin/stats"),
              c.get("/admin/stats", headers={"Authorization": "Bearer wrong"})):
        assert r.status_code == 404, "⛔ the admin door answered %s" % r.status_code


def test_a_guess_at_the_admin_door_is_recorded(app):
    c = _client(app)
    c.post("/admin/snapshot", headers={"Authorization": "Bearer wrong"})
    conn = app.logbook._conn()
    try:
        rows = conn.execute(
            "SELECT * FROM events WHERE kind='admin.denied'").fetchall()
    finally:
        conn.close()
    assert rows, ("⛔⛔ somebody guessing at the admin door is invisible until "
                  "the guess works")


def test_the_admin_stats_are_counts_and_only_counts(app):
    """⭐ The one admin READ that exists. Counts cannot translate anything —
    and that is the rule any future addition here has to meet."""
    c = _client(app)
    c.post("/say", json={"english": SAID})
    body = c.get("/admin/stats",
                 headers={"Authorization": "Bearer " + TOKEN}).json()
    for key, value in body.items():
        assert isinstance(value, (int, bool, str)), key
        if isinstance(value, str):
            assert value in ("dev", "TLON_LOG_PEPPER", "TLON_PROXY_SECRET",
                             "TURNSTILE_SECRET_KEY") or key == "last_failure", (
                "⛔⛔ /admin/stats grew a free-text field (%s=%r) — that is how "
                "a read endpoint starts" % (key, value))


def test_the_route_table_is_the_one_we_meant(app):
    """⛔⛔ THE GUARD THAT SURVIVES ME. Every check above tests the endpoints
    that exist today; this one fails when a NEW one appears, so adding a read
    path has to be a decision somebody takes rather than a line somebody adds.
    """
    from fastapi.routing import APIRoute
    paths = {r.path for r in app.app.routes if isinstance(r, APIRoute)}
    assert paths == {"/", "/healthz", "/new", "/conversation", "/say",
                     "/verify", "/reveal", "/admin/ban", "/admin/unban",
                     "/admin/snapshot", "/admin/stats"}, (
        "⛔⛔⛔ the route table changed. If the new route can return a turn, a "
        "gloss, a literary render or anything from the log, it publishes the "
        "answer key to a puzzle whose premise is that nothing on the face "
        "translates anything. Read `logbook.py`'s docstring before editing "
        "this set.")


def test_the_snapshot_lands_beside_the_log_not_in_public(app):
    c = _client(app)
    c.post("/say", json={"english": SAID})
    body = c.post("/admin/snapshot",
                  headers={"Authorization": "Bearer " + TOKEN}).json()
    assert body["ok"] and body["bytes"] > 0
    target = pathlib.Path(body["path"]).resolve()
    assert target.parent == pathlib.Path(app.LOG_PATH).resolve().parent
    assert pathlib.Path(app.STATIC).resolve() not in target.parents
