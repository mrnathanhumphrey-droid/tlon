"""⛔⛔ THE FORCE GATE, AT THE POINT WHERE THE ROWS ARE ASSEMBLED.

`act2_build_conversations.py` gates each POOL as it is written. That is not
where the training corpus comes from. `pipeline_puzzle.sh` blends two pools on
the box and hands the blend to `act2_build_multiturn_rows.py`, and a blend of
an accepted pool with a `ka`-monoculture pool is a corpus nothing has ever
looked at — the dose can re-dilute exactly the property the rebuild was for.

⭐ A GUARD THAT SITS BESIDE ITS PRODUCER DOES NOT FOLLOW THE ARTEFACT THROUGH A
TRANSFORM. This one is pinned where the CONSUMER reads.

    python tools/act2_force_gate.py runs/act2/corpus_conv_force_dosed/conversations.jsonl

Exit 0 accepted, 1 refused, 2 unreadable. ⛔ Unreadable is NOT a pass: a file
that could not be measured must never exit the same way as one that cleared.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def forces_of(path, voice: str = "T") -> list:
    """Every force the named voice used, in order. ⛔ Raises rather than
    returning [] on an unreadable file — an empty list reads as a measurement
    over nothing, and `force_variety` would refuse it for the wrong reason."""
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    out = []
    lines = 0
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            lines += 1
            for t in json.loads(line).get("turns", []):
                if t.get("voice") == voice:
                    out.append((t.get("scene") or {}).get("force"))
    if not lines:
        raise ValueError("%s has no conversations" % p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("conversations")
    ap.add_argument("--voice", default="T")
    ap.add_argument("--allow-monoculture", action="store_true",
                    help="⛔ reproducing a historical arm ON PURPOSE. It must "
                         "be SAID; there is no default that lets it through.")
    a = ap.parse_args()

    from tlon.act2.carry import ACCEPTANCE, force_variety

    try:
        forces = forces_of(a.conversations, a.voice)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("⛔⛔ FORCE GATE COULD NOT READ %s — %s: %s"
              % (a.conversations, type(exc).__name__, exc))
        print("   Refusing with rc=2. An unmeasured corpus is not a clean one.")
        return 2

    ok, detail, counts = force_variety(forces)
    total = sum(counts.values()) or 1
    print("force gate · %s · voice %s" % (a.conversations, a.voice))
    print("  cap %.0f%% top share · %d distinct minimum"
          % (100 * ACCEPTANCE["force_top_share_max"],
             ACCEPTANCE["force_distinct_min"]))
    for f, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        print("    %-3s %6d  %5.1f%%" % (f, c, 100 * c / total))
    if ok:
        print("  ✅ ACCEPTED — %s" % detail)
        return 0
    if a.allow_monoculture:
        print("  ⚠ REFUSED (%s) but --allow-monoculture was passed. This "
              "corpus teaches a speaker that cannot use the language's other "
              "speech acts, and that is now a recorded choice." % detail)
        return 0
    print("  ⛔⛔ REFUSED — %s" % detail)
    print("     The live bench shipped from a corpus like this one: 99.7% "
          "`ka` in voice T, and every reply on the public page ended in the "
          "same particle. Pass --allow-monoculture only to reproduce a "
          "historical arm on purpose.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
