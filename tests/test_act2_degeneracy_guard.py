"""RULING 5 — THE ABSOLUTE DEGENERACY GUARD. $0, offline.

⛔⛔ THE DEFECT THIS EXISTS FOR IS NOT HYPOTHETICAL: F4 READ "no degeneration
signature" ON THE 40-TURN EXCHANGE PROBE — 6 distinct utterances in 18 legal
turns, sharing a byte-identical 8-token prefix. Both of F4's branches are
RELATIVE and both read +0.0 %:

    within-arm decline   TTR was ALREADY 0.125 at the first window, so there
                         was no decline left to see
    level-vs-control     the control was equally degenerate (0.125 vs 0.125),
                         shortfall +0.0 %

⭐⭐ A RELATIVE MEASURE HAS NO OPINION WHEN BOTH ARMS ARE ON THE FLOOR — and
"both arms degenerate" is the case the probe actually measured. That is the
whole finding, and σ_cp must not inherit the shape: a coupling term defined as a
CHANGE reads 0 on a pair stuck from turn zero, and 0 there means "independent,
no pact", which is the exact opposite of the truth.

⛔ THE TWO THRESHOLDS NEVER SAW THE DEGENERATION. Both come from the corpus null
alone (root-TTR over 8-scene windows: min 0.700 over 2,500 windows; token
overlap between random corpus pairs: max 0.500 over 20,000 pairs). The measured
event's distance from each is a MARGIN, not the thing that placed the line.
"""
from __future__ import annotations

import json
import pathlib
import random

import pytest

from tlon.act2 import falsify as F

PROBE = pathlib.Path("runs/act2/harden/exchange_probe.json")
CORPUS = pathlib.Path("runs/act2/corpus/train.jsonl")


def _roots_from_tokens(surface: str) -> list[str]:
    """A stand-in root extractor so the unit tests never need the parser."""
    return surface.split()


# ══ THE MEASURED FAILURE, REPRODUCED FROM SYNTHETIC DATA ═════════════════
#: The six real utterances, verbatim from `runs/act2/harden/exchange_probe.json`.
#: ⭐ They are the fixture BECAUSE they defeated two pre-specified criteria: an
#: equality check cannot see `nimnimnimas` → `nimnimnimnimas`, and a positional
#: check cannot see `krax hrem` → `hrem krax`.
DEGENERATE = [
    "nol tim ung xom sim fen xun tan krax hrem nimnimnimas ram hunhunhunhunas ki",
    "nol tim ung xom sim fen xun tan krax hrem nimnimnimnimas ram hunas ki",
    "nol tim ung xom sim fen xun tan krax nimnimnimas hrem hunhunhunhunas ram ki",
    "nol tim ung xom sim fen xun tan hrem nimnimnimnimas krax hunas ram ki",
    "nol tim ung xom sim fen xun tan krax nimnimnimas hrem hunas ram ki",
    "nol tim ung xom sim fen xun tan krax nimnimnimnimas hrem hunas ram ki",
]


def test_the_absolute_guard_FIRES_on_the_measured_degeneration():
    """⛔⛔ THE POINT OF THE WHOLE MODULE."""
    g = F.degeneracy_guard(DEGENERATE, roots_of=_roots_from_tokens)
    assert g.fired
    assert g.floor_fired and g.repetition_fired


def test_a_decline_measure_reads_ZERO_on_it_which_is_why_absolute_is_needed():
    """⭐ THE CONTROL FOR THIS TEST IS THE OLD MEASURE. If a decline-based read
    ever starts catching this, the fixture has drifted and the lesson is lost."""
    first = DEGENERATE[:3]
    last = DEGENERATE[3:]

    def ttr(ws):
        toks = [t for s in ws for t in s.split()]
        return len(set(toks)) / len(toks)

    decline = (ttr(first) - ttr(last)) / ttr(first)
    assert abs(decline) < 0.25, (
        "the decline-based measure must read ~0 here — that is the defect")


def test_exact_match_and_cycle_checks_MISS_it_but_overlap_does_not():
    """⛔ The jitter is real: every pair differs, so no equality test fires."""
    assert len(set(DEGENERATE)) == len(DEGENERATE), "all six are distinct"
    pairs = [F.token_overlap(a, b)
             for i, a in enumerate(DEGENERATE) for b in DEGENERATE[i + 1:]]
    assert min(pairs) > F.NEAR_REPETITION_CEILING_SINGLE_TURN_NULL, (
        "every pair must clear the ceiling despite all six being distinct")


def test_reduplication_jitter_alone_defeats_equality_and_not_overlap():
    a = "nol tim krax hunas ki"
    b = "nol tim krax hunhunhunhunas ki"
    assert a != b
    assert F.token_overlap(a, b) >= 0.8


def test_sibling_reordering_alone_defeats_a_positional_check_and_not_overlap():
    a = "nol tim krax hrem ram ki"
    b = "nol tim hrem krax ram ki"
    assert a != b
    assert F.token_overlap(a, b) == 1.0


# ══ THE OTHER END — A LEGITIMATE NO-OP MUST NOT BE RED ═══════════════════
def test_varied_utterances_do_NOT_fire():
    """⛔⛔ A guard that fires on everything blocks the arena while looking
    rigorous. This is the half that keeps it honest."""
    varied = [f"r{i} o{i} t{i} m{i} ka" for i in range(20)]
    g = F.degeneracy_guard(varied, roots_of=_roots_from_tokens)
    assert not g.fired


def test_a_repeated_couplet_in_a_long_healthy_exchange_does_NOT_fire():
    """⭐ ONE incident of repetition is not a collapse — the share threshold is
    what separates 'they echoed once' from 'they are stuck'."""
    varied = [f"r{i} o{i} t{i} m{i} ka" for i in range(20)]
    exchange = varied + ["r0 o0 t0 m0 ka", "r0 o0 t0 m0 ka"]
    g = F.degeneracy_guard(exchange, roots_of=_roots_from_tokens)
    assert not g.fired, "a single repeated couplet is not degeneration"


@pytest.mark.parametrize("n_distinct,fires", [(1, True), (2, True), (20, False)])
def test_the_floor_separates_impoverished_from_varied(n_distinct, fires):
    utts = [f"r{i % n_distinct} o{i % n_distinct} ka" for i in range(20)]
    assert F.degeneracy_guard(utts, roots_of=_roots_from_tokens).fired is fires


# ══ THE REFUSAL ══════════════════════════════════════════════════════════
def test_one_utterance_is_REFUSED_not_scored_clean():
    """⛔ 'Not degenerate' from a sample with no repetition to measure would be a
    verdict from no evidence — the shape that produced the 0/64 comprehension
    read."""
    with pytest.raises(F.FalsifierError, match="at least 2 utterances"):
        F.degeneracy_guard(["nol tim ka"])


def test_zero_utterances_is_REFUSED_too():
    with pytest.raises(F.FalsifierError):
        F.degeneracy_guard([])


# ══ F4'S WIRING ══════════════════════════════════════════════════════════
BOTH_ON_THE_FLOOR_I = [{"root_ttr": 0.125}, {"root_ttr": 0.125}]
BOTH_ON_THE_FLOOR_C = [{"root_ttr": 0.125}, {"root_ttr": 0.125}]


def test_F4_WITHOUT_surfaces_still_misses_it_and_SAYS_SO():
    """⛔ The blind path is kept so no existing caller changes meaning silently —
    but it must ANNOUNCE that it is blind rather than reporting a clean null."""
    f = F.f4_degeneration(BOTH_ON_THE_FLOOR_I, BOTH_ON_THE_FLOOR_C)
    assert not f.fired
    assert "absolute reading NOT RUN" in f.detail


def test_F4_WITH_surfaces_catches_what_both_relative_branches_missed():
    f = F.f4_degeneration(BOTH_ON_THE_FLOOR_I, BOTH_ON_THE_FLOOR_C,
                          interacting_surfaces=DEGENERATE)
    assert f.fired
    assert "BOTH ARMS ON THE FLOOR" in f.detail


def test_F4s_PRE_REGISTERED_branch_is_NOT_weakened_by_the_supplement():
    """⛔⛔ The supplement may only ADD firings. A slow within-arm collapse that
    fired before must still fire, surfaces or not."""
    slow_i = [{"root_ttr": 0.90}, {"root_ttr": 0.10}]
    slow_c = [{"root_ttr": 0.90}, {"root_ttr": 0.88}]
    healthy = [f"r{i} o{i} ka" for i in range(20)]
    assert F.f4_degeneration(slow_i, slow_c).fired
    assert F.f4_degeneration(slow_i, slow_c, interacting_surfaces=healthy).fired


def test_a_genuinely_healthy_pair_stays_clear_through_F4():
    ok_i = [{"root_ttr": 0.90}, {"root_ttr": 0.88}]
    ok_c = [{"root_ttr": 0.90}, {"root_ttr": 0.89}]
    healthy = [f"r{i} o{i} t{i} ka" for i in range(20)]
    assert not F.f4_degeneration(ok_i, ok_c, interacting_surfaces=healthy).fired


# ══ THE THRESHOLDS ARE DERIVED, AND THE DERIVATION IS PINNED ═════════════
def test_the_caveat_is_in_the_NAME_not_only_the_prose():
    """⭐ The near-repetition ceiling is calibrated against the SINGLE-TURN null
    because no multi-turn corpus exists yet. That caveat decays if it lives only
    in a comment, so it lives in the identifier."""
    assert hasattr(F, "NEAR_REPETITION_CEILING_SINGLE_TURN_NULL")
    assert not hasattr(F, "NEAR_REPETITION_CEILING")


def test_the_floor_sits_BELOW_the_corpus_minimum_so_healthy_text_cannot_fire():
    """Corpus root-TTR over 8-scene windows had minimum 0.700 (n=2,500)."""
    assert F.DEGENERACY_TTR_FLOOR < 0.700


def test_the_ceiling_sits_ABOVE_the_random_pair_maximum():
    """Random unrelated corpus pairs maxed at 0.500 over 20,000 draws."""
    assert F.NEAR_REPETITION_CEILING_SINGLE_TURN_NULL > 0.500


# ══ AGAINST THE REAL ARTEFACTS, WHEN THEY ARE ON THE MACHINE ═════════════
@pytest.mark.skipif(not PROBE.exists(), reason="exchange probe not on this machine")
def test_against_the_REAL_probe_artefact_both_arms_read_degenerate():
    """⛔ READ THE RUN ARTEFACT, DO NOT RE-DERIVE IT."""
    d = json.loads(PROBE.read_text(encoding="utf-8"))
    for arm in ("transcript_interacting", "transcript_control"):
        surfaces = [s for s in d[arm] if s]
        assert F.degeneracy_guard(surfaces).fired, f"{arm} must read degenerate"


@pytest.mark.skipif(not CORPUS.exists(), reason="corpus not on this machine")
def test_against_the_REAL_corpus_healthy_windows_do_NOT_fire():
    """⛔⛔ THE FALSE-POSITIVE HALF, MEASURED ON REAL TEXT. 0/200 at build time."""
    rng = random.Random(20620)
    surfaces = []
    with CORPUS.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row["direction"] == "write":
                surfaces.append(row["surface"])
            if len(surfaces) >= 20000:
                break
    fires = sum(F.degeneracy_guard(rng.sample(surfaces, 40)).fired
                for _ in range(50))
    assert fires == 0, f"{fires}/50 healthy corpus windows fired"
