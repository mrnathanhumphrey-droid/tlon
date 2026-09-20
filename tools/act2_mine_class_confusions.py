"""CONTRASTIVE PAIRS from the corpus builds' own refusal logs.

⭐⭐ THE EVIDENCE, AT n=659 INSTEAD OF n=4. Across both Route-A builds the gate
refused 255 + 404 proposals, and the shape is overwhelmingly consistent:

    wrong-slot   209 + 334 = 543    the form EXISTS, it went in the wrong class
    absent        17 +  43 =  60    no such form anywhere
    other         29 +  27 =  56    invented schema fields, mostly 'evidential'

So the grammar is not missing a distinction. A specific class boundary is being
crossed, and the aspect slot dominates both builds.

⭐ AND IT CORROBORATES A NOTE THE REPO ALREADY CARRIED. `corpus.py` records, from
a hosted pre-flight, that `nol` "oft" (class Q) was put in the aspect slot 4x
where `sor` "habitual" (class A) was wanted — and observes that Q and A "collide
semantically in English". This mining finds the SAME boundary from the other
side: `sor` in the Q slot, 18x. Two independent measurements, four samples and
six hundred, agreeing on one boundary.

⛔⛔ THE ENGLISH SIDE IS NOT `gloss(scene)`. `corpus.contrastive_pairs` renders
its English with `gloss`, which is the austere machine register — the exact
thing that made the speaker collapse to two words and the reason $130 was just
spent replacing it. The scene construction there is reused untouched, because it
is the tested and valuable part; only the rendering is swapped at this call site.
Forking the function would have been the other way to get this wrong.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

#: `slot='form' is not in lexicon class X`
_WRONG = re.compile(r"(\w+)='([^']+)' is not in lexicon class (\w)")


def mine(paths) -> list:
    """Refusal JSONL -> ClassError records. ⛔ Only misassignments.

    An INVENTED form has no true class, so there is no contrast to draw: the
    lesson "this is not an aspect" cannot be paired with "it is a root" when it
    is not a root either. `ClassError.actual is None` marks those and
    `contrastive_pairs` already skips them; they are counted and dropped here
    so the count is visible rather than implied.
    """
    from tlon.act2.negatives import ClassError
    from tlon.grammar import classes as C

    lex = C.load()["classes"]
    out, invented, other = [], 0, 0
    for p in paths:
        path = pathlib.Path(p)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            m = _WRONG.search(row.get("detail", "") or "")
            if not m:
                other += 1
                continue
            slot, form, expected = m.groups()
            homes = [k for k, tab in lex.items() if form in tab]
            if not homes:
                invented += 1
                continue
            out.append(ClassError(form=form, used_as=slot, expected=expected,
                                  actual=homes[0]))
    return out, invented, other


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refusals", nargs="+", default=[
        "runs/act2/corpus_natural/refusals.jsonl",
        "runs/act2/corpus_conversations/refusals.jsonl"])
    ap.add_argument("--per-confusion", type=int, default=24,
                    help="unused when --target-rows is set; kept for parity "
                         "with corpus.contrastive_pairs")
    ap.add_argument("--target-rows", type=int, default=2600,
                    help="⛔ SIZE THE DRILL AGAINST THE CORPUS. ~2,600 is ~16%% "
                         "of the 13,389-row bench corpus — enough occupancy to "
                         "teach the slot, small enough not to become the "
                         "training distribution.")
    ap.add_argument("--lexicon", default="lexicon_expanded.yaml")
    ap.add_argument("--lexicon-env", default="TLON_LEXICON")
    ap.add_argument("--out", default="runs/act2/corpus_contrastive/pairs.jsonl")
    ap.add_argument("--seed", type=int, default=20624)
    args = ap.parse_args()

    os.environ[args.lexicon_env] = args.lexicon
    from tlon.act2 import corpus as CO
    from tlon.grammar import classes as C

    C.load.cache_clear()
    lex = C.load()
    print("lexicon %s  %s  %d roots"
          % (args.lexicon, lex["_hash"], len(lex["classes"]["R"])))

    errors, invented, other = mine(args.refusals)
    print("mined %d misassignments · %d invented forms (no contrast to draw) "
          "· %d other" % (len(errors), invented, other))
    if not errors:
        print("⛔ nothing to mine")
        return 1

    print("\nboundaries the model actually confuses, most-confused first:")
    for (a, b), n in CO.boundaries(errors).most_common(10):
        print("   %4d  %s <-> %s" % (n, a, b))

    slots = collections.Counter(e.used_as for e in errors)
    print("\nslot the wrong form was placed in:", dict(slots.most_common()))

    # ⛔⛔ DEDUPE THE ERRORS FIRST, AND SIZE THE DRILL AGAINST THE CORPUS.
    # `contrastive_pairs` builds `per_confusion` scenes per ERROR RECORD, and
    # 543 records at 24 produced 21,071 rows — larger than the entire 13,389-row
    # bench corpus, which would have made training 61% narrow drill in a
    # register that is not natural English. The same boundary observed 321 times
    # is ONE lesson seen often, not 321 lessons.
    #
    # ⭐ EQUAL ALLOCATION ACROSS DISTINCT CONFUSIONS, NOT PROPORTIONAL. A <-> R
    # is 59% of what was observed; weighting by frequency would spend the drill
    # on the boundary the model fails most while leaving the rarer ones
    # untaught, and every one of them is a real refusal.
    distinct = {}
    for e in errors:
        distinct.setdefault((e.form, e.used_as, e.expected, e.actual), e)
    uniq = list(distinct.values())
    per = max(1, round(args.target_rows / (2 * max(1, len(uniq)))))
    print("\n%d error records -> %d DISTINCT confusions · %d scenes each "
          "(target ~%d rows)" % (len(errors), len(uniq), per, args.target_rows))

    pairs = CO.contrastive_pairs(uniq, per_confusion=per, seed=args.seed)
    print("contrastive scenes built: %d" % len(pairs))

    # ⛔ THE SWAP. `Pair.english` arrived as gloss(scene); the bench must never
    # be trained on that register again.
    from tlon.act2 import schema_bridge as SB
    from tlon.product.literary import literary

    rows, seen = [], set()
    for p in pairs:
        if p.surface in seen:
            # ⭐ The generator samples a random base per attempt, so duplicates
            # are possible. A repeated row is not a second lesson; it is the
            # same lesson weighted twice for no stated reason.
            continue
        seen.add(p.surface)
        rows.append({"direction": "write", "prompt": literary(p.scene),
                     "english": literary(p.scene),
                     "scene": SB.scene_to_proposal(p.scene),
                     "surface": p.surface, "context": [],
                     "source": "contrastive", "lexicon": lex["_hash"]})

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(out)
    print("wrote %d distinct rows -> %s" % (len(rows), out))
    print("⛔ english rendered with literary(), NOT gloss()")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
