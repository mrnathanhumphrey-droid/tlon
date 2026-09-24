"""THE EXPANDED LEXICON — and the frozen one it must never disturb.

⛔⛔ THE FAILURE THIS FILE EXISTS TO PREVENT. Every number in the research
campaign was measured against `lexicon.yaml`, blake2b-16
`e2b8527010231a81fd31b6eeb9de3d8c`, and every artifact records that hash. If the
expansion ever became the default — an env var leaking, a fallback firing, a
root landing in the frozen file — the standing verdicts would still read fine
and would no longer be about the language they name. Nothing on screen would
change. That is the whole reason the two files are separate and the reason
these assertions are worth more than the ones about the new roots.
"""
from __future__ import annotations

import os
import pathlib
import sys

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tlon.grammar import classes as C                       # noqa: E402

FROZEN_HASH = "e2b8527010231a81fd31b6eeb9de3d8c"
FROZEN = pathlib.Path(C.__file__).with_name("lexicon.yaml")
EXPANDED = pathlib.Path(C.__file__).with_name("lexicon_expanded.yaml")

#: ⛔ The grammar is the SPEC, not vocabulary. Only R may grow.
CLOSED = ("O", "L", "A", "M", "D", "Q", "T", "F")


@pytest.fixture(autouse=True)
def _clean_lexicon_env(monkeypatch):
    """⛔ `load()` is `lru_cache(maxsize=1)`, so a cached value survives an env
    change. Every test here clears it on the way in AND the way out — a test
    that left the expanded lexicon cached would hand it to the next test in the
    session, which is the leak this file is about."""
    monkeypatch.delenv(C.LEXICON_ENV, raising=False)
    C.load.cache_clear()
    yield
    C.load.cache_clear()


def _load_with(path) -> dict:
    os.environ[C.LEXICON_ENV] = str(path)
    try:
        C.load.cache_clear()
        return C.load()
    finally:
        os.environ.pop(C.LEXICON_ENV, None)
        C.load.cache_clear()


# ── the frozen default ──────────────────────────────────────────────────────

def test_the_default_is_still_the_frozen_lexicon():
    """⛔⛔ The single most important assertion in this file."""
    lex = C.load()
    assert lex["_hash"] == FROZEN_HASH
    assert len(lex["classes"]["R"]) == 156
    assert C.lexicon_path() == FROZEN


def test_a_missing_override_raises_instead_of_falling_back(monkeypatch):
    """⛔ A mistyped path must stop the run. Falling back would mean speaking
    156 roots while every log line claimed 218 — healthy-looking and wrong."""
    monkeypatch.setenv(C.LEXICON_ENV, "no_such_lexicon.yaml")
    C.load.cache_clear()
    with pytest.raises(C.LexiconError):
        C.load()


def test_the_frozen_file_still_contains_exactly_the_frozen_roots():
    """⭐ Catches a new root landing in the WRONG FILE — the expansion applied
    in place. The hash test above would catch it too; this one says why."""
    roots = yaml.safe_load(FROZEN.read_bytes())["classes"]["R"]
    assert len(roots) == 156
    for form in ("tran", "löm", "nang", "xen"):
        assert form not in roots, "⛔⛔ %r is in the FROZEN lexicon" % form


# ── the expanded lexicon ────────────────────────────────────────────────────

def test_the_expanded_lexicon_loads_and_has_218_roots():
    lex = _load_with(EXPANDED)
    assert len(lex["classes"]["R"]) == 218
    assert lex["_hash"] != FROZEN_HASH


def test_the_expansion_neither_drops_nor_redefines_a_frozen_root():
    """⛔⛔ A silently redefined root is the worst outcome available here: every
    utterance that used it still parses, and means something else."""
    frozen = yaml.safe_load(FROZEN.read_bytes())["classes"]["R"]
    grown = _load_with(EXPANDED)["classes"]["R"]
    missing = sorted(set(frozen) - set(grown))
    changed = sorted(f for f in frozen if grown.get(f) != frozen[f])
    assert not missing, "dropped frozen roots: %s" % missing
    assert not changed, "redefined frozen roots: %s" % changed


@pytest.mark.parametrize("cls", CLOSED)
def test_the_grammar_classes_are_untouched(cls):
    """⛔ Nate's spec freezes these. The grammar is the spec — surface-disjoint
    classes in a fixed slot order — and growing one is a language change, not a
    vocabulary change."""
    frozen = yaml.safe_load(FROZEN.read_bytes())["classes"][cls]
    grown = _load_with(EXPANDED)["classes"][cls]
    assert grown == frozen


def test_phonotactics_are_untouched():
    frozen = yaml.safe_load(FROZEN.read_bytes())["phonotactics"]
    grown = _load_with(EXPANDED)["phonotactics"]
    assert grown == frozen


def test_new_roots_are_legal_and_surface_disjoint():
    """⭐ Asserted through the REAL loader, which runs `_validate` — the same
    code the app runs. A re-implementation here would be a verifier agreeing
    with itself."""
    lex = _load_with(EXPANDED)          # raises LexiconError if either fails
    frozen = yaml.safe_load(FROZEN.read_bytes())["classes"]["R"]
    added = set(lex["classes"]["R"]) - set(frozen)
    assert len(added) == 62
    seen = {}
    for cls, table in lex["classes"].items():
        for form in table:
            assert form not in seen, "%r in both %s and %s" % (form, seen[form], cls)
            seen[form] = cls


def test_no_new_root_has_an_empty_onset():
    """⭐ All 156 frozen roots begin with a consonant. A bare-vowel root would
    be legal and would not sound like the language."""
    lex = _load_with(EXPANDED)
    frozen = yaml.safe_load(FROZEN.read_bytes())["classes"]["R"]
    added = sorted(set(lex["classes"]["R"]) - set(frozen))
    vowels = set(lex["phonotactics"]["nuclei"])
    bare = [f for f in added if f[0] in vowels]
    assert not bare, "bare-vowel roots: %s" % bare


# ── the generator ───────────────────────────────────────────────────────────

def test_the_expanded_file_matches_what_the_generator_builds():
    """⛔ The file is GENERATED. If someone hand-edits it, the table and the
    file disagree and the next dose silently reverts the edit. `--check` is the
    same comparison, run here so CI enforces it."""
    import act2_expand_lexicon as EX

    built = EX.build_text(FROZEN.read_text(encoding="utf-8"), EX.expansion())
    on_disk = EXPANDED.read_text(encoding="utf-8")
    assert on_disk == built, (
        "⛔⛔ lexicon_expanded.yaml does not match tools/act2_expand_lexicon.py "
        "— rebuild it rather than editing it by hand")


def test_the_expansion_table_is_62_distinct_forms():
    import act2_expand_lexicon as EX

    assert len(EX.expansion()) == 62
    assert sum(len(d) for d in EX.DOSES) == 62, "a dose has duplicate forms"


def test_no_root_names_anything():
    """⛔⛔ NAMING IS THE ONE THING TLÖN REFUSES, and a root for it was drafted
    and cut. The moon in the story is never called — "axaxaxas mlö" is a fresh
    impression, not a second mention of a first thing. This guards the decision
    so a later dose cannot quietly reintroduce it.

    ⚠️ A word-list cannot police meaning; this catches the obvious spelling of
    the mistake, not every possible one.
    """
    import act2_expand_lexicon as EX

    banned = ("names", "calls by", "refers", "denotes", "means",
              "is called", "signifies")
    bad = [(f, m) for f, m in EX.expansion().items()
           if any(b in m.lower() for b in banned)]
    assert not bad, "⛔⛔ a root that names: %s" % bad


def test_no_root_is_a_self():
    """⛔ No I, no you, no mine. The language has no word for a self and the
    expansion must not give it one."""
    import act2_expand_lexicon as EX

    banned = (" i ", "you", "mine", "myself", "yourself", "oneself", "we ")
    bad = [(f, m) for f, m in EX.expansion().items()
           if any(b in (" " + m.lower() + " ") for b in banned)]
    assert not bad, "⛔⛔ a root with a self in it: %s" % bad


def test_every_new_root_is_impersonal_present():
    """⭐ Every frozen root reads "it VERBs". The expansion must too — a root
    that broke the frame would produce utterances the grammar renders but the
    voice does not own."""
    import act2_expand_lexicon as EX

    bad = [(f, m) for f, m in EX.expansion().items() if not m.startswith("it ")]
    assert not bad, "roots not in the impersonal frame: %s" % bad


# ── switching lexicons inside one process ───────────────────────────────────

def test_clearing_only_load_leaves_the_classifier_on_the_old_language(
        monkeypatch):
    """⛔⛔ THREE CACHES, AND TWO OF THEM ARE NOT `load`.

    `form_class` and `_aspect_re` each hold their own `lru_cache` built FROM a
    lexicon. A process that switches `TLON_LEXICON` after any token has been
    classified keeps classifying against the OLD language while `load()`
    truthfully reports the new one — so `parse` refuses tokens that exist and
    the caller reads it as the model emitting garbage.

    ⭐ Found when `tools/act2_onset_carry.py` went green alone and red in the
    full suite: an earlier test had warmed `form_class` on the frozen 156.
    """
    C.reset_caches()
    monkeypatch.delenv("TLON_LEXICON", raising=False)
    C.classify("nu")                                   # warm it on the frozen
    assert C.load()["_hash"] == FROZEN_HASH

    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.load.cache_clear()                               # ⛔ the INSUFFICIENT fix
    assert C.load()["_hash"] != FROZEN_HASH, "load did switch"

    stale = {f for f in C.form_class()}
    expanded_only = set(yaml.safe_load(EXPANDED.read_bytes())["classes"]["R"]) \
        - set(yaml.safe_load(FROZEN.read_bytes())["classes"]["R"])
    assert not (expanded_only & stale), (
        "⭐ form_class is stale, as documented — this assertion records the "
        "bug, not a wish")

    C.reset_caches()
    fresh = {f for f in C.form_class()}
    assert expanded_only & fresh, (
        "⛔⛔ reset_caches did NOT rebuild form_class — anything that parses "
        "would still refuse valid tokens")


def test_reset_caches_restores_the_frozen_default(monkeypatch):
    """⛔ The reset must work in BOTH directions, or a test that switched to
    the expansion would poison every later frozen-lexicon assertion in the
    same process."""
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.reset_caches()
    C.classify("nu")
    monkeypatch.delenv("TLON_LEXICON", raising=False)
    C.reset_caches()
    assert C.load()["_hash"] == FROZEN_HASH
    assert len(C.load()["classes"]["R"]) == 156
