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
import threading
import time

#: Per-IP: this many turns in this window.
IP_TURNS = 12
IP_WINDOW_S = 10 * 60

#: Global: this many turns a day across everyone. ⭐ At ~8s a turn this is well
#: under an hour of GPU, so the box is never the thing that runs out first.
GLOBAL_TURNS_PER_DAY = 1500

#: ⛔ ONE GPU, ONE GENERATION. The model is a single process-wide object; two
#: concurrent `generate()` calls on it contend for the same VRAM and both get
#: slower rather than one waiting. Serialise, and bound the queue so request
#: number fifty is REFUSED rather than kept waiting six minutes for a socket the
#: browser gave up on.
MAX_CONCURRENT = 1
MAX_QUEUED = 8


class Refused(Exception):
    """Carries the HTTP status and a line that is honest about which limit hit."""

    def __init__(self, status: int, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.retry_after = retry_after


def client_ip(request, *, trust_proxy: bool) -> str:
    """The caller's address.

    ⛔⛔ `X-Forwarded-For` IS CLIENT-SUPPLIED AND FORGEABLE. Trusting it on a
    naked socket lets anyone mint a fresh identity per request and walk straight
    through the per-IP limit. So it is read ONLY when `trust_proxy` says a proxy
    we control is definitely in front, and even then Fly's own `Fly-Client-IP` is
    preferred because Fly sets it itself rather than appending to a list the
    client started.
    """
    if trust_proxy:
        fly = request.headers.get("fly-client-ip")
        if fly:
            return fly.strip()
        xff = request.headers.get("x-forwarded-for")
        if xff:
            # ⛔ The LAST hop is the one our proxy appended; the leftmost entries
            # are whatever the client chose to claim.
            return xff.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


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
                wait = int(hits[0] + self.ip_window_s - now) + 1
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
