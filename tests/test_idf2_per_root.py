"""§7's per-root readout — the measurement, and the interval's real behaviour.

⛔⛔ THIS INSTRUMENT HAD NO INPUT FOR THE WHOLE CAMPAIGN. The lag read returned
aggregates and discarded the generated surfaces, so the readout §6 names as a
conjunct of PARTIAL and FLOORS could not be computed from a finished run at all.
Runs 1 and 2 died before the read phase, which is the only reason it was never
discovered at the end of one. These tests pin both halves: that the reader can
now save transcripts, and that the readout computed from them means what its
label says.
"""
from __future__ import annotations

import json
import pathlib
import random
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import act2_idf2_per_root as P                                     # noqa: E402
from tlon.discourse import transient as TR                         # noqa: E402


@pytest.fixture(scope="module")
def lex():
    return P._lex_roots()


def surf(roots) -> str:
    return " ".join(sorted(roots)) + " ka"


# ── the marker, inverted ──────────────────────────────────────────────────────

def test_marker_inverse_round_trips_against_the_real_builder(lex):
    """⛔ The inverse is checked against `marker_line`, not against a guess at
    its format. Two spellings of one encoding is the drift this campaign keeps
    paying for."""
    for s in (frozenset(), frozenset(sorted(lex)[:1]), frozenset(sorted(lex)[:4])):
        assert P.marked_from_line(TR.marker_line(s), lex) == s


def test_no_marker_and_empty_marker_are_different_things(lex):
    """⛔⛔ `None` (no annotation shown — the C1 arm) vs `let go: (none)` (a real
    stimulus meaning nothing is barred — M-strip). Collapsing them folds one
    arm into the other at a rate of zero."""
    assert P.marked_from_line(None, lex) is None
    assert P.marked_from_line(TR.marker_line(()), lex) == frozenset()


# ── the observations ──────────────────────────────────────────────────────────

def test_observations_match_a_hand_computation(lex):
    a, b, c, d, e = sorted(lex)[:5]
    chain = [{"surface": surf({a, b}), "marker": None, "refused": False},
             {"surface": surf({a, c}), "marker": TR.marker_line(()), "refused": False},
             {"surface": surf({a, d}), "marker": TR.marker_line({a}), "refused": False},
             {"surface": surf({c, e}), "marker": TR.marker_line({a}), "refused": False}]
    got = P.observations(chain, lex)
    #  t1: roots(t0)={a,b} unmarked — a reappears, b does not
    #  t2: roots(t1)={a,c}, a marked — a reappears, c does not
    #  t3: roots(t2)={a,d}, a marked — neither reappears
    assert sorted((o["turn"], o["root"], o["marked"], o["reappears"])
                  for o in got) == sorted([
        (1, a, False, True), (1, b, False, False),
        (2, a, True, True), (2, c, False, False),
        (3, a, True, False), (3, d, False, False)])
    r = P.rates([got])
    assert r["p_marked"] == pytest.approx(0.5)
    assert r["p_unmarked"] == pytest.approx(0.25)


def test_a_refusal_ends_the_chain_and_is_not_scored(lex):
    """⛔ Scoring 'did the root reappear' against a turn the model never
    produced reads every refusal as a successful letting-go — the flattering
    direction."""
    a, b, c = sorted(lex)[:3]
    chain = [{"surface": surf({a, b}), "marker": None, "refused": False},
             {"surface": surf({a, c}), "marker": TR.marker_line(()), "refused": False},
             {"surface": None, "marker": TR.marker_line({a}), "refused": True}]
    assert {o["turn"] for o in P.observations(chain, lex)} == {1}


def test_an_unmarked_arm_contributes_nothing_unless_held_is_recomputed(lex):
    """The C1 read carries `marker: None` on every turn. Those turns are
    MISSING for the marked/unmarked contrast, not unmarked observations."""
    a, b, c = sorted(lex)[:3]
    chain = [{"surface": surf({a, b}), "marker": None, "refused": False},
             {"surface": surf({a, c}), "marker": None, "refused": False}]
    assert P.observations(chain, lex) == []
    assert len(P.observations(chain, lex, recompute_held=True)) == 2


def test_recomputed_held_equals_what_marker_held_would_have_shown(lex):
    """⭐ The baseline partition must be the SAME rule the M arm was shown, or
    the two are not comparable. Asserted against `act2_idf2.marker_held`
    itself, on the same surfaces."""
    import act2_idf2 as I

    rng = random.Random(5)
    words = sorted(lex)
    surfaces = [surf(set(rng.sample(words, 3))) for _ in range(6)]
    chain = [{"surface": s, "marker": None, "refused": False} for s in surfaces]
    got = P.observations(chain, lex, recompute_held=True)
    for i in range(1, len(surfaces)):
        out = [P._Dot(s) for s in surfaces[:i]]
        expected = P.marked_from_line(I.marker_held(out, lex), lex)
        marked_here = {o["root"] for o in got if o["turn"] == i and o["marked"]}
        assert marked_here == set(expected)


# ── absence is never zero ─────────────────────────────────────────────────────

def test_a_read_without_transcripts_refuses(tmp_path):
    """⛔⛔ The whole reason this file exists. A missing input is a refusal with
    an instruction, never a rate of 0."""
    f = tmp_path / "lag_M.json"
    f.write_text(json.dumps({"lag_profile": {}, "transcripts_saved": False}))
    with pytest.raises(P.NoTranscripts) as exc:
        P.read_one(f)
    assert "--save-transcripts" in str(exc.value)


def test_an_empty_cell_is_missing_not_zero():
    per_chain = [[{"turn": 1, "root": "r", "marked": False, "reappears": True}]]
    r = P.rates(per_chain)
    assert r["p_marked"] is None and r["difference"] is None
    assert r["p_unmarked"] == pytest.approx(1.0)


# ── the interval ──────────────────────────────────────────────────────────────

def _null_chains(seed, chains_n=48, roots=20, p=0.4):
    rng = random.Random(seed)
    return [[{"turn": 1, "root": "r%d" % k, "marked": k % 2 == 0,
              "reappears": rng.random() < p} for k in range(roots)]
            for _ in range(chains_n)]


def test_the_ci_recovers_a_planted_effect():
    rng = random.Random(11)
    chains = [[{"turn": 1, "root": "r%d" % k, "marked": k % 2 == 0,
                "reappears": rng.random() < (0.15 if k % 2 == 0 else 0.55)}
               for k in range(20)] for _ in range(24)]
    ci = P.bootstrap_ci(chains, draws=2000)
    assert ci["excludes_zero"] and ci["hi"] < 0


def test_the_ci_is_resampled_over_chains_not_roots():
    """⛔⛔ The chain is what the experiment re-rolls. A root-level interval is
    narrow in exactly the direction that fires PARTIAL. Here every chain is
    internally constant, so the marked−unmarked difference is identically 0 in
    every cluster and a chain bootstrap must report no spread at all."""
    rng = random.Random(7)
    chains = []
    for _ in range(12):
        hot = rng.random() < 0.5
        chains.append([{"turn": 1, "root": "r%d" % k, "marked": k % 2 == 0,
                        "reappears": hot} for k in range(20)])
    ci = P.bootstrap_ci(chains, draws=2000)
    assert ci["se"] == pytest.approx(0.0, abs=1e-9)
    assert not ci["excludes_zero"]


def test_the_measured_false_positive_rate_has_not_degraded():
    """⛔⛔ THE LABEL IS NOT THE BEHAVIOUR, AND THE NUMBER IS PINNED.

    A cluster bootstrap at these counts is liberal: simulated at 7.0% on a true
    null with 48 chains against a nominal 5%. `USES-MARKER-PARTIAL` fires on
    'CI excludes 0', so an interval that drifts further liberal manufactures
    the cell it is a conjunct of. This asserts a band, not a point — the test
    is Monte Carlo and must not be flaky — but a real regression walks out of
    it. ⭐ `MEASURED_FALSE_POSITIVE` is what the tool PRINTS; if this moves,
    that constant is wrong and the printed caveat lies.
    """
    fires = sum(P.bootstrap_ci(_null_chains(s), draws=600, seed=s)["excludes_zero"]
                for s in range(200))
    rate = fires / 200
    assert 0.02 <= rate <= 0.12, (
        "true-null firing rate %.3f is outside the measured band; the printed "
        "caveat of %.3f no longer describes this interval"
        % (rate, P.MEASURED_FALSE_POSITIVE[48]))


# ── the reader's half ─────────────────────────────────────────────────────────

def test_model_turn_carries_the_marker_it_was_shown():
    """⛔ Without this the M-shuffle arm's readout is unrecoverable: its marker
    is drawn from an RNG and exists nowhere in the surfaces."""
    import act2_model_lag as ML

    t = ML.ModelTurn("fal ka", marker="let go: fal")
    assert t.marker == "let go: fal"
    assert ML.ModelTurn("fal ka").marker is None


def test_transcripts_are_off_by_default_so_no_historical_row_changes():
    """⭐ `C2` in DEVIATIONS is the record of what a silent change to this
    payload costs."""
    import act2_model_lag as ML

    built = [[ML.ModelTurn("fal ka", marker=None)]]
    assert ML._serialise_chains(built) == [
        [{"surface": "fal ka", "marker": None, "refused": False}]]
