"""⛔⛔ TURNSTILE IS VERIFIED ON THE SERVER, OR IT IS DECORATION.

`/say` is the endpoint that runs the 7B. A check the CLIENT performs — in the
browser, or in a separate call it may simply not make — guards nothing: a script
POSTs straight here and never renders a widget at all. So what is pinned below
is that the verification happens inside the request that spends the GPU, that a
missing secret in a deployed environment REFUSES TO BOOT rather than serving
unprotected, and that an unreachable Cloudflare is a refusal rather than a pass.

⭐ It does not replace `guard.py`. That bounds how much compute the world may
spend; this bounds who may spend it. A botnet politely obeying the per-IP limit
still eats the global daily budget real readers need.
"""
from __future__ import annotations

import importlib
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TS = importlib.import_module("puzzle.turnstile")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in ("TURNSTILE_SECRET_KEY", "FLY_APP_NAME", "FLY_MACHINE_ID",
              "KUBERNETES_SERVICE_HOST", "RENDER", "DYNO"):
        monkeypatch.delenv(k, raising=False)
    yield


# ── the fail-closed boot ────────────────────────────────────────────────────

def test_a_deployed_machine_without_the_secret_refuses_to_boot(monkeypatch):
    """⛔⛔ THE FAILURE THIS EXISTS TO PREVENT. Shipping without running
    `fly secrets set` would put a public GPU endpoint online with nothing but
    the rate limit in front of it — and it would report healthy the whole time,
    which is the silent-success shape this repo has now hit four times."""
    monkeypatch.setenv("FLY_APP_NAME", "tlon-bench")
    with pytest.raises(TS.Misconfigured) as exc:
        TS.preflight()
    assert "REFUSING TO START" in str(exc.value)
    assert "TURNSTILE_SECRET_KEY" in str(exc.value)


def test_a_deployed_machine_with_the_secret_boots(monkeypatch):
    """⭐ The control. A guard that fired unconditionally would prove nothing
    about the condition it names — and would make the app undeployable."""
    monkeypatch.setenv("FLY_APP_NAME", "tlon-bench")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "x")
    TS.preflight()


def test_local_without_a_secret_is_simply_off():
    """⭐ No card, no secret, no challenge. `required()` and the page's widget
    both read the same absence rather than being kept in step by hand."""
    TS.preflight()
    assert TS.required() is False
    ok, why = TS.verify("", None)
    assert ok is True and "off" in why


# ── the predicate ───────────────────────────────────────────────────────────

def test_a_missing_token_is_refused_once_a_secret_exists(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "x")
    ok, why = TS.verify("", "1.2.3.4")
    assert ok is False and "no turnstile token" in why


def test_an_unreachable_cloudflare_is_a_REFUSAL_not_a_pass(monkeypatch):
    """⛔⛔ FAIL CLOSED. Treating a network error as success hands the GPU to
    anyone who can make siteverify unreachable — or to a flaky minute. The
    reader is told to try again; the card stays shut."""
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "x")

    def boom(*a, **k):
        raise OSError("no route to host")

    monkeypatch.setattr(TS.urllib.request, "urlopen", boom)
    ok, why = TS.verify("tok", None)
    assert ok is False
    assert "unreachable" in why


def test_cloudflares_error_codes_survive_into_the_reason(monkeypatch):
    """⭐ `invalid-input-secret` means the WRONG KEY was deployed, and it would
    otherwise be indistinguishable from a reader failing the challenge — the
    first breaks the puzzle for everyone at once."""
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "x")

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"success": false, "error-codes": ["invalid-input-secret"]}'

    monkeypatch.setattr(TS.urllib.request, "urlopen", lambda *a, **k: Resp())
    ok, why = TS.verify("tok", None)
    assert ok is False and "invalid-input-secret" in why


def test_a_good_token_passes(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "x")

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"success": true}'

    monkeypatch.setattr(TS.urllib.request, "urlopen", lambda *a, **k: Resp())
    assert TS.verify("tok", "1.2.3.4")[0] is True


def test_the_secret_is_never_returned(monkeypatch):
    """⛔ Not in the reason string, not in an error. The reason is shown to the
    browser."""
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "s3cr3t-do-not-leak")
    for token in ("", "tok"):
        ok, why = TS.verify(token, None)
        assert "s3cr3t-do-not-leak" not in why


# ── the wiring ──────────────────────────────────────────────────────────────

def _src(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_say_verifies_before_it_reaches_the_model():
    """⛔⛔ ORDER IS THE WHOLE POINT. A verification after `speaker.turn` has
    already run costs exactly what it was meant to save."""
    import re
    body = _src("puzzle/server.py")
    fn = re.search(r"def say\(.*?\n(?=@app\.)", body, re.S)
    assert fn, "could not find the /say handler"
    text = fn.group(0)
    at_verify = text.index("TS.verify(")
    at_model = text.index("speaker.turn(")
    assert at_verify < at_model, (
        "⛔⛔ /say reaches the model before it verifies the token")


def test_the_page_never_carries_the_secret():
    """⛔ The SITE key is public by design and is substituted in. The SECRET
    must never appear in anything served to a browser."""
    for rel in ("puzzle/static/index.html", "puzzle/static/app.js"):
        assert "TURNSTILE_SECRET_KEY" not in _src(rel)
    assert "{{TURNSTILE_SITEKEY}}" in _src("puzzle/static/index.html")


def test_the_widget_is_reset_before_every_turn():
    """⛔⛔ A TURNSTILE TOKEN IS SINGLE-USE. Without a reset the first message
    works and the second replays a spent token — which presents as "it stopped
    answering me", and a one-message smoke test would never see it.

    ⛔ THE ASSERTION MOVED WITH THE CODE, AND THE REASON DID NOT. This read
    `turnstile.reset()` while the widget drew itself from the markup and there
    was only ever one. The widget is now rendered explicitly — which is what
    makes `error-callback` reachable at all — so the reset carries the widget
    id. A bare `reset()` would in fact be the WRONG call now, and the old
    literal would have kept passing on a build that never reset anything if the
    string appeared anywhere else. Matching the call, not the spelling.
    """
    js = _src("puzzle/static/app.js")
    assert re.search(r"turnstile\.reset\(\s*\w+\s*\)", js), (
        "⛔⛔ nothing resets the widget — the second message of every "
        "conversation will replay a spent token and be refused")


def test_the_page_does_not_send_a_token_per_message():
    """⛔⛔⛔ THE DESIGN ERROR ALL THREE VISIBLE BUGS CAME FROM.

    A Turnstile token is SINGLE-USE. Verifying one on every message therefore
    means CHALLENGING on every message — the widget has to be re-armed after
    each turn, and "cleared" is not a state the design contains. Nate hit the
    same root cause three times in three costumes: *"any time i try to send a
    message it activates"* → *"isn't visible but it is clearly blocking me"*
    → *"it hasn't cleared yet. its either invisible or permanent."*

    ⭐⭐ TURNSTILE IS A DOOR, NOT A TICKET INSPECTOR. The page solves it once,
    exchanges it at /verify for a session pass, and every later message rides
    the pass. This pins that /say is no longer handed a token by the page.
    """
    js = re.sub(r"/\*.*?\*/", "", _src("puzzle/static/app.js"), flags=re.S)
    call = js[js.index('post("/say"'):][:160]
    assert "turnstile" not in call, (
        "⛔⛔ the page is still attaching a token to every message — that is "
        "a fresh challenge per message, which is why it never cleared")
    assert 'post("/verify"' in js, (
        "⛔⛔ nothing exchanges a solved challenge for a session pass, so the "
        "gate can never be finished with")
def test_an_unpassed_gate_holds_the_message_instead_of_spending_it():
    """⛔⛔ WHAT NATE WAS HANDED THREE TIMES: *"could not verify you are a
    person — try again."* That sentence names no thing to press, does not say a
    check is involved, and is what you BUY by posting without a pass.

    ⭐ So an unpassed gate holds the typed line, raises the modal, and sends it
    itself the moment the check clears. Making someone retype a sentence a
    captcha interrupted is the small insult that reads as the whole site being
    broken."""
    js = re.sub(r"/\*.*?\*/", "", _src("puzzle/static/app.js"), flags=re.S)
    at_listener = js.index('form.addEventListener("submit"')
    guard = js[at_listener:js.index("submit(english);", at_listener)]
    assert "!human" in guard, (
        "⛔⛔ the composer sends without knowing whether the gate was passed")
    assert "queued = english" in guard, (
        "⛔⛔ the typed message is dropped instead of held — the reader has "
        "to type it again after clearing a check they did not expect")
    assert "gateOpen()" in guard, "⛔ nothing raises the gate"
    # ⭐ and the held message must actually be sent once the pass lands
    passed = js[js.index("function tsPassed"):]
    passed = passed[:passed.index("\n  function ")]
    assert "submit(q)" in passed, (
        "⛔⛔ the held message is never sent — the reader clears the check "
        "and nothing happens, which looks exactly like the old bug")


def test_the_refusal_says_which_check_failed():
    """⛔⛔ ONE SENTENCE COVERED FOUR DIFFERENT FAULTS. Missing token, spent
    token, expired token and `invalid-input-secret` — the WRONG KEY DEPLOYED,
    which breaks the puzzle for everyone at once — all presented to the reader
    as "could not verify you are a person". The server already returns the
    reason; the client was dropping it on the floor."""
    js = _src("puzzle/static/app.js")
    assert "err.turnstile" in js, (
        "⛔ the reason is discarded in post(), so every Turnstile fault is "
        "indistinguishable from every other")
    assert "e.turnstile" in js, "⛔ the reason is never shown to the reader"


def test_a_failed_challenge_is_survivable():
    """⛔⛔ THE DEFECT THAT SHIPPED FIRST. The widget carried no error
    handling at all. Observed live: the challenge failed with
    `TurnstileError 600010`, Turnstile REMOVED ITS OWN IFRAME, and the page was
    left with a hole, no message, and a 403 on every submit forever.

    ⭐ Three things, none enough alone: the callbacks exist, each DOES
    something (an empty handler is the same bug with a comment on it), and the
    error handler returns true so the widget stays alive to be pressed again."""
    js = _src("puzzle/static/app.js")
    for hook in ('"error-callback"', '"expired-callback"', '"timeout-callback"'):
        assert hook in js, (
            "⛔⛔ %s is missing — a failed challenge leaves the bench "
            "permanently and silently dead" % hook)

    # ⛔⛔ THE FIRST VERSION OF THIS CHECK DID NOT CATCH AN EMPTY HANDLER. It
    # read a fixed 400-character window after each key, which ran on into the
    # NEXT handler — so an emptied `error-callback` passed on the strength of
    # its neighbours' bodies. A mutant survived it. Each body is now bounded by
    # its own braces, the only window that can fail for the stated reason.
    body_src = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    err = _handler_body(body_src, "error-callback")
    assert "gateSay(" in err, (
        "⛔⛔ error-callback says nothing — the exact shape that left the "
        "live page with a hole in it and no explanation")
    assert "gateOpen()" in err, (
        "⛔ a failed challenge must SHOW the gate; failing behind a parked "
        "card is the invisible-blocker bug again")
    assert "return true" in err, (
        "⛔⛔ error-callback must return true to keep the widget alive; "
        "returning false hands control to Turnstile, which removes the iframe")
def _handler_body(js: str, hook: str) -> str:
    """The braces-balanced body of one Turnstile callback."""
    start = js.index("{", js.index('"%s"' % hook))
    depth = 0
    for i in range(start, len(js)):
        if js[i] == "{":
            depth += 1
        elif js[i] == "}":
            depth -= 1
            if depth == 0:
                return js[start:i + 1]
    raise AssertionError("⛔ unbalanced braces after %r" % hook)


def test_the_challenge_is_visible():
    """⛔⛔⛔ THE REGRESSION I SHIPPED, AND THE REASON THIS TEST OUTRANKS
    ELEGANCE. The original bug was a full-width white slab flush under the send
    button. I "fixed" it with `appearance: "interaction-only"` — an INVISIBLE
    widget — and Nate got *"could not verify you are a person"* with nothing on
    screen to press.

    ⭐⭐ A BLOCKER YOU CANNOT SEE IS STRICTLY WORSE THAN A BLOCKER IN THE WRONG
    PLACE, because there is no move that clears it. The answer to bad placement
    is placement, not invisibility.

    ⛔ COMMENTS ARE STRIPPED FIRST. The retraction above is recorded inside
    app.js in the very words it forbids, and the first draft of this test fired
    on that sentence. Third time this session; the fix is always the same —
    search the CODE, never the prose explaining the code."""
    code = re.sub(r"/\*.*?\*/", "", _src("puzzle/static/app.js"), flags=re.S)
    code = re.sub(r"//[^\n]*", "", code)
    js = code
    assert "interaction-only" not in js, (
        "⛔⛔⛔ the challenge is invisible again — a reader refused by something "
        "they cannot see has no way forward at all")
    assert "invisible" not in js, "⛔⛔ an invisible widget mode is back"


def test_the_widget_does_not_draw_itself_into_the_composer():
    """⛔⛔ THE GEOMETRY THAT MADE THE BENCH UNUSABLE. `data-size="flexible"`
    stretched the widget to the full width of the composer and `data-theme=
    "auto"` followed the OPERATING SYSTEM rather than the family's own theme,
    so a WHITE slab rendered flush under the send button — measured gap: zero.
    On any viewport under ~720px tall it sat entirely below the fold, which
    meant the reader was refused by something they could not see.

    ⭐ The class is what the implicit renderer looks for. Its absence is what
    guarantees the widget cannot draw itself from the markup again — and an
    explicit render is the ONLY way `error-callback` is reachable."""
    html = _src("puzzle/static/index.html")
    body = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    assert "cf-turnstile" not in body, (
        "⛔⛔ the implicit renderer is back — the widget will draw itself into "
        "the layout, and its failure callbacks become unreachable")
    for bad in ('data-size="flexible"', 'data-theme="auto"'):
        assert bad not in body, "⛔ %s is back in the markup" % bad
    js = _src("puzzle/static/app.js")
    assert 'size: "normal"' in js, (
        "⛔ anything but `normal` risks the slab: `flexible` stretches to the "
        "full composer width, which is what made it read as part of it")
    assert 'theme: document.documentElement' in js, (
        "⛔ the widget must take the FAMILY's theme, not the operating "
        "system's — `auto` is how a white slab landed on a dark page")


def test_a_widget_that_never_draws_is_reported():
    """⛔⛔⛔ THE FAILURE NO CALLBACK COVERS, AND IT IS ONE NATE HIT.

    Measured against the real sitekey: `turnstile.render()` returns a widget id,
    reserves its 300×71 box, injects NO iframe, and fires NOTHING — not
    `error-callback`, not `timeout-callback` — for 15 seconds or more. Console
    silent, page silent. Every other guard in this file passes, because every
    one of them watches a callback, and no callback runs.

    ⭐⭐ SO THE ABSENCE ITSELF IS WATCHED. This is `fetch_missing_not_zero` in
    another costume: a thing that never arrives must be recorded as missing,
    not left to read as fine."""
    js = re.sub(r"/\*.*?\*/", "", _src("puzzle/static/app.js"), flags=re.S)
    assert "tsWatch" in js, (
        "⛔⛔⛔ nothing watches for a challenge that simply never draws")
    body = js[js.index("function tsWatch"):]
    body = body[:body.index("\n  }") + 4]
    assert "gateSay(" in body, "the watcher notices and says nothing"

    # ⛔⛔⛔ AND IT MUST NOT LOOK FOR AN IFRAME. Turnstile builds its widget in
    # a CLOSED shadow root: `querySelector` cannot pierce one and `shadowRoot`
    # is `null` for one, so an iframe check reports "absent" for a widget that
    # is drawn and interactive on screen. Two versions of this watchdog made
    # that mistake and would have shown "your network is blocking this" to
    # readers whose check was working — worse than no watchdog at all.
    whole = re.sub(r"/\*.*?\*/", "", _src("puzzle/static/app.js"), flags=re.S)
    assert 'querySelector("iframe")' not in whole, (
        "⛔⛔⛔ something is probing for an iframe again — Turnstile's widget "
        "lives in a closed shadow root and that check can only ever lie")
    assert "tsRendered()" in body, "the watcher checks nothing"
    probe = whole[whole.index("function tsRendered"):]
    probe = probe[:probe.index("\n  }") + 4]
    assert "cf-turnstile-response" in probe, (
        "⛔ the only honest light-DOM evidence that render() ran is the hidden "
        "response input Turnstile inserts — everything else it builds is "
        "behind a closed shadow root")


def test_the_challenge_is_not_inside_the_chat_window():
    """⛔⛔⛔ THREE BUILDS PUT IT THERE AND ALL THREE BROKE THE PRODUCT:
    under the send button (*"any time i try to send a message it activates"*),
    then above the composer, then invisible. Nate, finally: *"MAKE IT A
    FLOATING MODAL THAT CLEARS ONCE THE USER HAS SUCCEEDED."*

    ⭐ It now lives at body level, outside the container entirely, so nothing
    in the page can clip it, no stacking context can trap it, and no thumb
    aimed at send can land on it."""
    html = re.sub(r"<!--.*?-->", "", _src("puzzle/static/index.html"), flags=re.S)
    bench = html[html.index('class="oracle oracle-chat'):html.index("</section>")]
    assert "ts-widget" not in bench and "ts-gate" not in bench, (
        "⛔⛔⛔ the challenge is back inside the chat window")
    assert 'id="ts-gate"' in html, "the gate is gone entirely"
    assert "ts-row" not in html, "the old inline row survives"
# ── the proxy's client address ──────────────────────────────────────────────

class _Req:
    def __init__(self, headers, peer="10.0.0.1"):
        self.headers = {k.lower(): v for k, v in headers.items()}
        self.client = type("C", (), {"host": peer})()


def test_the_proxy_header_is_ignored_without_the_secret(monkeypatch):
    """⛔⛔ THE FORGERY. The modal.run URL stays publicly reachable, so anyone
    could send X-Tlon-Client-IP and mint a fresh identity per request — which is
    unlimited per-IP budget on a GPU. Unsigned, it must count for nothing."""
    from puzzle import guard as G
    monkeypatch.delenv("TLON_PROXY_SECRET", raising=False)
    ip = G.client_ip(_Req({"X-Tlon-Client-IP": "1.2.3.4",
                           "X-Forwarded-For": "9.9.9.9"}), trust_proxy=True)
    assert ip != "1.2.3.4", "⛔⛔ an unsigned client-IP header was believed"
    assert ip == "9.9.9.9"


def test_a_wrong_secret_is_ignored(monkeypatch):
    from puzzle import guard as G
    monkeypatch.setenv("TLON_PROXY_SECRET", "right")
    ip = G.client_ip(_Req({"X-Tlon-Proxy-Secret": "wrong",
                           "X-Tlon-Client-IP": "1.2.3.4",
                           "X-Forwarded-For": "9.9.9.9"}), trust_proxy=True)
    assert ip == "9.9.9.9"


def test_the_signed_header_wins(monkeypatch):
    """⭐ The whole point: behind Cloudflare the last XFF entry is CLOUDFLARE's
    egress address, so without this every reader shares one identity and the
    per-IP limit becomes a second global limit — failing OPEN."""
    from puzzle import guard as G
    monkeypatch.setenv("TLON_PROXY_SECRET", "right")
    ip = G.client_ip(_Req({"X-Tlon-Proxy-Secret": "right",
                           "X-Tlon-Client-IP": "1.2.3.4",
                           "X-Forwarded-For": "cloudflare-egress"}),
                     trust_proxy=True)
    assert ip == "1.2.3.4"


def test_nothing_is_trusted_without_trust_proxy(monkeypatch):
    """⛔ On a naked socket every one of these headers is client-supplied."""
    from puzzle import guard as G
    monkeypatch.setenv("TLON_PROXY_SECRET", "right")
    ip = G.client_ip(_Req({"X-Tlon-Proxy-Secret": "right",
                           "X-Tlon-Client-IP": "1.2.3.4"}), trust_proxy=False)
    assert ip == "10.0.0.1"


def test_the_secret_is_compared_in_constant_time():
    """⛔ A `==` leaks the secret one character at a time to anyone willing to
    time the responses, and the prize is an unlimited per-IP budget on a GPU."""
    import inspect
    from puzzle import guard as G
    assert "compare_digest" in inspect.getsource(G._const_eq)


def test_the_worker_sends_both_halves():
    """⛔ The header is useless without the secret, and the secret is useless
    without the header. A Worker that sent one would look like it worked."""
    js = (ROOT / "puzzle" / "worker" / "tlon-proxy.js").read_text(encoding="utf-8")
    assert "CF-Connecting-IP" in js, (
        "⛔⛔ the Worker does not read Cloudflare's own client-IP header — "
        "X-Forwarded-For is forgeable and CF-Connecting-IP is not")
    assert "X-Tlon-Client-IP" in js and "X-Tlon-Proxy-Secret" in js
    assert 'headers.delete("host")' in js, (
        "⛔ a stale Host makes Modal fail to route — a 404 on a URL that exists")
    assert 'redirect: "manual"' in js, (
        "⛔ a followed redirect leaks the modal.run hostname into the address bar")
