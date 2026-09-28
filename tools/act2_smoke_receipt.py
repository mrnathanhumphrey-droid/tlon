"""The CPU dry run that a GPU launch is not allowed to proceed without.

    python tools/act2_smoke_receipt.py write --pipeline pipeline_idf2_train.sh
    python tools/act2_smoke_receipt.py check --pipeline pipeline_idf2_train.sh

⛔⛤ THIS EXISTS BECAUSE A RULE, A WORKED EXAMPLE AND A TEST ALL FAILED TO STOP
ONE TYPO. `pipeline_idf2_train.sh` called a subcommand that does not exist; the
run trained two adapters, took eighteen reads, and died on that line with ~7
GPU-h of weights on a box and nothing in durable storage.

⭐⭐ SO THE GATE IS NOT ANOTHER RULE. It is a RECEIPT: every command a pipeline
will run is checked on CPU first, the results are written to a file carrying the
**git sha they were checked at**, and the launcher refuses to start without a
receipt for the sha it is about to ship. Edit the pipeline, the sha moves, the
receipt is stale, the launch aborts.

⛔ WHAT IT CHECKS IS EXISTENCE, NOT BEHAVIOUR. Every `tools/*.py` invocation in
the script is parsed and its subcommand and required flags are validated against
that tool's own argparse, with `--help`, executing nothing. That is exactly the
class the typo lived in, and it is cheap enough to be unskippable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shlex
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
RECEIPTS = ROOT / "runs" / "act2" / "_receipts"

_VAR = re.compile(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|\$\([^)]*\)")
_QUOTE = re.compile(r"[\"']")


def git_sha() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT),
                          capture_output=True, text=True).stdout.strip()


def invocations(script: pathlib.Path):
    """-> [(tool, argv), …] for every `tools/*.py` call in the script.

    ⛔ CRLF-normalised and continuation-joined FIRST. A checker that misses
    `\\`-continued lines silently checks nothing, which is worse than absent.

    ⛔⛤ AND IT FOLLOWS `pipeline_lib.sh`, WHICH THE FIRST VERSION DID NOT.
    Moving the persist command into the shared helper — the fix for the typo —
    moved it OUT OF THIS CHECKER'S VIEW, so the one invocation that cost two
    adapters became the one invocation the receipt no longer covered. A gate
    that stops seeing what it was built for is worse than no gate.
    """
    text = script.read_text(encoding="utf-8").replace("\r\n", "\n")
    if "pipeline_lib.sh" in text:
        lib = script.parent / "pipeline_lib.sh"
        if lib.exists():
            text += "\n" + lib.read_text(encoding="utf-8").replace("\r\n", "\n")
    joined = text.replace("\\\n", " ")
    out = []
    for line in joined.splitlines():
        s = line.lstrip()
        if s.startswith(("#", "echo")):
            continue
        for m in re.finditer(r"tools/(act2_[a-z0-9_]+\.py|lock_prereg\.py)",
                             line):
            tool = m.group(1)
            frag = line[m.end():].split("2>&1")[0].split("|")[0]
            try:
                argv = shlex.split(_VAR.sub("X", _QUOTE.sub("", frag)))
            except ValueError:
                continue
            out.append((tool, argv))
    return out


def declared_subcommands(tool_src: str) -> set[str]:
    """-> the subcommands a tool declares, read from its own source."""
    return set(re.findall(r'add_parser\(\s*"([a-z0-9-]+)"', tool_src))


def check_one(tool: str, argv: list[str]) -> tuple[bool, str]:
    """-> (ok, detail). Validates shape against the tool's OWN argparse.

    ⛔⛤ THE SUBCOMMAND IS FOUND BY MEMBERSHIP, NEVER BY POSITION. Taking "the
    first bare word" picks a FLAG VALUE — `--root X --repo X cell …` starts
    with two of them — so every call through the shared helper reported the
    unknown subcommand `X` and the gate failed on correct code. That mistake
    has now been made three times in one day, in the test, in the extractor and
    here; the shape is always the same, and the fix is always to ask "which of
    the declared names is present" instead of "what came first".
    """
    p = TOOLS / tool
    if not p.exists():
        return False, "no such tool: tools/%s" % tool
    src = p.read_text(encoding="utf-8")
    # ⛔ NOT EVERY TOOL USES argparse. `lock_prereg.py` reads `sys.argv`
    # directly and treats its first token as a PATH, so probing it with
    # `--help` produced `FileNotFoundError: '--help'` — the gate reporting a
    # defect it had invented, which is the failure mode that has already cost
    # this checker two rewrites. For those, existence is all this step can
    # honestly assert, and it says so rather than manufacturing a verdict.
    if "argparse" not in src:
        return True, "%s (no argparse — existence only)" % tool
    declared = declared_subcommands(src)
    probe = [sys.executable, str(p)]
    named = [a for a in argv if a in declared]
    if declared:
        if not named:
            return False, ("%s declares subcommands %s and this call names "
                           "none: %r" % (tool, sorted(declared), argv))
        probe.append(named[0])
    # ⭐ `--help` on the named subcommand is what proves it exists. argparse
    # exits 0 for a valid one and 2 for an unknown one, and nothing in the
    # tool's body runs.
    probe.append("--help")
    # ⛔ utf-8 with replacement: these tools print glyphs cp1252 cannot
    # decode, and the reader thread raised inside subprocess itself.
    r = subprocess.run(probe, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(ROOT))
    if r.returncode != 0:
        first = (r.stderr or r.stdout or "").strip().splitlines()[-1:] or [""]
        return False, "%s %s --help -> rc=%d: %s" % (
            tool, named[0] if named else "", r.returncode, first[0][:160])
    # Required flags: argparse names them in its own error text when missing,
    # so the cheapest faithful check is the tool's own usage line.
    return True, "%s %s" % (tool, named[0] if named else "")


def receipt_path(pipeline: str) -> pathlib.Path:
    return RECEIPTS / ("%s.receipt.json" % pipeline)


def cmd_write(a):
    script = TOOLS / a.pipeline
    if not script.exists():
        raise SystemExit("⛔ no such pipeline: %s" % script)
    sha = git_sha()
    calls = invocations(script)
    rows, bad = [], 0
    print("SMOKE — %s at %s" % (a.pipeline, sha[:12]))
    for tool, argv in calls:
        ok, detail = check_one(tool, argv)
        rows.append({"tool": tool, "argv": argv, "ok": ok, "detail": detail})
        if not ok:
            bad += 1
            print("  ⛔ %s" % detail)
        else:
            print("  ✅ %s" % detail)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    body = {"pipeline": a.pipeline, "git_sha": sha,
            "script_sha256": hashlib.sha256(
                script.read_bytes()).hexdigest(),
            "checks": rows, "n_checks": len(rows), "n_failed": bad,
            "verdict": "PASS" if bad == 0 else "FAIL"}
    receipt_path(a.pipeline).write_text(json.dumps(body, indent=2),
                                        encoding="utf-8")
    print("\n  %d checks, %d failed -> %s" % (len(rows), bad, body["verdict"]))
    print("  wrote %s" % receipt_path(a.pipeline))
    # ⛔ A FAILING SMOKE STILL WRITES ITS RECEIPT, so `check` can say WHY rather
    # than "missing". A receipt that only exists when it passes is a receipt
    # that can be created by deleting evidence.
    return 0 if bad == 0 else 2


def cmd_check(a):
    """The launcher's gate. ⛔ Refuses on missing, stale or failing."""
    p = receipt_path(a.pipeline)
    if not p.exists():
        raise SystemExit(
            "⛔⛔ NO SMOKE RECEIPT for %s. Run:\n"
            "    python tools/act2_smoke_receipt.py write --pipeline %s\n"
            "A GPU launch without one is how `persist --cells` reached a box."
            % (a.pipeline, a.pipeline))
    r = json.loads(p.read_text(encoding="utf-8"))
    sha = git_sha()
    if r.get("git_sha") != sha:
        raise SystemExit(
            "⛔⛔ STALE RECEIPT: checked at %s, HEAD is %s. The pipeline may "
            "have changed since it was proved. Re-run `write`."
            % (str(r.get("git_sha"))[:12], sha[:12]))
    script = TOOLS / a.pipeline
    now = hashlib.sha256(script.read_bytes()).hexdigest()
    if r.get("script_sha256") != now:
        raise SystemExit(
            "⛔⛔ THE SCRIPT CHANGED since its receipt, even at the same commit "
            "(uncommitted edit). Re-run `write`.")
    if r.get("verdict") != "PASS":
        raise SystemExit(
            "⛔⛔ RECEIPT SAYS FAIL — %d of %d checks did not pass:\n%s"
            % (r["n_failed"], r["n_checks"],
               "\n".join("    " + c["detail"] for c in r["checks"]
                         if not c["ok"])))
    print("✅ smoke receipt OK — %s, %d checks, sha %s"
          % (a.pipeline, r["n_checks"], sha[:12]))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("write", cmd_write), ("check", cmd_check)):
        q = sub.add_parser(name)
        q.add_argument("--pipeline", required=True)
        q.set_defaults(fn=fn)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
