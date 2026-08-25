"""BUILD THE FINE-TUNE CORPUS — $0.00, offline, deterministic.

Exports (English gloss → Scene JSON) pairs for the class-partition fine-tune,
with the exposure report printed BEFORE anything is written, because that is the
number the fine-tune's success depends on and it must not be discovered after.

⭐ The confused forms from the hosted pre-flight are boosted as TARGETED
POSITIVES -- extra sightings in their CORRECT slot -- which is the only form a
contrastive signal can take in supervised fine-tuning.

    python tools/act2_build_corpus.py --n 40000
    python tools/act2_build_corpus.py --n 2000 --no-focus   # ablation
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from dataclasses import replace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.act2 import corpus                                  # noqa: E402
from tlon.act2 import schema_bridge as SB                     # noqa: E402
from tlon.grammar import classes as C                         # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs" / "act2" / "corpus"

#: Measured in the hosted pre-flight, 2026-08-24. Every one is a REAL form put
#: in the wrong slot -- so every one is fixed by seeing it in the right slot.
CONFUSED = {"pal": 60, "rän": 60, "plas": 60, "hul": 60}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40000)
    ap.add_argument("--eval", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20620)
    ap.add_argument("--naive", action="store_true",
                    help="ablation: free sampling, no balancing")
    ap.add_argument("--no-focus", action="store_true",
                    help="ablation: no targeted positives for confused forms")
    ap.add_argument("--write-only", action="store_true",
                    help="ablation: English→Scene only — the corpus that trained "
                         "a writer and was then tested as a reader (speak 9.4 %)")
    a = ap.parse_args()

    focus = None if a.no_focus else CONFUSED
    pairs = corpus.build(a.n + a.eval, seed=a.seed, balanced=not a.naive,
                         focus_forms=focus)
    rep = corpus.exposure_report(pairs)

    lex = C.load()["classes"]
    print(f"corpus {len(pairs):,} pairs · lexicon {C.load()['_hash'][:8]} · "
          f"{'naive' if a.naive else 'balanced'}"
          f"{'' if focus else ' · NO focus'}")
    print(f"⛔ the number the fine-tune depends on: worst-form exposure "
          f"{rep['worst_form_exposure']}  (spread {rep['exposure_spread']:.1f}×)")
    print("\n  class  forms  covered   per-form min..max")
    for cls in corpus.CLASSES:
        r = rep["by_class"][cls]
        print(f"    {cls:<4} {r['forms']:>5}  {r['covered']:>5}/{r['forms']:<4} "
              f"{r['min_form_exposure']:>7}..{r['max_form_exposure']}")

    if focus:
        exp = corpus.class_exposure(pairs)
        print("\n  targeted positives (the mined confusions, in their CORRECT slot):")
        for form in CONFUSED:
            cls = next(c for c in corpus.CLASSES if form in lex[c])
            print(f"    {form:<6} class {cls} · {exp[cls][form]:>5} sightings "
                  f"· {lex[cls][form]}")

    short = [c for c in corpus.CLASSES
             if rep["by_class"][c]["covered"] != rep["by_class"][c]["forms"]]
    if short:
        raise SystemExit(f"⛔ classes not fully covered: {short}. Refusing to "
                         "write a corpus that cannot teach the whole partition.")

    OUT.mkdir(parents=True, exist_ok=True)
    train, ev = pairs[:a.n], pairs[a.n:]

    # ⛔⛔ BOTH DIRECTIONS, OR THE MODEL IS A WRITER BEING TESTED AS A READER.
    # Measured on the fixed-dialect run: render (write, trained) 81.2 %, speak
    # (read, NEVER trained) 9.4 %, with 90 % of the offending forms lifted
    # verbatim off the Tlön history it had just been shown.
    #
    # ⭐ THE WRITE HALF IS LEFT EXACTLY AS IT WAS, so render stays directly
    # comparable to the previous run and any change in it is attributable to
    # INTERFERENCE from the added read half — a controlled single-variable
    # change, the same discipline that proved the dialect was the cause.
    #
    # ⭐ COMPUTE IS UNCHANGED: 80,000 rows at 1 epoch is the same 5,000 optimizer
    # steps, and the same tokens, as 40,000 rows at 2 epochs. The run costs what
    # the last one cost.
    if not a.write_only:
        train = train + [replace(q, direction="read") for q in train]
        ev = ev + [replace(q, direction="read") for q in ev]
        print(f"\n  ⭐ TWO DIRECTIONS: {len(train):,} train rows "
              f"({len(train) // 2:,} write + {len(train) // 2:,} read)")

    for name, part in (("train", train), ("eval", ev)):
        path = OUT / f"{name}.jsonl"
        with path.open("w", encoding="utf-8", newline="") as fh:
            for p in part:
                # ⛔⛔ `canon_json` WAS HERE AND IT COST A FINE-TUNE. It is the
                # canonical HASHING form -- `edges: [["nix",{…}]]`,
                # `aspect: ["sor",2]` -- not the proposal schema the gate and the
                # model-facing schema use. The model learned the hashing dialect
                # faithfully and the gate refused it: 39 of 44 render failures.
                # ⭐ `impression` still comes from the canonical form, because
                # that is exactly what canon IS for; only the TRAINING TARGET
                # moves to the proposal schema.
                fh.write(json.dumps({
                    "prompt": p.prompt(),
                    "direction": p.direction,
                    "english": p.english,
                    "surface": p.surface,
                    "scene": SB.scene_to_proposal(p.scene),
                    "impression": p.impression,
                    "source": p.source}, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"\n  wrote {len(part):,} → {path}")

    meta = OUT / "meta.json"
    meta.write_text(json.dumps({
        "n_train": len(train), "n_eval": len(ev), "seed": a.seed,
        "balanced": not a.naive, "focus_forms": focus,
        "lexicon": C.load()["_hash"], "exposure": rep},
        indent=2, ensure_ascii=False), encoding="utf-8", newline="")
    print(f"  wrote {meta}")
    print("\n⛔ nothing trained. The corpus is an input, not a run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
