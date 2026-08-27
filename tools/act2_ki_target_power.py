"""POWER FOR THE KI-AS-TARGET MECHANISM PROBE. Run BEFORE the box, $0.

⛔⛔ LIMIT #2 FROM THE LAST RUN, PAID DOWN. Last run declared MDE 0.0800 and
observed |Δ| 0.0723 — the effect landed BELOW the resolution and the magnitude
was never pinned. **This tool computes the required N before a dollar is spent**,
and the number it prints goes into the prereg. If the probe later observes relief
below the declared MDE the verdict is UNDERPOWERED, never "no relief."

⛔⛔ AND IT SIZES THE RIGHT MEASURE. The obvious one — the global `ki` marginal —
MANUFACTURES RELIEF: `ko`→`ki` forced means `ko` emits `ki` 100 % of the time by
construction, so the global marginal rises whether or not anything was relieved.
The stipulation would be measuring itself and it would look like a clean
confirmation. The primary measure is therefore `P(ki | prior ∈
COMMON_UNIFORM_ROWS)` — rows uniform in BOTH maps, whose corpus expectation is
0.20 in BOTH arms.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.discourse import force_map as FM                        # noqa: E402
from tlon.grammar.parse import parse, render                      # noqa: E402

#: ⭐ THE TARGET RESOLUTION, AND WHY. Full relief moves `ki` from the observed
#: baseline to the corpus expectation 0.20 — roughly a 0.10 shift. An MDE at half
#: that leaves the probe able to resolve PARTIAL relief, which is a pre-declared
#: branch and would be invisible at an MDE equal to the full effect.
TARGET_MDE = 0.04
POWER = 0.80
ALPHA = 0.05


def observed_baseline(logs: pathlib.Path) -> dict:
    """`P(ki | prior ∈ COMMON_UNIFORM_ROWS)` measured on the arm we already ran.

    ⭐ THE BASELINE RATE IS MEASURED, NOT ASSUMED. Power computed from a guessed
    base rate is a guess with a decimal point on it.
    """
    common = set(FM.COMMON_UNIFORM_ROWS)
    hit = n = 0
    per_ex, files = [], sorted(logs.glob("arm2_new_w1_*.json"))
    if not files:
        raise SystemExit(f"⛔ no baseline arm under {logs}")
    for p in files:
        t = json.loads(p.read_text(encoding="utf-8"))["transcript_interacting"]
        f = []
        for s in t:
            try:
                sc = parse(s)
            except Exception:                                      # noqa: BLE001
                continue
            if render(sc) == s and sc.force in FM.ORDER:
                f.append(sc.force)
        tr = [(a, b) for a, b in zip(f, f[1:]) if a in common]
        if tr:
            per_ex.append(sum(b == "ki" for _, b in tr) / len(tr))
        hit += sum(b == "ki" for _, b in tr)
        n += len(tr)
    return {"rate": hit / n, "hit": hit, "n": n, "exchanges": len(files),
            "per_exchange_n": n / len(files), "per_exchange_rates": per_ex}


def power_at(n_per_arm: int, p0: float, p1: float, *, trials: int,
             seed: int) -> float:
    """⚠️ THE NAÏVE, INDEPENDENCE-ASSUMING CALCULATION. Kept only to PRINT how
    much it overstates. Do not size on it."""
    rng = random.Random(seed)
    det = 0
    for _ in range(trials):
        a = sum(rng.random() < p0 for _ in range(n_per_arm))
        b = sum(rng.random() < p1 for _ in range(n_per_arm))
        pa, pb = a / n_per_arm, b / n_per_arm
        pp = (a + b) / (2 * n_per_arm)
        se = (pp * (1 - pp) * (2 / n_per_arm)) ** 0.5
        if se and abs(pa - pb) / se > 1.96:
            det += 1
    return det / trials


def required_n(p0: float, delta: float, *, trials: int, seed: int) -> int:
    lo, hi = 32, 64
    while power_at(hi, p0, p0 + delta, trials=trials, seed=seed) < POWER:
        lo, hi = hi, hi * 2
        if hi > 2 ** 20:
            raise SystemExit("⛔ required N exploded; check the base rate")
    while lo < hi:
        mid = (lo + hi) // 2
        if power_at(mid, p0, p0 + delta, trials=trials, seed=seed) >= POWER:
            hi = mid
        else:
            lo = mid + 1
    return lo


# ═══ THE SIZING THAT ACTUALLY GOVERNS ════════════════════════════════════════
# ⛔⛔ TRANSITIONS ARE **CLUSTERED WITHIN EXCHANGE** AND THE NAÏVE CALCULATION
# ABOVE PRETENDS THEY ARE NOT. Measured last run, per-exchange `ki` rates ran
# 0.000 to 0.258 — that is a large between-exchange component, and treating 1,024
# clustered transitions as 1,024 independent ones OVERSTATES power. Sizing on it
# would reproduce the exact failure this tool exists to fix, one level down:
# a declared MDE that the run cannot actually achieve.
#
# ⇒ Power is computed by resampling WHOLE EXCHANGES from the observed
#   per-exchange rates, and the test statistic is a two-sample t on the
#   EXCHANGE-LEVEL means — the unit of independence is the exchange, so that is
#   the unit the test uses.
def _t_two_sample(xs, ys) -> float:
    nx, ny = len(xs), len(ys)
    mx, my = sum(xs) / nx, sum(ys) / ny
    vx = sum((x - mx) ** 2 for x in xs) / (nx - 1)
    vy = sum((y - my) ** 2 for y in ys) / (ny - 1)
    se = (vx / nx + vy / ny) ** 0.5
    return abs(mx - my) / se if se else 0.0


#: t critical at α=0.05 two-sided; ~1.98 by 100 df and the arms are large, so a
#: single conservative constant is honest here (it is ABOVE the asymptotic 1.96).
T_CRIT = 2.00


def cluster_power(n_exchanges: int, rates, delta: float, m: float, *,
                  trials: int, seed: int) -> float:
    """Resample exchanges, shift the treatment arm by `delta`, t-test the means.

    `rates` are the OBSERVED per-exchange rates, so the between-exchange variance
    is empirical rather than assumed. `m` is the per-exchange transition count,
    which supplies the within-exchange binomial noise on top.
    """
    rng = random.Random(seed)
    mi = max(1, int(round(m)))
    det = 0
    for _ in range(trials):
        a, b = [], []
        for _ in range(n_exchanges):
            ra = rng.choice(rates)
            a.append(sum(rng.random() < ra for _ in range(mi)) / mi)
            rb = min(1.0, max(0.0, rng.choice(rates) + delta))
            b.append(sum(rng.random() < rb for _ in range(mi)) / mi)
        if _t_two_sample(a, b) > T_CRIT:
            det += 1
    return det / trials


def required_exchanges(rates, delta: float, m: float, *, trials: int,
                       seed: int, cap: int = 4096) -> int:
    lo, hi = 4, 8
    while cluster_power(hi, rates, delta, m, trials=trials, seed=seed) < POWER:
        lo, hi = hi, hi * 2
        if hi > cap:
            return -1                       # ⭐ unreachable, reported not hidden
    while lo < hi:
        mid = (lo + hi) // 2
        if cluster_power(mid, rates, delta, m, trials=trials, seed=seed) >= POWER:
            hi = mid
        else:
            lo = mid + 1
    return lo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default="runs/act2/logs/mt_run")
    ap.add_argument("--turns", type=int, default=40)
    ap.add_argument("--trials", type=int, default=3000)
    ap.add_argument("--out", default="runs/act2/ki_target/power.json")
    a = ap.parse_args()

    print("KI-AS-TARGET · POWER, DECLARED BEFORE THE BOX")
    print("=" * 78)
    print(FM.DERIVED_v1.describe())
    print()
    print(FM.STIPULATED_KI_TARGET_v1.describe())
    print()
    print(f"⭐ COMMON UNIFORM ROWS (uniform in BOTH maps): "
          f"{list(FM.COMMON_UNIFORM_ROWS)}")
    print(f"   corpus expectation on those rows, BOTH arms: "
          f"{FM.COMMON_UNIFORM_EXPECTATION:.4f}")
    print(f"   stipulated source {FM.STIPULATED_SOURCE!r} is EXCLUDED from the "
          f"primary measure — its row is a design zero in the treatment arm.")
    print(f"   replication source held: {FM.REPLICATION_SOURCE_HELD!r}")
    print()

    base = observed_baseline(pathlib.Path(a.logs))
    print("── OBSERVED BASELINE (measured, not assumed) ──")
    print(f"  P(ki | prior ∈ common) = {base['hit']}/{base['n']} = "
          f"{base['rate']:.4f}   over {base['exchanges']} exchanges")
    print(f"  common-stratum transitions per exchange: "
          f"{base['per_exchange_n']:.1f}  (at {a.turns} turns)")
    print(f"  ⇒ FULL relief would move it to "
          f"{FM.COMMON_UNIFORM_EXPECTATION:.4f}, a shift of "
          f"{FM.COMMON_UNIFORM_EXPECTATION - base['rate']:+.4f}")
    print()

    # ⛔ The treatment arm's common stratum is SMALLER: the stipulated row leaves
    # the uniform set. Size on the SMALLER of the two or the treatment arm is
    # quietly underpowered while the baseline looks fine.
    st_t = FM.STIPULATED_KI_TARGET_v1.stationary()
    share_t = sum(st_t[f] for f in FM.COMMON_UNIFORM_ROWS)
    st_b = FM.DERIVED_v1.stationary()
    share_b = sum(st_b[f] for f in FM.COMMON_UNIFORM_ROWS)
    print("── COMMON-STRATUM SHARE BY DESIGN (the treatment arm is smaller) ──")
    print(f"  baseline  {share_b:.4f}      treatment {share_t:.4f}")
    obs_share = base["per_exchange_n"] / (a.turns - 1)
    print(f"  observed baseline share {obs_share:.4f}; scaling the treatment by "
          f"the design ratio\n  gives "
          f"{obs_share * share_t / share_b:.4f} "
          f"⇒ {(a.turns - 1) * obs_share * share_t / share_b:.1f} usable "
          f"transitions per treatment exchange")
    per_ex_treat = (a.turns - 1) * obs_share * share_t / share_b
    print()

    rates = base["per_exchange_rates"]
    mean_r = sum(rates) / len(rates)
    sd_r = (sum((r - mean_r) ** 2 for r in rates) / (len(rates) - 1)) ** 0.5
    print("── ⛔⛔ TRANSITIONS ARE CLUSTERED WITHIN EXCHANGE ──")
    print(f"  observed per-exchange rates: "
          f"{[round(r, 3) for r in sorted(rates)]}")
    print(f"  mean {mean_r:.4f}  sd {sd_r:.4f}   ⇒ the unit of independence is "
          f"the EXCHANGE,\n  not the transition. Sizing on independent "
          f"transitions overstates power.")
    print()

    print(f"── REQUIRED N  (power {POWER:.0%}, α {ALPHA}, "
          f"{a.trials} trials/point) ──")
    print("     Δ    naïve-indep      CLUSTERED (governs)     overstatement")
    rows = []
    for delta in (0.10, 0.08, 0.06, TARGET_MDE, 0.03, 0.02):
        n = required_n(base["rate"], delta, trials=a.trials, seed=17)
        ex_naive = -(-n // int(per_ex_treat))
        ex_cl = required_exchanges(rates, delta, per_ex_treat,
                                   trials=a.trials, seed=17)
        rows.append({"delta": delta, "n_per_arm_naive": n,
                     "exchanges_naive": ex_naive,
                     "exchanges_clustered": ex_cl})
        star = "  ⭐ TARGET" if abs(delta - TARGET_MDE) < 1e-9 else ""
        cl = f"{ex_cl:5d}" if ex_cl > 0 else "  >4k"
        fac = (f"{ex_cl / ex_naive:.1f}×" if ex_cl > 0 else "unreachable")
        print(f"  {delta:.2f}   {ex_naive:5d} exch      {cl} exch"
              f"            {fac}{star}")
    chosen = next(r for r in rows if abs(r["delta"] - TARGET_MDE) < 1e-9)
    n_ex = chosen["exchanges_clustered"]
    print()
    if n_ex <= 0:
        print(f"⛔⛔ MDE {TARGET_MDE:.3f} IS UNREACHABLE at any feasible N once "
              "clustering is\n   honoured. The probe must be redesigned, not "
              "rescaled.")
    else:
        print(f"⭐⭐ DECLARED: {n_ex} exchanges per arm at {a.turns} turns "
              f"⇒ MDE {TARGET_MDE:.3f}")
        print(f"   The naïve calculation said {chosen['exchanges_naive']}. "
              f"Clustering makes it {n_ex}\n   — "
              f"{n_ex / chosen['exchanges_naive']:.1f}× more. **Sizing on the "
              f"naïve number would have\n   reproduced last run's failure one "
              f"level down: a declared MDE the run\n   cannot actually reach.**")
        print(f"   Last run used 14 exchanges (MDE 0.0800, effect 0.0723 — below "
              f"resolution).\n   This is {n_ex / 14:.1f}× that inference, per arm.")
    print()
    print("⛔ IF OBSERVED RELIEF LANDS BELOW THIS MDE THE VERDICT IS "
          "'UNDERPOWERED',\n   NEVER 'NO RELIEF'. Locked here, before the run.")
    chosen = dict(chosen, declared_exchanges_per_arm=n_ex)

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "target_mde": TARGET_MDE, "power": POWER, "alpha": ALPHA,
        "turns": a.turns,
        "common_uniform_rows": list(FM.COMMON_UNIFORM_ROWS),
        "common_uniform_expectation": FM.COMMON_UNIFORM_EXPECTATION,
        "stipulated_source": FM.STIPULATED_SOURCE,
        "replication_source_held": FM.REPLICATION_SOURCE_HELD,
        "observed_baseline": {k: v for k, v in base.items()
                              if k != "per_exchange_rates"},
        "design_common_share": {"baseline": share_b, "treatment": share_t},
        "per_exchange_transitions_treatment": per_ex_treat,
        "table": rows, "declared": chosen,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
