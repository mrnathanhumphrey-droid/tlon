"""Is the lambda->collapse curve novelty pressure, or just advantage variance?

WHERE THIS SITS. Phase 3 v2: concentration rose monotonically with lambda
(mean 0.356 -> 0.774) and so did R (0.193 -> 0.237, wrong sign).
  - lambda_purchase.py ruled out "lambda has no grip": R is action-steerable
    (within-state sd 0.113, SNR 1.28) and the novelty term reaches 76% of felt
    reward magnitude at lambda=2.
  - baseline_scope_control.py FALSIFIED the global-baseline explanation:
    per-referent baselining left lambda=2 concentration unchanged
    (0.774 -> 0.748) and merely degraded lambda=0 (0.356 -> 0.652).

WHAT IS LEFT. lambda multiplies a reward term, so it raises advantage VARIANCE
as well as novelty weight -- measured at 2.17x from lambda 0 to 2. REINFORCE
collapses faster under higher advantage variance. So the sweep confounds "more
novelty pressure" with "bigger, noisier steps", and lambda cannot be read as
novelty pressure alone.

TEST. Normalize the advantage by its running sd, which holds step magnitude
fixed while lambda still sets the novelty WEIGHT, and re-run the extremes.

This control also carries the scramble probe, because the question that actually
matters is KILL A, not concentration. Concentration measures how DETERMINISTIC
the generator became. A cipher additionally requires the listener to READ the
concentrated channels. Those are different claims and the v2 run separates them:
concentration 0.774 with every no-information channel at <= 0.20 pts is a fixed
idiolect, not a code.
"""
from __future__ import annotations
import json
import pathlib
import random
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

from tlon.listener import data, train as tr        # noqa: E402
from tlon.listener.model import Listener           # noqa: E402
from tlon.referents import schema                  # noqa: E402
from tlon.selfplay import phase3                   # noqa: E402
from run_phase3 import NOINFO, probe, sample_from_policy   # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
LAMBDAS = [0.0, 1.0, 2.0]
N_EVAL = 1200
FLAT = 0.08      # concentration change below this counts as "lambda-flat"
KILL_A = 0.50    # defensible no-info scramble threshold (prereg says 1.0)


def verdict(cells: dict) -> str:
    """One branch per outcome, loud fallback FIRST.

    A verdict function can only report outcomes it was written to recognise,
    and the previous control in this series printed PREDICTION HELD off two
    endpoint comparisons while its own mechanism had failed. So: start from
    'unrecognised', and let a named branch overwrite it only on a full match.
    """
    v = ("UNRECOGNISED PATTERN -- none of the enumerated branches matched. "
         "Read the table by hand before concluding anything.")
    n0, n2 = cells[("norm", 0.0)], cells[("norm", 2.0)]
    r0, r2 = cells[("raw", 0.0)], cells[("raw", 2.0)]

    dc_norm = n2["mean_conc"] - n0["mean_conc"]
    dc_raw = r2["mean_conc"] - r0["mean_conc"]
    dr_norm = n2["r"] - n0["r"]

    if dc_norm <= -FLAT and dr_norm < 0:
        # The branch the first run of this control did NOT have, which is why
        # it fell through to the fallback. I had not considered that lambda
        # could REDUCE concentration -- I only enumerated "flat" and "rises".
        v = ("SIGN REVERSAL. With step magnitude fixed, higher lambda LOWERS "
             "both concentration and R. The raw sweep's lambda axis measured "
             "advantage variance, not novelty pressure, and reads backwards. "
             "Novelty pressure diversifies the policy, as designed.")
    elif abs(dc_norm) < FLAT and dr_norm < 0:
        v = ("COLLAPSE WAS VARIANCE-DRIVEN. With step magnitude held fixed, "
             "lambda no longer drives concentration and R falls as novelty "
             "pressure rises. The v2 sweep measured gradient noise, not "
             "novelty pressure -- its lambda axis is not interpretable.")
    elif abs(dc_norm) < FLAT and dr_norm >= 0:
        v = ("PARTIAL. Normalising removes the concentration trend but R still "
             "does not fall with lambda. The novelty term has purchase on "
             "single actions yet no net directional effect over a run -- look "
             "at the repetition log's response, not the optimiser.")
    elif dc_norm >= FLAT and abs(dc_norm - dc_raw) < FLAT:
        v = ("NOT A VARIANCE ARTEFACT. Concentration tracks lambda just as "
             "hard with step magnitude fixed, so novelty pressure itself "
             "collapses the policy. That is a real property of the objective.")
    elif dc_norm >= FLAT:
        v = ("MIXED. Concentration still rises with lambda but markedly less "
             "than raw; variance is part of the story, not all of it.")
    return v


def main() -> int:
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    rs = schema.load_all()
    refs = rs.referents
    groups = {r.minimal_pair for r in refs if r.minimal_pair}
    cfg = tr.TrainCfg()

    print("=" * 76)
    print("VARIANCE CONFOUND -- normalised advantage vs raw, across lambda")
    print("=" * 76)

    ds = data.build(refs, per_ref=250)
    seed = tr.train(ds.train, ds.test_random, ds.n_classes, cfg, verbose=False)
    base_state = {k: v.detach().clone() for k, v in seed.state_dict().items()}

    cells, rows = {}, []
    for norm in (False, True):
        tag = "norm" if norm else "raw"
        print(f"\n  -- advantage: {'NORMALISED' if norm else 'raw'} "
              f"-------------------------------")
        for lam in LAMBDAS:
            listener = Listener(len(refs)).to(dev)
            listener.load_state_dict(base_state)
            t0 = time.time()
            policy, rep, st = phase3.run(
                refs, listener,
                phase3.P3Cfg(lam=lam, device=dev, normalize_advantage=norm),
                verbose=False)
            rng = random.Random(1000 + int(lam * 100))
            eval_rows = sample_from_policy(policy, refs, rng, N_EVAL)
            drops = probe(listener, eval_rows, refs, groups, cfg, rng)
            conc = policy.concentration()
            mean_conc = sum(conc.values()) / len(conc)
            r = st.rep_cost[-1] if st.rep_cost else float("nan")
            m = st.m_rate[-1] if st.m_rate else float("nan")
            worst = max((abs(drops.get(c, 0.0)) for c in NOINFO), default=0.0)
            print(f"    lambda={lam:<4} {time.time() - t0:.0f}s  M {100 * m:5.1f}%  "
                  f"R {r:.3f}  conc {mean_conc:.3f}  "
                  f"worst no-info scramble {100 * worst:+.2f} pts"
                  f"{'   <- KILL A' if 100 * worst > KILL_A else ''}")
            cell = {"lam": lam, "m": m, "r": r, "mean_conc": mean_conc,
                    "concentration": conc, "drops": drops, "worst_noinfo": worst}
            cells[(tag, lam)] = cell
            rows.append({"advantage": tag, **cell})

    print("\n" + "=" * 76)
    print(f"  raw : concentration {cells[('raw', 0.0)]['mean_conc']:.3f} -> "
          f"{cells[('raw', 2.0)]['mean_conc']:.3f}   "
          f"R {cells[('raw', 0.0)]['r']:.3f} -> {cells[('raw', 2.0)]['r']:.3f}")
    print(f"  norm: concentration {cells[('norm', 0.0)]['mean_conc']:.3f} -> "
          f"{cells[('norm', 2.0)]['mean_conc']:.3f}   "
          f"R {cells[('norm', 0.0)]['r']:.3f} -> {cells[('norm', 2.0)]['r']:.3f}")
    worst_all = max(c["worst_noinfo"] for c in cells.values())
    print(f"\n  KILL A: worst no-information scramble drop anywhere in this "
          f"control = {100 * worst_all:+.2f} pts (threshold {KILL_A})")
    print(f"\n  VERDICT: {verdict(cells)}")

    (OUT / "variance_confound.json").write_text(
        json.dumps({"rows": rows, "verdict": verdict(cells)}, indent=2,
                   default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'variance_confound.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
