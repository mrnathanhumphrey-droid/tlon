"""IDF-2 Step P — the absences that make it a READ, and the gate's arithmetic.

`PREREG_IDF2_2026_09_26.md`, LOCK `37363296` §3A.

⛔⛔ THE POINT OF STEP P IS THAT IT SPENDS ALMOST NOTHING AND CAN STOP THE RUN.
That only holds while it stays a read. A training leg, a corpus build or an
adapter persist sneaking into this pipeline would turn the cheap gate into a
second expensive run — and would do it silently, because the script would
still produce a `power.json`. Modelled on `test_reread_pipeline`, which exists
for the same reason.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

SH = ROOT / "tools" / "pipeline_idf2_stepP.sh"


@pytest.fixture(scope="module")
def script():
    return SH.read_text(encoding="utf-8")


# ── the absences ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("forbidden", [
    "act2_finetune", "--train", "pipeline_retrain", "build_corpus",
    "act2_build_multiturn", "full-weight", "persist_cell",
])
def test_step_P_has_no_training_or_build_leg(script, forbidden):
    """⛔ It reads an object that already exists. Anything that would MAKE one
    turns the gate into the run it is meant to gate."""
    assert forbidden not in script, (
        "pipeline_idf2_stepP.sh contains %r — it must stay a read" % forbidden)


def test_step_P_cannot_overwrite_the_object_it_reads(script):
    """⛔⛔ `ct-s20624` is the bridge to every published number in this arc.
    Step P pulls it and must never push anything back under that name."""
    assert "upload_file" not in script
    assert "--adapter" in script, "it must READ an adapter, or it reads a base"
    for line in script.splitlines():
        if "hf_hub_download" in line or "hf_hub_download" in script:
            break
    assert "hf_hub_download" in script, "the adapter is pulled, not assumed"


# ── the guards that must be present ────────────────────────────────────────

def test_the_watchdog_is_armed_before_any_gpu_work(script):
    """⛔⛔ HARD RULE. And BEFORE, not merely present — a watchdog armed after
    the reads guards nothing that could have gone wrong."""
    i_wd = script.index("tlon_arm_watchdog")
    i_read = script.index("act2_model_lag.py")
    assert i_wd < i_read, "the watchdog must be armed before the first read"
    assert "pipeline_idf2_stepP.sh" in script.split("tlon_arm_watchdog")[1][:200], (
        "the watchdog marker must be the SCRIPT, never an output path")


def test_the_prereg_lock_is_checked_before_a_gpu_hour(script):
    i_lock = script.index("lock_prereg.py")
    i_read = script.index("act2_model_lag.py")
    assert i_lock < i_read


def test_the_script_does_NOT_write_the_done_marker_itself(script):
    """⛔⛔ `~/DONE` means PERSISTED-AND-VERIFIED and the watchdog terminates
    within one poll of it. A pipeline that touches it itself has made every
    verification above advisory. `tests/test_pipeline_lib.py` pins the list of
    six older scripts that still do — and it caught this one, which is the
    debt register working."""
    assert "touch ~/DONE" not in script
    assert script.index("tlon_persist_run_files") < script.index(
        "tlon_mark_done"), "persist, THEN mark"


def test_each_seed_is_its_own_process(script):
    """⛔⛔ THE SD IS A BETWEEN-SEED SPREAD. One process looping eight reads
    shares a CUDA RNG lineage, so seed k+1 is not independent of seed k and
    the gate would be calibrated on a correlated sample."""
    body = script.split("step reads", 1)[1]
    assert "for S in $SEEDS" in body
    assert body.count("act2_model_lag.py") == 1, (
        "one invocation inside the loop — not a batched call")


def test_eight_seeds_not_three(script):
    """⭐ Wilson's sign-off #4: 7 df, not 2, on the number that protects the
    whole table."""
    line = [l for l in script.splitlines() if l.startswith("SEEDS=")][0]
    seeds = line.split('"')[1].split()
    assert len(seeds) == 8, seeds
    assert len(set(seeds)) == 8, "the seeds must be distinct"


def test_the_read_geometry_is_the_preregs(script):
    assert "CHAINS=${CHAINS:-48}" in script
    assert "TURNS=${TURNS:-10}" in script
    assert "--temperature 0.7" in script


def test_the_pipeline_is_on_the_orchestrator_allowlist():
    """⛔ The allowlist is what stops an arbitrary script running on a billing
    box. A pipeline that is not named there cannot be launched — which is the
    correct failure, but it must be fixed here rather than by widening the
    check at the call site."""
    import act2_retrain_orchestrate as O
    assert "pipeline_idf2_stepP.sh" in O.PIPELINES
    assert "pipeline_idf2_stepP.sh" not in O.NEEDS_RECIPE, (
        "Step P builds no corpus, so requiring a recipe would file it into an "
        "arm it is not in")


# ── the gate's arithmetic ──────────────────────────────────────────────────

def _read(tmp, seed, lag2, **kw):
    d = {"seed": seed, "temperature": 0.7, "max_new_tokens": 256,
         "decoder_sampled": True, "marker_fn": None,
         "lag_profile": {"1": 1.03, "2": lag2}, "n_pairs": {"2": 384},
         "chains_used": 48, "chains_dropped_too_short": 0}
    d.update(kw)
    (tmp / ("lag_ct-s20624_s%d.json" % seed)).write_text(json.dumps(d))


@pytest.fixture
def step0(tmp_path):
    p = tmp_path / "step0.json"
    p.write_text(json.dumps({"blind_lag2": 0.4456, "corpus_lag2": 0.0224}))
    return p


def _run(tmp, step0):
    import act2_idf2_power as P
    out = tmp / "power.json"
    rc = P.main(["--root", str(tmp), "--cell", "ct-s20624",
                 "--step0", str(step0), "--out", str(out)])
    return rc, json.loads(out.read_text(encoding="utf-8"))


def test_a_tight_spread_PASSES(tmp_path, step0):
    for i, s in enumerate(range(20624, 20632)):
        _read(tmp_path, s, 0.385 + 0.001 * i)
    rc, rep = _run(tmp_path, step0)
    assert rc == 0 and rep["verdict"] == "PASS"
    assert rep["df"] == 7


def test_a_WIDE_spread_FAILS_and_the_run_stops(tmp_path, step0):
    """⛔⛔ THE BRANCH THAT SAVES THREE ADAPTERS. It must be reachable, and it
    must return a non-zero rc so the pipeline halts rather than proceeding to
    a table that cannot separate its cells."""
    for i, s in enumerate(range(20624, 20632)):
        _read(tmp_path, s, 0.20 + 0.06 * i)
    rc, rep = _run(tmp_path, step0)
    assert rc == 2 and rep["verdict"] == "FAIL"
    assert rep["two_sd_points"] > rep["floors_boundary_points"]


def test_a_MARKED_read_is_excluded_not_pooled(tmp_path, step0):
    """⛔⛔ Step P is the UNMARKED arm. A marked read pooled in here would
    measure the marker's spread and call it C0's noise — calibrating the gate
    on the very treatment it exists to protect."""
    for s in range(20624, 20632):
        _read(tmp_path, s, 0.385)
    _read(tmp_path, 99999, 0.20, marker_fn="act2_idf2.marker_held")
    rc, rep = _run(tmp_path, step0)
    assert rep["n"] == 8
    assert len(rep["excluded"]) == 1
    assert "marker_fn" in rep["excluded"][0]["why"]


def test_a_GREEDY_read_is_excluded(tmp_path, step0):
    for s in range(20624, 20632):
        _read(tmp_path, s, 0.385)
    _read(tmp_path, 99998, 0.20, temperature=0.0, decoder_sampled=False)
    rc, rep = _run(tmp_path, step0)
    assert rep["n"] == 8 and len(rep["excluded"]) == 1


def test_the_denominator_is_the_corpus_not_the_oracle(step0):
    """⛔ §6's formula is locked. The 0b oracle agrees with the corpus to
    0.0008 — that agreement is the red-proof, not a licence to swap them."""
    import act2_idf2_power as P
    assert P.closes(0.0224, blind=0.4456, corpus=0.0224) == pytest.approx(100.0)
    assert P.closes(0.4456, blind=0.4456, corpus=0.0224) == pytest.approx(0.0)


def test_the_boundaries_are_not_redefined_here():
    """⭐ 15 and 35 are IDF-1b's, in IDF-1b's role. If they move it is a
    re-lock, not an edit to a helper."""
    import act2_idf2_power as P
    assert (P.FLOORS_POINTS, P.INSTALLS_POINTS) == (15.0, 35.0)
    assert P.TRIP_MULTIPLE == 2.0


def test_fewer_than_two_reads_refuses_rather_than_reporting_zero(tmp_path,
                                                                 step0):
    """⛔ An SD over one read is 0, which would PASS the gate vacuously —
    `x / (n or 1)` wearing a different hat."""
    _read(tmp_path, 20624, 0.385)
    import act2_idf2_power as P
    with pytest.raises(SystemExit):
        P.main(["--root", str(tmp_path), "--cell", "ct-s20624",
                "--step0", str(step0), "--out", str(tmp_path / "p.json")])
