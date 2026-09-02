"""THE DRIFT ESTIMAND — W2(LIVE) − W2(YOKED), against the frozen cold table.

Spec: docs/SPEC_TWO_SPEAKER_DRIFT_2026_08_30.md
Red-proof: tests/test_drift_estimand.py (written BEFORE this ran on real data)

⭐ THE QUESTION. Two Tlön speakers talk. Do they move toward each other because
the partner RESPONDS, or merely because the partner is THERE? The yoked null
answers it: each speaker faces a RECORDING of the other's live turns, so the
input is held and only mutuality is removed.

⭐ THE SIGN, stated once and asserted in the tests:

        delta = W2(LIVE) − W2(YOKED)
        delta < 0  ⇒  closer when the partner can respond  ⇒  COUPLING
        delta > 0  ⇒  farther                              ⇒  divergence

⛔⛔ THE RULER IS FROZEN. `axis_scale` comes from cold_table_ka.json (content sha
84c2a1b5…) and is never recomputed here. A scale derived from the drift
transcripts would move with the measurement.

⛔⛔ NEVER MEASURE THE RECORDING. A yoked arm holds 40 turns the live speaker
generated and 40 replayed from the partner's LIVE transcript. Pooling them puts
the partner's live behaviour inside the null, pulling YOKED toward LIVE and
shrinking |delta| toward zero — which reads as "no coupling" and therefore would
never look like a bug.

⛔ THE UNIT OF INDEPENDENCE IS THE ADAPTER, NOT THE REPLICATE. Seven replicates
of one pair re-roll sampling noise at fixed weights; they do not re-roll the
speakers. Intervals come from a cluster bootstrap over adapters.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

CONVERGENCE = "convergence"
DIVERGENCE = "divergence"

#: A conversation with too few parseable scenes is a noisy point, not a speaker.
#: Same threshold the cold table used, so the clouds are comparable.
MIN_SCENES = 8


def verdict_of(delta: float) -> str:
    return CONVERGENCE if delta < 0 else DIVERGENCE


def own_surfaces(log, speaker: str):
    """Turns THIS speaker actually generated: valid, not injected, not replayed.

    ⛔ Exact label match. `A_rec` is a recording, not speaker `A`; a prefix or
    substring test would silently pull the replayed partner into the arm.
    """
    return [e["surface"] for e in log
            if e.get("speaker") == speaker and e.get("valid")
            and not e.get("injected") and e.get("surface") is not None]


def point(surfaces, panel):
    """One conversation -> one panel vector, or None if too thin to count."""
    from act2_observable_screen import OBSERVABLES, scenes_of
    sc = scenes_of(surfaces)
    if len(sc) < MIN_SCENES:
        return None
    v = [OBSERVABLES[o](sc) for o in panel]
    return None if any(x is None for x in v) else v


def _w2(a, b, scale):
    from act2_distance import w2
    return w2(a, b, scale)


def pair_delta(live_a, live_b, yok_a, yok_b, scale):
    """The estimand for ONE pair, with both W2s decomposed."""
    L = _w2(live_a, live_b, scale)
    Y = _w2(yok_a, yok_b, scale)
    return {"w2_live": L["w2"], "w2_yoked": Y["w2"],
            "delta": L["w2"] - Y["w2"],
            "live_mean_term": L["mean_term"], "live_spread_term": L["spread_term"],
            "yoked_mean_term": Y["mean_term"], "yoked_spread_term": Y["spread_term"],
            "delta_mean_term": L["mean_term"] - Y["mean_term"],
            "delta_spread_term": L["spread_term"] - Y["spread_term"]}


def pairing_gain(a, b):
    """⭐⭐ THE CHANNEL W2 CANNOT SEE: conversation-specific convention.

    `W2(A,B)` compares MARGINAL distributions. Two speakers can agree *within
    each shared conversation* — each pair of transcripts landing on its own
    shared value — while neither speaker's marginal moves at all. W2 is blind to
    that by construction, and it is exactly the channel a self-accumulation
    architecture makes available: the speakers never hold each other's words, so
    whatever they share has to be re-established inside each conversation.

    ⛔⛔ AND IT IS WHY THE SELF-PAIR ARM IS A MARGINAL-NOISE FLOOR, NOT A PROOF
    THAT COUPLING IS IMPOSSIBLE. For identical weights the two marginals coincide
    by exchangeability, so the self-pair could NEVER have shown coupling under
    W2 — no matter how strongly the two trajectories actually converged.

        gain = mean_{i≠j} |A_i − B_j|  −  mean_i |A_i − B_i|

    POSITIVE = partners from the SAME conversation are more alike than partners
    drawn from different ones. A shared per-conversation offset cancels in the
    within term and survives in the across term, which is what makes it fire.

    ⭐ It is deliberately blind to a COMMON SHIFT (both speakers moving the same
    way leaves every difference unchanged) — that is a separate channel, and
    conflating the two is what `test_a_common_shift_does_NOT_fire` pins down.
    """
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    n = len(a)
    if n < 3 or len(b) != n:
        return None
    within = np.mean(np.abs(a - b))
    across = np.mean([abs(a[i] - b[j])
                      for i in range(n) for j in range(n) if i != j])
    return float(across - within)


def cluster_bootstrap(deltas, adapters, *, n_boot=5000, seed=20260831):
    """Resample ADAPTERS, not pairs — the pairs share speakers.

    Each pair (x, y) enters a resample with multiplicity count[x]*count[y], the
    standard dyadic cluster bootstrap. Resampling pairs instead would treat
    twelve overlapping dyads drawn from seven adapters as twelve independent
    observations and understate the interval.
    """
    deltas = np.asarray(deltas, dtype=float)
    names = sorted({n for ab in adapters for n in ab})
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n_boot):
        draw = rng.choice(len(names), size=len(names), replace=True)
        cnt = {names[i]: int((draw == i).sum()) for i in range(len(names))}
        w = np.array([cnt[x] * cnt[y] for x, y in adapters], dtype=float)
        if w.sum() > 0:
            means.append(float((w * deltas).sum() / w.sum()))
    means = np.asarray(means)
    return {"mean": float(deltas.mean()),
            "ci": (float(np.percentile(means, 2.5)),
                   float(np.percentile(means, 97.5))),
            "n_boot": int(len(means)), "n_pairs": int(len(deltas)),
            "n_adapters": len(names)}


#: ⛔⛔ THE ARM MUST BE NAMED IN THE DATA, NOT IN A NOTE BESIDE IT.
#: The positive control writes a SHARED-memory arm. Storing it under the key
#: `live` — with a comment saying "this run's live arm is actually shared" —
#: is the caveat-in-prose failure that this project keeps paying for: the note
#: gets separated from the number and a later reader pools two different
#: experiments. The arm is a KEY, and the file states which arm it holds.
ARM_LIVE = "live"
ARM_SHARED = "shared"
ARMS = (ARM_LIVE, ARM_SHARED)


def assert_arm(doc: dict, arm: str) -> None:
    """⛔⛔ REFUSE TO READ ONE ARM AS ANOTHER.

    A transcript records `arm_mode`. Loading a shared-memory transcript as
    `live` would silently pool the positive control with the drift run — two
    different memory models under one estimand — and the resulting number would
    look exactly like a normal result.

    ⛔ Files written before `arm_mode` existed carry no key; they are LIVE by
    construction (SHARED did not exist when they were made), so the default is
    explicit rather than permissive.
    """
    if arm not in ARMS:
        raise ValueError("unknown arm %r; valid arms are %s"
                         % (arm, ", ".join(ARMS)))
    got = doc.get("arm_mode", ARM_LIVE)
    if got != arm:
        raise ValueError(
            "this transcript is the %r arm and was asked for as %r — these are "
            "different memory models and must never be pooled under one "
            "estimand" % (got, arm))


def _adapter(path):
    return re.sub(r".*[/\\]", "", str(path).rstrip("/\\"))


def load_pairs(directory, panel, *, self_pair, arm=ARM_LIVE):
    """-> {(a, b): {'live_a': arr, 'live_b': arr, 'yoked_a': arr, 'yoked_b': arr}}

    Each replicate contributes ONE point per speaker per arm, so a pair's cloud
    has as many points as it has replicates.
    """
    acc, skipped = {}, 0
    for f in sorted(pathlib.Path(directory).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if bool(d.get("self_pair")) != self_pair:
            continue
        assert_arm(d, arm)
        key = (_adapter(d["adapter_a"]), _adapter(d["adapter_b"]))
        c = d["conditions"]
        pts = {"live_a": point(own_surfaces(c[arm]["log"], "A"), panel),
               "live_b": point(own_surfaces(c[arm]["log"], "B"), panel),
               "yoked_a": point(own_surfaces(c["yoked_a"]["log"], "A"), panel),
               "yoked_b": point(own_surfaces(c["yoked_b"]["log"], "B"), panel)}
        if any(v is None for v in pts.values()):
            skipped += 1
            continue
        slot = acc.setdefault(key, {k: [] for k in pts})
        for k, v in pts.items():
            slot[k].append(v)
    out = {k: {n: np.asarray(v, dtype=float) for n, v in s.items()}
           for k, s in acc.items()}
    return out, skipped


def analyse(directory, panel, scale, *, self_pair):
    pairs, skipped = load_pairs(directory, panel, self_pair=self_pair)
    rows = []
    for (x, y), c in sorted(pairs.items()):
        d = pair_delta(c["live_a"], c["live_b"], c["yoked_a"], c["yoked_b"],
                       scale)
        rows.append({"pair": "%s|%s" % (x, y), "a": x, "b": y,
                     "n_reps": int(len(c["live_a"])), **d})
    return rows, skipped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cold", default="runs/act2/cold_table_ka.json")
    ap.add_argument("--logs", default="runs/act2/drift/logs")
    ap.add_argument("--control", default="runs/act2/drift/control")
    ap.add_argument("--out", default="runs/act2/drift/drift_results.json")
    ap.add_argument("--n-boot", type=int, default=5000)
    a = ap.parse_args()

    cold = json.loads(pathlib.Path(a.cold).read_text(encoding="utf-8"))
    if not cold.get("frozen"):
        raise SystemExit("⛔⛔ the cold table is not frozen; it cannot be a "
                         "baseline")
    panel = tuple(cold["panel"])
    scale = np.asarray(cold["axis_scale"], dtype=float)

    print("DRIFT — W2(LIVE) − W2(YOKED)")
    print("=" * 78)
    print("  panel        %s" % (panel,))
    print("  frozen scale %s   (cold table sha %s…)"
          % (np.array2string(scale, precision=5), cold["sha256"][:8]))
    print("  sign         delta < 0 = closer when the partner responds = COUPLING")

    # ── ⛔⛔ THE CONTROL IS READ FIRST. It is a precondition, not a footnote. ──
    ctrl, ctrl_skip = analyse(a.control, panel, scale, self_pair=True)
    # ⛔ CORRECTED 2026-08-31: an earlier version of this label claimed identical
    # speakers are incapable of converging. They are not — they never hold each
    # other's words, so they are two individuated trajectories. The null holds
    # because identical weights make the two MARGINALS coincide, and W2 reads
    # marginals; trajectory divergence is invisible to it.
    print("\n── SELF-PAIR CONTROL · identical weights ⇒ marginals coincide ──")
    print("  %-18s %5s %8s %9s %9s" % ("pair", "reps", "W2 live", "W2 yoked",
                                       "delta"))
    for r in ctrl:
        print("  %-18s %5d %8.4f %9.4f %9.4f"
              % (r["pair"], r["n_reps"], r["w2_live"], r["w2_yoked"],
                 r["delta"]))
    cb = cluster_bootstrap([r["delta"] for r in ctrl],
                           [(r["a"], r["b"]) for r in ctrl],
                           n_boot=a.n_boot)
    print("  mean delta %+.4f   95%% CI [%+.4f, %+.4f]  (n=%d)"
          % (cb["mean"], cb["ci"][0], cb["ci"][1], cb["n_pairs"]))
    control_clean = cb["ci"][0] <= 0 <= cb["ci"][1]
    print("  %s" % ("✅ control consistent with zero — a coupling claim is "
                    "licensed" if control_clean else
                    "⛔⛔ CONTROL IS NOT ZERO — the pipeline manufactures drift; "
                    "NO coupling claim is licensed"))

    # ── the real pairs ──────────────────────────────────────────────────────
    rows, skip = analyse(a.logs, panel, scale, self_pair=False)
    print("\n── REAL PAIRS ──")
    print("  %-18s %5s %8s %9s %9s %10s" % ("pair", "reps", "W2 live",
                                            "W2 yoked", "delta", "verdict"))
    for r in sorted(rows, key=lambda z: z["delta"]):
        print("  %-18s %5d %8.4f %9.4f %9.4f %10s"
              % (r["pair"], r["n_reps"], r["w2_live"], r["w2_yoked"],
                 r["delta"], verdict_of(r["delta"])))

    bs = cluster_bootstrap([r["delta"] for r in rows],
                           [(r["a"], r["b"]) for r in rows], n_boot=a.n_boot)
    print("\n  mean delta %+.4f   95%% CI [%+.4f, %+.4f]"
          % (bs["mean"], bs["ci"][0], bs["ci"][1]))
    print("  clustered on ADAPTER (%d adapters, %d pairs, %d boots)"
          % (bs["n_adapters"], bs["n_pairs"], bs["n_boot"]))
    n_conv = sum(1 for r in rows if r["delta"] < 0)
    print("  pairs converging: %d of %d" % (n_conv, len(rows)))
    dm = float(np.mean([r["delta_mean_term"] for r in rows]))
    ds = float(np.mean([r["delta_spread_term"] for r in rows]))
    print("  decomposition of the mean shift: location %+.4f · spread %+.4f"
          % (dm, ds))
    if skip or ctrl_skip:
        print("  ⚠ skipped thin transcripts: %d real, %d control"
              % (skip, ctrl_skip))

    excl = bs["ci"][1] < 0 or bs["ci"][0] > 0
    print("\n" + "=" * 78)
    if not control_clean:
        print("  ⛔⛔ NO CLAIM. The self-pair control did not read zero.")
    elif excl and bs["ci"][1] < 0:
        print("  ⭐ COUPLING: speakers are closer when the partner can respond,")
        print("     and the interval excludes zero with the adapter as the unit.")
    elif excl:
        print("  ⭐ DIVERGENCE: speakers are FARTHER when the partner responds.")
    else:
        print("  ⚪ NO DETECTED EFFECT. ⛔ This is not evidence of no coupling")
        print("     unless the interval also excludes an effect worth having —")
        print("     read the CI width against the cold-table distances before")
        print("     calling it a null.")

    out = {"panel": list(panel), "axis_scale": scale.tolist(),
           "cold_sha256": cold["sha256"],
           "sign_convention": "delta = W2(LIVE) - W2(YOKED); negative = coupling",
           "unit_of_independence": "adapter",
           "control": {"rows": ctrl, "bootstrap": cb, "clean": control_clean},
           "real": {"rows": rows, "bootstrap": bs},
           "skipped": {"real": skip, "control": ctrl_skip}}
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                   encoding="utf-8", newline="")
    print("  wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
