"""Null band across seeds — prerequisite of PREREG 3c49ad47.

The single-seed band (<=0.03 pts) has no variance estimate, so it cannot justify
KILL A's 1.0 pt threshold. This re-runs the whole thing per seed: fresh data,
fresh listener, fresh paired scramble probe.
"""
from __future__ import annotations
import json
import pathlib
import random
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.listener import data, evaluate as ev, train as tr   # noqa: E402
from tlon.listener import tokenizer as tk                     # noqa: E402
from tlon.referents import schema                             # noqa: E402
from cipher_control import CHANNELS, scramble                 # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
SEEDS = [11, 23, 37, 53, 71]
PER_REF = 800


def main() -> int:
    OUT.mkdir(exist_ok=True)
    rs = schema.load_all()
    refs = rs.referents
    groups = {r.minimal_pair for r in refs if r.minimal_pair}
    per_seed = []

    for si, seed in enumerate(SEEDS):
        ds = data.build(refs, per_ref=PER_REF, seed=seed)
        cfg = tr.TrainCfg(seed=seed, epochs=10)
        model = tr.train(ds.train, ds.test_random, ds.n_classes, cfg, verbose=False)
        rng = random.Random(seed * 7)
        row = {"seed": seed}
        for ch, _ in CHANNELS:
            orig, scr = [], []
            for ex in ds.test_novel:
                s = scramble(ex.surface, ch, rng)
                if s is None:
                    continue
                orig.append(ex)
                scr.append(data.Example(label=ex.label, ref_id=ex.ref_id,
                                        surface=s, uid=ex.uid,
                                        ids=tk.encode(s), dec_key=ex.dec_key))
            if not scr:
                continue
            b = ev.within_pair(orig, tr.predict(model, orig, cfg).tolist(), refs, groups)
            a = ev.within_pair(scr, tr.predict(model, scr, cfg).tolist(), refs, groups)
            row[ch] = b["acc"] - a["acc"]
        per_seed.append(row)
        print(f"  seed {seed} ({si + 1}/{len(SEEDS)}): " +
              "  ".join(f"{k} {100 * v:+.2f}" for k, v in row.items() if k != "seed"))

    print("\n" + "=" * 70)
    print("NULL BAND — mean +/- sd over seeds (pts)")
    print("=" * 70)
    summary = {}
    for ch, why in CHANNELS:
        vals = [100 * r[ch] for r in per_seed if ch in r]
        if len(vals) < 2:
            continue
        m, sd = statistics.mean(vals), statistics.stdev(vals)
        summary[ch] = {"mean": m, "sd": sd, "max_abs": max(abs(v) for v in vals)}
        print(f"  {ch:14} {m:+6.2f} +/- {sd:4.2f}   worst |{max(abs(v) for v in vals):.2f}|")

    noinfo = ["orient_order", "coda", "degree", "aspect_reps"]
    band = max(summary[c]["max_abs"] for c in noinfo if c in summary)
    sd_max = max(summary[c]["sd"] for c in noinfo if c in summary)
    thresh = max(0.5, band + 3 * sd_max)
    print(f"\n  Widest honest excursion on a no-information channel: {band:.2f} pts")
    print(f"  Largest sd among them:                                {sd_max:.2f} pts")
    print(f"  => defensible KILL A threshold: {thresh:.2f} pts")
    print(f"     (PREREG 3c49ad47 pre-set 1.0 pt; "
          f"{'CONSISTENT' if thresh <= 1.0 else 'TOO TIGHT — record a deviation'})")

    (OUT / "null_band_seeds.json").write_text(json.dumps(
        {"seeds": SEEDS, "per_seed": per_seed, "summary": summary,
         "threshold": thresh}, indent=2, default=float),
        encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'null_band_seeds.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
