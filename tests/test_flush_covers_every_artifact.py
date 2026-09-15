"""⛔⛔ THE FLUSH PATTERNS ARE FOUND FROM THE PIPELINE, NOT MAINTAINED BY HAND.

`cmd_flush` has now been the site of SIX instances of one class: a hardcoded list
of names that drifted from the set of things the pipeline actually writes. The
worst cost two runs their entire measurement, and both survived only because
their numbers had been printed into a log the sweep happened to catch.

⭐⭐ AND A LIST CANNOT FIX A LIST. An author-maintained set of filenames catches
omissions only among the artifacts the author remembered — which is exactly the
call-site lesson (`tests/test_gate_sites_are_found_not_listed.py`) one layer
down. So this test does not enumerate artifacts. It SCANS the pipeline for every
`$ROOT/...` path it writes and asserts each one matches a flush pattern, so a new
artifact added to the pipeline without a pattern fails here rather than on the
box.

⛔ THE STAKES JUST ROSE. Under PREREG_EPOCHS_LEVER §2.2 the arms do NOT persist
their weights: the readings are the SOLE record, with no re-read-the-weights
fallback. A reading lost on an exit path is now a LOST RUN, not a recoverable one.
"""
import fnmatch
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from act2_box_persist import FLUSH_PATTERNS                   # noqa: E402

PIPE = (ROOT / "tools" / "pipeline_fullft.sh").read_text(encoding="utf-8")

#: ⭐ Always swept regardless of pattern — `cmd_flush` adds these by name.
ALWAYS = {"manifest.json", "watchdog.log"}

#: ⛔ DELIBERATELY NOT FLUSHED, EACH WITH ITS REASON. An exclusion list is
#: allowed to be hand-maintained only because every entry must say WHY, and a
#: new artifact is not excluded by default — the scan fails until someone
#: decides.
EXCLUDED = {
    # gigabytes of optimizer-delta working state; the readings derived from it
    # are what the run is for, and re-uploading it on every exit is the failure
    # `cmd_flush` was narrowed to avoid.
    "delta_snapshot.pt",
}


def artifacts():
    """Every `$ROOT/<file>` the pipeline names, discovered not listed."""
    out = set()
    for m in re.finditer(r"\$ROOT/([A-Za-z0-9_${}.*-]+)", PIPE):
        name = m.group(1)
        if "/" in name or "." not in name:
            continue                       # a directory (corpora, model_$CELL)
        # normalise the shell interpolations to a concrete example name
        name = re.sub(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?", "CELL", name)
        out.add(name)
    return sorted(out)


def test_the_scan_finds_artifacts_at_all():
    """⛔ A scan that finds nothing passes everything."""
    found = artifacts()
    assert len(found) >= 8, ("the artifact scan found only %d paths — the "
                             "pipeline's layout has changed and this guard is "
                             "now vacuous: %s" % (len(found), found))


def test_every_artifact_the_pipeline_writes_is_swept_or_excluded():
    """⛔⛔ THE WHOLE POINT. A reading the flush cannot see is a reading that
    does not survive the exit path that loses it — and with weights unpersisted
    there is no second copy anywhere."""
    missing = []
    for name in artifacts():
        if name in ALWAYS or name in EXCLUDED:
            continue
        if not any(fnmatch.fnmatch(name, p) for p in FLUSH_PATTERNS):
            missing.append(name)
    assert not missing, (
        "%d artifact(s) the pipeline writes match no flush pattern, so they do "
        "not survive an exit:\n  %s\nAdd a pattern, or add to EXCLUDED with the "
        "reason." % (len(missing), "\n  ".join(missing)))


def test_the_step_match_manifest_is_swept():
    """⛔⛔ THE ARMS' OWN IDENTITY. Without weights, this manifest is the only
    record of M, both step counts, Δ, the subsample seed and shas. Losing it
    leaves readings with no proof the arms were matched."""
    assert any(fnmatch.fnmatch("step_match_epochlevA-s20624.json", p)
               for p in FLUSH_PATTERNS)


def test_the_curve_and_the_verdicts_are_swept():
    """⛔ The readings themselves — the run's entire result under §2.2."""
    for name in ("dose_curve_epochlevB-s20624.jsonl",
                 "verdict_epochlevB-s20624_e1.json",
                 "model_lag_epochlevB-s20624_e1.json"):
        assert any(fnmatch.fnmatch(name, p) for p in FLUSH_PATTERNS), name


def test_the_big_working_file_is_still_NOT_swept():
    """⛔ `cmd_flush` runs on EVERY exit, including on a box being terminated for
    cost. Sweeping gigabytes there is how a bounded failure becomes an unbounded
    bill."""
    assert not any(fnmatch.fnmatch("delta_snapshot.pt", p)
                   for p in FLUSH_PATTERNS)
