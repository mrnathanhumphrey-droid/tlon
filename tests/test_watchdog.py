"""⛔⛔ THE ON-INSTANCE WATCHDOG — RED-PROOFED BEFORE IT IS EVER ARMED.

`PREREG_POSITIVE_CONTROL_KA` `c0de41c7` §8.2.

⛔⛔ WHY THIS IS CODE AND NOT A SHELL SNIPPET ON THE BOX. The drift run had only
a laptop-side poll, which is a PROGRESS monitor and cannot be a SAFETY watchdog:
if the SSH connection drops, a poll goes permanently silent, and silence is
indistinguishable from health. The box idled ~25 minutes after that run. A
watchdog that lives on the instance and terminates the instance is the only
arrangement in which the failure of the watchdog is not itself a silent cost.

⛔⛔ AND THE REGRESSION THIS FILE EXISTS TO MAKE IMPOSSIBLE. A pattern search over
the process table matches the WATCHDOG'S OWN COMMAND LINE — the pattern is in the
argv of the process doing the searching — so "is the job still alive?" answers YES
forever and the process-died branch is unreachable. That fix was learned on
2026-08-10, lived in memory instead of in code, and came back. It is now a test.

⭐ THE DISCIPLINE: every branch that can terminate a box must be shown to FIRE on
a fabricated version of the condition it watches for, and to STAY SILENT on a
healthy run. A watchdog that has never fired in testing is a watchdog whose kill
path is unexecuted code.
"""
from __future__ import annotations

import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

from act2_watchdog import (ARM_REFUSED, DONE, KILL, WAIT,  # noqa: E402
                           Observation, act, arm, decide)

MARKER = "pipeline_positive_control.sh"
DEADLINE = 40 * 3600.0      # 36 GPU-h prereg ceiling + slack
STALL = 90 * 60.0           # 90 min without log growth


def obs(**kw):
    """A HEALTHY observation. Each test perturbs exactly one field, so a test
    that fires proves the field it changed is what fired it."""
    base = dict(now=1000.0, started=0.0, pid=4242,
                cmdline="/bin/bash %s --pairs 7" % MARKER,
                log_bytes=5000, log_last_change=900.0, done_marker=False)
    base.update(kw)
    return Observation(**base)


def verdict(o):
    return decide(o, marker=MARKER, deadline_s=DEADLINE, stall_s=STALL)[0]


# ── 1 · the healthy run must be left alone ──────────────────────────────────

def test_a_healthy_run_is_NOT_killed():
    """⛔ The first thing to prove about a kill switch is that it does not fire
    on the normal case — otherwise every later "it fired" is meaningless."""
    assert verdict(obs()) == WAIT


def test_a_long_but_progressing_run_is_not_killed():
    """35 h in, still writing. Long is not the same as stuck."""
    assert verdict(obs(now=35 * 3600.0, log_last_change=35 * 3600.0 - 60)) == WAIT


# ── 2 · every kill branch must FIRE on a fabricated version of its condition ─

def test_FIRES_on_a_fabricated_runaway_past_the_deadline():
    """The canonical runaway: alive, correct process, simply never ending."""
    assert verdict(obs(now=DEADLINE + 1.0, log_last_change=DEADLINE)) == KILL


def test_FIRES_when_the_process_is_GONE_without_the_completion_marker():
    """⛔ Died mid-run. The box would otherwise bill forever on an idle GPU —
    this is the branch a pattern search made unreachable."""
    assert verdict(obs(cmdline=None)) == KILL


def test_FIRES_on_a_STALLED_log():
    """Alive, inside the deadline, writing nothing. A hung backend looks exactly
    like a healthy one to a pure liveness check."""
    assert verdict(obs(now=10000.0, log_last_change=10000.0 - STALL - 1)) == KILL


def test_FIRES_when_the_PID_HAS_BEEN_REUSED_by_another_process():
    """⛔ A PID outliving its process and being reassigned turns "my job is
    alive" into "some job is alive". Identity is PID **and** cmdline."""
    assert verdict(obs(cmdline="/usr/bin/python3 -m http.server")) == KILL


# ── 3 · ⛔⛔ THE SELF-MATCH, MADE INTO A TEST ────────────────────────────────

def test_the_watchdog_does_NOT_accept_its_OWN_cmdline_as_the_job():
    """⛔⛔ THE 2026-08-10 REGRESSION. A pattern search for the pipeline name
    matches the watchdog's own argv, because the pattern is IN that argv. The job
    then appears immortal and the died-branch never runs.

    Identity here is the PID handed at arm time plus the cmdline read from that
    exact PID — never a pattern search over the process table.
    """
    watchdog_argv = "/usr/bin/python3 tools/act2_watchdog.py --marker %s" % MARKER
    assert MARKER in watchdog_argv          # the pattern IS present ...
    assert verdict(obs(cmdline=watchdog_argv)) == KILL   # ... and still refused


def test_identity_requires_the_marker_to_be_the_SCRIPT_not_merely_present():
    """A cmdline that merely mentions the marker (an editor, a tail, a grep) is
    not the job. Substring presence is exactly what made the old check wrong."""
    for impostor in ("tail -f %s.log" % MARKER,
                     "grep -n foo %s" % MARKER,
                     "vim %s" % MARKER):
        assert verdict(obs(cmdline=impostor)) == KILL, impostor


# ── 4 · completion still terminates the box ─────────────────────────────────

def test_COMPLETION_terminates_too_because_finishing_work_is_not_finishing_billing():
    """⛔⛔ A SUCCESSFUL RUN THAT LEAVES THE BOX UP IS STILL A LOSS. The previous
    run idled ~25 min after finishing. DONE is a terminate verdict, not a
    stand-down."""
    assert verdict(obs(done_marker=True, cmdline=None)) == DONE


def test_completion_wins_over_the_deadline():
    """If the run finished, the recorded reason must be "finished", not
    "runaway" — that string is the whole postmortem."""
    o = obs(done_marker=True, now=DEADLINE + 5000)
    action, reason = decide(o, marker=MARKER, deadline_s=DEADLINE, stall_s=STALL)
    assert action == DONE and "complet" in reason.lower()


def test_every_kill_carries_a_DISTINCT_reason():
    """The reason string is the only postmortem available once the box is gone."""
    cases = [obs(now=DEADLINE + 1, log_last_change=DEADLINE),
             obs(cmdline=None),
             obs(now=10000.0, log_last_change=10000.0 - STALL - 1),
             obs(cmdline="/usr/bin/python3 -m http.server")]
    reasons = [decide(c, marker=MARKER, deadline_s=DEADLINE,
                      stall_s=STALL)[1] for c in cases]
    assert len(set(reasons)) == 4, reasons


# ── 5 · arming refuses rather than watching nothing ─────────────────────────

def test_arm_REFUSES_a_pid_that_does_not_exist():
    """⛔ Arming against a dead PID gives a watchdog that watches nothing and
    reports healthy forever."""
    ok, why = arm(pid=999999, marker=MARKER, cmdline_reader=lambda _p: None)
    assert ok is ARM_REFUSED and "not running" in why


def test_arm_REFUSES_when_the_cmdline_does_not_match_the_marker():
    ok, why = arm(pid=4242, marker=MARKER,
                  cmdline_reader=lambda _p: "/usr/bin/python3 -m http.server")
    assert ok is ARM_REFUSED and "does not look like" in why


def test_arm_ACCEPTS_the_real_job():
    ok, _why = arm(pid=4242, marker=MARKER,
                   cmdline_reader=lambda _p: "/bin/bash %s --pairs 7" % MARKER)
    assert ok is True


def test_arm_REFUSES_ITS_OWN_PID():
    """⛔⛔ The self-match at arm time. A watchdog handed its own PID would watch
    itself, find itself healthy forever, and terminate nothing."""
    ok, why = arm(pid=os.getpid(), marker=MARKER,
                  cmdline_reader=lambda _p: "python tools/act2_watchdog.py")
    assert ok is ARM_REFUSED and "own" in why.lower()


# ── 6 · the terminate path is EXECUTED, not merely returned ─────────────────

def test_the_terminate_action_actually_invokes_the_terminator():
    """⛔⛔ A VERDICT IS NOT A SHUTDOWN. Returning KILL and never calling the
    terminator is precisely the `cold_pin` failure — a check that reports instead
    of acting. This asserts the side effect."""
    called = []
    act(KILL, "fabricated runaway", terminator=called.append)
    assert called == ["fabricated runaway"]


def test_WAIT_does_NOT_invoke_the_terminator():
    called = []
    act(WAIT, "healthy", terminator=called.append)
    assert called == []


def test_DONE_invokes_the_terminator_as_well():
    called = []
    act(DONE, "run complete", terminator=called.append)
    assert called == ["run complete"]


def test_a_terminator_that_raises_does_not_leave_the_loop_alive():
    """⛔ If the terminate call fails, the watchdog must not swallow it and keep
    polling a box nobody is watching. Loudly, or not at all."""
    def boom(_why):
        raise RuntimeError("terminate api 500")
    with pytest.raises(RuntimeError):
        act(KILL, "runaway", terminator=boom)
