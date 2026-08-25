"""PHASE 13.2 -- the residue-conditioned head and the two arms.

⛔ WHAT THESE HAVE TO CERTIFY, beyond "it runs":

  1. The TABLE arm is byte-for-byte what it always was, or phases 3-8 stop
     reproducing and the 2x2's control cell is not the historical object.
  2. Both parameterisations START AT UNIFORM. A head initialised to a random
     code would hand its arm a head start at t=0 -- precisely the turns Part B's
     growth curve cares most about.
  3. The head is SMOOTH in the coordinate (nearby residues -> nearby channel
     distributions). That is the Pictionary property; without it the head arm is
     just a differently-shaped table and the 2x2 measures nothing.
  4. ⭐ The head still has the CAPACITY to memorise an arbitrary per-residue
     code. If it did not, "metric and categorical gap identically under head" --
     the cell that FALSIFIES the architectural claim -- would be unreachable and
     the 2x2 would be unfalsifiable by construction.
  5. One-hot coordinates are MUTUALLY EQUIDISTANT — the categorical arm has no
     'nearby' for the head to interpolate. ⛔ This file used to claim they
     "reduce the head to a table"; that was the 2x2's consistency check and it
     is RETRACTED (D16). A one-hot selects a row of the FIRST matrix only;
     everything above it is shared across all referents.
  6. Both arms present the SAME INPUT SCALE after global standardisation. They
     differ only in SHAPE — graded lattice vs equidistant simplex.
"""
from __future__ import annotations

import pytest
import torch

from tlon.grammar import residue as R
from tlon.referents import schema
from tlon.selfplay.policy import ChannelPolicy

COORDS = [(0, 0), (0, 1), (1, 0), (4, 4), (2, 2), (3, 1)]


def probs(pol: ChannelPolicy, ch: str) -> torch.Tensor:
    return torch.softmax(pol.logit_matrix(ch), dim=-1)


# ── 1. the table is untouched ─────────────────────────────────────────────
def test_the_table_arm_is_unchanged_so_phases_3_to_8_still_reproduce():
    p = ChannelPolicy(6)
    assert p.trunk is None
    assert set(p.logits) == set(p.vals)
    for ch, v in p.vals.items():
        assert tuple(p.logits[ch].shape) == (6, len(v))
        assert torch.all(p.logits[ch] == 0.0)


def test_head_mode_does_not_carry_a_dead_table():
    """Dead zero-gradient parameters would still be handed to the optimiser and
    still be counted by any parameter comparison between the arms."""
    p = ChannelPolicy(6, residues=COORDS)
    assert len(p.logits) == 0
    assert not any("logits." in n for n, _ in p.named_parameters())


# ── 2. both start knowing nothing ─────────────────────────────────────────
def test_both_parameterisations_start_at_exactly_uniform():
    t, h = ChannelPolicy(6), ChannelPolicy(6, residues=COORDS)
    # float32 softmax vs an exact 1/n; compare at tolerance, not by equality.
    assert t.concentration() == pytest.approx(t.uniform_baseline(), abs=1e-6)
    assert h.concentration() == pytest.approx(h.uniform_baseline(), abs=1e-6), (
        "the head starts at a non-uniform code — it would have a head start at "
        "t=0, corrupting exactly the early turns Part B measures")


# ── 3. smoothness: the Pictionary property, as a test ─────────────────────
def test_the_head_is_smooth_in_the_residue_coordinate():
    """Nearby residues must get nearby channel distributions. Checked after a
    real gradient step, because a zero-initialised head is trivially smooth and
    a test on the init state could not come back negative."""
    torch.manual_seed(0)
    pol = ChannelPolicy(4, residues=[(0, 0), (0, 1), (4, 4), (4, 3)])
    opt = torch.optim.Adam(pol.parameters(), lr=0.05)
    for _ in range(60):                      # drive it somewhere non-uniform
        loss = -pol.logit_matrix("coda")[0, 0] - pol.logit_matrix("coda")[2, 1]
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    p = probs(pol, "coda")
    near = float((p[0] - p[1]).abs().sum())          # (0,0) vs (0,1): L1 = 1
    far = float((p[0] - p[2]).abs().sum())           # (0,0) vs (4,4): L1 = 8
    assert near < far, (near, far)


def test_the_table_is_NOT_smooth_which_is_the_whole_contrast():
    """Red-proof for the test above: the same drive on a table leaves the
    'nearby' referent exactly where it started, because rows are independent."""
    torch.manual_seed(0)
    pol = ChannelPolicy(4)
    opt = torch.optim.Adam(pol.parameters(), lr=0.05)
    for _ in range(60):
        loss = -pol.logits["coda"][0, 0] - pol.logits["coda"][2, 1]
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    p = probs(pol, "coda")
    assert torch.allclose(p[1], torch.full_like(p[1], 1 / p.shape[1])), (
        "a table row moved without being trained — rows are not independent")


# ── 4. ⭐ the falsifying cell must be REACHABLE ───────────────────────────
def test_the_head_CAN_memorise_an_arbitrary_code():
    """⛔ IF THIS FAILS THE 2x2 IS UNFALSIFIABLE. The hypothesis is 'the arms
    differ only under head'. Its falsifier is 'the head trains to an arbitrary
    code anyway, so they gap identically'. A head without the capacity to hold
    an arbitrary code could never produce that outcome, and the design would be
    rigged to confirm itself."""
    torch.manual_seed(0)
    coords = [(0, 0), (0, 1), (1, 0), (1, 1)]
    want = [3, 0, 2, 1]                      # deliberately NOT smooth
    pol = ChannelPolicy(4, residues=coords)
    opt = torch.optim.Adam(pol.parameters(), lr=0.05)
    tgt = torch.tensor(want)
    for _ in range(400):
        loss = torch.nn.functional.cross_entropy(pol.logit_matrix("aspect_reps"), tgt)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    got = pol.logit_matrix("aspect_reps").argmax(dim=-1).tolist()
    assert got == want, (got, want)


# ── 5. one-hot reduces the head to a table ────────────────────────────────
def test_one_hot_coordinates_are_mutually_equidistant():
    """With one-hot inputs there is no 'nearby', so the head has nothing to
    interpolate and every pair sits equally far apart.

    ⛔ THIS TEST USED TO BE CALLED `..._make_the_head_a_lookup_table` AND THAT
    NAME ASSERTED A RETRACTED CLAIM (D16). What is true is the equidistance;
    what was false is that equidistance makes the MLP head equivalent to a
    per-referent table."""
    n = 6
    oh = [tuple(20 if j == i else 0 for j in range(n)) for i in range(n)]
    d = {R.normalized(a, b, span=4) for i, a in enumerate(oh)
         for b in oh[i + 1:]}
    assert len(d) == 1, f"one-hot distances are not constant: {sorted(d)}"
    ChannelPolicy(n, residues=oh)            # and it is a legal head input


# ── the arms as shipped ───────────────────────────────────────────────────
def test_the_two_arms_share_a_byte_identical_expressible_scaffold():
    """⛔ If the arms drift apart expressibly, a metric-vs-categorical
    difference is unattributable — the confound the whole 2x2 exists to avoid."""
    a = schema.load(schema.LYRIC_PATH, allow_unreviewed=True).referents
    b = schema.load(schema.RANDOM_PATH, allow_unreviewed=True).referents
    assert [r.id for r in a] == [r.id for r in b]
    for x, y in zip(a, b):
        assert x.roots() == y.roots()
        assert ([tuple(p.via) for p in x.signature.contains]
                == [tuple(p.via) for p in y.signature.contains])


def _with_arm(name: str, text: str, tmp_path):
    """Point a residue arm at a temp YAML for the duration of one test."""
    p = tmp_path / f"{name}.yaml"
    p.write_text(text, encoding="utf-8", newline="\n")
    orig = schema.RESIDUE_PATHS[name]
    schema.RESIDUE_PATHS[name] = p
    return orig


def test_an_UNFILLED_slot_is_REFUSED(tmp_path):
    """⛔ An empty residue_any parses fine and simply means 'no constraint', so
    build_scene would emit residue=None, every cluster-mate would fold to one
    medoid, and the arm would look healthy while manufacturing a null.

    ⭐ Tested by EMPTYING a slot in a temp copy, not by asserting the shipped
    file is unfilled. The first version did the latter and broke the moment the
    coordinates landed — it was asserting a transient state of the repo rather
    than the mechanism, so it could only ever have been right for a few hours.
    """
    src = schema.LYRIC_PATH.read_text(encoding="utf-8")
    i = src.index("          residue_any: [[")
    j = src.index("\n", i)
    emptied = src[:i] + "          residue_any: []" + src[j:]
    orig = _with_arm("lyric", emptied, tmp_path)
    try:
        with pytest.raises(schema.ReferentError, match="UNFILLED"):
            schema.load_residue_arm("lyric", allow_unreviewed=True)
    finally:
        schema.RESIDUE_PATHS["lyric"] = orig


def test_the_lyric_arm_as_shipped_loads_and_is_graded(tmp_path):
    """The complement: with every slot filled it must load, and the geometry
    must not be categorical wearing metric clothes."""
    refs = schema.load_residue_arm("lyric", allow_unreviewed=True).referents
    assert len(refs) == 24
    coords = [c for r in refs for p in r.signature.contains for c in p.residue_any]
    assert len(coords) == 24 and len(set(coords)) == 24
    assert all(len(c) == 3 and all(0 <= v <= 4 for v in c) for c in coords)
    ds = {R.normalized(a, b, span=4) for i, a in enumerate(coords)
          for b in coords[i + 1:]}
    assert len(ds) >= 5, (
        f"only {len(ds)} distinct pairwise distances — this is a categorical "
        "residue wearing metric clothes; the head has nothing to interpolate")


def test_the_categorical_arm_loads_and_is_a_real_cluster_set():
    refs = schema.load_residue_arm("random", allow_unreviewed=True).referents
    assert len(refs) == 24
    sigs: dict = {}
    for r in refs:
        sigs.setdefault(r.roots(), []).append(r)
    assert len(sigs) == 8, f"expected 8 clusters, got {len(sigs)}"
    assert all(len(v) == 3 for v in sigs.values())
    for mates in sigs.values():
        coords = [c for m in mates for p in m.signature.contains
                  for c in p.residue_any]
        assert len(set(coords)) == 3, "cluster-mates share a residue"


def test_two_mates_at_the_same_residue_are_refused(tmp_path):
    """Same expressible signature AND same residue is not two referents.

    ⭐ Built by REWRITING THE PARSED YAML, not by string-replacing a coordinate
    literal. The first version did the latter and silently SKIPPED the moment
    the arms were regenerated with a different one-hot scale — a test that opts
    itself out on a formatting change is not coverage, it is a green tick.
    """
    import yaml as _yaml
    raw = _yaml.safe_load(schema.LYRIC_PATH.read_text(encoding="utf-8"))
    rows = raw["referents"]
    first = next(p for p in rows[0]["signature"]["contains"]
                 if p.get("residue_any"))
    second = next(p for p in rows[1]["signature"]["contains"]
                  if p.get("residue_any"))
    assert rows[0]["id"][:2] == rows[1]["id"][:2], "rows 0,1 are not cluster-mates"
    assert second["residue_any"] != first["residue_any"], "already duplicated"
    second["residue_any"] = [list(first["residue_any"][0])]
    orig = _with_arm("lyric", _yaml.safe_dump(raw, allow_unicode=True), tmp_path)
    try:
        with pytest.raises(schema.ReferentError, match="SAME residue"):
            schema.load_residue_arm("lyric", allow_unreviewed=True)
    finally:
        schema.RESIDUE_PATHS["lyric"] = orig


# ── the scale-confound fix: global standardisation of the head's input ────
def _pairwise(x):
    import itertools
    return [float((x[i] - x[j]).norm())
            for i, j in itertools.combinations(range(x.shape[0]), 2)]


def test_both_arms_present_the_SAME_input_scale_after_standardisation():
    """⛔⛔ THE CONFOUND THIS EXISTS TO KILL. Measured before the fix: the
    categorical arm's coordinates sat 8.3x further apart in raw input space
    (mean inter-referent L2 24.04 vs 2.91), because the one-hot scale was set to
    match mean normalised residue distance for R — a quantity that at lambda=0
    is not even in the reward — while the same number silently set the trunk's
    input magnitude. The arms were unmatched on the one axis the 2x2 measures."""
    import statistics as _S
    got = {}
    for arm in ("lyric", "random"):
        c = [tuple(x) for r in schema.load_residue_arm(arm).referents
             for p in r.signature.contains for x in p.residue_any]
        pol = ChannelPolicy(len(c), residues=c)
        d = _pairwise(pol.coords)
        got[arm] = _S.fmean(d)
        assert float(pol.coords.mean(dim=0).norm()) < 1e-5, "not centred"
    ratio = max(got.values()) / min(got.values())
    assert ratio < 1.15, (f"arms still differ in input scale by {ratio:.2f}x "
                          f"({got}) — the confound is not closed")


def test_standardisation_preserves_SHAPE_and_only_removes_scale():
    """The fix must not touch the geometry under test: relative distances within
    an arm are unchanged, only the global scale is."""
    c = [(0, 0, 0), (1, 0, 0), (0, 4, 0), (4, 4, 4), (2, 2, 2), (0, 0, 4)]
    raw = ChannelPolicy(len(c), residues=c, standardize=False).coords
    std = ChannelPolicy(len(c), residues=c).coords
    a, b = _pairwise(raw), _pairwise(std)
    k = b[0] / a[0]
    assert all(abs(y - k * x) < 1e-4 for x, y in zip(a, b)), "shape changed"


def test_the_categorical_arm_stays_a_mutually_equidistant_simplex():
    """⭐ After the fix the arms differ ONLY in shape: the categorical cloud is
    exactly equidistant, the metric cloud is graded. That IS the contrast."""
    c = [tuple(x) for r in schema.load_residue_arm("random").referents
         for p in r.signature.contains for x in p.residue_any]
    d = _pairwise(ChannelPolicy(len(c), residues=c).coords)
    assert max(d) - min(d) < 1e-4, "categorical arm is no longer equidistant"


def test_the_metric_arm_stays_graded_after_standardisation():
    c = [tuple(x) for r in schema.load_residue_arm("lyric").referents
         for p in r.signature.contains for x in p.residue_any]
    d = _pairwise(ChannelPolicy(len(c), residues=c).coords)
    assert max(d) / min(d) > 3.0, (
        "the metric arm lost its gradation — it would now be a categorical arm "
        "wearing metric clothes")


def test_standardisation_is_deterministic_and_not_learned():
    """⛔ An adaptive input scale would be the embedding-distance failure
    novelty/distance.py exists to prevent, in a new place."""
    c = [(0, 0, 0), (1, 2, 3), (4, 4, 4), (2, 0, 1)]
    a = ChannelPolicy(len(c), residues=c)
    b = ChannelPolicy(len(c), residues=c)
    assert torch.equal(a.coords, b.coords)
    assert not any("coords" in n for n, _ in a.named_parameters())
