#!/usr/bin/env python
"""⭐⭐ ASSERT THE READINGS A RUN PRODUCED — NOT THE CONFIG THAT WAS SUPPOSED TO
PRODUCE THEM.

⛔⛔ THIS TOOL EXISTS BECAUSE 1,988 GREEN TESTS MISSED FOUR BUGS IN ONE RUN.
`epochlevB-s20624`, 2026-09-16: the run trained 3,760 clean steps and then

  1. died at `persist_leg1` on a `flush --cell` that `flush` does not accept,
     losing every end-of-run read;
  2. failed to terminate, because the watchdog's id lookup read a file that does
     not exist on the image — while its own arm-time preflight reported
     "terminate path verified" for a path it had never travelled;
  3. flushed with a NON-RECURSIVE glob, so `weight_delta*.json` and
     `factorial.json` — both listed in `FLUSH_PATTERNS`, both written one
     directory down — swept ZERO files and said nothing about it;
  4. recorded its whole in-training lag curve through an F-LOCAL backend at
     temperature 0.0, i.e. GREEDY, which measures the decoder's determinism
     rather than whether content persists — voiding the curve.

Every one of those was green at the level of configuration. The declaration was
right; the wiring was wrong; and no test asked the only question that separates
them: **what did the run actually write, and does it carry the settings the
measurement requires?**

⭐ So this runs AFTER a run, against its files, and it asks exactly that:

  A. every FLUSH_PATTERN matched at least one real file under the run root
     (catches 1 and 3 — a broken persist call and a glob that sweeps nothing
     both look identical from here: no file);
  B. every lag reading carries the decoder it was taken with, and that decoder
     is the SAMPLED one a lag read requires (catches 4).

⛔ It reads artefacts, never prose, and never a summary field: the numbers come
out of the JSON the instrument wrote.

exit 0 = every reading present and correctly configured
exit 1 = something is missing or was measured with the wrong instrument
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from act2_box_persist import (FLUSH_PATTERNS,                  # noqa: E402
                              flush_candidates)
from act2_model_lag import (LAG_MAX_NEW_TOKENS,                # noqa: E402
                            LAG_TEMPERATURE)

#: ⛔ Patterns a correct run may legitimately not produce. `vocab_coverage` and
#: `mapping_moved` are MAPPING-scope gates; a layer rung that wrote them would
#: be the bug (`lint_step_scope.py` enforces the pairing). `step_match_*` exists
#: only on a two-arm run. Everything NOT listed here is required, because a
#: missing reading is the failure mode this tool is for.
SCOPE_CONDITIONAL = {
    "vocab_coverage.json",
    "mapping_moved.json",
    "step_match_*.json",
}


def sweep(root: pathlib.Path) -> dict:
    """-> {pattern: [relative paths]}, from the flush's OWN sweep.

    ⛔⛔ THIS USED TO RE-SPELL THE SWEEP, and a re-spelling is the bug this
    whole arc is about: the audit would then certify a sweep that is not the
    one that runs. It had `rglob` because the flush had `rglob`, held in step
    by a source-level assertion — a guard keeping two copies honest instead of
    there being one copy.

    ⭐ Now it delegates. `flush_candidates` is the single definition of "what a
    run measures", shared by the flush that pushes the files, the
    `verify --readings` gate that certifies they arrived, and this audit.
    """
    found, _ = flush_candidates(root)
    rels = [p.relative_to(root).as_posix() for p in found if p.exists()]
    out = {}
    for pat in FLUSH_PATTERNS:
        out[pat] = sorted(r for r in rels
                          if fnmatch.fnmatch(pathlib.PurePosixPath(r).name, pat))
    return out


def lag_rows(root: pathlib.Path) -> list[tuple[str, dict]]:
    """Every lag reading the run wrote, from BOTH shapes it is written in.

    ⛔⛔ Both, always. The standalone `model_lag_*.json` readings were correct
    and the in-training `dose_curve_*.jsonl` rows were not, so a check that
    looked at only one shape would have passed this run — the CLI files carried
    their decoder and were right, and the curve rows carried nothing and were
    wrong. Auditing the shape that happens to be fine is not an audit.
    """
    out = []
    for p in sorted(root.rglob("model_lag_*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:                                 # noqa: BLE001
            out.append((p.name, {"_unreadable": "%s: %s" % (type(e).__name__, e)}))
            continue
        if isinstance(d, dict):
            out.append((p.name, d))
    for p in sorted(root.rglob("dose_curve_*.jsonl")):
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:                                  # noqa: BLE001
                continue
            lag = row.get("lag")
            if isinstance(lag, dict):
                out.append(("%s:%d (step %s)" % (p.name, i, row.get("step")),
                            lag))
    return out


def audit(root: pathlib.Path) -> tuple[int, list[str]]:
    """-> (failures, lines to print)."""
    lines, bad = [], 0

    lines.append("A · FLUSH PATTERNS — did each one match a real file?")
    hits = sweep(root)
    for pattern in FLUSH_PATTERNS:
        got = hits[pattern]
        if got:
            lines.append("    ✅ %-22s %d file(s): %s"
                         % (pattern, len(got), ", ".join(got[:3])
                            + (" …" if len(got) > 3 else "")))
        elif pattern in SCOPE_CONDITIONAL:
            lines.append("    ⓘ  %-22s no match — scope-conditional, allowed"
                         % pattern)
        else:
            bad += 1
            lines.append("    ⛔ %-22s MATCHED NOTHING. Either the run never "
                         "wrote it, or the persist step that should have died "
                         "trying." % pattern)

    lines.append("")
    lines.append("B · LAG READINGS — does each carry the decoder it was taken "
                 "with, and is that decoder SAMPLED?")
    rows = lag_rows(root)
    if not rows:
        bad += 1
        lines.append("    ⛔ NO LAG READING FOUND AT ALL. A release run with no "
                     "lag row has no result; an audit that passes on an empty "
                     "set is the failure it is meant to catch.")
    for name, row in rows:
        if "_unreadable" in row:
            bad += 1
            lines.append("    ⛔ %-42s unreadable: %s" % (name, row["_unreadable"]))
            continue
        t = row.get("temperature")
        n = row.get("max_new_tokens")
        if t is None or n is None:
            bad += 1
            lines.append(
                "    ⛔ %-42s NO DECODER RECORDED (temperature=%r, "
                "max_new_tokens=%r). The reading cannot be checked, which "
                "means it cannot be trusted — this is the exact state every "
                "in-training row was in while they were all wrong."
                % (name, t, n))
            continue
        if not t or t <= 0:
            bad += 1
            lines.append(
                "    ⛔ %-42s GREEDY (temperature=%r). A deterministic speaker "
                "repeats content because the same context yields the same "
                "continuation; this row measures the decoder, not persistence."
                % (name, t))
            continue
        if t != LAG_TEMPERATURE or n != LAG_MAX_NEW_TOKENS:
            bad += 1
            lines.append(
                "    ⛔ %-42s decoder %s/%s != the lag read's %s/%s — readings "
                "taken at different decoders are not comparable to each other "
                "or to the campaign."
                % (name, t, n, LAG_TEMPERATURE, LAG_MAX_NEW_TOKENS))
            continue
        lines.append("    ✅ %-42s T=%s tok=%s" % (name, t, n))
    return bad, lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True,
                    help="a run directory, e.g. runs/act2/fullft_<cell>")
    a = ap.parse_args()
    root = pathlib.Path(a.root)
    if not root.is_dir():
        print("⛔ %s is not a directory" % root, file=sys.stderr)
        return 2
    print("READINGS AUDIT · %s" % root)
    print("⛔ asserts what the run WROTE, not what it was configured to write")
    print()
    bad, lines = audit(root)
    print("\n".join(lines))
    print()
    if bad:
        print("⛔⛔ %d PROBLEM(S). This run's record is incomplete or was taken "
              "with the wrong instrument." % bad)
        return 1
    print("✅ every reading present, every lag row sampled at %s/%s."
          % (LAG_TEMPERATURE, LAG_MAX_NEW_TOKENS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
