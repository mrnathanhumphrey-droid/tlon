"""THE PUZZLE — a public bench where you speak English and a Tlönian answers.

⛔⛔ WHAT THIS IS NOT. There is no second speaker, no drift measurement, no lag
or release reading, no weight persistence, no research pipeline and no API
backend. This is a chat app. The model perceives English and speaks Tlön; the
WINDOW holds the conversation. If a future edit reaches for any of the above,
it has wandered into the art piece or the research, which are different things.

⛔⛔ THE ORACLE'S DEPLOY HAS TWO TRAPS AND BOTH LOOK HEALTHY WHEN WRONG:
its `fly.toml` has no `[http_service]` and no public IP (Cloudflare Tunnel
only), and its entrypoint binds `--host 127.0.0.1`. Either one produces an app
whose logs say "started" and which nothing on the internet can reach. This app
binds 0.0.0.0 in `docker-entrypoint.sh` and declares `[http_service]` in
`fly.toml`, and `test_public_ingress.py` fails if either regresses.
"""
from __future__ import annotations

import hmac
import os
import pathlib
import secrets
import threading
import time
import traceback as _tb

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import guard as G
from . import logbook as LB
from . import tripwire
from . import turnstile as TS
from .speaker import (BENCH_IDLE_MINUTES, CONTEXT_TURNS, MAX_ENGLISH_CHARS,
                      Speaker, SpeakerError, translate)
from .window import TLON, YOU, ConversationStore

HERE = pathlib.Path(__file__).resolve().parent
STATIC = HERE / "static"

DB_PATH = os.environ.get("TLON_DB", str(HERE / "data" / "bench.sqlite3"))

#: ⛔⛔⛔ BESIDE THE BENCH, NEVER UNDER `static/`. One log row holds a reader's
#: English and the Tlön it became — the aligned pair `_public()` exists to keep
#: off the page. Anything under `static/` is mounted and served, so a log file
#: there would publish the answer key to a puzzle whose whole premise is that
#: nothing on the face translates anything.
#: ⭐ On Modal this lands on the bench VOLUME (`TLON_DB=/bench/bench.sqlite3`),
#: which is the only writable path that survives a five-minute scaledown.
LOG_PATH = os.environ.get("TLON_LOG_DB") or str(
    pathlib.Path(DB_PATH).with_name("log.sqlite3"))

#: ⛔ The one credential that can write a ban. Unset means the admin routes
#: answer 404 — not 403, because a 403 advertises that they are there.
ADMIN_TOKEN_ENV = "TLON_ADMIN_TOKEN"

#: ⛔ Off by default. Set it ONLY where a proxy we control terminates the
#: connection (Fly does). On a naked socket it would let any caller forge a
#: fresh address per request and walk through the per-IP limit.
TRUST_PROXY = os.environ.get("TLON_TRUST_PROXY", "0") in ("1", "true", "yes")

#: ⭐ Eager by default so the first visitor does not pay the 25s load. Set
#: TLON_PRELOAD=0 for local UI work with no GPU — the page and the translate
#: button both work without the model; only `/say` needs it.
PRELOAD = os.environ.get("TLON_PRELOAD", "1") not in ("0", "false", "no")

COOKIE = "tlon_bench"

app = FastAPI(title="Tlön", docs_url=None, redoc_url=None, openapi_url=None)
store = ConversationStore(DB_PATH)
#: ⭐ The record. ⛔ It must never be able to take the bench down: every write
#: inside it is wrapped, and `/healthz` reports the failure count so a logger
#: that has quietly stopped cannot keep answering "nothing happened".
logbook = LB.Logbook(LOG_PATH)
# ⭐ THE SKELETON'S SPEAKER, WHEN ASKED FOR. `TLON_MOCK_SPEAKER=1` serves the
# whole shape — real window, real store, real translate button, real refusals —
# with no model and no GPU, so the page can be reacted to before anything is
# spent. ⛔ `mock.enabled()` REFUSES on a deployed environment rather than
# returning False: the mock emits legal Tlön, so it would answer every visitor
# plausibly and nothing on the page would say the speaker was not the trained
# model. A silent wrong answer is worse than a loud refusal to start.
from . import mock_speaker as mock                                # noqa: E402

if mock.enabled():
    speaker = mock.MockSpeaker()
    print("⚠⚠ MOCK SPEAKER — legal Tlön from the probe generator, carrying at "
          "v1's measured %.1f%%. NOT the trained model." % (100 * mock.V1_CARRY_RATE),
          flush=True)
    # ⛔⛤ THE SKELETON RUNS ON http://, SO THE COOKIE MUST NOT BE `Secure`, AND
    # `_set_cookie`'s own comment already warned about this: "the bench then
    # forgets every turn with no error anywhere". It does — the first mock run
    # of this server created a NEW conversation on every turn, so the window was
    # always empty and the puzzle had no recurring roots at all. Nothing failed;
    # it just quietly was not a conversation.
    # ⛔ Only when TLON_HTTPS is UNSET. An explicit setting is the operator's and
    # is never overridden — and this is safe to default only because
    # `mock.enabled()` refuses to run in a deployed environment at all.
    if "TLON_HTTPS" not in os.environ:
        os.environ["TLON_HTTPS"] = "0"
        print("   ↳ TLON_HTTPS=0 for the local skeleton; without it the bench "
              "cookie is Secure, never returns over http, and every turn "
              "starts a new conversation.", flush=True)
else:
    speaker = Speaker()
# ⛔⛔ THE PUBLIC DEFAULTS ARE THE DEFAULTS, and they are deliberately tight: a
# link mailed to strangers where every request runs a 7B model. But they are not
# right for every context, and discovering that by having the limiter silently
# eat a local measurement is how the first acceptance run was voided — 22 turns
# attempted, 12 admitted, two conversations empty, and the numbers looked like a
# result rather than a rate limit.
#
# ⭐ OVERRIDABLE BY ENV, NOT BY EDITING THE CONSTANTS. A local harness raises
# them for its own run; nothing about the deployed app changes, because the
# deployed app sets none of these.
limiter = G.Guard(
    ip_turns=int(os.environ.get("TLON_IP_TURNS", G.IP_TURNS)),
    ip_window_s=int(os.environ.get("TLON_IP_WINDOW_S", G.IP_WINDOW_S)),
    global_per_day=int(os.environ.get("TLON_GLOBAL_PER_DAY",
                                      G.GLOBAL_TURNS_PER_DAY)),
)

#: ⛔⛔ THE GATE NEEDS ITS OWN, LOOSER LIMIT — AND I SHIPPED IT WITH NONE.
#: `/verify` deliberately escapes the turn limit, because a reader whose pass
#: expired must be able to re-open the door even when they have used their
#: turns for the window. That reasoning is right and the omission that came
#: with it was not: every call makes an OUTBOUND request to Cloudflare's
#: siteverify, so an unmetered endpoint is a free amplifier pointed at our own
#: siteverify quota and at this box's CPU, reachable by anyone with curl.
#:
#: ⭐ 40 per ten minutes is roughly three times what the most confused human
#: could need (one pass lasts twelve hours) and nowhere near enough to be worth
#: aiming at anything. Loose enough to never touch a real reader, tight enough
#: that the amplifier is not free.
gate_limiter = G.Guard(
    ip_turns=int(os.environ.get("TLON_VERIFY_PER_WINDOW", "40")),
    ip_window_s=int(os.environ.get("TLON_IP_WINDOW_S", G.IP_WINDOW_S)),
    #: ⛔ The daily ceiling is the GPU's, and this endpoint never reaches it.
    #: Sharing `GLOBAL_TURNS_PER_DAY` here would let captcha traffic exhaust
    #: the model's budget without a single generation ever running.
    global_per_day=int(os.environ.get("TLON_VERIFY_PER_DAY", "20000")),
)


#: ⛔ "unknown" until the startup probe answers. A field that lied by
#: defaulting to "ok" would be the placeholder bug all over again.
KEY_VERDICT = "unknown"


@app.middleware("http")
async def _never_cache_a_bench(request: Request, call_next):
    """⛔⛔⛔ ONE READER'S BENCH MUST NEVER BE SERVED TO ANOTHER.

    Every response here is per-reader: the page carries a session, and
    `/conversation` carries somebody's actual conversation. None of it said so.
    Cloudflare happens not to cache these today (`CF-Cache-Status: DYNAMIC`,
    verified live) — but that is a DEFAULT, not an instruction, and the whole
    thing sits behind a CDN plus whatever corporate or ISP proxy a reader is
    behind. One cache rule added by anyone, at any layer, and two strangers are
    sharing a conversation.

    ⭐ SAID OUT LOUD, IN MIDDLEWARE, SO NO ENDPOINT CAN FORGET IT. A per-route
    header is one new route away from being wrong, and this is the failure
    where being wrong is invisible from our side and total from the reader's.
    ⛔ `/static` is excluded: those files are identical for everybody and SHOULD
    be cached — they are the only thing here that is not somebody's.
    """
    response = await call_next(request)
    if not request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "private, no-store, max-age=0"
        response.headers["Vary"] = "Cookie"
    return response


#: The routes this app actually declares. ⭐ Anything else that 404s is somebody
#: scanning us, which is worth seeing as a shape (`/wp-login.php`, `/.env`) even
#: though it is never actionable on its own.
_OURS = ("/", "/healthz", "/new", "/say", "/verify", "/reveal", "/conversation",
         "/admin/ban", "/admin/unban", "/admin/snapshot", "/admin/stats")


@app.middleware("http")
async def _write_it_down(request: Request, call_next):
    """⛔⛔ EVERY UNHANDLED EXCEPTION, AND WHERE IT HAPPENED.

    Before this, an error's only trace was a stack printed to Modal's stdout,
    which is discarded when the container scales down five minutes later. A
    reader mailing "it broke" had nothing to quote and we had nothing to look
    up — so the bug either reproduced on demand or did not exist.

    ⭐ THE READER GETS A REQUEST ID. It is in the response header and in the
    log row, which turns "it broke yesterday" into one indexed lookup.

    ⛔ LOGGING MUST NOT BE ABLE TO FAIL THE REQUEST. Every call in here is
    wrapped; the `Logbook` swallows its own errors and counts them, and this
    catches anything left. A logger that 500s the app it watches is worse than
    no logger.
    """
    request.state.request_id = secrets.token_hex(8)
    if request.url.path.startswith(("/static", "/assets")):
        return await call_next(request)

    started = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:                                      # noqa: BLE001
        _log_failure(request, exc, time.time() - started)
        # ⭐ An honest line, and the id to quote. ⛔ NOT the exception text:
        # that is for the log, not for a stranger's screen.
        return JSONResponse(
            {"error": "Something broke on our side. It has been written down.",
             "request_id": request.state.request_id},
            status_code=500,
            headers={"X-Request-Id": request.state.request_id})

    try:
        response.headers["X-Request-Id"] = request.state.request_id
        if response.status_code >= 500:
            _log_failure(request, None, time.time() - started,
                         status=response.status_code)
        elif response.status_code == 404 and request.url.path not in _OURS:
            logbook.record_event(kind="probe", **_who(request),
                                 detail="%s %s" % (request.method,
                                                   request.url.path[:200]))
    except Exception:                                             # noqa: BLE001
        pass
    return response


def _who(request) -> dict:
    """⛔ NEVER RAISES, AND NEVER RETURNS AN ADDRESS. The log's only identity is
    the HMAC; the address it was made from does not leave this function."""
    try:
        ip, trusted = G.client_ip_ex(request, trust_proxy=TRUST_PROXY)
        return {"reader": LB.reader_id(ip), "ip_trusted": trusted}
    except Exception:                                             # noqa: BLE001
        return {"reader": None, "ip_trusted": None}


def _log_failure(request, exc, seconds: float, *, status: int = 500) -> None:
    try:
        logbook.record_error(
            kind=type(exc).__name__ if exc is not None else "http",
            detail=str(exc) if exc is not None else "status %d" % status,
            traceback=_tb.format_exc() if exc is not None else None,
            method=request.method, route=request.url.path, status=status,
            seconds=seconds,
            request_id=getattr(request.state, "request_id", None),
            **_who(request))
    except Exception:                                             # noqa: BLE001
        pass
    # ⭐ STILL PRINTED. Modal's stdout is where an operator looks first and it
    # is live; the log is where they look second and it is durable.
    print("⛔ %s %s -> %s (%s)" % (request.method, request.url.path, status,
                                   exc if exc is not None else "no exception"),
          flush=True)
    if exc is not None:
        _tb.print_exc()


@app.on_event("startup")
def _startup():
    # ⛔⛔ FIRST, AND IT MAY KILL THE BOOT. A deployment whose Turnstile
    # secret was never set would serve a public GPU endpoint with nothing
    # but the rate limit in front of it, and report healthy while doing so.
    # Unlike the speaker below -- where dying would cost a restart loop and
    # the model can load late -- there is no safe degraded mode here.
    TS.preflight()
    # ⛔⛔⛔ AND THEN ASK WHETHER THE KEY IS A KEY. `preflight` only checks that
    # a secret EXISTS; the deployed value was a 30-character placeholder and the
    # app came up reporting perfectly healthy while refusing every reader with
    # "turnstile unreachable" for days. Presence is not validity.
    # ⭐ Reported rather than fatal: the verdict needs a network round-trip, and
    # killing the boot on a bad Cloudflare minute would turn a blip into an
    # outage. `/healthz` carries it too, so it is checkable from outside.
    global KEY_VERDICT
    KEY_VERDICT = TS.key_verdict()
    if KEY_VERDICT == "bad-key":
        print("⛔⛔⛔ TURNSTILE_SECRET_KEY IS NOT A VALID KEY — cloudflare says "
              "invalid-input-secret. EVERY reader will be refused. Set the real "
              "secret from the Turnstile dashboard.", flush=True)
    if PRELOAD:
        # ⛔⛔ IN A THREAD, BECAUSE A BLOCKING STARTUP IS A BOOT LOOP. FastAPI
        # does not accept a single connection until this handler returns, and
        # on a cold machine `load()` first pulls ~14 GB of base weights onto
        # the volume. Fly caps an http_service check's grace period at 60
        # seconds — it says so at deploy time and silently lowers the 180 this
        # config asks for — so a synchronous load fails the check, the machine
        # is restarted, and the download begins again. The app would never come
        # up, and every log line would say only "health check failed".
        #
        # ⭐ SERVING BEFORE READY IS CORRECT HERE. The page, the copy and the
        # translate button are all model-free, so the bench is genuinely usable
        # while the card warms. `/healthz` already reports `speaker_loaded`,
        # which is the honest signal; a reader who asks early waits on
        # `load()`'s own lock rather than getting a wrong answer, and
        # `guard.MAX_QUEUED` bounds how many may wait.
        def _warm():
            try:
                speaker.load()
            except Exception as exc:          # noqa: BLE001
                # ⛔ DO NOT DIE HERE. A machine that exits on startup is
                # restarted forever by the platform and the reason scrolls
                # past. Come up, serve the copy, and let /healthz report the
                # speaker as down.
                print("⛔ speaker did not load at startup: %s" % exc, flush=True)

        threading.Thread(target=_warm, name="speaker-warm", daemon=True).start()


# ── the door ────────────────────────────────────────────────────────────────

class Say(BaseModel):
    english: str = Field(min_length=1, max_length=MAX_ENGLISH_CHARS)
    #: ⛔⛔ THE TURNSTILE TOKEN, AND IT IS CHECKED ON THIS REQUEST.
    #: Verifying it anywhere else -- in the browser, in a separate call the
    #: client may simply not make -- guards nothing: `/say` is the endpoint
    #: that runs the 7B, so it is the endpoint that has to be satisfied.
    #: Optional in the SCHEMA so a request without one gets the app's own
    #: refusal rather than a 422 the page cannot explain.
    #: ⭐ The PAGE normally leaves this empty and rides the pass cookie issued
    #: by `/verify`; it stays here so a cookie-less client (a script, the smoke
    #: test) can still present a token inline and be let through.
    turnstile: str = ""


class Verify(BaseModel):
    """⭐ The gate's only input. One token, exchanged for a session pass."""
    turnstile: str = ""


class Reveal(BaseModel):
    turn: int = Field(ge=0)
    #: ⛔⛔ `tlon` ONLY. WE NEVER TRANSLATE THE USER. The reader's own line has
    #: nothing to reveal — they wrote it — and handing back its English would
    #: be an aligned pair, which is the parallel-text leak by request instead of
    #: by accident. Enforced HERE and not only by leaving the button off the
    #: page: a UI-only rule is one fetch away from being no rule.
    role: str = Field(pattern="^tlon$")


def _conversation(request: Request, *, expire: bool = True) -> str | None:
    """The caller's bench, or None if there isn't a live one.

    ⛔ THE IDLE TIME-OUT LIVES HERE SO IT CANNOT BE FORGOTTEN AT ONE DOOR. A
    bench gone quiet longer than `BENCH_IDLE_MINUTES` is over: the next thing
    said starts a new moment. `expire=False` is for reads that should still be
    able to show a cold bench rather than blanking it under the reader.
    """
    cid = request.cookies.get(COOKIE)
    if not cid or not store.exists(cid):
        return None
    if expire:
        idle = store.idle_seconds(cid)
        if idle is not None and idle > BENCH_IDLE_MINUTES * 60:
            return None
    return cid


def _set_cookie(response: Response, cid: str) -> None:
    response.set_cookie(
        COOKIE, cid, max_age=60 * 60 * 24 * 30, httponly=True, samesite="lax",
        # ⛔ Secure only where there IS TLS. Setting it unconditionally makes
        # the cookie silently vanish on a local http:// run, and the bench then
        # forgets every turn with no error anywhere.
        secure=os.environ.get("TLON_HTTPS", "1") not in ("0", "false", "no"))


#: ⛔ The page is RENDERED, not sent as a file, for exactly one reason:
#: the Turnstile SITE key has to reach the markup. It is public by design
#: -- it sits in the HTML of every site that uses Turnstile -- so this is
#: a substitution, not a secret. The SECRET never leaves the server.
#: ⭐ Read once at import. The file does not change under a running
#: machine, and re-reading it per request would put a disk hit in front
#: of every visitor for no gain.
_INDEX = (STATIC / "index.html").read_text(encoding="utf-8")


#: ⛔⛔⛔ THE BENCH'S ORIGIN IS NOW TRUSTED BY THE AUTH API, AND THAT CHANGED
#: WHAT AN XSS HERE IS WORTH.
#:
#: Until 2026-09-25 an injection on this page defaced a puzzle. Then
#: `tlon.resolveresearcher.com` was added to the API's CORS allowlist — with
#: `allow_credentials=True`, because the top bar has to read /v1/auth/me to
#: know whether to say "account" — and the blast radius moved: script running
#: on this origin can now make CREDENTIALED calls to api.resolveresearcher.com
#: as whoever is reading, and read the replies.
#:
#: ⭐ CSRF still blocks the writes: the token lives in each origin's own
#: localStorage and this origin has none, so state-changing calls fail. What
#: an injection WOULD get is read access to the victim's account through GET
#: endpoints. That is not account takeover and it is not nothing.
#:
#: ⛔ This page renders output from a language model that any stranger can
#: steer, which is the least trustworthy string in the building. `app.js` is
#: careful — every surface goes through `textContent`, never innerHTML — but
#: "we were careful" is not a control, and it is now the only thing standing
#: between a prompt and somebody's account data. The CSP is the control.
#:
#: ⭐ NONCE, NOT 'unsafe-inline'. Two inline scripts are load-bearing and
#: cannot move: the theme stamp must run before first paint or a light-mode
#: reader gets a dark flash, and the Turnstile onload handshake must be
#: registered before api.js arrives. A nonce lets exactly those two run and
#: nothing else — 'unsafe-inline' would permit the injected script too and
#: make the whole header decorative.
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'nonce-{nonce}' https://challenges.cloudflare.com "
    "https://resolveresearcher.com; "
    # ⛔ Styles keep 'unsafe-inline': apex's shared chrome sets style
    # attributes directly (and so does the gate's scroll lock), and there is no
    # nonce path for a style ATTRIBUTE. A style injection cannot exfiltrate a
    # session, so this is the cheap half to concede.
    "style-src 'self' 'unsafe-inline' https://resolveresearcher.com "
    "https://fonts.googleapis.com https://unpkg.com; "
    "font-src 'self' https://fonts.gstatic.com https://unpkg.com; "
    "img-src 'self' data: https://resolveresearcher.com; "
    # ⛔⛔ THE LINE THAT ACTUALLY MATTERS, AND THE ONE I FIRST GOT WRONG.
    # I left api.resolveresearcher.com OUT of this, reasoning that "nothing
    # served by this app calls the auth API". That is false in the way that
    # matters: apex's `theme.js` is FETCHED from resolveresearcher.com but
    # EXECUTES in this document, so its /v1/auth/me call is a connection from
    # THIS origin and CSP judges it here. Omitting it would have silently
    # broken the log-in this page had just been fixed to show — the same bug,
    # re-inflicted by its own mitigation.
    # ⭐ What this still buys: an injection can reach the auth API (which the
    # bar needs) but CANNOT post the result to an attacker's collector,
    # because that host is not in this list. Exfiltration is the step worth
    # blocking.
    "connect-src 'self' https://api.resolveresearcher.com "
    "https://challenges.cloudflare.com; "
    "frame-src https://challenges.cloudflare.com; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'self'; "
    "object-src 'none'"
)


@app.get("/")
def index():
    # ⛔ When no key is configured the placeholder resolves to an empty
    # string and `app.js` renders no widget -- which is correct locally,
    # where `turnstile.required()` is also false. The two agree because
    # both read the same absence, not because they were kept in step.
    # ⛔ A FRESH NONCE PER RESPONSE, OR IT IS NOT A NONCE. A fixed value would
    # be readable in the page source and an injection could simply quote it,
    # which is a CSP that costs a header and stops nothing.
    nonce = secrets.token_urlsafe(16)
    html = (_INDEX
            .replace("{{TURNSTILE_SITEKEY}}", TS.SITE_KEY)
            .replace("{{CSP_NONCE}}", nonce))
    return HTMLResponse(html, headers={
        "Content-Security-Policy": _CSP.format(nonce=nonce),
        # ⛔ The page is never framed, and the CSP's frame-ancestors says so —
        # this is the header older browsers actually obey.
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    })


@app.get("/healthz")
def healthz():
    # ⛔ `mock` IS REPORTED, ALWAYS. A skeleton that looks identical to the real
    # thing is exactly what a health check is for: without this the only way to
    # tell a mocked bench from a trained one is to read the Tlön, and both are
    # legal. It is a bare boolean on purpose — anything that has to be parsed
    # to be understood will eventually be misread.
    return {"ok": True, "speaker_loaded": speaker.ready,
            # ⛔⛔ THE FIELD THAT WOULD HAVE SAVED DAYS. A health
            # check that says "ok" while every reader is refused
            # is the silent-success shape this repo keeps hitting.
            "turnstile_key": KEY_VERDICT,
            # ⛔⛔ `proxy_unsigned > 0` MEANS THE CLIENT ADDRESS IS NOT
            # TRUSTWORTHY: every reader is being seen as Cloudflare's egress
            # IP, so the per-IP limit is a second global limit and the session
            # pass is bound to nobody. Reported because both failures look
            # exactly like a healthy app from every other angle.
            "proxy_signed": G.PROXY_TRUST["signed"],
            "proxy_unsigned": G.PROXY_TRUST["unsigned"],
            "mock": bool(getattr(speaker, "is_mock", False)),
            # ⛔⛔ THE PUBLIC HALF ONLY — "is the log working", never "did your
            # probe trip a wire". A public count of flagged turns would let an
            # attacker binary-search the tripwire: send a line, refresh this,
            # read the answer. The rest is behind `/admin/stats`.
            "log": logbook.stats(),
            "load_seconds": speaker.load_seconds, **limiter.stats()}


@app.post("/new")
def new_conversation(response: Response):
    """Start a fresh bench. ⭐ Free — it runs no model, so it is not rate
    limited; a reader who wants to start over should never be told to wait."""
    cid = store.new_conversation()
    out = JSONResponse({"conversation_id": cid, "messages": []})
    _set_cookie(out, cid)
    return out


@app.get("/conversation")
def conversation(request: Request):
    """The bench as it stands. ⛔ Sends NO gloss and NO literary — see /reveal.

    ⭐⭐ IT ALSO ANSWERS "MUST I SHOW THE GATE?". The pass cookie is httponly,
    so the page CANNOT look at it — which is the point, but it means the only
    honest source for that answer is the server. Without this the page would
    have to guess, and a page that guesses wrong shows a human a challenge they
    already passed. `true` also covers "Turnstile is switched off", because
    that is the same answer to the only question being asked.
    """
    ip = G.client_ip(request, trust_proxy=TRUST_PROXY)
    human = TS.has_pass(request, ip)
    cid = _conversation(request)
    if cid is None:
        return {"conversation_id": None, "messages": [], "human": human}
    return {"conversation_id": cid, "human": human,
            "messages": [_public(r) for r in store.history(cid)]}


@app.post("/say")
def say(body: Say, request: Request, response: Response):
    """One turn: your English becomes Tlön, and that provokes the reply."""
    ip, trusted = G.client_ip_ex(request, trust_proxy=TRUST_PROXY)
    reader = LB.reader_id(ip)
    rid = getattr(request.state, "request_id", None)
    # ⭐ SCANNED BEFORE ANY REFUSAL, NOT AFTER THE MODEL. An injection attempt
    # that happens to arrive on the reader's thirteenth turn is refused by the
    # rate limit — and if the scan lived after that, tripping the limit would be
    # a way to attack the bench unlogged.
    flags, severity = tripwire.scan(body.english)

    # ⛔⛔⛔ THE BAN LIST IS CONSULTED ONLY FOR AN ADDRESS WE CAN VOUCH FOR.
    # On an unsigned request `ip` is Cloudflare's egress address — the same
    # string for every reader on earth — so one ban would refuse the whole
    # internet, and it would look like the bench crashing rather than like a
    # ban. `logbook.ban()` guards the write; this guards the read.
    if trusted and logbook.is_banned(reader):
        logbook.record_event(kind="ban.blocked", reader=reader, ip_trusted=True,
                             detail=tripwire.flagline(flags))
        return JSONResponse({"error": "This bench is closed to you."},
                            status_code=403)

    try:
        limiter.check(ip)
    except G.Refused as exc:
        _note_refusal("rate", exc.message, reader, trusted, body.english,
                      flags, severity, rid)
        return _refused(exc)

    # ⛔⛔ AFTER THE RATE LIMIT, BEFORE THE MODEL. The order is
    # deliberate: the limiter is a dictionary lookup and Turnstile is a
    # network round-trip, so an IP that is already hammering is refused
    # without also making Cloudflare do work for it. Both come before
    # anything that touches the card.
    #
    # ⛔⛔⛔ A READER WHO HAS ALREADY PASSED IS NOT ASKED AGAIN. This used to
    # verify a token on EVERY message, and because a Turnstile token is
    # single-use that meant re-challenging a person between one sentence and
    # the next — the widget could never clear, because clearing it was not a
    # state the design had. Turnstile is a DOOR, and `has_pass` is the server
    # remembering that this reader already came through it.
    # ⭐ The inline-token path below is kept so a client with no cookie jar —
    # a script, a curl, the smoke test — still works exactly as before. The
    # endpoint is not weakened; it gained a second way in, not a way around.
    earned_pass = False
    if not TS.has_pass(request, ip):
        ok, why = TS.verify(body.turnstile, ip)
        if not ok:
            # ⭐ 403, not 400: this is "prove you are a person", and the page
            # opens its gate on it. ⛔ The REASON is returned because
            # `invalid-input-secret` (the wrong key was deployed) is otherwise
            # indistinguishable from a reader failing the challenge, and the
            # first would look like a broken puzzle to everyone at once.
            # ⭐⭐ AND IT IS THE REASON THAT GOES IN THE LOG. A sudden run of
            # `invalid-input-secret` is the placeholder-key outage — every
            # reader refused at once — which took days to spot when the only
            # evidence was one person saying it did not work.
            _note_refusal("turnstile", why, reader, trusted, body.english,
                          flags, severity, rid)
            return JSONResponse({"error": "could not verify you are a "
                                          "person — try again",
                                 "turnstile": why}, status_code=403)
        earned_pass = True

    english = body.english.strip()
    if not english:
        return JSONResponse({"error": "say something first"}, status_code=400)

    cid = _conversation(request)
    fresh = cid is None
    if fresh:
        cid = store.new_conversation()

    # ⭐⭐ THE WINDOW GOES TO THE MODEL. Without it no root ever recurs across
    # turns and there is nothing for a reader to decode — the puzzle IS the
    # language, and a language is solvable only because it repeats.
    write_pairs, provoke_pairs = store.threads(cid, max_turns=CONTEXT_TURNS)
    try:
        with limiter.slot():
            result = speaker.turn(english, write_pairs, provoke_pairs)
    except G.Refused as exc:
        _note_refusal("busy", exc.message, reader, trusted, body.english,
                      flags, severity, rid)
        return _refused(exc)
    except SpeakerError as exc:
        # ⛔ THE ONE ERROR A READER ACTUALLY MEETS, and until now it was
        # returned and forgotten. A model that has started refusing everything
        # looks, from outside, exactly like a model nobody is using.
        logbook.record_error(kind="SpeakerError", detail=str(exc),
                             reader=reader, ip_trusted=trusted, route="/say",
                             method="POST", status=503, request_id=rid,
                             traceback=_tb.format_exc())
        return JSONResponse({"error": str(exc)}, status_code=503)

    turn_no = store.next_turn(cid)
    rows = []
    for role, row in ((YOU, result["you"]), (TLON, result["tlon"])):
        if not row:
            continue
        store.append(cid, turn_no, role, english=row.get("english"),
                     surface=row.get("surface"), gloss=row.get("gloss"),
                     literary=row.get("literary"), refused=row.get("refused"))
        rows.append(_public({"turn": turn_no, "role": role, **row}))

    # ⛔ WHAT WAS SAID AND WHAT CAME BACK — which is what an abuse report needs.
    # ⛔⛔ `_tlon["surface"]` IS THE REPLY, AND `result["you"]["surface"]` IS
    # DELIBERATELY NOT WRITTEN. That one is the reader's own line rendered into
    # Tlön: the aligned pair `_public()` exists to withhold. The store keeps it
    # because the translate button needs it; the log has no use for it, so the
    # log does not get a copy.
    _tlon = result.get("tlon") or {}
    logbook.record_turn(
        reader=reader, ip_trusted=trusted, request_id=rid,
        conversation_id=cid, turn=turn_no, english=english,
        surface=_tlon.get("surface"),
        refused=result["you"].get("refused") or _tlon.get("refused"),
        seconds=result.get("seconds"), flags=tripwire.flagline(flags),
        severity=severity)

    out = JSONResponse({"conversation_id": cid, "messages": rows,
                        "seconds": result["seconds"]})
    if fresh:
        _set_cookie(out, cid)
    # ⭐ A token spent inline earns the same pass the gate does, so a reader
    # who arrives without a cookie is challenged once and not once per turn.
    if earned_pass:
        _set_pass(out, ip)
    return out


def _set_pass(response: Response, ip: str) -> None:
    """⛔ httponly: nothing in the page reads this, and a script that cannot
    read it cannot carry it anywhere else."""
    response.set_cookie(
        TS.PASS_COOKIE, TS.issue_pass(ip),
        max_age=TS.PASS_HOURS * 3600, httponly=True, samesite="lax",
        secure=os.environ.get("TLON_HTTPS", "1") not in ("0", "false", "no"))


@app.post("/verify")
def verify(body: Verify, request: Request):
    """⭐⭐ THE DOOR, AND IT IS OPENED ONCE.

    The page solves the challenge, posts the token here, and this hands back a
    signed pass. Every later message rides that pass, so the widget clears and
    stays cleared — which is the whole point, and what three attempts at fixing
    the *placement* of a per-message challenge could never have achieved.

    ⛔ NOT RATE LIMITED, DELIBERATELY. It runs no model and touches no GPU, and
    metering it would mean a reader who hit the turn limit could not re-open the
    door when their pass expired — locking out precisely the people who have
    been using it properly. The compute ceiling is still `guard.py`'s job.
    """
    ip, trusted = G.client_ip_ex(request, trust_proxy=TRUST_PROXY)
    reader = LB.reader_id(ip)
    # ⛔ THE DOOR IS SHUT TOO. Leaving this out would let a banned reader keep
    # a fresh pass in hand — harmless while `/say` refuses them, and exactly the
    # kind of "the other door still worked" gap that outlives the reason for it.
    if trusted and logbook.is_banned(reader):
        logbook.record_event(kind="ban.blocked", reader=reader, ip_trusted=True,
                             detail="/verify")
        return JSONResponse({"error": "This bench is closed to you."},
                            status_code=403)
    try:
        gate_limiter.check(ip)
    except G.Refused as exc:
        logbook.record_event(kind="refused.gate", reader=reader,
                             ip_trusted=trusted, detail=exc.message)
        return _refused(exc)
    if TS.has_pass(request, ip):
        return JSONResponse({"ok": True, "already": True})
    ok, why = TS.verify(body.turnstile, ip)
    if not ok:
        logbook.record_event(kind="refused.turnstile", reader=reader,
                             ip_trusted=trusted, detail=why)
        return JSONResponse({"ok": False, "error": "could not verify you are "
                                                   "a person — try again",
                             "turnstile": why}, status_code=403)
    out = JSONResponse({"ok": True})
    _set_pass(out, ip)
    return out


@app.post("/reveal")
def reveal(body: Reveal, request: Request):
    """The translate button. Pure function, no model, no rate limit.

    ⭐⭐ IT READS FROM THE STORE, NOT FROM THE REQUEST BODY. A reader can only
    translate lines that are already on their own bench — the endpoint is not a
    general-purpose parser for arbitrary text, and the translation of a line you
    have not been given cannot be fished out of it.
    """
    cid = _conversation(request)
    if cid is None:
        return JSONResponse({"error": "no conversation"}, status_code=404)
    for row in store.history(cid):
        if row["turn"] == body.turn and row["role"] == body.role:
            if not row["surface"]:
                return JSONResponse({"error": "nothing to translate"},
                                    status_code=404)
            # ⭐ Stored at write time, recomputed here only if absent. Both paths
            # are the same pure function over the same frozen lexicon.
            if row["gloss"] and row["literary"]:
                return {"gloss": row["gloss"], "literary": row["literary"]}
            return translate(row["surface"])
    return JSONResponse({"error": "no such line"}, status_code=404)


# ── the operator's door ─────────────────────────────────────────────────────
#
# ⛔⛔⛔ IT WRITES, IT DOES NOT READ. There is no endpoint here that returns a
# turn, a line of English or a Tlön surface, and there must never be one: this
# app is reachable by anyone and its log is the puzzle's answer key. Reading is
# done OFFLINE — `/admin/snapshot` settles a copy onto the volume, `modal volume
# get` carries it home, `tools/bench_log.py` reads it there. That split is the
# whole security design: the dangerous half never has a URL.
#
# ⛔ `/admin/stats` is the one read, and it returns COUNTS. Counts cannot
# translate anything.

class Ban(BaseModel):
    reader: str = Field(min_length=1, max_length=64)
    #: None means no expiry. ⭐ A dated ban is the better default in practice —
    #: addresses are reassigned, and a permanent ban on a home connection
    #: eventually lands on somebody who did nothing.
    days: int | None = Field(default=None, ge=1, le=3650)
    note: str = Field(default="", max_length=500)
    #: ⛔ Overrides the untrusted-address refusal. It has to be typed.
    force: bool = False


class Unban(BaseModel):
    reader: str = Field(min_length=1, max_length=64)


def _admin(request: Request) -> bool:
    """⛔ CONSTANT-TIME, and 404 rather than 403 at every call site. A 403 says
    "this endpoint exists and you are close"; a 404 says nothing at all."""
    token = os.environ.get(ADMIN_TOKEN_ENV, "")
    if not token:
        return False
    header = request.headers.get("authorization", "")
    offered = header[7:] if header[:7].lower() == "bearer " else ""
    return hmac.compare_digest(offered, token)


def _not_found() -> JSONResponse:
    return JSONResponse({"detail": "Not Found"}, status_code=404)


def _admin_denied(request: Request) -> JSONResponse:
    # ⭐ Recorded. Somebody guessing at the admin door is exactly the kind of
    # thing that is invisible until it worked.
    logbook.record_event(kind="admin.denied", detail=request.url.path,
                         **_who(request))
    return _not_found()


@app.post("/admin/ban")
def admin_ban(body: Ban, request: Request):
    if not _admin(request):
        return _admin_denied(request)
    result = logbook.ban(body.reader, days=body.days, note=body.note,
                         force=body.force)
    if not result.get("ok"):
        # ⭐ 409, and the body says WHY. "untrusted address" is the refusal an
        # operator must be able to read and understand in one line, because the
        # alternative to understanding it is forcing it.
        return JSONResponse(result, status_code=409)
    return result


@app.post("/admin/unban")
def admin_unban(body: Unban, request: Request):
    if not _admin(request):
        return _admin_denied(request)
    return logbook.unban(body.reader)


@app.post("/admin/snapshot")
def admin_snapshot(request: Request):
    """⛔ `modal volume get` ON THE LIVE FILE CAN TEAR — it is in WAL mode and
    being written to. This settles a single consistent copy beside it first."""
    if not _admin(request):
        return _admin_denied(request)
    result = logbook.snapshot()
    return result if result.get("ok") else JSONResponse(result, status_code=500)


@app.get("/admin/stats")
def admin_stats(request: Request):
    if not _admin(request):
        return _admin_denied(request)
    return logbook.stats(full=True)


# ── helpers ─────────────────────────────────────────────────────────────────

def _public(row: dict) -> dict:
    """⛔⛔⛔ ONE ROW NEVER CARRIES BOTH AN ENGLISH LINE AND ITS TLÖN. THAT PAIR
    IS THE WHOLE LEAK, AND FOR MONTHS THIS FUNCTION SHIPPED IT.

    ⛔⛤ THE GUARD WATCHED THE WRONG FIELD. Everything here — the docstring that
    used to say "no English leaves this function", the leak tests, the reply
    template's three warnings — was aimed at the `english` KEY. Meanwhile the
    function returned `surface` for BOTH roles, and the surface of the READER'S
    OWN TURN is their sentence rendered into Tlön. They typed the English. They
    were shown the Tlön. **That is an aligned pair on every single turn**, built
    out of a field nobody was guarding because it looked like Tlön.
    Nate, seeing it on the page: *"IF YOU TELL ME WHAT I SAID — THAT IS A
    TRANSLATION."* He is right, and it had been live the entire time.

    ⭐⭐ THE RULE IS NOW STATED IN THE SHAPE THAT CAN ACTUALLY BE CHECKED:
        the reader's turn  -> their OWN English, and NO Tlön
        the Tlönian's turn -> Tlön, and NO English
    Neither row is a pair, so no accumulation of rows is a word-list. Returning
    a reader their own sentence tells them nothing they did not type; it is the
    PAIRING that was ever the secret, not the English.

    ⛔ `gloss`, `literary` and `let_go` still never appear. `let_go` listed, in
    English, the nouns the language could not carry — "it let go — toast" —
    beside a Tlön line, every turn, unasked: the same leak wearing a friendlier
    name.
    """
    out = {"turn": row["turn"], "role": row["role"],
           "refused": row.get("refused")}
    if row["role"] == YOU:
        # ⛔⛔ NO `surface` HERE. EVER. The reader knows what they typed, so the
        # Tlön of it is the other half of an answer key they are holding.
        out["english"] = row.get("english")
    else:
        out["surface"] = row.get("surface")
    return out


def _note_refusal(kind: str, message: str, reader: str, trusted: bool,
                  english: str, flags, severity: int, rid) -> None:
    """A turn that never ran, written down anyway.

    ⛔⛔ A FLAGGED LINE IS RECORDED IN FULL EVEN WHEN IT WAS REFUSED. Otherwise
    the cheapest way to attack this bench unobserved is to attack it past the
    rate limit — the log would hold twelve innocent turns and nothing else.
    ⭐ An UNflagged refusal gets a one-line event instead: there are thousands of
    those and they are a rate, not a story.
    """
    try:
        if severity >= tripwire.INJECTION:
            logbook.record_turn(reader=reader, ip_trusted=trusted,
                                request_id=rid, english=english,
                                refused="refused:" + kind,
                                flags=tripwire.flagline(flags),
                                severity=severity)
        else:
            logbook.record_event(kind="refused." + kind, reader=reader,
                                 ip_trusted=trusted, detail=message)
    except Exception:                                             # noqa: BLE001
        pass


def _refused(exc: G.Refused) -> JSONResponse:
    headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after else None
    return JSONResponse({"error": exc.message}, status_code=exc.status,
                        headers=headers)


# ⛔ Mounted LAST. A StaticFiles mount at "/" would shadow every route declared
# after it, and the failure mode is a 404 on an endpoint that is plainly there.
#
# ⛔⛤ AND THE DIRECTORY IS ENSURED, BECAUSE `StaticFiles` RAISES ON A MISSING
# ONE AND TOOK THE WHOLE APP DOWN. `puzzle/static/assets/` held a stale fork of
# apex's theme.css/theme.js until those were deleted in favour of apex's own
# copies; what remains is `videos/`, which holds only placeholders and so is
# EMPTY. Git does not track an empty directory and neither Modal's
# `add_local_dir` nor a Docker COPY ships one — so the path existed on the
# laptop and nowhere else, and the container crashed at IMPORT time, before a
# single line of the app ran. The logs said only
# `RuntimeError: Directory '/app/puzzle/static/assets' does not exist`.
# ⭐ Ensuring it is right rather than conditional: the mount should exist even
# when there is nothing in it yet, so dropping a video in needs no code change.
(STATIC / "assets").mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=STATIC / "assets"), name="assets")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
