"""Does the auditor beat chance on data we KNOW is honest?

A detector that sits at 50% on honest glosses cannot detect anything, so this
gate runs before the auditor is trusted with any phase-3 claim.

Two conditions, both required:
  HONEST   -- real glosses from the phase-2 sampler. Must be > chance.
  SCRAMBLED -- the same glosses with the two candidate names shuffled at random
               relative to the gloss. Must sit AT chance, or the auditor is
               reading something other than the description.
"""
from __future__ import annotations
import json
import pathlib
import random
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

from tlon.grammar.gloss import gloss as to_gloss   # noqa: E402
from tlon.grammar.parse import parse, render       # noqa: E402
from tlon.listener import auditor                  # noqa: E402
from tlon.referents import schema                  # noqa: E402
from tlon.selfplay import scenes as gen            # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
N_PER_PAIR = 12


def main() -> int:
    OUT.mkdir(exist_ok=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    rs = schema.load_all()
    refs = rs.referents
    pairs = {}
    for r in refs:
        if r.minimal_pair:
            pairs.setdefault(r.minimal_pair, []).append(r)
    pairs = {k: v for k, v in pairs.items() if len(v) == 2}

    print("=" * 74)
    print(f"AUDITOR VALIDATION — {auditor.MODEL_ID} (frozen, log-prob choice)")
    print("=" * 74)
    print(f"  device {dev} · {len(pairs)} pairs · {N_PER_PAIR} glosses each")

    rng = random.Random(99)
    items, scrambled = [], []
    for pid, (a, b) in sorted(pairs.items()):
        for _ in range(N_PER_PAIR):
            which = rng.randrange(2)
            ref = (a, b)[which]
            sc = gen.sample(ref, rng, blend_pool=[a, b], blend_p=0.0)
            g = to_gloss(sc)
            items.append((g, a.name, b.name, which))
            scrambled.append((g, a.name, b.name, rng.randrange(2)))

    t0 = time.time()
    honest = auditor.audit_pairs(items, device=dev)
    ctrl = auditor.audit_pairs(scrambled, device=dev)
    dt = time.time() - t0

    print(f"\n  HONEST glosses     {100 * honest.acc:5.1f}%  "
          f"({honest.correct}/{honest.n})")
    print(f"  RANDOM label ctrl  {100 * ctrl.acc:5.1f}%  "
          f"({ctrl.correct}/{ctrl.n})   must sit at ~50%")
    print(f"  {dt:.0f}s total, {1000 * dt / (2 * len(items)):.0f}ms per choice")

    # per-pair, so a single strong pair cannot carry the average
    print("\n  per pair:")
    per = {}
    for pid, (a, b) in sorted(pairs.items()):
        sub = [it for it in items if it[1] == a.name and it[2] == b.name]
        r = auditor.audit_pairs(sub, device=dev)
        per[pid] = r.acc
        bar = "#" * int(round(20 * r.acc))
        print(f"    {pid:5} {100 * r.acc:5.1f}%  {bar}")

    print("\n" + "=" * 74)
    ok = honest.acc > 0.60 and 0.35 < ctrl.acc < 0.65
    if ok:
        print("  ✓ USABLE — above chance on honest glosses, at chance on the")
        print("    randomised control. The auditor is reading the description.")
    else:
        if honest.acc <= 0.60:
            print("  ✗ TOO WEAK — cannot separate honest glosses from each other.")
            print("    It would be blind to a cipher too. Needs a stronger model")
            print("    or an easier framing before phase 3 can rely on it.")
        if not 0.35 < ctrl.acc < 0.65:
            print("  ✗ CONTROL FAILED — accuracy on randomised labels is not at")
            print("    chance, so the auditor is keying on something other than")
            print("    the gloss (name length, ordering, priors).")

    (OUT / "auditor_validation.json").write_text(json.dumps(
        {"model": auditor.MODEL_ID, "honest": honest.acc, "control": ctrl.acc,
         "n": honest.n, "per_pair": per, "usable": ok}, indent=2),
        encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'auditor_validation.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
