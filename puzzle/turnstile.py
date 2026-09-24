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
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        return False, "turnstile unreachable: %s" % type(exc).__name__

    if body.get("success"):
        return True, "ok"
    # ⭐ Cloudflare's own codes, kept so a misconfiguration is diagnosable —
    # `invalid-input-secret` means the wrong key was set, which otherwise looks
    # identical to a reader failing the challenge.
    codes = body.get("error-codes") or []
    return False, "turnstile refused: %s" % (",".join(codes) or "no reason given")
