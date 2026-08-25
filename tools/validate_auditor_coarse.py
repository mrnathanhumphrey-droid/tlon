"""Auditor validation, take 2 — COARSE discrimination.

Take 1 asked the auditor to tell two readings of ONE scene apart ("the light's
side" vs "the night's side"). It scored 48.3% — chance. That is the wrong
question: those names are near-synonymous and the discrimination is not what an
anti-cipher detector needs.

The job is to notice a gloss that says nothing descriptive. So: pick the correct
referent against distractors drawn from SEMANTICALLY DISTANT territory (no
shared roots). An honest gloss should beat chance; a ciphered one cannot, having
no imagery to go on.

Two required conditions, as before:
  HONEST    -- real glosses. Must beat 1/K.
  SHUFFLED  -- gloss paired with someone else's candidate set. Must sit at 1/K.
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
from tlon.listener import auditor                  # noqa: E402
from tlon.referents import schema                  # noqa: E402
from tlon.selfplay import scenes as gen            # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
K = 4          # candidates per item
N = 240


def main() -> int:
    OUT.mkdir(exist_ok=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    rs = schema.load_all()
    refs = rs.referents
    rng = random.Random(2024)

    print("=" * 74)
    print(f"AUDITOR VALIDATION 2 — coarse, {K}-way, chance = {100 / K:.0f}%")
    print("=" * 74)

    def distant(target):
        """Distractors sharing no roots with the target — genuinely other."""
        tr = set(target.roots())
        pool = [r for r in refs if r.id != target.id and not (set(r.roots()) & tr)]
        return rng.sample(pool, K - 1) if len(pool) >= K - 1 else None

    items, shuffled = [], []
    tries = 0
    while len(items) < N and tries < N * 10:
        tries += 1
        ref = rng.choice(refs)
        others = distant(ref)
        if not others:
            continue
        sc = gen.sample(ref, rng, blend_pool=refs, blend_p=0.0)
        g = to_gloss(sc)
        names = [ref.name] + [o.name for o in others]
        order = list(range(K))
        rng.shuffle(order)
        shown = [names[i] for i in order]
        gold = order.index(0)
        items.append((g, shown, gold))
        shuffled.append((g, shown, rng.randrange(K)))

    print(f"  {len(items)} items · distractors share NO roots with the target")
    t0 = time.time()
    honest = auditor.audit_coarse(items, device=dev)
    ctrl = auditor.audit_coarse(shuffled, device=dev)
    dt = time.time() - t0

    print(f"\n  HONEST glosses      {100 * honest.acc:5.1f}%  "
          f"({honest.correct}/{honest.n})")
    print(f"  SHUFFLED-gold ctrl  {100 * ctrl.acc:5.1f}%  "
          f"({ctrl.correct}/{ctrl.n})   must sit at ~{100 / K:.0f}%")
    print(f"  {dt:.0f}s")

    lo = 100 / K
    ok = honest.acc > (1.5 / K) and (0.6 / K) < ctrl.acc < (1.6 / K)
    print("\n" + "=" * 74)
    if ok:
        print(f"  ✓ USABLE — {100 * honest.acc:.1f}% vs {lo:.0f}% chance, control clean.")
        print("    A gloss with no descriptive content cannot reach this, so a")
        print("    drop toward chance is evidence the imagery went away.")
    else:
        print(f"  ✗ STILL TOO WEAK at {100 * honest.acc:.1f}% (chance {lo:.0f}%).")
        print("    Qwen2.5-1.5B base cannot read these glosses. Phase 3 needs a")
        print("    stronger frozen auditor — a MODEL decision, so Nate's call.")

    (OUT / "auditor_validation_coarse.json").write_text(json.dumps(
        {"model": auditor.MODEL_ID, "k": K, "honest": honest.acc,
         "control": ctrl.acc, "n": honest.n, "usable": ok}, indent=2),
        encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'auditor_validation_coarse.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
