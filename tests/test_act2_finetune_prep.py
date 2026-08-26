"""FINE-TUNE PREP — the rulings of 2026-08-24, made mechanical. $0.00, offline.

WHAT THESE CERTIFY
  1. ⛔⛔ F-LOCAL CANNOT BE MEASURED VACUOUSLY. Constrained decoding or a lexicon
     card in context REFUSE, they do not warn. A falsifier that structurally
     cannot fire is not a falsifier.
  2. The card is a parameter, and the no-card path is real — leaving it
     hardcoded would have measured the card-reader and reported it as native.
  3. Every class confusion is mined, whole, from the proposal — not sampled
     from a prose error message.
  4. Balanced sampling raises the WORST-form exposure, which is the number that
     binds; naive sampling starves R while flooding F.
"""
from __future__ import annotations

import pytest

from tlon.act2 import corpus, negatives
from tlon.act2 import falsify
from tlon.act2.llm import LLMSpeaker, ScriptedBackend
from tlon.grammar import classes as C
from tlon.product.proposer import lexicon_card

SCENE = {"node": {"root": "klung"}, "force": "ka"}


# ══ 1. F-LOCAL CANNOT BE MADE VACUOUS ════════════════════════════════════
def test_F_LOCAL_REFUSES_grammar_constrained_decoding():
    """⛔⛔ THE SHARPEST CATCH OF THE ARC, one level down in the stack. Grammar-
    constrained generation makes an invalid emission STRUCTURALLY IMPOSSIBLE, so
    validity is 100 % by construction, F-LOCAL can never fire, and the number
    describes the sampler. This project has shipped a can't-come-back-positive
    test twice already; refusing is the only version that holds."""
    with pytest.raises(falsify.VacuousFalsifier, match="constrained"):
        falsify.f_local(render_rate=1.0, speak_rate=1.0, card=False,
                        constrained_decoding=True)


def test_F_LOCAL_REFUSES_a_lexicon_card_in_context():
    """The bar is explicitly "without the card": with the 233-form table in
    context, decoding is a lookup and the result describes the card."""
    with pytest.raises(falsify.VacuousFalsifier, match="card"):
        falsify.f_local(render_rate=1.0, speak_rate=1.0, card=True,
                        constrained_decoding=False)


@pytest.mark.parametrize("render,speak,fires", [
    (0.95, 0.95, False), (0.50, 1.00, True), (1.00, 0.50, True),
    (0.90, 0.90, False), (0.89, 0.99, True)])
def test_F_LOCAL_fires_on_the_WORST_of_the_two_rates(render, speak, fires):
    """⛔ The worst, not the mean. A model that renders perfectly and cannot hold
    a turn has not internalised the language, and averaging would hide it."""
    f = falsify.f_local(render_rate=render, speak_rate=speak, card=False,
                        constrained_decoding=False)
    assert f.fired is fires


def test_the_native_threshold_matches_the_prompted_one():
    """Both gates ask the same question of different subjects; a different bar
    for each would make the hosted pre-flight non-comparable to the local run."""
    assert falsify.NATIVE_THRESHOLD == falsify.VALID_EMISSION_THRESHOLD == 0.90


# ══ 2. THE CARD IS A PARAMETER ═══════════════════════════════════════════
def test_the_no_card_speaker_really_omits_the_lexicon():
    """⛔⛔ `card` WAS HARDCODED ON. Leaving it would have measured the
    card-reader and reported it as internalised — the crutch-as-competence
    failure the comprehension ceiling already exposed, one level down."""
    card = len(lexicon_card())
    lengths = {}
    for flag in (True, False):
        back = ScriptedBackend([dict(SCENE)] * 3)
        sp = LLMSpeaker("A", back, card=flag)
        sp.speak((), 1)
        lengths[flag] = len(back.calls[0]["system"])
        if not flag:
            body = back.calls[0]["system"]
            assert C.load()["_hash"] not in body
            # ⛔⛔ WAS `list(...)["R"][:20]` PLUS `len < 700`. The length bound
            # was a PROXY for "no table inline" and it ROTTED the moment the
            # prompt legitimately grew (the shared provocation is longer than
            # the CONVERSE string it replaced). Replaced with the property it
            # was standing in for, over EVERY class rather than 20 roots — a
            # strictly stronger check with no free constant left to rot.
            for cls in C.load()["classes"].values():
                for form in cls:
                    assert f"{form} =" not in body, form
    assert lengths[True] - lengths[False] >= card


@pytest.mark.parametrize("kind", ["speak", "render", "choose"])
def test_the_card_flag_reaches_EVERY_task_not_just_one(kind):
    """A flag honoured on `speak` and forgotten on `choose` would leave the
    comprehension half a lookup — which is the exact thing being fixed."""
    back = ScriptedBackend([dict(SCENE), dict(SCENE), {"choice": 0}])
    sp = LLMSpeaker("A", back, card=False)
    if kind == "speak":
        sp.speak((), 1)
    elif kind == "render":
        sp.render("a hollowing", ())
    else:
        sp.choose("nar frem ka", ("a", "b", "c", "d"), ())
    assert C.load()["_hash"] not in back.calls[0]["system"]


# ══ 3. HARD NEGATIVES, MINED WHOLE ═══════════════════════════════════════
def test_the_slot_class_map_is_DERIVED_and_covers_every_class():
    """⭐ Derived by matching each schema field's enum against the lexicon
    classes, so a hand-written second copy cannot drift from the gate."""
    m = negatives.slot_class_map()
    assert set(m.values()) == set(C.load()["classes"])
    assert m["root"] == "R" and m["aspect_root"] == "A" and m["relator"] == "L"


def test_the_derivation_RAISES_if_a_class_stops_being_reachable(monkeypatch):
    lex = {k: v for k, v in C.load()["classes"].items()}
    trimmed = dict(C.load())
    trimmed["classes"] = dict(lex, Z={"zzz": "an invented class"})
    monkeypatch.setattr(C, "load", lambda: trimmed)
    with pytest.raises(negatives.MiningError, match="Z"):
        negatives.slot_class_map()


def test_the_four_REAL_hosted_failures_mine_correctly():
    """⭐ The measured failures, replayed. Every one is a misassignment of a real
    form — the finding that says a fine-tune is the right instrument."""
    proposals = [
        {"node": {"root": "klung", "aspect_root": "pal"}, "force": "ka"},
        {"node": {"root": "klung", "aspect_root": "rän"}, "force": "ka"},
        {"node": {"root": "plas"}, "force": "ka"},
        {"node": {"root": "klung",
                  "edges": [{"relator": "hul", "node": {"root": "frem"}}]},
         "force": "ka"}]
    m = negatives.mine(proposals)
    assert m["n_errors"] == 4 and m["misassigned"] == 4 and m["invented"] == 0
    assert m["by_confusion"] == {"R→A": 2, "O→R": 1, "O→L": 1}


def test_an_invented_form_is_distinguished_from_a_misassignment():
    """⛔ Different failures needing different fixes: one is trainable class
    discipline, the other is hallucination. Measured hosted: 0 inventions."""
    m = negatives.mine([{"node": {"root": "NOT-A-WORD"}, "force": "ka"}])
    assert m["invented"] == 1 and m["misassigned"] == 0


def test_EVERY_error_in_a_proposal_is_mined_not_just_the_first():
    """⛔ The gate raises on the first; that is what truncated the record. A
    proposal with three confusions must yield three negatives."""
    bad = {"node": {"root": "plas", "aspect_root": "pal",
                    "edges": [{"relator": "hul", "node": {"root": "frem"}}]},
           "force": "ka"}
    assert len(negatives.class_errors(bad)) == 3


def test_a_negative_carries_the_CORRECTION_not_only_the_error():
    """"not A" alone does not say where the form belongs, and the failure is a
    misassignment — so the correction is exactly the thing to teach."""
    errs = negatives.class_errors(
        {"node": {"root": "klung", "aspect_root": "pal"}, "force": "ka"})
    item = corpus.negative_examples(errs)[0]
    assert item["true_class"] == "R" and item["correct_slot"] == "root"
    assert item["gloss"] == C.load()["classes"]["R"]["pal"]


# ══ 4. EXPOSURE, NOT COVERAGE ════════════════════════════════════════════
def test_coverage_is_satisfied_by_FREE_sampling_and_is_not_the_problem():
    """⛔ Measured: naive sampling already covers 9/9 classes at 100 % of forms.
    Reporting coverage as if it were the risk would hide the real one."""
    rep = corpus.exposure_report(corpus.build(1200, balanced=False))
    for cls, row in rep["by_class"].items():
        assert row["covered"] == row["forms"], cls


def test_the_STARVED_class_is_R_which_is_the_opposite_of_the_intuition():
    """⛔⛔ THE MEASUREMENT REFUTED THE PREMISE THIS WAS BUILT ON. The stated
    worry was that free sampling starves the SMALL classes. It does the reverse:
    a class with few forms concentrates its exposure, a class with many spreads
    it thin. R holds 67 % of the lexicon in one slot per node."""
    rep = corpus.exposure_report(corpus.build(2000, balanced=False))
    by_class = rep["by_class"]
    worst = min(by_class, key=lambda c: by_class[c]["min_form_exposure"])
    assert worst == "R", f"the starved class is {worst}, not R"
    assert (by_class["F"]["min_form_exposure"]
            > 5 * by_class["R"]["min_form_exposure"])


def test_balanced_sampling_raises_the_WORST_form_exposure():
    """⭐ The binding number is the least-seen form: that is the one the
    fine-tune will fail on, and an average hides it."""
    naive = corpus.exposure_report(corpus.build(2000, balanced=False))
    bal = corpus.exposure_report(corpus.build(2000, balanced=True))
    assert bal["worst_form_exposure"] > naive["worst_form_exposure"]
    assert bal["exposure_spread"] < naive["exposure_spread"]


def test_balanced_sampling_is_near_EXACT_within_a_class():
    """Round-robin over the least-exposed forms, so no form inside a class is
    starved relative to its neighbours."""
    rep = corpus.exposure_report(corpus.build(2000, balanced=True))
    for cls, row in rep["by_class"].items():
        spread = row["max_form_exposure"] - row["min_form_exposure"]
        assert spread <= 2, f"{cls} varies by {spread} within the class"


def test_a_short_corpus_RAISES_rather_than_being_returned(monkeypatch):
    """⛔ A corpus quietly smaller than asked for changes every exposure figure
    computed on it. Reached by making validation fail, which is the only honest
    way to exercise the branch."""
    from tlon.act2 import probes
    monkeypatch.setattr(probes, "_validate", lambda *a, **kw: None)
    with pytest.raises(RuntimeError, match="corpus short"):
        corpus.build(10, balanced=True)


def test_targeted_positives_actually_raise_the_confused_forms():
    """⭐⭐ THE MECHANISM THAT MAKES THE MINED FAILURES MATTER. A causal LM has no
    loss for a token it did not emit, so "`pal` is not an aspect" cannot be shown
    as a negative example. The contrastive signal has to arrive as extra
    sightings of the confused form IN ITS CORRECT SLOT. Without this, the failure
    log is a diagnosis nobody acts on."""
    confused = {"pal": 60, "rän": 60}
    plain = corpus.class_exposure(corpus.build(3000, balanced=True))
    boosted = corpus.class_exposure(
        corpus.build(3000, balanced=True, focus_forms=confused))
    for form in confused:
        assert boosted["R"][form] > plain["R"][form], form
    # and it must not be bought by starving the rest of the class
    others = [f for f in plain["R"] if f not in confused]
    assert min(boosted["R"][f] for f in others) > 0


def test_boosting_an_INVENTED_form_is_refused():
    """⛔ An invented form has no correct slot to be shown in. Inventions and
    misassignments are different failures and more exposure fixes only one of
    them — measured hosted: 4 misassignments, 0 inventions."""
    with pytest.raises(ValueError, match="not a Tlön form"):
        corpus.build(50, focus_forms={"NOT-A-WORD": 10})


def test_the_oracle_is_exact_and_costs_nothing():
    """`Scene → gloss → model → Scene′`, accepted iff the IMPRESSIONS match —
    two renderings can differ on the surface and mean the same thing."""
    pairs = corpus.build(20, balanced=True)
    for p in pairs:
        assert p.verify(p.scene)
        assert p.english == __import__(
            "tlon.grammar.gloss", fromlist=["gloss"]).gloss(p.scene)
    other = pairs[0].scene if pairs[0].impression != pairs[1].impression else None
    if other is not None:
        assert not pairs[1].verify(other)
