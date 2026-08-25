"""RULING 1 — THE M-SPINE IS KEYED ON THE LEXICON, NOT ON THE SPEC. $0, offline.

⛔⛔ FIVE OF TEN FORMS IN SPEC v0.1 DO NOT EXIST. The ontology was right and the
spelling was wrong, which is the most survivable version of this failure and
still cost a verification pass to catch. These tests make the binding structural.
"""
from __future__ import annotations

import inspect

import pytest

from tlon.discourse import evidential as E
from tlon.grammar import classes as C


def test_the_inventory_IS_the_lexicon_not_a_copy_of_it():
    assert E.EVIDENTIALS == dict(C.load()["classes"]["M"])


def test_there_is_no_hardcoded_list_of_M_FORMS_in_the_module():
    """⛔⛔ THE STRUCTURAL HALF. A test that merely compares two dicts passes
    happily while a literal list sits in the source waiting to drift. This
    asserts the literals are ABSENT, so there is nothing to drift.

    ⛔ Checked over STRING LITERALS IN CODE, not over the raw text — the first
    version of this test grepped the source and tripped over `ten` (felt) inside
    the phrase "ten ways-of-holding". A substring search answers a different
    question than the one being asked.
    """
    import ast
    tree = ast.parse(inspect.getsource(E))
    docstrings = {ast.get_docstring(n) for n in ast.walk(tree)
                  if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef))}
    literals = {n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and n.value not in docstrings}
    # the ghost→real map is allowed to name forms; it is the correction itself
    allowed = set(E.SPEC_v0_1_MISSPELLINGS) | set(E.SPEC_v0_1_MISSPELLINGS.values())
    leaked = (literals & set(C.load()["classes"]["M"])) - allowed
    assert not leaked, (
        f"{sorted(leaked)} appear as string literals in evidential.py — the "
        "inventory must come from the frozen lexicon, never from a copy")


def test_all_ten_ways_of_holding_are_present():
    assert len(E.EVIDENTIALS) == 10
    assert set(E.BY_GLOSS) == {
        "seen", "heard", "felt", "inferred", "remembered",
        "dreamt", "denied", "doubted", "wished", "feared"}


# ══ THE FIVE GHOSTS ══════════════════════════════════════════════════════
@pytest.mark.parametrize("ghost,real", sorted(E.SPEC_v0_1_MISSPELLINGS.items()))
def test_each_spec_misspelling_is_REFUSED_and_names_its_replacement(ghost, real):
    """⭐ A refusal that only says 'not in class M' teaches nothing. This one
    hands over the right form, which is what stops the table being rebuilt wrong
    a second time."""
    with pytest.raises(E.EvidentialError) as e:
        E.resolve(ghost)
    assert real in str(e.value)


@pytest.mark.parametrize("ghost", sorted(E.SPEC_v0_1_MISSPELLINGS))
def test_the_ghosts_really_are_absent_from_the_lexicon(ghost):
    """⛔ RED-PROOF THE PREMISE. If one of these ever turns out to BE a real
    form, this whole correction was wrong and must be revisited loudly."""
    assert ghost not in C.load()["classes"]["M"]


@pytest.mark.parametrize("real", sorted(E.SPEC_v0_1_MISSPELLINGS.values()))
def test_the_replacements_really_ARE_in_the_lexicon(real):
    assert real in C.load()["classes"]["M"]
    assert E.resolve(real) == real


def test_the_ghosts_are_not_in_ANY_class_so_this_is_not_a_class_mixup():
    """⭐ Rules out the other explanation: that the spec put a real form in the
    wrong class. These five are not anywhere in the lexicon at all."""
    lex = C.load()["classes"]
    for ghost in E.SPEC_v0_1_MISSPELLINGS:
        for cls, table in lex.items():
            assert ghost not in table, f"{ghost!r} is real, and it is class {cls}"


def test_an_unrelated_form_is_refused_with_the_full_inventory():
    with pytest.raises(E.EvidentialError, match="not in lexicon class M"):
        E.resolve("klung")


# ══ §8.1 IS ABSENT ON PURPOSE ════════════════════════════════════════════
def test_the_base_convention_table_RAISES_rather_than_defaulting():
    """⛔⛔ THE MOST IMPORTANT TEST IN THE FILE. A plausible default table would
    be consumed by the arena and reported as a measurement of ten forgotten
    guesses. Absent-and-loud beats present-and-plausible."""
    with pytest.raises(NotImplementedError, match="UNBUILT"):
        E.base_convention("xöl")


def test_the_unbuilt_table_still_validates_its_argument_first():
    """A ghost form must be refused as a ghost, not swallowed by the
    NotImplementedError — otherwise the misspelling survives until §8.1 lands."""
    with pytest.raises(E.EvidentialError):
        E.base_convention("sköl")
