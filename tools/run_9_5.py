"""PHASE 9.5 -- is Outcome A an enumeration artifact? SCOPE-CHECK, not a rescue.

⛔ THIS CANNOT OVERTURN OUTCOME A. That verdict was locked on the uniform
statistic and it failed on its own terms. What this can establish is whether the
CONCLUSION drawn from it -- "the referent-set lever cannot give the detectors
range" -- generalises, or holds only under uniform enumeration.

⛔⛔ RULE ZERO IS MECHANICAL HERE. Every set-size / share / count this prints
carries its expected value as an assert next to the print, so the number is
checked by the code and not by a human remembering to read it. That error has
now happened EIGHT times, most recently in this phase (D1: I printed
"v2 LIVE SET -- 50 referents" and did not read it).
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.harness.paired import ItemSet, Measurement, side_by_side  # noqa: E402
from tlon.referents import schema                            # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
GATE = 0.25


class BannerMismatch(RuntimeError):
    pass


def banner(label: str, value, expected, fmt="{}"):
    """Print a number AND assert it. Rule zero, mechanised."""
    if value != expected:
        raise BannerMismatch(
            f"{label}: printed {value!r} but expected {expected!r}. "
            "A banner that disagrees with its own expectation is the D1 failure "
            "-- fix the code or fix the expectation, do not print it anyway.")
    print(f"    {label:<52} {fmt.format(value)}")


def main() -> int:
    print("=" * 78)
    print("PHASE 9.5 -- POLICY-WEIGHTED f2. Scope-check on the locked Outcome A.")
    print("=" * 78)

    # ---- 9.5a precondition: do the banked rollouts carry selections? -------
    print("\n  9.5a PRECONDITION -- can P_policy(subset | referent) be recovered")
    print("  from banked data at all?\n")

    ckpts = (list(ROOT.rglob("*.pt")) + list(ROOT.rglob("*.pth"))
             + list(ROOT.rglob("*.ckpt")))
    banner("policy checkpoints on disk", len(ckpts), 0)

    rd = json.loads((RUNS / "reset_dynamics.json").read_text())
    run_keys = sorted(rd["runs"][0])
    banner("phase-8 rollout record: keys per run", len(run_keys), 9)
    print(f"      {run_keys}")
    sel_keys = [k for k in run_keys
                if any(w in k.lower() for w in ("select", "subset", "keep"))]
    banner("...of which carry subset selections", len(sel_keys), 0)

    p5 = json.loads((RUNS / "phase5.json").read_text())
    p5_keys = sorted(p5["results"][0])
    sel5 = [k for k in p5_keys
            if any(w in k.lower() for w in ("select", "subset", "keep"))]
    banner("phase-5 record: keys carrying subset selections", len(sel5), 0)

    print("\n  ⛔⛔ VERDICT ON THE PRECONDITION: THE DATA IS ABSENT, NOT SPARSE.")
    print("     No checkpoint was ever saved and no run banked a per-referent")
    print("     subset selection. There is no effective sample size to report")
    print("     because there is no sample: n = 0 for every referent.")

    # ---- the second blocker, which sparsity would not have fixed ----------
    print("\n  ⛔⛔ AND A STRUCTURAL BLOCKER THAT MORE ROLLOUTS WOULD NOT FIX\n")
    arch = schema.load_archive().referents
    live = schema.load_live().referents
    banner("referents the phase-8 policy was trained on (archive)", len(arch), 60)
    banner("referents Outcome A was measured on (v2)", len(live), 46)
    overlap = {r.id for r in arch} & {r.id for r in live}
    banner("ids in common", len(overlap), 0)
    print("\n     ChannelPolicy is a per-referent LOOKUP TABLE -- logits indexed")
    print("     by referent, and a selection head with per-referent Bernoullis.")
    print("     A policy trained on the archive HAS NO PARAMETERS for a v2")
    print("     referent. So P_policy(subset | v2 referent) does not exist in")
    print("     phase-8 data even in principle. Banking selections would not")
    print("     have helped; only a v2 policy could answer this, and that is")
    print("     TRAINING.")

    # ---- what IS banked, and it bears on the question ---------------------
    print("\n  ⭐ WHAT IS BANKED, AND IT ANSWERS THE QUESTION ON THE ARCHIVE\n")
    p4 = json.loads((RUNS / "phase4.json").read_text())
    arms = {r["arm"]: r for r in p4["results"]}
    rnd = arms["random"]
    banner("phase-4 'random' arm selection_rate", rnd["selection_rate"], 0.5)
    banner("phase-4 'random' arm decidedness", rnd["decidedness"], 0.5)
    print("      ⇒ rate 0.500 + decidedness 0.500 is Bernoulli(0.5) per slot,")
    print("        which IS uniform over subsets. The 'random' arm is the")
    print("        uniform-enumeration weighting, measured the same way.\n")

    print(f"    {'arm':<20} {'sel_rate':>9} {'decided':>9} "
          f"{'frac_ambiguous':>15}")
    for r in p4["results"]:
        tag = "  <- UNIFORM" if r["arm"] == "random" else ""
        print(f"    {r['arm']:<20} {r['selection_rate']:>9.3f} "
              f"{r['decidedness']:>9.3f} {100*r['frac_ambiguous']:>14.1f}%{tag}")

    learned = [r for r in p4["results"] if r["arm"] != "random"]
    lo = min(r["frac_ambiguous"] for r in learned)
    hi = max(r["frac_ambiguous"] for r in learned)
    print(f"\n    uniform (random arm)      {100*rnd['frac_ambiguous']:.1f}%")
    print(f"    every learned policy      {100*lo:.1f}% to {100*hi:.1f}%")
    print("    ⇒ POLICY-WEIGHTING DROVE AMBIGUITY DOWN IN EVERY ARM, by 6-12 pts.")

    # guard adjudicates: this is a distribution comparison, not item-paired
    m_uni = Measurement("uniform-weighted frac_ambiguous", rnd["frac_ambiguous"],
                        ItemSet.of("sampled-scene",
                                   [f"random-{i}" for i in range(900)],
                                   weighting="uniform", referent_set="archive"))
    m_pol = Measurement("policy-weighted frac_ambiguous",
                        arms["learned l=2.0"]["frac_ambiguous"],
                        ItemSet.of("sampled-scene",
                                   [f"learned-{i}" for i in range(900)],
                                   weighting="policy", referent_set="archive"))
    sbs = side_by_side(m_uni, m_pol, reason=(
        "the two weightings draw DIFFERENT scenes by construction -- that is "
        "what a weighting is -- so no item pairing exists even in principle"))
    print("\n  GUARD ADJUDICATION\n")
    print("    " + sbs.describe().replace("\n", "\n    "))
    try:
        _ = sbs.delta
        print("    ⛔ GUARD FAILED")
        return 1
    except Exception:
        print("    ✅ side_by_side, not paired_delta: a re-weighting cannot be")
        print("       item-paired against the thing it re-weights.")

    # ---- outcome -----------------------------------------------------------
    print("\n" + "=" * 78)
    print("  OUTCOME 3 -- INCONCLUSIVE FROM BANKED DATA, for the v2 measurement")
    print("  the check was actually about.\n")
    print("  Not sparse. ABSENT, twice over: nothing banked selections, and the")
    print("  phase-8 policy has no v2 parameters. A re-weighting computed here")
    print("  would be a vacuous number -- the D1 class, a dead measurement")
    print("  reading perfect -- so none is computed.")
    print("\n  ⭐ DIRECTION-ONLY, ON THE ARCHIVE, FROM BANKED PHASE-4 DATA:")
    print(f"     uniform {100*rnd['frac_ambiguous']:.1f}% vs learned "
          f"{100*lo:.1f}-{100*hi:.1f}% ⇒ policy-weighting REDUCES ambiguity,")
    print("     which is OUTCOME 1's direction (Outcome A robust) and matches")
    print("     the naive prior: a good speaker picks informative subsets.")
    print("  ⛔ It is the WRONG SET, ONE SEED PER ARM, and a different estimator")
    print("     granularity (per-sample, not per-distinct-utterance). It may not")
    print("     be quoted as a policy-weighted f2, and it does not decide v2.")

    (RUNS / "phase9_5.json").write_text(json.dumps(
        {"phase": "9.5", "outcome": "3_INCONCLUSIVE_FROM_BANKED_DATA",
         "precondition_failed": True,
         "checkpoints_on_disk": len(ckpts),
         "banked_selection_keys": sel_keys + sel5,
         "effective_sample_size_per_referent": 0,
         "structural_blocker": "phase-8 policy is a per-referent lookup table "
                               "trained on the archive; 0 id overlap with v2",
         "archive_direction_only": {
             "uniform_frac_ambiguous": rnd["frac_ambiguous"],
             "learned_frac_ambiguous_range": [lo, hi],
             "seeds": 1, "set": "archive",
             "caveat": "wrong set, one seed, per-sample not per-utterance; "
                       "direction only, not a policy-weighted f2"},
         "gate": GATE},
        indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {RUNS / 'phase9_5.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
