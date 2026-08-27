"""⛔⛔ THE REPO MUST PARSE UNDER THE PYTHON THE RENTED BOX ACTUALLY RUNS.

**This cost a live box.** `tools/act2_ki_attribution.py` used a multi-line
expression inside an f-string — PEP 701, valid on the 3.12 here, a hard
SyntaxError on the **3.10** the Lambda image ships. The pipeline died at stage 1
with the meter running, and it could not even IMPORT the file to find out.

⚠️⚠️ AND THE OBVIOUS GUARD IS A DEAD GUARD. `ast.parse(src,
feature_version=(3,10))` **accepts** the offending construct — measured, not
assumed:

    (3, 10) PARSED   (3, 9) PARSED

`feature_version` covers only a handful of features and PEP 701 is not among
them. A test built on it would pass forever while the box kept failing, which is
worse than no test. So this file uses the **tokenizer**, which does see it: a
single f-string whose START and END tokens sit on different physical lines is
exactly the 3.12-only construct.

⭐ THE AUTHORITATIVE CHECK RUNS ON THE TARGET, NOT HERE. `pipeline_ki_target.sh`
runs `python -m compileall` on the box before anything else, which catches every
syntax error under the real interpreter for ~2 seconds. This test is the local
tripwire that catches the known-dangerous shape before a box is ever rented.
"""
from __future__ import annotations

import io
import pathlib
import sys
import tokenize

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: The Lambda base image's interpreter, measured on the box 2026-08-27.
BOX_PYTHON = (3, 10)

SCANNED = ("tools", "tlon", "tests")


def _multiline_fstrings(path: pathlib.Path) -> list[int]:
    """Line numbers of f-strings that span physical lines.

    Only meaningful on 3.12+, where the tokenizer emits FSTRING_START/END. On an
    older interpreter the construct is a SyntaxError anyway, so the file would
    never get here.
    """
    start_tok = getattr(tokenize, "FSTRING_START", None)
    end_tok = getattr(tokenize, "FSTRING_END", None)
    if start_tok is None or end_tok is None:
        return []                        # pre-3.12 runner: nothing to detect
    # ⛔⛔ IT IS THE *EXPRESSION* THAT MAY NOT SPAN LINES, NOT THE F-STRING.
    # The first version of this flagged any f-string whose START and END sat on
    # different lines, which made every `f\"\"\"...\"\"\"` in the repo an offender —
    # FOUR false positives, against ONE real error that `compileall` on the box
    # had correctly found alone. A guard noisier than the thing it guards gets
    # switched off. Newlines inside FSTRING_MIDDLE are literal text and legal
    # everywhere; only a newline between `{` and its matching `}` is PEP 701.
    src = path.read_text(encoding="utf-8")
    bad, in_fstring, depth, opened_line = [], 0, 0, None
    try:
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t.type == start_tok:
                in_fstring += 1
            elif t.type == end_tok:
                in_fstring = max(0, in_fstring - 1)
            elif in_fstring and t.type == tokenize.OP:
                if t.string == "{":
                    if depth == 0:
                        opened_line = t.start[0]
                    depth += 1
                elif t.string == "}" and depth:
                    depth -= 1
                    if depth == 0 and opened_line is not None:
                        if t.end[0] != opened_line:
                            bad.append(opened_line)
                        opened_line = None
    except (tokenize.TokenError, SyntaxError):
        return []                        # a broken file is the other test's job
    return sorted(set(bad))


def test_no_multiline_fstring_expressions_anywhere():
    """⛔ PEP 701. Valid on 3.12, a SyntaxError on the box's 3.10."""
    offenders = {}
    for d in SCANNED:
        for p in sorted((ROOT / d).rglob("*.py")):
            lines = _multiline_fstrings(p)
            if lines:
                offenders[str(p.relative_to(ROOT))] = lines
    assert not offenders, (
        f"multi-line f-string expressions (PEP 701, needs Python 3.12) — the "
        f"rented box runs {'.'.join(map(str, BOX_PYTHON))} and cannot PARSE "
        f"these: {offenders}. Build the string in a local variable first.")


def test_the_detector_actually_detects(tmp_path):
    """⛔⛔ THE GUARD-ON-THE-GUARD. `ast.parse(feature_version=(3,10))` accepts
    this construct, so a plausible-looking guard would be dead. This asserts the
    tokenizer-based one is alive — on a 3.12 runner it must FIRE on the exact
    shape that killed the box."""
    if not hasattr(tokenize, "FSTRING_START"):
        return                            # pre-3.12: construct cannot exist
    p = tmp_path / "bad.py"
    p.write_text(
        'x = 1\n'
        'print(f"a {\'y\' if x else \'z \'\n'
        '            \'w\'}")\n', encoding="utf-8")
    assert _multiline_fstrings(p), (
        "the detector did not fire on the exact construct that killed the box — "
        "it is a dead guard, exactly like the feature_version approach it "
        "replaced")


def test_triple_quoted_fstrings_are_NOT_flagged(tmp_path):
    """⛔⛔ THE FALSE-POSITIVE CASE THAT NEARLY MADE THIS GUARD USELESS. A newline
    inside the literal TEXT of an f-string is legal on every version; the repo is
    full of them and the first version of the detector called all four
    offenders while `compileall` on the box had correctly found one."""
    p = tmp_path / "ok3.py"
    p.write_text('x = 1\nprint(f"""line one {x}\nline two {x}\n""")\n',
                 encoding="utf-8")
    assert _multiline_fstrings(p) == []


def test_single_line_fstrings_are_not_flagged(tmp_path):
    """A legitimate no-op must not be red — including implicit concatenation of
    SEPARATE f-strings across lines, which is fine on every version."""
    p = tmp_path / "ok.py"
    p.write_text(
        'x = 1\n'
        'print(f"a {x} "\n'
        '      f"b {x}")\n', encoding="utf-8")
    assert _multiline_fstrings(p) == []


def test_local_interpreter_is_newer_than_the_box():
    """⭐ Records WHY the local suite cannot be the authority here. If this ever
    fails, the local runner became the floor and the tokenizer path goes dark —
    at which point `compileall` on the box is the only real check."""
    assert sys.version_info[:2] >= BOX_PYTHON
