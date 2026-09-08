"""THE VERDICT MUST NAME THE PREREG IT ACTUALLY ANSWERS.

⛔⛔ IT DID NOT. `act2_fullft_verdict.py` hardcoded `"PREREG": "a0450b36"`, so
rung 1b — a run under `9ccf98d6`, with a different scope (19 layers vs 14), a
different LR (5e-6 vs 1e-5) and a different stopping rule — emitted a verdict
claiming it answered a document it did not answer. Nothing failed. No guard
fired. The artifact is self-describing and its description was false, and it
will outlive anyone's memory of which prereg was which.

⭐ So the id is READ FROM THE LOCKED FILE AND RE-VERIFIED at emit time. A stamp
line only proves someone typed an id; re-hashing proves the body that
pre-registered the reading is the body still on disk.
"""
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from act2_fullft_verdict import (GO, STOP_FLOORED,  # noqa: E402
                                 decide, verified_prereg_id)

VERDICT_SRC = (ROOT / "tools" / "act2_fullft_verdict.py").read_text(encoding="utf-8")
PIPE = (ROOT / "tools" / "pipeline_fullft.sh").read_text(encoding="utf-8")
PREREGS = sorted((ROOT / "docs").glob("PREREG_*.md"))


def _ok_delta():
    return {"verdict": "OK", "fraction_changed": 1.0}


def _lag(lag2=1.0):
    return {"z": {"1": 20.0, "2": lag2}}


def test_the_emitted_prereg_field_is_never_a_literal():
    """⛔ The exact defect, pinned. Prose references to an id in a docstring are
    fine and useful; what must never recur is the EMITTED field being typed."""
    m = re.search(r'"PREREG":\s*([^,\n]+)', VERDICT_SRC)
    assert m, "no PREREG field is emitted at all"
    val = m.group(1).strip()
    assert not re.fullmatch(r'''["'][0-9a-f]{8}["']''', val), (
        "the PREREG field is the hardcoded literal %s — the rung-1b defect "
        "exactly" % val)
    assert val == "prereg", val


def test_the_emitted_verdict_carries_the_id_it_was_given():
    out = decide(_ok_delta(), _lag(), {"fired": False}, prereg="9ccf98d6")
    assert out["PREREG"] == "9ccf98d6"
    assert out["verdict"] == GO


def test_every_locked_prereg_verifies_through_the_reader():
    """⭐ The reader is exercised against the real documents, so a change to the
    stamp format breaks a test rather than silently matching nothing."""
    checked = 0
    for p in PREREGS:
        text = p.read_text(encoding="utf-8")
        # ⚠️ Only 16 of this repo's 22 preregs carry a hashed LOCK line at all;
        # the other 6 are locked by PROSE ASSERTION and cannot be verified by
        # anything. Scoped explicitly rather than silently passing over them,
        # because "carries no hash" and "hash matches" are different states and
        # a test that conflates them reports coverage it does not have.
        if not re.search(r"^- \*\*LOCK:\*\* `", text, re.M):
            continue
        if "_(unset" in text:
            continue
        got = verified_prereg_id(p)
        assert re.fullmatch(r"[0-9a-f]{8}", got), (p.name, got)
        checked += 1
    assert checked >= 15, "expected the hash-locked preregs to verify, got %d" % checked


def test_a_tampered_prereg_is_REFUSED_not_reported():
    """⛔⛔ A body that moved after the lock must not be able to pre-register a
    reading. Refusal, not a warning — a warning in a pipeline log is a line
    nobody reads."""
    src = ROOT / "docs" / "PREREG_FULL_FINETUNE_RUNG_1B_PRIME_2026_09_07.md"
    tmp = pathlib.Path(str(src) + ".tampered.tmp")
    try:
        tmp.write_text(src.read_text(encoding="utf-8") + "\nsmuggled clause\n",
                       encoding="utf-8")
        with pytest.raises(SystemExit, match="TAMPERED"):
            verified_prereg_id(tmp)
    finally:
        tmp.unlink(missing_ok=True)


def test_an_unlocked_draft_cannot_pre_register_a_reading(tmp_path):
    d = tmp_path / "PREREG_draft.md"
    d.write_text("# draft\n\n- **LOCK:** _(unset)_\n\nbody\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="no LOCK id"):
        verified_prereg_id(d)


def test_a_missing_prereg_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="no prereg at"):
        verified_prereg_id(tmp_path / "nope.md")


def test_prereg_is_a_required_argument():
    """⛔ Optional would mean a run could emit an unattributed verdict."""
    assert '"--prereg", required=True' in VERDICT_SRC


def test_both_pipeline_verdict_calls_pass_the_prereg():
    """⛔ Two legs, two call sites — the same both-legs failure shape as the
    attention flag."""
    assert PIPE.count("--prereg $PREREG_PATH") == 2
    assert re.search(r"^PREREG_PATH=", PIPE, re.M)


def test_the_pipeline_points_at_the_prereg_its_config_implements():
    """⛔ The run is 19 layers at 5e-6, which is 9ccf98d6's config, so the
    verdict must be attributed to 9ccf98d6 and not to its predecessor."""
    m = re.search(r"^PREREG_PATH=\$\{PREREG_PATH:-(\S+)\}", PIPE, re.M)
    assert m, "PREREG_PATH is not set with a default"
    named = ROOT / m.group(1)
    assert named.exists(), named
    assert verified_prereg_id(named) == "bd435b37"


def test_the_factorial_entry_is_not_a_SECOND_hardcoded_prereg():
    """⛔⛔ THE SAME DEFECT, ONE FILE OVER, AND THE FIRST FIX DID NOT REACH IT.

    `act2_fullft_verdict.py` was corrected to read its prereg id from the locked
    body. `factorial.json` — a DIFFERENT artifact, persisted to the hub beside
    the weights — still carried `prereg="a0450b36"` typed into the pipeline. So
    rung 1b′ would have shipped a manifest claiming rung 1a's pre-registration
    while its verdict correctly claimed `bd435b37`: two artifacts of one run,
    disagreeing about which document the run answers.

    ⭐ The lesson is the guard's SCOPE, not the literal: a fix written on the
    file that got caught does not close the failure mode, and nothing asked the
    other call sites. ⛔ Prose references to an id in comments stay legal — this
    pins the ARGUMENT, the same shape as the verdict-field test above.

    ⚠️ Scoped to EXECUTABLE lines. The first form of this test read the whole
    file and matched its own explanatory comment — a guard reporting on prose
    while the live call sat untouched two lines down. Narrowed to the real
    invariant rather than weakened: EVERY `prereg=` argument the shell actually
    runs, not merely the first one found."""
    live = "\n".join(ln for ln in PIPE.splitlines()
                     if not ln.lstrip().startswith("#"))
    found = re.findall(r"prereg=([^,\s]+)", live)
    assert found, "the factorial entry names no prereg at all"
    for got in found:
        assert not re.fullmatch(r'"[0-9a-f]{8}"', got), (
            "a prereg id is hardcoded in the pipeline: %s" % got)
        assert got == '"$PREREG_ID"', got


def test_the_pipeline_resolves_that_id_through_the_verified_reader():
    """⛔ `PREREG_ID` must come from the LOCKED BODY, not be typed as a second
    literal one line up — that would move the defect, not close it."""
    assert "PREREG_ID=$(" in PIPE
    assert "verified_prereg_id('$PREREG_PATH')" in PIPE
    assert re.search(r"^step prereg_id", PIPE, re.M), (
        "the resolution must be its own logged step — an unlogged floor is a "
        "check nobody can confirm ran")
    # ⭐ A FLOOR, not an afterthought: it has to fail before the training spend,
    # and after the watchdog is armed so a failure cannot strand a live box.
    assert PIPE.index("tlon_arm_watchdog") < PIPE.index("step prereg_id")
    assert PIPE.index("step prereg_id") < PIPE.index("step train_leg1")


def test_readable_stop_still_gates_on_the_floored_row_only():
    """⭐ Guard against this edit having disturbed the stopping rule."""
    out = decide(_ok_delta(), _lag(lag2=9.0), {"fired": False}, prereg="x" * 8)
    assert out["verdict"] == STOP_FLOORED
