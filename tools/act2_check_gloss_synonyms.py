"""⛔⛔ THE THREE GUARDS, RUN AGAINST THE FIXED SETS.

The sets in `act2_build_gloss_synonyms.py` were judged from the glosses with no
number in view. This measures them against the acceptance bars that were
written down at the same time. ⛔ If a bar is missed, the answer is to re-judge
the MEANINGS — never to move the bar. A bar moved after seeing the number it
failed is not a bar.

  TOO LOOSE   `max_set_size`   — is any family so big that "carry any of these"
                                 has stopped meaning anything?
  TOO TIGHT   `reach`          — do the families touch enough of the steered
                                 corpus's real carry pairs to be a treatment?
  DIRECTION   `antonyms`       — does any family point both ways? ⛔⛔ THE ONLY
                                 GUARD THAT CATCHES `wearies ~ wakes`, which
                                 passed both shape guards in the dead route.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from act2_build_gloss_synonyms import ACCEPTANCE, ANTONYMS, FAMILIES, build


def carry_pairs(path, roots):
    """The shared-root set of every P->T pair in a conversation corpus."""
    from tlon.act2.carry import scene_roots
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            turns = json.loads(line).get("turns") or []
            for i in range(len(turns) - 1):
                a, b = turns[i], turns[i + 1]
                if a.get("voice") != "P" or b.get("voice") != "T":
                    continue
                shared = (scene_roots(a.get("scene"), roots)
                          & scene_roots(b.get("scene"), roots))
                if shared:
                    out.append(shared)
    return out


def guards(sets, pairs, names=None):
    """⛔⛔ EVERY GUARD READS `sets`, NOT THE MODULE-LEVEL `FAMILIES`.

    The first version checked antonyms by iterating `FAMILIES`, which meant the
    direction guard ignored the argument it was handed and certified whatever
    happened to be written in the builder. A test that fabricated a
    `wearies ~ wakes` family and passed it in saw the guard report clean — the
    guard was pinned to the artifact beside it rather than to the data its
    caller actually uses. A guard must read what the consumer reads.
    """
    sizes = sorted(len(v) for v in sets.values())
    touched = sum(1 for sh in pairs if any(len(sets.get(r, ())) > 1
                                           for r in sh))
    bad = []
    for members in {frozenset(v) for v in sets.values()}:
        name = (names or {}).get(sorted(members)[0]) or \
            "·".join(sorted(members))
        for a, b in ANTONYMS:
            if a in members and b in members:
                bad.append((name, a, b))
    bad.sort()
    return {
        "max_set_size": sizes[-1] if sizes else 0,
        "mean_set_size": round(sum(sizes) / len(sizes), 3) if sizes else 0.0,
        "roots_with_alternatives": len(sets),
        "pairs": len(pairs),
        "touchable": touched,
        "reach": round(touched / len(pairs), 4) if pairs else 0.0,
        "antonym_violations": bad,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus",
                    default="runs/act2/corpus_conv_steered/conversations.jsonl")
    ap.add_argument("--lexicon", default="lexicon_expanded.yaml")
    ap.add_argument("--show-families", action="store_true")
    args = ap.parse_args()

    os.environ["TLON_LEXICON"] = args.lexicon
    sets, rep = build(args.lexicon)
    if rep["problems"]:
        for p in rep["problems"]:
            print("⛔ %s" % p)
        raise SystemExit("⛔⛔ the sets are structurally invalid")
    glosses = rep["glosses"]

    if args.show_families:
        print("══ THE %d FAMILIES, FOR THE HAND-CHECK ══" % len(FAMILIES))
        for family, members in sorted(FAMILIES.items()):
            print("\n%s" % family)
            for r in members:
                print("    %-7s %s" % (r, glosses.get(r, "?")))
        print()

    from tlon.grammar import classes as C
    roots = frozenset(C.load()["classes"]["R"])
    pairs = carry_pairs(args.corpus, roots)
    g = guards(sets, pairs, rep["placed"])

    print("══ THE GUARDS, AGAINST PRE-REGISTERED ACCEPTANCE ══")
    print("corpus %s — %d carry pairs with a shared root"
          % (pathlib.Path(args.corpus).name, g["pairs"]))
    print()
    ok = True

    v = g["max_set_size"]
    bar = ACCEPTANCE["max_set_size_at_most"]
    good = v <= bar
    ok &= good
    print("  TOO LOOSE  max_set_size   %d  (bar: <= %d)   %s"
          % (v, bar, "PASS" if good else "FAIL"))

    v = g["reach"]
    bar = ACCEPTANCE["reach_at_least"]
    good = v >= bar
    ok &= good
    print("  TOO TIGHT  reach          %.1f%%  (bar: >= %.0f%%)   %s"
          % (100 * v, 100 * bar, "PASS" if good else "FAIL"))
    print("             %d of %d carry pairs are touchable"
          % (g["touchable"], g["pairs"]))

    n = len(g["antonym_violations"])
    good = n == ACCEPTANCE["antonym_pairs_within_sets"]
    ok &= good
    print("  DIRECTION  antonym pairs  %d  (bar: == %d)   %s"
          % (n, ACCEPTANCE["antonym_pairs_within_sets"],
             "PASS" if good else "FAIL"))
    for family, a, b in g["antonym_violations"]:
        print("             ⛔ %s holds %s (%s) and %s (%s)"
              % (family, a, glosses.get(a, "?"), b, glosses.get(b, "?")))

    print("\n  shape: %d families · %d roots placed · %d stand alone · "
          "mean set %.2f"
          % (len(FAMILIES), len(rep["placed"]),
             len(glosses) - len(rep["placed"]), g["mean_set_size"]))
    print("\n%s" % ("✅ ALL THREE GUARDS PASS" if ok
                    else "⛔⛔ ACCEPTANCE NOT MET — re-judge the meanings, "
                         "do not move a bar"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
