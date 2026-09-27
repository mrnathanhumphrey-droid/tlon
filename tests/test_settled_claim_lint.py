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
import lock_prereg as LP         # noqa: E402
import re                        # noqa: E402

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


def _locked_exempt(path, text):
    """-> True if this is a LOCKED prereg whose body still matches its hash.

    ⛔⛔ THE SECOND TIME A LINT HIT A LOCKED BODY, THE PROCESS WAS FIXED
    INSTEAD OF THE DOCUMENT. `PREREG_IDF1_2026_09_25.md` and
    `PREREG_IDF2_2026_09_26.md` both trip the keyword rule, and in both cases
    every available fix — rephrase, or an inline waiver — EDITS A LOCKED BODY
    AFTER RESULTS EXIST. A pre-registration whose text can be adjusted once
    the numbers are in is not a pre-registration, and "the change was only
    cosmetic" is exactly the judgment the lock is built not to trust.

    ⭐ THE EXEMPTION IS THE HASH, NOT THE FILENAME, SO NOTHING IS SILENTLY
    WAIVED. A locked file is exempt only while it matches its own recorded
    sha; the first later edit changes that sha and the lint fires again on the
    edited text. An unlocked prereg is never exempt — which is what makes the
    pre-lock gate in `tools/lock_prereg.py` the place the keywords actually
    get caught, while they can still be rewritten.
    *(Wilson, 2026-09-26.)*
    """
    if path.parent.name != "docs" or not path.name.startswith("PREREG_"):
        return False
    m = LP.LOCK_RE.search(text)
    if m is None or "_(unset" in m.group(0):
        return False
    stamped = re.search(r"`([0-9a-f]{8})`", m.group(0))
    return bool(stamped) and stamped.group(1) == LP.body_hash(text)


def test_the_live_decision_documents_are_currently_clean():
    """The suite fails if a new unqualified settled claim lands in a live doc."""
    root = pathlib.Path(__file__).resolve().parents[1]
    bad = {}
    for g in L.LIVE_GLOBS:
        for f in root.glob(g):
            text = f.read_text(encoding="utf-8")
            if _locked_exempt(f, text):
                continue
            v = L.violations(text)
            if v:
                bad[f.name] = [x[0] for x in v]
    assert not bad, bad


def test_the_exemption_is_the_HASH_and_not_the_name(tmp_path):
    """⛔⛔ An exemption keyed on a filename is a permanent waiver wearing a
    condition. This one must survive the file being locked and die the moment
    the body moves."""
    docs = tmp_path / "docs"
    docs.mkdir()
    p = docs / "PREREG_FAKE.md"
    body = ("- **Status:** _(unset)_\n- **LOCK:** _(unset)_\n\n"
            "The design is adapter-limited.\n")
    p.write_text(body, encoding="utf-8")

    # unlocked -> NOT exempt, and it really does violate
    assert L.violations(p.read_text(encoding="utf-8"))
    assert not _locked_exempt(p, p.read_text(encoding="utf-8"))

    # ⛔ The pre-lock gate REFUSES this body — that is the point of it, and it
    # is asserted here rather than worked around silently.
    assert LP.main([str(p), "--lock"]) == 1
    assert "_(unset" in p.read_text(encoding="utf-8"), (
        "a refused lock must not have stamped anything")

    # locked (over the gate, deliberately) -> exempt
    assert LP.main([str(p), "--lock", "--force"]) == 0
    text = p.read_text(encoding="utf-8")
    assert _locked_exempt(p, text)
    assert L.violations(text), "the fixture must still violate, or this is vacuous"

    # edited after the lock -> the sha moves and the exemption is GONE
    p.write_text(text + "\nAnd one more line.\n", encoding="utf-8")
    assert not _locked_exempt(p, p.read_text(encoding="utf-8"))


def test_the_pre_lock_gate_refuses_a_clean_looking_but_dirty_body(tmp_path):
    """⛔⛔ THE PROCESS FIX'S OTHER HALF. The suite exempting locked bodies is
    only safe because the words are caught BEFORE the hash exists. If this
    gate were advisory, the exemption would become the permanent waiver it
    was designed not to be."""
    docs = tmp_path / "docs"
    docs.mkdir()
    p = docs / "PREREG_GATE.md"
    p.write_text("- **Status:** _(unset)_\n- **LOCK:** _(unset)_\n\n"
                 "Identical speakers cannot converge — that's arithmetic.\n",
                 encoding="utf-8")
    assert LP.main([str(p), "--lock"]) == 1
    assert "_(unset" in p.read_text(encoding="utf-8")


def test_the_pre_lock_gate_passes_a_qualified_body(tmp_path):
    """⭐ And it must not be a blanket refusal: a claim carrying its interval
    locks normally. A gate that refuses everything is a gate nobody runs."""
    docs = tmp_path / "docs"
    docs.mkdir()
    p = docs / "PREREG_OK.md"
    p.write_text("- **Status:** _(unset)_\n- **LOCK:** _(unset)_\n\n"
                 "The effect is 0.42, CI [0.31, 0.54].\n", encoding="utf-8")
    assert LP.main([str(p), "--lock"]) == 0
    assert LP.main([str(p)]) == 0          # and it verifies afterwards


def test_a_non_prereg_live_document_is_never_exempt(tmp_path):
    """⭐ `MEASUREMENTS.md` is the document the rule exists for. It is live,
    it is edited constantly, and no lock may ever excuse it."""
    p = tmp_path / "MEASUREMENTS.md"
    p.write_text("- **LOCK:** `deadbeef`\n\nThe design is adapter-limited.\n",
                 encoding="utf-8")
    assert not _locked_exempt(p, p.read_text(encoding="utf-8"))


def test_the_check_can_FAIL_so_it_has_not_merely_been_consulted():
    assert L.violations("The design is adapter-limited.")
    assert not L.violations("nothing settled-sounding here at all")
