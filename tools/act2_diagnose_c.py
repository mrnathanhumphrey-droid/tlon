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
import math
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
#: ⛔ HOW MANY STANDARD ERRORS A MOVE MUST CLEAR TO BE CALLED A TREND. Fixed
#: before use, not tuned to make a curve read a particular way.
NOISE_SD_MULT = 2.0
#: ⛔ AND A FLOOR UNDER THAT, because at very small n the standard error itself
#: gets small near p=0 or p=1, and a 1-item move must never become a "trend".
MIN_REAL_MOVE = 0.15

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

    # ⛔⛔ THE THRESHOLD WAS BELOW THE NOISE IT WAS MEANT TO CLEAR. `rose`/`fell`
    # compared against a FIXED 0.1, and at n=12 the binomial standard deviation
    # near p≈0.85 is **0.106** — so the bar sat UNDER one sd and the verdict
    # fired on sampling noise by construction.
    #
    # Measured on run 4: the curve was 9,12,12,9,12,7,10,10 of 12 — scatter 1.81
    # items against a binomial sd of 1.27 — i.e. consistent with a FLAT ~84 %,
    # and non-monotone in both directions. The tool reported
    # "⛔ OVERTRAINED — rose to 100 % at step 1000, fell to 83 %."
    #
    # ⭐ THE FIX IS THE SAME ONE HARDEN 2 APPLIED ONE LEVEL UP: do not report a
    # movement the instrument cannot resolve. The bar is now the standard error
    # of the DIFFERENCE of two proportions at this n, times a pre-set multiple.
    def _se(a: float, b: float) -> float:
        return math.sqrt(max(a * (1 - a), 1e-9) / n + max(b * (1 - b), 1e-9) / n)

    rise_bar = NOISE_SD_MULT * _se(curve[peak], curve[0])
    fall_bar = NOISE_SD_MULT * _se(curve[-1], curve[peak])
    rose = curve[peak] - curve[0] > max(rise_bar, MIN_REAL_MOVE)
    fell = curve[peak] - curve[-1] > max(fall_bar, MIN_REAL_MOVE)
    noise_note = (f" · resolution at n={n}: a move must exceed "
                  f"{max(rise_bar, MIN_REAL_MOVE):.0%} to be called")

    if _at_ceiling(curve):
        first = steps[0]
        return (f"✅ AT CEILING FROM THE FIRST CHECKPOINT (step {first}) — the "
                f"task was already learned before anything was saved. Nothing to "
                f"read from the curve, and nothing to fix by training longer or "
                f"stopping earlier.{dep_note}")
    if rose and fell:
        return (f"⛔ OVERTRAINED — rose to {curve[peak]:.0%} at step "
                f"{steps[peak]}, fell to {curve[-1]:.0%}. Stop near the "
                f"peak.{dep_note}{noise_note}")
    if rose:
        return (f"✅ ROSE AND HELD — {curve[0]:.0%} → {curve[-1]:.0%} "
                f"(peak {curve[peak]:.0%} at step {steps[peak]}). No duration "
                f"problem to fix.{dep_note}{noise_note}")
    if max(curve) <= 0.1:
        return (f"⛔ NEVER ROSE, AND STAYED ON THE FLOOR ({curve[0]:.0%} → "
                f"{curve[-1]:.0%}) — the task is not in the training data at "
                f"all. Not a duration problem.{dep_note}")
    # ⛔ "NEVER ROSE" AND "COULD NOT TELL" ARE DIFFERENT FACTS. If the curve
    # moved but not past the resolution bar, say THAT — reporting it as a flat
    # null is the uninformative-cell error wearing a verdict's clothes.
    span = max(curve) - min(curve)
    # ⛔⛔ "NEVER ROSE" IS A CLAIM ABOUT THE MODEL. On run 4 it would have been
    # FALSE — that adapter went 0 % → 82 % render — and only the 12-sample curve
    # could not see the shape. A curve that swings WIDELY but resolves no
    # monotone trend is a statement about the INSTRUMENT, and must be reported
    # as one.
    mean = sum(curve) / len(curve)
    binom_sd = math.sqrt(max(mean * (1 - mean), 1e-9) / n)
    observed_sd = (math.sqrt(sum((c - mean) ** 2 for c in curve)
                             / max(1, len(curve) - 1)))
    if span > max(rise_bar, MIN_REAL_MOVE) and not rose and not fell:
        return (f"⚠️⚠️ NOISY — NO RESOLVED TREND. The curve swings "
                f"{min(curve):.0%}..{max(curve):.0%} but is NOT monotone, and "
                f"neither the rise nor the fall clears "
                f"{max(rise_bar, MIN_REAL_MOVE):.0%} at n={n} "
                f"(observed scatter {observed_sd:.3f} vs binomial "
                f"{binom_sd:.3f}). ⛔ This is NOT 'never rose' — that would be a "
                f"claim about the model, and this is a statement about the "
                f"instrument. Raise n per checkpoint to read it.{dep_note}")
    if span > 0.0 and span <= max(rise_bar, MIN_REAL_MOVE):
        return (f"⚠️ WITHIN NOISE — the curve moves {min(curve):.0%}..{max(curve):.0%} "
                f"but n={n} per point cannot resolve a move smaller than "
                f"{max(rise_bar, MIN_REAL_MOVE):.0%}. This is NOT 'flat' and NOT "
                f"'overtrained' — it is UNRESOLVED. Raise n to read it.{dep_note}")
    return (f"⛔ NEVER ROSE — {curve[0]:.0%} → {curve[-1]:.0%}, no rise beyond "
            f"noise. Not a training-duration problem.{dep_note}{noise_note}")


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
