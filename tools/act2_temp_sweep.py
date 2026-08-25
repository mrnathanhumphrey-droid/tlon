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
    ap.add_argument("--depth", type=int, default=F.MIN_SWEEP_HISTORY_DEPTH,
                    help="history depth to probe at. ⛔ DEPTH 1 IS REFUSED.")
    ap.add_argument("--out", default="runs/act2/logs/temp_sweep.json")
    a = ap.parse_args()

    # ⛔⛔ THE BUG THIS GUARD EXISTS FOR SHIPPED A VERDICT. The first version of
    # this sweep built one-surface histories, and at depth 1 the model
    # deterministically echoes `parse(history)` — 1/8 distinct at temperature
    # 0.0 AND at 1.5. Every grid point therefore read "cannot vary", the tool
    # concluded "NO USABLE TEMPERATURE ON THIS GRID", and that sentence was
    # recorded as a fact about the model. It was a fact about the probe.
    if a.depth < F.MIN_SWEEP_HISTORY_DEPTH:
        raise SystemExit(
            f"⛔ REFUSED: --depth {a.depth} is below {F.MIN_SWEEP_HISTORY_DEPTH}. "
            "At depth 1 the model is a deterministic echo of parse(history), so "
            "EVERY temperature reads 'cannot vary' and the sweep measures its "
            "own prompt. A floor derived here would be an artefact wearing a "
            "measurement's clothes — which is what happened the first time.")

    from act2_backends import LocalBackend

    battery = probes.build(seed=7, n_prod=64, n_comp=64)
    pool = [p.surface for p in battery.comprehension]
    #: ONE fixed history, at real conversational depth.
    one_history = tuple(pool[:a.depth])
    #: n DIFFERENT histories, each the same depth, none overlapping the above.
    varied = [tuple(pool[a.depth + i * a.depth: a.depth + (i + 1) * a.depth])
              for i in range(a.n)]
    varied = [h for h in varied if len(h) == a.depth]

    print(f"TEMPERATURE SWEEP · n={a.n} per point · depth={a.depth} · "
          f"adapter={a.adapter}")
    print(f"⛔ the floor must clear BOTH: it can vary, AND it stays legal "
          f"(>= {MIN_VALIDITY:.0%})")
    print(f"⛔ probing at depth {a.depth}, NOT depth 1 — at depth 1 the model is "
          f"a deterministic echo and every point reads 'cannot vary'\n")
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
    # ⛔⛔ WRITE THE LOUD FALLBACK BEFORE THE HAPPY PATH. "No usable temperature"
    # has TWO very different causes and the first version of this tool collapsed
    # them into one sentence. If the speaker VARIES everywhere but is never
    # legal, the sweep has not found a temperature fact at all — it has
    # re-measured the depth-competence gap that F-LOCAL and the multi-turn
    # corpus own. Saying "the arena cannot be run on this model" there would
    # blame the sampler for the corpus's missing task.
    can_vary_somewhere = [r for r in rows if r["can_vary"]]
    legal_nowhere = not any(r["legal"] for r in rows)
    if not usable and can_vary_somewhere and legal_nowhere:
        floor = None
        print(f"\n  ⚠️⚠️ NO USABLE TEMPERATURE — BUT THIS IS NOT A TEMPERATURE "
              f"FINDING.\n  The speaker VARIES at "
              f"{len(can_vary_somewhere)}/{len(rows)} grid points and is legal "
              f"at NONE of them (bar {MIN_VALIDITY:.0%} at depth {a.depth}).\n"
              "  ⇒ the binding constraint is DEPTH COMPETENCE, not the sampler. "
              "That is the\n     multi-turn corpus's gap, and no temperature "
              "setting can close it.\n  ⛔ A floor MUST NOT be declared from "
              "this run.")
    elif usable:
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
    out.write_text(json.dumps(
        {"rows": rows, "measured_floor": floor,
         "declared_floor": F.MIN_ARENA_TEMPERATURE,
         "declared_floor_provenance": F.MIN_ARENA_TEMPERATURE_PROVENANCE,
         "declared_floor_is_measured": F.MIN_ARENA_TEMPERATURE_IS_MEASURED,
         # ⛔ THE DEPTH IS RECORDED BESIDE THE RESULT, NOT ONLY IN THE COMMAND.
         # The superseded sweep's JSON does not say what depth it ran at, which
         # is why its verdict read as a fact about the model for a full day.
         "history_depth": a.depth,
         "min_sweep_history_depth": F.MIN_SWEEP_HISTORY_DEPTH,
         "min_validity": MIN_VALIDITY}, indent=2, ensure_ascii=False),
        encoding="utf-8", newline="")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
