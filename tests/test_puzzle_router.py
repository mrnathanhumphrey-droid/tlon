"""⛔⛔ RED-PROOF FOR THE INPUT ROUTER.

Production refused five of six lines containing the word `ka`, and told the
reader "The language would not hold that" — which was false. The language holds
it fine; the bench posted a Tlön-shaped string through the English door. Every
test here is a line a reader would plausibly type, and the assertion is that it
reaches a door that can read it.

⛔ No model is loaded anywhere in this file. The router is `parse`/`render`
against the frozen lexicon and nothing else, which is what makes it testable
without a GPU second.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from puzzle import router as R                       # noqa: E402

from tlon.grammar import classes as C                # noqa: E402
from tlon.grammar.parse import ParseError, parse, render  # noqa: E402

#: A real reply, taken verbatim from the production log.
REPLY = "hlim hlux les nang axas les ka"
#: Another, from a different reader.
REPLY2 = "nu har mil hram nang ka"


@pytest.fixture(autouse=True)
def expanded_lexicon(monkeypatch):
    """⛔⛔ THE BENCH SERVES `lexicon_expanded.yaml`, AND SETTING THAT AT MODULE
    IMPORT POISONS THE WHOLE RUN.

    Half of what the served adapter says is not a word under the process
    default (the frozen 156), so these tests must run under the expanded 218 —
    but a module-level `os.environ.setdefault` is applied at COLLECTION, before
    any test executes, and every other suite then runs under a language it did
    not ask for. I have made exactly this mistake before on this repo.

    ⛔ And the env var alone is not enough in either direction. `form_class` and
    `_aspect_re` hold their own caches built FROM a lexicon, so a process that
    switches after any token has been classified keeps classifying against the
    OLD language while `load()` reports the new one — nothing raises, `parse`
    just refuses tokens that exist. `reset_caches()` is called on the way in
    AND on the way out for that reason.
    """
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.reset_caches()
    yield
    monkeypatch.undo()
    C.reset_caches()


def test_the_served_lexicon_is_the_one_under_test():
    """⛔ If this drifts, every assertion below is about the wrong language."""
    assert C.load()["_hash"] == "08c03b0a81330e4ba42883fa8b08c873"


# ── the two exception types ────────────────────────────────────────────────

def test_LexiconError_is_not_a_ParseError():
    """⛔⛔ THE CRASH THIS ROUTER WOULD HAVE SHIPPED WITH. They share only
    RuntimeError. English raises the first; catching only the second would
    take down the most common path on the bench."""
    assert not issubclass(C.LexiconError, ParseError)
    with pytest.raises(C.LexiconError):
        parse("Are you there ka")
    with pytest.raises(ParseError):
        parse("ka")


def test_looks_like_tlon_survives_both():
    assert R.looks_like_tlon("Are you there ka") is None
    assert R.looks_like_tlon("ka") is None
    assert R.looks_like_tlon(REPLY) is not None


# ── (a) a pasted surface ───────────────────────────────────────────────────

def test_a_reply_pasted_back_skips_the_write_step():
    """The most likely repeat-back: the reader copies what they were shown."""
    d = R.classify(REPLY, prior_surface=REPLY2)
    assert d.route == R.TLON
    assert d.surface == REPLY
    assert d.skips_write


def test_a_pasted_surface_is_passed_through_byte_for_byte():
    """⛔ Not re-rendered. The reader is answered about the line they typed."""
    assert R.classify(REPLY).surface == REPLY


# ── (b) a bare force word ──────────────────────────────────────────────────

@pytest.mark.parametrize("word", ["ka", "ki", "ko", "ku", "kä"])
def test_every_force_word_alone_aims_at_the_last_line(word):
    d = R.classify(word, prior_surface=REPLY)
    assert d.route == R.FORCE
    assert d.force == word
    assert parse(d.surface).force == word, "the speech act did not take"


def test_the_refocused_line_keeps_the_scene_and_changes_only_the_act():
    """⭐ `ki` on the Tlönian's last line means "is it so?" OF THAT LINE —
    same scene, different force. If the node moved, we answered a different
    sentence than the one on the reader's screen."""
    d = R.classify("ki", prior_surface=REPLY)
    assert parse(d.surface).node == parse(REPLY).node
    assert parse(REPLY).force == "ka"
    assert parse(d.surface).force == "ki"


def test_ka_on_a_ka_line_reproduces_it_exactly():
    """⛔ RECORDED AS A KNOWN CONSEQUENCE, NOT AN ACCIDENT. "It is so" applied
    to a line that already asserts IS that line. The provocation then equals
    the Tlönian's own previous turn, which is a real echo risk and is why the
    route is logged — R4 measures it."""
    assert parse(REPLY).force == "ka"
    assert R.classify("ka", prior_surface=REPLY).surface == REPLY


def test_repeated_force_words_are_one_speech_act_not_english():
    """`ka ka` must not fall through to the write door, which cannot read it."""
    d = R.classify("ka ka", prior_surface=REPLY)
    assert d.route == R.FORCE and d.force == "ka"


def test_the_last_force_word_wins_and_both_routes_agree():
    """⭐ (b) and (c) use the SAME rule, so a line between them cannot get two
    different answers depending on which branch caught it."""
    assert R.classify("ka ki", prior_surface=REPLY).force == "ki"
    assert R.classify("Are you there ka ki").force == "ki"


def test_a_bare_force_with_nothing_to_answer_is_not_a_refusal():
    """⛔ The reader's FIRST line being `ka` is not the language failing. It is
    a speech act with no antecedent, and it must not reach the copy that says
    the language would not hold it."""
    d = R.classify("ka", prior_surface=None)
    assert d.route == R.NOTHING
    assert d.surface is None


# ── (c) English wearing a force word ───────────────────────────────────────

def test_the_line_that_broke_production():
    """`Are you there ka` — refused three times on the live bench."""
    d = R.classify("Are you there ka")
    assert d.route == R.TAGGED
    assert d.english == "Are you there"
    assert d.force == "ka"


def test_the_stripped_english_is_what_actually_worked_in_production():
    """⭐ `Are you there` (no `ka`) succeeded on the live bench at 19:18. The
    router hands the write step exactly that string."""
    assert R.classify("Are you there ka").english == "Are you there"


def test_roots_are_never_stripped_only_forces():
    """⛔ Out of scope by decision: mixed English and Tlön ROOTS goes to the
    write door untouched. Stripping a root would silently delete part of what
    somebody said."""
    root = sorted(C.load()["classes"]["R"])[0]
    text = "I think %s is a word ka" % root
    d = R.classify(text)
    assert d.route == R.TAGGED
    assert root in d.english, "a root was stripped"
    assert d.english == "I think %s is a word" % root


# ── (d) English ────────────────────────────────────────────────────────────

def test_plain_english_is_unchanged():
    d = R.classify("What is happiness?")
    assert d.route == R.ENGLISH
    assert d.english == "What is happiness?"
    assert not d.skips_write


def test_a_question_mark_still_goes_through_the_write_door():
    """⭐ `Ka?` already worked in production — it is English, and `?`→`ki` is a
    rule the write model learned over 744 rows. The router must not intercept
    it and must not case-fold `Ka` into the force word."""
    d = R.classify("Ka?")
    assert d.route == R.ENGLISH
    assert d.english == "Ka?"


def test_english_carrying_roots_is_routed_the_same_but_recorded_apart():
    """⭐ These are the rows a future write corpus needs; today there is no way
    to find them again."""
    root = sorted(C.load()["classes"]["R"])[0]
    d = R.classify("is %s a word" % root)
    assert d.route == R.ENGLISH_ROOTS
    assert d.english == "is %s a word" % root
    assert not d.skips_write


def test_empty_input_does_not_explode():
    assert R.classify("   ").route == R.ENGLISH


# ── refocus is proved, not assumed ─────────────────────────────────────────

def test_refocus_round_trips_for_every_force():
    for f in sorted(C.load()["classes"]["F"]):
        out = R.refocus(REPLY, f)
        assert parse(out) == parse(out), "unstable parse"
        assert parse(out).force == f
        assert render(parse(out)) == out


def test_refocus_refuses_a_non_force():
    root = sorted(C.load()["classes"]["R"])[0]
    with pytest.raises(R.RouterError):
        R.refocus(REPLY, root)


def test_refocus_refuses_a_line_that_is_not_a_surface():
    with pytest.raises(R.RouterError):
        R.refocus("Are you there", "ki")
