"""⛔⛔ THE ON-INSTANCE, SELF-TERMINATING WATCHDOG.

`PREREG_POSITIVE_CONTROL_KA` `c0de41c7` §8.2 · red-proof `tests/test_watchdog.py`,
written BEFORE this module.

    python tools/act2_watchdog.py --pid <PID> --log <FILE> --done <FILE> \
        --marker pipeline_positive_control.sh

⛔⛔ A LAPTOP-SIDE POLL IS NOT A WATCHDOG. It is a progress monitor. If the SSH
connection drops it goes permanently silent, and silence is indistinguishable
from health — so the failure of the monitor is itself an unbounded cost. The
previous run's box idled ~25 minutes after finishing for exactly this reason.
This runs ON the instance and terminates THE INSTANCE.

⛔⛔ IDENTITY IS `PID` + `/proc/<pid>/cmdline`, NEVER A PATTERN SEARCH. A search
over the process table for the pipeline's name matches the WATCHDOG'S OWN ARGV —
the pattern is in the argv of the process doing the searching — so the job looks
immortal and the died-branch is unreachable. Learned 2026-08-10, recorded only in
prose, and it came back. It is a test now (`test_the_watchdog_does_NOT_accept_...`).

⭐ Every terminating branch is red-proofed to FIRE on a fabricated version of its
condition and to stay silent on a healthy run. A kill path never exercised in
testing is unexecuted code holding a credit card.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys
import time
from dataclasses import dataclass

#: ⛔⛔ Cloudflare 403s `Python-urllib/*` with code 1010. See lambda_terminate.
LAMBDA_UA = "curl/8.4.0"

WAIT = "WAIT"     #: healthy, keep watching
KILL = "KILL"     #: something is wrong — terminate the instance
DONE = "DONE"     #: the run finished — terminate the instance anyway


class _ArmRefused:
    """⛔ Falsy, and its own type, so `if not ok` and `ok is ARM_REFUSED` both
    read correctly and neither can be confused with a plain `False` returned by
    some unrelated failure."""

    __slots__ = ()

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "ARM_REFUSED"


ARM_REFUSED = _ArmRefused()

#: Command names that RUN a script rather than merely mentioning it. Used to
#: decide whether the marker token is the job or is being read by something else.
INTERPRETERS = frozenset({"bash", "sh", "dash", "zsh", "python", "python3", "env"})


@dataclass(frozen=True)
class Observation:
    """Everything the decision needs, as data — so every branch is testable
    without a process, a clock or a box."""

    now: float
    started: float
    pid: int
    cmdline: str | None      # None = no such process
    log_bytes: int
    log_last_change: float
    done_marker: bool


def is_the_job(cmdline: str | None, marker: str) -> bool:
    """⛔ SUBSTRING PRESENCE IS NOT IDENTITY — that is the whole 08-10 bug.

    `tail -f run.sh.log`, `grep foo run.sh`, `vim run.sh` and
    `watchdog.py --marker run.sh` all CONTAIN the marker and none of them is the
    job. The marker must be the thing being EXECUTED: argv[0], or argv[1] behind
    an interpreter.
    """
    if not cmdline:
        return False
    argv = cmdline.split()
    if not argv:
        return False
    for i, tok in enumerate(argv):
        if os.path.basename(tok) != marker:
            continue
        if i == 0:
            return True
        if i == 1 and os.path.basename(argv[0]) in INTERPRETERS:
            return True
    return False


def decide(o: Observation, *, marker: str, deadline_s: float,
           stall_s: float) -> tuple[str, str]:
    """-> (action, reason). ⛔ The reason string is the ONLY postmortem that
    survives the instance, so each terminating branch carries a distinct one."""
    if o.done_marker:
        # ⛔⛔ FIRST, and above the deadline: a run that finished must be
        # recorded as finished. "Runaway" on a completed run would send whoever
        # reads this hunting a bug that is not there.
        return DONE, "run complete (done-marker present)"
    if o.cmdline is None:
        return KILL, "process %d is gone and the run did not complete" % o.pid
    if not is_the_job(o.cmdline, marker):
        return KILL, ("pid %d is no longer the run — cmdline does not execute "
                      "%s (pid reuse, or the wrong pid was armed)"
                      % (o.pid, marker))
    if o.now - o.started > deadline_s:
        return KILL, ("deadline exceeded: %.1f h elapsed against a %.1f h limit"
                      % ((o.now - o.started) / 3600.0, deadline_s / 3600.0))
    if o.now - o.log_last_change > stall_s:
        return KILL, ("stalled: no log growth for %.0f min (limit %.0f min) — "
                      "alive but producing nothing"
                      % ((o.now - o.log_last_change) / 60.0, stall_s / 60.0))
    return WAIT, "healthy"


def act(action: str, reason: str, *, terminator) -> None:
    """⛔⛔ A VERDICT IS NOT A SHUTDOWN.

    Returning KILL and never calling the terminator is the `cold_pin` failure —
    a check that reports instead of acting, which reads as a passing guard.

    ⛔ No try/except. If terminating fails, that must be LOUD: a swallowed
    exception leaves the loop polling a box nobody is watching, which is the
    exact cost this module exists to bound.
    """
    if action in (KILL, DONE):
        terminator(reason)


def run_flush(cmd: str, *, timeout_s: float = 900.0, runner=None) -> bool:
    """⛔⛔ LAST WORDS. Push whatever is still only on this box before it dies.

    ⭐ BEST-EFFORT BY DESIGN, AND IT CAN NEVER BLOCK THE TERMINATE. This runs on
    a box that is already being killed for stalling, overrunning, or dying — it
    is burning money for nothing at the moment this executes. A flush that
    raised, hung, or aborted the shutdown would convert a bounded failure into
    an unbounded bill, which is the one thing this module exists to prevent.

    ⛔ So: everything is caught, there is a hard timeout, and the return value is
    reported rather than acted on. The failure is LOUD in the log and silent in
    the control flow.
    """
    import subprocess
    print("FLUSH: %s" % cmd, flush=True)
    try:
        r = (runner or subprocess.run)(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout_s)
    except Exception as e:                                       # noqa: BLE001
        print("⛔ FLUSH FAILED (%s: %s) — terminating anyway"
              % (type(e).__name__, e), flush=True)
        return False
    for line in (getattr(r, "stdout", "") or "").splitlines():
        print("  flush| %s" % line, flush=True)
    rc = getattr(r, "returncode", 1)
    if rc != 0:
        print("⛔ FLUSH exited %s — terminating anyway: %s"
              % (rc, (getattr(r, "stderr", "") or "")[:400]), flush=True)
    return rc == 0


def with_flush(terminator, flush_cmd, *, timeout_s: float = 900.0,
               runner=None):
    """Wrap a terminator so it flushes FIRST. ⛔ Before, never instead of.

    ⛔⛔ THE ORDER IS THE WHOLE POINT. `retrain12` succeeded, wrote `~/DONE`, and
    was terminated within one 300 s poll with 84 solo transcripts and its run log
    still on it. The transcripts are regenerable; the log is not.
    """
    if not flush_cmd:
        return terminator

    def _terminate_after_flush(reason: str) -> None:
        run_flush(flush_cmd, timeout_s=timeout_s, runner=runner)
        terminator(reason)

    return _terminate_after_flush


def arm(*, pid: int, marker: str, cmdline_reader) -> tuple[object, str]:
    """Refuse to start watching unless the thing being watched is really there.

    ⛔ A watchdog armed on a dead or wrong PID is worse than none: it reports a
    healthy run forever, and the reassurance is what stops anyone looking.
    """
    if pid == os.getpid():
        return ARM_REFUSED, ("refusing to watch my own pid %d — a watchdog "
                             "watching itself is healthy forever" % pid)
    cmdline = cmdline_reader(pid)
    if cmdline is None:
        return ARM_REFUSED, "pid %d is not running" % pid
    if not is_the_job(cmdline, marker):
        return ARM_REFUSED, ("pid %d does not look like %s (cmdline: %r)"
                             % (pid, marker, cmdline[:120]))
    return True, "armed on pid %d" % pid


# ── the real world ──────────────────────────────────────────────────────────

def proc_cmdline(pid: int) -> str | None:
    """Read `/proc/<pid>/cmdline` for ONE pid. ⛔ Not a scan of the process
    table — the scan is the bug."""
    try:
        raw = pathlib.Path("/proc/%d/cmdline" % pid).read_bytes()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None
    return raw.replace(b"\0", b" ").decode("utf-8", "replace").strip()


def lambda_terminate(reason: str) -> None:
    """⛔⛔ ON LAMBDA, HALTING IS NOT TERMINATING — `shutdown -h` stops the OS and
    the instance KEEPS BILLING. Only the API call ends the charge, so that is
    what a self-terminating watchdog must do.

    ⛔ `LAMBDA_API_KEY` is read from the environment and never logged.
    """
    import json
    import urllib.request

    key = os.environ.get("LAMBDA_API_KEY")
    if not key:
        raise RuntimeError(
            "LAMBDA_API_KEY is not set — this watchdog cannot terminate the "
            "instance, and an unterminatable watchdog is not a safety device")
    iid = (os.environ.get("LAMBDA_INSTANCE_ID")
           or pathlib.Path("/etc/lambda-instance-id").read_text().strip())
    # ⛔⛔ THE USER-AGENT IS WHAT MAKES THIS WORK AT ALL. Cloudflare fronts the
    # API and 403s `Python-urllib/3.x` (error code 1010) — a browser-signature
    # block indistinguishable from an auth failure. Without it this watchdog
    # could not terminate anything, and would have found that out only at the
    # moment it needed to.
    req = urllib.request.Request(
        "https://cloud.lambdalabs.com/api/v1/instance-operations/terminate",
        data=json.dumps({"instance_ids": [iid]}).encode(),
        headers={"Authorization": "Bearer %s" % key,
                 "Content-Type": "application/json",
                 "Accept": "application/json",
                 "User-Agent": LAMBDA_UA})
    print("TERMINATING instance %s — %s" % (iid, reason), flush=True)
    with urllib.request.urlopen(req, timeout=60) as r:
        print("terminate response %s" % r.status, flush=True)


def terminate_reachable() -> tuple[bool, str]:
    """⛔⛔ PROVE THE KILL PATH WORKS BEFORE TRUSTING IT.

    A watchdog that cannot reach the terminate API is not a watchdog — it is a
    log with a countdown, and it discovers its own uselessness at exactly the
    moment it is needed. This makes a READ-ONLY authenticated call so the
    credential, the network path and the Cloudflare browser-signature check are
    all exercised at ARM TIME.

    ⭐ Found the hard way: the first version of `lambda_terminate` sent no
    User-Agent, which Cloudflare 403s with error code 1010 — a block that reads
    exactly like an auth failure. Every call would have failed, including the
    only one that matters.
    """
    import urllib.error
    import urllib.request
    key = os.environ.get("LAMBDA_API_KEY")
    if not key:
        return False, "LAMBDA_API_KEY is not set"
    req = urllib.request.Request(
        "https://cloud.lambdalabs.com/api/v1/instances",
        headers={"Authorization": "Bearer %s" % key,
                 "Accept": "application/json", "User-Agent": LAMBDA_UA},
        method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            if r.status != 200:
                return False, "terminate API returned HTTP %s" % r.status
    except urllib.error.HTTPError as e:
        return False, ("terminate API unreachable: HTTP %s (1010 means the "
                       "User-Agent was rejected, not the key)" % e.code)
    except Exception as e:                                     # noqa: BLE001
        return False, "terminate API unreachable: %s" % type(e).__name__
    return True, "terminate path verified"


def observe(pid, log, done, started) -> Observation:
    log_p, done_p = pathlib.Path(log), pathlib.Path(done)
    try:
        st = log_p.stat()
        size, mtime = st.st_size, st.st_mtime
    except FileNotFoundError:
        # ⛔ A missing log is NOT treated as fresh. Anchoring to `started` means
        # a run that never writes anything still trips the stall branch instead
        # of resetting its own timer every poll.
        size, mtime = 0, started
    return Observation(now=time.time(), started=started, pid=pid,
                       cmdline=proc_cmdline(pid), log_bytes=size,
                       log_last_change=mtime, done_marker=done_p.exists())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, required=True)
    ap.add_argument("--marker", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--done", required=True)
    ap.add_argument("--deadline-h", type=float, default=40.0)
    ap.add_argument("--stall-min", type=float, default=90.0)
    ap.add_argument("--poll-s", type=float, default=300.0)
    # ⛔⛔ WHAT TO SAVE ON THE WAY OUT. Without it, a box killed for a stall or a
    # dead process takes its run log with it — the record of WHY, which is the
    # one artifact that re-running cannot regenerate.
    ap.add_argument("--flush-cmd", default=None,
                    help="shell command run BEFORE terminating, on every "
                         "terminating verdict. Best-effort: its failure is "
                         "logged and never blocks the terminate.")
    ap.add_argument("--flush-timeout-s", type=float, default=900.0)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the verdict instead of terminating")
    a = ap.parse_args()

    ok, why = arm(pid=a.pid, marker=a.marker, cmdline_reader=proc_cmdline)
    if not ok:
        print("⛔ ARM REFUSED: %s" % why, file=sys.stderr)
        return 2
    if not a.dry_run:
        # ⛔ REFUSE TO ARM ON AN UNPROVEN KILL PATH. Running the job guarded by a
        # watchdog that cannot terminate is worse than running it unguarded,
        # because the guard is the reason nobody is watching.
        reachable, why = terminate_reachable()
        if not reachable:
            print("⛔⛔ REFUSING TO ARM: %s" % why, file=sys.stderr)
            return 3
        print("  ✅ %s" % why, flush=True)
    print("watchdog %s · deadline %.1f h · stall %.0f min · poll %.0f s"
          % (why, a.deadline_h, a.stall_min, a.poll_s), flush=True)

    started = time.time()
    terminator = ((lambda r: print("DRY-RUN would terminate: %s" % r, flush=True))
                  if a.dry_run else lambda_terminate)
    terminator = with_flush(terminator, a.flush_cmd,
                            timeout_s=a.flush_timeout_s)
    if a.flush_cmd:
        print("  flush-on-exit armed (timeout %.0f s): %s"
              % (a.flush_timeout_s, a.flush_cmd), flush=True)
    while True:
        o = observe(a.pid, a.log, a.done, started)
        action, reason = decide(o, marker=a.marker,
                                deadline_s=a.deadline_h * 3600.0,
                                stall_s=a.stall_min * 60.0)
        print("[%s] %s · %s · log %d B"
              % (time.strftime("%H:%M:%S"), action, reason, o.log_bytes),
              flush=True)
        if action != WAIT:
            act(action, reason, terminator=terminator)
            return 0 if action == DONE else 1
        time.sleep(a.poll_s)


if __name__ == "__main__":
    raise SystemExit(main())
