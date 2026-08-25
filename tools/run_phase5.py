"""PHASE 5 -- denotation projection + listener population. PREREG c09d0fb3.

Cleared to run by `pi_controls.py`: a 2-bit code in a STRIPPED channel buys
-0.30 pts under pi (vs +6.67 without it) => the receptor is gone; the same-sized
code in a SURVIVING channel is detected at +54.87 pts => the probe still works.

ABLATED, so we learn which move did the work:
    phase-4 replication | pi only | population only | both

THE DETECTOR THIS PHASE TURNS ON: the NAIVE-LISTENER GAP.
    gap = acc(co-trained) - acc(naive), both on the learned generator's output
The naive listener is trained ONLY on honest random-generator data and never
enters the loop. It must NOT be trained on the generator's output -- a listener
trained on coded data learns the code, the gap reads zero, and the test could
not have come back positive.

KILL E is the outcome to fear: naive gap stays open while the scramble probe
reads clean. That means the code moved into meaning-bearing structure where
scrambling cannot see it -- worse than phase 4, because it looks like success.
"""
from __future__ import annotations
import gc
import json
import pathlib
import random
import statistics as S
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

from tlon.grammar.denote import nondenoting_parts, project  # noqa: E402
from tlon.grammar.parse import render                      # noqa: E402
from tlon.listener import data, train as tr                # noqa: E402
from tlon.listener import tokenizer as tk                  # noqa: E402
from tlon.listener.model import Listener                   # noqa: E402
from tlon.referents import schema                          # noqa: E402
from tlon.referents.match import consistent                # noqa: E402
from tlon.selfplay import phase3                           # noqa: E402
from tlon.selfplay.policy import ChannelPolicy             # noqa: E402
from cipher_control import CHANNELS, scramble              # noqa: E402
from planted_cipher_control import build_partial           # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
LAMBDAS = [0.0, 2.0]
PRE_PER_REF = 200
N_EVAL = 1500
POOL_K = 6
RESET_EVERY = 500
SEED = 20260822
NOINFO = ("orient_order", "coda", "degree", "aspect_reps")
SURVIVING = ("aspect_root", "orient")
KILL_A = 1.0
KILL_E_GAP = 5.0

# Which EventNode part each probe channel perturbs. Used to decide, FROM pi
# ITSELF, which channels pi holds constant.
_CH_PART = {"aspect_reps": "aspect.reps", "degree": "degree", "coda": "force",
            "aspect_root": "aspect.root", "orient_order": "orient"}


def undefined_under_pi() -> set:
    """Channels pi pins to a constant -- the probe is MEANINGLESS on them.

    Scrambling a constant channel does not remove information, it manufactures
    an utterance that never occurs in training. Any resulting drop measures
    BRITTLENESS, not a code. The tell in the first run: aspect_reps read +0.00
    at lambda=0 and +7.84 at lambda=2 with the channel constant in both -- what
    scaled was overfitting. `orient_order` is excluded separately: pi sorts
    orientations, so the perturbation is a no-op by construction (+0.00 on every
    seed ever measured).
    """
    nd = nondenoting_parts()
    return {ch for ch, part in _CH_PART.items() if part in nd} | {"orient_order"}


def honest_rows(refs, rng, use_pi, per_ref=PRE_PER_REF):
    """Random-generator partial utterances -- the honest language.

    Used for BOTH the seed listener and the naive judge. Rendered in the same
    view as the arm: a naive listener trained on unprojected surfaces would fail
    on projected ones for reasons that have nothing to do with a code.
    """
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
            if use_pi:
                sc = project(sc)
            surf = render(sc)
            rows.append(data.Example(label=ri, ref_id=ref.id, surface=surf,
                                     uid="", ids=tk.encode(surf), dec_key=""))
            made += 1
    return rows


def sample_rows(policy, refs, rng, n, use_pi):
    rows, amb = [], []
    guard = 0
    while len(rows) < n and guard < n * 8:
        guard += 1
        ri = rng.randrange(len(refs))
        with torch.no_grad():
            ch = policy(ri)
        sc = phase3.build_scene(refs[ri], ch, rng)
        if sc is None:
            continue
        view = project(sc) if use_pi else sc
        surf = render(view)
        rows.append(data.Example(label=ri, ref_id=refs[ri].id, surface=surf,
                                 uid="", ids=tk.encode(surf), dec_key=""))
        amb.append(sum(1 for b in refs if consistent(view, b.signature)))
    return rows, amb


def acc(model, rows, cfg):
    if len(rows) < 10:
        return float("nan")
    p = tr.predict(model, rows, cfg).tolist()
    return sum(1 for a, r in zip(p, rows) if a == r.label) / len(rows)


def mean_acc(models, rows, cfg):
    return S.fmean([acc(m, rows, cfg) for m in models])


def stratified_probe(models, rows, amb, cfg, rng):
    """Paired scramble, averaged over every pool member."""
    out = {}
    for ch, _ in CHANNELS:
        orig, scr, keep = [], [], []
        for ex, av in zip(rows, amb):
            s = scramble(ex.surface, ch, rng)
            if s is None:
                continue
            orig.append(ex)
            keep.append(av)
            scr.append(data.Example(label=ex.label, ref_id=ex.ref_id,
                                    surface=s, uid="", ids=tk.encode(s),
                                    dec_key=""))
        if len(orig) < 50:
            out[ch] = {"overall": float("nan"), "ambiguous": float("nan"),
                       "n": len(orig), "unavailable": True}
            continue
        rec = {"overall": mean_acc(models, orig, cfg) - mean_acc(models, scr, cfg),
               "n": len(orig)}
        ao = [r for r, a in zip(orig, keep) if a > 1]
        as_ = [r for r, a in zip(scr, keep) if a > 1]
        rec["ambiguous"] = (mean_acc(models, ao, cfg) - mean_acc(models, as_, cfg)
                            if len(ao) >= 30 else float("nan"))
        out[ch] = rec
    return out


def main() -> int:
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    rng = random.Random(SEED)
    refs = schema.load_all().referents
    deps = [len(r.signature.contains) - 1 for r in refs]
    cfg = tr.TrainCfg()

    print("=" * 78)
    print("PHASE 5 -- pi + listener population. PREREG c09d0fb3")
    print("=" * 78)
    print(f"  pool K={POOL_K}, reset every {RESET_EVERY} steps, "
          f"advantage normalised, lambda in {LAMBDAS} (0 is the primary read)")

    # Seed + naive listeners, one pair per view. The naive judge NEVER enters a
    # training loop -- that is what makes the gap mean something.
    seeds, naives = {}, {}
    for use_pi in (False, True):
        tag = "pi" if use_pi else "raw"
        rows = honest_rows(refs, rng, use_pi)
        rng.shuffle(rows)
        cut = int(0.9 * len(rows))
        seeds[use_pi] = {k: v.detach().clone() for k, v in
                         tr.train(rows[:cut], rows[cut:], len(refs), cfg,
                                  verbose=False).state_dict().items()}
        # THE NAIVE JUDGE MUST BE AN INDEPENDENT MODEL. tr.train seeds itself
        # from cfg.seed, so training twice on the same rows with the same cfg
        # returns BYTE-IDENTICAL weights -- the frozen control then compares a
        # model to itself and its gap is 0.00 by construction, a test that
        # cannot come back positive. Different init seed AND a disjoint draw.
        nrows = honest_rows(refs, rng, use_pi)
        rng.shuffle(nrows)
        ncut = int(0.9 * len(nrows))
        naives[use_pi] = tr.train(nrows[:ncut], nrows[ncut:], len(refs),
                                  tr.TrainCfg(seed=cfg.seed + 991),
                                  verbose=False)
        naives[use_pi].eval()
        same = all(torch.equal(a.cpu(), b.detach().cpu()) for a, b in
                   zip(seeds[use_pi].values(), naives[use_pi].state_dict().values()))
        if same:
            raise SystemExit("naive judge is identical to the seed listener; "
                             "every gap would be 0.00 by construction")
        print(f"  [{tag}] seed listener on {len(rows)} rows; INDEPENDENT naive "
              f"judge on {len(nrows)} disjoint rows, held-out "
              f"{100 * acc(naives[use_pi], nrows[ncut:], cfg):.1f}%")

    # HONEST BASELINE per view. `aspect_root` genuinely denotes -- pi keeps it
    # precisely because signatures constrain it -- so scrambling it destroys
    # real meaning and a fixed 1.0 pt threshold there is a test that CANNOT come
    # back negative. The honest drop must be MEASURED, in the same view, with an
    # untrained policy that cannot have built a code. KILL A then rides on the
    # EXCESS over it.
    baseline = {}
    for use_pi in (False, True):
        pol = ChannelPolicy(len(refs), deps=deps).to(dev)
        L = Listener(len(refs)).to(dev)
        L.load_state_dict(seeds[use_pi])
        L.eval()
        ev = random.Random(4242)
        rows, amb = sample_rows(pol, refs, ev, N_EVAL, use_pi)
        baseline[use_pi] = stratified_probe([L], rows, amb, cfg, ev)
        b = baseline[use_pi]
        print(f"  [{'pi' if use_pi else 'raw'}] honest baseline "
              f"aspect_root {100 * b['aspect_root']['ambiguous']:+.2f} pts "
              f"(ambiguous stratum), M {100 * acc(L, rows, cfg):.1f}%")
        del pol, L
        gc.collect()
        if dev == "cuda":
            torch.cuda.empty_cache()

    # FROZEN arms are the distribution-shift control. The naive gap measures
    # "a listener that only knows the honest language cannot follow this
    # generator" -- which is a private code OR merely unusual statistics. With
    # the listener frozen, co-adaptation is impossible, so whatever gap remains
    # is the distribution-shift component. Subtract it to attribute the rest.
    # NOTE: the flag is `co_adapt`, never `co` -- `co` is the co-trained
    # ACCURACY thirty lines below, and naming both the same silently overwrote
    # the flag on every second lambda with a truthy float, so half the frozen
    # arms trained anyway and reported numbers identical to their co-adapting
    # twins.
    arms = [("FROZEN ctrl", False, False, False),
            ("FROZEN ctrl pi", True, False, False),
            ("phase-4 replication", False, False, True),
            ("pi only", True, False, True),
            ("population only", False, True, True),
            ("BOTH", True, True, True)]
    results = []
    for tag, use_pi, use_pop, co_adapt in arms:
        for lam in LAMBDAS:
            def mk():
                return Listener(len(refs)).to(dev)
            pool = None
            if use_pop:
                pool = []
                for _ in range(POOL_K):
                    L = mk()
                    L.load_state_dict(seeds[use_pi])
                    pool.append(L)
                listener = pool[0]
            else:
                listener = mk()
                listener.load_state_dict(seeds[use_pi])
            policy = ChannelPolicy(len(refs), deps=deps).to(dev)
            t0 = time.time()
            policy, rep, st = phase3.run(
                refs, listener,
                phase3.P3Cfg(lam=lam, device=dev, normalize_advantage=True,
                             project=use_pi, train_listener=co_adapt,
                             reset_every=RESET_EVERY if use_pop else 0),
                verbose=False, policy=policy, pool=pool, make_listener=mk)
            models = pool if pool else [listener]
            for m in models:
                m.eval()

            ev = random.Random(700 + int(lam * 100))
            rows, amb = sample_rows(policy, refs, ev, N_EVAL, use_pi)
            co = mean_acc(models, rows, cfg)
            nv = acc(naives[use_pi], rows, cfg)
            gap = co - nv
            floor = S.fmean([1.0 / x for x in amb])
            drops = stratified_probe(models, rows, amb, cfg, ev)
            dec = policy.selection_decidedness()
            r = st.rep_cost[-1] if st.rep_cost else float("nan")

            skip = undefined_under_pi() if use_pi else {"orient_order"}
            base = baseline[use_pi]
            excess, fired = {}, []
            for c in NOINFO + SURVIVING:
                if c in skip or c not in drops:
                    continue
                v = drops[c]["ambiguous"]
                if v != v:
                    continue
                # Subtract the honest drop for channels that genuinely denote.
                b = base.get(c, {}).get("ambiguous", 0.0)
                ref_v = b if (c in SURVIVING and b == b) else 0.0
                excess[c] = v - ref_v
                if 100 * excess[c] > KILL_A:
                    fired.append((c, round(100 * excess[c], 2)))
            probe_clean = not fired
            kill_e = probe_clean and 100 * gap > KILL_E_GAP

            print(f"\n  -- {tag}  lambda={lam} " + "-" * max(4, 40 - len(tag)))
            print(f"    {time.time() - t0:.0f}s   M {100 * co:.1f}%  "
                  f"(own floor {100 * floor:.1f}%)   R {r:.3f}   "
                  f"decidedness {dec:.3f}   ambiguous {100 * sum(1 for x in amb if x > 1) / len(amb):.1f}%")
            print(f"    NAIVE-LISTENER GAP  {100 * gap:+.2f} pts   "
                  f"(co-trained {100 * co:.1f} vs naive {100 * nv:.1f})")
            for ch in NOINFO + SURVIVING:
                if ch not in drops:
                    continue
                d = drops[ch]
                if ch in skip:
                    print(f"      {ch:<13} -- pi holds this constant; probe "
                          f"undefined (scrambling it is a distribution shift)")
                    continue
                mark = "  <- KILL A" if ch in dict(fired) else ""
                amb_s = ("   n/a" if d["ambiguous"] != d["ambiguous"]
                         else f"{100 * d['ambiguous']:+6.2f}")
                exc = ("" if ch not in excess
                       else f"   excess {100 * excess[ch]:+6.2f}")
                print(f"      {ch:<13} overall {100 * d['overall']:+6.2f}   "
                      f"ambiguous {amb_s}{exc}{mark}")
            if kill_e:
                print("    ⛔⛔ KILL E -- gap open while the probe reads clean. "
                      "The code went underground.")

            del models, pool, listener, policy
            gc.collect()
            if dev == "cuda":
                torch.cuda.empty_cache()

            results.append({"arm": tag, "lam": lam, "pi": use_pi, "pop": use_pop,
                            "m": co, "naive": nv, "gap": gap, "own_floor": floor,
                            "r": r, "decidedness": dec, "drops": drops,
                            "kill_a": fired, "kill_e": kill_e, "co_adapting": co_adapt,
                            "excess": excess})

    print("\n" + "=" * 78)
    frozen = {(r["pi"], r["lam"]): r["gap"] for r in results
              if not r["co_adapting"]}
    print(f"  {'arm':<22}{'lam':>5}{'M':>8}{'gap':>9}{'shift':>8}{'CODE':>8}"
          f"{'KILL A':>9}{'KILL E':>8}")
    for r in results:
        sh = frozen.get((r["pi"], r["lam"]))
        code = "" if sh is None or not r["co_adapting"] else f"{100 * (r['gap'] - sh):>+8.2f}"
        shs = "" if sh is None else f"{100 * sh:>+8.2f}"
        print(f"  {r['arm']:<22}{r['lam']:>5}{100 * r['m']:>7.1f}%"
              f"{100 * r['gap']:>+8.2f}{shs}{code}"
              f"{'FIRED' if r['kill_a'] else '  ok':>9}"
              f"{'FIRED' if r['kill_e'] else '  ok':>8}")

    (OUT / "phase5.json").write_text(json.dumps(
        {"prereg": "c09d0fb3", "pool_k": POOL_K, "reset_every": RESET_EVERY,
         "honest_baseline": baseline,
         "results": results}, indent=2, default=float),
        encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'phase5.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
