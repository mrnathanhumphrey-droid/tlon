"""STAGE 1 — is the contamination ranking STABLE, or does it move when the
builds move? $0, no box, pure re-analysis of transcripts already on disk.

Spec: docs/SPEC_TWO_SPEAKER_DRIFT_2026_08_30.md §2

⛔⛔ THE INSTRUMENT BUILT TO ESCAPE BUILD-VARIANCE HAD BUILD-VARIANCE. At k=4 the
ranking gave root TTR 0.07 and force:ki 0.65 — a 9.8x gap. At k=7: 0.13 and 0.28,
a 2.2x gap. The pre-declared prediction passed BY ITS LETTER and the magnitude
that made it compelling did not survive three more builds.

⇒ Recomputing a POINT ESTIMATE on 7 builds does not escape that. It relocates it.
A k=7 point estimate is the same KIND of object that just failed at k=4. So this
asks a different question: **is the ranking stable under RESAMPLING THE BUILDS?**

    jackknife   leave-one-build-out, 7 times -> the RANGE of each rank
    bootstrap   resample builds with replacement -> a CI on each contamination

⭐ PRE-DECLARED ADMISSION RULE (fixed in the spec before this ran):
    an observable may define a distance axis iff
        jackknife rank range <= MAX_RANK_RANGE   AND
        bootstrap CI upper bound < MAX_CI_UPPER
    Rank alone is what passed last time. Both, or it does not enter.

⛔⛔ AND THE HALT IS REAL: 0 qualifying observables means STOP — there is no
distance to define, the drift experiment is not yet buildable, and that is a
FINDING, not a failure. It does not mean "take the top 3 anyway."
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from act2_observable_screen import OBSERVABLES, scenes_of              # noqa: E402

#: ⛔ SAME-CODE, SAME-MAP (derived) ONLY. `adapter_mt` predates the 08-27
#: refactor and `adapter_treat` is the STIPULATED map — neither may be pooled
#: into a between-build sd that is supposed to describe one recipe.
BUILDS = [
    ("s20620", "runs/act2/ki_target/logs", "bfresh_*.json"),
    ("s20621", "runs/act2/recipe_var/logs", "s20621_*.json"),
    ("s20622", "runs/act2/recipe_var/logs", "s20622_*.json"),
    ("s20623", "runs/act2/recipe_var/logs", "s20623_*.json"),
    ("t30001", "runs/act2/var_decomp/logs", "t30001_w1_*.json"),
    ("t30002", "runs/act2/var_decomp/logs", "t30002_w1_*.json"),
    ("t30003", "runs/act2/var_decomp/logs", "t30003_w1_*.json"),
]

MAX_RANK_RANGE = 2          # jackknife: rank may move at most this many places
MAX_CI_UPPER = 0.50         # bootstrap: 97.5th pct of contamination
N_BOOT = 2000
BOOT_SEED = 20260830        # ⭐ fixed and recorded: the analysis is reproducible
MIN_DISTINCT_BUILDS = 3     # a resample below this cannot estimate a spread


def load_builds():
    out = {}
    for name, d, pat in BUILDS:
        ex = []
        for f in sorted(pathlib.Path(d).glob(pat)):
            data = json.loads(f.read_text(encoding="utf-8"))
            scs = scenes_of(data.get("transcript_interacting") or [])
            if len(scs) < 8:
                continue
            h = len(scs) // 2
            ex.append({"all": scs, "first": scs[:h], "second": scs[h:]})
        if ex:
            out[name] = ex
    return out


def contamination(per_build, names, fn):
    """between-build sd / mean within-conversation movement, over `names`.

    ⭐ BOTH terms are recomputed from the same build set. Holding the denominator
    fixed while resampling the numerator would make the CI describe a quantity
    that is never actually computed.
    """
    means, moves = [], []
    for n in names:
        vals = [v for e in per_build[n] if (v := fn(e["all"])) is not None]
        if len(vals) < 2:
            continue
        means.append(sum(vals) / len(vals))
        for e in per_build[n]:
            a, b = fn(e["first"]), fn(e["second"])
            if a is not None and b is not None:
                moves.append(abs(b - a))
    if len(means) < 2 or not moves:
        return None
    mv = sum(moves) / len(moves)
    if not mv:
        return float("inf")
    return statistics.stdev(means) / mv


def admit(rank_range, ci_hi) -> bool:
    """⭐ THE GATE, extracted so a test can prove it REFUSES.

    A gate that cannot return a negative has not been passed, it has been
    consulted. `ci_hi != ci_hi` catches NaN (an empty bootstrap), which must
    never read as admissible.
    """
    return bool(rank_range <= MAX_RANK_RANGE
                and ci_hi == ci_hi and ci_hi < MAX_CI_UPPER)


def verdict_of(admitted) -> str:
    if not admitted:
        return "HALT"
    return "NARROW" if len(admitted) < 3 else "PANEL"


def rank_of(per_build, names):
    """observable -> 1-based rank by contamination (lower is better)."""
    rows = []
    for o, fn in OBSERVABLES.items():
        c = contamination(per_build, names, fn)
        if c is not None:
            rows.append((o, c))
    rows.sort(key=lambda r: r[1])
    return {o: i for i, (o, _) in enumerate(rows, 1)}, dict(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/act2/ranking_stability.json")
    a = ap.parse_args()

    per_build = load_builds()
    print("STAGE 1 — IS THE CONTAMINATION RANKING STABLE UNDER RESAMPLING?")
    print("=" * 78)
    for n, ex in per_build.items():
        print("  %-8s %3d exchanges" % (n, len(ex)))
    names = list(per_build)
    if len(names) < 4:
        print("\n  ⛔ fewer than 4 builds — a jackknife over these is not an "
              "estimate.")
        return 1
    print("  %d builds · admission: jackknife rank range <= %d AND bootstrap "
          "CI upper < %.2f" % (len(names), MAX_RANK_RANGE, MAX_CI_UPPER))
    print("  bootstrap B=%d seed=%d" % (N_BOOT, BOOT_SEED))

    full_rank, full_c = rank_of(per_build, names)

    # ── jackknife: leave one BUILD out ───────────────────────────────────────
    jack = {o: [] for o in full_rank}
    jack_c = {o: [] for o in full_rank}
    for drop in names:
        keep = [n for n in names if n != drop]
        r, c = rank_of(per_build, keep)
        for o in full_rank:
            if o in r:
                jack[o].append(r[o])
                jack_c[o].append(c[o])

    # ── bootstrap over BUILDS ────────────────────────────────────────────────
    rng = random.Random(BOOT_SEED)
    boot = {o: [] for o in full_rank}
    thin = 0
    for _ in range(N_BOOT):
        samp = [rng.choice(names) for _ in names]
        if len(set(samp)) < MIN_DISTINCT_BUILDS:
            thin += 1
            continue
        for o, fn in OBSERVABLES.items():
            if o not in boot:
                continue
            c = contamination(per_build, samp, fn)
            if c is not None and c != float("inf"):
                boot[o].append(c)

    def pct(v, p):
        if not v:
            return float("nan")
        s = sorted(v)
        i = min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))
        return s[i]

    print("\n  %-18s %8s %10s %12s %11s %s" % (
        "observable", "k=7", "jack rank", "jack contam", "boot 95% CI", ""))
    print("  " + "-" * 74)
    rows = []
    for o in sorted(full_rank, key=lambda x: full_rank[x]):
        rr = (max(jack[o]) - min(jack[o])) if jack[o] else 99
        lo, hi = pct(boot[o], 0.025), pct(boot[o], 0.975)
        ok_rank = rr <= MAX_RANK_RANGE
        ok_ci = hi == hi and hi < MAX_CI_UPPER
        admitted = admit(rr, hi)
        flag = "  ⭐ADMIT" if admitted else ("  ⛔rank" if not ok_rank else
                                            "  ⛔CI")
        cs = "%.2f" % full_c[o] if full_c[o] != float("inf") else "inf"
        print("  %-18s %8s %4d-%-5d %5.2f-%-6.2f %5.2f-%-5.2f%s" % (
            o, cs, min(jack[o]), max(jack[o]),
            min(jack_c[o]), max(jack_c[o]), lo, hi, flag))
        rows.append({"observable": o, "contamination_k7": full_c[o],
                     "jack_rank_min": min(jack[o]), "jack_rank_max": max(jack[o]),
                     "jack_rank_range": rr,
                     "jack_contam_min": min(jack_c[o]),
                     "jack_contam_max": max(jack_c[o]),
                     "boot_ci_lo": lo, "boot_ci_hi": hi,
                     "rank_stable": bool(ok_rank), "ci_ok": bool(ok_ci),
                     "admitted": bool(admitted)})

    if thin:
        print("\n  ⚠️ %d/%d bootstrap resamples had < %d distinct builds and were "
              "discarded\n     (a spread over 1-2 builds is not a spread)."
              % (thin, N_BOOT, MIN_DISTINCT_BUILDS))

    admitted = [r["observable"] for r in rows if r["admitted"]]
    verdict = verdict_of(admitted)
    print("\n" + "=" * 78)
    if verdict == "HALT":
        print("  ⛔⛔ HALT — NO OBSERVABLE QUALIFIES.")
        print("     There is no distance to define, so the drift experiment is "
              "not yet\n     buildable. Pre-declared: this is a FINDING, not a "
              "failure, and it does\n     NOT license taking the top 3 anyway. "
              "The honest next move is MORE\n     BUILDS, not a metric built on "
              "an unstable ranking.")
    elif verdict == "NARROW":
        print("  ⚠️ NARROW PANEL — %d observable(s) qualify: %s" % (
            len(admitted), admitted))
        print("     Proceed, and record that the distance rests on a narrow "
              "basis.")
    else:
        print("  ⭐ PANEL ADMITTED (%d): %s" % (len(admitted), admitted))
        print("     These, and only these, may become distance axes in Stage 2.")

    # ⭐ The comparison that motivated this whole stage, stated explicitly.
    print("\n  ── did the k=4 story survive? ──")
    for o in ("root TTR", "force:ki"):
        if o in full_c:
            r = next(x for x in rows if x["observable"] == o)
            print("  %-10s k=7 %.2f · jackknife rank %d-%d · admitted %s"
                  % (o, full_c[o], r["jack_rank_min"], r["jack_rank_max"],
                     r["admitted"]))

    out = {"builds": {n: len(e) for n, e in per_build.items()},
           "rule": {"max_rank_range": MAX_RANK_RANGE,
                    "max_ci_upper": MAX_CI_UPPER, "n_boot": N_BOOT,
                    "boot_seed": BOOT_SEED, "thin_resamples": thin},
           "rows": rows, "admitted": admitted, "verdict": verdict}
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                   encoding="utf-8", newline="")
    print("\nwrote %s" % a.out)
    print("\n⛔ Stage 1 defines no distance and produces no drift number. It only "
          "says which\n   axes are stable enough to build one from.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
