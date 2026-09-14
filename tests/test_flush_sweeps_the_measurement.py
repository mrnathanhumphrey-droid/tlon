"""⛔⛔ THE DYING BOX MUST NOT TAKE THE MEASUREMENT WITH IT.

WHY THIS EXISTS. `cmd_flush`'s docstring already records that it was written
because a run log was lost, and already records a FOURTH instance of the
hardcoded-name class inside itself. It swept `pipeline_*.log`, `manifest.json`
and `watchdog.log` — and **nothing the run measured**.

So on 2026-09-13 `mismap-s20624` and on 2026-09-14 `miscurve-s20624` both died
on a branch that exited before their persist, and both measurements were
recovered ONLY because the numbers had been printed into a log the flush did
cover. The curve JSONL itself reached no hub at all. ⛔ Twice is not luck, it is
a dependency on an accident — and a lost measurement is worse than a lost model,
because the model retrains and the reading is simply gone.

⭐ THE FILENAMES BELOW ARE FROM RUNS THAT ACTUALLY FIRED. A test that invents
plausible names proves the patterns match the test author's imagination.
"""
import importlib.util
import pathlib

import pytest


def _bp():
    p = (pathlib.Path(__file__).resolve().parents[1] / "tools"
         / "act2_box_persist.py")
    spec = importlib.util.spec_from_file_location("_bp", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


#: ⭐ REAL ARTIFACT NAMES, taken from the run trees of fired cells.
FIRED_ARTIFACTS = [
    ("pipeline_fullft.log", "the record of WHY"),
    ("verdict_mismap-s20624_e1.json", "the verdict"),
    ("verdict_miscurve-s20624_e2.json", "the epoch-2 verdict"),
    ("model_lag_miscurve-s20624_e1.json", "the lag profile"),
    ("dose_curve_miscurve-s20624.jsonl", "THE CURVE — lost on 2026-09-14"),
    ("vocab_coverage.json", "the per-leaf gate's prediction"),
    ("mapping_moved.json", "the per-leaf gate's result"),
    ("factorial.json", "the run's own description of itself"),
    ("weight_delta.json", "the dose"),
]


@pytest.mark.parametrize("name,what", FIRED_ARTIFACTS,
                         ids=[n for n, _ in FIRED_ARTIFACTS])
def test_a_real_artifact_is_swept_by_some_flush_pattern(name, what, tmp_path):
    """Each artifact a fired run produced must match at least one pattern."""
    (tmp_path / name).write_text("x", encoding="utf-8")
    hit = any(list(tmp_path.glob(p)) for p in _bp().FLUSH_PATTERNS)
    assert hit, "%s (%s) is swept by no flush pattern" % (name, what)


def test_the_curve_that_was_actually_lost_is_covered():
    """⛔⛤ THE REGRESSION. This exact filename existed on a terminated box and
    reached no hub. If this ever fails again, the same $12 is at risk."""
    assert any(pathlib.PurePath("dose_curve_miscurve-s20624.jsonl").match(p)
               for p in _bp().FLUSH_PATTERNS)


def test_the_model_is_not_swept():
    """⛔ `flush` runs on a box already being terminated FOR COST. Sweeping the
    14.5 GB model would turn a shutdown into a long upload, which is how a
    bounded failure becomes an unbounded bill. The model has its own stage."""
    for heavy in ("model.safetensors", "model-00001-of-00003.safetensors",
                  "delta_snapshot.pt"):
        assert not any(pathlib.PurePath(heavy).match(p)
                       for p in _bp().FLUSH_PATTERNS), heavy


def test_the_patterns_are_patterns_not_names():
    """⛔⛔ THE CLASS ITSELF, five instances deep in this one function. A literal
    name cannot survive a cell rename, and every reading in this arm carries the
    cell name in its filename."""
    literals = [p for p in _bp().FLUSH_PATTERNS if "*" not in p]
    assert set(literals) <= {"vocab_coverage.json", "mapping_moved.json",
                             "factorial.json"}, (
        "cell-specific artifacts must be matched by pattern, not by name: %s"
        % literals)


def test_flush_is_best_effort_and_says_so(tmp_path):
    """⛔ It must not raise: it runs on a box that is already terminating, and
    an exception here strands a billing instance."""
    import inspect
    src = inspect.getsource(_bp().cmd_flush)
    assert "except Exception" in src
    assert "return 0" in src
