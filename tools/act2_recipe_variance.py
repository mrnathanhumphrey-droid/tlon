"""RECIPE VARIANCE — does building this model twice give you the same speaker?

⭐ A SPREAD, NOT A TEST. There is no treatment arm and nothing is being compared
to anything: `P(ki | prior ∈ COMMON_UNIFORM_ROWS)` is measured on k adapters
trained by the same recipe at different seeds, and the spread is the result.

⛔⛔ WHY THIS IS THE RIGHT NEXT QUESTION. The ki-as-target probe HALTED because a
fresh adapter scored 0.2520 where the stored one scored 0.1005 (t +6.89) — while
the stored adapter re-served reproduced ITSELF at t +0.62. The measurement is
stable; the pipeline's output is not. Everything the 2026-08-26 attribution said
about ki-suppression was measured inside ONE adapter.

⛔ AND THE UNIT IS THE ADAPTER. Exchanges buy within-adapter precision, which is
not the thing being estimated. 14 exchanges give SE ≈ 0.019 against a spread the
size of the observed 0.133. Spending on more adapters instead of more exchanges is
the whole lesson of the previous run.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.discourse import force_map as FM                        # noqa: E402
from tlon.grammar.parse import parse, render                      # noqa: E402

TARGET = "ki"
MIN_DISTINCT_RATIO = 0.50

#: ⭐ THE PRE-DECLARED BANDS, from docs/PREREG_RECIPE_VARIANCE_2026_08_27.md.
#: Fixed before any new adapter was trained; not chosen from the result.
BAND_STABLE = 0.04
BAND_UNSTABLE = 0.10
PREREG_SHA256 = None      # set at commit time; see the pipeline's hash check


def measure(paths, label: str) -> dict:
    ex = []
    for p in paths:
        d = json.loads(p.read_text(encoding="utf-8"))
        t = d["transcript_interacting"]
        if not t:
            continue
        f = []
        for s in t:
            try:
                sc = parse(s)
            except Exception:                                      # noqa: BLE001
                continue
            if render(sc) == s and sc.force in FM.ORDER:
                f.append(sc.force)
        tr = list(zip(f, f[1:]))
        sel = [(a, b) for a, b in tr if a in FM.COMMON_UNIFORM_ROWS]
        if not sel:
            continue
        ex.append({"file": p.name,
                   "dr": len(set(t)) / len(t),
                   "rate": sum(b == TARGET for _, b in sel) / len(sel),
                   "hit": sum(b == TARGET for _, b in sel), "n": len(sel),
                   "global_ki": (sum(b == TARGET for _, b in tr) / len(tr))
                   if tr else None})
    if not ex:
        raise SystemExit(f"⛔ {label}: no usable exchanges")
    r = [e["rate"] for e in ex]
    m = sum(r) / len(r)
    return {"label": label, "k": len(r), "mean": m,
            "sd": statistics.stdev(r) if len(r) > 1 else 0.0,
            "se": (statistics.stdev(r) / len(r) ** 0.5) if len(r) > 1 else 0.0,
            "pooled": sum(e["hit"] for e in ex) / sum(e["n"] for e in ex),
            # ⭐ REPORTED, NEVER A SILENT EXCLUSION — the amendment carried
            # forward from the ki-as-target run, where a degeneracy refusal
            # collided with the count lock and refused the whole arm.
            "n_degenerate": sum(e["dr"] < MIN_DISTINCT_RATIO for e in ex),
            "min_dr": min(e["dr"] for e in ex),
            "global_ki": sum(e["global_ki"] for e in ex) / len(ex),
            "exchanges": ex}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default="runs/act2/recipe_var/logs")
    ap.add_argument("--bfresh-logs", default="runs/act2/ki_target/logs",
                    help="B-fresh (seed 20620) is already measured; it is the "
                         "fourth draw and is included by pre-registration")
    ap.add_argument("--historical", default="runs/act2/logs/mt_run",
                    help="adapter_mt — DIFFERENT CODE, reported but NOT in the "
                         "estimate")
    ap.add_argument("--out", default="runs/act2/recipe_var/variance.json")
    a = ap.parse_args()

    print("RECIPE VARIANCE — does building this model twice give the same speaker?")
    print("=" * 78)
    print(f"  measure: P(ki | prior ∈ {list(FM.COMMON_UNIFORM_ROWS)})   "
          f"expectation {FM.COMMON_UNIFORM_EXPECTATION:.2f}")
    print(f"  bands (pre-declared): stable < {BAND_STABLE} · "
          f"unstable ≥ {BAND_UNSTABLE}")
    print()

    arms = [measure(sorted(pathlib.Path(a.bfresh_logs).glob("bfresh_*.json")),
                    "s20620 (B-fresh)")]
    for seed in (20621, 20622, 20623):
        ps = sorted(pathlib.Path(a.logs).glob(f"s{seed}_*.json"))
        if ps:
            arms.append(measure(ps, f"s{seed}"))
    print(f"  {'adapter':18s} {'k':>3s} {'mean':>8s} {'sd':>8s} {'se':>8s} "
          f"{'pooled':>8s}  {'globalki':>8s}  deg")
    for m in arms:
        print(f"  {m['label']:18s} {m['k']:3d} {m['mean']:8.4f} {m['sd']:8.4f} "
              f"{m['se']:8.4f} {m['pooled']:8.4f}  {m['global_ki']:8.4f}  "
              f"{m['n_degenerate']}")

    means = [m["mean"] for m in arms]
    S = max(means) - min(means)
    print()
    print(f"  ⭐ SPREAD S = {S:.4f}   (min {min(means):.4f} · max {max(means):.4f} "
          f"· k = {len(means)} adapters)")
    if len(means) > 2:
        print(f"     between-adapter sd {statistics.stdev(means):.4f}; "
              f"mean within-adapter se "
              f"{sum(m['se'] for m in arms)/len(arms):.4f}")

    if len(arms) < 3:
        verdict = "INCOMPLETE"
        why = (f"only {len(arms)} adapters present; the pre-registered design is "
               "4. A spread over 2 draws is not an estimate.")
    elif S < BAND_STABLE:
        verdict = "⭐ RECIPE STABLE"
        why = (f"S {S:.4f} < {BAND_STABLE}. Re-drawing does NOT move ki-emission, "
               "so the B-fresh/adapter_mt gap came from the CODE CHANGE between "
               "them, not from the draw. Diagnose the code delta; ki-suppression "
               "may be a real property of the older generator.")
    elif S < BAND_UNSTABLE:
        verdict = "⚠️ MODERATELY UNSTABLE"
        why = (f"{BAND_STABLE} ≤ S {S:.4f} < {BAND_UNSTABLE}. Map experiments "
               "remain possible but must use k ≥ 3 adapters per arm and be "
               "powered over ADAPTERS, not exchanges.")
    else:
        verdict = "⛔⛔ THE RECIPE DOES NOT DETERMINE ki-EMISSION"
        why = (f"S {S:.4f} ≥ {BAND_UNSTABLE}. The 2026-08-26 ki-suppression "
               "finding is a property of one draw. The asymmetry mechanism is "
               "UNFALSIFIABLE by this apparatus, and no map-level experiment on "
               "this measure is worth running until the variance source is fixed.")
    print(f"\n  ⇒ VERDICT: {verdict}\n     {why}")

    near = [m["label"] for m in arms
            if abs(m["mean"] - FM.COMMON_UNIFORM_EXPECTATION) < 0.03]
    if near:
        print(f"  ⭐ PRE-DECLARED SIDE-READING: {near} land within 0.03 of the "
              f"{FM.COMMON_UNIFORM_EXPECTATION:.2f} expectation ⇒ "
              "'suppression' is not the recipe's typical behaviour.")

    hp = sorted(pathlib.Path(a.historical).glob("arm2_new_w1_*.json"))
    if hp:
        h = measure(hp, "adapter_mt (HISTORICAL)")
        print(f"\n  ⚠️ {h['label']}: mean {h['mean']:.4f} over k={h['k']} — "
              "DIFFERENT CODE,\n     reported for context and NOT part of S.")

    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(
        {"spread": S, "verdict": verdict, "why": why,
         "bands": {"stable": BAND_STABLE, "unstable": BAND_UNSTABLE},
         "arms": [{k: v for k, v in m.items() if k != "exchanges"}
                  for m in arms]},
        indent=2, ensure_ascii=False), encoding="utf-8", newline="")
    print(f"\nwrote {a.out}")
    print("\n⛔ NO TREATMENT ARM. This cannot say the asymmetry mechanism is right "
          "or wrong.\n   A stable recipe would RE-ENABLE that question, not answer "
          "it. Still no drift.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
