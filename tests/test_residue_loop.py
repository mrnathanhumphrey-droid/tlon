"""PHASE 13.2 -- the residue in the TRAINING LOOP, which 13.0 never reached.

⛔ WHY A SECOND RESIDUE TEST FILE. `tests/test_residue.py` red-proofs the
GRAMMAR layer -- render, canon, pi, match, the metric -- and it does so by
building Scenes BY HAND. The loop builds them with `build_scene`, and that
function never read `pat.residue_any`, so every generated scene was residue-free
and `W_RESIDUE` was inert in every run. 13.0's red-proofs all passed throughout.
`tools/premise_13_2.py` is what found it.

⭐ The lesson is the repo's own: a test that cannot reach the defect is not
coverage. These tests reach it via `build_scene`, the way a run does.
"""
from __future__ import annotations

import random

import torch

from tlon.grammar.parse import render
from tlon.listener.model import Listener
from tlon.novelty import distance as D
from tlon.novelty.centroids import RepetitionLog
from tlon.referents import schema
from tlon.referents.schema import Referent, Signature
from tlon.selfplay import phase3
from tlon.selfplay.policy import Choice, ChannelPolicy


def mate(rid: str, coords: list[list[int]] | None) -> Referent:
    """A cluster-mate: identical on every EXPRESSIBLE part, residue apart."""
    head: dict = {"root_any": ["mlö"]}
    if coords is not None:
        head["residue_any"] = coords
    return Referent(id=rid, name=rid, tier=1, signature=Signature.parse(
        {"contains": [head, {"root_any": ["fox"]}]}))


def fixed_choice(select=None) -> Choice:
    """A Choice with no torch sampling, so a test can isolate build_scene."""
    return Choice(values={"aspect_root": None, "aspect_reps": 2,
                          "degree": None, "coda": "ka", "orient": None},
                  logprob=torch.zeros(()), entropy=torch.zeros(()),
                  select=select)


# ── the gap itself: the loop must actually emit a residue ─────────────────
def test_build_scene_sets_the_residue_from_the_signature():
    sc = phase3.build_scene(mate("A", [[3, 1]]), fixed_choice(), random.Random(0))
    assert sc is not None and sc.node.residue == (3, 1)


def test_a_residue_free_referent_still_gets_none():
    sc = phase3.build_scene(mate("A", None), fixed_choice(), random.Random(0))
    assert sc is not None and sc.node.residue is None


def test_cluster_mates_render_identically_but_are_two_medoids():
    """⛔ THE LANDMINE, NOW VIA build_scene RATHER THAN A HAND-BUILT SCENE.

    Same surface (the residue is inexpressible) but two distinct impressions
    (the residue is denoting). If these fold to one medoid, a metric-residue arm
    behaves exactly like a no-residue arm and Part 2 reads empty for reasons
    that have nothing to do with conventionability.
    """
    a = phase3.build_scene(mate("A", [[0, 0]]), fixed_choice(), random.Random(4))
    b = phase3.build_scene(mate("B", [[3, 3]]), fixed_choice(), random.Random(4))
    assert render(a) == render(b), "the residue leaked into the surface"
    assert D.normalized(a, b) > 0.0, "W_RESIDUE is still inert in the loop"
    log = RepetitionLog()
    log.observe("cluster", a, render(a))
    log.observe("cluster", b, render(b))
    assert len(log.buckets["cluster"].medoids) == 2


# ── ⛔ the reproduction guard: phases 3-8 must not move ───────────────────
def test_a_residue_free_set_consumes_ZERO_extra_rng_draws():
    """Every phase 3-8 tool calls build_scene. An unconditional rng.choice()
    for the residue would shift the shared random stream and silently stop all
    of them reproducing byte-identically -- the same class of harm as editing a
    locked prereg body. Compared on rng STATE, not on the output, because the
    residue does not render and a surface comparison could not see the draw."""
    r_none, r_single = random.Random(5), random.Random(5)
    phase3.build_scene(mate("A", None), fixed_choice(), r_none)
    phase3.build_scene(mate("B", [[2, 2]]), fixed_choice(), r_single)
    assert r_none.getstate() == r_single.getstate(), (
        "a singleton residue_any consumed a draw; the archive would drift")


def test_but_a_MULTI_coordinate_residue_DOES_draw():
    """Red-proof for the guard above: it must be a real conditional, not a
    function that never draws at all."""
    r_none, r_multi = random.Random(5), random.Random(5)
    phase3.build_scene(mate("A", None), fixed_choice(), r_none)
    phase3.build_scene(mate("B", [[0, 0], [2, 2]]), fixed_choice(), r_multi)
    assert r_none.getstate() != r_multi.getstate()


def test_the_live_set_is_untouched_so_phase_9_still_reproduces():
    """v2 carries no residue_any at all, so not one draw changes."""
    refs = schema.load_live().referents
    assert not any(p.residue_any
                   for r in refs
                   for p in r.signature.contains), "v2 gained a residue"


# ── the third standing log ────────────────────────────────────────────────
def _run(refs, seed=7, steps=60):
    deps = [len(r.signature.contains) - 1 for r in refs]
    torch.manual_seed(1234)
    pol = ChannelPolicy(len(refs), deps=deps)
    L = Listener(len(refs))
    _, _, st = phase3.run(refs, L,
                          phase3.P3Cfg(lam=0.0, device="cpu", steps=steps,
                                       seed=seed, listener_every=10_000),
                          verbose=False, policy=pol)
    return st


def test_the_residue_log_is_populated_and_keyed_by_coordinate():
    """⛔ Part B's growth curve is a PER-TURN residue statistic. Unlogged, it
    cannot be recovered after the run and the curve does not exist -- the 9.5
    stall (effective sample size 0, not merely small) in a new dimension."""
    refs = [mate("A", [[0, 0]]), mate("B", [[3, 3]]), mate("C", [[1, 2]])]
    st = _run(refs)
    assert st.residues, "the residue log is EMPTY -- vacuous"
    coords = {c for d in st.residues.values() for c in d}
    assert coords == {(0, 0), (3, 3), (1, 2)}, coords
    assert sum(sum(d.values()) for d in st.residues.values()) == \
        sum(sum(c.values()) for c in st.uttered.values())


def test_the_residue_log_stays_empty_on_a_residue_free_set():
    """It must not invent a key for `None`, which would make every legacy run
    look residue-bearing."""
    st = _run(schema.load_live().referents[:8])
    assert st.residues == {}


def test_the_residue_log_does_not_perturb_the_run():
    """⭐ OUTPUT ONLY -- no rng, no gradient, so a fixed seed still reproduces."""
    refs = schema.load_live().referents[:8]
    a, b = _run(refs, seed=23), _run(refs, seed=23)
    assert a.m_rate == b.m_rate and a.entropy == b.entropy
    assert a.selections == b.selections
