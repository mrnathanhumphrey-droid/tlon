"""⛔⛔ THE TWO-ARM PATH: a refusal nobody branches on is a printed opinion.

The epochs-lever arm is two runs that differ in ONE thing — repetition — and the
pipeline is where that stops being a design and becomes a command line. Every
guard below exists because the corresponding mistake has already been made here:

  * `$?` after a pipe is `tee`'s status and is ALWAYS 0. A 17-module suite once
    printed `ok` 17x while structurally unable to report a failure. The step
    match's rc=1 refusal reaches this pipeline THROUGH A PIPE.
  * "EPOCH_BUDGET" meant LEGS while the prereg declared EPOCHS. That disconnect
    already bought an epoch a locked prereg did not declare. Arm A runs FOUR
    epochs in ONE leg, so a budget compared against the leg count would fall
    through to leg 2 and spend eight.
  * The corpus path was hardcoded in both legs. Arm A must train on the DERIVED
    subsample, and a leg that quietly used the full corpus would report a repeat
    factor it never applied — the run would look right and be the control twice.
"""
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SH = ROOT / "tools" / "pipeline_fullft.sh"
SRC = SH.read_text(encoding="utf-8")


def _block(start, end):
    i = SRC.index(start)
    j = SRC.index(end, i)
    return SRC[i:j]


def _code_only(text):
    """⛔⛔ DROP THE COMMENTS BEFORE ASSERTING ON THE COMMANDS.

    A scan of raw source cannot tell a call from a sentence ABOUT a call — and
    this file learned that the embarrassing way: the moment the pipeline grew a
    comment explaining the `flush --cell` bug, the guard against `flush --cell`
    began failing on the explanation. Same class as `grep_a_rendering`: don't
    grep prose for values, read the artefact. Full-line shell comments only,
    which is what the pipeline's commentary is.
    """
    return "\n".join(ln for ln in text.splitlines()
                     if not ln.lstrip().startswith("#"))


#: The pipeline with its commentary removed — what actually RUNS.
CODE = _code_only(SRC)


# ── 1 · the refusal must HALT ──────────────────────────────────────────────

def test_the_step_match_refusal_is_read_from_PIPESTATUS_not_dollar_question():
    """⛔⛔ `$?` AFTER A PIPE IS `tee`'s. The step match prints through `tee -a`,
    so reading `$?` would see 0 on every refusal and train anyway — a confounded
    run fired past a guard that correctly refused."""
    blk = _block("step corpus_subsample", "step corpus_manifest")
    assert "PIPESTATUS[0]" in blk, (
        "the step match's exit code is not read from PIPESTATUS — through a "
        "pipe, `$?` is tee's status and the refusal would be invisible")
    assert not re.search(r"SM_RC=\$\?", blk)


def test_the_refusal_actually_exits_and_does_not_merely_print():
    """⛔⛔ `report≠gate`: six suites once SAW a failure, PRINTED it, exited 0."""
    blk = _block("step corpus_subsample", "step corpus_manifest")
    assert re.search(r'if \[ "\$SM_RC" -ne 0 \];', blk), \
        "nothing branches on the step match's exit code"
    tail = blk[blk.index("SM_RC"):]
    assert "exit 1" in tail, "the refusal branch does not halt the run"


def test_the_subsample_runs_AFTER_the_corpus_sha_is_verified():
    """⛔⛔ The whole point is that the row count comes from the corpus that was
    actually sha-verified. Deriving it before the pin would size the subsample
    off an unverified rebuild."""
    assert SRC.index("step corpus_pin") < SRC.index("step corpus_subsample")
    # ⛔ anchored on the COMPARISON, not on its message — a reworded echo is not
    # a moved guard, and a test that fails on prose is noise.
    pin = re.search(r'if \[ "\$GOT" != "\$CORPUS_SHA" \]', SRC)
    assert pin, "the corpus sha comparison has moved or been removed"
    assert pin.start() < SRC.index("step corpus_subsample")


# ── 2 · the arm's corpus reaches the trainer ───────────────────────────────

@pytest.mark.parametrize("leg", ["train_leg1", "train_leg2"])
def test_both_legs_train_on_CORPUS_DIR_not_the_hardcoded_full_corpus(leg):
    """⛔⛔ A leg that silently used the full corpus would run the CONTROL while
    reporting the repeat arm — the run would look right and be arm B twice."""
    i = SRC.index("step %s" % leg) if ("step %s" % leg) in SRC else None
    if i is None:                       # leg 2 lives inside a branch, not a step
        i = SRC.index("--delta-snapshot-in $SNAP")
        i = SRC.rindex("act2_finetune.py", 0, i)
    blk = SRC[i:i + 900]
    assert "--corpus $CORPUS_DIR" in blk, \
        "%s does not train on the arm's corpus" % leg
    assert "--corpus $ROOT/corpus_ct-s$SEED" not in blk, \
        "%s still hardcodes the full corpus" % leg


def test_CORPUS_DIR_defaults_to_the_full_corpus_when_no_repeat_is_set():
    """⭐ The ordinary one-arm pipeline must be unchanged. A default that pointed
    somewhere else would silently re-scope every standing run."""
    blk = _block("CORPUS_DIR=", "step corpus_manifest")
    assert blk.startswith("CORPUS_DIR=$ROOT/corpus_ct-s$SEED")


# ── 3 · ⛔⛔ epochs, not legs ───────────────────────────────────────────────

def test_the_budget_gate_compares_EPOCHS_SPENT_not_the_leg_count():
    """⛔⛔ THE DEFECT-3 COLLISION ONE LEVEL DOWN. `EPOCH_BUDGET -lt 2` reads the
    budget as a LEG count. Arm A declares EPOCH_BUDGET=4 and runs all four in ONE
    leg, so that test is false and leg 2 would spend four more."""
    assert '[ "$EPOCH_BUDGET" -lt 2 ]' not in SRC, (
        "the leg-2 gate still compares the budget against a LEG count; "
        "EPOCH_BUDGET=4 would fall through and spend eight epochs")
    assert "EPOCHS_SPENT + EPOCHS_PER_LEG )) -gt \"$EPOCH_BUDGET\"" in SRC


@pytest.mark.parametrize("spent,per_leg,budget,should_refuse", [
    (1, 1, 1, True),     # arm B: one epoch declared, one spent
    (4, 4, 4, True),     # arm A: four declared, four spent in one leg
    (1, 1, 2, False),    # the legacy two-epoch arm, unchanged
    (2, 1, 2, True),     # ...and it stops after the second
])
def test_the_gate_arithmetic_is_right_for_every_arm(spent, per_leg, budget,
                                                    should_refuse):
    """⭐ The shell condition, evaluated here rather than trusted. Both arms and
    the legacy default must land the way the prereg declares."""
    assert ((spent + per_leg) > budget) is should_refuse


def test_epochs_per_leg_reaches_BOTH_legs():
    """⛔ `--epochs 1` hardcoded in either leg makes EPOCHS_PER_LEG decorative."""
    assert SRC.count("--epochs $EPOCHS_PER_LEG") == 2
    assert "--accum $ACCUM --epochs 1 " not in SRC


def test_a_budget_that_cannot_be_spent_exactly_is_refused_up_front():
    """⛔ EPOCH_BUDGET=3 with EPOCHS_PER_LEG=2 can never be spent exactly; the
    run would stop at 2 while claiming 3, or overrun to 4."""
    assert "EPOCH_BUDGET % EPOCHS_PER_LEG" in SRC
    blk = SRC[SRC.index("EPOCH_BUDGET % EPOCHS_PER_LEG"):][:400]
    assert "exit 1" in blk


def test_EPOCHS_SPENT_is_advanced_after_leg_one_completes():
    """⛔ A counter that never moves makes the gate compare 0 forever."""
    assert "EPOCHS_SPENT=$(( EPOCHS_SPENT + EPOCHS_PER_LEG ))" in SRC
    assert SRC.index("step train_leg1") < SRC.index(
        "EPOCHS_SPENT=$(( EPOCHS_SPENT + EPOCHS_PER_LEG ))")


# ── 4 · the release read is opt-in and plumbed ─────────────────────────────

def test_the_lag_curve_flag_reaches_the_trainer():
    assert "${LAG_CURVE:+--lag-curve}" in SRC


def test_the_lag_curve_is_off_by_default():
    """⭐ Like the dose curve: a run that paid for reads nobody asked for would
    report a wall-clock and a cost no prereg declared."""
    assert "LAG_CURVE=${LAG_CURVE:-}" in SRC


def test_the_repeat_factor_is_off_by_default_so_standing_runs_are_unchanged():
    assert "REPEAT=${REPEAT:-}" in SRC


# ── 5 · ⛔⛔ PERSIST_WEIGHTS=0 — the readings become the SOLE record ─────────

def test_persist_weights_defaults_to_ON_so_standing_runs_are_unchanged():
    """⭐ Every prior run persisted its object. A default of 0 would silently
    stop keeping the deliverable of runs whose deliverable IS the weights."""
    assert "PERSIST_WEIGHTS=${PERSIST_WEIGHTS:-1}" in SRC


def test_the_capacity_floor_is_skipped_only_when_no_weights_are_written():
    """⛔ Asking for room for an object the run will never upload refuses a run
    that cannot fail the way that check exists to prevent — but the check must
    still run whenever weights ARE written."""
    i = SRC.index("act2_hub_capacity.py")
    head = SRC[:i]
    assert 'if [ "$PERSIST_WEIGHTS" = "1" ]; then' in head[-400:], \
        "the capacity floor is not gated on PERSIST_WEIGHTS"


@pytest.mark.parametrize("n", [1, 2, 3])
def test_every_persist_site_is_gated_and_falls_back_to_a_FLUSH(n):
    """⛔⛔ THE READINGS MUST STILL LEAVE. With weights unpersisted the readings
    are the only record; a persist site that simply did nothing would leave the
    whole run resting on the exit trap alone."""
    sites = [m.start() for m in re.finditer(r"full-weight --cell \$CELL", CODE)]
    assert len(sites) == 3, ("expected 3 persist sites (leg1, reads, leg2), found %d -- a NEW ungated site is the failure this counts for" % len(sites))
    blk = CODE[max(0, sites[n - 1] - 900): sites[n - 1] + 900]
    assert 'PERSIST_WEIGHTS' in blk, "persist site %d is not gated" % n
    # ⛔⛔ THIS ASSERTION USED TO READ `"flush --cell $CELL" in blk` — IT PINNED
    # THE BUG AS THE SPECIFICATION. `flush` takes no `--cell`; argparse exits 2;
    # on 2026-09-16 that killed `epochlevB-s20624` after 3,760 clean training
    # steps and cost the run every end-of-run read. The test could never have
    # caught it, because the test REQUIRED it: a guard written by copying the
    # call it was guarding, which then certified the copy forever.
    #
    # ⭐ So the check is no longer "does this string appear" but "is this call
    # one the tool would ACCEPT" — asserted against the real argparse below, in
    # test_every_flush_invocation_is_one_argparse_ACCEPTS.
    assert re.search(r"\bflush\b(?!\s+--cell)", blk), (
        "persist site %d has no flush fallback — the readings would not leave "
        "on the success path" % n)
    assert "flush --cell" not in blk, (
        "persist site %d passes --cell to `flush`, which does not accept it: "
        "argparse exits 2 and takes the run's reads with it" % n)


def test_every_flush_invocation_is_one_argparse_ACCEPTS():
    """⭐⭐ THE GENERALISATION, AND THE ONE THAT ACTUALLY CLOSES THE CLASS.

    ⛔⛔ Checking that a call site contains the right SUBSTRING is checking a
    copy against a copy. On 2026-09-16 three sites in this pipeline spelled
    `act2_box_persist.py ... flush --cell $CELL`, the test above asserted that
    exact string, and `flush` has never accepted `--cell`. argparse exited 2,
    `pipefail` carried it through `tee`, `set -e` aborted, and a run with 3,760
    clean training steps produced no F-LOCAL, no lag profile, no dose check and
    no verdict. The guard was a photocopy of the bug.

    ⭐ So every invocation in the pipeline is tokenised and fed to the REAL
    parser. A call the tool would reject fails here, in CI, in milliseconds —
    instead of eleven hours into an H100 run.
    """
    import contextlib
    import io as _io
    import shlex
    import sys as _sys
    _sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
    import act2_box_persist as BP

    # Join the shell's backslash continuations, then find each invocation.
    joined = re.sub(r"\\s*\n\s*", " ", CODE)
    calls = re.findall(r"act2_box_persist\.py\s+([^\n|]*)", joined)
    assert calls, "no act2_box_persist.py invocations found — this test is vacuous"

    checked = 0
    for raw in calls:
        # ⛔ Drop the shell's redirections; keep every argument.
        raw = re.sub(r"2>&1.*$", "", raw).strip()
        if not raw:
            continue
        # Substitute shell variables with a placeholder — the SHAPE of the call
        # is what argparse judges, not the values.
        argv = [re.sub(r"\$\{?\w+\}?", "X", tok) for tok in shlex.split(raw)]
        if not argv:
            continue
        err = _io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                BP.build_parser().parse_args(argv)
        except SystemExit as e:
            raise AssertionError(
                "pipeline_fullft.sh calls act2_box_persist.py with arguments "
                "the tool REFUSES (exit %s):\n    %s\n  argparse said: %s"
                % (e.code, " ".join(argv), err.getvalue().strip().splitlines()[-1]
                   if err.getvalue().strip() else "(nothing)"))
        checked += 1
    assert checked >= 4, (
        "only %d invocation(s) were checked; the pipeline has a persist site "
        "per leg plus the trap, so a smaller number means the scan is missing "
        "call sites and passing on the ones it found" % checked)


def test_the_readings_audit_is_actually_CALLED_by_the_pipeline():
    """⛔⛔ A GATE NOBODY CALLS IS A PRINTED OPINION. `act2_audit_readings.py` is
    the structural fix for the four bugs of 2026-09-16 — and a fix that exists
    in `tools/` and is never invoked is the `cold_pin` failure: a check that
    reports instead of acting, which reads as a passing guard.

    ⛔ It must also run AFTER the readings exist. An audit placed before
    `persist_reads` would find the verdict and the lag file missing on every
    run and be trained-away as noise within a week.
    """
    assert "act2_audit_readings.py" in CODE, (
        "the pipeline never invokes the readings audit — it is a tool nobody "
        "runs, which is worth less than no tool at all")
    assert CODE.index("step persist_reads") < CODE.index("act2_audit_readings.py"), (
        "the readings audit runs BEFORE the readings are persisted; it would "
        "fail on every healthy run and stop being read")
