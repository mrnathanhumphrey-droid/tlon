"""§4.2 — THE CONFIRMATORY DECOMPOSITION. `AMENDMENT A 8f3024fb` §3.

    python tools/act2_decompose.py --logs runs/act2/poscontrol/logs

⛔⛔ THIS TOOL CANNOT DISCRIMINATE COUPLING FROM REGRESSION. It was specified as
if it could, and the algebra says otherwise:

    if each speaker moves a fraction λ toward the store value S, then
        A' = A + λ(S−A),  B' = B + λ(S−B)
    ⇒   |A'−B'| = (1−λ)|A−B|

**Independent store-tracking closes the between-speaker gap by exactly (1−λ),
with no coupling whatsoever.** `force:ka` is a single axis, so there is no
direction orthogonal to the store on which coupling could leave a residual.
Coupling and common-attractor regression are **observationally equivalent from
endpoint positions alone** — not merely hard to separate, but identical.

⇒ **THE MATCHED `SHARED-YOKED` NULL DOES THE DISCRIMINATING.** Both arms carry
the same store-tracking, so it differences out and what survives is coupling.
This module reports the quantities that let a reader *see* the co-movement and
names it when it dominates. **It confirms. It does not decide.**

⭐ The caveat is emitted INSIDE the result dict, not only in this docstring — a
note beside a number separates from it the moment anyone copies the number.
"""
from __future__ import annotations

import argparse
import glob
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

CO_MOVEMENT = "A4 CO-MOVEMENT — both speakers moved together"
CONVERGED = "gap closed without a common shift"
#: ⛔⛔ THE GAP CAN WIDEN, AND CALLING THAT "CLOSED" IS A LABEL CONTRADICTING ITS
#: OWN NUMBER. Caught on the first real run of this tool: rows reading
#: gap_closure = -0.7000 were printed as "gap closed without a common shift".
#: The sign is the meaning; the name has to carry it.
DIVERGED = "gap WIDENED without a common shift"
INCONCLUSIVE = "INCONCLUSIVE — nothing moved enough to read"

#: Below this (in ka units) nothing is called anything. ⛔ Not tuned against a
#: result — it is the §3.1 grid's smallest resolvable step, so a reading can
#: never be finer than the calibration that produced the floor.
MIN_MOVE = 0.0125

CAVEAT = ("This decomposition CANNOT discriminate coupling from regression to a "
          "common attractor: on a single axis, independent store-tracking closes "
          "the gap by (1-lambda) with no coupling at all. The matched "
          "SHARED-YOKED null is what discriminates. These numbers are "
          "confirmatory only.")


def quarters(series, k=4):
    """Split into `k` CONTIGUOUS chunks covering everything.

    ⛔ The remainder goes to the LAST chunks, never dropped: discarding it would
    silently throw away the end of the conversation, which is the half the whole
    measure is about.
    """
    n = len(series)
    if n < k:
        return None
    edges = [round(i * n / k) for i in range(k + 1)]
    return [series[edges[i]:edges[i + 1]] for i in range(k)]


def _default_ka(surfaces):
    from act2_observable_screen import OBSERVABLES, scenes_of
    sc = scenes_of(surfaces)
    return OBSERVABLES["force:ka"](sc) if sc else None


def _own(log, who):
    """⛔ Same exclusion the estimand uses: injected material is not the
    speaker's, and invalid turns never entered the store."""
    return [e["surface"] for e in log
            if e.get("speaker") == who and e.get("valid")
            and not e.get("injected") and e.get("surface") is not None]


def _store(log):
    """Algorithm 1's `C`: everything said, in the order it was said."""
    return [e["surface"] for e in log
            if e.get("valid") and not e.get("injected")
            and e.get("surface") is not None]


def decompose(log, *, ka=_default_ka, k=4):
    """-> the three per-quarter series, the two summary moves, and a reading."""
    a, b, store = _own(log, "A"), _own(log, "B"), _store(log)
    qa, qb, qs = quarters(a, k), quarters(b, k), quarters(store, k)
    blank = {"ka_a": None, "ka_b": None, "ka_store": None,
             "gap_closure": None, "co_movement": None,
             "store_is_cumulative": True, "reading": INCONCLUSIVE,
             "caveat": CAVEAT}
    if not (qa and qb and qs):
        return blank

    ka_a = [ka(q) for q in qa]
    ka_b = [ka(q) for q in qb]
    # ⛔ CUMULATIVE, because the store is append-only: its value at quarter q is
    # everything said UP TO q, not that quarter's turns alone. A per-quarter
    # store would describe a sliding window, which is a different memory model.
    ends = [sum(len(x) for x in qs[:i + 1]) for i in range(k)]
    ka_store = [ka(store[:e]) for e in ends]
    if any(v is None for v in ka_a + ka_b + ka_store):
        return blank

    gap = [abs(x - y) for x, y in zip(ka_a, ka_b)]
    gap_closure = gap[0] - gap[-1]                       # + = closed
    shift_a, shift_b = ka_a[-1] - ka_a[0], ka_b[-1] - ka_b[0]
    co_movement = (shift_a + shift_b) / 2.0              # [A4]

    if abs(co_movement) < MIN_MOVE and abs(gap_closure) < MIN_MOVE:
        reading = INCONCLUSIVE
    elif abs(co_movement) > abs(gap_closure):
        # ⛔ A NAMED OUTCOME, NOT A WEAKENED GO. Both speakers moving the same
        # way is motion, and motion is not coupling.
        reading = CO_MOVEMENT
    elif gap_closure > 0:
        reading = CONVERGED
    else:
        reading = DIVERGED

    return {"ka_a": ka_a, "ka_b": ka_b, "ka_store": ka_store, "gap": gap,
            "gap_closure": gap_closure, "co_movement": co_movement,
            "shift_a": shift_a, "shift_b": shift_b,
            "store_is_cumulative": True, "reading": reading, "caveat": CAVEAT}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", required=True)
    ap.add_argument("--arm", default="shared")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    rows = []
    for f in sorted(glob.glob(str(pathlib.Path(a.logs) / "*.json"))):
        d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        cond = d.get("conditions", {}).get(a.arm)
        if not cond:
            continue
        r = decompose(cond["log"])
        r["file"] = pathlib.Path(f).name
        rows.append(r)

    print("§4.2 CONFIRMATORY DECOMPOSITION — %d transcripts, arm %r"
          % (len(rows), a.arm))
    print("⛔ %s\n" % CAVEAT)
    print("  %-34s %10s %12s  %s" % ("file", "gap close", "co-movement",
                                     "reading"))
    for r in rows:
        if r["gap_closure"] is None:
            print("  %-34s %10s %12s  %s" % (r["file"], "-", "-", r["reading"]))
            continue
        print("  %-34s %+10.4f %+12.4f  %s"
              % (r["file"], r["gap_closure"], r["co_movement"], r["reading"]))

    named = sum(r["reading"] == CO_MOVEMENT for r in rows)
    print("\n  %d of %d transcripts read as %s" % (named, len(rows), CO_MOVEMENT))
    print("  ⛔ This is confirmatory. The GO/STOP verdict comes from the "
          "matched-null estimand, not from this table.")
    if a.out:
        pathlib.Path(a.out).write_text(
            json.dumps({"caveat": CAVEAT, "arm": a.arm, "rows": rows}, indent=2),
            encoding="utf-8")
        print("  wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
