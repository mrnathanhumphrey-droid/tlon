"""THE PROMPT IS RED-TEAMED LIKE THE ORACLE WAS. $0.

⛔⛔ A PROMPT IS A CONTRACT AND THIS ONE IS LOAD-BEARING FOR THE WHOLE RESULT.
The string it replaces requested **content continuity** (*"say something that
follows from what was said"*), which C-D1 denies and the content-free corpus
cannot supply. The replacement must request **one-place coherence plus force**
and nothing else — and almost every natural phrasing of "produce the next turn"
smuggles a *coherence-with-prior* back in. That is the content-adjacency ghost
returning **through the instruction** after six rounds of killing it in the
oracle.

⭐ SO THE GUARD IS CLAUSE-BY-CLAUSE, NOT A WORD BLACKLIST. Continuity words are
ALLOWED — the licensing clause needs them ("it need not FOLLOW from it") — but
only inside a NEGATING clause. A continuity word in an affirmative sentence is
the ghost.
"""
from __future__ import annotations

import re

import pytest

from tlon.discourse import provocation as P


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n\n", text)
            if s.strip()]


def _is_negated(sentence: str) -> bool:
    low = sentence.lower()
    return any(n in low for n in P.NEGATORS)


def _offending(text: str) -> list[tuple[str, str]]:
    """Continuity words appearing in AFFIRMATIVE clauses."""
    out = []
    for s in _sentences(text):
        if _is_negated(s):
            continue
        low = s.lower()
        for w in P.CONTINUITY_WORDS:
            if w in low:
                out.append((w, s))
    return out


# ══ THE GHOST CHECK ══════════════════════════════════════════════════════
def test_no_continuity_word_appears_in_an_AFFIRMATIVE_clause():
    """⛔⛔ THE WHOLE POINT. The prompt may LICENSE content-freedom; it may never
    REQUEST content-continuity."""
    off = _offending(P.PROVOCATION)
    assert not off, f"two-place request(s) in the provocation: {off}"


def test_the_guard_FIRES_on_the_string_it_replaced():
    """⛔ RED-PROOF. The old CONVERSE clause is the exact defect; if the guard
    cannot catch that, it catches nothing."""
    old = "Say something that follows from what was said."
    off = _offending(old)
    assert off, "the guard failed to catch the known-bad clause"
    assert off[0][0] == "follow"


@pytest.mark.parametrize("bad", [
    "Respond to what was said.",
    "Continue the exchange.",
    "Stay on the same subject.",
    "Say the next thing in the conversation.",
    "Your scene should relate to the prior one.",
])
def test_the_guard_fires_on_every_natural_phrasing_that_smuggles_continuity(bad):
    """⭐ These are the phrasings a careful person writes by accident."""
    assert _offending(bad), bad


@pytest.mark.parametrize("ok", [
    "It need not be about what you were shown.",
    "It does not follow from it.",
    "Paint a scene that holds together on its own.",
])
def test_the_guard_does_NOT_fire_on_licences_or_one_place_clauses(ok):
    """A guard that fires on the licensing clause would make the fix
    unwritable."""
    assert not _offending(ok), ok


# ══ THE LICENCE IS PRESENT, NOT MERELY THE OMISSION ══════════════════════
def test_content_freedom_is_EXPLICITLY_LICENSED():
    """⛔⛔ OMISSION IS NOT ENOUGH. Every LLM prior pulls toward staying on topic,
    so a prompt merely silent on content gets continuity back by default. The
    string must say so."""
    low = P.PROVOCATION.lower()
    assert "need not be about what you were shown" in low
    assert "need not follow from it" in low
    assert "need not stay on any subject" in low


def test_the_force_connection_is_named_and_is_the_ONLY_thing_carried():
    low = P.PROVOCATION.lower()
    assert "provoke the force" in low
    assert "only the force carries across" in low


def test_one_place_coherence_is_requested():
    assert "holds together on its own" in P.PROVOCATION.lower()


def test_the_echo_is_addressed_directly():
    """The measured depth-1 failure was a deterministic ECHO (8/10, 1/8
    distinct). The prompt says not to translate, in as many words."""
    assert "do not translate" in P.PROVOCATION.lower()


def test_the_prompt_does_not_carry_a_lexicon_card_inline():
    """⛔ The bar is CARDLESS emission. The card is appended by the backend, not
    baked into the constant."""
    assert "xöl" not in P.PROVOCATION and "hrix" not in P.PROVOCATION


# ══ ONE OBJECT, BOTH SIDES ═══════════════════════════════════════════════
def test_the_trainer_and_the_arena_IMPORT_it_rather_than_re_spell_it():
    """⛔⛔ THE STRUCTURAL HALF OF THE FIX. Two copies of a prompt is exactly the
    defect this module exists to remove; a test that only checked the string's
    content would let them drift apart again."""
    import pathlib
    root = pathlib.Path(__file__).parents[1]
    trainer = (root / "tools/act2_finetune.py").read_text(encoding="utf-8")
    arena = (root / "tlon/act2/llm.py").read_text(encoding="utf-8")
    for name, src in (("trainer", trainer), ("arena", arena)):
        assert "provocation" in src, f"{name} does not import the provocation"
        assert "PROVOCATION" in src, f"{name} does not use PROVOCATION"


def test_the_old_follows_from_clause_is_GONE_from_the_arena():
    """⛔ RE-INTRODUCE THE DEFECT AND THE TEST MUST GO RED. A stale copy of the
    old wording anywhere in the serving path re-opens the contradiction."""
    import pathlib
    arena = (pathlib.Path(__file__).parents[1]
             / "tlon/act2/llm.py").read_text(encoding="utf-8")
    assert "follows from what was said" not in arena


def test_the_direction_key_is_declared():
    assert P.DIRECTION == "provoke"
