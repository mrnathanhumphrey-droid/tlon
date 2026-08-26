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


# ══ Q1/Q2 COUPLING — INSTRUMENTED, NOT ANNOTATED ═════════════════════════
def _ff():
    import importlib.util
    import pathlib
    spec = importlib.util.spec_from_file_location(
        "ff", pathlib.Path(__file__).parents[1] / "tools/act2_force_fidelity.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _tcounts(chains):
    c = {}
    for ch in chains:
        for t in ch:
            if t.prior_force:
                c[(t.prior_force, t.force)] = c.get((t.prior_force, t.force), 0) + 1
    return c


def _collapsed(pool, strength, seed, *, n=14, turns=40):
    """A model that OBEYS ki→ka but collapses the uniform rows onto `ka`."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        ch, prev = [], None
        for _i in range(turns):
            f = ("ka" if prev == "ki" else
                 "ka" if rng.random() < strength else rng.choice(FM.ORDER))
            ch.append(MT.Turn(rng.choice(pool[f]), f, prev))
            prev = f
        out.append(ch)
    return out


def test_Q1_clean_positive_on_a_faithful_corpus(pairs):
    q1 = _ff().q1_two_null(_tcounts(MT.build(14, turns=40, pairs=pairs, seed=9)))
    assert q1["verdict"] == "Q1 CLEAN POSITIVE", q1["verdict"]
    assert q1["beats_design"] and q1["beats_realized"]


def test_Q1_null_on_a_painter_that_ignores_the_prior(pairs):
    pool = MT._pool_by_force(pairs)
    rng = random.Random(5)
    chains = []
    for _ in range(14):
        ch, prev = [], None
        for _i in range(40):
            f = rng.choice(FM.ORDER)
            ch.append(MT.Turn(rng.choice(pool[f]), f, prev))
            prev = f
        chains.append(ch)
    assert _ff().q1_two_null(_tcounts(chains))["verdict"] == "Q1 NULL"


def test_Q1_reports_CONFOUNDED_when_mode_collapse_moved_the_marginal(pairs):
    """⛔⛔ THE COUPLING, CAUGHT. This model obeys ki→ka perfectly, so a
    design-null-only test would call it a clean force-transmission result. It
    beats the design null and NOT the realized one, because the collapsed
    marginal is what made ki→ka look distinctive."""
    q1 = _ff().q1_two_null(_tcounts(_collapsed(MT._pool_by_force(pairs), .75, 8)))
    assert q1["verdict"] == "⚠️ Q1 CONFOUNDED BY Q2", q1["verdict"]
    assert q1["beats_design"] and not q1["beats_realized"]


def test_Q2_says_the_uniform_rows_hold_on_a_faithful_corpus(pairs):
    q2 = _ff().q2_rows(_tcounts(MT.build(14, turns=40, pairs=pairs, seed=9)))
    assert q2["n_failed"] == 0, q2["rows"]
    assert all(r["verdict"] == "HOLDS FLAT" for r in q2["rows"].values())
    assert q2["foundation"].startswith("✅")


def test_Q2_CATCHES_mode_collapse_and_does_not_call_it_chance(pairs):
    """⛔⛔ RED-PROOF ON THE FALSE GREEN I SHIPPED FIRST. An earlier version
    branched on the realized-marginal comparison and reported a 75 %-collapsed
    model as CHANCE — "✅ the uniform rows hold flat". Mode-collapse had moved
    the very baseline Q2 measures against, making itself invisible. The uniform
    test must decide FIRST."""
    q2 = _ff().q2_rows(_tcounts(_collapsed(MT._pool_by_force(pairs), .75, 8)))
    assert q2["n_failed"] == 4, q2["rows"]
    assert q2["foundation"].startswith("⚠️ FOUNDATION FINDING")
    assert set(q2["collapsed_to_global_prior"]) == {"ka", "ko", "ku", "kä"}
    for r in q2["rows"].values():
        assert r["holds_flat"] is False


def test_extreme_collapse_STARVES_Q1_and_it_says_so(pairs):
    """⭐ At 95 % collapse there are almost no `ki` priors left. The honest
    answer is UNDERPOWERED, never CHANCE — a null from a starved row is a
    statement about the instrument."""
    q1 = _ff().q1_two_null(_tcounts(_collapsed(MT._pool_by_force(pairs), .95, 8)))
    assert q1["verdict"] == "UNDERPOWERED", q1["verdict"]


def test_the_two_nulls_are_actually_DIFFERENT_objects(pairs):
    """A two-null check whose nulls coincide is one null wearing two names."""
    q1 = _ff().q1_two_null(_tcounts(_collapsed(MT._pool_by_force(pairs), .75, 8)))
    assert q1["design_marginal"] != q1["realized_marginal"]
    assert abs(q1["d_design"] - q1["d_realized"]) > 0.05


def _biased_baseline(pool, ki_ka_rate, seed, *, n=30, turns=40):
    """A stand-in 'run 3' carrying some pre-existing ki→ka regularity."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        ch, prev = [], None
        for _i in range(turns):
            if prev == "ki":
                f = "ka" if rng.random() < ki_ka_rate else rng.choice(FM.ORDER)
            else:
                f = rng.choice(FM.ORDER)
            ch.append(MT.Turn(rng.choice(pool[f]), f, prev))
            prev = f
        out.append(ch)
    return _tcounts(out)


def test_Q1_without_a_baseline_is_CAPPED_at_unattributed(pairs):
    """⛔⛔ A MISSING BASELINE IS EXACTLY HOW PRE-EXISTING STRUCTURE GETS
    CREDITED TO A RUN. Real structure, unknown provenance — say so."""
    q = _ff().q1(_tcounts(MT.build(14, turns=40, pairs=pairs, seed=9)))
    assert q["verdict"] == "⚠️ Q1 POSITIVE (UNATTRIBUTED)", q["verdict"]
    assert q["baseline"] is None


def test_Q1_clean_positive_requires_beating_the_pre_training_baseline(pairs):
    pool = MT._pool_by_force(pairs)
    q = _ff().q1(_tcounts(MT.build(14, turns=40, pairs=pairs, seed=9)),
                 baseline_counts=_biased_baseline(pool, 0.20, 21))
    assert q["verdict"] == "Q1 CLEAN POSITIVE", q["verdict"]
    assert q["beats_baseline"] and q["delta_ci"][0] > 0


def test_Q1_reports_PRE_EXISTING_when_run3_already_had_the_structure(pairs):
    """⭐⭐ THE ATTRIBUTION NULL EARNING ITS KEEP. The multi-turn model transmits
    ki→ka perfectly — and so did the model before training. Nothing is
    attributable to the run, and a chance-only test would have called it a win."""
    pool = MT._pool_by_force(pairs)
    q = _ff().q1(_tcounts(MT.build(14, turns=40, pairs=pairs, seed=9)),
                 baseline_counts=_biased_baseline(pool, 0.97, 22))
    assert q["verdict"] == "⚠️ Q1 PRE-EXISTING", q["verdict"]
    assert q["beats_design"] and not q["beats_baseline"]


def test_a_starved_BASELINE_is_underpowered_not_a_win(pairs):
    """An attribution claim against a starved baseline is a statement about the
    instrument — it must not read as beating it."""
    pool = MT._pool_by_force(pairs)
    q = _ff().q1(_tcounts(MT.build(14, turns=40, pairs=pairs, seed=9)),
                 baseline_counts=_biased_baseline(pool, 0.2, 23, n=1, turns=12))
    assert q["verdict"] == "UNDERPOWERED", q["verdict"]


def test_render_speak_stability_is_pre_declared_NEUTRAL():
    """⛔ The multi-turn row is nearly the single-turn speak row, so a 0.5 mix is
    a small distribution shift and render/speak should barely move. That is
    EXPECTED and proves nothing — crediting a number that did not move is the
    dual of every failure in this ledger."""
    assert _ff().RENDER_SPEAK_STABILITY_IS_NEUTRAL is True


# ══ THE CORPUS WRITER ════════════════════════════════════════════════════
def _builder():
    import importlib.util
    import pathlib
    spec = importlib.util.spec_from_file_location(
        "bmt", pathlib.Path(__file__).parents[1] / "tools/act2_build_multiturn.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_a_provoke_row_resolves_to_the_SHARED_provocation(pairs):
    """⛔⛔ THE TRAIN/SERVE SEAM, ASSERTED END-TO-END. The written row must fold
    into the identical string the arena serves under — not an equal-looking copy."""
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parents[1]
                          / "tools"))
    from act2_finetune import row_messages
    from tlon.discourse import provocation as PV
    # ⚠️ MT.chain, not MT.build — a 4-chain corpus legitimately STARVES cells and
    # build() correctly refuses it. The refusal is not what this test is about.
    pool = MT._pool_by_force(pairs)
    rows = _builder().rows_from(
        [MT.chain(pool, turns=6, rng=random.Random(k)) for k in range(4)])
    msgs = row_messages(rows[0])
    assert msgs[0]["content"] is PV.PROVOCATION or \
        msgs[0]["content"] == PV.PROVOCATION
    assert msgs[1]["content"] == rows[0]["prompt"]


def test_the_provocation_row_is_provoked_by_the_PRIOR_surface(pairs):
    """One row per TRANSITION; a painting with no provocation is a cold start."""
    pool = MT._pool_by_force(pairs)
    chains = [MT.chain(pool, turns=8, rng=random.Random(k)) for k in range(3)]
    rows = _builder().rows_from(chains)
    assert len(rows) == 3 * 7
    for ch in chains:
        for prev, cur in zip(ch, ch[1:]):
            assert any(r["prompt"] == prev.surface and r["surface"] == cur.surface
                       for r in rows)


def test_every_written_target_ROUND_TRIPS(pairs):
    from tlon.grammar.parse import parse, render
    pool = MT._pool_by_force(pairs)
    chains = [MT.chain(pool, turns=8, rng=random.Random(k)) for k in range(6)]
    for r in _builder().rows_from(chains):
        assert render(parse(r["surface"])) == r["surface"]


def test_the_forced_cell_survives_SERIALISATION_not_just_generation(pairs):
    """⭐ The generator obeying the map is not the same claim as the WRITTEN
    corpus obeying it."""
    rows = _builder().rows_from(MT.build(60, turns=10, pairs=pairs, seed=2))
    ki = [r for r in rows if r["prior_force"] == "ki"]
    assert ki
    assert all(r["force"] == "ka" for r in ki)


def test_the_builder_REFUSES_a_fraction_outside_the_open_unit_interval():
    """Mix, don't replace — 0 and 1 are both 'replace'."""
    import subprocess
    import sys
    for bad in ("0", "1", "1.5"):
        r = subprocess.run([sys.executable, "tools/act2_build_multiturn.py",
                            "--multiturn-fraction", bad, "--chains", "2"],
                           capture_output=True, text=True)
        assert r.returncode != 0, bad
