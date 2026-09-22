"""⛔⛔ THE PRE-TRAINING KILL SWITCH for the softened steer.

Run on the pilot corpus BEFORE paying for a retrain. Three questions, and the
third is the one that decides whether the arm is worth running at all:

  1 · DOES THE SOFTENED CORPUS CLEAR ITS OWN GATE? Pooled over the survivors
      AND `scene_gate_missed.jsonl`. ⛔⛔ Reading only the survivors gives
      100% BY CONSTRUCTION — the gate is what put them there. This arc has
      already made that mistake once.

  2 · WHAT WOULD THE EXACT GATE HAVE SAID about the same pairs?

      ⛔⛤ AND THE SOFTENED GATE IS *NOT* STRICTLY MORE PERMISSIVE — an earlier
      version of this file said it was, and the control run refuted it: on the
      exactly steered sample the softened rate came in BELOW the exact one,
      95.1% against 97.0%. That is the design, not a defect. The softened gate
      widens what counts as CARRIED and narrows what counts as NEW, because
      `added` is measured against the expanded family. P `{flöx}` answered by
      T `{flöx, pön}` passes the exact gate — it carried `flöx` and added
      `pön` — and fails the softened one, because `pön` "it darkens" IS
      `flöx` "it dims": the reply restated one happening twice and said
      nothing further. The exact gate cannot see that echo. So the two rates
      are not ordered, and neither bounds the other.

  3 · ⭐⭐ WAS THE SOFTENING ACTUALLY EXERCISED? If the model keeps choosing
      the exact root anyway, the softened corpus is a near-replicate of the
      steered one and the retrain buys a relabelled copy of a run already
      paid for. This is the number that says "do not spend", and neither of
      the first two can see it: a corpus where the softening changed nothing
      scores IDENTICALLY on both.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def pairs_from_survivors(path, roots, scene_roots):
    out = []
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            conv = json.loads(line)
            turns = conv.get("turns") or []
            for i in range(len(turns) - 1):
                a, b = turns[i], turns[i + 1]
                if a.get("voice") != "P" or b.get("voice") != "T":
                    continue
                out.append((frozenset(scene_roots(a.get("scene"), roots)),
                            frozenset(scene_roots(b.get("scene"), roots)),
                            "survivor"))
    return out


def pairs_from_missed(path, roots, scene_roots):
    """⛔ THE FAILURES ARE HALF THE DENOMINATOR. `scene_gate_missed.jsonl`
    holds the exchange that stopped a conversation — exactly the pairs a
    survivors-only read would silently drop."""
    out = []
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            ex = rec.get("turns") or rec.get("exchange_turns") or []
            if len(ex) < 2:
                continue
            a, b = ex[0], ex[1]
            out.append((frozenset(scene_roots(a.get("scene"), roots)),
                        frozenset(scene_roots(b.get("scene"), roots)),
                        "missed"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True,
                    help="a corpus build directory")
    ap.add_argument("--lexicon", default="lexicon_expanded.yaml")
    ap.add_argument("--floor", type=float, default=0.50,
                    help="the carry floor below which the retrain is OFF")
    args = ap.parse_args()

    os.environ["TLON_LEXICON"] = args.lexicon
    from tlon.act2.carry import (expand_roots, scene_carry, scene_carry_soft,
                                 scene_roots, wilson)
    from tlon.grammar import classes as C
    C.load.cache_clear()
    roots = frozenset(C.load()["classes"]["R"])

    run = pathlib.Path(args.run)
    pairs = (pairs_from_survivors(run / "conversations.jsonl", roots,
                                  scene_roots)
             + pairs_from_missed(run / "scene_gate_missed.jsonl", roots,
                                 scene_roots))
    if not pairs:
        raise SystemExit("⛔⛔ no P->T pairs found under %s" % run)

    n = len(pairs)
    n_surv = sum(1 for p in pairs if p[2] == "survivor")

    # ⛔⛔ CROSS-CHECK THE DENOMINATOR AGAINST THE RUN THAT PRODUCED IT. A rate
    # is only as good as what it is over, and this tool reads two files that
    # are NOT the full gated set: a conversation dropped for ending up too
    # short takes its pairs with it, and they appear in neither
    # conversations.jsonl nor scene_gate_missed.jsonl. On the first softsteer
    # pilot this tool saw 56 pairs where the build had gated 67 — harmless
    # there because every one passed, and silently wrong the moment they do
    # not. Reported, never patched over.
    report = run / "build_report.json"
    gated = None
    if report.exists():
        gated = json.loads(report.read_text(encoding="utf-8")) \
            .get("counts", {}).get("scene_pairs")
    soft_ok = sum(1 for p, t, _ in pairs if scene_carry_soft(p, t).ok)
    exact_ok = sum(1 for p, t, _ in pairs if scene_carry(p, t).ok)

    # ⭐⭐ WAS THE SOFTENING EXERCISED? Among pairs the softened gate accepts,
    # how many carried ONLY through a synonym — i.e. share no exact root with
    # the prior turn. Those are the rows that could not exist in the exactly
    # steered corpus.
    via_synonym = sum(1 for p, t, _ in pairs
                      if scene_carry_soft(p, t).ok and not (p & t))
    # and how much of the corpus even HAD the option
    had_option = sum(1 for p, _t, _ in pairs if expand_roots(p) != p)

    print("run      %s" % run)
    print("pairs    %d  (%d survivors + %d from scene_gate_missed)"
          % (n, n_surv, n - n_surv))
    if gated is not None and gated != n:
        print("         ⚠ the build gated %d pairs, %d more than this tool can "
              "see — they sit in conversations that were dropped for ending up "
              "too short, so they are in neither file. The rates below are "
              "over %d, not %d." % (gated, gated - n, n, gated))
    print()
    lo, hi = wilson(soft_ok, n)
    print("1 · SOFTENED carry (its own gate, POOLED)   %d/%d = %.1f%% "
          "[%.1f, %.1f]" % (soft_ok, n, 100 * soft_ok / n, 100 * lo, 100 * hi))
    lo2, hi2 = wilson(exact_ok, n)
    print("2 · EXACT carry on the SAME pairs           %d/%d = %.1f%% "
          "[%.1f, %.1f]" % (exact_ok, n, 100 * exact_ok / n,
                            100 * lo2, 100 * hi2))
    # ⛔ The pairs the EXACT gate accepted and the softened one refuses: a
    # reply whose only novelty was a sibling of the root it carried. The exact
    # gate is blind to these, so they sit in the steered corpus unremarked.
    echoes = sum(1 for p, t, _ in pairs
                 if scene_carry(p, t).ok and not scene_carry_soft(p, t).ok)
    print("    of which the exact gate ACCEPTED but the softened one refuses "
          "as a synonym-echo: %d" % echoes)
    print()
    print("3 · SOFTENING EXERCISED                     %d/%d = %.1f%% of pairs"
          % (via_synonym, n, 100 * via_synonym / n))
    print("    (accepted carrying a SYNONYM, sharing no exact root — rows that")
    print("     could not exist in the exactly steered corpus)")
    print("    pairs whose prior root even HAS a family: %d/%d = %.1f%%"
          % (had_option, n, 100 * had_option / n))
    print()

    rate = soft_ok / n
    ok = rate >= args.floor
    print("KILL SWITCH  carry %.1f%% against a %.0f%% floor  ->  %s"
          % (100 * rate, 100 * args.floor,
             "TRAIN" if ok else "⛔⛔ DO NOT TRAIN"))
    if via_synonym == 0:
        print("⛔⛔ AND STOP ANYWAY: the softening was never exercised. This "
              "corpus is a relabelled copy of the steered one and the retrain "
              "would re-measure a run already paid for.")
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
