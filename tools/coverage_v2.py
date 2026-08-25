"""PHASE 9.1 coverage pass for referents_v2.yaml (Cosmicomics).

THE QUESTION: can the language say each of these, and can the GENERATOR build
them -- not only under full utterance, but under every impression-selection
subset the policy could choose?

⛔ THIS TOOL DELIBERATELY DOES NOT COMPUTE CONSISTENCY-SET SIZE. That is 9.2's
headline number and it is prereg-locked. Computing it here, while the
signatures are still editable, is exactly the tuning loop the phase ordering
exists to prevent -- the artistic choice would end up shaped by the detector.
Satisfiability and faithfulness only. The number comes later, whatever it is.

WHAT REACHABILITY MEANS AND WHY IT IS MEASURED. A depth-2 pattern hangs off a
depth-1 node, so a subset that keeps the deep dependent and drops every shallow
one CANNOT BUILD (phase3.build_scene returns None). That is a real hole in the
selection space -- the same kind of thing Phase 7 discovered too late -- so it
is counted per referent rather than assumed away.
"""
from __future__ import annotations

import collections
import itertools
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch                                              # noqa: E402

from tlon.grammar import classes as C                     # noqa: E402
from tlon.grammar.parse import render                     # noqa: E402
from tlon.referents import schema                         # noqa: E402
from tlon.selfplay import phase3                          # noqa: E402
from tlon.selfplay.policy import Choice, channel_values   # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
V2 = ROOT / "tlon" / "referents" / "referents_v2.yaml"
OUT = ROOT / "runs"
TRIES = 60


def a_choice(rng, vals, keep):
    return Choice(values={k: rng.choice(v) for k, v in vals.items()},
                  logprob=torch.zeros(()), entropy=torch.zeros(()),
                  select=keep)


def main() -> int:
    rs = schema.load(V2, allow_unreviewed=True)
    refs = rs.referents
    live = [r for r in refs if r.seed_2a]
    held = [r for r in refs if not r.seed_2a]
    lex = C.load()
    vals = channel_values()
    rng = random.Random(9191)

    print("=" * 78)
    print("PHASE 9.1 COVERAGE -- referents_v2.yaml (The Distance of the Moon)")
    print("=" * 78)
    print(f"  review_status : {rs.review_status}   (must be REVIEWED to run live)")
    print(f"  lexicon       : {lex['_hash']}  {len(lex['classes']['R'])} roots")
    print(f"  referents     : {len(refs)} declared = {len(live)} live "
          f"+ {len(held)} held back (seed_2a: false)")
    print("  ⇒ every root/orient/relator/aspect validated by schema.load()")

    # ---- structure -------------------------------------------------------
    depth = collections.Counter(len(r.signature.contains) for r in refs)
    feat = collections.Counter()
    for r in refs:
        if r.signature.forbid:
            feat["forbid"] += 1
        if r.signature.matrix:
            feat["matrix"] += 1
        for p in r.signature.contains:
            if p.at_depth is not None and p.at_depth > 1:
                feat["at_depth>1"] += 1
            if p.aspect_root_any:
                feat["aspect_root_any"] += 1
            if p.orient_any:
                feat["orient_any"] += 1
            if p.via:
                feat["via"] += 1
            if len(p.root_any) > 1:
                feat["disjunctive_root"] += 1
    nest = [r.id for r in refs
            if any(p.at_depth and p.at_depth > 1 for p in r.signature.contains)]

    print("\n  SIGNATURE BREADTH (contains-patterns; cap is 4)")
    for n in sorted(depth):
        print(f"    {n} patterns ({n-1} dependents): {depth[n]:>3}  {'#' * depth[n]}")
    print(f"    mean {sum(len(r.signature.contains) for r in refs)/len(refs):.2f}"
          f"   (old set: 2.50, max 3 patterns)")

    print("\n  SCHEMA FEATURES        v2      old 60")
    for k, old in (("via", 88), ("orient_any", 31), ("disjunctive_root", 16),
                   ("aspect_root_any", 2), ("at_depth>1", 2),
                   ("forbid", 0), ("matrix", 0)):
        print(f"    {k:<20} {feat[k]:>4}    {old:>4}")
    print(f"    referents using nesting: {len(nest)}  {nest}")

    # ---- the 9.3 decision, decided by the file, not by me ----------------
    uses_fm = [r.id for r in refs if r.signature.forbid or r.signature.matrix]
    print("\n  ⭐ 9.3 INPUT -- does v2 use forbid/matrix?")
    if uses_fm:
        print(f"    YES: {uses_fm}")
        print("    ⇒ 9.3 MUST re-run the Phase 6.2 taxonomy placement on v2.")
    else:
        print("    NO -- 0 of "
              f"{len(refs)}, as in the old set.")
        print("    ⇒ Phase 6's isolation claim carries over UNCHANGED. Its")
        print("      honest scope was 'impossible for signature families")
        print("      WITHOUT forbid/matrix', and v2 is such a family.")

    # ---- collision structure (the reason this world was chosen) ----------
    head_use = collections.Counter()
    any_use = collections.Counter()
    for r in refs:
        for f in r.signature.contains[0].root_any:
            head_use[f] += 1
        for p in r.signature.contains:
            for f in p.root_any:
                any_use[f] += 1
    uniq_head = [r.id for r in refs
                 if all(head_use[f] == 1 for f in r.signature.contains[0].root_any)]
    print("\n  COLLISION STRUCTURE -- the reason this world was chosen")
    print(f"    distinct roots used            : {len(any_use)} of "
          f"{len(lex['classes']['R'])}")
    print(f"    referents with a UNIQUE head root: {len(uniq_head)}/{len(refs)}"
          f"   (old set: 26/60 = 43 %)  {uniq_head}")
    print("    most-shared roots (appearances):")
    for f, c in any_use.most_common(10):
        print(f"      {f:<6} {c:>3}   {lex['classes']['R'][f]}")

    # ---- can it be built, and under every selection subset? --------------
    print("\n  REACHABILITY -- can the generator build it, per selection subset?")
    print(f"    {'id':<5} {'pats':>4} {'subsets':>8} {'reachable':>10}   name")
    rows, bad, holes = [], [], 0
    for r in refs:
        deps = len(r.signature.contains) - 1
        subs = [keep for k in range(deps + 1)
                for keep in itertools.combinations(range(deps), k)]
        ok = 0
        unreachable = []
        for keep in subs:
            built = False
            for _ in range(TRIES):
                sc = phase3.build_scene(r, a_choice(rng, vals, keep), rng)
                if sc is not None:
                    render(sc)
                    built = True
                    break
            if built:
                ok += 1
            else:
                unreachable.append(keep)
        holes += len(unreachable)
        rows.append({"id": r.id, "name": r.name, "patterns": deps + 1,
                     "subsets": len(subs), "reachable": ok,
                     "unreachable": [list(u) for u in unreachable],
                     "seed_2a": r.seed_2a})
        flag = "" if ok == len(subs) else f"   <- {unreachable}"
        if ok == 0:
            bad.append(r.id)
        print(f"    {r.id:<5} {deps+1:>4} {len(subs):>8} {ok:>7}/{len(subs):<2}"
              f"   {r.name[:40]}{flag}")

    total_subs = sum(x["subsets"] for x in rows)
    total_ok = sum(x["reachable"] for x in rows)
    print(f"\n    TOTAL {total_ok}/{total_subs} subsets reachable "
          f"({100*total_ok/total_subs:.1f} %), {holes} holes")

    # ---- verdict ---------------------------------------------------------
    print("\n" + "=" * 78)
    fail = False
    if bad:
        print(f"  ⛔ UNSAYABLE: {bad} -- no legal scene at ANY subset.")
        fail = True
    else:
        print(f"  ✅ ALL {len(refs)} REFERENTS ARE SAYABLE. The language can "
              "build every one.")
    if holes:
        print(f"  ⚠️  {holes} SELECTION SUBSETS UNREACHABLE ({100*holes/total_subs:.1f} %).")
        print("     Expected and structural: a depth-2 pattern needs a depth-1")
        print("     sibling present, so subsets keeping only the deep dependent")
        print("     cannot build. Recorded, not hidden -- it shrinks the space")
        print("     impression-selection can search, which is the quantity")
        print("     Phase 7 found was too small.")
    print("\n  ⛔ NOT MEASURED HERE, ON PURPOSE: consistency-set size, omission")
    print("     ceiling, RSA frontier. Those are 9.2, under a locked prereg.")

    OUT.mkdir(exist_ok=True)
    (OUT / "coverage_v2.json").write_text(json.dumps(
        {"phase": "9.1", "review_status": rs.review_status,
         "lexicon": lex["_hash"], "n_declared": len(refs), "n_live": len(live),
         "n_held_back": len(held),
         "breadth": {str(k): v for k, v in depth.items()},
         "features": dict(feat), "nesting_referents": nest,
         "uses_forbid_or_matrix": uses_fm,
         "distinct_roots": len(any_use),
         "unique_head_root": uniq_head,
         "subsets_total": total_subs, "subsets_reachable": total_ok,
         "referents": rows},
        indent=2, ensure_ascii=False), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'coverage_v2.json'}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
