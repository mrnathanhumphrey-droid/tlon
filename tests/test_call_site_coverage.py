"""⛔⛔ CORRECT AT THE DEFINITION, PARTIAL AT THE WIRING.

WHY THIS EXISTS, AS THREE DEFECTS WITH ONE CAUSE. On 2026-09-13/14 three things
went wrong in one run, and every one of them was a fix applied to ONE of TWO
call sites:

  1. `--mapping` was wired into `verdict_epoch1` and not `verdict_epoch2`, so
     epoch 2 fell back to the pooled §4.1 test that is invalid for mapping scope
     and reported a FALSE `INSTRUMENT FAULT`.
  2. `persist_reads` was placed after `verdict_epoch1` only, so the epoch-2
     failure path exited without it and the dose curve never reached the hub.
  3. The §4.1 fix changed `decide()`'s OUTPUT, which unblocked the epoch-2
     branch that reads its exit code — a downstream effect nobody traced.

⭐⭐ AND THE EXISTING TESTS COULD NOT HAVE CAUGHT ANY OF THEM. They exercise
`decide()`, `mapping_moved`, `isolated_read` — the DEFINITIONS. A function can
be correct at every one of its definitions and still be wired into half the
places it is needed, and no amount of unit testing the function sees that.

⛔ So these tests enumerate the CALL SITES and assert coverage across all of
them. The shape is: find every invocation of X in the pipeline, assert the
required flag appears at each. A new call site added without the flag fails
here, which is the only place it can fail before it costs a run.
"""
import pathlib
import re

PIPE = (pathlib.Path(__file__).resolve().parents[1] / "tools"
        / "pipeline_fullft.sh")
SRC = PIPE.read_text(encoding="utf-8")


def invocations(tool: str) -> list[str]:
    """Every invocation of `tool` in the pipeline, as its full continued line.

    ⛔ Backslash-continued, so a naive line match sees only the first line and
    would report every call site as missing every flag.
    """
    joined = SRC.replace("\\\n", " ")
    return [ln for ln in joined.splitlines() if tool in ln
            and not ln.strip().startswith("#")]


# ── defect 1: the flag that reached one of two verdicts ────────────────────

def test_every_verdict_call_site_passes_the_mapping_record():
    """⛔⛔ THE ONE THAT COST A FALSE INSTRUMENT FAULT. The pooled §4.1 test is
    invalid for mapping scope; the per-leaf record is what carries the
    precondition. A verdict call without it silently reverts to the invalid
    test."""
    sites = invocations("act2_fullft_verdict.py")
    assert len(sites) >= 2, "expected a verdict per epoch, found %d" % len(sites)
    missing = [s for s in sites if "--mapping" not in s]
    assert not missing, (
        "%d of %d verdict call sites do not pass --mapping:\n%s"
        % (len(missing), len(sites), "\n".join(m.strip()[:120] for m in missing)))


def test_every_verdict_call_site_names_its_prereg():
    """⛔ A verdict that cannot name its pre-registration is the defect that
    shipped rung 1b's artifact stamped with the wrong lock id."""
    sites = invocations("act2_fullft_verdict.py")
    assert all("--prereg" in s for s in sites)


def test_every_verdict_call_site_reads_the_matching_epoch_lag():
    """⛔ An epoch-2 verdict against the epoch-1 lag profile would read stale
    numbers under a fresh label — and both files exist, so nothing would fail."""
    for s in invocations("act2_fullft_verdict.py"):
        m = re.search(r"verdict_\$\{CELL\}_e(\d)\.json", s)
        assert m, s[:120]
        assert "_e%s.json" % m.group(1) in s.split("--lag")[1].split()[0], (
            "verdict for epoch %s does not read the epoch-%s lag" % (m.group(1),
                                                                     m.group(1)))


# ── defect 2: the measurement that left on one of many exit paths ──────────

def test_the_measurement_flush_is_a_trap_not_a_step():
    """⛔⛤ EVERY `exit` IS A PLACE SOMEONE MUST REMEMBER TO PERSIST FIRST, and
    the remembering failed on the first two branches exercised. A trap cannot be
    forgotten by a branch."""
    assert "trap _flush_measurement EXIT" in SRC


def test_the_trap_is_armed_before_the_first_reading_is_written():
    """⛔ The dose curve writes readings DURING train_leg1, so arming after
    training returns would miss exactly the run that lost its curve."""
    # ⛔ ANCHOR ON THE TRAINING LEG, NOT THE FIRST MENTION OF THE TOOL. The
    # first `act2_finetune.py` in the file is the `--probe-optim` PREFLIGHT,
    # which produces no readings — arming before it would flush an empty
    # directory on every preflight refusal. The first draft of this test
    # anchored there and failed against correct code.
    arm = SRC.index("MEASUREMENT_EXISTS=1")
    train = SRC.index("step train_leg1")
    assert arm < train, "the trap arms after the training leg starts"
    # and the curve writes during that leg, so arming must also precede the
    # dose-curve flags being passed
    assert arm < SRC.index("--dose-curve-out")


def test_the_trap_preserves_the_exit_code():
    """⛔ A trap that swallowed the failure would turn every instrument fault
    into a success and let `~/DONE` be written for a run that produced none."""
    body = SRC[SRC.index("_flush_measurement() {"):SRC.index("trap _flush")]
    assert "local rc=$?" in body
    assert "return $rc" in body


def test_the_trap_flushes_rather_than_re_persisting_the_model():
    """⛔ `full-weight` would re-upload 14.5 GB on every exit, including on a box
    already being terminated for cost. The readings are kilobytes."""
    body = SRC[SRC.index("_flush_measurement() {"):SRC.index("trap _flush")]
    assert " flush " in body
    assert "full-weight" not in body


def test_the_trap_cannot_abort_the_exit():
    """⛔ A flush that raised while the script was leaving would strand a
    billing box — a bounded failure becoming an unbounded bill."""
    body = SRC[SRC.index("_flush_measurement() {"):SRC.index("trap _flush")]
    assert "||" in body, "the flush is not best-effort"


# ── the general shape: a halt branch must never be the only persist ────────

def test_no_exit_branch_relies_on_having_persisted_first():
    """⭐ THE GENERAL FORM OF DEFECT 2. With the trap in place this is
    structural, so the assertion is simply that the trap exists and every exit
    is inside its scope — i.e. no `exit` appears before the trap is installed."""
    trap_at = SRC.index("trap _flush_measurement EXIT")
    early = [m.start() for m in re.finditer(r"^\s*exit \d", SRC, re.M)
             if m.start() < trap_at]
    assert not early, ("%d exit(s) occur before the flush trap is installed"
                       % len(early))


# ── defect 3: the declared epoch count that was not binding ────────────────

def test_the_leg_two_branch_is_gated_on_the_declared_epoch_budget():
    """⛔⛔ PREREG ac255dce §2 declared "epochs: 1, run to completion" AND THE
    RUN SPENT TWO. `--epochs 1` is passed to each LEG while the number of LEGS
    was decided from a verdict exit code, so the declared count and the executed
    one were never connected — a §4.1 change altered the exit code and the run
    quietly bought an epoch nobody registered.

    ⛔ This is not a claim that the extra epoch was harmful. On that run it moved
    every axis the good way. It is a claim that a run executes the experiment its
    locked prereg describes and buys nothing else."""
    assert "EPOCH_BUDGET" in SRC
    # the gate now compares EPOCHS SPENT against the budget, not the LEG count:
    # arm A of the epochs lever runs four epochs in ONE leg, so `-lt 2` was the
    # same disconnect one level down. Anchored on EPOCH_BUDGET appearing in the
    # elif, not on one spelling of the comparison.
    m = re.search(r'elif \[ .*EPOCH_BUDGET.*\]; then', SRC)
    assert m, "the leg-2 branch is no longer gated on the declared budget"
    i = m.start()
    j = SRC.index("step train_leg2")
    assert i < j, "the budget gate does not precede the second training leg"


def test_the_budget_defaults_to_two_so_no_standing_prereg_changes():
    """⭐ Every prereg before ac255dce was written against a two-epoch pipeline.
    A default of 1 would silently re-scope all of them."""
    m = re.search(r"EPOCH_BUDGET=\$\{EPOCH_BUDGET:-(\d+)\}", SRC)
    assert m and m.group(1) == "2"


def test_a_refused_second_epoch_still_names_a_final_verdict():
    """⛔ The `~/DONE` gate reads FINAL_LAG and FINAL_VERDICT. A branch that
    halts without setting them would fail at the gate instead of at the halt,
    which reads as a different fault than the one that occurred."""
    m = re.search(r'elif \[ .*EPOCH_BUDGET.*\]; then', SRC)
    assert m, "the leg-2 budget branch has moved or been removed"
    body = SRC[m.start():SRC.index("step train_leg2")]
    assert "EPOCHS_RUN=1" in body
    assert "FINAL_LAG=" in body and "FINAL_VERDICT=" in body
