"""2b step 1 — build the dataset and run the pre-registered baselines.

KILL 1 is checkable here, before any transformer exists.
Pre-reg: docs/PREREG_2B_LISTENER_2026_08_19.md (LOCK 612f37ba)
"""
from __future__ import annotations
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.listener import baselines, data, tokenizer as tk   # noqa: E402
from tlon.referents import schema                            # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
PER_REF = 4000


def main() -> int:
    OUT.mkdir(exist_ok=True)
    rs = schema.load()
    refs = rs.seeds()

    print("=" * 74)
    print("2b BASELINES — pre-reg LOCK 612f37ba")
    print("=" * 74)
    print(f"  vocab size           {tk.size()} tokens (morpheme-per-token)")
    print(f"  referents            {len(refs)}")

    t0 = time.time()
    ds = data.build(refs, per_ref=PER_REF)
    dt = time.time() - t0
    print(f"  built in             {dt:.1f}s")
    print(f"  train                {len(ds.train)}")
    print(f"  test (random)        {len(ds.test_random)}")
    print(f"  test (novel decor)   {len(ds.test_novel)}")
    print(f"  canonical dupes cut  {ds.dropped_dupes}")

    tests = {"random": ds.test_random, "novel": ds.test_novel}
    print("\n  --- pre-registered baselines ---")
    maj = baselines.majority(ds.train, ds.test_random)
    print(f"  majority class        {100 * maj:5.2f}%   (floor; 20 classes = 5.00%)")

    t0 = time.time()
    bor = baselines.bag_of_roots(ds.train, tests, ds.n_classes)
    print(f"  bag-of-roots  train   {100 * bor['train']:5.2f}%")
    print(f"  bag-of-roots  random  {100 * bor['random']:5.2f}%")
    print(f"  bag-of-roots  novel   {100 * bor['novel']:5.2f}%   "
          f"(fit {time.time() - t0:.1f}s)")

    null = baselines.shuffled_label_null(ds.train, ds.test_random, ds.n_classes)
    print(f"  shuffled-label null   {100 * null:5.2f}%   "
          f"({'OK — at chance' if null < 0.12 else 'LEAK — investigate'})")

    print("\n" + "=" * 74)
    print("KILL 1 CHECK — is the task trivial?")
    print("=" * 74)
    print(f"  bag-of-roots on the honest (novel-decoration) split: "
          f"{100 * bor['novel']:.2f}%")
    print("  KILL 1 fires if the transformer lands within 2 points of this.")
    if bor["novel"] > 0.95:
        print("  ⚠ Bag-of-roots is already near-ceiling. The transformer has")
        print("    almost no headroom, so KILL 1 is LIKELY to fire and the")
        print("    finding will be about the REFERENT SET, not the model.")
    elif bor["novel"] > 0.75:
        print("  ⚠ Bag-of-roots is strong. Headroom is thin.")
    else:
        print("  Headroom exists — structure may matter. Proceed to the model.")

    blob = {"per_ref": PER_REF, "vocab": tk.size(),
            "n_train": len(ds.train), "n_test_random": len(ds.test_random),
            "n_test_novel": len(ds.test_novel),
            "dropped_dupes": ds.dropped_dupes, "majority": maj,
            "bag_of_roots": {k: v for k, v in bor.items() if k != "_preds"},
            "shuffled_null": null}
    (OUT / "2b_baselines.json").write_text(json.dumps(blob, indent=2),
                                           encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / '2b_baselines.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
