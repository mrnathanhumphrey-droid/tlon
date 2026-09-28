"""Every `act2_box_persist.py` call in every pipeline must name a real subcommand.

⛔⛤ WRITTEN AFTER A TYPO COST TWO ADAPTERS AND ~16 GPU-h.
`pipeline_idf2_train.sh` ran `act2_box_persist.py … persist --cells "…"`. There
is no `persist` subcommand — it is `cell`, singular, with `--cell`, `--solo-n`
and `--corpus-manifest`. The run trained M and C1, took all eighteen reads, and
died at rc=2 on the persist step; the watchdog then correctly terminated a box
whose weights existed nowhere else. Only the log survived.

⛔⛔ AND THE SUITE MADE IT WORSE, NOT BETTER. The pipeline's own test asserted
`script.index("persist --cells") < script.index("tlon_mark_done")` — it pinned
the ORDERING of a string that could never run, so the typo had a green test
around it. **A test that checks where a command sits in a file has not checked
that the command exists.**

⭐ THE COMMAND WAS ALSO ALREADY WRITTEN CORRECTLY, in `pipeline_retrain.sh`,
beside a comment giving the ordering rule that would have made the typo cheap:
*"the adapter is already durable, so a fault in the read costs the read and not
the weights."* Neither the call nor the ordering was copied.
"""
from __future__ import annotations

import pathlib
import re
import shlex

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

#: Shell variables are opaque here, so they collapse to a token that is merely
#: *a* string. ⭐ Enough for the question being asked, which is about the SHAPE
#: of the command line rather than its values.
_VAR = re.compile(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|\$\([^)]*\)")
#: ⛔ Quotes are DELETED, not substituted. Folding them into `_VAR` turned
#: `--flush-cmd "… flush"` into the token `flushX`, so a correct call read as a
#: missing subcommand — the checker inventing the defect it hunts, twice over.
_QUOTE = re.compile(r"[\"']")

VALID_SUBCOMMANDS = {"cell", "full-weight", "file", "verify", "tree",
                     "restore", "flush", "probe"}


def _invocations(text: str, tool: str):
    """-> [argv, …] for each call of `tool` in a shell script.

    ⛔⛤ NORMALISE LINE ENDINGS FIRST. The first version joined `"\\\\\\n"` and
    this repo checks out CRLF on Windows, so every continuation was `\\` + CRLF
    and NONE of them joined — which made two perfectly correct pipelines look
    like they called the tool with no subcommand at all. A checker whose own
    parsing is wrong reports the thing it was built to catch, everywhere.

    ⛔ `echo` lines are skipped: `pipeline_solo_regen.sh` PRINTS a restore
    command as advice, and advice is not an invocation.
    """
    joined = text.replace("\r\n", "\n").replace("\\\n", " ")
    out = []
    for line in joined.splitlines():
        stripped = line.lstrip()
        if tool not in line or stripped.startswith(("#", "echo")):
            continue
        frag = line.split(tool, 1)[1].split("2>&1")[0].split("|")[0]
        try:
            out.append(shlex.split(_VAR.sub("X", _QUOTE.sub("", frag))))
        except ValueError:
            continue
    return out


def _subcommands(argv):
    """-> the valid subcommand tokens present in one invocation.

    ⛔ DELIBERATELY NOT "the first bare word". Flag VALUES are bare words too,
    so `--repo X cell --cell Y` has several and the first is the repo. The
    check that catches the real bug does not need to LOCATE the subcommand: a
    legal call contains one, and `persist --cells "a b"` contains none.
    """
    return [a for a in argv if a in VALID_SUBCOMMANDS]


def _pipelines():
    return sorted(p for p in TOOLS.glob("pipeline_*.sh")
                  if p.name != "pipeline_lib.sh")


@pytest.mark.parametrize("script", _pipelines(), ids=lambda p: p.name)
def test_every_box_persist_call_names_a_real_subcommand(script):
    """⛔⛔ THE CHECK THAT WOULD HAVE SAVED THE RUN, in milliseconds."""
    calls = _invocations(script.read_text(encoding="utf-8"),
                         "act2_box_persist.py")
    if not calls:
        pytest.skip("%s does not persist directly" % script.name)
    for argv in calls:
        assert _subcommands(argv), (
            "%s calls act2_box_persist.py with no valid subcommand: %r. "
            "Valid: %s" % (script.name, argv, sorted(VALID_SUBCOMMANDS)))


def test_the_valid_subcommand_list_matches_the_tool():
    """⭐ The list above is a copy; the tool is the authority. If they drift
    apart this fails rather than the check going quietly stale."""
    src = (TOOLS / "act2_box_persist.py").read_text(encoding="utf-8")
    declared = set(re.findall(r'sub\.add_parser\("([a-z-]+)"\)', src))
    assert declared == VALID_SUBCOMMANDS, declared


def test_idf2_train_persists_each_cell_BEFORE_its_reads():
    """⛔⛔ THE ORDERING THAT TURNED A TYPO INTO A LOSS. Run 1 persisted after
    all eighteen reads, so the failure landed with 7 GPU-h of weights on a box
    and nothing in durable storage."""
    s = (TOOLS / "pipeline_idf2_train.sh").read_text(encoding="utf-8")
    assert s.index("act2_box_persist.py") < s.index("step reads"), (
        "the cells must be durable before a single read is taken")
    assert "persist --cells" not in s, "the invented subcommand is back"
    assert "--solo-n 0" in s, (
        "persist_cell requires an EXACT solo count and this pipeline makes none")


def test_idf2_train_persist_call_has_every_required_argument():
    """⛔ `--corpus-manifest` has no default ON PURPOSE: the gate run persisted
    weights without it, and the corpus's own lag profile — the comparison
    quantity for the whole read — was nearly lost with the box terminating."""
    # ⛔ Taken from the EXTRACTED invocation, not from a text slice. The first
    # version sliced after the first occurrence of the tool name — which now
    # lands in the comment explaining the bug, so it was reading prose.
    calls = _invocations(
        (TOOLS / "pipeline_idf2_train.sh").read_text(encoding="utf-8"),
        "act2_box_persist.py")
    assert calls, "no persist invocation found"
    argv = calls[0]
    assert "cell" in argv
    for flag in ("--cell", "--solo-n", "--corpus-manifest"):
        assert flag in argv, "persist call is missing %s: %r" % (flag, argv)


def test_this_checker_can_fail(tmp_path):
    """⛔⛔ A GREEN CHECK PROVES NOTHING UNTIL IT HAS BEEN SEEN TO GO RED. This
    is the exact line that ran on the box."""
    bad = tmp_path / "pipeline_bogus.sh"
    bad.write_text('$PY tools/act2_box_persist.py --root $R --repo $H '
                   'persist --cells "a b"\n', encoding="utf-8")
    calls = _invocations(bad.read_text(encoding="utf-8"),
                         "act2_box_persist.py")
    assert calls, "the extractor must find the call"
    assert not _subcommands(calls[0]), (
        "`persist` must be rejected — it is not a subcommand")


def test_the_checker_accepts_the_REAL_call(tmp_path):
    """⭐ And it must not simply reject everything: the corrected invocation has
    to pass, or the check is a tripwire nobody can satisfy."""
    good = tmp_path / "pipeline_ok.sh"
    good.write_text('$PY tools/act2_box_persist.py --root $ROOT --repo $HF '
                    'cell --cell $CELL --solo-n 0 '
                    '--corpus-manifest $C/manifest.json\n', encoding="utf-8")
    calls = _invocations(good.read_text(encoding="utf-8"),
                         "act2_box_persist.py")
    assert _subcommands(calls[0]) == ["cell"]
