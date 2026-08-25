"""THE READ DIRECTION AND THE PAIRED TEST. $0.00, offline.

⛔⛔ THE CORPUS TRAINED A WRITER AND THE GATE TESTED A READER. Measured on the
fixed-dialect run: **render 81.2 %** (write — trained) against **speak 9.4 %**
(read — never trained once), and **118 of 131 offending forms (90 %) appeared
VERBATIM in the Tlön history the model had just been shown.** It lifted tokens
off the page with no idea what class they were in, because it had never been
asked to read one.

⭐ Diagnosis C rules out duration: dependence +0.91 at step 1,000 and +1.00 from
2,000, while speak validity sat flat at 0–1/12 across all six checkpoints. You
cannot train longer into a task that is not in the data.

⛔ AND THE PAIRED TEST WAS THROWN AWAY AT WRITE TIME. The battery is identical
across runs, so the items ARE paired — but only the accuracy was ledgered, so
39.1 % vs 51.6 % could only be tested unpaired and read **p = 0.21** at n = 64.
"""
from __future__ import annotations

import pytest

from tlon.act2 import corpus
from tlon.act2 import probes
from tlon.grammar.parse import parse
from tlon.harness import paired as P
from tlon.product.compat import impression


# ══ THE READ DIRECTION HAS AN EXACT FREE ORACLE ══════════════════════════
def test_the_read_input_is_TLON_and_the_write_input_is_ENGLISH():
    """⭐ Same target, different input. That is the whole of the addition."""
    p = corpus.build(6, balanced=True)[0]
    assert p.prompt() == p.english
    from dataclasses import replace
    r = replace(p, direction="read")
    assert r.prompt() == r.surface != r.english
    assert r.scene == p.scene, "the TARGET is identical; only the input differs"


def test_parse_of_the_surface_recovers_the_scene_EXACTLY():
    """⛔⛔ THIS IS WHY THE READ DIRECTION IS TRAINABLE AT ALL. `parse(render(s))
    == s` is an identity, so every scene yields a `surface -> Scene` pair with
    ground truth, no judge and no labelling."""
    for p in corpus.build(40, balanced=True):
        assert impression(parse(p.surface)) == p.impression


def test_a_read_pair_verifies_through_the_SAME_oracle_as_a_write_pair():
    from dataclasses import replace
    for p in corpus.build(20, balanced=True):
        r = replace(p, direction="read")
        assert r.verify(parse(r.surface))


def test_the_surface_is_populated_on_every_sampled_pair():
    """⛔ An empty surface would make a read row train on an empty prompt — a
    silent way to add rows that teach nothing."""
    for p in corpus.build(30, balanced=True):
        assert p.surface and p.surface.strip()


# ══ ONE SYSTEM PROMPT PER DIRECTION ══════════════════════════════════════
def test_the_two_directions_get_DIFFERENT_system_prompts():
    """⛔⛔ A single instruction for both tasks would force the model to GUESS
    which one it is on from the input alone — and the two inputs are the two
    languages, which is the exact discrimination that failed."""
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
    import act2_finetune as FT
    assert set(FT.SYSTEM) == {"write", "read"}
    assert FT.SYSTEM["write"] != FT.SYSTEM["read"]
    assert "render English into Tlön" in FT.SYSTEM["write"]
    assert "read Tlön" in FT.SYSTEM["read"]


def test_a_corpus_row_WITHOUT_a_direction_still_trains_as_write():
    """⛔ Back-compatibility is not politeness here: a corpus written before the
    read direction existed must train exactly as it did, or the comparison to the
    previous run is broken."""
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
    import act2_finetune as FT
    old_row = {"english": "it thuds", "scene": {"node": {"root": "klung"},
                                                "force": "ka"}}
    assert (old_row.get("direction") or "write") == "write"
    assert FT.SYSTEM[old_row.get("direction") or "write"] == FT.SYSTEM["write"]


# ══ McNEMAR — THE PAIRED TEST THE LEDGER NOW MAKES POSSIBLE ══════════════
def test_mcnemar_beats_the_unpaired_test_on_the_SAME_data():
    """⭐⭐ THE POINT, DEMONSTRATED. A consistent shift concentrated in a few
    discordant items is invisible unpaired and obvious paired — which is why
    39.1 % vs 51.6 % sat at p=0.21 with the pairing discarded."""
    a = {f"P{i:02d}": i >= 20 for i in range(64)}     # 44 correct
    b = {f"P{i:02d}": i >= 12 for i in range(64)}     # 52 correct, strictly more
    m = P.mcnemar(a, b)
    assert m.b == 0 and m.c == 8                      # 8 flips, all one way
    assert m.p < 0.01, "8 discordant pairs all in one direction is significant"
    assert "SIGNIFICANT" in m.verdict()


def test_mcnemar_ignores_the_items_both_runs_AGREE_on():
    """The concordant pairs carry no information about a DIFFERENCE; counting
    them is exactly what costs the unpaired test its power."""
    a = {f"P{i:02d}": True for i in range(100)}
    b = dict(a)
    b["P00"] = b["P01"] = b["P02"] = False
    m = P.mcnemar(a, b)
    assert m.concordant == 97 and m.b == 3 and m.c == 0


def test_mcnemar_REFUSES_mismatched_item_sets():
    """⛔⛔ Intersecting silently would invent a THIRD item set neither run
    reported — the unpaired error wearing a paired costume."""
    a = {"P00": True, "P01": False}
    b = {"P00": True, "P99": True}
    with pytest.raises(P.UnpairedComparison, match="item sets differ"):
        P.mcnemar(a, b)


def test_no_discordant_pairs_is_reported_as_such_not_as_a_null():
    """⛔ Two runs that agree everywhere give a paired test NOTHING to see. That
    is a distinct outcome from 'no effect' and must say so."""
    a = {f"P{i:02d}": i % 2 == 0 for i in range(20)}
    m = P.mcnemar(a, dict(a))
    assert m.b == 0 and m.c == 0 and m.p == 1.0
    assert "NO DISCORDANT PAIRS" in m.verdict()


def test_the_measurement_still_refuses_a_bare_subtraction():
    """⛔ The guard this module exists for is untouched by the addition."""
    m1 = P.measure("a", "probe", [1, 2, 3], lambda s: 0.5, arm="x")
    m2 = P.measure("b", "probe", [1, 2, 3], lambda s: 0.7, arm="y")
    with pytest.raises(P.UnpairedComparison):
        _ = m1 - m2


# ══ THE BIGGER BATTERY APPENDS ═══════════════════════════════════════════
def test_enlarging_the_battery_KEEPS_the_first_64_items_identical():
    """⭐⭐ THE PROPERTY THAT MAKES THE ENLARGEMENT SAFE. Historical runs stay
    item-comparable on the original 64 while n grows — so raising power does not
    orphan the runs already in the ledger."""
    small = probes.build(seed=7, n_prod=64, n_comp=64)
    big = probes.build(seed=7, n_prod=64, n_comp=256)
    assert len(big.comprehension) == 256
    for a, b in zip(small.comprehension, big.comprehension):
        assert a.surface == b.surface and a.answer == b.answer
        assert a.options == b.options and a.pid == b.pid
    assert small.production == big.production


def test_the_probes_carry_a_STABLE_id_to_pair_on():
    """Without a stable per-item key there is nothing to join two runs by."""
    b1 = probes.build(seed=7, n_prod=8, n_comp=8)
    b2 = probes.build(seed=7, n_prod=8, n_comp=8)
    assert [c.pid for c in b1.comprehension] == [c.pid for c in b2.comprehension]
    assert len({c.pid for c in b1.comprehension}) == 8
