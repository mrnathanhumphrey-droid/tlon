"""⛔⛔ EVERY READER GETS THEIR OWN BENCH, OR THE PUZZLE IS A PARTY LINE.

Nate, unprompted: *"i bet theres a bug you didn't account for — everyone that
loads the page should get a separate instance. not the same window and chat."*
He was right to look. The app logic was sound, but two things stood between it
and a shared conversation, and BOTH were relying on a default rather than on
anything this repo had said:

  * nothing declared these responses uncacheable. Cloudflare happened not to
    cache them, which is a default, not an instruction — and the app sits
    behind a CDN plus whatever proxy a reader's network runs;
  * the Worker rebuilt response headers with `new Headers(...)`, which joins
    repeated fields with ", ". That is right for every header except
    `Set-Cookie`, where it turns two cookies into one malformed value and the
    browser keeps neither.

⭐ THE SECOND ONE LANDS ON THE FIRST TURN OF EVERY NEW READER, because that is
the one response carrying two cookies at once (`tlon_bench` + `tlon_human`).
It would present as the bench forgetting people, with nothing in any log.
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("TLON_PRELOAD", "0")
    monkeypatch.setenv("TLON_HTTPS", "0")
    monkeypatch.setenv("TLON_DB", str(tmp_path / "bench.sqlite3"))
    monkeypatch.delenv("TURNSTILE_SECRET_KEY", raising=False)
    for mod in [m for m in list(sys.modules) if m.startswith("puzzle")]:
        del sys.modules[mod]

    from puzzle import server

    def fake_turn(english, write_pairs, provoke_pairs):
        return {"you": {"english": english, "surface": "mil prax ka",
                        "gloss": "g", "literary": "l", "let_go": [],
                        "refused": None, "seconds": 0.1},
                "tlon": {"english": None, "surface": "sen hlin tlux kae",
                         "gloss": "g", "literary": "l", "let_go": [],
                         "refused": None, "seconds": 0.1},
                "seconds": 0.2, "shape": "trained"}

    monkeypatch.setattr(server.speaker, "turn", fake_turn)
    monkeypatch.setattr(type(server.speaker), "ready", property(lambda s: True))
    return server


def _client(server):
    """⛔ A SEPARATE COOKIE JAR PER READER. Two `TestClient`s over one app is
    exactly two browsers over one server, which is the thing under test."""
    from fastapi.testclient import TestClient
    return TestClient(server.app)


def test_two_readers_do_not_share_a_bench(app):
    """⛔⛔ THE HEADLINE. Separate conversation ids, and neither sees the
    other's lines — checked from BOTH sides, because a leak in one direction is
    still a leak."""
    a, b = _client(app), _client(app)
    a.post("/say", json={"english": "alpha one"})
    a.post("/say", json={"english": "alpha two"})
    b.post("/say", json={"english": "bravo one"})

    ca = a.get("/conversation").json()
    cb = b.get("/conversation").json()

    assert ca["conversation_id"] != cb["conversation_id"], (
        "⛔⛔⛔ two readers were handed the same bench")
    said_a = [m.get("english") for m in ca["messages"] if m["role"] == "you"]
    said_b = [m.get("english") for m in cb["messages"] if m["role"] == "you"]
    assert said_a == ["alpha one", "alpha two"]
    assert said_b == ["bravo one"]
    assert "bravo one" not in said_a, "⛔⛔⛔ B's line appeared on A's bench"
    assert "alpha one" not in said_b, "⛔⛔⛔ A's line appeared on B's bench"


def test_a_reader_who_has_said_nothing_has_no_bench(app):
    """⭐ The control. If a fresh visitor inherited SOMEBODY's conversation,
    the test above could still pass while the page was a party line."""
    a = _client(app)
    a.post("/say", json={"english": "alpha one"})
    fresh = _client(app)
    body = fresh.get("/conversation").json()
    assert body["conversation_id"] is None
    assert body["messages"] == []


def test_a_readers_bench_survives_someone_elses_turn(app):
    """⛔ The store is one SQLite file and the speaker is one process-wide
    object. A second reader speaking must not disturb the first."""
    a, b = _client(app), _client(app)
    a.post("/say", json={"english": "alpha one"})
    before = a.get("/conversation").json()
    b.post("/say", json={"english": "bravo one"})
    after = a.get("/conversation").json()
    assert before == after


def test_nothing_personal_is_cacheable(app):
    """⛔⛔⛔ THE FAILURE THAT WOULD LOOK EXACTLY LIKE NATE'S HUNCH. A cached
    `/conversation` is one reader's bench served to the next person who asks.
    Cloudflare does not cache these today — but that is its default, not our
    instruction, and there is a CDN plus whoever else's proxy in the path."""
    c = _client(app)
    c.post("/say", json={"english": "alpha one"})
    for path in ("/", "/conversation", "/healthz"):
        r = c.get(path)
        cc = r.headers.get("cache-control", "")
        assert "no-store" in cc, (
            "⛔⛔⛔ %s does not forbid caching (%r) — one cache rule anywhere "
            "in the path and two strangers share a bench" % (path, cc))
        assert "private" in cc


def test_static_files_are_still_cacheable(app):
    """⭐ THE CONTROL, AND IT IS NOT DECORATION. A blanket no-store would make
    every reader re-download the stylesheet and the script on every navigation.
    Those files are identical for everybody; they are the only thing here that
    is not somebody's."""
    c = _client(app)
    r = c.get("/static/app.js")
    assert r.status_code == 200
    assert "no-store" not in r.headers.get("cache-control", "")


def test_the_worker_does_not_collapse_two_cookies():
    """⛔⛔⛔ `new Headers(...)` JOINS REPEATED FIELDS WITH ", ", WHICH IS RIGHT
    FOR EVERY HEADER EXCEPT THIS ONE. Two cookies become one malformed value
    and the browser stores NEITHER.

    `/say` returns exactly that pair on a new reader's first turn —
    `tlon_bench` (their conversation) and `tlon_human` (their pass) — so this
    would land on the first message of every new visitor and present as the
    bench forgetting them, with nothing in any log to say why.

    ⭐ Asserted on the Worker source because there is no way to reach this from
    Python, and an untested proxy is where this repo has already lost a day."""
    js = (ROOT / "puzzle" / "worker" / "tlon-proxy.js").read_text(
        encoding="utf-8")
    code = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    code = re.sub(r"//[^\n]*", "", code)
    assert "getSetCookie" in code, (
        "⛔⛔⛔ the Worker rebuilds headers without re-applying Set-Cookie "
        "individually — two cookies in one response will be merged and lost")
    assert re.search(r'append\(\s*["\']set-cookie["\']', code), (
        "⛔ they must be APPENDED one at a time; a `set` would keep only the "
        "last, which is the same bug with one survivor")


# ── and their own CONTEXT, which is the sharper question ────────────────────

def test_concurrent_readers_never_see_each_others_context(app):
    """⛔⛔⛔ THE QUESTION SEQUENTIAL TESTS DO NOT ANSWER. Two readers having
    their own conversation ROWS is not the same as the model being handed the
    right WINDOW. The window is what makes the puzzle solvable — roots recur
    across turns — so a crossed context would not throw, would not log, and
    would read as the Tlönian mysteriously answering someone else.

    ⛔ The backend that carries it is ONE PROCESS-WIDE OBJECT with a
    `conversation` attribute set per call. Nothing about that is safe by
    construction; it is safe because `guard.MAX_CONCURRENT` is 1 and the call
    happens inside the slot. This fires both readers at each other in threads
    and checks what the model was actually given.
    """
    import threading

    server = app
    seen = []
    lock = threading.Lock()
    real_turn = server.speaker.turn

    def recording_turn(english, write_pairs, provoke_pairs):
        with lock:
            seen.append((english, list(write_pairs), list(provoke_pairs)))
        return real_turn(english, write_pairs, provoke_pairs)

    server.speaker.turn = recording_turn
    try:
        a, b = _client(server), _client(server)
        # each reader needs a bench before the threads race for it
        a.post("/say", json={"english": "alpha 0"})
        b.post("/say", json={"english": "bravo 0"})

        def run(client, tag, n):
            for i in range(1, n + 1):
                client.post("/say", json={"english": "%s %d" % (tag, i)})

        ta = threading.Thread(target=run, args=(a, "alpha", 4))
        tb = threading.Thread(target=run, args=(b, "bravo", 4))
        ta.start(); tb.start(); ta.join(); tb.join()
    finally:
        server.speaker.turn = real_turn

    assert len(seen) >= 10, "the race did not actually run"
    for english, write_pairs, _provoke in seen:
        mine = "alpha" if english.startswith("alpha") else "bravo"
        theirs = "bravo" if mine == "alpha" else "alpha"
        # the WRITE window carries the reader's own prior English
        flat = " ".join(u for pair in write_pairs for u in pair)
        assert theirs not in flat, (
            "⛔⛔⛔ while answering %r the model was given the OTHER reader's "
            "context: %r" % (english, flat))


def test_one_generation_at_a_time_is_what_makes_that_true(app):
    """⛔⛔ THE COUPLING THAT IS EASY TO BREAK AND INVISIBLE WHEN BROKEN.

    The test above passes because `speaker.turn` runs inside a slot that admits
    ONE caller. The backend holds the window on a single shared object, so
    raising MAX_CONCURRENT for throughput would let two readers' contexts
    interleave — and the symptom would be the Tlönian answering the wrong
    person, with nothing in any log.

    ⭐ Pinned here so the number cannot be raised without someone reading this.
    """
    from puzzle import guard as G
    assert G.MAX_CONCURRENT == 1, (
        "⛔⛔⛔ MAX_CONCURRENT > 1 while the backend keeps conversation state on "
        "one process-wide object — readers' contexts can interleave")

    src = (ROOT / "puzzle" / "server.py").read_text(encoding="utf-8")
    at_slot = src.index("with limiter.slot():")
    at_turn = src.index("speaker.turn(", at_slot)
    assert at_turn - at_slot < 200, (
        "⛔⛔ speaker.turn is no longer inside the concurrency slot")


def test_the_shared_window_is_cleared_even_when_a_turn_fails(app):
    """⛔⛔ THE BENCH LEAK, WHICH ALREADY HAPPENED ONCE. A refused write left
    `backend.conversation` set, so the NEXT reader's generation inherited the
    previous one's window — cross-reader context bleed via an error path, which
    no happy-path test can see."""
    import re
    src = (ROOT / "puzzle" / "speaker.py").read_text(encoding="utf-8")
    body = src[src.index("def turn("):]
    body = body[:body.index("\n    def ", 1)] if "\n    def " in body[1:] else body
    assert re.search(r"finally:\s*\n\s*backend\.conversation = \[\]", body), (
        "⛔⛔⛔ the shared window is not cleared in a `finally` — a refused or "
        "raising turn leaves it set for whoever speaks next")
