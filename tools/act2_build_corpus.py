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

#: ⛔⛔ STALE, AND KEPT ONLY AS THE RECORD OF WHY THE LIST IS NO LONGER HAND-KEPT.
#: Mined from the hosted pre-flight on 2026-08-24 and still being boosted three
#: runs later — by which point ALL FOUR WERE FIXED (none appears in the n=256
#: confusions) and the live offenders were `nol` `nem` `xom` `sen` `fral` `hrix`.
#: The boost was spending itself on solved problems while the real ones went
#: untargeted. ⭐ The mechanism worked; the list rotted. `--from-ledger` reads the
#: confusions out of the newest run instead, and cannot rot.
STALE_PREFLIGHT_CONFUSED = {"pal": 60, "rän": 60, "plas": 60, "hul": 60}

LEDGER = pathlib.Path(__file__).resolve().parents[1] / "runs/act2/harden/ledger_harden.jsonl"


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
    ap.add_argument("--from-ledger", default=str(LEDGER),
                    help="mine the confusions from this run ledger (§8.2)")
    ap.add_argument("--stale-list", action="store_true",
                    help="ablation: use the frozen pre-flight list instead of the "
                         "ledger — reproduces run 3's corpus exactly")
    ap.add_argument("--slot-floor", type=float, default=None,
                    help=f"§8.2: minimum slot occupancy for {corpus.FLOORED_CLASSES}. "
                         f"Measured-derived value is {corpus.SLOT_OCCUPANCY_FLOOR}")
    ap.add_argument("--contrastive", type=int, default=0,
                    help="§8.2: minimal pairs per mined confusion (0 = off)")
    # ⛔ ADDED AFTER A 3,000-ROW TEST BUILD OVERWROTE THE LIVE 40,000-ROW CORPUS.
    # It was fully recoverable — the build is deterministic and the restore was
    # verified against fingerprints — but only because the fingerprints had been
    # measured minutes earlier by luck, not by discipline. A search over `--n`
    # writes many candidate corpora; none of them may land on the live one.
    ap.add_argument("--out", default=str(OUT),
                    help="corpus directory. Defaults to the LIVE corpus — pass "
                         "a scratch path when sweeping.")
    a = ap.parse_args()
    out_dir = pathlib.Path(a.out)

    # ── §8.2 — the confusions come from the RUN, not from a list ──────────
    mined, focus = [], None
    if a.stale_list:
        focus = None if a.no_focus else STALE_PREFLIGHT_CONFUSED
        print("⚠️ using the STALE pre-flight list (ablation)")
    elif not a.no_focus:
        mined = corpus.mined_confusions(a.from_ledger)
        counts = {}
        for e in mined:
            counts[e.form] = counts.get(e.form, 0) + 1
        # boost in proportion to how often the form was actually misplaced
        focus = {f: 60 * c for f, c in counts.items()} or None
        bounds = corpus.boundaries(mined)
        print(f"⭐ mined {len(mined)} class confusions from {a.from_ledger}")
        print(f"   forms to target: "
              + ", ".join(f"{f}×{c}" for f, c in sorted(counts.items(),
                                                        key=lambda kv: -kv[1])))
        print("   boundaries (most-confused first): "
              + ", ".join(f"{x}/{y}:{n}" for (x, y), n in bounds.most_common(6)))
        for old in STALE_PREFLIGHT_CONFUSED:
            if old in counts:
                print(f"   ⚠️ {old} is STILL confused — the old boost did not take")
        gone = [f for f in STALE_PREFLIGHT_CONFUSED if f not in counts]
        if gone:
            print(f"   ✅ fixed since the pre-flight, no longer boosted: "
                  f"{', '.join(gone)}")

    pairs = corpus.build(a.n + a.eval, seed=a.seed, balanced=not a.naive,
                         focus_forms=focus, slot_floor=a.slot_floor)
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

    # ⭐⭐ SLOT OCCUPANCY IS PRINTED BESIDE PER-FORM EXPOSURE, because run 3 had
    # flat exposure and 16 of 48 errors in one slot. Exposure teaches the FORM;
    # occupancy teaches the FUNCTION, and only one of them was ever reported.
    print("\n  slot occupancy (the number run 3's report did not carry):")
    nodes = sum(1 for p in pairs for _ in corpus._walk(p.scene.node))  # noqa: SLF001
    filled = {s: 0 for s in ("orient", "modal", "aspect_root", "quant",
                             "tense", "degree")}
    for p in pairs:
        for nd in corpus._walk(p.scene.node):                 # noqa: SLF001
            if nd.orient:
                filled["orient"] += 1
            if nd.aspect:
                filled["aspect_root"] += 1
            for s, v in (("modal", nd.modal), ("quant", nd.quant),
                         ("tense", nd.tense), ("degree", nd.degree)):
                if v is not None:
                    filled[s] += 1
    for s, c in filled.items():
        mark = " ← floored" if a.slot_floor and s in (
            "modal", "aspect_root", "quant", "tense", "degree") else ""
        print(f"    {s:<13}{c:>8}/{nodes} = {100 * c / nodes:>5.1f}%{mark}")

    if focus:
        exp = corpus.class_exposure(pairs)
        print("\n  targeted positives (the mined confusions, in their CORRECT slot):")
        for form in sorted(focus):
            cls = next((c for c in corpus.CLASSES if form in lex[c]), None)
            if cls is None:
                continue
            print(f"    {form:<6} class {cls} · {exp[cls][form]:>5} sightings "
                  f"· {lex[cls][form]}")

    short = [c for c in corpus.CLASSES
             if rep["by_class"][c]["covered"] != rep["by_class"][c]["forms"]]
    if short:
        raise SystemExit(f"⛔ classes not fully covered: {short}. Refusing to "
                         "write a corpus that cannot teach the whole partition.")

    out_dir.mkdir(parents=True, exist_ok=True)
    train, ev = pairs[:a.n], pairs[a.n:]

    # ⭐⭐ §8.2 — THE MINIMAL PAIRS. Two legal scenes differing in ONE slot, so
    # the only thing that varies between the rows is the class assignment. ⛔ They
    # go into TRAIN ONLY — a held-out set that shares a generator with a targeted
    # intervention is measuring its own training data.
    #
    # ⚠️ BE PRECISE ABOUT WHAT IS AND IS NOT COMPARABLE. `--slot-floor` changes
    # the sampling distribution, so eval.jsonl is NOT the same set run 3 held
    # out, and `eval_loss` is therefore NOT comparable across the two runs.
    # ⭐ THE GATE IS UNAFFECTED: F-LOCAL scores an independent battery
    # (`probes.build(seed=7)`) that no corpus setting can reach. eval_loss is a
    # training-time diagnostic here, nothing more, and must not be quoted as a
    # cross-run improvement.
    if a.contrastive and mined:
        extra = corpus.contrastive_pairs(mined, per_confusion=a.contrastive,
                                         seed=a.seed)
        print(f"\n  ⭐ {len(extra):,} contrastive minimal pairs "
              f"({a.contrastive} per confusion × {len(mined)} confusions)")
        print("     sample — the same base scene, one slot apart:")
        for p in extra[:2]:
            print(f"       {p.surface}")
            print(f"         {p.english}")
        train = train + extra

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
        path = out_dir / f"{name}.jsonl"
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

    # ⛔⛔ "HOLD COMPUTE CONSTANT" MEANS TOKENS, NOT ROWS, AND THE TWO COME APART
    # HERE. Raising slot occupancy makes every scene longer; adding contrastive
    # pairs adds rows. Either one silently buys extra gradient steps, and a
    # render number that improved because the run was bigger is not evidence that
    # the intervention worked. The count is printed so `--n` can be trimmed to
    # match run 3's budget rather than assumed to.
    approx = sum(len(p.prompt().split()) + len(p.surface.split()) + 12
                 for p in train)
    print(f"\n  ⛔ COMPUTE BUDGET — approx {approx:,} whitespace tokens over "
          f"{len(train):,} train rows ({approx / max(1, len(train)):.1f}/row)")
    print("     run 3's corpus, for comparison: 80,000 rows · "
          "110 mean real tokens/row")
    print("     ⇒ trim --n so the TOKEN total matches, or the render delta is "
          "confounded with a longer run.")

    meta = out_dir / "meta.json"
    meta.write_text(json.dumps({
        "n_train": len(train), "n_eval": len(ev), "seed": a.seed,
        "balanced": not a.naive, "focus_forms": focus,
        "slot_floor": a.slot_floor, "contrastive_per_confusion": a.contrastive,
        "mined_confusions": len(mined),
        "mined_from": None if a.stale_list else a.from_ledger,
        "approx_train_tokens": approx,
        "slot_occupancy": {s: c / nodes for s, c in filled.items()},
        "lexicon": C.load()["_hash"], "exposure": rep},
        indent=2, ensure_ascii=False), encoding="utf-8", newline="")
    print(f"  wrote {meta}")
    print("\n⛔ nothing trained. The corpus is an input, not a run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
