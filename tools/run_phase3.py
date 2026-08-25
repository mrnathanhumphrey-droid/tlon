"""Phase 3 — lambda sweep. PREREG 3c49ad47.

For each lambda: co-train generator and listener, then measure with THREE
independent detectors.

  1. SCRAMBLE PROBE  — paired, on policy-generated utterances. A no-information
                       channel that suddenly matters is a code.
  2. GLOSS AUDITOR   — frozen Qwen2.5-1.5B, coarse 4-way. Audit only.
  3. CONCENTRATION   — free-and-cheap early warning: how peaked the policy has
                       become per channel. Uniform means no code.
"""
from __future__ import annotations
import json
import pathlib
import random
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

from tlon.grammar.gloss import gloss as to_gloss                   # noqa: E402
from tlon.grammar.parse import render                              # noqa: E402
from tlon.listener import auditor, data, evaluate as ev, train as tr  # noqa: E402
from tlon.listener import tokenizer as tk                          # noqa: E402
from tlon.listener.model import Listener                           # noqa: E402
from tlon.referents import schema                                  # noqa: E402
from tlon.selfplay import phase3                                   # noqa: E402
from cipher_control import CHANNELS, scramble                      # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
LAMBDAS = [0.0, 0.25, 0.5, 1.0, 2.0]
N_EVAL = 1800
N_AUDIT = 200
NOINFO = ("orient_order", "coda", "degree", "aspect_reps")


def sample_from_policy(policy, refs, rng, n):
    rows = []
    while len(rows) < n:
        ri = rng.randrange(len(refs))
        with torch.no_grad():
            ch = policy(ri)
        sc = phase3.build_scene(refs[ri], ch, rng)
        if sc is None:
            continue
        surf = render(sc)
        rows.append(data.Example(label=ri, ref_id=refs[ri].id, surface=surf,
                                 uid="", ids=tk.encode(surf), dec_key=""))
    return rows


def probe(model, rows, refs, groups, cfg, rng):
    out = {}
    for ch, _ in CHANNELS:
        orig, scr = [], []
        for ex in rows:
            s = scramble(ex.surface, ch, rng)
            if s is None:
                continue
            orig.append(ex)
            scr.append(data.Example(label=ex.label, ref_id=ex.ref_id, surface=s,
                                    uid="", ids=tk.encode(s), dec_key=""))
        if len(orig) < 50:
            continue
        b = ev.within_pair(orig, tr.predict(model, orig, cfg).tolist(), refs, groups)
        a = ev.within_pair(scr, tr.predict(model, scr, cfg).tolist(), refs, groups)
        if b["n"] < 30:
            continue
        out[ch] = b["acc"] - a["acc"]
    return out


def audit(rows, refs, rng, dev):
    items = []
    by_id = {r.id: r for r in refs}
    for ex in rows[:N_AUDIT]:
        target = refs[ex.label]
        tr_roots = set(target.roots())
        pool = [r for r in refs if r.id != target.id and not (set(r.roots()) & tr_roots)]
        if len(pool) < 3:
            continue
        names = [target.name] + [o.name for o in rng.sample(pool, 3)]
        order = list(range(4))
        rng.shuffle(order)
        items.append((to_gloss(__import__("tlon.grammar.parse", fromlist=["parse"]).parse(ex.surface)),
                      [names[i] for i in order], order.index(0)))
    return auditor.audit_coarse(items, device=dev).acc if items else float("nan")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    rs = schema.load_all()
    refs = rs.referents
    groups = {r.minimal_pair for r in refs if r.minimal_pair}
    cfg = tr.TrainCfg()

    print("=" * 76)
    print("PHASE 3 — lambda sweep. PREREG 3c49ad47")
    print("=" * 76)

    print("\n  pre-training the listener on random-generator data (phase-2 style)")
    ds = data.build(refs, per_ref=250)
    seed_listener = tr.train(ds.train, ds.test_random, ds.n_classes, cfg, verbose=False)
    base_state = {k: v.detach().clone() for k, v in seed_listener.state_dict().items()}
    print(f"    seeded listener ready ({len(ds.train)} examples)")

    results = []
    for lam in LAMBDAS:
        print(f"\n  ── lambda = {lam} ─────────────────────────────────────────")
        listener = Listener(len(refs)).to(dev)
        listener.load_state_dict(base_state)
        t0 = time.time()
        policy, rep, st = phase3.run(
            refs, listener, phase3.P3Cfg(lam=lam, device=dev), verbose=False)
        rng = random.Random(1000 + int(lam * 100))
        rows = sample_from_policy(policy, refs, rng, N_EVAL)

        conc = policy.concentration()
        unif = policy.uniform_baseline()
        drops = probe(listener, rows, refs, groups, cfg, rng)
        aud = audit(rows, refs, rng, dev)
        m_final = st.m_rate[-1] if st.m_rate else float("nan")
        r_final = st.rep_cost[-1] if st.rep_cost else float("nan")

        print(f"    {time.time() - t0:.0f}s   M {100 * m_final:.1f}%   "
              f"R {r_final:.3f}   auditor {100 * aud:.1f}%")
        print("    policy concentration (uniform -> collapsed):")
        for ch in conc:
            print(f"      {ch:12} {conc[ch]:.3f}  (uniform {unif[ch]:.3f})")
        print("    scramble drops (pts):")
        for ch, d in sorted(drops.items(), key=lambda x: -abs(x[1])):
            tag = "  ← NO-INFO CHANNEL" if ch in NOINFO and abs(d) > 0.01 else ""
            print(f"      {ch:12} {100 * d:+6.2f}{tag}")

        results.append({"lam": lam, "m": m_final, "r": r_final, "auditor": aud,
                        "concentration": conc, "drops": drops})

    (OUT / "phase3_sweep.json").write_text(
        json.dumps({"prereg": "3c49ad47", "results": results}, indent=2,
                   default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'phase3_sweep.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

