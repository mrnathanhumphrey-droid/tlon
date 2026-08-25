"""PHASE 10.0 -- minimum detectable effect at 5 seeds, BEFORE any spend.

THE 9.2c DISCIPLINE, APPLIED PER SUB-QUESTION. Check whether a measurement can
fire before spending the cell that runs it. 9.2c was not run because its
predictor had 24/46 referents tied at 1.00; this asks the same question of
10.2 (dynamic reset), 10.3 (neural horn) and 10.4 (population).

VARIANCE PRIOR: Phase 8's observed within-arm seed spread on the ARCHIVE --
gaps +4.56 +5.39 +9.04 +10.15 +13.19 (runs/reset_dynamics.json).

⛔⛔ THAT PRIOR IS AN ASSUMPTION AND ITS RISK RUNS ONE WAY. A long green record
in one regime says nothing about a regime the code has never run in. v2 has
f2 = 10.5% against the archive's 15.9%, so v2's gap may be SMALLER; if the gap
shrinks while sd holds, power gets WORSE, not better. Every MDE below is
therefore OPTIMISTIC.

⛔ RULE ZERO IS MECHANICAL: every count/size printed carries an asserted
expected value. Measured statistics have nothing to assert against and are
flagged human-read-required.
"""
from __future__ import annotations

import json
import math
import pathlib
import statistics as S
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"

# t(df, 0.975) for a two-sided 95% interval
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
        8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 14: 2.145,
        19: 2.093, 24: 2.064, 29: 2.045, 39: 2.023, 49: 2.010}

FROZEN_SUBOPTIMALITY_BOUND = 3.73     # VERDICT_8: listener suboptimality, pts


class BannerMismatch(RuntimeError):
    pass


def banner(label, value, expected, fmt="{}"):
    if value != expected:
        raise BannerMismatch(f"{label}: printed {value!r}, expected {expected!r}")
    print(f"    {label:<54} {fmt.format(value)}")


def t975(df):
    if df in T975:
        return T975[df]
    return min(T975[k] for k in T975 if k >= df) if df <= 49 else 1.96


def mde(sd, n, alpha_t=None):
    """Smallest true effect a two-sided 95% test at n can exclude zero for."""
    t = alpha_t or t975(n - 1)
    return t * sd / math.sqrt(n)


def n_for(sd, target_hw):
    """Seeds needed for a 95% CI half-width of target_hw."""
    for n in range(3, 400):
        if t975(n - 1) * sd / math.sqrt(n) <= target_hw:
            return n
    return None


def main() -> int:
    print("=" * 78)
    print("PHASE 10.0 -- MDE AT 5 SEEDS, COMPUTED BEFORE ANY TRAINING SPEND")
    print("=" * 78)

    rd = json.loads((RUNS / "reset_dynamics.json").read_text())
    gaps = [100 * r["gap_final"] for r in rd["runs"]]
    banner("phase-8 seeds in the variance prior", len(gaps), 5)
    n = 5
    sd = S.stdev(gaps)                     # sample sd, the one a t-test uses
    mean = S.fmean(gaps)
    print(f"    {'observed gaps (pts)':<54} "
          f"{', '.join(f'{g:+.2f}' for g in gaps)}")
    print(f"    {'mean / sample sd (HUMAN-READ)':<54} "
          f"{mean:.2f} / {sd:.2f}")

    m5 = mde(sd, n)
    print(f"\n  MDE at n=5, two-sided 95%: {m5:.2f} pts")
    print(f"  (= t(4)={t975(4)} x {sd:.2f}/sqrt(5))")
    print(f"  95% CI half-width at n=5 is the same number: +/-{m5:.2f} pts,")
    print(f"  against a gap whose own level is {mean:.2f} pts "
          f"({100*m5/mean:.0f}% of it).")

    out = {"variance_prior": {"gaps_pts": gaps, "mean": mean, "sample_sd": sd,
                              "source": "runs/reset_dynamics.json, ARCHIVE set"},
           "n": n, "mde_pts": m5, "subquestions": {}}

    # ---- 10.2 dynamic reset ------------------------------------------------
    print("\n" + "-" * 78)
    print("  10.2 DYNAMIC RESET -- and branch 1 is an EQUIVALENCE claim\n")
    print("  Branches 2 and 4 (different level / no re-climb) are DIFFERENCE")
    print("  claims: they need the CI to exclude zero, so MDE applies directly")
    print(f"  and they are detectable if the change exceeds {m5:.2f} pts.")
    print("\n  ⛔⛔ BRANCH 1 -- 'RE-CLIMBS TO THE SAME LEVEL' -- IS NOT A")
    print("     DIFFERENCE CLAIM. It asserts post_final EQUALS pre. To assert")
    print("     equality you must EXCLUDE a difference you would care about,")
    print("     which needs the CI HALF-WIDTH below that margin -- a strictly")
    print("     harder thing than excluding zero.")
    for margin_frac in (0.25, 0.50):
        margin = margin_frac * mean
        need = n_for(sd, margin)
        ok = m5 <= margin
        print(f"     to claim 'same level' to within +/-{100*margin_frac:.0f}% "
              f"({margin:.2f} pts): "
              f"{'OK at n=5' if ok else f'needs n≈{need}'}")
    hw_frac = 100 * m5 / mean
    print(f"\n     At n=5 the CI half-width is {hw_frac:.0f}% of the gap level.")
    print("     'Same level' could only be asserted to about +/-half the gap,")
    print("     which is not a conservation claim in any useful sense.")
    verdict_102 = ("BRANCH 1 UNDERPOWERED-BY-CONSTRUCTION at n=5; "
                   "branches 2/4 detectable")
    print(f"\n  ⇒ {verdict_102}")
    print("     ⭐ The reset test is still WORTH RUNNING -- it can KILL")
    print("        conservation (branch 2 or 4) even though it cannot EARN it.")
    print("        Asymmetric, and the kill is the cheaper, more likely result.")
    out["subquestions"]["10.2"] = {
        "branch1_equivalence": True, "mde_pts": m5,
        "ci_halfwidth_pct_of_gap": hw_frac,
        "n_for_25pct_equivalence": n_for(sd, 0.25 * mean),
        "n_for_50pct_equivalence": n_for(sd, 0.50 * mean),
        "verdict": verdict_102}

    # ---- 10.3 neural horn --------------------------------------------------
    print("\n" + "-" * 78)
    print("  10.3 NEURAL-SUBOPTIMALITY HORN\n")
    print(f"    frozen-arm suboptimality bound      {FROZEN_SUBOPTIMALITY_BOUND:.2f} pts")
    print(f"    MDE at n=5                          {m5:.2f} pts")
    if m5 > FROZEN_SUBOPTIMALITY_BOUND:
        print("\n  ⛔⛔ THE MDE EXCEEDS THE THING WE ARE TRYING TO RULE OUT.")
        print("     At 5 seeds we cannot resolve a difference smaller than the")
        print("     suboptimality bound itself, so no direct measurement can")
        print("     separate 'pact' from 'suboptimality' at this n.")
        verdict_103 = "UNDERPOWERED-BY-CONSTRUCTION for a DIRECT measure at n=5"
    else:
        verdict_103 = "direct measure may be feasible at n=5"
    print(f"\n  ⇒ {verdict_103}")
    print("     ⭐ 10.2 still bears on it INDIRECTLY and at no extra cell: a")
    print("        suboptimality artefact should not collapse-and-re-climb the")
    print("        way a co-adapted pact does. Branch 4 is consistent with")
    print("        suboptimality; branch 1 or 2 is against pure suboptimality.")
    print("     ⇒ report the horn as NARROWED-BY-10.2, never independently closed.")
    out["subquestions"]["10.3"] = {
        "frozen_bound_pts": FROZEN_SUBOPTIMALITY_BOUND, "mde_pts": m5,
        "direct_measure": verdict_103, "status": "narrowed-by-10.2 only"}

    # ---- 10.4 population ---------------------------------------------------
    print("\n" + "-" * 78)
    print("  10.4 POPULATION, PAIRED CONTROL\n")
    print("    (b) GAP LEVEL CHANGE uses the same variance prior as 10.2, so")
    print(f"        its MDE is also {m5:.2f} pts. Phase 8.3b already reported no")
    print("        power below ~3 pts, and this is the same statement computed")
    print("        from the same five seeds.")
    print("\n    (a) ENTROPY SPIKE is the one genuinely improved by pairing.")
    print("        Phase 8.3a was void because it compared windows WITHIN one")
    print("        run, so the monotone convergence trend swamped the transient")
    print("        (read -7.0%). A matched no-reset control differences that")
    print("        trend out, and the paired sd is UNKNOWN -- no run has ever")
    print("        produced one. ⛔ Its MDE therefore CANNOT be computed here")
    print("        and must be reported from the run itself.")
    print("\n  ⇒ 10.4b UNDERPOWERED on the same grounds as 10.2 branch 1;")
    print("     10.4a NOT PRE-COMPUTABLE -- pairing is exactly what changes the")
    print("     variance, and we have no paired variance estimate to use.")
    out["subquestions"]["10.4"] = {
        "b_gap_level_mde_pts": m5,
        "b_verdict": "UNDERPOWERED at n=5, same prior as 10.2",
        "a_entropy_spike": "MDE NOT PRE-COMPUTABLE -- no paired variance "
                           "estimate exists; report from the run"}

    # ---- red-proof: does this calculator compute anything? -----------------
    print("\n" + "-" * 78)
    print("  RED-PROOF -- can the MDE calculator move at all?\n")
    a, b = mde(sd, 5), mde(sd, 25)
    c = mde(sd / 4, 5)
    print(f"    same sd, n=5 -> n=25 : {a:.2f} -> {b:.2f} pts  "
          f"({'falls' if b < a else 'DOES NOT FALL'})")
    print(f"    same n, sd/4         : {a:.2f} -> {c:.2f} pts  "
          f"({'falls' if c < a else 'DOES NOT FALL'})")
    if not (b < a and c < a):
        print("  XX RED-PROOF FAILED -- the calculator is not computing an MDE.")
        return 1
    print("    ✅ responds to both n and sd, so the numbers above are an MDE")

    print("\n" + "=" * 78)
    print("  BOTTOM LINE, BEFORE ANY TRAINING")
    print("  • 10.2 CAN KILL conservation (branch 2/4) but CANNOT EARN it")
    print(f"    (branch 1) at n=5 -- equivalence needs n≈{n_for(sd, 0.25*mean)}"
          " for a +/-25% claim.")
    print("  • 10.3 has NO direct measure at n=5; narrowed by 10.2 only.")
    print("  • 10.4b is underpowered; 10.4a is not pre-computable.")
    print("  ⛔ All MDEs are OPTIMISTIC: they use the ARCHIVE's variance, and")
    print("     v2's lower f2 may shrink the gap while leaving sd alone.")
    print("  ⭐ HUMAN-READ REQUIRED: mean/sd above are measured, so no banner")
    print("     can assert them. Rule zero does not cover them.")

    (RUNS / "phase10_0_mde.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {RUNS / 'phase10_0_mde.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
