"""PHASE 11 red-check: is any referent traceable to source EXPRESSION?

THE PRECONDITION IT AUDITS. Phase 11's sets must carry philosophical POSITIONS
(ideas, free) and not source LANGUAGE (expression, walled). Nate distilled the
positions in his own words in the brief; the compilation step consulted no text
at all, so no expression was ever ingested. This tool checks that the artefact
on disk is consistent with that claim rather than taking it on trust.

⛔ WHAT A WEAK VERSION OF THIS WOULD BE. "Grep the notes for quotation marks"
is satisfied by a file that simply never uses them, and would pass on a set
built entirely of paraphrased lines. A guard that a report can satisfy by
naming what it lacks is not a guard.

SO THE REAL CHECK IS TRACEABILITY, POSITIVELY: every referent must declare
which distilled position it derives from, and every declared position must be
one the brief actually listed. A referent that cannot name its position is one
whose provenance is unaccounted for -- which is the only way expression could
have entered. That is checkable, and it fails loudly.

Secondary checks are cheap and included: quoted spans, and names long enough to
be a line rather than a description of an impression.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.referents import schema                            # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"

# The positions Nate wrote in the Phase 11 brief. Nothing may cite a position
# that is not on this list -- an invented position is unaccounted provenance.
POSITIONS = {
    "cr": {
        "P1": "knowledge-of-self / continuous self-creation",
        "P2": "the cipher as collective meaning-making-in-motion",
        "P3": "identity-as-enacted-not-possessed",
        "P4": "the word as world-building act",
        "P5": "meaning-collapse-as-operation (identity as operation, not noun)",
    },
    "tao": {
        "P1": "the uncarved block",
        "P2": "water taking every shape",
        "P3": "named vs unnamed",
        "P4": "wu wei",
        "P5": "dissolution of object-boundaries",
    },
}

# ⛔ `P([1-5])` was the first version and it is a NARROWER CHECK than the thing
# it must match: "P9" simply failed to match, so an invented position was
# reported as "cites no position" -- right verdict, wrong reason -- and a note
# reading "P1. P9." would have cited P1 and hidden the P9 entirely. Match any
# P<digits> and validate afterwards, so an invented position is SEEN.
CITE = re.compile(r"\bP(\d+)\b")
QUOTED = re.compile(r"[\"“”‘’]([^\"“”]{12,})")
MAX_NAME_WORDS = 12          # a description of an impression, not a line


def audit(setname: str) -> dict:
    rs = schema.load_worldview(setname, allow_unreviewed=True)
    valid = set(POSITIONS[setname])
    rows, fails = [], []
    cited_any = {p: 0 for p in valid}

    for r in rs.referents:
        note = r.notes or ""
        cites = sorted({f"P{m}" for m in CITE.findall(note)})
        row = {"id": r.id, "name": r.name, "positions": cites}
        rows.append(row)

        if not cites:
            fails.append(f"{r.id}: cites NO position -- provenance unaccounted")
        for c in cites:
            if c not in valid:
                fails.append(f"{r.id}: cites {c}, which the brief did not list")
            else:
                cited_any[c] += 1

        q = QUOTED.search(note) or QUOTED.search(r.name)
        if q:
            fails.append(f"{r.id}: quoted span {q.group(1)[:40]!r}")

        nw = len(r.name.split())
        row["name_words"] = nw
        if nw > MAX_NAME_WORDS:
            fails.append(f"{r.id}: name is {nw} words -- reads as a line, "
                         "not a description of an impression")

    unused = [p for p, n in cited_any.items() if n == 0]
    return {"set": setname, "n": len(rs.referents), "rows": rows,
            "per_position": cited_any, "positions_unused": unused,
            "failures": fails}


def main() -> int:
    print("=" * 78)
    print("PHASE 11 EXPRESSION-STRIP RED-CHECK")
    print("=" * 78)
    print("  Source text consulted at compilation: NONE. Both sets were built")
    print("  only from the distilled positions in Nate's brief. This audits the")
    print("  artefact against that claim instead of trusting it.\n")

    out, bad = {}, 0
    for setname in ("cr", "tao"):
        a = audit(setname)
        out[setname] = a
        print(f"  {setname.upper()} -- {a['n']} referents")
        for p, label in POSITIONS[setname].items():
            n = a["per_position"][p]
            mark = "ok  " if n else "FAIL"
            print(f"    [{mark}] {p} x{n:<3} {label}")
        longest = max(a["rows"], key=lambda r: r["name_words"])
        print(f"    longest name: {longest['name_words']} words "
              f"(cap {MAX_NAME_WORDS}) -- {longest['name']!r}")
        untraced = [r["id"] for r in a["rows"] if not r["positions"]]
        print(f"    referents citing no position: {len(untraced)} {untraced}")
        if a["failures"]:
            bad += len(a["failures"])
            for f in a["failures"]:
                print(f"    ⛔ {f}")
        print()

    # ---- red-proof: the check must be able to FAIL --------------------------
    print("  RED-PROOF -- can this check report a violation at all?\n")
    probes = [
        ("a referent citing no position",
         {"notes": "An impression with no provenance.", "name": "a thing"}),
        ("an invented position HIDDEN BESIDE A VALID ONE",
         {"notes": "P1. And also P9, which the brief never listed.",
          "name": "a thing"}),
        ("a quoted span in a note",
         {"notes": 'P1. It says "a long remembered phrase of source language".',
          "name": "a thing"}),
        ("a name long enough to be a line",
         {"notes": "P1. Fine.",
          "name": " ".join(["word"] * (MAX_NAME_WORDS + 3))}),
    ]
    fired = 0
    for label, fake in probes:
        f = []
        cites = sorted({f"P{m}" for m in CITE.findall(fake["notes"])})
        if not cites:
            f.append("no position")
        for c in cites:
            if c not in {"P1", "P2", "P3", "P4", "P5"}:
                f.append("invalid position")
        if QUOTED.search(fake["notes"]) or QUOTED.search(fake["name"]):
            f.append("quoted span")
        if len(fake["name"].split()) > MAX_NAME_WORDS:
            f.append("name too long")
        ok = bool(f)
        fired += ok
        print(f"    [{'ok  ' if ok else 'FAIL'}] {label} -> {f or 'MISSED'}")
    if fired != len(probes):
        print("\n  XX RED-PROOF FAILED -- the check cannot detect a violation,")
        print("     so the clean result above means nothing.")
        return 1
    print(f"    ✅ all {len(probes)} probes caught; a clean pass is informative")

    print("\n" + "=" * 78)
    if bad:
        print(f"  ⛔ {bad} EXPRESSION-STRIP FAILURE(S). Re-distil before use.")
        return 1
    print("  ✅ EXPRESSION-STRIP CLEAN. Every referent in both sets traces to a")
    print("     position the brief declared; no quoted spans; no name reads as")
    print("     a line. Combined with 'no source consulted at compilation',")
    print("     nothing here could be reconstructed back to source expression.")
    print("  ⛔ SCOPE: this audits the ARTEFACT. It cannot verify what a human")
    print("     read before writing the brief -- that provenance is Nate's to")
    print("     confirm and keep confirmable, and nothing downstream saw it.")

    OUT.mkdir(exist_ok=True)
    (OUT / "phase11_expression_check.json").write_text(
        json.dumps({"source_consulted_at_compilation": None,
                    "sets": out, "clean": bad == 0},
                   indent=2, ensure_ascii=False),
        encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'phase11_expression_check.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
