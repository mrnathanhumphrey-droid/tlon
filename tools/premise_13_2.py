"""PREMISE CHECKS for 13.2, run BEFORE the arms are authored and the prereg locks.

⛔ WHY THIS FILE EXISTS. 13.0 built the residue at the GRAMMAR/METRIC layer and
red-proofed it there. 13.2 runs it through the TRAINING LOOP, which is a
different set of objects (`build_scene`, `ChannelPolicy`, the listener). None of
13.0's red-proofs touch those. So before authoring the arms, ask the loop the
question the scope assumes the answer to:

    WHERE, IN THE PHASE-3 LOOP, CAN THE RESIDUE'S METRIC STRUCTURE ENTER?

The metric-vs-categorical contrast is only meaningful if the answer is "somewhere
that matters". If neither agent's parameterisation is organised by residue
distance, `metric` and `categorical` are the same experiment run twice and the
contrast reads as a null that was architectural, never about ineffability.

Static only. Draws no gradient, runs no training, spends nothing.
"""
from __future__ import annotations

import pathlib
import sys

# Windows consoles default to cp1252 and this file's report is full of the
# project's ⛔/⭐ markers. Reconfigure rather than ASCII-ify: a report that
# silently loses its severity markers is a report nobody reads twice.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import random                                                    # noqa: E402

import torch                                                     # noqa: E402

from tlon.grammar.parse import render                            # noqa: E402
from tlon.novelty import distance as D                           # noqa: E402
from tlon.referents.schema import Referent, Signature            # noqa: E402
from tlon.selfplay.policy import FREE, ChannelPolicy, channel_values  # noqa: E402
from tlon.selfplay.phase3 import build_scene                     # noqa: E402

FAIL: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'ok ' if ok else 'FLAG'}] {label}" + (f"\n         {detail}" if detail else ""))
    if not ok:
        FAIL.append(label)


def cluster() -> tuple[Referent, Referent]:
    """Two referents identical on every EXPRESSIBLE part, differing ONLY in
    residue. This is the construction the whole lever rests on."""
    def mk(rid: str, coord: list[int]) -> Referent:
        sig = Signature.parse({"contains": [
            {"root_any": ["mlö"], "residue_any": [coord]},
            {"root_any": ["fox"]}]})
        return Referent(id=rid, name=f"cluster mate {rid}", tier=1, signature=sig)
    return mk("X01", [0, 0]), mk("X02", [3, 3])


def main() -> int:
    a, b = cluster()
    vals = channel_values()
    space = 1
    for ch in FREE:
        space *= len(vals[ch])

    print("\n── P1  the free channel is the ONLY carrier, and how wide is it ──")
    check("two cluster-mates have byte-identical EXPRESSIBLE signatures",
          tuple(p.root_any for p in a.signature.contains)
          == tuple(p.root_any for p in b.signature.contains))
    check(f"free-channel code space = {space:,} distinct codes per referent",
          True, " · ".join(f"{ch}={len(vals[ch])}" for ch in FREE))
    check("an EXACT arbitrary code therefore exists in BOTH arms "
          "(no capacity pressure at any realistic cluster size)", True,
          f"{space:,} codes ≫ cluster size; so metric-vs-categorical is NOT an "
          "existence contrast — both codes are equally realisable.")

    print("\n── P2  can the SPEAKER's parameterisation see residue distance? ──")
    pol = ChannelPolicy(n_refs=2)
    shapes = {ch: tuple(p.shape) for ch, p in pol.logits.items()}
    check("ChannelPolicy is a per-referent lookup table, indexed by ref_idx only",
          all(s[0] == 2 for s in shapes.values()),
          f"logit shapes {shapes} — one INDEPENDENT row per referent, "
          "nothing shared. Its own docstring: 'nothing forcing generalisation'.")
    check("no policy parameter is a function of the residue coordinate",
          not any("residue" in n for n, _ in pol.named_parameters()),
          "⇒ a graded residue and an arbitrary one cost the speaker exactly the "
          "same. Metric structure buys the SPEAKER nothing, BY CONSTRUCTION.")

    print("\n── P3  can the LISTENER see residue distance? ──")
    rng = random.Random(0)
    pol2 = ChannelPolicy(n_refs=2)
    torch.manual_seed(0)
    ch_a = pol2(0)
    sa = build_scene(a, ch_a, random.Random(7))
    sb = build_scene(b, ch_a, random.Random(7))
    check("under the SAME channel choice, cluster-mates render byte-identically",
          sa is not None and sb is not None and render(sa) == render(sb),
          f"surface = {render(sa)!r}" if sa else "build failed")
    check("the listener's input is residue-invariant "
          "(the renders-never red-proof, restated as a loop fact)", True,
          "residue never reaches the surface ⇒ the listener never perceives "
          "residue PROXIMITY. It learns surface→ref-index, an arbitrary map.")

    print("\n── P4  ⛔ THE BUILD GAP: does the loop emit a residue at all? ──")
    # ⛔ Both branches spelled out. A detail line that only describes the
    # failure reads as an accusation next to an [ok ], and a reader skimming
    # for markers would carry away the wrong state.
    got = sa.node.residue if sa is not None else "<build failed>"
    check("build_scene sets scene.residue from pat.residue_any",
          sa is not None and sa.node.residue is not None,
          f"scene.node.residue = {got!r} — reads pat.residue_any, drawing only "
          "when there is more than one coordinate to choose between."
          if sa is not None and sa.node.residue is not None else
          f"scene.node.residue = {got!r} — `node()` constructs "
          "EventNode(root=…, orient=…) and never reads pat.residue_any, so "
          "every generated scene is residue-free and W_RESIDUE is inert.")
    if sa is not None and sb is not None:
        nd = D.normalized(sa, sb)
        check("R therefore sees a residue difference between cluster-mates",
              nd > 0.0,
              f"D.normalized = {nd:.4f} > 0 — 13.0's landmine fix is now "
              "reached by an actual run, so cluster-mates are two medoids."
              if nd > 0.0 else
              f"D.normalized = {nd:.4f} — the W_RESIDUE term is INERT in the "
              "loop, so 13.0's landmine fix is not reached by a single run.")

    print("\n── P6  the steelman: could gradedness help on HELD-OUT residues? ──")
    fresh = ChannelPolicy(n_refs=3)
    untrained_is_uniform = all(
        bool(torch.all(p[2] == 0.0)) for p in fresh.logits.values())
    check("a referent the pair never co-adapted on has an ALL-ZERO policy row",
          untrained_is_uniform,
          "⇒ the speaker emits a uniform-random code for it. A lookup table "
          "cannot INTERPOLATE between rows, so it cannot gesture at an unseen "
          "residue 'like its neighbours' whether the space is graded or not.")
    check("⛔ held-out generalisation cannot rescue the contrast either — "
          "ADDRESSED BY THE 2×2", True,
          "The Pictionary property — 'nearby residues get gestured at "
          "similarly' — is a GENERALISATION claim, and generalisation is "
          "structurally unavailable to a per-referent TABLE. That is why "
          "PREREG 4ad552d4 adds the residue-conditioned HEAD and runs both "
          "parameterisations: the architectural claim becomes a measured "
          "result instead of an assumption. The statement above remains TRUE "
          "of the table arm, which is the 2×2's control cell.")

    print("\n── P7  is Part 2's CORE measurement non-vacuous? (the good news) ──")

    # ⛔ THE FIRST VERSION OF THIS CHECK WAS FAKE. It re-seeded torch and the
    # rng IDENTICALLY for both cluster-mates, so the two runs drew the SAME
    # channel sequence and total variation was 0.0000 BY CONSTRUCTION -- a
    # statistic that could not have come back positive. Two fixes: sample the
    # arms INDEPENDENTLY, and score a DENSE statistic (the coda x aspect_reps
    # joint, 20 cells) instead of the raw surface, which was 1,987 distinct
    # strings in 2,000 draws and so estimated nothing.
    def joint(ref, seed: int, n: int = 4000) -> dict[tuple, int]:
        pol3 = ChannelPolicy(n_refs=2)
        torch.manual_seed(seed)
        r = random.Random(seed)
        out: dict[tuple, int] = {}
        for _ in range(n):
            ch = pol3(0)
            if build_scene(ref, ch, r) is None:
                continue
            k = (ch.values["coda"], ch.values["aspect_reps"])
            out[k] = out.get(k, 0) + 1
        return out

    def tvd(p: dict, q: dict) -> float:
        np_, nq = sum(p.values()), sum(q.values())
        return 0.5 * sum(abs(p.get(k, 0) / np_ - q.get(k, 0) / nq)
                         for k in set(p) | set(q))

    ja, jb = joint(a, 101), joint(b, 202)          # INDEPENDENT seeds
    tv = tvd(ja, jb)
    bayes = 0.5 * (1.0 + tv)
    check("at policy init, cluster-mates induce the SAME surface distribution",
          tv < 0.05,
          f"total variation = {tv:.4f} over {len(set(ja) | set(jb))} dense "
          f"cells, independently sampled ⇒ the Bayes-optimal listener is "
          f"capped at {100*bayes:.1f}% within the cluster. NO listener, "
          "however good, can beat that without a code.")

    # RED-PROOF the estimator: give one mate a real code and it must SEE it.
    pol4 = ChannelPolicy(n_refs=2)
    with torch.no_grad():
        pol4.logits["coda"][0, 0] = 8.0            # referent A: always coda #0

    def joint_coded(seed: int, n: int = 4000) -> dict[tuple, int]:
        torch.manual_seed(seed)
        r = random.Random(seed)
        out: dict[tuple, int] = {}
        for _ in range(n):
            ch = pol4(0)
            if build_scene(a, ch, r) is None:
                continue
            k = (ch.values["coda"], ch.values["aspect_reps"])
            out[k] = out.get(k, 0) + 1
        return out

    tv_coded = tvd(joint_coded(303), jb)
    check("RED-PROOF: the same statistic DETECTS a planted code",
          tv_coded > 0.5,
          f"plant 'referent A always takes coda #0' and total variation goes "
          f"{tv:.4f} → {tv_coded:.4f}. The estimator can come back positive, "
          "so the ≈0 above is a measurement and not an artefact of seeding.")
    print(f"""    ⭐⭐ THAT IS THE FIRST NON-VACUOUS M IN THE PROJECT. phase3.py's own
    note: "accuracy saturates at 100% immediately -- the signature core already
    determines the referent -- and a constant term has zero gradient, so the
    gate was never actually under test." Inside a residue cluster the signature
    core does NOT determine the referent, so the free channel has to carry real
    information for the first time. Part 2's core question — does a pact form
    around an INEXPRESSIBLE distinction — is sound, and worth running.""")

    print("\n── P5  so where CAN the metric enter the loop? ──")
    print("""    speaker policy ...... NO  (lookup table on ref_idx; P2)
    listener input ...... NO  (surface is residue-invariant; P3)
    M / the reward's  ... NO  (M = probs[ri], hard identity, no partial credit
      comprehension term       for a near-miss residue)
    R / novelty ......... YES (W_RESIDUE * residue.normalized, once P4 is fixed)

    ⇒ ⛔⛔ ON TRAINED CLUSTER MATES THE METRIC ENTERS THROUGH R AND NOWHERE
    ELSE. R is a NOVELTY-PRESSURE term, not a conventionability one, so a
    metric-vs-random difference measured this way is attributable to the arms
    having different reward landscapes — a confound, not the mechanism.""")

    print("\n" + "=" * 72)
    if FAIL:
        print(f"⛔ {len(FAIL)} PREMISE(S) FLAGGED — 13.2 cannot run as-is:")
        for f in FAIL:
            print(f"     · {f}")
    else:
        print("""all premises hold, AND THE P5 FINDING IS NOT 'RESOLVED' — IT IS
  DESIGNED AROUND. The metric still cannot reach a per-referent TABLE; PREREG
  4ad552d4 makes that the control cell and adds the residue-conditioned HEAD
  as the treatment, with lambda=0 closing R's confound route by construction.
  ⛔ Whether the head USES the metric is the open empirical question, and the
  cell where it does not is allowed to win.""")
    print("=" * 72)
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
