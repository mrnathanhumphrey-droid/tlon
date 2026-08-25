"""2b.2 — train the listener and score it. PREREG 080bc40f.

Local, no Lambda. Headline numbers are WITHIN-PAIR, never overall accuracy.
"""
from __future__ import annotations
import collections
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

from tlon.listener import baselines, data, evaluate as ev, train as tr  # noqa: E402
from tlon.listener import tokenizer as tk                              # noqa: E402
from tlon.listener.model import Listener                               # noqa: E402
from tlon.referents import schema                                      # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
PER_REF = 1500


def pct(t) -> str:
    m, lo, hi = t
    return f"{100 * m:5.1f}%  [{100 * lo:4.1f}, {100 * hi:4.1f}]"


def main() -> int:
    OUT.mkdir(exist_ok=True)
    rs = schema.load_all()
    refs = rs.referents
    persp = {r.minimal_pair for r in refs if r.minimal_pair and r.minimal_pair.startswith("J")}
    diag = {r.minimal_pair for r in refs if r.minimal_pair and r.minimal_pair.startswith("P")}

    print("=" * 76)
    print("2b.2 LISTENER — PREREG 080bc40f")
    print("=" * 76)
    print(f"  referents {len(refs)}  ({len(persp)} perspective pairs, "
          f"{len(diag)} diagnostic pairs)")
    print(f"  vocab     {tk.size()} morpheme tokens")

    t0 = time.time()
    ds = data.build(refs, per_ref=PER_REF)
    print(f"  data      {len(ds.train)} train / {len(ds.test_random)} random / "
          f"{len(ds.test_novel)} novel  ({time.time() - t0:.0f}s, "
          f"{ds.dropped_dupes} canonical dupes cut)")

    cfg = tr.TrainCfg()
    print(f"  device    {cfg.device}")
    model = Listener(ds.n_classes)
    print(f"  params    {model.n_params():,}\n")

    t0 = time.time()
    model = tr.train(ds.train, ds.test_random, ds.n_classes, cfg)
    print(f"    trained in {time.time() - t0:.0f}s\n")

    results = {}
    for split, rows in (("random", ds.test_random), ("novel", ds.test_novel)):
        preds = tr.predict(model, rows, cfg).tolist()
        overall = sum(p == r.label for p, r in zip(preds, rows)) / len(rows)
        wp = ev.within_pair(rows, preds, refs, persp)
        wd = ev.within_pair(rows, preds, refs, diag)
        off = ev.off_pair_rate(rows, preds, refs)
        results[split] = {"overall": overall, "persp": wp, "diag": wd, "off": off}

        print(f"  --- {split} split ---")
        print(f"  overall (context only)      {100 * overall:5.1f}%")
        print(f"  WITHIN perspective pairs    {pct((wp['acc'], wp['lo'], wp['hi']))}  n={wp['n']}")
        print(f"  WITHIN diagnostic pairs     {pct((wd['acc'], wd['lo'], wd['hi']))}  n={wd['n']}")
        print(f"  predicted outside the pair  {100 * off:5.1f}%")
        print("  per channel:")
        for ch, t in sorted(wd["per_channel"].items(),
                            key=lambda x: -x[1][0]):
            print(f"      {ch:12} {pct(t)}")
        print()

    # baselines on the same items
    print("  --- baselines, same test items ---")
    bor = baselines.bag_of_roots(ds.train, {"novel": ds.test_novel}, ds.n_classes)
    null = baselines.shuffled_label_null(ds.train, ds.test_novel, ds.n_classes)
    bor_p = bor["_preds"]["novel"]
    model_p = tr.predict(model, ds.test_novel, cfg).tolist()
    diff = ev.paired_diff(ds.test_novel, model_p, bor_p)
    print(f"  bag-of-roots overall        {100 * bor['novel']:5.1f}%")
    print(f"  shuffled-label null         {100 * null:5.1f}%")
    print(f"  model - bag-of-roots        {pct(diff)}  (paired)")

    # ── pre-registered kill checks ────────────────────────────────────────
    n = results["novel"]
    P, D = n["persp"]["acc"], n["diag"]["acc"]
    chs = [v[0] for v in n["diag"]["per_channel"].values()]
    spread = (max(chs) - min(chs)) if chs else 0.0
    gap = results["random"]["diag"]["acc"] - D

    print("\n" + "=" * 76)
    print("PRE-REGISTERED KILL CHECKS (novel-decoration split)")
    print("=" * 76)
    kills = []
    if D <= 0.55 or n["diag"]["lo"] < 0.50:
        kills.append("A")
    print(f"  A  no structure read      diag {100 * D:.1f}% "
          f"(lo {100 * n['diag']['lo']:.1f}%)  -> "
          f"{'FIRED' if 'A' in kills else 'not fired'}")
    if P >= 0.95 and D <= 0.60:
        kills.append("B")
    print(f"  B  shortcut only          persp {100 * P:.1f}% / diag {100 * D:.1f}%  -> "
          f"{'FIRED' if 'B' in kills else 'not fired'}")
    if chs and spread <= 0.05:
        kills.append("C")
    print(f"  C  flat channel profile   spread {100 * spread:.1f} pts  -> "
          f"{'FIRED' if 'C' in kills else 'not fired'}")
    if gap > 0.10:
        kills.append("D")
    print(f"  D  leakage                random-novel {100 * gap:+.1f} pts  -> "
          f"{'FIRED' if 'D' in kills else 'not fired'}")

    print(f"\n  KILLS FIRED: {', '.join(kills) if kills else 'none'}")

    blob = {"prereg": "080bc40f", "per_ref": PER_REF,
            "params": model.n_params(), "results": results,
            "bag_of_roots": bor["novel"], "null": null,
            "paired_diff": diff, "kills": kills}
    (OUT / "2b2_results.json").write_text(
        json.dumps(blob, indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / '2b2_results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
