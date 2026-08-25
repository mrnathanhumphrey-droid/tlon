"""PHASE 13.2 -- Part 1 (scenes-per-form) and Part 2 (the 2x2).

⭐⭐ THE CLUSTER CONSTRUCTION HANDS US THE PAIRED CONTROL FOR FREE, and it is
the honesty of the whole temporal axis. Every eval utterance yields TWO
accuracies over the SAME item, from the SAME listener:

    expressible ... argmax over the 8 CLUSTER scores == the true cluster.
                    The signature core determines this. It is what a listener
                    can get right with no pact at all.
    residue ....... argmax over the 3 MATES OF THE TRUE CLUSTER == the true
                    mate. The core is byte-identical across mates, so ONLY a
                    pact in the free channel can move this above 1/3.

Restricting to the true cluster's mates (rather than conditioning on "the
cluster was predicted correctly") is what keeps the two measurements over
IDENTICAL items. Conditioning would make the item set depend on the listener
being compared, which is the unpaired comparison in its phase-7 costume.

⛔ R-ISOLATION IS lambda=0, AND IT IS EXACT RATHER THAN APPROXIMATE.
`reward = M + lambda * (1 - novelty_cost)`, so at lambda=0 R is not in the
reward at all and the residue's ONLY remaining route into the loop -- the one
`tools/premise_13_2.py` identified as the confound -- is closed by construction.
The lambda=1 cells then MEASURE R's contribution rather than assuming it away.
Setting W_RESIDUE=0 would NOT have worked: it re-arms the RepetitionLog landmine
(nd == 0.0 folds cluster-mates into one medoid), so the isolation would have
manufactured the very null it was meant to rule out.

⛔ CROSS-CELL COMPARISONS ARE NOT PAIRED AND ARE NOT PRETENDED TO BE. Different
arms and different parameterisations produce different utterances, so no item
pairing exists; they go through side_by_side() and a seed-level unpaired test.
The guard governs the WITHIN-run comparisons, where pairing is real.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import statistics as S
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

import torch                                                     # noqa: E402

from tlon.grammar.denote import project                          # noqa: E402
from tlon.grammar.parse import parse, render                     # noqa: E402
from tlon.referents.match import consistent                      # noqa: E402
from tlon.harness.ceiling import (bayes_ceiling, classify_policy,  # noqa: E402
                                  readable)
from tlon.harness.paired import (ItemSet, Measurement,           # noqa: E402
                                 paired_delta, side_by_side)
from tlon.listener import data, train as tr                      # noqa: E402
from tlon.listener import tokenizer as tk                        # noqa: E402
from tlon.listener.model import Listener                         # noqa: E402
from tlon.novelty import distance as D                           # noqa: E402
from tlon.novelty.centroids import RepetitionLog                 # noqa: E402
from tlon.referents import schema                                # noqa: E402
from tlon.selfplay import phase3                                 # noqa: E402
from tlon.selfplay.policy import ChannelPolicy                   # noqa: E402
from run_10_0_mde import mde, t975                               # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
SEEDS = [11, 22, 33, 44, 55, 66, 77, 88]        # n=8, Nate's ruling
STEPS = 4000
N_EVAL = 900
PRE_PER_REF = 120
MDE_FLOOR = 2.96                                # prior sd 3.54 at n=8


class BannerMismatch(RuntimeError):
    pass


def banner(label: str, value, expected, fmt="{}") -> None:
    if value != expected:
        raise BannerMismatch(f"{label}: printed {value!r}, expected {expected!r}")
    print(f"    {label:<52} {fmt.format(value)}")


# ── cluster bookkeeping ───────────────────────────────────────────────────
def clusters_of(refs) -> tuple[list[int], list[list[int]]]:
    """cluster index per referent, and the referent indices in each cluster.

    Grouped by the EXPRESSIBLE signature, which is what makes them a cluster.
    """
    key_of, groups = {}, []
    cidx = []
    for i, r in enumerate(refs):
        key = tuple(tuple(sorted(p.root_any)) + tuple(sorted(p.via))
                    for p in r.signature.contains)
        if key not in key_of:
            key_of[key] = len(groups)
            groups.append([])
        c = key_of[key]
        groups[c].append(i)
        cidx.append(c)
    return cidx, groups


def residues_of(refs) -> list[tuple[int, ...]]:
    out = []
    for r in refs:
        got = [c for p in r.signature.contains for c in p.residue_any]
        if len(got) != 1:
            raise RuntimeError(
                f"{r.id}: expected exactly one residue coordinate, got {len(got)}")
        out.append(got[0])
    return out


# ── PART 1 ────────────────────────────────────────────────────────────────
def part1(refs, tag: str) -> dict:
    """SCENES-PER-FORM: how many distinct scenes share one surface.

    ⛔ TRUE BY CONSTRUCTION AND THEREFORE A BUILD CHECK, NEVER A RESULT. 13.1
    records it as the frontier-relevant quantity that every previous set
    measured as exactly 1. If it is 1 here the residue is not contained and the
    build is wrong; that is all this can tell us.

    ⛔ MEASURED WITH `consistent()`, NOT BY COUNTING SAMPLED SURFACE
    COLLISIONS. The first version of this counted how often two sampled scenes
    happened to render to the same string and reported mean 1.016 -- because
    the free channel holds 24,500 codes and two mates almost never draw the
    same one, so collisions are rare NO MATTER HOW AMBIGUOUS THE SET IS. That
    measures the sampler, not the structure. `consistent()` is the exact
    instrument the f2 and RSA-frontier work already uses: for a heard utterance
    it returns every referent the utterance could denote, and for a residue
    cluster that set is the whole cluster BECAUSE the parse recovers no residue
    (unknown-as-ignorance). The two numbers answer different questions and only
    the second is the frontier quantity.
    """
    rng = random.Random(31337)
    pol = ChannelPolicy(len(refs))
    torch.manual_seed(31337)
    sizes, collisions, n = [], {}, 0
    for _ in range(3000):
        ri = rng.randrange(len(refs))
        with torch.no_grad():
            ch = pol(ri)
        sc = phase3.build_scene(refs[ri], ch, rng)
        if sc is None:
            continue
        surf = render(sc)
        collisions.setdefault(surf, set()).add(ri)
        try:
            heard = parse(surf)
        except Exception:
            continue
        sizes.append(sum(1 for r in refs if consistent(heard, r.signature)))
        n += 1
    coll = [len(v) for v in collisions.values()]
    out = {"set": tag, "n_utterances": n,
           "scenes_per_form_mean": S.fmean(sizes),
           "scenes_per_form_max": max(sizes),
           "share_gt1": sum(1 for x in sizes if x > 1) / len(sizes),
           "sampled_surface_collision_mean": S.fmean(coll)}
    print(f"    {tag:<10} scenes/form (via consistent()) mean "
          f"{out['scenes_per_form_mean']:.3f}  max {out['scenes_per_form_max']}"
          f"  >1 on {100*out['share_gt1']:.1f}% of utterances")
    print(f"    {'':<10} (sampled surface-collision rate {S.fmean(coll):.3f} — "
          "a DIFFERENT quantity, reported so it is not mistaken for the above)")
    return out


# ── the two carried confirmations, on the 13.2 sets ───────────────────────
def confirmations(refs, tag: str) -> dict:
    """⛔ NO PART-2 NULL IS INTERPRETABLE UNTIL BOTH OF THESE PASS.

    They are re-run per ARM rather than trusted from tests/test_residue.py,
    because the ledger's landmine is a property of the scenes a SET produces,
    not of the code in the abstract -- and the build-gap lesson is exactly that
    a hand-built object cannot certify the pipeline that builds the real ones.
    """
    rng = random.Random(4242)
    pol = ChannelPolicy(len(refs))
    torch.manual_seed(4242)
    cidx, groups = clusters_of(refs)
    ok_medoids, checked, no_residue = 0, 0, 0
    for g in groups:
        if len(g) < 2:
            continue
        scenes = []
        for ri in g:
            for _ in range(40):
                with torch.no_grad():
                    ch = pol(ri)
                sc = phase3.build_scene(refs[ri], ch, rng)
                if sc is not None:
                    scenes.append((ri, sc))
                    break
        if len(scenes) < 2:
            continue
        for _, sc in scenes:
            if sc.node.residue is None:
                no_residue += 1
        log = RepetitionLog()
        for _, sc in scenes:
            log.observe("c", sc, render(sc))
        checked += 1
        if len(log.buckets["c"].medoids) == len(scenes):
            ok_medoids += 1
    (a_ri, a), (b_ri, b) = scenes[0], scenes[1]
    out = {"set": tag, "clusters_checked": checked,
           "clusters_with_one_medoid_per_mate": ok_medoids,
           "scenes_missing_a_residue": no_residue,
           "example_normalized_distance": D.normalized(a, b)}
    good = (checked > 0 and ok_medoids == checked and no_residue == 0)
    print(f"    {tag:<16} landmine: {ok_medoids}/{checked} clusters give one "
          f"medoid per mate   ·  scenes missing a residue: {no_residue}   "
          f"{'OK' if good else '⛔ FAILED'}")
    if not good:
        raise RuntimeError(
            f"{tag}: carried confirmations FAILED — residue-differing scenes "
            "collapse, or a generated scene carries no residue. Either "
            "manufactures a null; no Part-2 number from this arm is readable.")
    return out


# ── listener plumbing ─────────────────────────────────────────────────────
def honest_rows(refs, rng, per_ref=PRE_PER_REF):
    """Utterances with NO pact: uniform free channels, so the naive judge learns
    the language and nothing else. Inside a cluster these are identical across
    mates by construction, which is exactly why the naive mate-accuracy floor is
    1/k and the gap is directly interpretable."""
    pol = ChannelPolicy(len(refs))              # all-zero logits == uniform
    rows = []
    for ri, ref in enumerate(refs):
        made, guard = 0, 0
        while made < per_ref and guard < per_ref * 8:
            guard += 1
            with torch.no_grad():
                ch = pol(ri)
            sc = phase3.build_scene(ref, ch, rng)
            if sc is None:
                continue
            surf = render(project(sc))
            rows.append(data.Example(label=ri, ref_id=ref.id, surface=surf,
                                     uid="", ids=tk.encode(surf), dec_key=""))
            made += 1
    return rows


def sample_eval(policy, refs, rng, n):
    rows, guard = [], 0
    while len(rows) < n and guard < n * 10:
        guard += 1
        ri = rng.randrange(len(refs))
        with torch.no_grad():
            ch = policy(ri)
        sc = phase3.build_scene(refs[ri], ch, rng)
        if sc is None:
            continue
        surf = render(project(sc))
        rows.append(data.Example(label=ri, ref_id=refs[ri].id, surface=surf,
                                 uid="", ids=tk.encode(surf), dec_key=""))
    return rows


@torch.no_grad()
def components(model, rows, cidx, groups, dev) -> tuple[list[bool], list[bool]]:
    """Per-item (expressible_correct, residue_correct) — SAME items for both."""
    model.eval()
    ids = torch.tensor([r.ids for r in rows], dtype=torch.long, device=dev)
    logits = model(ids).float().cpu()
    exp_ok, res_ok = [], []
    for j, r in enumerate(rows):
        lg = logits[j]
        c = cidx[r.label]
        # expressible: which CLUSTER, by log-sum-exp over its members
        cs = [torch.logsumexp(lg[torch.tensor(g)], dim=0) for g in groups]
        exp_ok.append(int(max(range(len(cs)), key=lambda k: cs[k])) == c)
        # residue: which MATE of the TRUE cluster (identical items, no
        # conditioning on the cluster having been predicted correctly)
        mates = groups[c]
        best = max(mates, key=lambda i: float(lg[i]))
        res_ok.append(best == r.label)
    return exp_ok, res_ok


def one_run(refs, cidx, groups, *, seed: int, param: str, lam: float,
            train_listener: bool, seed_state, naive, dev, cfg,
            steps: int, entropy_bonus: float) -> dict:
    residues = residues_of(refs) if param == "head" else None
    torch.manual_seed(seed)
    pol = ChannelPolicy(len(refs), residues=residues).to(dev)
    L = Listener(len(refs)).to(dev)
    L.load_state_dict(seed_state)
    trained, _, st = phase3.run(
        refs, L,
        phase3.P3Cfg(lam=lam, device=dev, project=True, steps=steps, seed=seed,
                     normalize_advantage=True, train_listener=train_listener,
                     entropy_bonus=entropy_bonus),
        verbose=False, policy=pol)

    ev = random.Random(9000 + seed)
    rows = sample_eval(trained, refs, ev, N_EVAL)
    keys = [f"{i}|{r.ref_id}|{r.surface}" for i, r in enumerate(rows)]
    co_e, co_r = components(L, rows, cidx, groups, dev)
    nv_e, nv_r = components(naive, rows, cidx, groups, dev)

    def M(name, vals, **facets):
        return Measurement(name=name, value=S.fmean(vals),
                           items=ItemSet.of("eval-utterance", keys, **facets))

    base = dict(seed=seed, param=param, lam=lam,
                coadapt=train_listener)
    d_res = paired_delta(M("co-adapted residue", co_r, listener="coadapted",
                           component="residue", **base),
                         M("naive residue", nv_r, listener="naive",
                           component="residue", **base), contrast="listener")
    d_exp = paired_delta(M("co-adapted expressible", co_e, listener="coadapted",
                           component="expressible", **base),
                         M("naive expressible", nv_e, listener="naive",
                           component="expressible", **base), contrast="listener")
    # ⛔⛔ CEILING DETECTOR ON THE EXPRESSIBLE CONTROL. Measured in the first
    # dry run: co_expressible == naive_expressible == 1.0000 on every seed. The
    # signature core is always fully uttered and exactly parseable, so cluster
    # identification is at ceiling for BOTH listeners from step 0 -- which makes
    # the specified residue-vs-expressible paired control a comparison against a
    # FLAT LINE. "Residue grows faster than expressible" would then be trivially
    # true and the control would prove nothing: a control that cannot come back
    # positive is not a control. Flagged per run so it can never pass silently;
    # the FROZEN-LISTENER arm is the substitute that can move.
    at_ceiling = (min(S.fmean(co_e), S.fmean(nv_e)) > 0.999)

    # ── FIX 2: THE BAYES-CEILING GATE, per cell (PROPOSAL_13_2_...) ────────
    # Replaces `categorical x head == categorical x table`, which D16 showed was
    # invalid under the MLP trunk. This reads what the POLICY DOES and never how
    # it is built, so it cannot be invalidated by an architecture change the way
    # the old invariant was. It refuses a cell whose own policy left a
    # Bayes-optimal listener no room -- collapse AND over-entropy both land
    # there -- and its refusal means UNINFORMATIVE, never "null".
    cei = bayes_ceiling(trained, groups)
    verdict, why = classify_policy(trained, groups, MDE_FLOOR)
    gate_ok, gate_why = readable(cei, MDE_FLOOR)

    return {"seed": seed, "param": param, "lam": lam,
            "coadapt": train_listener,
            "expressible_at_ceiling": at_ceiling,
            "bayes_ceiling": cei["ceiling"], "bayes_floor": cei["floor"],
            "headroom_pts": cei["headroom_pts"],
            "policy_verdict": verdict, "policy_why": why,
            "gate_readable": gate_ok, "gate_why": gate_why,
            "gap_residue": d_res.value, "gap_expressible": d_exp.value,
            "co_residue": S.fmean(co_r), "naive_residue": S.fmean(nv_r),
            "co_expressible": S.fmean(co_e), "naive_expressible": S.fmean(nv_e),
            "n_eval": len(rows), "digest": d_res.left.items.digest,
            "residue_log_size": len(st.residues)}


def welch(a: list[float], b: list[float]) -> tuple[float, float]:
    """Unpaired seed-level contrast. ⛔ Cross-cell comparisons are NOT paired --
    different arms/parameterisations emit different utterances -- so the honest
    test is a between-seeds one, reported as such."""
    ma, mb = S.fmean(a), S.fmean(b)
    va, vb = S.variance(a), S.variance(b)
    se = math.sqrt(va / len(a) + vb / len(b))
    if se == 0:
        return ma - mb, float("nan")
    df = (va / len(a) + vb / len(b)) ** 2 / (
        (va / len(a)) ** 2 / (len(a) - 1) + (vb / len(b)) ** 2 / (len(b) - 1))
    return ma - mb, (ma - mb) / se


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="random",
                    help="comma list of residue arms (lyric,random)")
    ap.add_argument("--seeds", type=int, default=len(SEEDS))
    ap.add_argument("--steps", type=int, default=STEPS)
    ap.add_argument("--lams", default="0.0",
                    help="0.0 is the R-ISOLATED primary; add 1.0 to measure R")
    ap.add_argument("--dry", action="store_true",
                    help="pipeline check only — NOT a Part-2 result")
    ap.add_argument("--entropy", type=float, default=0.01,
                    help="speaker entropy bonus. 0.01 is the INCUMBENT that "
                         "collapsed; the frozen value comes from "
                         "tools/entropy_sweep_13_2.py, chosen on the CONTROL "
                         "arm on seeds disjoint from these.")
    ap.add_argument("--out", default="phase13_2.json")
    args = ap.parse_args()

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    lams = [float(x) for x in args.lams.split(",")]
    seeds = SEEDS[:args.seeds]

    print("=" * 78)
    print("PHASE 13.2 -- the 2x2." + ("  ⛔⛔ DRY RUN: PIPELINE CHECK, NOT A "
                                      "RESULT." if args.dry else ""))
    print("=" * 78)
    print(f"  device {dev} · arms {arms} · lambdas {lams} · "
          f"{len(seeds)} seeds · {args.steps} steps")
    if not args.dry:
        banner("seeds (Nate's ruling)", len(seeds), 8)
        print(f"    {'MDE floor at n=8 (prior sd 3.54)':<52} "
              f"{MDE_FLOOR:.2f} pts")
        print("    ⛔ the prior came from a CEILINGED M; treat as a FLOOR.")

    results: dict = {"dry_run": args.dry, "steps": args.steps,
                     "entropy_bonus": args.entropy,
                     "seeds": seeds, "lams": lams, "arms": arms,
                     "mde_floor_pts": MDE_FLOOR, "part1": {},
                     "confirmations": {}, "runs": []}

    for arm in arms:
        refs = schema.load_residue_arm(arm, allow_unreviewed=True).referents
        cidx, groups = clusters_of(refs)
        print(f"\n  ── ARM {arm.upper()} — {len(refs)} referents, "
              f"{len(groups)} clusters, mates {sorted({len(g) for g in groups})}"
              f", residue dim {len(residues_of(refs)[0])} ──")
        print("\n  PART 1 — scenes-per-form (BUILD CHECK, true by construction)")
        p1 = part1(refs, arm)
        results["part1"][arm] = p1
        if p1["scenes_per_form_max"] <= 1:
            print("    ⛔ scenes-per-form is 1 — the residue is not contained "
                  "and the build is WRONG. Stopping.")
            return 1
        print("\n  CARRIED CONFIRMATIONS (landmine + unknown-as-ignorance)")
        results["confirmations"][arm] = confirmations(refs, arm)

        cfg = tr.TrainCfg()
        brng = random.Random(4242)
        hr = honest_rows(refs, brng)
        brng.shuffle(hr)
        cut = int(0.9 * len(hr))
        seed_state = {k: v.detach().clone() for k, v in tr.train(
            hr[:cut], hr[cut:], len(refs), cfg, verbose=False
        ).state_dict().items()}
        nr = honest_rows(refs, brng)
        brng.shuffle(nr)
        ncut = int(0.9 * len(nr))
        naive = tr.train(nr[:ncut], nr[ncut:], len(refs),
                         tr.TrainCfg(seed=cfg.seed + 991), verbose=False)
        naive.eval()

        print(f"\n  PART 2 — 2x2  (naive judge held-out "
              f"{100*S.fmean(components(naive, nr[ncut:], cidx, groups, dev)[1]):.1f}% "
              "residue)")
        for lam in lams:
            for param in ("table", "head"):
                # ⛔ THE FROZEN ARM IS NOT OPTIONAL AND IT IS NOT A BASELINE
                # FOR SHOW. train_listener=False makes co-adaptation
                # IMPOSSIBLE, while the generator still shifts its distribution
                # to be understood -- so it separates "a pact formed" from "the
                # policy concentrated and the listener happens to do better on
                # a narrower distribution". With the expressible component
                # pinned at ceiling this is the ONLY control in the design that
                # can come back positive, so it carries the weight the
                # residue-vs-expressible pairing cannot.
                for coadapt in (True, False):
                    rows = []
                    for sd in seeds:
                        t0 = time.time()
                        r = one_run(refs, cidx, groups, seed=sd, param=param,
                                    lam=lam, train_listener=coadapt,
                                    seed_state=seed_state, naive=naive,
                                    dev=dev, cfg=cfg, steps=args.steps,
                                    entropy_bonus=args.entropy)
                        r["arm"] = arm
                        r["secs"] = time.time() - t0
                        rows.append(r)
                        results["runs"].append(r)
                        print(f"    {arm:<7} {param:<5} λ={lam:<4} "
                              f"{'coadapt' if coadapt else 'FROZEN ':<8} "
                              f"seed {sd:>3}  residue "
                              f"{100*r['co_residue']:>5.1f}% vs naive "
                              f"{100*r['naive_residue']:>5.1f}%  gap "
                              f"{100*r['gap_residue']:>+6.2f}"
                              f"{'  ⚠exp@ceiling' if r['expressible_at_ceiling'] else ''}"
                              f"  [{r['secs']:.0f}s]")
                    g = [100 * x["gap_residue"] for x in rows]
                    sd_ = S.stdev(g) if len(g) > 1 else float("nan")
                    print(f"    {'':>7} {param:<5} λ={lam:<4} "
                          f"{'coadapt' if coadapt else 'FROZEN ':<8} MEAN "
                          f"{S.fmean(g):+.2f} pts  sd {sd_:.2f}  MDE@n="
                          f"{len(g)} "
                          f"{mde(sd_, len(g)) if len(g) > 1 else float('nan'):.2f}")

    # ── the four-way read, only when the full 2x2 is present ──────────────
    def cell(arm, param, lam, coadapt=True):
        return [100 * r["gap_residue"] for r in results["runs"]
                if r["arm"] == arm and r["param"] == param
                and r["lam"] == lam and r["coadapt"] is coadapt]

    # ⭐⭐ FREE INTEGRITY CHECK, AND IT IS EXACT. In `table` mode the policy
    # never sees a residue coordinate; at lambda=0 R is out of the reward; the
    # expressible scaffold is byte-identical between the arms; and a singleton
    # residue_any draws no rng. So metric x table and categorical x table must
    # come out BIT-IDENTICAL at lambda=0. If they diverge, the residue is
    # reaching the loop through some route the design does not know about, and
    # NO cell is readable until that is found.
    if set(arms) >= {"lyric", "random"} and 0.0 in lams:
        for coad in (True, False):
            a, b = cell("lyric", "table", 0.0, coad), cell("random", "table", 0.0, coad)
            if a and b:
                same = all(abs(x - y) < 1e-12 for x, y in zip(a, b))
                tagc = "coadapt" if coad else "FROZEN"
                print(f"\n  ⭐ λ=0 TABLE-IDENTITY CHECK ({tagc}): "
                      f"{'PASS — bit-identical across arms' if same else '⛔⛔ FAIL'}")
                if not same:
                    print("     The residue reached the loop through a route "
                          "the design does not know about.\n     No cell is "
                          "readable until that is found.")
                    results["table_identity_fail"] = True

    n_ceil = sum(1 for r in results["runs"] if r["expressible_at_ceiling"])
    if n_ceil:
        print(f"\n  ⚠ EXPRESSIBLE COMPONENT AT CEILING ON {n_ceil}/"
              f"{len(results['runs'])} RUNS. The signature core is always fully "
              "uttered and exactly\n    parseable, so cluster identification is "
              "1.0000 for BOTH listeners from step 0. The specified\n    "
              "residue-vs-expressible paired control is therefore a comparison "
              "against a flat line and\n    CANNOT ADJUDICATE. The frozen arm "
              "carries that role. Recorded, not worked around.")
    results["expressible_at_ceiling_runs"] = n_ceil

    if set(arms) >= {"lyric", "random"} and not args.dry:  # four-way read
        for lam in lams:
            mh, ch_ = cell("lyric", "head", lam), cell("random", "head", lam)
            mt, ct = cell("lyric", "table", lam), cell("random", "table", lam)
            print(f"\n  ── THE FOUR-WAY READ, λ={lam} ──")
            print(f"    metric×head {S.fmean(mh):+.2f}   categorical×head "
                  f"{S.fmean(ch_):+.2f}   metric×table {S.fmean(mt):+.2f}   "
                  f"categorical×table {S.fmean(ct):+.2f}")
            d, t = welch(mh, ch_)
            print(f"    head contrast (metric - categorical): {d:+.2f} pts, "
                  f"Welch t {t:.2f}  [UNPAIRED by construction]")
            # ── FIX 2: THE GATE. Per-cell Bayes ceiling, not table-equality.
            # The old invariant (`cat x head == cat x table`) was invalid under
            # the MLP trunk (D16) and fired on a design error. This one asks
            # only what each policy DOES.
            print(f"\n    ⭐ THE GATE — per-cell Bayes ceiling "
                  f"(bar: headroom > MDE {MDE_FLOOR:.2f} pts)")
            gates = {}
            for arm, param in (("random", "head"), ("lyric", "head"),
                               ("random", "table"), ("lyric", "table")):
                rs = [r for r in results["runs"] if r["arm"] == arm
                      and r["param"] == param and r["lam"] == lam
                      and r["coadapt"]]
                if not rs:
                    continue
                hr = S.fmean(r["headroom_pts"] for r in rs)
                ok = all(r["gate_readable"] for r in rs)
                gates[(arm, param)] = ok
                verds = {r["policy_verdict"] for r in rs}
                print(f"      {arm:<7}×{param:<6} ceiling "
                      f"{100*S.fmean(r['bayes_ceiling'] for r in rs):>5.1f}%  "
                      f"headroom {hr:>6.2f} pts  "
                      f"{'READABLE' if ok else '⛔ REFUSED'}  "
                      f"{'/'.join(sorted(verds))}")
            control_ok = gates.get(("random", "head"), False)
            metric_ok = gates.get(("lyric", "head"), False)
            if not control_ok:
                print("      ⛔⛔ THE CONTROL CELL (categorical×head) IS REFUSED "
                      "— the head cannot read even a\n         categorical "
                      "residue, so no metric×head number rides on a proven "
                      "head. STOP.")
            elif not metric_ok:
                print("      ⛔ metric×head is REFUSED by its own ceiling: its "
                      "policy left a Bayes-optimal\n         listener no room, "
                      "so its result is UNINFORMATIVE about the residue — "
                      "NOT a null.")
            else:
                print("      ✅ both head cells readable — the metric contrast "
                      "above is interpretable.")
            results.setdefault("gate", {})[str(lam)] = {
                "control_readable": control_ok, "metric_readable": metric_ok}
            print(side_by_side(
                Measurement("metric×head gap", S.fmean(mh) / 100,
                            ItemSet.of("seed-gap", [f"lyric-head-{s}" for s in seeds],
                                       arm="lyric", param="head")),
                Measurement("categorical×head gap", S.fmean(ch_) / 100,
                            ItemSet.of("seed-gap", [f"random-head-{s}" for s in seeds],
                                       arm="random", param="head")),
                reason="different arms emit different utterances, so no "
                       "item-level pairing exists; the seed-level Welch "
                       "contrast above is the honest test").describe())

    (OUT / args.out).write_text(json.dumps(results, indent=2, default=float),
                                encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / args.out}")
    if args.dry:
        print("  ⛔⛔ DRY RUN — pipeline only. No number here is a Part-2 result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
