"""FIX 1 — the entropy-coefficient sweep. PHASE 13.2 re-run.

⛔ THE COEFFICIENT IS CHOSEN ON THE CONTROL ARM AND APPLIED BLIND TO THE
TREATMENT. The sweep runs on CATEGORICAL only, because that is the arm whose
target behaviour is known independently of the hypothesis. Tuning on the metric
arm would be tuning on the arm under test.

⛔⛔ AND THE SWEEP SEEDS ARE DISJOINT FROM THE MEASUREMENT SEEDS. The sweep uses
101/202/303; Part A measures on 11..88. Choosing the coefficient on the same
seeds that later produce the headline would let seed-specific luck select the
knob that flatters it -- a leak that no amount of "we tuned on categorical"
would fix.

⭐ NOTE THE INCUMBENT. `P3Cfg.entropy_bonus` already defaults to 0.01 and
`run_13_2.py` never overrode it, so the collapsed first run ALREADY HAD an
entropy bonus. Fix 1 is not "add one", it is "the one that was there did not
work, find how much more is needed". 0.01 is therefore in the grid as the
incumbent and as the stability reference.

── THE PRE-REGISTERED CRITERION, fixed before the sweep is run ──────────────
Pick the MINIMUM coefficient that satisfies BOTH:

  RESTORES   mean Bayes-ceiling headroom on categorical x head > 2 x MDE_floor
             (= 5.92 pts). Headroom, not "distinct codes": a near-uniform policy
             has a varied ARGMAX and no signal, so counting codes would call
             over-entropy a success. See tlon/harness/ceiling.py.
  STABLE     mean final M-rate >= 0.9 x the M-rate at the incumbent 0.01.

⛔ MINIMUM, NOT MAXIMUM, AND THAT IS THE NAMED RISK. A coefficient large enough
to force diversity pushes the policy toward uniform-random codes, which
manufactures diversity that is not the residue doing work. Over-large entropy is
its own vacuity. The headroom criterion catches it from one side (uniform =>
headroom 0) and "minimum that clears the bar" from the other.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics as S
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

import torch                                                     # noqa: E402

from tlon.harness.ceiling import bayes_ceiling, classify_policy  # noqa: E402
from tlon.listener.model import Listener                         # noqa: E402
from tlon.referents import schema                                # noqa: E402
from tlon.selfplay import phase3                                 # noqa: E402
from tlon.selfplay.policy import ChannelPolicy                   # noqa: E402
from run_13_2 import clusters_of, residues_of, MDE_FLOOR         # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
GRID = [0.01, 0.03, 0.10, 0.30, 1.00]
SWEEP_SEEDS = [101, 202, 303]          # DISJOINT from Part A's 11..88
STEPS = 4000
RESTORE_BAR = 2.0 * MDE_FLOOR          # 5.92 pts
STABILITY_FRAC = 0.9


def one(refs, groups, coords, seed: int, ent: float, dev: str) -> dict:
    torch.manual_seed(seed)
    pol = ChannelPolicy(len(refs), residues=coords).to(dev)
    L = Listener(len(refs)).to(dev)
    _, _, st = phase3.run(
        refs, L,
        phase3.P3Cfg(lam=0.0, device=dev, project=True, steps=STEPS, seed=seed,
                     normalize_advantage=True, entropy_bonus=ent),
        verbose=False, policy=pol)
    cei = bayes_ceiling(pol, groups)
    verdict, why = classify_policy(pol, groups, MDE_FLOOR)
    return {"seed": seed, "entropy_bonus": ent,
            "headroom_pts": cei["headroom_pts"], "ceiling": cei["ceiling"],
            "m_rate": st.m_rate[-1] if st.m_rate else float("nan"),
            "verdict": verdict, "why": why}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=STEPS)
    ap.add_argument("--arm", default="random",
                    help="'random' = the CONTROL arm, which is what SELECTS the "
                         "coefficient. 'lyric' is DIAGNOSTIC ONLY -- it reports "
                         "the treatment arm's headroom curve so a criterion can "
                         "be judged, and it must never be used to pick the knob "
                         "without an explicit ruling.")
    args = ap.parse_args()
    dev = "cuda" if torch.cuda.is_available() else "cpu"

    refs = schema.load_residue_arm(args.arm).referents
    _, groups = clusters_of(refs)
    coords = residues_of(refs)

    print("=" * 78)
    label = "CATEGORICAL (control, SELECTS)" if args.arm == "random" else             "LYRIC/METRIC (treatment, DIAGNOSTIC ONLY — selects nothing)"
    print(f"FIX 1 — ENTROPY SWEEP on the {label} arm (head parameterisation)")
    print("=" * 78)
    print(f"  device {dev} · {len(refs)} referents · {len(groups)} clusters · "
          f"{args.steps} steps · seeds {SWEEP_SEEDS} (disjoint from Part A)")
    print(f"  PRE-REGISTERED CRITERION: minimum coefficient with mean headroom "
          f"> {RESTORE_BAR:.2f} pts")
    print(f"  (= 2 x MDE floor {MDE_FLOOR}) AND mean M-rate >= "
          f"{STABILITY_FRAC:g} x the incumbent (0.01) M-rate.\n")

    rows, by_c = [], {}
    for ent in GRID:
        cell = []
        for sd in SWEEP_SEEDS:
            t0 = time.time()
            r = one(refs, groups, coords, sd, ent, dev)
            r["secs"] = time.time() - t0
            cell.append(r)
            rows.append(r)
            print(f"    ent {ent:<5} seed {sd:>4}  headroom "
                  f"{r['headroom_pts']:>6.2f} pts  ceiling "
                  f"{100*r['ceiling']:>5.1f}%  M {100*r['m_rate']:>5.1f}%  "
                  f"{r['verdict']}  [{r['secs']:.0f}s]")
        by_c[ent] = {"headroom": S.fmean(x["headroom_pts"] for x in cell),
                     "m_rate": S.fmean(x["m_rate"] for x in cell),
                     "verdicts": [x["verdict"] for x in cell]}
        print(f"    {'':>9} ent {ent:<5} MEAN headroom "
              f"{by_c[ent]['headroom']:>6.2f}  M {100*by_c[ent]['m_rate']:>5.1f}%\n")

    ref_m = by_c[GRID[0]]["m_rate"]
    print("  ── SELECTION against the pre-registered criterion ──")
    chosen = None
    for ent in GRID:
        c = by_c[ent]
        restores = c["headroom"] > RESTORE_BAR
        stable = c["m_rate"] >= STABILITY_FRAC * ref_m
        mark = "  <-- CHOSEN" if (restores and stable and chosen is None) else ""
        if restores and stable and chosen is None:
            chosen = ent
        print(f"    ent {ent:<5} headroom {c['headroom']:>6.2f} "
              f"{'PASS' if restores else 'fail'}   M {100*c['m_rate']:>5.1f}% "
              f"{'PASS' if stable else 'fail'}{mark}")

    print()
    is_control = (args.arm == "random")
    if chosen is None:
        print("  ⛔⛔ NO COEFFICIENT IN THE GRID SATISFIES BOTH CRITERIA.\n"
              "     The collapse is not an entropy problem, or the grid is too "
              "narrow. Do NOT\n     widen the grid and re-pick silently — that "
              "is tuning to taste. Report and decide.")
    elif not is_control:
        # ⛔⛔ THE DIAGNOSTIC PATH SELECTS NOTHING. An earlier version printed
        # "FROZEN ENTROPY COEFFICIENT ... chosen on the CONTROL arm" from a run
        # on the TREATMENT arm -- a banked artefact asserting the exact thing
        # the design forbids (tuning on the arm under test). The caveat belongs
        # in the OUTPUT, not in prose beside it.
        print(f"  ⛔ DIAGNOSTIC ARM ({args.arm}) — SELECTS NOTHING.\n"
              f"     The minimum value passing the criterion here is {chosen}, "
              f"reported ONLY so the\n     criterion can be judged against the "
              f"arm that actually failed. Choosing a\n     coefficient on this "
              f"arm would be tuning on the treatment.")
        chosen = None
    else:
        print(f"  ⭐ FROZEN ENTROPY COEFFICIENT: {chosen}\n"
              f"     Minimum passing value on the CONTROL arm, seeds disjoint "
              f"from Part A's.\n     Applied BLIND and IDENTICALLY to both "
              f"arms.")

    # ⛔ Per-seed consistency, because a MEAN over 3 seeds can pass on ONE.
    for ent in GRID:
        hs = [x["headroom_pts"] for x in rows if x["entropy_bonus"] == ent]
        if any(h <= RESTORE_BAR for h in hs) and by_c[ent]["headroom"] > RESTORE_BAR:
            print(f"     ⚠ ent {ent}: mean clears the bar but "
                  f"{sum(1 for h in hs if h <= RESTORE_BAR)}/{len(hs)} seeds are "
                  f"at or below it ({', '.join(f'{h:.1f}' for h in hs)}) — the "
                  f"mean is carried by a minority of seeds.")

    (OUT / f"entropy_sweep_13_2_{args.arm}.json").write_text(json.dumps(
        {"arm": args.arm, "selects": args.arm == "random",
         "standardised_input": True,
         "grid": GRID, "seeds": SWEEP_SEEDS, "steps": args.steps,
         "restore_bar_pts": RESTORE_BAR, "stability_frac": STABILITY_FRAC,
         "incumbent_m_rate": ref_m, "by_coefficient": by_c,
         "chosen": chosen, "runs": rows}, indent=2, default=float),
        encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'entropy_sweep_13_2.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
