"""KI-ATTRIBUTION — is the Q2 collapse KA-COUPLED or GLOBAL-FLAT? $0, no box.

⭐ THE FINDING THIS INTERROGATES. Q2 read "the substrate cannot hold a flat
prior on 3 of 4 uniform rows". Re-analysis of the same file says something
narrower and sharper: `ko`, `ku` and `kä` are ONE distribution (pairwise TV
0.036-0.091), and its only real feature is that **`ki` is halved against the
corpus** (arena 0.084 vs corpus 0.164) while `ka` and `ko` land dead on. The
model reproduces its training marginal everywhere except one force: it will not
ask.

⛔⛔ `kä` "HOLDS FLAT" IS AN UNDERPOWERED NULL, NOT A FINDING. Pooling its two
twins and re-simulating the band at the pooled n flips it:

    kä alone         n=111  d_uniform 0.112  band 0.124  -> fails to reject
    POOLED ko+ku+kä  n=319  d_uniform 0.137  band 0.074  -> REJECTS

A per-row verdict table cannot say this, because each row is separately
underpowered. **The band moved, not the data.**

═══ THE TWO HYPOTHESES ═══════════════════════════════════════════════════════

    H_prompt  (GLOBAL-FLAT)  the provocation's "paint a scene that holds
                             together on its own" suppresses interrogatives.
                             A system prompt is present on EVERY turn, so its
                             effect CANNOT depend on the prior force.
                             ⇒ predicts ki suppressed EQUALLY after every prior.

    H_forced  (KA-COUPLED)   the single forced cell `ki->ka` built a ki/ka
                             association, and ki-emission is conditional on it.
                             ⇒ predicts ki-suppression VARIES with prior force.

⭐⭐ THE LOGIC IS ASYMMETRIC AND THIS TOOL DOES NOT OVERCLAIM IT. Global-flat is
the falsifiable one. Finding ka-coupling **REFUTES global-flat** — no
always-present system prompt can produce a prior-conditional effect — but it does
NOT by itself confirm H_forced, because "assert, then question the assertion" is
an ordinary discourse move that would also be prior-conditional. The verdict
strings say `GLOBAL-FLAT REFUTED`, never `H_forced CONFIRMED`.

═══ WHAT IS AND IS NOT AVAILABLE ON DISK ═════════════════════════════════════

  TEST B  ka-coupling            arm2, 546 transitions   ⚠️ POST-HOC (see below)
  TEST C  cross-exchange         14 independent runs     ✅ failable robustness
  TEST D  held-out replication   arm1, 39 transitions    ⚠️ underpowered BY
                                                            CONSTRUCTION — the
                                                            MDE is computed and
                                                            declared BEFORE the
                                                            number is read
  TEST A  substrate baseline     ⛔ VOID. NO SOURCE EXISTS.

⛔ TEST A IS VOID AND THAT IS A RESULT, NOT AN OMISSION. Attributing the
suppression to the substrate needs run 3 generating freely. Every candidate on
disk fails a stated precondition:
  · `harden/exchange_probe.json`  — DEGENERATE (7 distinct surfaces / 40 turns,
    TTR 0.125, cycle period 1, validity 0.45). Every round-tripping surface reads
    force `ki` because the seed history ends in `ki`. A 7-surface echo of the
    seed is a statement about the loop.
  · `mt_run/arm3_run3_w1_*.json`  — illegal force `"u"`, validity 0.000.
  · `mt_run/temp_floor_depth3.json` — counts only, no surfaces retained.
  · flocal / speak_recon generations — force is fixed by the ENGLISH PROMPT, so
    the model never chose it. Void for a force-PREFERENCE question.

⚠️⚠️ TEST B IS POST-HOC AND IS LABELLED SO EVERYWHERE IT IS PRINTED. The
ka-row contrast (0.138 vs 0.066) was SEEN during the re-analysis that motivated
this tool. It is a discovery, not a confirmation, and no split of these same 546
transitions can launder that. TEST C is what keeps it honest: an effect carried
by one or two of the fourteen exchanges is a fluke wearing a p-value.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.discourse import force_map as FM                        # noqa: E402
from tlon.grammar.parse import parse, render                      # noqa: E402

#: The force under investigation. Not a parameter — the whole tool is about it.
TARGET = "ki"

#: ⛔ Below this many observations in EITHER side of the contrast, the test
#: reports UNDERPOWERED and refuses a verdict. A null from fewer is a statement
#: about the instrument. (Q2 shipped four separately-underpowered rows and one
#: of them read as a finding.)
MIN_PER_SIDE = 30

#: ⭐ TEST C's bar, declared as a FRACTION of exchanges, never a count.
CROSS_EXCHANGE_FLOOR = 10 / 14


class Void(RuntimeError):
    """A precondition failed. The test does not run and does not return a null."""


# ── degeneracy gate ───────────────────────────────────────────────────────────
#: A transcript below this distinct-surface ratio is an echo loop, and its force
#: marginal describes the loop. Matches `falsify.DEGENERACY_TTR_FLOOR` in intent.
MIN_DISTINCT_RATIO = 0.50


def forces_from(transcript: list[str]) -> list[str]:
    """Round-tripping surfaces only — the one-place oracle, enforced here too."""
    out = []
    for s in transcript:
        try:
            sc = parse(s)
        except Exception:                                          # noqa: BLE001
            continue
        if render(sc) == s and sc.force in FM.ORDER:
            out.append(sc.force)
    return out


def assert_not_degenerate(transcript: list[str], label: str) -> None:
    """⛔⛔ THE GATE THAT VOIDED TEST A. Run it on every source, including ours.

    A degenerate transcript still yields a clean-looking force marginal — run 3's
    reads `ki` 100 %, which would have been a spectacular and completely false
    baseline. The distinct-ratio is what exposes it.
    """
    if not transcript:
        raise Void(f"{label}: empty transcript")
    ratio = len(set(transcript)) / len(transcript)
    if ratio < MIN_DISTINCT_RATIO:
        raise Void(
            f"{label}: DEGENERATE — {len(set(transcript))} distinct surfaces in "
            f"{len(transcript)} turns (ratio {ratio:.3f} < {MIN_DISTINCT_RATIO}). "
            "Its force marginal describes the echo loop, not the model. This is "
            "the gate that voided the run-3 baseline; it applies to us too.")


# ── transitions ───────────────────────────────────────────────────────────────
def transitions_from_file(path: pathlib.Path, *, key: str) -> list[tuple]:
    d = json.loads(path.read_text(encoding="utf-8"))
    t = d[key]
    assert_not_degenerate(t, path.name)
    f = forces_from(t)
    if len(f) < len(t):
        # ⭐ NOT silently dropped. A file that loses turns to the oracle has a
        # different effective n than its turn count, and Q2's bands were
        # simulated at row sizes — so the loss must be visible.
        print(f"  ⚠️  {path.name}: {len(t) - len(f)} of {len(t)} turns did not "
              f"round-trip and are excluded")
    return list(zip(f, f[1:]))


# ── the contrast ──────────────────────────────────────────────────────────────
def contrast(trans: list[tuple], *, pivot: str = "ka",
             target: str = TARGET) -> dict:
    """P(response==target | prior==pivot) vs P(... | prior in the OTHER uniform
    rows). ⛔ The forced row is EXCLUDED: `ki->ka` is deterministic by design, so
    including it would let a design zero masquerade as evidence."""
    uniform = [f for f in FM.ORDER if FM.verdict(f) == FM.UNIFORM]
    if pivot not in uniform:
        raise Void(f"pivot {pivot!r} is not a uniform row; the contrast would "
                   "compare a design zero against a measurement")
    others = [f for f in uniform if f != pivot]
    a_hit = sum(1 for p, r in trans if p == pivot and r == target)
    a_n = sum(1 for p, _ in trans if p == pivot)
    b_hit = sum(1 for p, r in trans if p in others and r == target)
    b_n = sum(1 for p, _ in trans if p in others)
    return {"pivot": pivot, "others": others, "target": target,
            "pivot_hit": a_hit, "pivot_n": a_n,
            "other_hit": b_hit, "other_n": b_n,
            "pivot_rate": a_hit / a_n if a_n else float("nan"),
            "other_rate": b_hit / b_n if b_n else float("nan")}


def permutation_p(trans: list[tuple], c: dict, *, trials: int = 20000,
                  seed: int = 11) -> float:
    """⭐ PERMUTATION, NOT A CLOSED FORM. Shuffles the PRIOR labels within the
    uniform rows only, which is exactly the null 'the prior force carries no
    information about whether the response is `ki`' — i.e. GLOBAL-FLAT. No
    distributional assumption, and it holds the marginals fixed by construction.
    """
    uniform = set(c["others"]) | {c["pivot"]}
    sub = [(p, r) for p, r in trans if p in uniform]
    priors = [p for p, _ in sub]
    resps = [r for _, r in sub]
    obs = abs(c["pivot_rate"] - c["other_rate"])
    rng = random.Random(seed)
    hits = 0
    for _ in range(trials):
        rng.shuffle(priors)
        ah = an = bh = bn = 0
        for p, r in zip(priors, resps):
            if p == c["pivot"]:
                an += 1
                ah += r == c["target"]
            else:
                bn += 1
                bh += r == c["target"]
        if an and bn and abs(ah / an - bh / bn) >= obs:
            hits += 1
    return (hits + 1) / (trials + 1)


def mde(n_pivot: int, n_other: int, base: float, *, trials: int = 4000,
        seed: int = 3) -> float:
    """⭐⭐ MINIMUM DETECTABLE EFFECT, COMPUTED BEFORE THE NUMBER IS READ.

    The smallest absolute rate difference this sample size can separate from
    global-flat at 80 % power. **Declared up front so an underpowered null cannot
    be read as evidence of flatness after the fact** — which is precisely how
    `kä` "HOLDS FLAT" got into the Q2 table.
    """
    rng = random.Random(seed)
    for delta in [x / 200 for x in range(1, 101)]:
        det = 0
        for _ in range(trials):
            a = sum(rng.random() < min(1.0, base + delta) for _ in range(n_pivot))
            b = sum(rng.random() < base for _ in range(n_other))
            # crude two-proportion z, sufficient for a power sweep
            pa, pb = a / n_pivot, b / n_other
            pp = (a + b) / (n_pivot + n_other)
            se = (pp * (1 - pp) * (1 / n_pivot + 1 / n_other)) ** 0.5
            if se and abs(pa - pb) / se > 1.96:
                det += 1
        if det / trials >= 0.80:
            return delta
    return float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default="runs/act2/logs/mt_run")
    ap.add_argument("--out", default="runs/act2/logs/mt_run/ki_attribution.json")
    a = ap.parse_args()
    logs = pathlib.Path(a.logs)

    print("KI-ATTRIBUTION — KA-COUPLED vs GLOBAL-FLAT   ($0, re-analysis only)")
    print("=" * 78)
    print("H_prompt  GLOBAL-FLAT : a system prompt is on every turn ⇒ its effect")
    print("                        CANNOT depend on the prior force.")
    print("H_forced  KA-COUPLED  : the forced cell ki->ka built a ki/ka coupling.")
    print("⭐ Refuting global-flat is what this can do. Confirming H_forced is not.")
    print()

    report: dict = {"target": TARGET, "tests": {}}

    # ── TEST A ────────────────────────────────────────────────────────────────
    print("── TEST A · substrate baseline (run 3 generating freely) ──")
    a_void = ("⛔ VOID — no source exists. harden/exchange_probe.json is "
              "DEGENERATE (7 distinct / 40 turns, all force ki, echoing a "
              "ki-final seed); arm3 emitted illegal force 'u' at validity 0.000; "
              "temp_floor kept counts not surfaces; flocal/speak_recon fix the "
              "force via the English prompt so the model never chose it.")
    print("  " + a_void)
    print("  ⇒ H_substrate is NOT under test here and is NOT excluded by any "
          "result below.")
    report["tests"]["A_substrate"] = {"verdict": "VOID", "why": a_void}
    print()

    # ── TEST B ────────────────────────────────────────────────────────────────
    arm2 = sorted(logs.glob("arm2_new_w1_*.json"))
    if not arm2:
        raise SystemExit(f"⛔ no arm2 files under {logs}")
    per_ex, trans = [], []
    for p in arm2:
        t = transitions_from_file(p, key="transcript_interacting")
        per_ex.append((p.name, t))
        trans += t

    print(f"── TEST B · ka-coupling   ⚠️ POST-HOC (discovery sample) ──")
    c = contrast(trans)
    print(f"  transitions {len(trans)} from {len(arm2)} exchanges")
    print(f"  P({TARGET} | prior=ka)              = {c['pivot_hit']}/{c['pivot_n']}"
          f" = {c['pivot_rate']:.4f}")
    print(f"  P({TARGET} | prior in {c['others']}) = "
          f"{c['other_hit']}/{c['other_n']} = {c['other_rate']:.4f}")
    if min(c["pivot_n"], c["other_n"]) < MIN_PER_SIDE:
        print(f"  ⛔ UNDERPOWERED (<{MIN_PER_SIDE} per side) — no verdict")
        report["tests"]["B_ka_coupling"] = {"verdict": "UNDERPOWERED", **c}
    else:
        d = mde(c["pivot_n"], c["other_n"], c["other_rate"])
        p = permutation_p(trans, c)
        print(f"  MDE at 80 % power (declared from n, not from the result): "
              f"{d:.4f}   observed |Δ| = {abs(c['pivot_rate']-c['other_rate']):.4f}")
        print(f"  permutation p (prior labels shuffled within uniform rows) = "
              f"{p:.5f}   [{20000} trials]")
        v = ("GLOBAL-FLAT REFUTED" if p < 0.05 else
             "consistent with GLOBAL-FLAT")
        print(f"  ⇒ {v}")
        if p >= 0.05 and abs(c["pivot_rate"] - c["other_rate"]) < d:
            print("  ⚠️ …but the effect is BELOW the MDE, so this is a failure to "
                  "detect, NOT evidence of flatness. (The kä mistake.)")
        report["tests"]["B_ka_coupling"] = {
            "verdict": v, "post_hoc": True, "permutation_p": p, "mde_80": d, **c}
    print()

    # ── TEST C ────────────────────────────────────────────────────────────────
    print("── TEST C · cross-exchange consistency  ✅ FAILABLE ──")
    print("  An effect carried by one or two of fourteen independent exchanges "
          "is a fluke\n  wearing a p-value. Pre-declared bar: "
          f"≥ {CROSS_EXCHANGE_FLOOR:.0%} of exchanges in the same direction.")
    agree, usable = 0, 0
    for name, t in per_ex:
        try:
            cc = contrast(t)
        except Void:
            continue
        if not (cc["pivot_n"] and cc["other_n"]):
            continue
        usable += 1
        agree += cc["pivot_rate"] > cc["other_rate"]
    share = agree / usable if usable else float("nan")
    print(f"  {agree}/{usable} exchanges show P({TARGET}|ka) > "
          f"P({TARGET}|other)   = {share:.1%}")
    passed = usable and share >= CROSS_EXCHANGE_FLOOR
    print(f"  ⇒ {'✅ CONSISTENT' if passed else '⛔ NOT CONSISTENT — the pooled '
                                                'effect is carried by a minority'}")
    report["tests"]["C_cross_exchange"] = {
        "agree": agree, "usable": usable, "share": share,
        "floor": CROSS_EXCHANGE_FLOOR, "passed": bool(passed)}
    print()

    # ── TEST D ────────────────────────────────────────────────────────────────
    print("── TEST D · held-out replication (arm1, accumulating context) ──")
    arm1 = logs / "arm1_new_accum.json"
    try:
        t1 = transitions_from_file(arm1, key="transcript_interacting")
        c1 = contrast(t1)
        d1 = mde(max(1, c1["pivot_n"]), max(1, c1["other_n"]),
                 c["other_rate"])
        print(f"  transitions {len(t1)}  (held out — NOT part of the 546)")
        print(f"  ⭐ MDE DECLARED BEFORE READING: {d1:.4f} at n=({c1['pivot_n']},"
              f"{c1['other_n']}). The arm2 effect is "
              f"{abs(c['pivot_rate']-c['other_rate']):.4f}.")
        if d1 != d1 or d1 > abs(c["pivot_rate"] - c["other_rate"]):
            print("  ⛔ UNDERPOWERED BY CONSTRUCTION — this arm CANNOT detect an "
                  "effect of the\n     size arm2 shows. Reported as DIRECTIONAL "
                  "ONLY; a null here means nothing.")
            verdict_d = "UNDERPOWERED_BY_CONSTRUCTION"
        else:
            verdict_d = "POWERED"
        print(f"  P({TARGET}|ka) = {c1['pivot_hit']}/{c1['pivot_n']}   "
              f"P({TARGET}|other) = {c1['other_hit']}/{c1['other_n']}   "
              f"direction {'AGREES' if c1['pivot_rate'] > c1['other_rate'] else 'DIFFERS'}")
        report["tests"]["D_heldout"] = {"verdict": verdict_d, "mde_80": d1, **c1}
    except (Void, KeyError, FileNotFoundError) as e:
        print(f"  ⛔ VOID — {e}")
        report["tests"]["D_heldout"] = {"verdict": "VOID", "why": str(e)}
    print()

    # ── TEST E ────────────────────────────────────────────────────────────────
    # ⭐⭐ NOT IN THE ORIGINAL SPEC. It fell out of TEST D and it is a STRONGER
    # refutation of every context-free cause than the ka-row contrast, because
    # arm1 and arm2 differ in EXACTLY ONE THING: the history window. Same
    # weights, same provocation, same temperature, same turns.
    #
    # ⚠️ POST-HOC AND SINGLE-EXCHANGE. arm1 is n=1, so the between-exchange
    # variance is unmeasured in that arm. The bar used here is therefore not a
    # p-value but a RANGE test: is arm1 outside the full observed spread of the
    # fourteen independent arm2 exchanges? A p-value alone would ignore the
    # clustering and overstate it.
    print("── TEST E · window dependence  ⚠️ POST-HOC, SINGLE EXCHANGE ──")
    try:
        import statistics
        per_rate = []
        for _name, t in per_ex:
            u = [(p, r) for p, r in t if p in c["others"] or p == c["pivot"]]
            if u:
                per_rate.append(sum(r == TARGET for _, r in u) / len(u))
        t1 = transitions_from_file(arm1, key="transcript_interacting")
        u1 = [(p, r) for p, r in t1 if p in c["others"] or p == c["pivot"]]
        r1 = sum(r == TARGET for _, r in u1) / len(u1)
        mu, sd = statistics.mean(per_rate), statistics.stdev(per_rate)
        print(f"  arm2 (window=1, {len(per_rate)} exchanges): mean "
              f"{mu:.4f}  sd {sd:.4f}  range [{min(per_rate):.3f}, "
              f"{max(per_rate):.3f}]")
        print(f"  arm1 (accumulating, 1 exchange): "
              f"{sum(r == TARGET for _, r in u1)}/{len(u1)} = {r1:.4f}")
        outside = r1 > max(per_rate) or r1 < min(per_rate)
        print(f"  ⇒ arm1 is {(r1 - mu) / sd:+.1f} SD from the arm2 mean and "
              f"{'OUTSIDE' if outside else 'INSIDE'} the full observed range")
        if outside:
            print("  ⭐⭐ THE PROMPT IS IDENTICAL IN BOTH ARMS. A cause that does "
                  "not vary with\n     context cannot produce this. ⇒ EVERY "
                  "CONTEXT-FREE CAUSE IS REFUTED — which\n     covers H_prompt "
                  "AND the simple form of H_substrate ('the substrate will not\n"
                  "     ask'), since both are global by construction.")
        report["tests"]["E_window"] = {
            "post_hoc": True, "single_exchange": True,
            "arm2_mean": mu, "arm2_sd": sd,
            "arm2_range": [min(per_rate), max(per_rate)],
            "arm1_rate": r1, "outside_range": bool(outside)}
    except (Void, KeyError, FileNotFoundError, statistics.StatisticsError) as e:
        print(f"  ⛔ VOID — {e}")
        report["tests"]["E_window"] = {"verdict": "VOID", "why": str(e)}
    print()

    # ── the standing confound, checked rather than asserted ───────────────────
    print("── CONFOUND CHECK · is `ki` just harder to emit? ──")
    corp = pathlib.Path("runs/act2/corpus_mt/train.jsonl")
    if corp.exists():
        by: dict[str, list[int]] = {f: [] for f in FM.ORDER}
        for line in corp.open(encoding="utf-8"):
            r = json.loads(line)
            if r.get("source") == "multiturn" and r.get("force") in by:
                by[r["force"]].append(len(r["surface"]))
        print("  target-surface length by force, in the corpus the model saw:")
        for f in FM.ORDER:
            v = by[f]
            print(f"    {f:3s} n={len(v):5d}  mean {sum(v)/len(v):5.1f} chars"
                  if v else f"    {f:3s} n=0")
        report["confound_surface_length"] = {
            f: {"n": len(v), "mean_chars": (sum(v) / len(v)) if v else None}
            for f, v in by.items()}
        print("  ⇒ if `ki` targets are not longer/rarer, 'ki is harder to emit' "
              "is not\n     carrying the suppression.")
    else:
        print(f"  ⚠️ {corp} not on disk — confound NOT checked")
    print()

    pathlib.Path(a.out).write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {a.out}")
    print()
    print("⛔ WHAT NO RESULT ABOVE CAN SAY: whether the suppression predates the "
          "force map.\n   That is TEST A, it is VOID on disk, and it is the only "
          "part that needs a box.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
