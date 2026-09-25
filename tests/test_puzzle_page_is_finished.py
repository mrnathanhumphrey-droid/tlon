"""⛔⛔ THE BENCH WENT PUBLIC WEARING ITS SKELETON.

`tlon.resolveresearcher.com` was live, healthy, and reporting `speaker_loaded:
true` while the page served to readers carried TEN dashed "PLACEHOLDER" chips
over finished copy, four `<video>` elements pointing at files that do not exist
(four 404s on every load), a bracketed stub where the crib should be, and no
visible chat box at all — it wore `.oracle-ask`, the Oracle's LANDING-PAGE ask
row, while the Oracle's real bounded composer sat unused in a stylesheet the
page already loaded.

⭐ NONE OF THAT COULD FAIL A CHECK, WHICH IS THE POINT OF THIS FILE. Every
existing guard was about leaks, limits and verification — all of them green.
"The page looks unfinished" has no endpoint, no status code and no exception,
so it can only be caught by reading the markup the server actually serves.

⛔ EVERY ASSERTION BELOW STRIPS COMMENTS FIRST. The explanation of why the
placeholders are gone necessarily names them, and this repo has fired a guard
on its own prose twice.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATIC = ROOT / "puzzle" / "static"


def _html() -> str:
    """The page with HTML comments removed."""
    raw = (STATIC / "index.html").read_text(encoding="utf-8")
    return re.sub(r"<!--.*?-->", "", raw, flags=re.S)


def _css() -> str:
    raw = (STATIC / "puzzle.css").read_text(encoding="utf-8")
    return re.sub(r"/\*.*?\*/", "", raw, flags=re.S)


def _js() -> str:
    raw = (STATIC / "app.js").read_text(encoding="utf-8")
    stripped = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)
    return re.sub(r"//[^\n]*", "", stripped)


# ── the stubs ───────────────────────────────────────────────────────────────

def test_the_comment_stripper_actually_strips():
    """⛔ A vacuous pass is the failure mode of every test in this file: if
    `_html()` returned the raw markup, the assertions below would be searching
    prose that deliberately names what it forbids. Pin the instrument."""
    assert "<!--" not in _html()
    # ⛔ The sentinel is a piece of real, reader-visible copy. It was "the
    # onset" until the crib was removed as a cardinal sin, at which point this
    # test failed for the RIGHT reason and proved it was watching something.
    assert "A language with no nouns" in _html(), "the stripper ate real content"


def _visible(html: str) -> str:
    """Only the text a reader actually sees: comments and tags removed.

    ⛔ `placeholder="say something about your day…"` is a legitimate HTML
    attribute — both its name and its value — and the first two drafts of this
    test fired on it. That is the grep-the-prose trap wearing a new costume,
    and it was caught only because the suite was actually run rather than
    reasoned about. The claim is about what the page SAYS, so the search is
    over text nodes and nothing else; the attribute side is pinned separately
    by `test_the_stub_attribute_is_gone_from_the_markup`.
    """
    return re.sub(r"<[^>]+>", " ", html)


@pytest.mark.parametrize("word", ["placeholder", "PLACEHOLDER", "TODO", "lorem"])
def test_no_stub_marker_reaches_a_reader(word):
    """⛔⛔ TEN OF THESE SHIPPED. `[data-placeholder]` drew a dashed outline and
    a green chip, which was right while the page was a skeleton and wrong the
    instant it had a public URL — and it was applied to copy that was FINISHED,
    so the page libelled its own words as unwritten."""
    assert word not in _visible(_html()), (
        "⛔⛔ %r is in the text the server hands to readers" % word)


def test_the_stub_attribute_is_gone_from_the_markup():
    """⛔ The attribute is the other half: it is what the chip hangs on, and it
    survives in attribute position where the test above cannot see it."""
    assert "data-placeholder" not in _html()


def test_the_placeholder_treatment_is_gone_from_the_stylesheet_too():
    """⛔ Removing the attributes is half a fix: the rule that draws the chip
    would reattach to the first `data-placeholder` anyone adds back, which is
    how this shipped in the first place."""
    assert "data-placeholder" not in _css()
    assert "data-placeholder" not in _html()


def _lexicon_roots() -> set[str]:
    yaml = pytest.importorskip("yaml")
    lex = yaml.safe_load(
        (ROOT / "tlon" / "grammar" / "lexicon_expanded.yaml").read_text(
            encoding="utf-8"))
    known = set()
    for entries in lex["classes"].values():
        if isinstance(entries, dict):
            known.update(entries)
    return known


def test_nothing_on_the_face_translates_anything():
    """⛔⛔⛔ THE CARDINAL SIN, AND MY OWN SUITE ENCODED IT.

    A crib stood inside the chat box printing an English sentence, its Tlön
    rendering and a word-by-word gloss — an aligned pair AND a starter
    dictionary, on the face of the page, before the reader had typed a word.
    Two tests here USED TO REQUIRE IT: they asserted the crib had a Tlön line
    and a gloss under it, so the suite would have gone red if anyone removed
    the leak. A green suite that demands the bug is worse than no suite.

    ⭐⭐ THE RULE IS NOW THE OPPOSITE AND IT IS ABSOLUTE: there is exactly one
    way meaning crosses into English in this app, and it is the reader pressing
    TRANSLATE. That press is the mechanic — Tlön encroaching because someone
    let it, one line at a time, by choice. Anything printed for free spends
    that decision on their behalf.

    ⛔ TESTED AS "NO TLÖN LINE ON THE FACE" rather than "no single root",
    because a few roots collide with English words (`ten`, `max`, `pal`) and a
    naive search would fire on prose. A SPECIMEN is what does the damage, and a
    specimen is a run of roots. Three in a row is one.
    """
    roots = _lexicon_roots()
    text = _visible(_html())
    # the page writes ä/ö as entities; the lexicon holds the letters
    text = text.replace("&auml;", "ä").replace("&ouml;", "ö")
    words = re.findall(r"[A-Za-zäöüÄÖÜ]+", text)
    run, worst = 0, []
    for w in words:
        if w.lower() in roots:
            run += 1
            worst.append(w)
            assert run < 3, (
                "⛔⛔⛔ a line of Tlön is printed on the face of the page: %r. "
                "The only thing allowed to render Tlön is a reply, and the "
                "only thing allowed to translate it is the reader pressing "
                "translate." % " ".join(worst[-6:]))
        else:
            run, worst = 0, []


def test_the_crib_markup_and_its_styling_are_both_gone():
    """⛔ Removing the words is half a fix. A surviving `.onset-gloss` rule is
    an invitation: the next person to paste the block back gets a page that
    looks deliberately designed rather than obviously wrong."""
    html, css = _html(), _css()
    for cls in ("onset-line", "onset-gloss", "onset-lead", "onset-body"):
        assert cls not in html, "⛔⛔ the crib markup is back: %s" % cls
        assert cls not in css, "⛔ styling for the crib survives: %s" % cls
    assert "[PLACEHOLDER" not in html


# ── the videos ──────────────────────────────────────────────────────────────

def test_the_page_requests_no_media_that_does_not_exist():
    """⛔⛔ FOUR 404s ON EVERY SINGLE LOAD. Two side runners and two copy slots
    pointed at `/assets/videos/*.mp4`, none of which was ever supplied. The
    `.is-missing` fallback only half-fired — the figures got their dashed box
    while the players kept their controls — and apex's shared chrome painted a
    big black play button over each one, which is the blob at the top of the
    page nobody could account for."""
    html = _html()
    assert "<video" not in html, "⛔⛔ a <video> is back on the page"
    for ref in re.findall(r'src="(/assets/[^"]+)"', html):
        assert (STATIC / ref.lstrip("/")).exists(), (
            "⛔⛔ the page requests %s and there is no such file — that is a "
            "404 in front of every reader" % ref)


def test_the_dead_video_handler_went_with_the_markup():
    """⛔ A handler for elements that no longer exist is an invitation to add
    the elements back. It also silently re-enables the half-working hide."""
    assert "data-placeholder-video" not in _js()
    assert "data-placeholder-video" not in _html()
    assert "copy-video" not in _css(), "styling for a deleted element"


# ── the chat box ────────────────────────────────────────────────────────────

def test_the_composer_is_the_real_chat_composer():
    """⛔⛔ "THERE'S NO CLEAR ACTUAL CHAT BOX." The page wore `.oracle-ask` +
    `.oracle-input`, which is the Oracle's LANDING-PAGE ask row: a bare field
    floating in whitespace. `.oracle-composer` — bounded, bordered, with its
    own send button — was already defined in the oracle.css this page loads and
    was simply never used."""
    html = _html()
    assert "oracle-composer" in html, "⛔⛔ the bench has no real composer"
    assert "oracle-composer-input" in html
    assert 'class="oracle-ask"' not in html, (
        "⛔ the landing-page ask row is back")


def test_the_bench_is_a_bounded_box():
    """⭐ The complaint was that nothing on the page said 'this is where you
    type'. A border is what says it."""
    assert "bench-box" in _html()
    css = _css()
    box = css[css.index(".bench-box {"):]
    box = box[:box.index("}")]
    assert "border" in box, "the bench box has no border"


def test_main_content_exists_for_the_three_things_that_key_off_it():
    """⛔⛔ THREE SILENT FAILURES FROM ONE MISSING ELEMENT, in sheets the page
    already loads:
      * apex's bar.js injects a skip-link to `#main-content` — it pointed at
        nothing, so the page's only keyboard shortcut was a no-op;
      * `main > .container { max-width: none }` never applied, so the chat kept
        a narrow measure instead of the 900px reading column;
      * `main { position: relative; z-index: 1 }` never applied.
    None of the three raises anything."""
    html = _html()
    assert re.search(r'<main[^>]*id="main-content"', html), (
        "⛔⛔ #main-content is missing — the skip link points at nothing and "
        "two layout rules in oracle.css are silently dead")


# ── the order ───────────────────────────────────────────────────────────────

def test_the_brief_comes_before_the_bench():
    """⛔⛔ THE PAGE ASKED YOU TO TALK TO IT BEFORE TELLING YOU WHAT IT WAS.
    "what this is" and "how to use it" sat UNDER the composer, and a reader who
    scrolls past a chat box does not come back up for the explanation."""
    html = _html()
    at_what = html.index('id="what"')
    at_how = html.index('id="how"')
    at_form = html.index('id="ask-form"')
    assert at_what < at_form, "⛔⛔ 'what this is' is below the composer again"
    assert at_how < at_form, "⛔⛔ 'how to use it' is below the composer again"


def test_the_empty_state_survives_a_refused_turn():
    """⛔⛔ IT WAS TAKEN AWAY BEFORE ANYTHING REPLACED IT. `app.js` hid the
    empty state the moment you pressed send, so a turn that came back refused —
    a rate limit, a failed check, a cold container — left the reader looking at
    a blank box with no way back short of a reload they had no reason to try.

    ⭐ Caught by watching the real failure path rather than by reading the
    code: the challenge went interactive, the turn never completed, and the
    empty state had already vanished.

    ⛔ THE ANCHOR MOVED WITH THE CODE. The send logic now lives in `submit()`
    so the gate can finish a message the reader queued before passing it; the
    old anchor was the form listener, which no longer contains the POST."""
    js = _js()
    at_fn = js.index("function submit(english)")
    at_post = js.index('post("/say"', at_fn)
    at_hide = js.index("empty.hidden = true", at_fn)
    assert at_hide > at_post, (
        "⛔⛔ the empty state is hidden before the turn is known to have "
        "succeeded — a refused turn leaves the bench blank")


def test_the_closing_note_stays_below():
    """⭐ The control. If everything moved above the bench the test above would
    pass while the page had become a wall of copy with a field at the bottom —
    which is the failure it was written to prevent, mirrored."""
    html = _html()
    assert html.index('id="why"') > html.index('id="ask-form"'), (
        "the closing note belongs after you have talked to it, not before")


def test_the_tab_has_an_icon():
    """⛔ `/favicon.ico` WAS A 404 — checked against the live site during the v1
    audit, so every tab showed the browser's blank-page mark. It is the one
    piece of chrome a reader meets before they have read a word, and the one
    that silently says whether anybody finished this.

    ⭐ Apex's own logo, which the page's `img-src` already allows — so this
    costs no CSP change and cannot be the thing that breaks the policy."""
    html = (ROOT / "puzzle" / "static" / "index.html").read_text(encoding="utf-8")
    assert re.search(r'<link[^>]+rel="icon"[^>]+href="[^"]+"', html), (
        "⛔ the page declares no icon, so the tab falls back to /favicon.ico "
        "and that path does not exist")
