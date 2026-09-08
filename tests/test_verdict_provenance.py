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


def test_readable_stop_still_gates_on_the_floored_row_only():
    """⭐ Guard against this edit having disturbed the stopping rule."""
    out = decide(_ok_delta(), _lag(lag2=9.0), {"fired": False}, prereg="x" * 8)
    assert out["verdict"] == STOP_FLOORED
