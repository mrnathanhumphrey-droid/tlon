"""Score which ENGLISH words actually buy a shared Tlön ROOT.

⛔⛤ WHY THIS IS MEASURED AND NOT LISTED BY HAND. The distinction the carry
gate needs looks like "verbs", and it is not. `feels` is a verb and buys
nothing — two lines sharing it share a root 5% of the time, against a 3.8%
random-pair baseline. `dims` buys one every time. What separates them is that
a Tlön ROOT is a HAPPENING, so an English word that names a happening maps to
a root and an English word that names a stance, a time or a degree maps to a
PARTICLE. That is exactly the 35% D / 24.5% T / 21% L split that was once
mistaken for content continuity.

So the list is derived, never authored. For every English word, measure the
root it lands on and HOW RELIABLY:

    root   = the most common root among turns containing the word
    purity = the share of those turns that carry it

⭐⭐ PURITY IS THE WHOLE DISCRIMINATOR, and it does two jobs at once.
It separates happenings from stance — `dims` 1.00, `waited` 1.00,
`breathing` 1.00 against `feels` 0.11, `today` 0.08, `little` 0.06 — and
because inflections of one happening land on ONE root, it also dissolves
morphology without a stemmer: `waited`/`waiting`/`wait` are all `hlun`
(1.00/0.95/0.76), `dims`/`dimmed`/`dimming` are all `flöx`.

⛔⛤ THE FIRST VERSION OF THIS FILE SCORED `P(two lines sharing the word share
a root)` AND A TEST CAUGHT IT. That statistic is real but it made the gate
compare word STRINGS, so "I waited far too long" / "A waiting stretches out"
failed — the exact shape the new prompt produces, since the Tlönian names a
happening by nominalising it. Comparing PREDICTED ROOTS instead makes the
stage-1 gate a direct proxy for the stage-2 property it is meant to anticipate.

⛔ The scored corpus must pair `english` with `scene` on the SAME row. A file
that carries only surfaces cannot support this and is refused rather than
silently skipped.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import pathlib
import random
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# ⛔ Words that are pure scaffolding. They are removed before scoring only to
# keep the pair enumeration tractable — they would score at baseline anyway,
# and the printed bottom of the table is the check on that.
STOP = set("""a an the and or but so then than that this those these it its
is are was were be been being am i me my we our you your he she they them his
her their of in on at to for from with by as if not no nor do does did done
have has had will would can could should may might must just about into over
under again very too much more most some any all own same don now there here
when where how what who whom which while up down out off once""".split())
WORD = re.compile(r"[a-z']+")

# ⭐ No fan-out cap is needed any more. The old pair-enumeration statistic was
# quadratic in a word's frequency and had to exclude common words to stay
# tractable; purity is linear, so `today` and `feels` are now SCORED and
# rejected on their merits (0.08, 0.11) rather than excluded for being common.


def read_rows(path: pathlib.Path):
    """Yield `(english, scene)` from either corpus shape."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "turns" in row:                      # a conversation
                for turn in row["turns"]:
                    if isinstance(turn, dict):
                        yield turn.get("english"), turn.get("scene")
            else:                                   # a single pair
                yield row.get("english"), row.get("scene")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", nargs="+", required=True,
                    help="jsonl files pairing english with scene")
    ap.add_argument("--lexicon", default="lexicon_expanded.yaml")
    ap.add_argument("--lexicon-env", default="TLON_LEXICON")
    ap.add_argument("--threshold", type=float, default=0.70,
                    help="keep words whose dominant root holds this purity")
    ap.add_argument("--min-turns", type=int, default=8,
                    help="a word must appear in this many scored turns")
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve()
                                         .parents[1] / "tlon" / "act2"
                                         / "happening_words.json"))
    ap.add_argument("--seed", type=int, default=20260921)
    args = ap.parse_args()

    os.environ[args.lexicon_env] = args.lexicon
    from tlon.act2.carry import scene_roots
    from tlon.grammar import classes as C

    C.load.cache_clear()
    lex = C.load()
    roots = frozenset(lex["classes"]["R"])
    print("lexicon %s  %s  %d roots" % (args.lexicon, lex["_hash"], len(roots)))

    turns, sources = [], []
    for name in args.corpus:
        path = pathlib.Path(name)
        if not path.exists():
            raise SystemExit("⛔ no such corpus: %s" % path)
        before = len(turns)
        for english, scene in read_rows(path):
            if not english or scene is None:
                continue
            rts = scene_roots(scene, roots)
            if not rts:
                continue
            words = {w for w in WORD.findall(english.lower())
                     if w not in STOP and len(w) > 2}
            turns.append((words, rts))
        got = len(turns) - before
        if not got:
            raise SystemExit(
                "⛔⛔ %s contributed 0 scorable turns. It must pair `english` "
                "with `scene` on the same row; a surface-only corpus cannot "
                "support this measurement." % path)
        sources.append({"path": str(path), "turns": got})
        print("  %-58s %6d turns" % (path.name, got))

    # ── the random-pair baseline: same rows, same estimator, no word filter ──
    rng = random.Random(args.seed)
    hit = trials = 0
    for _ in range(300000):
        a, b = rng.randrange(len(turns)), rng.randrange(len(turns))
        if a == b:
            continue
        trials += 1
        hit += 1 if (turns[a][1] & turns[b][1]) else 0
    baseline = hit / trials
    print("random-pair baseline %.3f  (n=%d)" % (baseline, trials))

    # ── each word's dominant root, and how reliably it holds ───────────────
    hits = collections.defaultdict(collections.Counter)
    seen = collections.Counter()
    for words, rts in turns:
        for w in words:
            seen[w] += 1
            for r in rts:
                hits[w][r] += 1

    scored = {}
    for w, n in seen.items():
        if n < args.min_turns or not hits[w]:
            continue
        root, k = hits[w].most_common(1)[0]
        scored[w] = {"root": root, "purity": round(k / n, 4), "turns": n}

    kept = {w: s for w, s in scored.items() if s["purity"] >= args.threshold}
    ranked = sorted(scored.items(), key=lambda kv: -kv[1]["purity"])
    print("scored %d words · %d hold purity >= %.2f"
          % (len(scored), len(kept), args.threshold))
    print("  purest:  %s"
          % ", ".join("%s->%s" % (w, s["root"]) for w, s in ranked[:8]))
    print("  muddiest: %s"
          % ", ".join("%s(%.2f)" % (w, s["purity"]) for w, s in ranked[-8:]))
    # ⭐ The check that the threshold is doing the intended work, printed so a
    # reader sees it rather than trusting it.
    for probe in ("waited", "waiting", "dims", "dimming", "feels", "today"):
        s = scored.get(probe)
        print("    %-9s %s" % (probe, "absent" if not s else
                               "%s purity %.2f n=%d %s"
                               % (s["root"], s["purity"], s["turns"],
                                  "KEPT" if probe in kept else "dropped")))

    body = {
        "words": {w: s for w, s in sorted(scored.items())},
        "threshold": args.threshold,
        "min_turns": args.min_turns,
        "baseline": round(baseline, 4),
        "provenance": {
            "generated": dt.date.today().isoformat(),
            "tool": pathlib.Path(__file__).name,
            "lexicon": args.lexicon,
            "lexicon_hash": lex["_hash"],
            "sources": sources,
            "turns_scored": len(turns),
            "seed": args.seed,
            "statistic": "P(the word's dominant root | turns containing the "
                         "word) — 'purity'. A word is a HAPPENING when its "
                         "root is reliable; inflections share one root, so "
                         "this needs no stemmer.",
        },
    }
    out = pathlib.Path(args.out)
    # ⛔ TEMP FILE, VERIFY, REPLACE. `open(p, "w")` truncates before the write
    # can fail, and this file is the gate's whole ability to tell a happening
    # from a mood.
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(body, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    check = json.loads(tmp.read_text(encoding="utf-8"))
    if len(check["words"]) != len(body["words"]):
        raise SystemExit("⛔ readback mismatch, refusing to replace %s" % out)
    tmp.replace(out)
    print("wrote %s  (%d words, %d bytes)"
          % (out, len(body["words"]), len(out.read_bytes())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
