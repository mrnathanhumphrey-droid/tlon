"""⛔⛔ RED-PROOF: THE GUARD WHOSE ABSENCE OVERWROTE AN ADAPTER.

`pipeline_puzzle.sh` defaulted `CELL=bench-s20624`. A second run took that
default, trained a different model, and its persist wrote over the first run's
weights in durable storage — silently. Recovery was luck: a local pull existed
and the hub kept the prior revision.

⭐ Every arm below FIRES the guard on a fabricated version of that failure, or
proves it stays quiet on a healthy one. A guard only ever observed passing is
unexecuted code standing between you and a permanent loss.
"""
from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

from act2_cell_guard import OK, REFUSE, WARN, decide  # noqa: E402

EXISTING = [
    "bench-s20624/adapter_model.safetensors",
    "bench-s20624/adapter_config.json",
    "rowmatch-s20624/adapter_model.safetensors",
    "README.md",
]


def test_the_exact_collision_that_lost_the_adapter_is_REFUSED():
    """⛔⛔ THE REGRESSION. This is the real cell name and the real repo shape
    on the day it happened."""
    verdict, msg = decide("bench-s20624", EXISTING, allow=False)
    assert verdict == REFUSE
    assert "ALREADY EXISTS" in msg
    assert "bench-s20624/adapter_model.safetensors" in msg


def test_an_EMPTY_cell_is_REFUSED_because_that_was_the_default():
    """⛔ The fix removed the default, so the empty value must not sail through
    as "nothing to collide with"."""
    verdict, msg = decide("", EXISTING, allow=False)
    assert verdict == REFUSE
    assert "NO DEFAULT" in msg


def test_a_FREE_cell_PROCEEDS():
    """⛔ Non-vacuity. A guard that refused everything would pass both tests
    above and make every run unlaunchable."""
    verdict, _ = decide("bench5208-s20624", EXISTING, allow=False)
    assert verdict == OK


def test_a_DELIBERATE_overwrite_PROCEEDS_but_SAYS_SO():
    """⭐ Re-running a cell on purpose is legitimate; defaulting into it is not.
    The difference must be visible in the log, not merely permitted."""
    verdict, msg = decide("bench-s20624", EXISTING, allow=True)
    assert verdict == WARN
    assert "ON PURPOSE" in msg


def test_the_match_is_on_the_directory_SEPARATOR_not_a_bare_prefix():
    """⛔⛔ BOTH DIRECTIONS OF THE PREDICATE, per the predicate-equality rule.

    A bare `startswith(cell)` breaks two ways, and only one of them is loud:
    `bench-s2` would collide with `bench-s20624` (annoying), and a repo holding
    only `bench-s20624x/` would report `bench-s20624` FREE (a silent overwrite
    of nothing, then a real one later). The cell is a DIRECTORY; the separator
    is part of its identity.
    """
    # a shorter name is not a collision with a longer one
    assert decide("bench-s2", EXISTING, allow=False)[0] == OK
    # and a longer existing name does not make a shorter one look taken
    assert decide("bench-s20624", ["bench-s20624x/adapter_model.safetensors"],
                  allow=False)[0] == OK
    # while the real directory still refuses
    assert decide("bench-s20624", EXISTING, allow=False)[0] == REFUSE


def test_the_pipeline_calls_the_guard_before_it_trains():
    """⛔ THE TOOL EXISTING IS NOT THE TOOL RUNNING. The guard is only worth
    anything if the pipeline reaches it, and reaches it BEFORE the GPU."""
    src = (_ROOT / "tools" / "pipeline_puzzle.sh").read_text(encoding="utf-8")
    assert "act2_cell_guard.py" in src, "the pipeline never calls the guard"
    assert src.index("act2_cell_guard.py") < src.index("step train"), (
        "the cell guard runs AFTER training — it would refuse a cell whose "
        "GPU time has already been paid for")
    assert src.index("tlon_arm_watchdog") < src.index("act2_cell_guard.py"), (
        "the guard can refuse, and a refusal before the watchdog arms strands "
        "a billing box")
