"""PAIRED comparison of two F-LOCAL runs from the ledger. $0.00, offline.

⛔⛔ THE PAIRING EXISTED AND WAS THROWN AWAY AT WRITE TIME. The comprehension
battery is byte-identical across runs, so the items ARE paired -- but the ledger
stored only the ACCURACY, so the only test available was the unpaired one, and
baseline 39.1 % vs tuned 51.6 % read **p = 0.21** at n = 64 and could not be
resolved either way. **You cannot recover pairing you did not record.**

⭐ With per-item outcomes ledgered, McNemar becomes available: it discards the
items both runs agree on -- they say nothing about a DIFFERENCE -- and tests only
the discordant pairs, which is where the power the unpaired test cannot reach
comes from.

    python tools/act2_compare.py                       # last baseline vs last tuned
    python tools/act2_compare.py --ledger <path>
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

from tlon.harness import paired as P                           # noqa: E402


def _items(entry: dict) -> dict:
    raw = entry.get("comprehension_items") or {}
    return {k: bool(v["correct"]) for k, v in raw.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default="runs/act2/ledger.jsonl")
    a = ap.parse_args()

    path = pathlib.Path(a.ledger)
    entries = [json.loads(l) for l in
               path.read_text(encoding="utf-8").splitlines()]
    runs = [e for e in entries if e.get("event") == "f_local"]
    base = [e for e in runs if not e.get("adapter")]
    tuned = [e for e in runs if e.get("adapter")]
    if not base or not tuned:
        raise SystemExit("⛔ need one baseline and one adapter run in the ledger")
    b, t = base[-1], tuned[-1]

    bi, ti = _items(b), _items(t)
    print(f"PAIRED COMPARISON · battery {b.get('battery')} vs {t.get('battery')}")
    print(f"  baseline  comprehension {b['comprehension']:.1%}  "
          f"(per-item recorded: {len(bi)})")
    print(f"  tuned     comprehension {t['comprehension']:.1%}  "
          f"(per-item recorded: {len(ti)})")

    if not bi or not ti:
        # ⛔ SAY WHICH RUN IS MISSING THE DATA. "cannot compare" without the
        # reason is how an instrument gap gets mistaken for a null result.
        missing = [n for n, d in (("baseline", bi), ("tuned", ti)) if not d]
        print(f"\n  ⛔⛔ NO PAIRED TEST AVAILABLE — {', '.join(missing)} has no "
              "per-item outcomes. Runs recorded before per-item logging cannot "
              "be paired retroactively; only runs from here on can.")
        return 0

    if b.get("battery") != t.get("battery"):
        print("\n  ⚠️ different battery digests — comparing the SHARED items only")

    shared = set(bi) & set(ti)
    m = P.mcnemar({k: bi[k] for k in shared}, {k: ti[k] for k in shared})
    print(f"\n  McNEMAR on {m.n} paired items")
    print(f"    baseline right / tuned wrong : {m.b}")
    print(f"    baseline wrong / tuned right : {m.c}")
    print(f"    both agree (carry no signal) : {m.concordant}")
    print(f"\n  ⇒ {m.verdict()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
