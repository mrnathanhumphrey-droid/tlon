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


def test_the_widget_is_reset_after_every_turn():
    """⛔⛔ A TURNSTILE TOKEN IS SINGLE-USE. Without a reset the first message
    works and the second replays a spent token — which presents as "it stopped
    answering me", and a one-message smoke test would never see it."""
    js = _src("puzzle/static/app.js")
    assert "turnstile.reset()" in js


def test_the_token_is_read_at_submit_not_at_load():
    """⭐ Tokens expire in minutes. A reader who opens the bench, reads the
    copy and then types would send a stale one."""
    js = _src("puzzle/static/app.js")
    at_handler = js.index('form.addEventListener("submit"')
    at_read = js.index("cf-turnstile-response")
    assert at_read > at_handler
