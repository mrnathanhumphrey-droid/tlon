"""§8.2 — CLOSING THE RENDER GAP. $0, offline.

⛔⛔ THE BRIEF NAMED THE WRONG INSTRUMENT AND THE CORPUS SAID SO. §8.2 asks for
"the small-class targeted positives". Measured on the corpus that trained run 3,
per-form exposure was already FLAT — A 663, M 663, Q 662, T 649, D 670 — and the
four forms targeted after the hosted pre-flight (`pal` `rän` `plas` `hul`) appear
in **none** of the n=256 confusions. More positives on forms with 663 sightings
apiece cannot be the missing ingredient.

⭐⭐ ERRORS TRACK SLOT RARITY, NOT FORM RARITY. `root` is 100 % occupied, holds
156 forms, and produced 8 missed-slot errors. `aspect_root` is 3.9 % occupied,
holds 6 forms, and produced 16 — the single biggest hole. The model has seen
every A-form 663 times and still has not learned WHICH SLOT IS AN A-SLOT, because
it has only seen one filled once every 26 nodes.

**Exposure teaches the form. Occupancy teaches the function. Only one of them was
ever reported.**
"""
from __future__ import annotations

import pathlib

import pytest

from tlon.act2 import corpus
from tlon.act2.negatives import ClassError, slot_class_map
from tlon.grammar import classes as C

LEDGER = pathlib.Path("runs/act2/harden/ledger_harden.jsonl")


def _occupancy(pairs, slot):
    nodes = [n for p in pairs for n in corpus._walk(p.scene.node)]  # noqa: SLF001
    if slot == "aspect_root":
        return sum(1 for n in nodes if n.aspect) / len(nodes)
    return sum(1 for n in nodes if getattr(n, slot) is not None) / len(nodes)


# ══ THE FLOOR DOES WHAT IT SAYS ══════════════════════════════════════════
def test_without_a_floor_the_rare_slots_stay_rare():
    """⛔ THE BASELINE THIS EXISTS TO CHANGE. Reproduces run 3's shape."""
    pairs = corpus.build(600, seed=1)
    assert _occupancy(pairs, "aspect_root") < 0.10
    assert _occupancy(pairs, "modal") < 0.12


def test_the_floor_raises_every_floored_slot():
    pairs = corpus.build(600, seed=1, slot_floor=0.30)
    for slot in ("aspect_root", "modal", "quant", "tense", "degree"):
        occ = _occupancy(pairs, slot)
        assert occ > 0.20, f"{slot} occupancy {occ:.1%} did not rise"


def test_the_floor_does_NOT_starve_per_form_exposure():
    """⛔⛔ THE HALF THAT COULD GO WRONG SILENTLY. Raising slot occupancy while
    losing per-form balance would trade one failure mode for the one the
    balancer was built to fix. Both must hold at once."""
    plain = corpus.exposure_report(corpus.build(1200, seed=1))
    floored = corpus.exposure_report(corpus.build(1200, seed=1, slot_floor=0.30))
    for cls in corpus.FLOORED_CLASSES:
        assert (floored["by_class"][cls]["min_form_exposure"]
                >= plain["by_class"][cls]["min_form_exposure"]), cls


def test_orient_is_deliberately_NOT_floored():
    """⭐ O sits at ~31 % effective occupancy already and caused 2 of 48 errors.
    Flooring it would spend tokens on a slot the model has learned."""
    assert "O" not in corpus.FLOORED_CLASSES


def test_the_floor_is_off_by_default_so_run_3_stays_reproducible():
    lex = C.load()["classes"]
    assert corpus._decoration_p(lex) == corpus._decoration_p(lex, slot_floor=None)


def test_the_default_decoration_probability_is_what_made_the_slots_rare():
    """Pins the mechanism, so the explanation cannot drift from the code."""
    lex = C.load()["classes"]
    p = corpus._decoration_p(lex)
    assert p["A"] == pytest.approx(len(lex["A"]) / len(lex["R"]))
    assert p["A"] < 0.05


# ══ THE LIST IS MINED, NOT MAINTAINED ════════════════════════════════════
@pytest.mark.skipif(not LEDGER.exists(), reason="ledger not on this machine")
def test_confusions_are_mined_from_the_run_ledger():
    errs = corpus.mined_confusions(LEDGER)
    assert len(errs) == 48, f"expected the n=256 run's 48 confusions, got {len(errs)}"
    assert all(e.form and e.actual and e.expected for e in errs)


@pytest.mark.skipif(not LEDGER.exists(), reason="ledger not on this machine")
def test_THE_STALE_LIST_IS_DEMONSTRABLY_STALE():
    """⛔⛔ THE FINDING, PINNED. Three of the four hand-kept targets were fixed
    runs ago and were still being boosted. If this ever fails because one
    reappears, the boost genuinely stopped working and that is worth knowing."""
    live = {e.form for e in corpus.mined_confusions(LEDGER)}
    fixed = {"pal", "rän", "plas"} - live
    assert fixed == {"pal", "rän", "plas"}, (
        "these were being boosted long after they stopped being confused")


@pytest.mark.skipif(not LEDGER.exists(), reason="ledger not on this machine")
def test_the_measured_boundaries_match_the_run():
    """⛔ READ THE ARTEFACT. The top boundary is M/R at 8, not the L/M the
    summary named."""
    b = corpus.boundaries(corpus.mined_confusions(LEDGER))
    assert b[("M", "R")] == 8
    assert b.most_common(1)[0][0] == ("M", "R")


def test_a_missing_ledger_is_REFUSED_not_defaulted():
    with pytest.raises(Exception, match="no ledger"):
        corpus.mined_confusions("runs/act2/does_not_exist.jsonl")


# ══ THE MINIMAL PAIRS ════════════════════════════════════════════════════
CONF = [ClassError(form="nol", used_as="aspect_root", expected="A", actual="Q")]


def test_contrastive_pairs_come_in_twos_one_slot_apart():
    got = corpus.contrastive_pairs(CONF, per_confusion=6, seed=3)
    assert got, "no pairs produced"
    slots = slot_class_map()
    # every row is a legal scene with a true gloss — nothing here is a negative
    for p in got:
        assert p.source == "contrastive"
        assert p.english and p.surface
    forms = {n.quant for p in got for n in corpus._walk(p.scene.node)}  # noqa: SLF001
    assert "nol" in forms, "the confused form must appear in ITS OWN slot"
    assert slots["quant"] == "Q"


def test_the_pair_shows_BOTH_readings_not_just_the_correction():
    """⭐ THE POINT. One row puts `nol` in the quant slot; its partner puts a
    real A-form in the aspect slot. Two correct sentences, chosen so the
    difference between them is the lesson."""
    got = corpus.contrastive_pairs(CONF, per_confusion=8, seed=3)
    has_quant = any(n.quant == "nol"
                    for p in got for n in corpus._walk(p.scene.node))  # noqa: SLF001
    has_aspect = any(n.aspect for p in got for n in corpus._walk(p.scene.node))  # noqa: SLF001
    assert has_quant and has_aspect


def test_contrastive_pairs_are_deterministic():
    a = corpus.contrastive_pairs(CONF, per_confusion=4, seed=7)
    b = corpus.contrastive_pairs(CONF, per_confusion=4, seed=7)
    assert [p.surface for p in a] == [p.surface for p in b]


def test_every_contrastive_row_round_trips_through_the_oracle():
    """⛔ The free exact oracle applies here too — a contrastive row that does
    not survive `parse(render(s)) == s` is not a training example, it is a bug."""
    from tlon.grammar.parse import parse
    for p in corpus.contrastive_pairs(CONF, per_confusion=6, seed=11):
        assert parse(p.surface) == p.scene


def test_a_confusion_with_no_true_class_is_skipped_not_crashed():
    """A refusal with an absent field has no correct slot to teach."""
    bad = [ClassError(form="x", used_as="root", expected="R", actual=None)]
    assert corpus.contrastive_pairs(bad, per_confusion=4) == []
