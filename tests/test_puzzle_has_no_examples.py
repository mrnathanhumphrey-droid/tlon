"""⛔⛔ THE THIRD CROSSING, WHICH NOBODY HAD ENUMERATED.

`tests/test_puzzle_translation_never_ships_unasked.py` guards the reply payload,
and the reply template's own comment names the two sanctioned ways meaning may
cross into English: the ONSET, a crib we write deliberately, and a press of
TRANSLATE, which is the reader's decision.

Suggested example lines were a THIRD way, and none of those guards saw it. A
reader who presses a known English sentence and reads the Tlön that comes back
is holding an aligned pair — handed over free, before they have decoded
anything. It is the parallel-text leak under another name, and it is worse than
the others because it arrives FIRST, at the top of the page, to someone who has
not yet seen a single line of the language.

⛔ This is a markup and script check, not a runtime one, because that is where
the leak lives: no endpoint is involved, and an example block would look like a
kindness in review.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATIC = ROOT / "puzzle" / "static"
INDEX = STATIC / "index.html"
APP = STATIC / "app.js"


def test_the_static_files_are_there():
    """⛔ A guard that silently checks nothing is a vacuous pass."""
    assert INDEX.is_file() and APP.is_file()


def test_the_page_offers_no_example_english():
    """⛔⛔ No `data-q`, which is how an example handed its sentence over."""
    html = INDEX.read_text(encoding="utf-8")
    # ⛔ Strip HTML comments first: the explanation of WHY there are no examples
    # necessarily names the thing it forbids, and a raw search would fire on the
    # prose. This repo has made that mistake twice.
    body = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    assert "data-q" not in body, (
        "⛔⛔ an example line is back in the page. A reader who presses a known "
        "English sentence and reads the Tlön that returns has an aligned pair "
        "before decoding anything — the parallel-text leak, arriving first.")
    assert "ex-list" not in body, "the examples list is back"


def test_the_composer_cannot_be_filled_from_the_markup():
    """⛔ Removing the markup is not enough: a live handler would make any
    future `data-q` — added by anyone, for any reason — a working leak again."""
    js = APP.read_text(encoding="utf-8")
    stripped = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    stripped = re.sub(r"//[^\n]*", "", stripped)
    assert "data-q" not in stripped, (
        "⛔⛔ app.js still reads `data-q`. The attribute must be dead in this "
        "app, so that markup alone cannot reintroduce the leak.")


def test_the_reason_is_recorded_where_the_next_person_will_look():
    """⭐ The removal is only durable if it reads as a decision rather than an
    oversight. An empty slot invites a well-meaning UX addition; a stated
    reason is what makes someone stop."""
    html = INDEX.read_text(encoding="utf-8")
    comments = " ".join(re.findall(r"<!--(.*?)-->", html, flags=re.S)).lower()
    assert "no examples" in comments or "there are no examples" in comments
    for word in ("onset", "translate"):
        assert word in comments, (
            "the comment must name the two crossings that ARE sanctioned, or "
            "it reads as a style preference rather than a boundary")


@pytest.mark.parametrize("phrase", [
    "try one of these",
])
def test_the_invitation_copy_is_gone_too(phrase):
    """⛔ The label outlived the list once already in draft. A heading with
    nothing under it is an invitation to refill it."""
    body = re.sub(r"<!--.*?-->", "", INDEX.read_text(encoding="utf-8"),
                  flags=re.S)
    assert phrase not in body.lower()
