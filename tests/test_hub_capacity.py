"""THE PERSIST-CAPACITY FLOOR — red-proofed in both directions.

⛔⛔ THE LOSS THIS PINS. Rung 1b' trained 3,760 clean steps on a rented H100 and
died at `persist_leg1` on "Private repository storage limit reached". The run's
actual measurement never executed. A check had already passed -- a tiny probe
file written to the hub, reported as "persist path verified writable" -- and it
was true and it was about the PATH while the run depended on the CAPACITY.

⭐ So the test is not "does the function return a bool". It is: does this refuse
the exact situation that was paid for, and admit the situation that works.
"""
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tlon.act2.hub_capacity import (FITS, NO_ROOM,  # noqa: E402
                                    OBSERVED_REFUSED_BYTES,
                                    PROVEN_ACCEPTED_BYTES, check,
                                    projected_artifact_bytes,
                                    used_storage_bytes)

PIPE = (ROOT / "tools" / "pipeline_fullft.sh").read_text(encoding="utf-8")

#: The real scope of the run that was lost.
N_TRAIN, N_FROZEN = 4_428_098_048, 3_187_518_464
#: What the hub actually received for that same scope, all files.
RUNG_1B_UPLOADED = 24_098_988_333


class _Info:
    def __init__(self, used):
        self.used_storage = used


class _Api:
    def __init__(self, used):
        self._used = used

    def model_info(self, repo, expand=None):
        return _Info(self._used)


class _ApiNoField:
    def model_info(self, repo, expand=None):
        return _Info(None)


# ── the projection ─────────────────────────────────────────────────────────

def test_the_projection_covers_what_the_hub_actually_received():
    """⭐ CALIBRATION, against a real upload rather than an imagined one. The
    projection must be >= the bytes rung 1b really sent, or the floor passes a
    run whose artifacts do not fit."""
    p = projected_artifact_bytes(N_TRAIN, N_FROZEN)
    assert p >= RUNG_1B_UPLOADED, (p, RUNG_1B_UPLOADED)
    # ⛔ ...and not absurdly over, or the floor becomes a nuisance that gets
    # switched off. Within 2% of truth.
    assert p <= RUNG_1B_UPLOADED * 1.02, (p, RUNG_1B_UPLOADED)


def test_the_fp32_master_is_not_optional():
    """⛔⛔ §5 declares an fp32 master over the trainable parameters. Projecting
    the whole model at bf16 -- the obvious `params * 2` -- under-counts a
    full-weight run badly enough to pass it into the wall."""
    honest = projected_artifact_bytes(N_TRAIN, N_FROZEN)
    naive = projected_artifact_bytes(N_TRAIN, N_FROZEN, master_bytes=2)
    assert naive < honest
    assert naive < RUNG_1B_UPLOADED, (
        "the bf16-everywhere projection must be demonstrably WRONG for this "
        "run, otherwise this test is not pinning anything")
    assert honest / naive > 1.5


def test_a_lora_sized_run_projects_small():
    """⭐ The floor must not block the LoRA arm, whose adapters are ~0.32 GB."""
    assert projected_artifact_bytes(80_000_000, 0) < 1e9


# ── the decision, red-proofed on the real numbers ──────────────────────────

def test_it_REFUSES_the_exact_run_that_was_lost():
    """⛔⛔ THE RED PROOF. 94.21 GB was in the repo; this run needed 24.1 GB.
    That commit was refused by the hub at hour two. The floor must refuse it at
    minute zero."""
    used = PROVEN_ACCEPTED_BYTES
    projected = projected_artifact_bytes(N_TRAIN, N_FROZEN)
    verdict, why = check(used, projected)
    assert verdict == NO_ROOM, why
    assert "NO ROOM" in why


def test_it_ADMITS_the_same_run_once_the_space_exists():
    """⭐ The other direction, and it is the one that makes the floor useful
    rather than merely obstructive: with the dead history reclaimed (50.72 GB
    of live files), the identical run fits and must be allowed to start."""
    used = 50_720_000_000
    projected = projected_artifact_bytes(N_TRAIN, N_FROZEN)
    verdict, why = check(used, projected)
    assert verdict == FITS, why


def test_the_boundary_is_inclusive_and_one_byte_over_refuses():
    projected = 1_000_000_000
    assert check(PROVEN_ACCEPTED_BYTES - projected, projected)[0] == FITS
    assert check(PROVEN_ACCEPTED_BYTES - projected + 1, projected)[0] == NO_ROOM


def test_the_ceiling_sits_inside_the_measured_bracket():
    """⛔ Both ends are OBSERVATIONS: this much was held, that much was
    refused. The guard must use the LOW end, so it stays correct for any true
    limit inside the bracket instead of depending on a number picked within
    it."""
    assert PROVEN_ACCEPTED_BYTES < OBSERVED_REFUSED_BYTES
    assert OBSERVED_REFUSED_BYTES - PROVEN_ACCEPTED_BYTES >= RUNG_1B_UPLOADED


# ── the two ways this guard could go vacuous ───────────────────────────────

def test_a_missing_quota_field_RAISES_and_never_reads_as_empty():
    """⛔⛔ `or 0` here would report an empty repo and pass EVERY run, precisely
    when the check has gone blind. A failed fetch records MISSING, never 0."""
    with pytest.raises(RuntimeError, match="REFUSING to guess"):
        used_storage_bytes("any/repo", api=_ApiNoField())


def test_used_storage_is_read_from_the_quota_field_not_summed_from_files():
    """⛔⛔ THE SUM OF THE LIVE FILES IS THE WRONG NUMBER. This repo's current
    files total 50.72 GB and it is charged 94.21 GB -- 43.49 GB of superseded
    LFS blobs are still billed. Summing `siblings`, the obvious
    implementation, under-reports by 46% and admits a run that cannot
    persist.

    ⚠️ Pinned on the ATTRIBUTE ACCESS, not the word. The first form asserted
    the string "siblings" was absent from the file and failed on this test's
    own rationale for why summing it is wrong -- the second time in one session
    a whole-file text guard matched the prose explaining the bug instead of the
    bug. Narrowed to what the code would actually have to do."""
    src = (ROOT / "tlon" / "act2" / "hub_capacity.py").read_text(encoding="utf-8")
    assert ".siblings" not in src, (
        "used storage must come from usedStorage, not from summing live files")
    assert used_storage_bytes("any/repo", api=_Api(94_214_989_055)) == 94_214_989_055


# ── the wiring ─────────────────────────────────────────────────────────────

def _floor_call() -> str:
    """The capacity floor's FULL shell invocation, continuations joined.

    ⛔ Written once because getting it wrong is silent. A regex like
    `[^\\n]*cmd[^\\n]*(?:\\\\\\n[^\\n]*)*` never matches the continuation --
    the greedy class consumes the backslash -- so every assertion downstream
    runs against the first line only and passes on a fragment.
    """
    from textguard import one_call
    return one_call(PIPE, "act2_hub_capacity.py")

def test_the_floor_runs_BEFORE_training_and_after_the_watchdog():
    """⛔ Before `train_leg1`, or it is not a floor -- it is a postmortem. After
    the watchdog, so a refusal cannot strand a live box."""
    assert re.search(r"^step hub_capacity", PIPE, re.M), (
        "the capacity check must be its own logged step")
    assert PIPE.index("tlon_arm_watchdog") < PIPE.index("step hub_capacity")
    assert PIPE.index("step hub_capacity") < PIPE.index("step train_leg1")


def test_the_floor_is_passed_the_runs_REAL_scope():
    """⛔ A floor sized on the wrong scope is decoration. The trainable count
    must be the pipeline's own variable, not a literal that drifts from it."""
    m = re.search(r"act2_hub_capacity\.py[^\n]*\n(?:[^\n]*\n){0,4}", PIPE)
    assert m, "the capacity tool is never invoked"
    call = m.group(0)
    assert "$HF_REPO" in call
    # ⛔ THE PIPELINE'S OWN SCOPE VARIABLES, not typed-in integer counts. A
    # literal here would survive a change to UNFREEZE_TOP and silently size the
    # floor for a run that no longer exists.
    assert "$TRAINABLE_B" in call and "$TOTAL_B" in call, call
    assert not re.search(r"--\S*trainable\S*\s+\d{6,}", call), (
        "the scope is hardcoded as an integer and will drift from UNFREEZE_TOP")
    assert re.search(r"^TOTAL_B=", PIPE, re.M)


def test_a_refusal_actually_stops_the_pipeline():
    """⛔⛔ The whole point. `set -e` is on, so an un-swallowed non-zero exit
    halts -- this pins that the call is NOT wrapped in `|| true` or a captured
    exit code the way the verdict step deliberately is."""
    call = _floor_call()
    assert "|| true" not in call and "||" not in call.replace("2>&1", "")
    # ⛔ The call must actually be the whole invocation. An earlier form of this
    # test matched `[^\n]*...(?:\\\n[^\n]*)*`, where the greedy class eats the
    # continuation backslash -- so it silently tested a TRUNCATED fragment and
    # would have passed with `|| true` sitting on the second line.
    assert call.rstrip().endswith("tee -a $LOG"), call


def test_the_floor_depends_on_pipefail_being_set():
    """⛔⛔ THE FLOOR IS PIPED INTO `tee`, SO ITS EXIT CODE ONLY SURVIVES UNDER
    `pipefail`. Without it the shell reports `tee`'s status -- always 0 -- and a
    NO_ROOM refusal becomes a line in the log that the run scrolls straight
    past, which is indistinguishable from having no floor at all.

    ⭐ Verified live: the tool exits 1, and `set -o pipefail` + `tee` still
    exits 1. This pins the shell option that makes that true."""
    assert re.search(r"^set -\w*o\w* pipefail|^set -o pipefail|^set -uo pipefail",
                     PIPE, re.M), "pipefail is not set; piped floors cannot fail"
    assert "tee -a $LOG" in _floor_call(), (
        "if the floor stops being piped this test's premise changed — re-check "
        "that its exit code still reaches `set -e`")
