"""THE §8.2 SLOT ANALYSIS — WRITTEN BEFORE RUN 4's NUMBERS EXIST. $0, offline.

⛔⛔ THE ANALYSIS CODE IS PART OF THE PRE-REGISTRATION, NOT A THING WRITTEN
AFTERWARDS TO DESCRIBE WHAT HAPPENED. A comparison authored after seeing the
result is shaped by the result even when nobody intends it to be — the choice of
which slots to pool, whether to use counts or rates, where to put the cutoff, all
become free parameters once the answer is visible. So this file is committed with
the instance still training and the ledger still empty.

Implements `docs/PREREG_ASPECT_ROOT_MECHANISM_2026_08_25.md` exactly:

  1. `k` = pooled fractional error reduction over the floored NON-aspect slots
     (modal, tense, quant, degree). `aspect_root` is HELD OUT of the fit, so its
     prediction is out-of-sample.
  2. PREDICTED aspect_root errors = baseline × (1 − k).
  3. Reading, pre-declared:
       ≈ predicted   ⇒ slot-rarity sufficient; BOTH hypotheses STAY OPEN
       ≪ predicted   ⇒ something aspect-specific; evidence for H-COLLIDE
       ≫ predicted   ⇒ aspect resisted the fix; evidence for H-REDUP
  4. ⛔ And it must be able to say UNDERPOWERED, because the counts are small
     (Poisson sd 4.0 on 16, 3.3 on 11; quant/tense/degree carry 5/3/2 and can
     show nothing). A verdict function with no underpowered branch would have to
     call every result informative.

    python tools/act2_slot_analysis.py --before runs/act2/harden/ledger_harden.jsonl \\
        --after runs/act2/tlon_run4/ledger_tlon.jsonl
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

#: The four floored slots the fit uses. ⛔ `aspect_root` is deliberately ABSENT.
FIT_SLOTS = ("modal", "tense", "quant", "degree")
HELD_OUT = "aspect_root"

#: Pre-declared. "Within noise" is |observed − predicted| under this many pooled
#: Poisson sd. Fixed before the data; not tuned to make a result come out.
NOISE_SD = 2.0


def load(path, *, want_n: int | None = None) -> dict:
    rows = [json.loads(x) for x in
            pathlib.Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
    runs = [r for r in rows if r.get("event") == "f_local"
            and r.get("results", {}).get("render", {}).get("failures") is not None]
    if want_n is not None:
        runs = [r for r in runs
                if r["results"]["render"].get("n") == want_n] or runs
    if not runs:
        raise SystemExit(f"⛔ no usable f_local row in {path}")
    return runs[-1]


def slots(run) -> tuple[collections.Counter, collections.Counter, collections.Counter]:
    """(errors by slot, errors by (source→slot), refusal-reason buckets)."""
    by_slot, by_src, reasons = collections.Counter(), collections.Counter(), collections.Counter()
    for f in run["results"]["render"]["failures"]:
        rs = f.get("reason", "")
        # ⛔ `aspect_reps` IS AN INTEGER, NOT A FORM, so it never produces a
        # class_error row. A mechanism test that only reads class_errors is a
        # test shaped by what its miner happens to walk. Counted here separately.
        if "aspect_reps" in rs:
            reasons["aspect_reps"] += 1
        elif "not in lexicon class" in rs:
            reasons["class"] += 1
        else:
            reasons[rs[:44]] += 1
        for e in f.get("class_errors", []):
            by_slot[e["used_as"]] += 1
            if e["used_as"] == HELD_OUT:
                by_src[e["actual"]] += 1
    return by_slot, by_src, reasons


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default="runs/act2/harden/ledger_harden.jsonl")
    ap.add_argument("--after", required=True)
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--out", default="runs/act2/slot_analysis.json")
    a = ap.parse_args()

    b, af = load(a.before, want_n=a.n), load(a.after, want_n=a.n)
    bs, bsrc, brs = slots(b)
    as_, asrc, ars = slots(af)
    b_rate = b["results"]["render"]["rate"]
    a_rate = af["results"]["render"]["rate"]

    print(f"§8.2 SLOT ANALYSIS · n={a.n} · battery "
          f"{b.get('battery')} → {af.get('battery')}")
    if b.get("battery") != af.get("battery"):
        print("  ⛔⛔ DIFFERENT BATTERIES — these numbers are NOT comparable.")
    print(f"  render {b_rate:.1%} → {a_rate:.1%}   "
          f"({sum(bs.values())} → {sum(as_.values())} class errors)\n")

    print(f"  {'slot':<13}{'before':>7}{'after':>7}{'Δ':>7}   floored?")
    for s in ("aspect_root", "modal", "root", "quant", "tense", "degree",
              "orient", "relator", "force"):
        tag = ("← HELD OUT of the fit" if s == HELD_OUT else
               "in the fit" if s in FIT_SLOTS else "")
        print(f"  {s:<13}{bs[s]:>7}{as_[s]:>7}{as_[s] - bs[s]:>+7}   {tag}")

    # ── the fit, aspect_root held out ────────────────────────────────────
    fit_before = sum(bs[s] for s in FIT_SLOTS)
    fit_after = sum(as_[s] for s in FIT_SLOTS)
    if fit_before == 0:
        raise SystemExit("⛔ the fit slots had no baseline errors; k undefined.")
    k = 1.0 - fit_after / fit_before
    predicted = bs[HELD_OUT] * (1.0 - k)
    observed = as_[HELD_OUT]
    # Poisson sd on the difference: sqrt(var(observed) + var(predicted)).
    sd = math.sqrt(max(observed, 1) + max(predicted, 1))
    z = (observed - predicted) / sd if sd else 0.0

    print(f"\n  ── THE OUT-OF-SAMPLE TEST ──")
    print(f"    k from {FIT_SLOTS} = 1 − {fit_after}/{fit_before} = {k:+.3f}")
    print(f"    PREDICTED aspect_root = {bs[HELD_OUT]} × (1 − {k:.3f}) "
          f"= {predicted:.1f}")
    print(f"    OBSERVED  aspect_root = {observed}")
    print(f"    difference {observed - predicted:+.1f}  (±{sd:.1f} Poisson sd, "
          f"z = {z:+.2f})")

    # ── ⛔ THE UNDERPOWERED BRANCH, WRITTEN FIRST ────────────────────────
    thin = [s for s in FIT_SLOTS if bs[s] < 8]
    if fit_before < 15 or abs(z) < NOISE_SD:
        verdict = "UNDERPOWERED — NOTHING SEPARATED, NOTHING CLOSED"
        why = (f"|z| = {abs(z):.2f} < {NOISE_SD}. The counts cannot resolve a "
               f"difference this size. Slots too thin to contribute: "
               f"{thin or 'none'}. ⛔ This is NOT 'the mechanisms are the same' "
               "and NOT 'H-COLLIDE is absent' — it is the instrument declining "
               "to answer, exactly as the prereg said it might. A powered "
               "version needs n≈1024.")
    elif z < -NOISE_SD:
        verdict = "ASPECT IMPROVED BEYOND THE DOSE-RESPONSE ⇒ evidence for H-COLLIDE"
        why = ("aspect_root fell further than its occupancy increase alone "
               "predicts, and modal received MORE contrastive attention (21 vs "
               "16), so preferential targeting does not explain it.")
    else:
        verdict = "ASPECT RESISTED THE FIX ⇒ evidence for H-REDUP"
        why = ("aspect_root improved less than the dose-response predicts, "
               "which is what a structural difficulty (two fields, reduplicated "
               "surface) would do — occupancy cannot fix a shape problem.")
    print(f"\n  ⇒ {verdict}\n    {why}")

    # ── the categorical observable, readable at low N ────────────────────
    print(f"\n  ── RESIDUAL aspect_root ERRORS BY SOURCE CLASS ──")
    print("    (H-COLLIDE predicts Q→A vanishes; H-REDUP predicts all sources "
          "persist)")
    for cls in sorted(set(bsrc) | set(asrc)):
        print(f"    {cls} → A   {bsrc[cls]:>3} → {asrc[cls]:<3}")
    qa_gone = bsrc.get("Q", 0) > 0 and asrc.get("Q", 0) == 0
    others = sum(v for c, v in asrc.items() if c != "Q")
    if qa_gone and others:
        print("    ⭐ Q→A is GONE while other sources persist — the signature "
              "H-COLLIDE predicts.")
    elif qa_gone and not others:
        print("    ⚠️ ALL aspect sources are gone, not just Q→A. That is "
              "consistent with either mechanism and separates nothing.")

    print(f"\n  ── aspect_reps (an INTEGER, invisible to class_errors) ──")
    print(f"    refusals mentioning aspect_reps: {brs['aspect_reps']} → "
          f"{ars['aspect_reps']}")

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "n": a.n, "render_before": b_rate, "render_after": a_rate,
        "battery_before": b.get("battery"), "battery_after": af.get("battery"),
        "by_slot_before": dict(bs), "by_slot_after": dict(as_),
        "k": k, "predicted_aspect_root": predicted, "observed_aspect_root": observed,
        "z": z, "sd": sd, "verdict": verdict,
        "aspect_sources_before": dict(bsrc), "aspect_sources_after": dict(asrc),
        "aspect_reps_before": brs["aspect_reps"],
        "aspect_reps_after": ars["aspect_reps"]},
        indent=2, ensure_ascii=False), encoding="utf-8", newline="")
    print(f"\n  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
