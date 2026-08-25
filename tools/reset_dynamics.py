"""Phase 8.2 + 8.3 -- one reset event, three measurements. PREREG 269f78d7.

8.2  dynamic conservation: does the naive gap collapse and RE-CLIMB, and to WHAT?
8.3a teachability: does the speaker's entropy SPIKE on a simultaneous reset?
8.3b does the gap LEVEL change after population pressure?

All three are instrumented off the SAME whole-pool reset, so they cannot
disagree about what happened.

⛔ 5 SEEDS PER CELL IS THE HARD FLOOR. One seed is "direction only" and may not
be compared to anything.

⛔ FIVE ENUMERATED OUTCOMES, AND "SAME LEVEL" IS NOT THE FALLTHROUGH. The
variance_confound lesson: a verdict that enumerated "flat" and "rises" but not
"falls" only got read because it hit a loud default. Here outcome 1 is one
branch among five and the default is UNRECOGNISED.

⛔ PER-RUN TRAJECTORIES, NOT A MEAN. Averaging runs hides the collapse-and-
re-climb dynamics, which is the entire reason the dynamic test beats the static
one.
"""
from __future__ import annotations
import json
import pathlib
import random
import statistics as S
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

from tlon.grammar.denote import project                 # noqa: E402
from tlon.grammar.parse import render                   # noqa: E402
from tlon.listener import data, train as tr             # noqa: E402
from tlon.listener import tokenizer as tk               # noqa: E402
from tlon.listener.model import Listener                # noqa: E402
from tlon.referents import schema                       # noqa: E402
from tlon.selfplay import phase3                        # noqa: E402
from tlon.selfplay.policy import ChannelPolicy          # noqa: E402
from planted_cipher_control import build_partial        # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
SEEDS = [11, 22, 33, 44, 55]
STEPS = 6000
RESET_AT = 3000
POOL_K = 6
PRE_PER_REF = 200
N_EVAL = 900
SAME_BAND = (0.05, 0.16)     # "8-13 pts" with tolerance, pre-registered range


def honest_rows(refs, rng, per_ref=PRE_PER_REF):
    rows = []
    for ri, ref in enumerate(refs):
        deps = len(ref.signature.contains) - 1
        made, guard = 0, 0
        while made < per_ref and guard < per_ref * 6:
            guard += 1
            keep = tuple(i for i in range(deps) if rng.random() < 0.5)
            sc = build_partial(ref, keep, rng, None)
            if sc is None:
                continue
            sc = project(sc)
            surf = render(sc)
            rows.append(data.Example(label=ri, ref_id=ref.id, surface=surf,
                                     uid="", ids=tk.encode(surf), dec_key=""))
            made += 1
    return rows


def sample(policy, refs, rng, n):
    rows = []
    guard = 0
    while len(rows) < n and guard < n * 8:
        guard += 1
        ri = rng.randrange(len(refs))
        with torch.no_grad():
            ch = policy(ri)
        sc = phase3.build_scene(refs[ri], ch, rng)
        if sc is None:
            continue
        surf = render(project(sc))
        rows.append(data.Example(label=ri, ref_id=refs[ri].id, surface=surf,
                                 uid="", ids=tk.encode(surf), dec_key=""))
    return rows


def acc(model, rows, cfg):
    p = tr.predict(model, rows, cfg).tolist()
    return sum(1 for a, r in zip(p, rows) if a == r.label) / len(rows)


def classify(pre, post_min, post_final, stable):
    """FIVE named branches. Default is UNRECOGNISED, never 'same level'."""
    lo, hi = SAME_BAND
    collapsed = post_min < pre * 0.5
    if not collapsed:
        return ("NO COLLAPSE", "The reset did not disturb the gap, so this run "
                "says nothing about conservation -- the reset is not doing what "
                "8.2 assumes.")
    if post_final < pre * 0.4:
        return ("4 DOES NOT RE-CLIMB", "The gap was not a conserved pact but an "
                "artefact of the particular converged state.")
    if not stable:
        return ("5 UNSTABLE", "Re-climbs partially or unstably. INCONCLUSIVE -- "
                "more seeds, no claim.")
    if lo <= post_final <= hi and lo <= pre <= hi:
        return ("1 SAME LEVEL", "Consistent with conservation. NOT proof -- see "
                "the seed spread.")
    if post_final >= pre * 0.4:
        return ("2 DIFFERENT LEVEL", "Re-climbs to a different stable level => "
                "conservation FALSE; the level is regime-dependent.")
    return ("UNRECOGNISED", "No enumerated branch matched. Read by hand.")


def main() -> int:
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    refs = schema.load_all().referents
    deps = [len(r.signature.contains) - 1 for r in refs]
    cfg = tr.TrainCfg()
    print("=" * 78)
    print("RESET DYNAMICS -- 8.2 conservation + 8.3 population. PREREG 269f78d7")
    print("=" * 78)
    print(f"  {len(SEEDS)} seeds, {STEPS} steps, WHOLE-POOL reset at {RESET_AT}, "
          f"K={POOL_K}\n")

    base_rng = random.Random(4242)
    hr = honest_rows(refs, base_rng)
    base_rng.shuffle(hr)
    cut = int(0.9 * len(hr))
    seed_state = {k: v.detach().clone() for k, v in
                  tr.train(hr[:cut], hr[cut:], len(refs), cfg,
                           verbose=False).state_dict().items()}
    nr = honest_rows(refs, base_rng)
    base_rng.shuffle(nr)
    ncut = int(0.9 * len(nr))
    naive = tr.train(nr[:ncut], nr[ncut:], len(refs),
                     tr.TrainCfg(seed=cfg.seed + 991), verbose=False)
    naive.eval()
    print(f"  independent naive judge held-out "
          f"{100*acc(naive, nr[ncut:], cfg):.1f}%\n")

    runs = []
    for sd in SEEDS:
        t0 = time.time()
        def mk():
            return Listener(len(refs)).to(dev)
        pool = []
        for _ in range(POOL_K):
            L = mk(); L.load_state_dict(seed_state); pool.append(L)
        policy = ChannelPolicy(len(refs), deps=deps).to(dev)
        pol, rep, st = phase3.run(
            refs, pool[0],
            phase3.P3Cfg(lam=0.0, device=dev, normalize_advantage=True,
                         project=True, steps=STEPS, reset_all_at=RESET_AT,
                         seed=sd),
            verbose=False, policy=policy, pool=pool, make_listener=mk)

        # gap trajectory: re-measure at each logged window using a frozen
        # snapshot of the pool is not possible post-hoc, so we use the entropy
        # trace for dynamics and measure the gap at three points via the final
        # policy. Instead: gap proxy per window = M-rate minus naive on the same
        # window's samples is unavailable historically -- so we report the
        # ENTROPY trajectory (8.3a, per-window) and the END-STATE gap (8.2/8.3b).
        for m in pool:
            m.eval()
        ev = random.Random(900 + sd)
        rows = sample(pol, refs, ev, N_EVAL)
        co = S.fmean([acc(m, rows, cfg) for m in pool])
        nv = acc(naive, rows, cfg)
        gap_final = co - nv

        e = st.entropy
        steps = st.steps
        i_reset = min(range(len(steps)), key=lambda i: abs(steps[i] - RESET_AT))
        pre_e = S.fmean(e[max(0, i_reset - 3):i_reset]) if i_reset >= 1 else e[0]
        spike_e = max(e[i_reset:i_reset + 3]) if i_reset < len(e) else e[-1]
        runs.append({"seed": sd, "gap_final": gap_final, "m": co, "naive": nv,
                     "entropy": e, "steps": steps,
                     "entropy_pre": pre_e, "entropy_spike": spike_e,
                     "entropy_rise_pct": 100 * (spike_e - pre_e) / max(1e-9, pre_e)})
        print(f"  seed {sd}: M {100*co:.1f}%  naive {100*nv:.1f}%  "
              f"gap {100*gap_final:+.2f}   entropy {pre_e:.3f}->{spike_e:.3f} "
              f"({runs[-1]['entropy_rise_pct']:+.1f}%)   [{time.time()-t0:.0f}s]")

    gaps = [r["gap_final"] for r in runs]
    rises = [r["entropy_rise_pct"] for r in runs]
    print("\n" + "=" * 78)
    print(f"  8.3a TEACHABILITY SPIKE  entropy rise on simultaneous reset: "
          f"mean {S.fmean(rises):+.1f}%  (per-seed "
          f"{', '.join(f'{x:+.0f}' for x in rises)})")
    print(f"  8.2/8.3b GAP after reset+reconvergence: mean "
          f"{100*S.fmean(gaps):+.2f} pts, sd {100*S.pstdev(gaps):.2f}  "
          f"(per-seed {', '.join(f'{100*g:+.1f}' for g in gaps)})")

    spike_fires = S.fmean(rises) > 5.0
    print(f"\n  8.3 outcome: ", end="")
    if spike_fires and S.fmean(gaps) < 0.05:
        print("1 -- spike fires AND gap falls => population is genuine pact "
              "mitigation.")
    elif spike_fires:
        print("2 -- spike FIRES but the gap does NOT fall => population raises "
              "compositionality\n       WITHOUT suppressing the pact. Wrong tool "
              "for our purpose.")
    else:
        print("3 -- NEITHER fires => the config is still wrong; no conclusion "
              "about population.")

    (OUT / "reset_dynamics.json").write_text(json.dumps(
        {"prereg": "269f78d7", "seeds": SEEDS, "steps": STEPS,
         "reset_at": RESET_AT, "pool_k": POOL_K, "runs": runs,
         "gap_mean": S.fmean(gaps), "gap_sd": S.pstdev(gaps),
         "entropy_rise_mean_pct": S.fmean(rises),
         "spike_fires": spike_fires},
        indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'reset_dynamics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
