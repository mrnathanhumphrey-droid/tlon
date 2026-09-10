"""⛔⛔ RED-PROOF FOR THE STEP-SCOPE LINT — the fifth instance of a class.

A step written for one `SCOPE_MODE` running unconditionally in the other, four
times patched per-instance and still recurring:

    --unfreeze-top    required in layers, refused in mapping. Deleted outright
                      when the file was set up for mapping, which made a layer
                      rung unrunnable — and a test pinned the ABSENCE.
    mapping_moved     asserts movement in leaves a layer rung FREEZES BY DESIGN.
                      Refused run 2a after a clean train and a clean read,
                      killing the pipeline before `verdict_epoch1` and before
                      the run files were persisted. The numbers survived only
                      because the watchdog's flush pushed the log.
    vocab_coverage    feeds `mapping_moved` and nothing else; ran on the OLMo
                      layer rung and produced a number no gate consumed.

⭐ Four patches did not stop it, so the check is structural — the heredoc lint's
lesson applied a second time.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

import lint_step_scope as L                                       # noqa: E402

PIPE = _ROOT / "tools" / "pipeline_fullft.sh"

HEAD = 'SCOPE_MODE=${SCOPE_MODE:-mapping}\n'


def _write(tmp_path, body):
    p = tmp_path / "pipeline_x.sh"
    p.write_text(HEAD + body, encoding="utf-8")
    return p


def test_the_live_pipeline_passes():
    """⭐ The state this lint was built to reach, asserted on the real file."""
    assert L.check(PIPE) == []


def test_an_unannotated_step_is_REFUSED(tmp_path):
    """⛔⛔ THE TEETH. A new step arrives unclassified, and that is the moment
    the decision is actually being made."""
    p = _write(tmp_path, "step brand_new\n$PY tools/x.py\n")
    probs = L.check(p)
    assert len(probs) == 1
    assert "no `# SCOPE:` annotation" in probs[0]


def test_a_mode_specific_step_OUTSIDE_its_guard_is_REFUSED(tmp_path):
    """⛔⛔ RUN 2a, REPRODUCED. `mapping_moved` declared mapping-only and sitting
    unguarded is exactly the state that refused a clean OLMo run."""
    p = _write(tmp_path, "step mapping_moved            # SCOPE: mapping\n"
                         "$PY - <<PY\nprint(1)\nPY\n")
    probs = L.check(p)
    assert len(probs) == 1
    assert "must sit inside a matching" in probs[0]


def test_a_mode_specific_step_INSIDE_its_guard_passes(tmp_path):
    p = _write(tmp_path,
               'if [ "$SCOPE_MODE" = "mapping" ]; then\n'
               "step mapping_moved            # SCOPE: mapping\n"
               "fi\n")
    assert L.check(p) == []


def test_a_step_in_the_WRONG_guard_is_REFUSED(tmp_path):
    """⛔ Guarded is not enough — guarded by the mode it CLAIMS."""
    p = _write(tmp_path,
               'if [ "$SCOPE_MODE" = "layers" ]; then\n'
               "step mapping_moved            # SCOPE: mapping\n"
               "fi\n")
    probs = L.check(p)
    assert len(probs) == 1
    assert "guarded by 'layers'" in probs[0]


def test_an_ANY_step_inside_a_guard_is_REFUSED(tmp_path):
    """⛔ The symmetric lie. A step labelled `any` that only runs in one mode
    is a false label, and a reader trusting the label would be wrong about when
    it runs."""
    p = _write(tmp_path,
               'if [ "$SCOPE_MODE" = "mapping" ]; then\n'
               "step persist_leg1            # SCOPE: any\n"
               "fi\n")
    probs = L.check(p)
    assert len(probs) == 1
    assert "declares SCOPE: any but sits inside" in probs[0]


def test_an_unknown_mode_is_REFUSED(tmp_path):
    p = _write(tmp_path, "step x            # SCOPE: sometimes\n")
    assert "unknown SCOPE" in L.check(p)[0]


def test_a_PYTHON_if_inside_a_heredoc_cannot_corrupt_the_depth_count(tmp_path):
    """⛔⛔ THE FALSE-POSITIVE THAT WOULD HAVE MADE THIS LINT USELESS. The
    pipeline embeds Python heredocs full of `if ...:` and `else:`. Shell `if [`
    and a bare `fi` are the only tokens counted, and Python has neither — so a
    heredoc payload cannot open or close a guard."""
    p = _write(tmp_path,
               'if [ "$SCOPE_MODE" = "mapping" ]; then\n'
               "$PY - <<PY\n"
               "if verdict != MAPPING_MOVED:\n"
               "    raise SystemExit(1)\n"
               "else:\n"
               "    pass\n"
               "PY\n"
               "step mapping_moved            # SCOPE: mapping\n"
               "fi\n")
    assert L.check(p) == []


def test_a_file_without_SCOPE_MODE_is_not_policed(tmp_path):
    """⭐ The read-only pipeline has no scope modes and nothing to classify;
    policing it would be a rule stretched past its scope."""
    p = tmp_path / "pipeline_y.sh"
    p.write_text("step anything\n", encoding="utf-8")
    assert L.check(p) == []


def test_nested_guards_close_correctly(tmp_path):
    """⛔ A plain `if` nested inside the guard must not pop it."""
    p = _write(tmp_path,
               'if [ "$SCOPE_MODE" = "mapping" ]; then\n'
               'if [ -f x ]; then\n'
               '  echo hi\n'
               'fi\n'
               "step mapping_moved            # SCOPE: mapping\n"
               "fi\n"
               "step persist_leg1            # SCOPE: any\n")
    assert L.check(p) == []
