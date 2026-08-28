"""VARIANCE DECOMPOSITION — data draw or training draw? Plus two screens.

Prereg: docs/PREREG_VARIANCE_DECOMPOSE_2026_08_28.md

⭐ THE DESIGN IN ONE LINE: `S_combined` (0.1549) was measured with `--seed`
driving BOTH the corpus draw and the trainer. Here the corpus is held
BYTE-IDENTICAL and only the trainer seed varies, so the spread that survives is
the TRAINING draw's contribution.

⛔ THREE OUTPUTS, AND THEY ARE READ IN ORDER — each can void the next:
    1  DECOMPOSITION  R = S_training / S_combined
    2  SCREEN A       does the observable ranking survive builds it never saw?
    3  SCREEN B       coupling, measured with ACCUMULATION (the only regime in
                      which convention formation is even possible)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from act2_observable_screen import OBSERVABLES, scenes_of                # noqa: E402
from tlon.discourse import force_map as FM                               # noqa: E402
from tlon.grammar.parse import parse, render                             # noqa: E402

#: Measured 2026-08-28 over four adapters whose seed drove corpus AND trainer.
S_COMBINED = 0.1549
SEEDS = (30001, 30002, 30003)
MIN_DISTINCT_RATIO = 0.50
TARGET = "ki"


def ki_rate(transcript):
    f = [sc.force for sc, _ in scenes_of(transcript)]
    tr = [(a, b) for a, b in zip(f, f[1:]) if a in FM.COMMON_UNIFORM_ROWS]
    return (sum(b == TARGET for _, b in tr) / len(tr)) if tr else None


def load(paths, key="transcript_interacting"):
    out = []
    for p in paths:
        d = json.loads(p.read_text(encoding="utf-8"))
        t = d.get(key) or []
        if not t:
            continue
        out.append({"file": p.name, "t": t,
                    "c": d.get("transcript_control") or [],
                    "dr": len(set(t)) / len(t)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default="runs/act2/var_decomp/logs")
    ap.add_argument("--bfresh-logs", default="runs/act2/ki_target/logs")
    ap.add_argument("--out", default="runs/act2/var_decomp/decompose.json")
    a = ap.parse_args()
    L = pathlib.Path(a.logs)
    report = {}

    print("VARIANCE DECOMPOSITION — data draw or training draw?")
    print("=" * 78)
    print(f"  corpus held BYTE-IDENTICAL; only the trainer seed varies.")
    print(f"  S_combined (seed drove corpus AND trainer) = {S_COMBINED}")

    # ── 1 · DECOMPOSITION ────────────────────────────────────────────────────
    arms = {"s20620 (B-fresh)":
            load(sorted(pathlib.Path(a.bfresh_logs).glob("bfresh_*.json")))}
    for s in SEEDS:
        ps = sorted(L.glob(f"t{s}_w1_*.json"))
        if ps:
            arms[f"t{s}"] = load(ps)

    print("\n── 1 · DECOMPOSITION (window-1 arms) ──")
    means, deg = {}, {}
    for name, ex in arms.items():
        vals = [v for e in ex if (v := ki_rate(e["t"])) is not None]
        if len(vals) < 2:
            continue
        means[name] = sum(vals) / len(vals)
        deg[name] = sum(e["dr"] < MIN_DISTINCT_RATIO for e in ex)
        print(f"  {name:18s} k={len(vals):2d}  mean {means[name]:.4f}  "
              f"sd {statistics.stdev(vals):.4f}  degenerate {deg[name]}")

    if len(means) < 3:
        print("\n  ⛔ INCOMPLETE — fewer than 3 adapters; a spread over 2 draws "
              "is not an estimate.")
        verdict, R = "INCOMPLETE", None
    else:
        S_training = max(means.values()) - min(means.values())
        R = S_training / S_COMBINED
        print(f"\n  ⭐ S_training = {S_training:.4f}   "
              f"(min {min(means.values()):.4f} · max {max(means.values()):.4f})")
        print(f"     R = S_training / S_combined = {R:.2f}")
        if S_training > S_COMBINED:
            verdict = "⛔ UNSTABLE AT k=4 — NOT A DECOMPOSITION"
            why = ("S_training exceeds S_combined, which cannot be true of a "
                   "component. Both are sd-of-4-means and neither should be "
                   "quoted as a split. Pre-declared: do not pick the flattering "
                   "reading.")
        elif R >= 0.7:
            verdict = "⭐ THE VARIANCE IS IN THE TRAINING DRAW"
            why = ("Holding the corpus fixed did not shrink the spread. Cause is "
                   "init / shuffle / bf16 non-determinism. Fixes: average over "
                   "trainer seeds, or make training deterministic.")
        elif R <= 0.3:
            verdict = "⭐ THE VARIANCE IS IN THE DATA DRAW"
            why = ("Holding the corpus fixed collapsed the spread. Cause is WHICH "
                   "SURFACES the corpus sampled. Fixes: a larger corpus, or pin "
                   "the draw across arms so both maps see the same surfaces.")
        else:
            verdict = "BOTH CONTRIBUTE"
            why = (f"R {R:.2f} sits between the pre-declared bands; report the "
                   "split, claim neither source.")
        print(f"  ⇒ {verdict}\n     {why}")
        report["decomposition"] = {"S_training": S_training,
                                   "S_combined": S_COMBINED, "R": R,
                                   "verdict": verdict, "why": why,
                                   "means": means, "degenerate": deg}
    print("  ⚠️ R is a ratio of two noisy k=4 quantities — read as a DIRECTION, "
          "not a coefficient.")

    # ── 2 · SCREEN A ─────────────────────────────────────────────────────────
    print("\n── 2 · SCREEN A · does the observable ranking survive fresh builds? ──")
    per_build = {n: [scenes_of(e["t"]) for e in ex] for n, ex in arms.items()}
    rank = []
    for oname, fn in OBSERVABLES.items():
        bmeans, moves = [], []
        for scl in per_build.values():
            vals = [v for scs in scl if (v := fn(scs)) is not None]
            if len(vals) < 2:
                continue
            bmeans.append(sum(vals) / len(vals))
            for scs in scl:
                h = len(scs) // 2
                f1, f2 = fn(scs[:h]), fn(scs[h:])
                if f1 is not None and f2 is not None:
                    moves.append(abs(f2 - f1))
        if len(bmeans) < 3 or not moves:
            continue
        mv = sum(moves) / len(moves)
        rank.append((oname, statistics.stdev(bmeans) / mv if mv else float("inf")))
    rank.sort(key=lambda x: x[1])
    for i, (o, c) in enumerate(rank, 1):
        print(f"  {i:2d}. {o:18s} contamination {c:.2f}")
    top3 = [o for o, _ in rank[:3]]
    ki_rank = next((i for i, (o, _) in enumerate(rank, 1) if o == "force:ki"), None)
    held = ("root TTR" in top3) and (ki_rank is None or ki_rank > 3)
    print(f"\n  pre-declared: root TTR in top 3 AND force:ki outside it")
    print(f"  observed: top3={top3}  force:ki rank={ki_rank}")
    print(f"  ⇒ {'⭐ RANKING HELD — selectable' if held else '⛔ RANKING REORDERED — no observable may be selected on contamination yet'}")
    report["screen_a"] = {"rank": rank, "top3": top3, "ki_rank": ki_rank,
                          "held": bool(held)}

    # ── 3 · SCREEN B ─────────────────────────────────────────────────────────
    print("\n── 3 · SCREEN B · coupling, WITH ACCUMULATION ──")
    acc = []
    for s in SEEDS:
        acc += load(sorted(L.glob(f"t{s}_acc_*.json")))
    if not acc:
        print("  ⛔ no accumulating exchanges found")
    else:
        ndeg = sum(e["dr"] < MIN_DISTINCT_RATIO for e in acc)
        print(f"  {len(acc)} accumulating exchanges · degenerate {ndeg} "
              "(REPORTED, not dropped)")
        print(f"  {'observable':18s} {'live':>9s} {'frozen':>9s} {'paired Δ':>10s} "
              f"{'t':>7s}")
        couples = []
        for oname, fn in OBSERVABLES.items():
            deltas = []
            for e in acc:
                si, sc = scenes_of(e["t"]), scenes_of(e["c"])
                if len(si) < 8 or len(sc) < 8:
                    continue
                hi, hc = len(si) // 2, len(sc) // 2
                a1, a2 = fn(si[:hi]), fn(si[hi:])
                c1, c2 = fn(sc[:hc]), fn(sc[hc:])
                if None in (a1, a2, c1, c2):
                    continue
                deltas.append(abs(a2 - a1) - abs(c2 - c1))
            if len(deltas) < 3:
                continue
            m = sum(deltas) / len(deltas)
            sd = statistics.stdev(deltas)
            t = m / (sd / len(deltas) ** 0.5) if sd else 0.0
            couples.append({"observable": oname, "paired_delta": m, "t": t,
                            "n": len(deltas)})
            print(f"  {oname:18s} {'':>9s} {'':>9s} {m:+10.4f} {t:+7.2f}")
        live = [c for c in couples if c["paired_delta"] > 0 and c["t"] > 2.0]
        if live:
            print(f"\n  ⭐ COUPLES (paired t > 2): {[c['observable'] for c in live]}")
        elif any(c["paired_delta"] > 0 for c in couples):
            print("\n  ⚠️ UNDERPOWERED — positive coupling excess but no paired "
                  "t > 2 at this n.\n     Pre-declared: NOT 'no coupling'.")
        else:
            print("\n  ⛔⛔ NO OBSERVABLE COUPLES EVEN WITH ACCUMULATION.\n"
                  "     A foundation finding larger than any map question: these "
                  "models do not\n     adapt to each other, and 'emergent "
                  "convention' is not measurable with this\n     apparatus "
                  "regardless of observable.")
        report["screen_b"] = {"n_exchanges": len(acc), "n_degenerate": ndeg,
                              "couples": couples}

    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                   encoding="utf-8", newline="")
    print(f"\nwrote {a.out}")
    print("\n⛔ No treatment arm, no map comparison, no drift number. σ_cp remains "
          "unmeasured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
