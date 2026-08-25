"""v2 (Cosmicomics) loads, and the archive switch cannot fire silently.

PHASE 9.1. The measurement claims about v2 are 9.2's and are prereg-locked;
these are the structural invariants, which are not claims about the world.
"""
from __future__ import annotations

import pytest

from tlon.referents import schema
from tlon.referents.schema import ReferentError


def v2():
    return schema.load(schema.V2_PATH, allow_unreviewed=True)


# ── the review gate still gates ───────────────────────────────────────────
def test_v2_is_reviewed_and_load_live_serves_it():
    """Nate marked v2 REVIEWED on 2026-08-23 ("locked. lets go").

    Was `test_v2_is_unreviewed_and_load_live_refuses_it` until then. Flipped
    deliberately with the flag, not around it.
    """
    assert v2().review_status == "REVIEWED"
    assert len(schema.load_live().referents) == 46      # seeded_only, see below


def test_the_review_gate_still_refuses_an_unreviewed_file(tmp_path):
    """RED-PROOF: the gate must still bite, or passing it meant nothing.

    v2 being REVIEWED could hide a broken gate, so this writes an UNREVIEWED
    file and checks `load` refuses it — the mechanism, not the current value.
    """
    src = schema.V2_PATH.read_text(encoding="utf-8")
    p = tmp_path / "unreviewed.yaml"
    p.write_text(src.replace("review_status: REVIEWED",
                             "review_status: UNREVIEWED", 1), encoding="utf-8")
    assert "review_status: UNREVIEWED" in p.read_text(encoding="utf-8")
    with pytest.raises(ReferentError, match="UNREVIEWED"):
        schema.load(p)
    schema.load(p, allow_unreviewed=True)               # review tooling may


def test_load_all_still_returns_the_archived_60():
    """The switch must not fire silently -- every phase 3-8 tool calls this."""
    assert len(schema.load_all().referents) == 60
    assert len(schema.load_archive().referents) == 60
    assert {r.id for r in schema.load_all().referents} == \
           {r.id for r in schema.load_archive().referents}


def test_archive_and_live_are_disjoint_sets():
    assert not ({r.id for r in schema.load_archive().referents} &
                {r.id for r in v2().referents})


# ── construction rules that were ruled on, asserted rather than trusted ───
def test_no_forbid_or_matrix_anywhere():
    """Phase 6's isolation claim is scoped to families WITHOUT these.

    If this ever fails, 9.3 owes a re-run of the 6.2 taxonomy placement --
    the assertion is the reminder.
    """
    for r in v2().referents:
        assert not r.signature.forbid, f"{r.id} uses forbid"
        assert r.signature.matrix is None, f"{r.id} uses matrix"


def test_clause_cap_respected_so_the_lexicon_hash_never_had_to_move():
    for r in v2().referents:
        assert len(r.signature.contains) <= 4, r.id


def test_depth_comes_from_nesting():
    """The ruling was depth-by-nesting. Old set used at_depth twice."""
    nested = [r.id for r in v2().referents
              if any(p.at_depth and p.at_depth > 1 for p in r.signature.contains)]
    assert len(nested) >= 10, nested


def test_every_nested_pattern_has_a_shallow_sibling_to_hang_from():
    """⛔ THE BUILD CONSTRAINT, ASSERTED.

    build_scene walks down from the matrix to place a depth-2 pattern, so a
    signature whose ONLY dependent is deep can never build at all -- not just
    for some subsets. Found by reading the builder; pinned here so a future
    signature cannot reintroduce it.
    """
    for r in v2().referents:
        deps = r.signature.contains[1:]
        deep = [p for p in deps if p.at_depth and p.at_depth > 1]
        if not deep:
            continue
        shallow = [p for p in deps if not (p.at_depth and p.at_depth > 1)]
        assert shallow, f"{r.id}: only deep dependents, can never build"
        first_deep = min(deps.index(p) for p in deep)
        first_shallow = min(deps.index(p) for p in shallow)
        assert first_shallow < first_deep, \
            f"{r.id}: deep dependent listed before its shallow sibling"


def test_held_back_referents_are_the_conservation_whisper_plus_abstractions():
    """M38 and M50 state the RETRACTED conservation claim as an image.

    They are declared so the world is complete and withheld so they cannot
    whisper into a live measurement. If someone flips seed_2a on either, this
    fails and they have to say why in a DEVIATIONS entry.
    """
    held = {r.id for r in v2().referents if not r.seed_2a}
    assert {"M38", "M50"} <= held
    assert len([r for r in v2().referents if r.seed_2a]) == 46


def test_the_loader_ACTUALLY_withholds_them():
    """⛔⛔ THE ASSERTION THAT WAS MISSING, AND IT COST THREE RE-RUNS.

    The test above checks the YAML DECLARATION. It passed the whole time while
    `load_live()` served all 50 — it called bare `load()`, which unlike
    `load_all()` does not filter seed_2a — so M38 and M50 were in 9.2a, 9.2b
    and 9.3's first runs (DEVIATIONS_9 D1).

    A test that cannot reach the defect is not coverage. This one asserts the
    LOADER'S OUTPUT, which is the thing every measurement actually consumes.
    """
    live = schema.load_live().referents
    assert len(live) == 46
    ids = {r.id for r in live}
    assert not ({"M37", "M38", "M49", "M50"} & ids), \
        "a held-back referent reached the live measurement set"
    assert all(r.seed_2a for r in live)
    # and the escape hatch still returns everything, for review tooling
    assert len(schema.load_live(seeded_only=False).referents) == 50


# ── collision is the technical requirement, so it gets an assertion ───────
def test_head_roots_are_shared_more_than_in_the_archived_set():
    """Old set: 26/60 = 43 % had a head root unique to them, and a unique head
    can never be made ambiguous by selection because the head is never dropped.
    """
    def unique_frac(refs):
        use: dict[str, int] = {}
        for r in refs:
            for f in r.signature.contains[0].root_any:
                use[f] = use.get(f, 0) + 1
        return sum(1 for r in refs
                   if all(use[f] == 1 for f in r.signature.contains[0].root_any)
                   ) / len(refs)

    assert unique_frac(v2().referents) < unique_frac(schema.load_archive().referents)
