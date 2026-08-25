"""The Phase 9.0 comparison guard. Lives in the suite, not only in a tool.

`tools/guard_redproof.py` is the phase gate and runs the mutation (battery vs a
decorative guard). These are the unit-level invariants, so a change to the
guard that keeps the tool green but breaks the mechanism still fails.
"""
from __future__ import annotations

import pytest

from tlon.harness.paired import (ConfoundedContrast, DegenerateContrast,
                                 ItemIdentityError, ItemSet, Measurement,
                                 UnpairedComparison, measure, paired_delta,
                                 side_by_side)

ITEMS = [f"eval-{i:03d}" for i in range(50)]


def mk(name, value, keys=ITEMS, kind="eval-row", **facets):
    return Measurement(name, value, ItemSet.of(kind, keys, **facets))


# ── item identity cannot be faked ─────────────────────────────────────────
def test_digest_is_over_the_items_not_a_label():
    """Two sets of the same SIZE and KIND must not collide."""
    a = ItemSet.of("eval-row", [f"a{i}" for i in range(50)])
    b = ItemSet.of("eval-row", [f"b{i}" for i in range(50)])
    assert a.n == b.n and a.digest != b.digest


def test_digest_is_order_independent():
    a = ItemSet.of("eval-row", ITEMS)
    b = ItemSet.of("eval-row", list(reversed(ITEMS)))
    assert a == b


def test_empty_item_set_refused():
    """Two empty sets compare EQUAL, which would pair two vacuous numbers."""
    with pytest.raises(ItemIdentityError, match="empty"):
        ItemSet.of("eval-row", [])


def test_duplicate_keys_refused():
    with pytest.raises(ItemIdentityError, match="duplicate"):
        ItemSet.of("eval-row", ["a", "b", "a"])


def test_facet_values_normalise_so_look_alikes_cannot_disagree():
    assert ItemSet.of("x", ITEMS, p=0.5) == ItemSet.of("x", ITEMS, p=0.50)
    assert ItemSet.of("x", ITEMS, seed=11) == ItemSet.of("x", ITEMS, seed="11")


# ── a measurement will not be subtracted by hand ──────────────────────────
def test_measurement_refuses_direct_subtraction():
    a, b = mk("a", 0.9, arm="x"), mk("b", 0.8, arm="y")
    with pytest.raises(UnpairedComparison, match="paired_delta"):
        _ = a - b
    with pytest.raises(UnpairedComparison):
        _ = b - a


def test_paired_delta_refuses_bare_floats():
    with pytest.raises(UnpairedComparison, match="bare float"):
        paired_delta(0.9, 0.8, contrast="arm")


# ── the five conditions ───────────────────────────────────────────────────
def test_different_items_raise():
    """PHASE 3 costume: a subset compared against the full set."""
    a = mk("scrambled", 0.931, ITEMS[:30], arm="scrambled")
    b = mk("baseline", 0.945, ITEMS, arm="honest")
    with pytest.raises(UnpairedComparison, match="UNPAIRED"):
        paired_delta(a, b, contrast="arm")


def test_same_size_different_items_raise():
    """PHASE 7 costume: same n per withholding rate, different item sets."""
    a = mk("p25", 0.464, [f"p25-{i}" for i in range(50)], p_utter=0.25)
    b = mk("p75", 0.480, [f"p75-{i}" for i in range(50)], p_utter=0.75)
    with pytest.raises(UnpairedComparison, match="UNPAIRED"):
        paired_delta(a, b, contrast="p_utter")


def test_different_kinds_raise():
    a = mk("u", 0.93, [f"u{i}" for i in range(50)], kind="utterance", arm="x")
    b = mk("r", 0.88, [f"u{i}" for i in range(50)], kind="referent", arm="y")
    with pytest.raises(UnpairedComparison, match="KINDS differ"):
        paired_delta(a, b, contrast="arm")


def test_second_differing_facet_is_confounded():
    """PHASE 8.3a costume: the contrast moves and so does the step window."""
    a = mk("pre", 1.842, reset="before", step_window="2700-3000", seed=11)
    b = mk("post", 1.713, reset="after", step_window="3000-3300", seed=11)
    with pytest.raises(ConfoundedContrast, match="step_window"):
        paired_delta(a, b, contrast="reset")


def test_identical_contrast_is_degenerate():
    """A 0.00 that is a difference between a thing and itself."""
    a = mk("naive judge", 0.884, judge="naive", seed=11)
    b = mk("arm listener", 0.884, judge="naive", seed=11)
    with pytest.raises(DegenerateContrast, match="DEGENERATE"):
        paired_delta(a, b, contrast="judge")


def test_undeclared_contrast_raises():
    a, b = mk("adapted", 0.971, seed=11), mk("naive", 0.883, seed=11)
    with pytest.raises(UnpairedComparison, match="not a declared facet"):
        paired_delta(a, b, contrast="listener")


def test_asymmetric_facet_declaration_raises():
    """A condition recorded on one side only was not controlled."""
    a = mk("a", 0.9, arm="x", seed=11)
    b = mk("b", 0.8, arm="y")
    with pytest.raises(UnpairedComparison, match="different facets"):
        paired_delta(a, b, contrast="arm")


# ── and a legitimate pairing goes through ─────────────────────────────────
def test_paired_comparison_passes_and_carries_its_contrast():
    """PHASE 7 done right: FULL vs HEAD-ONLY gloss on identical items."""
    a = mk("FULL", 0.428, gloss="full", seed=7)
    b = mk("HEAD-ONLY", 0.349, gloss="head_only", seed=7)
    d = paired_delta(a, b, contrast="gloss")
    assert d.value == pytest.approx(0.079)
    assert d.contrast == "gloss"
    assert d.contrast_values == ("full", "head_only")
    assert "gloss: full vs head_only" in d.describe()


# ── the unpairable case has no difference operator ────────────────────────
def test_side_by_side_has_no_delta():
    a = mk("old set", 1.26, [f"old-{i}" for i in range(50)], referent_set="v1")
    b = mk("new set", 2.90, [f"new-{i}" for i in range(50)], referent_set="v2")
    s = side_by_side(a, b, reason="different referents; no pairing exists")
    with pytest.raises(UnpairedComparison, match="no delta here"):
        _ = s.delta
    assert "old set" in s.describe() and "new set" in s.describe()


def test_side_by_side_refuses_a_pairable_comparison():
    a = mk("a", 0.9, arm="x")
    with pytest.raises(ValueError, match="ARE paired"):
        side_by_side(a, a, reason="x")


def test_side_by_side_demands_a_reason():
    a = mk("a", 0.9, [f"a{i}" for i in range(50)], arm="x")
    b = mk("b", 0.8, [f"b{i}" for i in range(50)], arm="y")
    with pytest.raises(ValueError, match="written reason"):
        side_by_side(a, b, reason="   ")


# ── measure() ties the recorded set to the scored one ─────────────────────
def test_measure_records_the_list_it_scored():
    rows = [("r01", True), ("r02", False), ("r03", True)]
    seen: list = []

    def score(items):
        seen.extend(items)
        return sum(1 for _, ok in items if ok) / len(items)

    got = measure("acc", "eval-row", rows, score, key=lambda r: r[0], seed=11)
    assert seen == rows                       # scored exactly what was keyed
    assert got.value == pytest.approx(2 / 3)
    assert got.items == ItemSet.of("eval-row", ["r01", "r02", "r03"], seed=11)


def test_measure_pairs_with_itself_under_a_contrast():
    rows = [(f"r{i:02d}", i % 3 != 0) for i in range(30)]
    acc = lambda xs: sum(1 for _, ok in xs if ok) / len(xs)   # noqa: E731
    a = measure("full", "eval-row", rows, acc, key=lambda r: r[0], gloss="full")
    b = measure("head", "eval-row", rows, lambda xs: acc(xs) - 0.1,
                key=lambda r: r[0], gloss="head_only")
    assert paired_delta(a, b, contrast="gloss").value == pytest.approx(0.1)
