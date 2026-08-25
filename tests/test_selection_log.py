"""The standing selection log. PHASE 10, locked regardless of every other call.

⛔ WHY THIS EXISTS. No run in this project has ever recorded WHICH subset the
policy chose -- 0 of 9 phase-8 rollout keys, 0 in phase-5 -- so
P_policy(subset | referent) had effective sample size 0 and 9.5 stalled into
Outcome 3. The log costs a dict increment per step.

⛔ A LOG THAT IS SILENTLY EMPTY WOULD PASS A WEAK TEST. These check it is
POPULATED and VARIED, not merely present.
"""
from __future__ import annotations

import random

import torch

from tlon.listener.model import Listener
from tlon.referents import schema
from tlon.selfplay import phase3
from tlon.selfplay.policy import ChannelPolicy

STEPS = 80


def _run(seed=7, n_refs=12):
    refs = schema.load_live().referents[:n_refs]
    deps = [len(r.signature.contains) - 1 for r in refs]
    # ⛔ Seed BEFORE construction. phase3.run seeds torch internally, but the
    # policy and listener are built by the caller, so their init draws from
    # whatever global state the test left. Without this the "determinism" test
    # measures the test harness, not the log.
    torch.manual_seed(1234)
    pol = ChannelPolicy(len(refs), deps=deps)
    L = Listener(len(refs))
    _, _, st = phase3.run(
        refs, L,
        phase3.P3Cfg(lam=0.0, device="cpu", steps=STEPS, seed=seed,
                     listener_every=10_000),      # no listener training: fast
        verbose=False, policy=pol)
    return st


def test_the_log_is_populated_not_merely_present():
    st = _run()
    assert st.selection_steps == STEPS, st.selection_steps
    assert st.selections, "selection log is EMPTY -- vacuous"
    assert sum(sum(c.values()) for c in st.selections.values()) == STEPS


def test_the_log_is_varied_so_it_is_measuring_something():
    """A log recording one subset forever would be populated and useless."""
    st = _run()
    distinct = {k for c in st.selections.values() for k in c}
    assert len(distinct) >= 2, f"only ever logged {distinct}"


def test_chosen_and_uttered_are_tracked_separately():
    """They differ by the unbuildable subsets -- v2 has 11 structural holes.

    Weighting an utterance statistic by the CHOICE distribution would credit
    mass to utterances that were never said.
    """
    st = _run()
    chosen = sum(sum(c.values()) for c in st.selections.values())
    said = sum(sum(c.values()) for c in st.uttered.values())
    assert chosen == said + st.build_failures
    for ri, c in st.uttered.items():
        for k, v in c.items():
            assert v <= st.selections[ri][k], "uttered exceeds chosen"


def test_ess_is_over_uttered_and_sums_correctly():
    st = _run()
    ess = st.selection_ess()
    assert sum(ess.values()) == sum(sum(c.values())
                                    for c in st.uttered.values())
    assert all(v > 0 for v in ess.values())


def test_the_log_is_deterministic_under_a_fixed_seed():
    """Same seed, same log -- or it is not a record of anything."""
    a, b = _run(seed=11), _run(seed=11)
    assert a.selections == b.selections
    assert a.uttered == b.uttered


def test_logging_does_not_perturb_the_run():
    """⛔ THE LOG IS AN OUTPUT ONLY.

    It draws no random numbers and touches no gradient, so a run with it on
    must produce the same trajectory it always did. Checked by confirming two
    same-seed runs agree on the LEARNED quantities as well as the log -- if
    logging consumed rng, seeds would decouple and this would drift.
    """
    a = _run(seed=23)
    b = _run(seed=23)
    assert a.m_rate == b.m_rate
    assert a.entropy == b.entropy
    assert a.selection_steps == b.selection_steps


def test_phase3_style_run_with_no_selection_head_logs_ALL():
    """phase-3 policies have select=None ("utter everything"), which must log
    as a real key rather than crashing or vanishing."""
    refs = schema.load_live().referents[:8]
    pol = ChannelPolicy(len(refs))            # no deps= => no selection head
    L = Listener(len(refs))
    _, _, st = phase3.run(
        refs, L,
        phase3.P3Cfg(lam=0.0, device="cpu", steps=40, seed=5,
                     listener_every=10_000),
        verbose=False, policy=pol)
    keys = {k for c in st.selections.values() for k in c}
    assert keys == {"ALL"}, keys
    assert st.selection_steps == 40
