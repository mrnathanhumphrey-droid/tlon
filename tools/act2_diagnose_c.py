"""DIAGNOSIS C — diversity vs TRAINING STEP, across saved checkpoints.

⛔⛔ THE RE-RUN IS ITS OWN DIAGNOSTIC, WHICH IS THE POINT. Diagnoses A/B/D ruled
out the corpus, input-conditioning and the weights on FREE artefacts. C is the
one that could not be answered without checkpoints, so the retrain saves them and
this reads the curve:

    diversity ROSE THEN FELL  ⇒ overtrained — stop at the peak, do not retrain longer
    diversity NEVER ROSE      ⇒ not a training-duration problem at all
    diversity ROSE AND HELD   ⇒ nothing here to fix; the earlier reading was the harness

⛔ Two checkpoints cannot tell the first case from the third, which is why
`--save-steps` exists.

⭐ Decoding is GREEDY here on purpose. With varied inputs, greedy is the honest
native signature: the same meaning must give the same scene, different meanings
different scenes. Sampling would inflate `varied` for free and hide a real
collapse behind the temperature.
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

from tlon.act2 import diversity as DV                          # noqa: E402
from tlon.act2 import probes                                   # noqa: E402
from tlon.act2.llm import LLMSpeaker                           # noqa: E402
from tlon.product import schema as PS                          # noqa: E402


def _valid(proposals) -> int:
    ok = 0
    for p in proposals:
        try:
            PS.validate(p)
            ok += 1
        except Exception:                                      # noqa: BLE001
            pass
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter-root", default="runs/act2/adapter")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--out", default="runs/act2/logs/diagnosis_c.json")
    a = ap.parse_args()

    from act2_backends import LocalBackend

    root = pathlib.Path(a.adapter_root)
    ckpts = sorted((d for d in root.glob("checkpoint-*") if d.is_dir()),
                   key=lambda d: int(d.name.split("-")[1]))
    if root.joinpath("adapter_config.json").exists():
        ckpts.append(root)                                     # the final adapter
    if not ckpts:
        raise SystemExit(f"⛔ no checkpoints under {root}")

    battery = probes.build(seed=7, n_prod=64, n_comp=64)
    histories = [tuple(p.surface for p in battery.comprehension[i:i + 1])
                 for i in range(a.n)]

    print(f"DIAGNOSIS C — {len(ckpts)} checkpoints · n={a.n} · greedy\n")
    print(f"  {'step':>7}  {'distinct':>8} {'repeat':>7} {'response':>8} "
          f"{'depend':>7}  {'valid':>7}  verdict")
    rows = []
    for ck in ckpts:
        step = (int(ck.name.split("-")[1]) if ck.name.startswith("checkpoint-")
                else -1)                                       # -1 = final
        back = LocalBackend(a.model, adapter=str(ck))
        sp = LLMSpeaker("native", back, card=False)
        varied = [sp.speak(h, i + 1) for i, h in enumerate(histories)]
        repeated = [sp.speak((), 1) for _ in range(a.n)]
        try:
            d = DV.measure(repeated=repeated, varied=varied)
            row = dict(step=step, distinct=d.distinct, repeat=d.repeat_rate,
                       response=d.response_rate, dependence=d.dependence,
                       verdict=d.verdict, valid=_valid(varied), n=a.n)
        except DV.DegenerateSpeaker as exc:
            row = dict(step=step, distinct=None, repeat=None, response=None,
                       dependence=None, verdict=f"REFUSED: {exc}",
                       valid=_valid(varied), n=a.n)
        rows.append(row)
        lbl = "final" if step < 0 else str(step)
        print(f"  {lbl:>7}  {str(row['distinct']):>8} "
              f"{'' if row['repeat'] is None else format(row['repeat'], '.2f'):>7} "
              f"{'' if row['response'] is None else format(row['response'], '.2f'):>8} "
              f"{'' if row['dependence'] is None else format(row['dependence'], '+.2f'):>7}"
              f"  {row['valid']:>3}/{a.n:<3}  {row['verdict'][:46]}")
        del back
        import gc
        import torch
        gc.collect()
        torch.cuda.empty_cache()

    # ⛔ THE READING IS COMPUTED, NOT EYEBALLED. A curve a human squints at is a
    # curve two humans read differently.
    curve = [r["dependence"] for r in rows if r["dependence"] is not None]
    if len(curve) < 2:
        reading = "⛔ too few scoreable checkpoints to read a curve"
    else:
        peak = max(range(len(curve)), key=lambda i: curve[i])
        rose = curve[peak] > curve[0] + 0.1
        fell = curve[-1] < curve[peak] - 0.1
        reading = ("⛔ OVERTRAINED — diversity rose then fell; stop near the peak"
                   if rose and fell else
                   "⛔ NEVER ROSE — not a training-duration problem"
                   if not rose else
                   "✅ ROSE AND HELD — no duration problem to fix")
    print(f"\n  READING: {reading}")

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rows": rows, "reading": reading}, indent=2),
                   encoding="utf-8", newline="")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
