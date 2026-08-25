"""The door. `python tools/chat.py` — arbitrary English in, Tlön out.

⛔ ROUTE A: this SPENDS. It is the project's first non-$0.00 dependency, it is
deliberate and bounded, and `--cost` prints the bill after every session.
`--offline` runs the whole pipeline on a scripted proposer for $0.00.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.product import compat, corpus                          # noqa: E402
from tlon.product.chat import Refused, render_english            # noqa: E402
from tlon.product.proposer import (AnthropicProposer,            # noqa: E402
                                   ScriptedProposer)

BANNER = """\
────────────────────────────────────────────────────────────────────────
  TLÖN — the southern hemisphere. Say anything.
  It has no nouns. It will not hold your objects as things; it renders
  the happening underneath them, and tells you what it let go.
    /reveal    show the translation — you will be asked if you are sure
    /austere   deeper: the morpheme-exact gloss
    /compat    what else collapses onto this same impression
    /corpus    corpus status and the Route-B milestone
    /cost      the bill so far
    /quit
────────────────────────────────────────────────────────────────────────"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true",
                    help="scripted proposer, $0.00 — exercises the full gate")
    ap.add_argument("--model", default=None)
    ap.add_argument("--say", action="append", default=[],
                    help="render one line and exit (repeatable)")
    ap.add_argument("--no-log", action="store_true")
    args = ap.parse_args()

    if args.offline:
        prop = ScriptedProposer([{
            "node": {"root": "klung", "orient": ["nar"],
                     "aspect_root": "tes", "aspect_reps": 2,
                     "edges": [{"relator": "sen", "node": {"root": "lan"}}]},
            "force": "ka", "refused_objects": ["landlord"],
            "note": "a hollowing that recurs, witnessed"}] * 50)
    else:
        prop = (AnthropicProposer(args.model) if args.model
                else AnthropicProposer())

    last: dict = {}

    def show(text: str, austere: bool = False) -> None:
        try:
            r = render_english(text, prop, log=not args.no_log)
        except Refused as exc:
            print(f"\n  ⛔ {exc}\n")
            return
        last["r"] = r
        print("\n" + r.speak())
        if austere:
            print(f"\n  {r.literary}")
            print(f"  austere: {r.austere}")
        if r.attempts > 1:
            print(f"  (accepted on attempt {r.attempts}; the parser refused "
                  f"{r.attempts - 1} before it)")
        print()

    if args.say:
        for line in args.say:
            show(line, austere=True)
        rep = prop.cost_report()
        print(f"  [{rep['calls']} calls · ${rep['usd_total']:.4f} · "
              f"${rep['usd_per_message']:.4f}/message]")
        return 0

    print(BANNER)
    austere = False   # opacity-first: the gloss is behind /reveal
    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        if line == "/quit":
            break
        if line == "/reveal":
            # ⛔ OPACITY-FIRST. The gate is the point, not friction: choosing to
            # see the translation is the esoteric/carnal choice and it should
            # cost something to make.
            #
            # ⭐⭐ WHAT THE GATE OPENS ONTO IS THE LITERARY RENDER — Nate's call.
            # "The reveal is the literal english translation of what it said. It
            # still isn't normal english. It is the high gloss nounless english
            # instead of the cypher." So the puzzle does not resolve into
            # ordinary speech; it resolves into a language with no objects in it.
            # At first all they get is the cypher: pronounceable without being
            # comprehensible — and solvable, if someone thought about it right.
            if "r" not in last:
                print("  nothing said yet.")
                continue
            ans = input("  are you sure you want to ruin the puzzle? [y/N] ")
            if ans.strip().lower() not in ("y", "yes"):
                print("  kept.")
                continue
            print(f"\n  {last['r'].literary}")
            print(f"\n  you said: {last['r'].english}")
            continue
        if line == "/austere":
            # ⭐ ONE LEVEL DEEPER, for whoever wants the machine-exact version:
            # the morpheme-faithful gloss, which is also the measurement
            # instrument. Not gated — anyone who knows to ask for it has already
            # ruined the puzzle.
            if "r" not in last:
                print("  nothing said yet.")
                continue
            print(f"\n  austere: {last['r'].austere}")
            continue
        if line == "/compat":
            if "r" not in last:
                print("  nothing said yet.")
                continue
            r = last["r"]
            c = compat.compatible_with(r.scene, r.english, r.surface)
            print("\n" + c.reveal())
            continue
        if line == "/corpus":
            st = corpus.status()
            print(f"  accepted {st['accepted']} · refused {st['refused']} "
                  f"{st['refused_by_stage'] or ''} · distinct English "
                  f"{st['distinct_english']} · roots "
                  f"{st['distinct_roots_covered']}/156")
            m = st["milestone"]
            print(f"  Route-B milestone: {m['distinct_english']} distinct "
                  f"English AND {m['distinct_roots_covered']} roots — "
                  f"{'REACHED' if st['b_trainable'] else 'not yet'}")
            # ⭐ The integrity check runs against the FILE, not against the code
            # that wrote it. A corpus is only as good as its worst row and the
            # dangerous row is the one that validates and misrepresents itself.
            a = corpus.audit()
            if a["ok"]:
                print(f"  integrity: {a['rows']} rows, all three views agree")
            else:
                print(f"  ⛔ integrity: {len(a['problems'])} of {a['rows']} "
                      f"rows are wrong")
                for p in a["problems"][:5]:
                    print(f"     row {p['row']}: {p['why']}")
            continue
        if line == "/cost":
            print(f"  {prop.cost_report()}")
            continue
        show(line, austere=austere)

    rep = prop.cost_report()
    print(f"\n  session: {rep['calls']} calls · ${rep['usd_total']:.4f} total · "
          f"${rep['usd_per_message']:.4f}/message")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
