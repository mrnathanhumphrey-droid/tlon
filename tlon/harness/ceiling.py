"""The BAYES CEILING of a trained policy. PHASE 13.2 re-run, Fix 2.

⛔⛔ WHY THIS REPLACES THE OLD CONSISTENCY CHECK.

The old check asserted `categorical x head == categorical x table`, on the
reasoning that "one-hot into a linear layer is a row lookup". That is true of a
SINGLE linear layer. The trunk is `Linear -> Tanh -> Linear -> Tanh -> Linear`,
so a one-hot selects a 32-dim EMBEDDING and everything above it is SHARED across
all referents. The check was invalid by construction (DEVIATIONS_13_2 D16) and
it fired on a design error rather than on a residue property.

WHAT THE OLD CHECK WAS FOR, AND WHAT MUST BE PRESERVED:

    it protected against reading `metric x head ~= 0` as "a metric residue is
    not conventionable" when the true cause was "this head emitted a policy that
    CANNOT express the distinction at all".

WHAT THIS MEASURES INSTEAD. Given the trained policy, compute the accuracy of a
BAYES-OPTIMAL listener that knows the policy exactly. For one cluster of k mates
with a uniform prior, observing code x, the best guess is argmax_m P_m(x), so

    ceiling = (1/k) * SUM_over_codes  max_over_mates  P_mate(code)

⭐ THIS IS EXACT, NOT ESTIMATED. The policy is a product of independent
per-channel categoricals, so the joint over the 24,500-code space is enumerated
in closed form. No sampling, no threshold chosen to taste.

⭐⭐ IT IS ALSO PARAMETERISATION-AGNOSTIC, which is precisely what D16 broke on.
It asks what the POLICY does, never how the policy is built, so it cannot become
invalid because the architecture changed.

⭐⭐⭐ AND IT GUARDS BOTH FAILURE MODES WITH ONE QUANTITY:
  * COLLAPSE (the observed failure): all mates share one code, the max is the
    only distribution, the sum is 1, ceiling = 1/k -- exactly the naive floor.
  * OVER-ENTROPY (the named risk of Fix 1): the policy goes uniform, all mates
    have the SAME distribution, the sum is again 1, ceiling = 1/k.
    ⛔ An argmax-based "count the distinct codes" statistic would MISS this --
    a near-uniform policy still has a well-defined and possibly varied argmax,
    so it would report healthy diversity for a policy carrying no signal. That
    is why the ceiling is computed from the distributions and not from argmax.
"""
from __future__ import annotations

from typing import Sequence

import torch


@torch.no_grad()
def joint_over_codes(policy, ref_idx: int) -> torch.Tensor:
    """Exact distribution over the full free-channel code space for one referent.

    The channels are sampled independently, so the joint is the outer product of
    the per-channel categoricals. Built by successive kron so it stays exact.
    """
    joint = torch.ones(1, dtype=torch.float64)
    for ch in sorted(policy.vals):
        if ch in getattr(policy, "uniform_channels", set()):
            n = len(policy.vals[ch])
            p = torch.full((n,), 1.0 / n, dtype=torch.float64)
        else:
            logits = policy.logit_matrix(ch)[ref_idx] / policy.temperature
            p = torch.softmax(logits.double().cpu(), dim=-1)
        joint = (joint[:, None] * p[None, :]).reshape(-1)
    return joint


@torch.no_grad()
def cluster_ceiling(policy, mates: Sequence[int]) -> float:
    """Bayes-optimal within-cluster accuracy for a uniform prior over `mates`."""
    if len(mates) < 2:
        return 1.0
    stack = torch.stack([joint_over_codes(policy, i) for i in mates])
    return float(stack.max(dim=0).values.sum() / len(mates))


@torch.no_grad()
def bayes_ceiling(policy, groups: Sequence[Sequence[int]]) -> dict:
    """Per-cluster and mean ceiling for a trained policy.

    `floor` is the no-information baseline (1/k averaged over clusters): what a
    listener gets by guessing when the policy tells it nothing.
    """
    per = [cluster_ceiling(policy, g) for g in groups]
    floor = sum(1.0 / max(1, len(g)) for g in groups) / len(groups)
    mean = sum(per) / len(per)
    return {"per_cluster": per, "ceiling": mean, "floor": floor,
            "headroom_pts": 100.0 * (mean - floor)}


@torch.no_grad()
def classify_policy(policy, groups: Sequence[Sequence[int]],
                    mde_pts: float) -> tuple[str, str]:
    """Name what the trained policy actually IS. PHASE 13.2 Fix 3 (D17).

    ⛔ THE LOUD FALLBACK IS WRITTEN FIRST AND EVERY BRANCH IS REACHED FROM IT.
    The previous diagnostic had branches for "some pairs collide" and "no pairs
    collide" and crashed on the outcome that actually happened -- total collapse
    -- because it was the one case nobody enumerated. So the default here is
    UNRECOGNISED and it is a real, reportable answer rather than an exception.

    ⭐ Both an argmax view (how many distinct codes) and a distribution view
    (the Bayes ceiling) are used, because they disagree in exactly the case that
    matters: a near-uniform policy has a varied ARGMAX and no signal at all.
    """
    cei = bayes_ceiling(policy, groups)
    n_refs = sum(len(g) for g in groups)
    words = []
    for i in range(n_refs):
        words.append(tuple(int(policy.logit_matrix(ch)[i].argmax())
                           for ch in sorted(policy.vals)))
    distinct = len({words[i] for g in groups for i in g})
    sep = [len({words[i] for i in g}) for g in groups]
    live = cei["headroom_pts"] > mde_pts

    verdict, why = "UNRECOGNISED", (
        f"no enumerated branch matched: {distinct}/{n_refs} distinct codes, "
        f"per-cluster separation {sep}, ceiling {100*cei['ceiling']:.1f}% vs "
        f"floor {100*cei['floor']:.1f}%. READ BY HAND.")

    if distinct == 1:
        verdict, why = "TOTAL COLLAPSE", (
            "every referent converged to ONE code; the listener has nothing to "
            "read, so any gap here is ~0 for reasons about the optimiser.")
    elif not live and distinct > 1:
        verdict, why = "DIVERSE ARGMAX, NO SIGNAL", (
            f"{distinct}/{n_refs} distinct argmax codes but headroom is only "
            f"{cei['headroom_pts']:.2f} pts -- the distributions OVERLAP, which "
            "is what an over-large entropy bonus produces. Counting distinct "
            "codes would have called this healthy.")
    elif live and all(s == len(g) for s, g in zip(sep, groups)):
        verdict, why = "FULLY SEPARATED", (
            f"every mate of every cluster has its own code; headroom "
            f"{cei['headroom_pts']:.2f} pts.")
    elif live and any(s == 1 for s in sep):
        verdict, why = "PARTIAL COLLAPSE", (
            f"{sum(1 for s in sep if s == 1)}/{len(groups)} clusters have all "
            f"mates on one code; the rest separate. Per-cluster {sep}.")
    elif live:
        verdict, why = "PARTIALLY SEPARATED", (
            f"per-cluster separation {sep}; headroom "
            f"{cei['headroom_pts']:.2f} pts, so a gap is detectable but the "
            "ceiling is below 100%.")
    return verdict, why


def readable(ceiling: dict, mde_pts: float) -> tuple[bool, str]:
    """THE GATE. A cell's residue gap is readable only if its own policy left
    enough room for a detectable gap to exist.

    ⛔ This is not a quality bar on the result -- it is a statement about whether
    the cell COULD have produced one. A cell whose ceiling sits at the floor is
    structurally incapable of showing an effect, so its ~0 says nothing about
    the residue, exactly as a `residue=None` set would say nothing.
    """
    head = ceiling["headroom_pts"]
    if head > mde_pts:
        return True, (f"headroom {head:.2f} pts > MDE {mde_pts:.2f} — the "
                      "policy left room for a detectable gap")
    return False, (
        f"headroom {head:.2f} pts <= MDE {mde_pts:.2f} — a Bayes-optimal "
        "listener that knew this policy exactly could not beat the floor by a "
        "detectable margin, so this cell CANNOT show an effect and its result "
        "is uninformative about the residue. Not a null.")
