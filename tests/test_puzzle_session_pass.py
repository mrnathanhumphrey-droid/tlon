"""⛔⛔⛔ THE CAPTCHA THAT WOULD NOT CLEAR, AND WHY IT COULD NOT.

Three builds put a Turnstile widget in three different places and all three
broke the product. The placement was never the bug. The bug was that `/say`
verified a TOKEN ON EVERY MESSAGE — and a Turnstile token is SINGLE-USE, so
that means a fresh challenge between one sentence and the next. There was no
state in the design called "done", which is why the reader's report walked
through every possible symptom of the same root cause:

    "any time i try to send a message it activates"
    "the cloudflare isn't visible but it is clearly blocking me"
    "it hasn't cleared yet. its either invisible or permanent"

⭐⭐ TURNSTILE IS A DOOR, NOT A TICKET INSPECTOR. `/verify` exchanges one solved
challenge for a signed, IP-bound, httponly session pass; every later message
rides the pass. This file pins the door: that it opens, that it stays open, and
— the part that matters for a public GPU — that it cannot be forced.

⛔ IT DOES NOT REPLACE THE RATE LIMITS. `guard.py` still bounds turns per IP and
per day, which is the protection that actually matters against someone who has
already solved one challenge. The honest statement of the trade is that a
determined attacker can farm one token either way, so a per-message challenge
bought almost nothing and cost the product its usability.
"""
from __future__ import annotations

import pathlib
import sys
import time

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puzzle import turnstile as TS  # noqa: E402


class _Req:
    def __init__(self, cookies=None):
        self.cookies = cookies or {}


@pytest.fixture(autouse=True)
def _secret(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "a-test-secret")
    yield


# ── the pass itself ─────────────────────────────────────────────────────────

def test_a_fresh_pass_is_good():
    assert TS.pass_is_good(TS.issue_pass("1.2.3.4"), "1.2.3.4")


def test_the_pass_is_bound_to_the_address_that_earned_it():
    """⛔⛔ A COOKIE LIFTED FROM ONE MACHINE MUST BE WORTHLESS ON ANOTHER.
    Without this, one solved challenge is a transferable key to a public GPU —
    post the cookie anywhere and every reader of that post skips the door.

    ⭐ A reader whose address genuinely changes is simply asked once more,
    which is correct behaviour and not a defect."""
    p = TS.issue_pass("1.2.3.4")
    assert not TS.pass_is_good(p, "9.9.9.9")


def test_a_tampered_signature_is_refused():
    p = TS.issue_pass("1.2.3.4")
    flipped = p[:-1] + ("0" if p[-1] != "0" else "1")
    assert not TS.pass_is_good(flipped, "1.2.3.4")


def test_an_expiry_cannot_be_extended_by_editing_it():
    """⛔⛔ THE OBVIOUS ATTACK. The expiry is in the cookie in plain sight, so
    it MUST be inside the signed message — otherwise a reader simply edits the
    number and holds a permanent key."""
    p = TS.issue_pass("1.2.3.4")
    _, _, sig = p.partition(".")
    forged = "%d.%s" % (int(time.time()) + 999999, sig)
    assert not TS.pass_is_good(forged, "1.2.3.4")


def test_an_expired_pass_is_refused():
    stale = "%d.%s" % (1, TS._pass_sig(1, "1.2.3.4"))
    assert not TS.pass_is_good(stale, "1.2.3.4")


@pytest.mark.parametrize("junk", ["", "nonsense", ".", "abc.def", "12.", ".xyz"])
def test_malformed_passes_are_refused_without_raising(junk):
    """⛔ A pass that raises is a 500 on a public endpoint. Every shape of
    rubbish a client can put in a cookie has to come back False."""
    assert TS.pass_is_good(junk, "1.2.3.4") is False


def test_the_secret_is_what_signs_it(monkeypatch):
    """⛔⛔ THE PASS MUST NOT SURVIVE A KEY ROTATION. If it did, the signature
    would be keyed on something an attacker could reconstruct."""
    p = TS.issue_pass("1.2.3.4")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "a-different-secret")
    assert not TS.pass_is_good(p, "1.2.3.4")


def test_has_pass_reads_the_cookie():
    p = TS.issue_pass("1.2.3.4")
    assert TS.has_pass(_Req({TS.PASS_COOKIE: p}), "1.2.3.4")
    assert not TS.has_pass(_Req({}), "1.2.3.4")


def test_with_turnstile_off_everyone_has_a_pass(monkeypatch):
    """⭐ Local dev, where there is no secret and no card. `has_pass` answers
    the only question the caller asks — *must I challenge this person?* — so
    "off" and "already passed" are correctly the same answer."""
    monkeypatch.delenv("TURNSTILE_SECRET_KEY", raising=False)
    assert TS.has_pass(_Req({}), "1.2.3.4")


# ── the wiring, at the endpoints ────────────────────────────────────────────

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TLON_PRELOAD", "0")
    monkeypatch.setenv("TLON_HTTPS", "0")
    monkeypatch.setenv("TLON_DB", str(tmp_path / "bench.sqlite3"))
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "a-test-secret")
    for mod in [m for m in list(sys.modules) if m.startswith("puzzle")]:
        del sys.modules[mod]

    from fastapi.testclient import TestClient

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
    return TestClient(server.app), server


def _pass_cloudflare(monkeypatch, server, ok=True):
    """Stand in for siteverify so the door can be opened without a network."""
    monkeypatch.setattr(server.TS, "verify",
                        lambda tok, ip=None: (ok, "ok" if ok else "refused"))


def test_without_a_pass_a_message_is_refused(client):
    """⛔ The control. If this passed, everything below would prove nothing —
    the door would simply be open to all."""
    c, _ = client
    r = c.post("/say", json={"english": "hello"})
    assert r.status_code == 403
    assert "person" in r.json()["error"]


def test_verify_opens_the_door_and_one_message_does_not_close_it(
        client, monkeypatch):
    """⛔⛔⛔ THE WHOLE POINT, AND THE ONE THING EVERY EARLIER BUILD FAILED.
    After the door is opened, message two, three and four must go through with
    NO token and NO further challenge. A build that verified per-message passes
    the first half of this test and fails the second."""
    c, server = client
    _pass_cloudflare(monkeypatch, server)

    assert c.post("/verify", json={"turnstile": "solved"}).json()["ok"] is True
    assert TS.PASS_COOKIE in c.cookies

    # ⛔ And now Cloudflare is made to REFUSE everything, so a build that still
    # verified per-message could not sneak through on a lenient stub.
    _pass_cloudflare(monkeypatch, server, ok=False)
    for n in range(4):
        r = c.post("/say", json={"english": "message %d" % n})
        assert r.status_code == 200, (
            "⛔⛔⛔ message %d was challenged again — the gate does not stay "
            "cleared, which is the bug this whole design replaced: %s"
            % (n, r.text))


def test_a_failed_challenge_does_not_open_the_door(client, monkeypatch):
    c, server = client
    _pass_cloudflare(monkeypatch, server, ok=False)
    r = c.post("/verify", json={"turnstile": "bad"})
    assert r.status_code == 403
    assert TS.PASS_COOKIE not in c.cookies
    assert c.post("/say", json={"english": "hello"}).status_code == 403


def test_a_token_presented_inline_still_works_and_earns_the_pass(
        client, monkeypatch):
    """⭐ THE COOKIE-LESS CLIENT IS NOT LOCKED OUT. A script, a curl, the smoke
    test — anything with a valid token gets through `/say` exactly as before.
    The endpoint gained a second way IN, not a way around: this is what stops
    the redesign from quietly narrowing who may use the bench."""
    c, server = client
    _pass_cloudflare(monkeypatch, server)
    r = c.post("/say", json={"english": "hello", "turnstile": "solved"})
    assert r.status_code == 200
    assert TS.PASS_COOKIE in c.cookies, (
        "⛔ an inline token should also earn the pass, or that caller is "
        "challenged on every message — the original bug, for scripts")


def test_the_pass_cookie_is_httponly(client, monkeypatch):
    """⛔⛔ NOTHING IN THE PAGE READS THIS. A script that cannot read the pass
    cannot carry it anywhere else, and the page has no need for it: it asks the
    SERVER whether the gate is required."""
    c, server = client
    _pass_cloudflare(monkeypatch, server)
    r = c.post("/verify", json={"turnstile": "solved"})
    setc = r.headers.get("set-cookie", "")
    assert TS.PASS_COOKIE in setc
    assert "httponly" in setc.lower(), "⛔⛔ the pass is readable from JS"


def test_conversation_tells_the_page_whether_the_gate_is_needed(
        client, monkeypatch):
    """⛔⛔ THE PAGE MUST NOT GUESS. The pass is httponly, so the browser cannot
    see it; a page that guessed would show a human a challenge they had already
    passed — which is precisely the complaint this redesign answers."""
    c, server = client
    assert c.get("/conversation").json()["human"] is False
    _pass_cloudflare(monkeypatch, server)
    c.post("/verify", json={"turnstile": "solved"})
    assert c.get("/conversation").json()["human"] is True


def test_verify_is_not_metered_by_the_turn_limit(client, monkeypatch):
    """⭐ It runs no model and touches no GPU. Metering it would lock out
    exactly the readers who have been using the bench properly: hit the turn
    limit, have your pass expire, and now you cannot re-open the door either."""
    c, server = client
    _pass_cloudflare(monkeypatch, server)
    before = c.get("/healthz").json()["turns_today"]
    c.post("/verify", json={"turnstile": "solved"})
    assert c.get("/healthz").json()["turns_today"] == before


# ── the placeholder key, and the three faults that hid it ───────────────────

def test_a_bad_secret_is_reported_as_a_bad_secret_not_as_unreachable(
        monkeypatch):
    """⛔⛔⛔ THE BUG THAT COST THE MOST, AND IT HID IN AN `except` CLAUSE.

    Cloudflare answers a bad secret with **HTTP 400**, not 200, and `urllib`
    raises `HTTPError` on any non-2xx. That was caught alongside the genuine
    network errors, so a perfectly reachable Cloudflare was reported as
    "turnstile unreachable" — AND THE RESPONSE BODY WAS DISCARDED. The body
    said `invalid-input-secret`: the deployed key was a 30-character
    placeholder, every reader was refused for days, and the one code that
    would have named it was thrown away by the handler meant to be defensive.

    ⭐ This module's own docstring already said `invalid-input-secret` must
    stay diagnosable. The comment was right; the code three lines below it was
    not. A 4xx body is still an answer — read it.
    """
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "x")

    class Err(TS.urllib.error.HTTPError):
        def __init__(self):
            super().__init__("u", 400, "Bad Request", {}, None)

        def read(self):
            return b'{"success":false,"error-codes":["invalid-input-secret"]}'

    def boom(*a, **k):
        raise Err()

    monkeypatch.setattr(TS.urllib.request, "urlopen", boom)
    ok, why = TS.verify("tok", None)
    assert ok is False
    assert "invalid-input-secret" in why, (
        "⛔⛔⛔ a misconfigured server key is being reported as a network "
        "problem — the operator chases Cloudflare while every reader is "
        "refused, which is exactly what happened: %r" % why)
    assert "unreachable" not in why


def test_a_real_network_failure_is_still_reported_as_unreachable(monkeypatch):
    """⭐ THE CONTROL. Reading 4xx bodies must not swallow the genuine case —
    an unreachable Cloudflare still has to fail closed and say so."""
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "x")

    def boom(*a, **k):
        raise OSError("no route to host")

    monkeypatch.setattr(TS.urllib.request, "urlopen", boom)
    ok, why = TS.verify("tok", None)
    assert ok is False and "unreachable" in why


def test_the_key_verdict_distinguishes_a_bad_key_from_a_bad_minute(monkeypatch):
    """⛔⛔ PRESENCE IS NOT VALIDITY. `preflight()` only ever asked whether a
    secret EXISTED, so a placeholder booted the app into a state where it
    reported healthy and refused everybody. `scope_hides_in_the_constant`: the
    predicate checked the cheap half of the condition.

    ⛔ And it must NOT call a network blip a bad key — that would turn one bad
    Cloudflare minute into a self-inflicted outage."""
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "x")

    monkeypatch.setattr(TS, "verify",
                        lambda t, ip=None: (False, "turnstile refused: invalid-input-secret"))
    assert TS.key_verdict() == "bad-key"

    monkeypatch.setattr(TS, "verify",
                        lambda t, ip=None: (False, "turnstile unreachable: OSError"))
    assert TS.key_verdict() == "unknown", (
        "⛔ a network failure must never be diagnosed as a bad key")

    monkeypatch.setattr(TS, "verify",
                        lambda t, ip=None: (False, "turnstile refused: invalid-input-response"))
    assert TS.key_verdict() == "ok", (
        "⛔ invalid-input-response means the KEY is fine and only our dummy "
        "token was junk — that is the expected healthy answer")


def test_healthz_reports_the_key_verdict(client):
    """⛔⛔ A HEALTH CHECK THAT SAYS `ok: true` WHILE EVERY READER IS REFUSED IS
    THE SILENT-SUCCESS SHAPE THIS REPO KEEPS HITTING. The field is what makes
    the placeholder visible from outside without reading any logs."""
    c, _ = client
    assert "turnstile_key" in c.get("/healthz").json()


def test_the_page_does_not_retry_a_misconfiguration_forever():
    """⛔⛔⛔ THE SPIN NATE SAW. A failed /verify reset the widget, the widget
    auto-solved, that re-fired /verify, and round it went — unbounded, with
    "HTTPError" flashing. The failure was a bad SERVER key: no number of
    retries could ever fix it and each one cost a siteverify round-trip.

    ⭐ An unbounded retry on a non-transient failure is not resilience, it is a
    loop. Capped, and `invalid-input-secret` is never retried at all because
    the reader genuinely cannot clear it."""
    js = (ROOT / "puzzle" / "static" / "app.js").read_text(encoding="utf-8")
    import re as _re
    code = _re.sub(r"/\*.*?\*/", "", js, flags=_re.S)
    assert "TS_MAX_TRIES" in code, (
        "⛔⛔⛔ nothing bounds the verify retries — a misconfigured key spins "
        "the gate forever")
    body = code[code.index("function tsPassed"):]
    body = body[:body.index("\n  function ")]
    assert "invalid-input-secret" in body, (
        "⛔ the one failure the reader cannot fix must be named and must stop "
        "the retry, or they sit watching a spinner that will never clear")
