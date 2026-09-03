"""⛔⛔ RED-PROOF FOR CONTENT-TRANSIENCE — both halves, or the recipe is a lie.

The corpus claim has two limbs and they fail in opposite directions:

    lag 1 at chance      -> content-FREE. The control recipe wearing the
                            treatment's name, which would put the control arm
                            in the treatment cell of the factorial.
    lag ≥2 above chance  -> content PERSISTS. "Ingest and release" has become
                            "hold through my own history" -- object permanence
                            rebuilt out of individually-innocent local choices.
                            ⭐ lag 2 IS the speaker's own previous turn.

⛔⛔ THE SECOND ONE IS THE DANGEROUS ONE, because the naive implementation of
"respond to what provoked you" produces it AND LOOKS CORRECT. A shares a root
with B, B shares a root with C, and the root walks the chain. Every local step
is right; the global property is exactly what Tlön denies. So there is a test
here that builds the naive generator on purpose and proves the gate refuses it.

⭐ AND EVERY THRESHOLD IS STATED AGAINST A PERMUTATION NULL, never against zero.
Measured on the real corpus: chance overlap is 0.042 shared roots per pair, so a
generator that does nothing passes a `> 0` test.
"""
from __future__ import annotations

import pathlib
import random
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.discourse import force_map as FM                      # noqa: E402
from tlon.discourse.multiturn import MultiturnError, _pool_by_force  # noqa: E402
from tlon.discourse.transient import (TTurn, chain_transient,   # noqa: E402
                                      check_transience, index_by_root,
                                      lag_profile, permutation_null,
                                      responsive_choice, roots_of)
from tlon.grammar import classes as C                           # noqa: E402
from tlon.product import schema as PS                           # noqa: E402


class _P:
    """A pool entry — only `.surface` is read by `_pool_by_force`."""

    def __init__(self, surface):
        self.surface = surface


def _lex():
    return C.load()["classes"]


def make_pairs(n_per_force=60, seed=7):
    """Legal two-root surfaces spanning every force.

    ⭐ TWO roots per surface on purpose: with one root there is almost no room
    for overlap to be anything but present-or-absent, and the lag statistic
    would be measuring the pool's shape rather than the generator's choices.
    """
    lex = _lex()
    rng = random.Random(seed)
    roots = sorted(lex["R"])
    rels = sorted(lex["L"])
    out = []
    for force in FM.ORDER:
        made, tries = 0, 0
        while made < n_per_force and tries < n_per_force * 40:
            tries += 1
            r1, r2 = rng.choice(roots), rng.choice(roots)
            if r1 == r2:
                continue
            prop = {"node": {"root": r1,
                             "edges": [{"relator": rng.choice(rels),
                                        "node": {"root": r2}}]},
                    "force": force}
            try:
                _scene, surface, _ref = PS.validate(prop)
            except Exception:                                  # noqa: BLE001
                continue
            out.append(_P(surface))
            made += 1
    return out


@pytest.fixture(scope="module")
def rig():
    lex_r = _lex()["R"]
    pairs = make_pairs()
    pool = _pool_by_force(pairs)
    return pool, index_by_root(pool, lex_r), lex_r


def transient_chains(rig, *, n=300, turns=10, seed=11, responsiveness=1.0):
    pool, idx, lex_r = rig
    rng = random.Random(seed)
    rc = random.Random(seed ^ 0x5F5E100)
    return [chain_transient(pool, idx, turns=turns, rng=rng,
                            responsiveness=responsiveness, lex_r=lex_r,
                            rng_content=rc)
            for _ in range(n)]


# ── 0 · the null is not zero, which is why every threshold is stated on it ──

def test_the_permutation_null_is_NOT_zero(rig):
    """⛔⛔ THE WHOLE REASON THE ACCEPTANCE CRITERION IS A Z-SCORE. Two short
    utterances drawn from 156 roots overlap by chance. A target of 'shared
    roots > 0' is passed by a generator that does nothing at all."""
    _pool, _idx, lex_r = rig
    chains = transient_chains(rig)
    mu, sd = permutation_null(chains, lag=1, shuffles=60,
                              rng=random.Random(3), lex_r=lex_r)
    assert mu > 0.0, "chance overlap measured as zero — the fixture is degenerate"
    assert sd > 0.0


# ── 1 · limb one: the response IS provoked by the provocation ──────────────

def test_lag1_is_ELEVATED_above_chance(rig):
    _pool, _idx, lex_r = rig
    rep = check_transience(transient_chains(rig), lex_r=lex_r, shuffles=60)
    assert rep["z"][1] >= 6.0, rep["z"]
    assert rep["verdict"] == "content-transient"


def test_a_CONTENT_FREE_generator_is_REFUSED_as_not_responsive(rig):
    """⛔ responsiveness=0 reproduces `multiturn.chain` — the control recipe.
    It must be refused BY NAME here, or the two arms of the factorial could be
    built by the same call and labelled differently."""
    _pool, _idx, lex_r = rig
    flat = transient_chains(rig, responsiveness=0.0)
    with pytest.raises(MultiturnError, match="NOT RESPONSIVE"):
        check_transience(flat, lex_r=lex_r, shuffles=60)


# ── 2 · ⛔⛔ limb two: content does NOT survive the turn ────────────────────

def test_lag2_and_beyond_are_AT_CHANCE(rig):
    """⭐ lag 2 is the speaker's own previous turn in an alternating exchange,
    so this cell IS the own-chain-persistence guard."""
    _pool, _idx, lex_r = rig
    rep = check_transience(transient_chains(rig), lex_r=lex_r, shuffles=60)
    for k in (2, 3, 4):
        assert rep["z"][k] <= 3.0, (k, rep["z"])


def test_the_NAIVE_responsive_generator_LEAKS_and_the_gate_CATCHES_IT(rig):
    """⛔⛔ THE TEST THIS FILE EXISTS FOR.

    Build the obvious version -- every turn echoes a root of the turn before it,
    with NO transitivity break -- and the content walks the whole chain. Each
    local step is defensible; the global property is object permanence, which is
    the one thing Tlön denies. The gate must refuse it, and name lag 2.
    """
    pool, idx, lex_r = rig
    rng = random.Random(5)
    chains = []
    for _ in range(300):
        f = rng.choice(FM.ORDER)
        out = [TTurn(rng.choice(pool[f]), f, None, frozenset(), None)]
        for _ in range(9):
            dist = FM.DERIVED_v1.row(f)
            nxt = rng.choices(FM.ORDER, weights=[dist[x] for x in FM.ORDER])[0]
            prev = out[-1]
            # ⛔ THE BUG, ON PURPOSE: `barred` is empty, so the root a turn
            # INHERITED is free to be echoed onward. Nothing here looks wrong.
            surface, echoed = responsive_choice(
                idx[nxt], pool[nxt], roots_of(prev.surface, lex_r),
                frozenset(), rng, lex_r=lex_r)
            out.append(TTurn(surface, nxt, f,
                             frozenset({echoed}) if echoed else frozenset(),
                             echoed))
            f = nxt
        chains.append(out)

    prof = lag_profile(chains, max_lag=4, lex_r=lex_r)
    assert prof[2] > prof[4], \
        "the fabricated leak did not actually leak; the test proves nothing"
    with pytest.raises(MultiturnError, match="CONTENT PERSISTS"):
        check_transience(chains, lex_r=lex_r, shuffles=60)


def test_the_leak_message_NAMES_lag2_as_the_own_chain(rig):
    """⛔ The refusal is the only postmortem a corpus build leaves behind."""
    pool, idx, lex_r = rig
    rng = random.Random(5)
    chains = []
    for _ in range(300):
        f = rng.choice(FM.ORDER)
        out = [TTurn(rng.choice(pool[f]), f, None, frozenset(), None)]
        for _ in range(9):
            nxt = rng.choice(FM.ORDER)
            prev = out[-1]
            s, e = responsive_choice(idx[nxt], pool[nxt],
                                     roots_of(prev.surface, lex_r),
                                     frozenset(), rng, lex_r=lex_r)
            out.append(TTurn(s, nxt, f, frozenset({e}) if e else frozenset(), e))
            f = nxt
        chains.append(out)
    with pytest.raises(MultiturnError) as exc:
        check_transience(chains, lex_r=lex_r, shuffles=60)
    assert "own" in str(exc.value).lower()


# ── 3 · the transitivity break itself ──────────────────────────────────────

def test_responsive_choice_NEVER_echoes_a_BARRED_root(rig):
    """⛔⛔ THE MECHANISM. A response may echo what its provocation contributed
    itself, never what its provocation inherited."""
    pool, idx, lex_r = rig
    rng = random.Random(2)
    for _ in range(300):
        force = rng.choice(FM.ORDER)
        prov = rng.choice(pool[force])
        pr = roots_of(prov, lex_r)
        if not pr:
            continue
        barred = frozenset({sorted(pr)[0]})
        s, echoed = responsive_choice(idx[force], pool[force], pr, barred, rng,
                                      lex_r=lex_r)
        assert echoed not in barred
        # ⛔⛔ THE CORRECTION THE GATE FORCED: the bar is on CONTAINMENT, not on
        # the echo slot. Barring only the echo let the root ride along in the
        # chosen surface and lag-2 read z=29.65.
        if any(not (roots_of(x, lex_r) & barred) for x in pool[force]):
            assert not (roots_of(s, lex_r) & barred)


def test_barring_EVERYTHING_degrades_to_an_unresponsive_draw_not_a_crash(rig):
    """⭐ A turn with nothing legal to echo is a real state. It returns
    `echoed=None` -- recorded as the non-echo it is, never retried until it
    looks like a success."""
    pool, idx, lex_r = rig
    rng = random.Random(4)
    force = FM.ORDER[0]
    prov = pool[force][0]
    pr = roots_of(prov, lex_r)
    s, echoed = responsive_choice(idx[force], pool[force], pr, pr, rng,
                                  lex_r=lex_r)
    assert echoed is None and s in pool[force]


def test_an_echoed_turn_records_WHAT_it_echoed(rig):
    """⛔ Bookkeeping the next turn depends on. If `inherited` were not carried,
    the transitivity break has nothing to subtract and silently does nothing."""
    chains = transient_chains(rig, n=40)
    echoed = [t for ch in chains for t in ch[1:] if t.echoed]
    assert echoed, "no turn echoed anything — responsiveness is not working"
    for t in echoed:
        assert t.inherited == frozenset({t.echoed})


# ── 4 · the recipes differ in ONE variable ────────────────────────────────

def test_responsiveness_is_a_REAL_DIAL_not_a_boolean(rig):
    """⭐ The factorial needs the control reachable from the same code path, or
    'content-free vs content-transient' is a comparison across two generators
    that could differ in ways nobody wrote down."""
    _pool, _idx, lex_r = rig
    lo = lag_profile(transient_chains(rig, responsiveness=0.0),
                     max_lag=1, lex_r=lex_r)[1]
    hi = lag_profile(transient_chains(rig, responsiveness=1.0),
                     max_lag=1, lex_r=lex_r)[1]
    assert hi > lo * 2, (lo, hi)


def test_an_out_of_range_responsiveness_RAISES(rig):
    pool, idx, lex_r = rig
    with pytest.raises(MultiturnError, match="responsiveness"):
        chain_transient(pool, idx, turns=4, rng=random.Random(1),
                        responsiveness=1.5, lex_r=lex_r)


def test_the_force_machinery_is_UNCHANGED_between_recipes(rig):
    """⛔⛔ ONE KNOB. If the transient recipe also moved the force map, a
    difference between the arms could not be attributed to content at all."""
    pool, idx, lex_r = rig
    a = chain_transient(pool, idx, turns=12, rng=random.Random(99),
                        responsiveness=1.0, lex_r=lex_r, seed_force="ka",
                        rng_content=random.Random(7))
    b = chain_transient(pool, idx, turns=12, rng=random.Random(99),
                        responsiveness=0.0, lex_r=lex_r, seed_force="ka",
                        rng_content=random.Random(7))
    assert [t.force for t in a] == [t.force for t in b], \
        "responsiveness perturbed the force sequence — the arms differ in two " \
        "variables and no contrast between them is attributable"
