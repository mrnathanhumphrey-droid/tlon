"""⛔⛔ UNDEFINED NAMES, CAUGHT BEFORE THE MONEY IS SPENT.

`python -m py_compile` accepts a name that is never bound. The interpreter
only objects when control reaches it, and in this repo the lines that run last
are the ones that write the report, persist the adapter and record the spend —
so the cheapest possible bug detonates at the single most expensive moment.

⛔⛤ THIS SUITE EXISTS BECAUSE I WROTE ONE. Rewriting a print in
`act2_build_conversations.py` as a bare if/else left `per_conv` unbound while
the `build_report.json` writer still read it: a NameError raised AFTER a
$45 build, at the one line that records what the build measured. It compiled
cleanly and every other test stayed green.

⭐ Scoped to the one pyflakes class that is never a style opinion. Unused
imports and shadowed names are judgement calls; a name that is not defined is
a crash with a delay fuse.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGES = ("tlon", "tools", "puzzle", "tests")

#: ⛔⛔ KNOWN AND UNFIXED, LISTED RATHER THAN SILENCED. Each entry is a live
#: crash somebody has to decide about; an allowlist that nobody can read is
#: how a suppression becomes permanent.
#:
#: ✅ EMPTY, AND IT WAS NOT. `act2_two_speaker_probe.py` READ `history_limit`
#: inside the two-adapter branch and BOUND it 33 lines later, so every
#: shared-arm run died with UnboundLocalError before generating a turn — the
#: arm could not run at all. Introduced by e4b4560, whose subject is "the
#: history window was silently truncating the shared store": the fix for the
#: truncation crashed the arm it was fixing. Fixed 2026-09-26 by moving the
#: binding up beside `seed_history`, the only thing it depends on.
#:
#: ⭐ The entry is DELETED rather than left with a note, because
#: `test_a_fixed_entry_must_be_removed_from_the_list` is what forced this edit:
#: a register that keeps paid debts starts lying about what is outstanding.
KNOWN_UNDEFINED: dict[str, int] = {}


def _undefined_names():
    """-> {relative path: count} for pyflakes' undefined-name class."""
    proc = subprocess.run(
        [sys.executable, "-m", "pyflakes", *PACKAGES],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT))
    out = {}
    for line in (proc.stdout or "").splitlines():
        if "undefined name" not in line and "referenced before assignment" \
                not in line:
            continue
        path = line.split(":", 1)[0].replace("\\", "/")
        out[path] = out.get(path, 0) + 1
    return out


@pytest.fixture(scope="module")
def found():
    try:
        import pyflakes                                   # noqa: F401
    except ImportError:                                   # pragma: no cover
        pytest.skip("pyflakes is not installed on this machine")
    return _undefined_names()


def test_no_new_undefined_names(found):
    """⛔ The whole point: a name used before it is bound is a crash that
    compiles, and the deferred ones land on the expensive lines."""
    new = {p: n for p, n in found.items() if p not in KNOWN_UNDEFINED}
    assert not new, (
        "undefined name(s) in %s — these compile and crash at run time; if "
        "one is genuinely intentional, add it to KNOWN_UNDEFINED with the "
        "reason" % new)


def test_the_known_list_shrinks_and_never_grows(found):
    """⛔⛔ AN ALLOWLIST THAT IS NEVER RE-READ IS A PERMANENT SUPPRESSION.
    If a listed file gains another undefined name, that is a NEW bug hiding
    behind an old entry's exemption."""
    for path, expected in KNOWN_UNDEFINED.items():
        got = found.get(path, 0)
        assert got <= expected, (
            "%s now has %d undefined names, was %d — a new one is hiding "
            "behind the existing exemption" % (path, got, expected))


def test_a_fixed_entry_must_be_removed_from_the_list(found):
    """⭐ The list is a debt register, so paying a debt has to close it —
    otherwise the next reader believes a crash is still outstanding."""
    stale = [p for p, n in KNOWN_UNDEFINED.items() if found.get(p, 0) < n]
    assert not stale, (
        "fixed, but still listed as known-broken: %s — delete the entry, it "
        "is now telling the next reader something false" % stale)


def test_the_checker_can_actually_fail(tmp_path):
    """⛔⛔ A GREEN CHECK PROVES NOTHING UNTIL IT HAS BEEN SEEN TO GO RED.
    This is the exact shape that got past `py_compile`: a name bound on
    neither branch of an if/else and read afterwards."""
    pytest.importorskip("pyflakes")
    probe = tmp_path / "probe.py"
    probe.write_text(
        "def f(n):\n"
        "    if n:\n"
        "        print('a')\n"
        "    else:\n"
        "        print('b')\n"
        "    return {'k': per_conv}\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "pyflakes", str(probe)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert "undefined name 'per_conv'" in proc.stdout, proc.stdout
    assert proc.returncode != 0
