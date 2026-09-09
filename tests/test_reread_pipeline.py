"""⛔⛔ THE RE-READ MUST NOT BE ABLE TO DESTROY WHAT IT READS.

Run 0's weights survived its crash because persist ran BEFORE the reads. The
object is on the hub and its verdict is not, so the cheap fix is to buy back
just the read. ⛔ But the obvious way to do that -- re-run `pipeline_fullft.sh`
at the same CELL -- re-trains and re-persists OVER the only copy of the object
whose verdict is missing, which would destroy the evidence in order to measure
it.

So the re-read script is guarded on the property that makes it safe: it has no
training leg, no `full-weight` persist, and no epoch-2 branch to fall into.
"""
from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from textguard import code_only, one_call                         # noqa: E402

SRC = (_ROOT / "tools" / "pipeline_fullft_read.sh").read_text(encoding="utf-8")
CODE = code_only(SRC)


def test_it_NEVER_persists_a_full_weight_object():
    """⛔⛔ THE LOAD-BEARING GUARD. One `full-weight --cell` here would overwrite
    the 17.42 GB object this script exists to preserve."""
    assert "full-weight" not in CODE, \
        "the re-read script must never persist a full-weight object"


def test_it_has_no_training_leg():
    """⛔ `act2_finetune.py` anywhere in this file means it can move weights."""
    assert "act2_finetune" not in CODE


def test_it_has_no_epoch_2_branch():
    """⛔ The epoch-2 fallthrough is what would have spent a second H100 epoch on
    an unscoreable run. There is nothing here to fall through TO, and that must
    stay true."""
    for banned in ("leg2", "epoch 2", "--epochs"):
        assert banned not in CODE, "re-read script gained %r" % banned


def test_the_watchdog_is_armed_before_anything_else():
    """⛔⛔ HARD RULE, NO EXCEPTION. A read is shorter than a train, which makes
    an unguarded stall cheaper, not acceptable."""
    wd = CODE.index("tlon_arm_watchdog")
    for later in ("act2_flocal", "act2_model_lag", "snapshot_download"):
        assert wd < CODE.index(later), \
            "%s runs before the watchdog is armed" % later


def test_the_watchdog_marker_is_the_SCRIPT_not_an_output_path():
    """⛔⛔ `is_the_job` matches the marker against argv[0]/argv[1] — the thing
    being EXECUTED — precisely so `tail -f x.log` is not mistaken for the job.
    A filename here makes the watchdog refuse to arm, and the pipeline then
    refuses to run unguarded. Correct, and caught only on a billing box."""
    call = one_call(CODE, "tlon_arm_watchdog")
    assert "pipeline_fullft_read.sh" in call
    assert ".json" not in call, "the marker must not be an output path"


def test_it_refuses_an_incomplete_object():
    """⛔ A read of whatever survived is not a read of this run."""
    assert "REFUSING: the persisted object is missing" in SRC
    for need in ("model.safetensors", "weight_delta.json", "config.json"):
        assert need in SRC


def test_the_corpus_is_sha_pinned_like_the_training_pipeline():
    """⛔ `vocab_coverage` builds the per-leaf prediction from THIS corpus under
    THIS tokenizer, so an unpinned corpus would silently change the gate."""
    assert "CORPUS SHA MISMATCH" in SRC
    assert one_call(CODE, "act2_build_multiturn.py")


def test_the_delta_read_is_the_one_persisted_WITH_the_object():
    """⭐ Not a locally recomputed delta — the lag profile and the precondition
    must be about the same weights."""
    assert "--delta $OUT/weight_delta.json" in CODE


def test_every_verdict_exit_code_is_handled_including_unscoreable():
    """⛔ Exit 5 must be NAMED here. A `*)` catch-all would file "nothing was
    measured" under "a STOP row", which is the collapse the whole fix exists to
    prevent."""
    case = CODE[CODE.index("case $EV in"):CODE.index("esac")]
    for code in ("0)", "3)", "4)", "5)", "*)"):
        assert code in case, "exit %s is unhandled" % code
    assert "UNSCOREABLE" in case


def test_it_does_NOT_certify_itself_with_a_CELL_verification():
    """⛔⛔ `tlon_gate_done` verifies CELLS, and `unpersisted()` reads THIS RUN'S
    OWN persist ledger — so a run that deliberately persists no cell can never
    satisfy it. The first version called it with $CELL on the theory that it
    would re-verify the object on the hub. It does not. That was asserted from
    the function's NAME rather than read from its body, and it refused after the
    verdict was already computed.

    ⭐ The library already anticipates this: the marker is factored out from the
    verification because the check varies and the marker's meaning must not.
    """
    assert "tlon_gate_done" not in CODE, \
        "a read-only run cannot satisfy a cell verification"
    assert "tlon_mark_done" in CODE
    assert "tlon_persist_run_files" in CODE


def test_it_verifies_its_READ_ARTIFACTS_before_marking_done():
    """⛔ `~/DONE` is a claim the output is safe, and the watchdog terminates
    within one poll of seeing it. So the marker must follow a real check of the
    thing this run actually produced."""
    assert CODE.index("step verify_reads") < CODE.index("tlon_mark_done"), \
        "the marker must come AFTER the verification"
    assert "REFUSING to mark done" in SRC
    # ⛔ Sliced out of the SAME string the offsets came from. The first version
    # indexed SRC with CODE's offsets — comments are stripped from one and not
    # the other, so the window landed hundreds of characters away.
    window = CODE[CODE.index("step verify_reads"):CODE.index("tlon_mark_done")]
    for art in ("_reread.json", "vocab_coverage.json",
                "pipeline_fullft_read.log"):
        assert art in window, "%s is not verified before ~/DONE" % art


def test_it_sources_the_shared_scaffolding_rather_than_respelling_it():
    """⭐ The failure handler, log rotation, watchdog arming and the ~/DONE gate
    are where both 2026-09-04 losses happened. They exist once."""
    assert "source" in CODE and "pipeline_lib.sh" in CODE
    assert "tlon_trap_init" in CODE
    # ⭐ `tlon_gate_done` is the CELL path and cannot apply here; the pieces it
    # composes are used directly instead, in the same order.
    assert "tlon_persist_run_files" in CODE
    assert "tlon_arm_watchdog" in CODE
    assert "tlon_mark_done" in CODE
