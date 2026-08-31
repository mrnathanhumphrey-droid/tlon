"""⛔⛔ RED-PROOF FOR THE GRAMMAR TRIPWIRE — and it caught its own dead spot.

The linter exists because three inquiry-closing claims survived full adversarial
review. So the first thing it must do is fire on those three ACTUAL sentences,
not on invented examples that flatter it.

⭐ It did not, at first. With the original 500-char window it stayed SILENT on
the real "adapter-limited, not replicate-limited" sentence, because "CI
half-width" appeared elsewhere in the same paragraph — an interval on the DRIFT
ESTIMAND, not on `h`, the parameter the diagnosis rested on. The exemption was
satisfied by an interval on the WRONG QUANTITY. Swept 500→60 and pinned 120.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

import lint_settled_claims as L  # noqa: E402

#: ⛔ The real sentence, verbatim from the doc as it stood. It nearly bought 13
#: adapters on a parameter whose CI contains zero.
REAL_ADAPTER_LIMITED = (
    "Quadrupling replicates to 28 shrinks the CI half-width only to roughly "
    "0.27 — still ~23% of the median speaker separation. **The experiment is "
    "adapter-limited, not replicate-limited.** Any serious next attempt needs "
    "more independently-trained speakers first, and more replicates second.")

REAL_ARITHMETIC = ("Identical speakers cannot converge — that is a fact about "
                   "the world, not a hypothesis.")

QUALIFIED = ("h = 0.2519, 95% CI [0.0000, 0.4033], so the lower bound is zero "
             "and the adapter-limited reading is not established.")


def test_it_fires_on_the_real_adapter_limited_sentence():
    assert L.violations(REAL_ADAPTER_LIMITED), (
        "SILENT on the exact claim it was built for — the failure that made a "
        "500-char window useless")


def test_it_fires_on_the_real_arithmetic_lemma():
    assert L.violations(REAL_ARITHMETIC)


def test_a_properly_qualified_claim_passes():
    assert not L.violations(QUALIFIED)


def test_an_interval_on_a_DIFFERENT_quantity_must_not_excuse_the_claim():
    """⛔⛔ THE DEAD SPOT. A CI far away, about something else, is not evidence
    for this claim. The window is what keeps the exemption local."""
    far = ("The drift CI is [-0.2856, +0.4637]. " + "padding text. " * 14 +
           "The experiment is adapter-limited, not replicate-limited.")
    assert L.violations(far)


def test_a_line_break_inside_the_phrase_does_not_hide_it():
    """A line-oriented grep declared a file clean while the false lemma was in
    it, wrapped across a newline."""
    assert L.violations("The design is adapter-\nlimited." .replace("-\n", "-"))
    assert L.violations("Identical speakers cannot\nconverge, so the column is 0.")


def test_the_waiver_works_and_needs_to_be_deliberate():
    assert not L.violations(
        "The design is adapter-limited. settled-claim-ok: definitional here.")


def test_a_file_level_waiver_covers_the_whole_document():
    doc = ("<!-- settled-claim-ok: this doc is ABOUT the uncertainty -->\n" +
           "filler. " * 40 + "\nThe experiment is adapter-limited.")
    assert not L.violations(doc)


def test_hypothesis_TEST_is_a_different_and_legitimate_sense():
    assert not L.violations("Descriptive, not a hypothesis test: it estimates "
                            "a spread.")


def test_the_live_decision_documents_are_currently_clean():
    """The suite fails if a new unqualified settled claim lands in a live doc."""
    root = pathlib.Path(__file__).resolve().parents[1]
    bad = {}
    for g in L.LIVE_GLOBS:
        for f in root.glob(g):
            v = L.violations(f.read_text(encoding="utf-8"))
            if v:
                bad[f.name] = [x[0] for x in v]
    assert not bad, bad


def test_the_check_can_FAIL_so_it_has_not_merely_been_consulted():
    assert L.violations("The design is adapter-limited.")
    assert not L.violations("nothing settled-sounding here at all")
