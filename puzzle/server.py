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

import os
import pathlib

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import guard as G
from .speaker import (BENCH_IDLE_MINUTES, CONTEXT_TURNS, MAX_ENGLISH_CHARS,
                      Speaker, SpeakerError, translate)
from .window import TLON, YOU, ConversationStore

HERE = pathlib.Path(__file__).resolve().parent
STATIC = HERE / "static"

DB_PATH = os.environ.get("TLON_DB", str(HERE / "data" / "bench.sqlite3"))

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


@app.on_event("startup")
def _startup():
    if PRELOAD:
        try:
            speaker.load()
        except Exception as exc:              # noqa: BLE001
            # ⛔ DO NOT DIE HERE. A machine that exits on startup is restarted
            # forever by the platform and the reason scrolls past. Come up,
            # serve the copy, and let /healthz report the speaker as down.
            print("⛔ speaker did not load at startup: %s" % exc, flush=True)


# ── the door ────────────────────────────────────────────────────────────────

class Say(BaseModel):
    english: str = Field(min_length=1, max_length=MAX_ENGLISH_CHARS)


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


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/healthz")
def healthz():
    # ⛔ `mock` IS REPORTED, ALWAYS. A skeleton that looks identical to the real
    # thing is exactly what a health check is for: without this the only way to
    # tell a mocked bench from a trained one is to read the Tlön, and both are
    # legal. It is a bare boolean on purpose — anything that has to be parsed
    # to be understood will eventually be misread.
    return {"ok": True, "speaker_loaded": speaker.ready,
            "mock": bool(getattr(speaker, "is_mock", False)),
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
    """The bench as it stands. ⛔ Sends NO gloss and NO literary — see /reveal."""
    cid = _conversation(request)
    if cid is None:
        return {"conversation_id": None, "messages": []}
    return {"conversation_id": cid,
            "messages": [_public(r) for r in store.history(cid)]}


@app.post("/say")
def say(body: Say, request: Request, response: Response):
    """One turn: your English becomes Tlön, and that provokes the reply."""
    ip = G.client_ip(request, trust_proxy=TRUST_PROXY)
    try:
        limiter.check(ip)
    except G.Refused as exc:
        return _refused(exc)

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
        return _refused(exc)
    except SpeakerError as exc:
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

    out = JSONResponse({"conversation_id": cid, "messages": rows,
                        "seconds": result["seconds"]})
    if fresh:
        _set_cookie(out, cid)
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


# ── helpers ─────────────────────────────────────────────────────────────────

def _public(row: dict) -> dict:
    """⛔⛔ THE PUZZLE'S ONE LOAD-BEARING RULE: NO ENGLISH LEAVES THIS FUNCTION.

    `gloss` and `literary` are the obvious half. `english` is the half that
    shipped anyway — the reader's own sentence, returned beside the Tlön it
    became. That is a PARALLEL TEXT: one aligned pair per turn, handed over
    free, and a handful of turns is a word-list. It makes the onset redundant
    and the translate button decorative, which is the difference between a
    puzzle and a chatbot with subtitles.

    ⛔ `let_go` WENT THE SAME WAY. It listed, in English, the nouns the language
    could not carry — "it let go — toast" — on every turn, unasked. Honest about
    the coverage edge and still a free English word beside a Tlön line, which is
    the same leak wearing a different name.

    ⛔ The store still keeps the English — it is the reader's own input and the
    server's record. This function is the WIRE, and the wire carries Tlön.
    """
    return {"turn": row["turn"], "role": row["role"],
            "surface": row.get("surface"),
            "refused": row.get("refused")}


def _refused(exc: G.Refused) -> JSONResponse:
    headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after else None
    return JSONResponse({"error": exc.message}, status_code=exc.status,
                        headers=headers)


# ⛔ Mounted LAST. A StaticFiles mount at "/" would shadow every route declared
# after it, and the failure mode is a 404 on an endpoint that is plainly there.
app.mount("/assets", StaticFiles(directory=STATIC / "assets"), name="assets")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
