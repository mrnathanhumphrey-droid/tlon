"""⛔⛔⛔ WHAT ADDING tlon. TO A *CREDENTIALED* CORS ALLOWLIST ACTUALLY COST.

Until 2026-09-25 an injection on the bench defaced a puzzle. Then
`tlon.resolveresearcher.com` was added to the auth API's CORS allowlist — with
`allow_credentials=True`, because the shared top bar has to read `/v1/auth/me`
to know whether to say "account" — and the blast radius moved with it. Script
running on this origin can now make CREDENTIALED calls to
api.resolveresearcher.com as whoever is reading, and read the replies.

⭐ CSRF still blocks the WRITES: its token lives in each origin's own
localStorage and this origin has none. What an injection would get is READ
access to a reader's account through GET endpoints. Not account takeover, and
not nothing.

⛔ AND THIS PAGE RENDERS OUTPUT FROM A LANGUAGE MODEL THAT ANY STRANGER CAN
STEER — the least trustworthy string in the building. `app.js` is careful
(every surface goes through `textContent`), but "we were careful" is not a
control, and after the allowlist change it was the only thing standing between
a prompt and somebody's account data.

This file pins the controls that replaced the carefulness.
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
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TLON_PRELOAD", "0")
    monkeypatch.setenv("TLON_HTTPS", "0")
    monkeypatch.setenv("TLON_DB", str(tmp_path / "bench.sqlite3"))
    monkeypatch.delenv("TURNSTILE_SECRET_KEY", raising=False)
    for mod in [m for m in list(sys.modules) if m.startswith("puzzle")]:
        del sys.modules[mod]
    from fastapi.testclient import TestClient
    from puzzle import server
    monkeypatch.setattr(type(server.speaker), "ready", property(lambda s: True))
    return TestClient(server.app), server


# ── the content security policy ─────────────────────────────────────────────

def _csp(client) -> str:
    c, _ = client
    return c.get("/").headers.get("content-security-policy", "")


def test_the_page_carries_a_csp(client):
    assert _csp(client), "⛔⛔ no Content-Security-Policy on a page that renders "\
                         "model output from an origin the auth API trusts"


def test_script_src_does_not_permit_unsafe_inline(client):
    """⛔⛔⛔ THE ONE THAT MAKES THE WHOLE HEADER REAL OR DECORATIVE. With
    'unsafe-inline' an injected <script> runs exactly like ours, and everything
    else in the policy is theatre."""
    policy = _csp(client)
    script = [d for d in policy.split(";") if d.strip().startswith("script-src")]
    assert script, "no script-src directive"
    assert "'unsafe-inline'" not in script[0], (
        "⛔⛔⛔ script-src allows 'unsafe-inline' — an injected script would run")
    assert "'nonce-" in script[0], "the two load-bearing inline scripts need a nonce"


def test_the_nonce_is_fresh_on_every_response(client):
    """⛔⛔ A FIXED NONCE IS NOT A NONCE. It would sit in the page source for an
    injection to quote, which is a CSP that costs a header and stops nothing."""
    c, _ = client
    seen = {re.search(r"'nonce-([^']+)'", c.get("/").headers["content-security-policy"]).group(1)
            for _ in range(5)}
    assert len(seen) == 5, "⛔⛔ the CSP nonce repeats across responses"


def test_the_nonce_in_the_header_matches_the_one_in_the_page(client):
    """⛔ Mismatched and the two inline scripts are silently blocked — the theme
    stamp stops running (dark flash for light readers) and the Turnstile
    handshake never registers, which is a dead gate."""
    c, _ = client
    r = c.get("/")
    header = re.search(r"'nonce-([^']+)'", r.headers["content-security-policy"]).group(1)
    in_page = re.findall(r'<script nonce="([^"]+)"', r.text)
    assert len(in_page) == 2, "expected exactly the two load-bearing inline scripts"
    assert set(in_page) == {header}
    assert "{{CSP_NONCE}}" not in r.text, "⛔ the placeholder leaked to the browser"


def test_connect_src_still_allows_the_auth_api(client):
    """⛔⛔ THE MISTAKE I MADE WRITING THIS POLICY, CAUGHT IN A BROWSER. I left
    api.resolveresearcher.com out, reasoning that "nothing served by this app
    calls the auth API". False where it counts: apex's `theme.js` is FETCHED
    from resolveresearcher.com but EXECUTES in this document, so its
    /v1/auth/me call is judged against THIS origin's policy. Omitting it would
    have silently re-broken the log-in this page had just been fixed to show —
    the same bug, re-inflicted by its own mitigation."""
    policy = _csp(client)
    connect = [d for d in policy.split(";") if d.strip().startswith("connect-src")][0]
    assert "https://api.resolveresearcher.com" in connect, (
        "⛔⛔ the top bar's auth call would be blocked and the reader would be "
        "told to log in while signed in")
    assert "https://challenges.cloudflare.com" in connect, "the gate needs this"


def test_the_policy_blocks_exfiltration_and_framing(client):
    """⭐ WHAT IS STILL BOUGHT once the auth API must be reachable: an injection
    can call it, but cannot post what it reads anywhere. Exfiltration is the
    step worth blocking."""
    policy = _csp(client)
    assert "default-src 'self'" in policy
    assert "frame-ancestors 'none'" in policy
    assert "object-src 'none'" in policy
    assert "base-uri 'none'" in policy


def test_no_model_output_can_reach_innerhtml():
    """⛔⛔ THE INVARIANT THE CSP IS BACKUP FOR, NOT A REPLACEMENT OF. Every
    Tlön surface, gloss and literary render is written with textContent. A
    single innerHTML on a model-authored string is an injection on an origin
    the auth API now trusts with credentials."""
    js = (ROOT / "puzzle" / "static" / "app.js").read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    code = re.sub(r"//[^\n]*", "", code)
    for bad in ("innerHTML", "outerHTML", "insertAdjacentHTML",
                "document.write", "eval("):
        assert bad not in code, (
            "⛔⛔⛔ app.js uses %s — model output is attacker-steerable and this "
            "origin can now make credentialed calls to the auth API" % bad)


# ── the gate's own rate limit ───────────────────────────────────────────────

def test_verify_is_metered(client, monkeypatch):
    """⛔⛔ I SHIPPED /verify UNMETERED. It escapes the TURN limit on purpose —
    a reader whose pass expired must be able to re-open the door even after
    spending their turns — but every call makes an OUTBOUND request to
    Cloudflare's siteverify, so with no limit at all it is a free amplifier
    pointed at our own quota and this box's CPU, reachable by anyone."""
    c, server = client
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "x")
    monkeypatch.setattr(server.TS, "verify", lambda t, ip=None: (False, "no"))
    seen = {c.post("/verify", json={"turnstile": "x"}).status_code
            for _ in range(60)}
    assert 429 in seen, (
        "⛔⛔ /verify never rate limits — 60 calls all went through to "
        "siteverify. That is an open amplifier.")


def test_the_gate_limit_is_looser_than_the_turn_limit():
    """⭐ THE CONTROL. Metering it with the TURN limit would lock out exactly
    the readers who have been using the bench properly: spend your turns, have
    your pass expire, and now you cannot re-open the door either."""
    from puzzle import server
    assert server.gate_limiter.ip_turns > server.limiter.ip_turns


# ── the client address, and what silently depends on it ────────────────────

def test_an_unsigned_request_is_counted_not_swallowed(monkeypatch):
    """⛔⛔⛔ THE SILENT DEGRADATION. If `TLON_PROXY_SECRET` is wrong on either
    side, `client_ip` falls through to Cloudflare's egress address — the SAME
    STRING FOR EVERY READER. That does not merely merge the rate limit:
    `issue_pass` signs HMAC(exp, ip), so a shared ip means ONE READER'S PASS
    VALIDATES FOR EVERYONE. The binding whose whole job is to make a lifted
    cookie worthless elsewhere becomes no binding at all.

    ⛔ It has already happened — the secret was a single non-printable
    character for days and nothing reported it."""
    from puzzle import guard as G

    class Req:
        def __init__(self, headers):
            self.headers = {k.lower(): v for k, v in headers.items()}
            self.client = type("C", (), {"host": "10.0.0.1"})()

    monkeypatch.setenv("TLON_PROXY_SECRET", "right")
    before = dict(G.PROXY_TRUST)
    G.client_ip(Req({"X-Forwarded-For": "cf-egress"}), trust_proxy=True)
    assert G.PROXY_TRUST["unsigned"] == before["unsigned"] + 1, (
        "⛔⛔ an unsigned request was not counted — the degradation stays "
        "invisible and /healthz keeps saying everything is fine")

    G.client_ip(Req({"X-Tlon-Proxy-Secret": "right",
                     "X-Tlon-Client-IP": "1.2.3.4"}), trust_proxy=True)
    assert G.PROXY_TRUST["signed"] == before["signed"] + 1


def test_healthz_reports_the_proxy_trust(client):
    """⭐ `proxy_unsigned > 0` in production is the one number that says the
    per-IP limit and the pass binding are both inert."""
    c, _ = client
    body = c.get("/healthz").json()
    assert "proxy_unsigned" in body and "proxy_signed" in body


def test_the_page_demands_https_for_next_time(client):
    """⛔⛔ HSTS WAS MISSING ENTIRELY, and it was found by reading the LIVE
    headers rather than the code — nothing in this suite had ever asked.

    Without it the first visit of every reader is one `http://` away from being
    read on a café network, and both the bench cookie and the session pass ride
    that request. Cloudflare does not add it by default; measured on the
    deployed site during the v1 audit, where it was absent."""
    c, _ = client
    for path in ("/", "/healthz", "/conversation"):
        hsts = c.get(path).headers.get("strict-transport-security", "")
        assert "max-age=" in hsts, "⛔⛔ %s carries no HSTS" % path
        assert int(hsts.split("max-age=")[1].split(";")[0]) >= 15552000, (
            "⛔ an HSTS shorter than six months is treated as a rounding error "
            "by the preload lists and barely protects a returning reader")


def test_starting_a_new_bench_is_metered(client):
    """⛔⛤ `/new` WAS FREE IN BOTH SENSES AND ONLY ONE WAS INTENDED. It runs no
    model, so it rightly escapes the TURN limit — but every call INSERTS A ROW,
    and it needs no captcha, no cookie and no pass. A one-line script could add
    empty conversations until the bench volume filled, taking the puzzle down
    without ever running a generation.

    ⭐ Found by asking each door "what does this COST", which is a different
    question from "what does this COMPUTE" — the question `guard.py` was
    written to answer, and the reason this one slipped past it."""
    c, _ = client
    seen = {c.post("/new").status_code for _ in range(60)}
    assert 429 in seen, (
        "⛔⛔ /new never rate limits — 60 calls all inserted a conversation")


def test_but_a_person_starting_over_is_never_told_to_wait(client):
    """⭐ THE CONTROL. Metering it with the TURN limit would punish exactly the
    reader who is using the bench properly: spend your twelve turns, want a
    fresh start, and be refused the free thing too."""
    from puzzle import server
    assert server.gate_limiter.ip_turns > server.limiter.ip_turns
    c, _ = client
    assert c.post("/new").status_code == 200
