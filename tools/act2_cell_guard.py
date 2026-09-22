"""⛔⛔ REFUSE TO PERSIST ONTO ANOTHER RUN'S CELL. The guard whose absence lost
the render-98.4% adapter.

`pipeline_puzzle.sh` defaulted `CELL=bench-s20624`. On 2026-09-22 a second run
took that default, trained a DIFFERENT model, and its persist wrote over the
first run's weights in durable storage. Nothing in either run said so. It was
recoverable — a local pull existed and the hub keeps the prior revision — but
by luck, not by design, and the next collision might land on a cell with
neither.

⭐ THE LESSON IS NOT "PASS `CELL=`". A fixed default cell name is a data-loss
trap that arms itself on every run, and the only thing between two runs and one
overwritten adapter was somebody remembering. Remembering is an instruction;
this is a guard. Deny by default, allow only when the overwrite is SAID.

⛔ THE DECISION IS A PURE FUNCTION so it can be red-proofed without a network.
A guard that has only ever been observed passing is unexecuted code standing
between you and a permanent loss — the same argument `test_provision` makes
about the transfer checksum.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

OK = "OK"
WARN = "WARN"
REFUSE = "REFUSE"


def decide(cell: str, repo_files, allow: bool) -> tuple[str, str]:
    """-> (verdict, message). Pure; unit-tested.

    ⛔ The match is on the `cell + "/"` PREFIX, not on `startswith(cell)`. A
    bare prefix test makes `bench-s2` collide with `bench-s20624` and, worse,
    lets `bench-s20624` look FREE when only `bench-s20624x/` exists. The cell is
    a directory in the repo; the separator is part of its identity.
    """
    if not cell:
        return REFUSE, ("CELL IS REQUIRED AND HAS NO DEFAULT. Name the cell "
                        "this run persists to — a fixed default is what "
                        "overwrote bench-s20624.")
    hit = sorted(f for f in repo_files if f.startswith(cell + "/"))
    if hit and not allow:
        return REFUSE, (
            "CELL %r ALREADY EXISTS (%d files). Persisting would overwrite "
            "another run's weights in durable storage — which is how the "
            "render-98.4%% adapter was lost. Pick a new cell name, or set "
            "ALLOW_CELL_OVERWRITE=1 if replacing it is the intent.\n  %s"
            % (cell, len(hit), "\n  ".join(hit[:6])))
    if hit:
        return WARN, ("cell %s exists and ALLOW_CELL_OVERWRITE is set — "
                      "overwriting %d files ON PURPOSE" % (cell, len(hit)))
    return OK, "cell %s is free" % cell


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cell", default=os.environ.get("CELL", ""))
    ap.add_argument("--repo", default=os.environ.get("HF_REPO", ""))
    a = ap.parse_args()
    if not a.repo:
        raise SystemExit("⛔ --repo / HF_REPO is required")

    # ⛔ Imported here, not at module scope: the pure decision above must be
    # testable on a machine with no hub credentials and no network.
    from act2_provision import _hf_token
    from huggingface_hub import HfApi

    files = HfApi(token=_hf_token()).list_repo_files(a.repo, repo_type="model")
    verdict, msg = decide(a.cell, files,
                          bool(os.environ.get("ALLOW_CELL_OVERWRITE", "")))
    if verdict == REFUSE:
        raise SystemExit("⛔⛔ %s" % msg)
    print("  %s %s" % ("⚠" if verdict == WARN else "✅", msg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
