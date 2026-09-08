"""⛔⛔ A TEXT GUARD THAT READS A WHOLE FILE MATCHES ITS OWN DOCUMENTATION.

FIVE TIMES IN ONE SESSION (2026-09-08), each with the same shape and the same
fix, each narrowed by hand as if it were a one-off:

  1. a test banning a hardcoded `prereg=` id matched its own docstring quoting
     the hardcoded id;
  2. a test banning `siblings` matched its own rationale for why summing
     `siblings` is wrong;
  3. a test named for asserting a refusal matched only the FIRST LINE of a
     multi-line shell call, so it would have passed with `|| true` on line two;
  4. a test banning `--unfreeze-top` matched the pipeline comment explaining
     that the flag is refused;
  5. a test banning a literal backslash matched the lint docstring explaining
     what backslashes did.

⭐⭐ FIVE OCCURRENCES OF A KNOWN FIX IS A MISSING HELPER, NOT FIVE MISTAKES.
Documenting a defect necessarily writes the defect's text into the file, so any
guard that greps the file finds it. Narrowing each instance individually leaves
the next guard to rediscover it. This is the fix, once:

    from textguard import code_only
    assert "--unfreeze-top" not in code_only(src)

⛔ NARROW, NEVER WEAKEN. `code_only` removes prose so the assertion can stay
strict about the code. It is not a licence to soften what is asserted.
"""
from __future__ import annotations

import re

_TRIPLE = ("'''", '"""')


def code_only(text: str, *, comment: str = "#") -> str:
    """The text with comments and triple-quoted blocks removed.

    ⭐ Line COUNT is preserved -- blanked lines, not deleted ones -- so a match
    offset still points at the right line of the original file.

    ⛔ Deliberately simple and conservative: it drops whole lines that open or
    sit inside a triple-quoted block, and whole lines whose first non-space
    character starts a comment. A trailing comment on a code line is left
    alone, because removing it could corrupt the code the guard is inspecting,
    and a guard tripping on a trailing comment has not happened.
    """
    out, in_block, closer = [], False, None
    for ln in text.splitlines():
        s = ln.strip()
        if in_block:
            out.append("")
            if closer in s:
                in_block = False
            continue
        if s.startswith(comment):
            out.append("")
            continue
        opened = next((q for q in _TRIPLE if q in s), None)
        if opened is not None:
            # a one-line docstring closes on the same line
            if s.count(opened) < 2:
                in_block, closer = True, opened
            out.append("")
            continue
        out.append(ln)
    return "\n".join(out)


def joined_continuations(text: str) -> str:
    """Shell text with line continuations folded into single logical lines.

    ⛔⛔ FAILURE 3 ABOVE. A pattern like `[^BSn]*cmd[^BSn]*(?:BSBSn[^BSn]*)*`
    never matches the continuation -- the greedy class eats the backslash -- so
    the guard silently inspects a FRAGMENT and passes on a defect sitting one
    line down. Fold first, then match.
    """
    return text.replace(chr(92) + "\n", " ")


def one_call(text: str, needle: str) -> str:
    """The full logical shell command containing `needle`, continuations joined."""
    flat = joined_continuations(text)
    m = re.search(r"[^\n]*" + re.escape(needle) + r"[^\n]*", flat)
    if not m:
        raise AssertionError("no command containing %r" % needle)
    return m.group(0)
