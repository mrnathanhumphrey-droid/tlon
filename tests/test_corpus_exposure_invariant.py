"""THE BOOST IS A "CONSTANT" THAT WAS SECRETLY A FUNCTION OF THE DATA. $0.

⛔⛔ A NEW ENTRY IN THIS PROJECT'S FAILURE CATALOG, NOT A REPEAT OF ONE.

Run 5 held tokens (+0.03 %), steps (+3.3 %), seq, batch, battery, decoding and
hardware — **every variable that LOOKS like a variable** — and was confounded
anyway, because `focus = {form: 60 × times_confused}` is not a constant. It is a
FUNCTION OF THE CORPUS. Four hand-picked forms became 89 mined confusions and the
total boost went **240 → 5,340, a 22× move nobody had named.**

    run 3   4 forms ·   240 total · M-class exposure FLAT 663–664 (1.002×)
    run 5  42 forms · 5,340 total · `nem` 2,563 = 34.9 % of ALL M exposure

⭐⭐ THAT IS THE HARDEST CONFOUND TO CATCH: not a variable someone forgot to
hold, but a "constant" coupled to the thing that changed. It moved because the
DATA moved. Nothing in the held-variable list named it, so nothing could notice,
and a broken corpus trained for 93 minutes and produced an uninterpretable
render number.

⇒ **THE INVARIANT IS THE TOTAL BOOST**, and the exposure balance is checked
before a corpus may be written.
"""
from __future__ import annotations

import pytest

from tlon.act2 import corpus
from tlon.grammar import classes as C


# ══ THE BUDGET IS FIXED, NOT PER-FORM ════════════════════════════════════
@pytest.mark.parametrize("n_forms", [1, 4, 42, 200])
def test_the_total_boost_does_NOT_grow_with_the_number_of_confusions(n_forms):
    """⛔⛔ THE WHOLE POINT. The old rule multiplied by 22× between two runs
    purely because the mined list got longer."""
    counts = {f"form{i}": (i % 7) + 1 for i in range(n_forms)}
    budget = corpus.focus_budget(counts, n_pairs=41_000)
    total = sum(budget.values())
    cap = round(corpus.FOCUS_BOOST_FRACTION * 41_000)
    assert total <= cap + n_forms, (
        f"{n_forms} forms produced a total boost of {total}; the budget is {cap}")


def test_the_OLD_rule_would_FAIL_this_and_that_is_the_point():
    """⛔ The red-proof, as a test. Reconstruct run 5's list under the old rule
    and watch it blow the budget by 22×."""
    # run 5's real shape: 89 confusions over 42 distinct forms
    counts = {f"f{i}": c for i, c in enumerate([25] + [3] * 8 + [2] * 10 + [1] * 20)}
    assert sum(counts.values()) == 89
    old_total = sum(60 * c for c in counts.values())
    assert old_total == 5340, old_total
    cap = round(corpus.FOCUS_BOOST_FRACTION * 41_000)
    assert old_total > 20 * cap, "run 5's boost really was ~22x the budget"
    new_total = sum(corpus.focus_budget(counts, n_pairs=41_000).values())
    assert new_total <= cap + len(counts)


def test_the_budget_SCALES_with_the_corpus_not_just_the_list():
    """⛔⛔ THE BUG IN MY FIRST FIX. An absolute cap of 240 is harmless against
    41,000 pairs and enormous against 1,500 — a constant coupled to CORPUS SIZE
    instead of list length. Same shape, one level down."""
    small = sum(corpus.focus_budget({"a": 1}, n_pairs=1_500).values())
    large = sum(corpus.focus_budget({"a": 1}, n_pairs=41_000).values())
    assert large > small * 5


def test_n_pairs_is_REQUIRED_so_it_cannot_become_a_hidden_constant():
    with pytest.raises(TypeError):
        corpus.focus_budget({"a": 1})


def test_the_budget_still_TARGETS_proportionally():
    """⭐ The mechanism run 3 proved must survive: a form confused 10× gets more
    than one confused once. Only the TOTAL is capped."""
    b = corpus.focus_budget({"often": 20, "rarely": 1}, n_pairs=41_000)
    assert b["often"] > b["rarely"] * 5


def test_every_mined_form_still_gets_at_least_one():
    """A form that was confused must not be dropped by rounding."""
    b = corpus.focus_budget({f"f{i}": 1 for i in range(500)}, n_pairs=41_000)
    assert all(v >= 1 for v in b.values())


def test_an_empty_mining_result_yields_an_empty_budget():
    assert corpus.focus_budget({}, n_pairs=41_000) == {}


# ══ THE EXPOSURE INVARIANT IS CHECKED, NOT ASSUMED ═══════════════════════
def test_a_balanced_corpus_PASSES_the_fairness_check():
    pairs = corpus.build(1500, seed=5)
    rep = corpus.check_exposure_fairness(pairs)
    assert rep["worst_ratio"] >= corpus.MIN_EXPOSURE_FAIRNESS


def test_a_run5_shaped_boost_is_REFUSED_before_it_can_be_written():
    """⛔⛔ THE RED-PROOF ON THE REAL FAILURE. `nem` took 34.9 % of all
    evidential exposure and nothing complained. Now it raises."""
    lex = C.load()["classes"]
    victim = sorted(lex["M"])[0]
    pairs = corpus.build(1500, seed=5, focus_forms={victim: 6000})
    with pytest.raises(corpus.CorpusError, match="EXPOSURE COLLAPSE"):
        corpus.check_exposure_fairness(pairs)


def test_the_refusal_NAMES_the_class_and_the_numbers():
    """A refusal that does not say which class collapsed, and by how much,
    leaves the reader to re-derive it."""
    lex = C.load()["classes"]
    victim = sorted(lex["M"])[0]
    pairs = corpus.build(1500, seed=5, focus_forms={victim: 6000})
    with pytest.raises(corpus.CorpusError) as e:
        corpus.check_exposure_fairness(pairs)
    msg = str(e.value)
    assert "class M" in msg and "sightings" in msg and "mean" in msg


def test_the_boost_the_NEW_rule_produces_passes_the_fairness_check():
    """⭐ The two halves have to be compatible: the capped budget must actually
    survive the invariant it was written to protect."""
    counts = {f: c for f, c in
              zip(sorted(C.load()["classes"]["M"]), [25, 5, 4, 3, 2, 2, 1, 1, 1, 1])}
    pairs = corpus.build(1500, seed=5,
                         focus_forms=corpus.focus_budget(counts, n_pairs=1500))
    assert corpus.check_exposure_fairness(pairs)["worst_ratio"] >= \
        corpus.MIN_EXPOSURE_FAIRNESS


def test_the_constants_are_declared_and_explained():
    """⚠️ Both are pre-registration-adjacent: moving either changes what a run
    means, so it should be a visible decision."""
    assert corpus.FOCUS_BOOST_FRACTION == 240 / 41_000
    assert 0.0 < corpus.MIN_EXPOSURE_FAIRNESS < 1.0
