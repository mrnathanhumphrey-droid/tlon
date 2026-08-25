"""⛔ DIAGNOSIS — why categorical x head did NOT land on categorical x table.

PREREG 4ad552d4's internal consistency check FAILED: -30.60 pts, Welch t -7.94.
The locked rule says the metric cells are UNREADABLE until this is understood,
so this file asks why, and it asks with measurements rather than an argument.

THE PREDICTION THAT FAILED, IN MY OWN WORDS:
    "one-hot into a linear layer IS a row lookup, so the residue-conditioned
     HEAD degenerates to exactly the per-referent TABLE on this arm."

⛔ THAT IS TRUE OF A SINGLE LINEAR LAYER AND THE HEAD IS NOT ONE. The trunk is
    one_hot -> Linear(d,32) -> Tanh -> Linear(32,32) -> Tanh -> Linear(32,|vals|)
A one-hot input does select a row of the FIRST weight matrix -- but that row is
a 32-dim EMBEDDING, not an output. Everything above it (the second trunk layer
and every channel head) is SHARED ACROSS ALL 24 REFERENTS. So the arm has a
per-referent embedding passed through a shared nonlinear map, which is not a
free per-referent output and cannot be assumed to reach the same place a table
reaches.

⭐ AND THE TWO DESIGN GOALS WERE IN TENSION AND I DID NOT NOTICE. The trunk was
made an MLP *on purpose* so the falsifying cell stayed reachable (a linear trunk
could not memorise an arbitrary code, which would have made the 2x2
self-confirming). That same depth is what breaks the "one-hot == table"
equivalence the consistency check assumed. Both requirements were written into
the prereg; they cannot both hold.

TWO QUESTIONS, MEASURED:
  Q1  CAPACITY or OPTIMISATION? Can the head fit an ARBITRARY code at the real
      scale (24 referents x 5 channels) in the real step budget? The existing
      unit test used 4 referents, 1 channel -- a scale at which the answer can
      be yes while it is no here.
  Q2  Does the metric arm's SMOOTHNESS prevent separation? If nearby residues
      are forced toward nearby codes, then cluster-mates that sit close in the
      lattice cannot be given distinguishable codes -- which would make the
      inductive bias that was supposed to CREATE conventionability the very
      thing that blocks it.
"""
from __future__ import annotations

import pathlib
import random
import statistics as S
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

import torch                                                     # noqa: E402

from tlon.grammar import residue as R                            # noqa: E402
from tlon.listener.model import Listener                         # noqa: E402
from tlon.referents import schema                                # noqa: E402
from tlon.selfplay import phase3                                 # noqa: E402
from tlon.selfplay.policy import ChannelPolicy                   # noqa: E402
from run_13_2 import residues_of, clusters_of                    # noqa: E402

STEPS = 4000


def q1_capacity() -> None:
    """Fit an arbitrary per-referent code at the REAL scale, supervised."""
    print("\n── Q1  can the head hold an arbitrary code at the real scale? ──")
    for arm in ("random", "lyric"):
        refs = schema.load_residue_arm(arm).referents
        coords = residues_of(refs)
        torch.manual_seed(0)
        pol = ChannelPolicy(len(refs), residues=coords)
        opt = torch.optim.Adam(pol.parameters(), lr=0.05)
        rng = random.Random(0)
        # a deliberately arbitrary target: one value per (referent, channel)
        tgt = {ch: torch.tensor([rng.randrange(len(v)) for _ in refs])
               for ch, v in pol.vals.items()}
        for _ in range(STEPS):
            loss = sum(torch.nn.functional.cross_entropy(
                pol.logit_matrix(ch), tgt[ch]) for ch in pol.vals)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
        hit = {ch: float((pol.logit_matrix(ch).argmax(-1) == tgt[ch]).float().mean())
               for ch in pol.vals}
        overall = S.fmean(hit.values())
        print(f"    {arm:<8} arbitrary-code fit after {STEPS} supervised steps: "
              f"{100*overall:5.1f}%   "
              + " ".join(f"{ch[:6]}={100*v:.0f}%" for ch, v in hit.items()))
    print("    (the TABLE reaches 100% trivially — every logit is independent)")


def q2_smoothness() -> None:
    """Train one real seed per arm and ask what code each referent ended with."""
    print("\n── Q2  does smoothness stop the head separating nearby residues? ──")
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    for arm in ("lyric", "random"):
        refs = schema.load_residue_arm(arm).referents
        coords = residues_of(refs)
        _, groups = clusters_of(refs)
        torch.manual_seed(11)
        pol = ChannelPolicy(len(refs), residues=coords).to(dev)
        L = Listener(len(refs)).to(dev)
        phase3.run(refs, L, phase3.P3Cfg(lam=0.0, device=dev, project=True,
                                         steps=STEPS, seed=11,
                                         normalize_advantage=True),
                   verbose=False, policy=pol)
        with torch.no_grad():
            code = {ch: pol.logit_matrix(ch).argmax(-1).cpu().tolist()
                    for ch in pol.vals}
        words = [tuple(code[ch][i] for ch in sorted(pol.vals))
                 for i in range(len(refs))]
        distinct = len(set(words))
        # within-cluster: do the three mates get DIFFERENT codes?
        sep = [len({words[i] for i in g}) for g in groups]
        # relate code-identity to residue distance
        same_pairs, diff_pairs = [], []
        for i in range(len(refs)):
            for j in range(i + 1, len(refs)):
                d = R.normalized(coords[i], coords[j], span=4)
                (same_pairs if words[i] == words[j] else diff_pairs).append(d)
        conc = pol.concentration()
        print(f"    {arm:<8} distinct codes {distinct}/{len(refs)}   "
              f"mates separated per cluster {sep}")
        print(f"    {'':<8} concentration " + " ".join(
            f"{ch[:6]}={v:.2f}" for ch, v in sorted(conc.items())))
        # ⛔ THREE BRANCHES, and the FIRST one is why this crashed on its first
        # run: I wrote the "some collide" and "none collide" cases and not the
        # TOTAL COLLAPSE case, so `diff_pairs` was empty and fmean raised. A
        # verdict can only report outcomes it was written to recognise -- and
        # total collapse is the outcome that actually happened.
        if distinct == 1:
            print(f"    {'':<8} ⛔⛔ TOTAL COLLAPSE — every referent converged to "
                  "ONE code. The listener has\n              nothing to read, so "
                  "the gap is ~0 for a reason that is about the OPTIMISER, "
                  "not\n              about whether a metric residue is "
                  "conventionable.")
        elif same_pairs and diff_pairs:
            ms, md = S.fmean(same_pairs), S.fmean(diff_pairs)
            print(f"    {'':<8} colliding pairs {len(same_pairs)} (mean residue "
                  f"distance {ms:.3f})  |  separated {len(diff_pairs)} "
                  f"(mean {md:.3f})")
            if ms < md:
                print(f"    {'':<8} ⇒ colliding pairs are CLOSER in the lattice: "
                      "smoothness is merging nearby residues.")
        else:
            print(f"    {'':<8} no colliding pairs — every referent got its own "
                  "code.")


def main() -> int:
    print("=" * 78)
    print("13.2 — WHY THE CONSISTENCY CHECK FAILED. Metric cells stay UNREAD.")
    print("=" * 78)
    q1_capacity()
    q2_smoothness()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
