"""IDF-2's instruments — the structural pins `PREREG_IDF2` §1 and §8 require.

LOCK `37363296`. Two things are asserted here that a behavioural test cannot:
that the bar has ONE definition every consumer reaches by identity, and that
the new recipe is quarantined by absence from `RECIPES` rather than by a
sentence in a prereg.

⛔⛤ AND ONE OF THESE IS A REGRESSION TEST FOR A BUG THAT NEVER RAN.
`verify_recipe` dispatches on the recipe string and FALLS THROUGH to the
content-FREE verifier for anything it does not name. `content-transient-held`
was not named, so 0a's very first build would have been checked against the
control's invariant — "refuse if lag-1 is responsive" — and aborted with
`CONTROL IS CONTAMINATED` at lag-1 z +488. The treatment arm, refused for being
the treatment, under the control's name. Found by reading the fall-through
instead of the branches; `test_a_probe_recipe_is_not_verified_as_a_control` is
what keeps it found.
"""
from __future__ import annotations

import collections
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from tlon.discourse import transient as TR              # noqa: E402

Turn = collections.namedtuple("Turn", "surface force inherited")


@pytest.fixture(scope="module")
def lex_r():
    return TR._lex_roots()


@pytest.fixture(scope="module")
def roots(lex_r):
    return sorted(lex_r)[:8]


# ── §1 · one definition, reached by identity ───────────────────────────────

def test_the_oracle_delegates_to_the_one_held():
    """⛔⛔ §1: the builder, the row builder and the reader call THE SAME
    OBJECT. `act2_idf2.barred_held` is the oracle's entry point and it must
    delegate rather than restate — a second spelling of the bar is the drift
    that has already voided one curve in this campaign."""
    import act2_idf2 as I
    src = pathlib.Path(I.__file__).read_text(encoding="utf-8")
    assert "TR.held(out, prev, lex_r)" in src, (
        "barred_held must call TR.held, not restate the intersection")
    # ⭐ And the corpus builder is handed the object itself, not a wrapper.
    assert "barred_fn=TR.held" in src, (
        "0a must pass TR.held directly, so builder and oracle are provably "
        "the same bar")


def test_no_second_spelling_of_the_intersection():
    """⛔ The failure mode is not a wrong answer, it is two right answers that
    drift apart later. So the literal intersection may appear exactly once in
    the codebase — inside `held` itself."""
    hits = []
    for p in list((ROOT / "tools").glob("*.py")) + [ROOT / "tlon" / "discourse"
                                                    / "transient.py"]:
        txt = p.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(txt.splitlines(), 1):
            if "roots_of(prev.surface" in line and "roots_of(out[-2]" in line:
                hits.append("%s:%d" % (p.name, i))
    assert hits == ["transient.py:%d" % _held_line()], (
        "the held intersection is spelt in more than one place: %s" % hits)


def _held_line():
    txt = (ROOT / "tlon" / "discourse" / "transient.py").read_text(
        encoding="utf-8").splitlines()
    for i, line in enumerate(txt, 1):
        if "roots_of(prev.surface" in line and "roots_of(out[-2]" in line:
            return i
    raise AssertionError("held's intersection line not found")


# ── §1 · the semantics, including the off-by-one ───────────────────────────

def test_held_is_empty_when_there_is_no_t_minus_2(lex_r, roots):
    """⛔ `held = ∅` on turns 1 AND 2, not just turn 1. `out[-1]` is `prev`, so
    generating the second turn leaves `out` one element long. An off-by-one
    here desynchronises the builder from the reader silently."""
    a = Turn(" ".join(roots[:3]), "ka", frozenset())
    assert TR.held([a], a, lex_r) == frozenset()
    assert TR.held([], a, lex_r) == frozenset()


def test_held_is_the_intersection_of_the_two_previous_surfaces(lex_r, roots):
    a = Turn(" ".join(roots[0:3]), "ka", frozenset())
    b = Turn(" ".join(roots[1:5]), "ki", frozenset())
    assert TR.held([a, b], b, lex_r) == frozenset(roots[1:3])


def test_held_reads_prev_not_the_last_element(lex_r, roots):
    """⭐ The signature offers both `out[-1]` and `prev`. They are the same
    object in the generator, and a reader that assumed otherwise would still
    pass every test above — so the distinction is pinned here."""
    a = Turn(" ".join(roots[0:3]), "ka", frozenset())
    b = Turn(" ".join(roots[1:5]), "ki", frozenset())
    other = Turn(" ".join(roots[5:8]), "ko", frozenset())
    # `prev` is what is barred against `out[-2]`; passing a different `prev`
    # must change the answer, or `prev` is being ignored.
    assert TR.held([a, b], other, lex_r) == frozenset()


def test_held_ignores_tokens_that_are_not_roots(lex_r, roots):
    a = Turn(roots[0] + " zzzz", "ka", frozenset())
    b = Turn(roots[0] + " qqqq", "ki", frozenset())
    assert TR.held([a, b], b, lex_r) == frozenset({roots[0]})


# ── §1 · the quarantine is structural ──────────────────────────────────────

def test_the_probe_recipe_is_outside_the_factorial():
    """⛔⛔ `RECIPES` is not a list of labels, it is the quarantine.
    `tlon.act2.factorial` validates against it, so absence is what makes
    'never pooled with the dd40e22f / 16abeb8d cells' a fact about the code."""
    assert TR.CONTENT_TRANSIENT_HELD not in TR.RECIPES
    assert TR.CONTENT_TRANSIENT_HELD not in TR.DOSE_ARM_RECIPES
    assert TR.CONTENT_TRANSIENT_HELD in TR.PROBE_RECIPES
    assert TR.CONTENT_TRANSIENT_HELD in TR.ALL_RECIPES


def test_the_factorial_refuses_the_probe_recipe():
    """⭐ The quarantine asserted where it fires, not where it is declared."""
    from tlon.act2 import factorial as F
    src = pathlib.Path(F.__file__).read_text(encoding="utf-8")
    assert "ALL_RECIPES" not in src, (
        "factorial must validate against RECIPES, never ALL_RECIPES — "
        "widening it would admit the probe cell into the matrix")


# ── the regression test for the mislabel ───────────────────────────────────

def test_a_probe_recipe_is_not_verified_as_a_control():
    """⛔⛤ THE BUG THIS FILE EXISTS FOR. `verify_recipe` falls through to the
    content-FREE verifier for any recipe it does not name, and that verifier
    REFUSES a responsive corpus. So the held corpus — responsive at lag-1
    z +488 by construction — would have aborted 0a with `CONTROL IS
    CONTAMINATED`, before a single adapter was priced.

    ⭐ The assertion is on the dispatch, not on an output, because the symptom
    was a refusal message and the cause was a missing branch.
    """
    src = pathlib.Path(TR.__file__).read_text(encoding="utf-8")
    body = src.split("def verify_recipe", 1)[1].split("\ndef ", 1)[0]
    assert "CONTENT_TRANSIENT_HELD" in body, (
        "verify_recipe has no branch for the probe recipe — it will fall "
        "through to the content-free verifier and refuse the treatment arm "
        "for being responsive")
    # ⛔ And the branch must restamp the verdict: `check_transience` returns
    # the string `content-transient`, which the builder writes into the
    # manifest as `recipe_VERIFIED` — the one label that must never attach to
    # this corpus, because that is what `factorial` matches on.
    held_branch = body.split("CONTENT_TRANSIENT_HELD", 1)[1]
    assert 'rep["verdict"] = CONTENT_TRANSIENT_HELD' in held_branch, (
        "the held branch must restamp the verdict, or PROBE_RECIPES is "
        "undone by a manifest field")


def test_the_dispatch_check_can_actually_fail():
    """⛔⛔ A GREEN CHECK PROVES NOTHING UNTIL IT HAS BEEN SEEN TO GO RED."""
    body = "if recipe == CONTENT_TRANSIENT:\n    return check_transience(...)"
    assert "CONTENT_TRANSIENT_HELD" not in body


# ── §3-0f · the shard tripwire ─────────────────────────────────────────────

def test_the_rms_tensor_count_is_asserted_not_trusted():
    """⛔⛔ An rms computed over ONE RANK'S SHARD is a plausible number that
    nothing detects (`01_OUR_FRONTIER.md:222`), and it corrupts the dose that
    §4 matches M, C1 and W2 against. A count is what detects it."""
    import act2_idf2 as I
    assert I.CT_EXPECT_TENSORS == 28 * 7 * 2
    src = pathlib.Path(I.__file__).read_text(encoding="utf-8")
    assert "if n_t != CT_EXPECT_TENSORS" in src, (
        "0f must refuse on a tensor-count mismatch, not merely record it")


def test_step0a_stops_rather_than_reports_on_a_lag1_miss():
    """⛔ §3-0a: the held bar acts on what turn t may OFFER, not on how much it
    echoes, so it is not meant to touch lag-1. A miss is wiring, and wiring
    stops the run — it does not become a row in a table."""
    import act2_idf2 as I
    src = pathlib.Path(I.__file__).read_text(encoding="utf-8")
    a = src.split("def step_0a", 1)[1].split("\ndef ", 1)[0]
    assert "raise SystemExit" in a and "STOP" in a


def test_the_lag1_reference_is_the_measured_one():
    """⭐ Copied out of the artefact, not recalled: `ct-s20624`'s corpus
    manifest records lag-1 0.9621893677256999."""
    import json
    import act2_idf2 as I
    m = json.loads((ROOT / "runs/act2/retrain12_ct/corpus_ct-s20624"
                    / "manifest.json").read_text(encoding="utf-8"))
    assert I.REF_LAG1 == m["recipe_lag_profile"]["1"]
    assert I.REF_CHAINS == m["chains"] and I.REF_TURNS == m["turns"]
    assert I.REF_RESPONSIVENESS == m["recipe_responsiveness"]


# ── §8 · the statistic is imported, never re-spelt ─────────────────────────

def test_the_statistic_is_imported():
    import act2_idf2 as I
    src = pathlib.Path(I.__file__).read_text(encoding="utf-8")
    for spelt in ("def lag_profile", "def permutation_null",
                  "def resolving_power", "def check_transience", "def held"):
        assert spelt not in src, (
            "%s is re-spelt in act2_idf2.py; it must be imported from "
            "tlon.discourse.transient" % spelt)


def test_the_prereg_is_locked_and_unmodified():
    """⛔ Every number this suite pins is read against a LOCKED body. If the
    prereg drifts, the instruments are pinned to a document that no longer
    says what they assume."""
    sys.path.insert(0, str(ROOT / "tools"))
    import lock_prereg
    p = ROOT / "docs" / "PREREG_IDF2_2026_09_26.md"
    text = p.read_text(encoding="utf-8")
    assert lock_prereg.body_hash(text) == "37363296", (
        "PREREG_IDF2 body no longer hashes to its lock")
