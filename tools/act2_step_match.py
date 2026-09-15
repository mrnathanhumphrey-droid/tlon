"""Derive arm A's subsample from the corpus that was ACTUALLY sha-verified.

    python tools/act2_step_match.py --corpus runs/act2/corpus_ct-s20624/train.jsonl \
        --out runs/act2/corpus_quarter-s20624/train.jsonl \
        --manifest runs/act2/epochlev/step_match.json --repeat 4 --seed 20624

⛔⛔ RUN THIS AFTER `corpus_pin` PASSES, NEVER BEFORE. The whole point is that the
row count comes from the rebuilt, sha-verified corpus. A subsample size copied
from a local file is a number about a DIFFERENT corpus -- the pinned one need not
exist on any developer's disk, and did not.

⭐ Exits 1 when the arms cannot be matched inside the pre-declared tolerance, so
an awkward row count blocks a confounded run rather than being waved through.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.act2.step_match import (STEP_MATCH_TOL,            # noqa: E402
                                  derive_subsample)


def _sha16(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True,
                    help="the SHA-VERIFIED train.jsonl — arm B's corpus")
    ap.add_argument("--out", required=True, help="arm A's subsample train.jsonl")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--repeat", type=int, default=4)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--accum", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20624)
    ap.add_argument("--tol", type=float, default=STEP_MATCH_TOL)
    a = ap.parse_args(argv)

    src = pathlib.Path(a.corpus)
    rows = src.read_text(encoding="utf-8").splitlines()
    rows = [r for r in rows if r.strip()]
    n = len(rows)
    print("  corpus %s · %d rows · sha %s" % (src, n, _sha16(src)))

    r = derive_subsample(n, batch=a.batch, accum=a.accum, repeat=a.repeat,
                         tol=a.tol)

    # ⭐⭐ BOTH ARMS' EXACT COUNTS, NEVER THE WORD "MATCHED". A reader has to be
    # able to judge the match QUALITY, which a boolean hides.
    print("  arm B  %d steps   (full corpus x 1 epoch)" % r["s_b"])
    if r["m"] is not None:
        print("  arm A  %d steps   (%d rows x %d epochs, %d steps/epoch)"
              % (r["s_a"], r["m"], a.repeat, r["per_epoch"]))
        print("  Δsteps %d  ·  Δfrac %.5f%%  ·  declared tol %.4f%%"
              % (r["delta_steps"], 100 * r["delta_frac"], 100 * a.tol))

    if not r["ok"]:
        print("\n⛔⛔ STEP MATCH REFUSED\n   %s" % r["why"])
        mp = pathlib.Path(a.manifest)
        mp.parent.mkdir(parents=True, exist_ok=True)
        # ⛔ The refusal is RECORDED too. A run that refuses and leaves no trace
        # teaches the next person nothing about why.
        mp.write_text(json.dumps({**r, "seed": a.seed, "refused": True,
                                  "corpus": str(src), "corpus_rows": n,
                                  "corpus_sha16": _sha16(src)}, indent=2),
                      encoding="utf-8")
        return 1

    rng = random.Random(a.seed)
    idx = list(range(n))
    rng.shuffle(idx)
    keep = sorted(idx[:r["m"]])
    outp = pathlib.Path(a.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(rows[i] for i in keep) + "\n",
                    encoding="utf-8", newline="")

    manifest = {
        **r,
        "seed": a.seed, "refused": False,
        "corpus": str(src), "corpus_rows": n, "corpus_sha16": _sha16(src),
        "subsample": str(outp), "subsample_rows": len(keep),
        "subsample_sha16": _sha16(outp),
        # ⛔ These are PREDICTIONS from the trainer's own formula. The record is
        # `state.max_steps` on each arm; re-check with `check_match` on those.
        "step_counts_are": "PREDICTED — re-check against state.max_steps per arm",
        "tol_declared_in": "PREREG_EPOCHS_LEVER_2026_09_14.md §2.1",
    }
    mp = pathlib.Path(a.manifest)
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("  ✅ wrote %s (%d rows, sha %s)"
          % (outp, len(keep), manifest["subsample_sha16"]))
    print("  ✅ manifest %s" % mp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
