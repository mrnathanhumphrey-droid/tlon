"""⛔⛔ THE ONSET PROBE'S PURE PARTS — selection, the joint, and the refusal rule.

The expensive half of `act2_onset_carry` needs a GPU. Everything that decides
what the number MEANS does not, and that is what is pinned here.
"""
from __future__ import annotations

import importlib
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

OC = importlib.import_module("act2_onset_carry")


@pytest.fixture(autouse=True)
def expanded_lexicon(monkeypatch):
    """⛔⛔ THE CORPUS AND THE ADAPTER SPEAK 218 ROOTS; THE DEFAULT SPEAKS 156.

    Without this the probe's own tests parse every reply against the frozen
    lexicon and die on tokens like `fex` — which is precisely the failure the
    PRODUCT would hit, since nothing under `puzzle/` sets `TLON_LEXICON`. Pinned
    here so the probe is at least measured in the language it was trained on.
    """
    from tlon.grammar import classes as C
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.reset_caches()
    yield
    C.reset_caches()


def conv(cid, n_exchanges, theme="t"):
    turns = []
    for i in range(n_exchanges):
        turns.append({"voice": "P", "english": "p%d" % i, "surface": "s%d" % i})
        turns.append({"voice": "T", "english": "t%d" % i, "surface": "r%d" % i})
    return {"id": cid, "theme": theme, "turns": turns}


# ── selection ───────────────────────────────────────────────────────────────

def test_held_out_excludes_by_id_not_by_file():
    pool = [conv("a", 3), conv("b", 3), conv("c", 3)]
    assert [c["id"] for c in OC.held_out(pool, {"b"})] == ["a", "c"]


def test_english_thread_is_p_turns_only_in_order():
    assert OC.english_thread(conv("a", 3)) == ["p0", "p1", "p2"]


def test_select_drops_conversations_too_short_for_the_claim():
    """⛔ A 2-exchange conversation cannot contribute to a 3-turn joint, but it
    WOULD have inflated the depth-0 and depth-1 counts while shrinking the
    joint's denominator — two populations reported as one."""
    pool = [conv("a", 2), conv("b", 3), conv("c", 5)]
    got = OC.select(pool, set(), n=10, seed=1)
    assert sorted(c["id"] for c in got) == ["b", "c"]


def test_select_excludes_trained_ids():
    pool = [conv("a", 5), conv("b", 5)]
    got = OC.select(pool, {"a"}, n=10, seed=1)
    assert [c["id"] for c in got] == ["b"]


def test_select_is_stable_under_input_file_order():
    """⛔ The shuffle is seeded, but a seeded shuffle of a DIFFERENTLY ORDERED
    list is a different sample. Sorting by id first is what makes the probe
    reproducible against a pool that was rebuilt or re-concatenated."""
    pool = [conv(c, 5) for c in "abcdefgh"]
    a = [c["id"] for c in OC.select(pool, set(), n=4, seed=3)]
    b = [c["id"] for c in OC.select(list(reversed(pool)), set(), n=4, seed=3)]
    assert a == b


# ── the joint ───────────────────────────────────────────────────────────────

def turnrec(depth, carried, soft=None, parsed=True):
    return {"depth": depth, "carried": carried, "parsed": parsed,
            "carried_soft": carried if soft is None else soft}


def test_joint_counts_a_conversation_once_however_many_times_it_carries():
    c = {"turns": [turnrec(0, True), turnrec(1, True), turnrec(2, True)]}
    j = OC.joint([c], window=3)
    assert j["clean_hits"] == 1 and j["clean_n"] == 1


def test_joint_clean_requires_every_turn_scorable():
    """⭐ A conversation whose 2nd turn refused has no defensible place in the
    independence contrast — its marginal at depth 1 is undefined."""
    good = {"turns": [turnrec(0, False), turnrec(1, True), turnrec(2, False)]}
    short = {"turns": [turnrec(0, False), turnrec(1, None, parsed=False)]}
    j = OC.joint([good, short], window=3)
    assert j["clean_n"] == 1
    assert j["all_n"] == 2


def test_joint_all_counts_a_refusal_as_a_miss():
    """⛔ A reader shown a refusal was shown nothing to notice. Dropping those
    conversations would report the experience of a luckier reader."""
    refused = {"turns": [turnrec(0, None, parsed=False),
                         turnrec(1, None, parsed=False),
                         turnrec(2, None, parsed=False)]}
    j = OC.joint([refused], window=3)
    assert j["all_hits"] == 0 and j["all_rate"] == 0.0
    assert j["clean_n"] == 0


def test_joint_ignores_turns_beyond_the_window():
    """⛔ Depth 3 and 4 are driven to catch an UNCONDITIONAL lift. Letting them
    into the product number would quietly promise more than three messages.

    ⛔⛤ THIS ASSERTED ONLY `clean_hits == 0` AND A MUTANT THAT DROPPED THE
    WINDOW FILTER SURVIVED IT. With the filter gone the conversation has five
    turns, fails the `len(got) == window` cleanliness test, and is EXCLUDED —
    so the hit count was zero because the row vanished, not because the window
    held. A count of successes cannot distinguish a correct zero from an empty
    denominator; the denominator has to be asserted too.
    """
    c = {"turns": [turnrec(0, False), turnrec(1, False), turnrec(2, False),
                   turnrec(3, True), turnrec(4, True)]}
    j = OC.joint([c], window=3)
    assert j["clean_n"] == 1, "the conversation was dropped, not windowed"
    assert j["clean_hits"] == 0
    assert j["all_hits"] == 0, "a depth-3 carry leaked into the product number"


def test_independence_prediction_uses_the_clean_subsets_own_marginals():
    """⛔⛔ THE GUARD THIS FILE EXISTS FOR.

    Here the FULL population carries often at depth 0 — but every one of those
    conversations is dirty (a later turn refused) and so is excluded from the
    joint. If the prediction were built from the full per-depth table it would
    inherit that high marginal and predict a reach the clean subset never had.
    The prediction must be computed on the same rows as the observed joint.
    """
    dirty = [{"turns": [turnrec(0, True), turnrec(1, None, parsed=False),
                        turnrec(2, None, parsed=False)]} for _ in range(8)]
    clean = [{"turns": [turnrec(0, False), turnrec(1, False), turnrec(2, False)]}
             for _ in range(4)]
    j = OC.joint(dirty + clean, window=3)
    assert j["clean_n"] == 4
    # the clean subset never carries, so every marginal is 0 and so is the
    # prediction — despite 8 carries at depth 0 in the wider sample
    assert j["marginals_clean"] == [0.0, 0.0, 0.0]
    assert j["independent_prediction"] == 0.0


def test_perfect_clustering_shows_a_negative_gap():
    """⭐ The whole reason the joint is measured instead of derived. Half the
    conversations carry on ALL three turns, half on none. Marginals are 0.5
    each, so independence predicts 87.5% — the truth is 50%."""
    hot = [{"turns": [turnrec(d, True) for d in range(3)]} for _ in range(50)]
    cold = [{"turns": [turnrec(d, False) for d in range(3)]} for _ in range(50)]
    j = OC.joint(hot + cold, window=3)
    assert j["clean_rate"] == 0.5
    assert j["independent_prediction"] == 0.875
    assert j["clustering_gap"] == pytest.approx(-0.375)


def test_independent_data_shows_no_material_gap():
    """⭐ The control. If the gap fired on independent data it would be an
    artifact of the estimator rather than a property of the model."""
    convs = []
    for a in (True, False):
        for b in (True, False):
            for c in (True, False):
                convs += [{"turns": [turnrec(0, a), turnrec(1, b),
                                     turnrec(2, c)]}] * 10
    j = OC.joint(convs, window=3)
    assert j["marginals_clean"] == [0.5, 0.5, 0.5]
    assert abs(j["clustering_gap"]) < 1e-9


# ── depth table ─────────────────────────────────────────────────────────────

def test_by_depth_excludes_refusals_from_the_carry_denominator():
    """⛔ Folding invalid emissions into a carry denominator lets a model that
    emits garbage look like one that merely changed the subject."""
    items = [turnrec(0, True), turnrec(0, False),
             turnrec(0, None, parsed=False)]
    t = OC.by_depth(items)["0"]
    assert t["turns"] == 3 and t["refused"] == 1
    assert t["scorable"] == 2 and t["carry_rate"] == 0.5


# ── the drive loop ──────────────────────────────────────────────────────────

class FakeSpeaker:
    """Records the window it was handed on each call."""

    def __init__(self, script):
        self.script = list(script)
        self.seen = []

    def turn(self, english, write_pairs, provoke_pairs):
        self.seen.append((list(write_pairs), list(provoke_pairs)))
        prov, reply = self.script.pop(0)
        return {"you": {"surface": prov, "refused": None if prov else "gate"},
                "tlon": ({"surface": reply, "refused": None} if reply
                         else {"surface": None, "refused": "gate"})}


def _real_surfaces(n):
    p = ROOT / "runs" / "act2" / "corpus_conv_steered" / "conversations.jsonl"
    if not p.exists():
        pytest.skip("steered corpus not in this checkout")
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        for t in json.loads(line)["turns"]:
            out.append(t["surface"])
            if len(out) >= n:
                return out
    return out


def test_a_refusal_does_not_extend_the_window():
    """⛔⛔ THE SHAPE THE SERVER NEVER BUILDS. If a refused turn still appended
    to the window, every later turn would be conditioned on a half-exchange
    that `puzzle/speaker.turn` can never produce — the probe would measure the
    model out of distribution and blame the adapter."""
    from tlon.grammar import classes as C
    roots = frozenset(C.load()["classes"]["R"])
    s = _real_surfaces(4)
    speaker = FakeSpeaker([(s[0], s[1]), (s[2], None), (s[3], s[0])])
    out = OC.drive(speaker, conv("x", 3), roots, max_turns=3)

    assert [r["depth"] for r in out["turns"]] == [0, 1, 2]
    assert out["turns"][1]["carried"] is None      # the refused turn
    # turn 2 (index 2) must have been handed the SAME window as the refused
    # turn 1 — one completed exchange, not two
    assert len(speaker.seen[1][1]) == 1
    assert speaker.seen[2][1] == speaker.seen[1][1]


def test_drive_scores_a_completed_exchange():
    from tlon.grammar import classes as C
    roots = frozenset(C.load()["classes"]["R"])
    s = _real_surfaces(2)
    speaker = FakeSpeaker([(s[0], s[1])])
    out = OC.drive(speaker, conv("x", 1), roots, max_turns=1)
    rec = out["turns"][0]
    assert rec["parsed"] is True
    assert rec["carried"] in (True, False)
    assert rec["carried_soft"] in (True, False)


def test_soft_is_never_reported_without_exact():
    """⛔ The product sentence has two clauses and they are two measurements.
    A soft-only report would let 'similar enough' stand in for 'his word'."""
    from tlon.grammar import classes as C
    roots = frozenset(C.load()["classes"]["R"])
    s = _real_surfaces(2)
    from tlon.grammar.parse import parse
    r = OC.score_turn(s[0], parse(s[1]), roots)
    assert "carried" in r and "carried_soft" in r


def test_the_probe_drives_the_served_turn_and_respells_no_prompt():
    """⛔⛔ MEASURING A COPY OF THE PRODUCT AND REPORTING IT AS THE PRODUCT.
    `puzzle/speaker.turn` exists precisely because the window must be set
    between its two generate calls; a probe that re-spelt that seam would drift
    from the server silently.

    ⛔⛤ THE FIRST VERSION OF THIS TEST GREPPED THE SOURCE AS TEXT AND FIRED ON
    ITS OWN DOCSTRING — the word `WRITE` appears in the prose explaining what a
    refused write does. That is the repo's most-logged trap (PARSE THE
    ARTEFACT, DON'T GREP PROSE) reproduced inside the guard written to prevent
    a different one. It now reads the AST, where a comment cannot reach.
    """
    import ast

    tree = ast.parse((ROOT / "tools" / "act2_onset_carry.py")
                     .read_text(encoding="utf-8"))
    calls, names = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute):
                calls.add(f.attr)
            elif isinstance(f, ast.Name):
                calls.add(f.id)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.alias):
            names.add(node.asname or node.name)

    assert "turn" in calls, "⛔ the probe never drives the served turn function"
    assert "generate" not in calls, (
        "⛔ the probe calls generate() itself — that is the server's seam")
    for forbidden in ("PROVOKE", "WRITE"):
        assert forbidden not in names, (
            "⛔ the probe names the direction constant %r, so it is building "
            "prompts rather than driving the product" % forbidden)


# ── the shape equivalence, certified on the real corpus ─────────────────────

def test_parsed_roots_equals_scene_roots_on_every_corpus_turn():
    """⛔⛔ THE BUG THAT REPORTED 0.0% CARRY WITH CLEAN CONFIDENCE INTERVALS.

    `scene_roots` reads the PROPOSER shape (`aspect_root`, `edge["node"]`).
    `parse()` returns the dataclass shape (`aspect`, `(relator, node)`). The
    probe re-parses replies, so it must extract roots from the parsed tree —
    and that extraction has to be provably the SAME extraction, or the depth
    numbers stop being comparable to the published 27.5%.

    ⭐ EVERY TURN, EXACT SET EQUALITY. A spot check would have passed on the
    18% of turns with no aspect root and no nesting, which is exactly the
    subset where the two shapes happen to agree.
    """
    from tlon.act2.carry import parsed_roots, scene_roots
    from tlon.grammar import classes as C
    from tlon.grammar.parse import ParseError, parse

    src = ROOT / "runs" / "act2" / "corpus_conv_steered" / "conversations.jsonl"
    if not src.exists():
        pytest.skip("steered corpus not in this checkout")
    roots = frozenset(C.load()["classes"]["R"])

    checked = mismatched = 0
    for line in src.read_text(encoding="utf-8").splitlines():
        for t in json.loads(line)["turns"]:
            try:
                parsed = parse(t["surface"])
            except (ParseError, KeyError, ValueError):
                continue
            checked += 1
            if parsed_roots(parsed, roots) != scene_roots(t["scene"], roots):
                mismatched += 1
    assert checked > 1000, "corpus too small to certify on (%d)" % checked
    assert mismatched == 0, (
        "⛔⛔ %d of %d turns disagree — the probe's root extraction is not the "
        "corpus instrument's" % (mismatched, checked))


def test_scene_roots_refuses_a_parsed_tree_instead_of_returning_empty():
    """⛔⛔ A SILENT ZERO IS THE WORST SHAPE A BUG CAN TAKE. This returned
    `frozenset()` for a dataclass, which reads downstream as 'the model carried
    nothing' — indistinguishable from a real finding."""
    from tlon.act2.carry import CarryError, scene_roots
    from tlon.grammar import classes as C
    from tlon.grammar.parse import parse

    roots = frozenset(C.load()["classes"]["R"])
    src = ROOT / "runs" / "act2" / "corpus_conv_steered" / "conversations.jsonl"
    if not src.exists():
        pytest.skip("steered corpus not in this checkout")
    surface = json.loads(src.read_text(encoding="utf-8").splitlines()[0])[
        "turns"][0]["surface"]
    with pytest.raises(CarryError) as exc:
        scene_roots(parse(surface), roots)
    assert "parsed_roots" in str(exc.value), (
        "the refusal must name the function that handles this shape")


def test_scene_roots_still_treats_an_absent_scene_as_empty():
    """⭐ THE CONTROL ON THAT REFUSAL. An ABSENT scene is a legitimate input —
    `t.get("scene")` on a refused turn is None — and is not the same thing as a
    scene of the wrong type. A guard that conflated them would turn every
    refusal into a crash."""
    from tlon.act2.carry import scene_roots
    assert scene_roots(None, frozenset(["ax"])) == frozenset()


def test_as_proposer_shape_round_trips_through_the_published_predicate():
    """⭐ The translation must be lossless in the only way that matters: the
    roots `scene_roots` recovers from the stub are the roots put in."""
    from tlon.act2.carry import scene_roots
    for given in (set(), {"ax"}, {"ax", "hun"}, {"ax", "hun", "fex", "pön"}):
        stub = OC.as_proposer_shape(given)
        assert scene_roots(stub, frozenset(given) | {"zzz"}) == frozenset(given)
