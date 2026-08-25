"""Does lambda actually have purchase on the policy's action space?

THE QUESTION THIS ANSWERS. Phase 3 v2 came back with no cipher at any lambda,
and R (repetition cost) RISING with lambda -- 0.193 -> 0.237 -- which is the
wrong sign. Novelty pressure that increases repetition is not novelty pressure.

The REINFORCE update is  advantage = reward - EMA(reward),  with
reward = m + lambda * (1 - R). The policy can only learn from the part of that
which VARIES WITH THE ACTION at a fixed state. Any variation that comes from the
state (which referent came up, what the log happens to hold) is noise: it enters
the advantage, scales with lambda, and inflates gradient magnitude in a
direction the action did not choose.

So measure both, separately:

  WITHIN-STATE  spread of R across actions   -> the signal lambda can exploit
  ACROSS-STATE  spread of R                  -> the noise lambda multiplies

and compare the novelty term's action-level spread against M's. If M's spread
dominates even at lambda=2, then the sweep never applied novelty pressure at
all, and "no cipher at any lambda" is a statement about a knob that was never
turned -- not about the framework.

Read-only. Trains nothing, writes one JSON.
"""
from __future__ import annotations
import json
import pathlib
import random
import statistics as S
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

from tlon.grammar.parse import render                    # noqa: E402
from tlon.listener import data, train as tr              # noqa: E402
from tlon.listener import tokenizer as tk                # noqa: E402
from tlon.novelty.centroids import RepetitionLog         # noqa: E402
from tlon.referents import schema                        # noqa: E402
from tlon.selfplay import phase3                         # noqa: E402
from tlon.selfplay.policy import ChannelPolicy           # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
WARM = 1500          # steps of uniform-policy history to build a realistic log
N_STATES = 120       # states sampled from that history
N_ACTIONS = 64       # distinct free-channel actions per state
LAMBDAS = [0.0, 0.25, 0.5, 1.0, 2.0]


def main() -> int:
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    refs = schema.load_all().referents
    rng = random.Random(90210)
    policy = ChannelPolicy(len(refs)).to(dev)      # untrained == uniform

    print("=" * 76)
    print("LAMBDA PURCHASE CONTROL — is the novelty term steerable by the action?")
    print("=" * 76)

    print(f"\n  listener (same pretraining as the sweep, per_ref=250)")
    ds = data.build(refs, per_ref=250)
    cfg = tr.TrainCfg()
    listener = tr.train(ds.train, ds.test_random, ds.n_classes, cfg, verbose=False)
    listener.eval()

    print(f"  warming a repetition log with {WARM} uniform-policy utterances")
    rep = RepetitionLog(half_life=48.0)
    for _ in range(WARM):
        ri = rng.randrange(len(refs))
        with torch.no_grad():
            ch = policy(ri)
        sc = phase3.build_scene(refs[ri], ch, rng)
        if sc is None:
            continue
        rep.observe(refs[ri].id, sc, render(sc))
    print(f"    log holds {rep.total_medoids()} medoids across "
          f"{len(rep.buckets)} buckets, seq={rep.seq}")

    within_R, within_M, state_R, state_M = [], [], [], []
    zero_spread = 0

    for _ in range(N_STATES):
        ri = rng.randrange(len(refs))
        ref = refs[ri]
        rs, ms = [], []
        seen = set()
        for _ in range(N_ACTIONS * 3):
            if len(rs) >= N_ACTIONS:
                break
            with torch.no_grad():
                ch = policy(ri)
            key = tuple(sorted((k, str(v)) for k, v in ch.values.items()))
            if key in seen:
                continue
            seen.add(key)
            sc = phase3.build_scene(ref, ch, rng)
            if sc is None:
                continue
            surf = render(sc)
            ids = torch.tensor([tk.encode(surf)], device=dev)
            with torch.no_grad():
                p = float(torch.softmax(listener(ids), dim=1)[0][ri])
            rs.append(rep.score(ref.id, sc)["novelty_cost"])
            ms.append(p)
        if len(rs) < 8:
            continue
        sr, sm = S.pstdev(rs), S.pstdev(ms)
        if sr == 0.0:
            zero_spread += 1
        within_R.append(sr)
        within_M.append(sm)
        state_R.append(S.fmean(rs))
        state_M.append(S.fmean(ms))

    wR, wM = S.fmean(within_R), S.fmean(within_M)
    aR, aM = S.pstdev(state_R), S.pstdev(state_M)

    print(f"\n  states usable: {len(within_R)}/{N_STATES}")
    print(f"  states where R was IDENTICAL for every action: {zero_spread}")
    print("\n  spread of each reward term (sd):")
    print(f"    R  within-state (action-steerable)  {wR:.4f}")
    print(f"    R  across-state (noise lambda scales) {aR:.4f}")
    print(f"    M  within-state (action-steerable)  {wM:.4f}")
    print(f"    M  across-state                      {aM:.4f}")
    if wR > 0:
        print(f"\n  R signal-to-noise across the action space: {wR / aR:.3f}"
              if aR else "")

    print("\n  per-lambda: which term does the policy actually feel?")
    print(f"    {'lambda':>7}  {'lam*sd(R)':>10}  {'sd(M)':>8}  {'novelty share':>14}")
    shares = {}
    for lam in LAMBDAS:
        nov = lam * wR
        share = nov / (nov + wM) if (nov + wM) > 0 else 0.0
        shares[lam] = share
        print(f"    {lam:>7}  {nov:>10.4f}  {wM:>8.4f}  {100 * share:>13.1f}%")

    print("\n  per-lambda: gradient magnitude the advantage actually carries")
    print(f"    {'lambda':>7}  {'sd(advantage)':>14}  {'vs lambda=0':>12}")
    a0 = None
    for lam in LAMBDAS:
        # advantage sd ~ sd of (m + lam*(1-R)) over ALL steps, signal+noise
        tot = ((wM ** 2 + aM ** 2) + (lam ** 2) * (wR ** 2 + aR ** 2)) ** 0.5
        a0 = tot if a0 is None else a0
        print(f"    {lam:>7}  {tot:>14.4f}  {tot / a0:>11.2f}x")

    (OUT / "lambda_purchase.json").write_text(json.dumps({
        "warm": WARM, "n_states": len(within_R), "n_actions": N_ACTIONS,
        "zero_spread_states": zero_spread,
        "within_R": wR, "across_R": aR, "within_M": wM, "across_M": aM,
        "novelty_share": shares,
    }, indent=2), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'lambda_purchase.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
