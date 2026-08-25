"""HARDEN 3 (empirical half) — DERIVE the arena temperature floor by measuring it.

⛔⛔ THE FLOOR IS A PRE-REGISTERED PARAMETER, SO IT MUST NOT BE PICKED BY TASTE.
`falsify.MIN_ARENA_TEMPERATURE` decides whether a drift run is scoreable at all,
and a number chosen because it "felt about right" would be a knob wearing a
lock's clothes. This measures the two things that actually bound it:

    TOO COLD  -> the speaker cannot vary, so it cannot drift, and the run returns
                 a clean null indistinguishable from the boundary finding.
    TOO HOT   -> the speaker stops emitting legal Tlön, and drift is confounded
                 with validity-failure (which is F1's whole subject).

⭐ THE FLOOR IS THE COLDEST TEMPERATURE THAT CLEARS BOTH. Reported with the whole
curve, so the choice can be argued with rather than trusted.

    python tools/act2_temp_sweep.py --model <id> --adapter runs/act2/adapter
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.act2 import falsify as F                             # noqa: E402
from tlon.act2 import probes                                   # noqa: E402
from tlon.act2.llm import LLMSpeaker                           # noqa: E402
from tlon.product import schema as PS                          # noqa: E402

GRID = (0.0, 0.2, 0.4, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5)

#: A speaker must stay legal to be worth measuring drift on. Set to F-LOCAL's own
#: bar so the arena is not held to a laxer standard than the gate that admits it.
MIN_VALIDITY = F.NATIVE_THRESHOLD


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--n", type=int, default=16)
    ap.add_argument("--out", default="runs/act2/logs/temp_sweep.json")
    a = ap.parse_args()

    from act2_backends import LocalBackend

    battery = probes.build(seed=7, n_prod=64, n_comp=64)
    one_history = (battery.comprehension[0].surface,)      # ONE fixed history
    varied = [tuple(p.surface for p in battery.comprehension[i:i + 1])
              for i in range(a.n)]

    print(f"TEMPERATURE SWEEP · n={a.n} per point · adapter={a.adapter}")
    print(f"⛔ the floor must clear BOTH: it can vary, AND it stays legal "
          f"(>= {MIN_VALIDITY:.0%})\n")
    print(f"  {'temp':>5}  {'distinct':>9}  {'valid':>8}  reading")

    rows = []
    for temp in GRID:
        back = LocalBackend(a.model, adapter=a.adapter, temperature=temp)
        sp = LLMSpeaker("native", back, card=False)
        # variability: the SAME history, n times
        same = [sp.speak(one_history, 1) for _ in range(a.n)]
        keys = {json.dumps(s, sort_keys=True, ensure_ascii=False) if s else "<none>"
                for s in same}
        # legality: n DIFFERENT histories
        diff = [sp.speak(h, i + 1) for i, h in enumerate(varied)]
        ok = 0
        for p in diff:
            try:
                PS.validate(p)
                ok += 1
            except Exception:                                  # noqa: BLE001
                pass
        vrate = ok / a.n
        can_vary = len(keys) >= F.PRECONDITION_MIN_DISTINCT
        legal = vrate >= MIN_VALIDITY
        reading = ("USABLE" if can_vary and legal else
                   "too cold — cannot vary" if not can_vary and legal else
                   "too hot — illegal emissions" if can_vary else
                   "unusable — both")
        rows.append({"temp": temp, "distinct": len(keys), "n": a.n,
                     "valid": ok, "valid_rate": vrate,
                     "can_vary": can_vary, "legal": legal, "reading": reading})
        print(f"  {temp:>5.1f}  {len(keys):>4}/{a.n:<4}  {ok:>3}/{a.n:<4}  {reading}")
        del back
        import gc
        import torch
        gc.collect()
        torch.cuda.empty_cache()

    usable = [r for r in rows if r["reading"] == "USABLE"]
    if usable:
        floor = min(r["temp"] for r in usable)
        ceiling = max(r["temp"] for r in usable)
        print(f"\n  ⭐ USABLE BAND: {floor} .. {ceiling}")
        print(f"  ⭐ MEASURED FLOOR = {floor}  (coldest temperature that both "
              f"varies and stays legal)")
        cur = F.MIN_ARENA_TEMPERATURE
        if abs(cur - floor) < 1e-9:
            print(f"  ✅ falsify.MIN_ARENA_TEMPERATURE = {cur} MATCHES the "
                  "measurement.")
        else:
            print(f"  ⛔ falsify.MIN_ARENA_TEMPERATURE = {cur} does NOT match the "
                  f"measured floor {floor}. The constant is pre-registered: change "
                  "it deliberately, with this sweep as the evidence, or explain "
                  "why the measurement is wrong.")
    else:
        floor = None
        print("\n  ⛔⛔ NO USABLE TEMPERATURE ON THIS GRID. The arena cannot be "
              "run on this model: every setting either cannot vary or cannot "
              "stay legal. That is a finding about the model, not a config bug.")

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rows": rows, "measured_floor": floor,
                               "declared_floor": F.MIN_ARENA_TEMPERATURE,
                               "min_validity": MIN_VALIDITY}, indent=2),
                   encoding="utf-8", newline="")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
