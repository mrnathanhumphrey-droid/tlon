"""PAIRED control: is the global advantage baseline what drives the collapse?

Phase 3 v2 produced two things that do not fit together. Policy concentration
rose monotonically with lambda (orient 0.204 -> 0.658), and so did R, the
repetition cost (0.193 -> 0.237). Novelty pressure that produces MORE repetition
is the wrong sign, and lambda_purchase.py rules out the easy explanations: R is
genuinely action-steerable (within-state sd 0.113, SNR 1.28) and the novelty
term really does take over the reward (0% -> 76% of felt magnitude), while total
gradient magnitude grows only 2.17x.

CLAIM UNDER TEST. The advantage baseline is a single global EMA across all
referents, but R varies strongly BY referent -- a sparse bucket scores low
whatever you say into it (across-state sd 0.088, ~78% of the within-state
signal). A global baseline leaves that in the advantage. So every action sampled
at a low-R referent is reinforced together regardless of which action it was,
and every action at a crowded referent is suppressed together. That is collapse
driven by which referent came up. It scales with lambda, which is why both
curves are monotone.

PREDICTION, stated before running: with a per-referent baseline at lambda=2,
concentration falls AND R falls below the lambda=0 value.

FALSIFIER: if concentration falls but R still rises with lambda, the mechanism
above is wrong and the sign anomaly is something else. Say so.

Paired: identical seed, identical lambda, one flag differs.
"""
from __future__ import annotations
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

from tlon.listener import data, train as tr        # noqa: E402
from tlon.listener.model import Listener           # noqa: E402
from tlon.referents import schema                  # noqa: E402
from tlon.selfplay import phase3                   # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
LAMBDAS = [0.0, 2.0]


def main() -> int:
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    refs = schema.load_all().referents
    cfg = tr.TrainCfg()

    print("=" * 76)
    print("BASELINE SCOPE — paired control (global EMA vs per-referent EMA)")
    print("=" * 76)
    print("\n  prediction: per-ref at lambda=2 -> concentration falls AND")
    print("              R falls below the lambda=0 value.")
    print("  falsifier:  concentration falls but R still rises with lambda.\n")

    ds = data.build(refs, per_ref=250)
    seed_listener = tr.train(ds.train, ds.test_random, ds.n_classes, cfg, verbose=False)
    base_state = {k: v.detach().clone() for k, v in seed_listener.state_dict().items()}

    rows = []
    for per_ref in (False, True):
        tag = "per-referent" if per_ref else "global"
        for lam in LAMBDAS:
            listener = Listener(len(refs)).to(dev)
            listener.load_state_dict(base_state)
            t0 = time.time()
            policy, rep, st = phase3.run(
                refs, listener,
                phase3.P3Cfg(lam=lam, device=dev, per_ref_baseline=per_ref),
                verbose=False)
            conc = policy.concentration()
            r = st.rep_cost[-1] if st.rep_cost else float("nan")
            m = st.m_rate[-1] if st.m_rate else float("nan")
            mean_conc = sum(conc.values()) / len(conc)
            print(f"  {tag:<13} lambda={lam:<4}  {time.time() - t0:.0f}s   "
                  f"M {100 * m:5.1f}%   R {r:.3f}   "
                  f"mean concentration {mean_conc:.3f}   orient {conc['orient']:.3f}")
            rows.append({"baseline": tag, "lam": lam, "m": m, "r": r,
                         "mean_conc": mean_conc, "concentration": conc})

    print()
    for tag in ("global", "per-referent"):
        a = next(x for x in rows if x["baseline"] == tag and x["lam"] == 0.0)
        b = next(x for x in rows if x["baseline"] == tag and x["lam"] == 2.0)
        dr, dc = b["r"] - a["r"], b["mean_conc"] - a["mean_conc"]
        print(f"  {tag:<13} lambda 0 -> 2:  R {dr:+.3f}   concentration {dc:+.3f}"
              f"   {'<-- WRONG SIGN on R' if dr > 0 else ''}")

    g2 = next(x for x in rows if x["baseline"] == "global" and x["lam"] == 2.0)
    p2 = next(x for x in rows if x["baseline"] == "per-referent" and x["lam"] == 2.0)
    p0 = next(x for x in rows if x["baseline"] == "per-referent" and x["lam"] == 0.0)
    print(f"\n  at lambda=2, per-ref vs global:  R {p2['r'] - g2['r']:+.3f}   "
          f"concentration {p2['mean_conc'] - g2['mean_conc']:+.3f}")
    conc_fell = p2["mean_conc"] < g2["mean_conc"]
    r_fell = p2["r"] < p0["r"]
    if conc_fell and r_fell:
        print("  => PREDICTION HELD. Global baseline was the collapse driver.")
    elif conc_fell and not r_fell:
        print("  => FALSIFIER FIRED. Concentration is baseline-scope sensitive but")
        print("     the R sign anomaly is NOT explained. Mechanism above is wrong.")
    else:
        print("  => Neither. Baseline scope is not the lever; look elsewhere.")

    (OUT / "baseline_scope.json").write_text(
        json.dumps(rows, indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'baseline_scope.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
