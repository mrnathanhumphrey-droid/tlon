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


#: ⛔ TWO DIFFERENT THRESHOLDS, BECAUSE THEY ANSWER TWO DIFFERENT QUESTIONS.
#:
#: `_PINNED` is for a metric that is ALGEBRAICALLY stuck — `dependence` computes
#: to exactly 1.00 under greedy decoding, so exact equality is the right test.
#:
#: `_CEILING_BAND` is for a SAMPLED rate. Diagnosis C measures 12 probes per
#: checkpoint, so one item is ±8 %: run 3's real curve was [12, 11, 12, 12, 12,
#: 12], and a rigid 0.999 threshold called that "not at ceiling" over a
#: single-sample dip. A threshold finer than the sampling granularity of the
#: thing it reads is measuring noise.
_PINNED = 0.999
_CEILING_BAND = 0.90


def _saturated(curve: list[float]) -> bool:
    """Algebraically pinned — for `dependence`, which computes to exactly 1.00."""
    return bool(curve) and min(curve) >= _PINNED


def _at_ceiling(curve: list[float]) -> bool:
    """Already at the top when the first checkpoint was taken, and never left."""
    return bool(curve) and curve[0] >= _CEILING_BAND and min(curve) >= _CEILING_BAND


def read_curve(rows: list[dict]) -> str:
    """The automatic reading. ⛔ COMPUTED, NOT EYEBALLED — a curve a human squints
    at is a curve two humans read differently.

    ⛔⛔ THIS KEYED ON `dependence` AND WAS THEREFORE ALWAYS WRONG. Under greedy
    decoding `dependence` is +1.00 for any functioning model, so it had no
    variance to read and the verdict printed "NEVER ROSE" forever regardless of
    what the run did. On run 3 the informative curve was `valid`, which moved
    **0–1/12 → 12/12**, and the verdict never looked at it.

    ⭐ SO THE PRIMARY METRIC IS `valid`, AND THE VERDICT NOW DETECTS ITS OWN
    SATURATION. A verdict that keys on a pinned metric is the vacuity trap one
    level up — a check that can only ever return one value — and the fix is not
    "pick a better metric once", it is "notice when the metric cannot vary".
    """
    scoreable = [r for r in rows if r.get("valid") is not None]
    if len(scoreable) < 2:
        return "⛔ too few scoreable checkpoints to read a curve"

    n = scoreable[0].get("n") or 1
    curve = [r["valid"] / n for r in scoreable]
    steps = [r.get("step", -1) for r in scoreable]

    # ⛔ The old metric is still REPORTED as saturated rather than silently
    # dropped, so its uselessness stays visible instead of being forgotten.
    dep = [r["dependence"] for r in scoreable if r.get("dependence") is not None]
    dep_note = (" · ⚠️ `dependence` is SATURATED at its ceiling here and carries "
                "no information — this is why it cannot be the verdict metric"
                if _saturated(dep) else "")

    peak = max(range(len(curve)), key=lambda i: curve[i])
    rose = curve[peak] > curve[0] + 0.1
    fell = curve[-1] < curve[peak] - 0.1

    if _at_ceiling(curve):
        first = steps[0]
        return (f"✅ AT CEILING FROM THE FIRST CHECKPOINT (step {first}) — the "
                f"task was already learned before anything was saved. Nothing to "
                f"read from the curve, and nothing to fix by training longer or "
                f"stopping earlier.{dep_note}")
    if rose and fell:
        return (f"⛔ OVERTRAINED — rose to {curve[peak]:.0%} at step "
                f"{steps[peak]}, fell to {curve[-1]:.0%}. Stop near the "
                f"peak.{dep_note}")
    if rose:
        return (f"✅ ROSE AND HELD — {curve[0]:.0%} → {curve[-1]:.0%} "
                f"(peak {curve[peak]:.0%} at step {steps[peak]}). No duration "
                f"problem to fix.{dep_note}")
    if max(curve) <= 0.1:
        return (f"⛔ NEVER ROSE, AND STAYED ON THE FLOOR ({curve[0]:.0%} → "
                f"{curve[-1]:.0%}) — the task is not in the training data at "
                f"all. Not a duration problem.{dep_note}")
    return (f"⛔ NEVER ROSE — {curve[0]:.0%} → {curve[-1]:.0%}, no rise beyond "
            f"noise. Not a training-duration problem.{dep_note}")


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

    reading = read_curve(rows)
    print(f"\n  READING: {reading}")

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rows": rows, "reading": reading}, indent=2),
                   encoding="utf-8", newline="")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
