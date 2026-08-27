"""KI-AS-TARGET — the locked readings. Scores the probe against the prereg.

⛔⛔ THE ORDER OF THE CHECKS IS ITSELF A GUARD. Last run's Q2 branched on the
realised marginal before testing uniformity, so a 75 %-collapsed model read
"✅ holds flat". The fix was ordering, and it is ordering again here: the
commitment, the harness, the reproduction and the variance checks each run BEFORE
the relief verdict and each can HALT it. A reading that cannot be halted by its
own preconditions is not a reading.

    1  COMMITMENT   every scored arm carries the sha of N_COMMITTED.json, and
                    the arm count equals the committed N          → else REFUSE
    2  HARNESS      adapter_mt re-served reproduces the stored 14 → else HALT
    3  REPRODUCTION B-fresh reproduces the known suppression      → else HALT
    4  VARIANCE     run-to-run noise does not swamp the contrast  → else HALT
    5  RELIEF       the pre-declared verdict, and only now

⭐ The unit of independence is the EXCHANGE. Every test here is on exchange-level
means, because sizing and testing must agree — the power calculation was
clustered, so the test is clustered.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
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
#: Reproduction tolerance, as a t-statistic against the STORED baseline
#: exchanges. Not an absolute band: the stored arm has its own sampling error and
#: a fixed "±0.02" would ignore it.
REPRODUCTION_T_MAX = 2.00
MIN_DISTINCT_RATIO = 0.50


class Refuse(RuntimeError):
    pass


def _forces(transcript):
    out = []
    for s in transcript:
        try:
            sc = parse(s)
        except Exception:                                          # noqa: BLE001
            continue
        if render(sc) == s and sc.force in FM.ORDER:
            out.append(sc.force)
    return out


def exchange_rate(path: pathlib.Path, rows) -> dict:
    """`P(ki | prior ∈ rows)` for ONE exchange, plus its per-prior breakdown."""
    d = json.loads(path.read_text(encoding="utf-8"))
    t = d["transcript_interacting"]
    if not t or len(set(t)) / len(t) < MIN_DISTINCT_RATIO:
        raise Refuse(f"{path.name}: DEGENERATE ({len(set(t))}/{len(t)} distinct)")
    f = _forces(t)
    tr = list(zip(f, f[1:]))
    sel = [(p, r) for p, r in tr if p in rows]
    by = {}
    for p in FM.ORDER:
        sub = [r for q, r in tr if q == p]
        if sub:
            by[p] = {"n": len(sub),
                     "ki_rate": sum(r == TARGET for r in sub) / len(sub)}
    return {"file": path.name, "commitment_sha": d.get("commitment_sha"),
            "n": len(sel), "hit": sum(r == TARGET for _, r in sel),
            "rate": (sum(r == TARGET for _, r in sel) / len(sel)) if sel else None,
            "by_prior": by,
            "global_ki": (sum(r == TARGET for _, r in tr) / len(tr)) if tr else None}


def load_arm(paths, rows, *, label: str, commitment: str | None,
             expect_n: int | None) -> dict:
    ex = []
    for p in paths:
        e = exchange_rate(p, rows)
        if commitment is not None:
            # ⛔⛔ THE ORDERING LOCK. An arm generated before the commitment
            # existed cannot carry its hash — so this is not a formality, it is
            # the proof that the MDE branch was fixed before any relief datum.
            if e["commitment_sha"] != commitment:
                raise Refuse(
                    f"{p.name}: commitment sha {e['commitment_sha']!r} != "
                    f"{commitment!r}. Either this arm predates the throughput "
                    "commitment or the commitment changed after the arms ran. "
                    "Both make the MDE branch uninterpretable.")
        if e["rate"] is not None:
            ex.append(e)
    if expect_n is not None and len(ex) != expect_n:
        raise Refuse(
            f"{label}: {len(ex)} usable exchanges but {expect_n} were COMMITTED. "
            "A count that does not match the commitment is a design chosen after "
            "the fact — report the committed N or amend the prereg, not both.")
    rates = [e["rate"] for e in ex]
    hit = sum(e["hit"] for e in ex)
    n = sum(e["n"] for e in ex)
    return {"label": label, "exchanges": ex, "rates": rates,
            "mean": sum(rates) / len(rates), "pooled": hit / n,
            "hit": hit, "n": n,
            "sd": (sum((r - sum(rates) / len(rates)) ** 2 for r in rates)
                   / (len(rates) - 1)) ** 0.5 if len(rates) > 1 else 0.0}


def welch(a: dict, b: dict) -> tuple[float, float]:
    """Δ of exchange-level means, and Welch t. Exchange = unit of independence."""
    na, nb = len(a["rates"]), len(b["rates"])
    va = a["sd"] ** 2
    vb = b["sd"] ** 2
    se = (va / na + vb / nb) ** 0.5
    d = b["mean"] - a["mean"]
    return d, (d / se if se else 0.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default="runs/act2/ki_target/logs")
    ap.add_argument("--commitment-file",
                    default="runs/act2/ki_target/N_COMMITTED.json")
    ap.add_argument("--stored-baseline", default="runs/act2/logs/mt_run")
    ap.add_argument("--out", default="runs/act2/ki_target/verdict.json")
    a = ap.parse_args()
    rows = set(FM.COMMON_UNIFORM_ROWS)
    L = pathlib.Path(a.logs)

    print("KI-AS-TARGET · THE LOCKED READINGS")
    print("=" * 78)
    print(f"  primary measure: P(ki | prior ∈ {list(FM.COMMON_UNIFORM_ROWS)})"
          f"   expectation {FM.COMMON_UNIFORM_EXPECTATION:.4f} in BOTH arms")
    print(f"  ⛔ stipulated row {FM.STIPULATED_SOURCE!r} EXCLUDED — it emits ki "
          "100 % by construction")
    report: dict = {"primary_rows": list(FM.COMMON_UNIFORM_ROWS)}

    # ── 1 · COMMITMENT ────────────────────────────────────────────────────────
    cf = pathlib.Path(a.commitment_file)
    if not cf.exists():
        raise SystemExit(f"⛔⛔ {cf} missing. The throughput branch was never "
                         "committed, so nothing here can be scored. Run "
                         "tools/act2_throughput_gate.py FIRST — that ordering "
                         "is the experiment's integrity, not a convenience.")
    commit = json.loads(cf.read_text(encoding="utf-8"))
    sha = hashlib.sha256(cf.read_bytes()).hexdigest()
    n_arm = commit["exchanges_per_arm"]
    mde = commit["mde"]
    print(f"\n── 1 · COMMITMENT ──")
    print(f"  branch {commit['branch']}  {n_arm}/arm  MDE {mde:.3f}  "
          f"partial_resolvable={commit['partial_resolvable']}")
    print(f"  sha256 {sha}")
    report["commitment"] = {**commit, "sha256": sha}

    try:
        b_fresh = load_arm(sorted(L.glob("bfresh_*.json")), rows,
                           label="B-fresh", commitment=sha, expect_n=n_arm)
        treat = load_arm(sorted(L.glob("treat_*.json")), rows,
                         label="T", commitment=sha, expect_n=n_arm)
        b_prior = load_arm(sorted(L.glob("bprior_*.json")), rows,
                           label="B-prior", commitment=sha,
                           expect_n=commit["variance_arm_exchanges"])
        stored = load_arm(sorted(pathlib.Path(a.stored_baseline)
                                 .glob("arm2_new_w1_*.json")), rows,
                          label="stored-14", commitment=None, expect_n=None)
    except Refuse as e:
        print(f"\n⛔⛔ REFUSED: {e}")
        return 1

    for arm in (b_fresh, treat, b_prior, stored):
        print(f"  {arm['label']:9s} {len(arm['rates']):3d} exch  "
              f"mean {arm['mean']:.4f}  sd {arm['sd']:.4f}  "
              f"pooled {arm['hit']}/{arm['n']} = {arm['pooled']:.4f}")
        report[arm["label"]] = {k: v for k, v in arm.items() if k != "exchanges"}

    halt = None

    # ── 2 · HARNESS ───────────────────────────────────────────────────────────
    print("\n── 2 · HARNESS CHECK (adapter_mt now vs the stored 14) ──")
    d2, t2 = welch(stored, b_prior)
    print(f"  Δ {d2:+.4f}   t {t2:+.2f}   (same weights, same prompt, same "
          "window)")
    if abs(t2) > REPRODUCTION_T_MAX:
        halt = ("⛔⛔ HARNESS DRIFT — the SAME adapter no longer reproduces its "
                "own stored result. The instrument changed; nothing downstream "
                "is readable.")
        print(f"  {halt}")
    else:
        print("  ✅ the harness reproduces itself")

    # ── 3 · REPRODUCTION ──────────────────────────────────────────────────────
    print("\n── 3 · REPRODUCTION CHECK (B-fresh vs the known suppression) ──")
    d3, t3 = welch(stored, b_fresh)
    print(f"  B-fresh {b_fresh['mean']:.4f} vs stored {stored['mean']:.4f}   "
          f"Δ {d3:+.4f}  t {t3:+.2f}")
    print(f"  global ki (continuity, NOT the primary measure): "
          f"{sum(e['global_ki'] for e in b_fresh['exchanges']) / len(b_fresh['exchanges']):.4f}"
          f"   stored 0.0920-ish")
    if abs(t3) > REPRODUCTION_T_MAX and halt is None:
        halt = ("⛔⛔ B-FRESH DOES NOT REPRODUCE THE KNOWN SUPPRESSION. The "
                "control failed, so the treatment arm is NOT READ. Halt and "
                "diagnose — pre-declared.")
        print(f"  {halt}")
    elif halt is None:
        print("  ✅ the control reproduces the suppression")

    # ── 4 · VARIANCE ──────────────────────────────────────────────────────────
    print("\n── 4 · RUN-TO-RUN VARIANCE (B-fresh vs B-prior, same map) ──")
    d4, _ = welch(b_prior, b_fresh)
    d5, t5 = welch(b_fresh, treat)
    print(f"  same-map difference   |Δ| {abs(d4):.4f}")
    print(f"  map effect (B→T)      |Δ| {abs(d5):.4f}")
    if abs(d4) >= abs(d5) and halt is None:
        halt = ("⛔ RUN-TO-RUN NOISE DOMINATES — two trainings on the SAME map "
                "differ by at least as much as the map effect. The contrast is "
                "uninterpretable in either direction. Pre-declared.")
        print(f"  {halt}")
    elif halt is None:
        print("  ✅ the map effect exceeds same-map run-to-run noise")

    # ── 5 · RELIEF ────────────────────────────────────────────────────────────
    print("\n── 5 · RELIEF — the pre-declared verdict ──")
    if halt:
        verdict = "HALTED"
        why = halt
        print(f"  {halt}\n  ⇒ VERDICT: HALTED (the treatment arm is not scored)")
    else:
        full = FM.COMMON_UNIFORM_EXPECTATION
        print(f"  B-fresh {b_fresh['mean']:.4f} → T {treat['mean']:.4f}   "
              f"relief {d5:+.4f}   (t {t5:+.2f}, MDE {mde:.3f})")
        print(f"  full relief would be {full:.4f} "
              f"(+{full - b_fresh['mean']:.4f})")
        if abs(d5) < mde:
            verdict = "UNDERPOWERED"
            why = (f"relief {d5:+.4f} is below the COMMITTED MDE {mde:.3f}. "
                   "Pre-declared: this is UNDERPOWERED, never 'no relief'.")
        elif d5 < 0:
            verdict = "REFUTED (relief is NEGATIVE)"
            why = (f"ki-emission FELL by {abs(d5):.4f} when ki became a target. "
                   "The asymmetry mechanism predicts the opposite sign.")
        elif treat["mean"] >= full - mde:
            verdict = "ASYMMETRY MECHANISM CONFIRMED"
            why = (f"relief {d5:+.4f} reaches the corpus expectation {full:.4f}. "
                   "Limit #1 paid down; forced cells must not create source-only "
                   "forces.")
        else:
            verdict = "PARTIAL"
            why = (f"relief {d5:+.4f} clears the MDE but stops at "
                   f"{treat['mean']:.4f}, short of {full:.4f}. Asymmetry is A "
                   f"cause, not THE cause. Residual "
                   f"{full - treat['mean']:.4f} unexplained.")
            if not commit["partial_resolvable"]:
                verdict = "UNDERPOWERED (fallback branch: PARTIAL not resolvable)"
                why += (" ⛔ The FALLBACK branch was committed, on which PARTIAL "
                        "is UNDERPOWERED BY DECLARATION.")
        print(f"  ⇒ VERDICT: {verdict}\n     {why}")

    report["relief"] = {"delta": d5, "t": t5, "mde": mde,
                        "verdict": verdict, "why": why}

    # ── stratified, because a pooled number can hide a row moving backwards ───
    print("\n── STRATIFIED BY PRIOR FORCE (the mechanism is directional) ──")
    print(f"  {'prior':>6} │ {'B-fresh':>9} {'T':>9}   Δ")
    strat = {}
    for f in FM.ORDER:
        def m(arm):
            v = [e["by_prior"][f]["ki_rate"] for e in arm["exchanges"]
                 if f in e["by_prior"]]
            return sum(v) / len(v) if v else None
        bf, tt = m(b_fresh), m(treat)
        mark = "  ⛔STIP" if f == FM.STIPULATED_SOURCE else (
            "" if f in rows else "  (forced)")
        if bf is None or tt is None:
            print(f"  {f:>6} │ {'--':>9} {'--':>9}{mark}")
            continue
        strat[f] = {"b_fresh": bf, "treatment": tt, "delta": tt - bf}
        print(f"  {f:>6} │ {bf:9.4f} {tt:9.4f}   {tt - bf:+.4f}{mark}")
    print(f"  ⭐ only {list(FM.COMMON_UNIFORM_ROWS)} enter the primary measure")
    report["stratified"] = strat

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                   encoding="utf-8", newline="")
    print(f"\nwrote {out}")
    print("\n⛔ THIS RUN PRODUCES NO DRIFT NUMBER. It unblocks the map-design "
          "question\n   that gates the arena; σ_cp remains downstream and "
          "unmeasured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
