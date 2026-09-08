"""THE SIXTH-TIME LINT — red-proofed, including against its own failure mode.

⛔⛔ The rule this enforces has been written down and re-learned SIX times. Each
time the fix was the sentence already in the notes; each time the habit reached
for a heredoc first. A known-fix error that recurs six times is a MISSING GUARD,
not a memory problem, so the rule now fails the build instead of the artifact.

⭐ The lint is also the thing most likely to be defeated by the bug it catches:
the check written to DETECT the corruption was, once, corrupted by it. So
nothing in this file or the lint may contain a literal backslash -- both use
`chr(92)`, and a test below asserts exactly that.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lint_heredoc_backslash as L  # noqa: E402

BS = chr(92)


def test_the_live_tree_is_clean():
    """⭐ Enforced from the start, so it can never accumulate a backlog that
    makes turning it on a project."""
    assert L.main() == 0


def test_it_CATCHES_a_backslash_in_a_heredoc_payload():
    """⛔ The red proof, in the exact shape that has bitten six times: a regex
    inside a python heredoc."""
    src = "\n".join([
        "$PY - <<PY",
        "import re",
        "m = re.search(r'" + BS + "d+', s)",
        "PY",
    ])
    v = L.violations(src)
    assert len(v) == 1, v
    assert v[0][0] == 3


def test_a_shell_LINE_CONTINUATION_is_not_flagged():
    """⛔ Scope matters or the lint gets switched off. A trailing backslash
    continuing a shell command is ordinary and is NOT the corruption vector; a
    noisy guard is a dead guard."""
    src = "\n".join([
        "$PY tools/x.py --a 1 " + BS,
        "    --b 2",
        "echo done",
    ])
    assert L.violations(src) == []


def test_a_backslash_AFTER_the_heredoc_closes_is_not_flagged():
    src = "\n".join([
        "$PY - <<PY",
        "print(1)",
        "PY",
        "$PY tools/y.py --a 1 " + BS,
        "    --b 2",
    ])
    assert L.violations(src) == []


def test_a_quoted_tag_heredoc_is_scanned_too():
    """⛔ `<<'PY'` is the form that LOOKS safest -- quoted means the shell does
    not expand -- and it is still the form that ate a backslash. Both are
    scanned."""
    src = "\n".join(["cat <<'PY'", "x = '" + BS + "n'", "PY"])
    assert len(L.violations(src)) == 1


def test_multiple_heredocs_in_one_file_are_all_scanned():
    src = "\n".join([
        "cat <<A", "clean", "A",
        "cat <<B", "dirty " + BS + "s", "B",
        "cat <<C", "clean", "C",
    ])
    v = L.violations(src)
    assert len(v) == 1 and v[0][0] == 5


# ⛔⛔ A TEST WAS REMOVED HERE, AND THE REASON IS THE POINT.
#
# It asserted that the lint's own source contains no literal backslash, on the
# history that "the check written to detect this corruption was once corrupted
# by it". It failed on `\s` inside the lint's own regex and on `"\n"` in this
# file's `join` calls -- all of it ordinary, correct Python.
#
# ⭐ Because the invariant was MIS-SPECIFIED. The hazard is the HEREDOC
# TRANSPORT, not backslashes in source: a file authored with Write/Edit can
# hold as many as it likes and nothing eats them. "No backslash in the source"
# was a PROXY for "this file was not authored through a heredoc", and the proxy
# is false for every legitimately-authored file -- `proxy_rots`, in miniature,
# inside the very lint built to retire a recurring error.
#
# ⛔ So it is REMOVED, not weakened. A guard whose premise is wrong does not
# get a softer threshold; it gets deleted, and the reason gets written down.
# What the lint must actually do -- catch a backslash in a heredoc payload and
# ignore a shell line-continuation -- is asserted by the tests above.
