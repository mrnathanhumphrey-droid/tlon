"""IDF-2 — prove M's and C1's corpora differ ONLY by the marker line.

`docs/PREREG_IDF2_2026_09_26.md`, LOCK `37363296` §2.

    python tools/act2_idf2_corpus_diff.py --marked <dir> --unmarked <dir> \
        --out corpus_diff.json

⛔⛔ THE ESTIMAND DEPENDS ON THIS AND NOTHING ELSE CHECKS IT. `closes(M) −
closes(C1)` is the marker's effect only if the two corpora are otherwise the
same corpus. They are produced by two SEPARATE invocations of a generator that
draws from its own RNG, so "same seed, same chains" is a claim about determinism
— and this campaign has already been bitten by a build whose force stream
diverged between arms at a fixed seed because one path consumed randomness the
other did not.

⭐ So the check is on the FILES, row by row: every non-provoke row byte-identical,
every provoke row identical once the marker line is stripped, and the marker
present in exactly one of them. A shared seed is not evidence; a diff is.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.discourse import transient as TR      # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def _rows(d: pathlib.Path):
    out = []
    for name in ("train.jsonl", "eval.jsonl"):
        p = d / name
        if p.exists():
            out += [(name, i, json.loads(l)) for i, l in
                    enumerate(p.read_text(encoding="utf-8").splitlines())]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--marked", required=True)
    ap.add_argument("--unmarked", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    M, C = _rows(pathlib.Path(a.marked)), _rows(pathlib.Path(a.unmarked))
    print("  marked rows    %d" % len(M))
    print("  unmarked rows  %d" % len(C))
    if len(M) != len(C):
        raise SystemExit(
            "⛔⛔ ROW COUNT DIFFERS: %d vs %d. The two corpora are not the same "
            "corpus, so their difference is not the marker." % (len(M), len(C)))

    bad, marked_provoke, unmarked_provoke, other = [], 0, 0, 0
    for (fm, im, rm), (fc, ic, rc) in zip(M, C):
        if (fm, im) != (fc, ic):
            bad.append((im, "row alignment diverged"))
            continue
        if rm.get("direction") != rc.get("direction"):
            bad.append((im, "direction differs"))
            continue
        if rm.get("direction") != "provoke":
            # ⛔ Non-provoke rows carry no marker in either arm, so they must be
            # byte-identical. A difference here is a corpus difference.
            if rm != rc:
                bad.append((im, "non-provoke row differs"))
            other += 1
            continue
        pm, pc = rm.get("prompt", ""), rc.get("prompt", "")
        if TR.MARKER_PREFIX not in pm:
            bad.append((im, "marked arm's provoke row has NO marker"))
            continue
        if TR.MARKER_PREFIX in pc:
            bad.append((im, "unmarked arm's provoke row HAS a marker"))
            continue
        marked_provoke += 1
        unmarked_provoke += 1
        # ⭐ Strip exactly the marker line and everything must match — including
        # the target surface, the scene and both forces.
        stripped = dict(rm, prompt=pm.split("\n")[0])
        if stripped != rc:
            keys = [k for k in set(stripped) | set(rc)
                    if stripped.get(k) != rc.get(k)]
            bad.append((im, "differs beyond the marker in %s" % keys))

    print("  provoke rows   %d marked / %d unmarked" % (marked_provoke,
                                                        unmarked_provoke))
    print("  other rows     %d byte-identical" % other)
    print("  mismatches     %d" % len(bad))
    for i, why in bad[:5]:
        print("    row %d: %s" % (i, why))

    rep = {"prereg": "docs/PREREG_IDF2_2026_09_26.md", "LOCK": "37363296",
           "marked": a.marked, "unmarked": a.unmarked,
           "rows": len(M), "provoke_rows": marked_provoke,
           "other_rows_identical": other, "mismatches": len(bad),
           "verdict": "MARKER-ONLY" if not bad else "DIVERGED"}
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(rep, indent=2),
                                       encoding="utf-8")
        print("  wrote %s" % a.out)
    if bad:
        raise SystemExit(
            "\n⛔⛔ THE TWO CORPORA DIFFER BEYOND THE MARKER (%d rows). "
            "`closes(M) − closes(C1)` would be the marker's effect PLUS "
            "whatever else moved, and nothing downstream could separate them. "
            "STOP." % len(bad))
    print("  ✅ MARKER-ONLY — the difference is the annotation line and "
          "nothing else")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
