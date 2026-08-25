"""PHASE 4 — impression-selection. PREREG c1f7d06c + DEVIATIONS_4.

The generator now chooses what to LEAVE OUT. Reference resolution stops being
free, so a code finally has something to buy, and KILL A is reachable --
established by `planted_cipher_control.py`, which showed the probe fires at
+27.05 pts on a code that is known to be there and stays at +0.17 without one.

ARMS
  random        untrained policy, selection on. No optimisation, so no code can
                form. This is the D2 negative control: absence CONSTRUCTED, not
                inferred. The stratum split cannot serve this role -- a real
                cipher bleeds +14.29 pts onto the unambiguous stratum.
  learned l=..  REINFORCE on NORMALISED advantage (phase 3: lambda scales
                advantage variance 2.17x as well as novelty weight, so a raw
                sweep confounds the two and reads backwards).

REPORTING
  m_vs_ceiling against m_honest_observed = 0.921, never 100%. D1: the 89.3%
  figure is E[1/|consistent set|] -- uniform picking inside the consistency set,
  a FLOOR on a perfect listener, not a ceiling. The no-code arm exceeded it.
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

from tlon.grammar.parse import render                  # noqa: E402
from tlon.listener import data, train as tr            # noqa: E402
from tlon.listener import tokenizer as tk              # noqa: E402
from tlon.listener.model import Listener               # noqa: E402
from tlon.referents import schema                      # noqa: E402
from tlon.selfplay import phase3                       # noqa: E402
from tlon.selfplay.policy import ChannelPolicy         # noqa: E402
from cipher_control import CHANNELS, scramble          # noqa: E402
from confusability import consistent                   # noqa: E402
from planted_cipher_control import build_partial       # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
LAMBDAS = [0.0, 1.0, 2.0]
PRE_PER_REF = 200
N_EVAL = 1500
SEED = 20260820
NOINFO = ("orient_order", "coda", "degree", "aspect_reps")
M_HONEST = 0.921      # measured no-code arm, planted_cipher.json
M_FLOOR = 0.893       # E[1/|C|]; a FLOOR, not a ceiling (DEVIATIONS_4 D1)
KILL_A = 1.0
KILL_A_PRIME = 0.5
KILL_D = 0.70


def pretrain_rows(refs, rng):
    """Partial utterances, random selection -- the regime the listener must
    start in. Pre-training on full utterances would hand it a world that no
    longer exists and the first gradient steps would be spent unlearning it."""
    rows = []
    for ri, ref in enumerate(refs):
        deps = len(ref.signature.contains) - 1
        made, guard = 0, 0
        while made < PRE_PER_REF and guard < PRE_PER_REF * 6:
            guard += 1
            keep = tuple(i for i in range(deps) if rng.random() < 0.5)
            sc = build_partial(ref, keep, rng, None)
            if sc is None:
                continue
            surf = render(sc)
            rows.append(data.Example(label=ri, ref_id=ref.id, surface=surf,
                                     uid="", ids=tk.encode(surf), dec_key=""))
            made += 1
    return rows


def sample_rows(policy, refs, rng, n):
    """Draw from the policy and record the ambiguity of each utterance.

    Ambiguity is computed on the SUBSET THE POLICY ACTUALLY CHOSE, not from a
    static per-referent label -- the policy decides per utterance how much to
    withhold, so the stratum is a property of the utterance.
    """
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
        surf = render(sc)
        rows.append(data.Example(label=ri, ref_id=refs[ri].id, surface=surf,
                                 uid="", ids=tk.encode(surf), dec_key=""))
        amb.append(sum(1 for b in refs if consistent(sc, b.signature)))
    return rows, amb


def acc(model, rows, cfg) -> float:
    if len(rows) < 10:
        return float("nan")
    preds = tr.predict(model, rows, cfg).tolist()
    return sum(1 for p, r in zip(preds, rows) if p == r.label) / len(rows)


def stratified_probe(model, rows, amb, cfg, rng):
    """Paired scramble, reported overall / ambiguous / unambiguous."""
    out = {}
    for ch, _ in CHANNELS:
        orig, scr, keep_amb = [], [], []
        for ex, av in zip(rows, amb):
            s = scramble(ex.surface, ch, rng)
            if s is None:
                continue
            orig.append(ex)
            keep_amb.append(av)
            scr.append(data.Example(label=ex.label, ref_id=ex.ref_id, surface=s,
                                    uid="", ids=tk.encode(s), dec_key=""))
        if len(orig) < 50:
            continue

        def split(rs, want):
            return [r for r, a in zip(rs, keep_amb) if (a > 1) == want]

        rec = {"overall": acc(model, orig, cfg) - acc(model, scr, cfg)}
        for name, want in (("ambiguous", True), ("unambiguous", False)):
            o, s_ = split(orig, want), split(scr, want)
            rec[name] = (acc(model, o, cfg) - acc(model, s_, cfg)
                         if len(o) >= 30 else float("nan"))
        rec["n"] = len(orig)
        out[ch] = rec
    return out


def main() -> int:
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    rng = random.Random(SEED)
    refs = schema.load_all().referents
    deps = [len(r.signature.contains) - 1 for r in refs]
    cfg = tr.TrainCfg()

    print("=" * 78)
    print("PHASE 4 -- IMPRESSION-SELECTION. PREREG c1f7d06c")
    print("=" * 78)
    print(f"  {len(refs)} referents, dependents per referent: "
          f"min {min(deps)} max {max(deps)} mean {S.fmean(deps):.2f}")
    print(f"  M reported against m_honest_observed = {100 * M_HONEST:.1f}% "
          f"(NOT 100%; the {100 * M_FLOOR:.1f}% figure is a FLOOR -- see "
          f"DEVIATIONS_4 D1)")

    print(f"\n  pre-training the listener ON PARTIAL UTTERANCES")
    pre = pretrain_rows(refs, rng)
    cut = int(0.9 * len(pre))
    rng.shuffle(pre)
    seed_l = tr.train(pre[:cut], pre[cut:], len(refs), cfg, verbose=False)
    base_state = {k: v.detach().clone() for k, v in seed_l.state_dict().items()}
    print(f"    {len(pre)} examples, held-out accuracy "
          f"{100 * acc(seed_l, pre[cut:], cfg):.1f}%")

    # The last arm is the artefact control: identical training, but the policy
    # is FORBIDDEN to steer aspect_reps/degree, so those channels provably carry
    # no code. The policy still concentrates on what it does control and the
    # listener still overfits a narrow distribution -- so if the probe fires
    # here too, it is reading overfitting, not ciphering, and KILL A's number is
    # uninterpretable. This is the alternative explanation the `random` arm
    # cannot rule out, because that listener is never overfit at all.
    arms = ([("random", None, ())]
            + [(f"learned l={l}", l, ()) for l in LAMBDAS]
            + [("l=2 CODELESS ctrl", 2.0, ("aspect_reps", "degree"))])
    results = []
    for tag, lam, uni in arms:
        print(f"\n  -- {tag} " + "-" * max(4, 58 - len(tag)))
        listener = Listener(len(refs)).to(dev)
        listener.load_state_dict(base_state)
        policy = ChannelPolicy(len(refs), deps=deps,
                               uniform_channels=uni).to(dev)
        t0 = time.time()
        if lam is None:
            rep = st = None                      # untrained: no code can form
        else:
            policy, rep, st = phase3.run(
                refs, listener,
                phase3.P3Cfg(lam=lam, device=dev, normalize_advantage=True),
                verbose=False, policy=policy)
        ev_rng = random.Random(500 + int((lam or 0) * 100))
        rows, amb = sample_rows(policy, refs, ev_rng, N_EVAL)
        a = acc(listener, rows, cfg)
        sel = policy.selection_rate()
        dec = policy.selection_decidedness()
        conc = policy.concentration()
        frac_amb = sum(1 for x in amb if x > 1) / len(amb)
        drops = stratified_probe(listener, rows, amb, cfg, ev_rng)

        # Each arm's own uniform floor. M_HONEST was measured under RANDOM
        # selection; a learned policy selects informatively and shifts the
        # ambiguity distribution (25.1% -> ~15%), so dividing every arm by one
        # cross-regime constant compares two numbers that share a name without
        # sharing a measurement. The floor is a property of the utterances the
        # arm actually produced.
        floor = S.fmean([1.0 / x for x in amb])
        print(f"    {time.time() - t0:.0f}s   M {100 * a:.1f}%   ambiguous rows "
              f"{100 * frac_amb:.1f}%   own uniform floor "
              f"{100 * floor:.1f}%   M - floor {100 * (a - floor):+.1f} pts")
        print(f"    selection: rate {sel:.3f}  DECIDEDNESS {dec:.3f} "
              f"(0.50 undecided, 1.0 committed)   mean concentration "
              f"{sum(conc.values()) / len(conc):.3f}")
        print(f"    {'channel':<13}{'overall':>9}{'ambiguous':>11}"
              f"{'unambig':>9}")
        for ch, d in sorted(drops.items(), key=lambda x: -abs(x[1]["ambiguous"])
                            if x[1]["ambiguous"] == x[1]["ambiguous"] else 0):
            flag = ""
            if ch in NOINFO and 100 * d["ambiguous"] > KILL_A:
                flag = "  <- KILL A"
            print(f"    {ch:<13}{100 * d['overall']:>+9.2f}"
                  f"{100 * d['ambiguous']:>+11.2f}"
                  f"{100 * d['unambiguous']:>+9.2f}{flag}")
        results.append({"arm": tag, "lam": lam, "m": a, "uniform": list(uni),
                        "own_uniform_floor": floor, "m_minus_floor": a - floor,
                        "selection_rate": sel,
                        "decidedness": dec, "concentration": conc,
                        "frac_ambiguous": frac_amb, "drops": drops,
                        "r": (st.rep_cost[-1] if st and st.rep_cost else None)})

    # ── kills ────────────────────────────────────────────────────────────
    print("\n" + "=" * 78)
    ctrl = results[0]
    worst_ctrl = max((abs(ctrl["drops"][c]["overall"])
                      for c in NOINFO if c in ctrl["drops"]), default=0.0)
    print(f"  KILL A' (probe specificity, on the CONSTRUCTED no-code arm): "
          f"{100 * worst_ctrl:+.2f} pts, needs <= {KILL_A_PRIME}"
          f"   {'PASS' if 100 * worst_ctrl <= KILL_A_PRIME else 'FAIL'}")
    for r in results[1:]:
        if r["uniform"]:
            continue
        fired = [(c, r["drops"][c]["ambiguous"]) for c in NOINFO
                 if c in r["drops"] and 100 * r["drops"][c]["ambiguous"] > KILL_A]
        # KILL C watches DECIDEDNESS, not rate. Mean rate can sit at 0.50
        # while the policy is fully committed per slot -- rate answers "how
        # much does it say", decidedness answers "has it learned to choose".
        sel_moved = r["decidedness"] - 0.5 > 0.05
        print(f"  {r['arm']:<14} KILL A "
              f"{'FIRED ' + str([(c, round(100 * v, 2)) for c, v in fired]) if fired else 'not fired'}"
              f"   | KILL C {'ok (selection moved)' if sel_moved else 'FIRED (selection inert)'}"
              f"   | KILL D {'FIRED' if r['m'] < KILL_D else 'ok'}")

    (OUT / "phase4.json").write_text(json.dumps(
        {"prereg": "c1f7d06c", "m_honest_observed": M_HONEST,
         "m_uniform_floor": M_FLOOR, "results": results}, indent=2,
        default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'phase4.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
