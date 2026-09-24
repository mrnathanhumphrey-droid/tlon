"""⛔⛔ IS A MISSED TURN 1 DECODE VARIANCE, OR IS IT THE PROVOCATION'S FAULT?

THE FINDING THIS ANSWERS. The onset baseline showed the whole conversation is
decided by its first exchange: P(carry | previous turn carried) = 0.842 against
0.156 if it missed, and turn 1 has NO CONTEXT at all. Turn-1 carry is 0.510 and
the three-turn joint is 0.657; the governing arithmetic is

    joint  ~=  p1 + (1 - p1) * 0.3325

so p1 -> 0.80 gives 0.867 and p1 -> 0.90 gives 0.933. Raising turn-1 carry is
the entire lever, and there are two very differently priced ways to do it.

    DECODE VARIANCE      the same provocation sometimes carries and sometimes
                         does not. Then a bounded retry buys 1 - (1-p1)^k for
                         free: no training, a few lines in the server.
    PROVOCATION-DETERMINED  some provocations never carry however often they
                         are asked. Then retries are wasted GPU and the fix is
                         in the weights.

⛔⛔ THE PROVOCATION IS HELD FIXED AND ONLY THE REPLY IS RESAMPLED, because that
is the only retry the product could honestly offer. `yours.surface` is the
READER'S OWN LINE, already rendered and already on their screen; re-rendering it
would answer a different sentence than the one they can see. So this drives
`Speaker.reply_to`, which `turn` itself calls.

⛔ PAIRED BY CONSTRUCTION. Every attempt reuses the EXACT provocation string
from the baseline ledger, so "did this one flip?" is a within-item question and
needs no between-run comparison. The baseline verdict is re-derived here from
the stored provocation rather than trusted from the ledger's `carried` field —
see `main`.

⛔ The backend samples at temperature 0.7 with no per-call seed, so successive
calls are independent draws. Nothing here arranges that; it is the mechanism a
retry would rely on, which is exactly why it must be measured and not assumed.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def load_turn1(ledger: dict) -> list[dict]:
    """Every conversation's FIRST exchange, as the baseline recorded it.

    ⛔ Depth 0 only. A deeper turn carries context, and the question is about
    the exchange that has none — the one the baseline showed decides the rest.

    ⛔ A turn the baseline could not score is DROPPED, not counted as a miss.
    Its provocation is absent or unparseable, so there is nothing to resample
    and calling it a miss would charge the retry for the baseline's refusals.
    """
    out = []
    for c in ledger["items"]:
        for t in c["turns"]:
            if t.get("depth") != 0:
                continue
            if t.get("carried") is None or not t.get("provocation"):
                continue
            out.append({"id": c["id"], "theme": c.get("theme"),
                        "provocation": t["provocation"],
                        "baseline_carried": bool(t["carried"])})
    return out


def summarise(rows: list[dict], k: int) -> dict:
    """What a bounded retry would buy, split by what the baseline did."""
    from tlon.act2.carry import wilson

    miss = [r for r in rows if not r["baseline_carried"]]
    hit = [r for r in rows if r["baseline_carried"]]

    def rescue(group):
        """P(at least one of k resamples carries), per item."""
        n = len(group)
        if not n:
            return None
        anyk = sum(1 for r in group if any(r["attempts"]))
        lo, hi = wilson(anyk, n)
        # ⭐ per-ATTEMPT rate too: if retries were independent draws at the
        # baseline rate, per-attempt carry should match the baseline's 0.51 in
        # the HIT group and be far lower in the MISS group if the provocation
        # is what decides it.
        att = [a for r in group for a in r["attempts"]]
        return {"n": n, "any_of_k": anyk, "rate": round(anyk / n, 4),
                "ci95": [round(lo, 4), round(hi, 4)],
                "per_attempt": round(sum(att) / len(att), 4) if att else None,
                "attempts": len(att)}

    base_p1 = sum(1 for r in rows if r["baseline_carried"]) / len(rows)
    m = rescue(miss)
    h = rescue(hit)
    # ⭐ WHAT A RETRY WOULD ACTUALLY BUY. The server only retries when the first
    # reply missed, so the new p1 is the old one plus the rescued share of the
    # misses -- not `1-(1-p)^k`, which assumes every draw is a fresh coin.
    new_p1 = base_p1 + (1 - base_p1) * (m["rate"] if m else 0.0)
    return {"k": k, "n": len(rows),
            "baseline_p1": round(base_p1, 4),
            "missed": m, "hit": h,
            "projected_p1_with_retry": round(new_p1, 4),
            # joint = p1 + (1-p1)*P(>=1 in turns 2-3 | turn 1 missed), and that
            # conditional was measured at 0.3325 in the onset baseline.
            "projected_joint": round(new_p1 + (1 - new_p1) * 0.3325, 4),
            "baseline_joint": round(base_p1 + (1 - base_p1) * 0.3325, 4)}


def _report(s: dict) -> None:
    print("  baseline turn-1 carry   %.1f%%  (n=%d)"
          % (100 * s["baseline_p1"], s["n"]))
    for label, key in (("baseline MISSED", "missed"), ("baseline carried", "hit")):
        g = s[key]
        if not g:
            continue
        print("\n  ── %s · n=%d ──" % (label, g["n"]))
        print("     >=1 of %d resamples carried   %d/%d = %.1f%%  [%.1f, %.1f]"
              % (s["k"], g["any_of_k"], g["n"], 100 * g["rate"],
                 100 * g["ci95"][0], 100 * g["ci95"][1]))
        print("     per-attempt carry             %.1f%%  (%d attempts)"
              % (100 * g["per_attempt"], g["attempts"]))
    print("\n  ── WHAT A BOUNDED RETRY WOULD BUY ──")
    print("     turn-1 carry   %.1f%%  ->  %.1f%%"
          % (100 * s["baseline_p1"], 100 * s["projected_p1_with_retry"]))
    print("     three-turn joint   %.1f%%  ->  %.1f%%"
          % (100 * s["baseline_joint"], 100 * s["projected_joint"]))
    m = s["missed"]
    if m and m["per_attempt"] is not None:
        print("\n  ⭐ READ IT THIS WAY: if the misses were DECODE VARIANCE their "
              "per-attempt\n     rate would sit near the baseline %.2f; if the "
              "PROVOCATION decides, it\n     sits near zero. Measured: %.2f"
              % (s["baseline_p1"], m["per_attempt"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ledger", required=True,
                    help="the onset baseline's per-item JSON")
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--k", type=int, default=3, help="resamples per provocation")
    ap.add_argument("--limit", type=int, default=0,
                    help="cap the provocations (0 = all)")
    ap.add_argument("--lexicon", default="lexicon_expanded.yaml")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    import os
    os.environ["TLON_LEXICON"] = a.lexicon
    if a.adapter:
        os.environ["TLON_ADAPTER"] = a.adapter

    from tlon.grammar import classes as C
    C.reset_caches()
    lex = C.load()
    roots = frozenset(lex["classes"]["R"])
    print("lexicon %s · %d roots · %s" % (a.lexicon, len(roots), lex["_hash"]))

    ledger = json.loads(pathlib.Path(a.ledger).read_text(encoding="utf-8"))
    if ledger.get("replay"):
        raise SystemExit("⛔⛔ REFUSING: that ledger is a --replay run. Its "
                         "'carried' flags are the CORPUS's, not the model's, "
                         "and resampling against them would compare the model "
                         "to a transcript.")
    rows = load_turn1(ledger)
    if a.limit:
        rows = rows[:a.limit]

    import importlib
    from act2_onset_carry import score_turn
    from tlon.grammar.parse import ParseError, parse
    sp = importlib.import_module("puzzle.speaker")
    speaker = sp.Speaker()

    print("RESEED TURN 1 · adapter=%s · n=%d · k=%d"
          % (sp.ADAPTER, len(rows), a.k))
    print("⛔ the provocation is held FIXED; only the reply is resampled\n")

    for i, r in enumerate(rows):
        # ⛔⛔ RE-DERIVE THE BASELINE VERDICT FROM THE STORED PROVOCATION RATHER
        # THAN TRUST THE LEDGER'S FLAG. The flag was written by a different
        # process; if the scorer or the lexicon has moved since, trusting it
        # would silently mix two definitions of carry inside one comparison.
        r["attempts"] = []
        for _ in range(a.k):
            reply = speaker.reply_to(r["provocation"], [])
            if not getattr(reply, "ok", False) or not reply.surface:
                r["attempts"].append(False)
                continue
            try:
                scene = parse(reply.surface)
            except (ParseError, KeyError, ValueError):
                r["attempts"].append(False)
                continue
            v = score_turn(r["provocation"], scene, roots)
            r["attempts"].append(bool(v.get("carried")))
        if (i + 1) % 10 == 0:
            print("    %d/%d provocations" % (i + 1, len(rows)), flush=True)

    s = summarise(rows, a.k)
    print()
    _report(s)

    if a.out:
        out = pathlib.Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"summary": s, "adapter": sp.ADAPTER,
                                   "k": a.k, "ledger": a.ledger, "items": rows},
                                  ensure_ascii=False, indent=1),
                       encoding="utf-8", newline="\n")
        tmp.replace(out)
        print("\n  ledgered → %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
