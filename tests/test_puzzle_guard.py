"""The abuse and cost ceiling — the part that has no Oracle to copy from.

⛔ Every request to `/say` runs a 7B model. The Oracle needs none of this
because Cloudflare Access decides who reaches it at all; a public URL mailed to
strangers has no such door, so these limits ARE the door.

⭐ EACH LIMIT IS TESTED BY THE ATTACK IT EXISTS TO STOP, not by its own
arithmetic. A per-IP limit is defeated by a proxy pool and a global limit lets
one client eat everyone's budget — asserting "the counter increments" would
pass on a guard that stops neither.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puzzle.guard import Guard, Refused, client_ip          # noqa: E402


class _Req:
    """Just enough of a Starlette request for `client_ip`."""

    class _C:
        def __init__(self, host): self.host = host

    def __init__(self, peer="1.1.1.1", headers=None):
        self.client = self._C(peer)
        self.headers = headers or {}


# ── per-IP ──────────────────────────────────────────────────────────────────

def test_one_address_is_cut_off_after_its_allowance():
    g = Guard(ip_turns=3, global_per_day=1000)
    for _ in range(3):
        g.check("9.9.9.9")
    with pytest.raises(Refused) as e:
        g.check("9.9.9.9")
    assert e.value.status == 429
    assert e.value.retry_after and e.value.retry_after > 0


def test_a_second_address_is_unaffected():
    """⛔ The limit must be PER address. A global-only counter dressed up as a
    per-IP one would also pass the test above."""
    g = Guard(ip_turns=2, global_per_day=1000)
    g.check("9.9.9.9")
    g.check("9.9.9.9")
    g.check("8.8.8.8")          # must not raise


# ── global ──────────────────────────────────────────────────────────────────

def test_a_proxy_pool_still_hits_the_global_ceiling():
    """⭐⭐ THE ATTACK THE PER-IP LIMIT CANNOT SEE. Ten thousand addresses each
    behaving politely is the cheapest way to pin one GPU, and every per-IP
    check passes throughout."""
    g = Guard(ip_turns=50, global_per_day=5)
    for i in range(5):
        g.check("10.0.0.%d" % i)
    with pytest.raises(Refused) as e:
        g.check("10.0.0.99")
    assert e.value.status == 503


def test_the_ceiling_counts_admissions_not_successes():
    """⛔ A turn that is admitted and then crashes still cost the GPU the time
    it ran. A ceiling that only counted successes would be one crash-loop away
    from unbounded."""
    g = Guard(ip_turns=50, global_per_day=2)
    g.check("1.2.3.4")
    g.check("1.2.3.4")
    with pytest.raises(Refused):
        g.check("1.2.3.4")
    assert g.stats()["turns_today"] == 2


# ── concurrency ─────────────────────────────────────────────────────────────

def test_the_queue_refuses_rather_than_parking_everyone():
    """⛔ One GPU serialises. Past a small depth the honest answer is 'no' —
    a caller held for six minutes has already been abandoned by the browser,
    and the work still runs."""
    g = Guard(ip_turns=99, global_per_day=999, max_concurrent=1, max_queued=0)
    with g.slot():
        with pytest.raises(Refused) as e:
            with g.slot():
                pass
    assert e.value.status == 503


def test_the_slot_is_released_after_use():
    g = Guard(max_concurrent=1, max_queued=0)
    with g.slot():
        pass
    with g.slot():          # must be free again
        pass


# ── identity ────────────────────────────────────────────────────────────────

def test_forwarded_headers_are_ignored_without_a_trusted_proxy():
    """⛔⛔ X-Forwarded-For IS CLIENT-SUPPLIED. Trusting it on a naked socket
    lets one caller mint a fresh identity per request and walk straight through
    the per-IP limit — the limit would still 'work', against nobody."""
    req = _Req(peer="5.5.5.5",
               headers={"x-forwarded-for": "6.6.6.6", "fly-client-ip": "7.7.7.7"})
    assert client_ip(req, trust_proxy=False) == "5.5.5.5"


def test_flys_own_header_wins_when_the_proxy_is_trusted():
    """⭐ Fly SETS `Fly-Client-IP` itself; X-Forwarded-For is a list the client
    started and the proxy appended to."""
    req = _Req(peer="5.5.5.5",
               headers={"x-forwarded-for": "6.6.6.6", "fly-client-ip": "7.7.7.7"})
    assert client_ip(req, trust_proxy=True) == "7.7.7.7"


def test_a_forged_chain_cannot_prepend_its_way_out():
    """⛔ The LAST hop is the one our proxy appended; everything to its left is
    whatever the caller chose to claim."""
    req = _Req(peer="5.5.5.5",
               headers={"x-forwarded-for": "evil, 6.6.6.6"})
    assert client_ip(req, trust_proxy=True) == "6.6.6.6"
