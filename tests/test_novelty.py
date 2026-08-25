"""Repetition log and orbit budget.

The properties that matter are the ones that would silently corrupt the whole
premise if they failed: buckets must not leak into each other, decay must
actually forgive, the log must stay bounded forever, and a forked experiment
must not mutate the ledger it forked from.
"""
from __future__ import annotations
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tlon.grammar.parse import parse                        # noqa: E402
from tlon.novelty.centroids import RepetitionLog            # noqa: E402
from tlon.novelty.orbit import Decision, Orbit, Policy      # noqa: E402

MOON = "u fang mlö ka"
MOON2 = "hlör u fang axaxaxas mlö ka"
RIVER = "mil flex fang ka"
CLOCK = "xom rän kön ka"


def _obs(log, key, text):
    log.observe(key, parse(text), text)


# ── scoring ────────────────────────────────────────────────────────────────
def test_empty_bucket_is_free():
    log = RepetitionLog()
    s = log.score("03", parse(MOON))
    assert s["novelty_cost"] == 0.0
    assert s["nearest_dist"] is None


def test_immediate_exact_repeat_is_maximally_costly():
    log = RepetitionLog()
    _obs(log, "03", MOON)
    s = log.score("03", parse(MOON))
    assert s["nearest_dist"] == 0.0
    assert s["novelty_cost"] == pytest.approx(1.0)


def test_a_different_impression_of_the_same_referent_is_cheap():
    log = RepetitionLog()
    _obs(log, "03", MOON)
    near = log.score("03", parse(MOON))["novelty_cost"]
    far = log.score("03", parse("nar tris melas ka"))["novelty_cost"]
    assert far < near
    assert far < 0.5, "an unrelated impression should not read as repetition"


def test_permuted_surface_is_still_a_repeat():
    """Different string, same meaning. If this passed as novel, the whole
    counter is a lie (spec §6)."""
    log = RepetitionLog()
    _obs(log, "03", "hlör nar mlö ka")
    s = log.score("03", parse("nar hlör mlö ka"))
    assert s["novelty_cost"] == pytest.approx(1.0)


# ── the property flag ③ depends on ─────────────────────────────────────────
def test_buckets_do_not_leak():
    log = RepetitionLog()
    _obs(log, "03", MOON)
    assert log.score("15", parse(MOON))["novelty_cost"] == 0.0
    assert log.score("03", parse(MOON))["novelty_cost"] > 0.9


# ── decay ──────────────────────────────────────────────────────────────────
def test_decay_forgives_over_time():
    log = RepetitionLog(half_life=8.0)
    _obs(log, "03", MOON)
    fresh = log.score("03", parse(MOON))["novelty_cost"]
    for i in range(32):
        _obs(log, "other", f"{'hlör ' * (i % 2)}mlö ka".strip())
    aged = log.score("03", parse(MOON))["novelty_cost"]
    assert aged < fresh / 4, f"decay did not forgive: {fresh} -> {aged}"


def test_decay_can_be_switched_off():
    """Red-proof for the test above: if cost fell regardless of half_life,
    the decay test would be measuring something else."""
    log = RepetitionLog(half_life=0.0)
    _obs(log, "03", MOON)
    fresh = log.score("03", parse(MOON))["novelty_cost"]
    for _ in range(32):
        _obs(log, "other", CLOCK)
    assert log.score("03", parse(MOON))["novelty_cost"] == pytest.approx(fresh)


# ── boundedness ────────────────────────────────────────────────────────────
def test_log_stays_bounded_under_sustained_load():
    log = RepetitionLog(k_per_bucket=5, half_life=32.0)
    texts = [MOON, MOON2, RIVER, CLOCK, "nar tris melas ka", "hlör mlö ka",
             "mlö axaxas ka", "u fang sen tris mlö ka", "fang ka", "mlö ka"]
    for i in range(400):
        _obs(log, f"{i % 4:02d}", texts[i % len(texts)])
    assert log.total_medoids() <= 4 * 5
    for b in log.buckets.values():
        assert len(b.medoids) <= 5


def test_exact_repeats_reinforce_rather_than_accumulate():
    log = RepetitionLog(k_per_bucket=8)
    for _ in range(20):
        _obs(log, "03", MOON)
    assert len(log.buckets["03"].medoids) == 1
    assert log.buckets["03"].medoids[0].hits == 20


# ── persistence / experiment forking ───────────────────────────────────────
def test_roundtrip_preserves_scores():
    log = RepetitionLog(half_life=16.0)
    for t in (MOON, RIVER, CLOCK):
        _obs(log, "03", t)
    before = log.score("03", parse(MOON2))
    after = RepetitionLog.from_dict(log.to_dict()).score("03", parse(MOON2))
    assert before == after


def test_fork_does_not_mutate_the_ledger():
    """Two experiments forked from one snapshot must be comparable; that fails
    the moment a fork writes back into what it forked from."""
    ledger = RepetitionLog()
    _obs(ledger, "03", MOON)
    snapshot = ledger.to_dict()

    a, b = ledger.fork(), ledger.fork()
    for _ in range(5):
        _obs(a, "03", RIVER)
    _obs(b, "03", CLOCK)

    assert ledger.to_dict() == snapshot
    assert a.to_dict() != b.to_dict()


# ── orbit ──────────────────────────────────────────────────────────────────
def test_orbit_accepts_within_budget():
    o = Orbit("o1", budget=1.0)
    assert o.offer("03", 0.4) is Decision.ACCEPT
    o.commit("03", 0.4, Decision.ACCEPT)
    assert o.remaining() == pytest.approx(0.6)


def test_offer_does_not_spend():
    """A candidate that never passes the M gate must not drain the arc."""
    o = Orbit("o1", budget=1.0)
    for _ in range(10):
        o.offer("03", 0.9)
    assert o.remaining() == pytest.approx(1.0)
    assert o.turns == 0


def test_over_budget_closes_under_close_policy():
    o = Orbit("o1", budget=0.5, policy=Policy.CLOSE_ORBIT)
    assert o.offer("03", 0.9) is Decision.CLOSE
    o.commit("03", 0.9, Decision.CLOSE)
    assert o.closed
    with pytest.raises(RuntimeError):
        o.commit("03", 0.1, Decision.ACCEPT)


def test_over_budget_repeats_under_keep_alive():
    o = Orbit("o1", budget=0.5, policy=Policy.KEEP_ALIVE)
    d = o.offer("03", 0.9)
    assert d is Decision.REPEAT
    o.commit("03", 0.9, d)
    assert not o.closed and o.turns == 1


def test_policy_actually_changes_the_outcome():
    """Red-proof: if both policies returned the same decision the parameter
    would be decorative."""
    over = 0.9
    assert (Orbit("a", budget=0.5, policy=Policy.CLOSE_ORBIT).offer("03", over)
            is not Orbit("b", budget=0.5, policy=Policy.KEEP_ALIVE).offer("03", over))


def test_orbit_roundtrip():
    o = Orbit("o1", budget=2.0, policy=Policy.KEEP_ALIVE)
    o.commit("03", 0.4, Decision.ACCEPT)
    o.commit("15", 0.3, Decision.ACCEPT)
    assert Orbit.from_dict(o.to_dict()).to_dict() == o.to_dict()
