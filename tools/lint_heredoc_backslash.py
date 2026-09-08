"""⛔⛔ NO BACKSLASH MAY LIVE INSIDE A HEREDOC PAYLOAD.

    python tools/lint_heredoc_backslash.py        # exit 1 on any violation

WHY THIS IS CODE AND NOT A NOTE. The rule "author backslash-carrying payloads
with Write/Edit, never a heredoc" has been written down, banked in memory, and
re-learned **six times**: `\\s`, `\\*` and `\\b` inside regexes; the check
written to DETECT the corruption was itself corrupted by it; a `\\\\n` that
arrived as `\\n` and silently truncated a test to a fragment; and a shell
substitution whose line-continuations were eaten.

⭐⭐ A KNOWN-FIX ERROR THAT RECURS SIX TIMES IS NOT A MEMORY PROBLEM, IT IS A
MISSING GUARD. Every one of those was caught late, by a failing test or a
mangled file, and the fix each time was the same sentence already sitting in
the notes. The habit reaches for a heredoc faster than the note fires. So the
rule moves out of vigilance and into the build: a payload that needs a
backslash belongs in its own file, authored with a real editor, where nothing
can eat it.

⛔ THE RULE IS DELIBERATELY ABSOLUTE. "Backslashes are fine if you escape them
correctly" is exactly the judgement call that failed six times. There is always
an alternative — put the payload in a `.py` file and run it — so a blanket ban
costs nothing and removes the class.
"""
from __future__ import annotations

import pathlib
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKSLASH = chr(92)  # ⛔ NEVER a literal here — see the module docstring.

#: `<<PY`, `<<'PY'`, `<<-PY`. The tag ends the payload when alone on a line.
_OPEN = re.compile(r"<<-?\s*'?([A-Za-z_][A-Za-z0-9_]*)'?\s*$")


def violations(text: str) -> list[tuple[int, str]]:
    """(line number, line) for every backslash inside a heredoc payload.

    ⛔ Only the PAYLOAD is scanned. A trailing backslash that continues a shell
    command is ordinary shell and is not what corrupts -- flagging it would
    make the lint noisy enough to be switched off, which is how a guard dies.
    """
    out, inside, tag = [], False, None
    for i, ln in enumerate(text.splitlines(), 1):
        if not inside:
            m = _OPEN.search(ln)
            if m:
                inside, tag = True, m.group(1)
            continue
        if ln.strip() == tag:
            inside, tag = False, None
            continue
        if BACKSLASH in ln:
            out.append((i, ln.strip()[:100]))
    return out


def main() -> int:
    files = sorted(ROOT.glob("tools/*.sh")) + sorted(ROOT.glob("*.sh"))
    bad = 0
    for p in files:
        v = violations(p.read_text(encoding="utf-8"))
        if v:
            bad += len(v)
            print("⛔ %s — %d backslash line(s) inside a heredoc payload:"
                  % (p.relative_to(ROOT).as_posix(), len(v)))
            for i, s in v:
                print("     %5d | %s" % (i, s))
    if bad:
        print()
        print("⛔⛔ %d violation(s). A heredoc EATS BACKSLASHES (6 occurrences "
              "in this project). Move the payload into its own .py file, "
              "author it with a real editor, and run that file instead."
              % bad)
        return 1
    print("scanned %d shell file(s) - 0 backslashes inside heredoc payloads"
          % len(files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
