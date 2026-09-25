"""⛔⛔ TURNSTILE — VERIFIED ON THE SERVER, BECAUSE THAT IS THE ONLY PLACE IT
COUNTS.

⛔ THE SHAPE THAT LOOKS RIGHT AND PROTECTS NOTHING. The obvious wiring — the
browser solves the challenge, asks something whether the token is good, and then
proceeds — guards the BROWSER. A script skips all of it and POSTs straight to
`/say`, which is the endpoint that runs the 7B. Any check that a client can
decline to perform is decoration. So the token is verified HERE, inside the
request that spends the GPU, before `speaker.turn` is reached.

⭐ IT IS NOT THE RATE LIMIT AND DOES NOT REPLACE IT. `guard.py` bounds how much
compute the world may spend; this bounds WHO may spend it. A botnet politely
obeying the per-IP limit still eats the global daily budget that real readers
need, and a captcha alone would let one logged-in human hammer the box. The two
fail in different directions on purpose, which is the same reasoning `guard.py`
already gives for having three limits rather than one.

⛔⛔ IT FAILS CLOSED ON A MISSING SECRET, AND ONLY IN A DEPLOYED ENVIRONMENT.
An unset `TURNSTILE_SECRET_KEY` on Fly means somebody shipped without running
`fly secrets set`. Waving requests through in that case would produce a public
GPU endpoint with no protection, reporting healthy — the exact silent-success
shape this repo has now hit four times (the wrong lexicon, the leaked bench, the
0.0% carry probe, the arena-shape read). Locally, where there is no secret and
no card, it is simply off, the same way `mock_speaker` decides.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

#: Cloudflare's verification endpoint. ⛔ Called from the SERVER, never the
#: browser: the secret would be readable by anyone who opened devtools.
SITEVERIFY = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

#: ⛔ Same markers `mock_speaker` uses, and for the same reason: one definition
#: of "this is a real deployment" rather than two that can disagree.
_DEPLOYED = ("FLY_APP_NAME", "FLY_MACHINE_ID", "KUBERNETES_SERVICE_HOST",
             "RENDER", "DYNO")

#: ⭐ Published to the page so the widget can render. A SITE key is public by
#: design — it is in the HTML of every site that uses Turnstile.
SITE_KEY = os.environ.get("TLON_TURNSTILE_SITEKEY", "")

#: ⛔ NEVER LOGGED, never returned, never written to disk. Set with
#: `fly secrets set TURNSTILE_SECRET_KEY=...`.
_SECRET_ENV = "TURNSTILE_SECRET_KEY"

#: How long to wait on Cloudflare before giving up.
TIMEOUT_S = float(os.environ.get("TLON_TURNSTILE_TIMEOUT_S", "6"))


class Misconfigured(RuntimeError):
    """Raised at import/startup, never per-request."""


def deployed() -> bool:
    return any(os.environ.get(k) for k in _DEPLOYED)


def secret() -> str:
    return os.environ.get(_SECRET_ENV, "")


def required() -> bool:
    """Must a request carry a valid token?

    ⛔ TRUE WHENEVER A SECRET EXISTS, deployed or not, so the integration can be
    exercised locally before it is trusted in production. A check that has only
    ever run in the place it must not fail is not a check.
    """
    return bool(secret())


def preflight() -> None:
    """⛔⛔ CALLED AT STARTUP. A deployment without the secret REFUSES TO SERVE
    rather than serving unprotected."""
    if deployed() and not secret():
        raise Misconfigured(
            "⛔⛔ REFUSING TO START: %s is unset in a deployed environment. "
            "This app is a public URL in front of a GPU; without Turnstile the "
            "only thing between a script and the card is the rate limit. Set it "
            "with `fly secrets set %s=...`, or set TLON_TURNSTILE_OPTIONAL=1 if "
            "an unprotected deploy is genuinely intended."
            % (_SECRET_ENV, _SECRET_ENV))


def key_verdict() -> str:
    """⛔⛔⛔ IS THE SECRET A KEY, OR JUST A STRING? `preflight` only ever asked
    whether one was PRESENT, and presence is not validity — the deployed value
    was a 30-character placeholder starting `<` and ending `>`, the app booted
    reporting healthy, and every single reader was refused. That is this repo's
    signature failure (`scope_hides_in_the_constant`): the predicate checked
    the cheap half of the condition.

    ⭐ Cloudflare distinguishes the two faults for us, and a dummy token is
    enough to ask: `invalid-input-secret` means the KEY is wrong and nobody can
    ever pass; `invalid-input-response` means the key is FINE and only our
    throwaway token was junk, which is the expected answer.

    Returns "ok", "bad-key", or "unknown". ⛔ NEVER raises and never returns the
    secret.
    """
    if not required():
        return "ok"
    ok, why = verify("tlon-preflight-dummy-token")
    if "invalid-input-secret" in why:
        return "bad-key"
    # ⛔ A network failure is NOT a verdict. Refusing to boot because Cloudflare
    # had a bad minute would turn a blip into an outage.
    if "unreachable" in why or "http " in why:
        return "unknown"
    return "ok"


def verify(token: str, ip: str | None = None) -> tuple[bool, str]:
    """`(ok, reason)` for one token. ⛔ Never raises — a turn must not 500
    because Cloudflare was slow.

    ⛔ A NETWORK FAILURE IS A REFUSAL, NOT A PASS. Treating an unreachable
    siteverify as success would mean an attacker who can make Cloudflare
    unreachable — or simply a flaky minute — gets a free run at the GPU. The
    reader sees "try again"; the card stays shut.
    """
    if not required():
        return True, "turnstile off (no secret configured)"
    if not token:
        return False, "no turnstile token"

    payload = {"secret": secret(), "response": token}
    if ip:
        payload["remoteip"] = ip
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SITEVERIFY, data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # ⛔⛔⛔ SITEVERIFY ANSWERS A BAD SECRET WITH HTTP 400, NOT 200, AND
        # `urllib` RAISES ON ANY NON-2xx. Catching that alongside the network
        # errors reported a perfectly reachable Cloudflare as "unreachable" and
        # THREW AWAY THE BODY — which contained `invalid-input-secret`, i.e.
        # the one code this module's own comment calls out as the one that must
        # stay diagnosable because it breaks the puzzle for everybody at once.
        # It did exactly that: the deployed key was a placeholder for days and
        # every reader saw "turnstile unreachable".
        # ⭐ The body of a 4xx is still the answer. Read it.
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            return False, "turnstile http %s" % exc.code
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        return False, "turnstile unreachable: %s" % type(exc).__name__

    if body.get("success"):
        return True, "ok"
    # ⭐ Cloudflare's own codes, kept so a misconfiguration is diagnosable —
    # `invalid-input-secret` means the wrong key was set, which otherwise looks
    # identical to a reader failing the challenge.
    codes = body.get("error-codes") or []
    return False, "turnstile refused: %s" % (",".join(codes) or "no reason given")


# ── the session pass ────────────────────────────────────────────────────────
#
# ⛔⛔⛔ THE DESIGN ERROR THIS FIXES, AND IT WAS MINE. The first wiring verified
# a token on EVERY message. A Turnstile token is SINGLE-USE, so "verify every
# message" means "challenge every message": the widget had to be re-armed after
# each turn, and a reader who had just proved they were a person was asked to
# prove it again before they could say a second sentence. Nate's words, after
# three attempts at fixing the symptom: *"it hasn't cleared yet. its either
# invisible or permanent."* Both of those are the same root cause — a gate
# being used as a per-request signature.
#
# ⭐⭐ TURNSTILE IS A DOOR, NOT A TICKET INSPECTOR. You pass it once, and the
# server remembers. That is what every site using it actually does, and it is
# why nobody else's captcha "won't clear".
#
# ⛔ WHAT THIS DOES NOT DO IS REPLACE THE RATE LIMITS. `guard.py` still bounds
# turns per IP and per day, which is the protection that actually matters
# against someone who has already solved one challenge. The honest statement of
# the trade: a determined attacker can farm one token either way, so per-message
# challenges bought us close to nothing and cost the product its usability.
#
# ⛔ THE PASS IS BOUND TO THE CLIENT ADDRESS. A cookie lifted from one machine
# is worthless on another, and a reader whose address changes is simply asked
# once more — which is correct, not a bug.

import hashlib
import hmac as _hmac
import time as _time

#: The cookie the pass travels in. ⛔ httponly: nothing in the page ever needs
#: to read it, and a script that cannot read it cannot replay it elsewhere.
PASS_COOKIE = "tlon_human"

#: ⭐ Long enough that a reader is never re-challenged mid-visit, short enough
#: that a lifted cookie is not a permanent key. A puzzle mailed to a short list
#: does not need days.
PASS_HOURS = 12


def _pass_sig(exp: int, ip: str) -> str:
    #: ⛔ Keyed on the Turnstile SECRET, which is already the one value this
    #: process holds that an attacker does not. No second secret to deploy,
    #: forget, or malform — and this repo has already lost a day to exactly
    #: that with TLON_PROXY_SECRET.
    msg = ("tlon-human:%d:%s" % (exp, ip or "")).encode("utf-8")
    return _hmac.new(secret().encode("utf-8"), msg, hashlib.sha256).hexdigest()


def issue_pass(ip: str) -> str:
    exp = int(_time.time()) + PASS_HOURS * 3600
    return "%d.%s" % (exp, _pass_sig(exp, ip))


def pass_is_good(value: str, ip: str) -> bool:
    """⛔ Forgery-proof and expiry-checked, compared in constant time."""
    if not value or "." not in value:
        return False
    raw_exp, _, sig = value.partition(".")
    try:
        exp = int(raw_exp)
    except ValueError:
        return False
    if exp < _time.time():
        return False
    return _hmac.compare_digest(sig, _pass_sig(exp, ip))


def has_pass(request, ip: str) -> bool:
    """⭐ True when this reader has already proved they are a person, OR when
    Turnstile is switched off entirely — the two are the same answer to the
    only question the caller is asking: *must I challenge this person?*"""
    if not required():
        return True
    return pass_is_good(request.cookies.get(PASS_COOKIE, ""), ip)
