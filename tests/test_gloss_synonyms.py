"""⛔⛔ THE GLOSS-DERIVED SYNONYM-SETS AND THEIR THREE GUARDS.

The sets are a HAND-MADE SEMANTIC JUDGMENT over the root glosses, which is the
appropriate derivation for a product crib and NOT a measured claim. What can be
tested is not the taste but the structure and the guards: that the sets are a
partition of real roots, that the direction guard FIRES on a family pointing
both ways, and that the specific traps this arc walked into are closed.

⛔⛤ THE ROUTE THIS REPLACES merged `max` "it sleeps" with `nur` "it falls" and
`fläm` "it wearies" with `mim` "it wakes". Both passed a max-set guard and a
reach guard, because they were the wrong DIRECTION and not the wrong SHAPE.
"""
import pathlib
import sys

import pytest

TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import act2_build_gloss_synonyms as B          # noqa: E402
import act2_check_gloss_synonyms as K          # noqa: E402


@pytest.fixture
def lexicon(monkeypatch):
    """⛔ `build()` sets TLON_LEXICON and clears the load cache PROCESS-WIDE."""
    from tlon.grammar import classes as C
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.load.cache_clear()
    yield
    C.load.cache_clear()


# ── 1 · the structure ───────────────────────────────────────────────────────

def test_the_sets_are_a_partition_of_real_roots(lexicon):
    sets, rep = B.build()
    assert rep["problems"] == []
    assert len(sets) == len(rep["placed"])


def test_every_family_has_at_least_two_roots():
    for family, roots in B.FAMILIES.items():
        assert len(roots) >= 2, family
        assert len(set(roots)) == len(roots), "%s repeats a root" % family


def test_a_root_in_two_families_is_REFUSED(lexicon, monkeypatch):
    """⛔ NON-VACUITY for the partition check: fabricate the collision."""
    broken = dict(B.FAMILIES)
    broken["dimming"] = list(broken["dimming"])
    broken["shining"] = list(broken["shining"]) + [broken["dimming"][0]]
    monkeypatch.setattr(B, "FAMILIES", broken)
    _, rep = B.build()
    assert any("partition" in p for p in rep["problems"]), rep["problems"]


def test_a_family_naming_a_non_root_is_REFUSED(lexicon, monkeypatch):
    broken = dict(B.FAMILIES)
    broken["dimming"] = list(broken["dimming"]) + ["notaroot"]
    monkeypatch.setattr(B, "FAMILIES", broken)
    _, rep = B.build()
    assert any("not an R root" in p for p in rep["problems"]), rep["problems"]


# ── 2 · the DIRECTION guard, which is the new one ───────────────────────────

def test_the_antonym_guard_FIRES_on_the_pair_the_dead_route_merged(lexicon,
                                                                   monkeypatch):
    """⛔⛔ RED-PROOF. `fläm` "it wearies" and `mim` "it wakes" in one family
    is exactly what co-occurrence produced, and it passed both shape guards.
    If this guard cannot fire, nothing in the pipeline catches direction.
    """
    broken = dict(B.FAMILIES)
    broken["fabricated"] = ["fläm", "mim"]
    monkeypatch.setattr(B, "FAMILIES", broken)
    sets, _ = B.build()
    g = K.guards(sets, [])
    assert any(v[1:] == ("fläm", "mim") for v in g["antonym_violations"]), (
        g["antonym_violations"])


def test_the_antonym_guard_is_SILENT_on_the_real_sets(lexicon):
    """⛔ And it must not fire on the healthy case, or it says nothing."""
    sets, _ = B.build()
    g = K.guards(sets, [])
    assert g["antonym_violations"] == []


def test_the_gloss_string_trap_is_closed(lexicon):
    """⛔⛔ THE TRAP THE SPEC NAMED. `hram` "it breathes", `mläng` "it breathes
    its last" and `hläx` "it stills, goes unbreathing" share gloss WORDS and
    span a breath to a death. A derivation by string overlap would merge them.
    `nöl` "it stills, silences" shares "stills" with `hläx` and is a different
    happening. None of these may share a family.
    """
    sets, _ = B.build()
    for a, b in (("hram", "mläng"), ("hram", "hläx"), ("nöl", "hläx")):
        fam_a, fam_b = sets.get(a, frozenset()), sets.get(b, frozenset())
        assert b not in fam_a and a not in fam_b, "%s and %s share a family" % (a, b)


def test_antonym_list_names_only_real_roots(lexicon):
    """⛔ An antonym pair naming a typo'd root would silently never fire."""
    from tlon.grammar import classes as C
    roots = set(C.load()["classes"]["R"])
    for a, b in B.ANTONYMS:
        assert a in roots and b in roots, (a, b)


# ── 3 · the SHAPE guards ────────────────────────────────────────────────────

def test_max_set_size_meets_the_pre_registered_bar(lexicon):
    sets, _ = B.build()
    biggest = max(len(v) for v in sets.values())
    assert biggest <= B.ACCEPTANCE["max_set_size_at_most"]


def test_reach_is_computed_over_pairs_not_conversations(lexicon):
    """⭐ A hand-built case, so the statistic is pinned independently of the
    corpus: 3 pairs, 2 of which share a root that has alternatives.
    """
    sets, _ = B.build()
    dimming = sets["flöx"]
    assert len(dimming) > 1
    lonely = next(r for r in ("hram", "nur", "max") if r not in sets)
    g = K.guards(sets, [frozenset({"flöx"}), frozenset({lonely}),
                        frozenset({"pön"})])
    assert g["pairs"] == 3 and g["touchable"] == 2
    assert g["reach"] == pytest.approx(2 / 3, abs=1e-4)


def test_an_unplaced_root_has_no_alternatives_and_so_TIGHTENS(lexicon):
    """⛔ The fallback must be the EXACT root, never anything-goes."""
    sets, rep = B.build()
    unplaced = [r for r in rep["glosses"] if r not in sets]
    assert unplaced, "every root is placed — the fallback is untested"
    assert all(sets.get(r) is None for r in unplaced)
