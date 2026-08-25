"""The Bayes-ceiling gate. PHASE 13.2 re-run, Fix 2 — the replacement for the
consistency check D16 invalidated.

⛔ WHAT THESE MUST CERTIFY. The gate exists to stop `metric x head ~= 0` being
read as "a metric residue is not conventionable" when the head emitted a policy
that cannot express the distinction at all. So it has to fire on BOTH ways a
policy can carry no signal, and it has to stay quiet on a policy that does:

  1. COLLAPSE  — every mate on one code (the observed 13.2 failure, 1/24 codes)
  2. UNIFORM   — the over-entropy vacuity Fix 1 could induce
  3. SEPARATED — a real code must PASS, or the gate blocks the experiment

⭐ (2) is the one an argmax-based diversity count would miss, and it is the
named risk of raising the entropy coefficient. If this file only tested (1) and
(3), the gate would look healthy while being blind to the failure mode the fix
it guards is most likely to cause.
"""
from __future__ import annotations

import pytest
import torch

from tlon.harness.ceiling import bayes_ceiling, cluster_ceiling, readable
from tlon.selfplay.policy import ChannelPolicy

GROUPS = [[0, 1, 2], [3, 4, 5]]


def policy_with(logit_fn, n=6) -> ChannelPolicy:
    pol = ChannelPolicy(n)
    with torch.no_grad():
        for ch in pol.logits:
            logit_fn(pol.logits[ch])
    return pol


def test_a_uniform_policy_sits_exactly_at_the_floor():
    """⛔ THE OVER-ENTROPY CASE. All logits zero => every mate has an IDENTICAL
    distribution, so no listener can separate them however clever it is."""
    pol = ChannelPolicy(6)                       # zeros == uniform
    c = bayes_ceiling(pol, GROUPS)
    assert c["ceiling"] == pytest.approx(1 / 3, abs=1e-9)
    assert c["floor"] == pytest.approx(1 / 3, abs=1e-9)
    assert c["headroom_pts"] == pytest.approx(0.0, abs=1e-7)


def test_a_collapsed_policy_also_sits_at_the_floor():
    """The observed 13.2 failure: every referent driven to the SAME code."""
    pol = policy_with(lambda w: w.zero_().__setitem__((slice(None), 0), 20.0))
    c = bayes_ceiling(pol, GROUPS)
    assert c["ceiling"] == pytest.approx(1 / 3, abs=1e-6)
    assert c["headroom_pts"] == pytest.approx(0.0, abs=1e-4)


def test_a_fully_separated_policy_reaches_one():
    """Each mate deterministically on its own coda value."""
    pol = ChannelPolicy(6)
    with torch.no_grad():
        for r in range(6):
            pol.logits["coda"][r, r % 3] = 30.0
    c = bayes_ceiling(pol, GROUPS)
    assert c["ceiling"] == pytest.approx(1.0, abs=1e-6)
    assert c["headroom_pts"] > 60.0


def test_partial_separation_gives_the_exact_two_thirds():
    """⭐ The arithmetic, checked against a hand-computed value rather than a
    range: two mates share a code, one is distinct => (1 + 1/2 + 1/2)/3 = 2/3."""
    pol = ChannelPolicy(3)
    with torch.no_grad():
        pol.logits["coda"][0, 0] = 30.0
        pol.logits["coda"][1, 1] = 30.0
        pol.logits["coda"][2, 1] = 30.0
    assert cluster_ceiling(pol, [0, 1, 2]) == pytest.approx(2 / 3, abs=1e-6)


def test_the_gate_fires_on_collapse_and_on_uniform_and_passes_a_real_code():
    mde = 2.96
    assert not readable(bayes_ceiling(ChannelPolicy(6), GROUPS), mde)[0]
    collapsed = policy_with(
        lambda w: w.zero_().__setitem__((slice(None), 0), 20.0))
    assert not readable(bayes_ceiling(collapsed, GROUPS), mde)[0]
    good = ChannelPolicy(6)
    with torch.no_grad():
        for r in range(6):
            good.logits["coda"][r, r % 3] = 30.0
    ok, why = readable(bayes_ceiling(good, GROUPS), mde)
    assert ok, why


def test_the_refusal_message_says_uninformative_not_null():
    """⛔ The whole point of the gate is that a blocked cell is NOT a null."""
    ok, why = readable(bayes_ceiling(ChannelPolicy(6), GROUPS), 2.96)
    assert not ok
    assert "uninformative" in why and "Not a null" in why


def test_it_reads_the_HEAD_parameterisation_too():
    """⛔ D16's failure was an invariant that assumed a parameterisation. This
    one must work on the head without knowing anything about the trunk."""
    coords = [(0, 0, 0), (1, 1, 1), (4, 4, 4), (0, 4, 0), (4, 0, 4), (2, 2, 2)]
    pol = ChannelPolicy(6, residues=coords)
    c = bayes_ceiling(pol, GROUPS)          # zero-init head == uniform
    assert c["ceiling"] == pytest.approx(1 / 3, abs=1e-9)


def test_the_joint_is_a_probability_distribution():
    """Guards the kron construction: if it stopped normalising, every ceiling
    above would be silently wrong and still look plausible."""
    from tlon.harness.ceiling import joint_over_codes
    pol = ChannelPolicy(4)
    with torch.no_grad():
        pol.logits["orient"][2, 5] = 3.0
    j = joint_over_codes(pol, 2)
    assert float(j.sum()) == pytest.approx(1.0, abs=1e-9)
    n = 1
    for v in pol.vals.values():
        n *= len(v)
    assert j.numel() == n == 24500


# ── Fix 3 (D17): the classifier must NAME every outcome, incl. the unexpected ──
def _pol(setup, n=6, coords=None):
    p = ChannelPolicy(n, residues=coords)
    with torch.no_grad():
        setup(p)
    return p


def test_classifier_names_total_collapse():
    from tlon.harness.ceiling import classify_policy

    def s(p):
        for ch in p.logits:
            p.logits[ch].zero_()
            p.logits[ch][:, 0] = 20.0
    v, _ = classify_policy(_pol(s), GROUPS, 2.96)
    assert v == "TOTAL COLLAPSE", v


def test_classifier_names_the_over_entropy_case_argmax_would_miss():
    """⛔ THE ONE A DIVERSITY COUNT GETS WRONG. Tiny logit differences give a
    VARIED argmax while the distributions almost completely overlap."""
    from tlon.harness.ceiling import classify_policy

    def s(p):
        for r in range(6):
            p.logits["coda"][r, r % 3] = 1e-3
    v, why = classify_policy(_pol(s), GROUPS, 2.96)
    assert v == "DIVERSE ARGMAX, NO SIGNAL", (v, why)


def test_classifier_names_full_separation():
    from tlon.harness.ceiling import classify_policy

    def s(p):
        for r in range(6):
            p.logits["coda"][r, r % 3] = 30.0
    v, _ = classify_policy(_pol(s), GROUPS, 2.96)
    assert v == "FULLY SEPARATED", v


def test_classifier_names_partial_collapse():
    from tlon.harness.ceiling import classify_policy

    def s(p):                       # cluster 0 separated, cluster 1 collapsed
        for r in (0, 1, 2):
            p.logits["coda"][r, r] = 30.0
        for r in (3, 4, 5):
            p.logits["coda"][r, 0] = 30.0
    v, _ = classify_policy(_pol(s), GROUPS, 2.96)
    assert v == "PARTIAL COLLAPSE", v


def test_the_default_branch_is_a_reportable_verdict_not_a_crash():
    """⭐ D17's lesson: the outcome nobody enumerated must still come back with
    a name. Whatever a policy does, classify_policy returns a string."""
    from tlon.harness.ceiling import classify_policy
    import random as _r
    rng = _r.Random(0)
    for _ in range(12):
        def s(p):
            for ch in p.logits:
                p.logits[ch].uniform_(-rng.random() * 8, rng.random() * 8)
        v, why = classify_policy(_pol(s), GROUPS, 2.96)
        assert isinstance(v, str) and why
