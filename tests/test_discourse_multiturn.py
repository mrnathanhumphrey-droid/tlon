"""THE LOCALITY BUILD — force-map, Markov generator, and the gate that can fail.

⛔⛔ THE GATE IS FORCE-FIDELITY, NOT EXTENT. Measured: a painter that ignores the
prior turn scores **0/200 degeneracy-guard fires** at depths 8/20/40. Extent is
maxed by noise under this architecture, so it is a tripwire; the only test that
can come back negative on a model that learned nothing is whether the realised
force-transition matrix reproduces the map.
"""
from __future__ import annotations

import random

import pytest

from tlon.act2 import corpus, falsify
from tlon.discourse import force_map as FM
from tlon.discourse import multiturn as MT


@pytest.fixture(scope="module")
def pairs():
    return corpus.build(3000, seed=3)


@pytest.fixture(scope="module")
def pool(pairs):
    return MT._pool_by_force(pairs)


# ══ THE MAP ══════════════════════════════════════════════════════════════
def test_rows_are_distributions():
    for f in FM.ORDER:
        assert abs(sum(FM.row(f).values()) - 1.0) < 1e-12


def test_only_the_mutation_surviving_cell_is_non_uniform():
    """⭐ ONE forced cell. `ku`↦{`ka`,`kä`} looked derivable from
    offer/accept-or-decline and inverts cleanly (a dispreferred response is a
    delay — `ko`), so it is PICKED and left flat."""
    assert FM.FORCED_CELLS == {"ki": "ka"}
    assert FM.verdict("ki") == FM.FORCED
    for f in ("ka", "ko", "ku", "kä"):
        assert FM.verdict(f) == FM.UNIFORM
        assert len(set(FM.row(f).values())) == 1


def test_the_chance_baseline_is_NOT_uniform():
    """⛔ THE TRAP A UNIFORM NULL WOULD HAVE WALKED INTO. The `ki`→`ka` row makes
    `ka` twice as common as anything else in the stationary state, so an
    independence null assumed uniform would be wrong before it was computed."""
    st = FM.stationary()
    assert abs(st["ka"] - 1 / 3) < 1e-9
    for f in ("ki", "ko", "ku", "kä"):
        assert abs(st[f] - 1 / 6) < 1e-9


def test_separation_is_the_derived_ceiling_and_is_far_below_one():
    """⛔⛔ THE NUMBER THAT FAILED MY OWN PICKED THRESHOLD. A perfectly faithful
    model can only reach 0.222 — a hand-chosen `far` of 0.30 was a gate that
    could never pass."""
    sep = FM.separation()
    assert abs(sep - 0.2222222) < 1e-6
    assert sep < 0.30, "the first version's threshold was above the ceiling"


def test_an_unknown_force_is_refused_with_the_five_named():
    with pytest.raises(FM.ForceMapError, match="not in lexicon class F"):
        FM.row("zzz")


def test_the_map_keys_on_the_frozen_lexicon():
    from tlon.grammar import classes as C
    assert set(FM.ORDER) == set(C.load()["classes"]["F"])


# ══ THE GENERATOR ════════════════════════════════════════════════════════
def test_every_force_has_a_well_formed_exemplar(pool):
    assert set(pool) == set(FM.ORDER)
    assert all(pool[f] for f in FM.ORDER)


def test_every_painting_is_well_formed_the_one_place_oracle(pool):
    """⭐ COHERENCE IS ONE-PLACE. `parse(render(s)) == s`, per painting. There is
    no pair-coherence check because there is no pair-coherence claim."""
    from tlon.grammar.parse import parse, render
    ch = MT.chain(pool, turns=30, rng=random.Random(1))
    for t in ch:
        assert render(parse(t.surface)) == t.surface


def test_the_chain_is_MARKOV_only_the_prior_force_is_carried(pool):
    ch = MT.chain(pool, turns=20, rng=random.Random(2))
    assert ch[0].prior_force is None
    for a, b in zip(ch, ch[1:]):
        assert b.prior_force == a.force


def test_the_forced_cell_is_obeyed_absolutely(pool):
    ch = MT.chain(pool, turns=400, rng=random.Random(4))
    seen = [(a.force, b.force) for a, b in zip(ch, ch[1:]) if a.force == "ki"]
    assert seen, "no ki transitions sampled"
    assert all(b == "ka" for _, b in seen)


def test_content_is_FREE_successive_paintings_are_not_similar(pool):
    """⛔ ANY CONTENT-SIMILARITY RULE IS THE SPATIAL GHOST. Successive surfaces
    must be no more alike than random draws are."""
    ch = MT.chain(pool, turns=200, rng=random.Random(6))
    adj = [falsify.token_overlap(a.surface, b.surface)
           for a, b in zip(ch, ch[1:])]
    assert sum(adj) / len(adj) < 0.5


def test_extent_is_a_TRIPWIRE_that_never_fires_on_generated_chains(pairs):
    """⛔⛔ NOT ENFORCEMENT. If this ever fires during generation it is a sampler
    bug, not a caught exemplar."""
    chains = MT.build(20, turns=40, pairs=pairs, seed=9)
    fired = sum(falsify.degeneracy_guard([t.surface for t in ch]).fired
                for ch in chains)
    assert fired == 0


def test_a_chain_too_short_to_have_a_transition_is_refused(pool):
    with pytest.raises(MT.MultiturnError, match="no transition"):
        MT.chain(pool, turns=1, rng=random.Random(0))


# ══ COVERAGE: STRATIFIED BY ROW, DESIGN ZEROS EXEMPT ═════════════════════
def test_a_generated_corpus_passes_its_own_fairness_check(pairs):
    chains = MT.build(40, turns=40, pairs=pairs, seed=9)
    rep = MT.check_force_pair_fairness(chains)
    assert rep["worst_ratio"] >= MT.FORCE_PAIR_FLOOR_FRACTION


def test_a_DESIGN_ZERO_is_not_reported_as_starvation(pairs):
    """⭐⭐ A LEGITIMATE NO-OP MUST NOT BE RED. The forced row puts zero in four
    of five cells ON PURPOSE; a floor that fired on those would be demanding the
    corpus contradict its own map."""
    chains = MT.build(20, turns=40, pairs=pairs, seed=11)
    rep = MT.check_force_pair_fairness(chains)
    for dead in ("ki->ki", "ki->ko", "ki->ku", "ki->kä"):
        assert rep["counts"].get(dead, 0) == 0
    assert rep["worst_cell"][0] != "ki" or rep["worst_cell"][1] == "ka"


def test_starvation_IS_refused_when_it_is_real(pairs):
    """⛔ RED-PROOF ON THE REFUSAL. Hand-build a corpus that starves a live cell
    and assert the check comes back positive."""
    pool = MT._pool_by_force(pairs)
    rng = random.Random(3)
    starved = [[MT.Turn(rng.choice(pool["ka"]), "ka",
                        None if i == 0 else "ka") for i in range(40)]]
    with pytest.raises(MT.MultiturnError, match="never appears as a prior"):
        MT.check_force_pair_fairness(starved)


# ══ THE GATE — BOTH BRANCHES PROVEN REACHABLE ════════════════════════════
def _counts(chains):
    """⚠️ Takes the SERIALISED (dict) form — the same shape the arena writes."""
    c = {}
    for ch in chains:
        for t in ch:
            if t["prior_force"]:
                k = (t["prior_force"], t["force"])
                c[k] = c.get(k, 0) + 1
    return c


def _as_dicts(chains):
    return [[{"surface": t.surface, "force": t.force,
              "prior_force": t.prior_force} for t in ch] for ch in chains]


def test_the_gate_reads_FIDELITY_on_a_map_faithful_corpus(pairs):
    import importlib.util
    import pathlib
    spec = importlib.util.spec_from_file_location(
        "ff", pathlib.Path(__file__).parents[1] / "tools/act2_force_fidelity.py")
    ff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ff)
    chains = _as_dicts(MT.build(14, turns=40, pairs=pairs, seed=9))
    v, _ = ff.verdict(ff.distances(_counts(chains)))
    assert v == "FIDELITY", v


def test_the_gate_reads_CHANCE_on_a_painter_that_IGNORES_the_prior(pairs):
    """⛔⛔ THE RED-PROOF THAT MATTERS. Extent scores this 0/200 fires — a clean
    pass. The gate must come back negative on it, or it is not a gate."""
    import importlib.util
    import pathlib
    spec = importlib.util.spec_from_file_location(
        "ff", pathlib.Path(__file__).parents[1] / "tools/act2_force_fidelity.py")
    ff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ff)
    pool = MT._pool_by_force(pairs)
    rng = random.Random(5)
    chains = []
    for _ in range(14):
        ch, prev = [], None
        for _i in range(40):
            f = rng.choice(FM.ORDER)
            ch.append({"surface": rng.choice(pool[f]), "force": f,
                       "prior_force": prev})
            prev = f
        chains.append(ch)
    v, why = ff.verdict(ff.distances(_counts(chains)))
    assert v == "CHANCE", f"{v}: {why}"


def test_an_underpowered_sample_is_REFUSED_not_reported_as_a_null(pairs):
    """⭐ A NULL FROM TOO FEW OBSERVATIONS IS A STATEMENT ABOUT THE INSTRUMENT."""
    import importlib.util
    import pathlib
    spec = importlib.util.spec_from_file_location(
        "ff", pathlib.Path(__file__).parents[1] / "tools/act2_force_fidelity.py")
    ff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ff)
    # ⚠️ MT.chain, not MT.build — build's fairness check refuses a sample this
    # small for a DIFFERENT and also correct reason, which would mask the branch
    # under test.
    pool = MT._pool_by_force(pairs)
    chains = _as_dicts([MT.chain(pool, turns=8, rng=random.Random(k))
                        for k in range(2)])
    v, _ = ff.verdict(ff.distances(_counts(chains)))
    assert v == "UNDERPOWERED", v


# ══ THE LEDGER ═══════════════════════════════════════════════════════════
def test_the_mix_fraction_is_ledgered_and_is_a_FRACTION():
    assert MT.MULTITURN_FRACTION_LEDGERED == 0.5
    assert 0.0 < MT.MULTITURN_FRACTION_LEDGERED < 1.0


def test_the_coverage_floor_is_a_FRACTION_not_a_count():
    assert 0.0 < MT.FORCE_PAIR_FLOOR_FRACTION < 1.0
