"""THROUGHPUT GATE — measure, branch, COMMIT. Runs BEFORE any scored arm.

⛔⛔ THIS TOOL EXISTS TO MAKE AN ORDERING UNFORGEABLE, NOT TO TIME A GPU.

The pre-registered fallback changes the MDE (0.040 → 0.060), and therefore
changes **what counts as PARTIAL versus UNDERPOWERED**. Dropping power because
the box is slow is a resource decision; dropping it because you peeked at the
effect is p-hacking. They are different — but only if the branch is provably
taken **before any relief datum exists**. If the throughput check and the relief
scoring can happen in either order, then "we went to the fallback" is
contaminable by "we saw the effect was weak and wanted the softer MDE."

⇒ THE ORDER IS ENFORCED, NOT PROMISED:

    1. this tool runs N timing exchanges and **DISCARDS THEM**
    2. it projects the full design and BRANCHES on the projection alone
    3. it writes `N_COMMITTED.json` and prints its sha256
    4. every scored arm is invoked with `--commitment <sha>` and stamps it
    5. `act2_ki_target_analyse.py` REFUSES any arm whose sha does not match

**An arm generated before the commitment existed cannot carry its hash.** That is
the whole mechanism.

⛔ THE TIMING EXCHANGES ARE DISCARDED, AND THAT IS LOAD-BEARING. If they were
scored, the branch would have been taken with relief data already in hand and the
"before" claim would be false. They are written under `throughput_discard/`,
carry NO commitment sha (they precede it, by construction), and the analyser's
sha check therefore rejects them automatically — the guard and the discard are
the same mechanism rather than two that could drift apart.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

#: ⭐ THE PRE-REGISTERED BRANCH. Both limbs fixed in
#: docs/PREREG_KI_AS_TARGET_2026_08_26.md before the box; neither is chosen here.
PRIMARY = {"exchanges_per_arm": 82, "mde": 0.040,
           "partial_resolvable": True}
FALLBACK = {"exchanges_per_arm": 38, "mde": 0.060,
            "partial_resolvable": False}
PROJECTION_BUDGET_S = 4 * 3600

#: The variance-control arm (adapter_mt re-served). Fixed, not scaled.
VARIANCE_ARM_EXCHANGES = 14

PREREG = "docs/PREREG_KI_AS_TARGET_2026_08_26.md"
PREREG_SHA256 = "9b21976c520f7e2660b95391fefc1a4355398a375399e4fe7175b3c35a37b0be"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter", required=True,
                    help="the arm the timing runs on — use the BASELINE model, "
                         "so the projection reflects real per-exchange cost")
    ap.add_argument("--turns", type=int, default=40)
    ap.add_argument("--timing-exchanges", type=int, default=3)
    ap.add_argument("--discard-dir",
                    default="runs/act2/ki_target/throughput_discard")
    ap.add_argument("--out", default="runs/act2/ki_target/N_COMMITTED.json")
    a = ap.parse_args()

    print("THROUGHPUT GATE — measure, branch, COMMIT (before any scored arm)")
    print("=" * 78)

    # ── the prereg must be the one that was hashed ────────────────────────────
    p = pathlib.Path(PREREG)
    if not p.exists():
        raise SystemExit(f"⛔ {PREREG} missing — the pre-registration IS the "
                         "experiment; without it nothing below is meaningful")
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != PREREG_SHA256:
        # ⛔⛔ Not a warning. A prereg edited after locking is an amendment, and
        # an amendment that nobody declared is just a changed hypothesis.
        raise SystemExit(
            f"⛔⛔ PREREG HASH MISMATCH\n   expected {PREREG_SHA256}\n   got      "
            f"{got}\nThe pre-registration has changed since it was locked. Either "
            "restore it or\nrecord an explicit AMENDMENT and update the constant "
            "in this file — but do\nNOT run a probe against a hypothesis that "
            "moved after the fact.")
    print(f"  ✅ prereg hash matches ({PREREG_SHA256[:16]}…)")

    # ── time, and DISCARD ─────────────────────────────────────────────────────
    dd = pathlib.Path(a.discard_dir)
    dd.mkdir(parents=True, exist_ok=True)
    print(f"\n  timing {a.timing_exchanges} exchanges at {a.turns} turns "
          f"→ {dd}  ⛔ DISCARDED, NEVER SCORED")
    per = []
    for i in range(a.timing_exchanges):
        t0 = time.time()
        # ⛔ NO `tail -N`. A truncated traceback decapitated the diagnosis last
        # run; the whole stream is captured and the whole stream is printed on
        # failure.
        r = subprocess.run(
            [sys.executable, "-X", "utf8", "tools/act2_exchange_probe.py",
             "--model", a.model, "--adapter", a.adapter,
             "--turns", str(a.turns), "--history-window", "1",
             "--out", str(dd / f"timing_{i + 1}.json")],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout)
            print(r.stderr, file=sys.stderr)
            raise SystemExit(f"⛔ timing exchange {i + 1} failed "
                             f"(rc={r.returncode}) — full output above")
        dt = time.time() - t0
        per.append(dt)
        print(f"    exchange {i + 1}: {dt:7.1f}s")

    # ⭐ THE SLOWEST, NOT THE MEAN. The planner-correction lesson: a factor that
    # varies must be used at its WORST observed value against a hard wall, never
    # averaged into a constant that hides the tail.
    worst = max(per)
    mean = sum(per) / len(per)
    print(f"\n  mean {mean:.1f}s   worst {worst:.1f}s   "
          f"⭐ projecting on the WORST")

    rows = []
    for br, name in ((PRIMARY, "PRIMARY"), (FALLBACK, "FALLBACK")):
        n_ex = 2 * br["exchanges_per_arm"] + VARIANCE_ARM_EXCHANGES
        rows.append({**br, "branch": name, "total_exchanges": n_ex,
                     "projected_s": n_ex * worst})
        print(f"  {name:9s} {br['exchanges_per_arm']:3d}/arm ×2 + "
              f"{VARIANCE_ARM_EXCHANGES} control = {n_ex:3d} exchanges "
              f"→ {n_ex * worst / 3600:5.2f} h   (MDE {br['mde']:.3f})")

    chosen = rows[0] if rows[0]["projected_s"] <= PROJECTION_BUDGET_S else rows[1]
    print(f"\n  budget {PROJECTION_BUDGET_S / 3600:.1f} h  ⇒ "
          f"⭐⭐ BRANCH = {chosen['branch']}  "
          f"({chosen['exchanges_per_arm']}/arm, MDE {chosen['mde']:.3f})")
    if not chosen["partial_resolvable"]:
        print("  ⚠️ ON THE FALLBACK, **PARTIAL RELIEF IS UNDERPOWERED BY "
              "DECLARATION** — only\n     FULL relief is resolvable. Declared in "
              "the prereg, not decided here.")

    commit = {
        "prereg": PREREG, "prereg_sha256": PREREG_SHA256,
        "branch": chosen["branch"],
        "exchanges_per_arm": chosen["exchanges_per_arm"],
        "mde": chosen["mde"],
        "partial_resolvable": chosen["partial_resolvable"],
        "variance_arm_exchanges": VARIANCE_ARM_EXCHANGES,
        "turns": a.turns,
        "timing_seconds": per, "worst_s": worst, "mean_s": mean,
        "projection_budget_s": PROJECTION_BUDGET_S,
        "projected_s": chosen["projected_s"],
        "considered": rows,
        "NOTE": ("Committed BEFORE any scored arm. Timing exchanges were "
                 "DISCARDED and carry no commitment sha, so the analyser "
                 "rejects them by the same mechanism that enforces the order."),
    }
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # ⛔ sort_keys + fixed separators: the sha must not depend on dict ordering,
    # or "the same commitment" hashes differently on a re-read.
    body = json.dumps(commit, indent=2, ensure_ascii=False, sort_keys=True)
    out.write_text(body, encoding="utf-8", newline="")
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"\n  wrote {out}")
    print(f"⭐⭐ COMMITMENT SHA256 = {sha}")
    print(f"   Pass to every scored arm:  --commitment {sha}")
    print("\n⛔ NOTHING SCORED HAS BEEN GENERATED. The branch is now fixed and "
          "the relief\n   data does not yet exist. That ordering is the point.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
