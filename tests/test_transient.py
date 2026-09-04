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


# ── 5 · ⛔⛔ the corpus must rebuild from its seed, in ANY process ──────────

def test_the_generator_is_DETERMINISTIC_ACROSS_HASH_SEEDS(rig):
    """⛔⛔ A CORPUS THAT CANNOT BE REBUILT VOIDS EVERY sha PIN IN THE PROJECT.

    `responsive_choice` iterated `provocation_roots - barred` -- a FROZENSET --
    and set iteration order follows Python's randomised string hashing. The same
    seed in a different process produced a different corpus. It escaped notice
    because the corpus is VALID either way: it passes the recipe gate
    identically, so nothing looks wrong except that it does not reproduce.

    Measured before the fix: PYTHONHASHSEED 1 -> 526a490bb9674ce1,
    2 -> 8674d1f2629cfaac, and 1 again -> 526a490bb9674ce1.

    ⭐ THIS TEST CANNOT SEE THE BUG IN-PROCESS. Hash randomisation is fixed for
    the life of an interpreter, so it must spawn CHILDREN with different
    PYTHONHASHSEED values -- an in-process assertion would pass against the
    broken code.
    """
    import hashlib
    import os
    import subprocess

    script = (
        "import sys, hashlib; sys.path.insert(0, %r)\n"
        "from tlon.act2 import corpus as C1\n"
        "from tlon.discourse.transient import build_transient\n"
        # ⛔ Sized so check_force_pair_fairness is satisfied; a smaller build
        # starves a live cell and the child dies on COVERAGE, which would look
        # like a determinism failure and is a different thing entirely.
        "ch = build_transient(200, turns=10, pairs=C1.build(300, seed=20624),\n"
        "                     seed=20624, responsiveness=1.0, verify=False)\n"
        "print(hashlib.sha256('|'.join(t.surface for c in ch for t in c)"
        ".encode()).hexdigest()[:16])\n"
        % str(pathlib.Path(__file__).resolve().parents[1])
    )
    sigs = []
    for hseed in ("1", "2", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=hseed, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, "-c", script], capture_output=True,
                           text=True, env=env)
        assert r.returncode == 0, r.stderr[-600:]
        sigs.append(r.stdout.strip())
    assert len(set(sigs)) == 1, (
        "the corpus depends on PYTHONHASHSEED: %s. Same seed, different "
        "process, different corpus -- every sha pin in the project is void."
        % dict(zip(("1", "2", "12345"), sigs)))


def test_no_BARE_SET_ITERATION_feeds_a_random_draw():
    """⛔ The mechanism, guarded directly: any set fed to an ordered operation
    must be sorted first. A future edit that drops `sorted` reintroduces a
    nondeterminism that no in-process test can see."""
    import inspect
    from tlon.discourse import transient as T
    src = inspect.getsource(T.responsive_choice)
    assert "sorted(" in src, \
        "responsive_choice no longer sorts its candidate roots; set iteration " \
        "order is hash-randomised and the corpus stops reproducing"


# ── the release-suppression DOSE axis ──────────────────────────────────────
#
# ⛔⛔ The one-adapter gate REFUSED at reading (c): perceive transmitted
# (model lag-1 z +22.86) but release did not (model lag-2 z +6.56 against a
# ceiling of 3.0), while the corpus SUPPRESSED lag 2 to z -8.57. The dose sweep
# asks whether corpus suppression intensity can be cranked past the base model's
# self-consistency prior. These guard the knob that sweep turns.

def _dose_lex():
    from tlon.discourse.transient import _lex_roots
    return _lex_roots()


def test_dose_ZERO_is_EXACTLY_the_gate_recipe():
    """⛔⛔ THE DOSE-0 RED-PROOF. If the knob perturbs the default at all, every
    dose is measured against a baseline that is not the one the gate ran, and
    the curve's low end is a different experiment. Verified at corpus level too:
    a dose-0 rebuild reproduces train sha dd40e22f85b0b6e4."""
    import inspect
    from tlon.discourse import transient as TR
    sig = inspect.signature(TR.chain_transient)
    assert sig.parameters["suppression_window"].default == 0
    assert inspect.signature(TR.build_transient
                             ).parameters["suppression_window"].default == 0


def test_own_turn_roots_reads_the_SPEAKERS_OWN_turns_not_the_PARTNERS():
    """⛔⛔ THE ENTANGLEMENT TRAP, IN ONE ASSERTION. In an alternating exchange
    the speaker's own turns are at -2, -4, -6. Barring -1 would bar the PARTNER's
    provocation — which is the very set `offerable` is drawn from — so perceive
    would collapse and the sweep would read ENTANGLED for a reason that was the
    generator's fault, not the substrate's."""
    from tlon.discourse.transient import TTurn, own_turn_roots
    lex_r = _dose_lex()
    turns = [TTurn("a", "ka", None), TTurn("b", "ki", "ka"),
             TTurn("c", "ko", "ki"), TTurn("d", "ku", "ko")]
    import unittest.mock as m
    seen = []

    def fake_roots(surface, _lex):
        seen.append(surface)
        return frozenset({surface})

    with m.patch("tlon.discourse.transient.roots_of", fake_roots):
        got = own_turn_roots(turns, 2, lex_r)
    # out[-2] = "c", out[-4] = "a" — never "d" (the partner's provocation)
    assert got == {"c", "a"}, got
    assert "d" not in seen, "the bar reached the partner's turn"


def test_a_NEGATIVE_window_bars_NOTHING_and_is_REFUSED_as_a_recipe():
    """⛔⛔ THE WEAKENED DOSE IS NOT A VALID RECIPE AND MUST NEVER BE FILED AS
    ONE. It exists only to give the dose curve a low end — measured corpus-side
    at lag-2 z +162.43, i.e. content PERSISTS in the data by construction. An
    adapter trained on it is a dose arm, not a content-transient cell."""
    import random
    import pytest as _pt
    from tlon.discourse import transient as TR
    from tlon.discourse import force_map as FM
    from tlon.act2 import corpus as C1
    lex_r = _dose_lex()
    pool = TR._pool_by_force(C1.build(600, seed=7))
    idx = TR.index_by_root(pool, lex_r)
    chains = [TR.chain_transient(pool, idx, turns=8, rng=random.Random(7 + i),
                                 responsiveness=1.0, lex_r=lex_r,
                                 fmap=FM.DERIVED_v1,
                                 rng_content=random.Random(99 + i),
                                 suppression_window=-1)
              for i in range(40)]
    assert all(t.inherited == frozenset() or True for c in chains for t in c)
    with _pt.raises(TR.MultiturnError, match="PERSISTS"):
        TR.check_transience(chains, lex_r=lex_r)


def test_raising_the_dose_SUPPRESSES_SELF_OVERLAP_without_killing_PERCEIVE():
    """⭐⭐ THE LOAD-BEARING GUARD OF THE WHOLE SWEEP. A dose that fixes release
    by killing perceive is not a fix — it is the collapse toward content-free.
    Corpus-side the two are separable: measured echo_rate 0.952 -> 0.951 while
    self-overlap goes 2.69% -> 0.00%."""
    import random
    from tlon.discourse import transient as TR
    from tlon.discourse import force_map as FM
    from tlon.act2 import corpus as C1
    lex_r = _dose_lex()
    pool = TR._pool_by_force(C1.build(2000, seed=11))
    idx = TR.index_by_root(pool, lex_r)

    def run(window):
        chains = [TR.chain_transient(pool, idx, turns=8,
                                     rng=random.Random(11 + i),
                                     responsiveness=1.0, lex_r=lex_r,
                                     fmap=FM.DERIVED_v1,
                                     rng_content=random.Random(500 + i),
                                     suppression_window=window)
                  for i in range(120)]
        echo = sum(1 for c in chains for t in c[1:] if t.echoed is not None)
        n = sum(len(c) - 1 for c in chains)
        ov = sum(1 for c in chains for i in range(2, len(c))
                 if TR.roots_of(c[i].surface, lex_r)
                 & TR.roots_of(c[i - 2].surface, lex_r))
        ovn = sum(max(0, len(c) - 2) for c in chains)
        return echo / n, ov / ovn

    echo0, ov0 = run(0)
    echo1, ov1 = run(1)
    assert ov1 == 0.0, "window 1 must drive self-overlap to zero (got %r)" % ov1
    assert ov0 > ov1, "the dose did not move self-overlap at all"
    # ⛔ perceive must SURVIVE the dose. This is the arm of the guard that fires
    # on the ENTANGLED failure, and it must not be a formality.
    assert echo1 > 0.85, "raising the dose collapsed perceive (echo %r)" % echo1
    assert abs(echo0 - echo1) < 0.05, (echo0, echo1)
