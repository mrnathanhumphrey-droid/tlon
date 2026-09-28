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


def inputs_sha(script: pathlib.Path, calls) -> str:
    """A hash of EVERY file this receipt's verdict depends on.

    ⛔⛤ THE RECEIPT CANNOT BE GATED ON `HEAD`, AND FINDING OUT WHY TOOK A
    ROUND TRIP: the receipt has to be committed so the box can read it, and
    committing it MOVES HEAD — so a receipt written at the sha it checked is
    stale the instant it is stored. A gate that invalidates itself on being
    saved is not a gate.

    ⭐ SO THE IDENTITY IS THE INPUTS, NOT THE COMMIT: the pipeline, the shared
    library it sources, and every tool whose argparse was consulted. That is
    strictly better than a git sha — invariant to commits that touch nothing
    here, and sensitive to an UNCOMMITTED edit to any of them, which a sha
    comparison would miss entirely.

    ⛔⛤ LINE ENDINGS ARE NORMALISED, AND THE GATE CAUGHT ITSELF ON THIS. The
    receipt is written on Windows, where the repo checks out CRLF, and verified
    on a Linux box, where it checks out LF — so the identical files hashed
    differently and the run refused for a difference that means nothing. The
    refusal was correct behaviour on a wrong input; a gate this strict has to
    compare CONTENT rather than bytes-as-stored, or it is unusable across the
    only two machines this project runs on.
    """
    h = hashlib.sha256()
    for f in [script, script.parent / "pipeline_lib.sh"] + sorted(
            {TOOLS / t for t, _ in calls}):
        h.update(f.name.encode())
        body = f.read_bytes() if f.exists() else b"<missing>"
        h.update(body.replace(b"\r\n", b"\n"))
    return h.hexdigest()


def check_persist_preconditions() -> tuple[bool, str]:
    """Would `persist_cell` actually accept a cell this pipeline produces?

    ⛔⛤ THE RECEIPT PROVED THE COMMAND EXISTED AND THE RUN STILL DIED ON IT.
    `act2_box_persist.py cell --cell X --solo-n 0 --corpus-manifest Y` parses
    perfectly; `persist_cell` then refuses at RUN TIME unless the adapter
    directory holds every one of `CELL_FILES` — and `factorial.json` was not
    among what the pipeline wrote. M trained for 3.7 GPU-h, cleared F-LOCAL,
    passed the dose gate, and was refused with the weights nowhere else.

    ⭐ SO THE GATE GREW A SECOND QUESTION. "Does the command parse?" is not
    "will the command succeed?", and the second one is the one that costs
    GPU-hours. This builds a fake cell in a temp directory, omits each required
    file in turn, and asserts the refusal — proving the precondition list this
    check reads is the one `persist_cell` enforces, rather than a copy of it.
    """
    import tempfile
    sys.path.insert(0, str(TOOLS))
    try:
        import act2_box_persist as BP
    except Exception as exc:                                # pragma: no cover
        return False, "cannot import act2_box_persist: %s" % exc

    required = list(BP.CELL_FILES)
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        d = root / "adapter_probe"
        d.mkdir(parents=True)
        for f in required:
            (d / f).write_text("{}", encoding="utf-8")
        missing = BP.missing_cell_files(root, "probe")
        if missing:
            return False, ("a complete cell still reports missing %s — the "
                           "required set is not what this check builds"
                           % missing)
        # ⛔ And each one really is required: drop it and the refusal must name
        # it. A precondition list that is not enforced is documentation.
        for f in required:
            (d / f).unlink()
            if f not in (BP.missing_cell_files(root, "probe") or []):
                return False, ("%s is in CELL_FILES but its absence is not "
                               "detected — the guard is advisory" % f)
            (d / f).write_text("{}", encoding="utf-8")
    return True, "persist_cell preconditions: %s" % ", ".join(required)


def check_pipeline_writes_cell_files(script: pathlib.Path) -> tuple[bool, str]:
    """Does the pipeline actually PRODUCE every file persist will demand?

    ⛔ `adapter_model.safetensors` and `adapter_config.json` come from the
    trainer; `factorial.json` does not, and that is the one that was missing.
    """
    sys.path.insert(0, str(TOOLS))
    import act2_box_persist as BP
    text = script.read_text(encoding="utf-8")
    from_trainer = {"adapter_model.safetensors", "adapter_config.json"}
    owed = [f for f in BP.CELL_FILES if f not in from_trainer]
    absent = [f for f in owed if f not in text]
    if absent:
        return False, ("the pipeline persists cells but never writes %s — "
                       "persist_cell will refuse after the GPU time is spent"
                       % ", ".join(absent))
    return True, "pipeline writes the non-trainer cell files: %s" % ", ".join(owed)


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
    # ⛔⛤ THE SECOND CLASS OF CHECK, ADDED AFTER THE FIRST ONE PASSED AND THE
    # RUN DIED ANYWAY. Commands that parse can still fail on preconditions, and
    # a precondition failure lands AFTER the GPU-hours that produced the thing
    # it refuses.
    if any(t == "act2_box_persist.py" and "cell" in argv for t, argv in calls):
        for fn in (check_persist_preconditions,
                   lambda: check_pipeline_writes_cell_files(script)):
            ok, detail = fn()
            rows.append({"tool": "precondition", "argv": [], "ok": ok,
                         "detail": detail})
            print(("  ✅ %s" if ok else "  ⛔ %s") % detail)
            if not ok:
                bad += 1
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    body = {"pipeline": a.pipeline,
            # ⭐ Recorded for PROVENANCE — which commit this was proved at —
            # but NOT what the gate compares; see `inputs_sha`.
            "git_sha_at_write": sha,
            "inputs_sha256": inputs_sha(script, calls),
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
    script = TOOLS / a.pipeline
    now = inputs_sha(script, invocations(script))
    if r.get("inputs_sha256") != now:
        raise SystemExit(
            "⛔⛔ STALE RECEIPT. The pipeline, its shared library, or one of "
            "the tools it calls has changed since this was proved.\n"
            "    receipt %s\n    now     %s\n"
            "Re-run `write`. ⭐ This compares the FILES, not the commit, so it "
            "also catches an uncommitted edit."
            % (str(r.get("inputs_sha256"))[:16], now[:16]))
    if r.get("verdict") != "PASS":
        raise SystemExit(
            "⛔⛔ RECEIPT SAYS FAIL — %d of %d checks did not pass:\n%s"
            % (r["n_failed"], r["n_checks"],
               "\n".join("    " + c["detail"] for c in r["checks"]
                         if not c["ok"])))
    print("✅ smoke receipt OK — %s, %d checks, inputs %s (proved at %s)"
          % (a.pipeline, r["n_checks"], now[:12],
             str(r.get("git_sha_at_write"))[:12]))
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
