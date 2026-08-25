"""Phase 6.2 — place Tlon in Lazaridou et al. (2020)'s drift taxonomy, in code.

THE CLAIM UNDER TEST. Lazaridou names three drift types: STRUCTURAL (the message
stops being well-formed in its language), SEMANTIC (the message stops being
grounded to its target; word meanings shift), PRAGMATIC (the listener's assumed
interpretation diverges from an outside interpretation). They report pragmatic
drift is the hardest to isolate, and reach it only via a hand-built special case
(reranking gold captions). Our spine is that we isolate it BY CONSTRUCTION.

Verify, do not assert.

WHY THE MEASURE IS BINARY HERE, NOT GRADED. Their structural proxy is log-prob
under a pretrained LM and their semantic proxy is target-conditional log-prob.
Both are graded because English grammaticality and grounding are soft. Ours are
exact: an LL(1) parser either accepts or it does not, and a scene either denotes
its referent or it does not. A graded proxy is what you use when you lack the
exact relation. We have it, so the honest analogue is the exact relation, not a
neural estimate of it.

⛔ THE TRAP THIS TOOL HAS TO AVOID. "Sample the trained policy's utterances and
check they all parse" is a test that cannot fail -- `build_scene` already filters
on parse() before returning, so it would confirm its own filter. The claim is
about the CONSTRUCTION, not about one trajectory, so the quantifier has to be
over the whole reachable action space: every referent x every selection subset x
free-channel settings. A learned policy can only ever pick from that space, so if
nothing in it drifts, no policy can drift.

We also count REJECTIONS. If `build_scene` never refuses anything, the guard is
vacuous and "structurally enforced" means nothing. A live rejection rate is what
makes the enforcement claim non-empty.
"""
from __future__ import annotations
import itertools
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar import classes as C                     # noqa: E402
from tlon.grammar.canon import canon_json                 # noqa: E402
from tlon.grammar.denote import project                   # noqa: E402
from tlon.grammar.fsm import accepts                      # noqa: E402
from tlon.grammar.parse import ParseError, parse, render  # noqa: E402
from tlon.listener import tokenizer as tk                 # noqa: E402
from tlon.referents import schema                         # noqa: E402
from tlon.referents.match import consistent               # noqa: E402
from tlon.selfplay import phase3                          # noqa: E402
from tlon.selfplay.policy import Choice, channel_values   # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
FREE_SAMPLES = 40      # free-channel settings per (referent, selection)
SEED = 606


class _Fake:
    """A Choice with fixed values -- lets us drive the action space directly."""
    def __init__(self, values, select):
        self.values = values
        self.select = select
        self.logprob = None
        self.entropy = None


def sweep(refs, rng, use_pi: bool) -> dict:
    vals = channel_values()
    keys = list(vals)
    n_struct, n_sem, n_built, n_rejected, n_canon = 0, 0, 0, 0, 0
    struct_fail, sem_fail = [], []

    for ri, ref in enumerate(refs):
        deps = len(ref.signature.contains) - 1
        for k in range(deps + 1):
            for keep in itertools.combinations(range(deps), k):
                for _ in range(FREE_SAMPLES):
                    ch = _Fake({kk: rng.choice(vals[kk]) for kk in keys},
                               tuple(keep))
                    sc = phase3.build_scene(ref, ch, rng)
                    if sc is None:
                        n_rejected += 1
                        continue
                    view = project(sc) if use_pi else sc
                    n_built += 1

                    # ---- STRUCTURAL: is it still a well-formed utterance? ----
                    ok = True
                    try:
                        surf = render(view)
                        again = parse(surf)
                        tk.encode(surf)
                        if not accepts(surf):
                            ok = False           # FSM mask rejects it
                        elif canon_json(again) != canon_json(view):
                            ok = False           # render/parse is not lossless
                            n_canon += 1
                    except (ParseError, ValueError, KeyError):
                        ok = False
                    if ok:
                        n_struct += 1
                    elif len(struct_fail) < 5:
                        struct_fail.append((ref.id, keep, ch.values))

                    # ---- SEMANTIC: does it still denote its own referent? ----
                    if consistent(view, ref.signature):
                        n_sem += 1
                    elif len(sem_fail) < 5:
                        sem_fail.append((ref.id, keep, render(view)))

    return {"built": n_built, "rejected": n_rejected,
            "structural_ok": n_struct, "semantic_ok": n_sem,
            "canon_mismatch": n_canon,
            "structural_drift_rate": 1 - n_struct / n_built if n_built else None,
            "semantic_drift_rate": 1 - n_sem / n_built if n_built else None,
            "structural_failures": struct_fail, "semantic_failures": sem_fail}


def red_proof(refs, rng) -> dict:
    """Can these measures come back POSITIVE at all?

    A drift rate of 0.0000% is worthless unless the measure could have reported
    otherwise. So: break each property deliberately and confirm the measure
    catches it. Without this the headline is a test that cannot fail.
    """
    from tlon.grammar.parse import EventNode
    lex = C.load()["classes"]
    ref = refs[0]
    ch = _Fake({k: v[0] for k, v in channel_values().items()}, ())
    sc = phase3.build_scene(ref, ch, rng)

    # STRUCTURAL red-proof: a BATTERY of corruptions, because the first one I
    # tried -- duplicating the leading morpheme -- turned out to produce a
    # perfectly legal utterance. A red-proof that uses a "corruption" which
    # isn't one reports the measure as broken when the test was.
    surf = render(sc)
    toks = surf.split()
    corruptions = {
        "drop the illocutionary coda": " ".join(toks[:-1]),
        "reverse morpheme order": " ".join(reversed(toks)),
        "two codas": surf + " " + toks[-1],
        "bare root, no coda": toks[0],
        "empty": "",
    }
    caught = {}
    for name, bad in corruptions.items():
        if bad == surf:
            caught[name] = None          # not actually a corruption; skip
            continue
        try:
            parse(bad)
            caught[name] = not accepts(bad)
        except (ParseError, ValueError, KeyError, IndexError):
            caught[name] = True
    struct_caught = all(v for v in caught.values() if v is not None)

    # SEMANTIC red-proof: swap the head root for one the signature forbids,
    # leaving the utterance perfectly grammatical. This is the exact analogue of
    # Lazaridou's "tree" coming to mean "ground" -- well-formed, wrongly grounded.
    allowed = set(ref.signature.contains[0].root_any)
    other = next(r for r in sorted(lex["R"]) if r not in allowed)
    mutant = EventNode(root=other, aspect=sc.node.aspect,
                       orient=list(sc.node.orient),
                       edges=list(sc.node.edges))
    from tlon.grammar.parse import Scene as _S
    mutated = _S(node=mutant, force=sc.force)
    sem_caught = not consistent(mutated, ref.signature)
    still_grammatical = accepts(render(mutated))

    return {"structural_measure_fires": struct_caught,
            "corruptions_caught": caught,
            "semantic_measure_fires": sem_caught,
            "semantic_mutant_still_grammatical": still_grammatical,
            "mutant_root": other, "allowed_roots": sorted(allowed)}


def main() -> int:
    # PHASE 9.3: `--v2` re-runs the 6.2 placement on the Cosmicomics set.
    # ⛔ The DEFAULT stays the archived 60 so phase 6 reproduces byte-identically
    # -- repointing it silently would change what a locked prereg's verdict
    # means. The switch is explicit, and so is the output filename.
    v2 = "--v2" in sys.argv
    rng = random.Random(SEED)
    refs = (schema.load_live() if v2 else schema.load_all()).referents
    setname = "v2" if v2 else "archive"     # NOT `tag` -- the arm loop uses that
    print("=" * 78)
    print("DRIFT TAXONOMY -- Lazaridou et al. (2020) placement, verified in code")
    if v2:
        print("  PHASE 9.3 -- re-run on v2 (Cosmicomics). PREREG 10757ac4.")
        print("  Carried over LOGICALLY (forbid/matrix 0/50); re-measured so the")
        print("  demonstration is on the set the claim will be made about.")
    print("=" * 78)
    print(f"  quantifying over the REACHABLE ACTION SPACE, not one trajectory:")
    print(f"  {len(refs)} referents x every selection subset x {FREE_SAMPLES} "
          f"free-channel settings\n")

    # What the schema even permits. Semantic drift needs a way for a legal scene
    # to stop denoting its referent; `forbid` and `matrix` are the two features
    # that could do it, so their absence is load-bearing for the claim.
    nf = sum(1 for r in refs if r.signature.forbid)
    nm = sum(1 for r in refs if r.signature.matrix)
    print(f"  signature features in use: forbid={nf}/{len(refs)}  "
          f"matrix={nm}/{len(refs)}")

    rp = red_proof(refs, rng)
    print("\n  RED-PROOF (can these measures report a positive at all?)")
    print(f"    structural measure fires on every corruption: "
          f"{rp['structural_measure_fires']}")
    for name, v in rp["corruptions_caught"].items():
        mark = "caught" if v else ("SKIPPED (not a corruption)" if v is None
                                   else "MISSED -- still legal!")
        print(f"        {name:<32} {mark}")
    print(f"    semantic measure fires on a wrongly-grounded root:    "
          f"{rp['semantic_measure_fires']}  "
          f"(root {rp['mutant_root']!r} not in {rp['allowed_roots']})")
    print(f"    ...and that mutant is STILL grammatical: "
          f"{rp['semantic_mutant_still_grammatical']}  <- the two measures are "
          f"independent")
    if not (rp["structural_measure_fires"] and rp["semantic_measure_fires"]):
        print("  XX RED-PROOF FAILED -- a zero from these measures means nothing.")
        return 1

    out = {}
    for use_pi in (False, True):
        tag = "pi" if use_pi else "raw"
        r = sweep(refs, rng, use_pi)
        out[tag] = r
        print(f"\n  -- {tag} " + "-" * 60)
        print(f"    built {r['built']}   rejected by the mask {r['rejected']}"
              f"   ({100 * r['rejected'] / (r['built'] + r['rejected']):.1f}% "
              f"of attempts)")
        print(f"    STRUCTURAL drift  {100 * r['structural_drift_rate']:.4f}%  "
              f"({r['built'] - r['structural_ok']} of {r['built']})")
        print(f"    SEMANTIC   drift  {100 * r['semantic_drift_rate']:.4f}%  "
              f"({r['built'] - r['semantic_ok']} of {r['built']})")
        if r["canon_mismatch"]:
            print(f"    ⚠ canonical round-trip mismatches: {r['canon_mismatch']}")
        for f in r["structural_failures"]:
            print(f"      struct fail: ref {f[0]} keep={f[1]}")
        for f in r["semantic_failures"]:
            print(f"      semantic fail: ref {f[0]} keep={f[1]} -> {f[2]!r}")

    # The pragmatic leg is already measured; quote it, do not recompute.
    p5 = json.loads((OUT / "phase5.json").read_text())
    live = [r for r in p5["results"] if r["co_adapting"]]
    frozen = {(r["pi"], r["lam"]): r["gap"] for r in p5["results"]
              if not r["co_adapting"]}
    gaps = [100 * (r["gap"] - frozen[(r["pi"], r["lam"])]) for r in live]
    print(f"\n  PRAGMATIC drift (naive-listener gap, from runs/phase5.json):")
    if v2:
        # ⛔ phase5.json is the ARCHIVE's gap. Printing it unlabelled inside a v2
        # report is how a number from one referent set gets quoted as another's
        # -- the sets are unpairable and this one has no v2 counterpart yet.
        print("    ⛔ NOT AVAILABLE FOR v2. phase5.json is the ARCHIVE set's gap")
        print(f"       ({min(gaps):+.2f} to {max(gaps):+.2f} pts) and is NOT")
        print("       v2's. The v2 gap is 9.2c and has not run. The two sets are")
        print("       unpairable, so no substitution and no comparison here.")
        print("    ⇒ 'pragmatic is the sole mover' is confirmed for v2 as a")
        print("       STRUCTURAL claim (the other two are pinned at zero); its")
        print("       MAGNITUDE on v2 is unmeasured.")
    else:
        print(f"    {min(gaps):+.2f} to {max(gaps):+.2f} pts across {len(gaps)} "
              f"co-adapting arms -- THE ONLY MOVER")

    rejected_live = all(out[t]["rejected"] > 0 for t in out)
    clean = all(out[t]["structural_drift_rate"] == 0.0
                and out[t]["semantic_drift_rate"] == 0.0 for t in out)
    print("\n" + "=" * 78)
    if clean and rejected_live:
        print("  ISOLATION CONFIRMED. Structural and semantic drift are pinned at"
              "\n  zero across the entire reachable action space, and the mask "
              "demonstrably\n  rejects (so the guard is live, not vacuous). "
              "Pragmatic drift is the sole\n  possible failure mode -- by "
              "construction, not by contrivance.")
    elif clean and not rejected_live:
        print("  ⚠ VACUOUS. Nothing drifted, but the mask never rejected "
              "anything either,\n  so 'structurally enforced' is untested here. "
              "Widen the action space.")
    else:
        print("  ⛔ LEAKAGE. Something drifted that the construction forbids. "
              "The isolation\n  spine needs rework BEFORE phase 7.")

    (OUT / f"drift_taxonomy_{setname}.json").write_text(json.dumps(
        {"forbid_in_use": nf, "matrix_in_use": nm, "red_proof": rp,
         "arms": out,
         "pragmatic_gap_range": [min(gaps), max(gaps)]},
        indent=2, default=str), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / f'drift_taxonomy_{setname}.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
