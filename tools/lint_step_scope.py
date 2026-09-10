"""⛔⛔ EVERY PIPELINE STEP DECLARES WHICH SCOPE MODES IT IS VALID FOR.

THE CLASS THIS RETIRES, at five instances and counting: a step written for one
`SCOPE_MODE` running unconditionally in the other.

    `--unfreeze-top`  REQUIRED in layers, REFUSED in mapping. Deleted outright
                      when the file was set up for the mapping rung, which made
                      a layer rung unrunnable -- and a test pinned the absence.
    `mapping_moved`   asserts per-leaf movement of `embed_tokens`/`lm_head`,
                      which a LAYER rung freezes BY DESIGN. It refused run 2a
                      after a clean train and a clean read, killing the pipeline
                      before `verdict_epoch1` and before the run files were
                      persisted. The numbers survived only because the
                      watchdog's flush pushed the log.
    `vocab_coverage`  feeds `mapping_moved`'s prediction and nothing else. It
                      ran on the OLMo layer rung and produced a number no gate
                      consumed -- harmless, and the same defect.

⭐ FOUR PER-INSTANCE PATCHES DID NOT STOP IT, SO THE CHECK IS STRUCTURAL. This is
the heredoc lint's lesson applied again: a known-fix error that keeps recurring
gets a grammar tripwire, not more vigilance.

THE RULE. Every `step <name>` carries an annotation:

    step train_leg1        # SCOPE: any
    step mapping_moved     # SCOPE: mapping

and a step declaring a specific mode must LEXICALLY SIT INSIDE a matching
`if [ "$SCOPE_MODE" = "<mode>" ]` guard. A step declaring `any` must NOT sit
inside one, because an unguarded claim inside a guard is a false label.

⚠️ WHAT THIS CANNOT DO, STATED RATHER THAN IMPLIED: it cannot verify that an
`any` annotation is TRUE -- that a step so labelled really is mode-agnostic.
It enforces that the classification is DECLARED and that a declared
mode-specific step is really guarded. Its teeth are on the NEW step: one added
without an annotation fails immediately, which is the moment the decision is
actually being made.
"""
from __future__ import annotations

import pathlib
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass

MODES = ("any", "layers", "mapping")
STEP_RE = re.compile(r"^(\s*)step\s+([A-Za-z_][A-Za-z0-9_]*)\s*(.*)$")
ANNOT_RE = re.compile(r"#\s*SCOPE:\s*(\w+)")
GUARD_RE = re.compile(r'^\s*if\s+\[\s*"\$SCOPE_MODE"\s*=\s*"(\w+)"\s*\]')
IF_RE = re.compile(r"^\s*if\s+\[")
FI_RE = re.compile(r"^\s*fi\s*$")


def guarded_modes(lines) -> list:
    """-> per line index, the SCOPE_MODE this line is lexically guarded by.

    ⛔ Shell `if`/`fi` only. A Python `if x:` inside a heredoc does not match
    `if [`, and Python has no bare `fi`, so heredoc payloads cannot corrupt the
    depth count.
    """
    out = [None] * len(lines)
    stack = []          # (depth_at_open, mode)
    depth = 0
    for i, line in enumerate(lines):
        g = GUARD_RE.match(line)
        if IF_RE.match(line):
            depth += 1
            if g:
                stack.append((depth, g.group(1)))
        elif FI_RE.match(line):
            if stack and stack[-1][0] == depth:
                stack.pop()
            depth = max(0, depth - 1)
        out[i] = stack[-1][1] if stack else None
    return out


def check(path: pathlib.Path) -> list:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if "SCOPE_MODE" not in text:
        return []       # not a scope-mode pipeline; nothing to classify
    guards = guarded_modes(lines)
    problems = []
    for i, line in enumerate(lines):
        m = STEP_RE.match(line)
        if not m:
            continue
        name, tail = m.group(2), m.group(3)
        a = ANNOT_RE.search(tail)
        if not a:
            problems.append(
                "%s:%d  step %s has no `# SCOPE:` annotation. Declare which "
                "scope modes it is valid for (%s) -- an unclassified step is "
                "how a mapping-only gate came to refuse a layer run."
                % (path.name, i + 1, name, "/".join(MODES)))
            continue
        mode = a.group(1)
        if mode not in MODES:
            problems.append("%s:%d  step %s: unknown SCOPE %r (expected %s)"
                            % (path.name, i + 1, name, mode, "/".join(MODES)))
            continue
        actual = guards[i]
        if mode == "any" and actual is not None:
            problems.append(
                "%s:%d  step %s declares SCOPE: any but sits inside a "
                "`SCOPE_MODE = %s` guard. The label is false: it does not run "
                "in every mode." % (path.name, i + 1, name, actual))
        elif mode != "any" and actual != mode:
            problems.append(
                "%s:%d  step %s declares SCOPE: %s but is guarded by %r. A "
                "mode-specific step must sit inside a matching "
                "`if [ \"$SCOPE_MODE\" = \"%s\" ]` guard, or it runs in the "
                "mode it was never written for."
                % (path.name, i + 1, name, mode, actual, mode))
    return problems


def main(argv) -> int:
    root = pathlib.Path(argv[0]) if argv else pathlib.Path("tools")
    files = sorted(root.glob("pipeline_*.sh")) if root.is_dir() else [root]
    bad, scanned = [], 0
    for f in files:
        if "SCOPE_MODE" not in f.read_text(encoding="utf-8"):
            continue
        scanned += 1
        bad.extend(check(f))
    for b in bad:
        print("⛔ " + b)
    print("scanned %d scope-mode pipeline(s) - %d unclassified or misplaced "
          "step(s)" % (scanned, len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
