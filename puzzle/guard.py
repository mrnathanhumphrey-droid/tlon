"""ABUSE + COST PROTECTION — the part the Oracle never needed and this app does.

⛔⛔ THE ORACLE HAS NO RATE LIMITING AND NO CAPTCHA, AND THAT IS NOT AN OVERSIGHT
IN IT. It sits behind Cloudflare Access, so the only people who can reach it are
people who were let in. This app is the opposite: a public URL mailed to
strangers, where **every single request runs a 7B model on the box**. The
protection is therefore not copied from anywhere. It is new, and it is the only
thing between a link and a machine pinned at 100% by one script.

⭐ THE CEILING IS COMPUTE, NOT DOLLARS. There is no per-token bill to meter — the
weights are ours. What is finite is GPU-seconds, so the limits are denominated in
TURNS and in CONCURRENCY, which is what actually runs out. Pricing a compute
ceiling in dollars would be an anchor of the wrong shape.

⛔ THREE LIMITS, AND THEY FAIL IN DIFFERENT DIRECTIONS ON PURPOSE:

  per-IP     stops one person hammering it
  global     stops a botnet of many IPs each behaving "politely"
  concurrency stops the box from thrashing when both of the above are satisfied

A per-IP limit alone is defeated by a proxy pool; a global limit alone lets one
client eat everybody's budget. Neither substitutes for the other.
"""
from __future__ import annotations

import collections
import hmac
import os
import threading
import time

#: Per-IP: this many turns in this window.
IP_TURNS = 12
IP_WINDOW_S = 10 * 60

#: Global: this many turns a day across everyone.
#:
#: ⛔⛤ THE JUSTIFICATION THAT WAS HERE IS NO LONGER TRUE, AND THE NUMBER WAS
#: SIZED UNDER IT. It read "at ~8s a turn this is well under an hour of GPU".
#: Two things are wrong with that now:
#:   * the arithmetic never worked — 1500 × 8s is 3.3 hours, not "well under
#:     an hour";
#:   * and a turn is no longer ~8s. `speaker.CARRY_RETRIES` lets the FIRST
#:     exchange draw up to four replies when none carries, which is what takes
#:     the three-turn reach from 67.3% to 83.3%. Expected draws on turn 1 are
#:     ~2.1 provoke generations plus the write, so ~3.1 against 2, and roughly
#:     2.3 generations per turn averaged over a four-turn conversation.
#:
#: ⭐ SO THE HONEST FIGURE IS ~16s A TURN AND ~6.7 GPU-HOURS A DAY AT THIS
#: CEILING. That may well be the right ceiling — it is a cost decision, not a
#: correctness one, and it is Nate's. What is not defensible is a constant
#: carrying a reason that stopped being true when something else shipped.
GLOBAL_TURNS_PER_DAY = 1500

#: ⛔ ONE GPU, ONE GENERATION. The model is a single process-wide object; two
#: concurrent `generate()` calls on it contend for the same VRAM and both get
#: slower rather than one waiting. Serialise, and bound the queue so request
#: number fifty is REFUSED rather than kept waiting six minutes for a socket the
#: browser gave up on.
MAX_CONCURRENT = 1
MAX_QUEUED = 8


#: ⛔⛔ HOW MANY REQUESTS ARRIVED WITH A TRUSTWORTHY CLIENT ADDRESS, AND HOW
#: MANY DID NOT. In a healthy deployment `unsigned` stays at 0: the Worker
#: signs every request. Any other number means the proxy secret is wrong on one
#: side, in which case every reader shares Cloudflare's egress address — the
#: per-IP limit becomes a second global one AND the session pass stops being
#: bound to anybody. Both failures are invisible from the outside, which is the
#: only reason this counter exists.
PROXY_TRUST = {"signed": 0, "unsigned": 0}


class Refused(Exception):
    """Carries the HTTP status and a line that is honest about which limit hit."""

    def __init__(self, status: int, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.retry_after = retry_after


def client_ip(request, *, trust_proxy: bool) -> str:
    """The caller's address. ⭐ See `client_ip_ex` for whether to believe it."""
    return client_ip_ex(request, trust_proxy=trust_proxy)[0]


def client_ip_ex(request, *, trust_proxy: bool) -> tuple[str, bool]:
    """The caller's address, AND WHETHER WE CRYPTOGRAPHICALLY KNOW IT IS THEIRS.

    ⛔⛔⛔ THE SECOND VALUE IS WHAT MAKES A BAN SAFE. Everything below the
    signature check hands back a FALLBACK — behind Cloudflare that fallback is
    the egress address, which is the same string for every reader on earth.
    Rate-limiting on it merely degrades (one shared budget); BANNING on it takes
    the bench off the internet for everybody, and looks exactly like a crash.
    So the flag is `True` only when:

      * there is no proxy in front at all, so the socket peer IS the reader; or
      * the Worker signed the request and we checked the signature.

    ⛔ `Fly-Client-IP` is deliberately NOT enough. Fly sets it itself, but the
    `modal.run` URL stays publicly reachable, so anyone may send that header
    directly and mint a clean identity. It is fine to rate-limit on — the worst
    case is somebody evading their own limit — and not fine to ban on.

    ⛔⛔ `X-Forwarded-For` IS CLIENT-SUPPLIED AND FORGEABLE. Trusting it on a
    naked socket lets anyone mint a fresh identity per request and walk straight
    through the per-IP limit. So it is read ONLY when `trust_proxy` says a proxy
    we control is definitely in front, and even then Fly's own `Fly-Client-IP` is
    preferred because Fly sets it itself rather than appending to a list the
    client started.
    """
    if trust_proxy:
        # ⛔⛔ THE CLOUDFLARE-IN-FRONT-OF-MODAL CASE, AND IT BREAKS EVERY RULE
        # BELOW. `tlon.resolveresearcher.com` is a Cloudflare Worker proxying to
        # a `modal.run` URL, because Modal gates custom domains behind a $250/mo
        # plan. In that chain the LAST `X-Forwarded-For` entry is CLOUDFLARE'S
        # egress address, not the reader's — so the rule below would give every
        # reader on earth one shared identity and the per-IP limit would quietly
        # become a second global limit. It would fail OPEN and look fine.
        #
        # ⛔ A CUSTOM HEADER ALONE IS NOT ENOUGH. The `modal.run` URL stays
        # publicly reachable, so anyone could send `X-Tlon-Client-IP` themselves
        # and mint a fresh identity per request — which is the exact forgery
        # this function's docstring already refuses to allow on a naked socket.
        # The header is therefore only believed when it arrives with a secret
        # that only the Worker knows.
        secret = os.environ.get("TLON_PROXY_SECRET", "")
        if secret and _const_eq(request.headers.get("x-tlon-proxy-secret", ""),
                                secret):
            claimed = (request.headers.get("x-tlon-client-ip") or "").strip()
            if claimed:
                PROXY_TRUST["signed"] += 1
                return claimed, True
        if secret:
            # ⛔⛔⛔ THE SECRET IS CONFIGURED AND THE REQUEST DID NOT CARRY IT.
            # Everything below hands back CLOUDFLARE'S EGRESS ADDRESS, which is
            # the SAME STRING FOR EVERY READER ON EARTH — and that does not just
            # merge the rate limit. `turnstile.issue_pass` signs HMAC(exp, ip),
            # so a shared ip means ONE READER'S PASS VALIDATES FOR EVERYONE.
            # The IP binding, whose entire job is to make a lifted cookie
            # worthless elsewhere, silently becomes no binding at all.
            #
            # ⛔ THIS IS NOT HYPOTHETICAL. `TLON_PROXY_SECRET` was stored as a
            # single non-printable character for days and nothing anywhere
            # reported it; the Worker now refuses to send a malformed one,
            # which lands the request in exactly this branch. Counted so that
            # `/healthz` can say it out loud instead of it being inferred from
            # a bug report months later.
            PROXY_TRUST["unsigned"] += 1

        fly = request.headers.get("fly-client-ip")
        if fly:
            return fly.strip(), False
        xff = request.headers.get("x-forwarded-for")
        if xff:
            # ⛔ The LAST hop is the one our proxy appended; the leftmost entries
            # are whatever the client chose to claim.
            return xff.split(",")[-1].strip(), False
    # ⭐ No proxy in front means the socket peer IS the reader, so this is
    # the one fallback that is also the truth.
    return (request.client.host if request.client else "unknown"), not trust_proxy


def _const_eq(a: str, b: str) -> bool:
    """⛔ Constant-time. A `==` here leaks the secret one character at a time to
    anyone willing to time the responses, and the reward for guessing it is an
    unlimited per-IP budget on a GPU."""
    return hmac.compare_digest(a or "", b or "")


class Guard:
    """All three limits, one lock, no external store.

    ⛔ IN-PROCESS ON PURPOSE. A Redis would be a second thing to run, a second
    thing to secure and a second thing to be down. This app is one machine with
    one GPU; when it restarts, the limits resetting is correct, because the thing
    they were protecting restarted too.
    """

    def __init__(self, *, ip_turns: int = IP_TURNS,
                 ip_window_s: int = IP_WINDOW_S,
                 global_per_day: int = GLOBAL_TURNS_PER_DAY,
                 max_concurrent: int = MAX_CONCURRENT,
                 max_queued: int = MAX_QUEUED):
        self.ip_turns = ip_turns
        self.ip_window_s = ip_window_s
        self.global_per_day = global_per_day
        self.max_queued = max_queued
        self._lock = threading.Lock()
        self._hits: dict[str, collections.deque] = {}
        self._day: tuple[int, int] = (self._today(), 0)
        self._sem = threading.BoundedSemaphore(max_concurrent)
        # ⛔ CAPACITY IS RUNNING + WAITING, NOT WAITING ALONE. The first version
        # compared `waiting >= max_queued` before admitting anyone, so with
        # max_queued=0 it refused the very first caller — a limiter that
        # rejected 100% of traffic while every per-IP and global check passed.
        # Caught by `test_the_queue_refuses_rather_than_parking_everyone`.
        self._capacity = max_concurrent + max_queued
        self._inflight = 0

    @staticmethod
    def _today() -> int:
        return int(time.time() // 86400)

    def check(self, ip: str) -> None:
        """Per-IP and global. ⛔ Raises `Refused`; never returns a bool nobody
        checked."""
        now = time.time()
        with self._lock:
            day, count = self._day
            today = self._today()
            if today != day:
                self._day = (today, 0)
                count = 0
            if count >= self.global_per_day:
                raise Refused(
                    503,
                    "The bench is closed for today — this is a free thing "
                    "running on one machine, and it has answered as much as it "
                    "can. Come back tomorrow.",
                    retry_after=int((today + 1) * 86400 - now))

            hits = self._hits.setdefault(ip, collections.deque())
            cutoff = now - self.ip_window_s
            while hits and hits[0] < cutoff:
                hits.popleft()
            if len(hits) >= self.ip_turns:
                # ⛔ `hits` CAN BE EMPTY HERE, AND `hits[0]` RAISED. With
                # `ip_turns=0` — which is how an operator closes the bench
                # without redeploying — every request died on an IndexError, so
                # the app answered 500 where it meant 429. Found by a logging
                # test that set the limit to 0 expecting a refusal; nothing
                # else in the suite had ever passed that value.
                wait = (int(hits[0] + self.ip_window_s - now) + 1 if hits
                        else self.ip_window_s)
                raise Refused(
                    429,
                    "You are speaking faster than it can answer. Wait a few "
                    "minutes — the Tlönian is in no hurry.",
                    retry_after=max(wait, 1))

            # ⛔ COUNTED AT ADMISSION, NOT AT COMPLETION. A turn that is admitted
            # and then fails still cost the GPU the time it ran for, and a limit
            # that only counts successes is one crash-loop away from unbounded.
            hits.append(now)
            self._day = (self._day[0], count + 1)

            # ⭐ Evict cold IPs here rather than on a timer — this is the only
            # place that already holds the lock, and the dict is the only thing
            # in this object that grows without bound.
            if len(self._hits) > 4096:
                for k in [k for k, v in self._hits.items()
                          if not v or v[-1] < cutoff]:
                    self._hits.pop(k, None)

    def slot(self):
        """Context manager for the one generation slot."""
        return _Slot(self)

    def stats(self) -> dict:
        with self._lock:
            return {"turns_today": self._day[1],
                    "global_per_day": self.global_per_day,
                    "tracked_ips": len(self._hits),
                    "inflight": self._inflight,
                    "capacity": self._capacity}


class _Slot:
    def __init__(self, guard: Guard):
        self.guard = guard

    def __enter__(self):
        g = self.guard
        with g._lock:
            if g._inflight >= g._capacity:
                raise Refused(
                    503,
                    "Too many people are talking to it at once. Try again in a "
                    "moment.",
                    retry_after=20)
            g._inflight += 1
        try:
            g._sem.acquire()
        except BaseException:
            # ⛔ Give the seat back on ANY failure, including a KeyboardInterrupt
            # between the two statements. A leaked count is permanent: it never
            # decays, so the app refuses everyone forever and the logs show only
            # 503s from a healthy process.
            with g._lock:
                g._inflight -= 1
            raise
        return self

    def __exit__(self, *exc):
        g = self.guard
        g._sem.release()
        with g._lock:
            g._inflight -= 1
        return False
