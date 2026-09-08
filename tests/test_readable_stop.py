"""THE FIXED STOPPING RULE — PREREG `9ccf98d6` §3.

⛔⛔ THE BUG THIS PINS COST A RUN. Rung 1a's early stop fired on `[ $E1 -eq 0 ]`
— GO alone. Its epoch 1 was a clean floored-but-fluent (b): release FAIL,
perceive PASS, f_local PASS, §4.1 precondition satisfied. That is a complete,
coherent, interpretable measurement, and the stop could not see it. Epoch 2 then
trained past it, every lag rose, f_local cratered, and the verdict of record
became uninterpretable.

⭐ So the rule under test is: **a run must not be able to train past a result it
already has.** GO and floored-but-fluent are both readable and both halt; every
other STOP is not readable and runs epoch 2.

⛔ And the shell condition is pinned in BOTH directions, because a revert to
GO-only would not fail anything else — it would silently reproduce rung 1a.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

from act2_fullft_verdict import (GO, STOP_CRATERED,  # noqa: E402
                                 STOP_FLOORED, STOP_INCOHERENT,
                                 STOP_PERCEIVE, readable_stop)

PIPE = pathlib.Path(__file__).resolve().parents[1] / "tools" / "pipeline_fullft.sh"


def _out(verdict, *, perceive=True, f_local=True):
    return {"verdict": verdict,
            "axes": {"release": {"ok": verdict == GO},
                     "perceive": {"ok": perceive},
                     "f_local": {"ok": f_local}}}


def test_floored_but_fluent_is_readable():
    """⭐ The exact state rung 1a produced at epoch 1 and then destroyed."""
    assert readable_stop(_out(STOP_FLOORED)) is True


def test_go_is_not_a_readable_STOP():
    """GO halts too, but through exit 0 — not through this predicate."""
    assert readable_stop(_out(GO)) is False


def test_a_cratered_or_perceive_killed_or_incoherent_row_is_not_protected():
    """⛔ Nothing there for an epoch 2 to destroy that is not already lost.
    Widening this would turn 'protect a result' into 'halt on anything', which
    is a different procedure than the one hashed into the body."""
    for v in (STOP_CRATERED, STOP_PERCEIVE, STOP_INCOHERENT):
        assert readable_stop(_out(v)) is False, v


def test_floored_with_a_broken_axis_is_not_readable():
    assert readable_stop(_out(STOP_FLOORED, f_local=False)) is False
    assert readable_stop(_out(STOP_FLOORED, perceive=False)) is False


def test_missing_axes_do_not_read_as_readable():
    assert readable_stop({"verdict": STOP_FLOORED}) is False
    assert readable_stop({}) is False


# ── the shell side, pinned in both directions ──────────────────────────────

def test_the_pipeline_halts_on_exit_4_as_well_as_0():
    s = PIPE.read_text(encoding="utf-8")
    assert "[ $E1 -eq 0 ] || [ $E1 -eq 4 ]" in s, (
        "the early stop must halt on a READABLE stop (exit 4) as well as GO. "
        "GO-only is rung 1a's bug and it reproduces silently.")


def test_the_pipeline_does_not_still_carry_the_go_only_stop():
    """⛔ Checked as an absence too: an added clause elsewhere would not
    remove the old one, and the old one would still fire first."""
    s = PIPE.read_text(encoding="utf-8")
    bad = re.findall(r"if \[ \$E1 -eq 0 \]; then", s)
    assert not bad, "the GO-only early-stop condition is still present"


def test_the_verdict_tool_returns_4_for_a_readable_stop_and_1_otherwise():
    """⛔ The contract the shell depends on, asserted on the source so a
    renumbering cannot pass silently."""
    src = (pathlib.Path(__file__).resolve().parents[1] / "tools"
           / "act2_fullft_verdict.py").read_text(encoding="utf-8")
    assert "if readable_stop(out):\n        return 4" in src
    assert "return 3" in src          # precondition fault, unchanged
    assert "return 0" in src          # GO, unchanged


def test_rung_1b_prime_config_is_what_the_prereg_declares():
    """⭐ 19 layers is held from rung 1b; the LR moves to 1e-5 so the
    PER-PARAMETER dose lands on rung 1a's 3.118e-4 (PREREG bd435b37 §2)."""
    s = PIPE.read_text(encoding="utf-8")
    assert re.search(r"^UNFREEZE_TOP=19\b", s, re.M), "bd435b37 §2: 19 layers"
    assert re.search(r"^LR=1e-5\b", s, re.M), "bd435b37 §2: 1e-5, dose-matched"
    assert re.search(r"^TRAINABLE_B=4\.428\b", s, re.M)
    assert re.search(r"^ATTN_IMPL=eager\b", s, re.M), "D-8"


def test_the_cell_does_not_collide_with_rung_1a():
    """⛔⛔ `fw-s$SEED` is rung 1a's cell and its model, verdicts and lag
    profiles are already on the hub. Reusing it would overwrite the artifact
    this run is COMPARED AGAINST — the 17.81 dose figure and the lag2 z=+5.79
    baseline the prereg reads against."""
    s = PIPE.read_text(encoding="utf-8")
    m = re.search(r"^CELL=(\S+)", s, re.M)
    assert m and m.group(1) != "fw-s$SEED", "rung 1b must not write into rung 1a's cell"
    assert m.group(1) == "fw19b-s$SEED"


def test_the_dose_check_runs_before_the_verdict():
    """⭐ §2.1 is a precondition on how the verdict is READ, so it has to be in
    the log before the verdict, not after it."""
    s = PIPE.read_text(encoding="utf-8")
    assert "step dose_check" in s
    assert s.index("step dose_check") < s.index("step verdict_epoch1")
    # ⭐ the gate keys on per-parameter rms, not on delta_norm
    assert "3.118e-4" in s and "2.18e-4" in s and "4.05e-4" in s
    assert "sqrt(n)" in s or "math.sqrt(n)" in s
    assert "NOT the gate" in s, "delta_norm must be labelled a companion"


def test_fraction_changed_is_labelled_precondition_only_in_the_dose_check():
    """⛔ It saturated to the same 16 digits at both of rung 1a's epochs."""
    s = PIPE.read_text(encoding="utf-8")
    assert "PRECONDITION ONLY" in s
    assert "delta_norm_estimated" in s
