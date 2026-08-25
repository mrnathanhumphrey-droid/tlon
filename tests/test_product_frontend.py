"""The chatbot front end. Route A's gate, corpus and presentation.

⛔ EVERY TEST HERE IS OFFLINE AND COSTS $0.00. The hosted proposer is swapped
for `ScriptedProposer`, which exercises the entire pipeline -- gate, retry,
corpus, presentation -- without a network call. A product whose tests need the
API is a product nobody runs the tests on.

WHAT THESE CERTIFY:
  1. THE PARSER IS THE BOUNDARY. Nothing the model proposes can reach the screen
     without surviving class membership, every grammar bound, and the
     round trip parse(render(s)) == s.
  2. The coverage edge is STRUCTURALLY required, not merely requested. It was
     optional at first launch and came back empty on all three live renders.
  3. Every accepted pair is logged (Route B's corpus) AND every refusal is
     logged, including ones a retry rescues.
"""
from __future__ import annotations

import json

import pytest

from tlon.grammar import classes as C
from tlon.grammar.parse import parse, render
from tlon.product import chat, corpus
from tlon.product import schema as PS
from tlon.product.proposer import ScriptedProposer, lexicon_card

LEGAL = {"node": {"root": "klung", "orient": ["nar"],
                  "edges": [{"relator": "sen", "node": {"root": "lan"}}]},
         "force": "ka", "refused_objects": ["landlord"], "note": "a hollowing"}


def test_a_legal_proposal_becomes_a_scene_that_survives_its_own_round_trip():
    scene, surface, refusal = PS.validate(LEGAL)
    assert parse(surface) == scene
    assert render(scene) == surface
    assert refusal.objects == ("landlord",)


def test_the_product_scene_never_carries_a_residue():
    """⛔ The product does not inherit the research scaffolding. A residue
    cannot render, so a product Scene carrying one would not be reproducible
    from its own surface."""
    scene, _, _ = PS.validate(LEGAL)
    assert scene.node.residue is None
    assert all(c.residue is None for _, c in scene.node.edges)


@pytest.mark.parametrize("bad,why", [
    ({"node": {"root": "NOPE"}, "force": "ka"}, "invented root"),
    ({"node": {"root": "klung"}, "force": "zz"}, "invented force"),
    ({"node": {"root": "klung", "orient": ["nar", "nar"]}, "force": "ka"},
     "repeated orientation"),
    ({"node": {"root": "klung", "orient": ["nar", "sil", "fen"]}, "force": "ka"},
     "too many orientations"),
    ({"node": {"root": "klung", "aspect_root": "tes", "aspect_reps": 99},
      "force": "ka"}, "aspect reps over cap"),
    ({"node": {"root": "klung", "edges": [{"node": {"root": "lan"}}]},
      "force": "ka"}, "edge with no relator"),
    ({"node": {"root": "klung", "edges": [{"relator": "NOPE",
                                           "node": {"root": "lan"}}]},
      "force": "ka"}, "invented relator"),
    ({"force": "ka"}, "no node"),
    ({"node": {"orient": ["nar"]}, "force": "ka"}, "node with no root"),
])
def test_illegal_proposals_are_REFUSED_not_repaired(bad, why):
    with pytest.raises(PS.ProposalError):
        PS.validate(dict(bad, refused_objects=[], note=""))


def test_too_many_clauses_is_refused():
    k = C.constraints()
    edges = [{"relator": "sen", "node": {"root": "lan"}}
             for _ in range(k["MAX_CLAUSES_PER_PRED"] + 1)]
    with pytest.raises(PS.ProposalError, match="clauses"):
        PS.validate({"node": {"root": "klung", "edges": edges},
                     "force": "ka", "refused_objects": [], "note": ""})


def test_nesting_past_MAX_DEPTH_is_refused():
    k = C.constraints()
    node = {"root": "lan"}
    for _ in range(k["MAX_DEPTH"] + 1):
        node = {"root": "klung", "edges": [{"relator": "sen", "node": node}]}
    with pytest.raises(PS.ProposalError, match="MAX_DEPTH"):
        PS.validate({"node": node, "force": "ka",
                     "refused_objects": [], "note": ""})


# ── 2. the coverage edge is STRUCTURAL ────────────────────────────────────
def test_the_coverage_edge_fields_are_REQUIRED_by_the_schema():
    """⛔⛔ THE REGRESSION THIS EXISTS FOR. They were optional at first launch
    while the system prompt merely ASKED for them, so the prompt was advisory
    and the schema was authoritative -- and `refused_objects` came back EMPTY on
    all three of the first live renders. "landlord", "girlfriend" and "bread"
    were silently dropped with nothing shown, which is exactly the
    silent-approximation behaviour that was ruled out."""
    req = PS.json_schema()["required"]
    assert "refused_objects" in req and "note" in req


def test_the_schema_is_DERIVED_from_the_frozen_lexicon():
    """Nothing hardcodes a root or a bound; if the lexicon moves, this moves."""
    s = PS.json_schema()
    lex, k = C.load()["classes"], C.constraints()
    node = s["properties"]["node"]["properties"]
    assert set(node["root"]["enum"]) == set(lex["R"])
    assert set(s["properties"]["force"]["enum"]) == set(lex["F"])
    assert node["aspect_reps"]["maximum"] == k["MAX_ASPECT_REPS"]
    assert node["orient"]["maxItems"] == k["MAX_ORIENT_PER_PRED"]
    assert node["edges"]["maxItems"] == k["MAX_CLAUSES_PER_PRED"]


def test_the_lexicon_card_shows_the_whole_expressible_world():
    card = lexicon_card()
    lex = C.load()["classes"]
    assert C.load()["_hash"] in card
    for form in list(lex["R"])[:20]:
        assert form in card
    assert "no nouns" in card.lower()


# ── 3. corpus: every pair, and every refusal ──────────────────────────────
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(corpus, "ACCEPTED", tmp_path / "a.jsonl")
    monkeypatch.setattr(corpus, "REFUSED", tmp_path / "r.jsonl")


def test_an_accepted_render_logs_a_training_row(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    r = chat.render_english("my landlord raised the rent",
                            ScriptedProposer([LEGAL]))
    rows = [json.loads(l) for l in
            (tmp_path / "a.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["english"] == "my landlord raised the rent"
    assert rows[0]["surface"] == r.surface
    assert rows[0]["refused_objects"] == ["landlord"]
    assert rows[0]["lexicon"] == C.load()["_hash"]


def test_a_refusal_RESCUED_BY_RETRY_is_still_logged(tmp_path, monkeypatch):
    """⛔ THE SECOND REGRESSION. The first version logged only FINAL failures,
    so a proposal refused once and accepted on retry left no trace -- and two of
    the first three live renders took a retry. The refusal SHAPE is how we know
    whether the front end is healthy."""
    _isolate(tmp_path, monkeypatch)
    bad = {"node": {"root": "NOPE"}, "force": "ka",
           "refused_objects": [], "note": ""}
    r = chat.render_english("x", ScriptedProposer([bad, LEGAL]))
    assert r.attempts == 2
    rows = [json.loads(l) for l in
            (tmp_path / "r.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1 and rows[0]["rescued_on_retry"] is True
    assert (tmp_path / "a.jsonl").exists(), "the rescued render was not logged"


def test_two_failures_refuse_plainly_and_log(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    bad = {"node": {"root": "NOPE"}, "force": "ka",
           "refused_objects": [], "note": ""}
    with pytest.raises(chat.Refused):
        chat.render_english("x", ScriptedProposer([bad, bad]))
    rows = (tmp_path / "r.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 2
    assert not (tmp_path / "a.jsonl").exists(), "a failure produced a training row"


def test_corpus_status_reports_the_B_milestone(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    chat.render_english("a", ScriptedProposer([LEGAL]))
    st = corpus.status()
    assert st["accepted"] == 1 and st["distinct_english"] == 1
    assert st["distinct_roots_covered"] == 2      # klung + lan
    assert st["b_trainable"] is False
    assert st["milestone"]["distinct_english"] == 2000


# ── 4. presentation ───────────────────────────────────────────────────────
def test_the_note_is_never_spliced_into_a_sentence_of_ours(tmp_path, monkeypatch):
    """⛔ The first live output read "It rendered Rendered as a warming..."
    because the template supplied half a sentence and the model the other half."""
    _isolate(tmp_path, monkeypatch)
    p = dict(LEGAL, note="Rendered as a warming that gladdens")
    r = chat.render_english("x", ScriptedProposer([p]))
    said = r.speak()
    assert "It rendered" not in said
    assert said.count("Rendered as") == 1


def test_plural_refusals_read_as_things(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    one = chat.render_english("x", ScriptedProposer([LEGAL])).speak()
    assert "as a thing." in one
    many = dict(LEGAL, refused_objects=["landlord", "rent"])
    two = chat.render_english("y", ScriptedProposer([many])).speak()
    assert "as things." in two


def test_the_surface_is_always_the_first_thing_said(tmp_path, monkeypatch):
    """Opacity-first: the Tlön leads, the explanation follows."""
    _isolate(tmp_path, monkeypatch)
    r = chat.render_english("x", ScriptedProposer([LEGAL]))
    assert r.speak().splitlines()[0] == r.surface


# ── 5. the mode field (preventive hygiene, added before the conversant) ───
def test_mode_is_required_and_has_no_default():
    """⛔⛔ THE POISON THIS PREVENTS. `translate` rows mean "the Scene MEANS the
    English"; `reply` rows mean "the Scene ANSWERS it". Both validate, both
    round-trip, both look like clean pairs — so mixed under one field name they
    would teach Route B a blend of "say this" and "answer this" and it would
    learn neither. A default would let an unlabelled row pass as a labelled one."""
    scene, surface, _ = PS.validate(LEGAL)
    with pytest.raises(TypeError):
        corpus.log_accepted("x", scene, surface, proposer="t")   # no mode
    with pytest.raises(corpus.ModeError):
        corpus.log_accepted("x", scene, surface, proposer="t", mode="chat")


def test_reply_rows_do_NOT_advance_the_translator_milestone(tmp_path, monkeypatch):
    """⭐ The whole reason the field exists: a conversant's rows must never
    count toward a milestone that gates a TRANSLATOR's training."""
    _isolate(tmp_path, monkeypatch)
    scene, surface, _ = PS.validate(LEGAL)
    corpus.log_accepted("a translation", scene, surface, proposer="t",
                        mode="translate")
    corpus.log_accepted("a reply", scene, surface, proposer="t", mode="reply")
    st = corpus.status()
    assert st["accepted"] == 2
    assert st["translate_rows"] == 1
    assert st["distinct_english"] == 1, "a reply row advanced the milestone"
    assert st["by_mode"] == {"translate": 1, "reply": 1}


def test_legacy_rows_are_counted_but_tallied_SEPARATELY(tmp_path, monkeypatch):
    """A row that merely LACKS a label must never be indistinguishable from one
    that declared its mode."""
    _isolate(tmp_path, monkeypatch)
    import json as _j
    (tmp_path / "a.jsonl").write_text(_j.dumps(
        {"english": "old row", "surface": "x", "scene":
         {"node": {"root": "klung"}, "force": "ka"}}) + "\n", encoding="utf-8")
    st = corpus.status()
    assert st["legacy_rows"] == 1
    assert st["by_mode"] == {"translate:legacy": 1}
    assert st["distinct_english"] == 1        # counted for the milestone


def test_the_pipeline_logs_translate_mode(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    chat.render_english("x", ScriptedProposer([LEGAL]))
    row = json.loads((tmp_path / "a.jsonl").read_text(encoding="utf-8").strip())
    assert row["mode"] == "translate"


# ── 6. the compatibility-set reveal (B2) ──────────────────────────────────
def test_decoration_only_differences_share_an_impression():
    """⭐ THE REVEAL'S WHOLE BASIS, and it is the project's own definition
    (Phase 5): two utterances differing only in NON-DENOTING decoration are the
    SAME IMPRESSION. Different surfaces, one impression."""
    from tlon.product import compat
    plain = dict(LEGAL)
    dressed = {"node": {"root": "klung", "orient": ["nar"], "degree": "tos",
                        "tense": "pral",
                        "edges": [{"relator": "sen", "node": {"root": "lan"}}]},
               "force": "ki", "refused_objects": [], "note": ""}
    a, sa, _ = PS.validate(plain)
    b, sb, _ = PS.validate(dressed)
    assert sa != sb, "the two surfaces are identical; nothing is being tested"
    assert compat.impression(a) == compat.impression(b)


def test_a_genuinely_different_scene_does_NOT_share_an_impression():
    """Red-proof: without this the reveal could group everything."""
    from tlon.product import compat
    a, _, _ = PS.validate(LEGAL)
    c, _, _ = PS.validate({"node": {"root": "frem"}, "force": "ka",
                           "refused_objects": [], "note": ""})
    assert compat.impression(a) != compat.impression(c)


def test_the_reveal_groups_by_impression_not_by_surface(tmp_path, monkeypatch):
    from tlon.grammar.canon import canon_json
    from tlon.product import compat
    a, sa, _ = PS.validate(LEGAL)
    dressed = {"node": {"root": "klung", "orient": ["nar"], "degree": "tos",
                        "edges": [{"relator": "sen", "node": {"root": "lan"}}]},
               "force": "ka", "refused_objects": [], "note": ""}
    b, sb, _ = PS.validate(dressed)
    other, _, _ = PS.validate({"node": {"root": "frem"}, "force": "ka",
                               "refused_objects": [], "note": ""})
    rows = [{"english": "the pressure keeps coming back",
             "scene": json.loads(canon_json(b))},
            {"english": "it rains", "scene": json.loads(canon_json(other))}]
    c = compat.compatible_with(a, "my landlord raised the rent", sa, rows)
    assert c.others == ("the pressure keeps coming back",)
    assert c.n == 2
    assert "cannot tell them apart" in c.reveal()
    assert "it rains" not in c.reveal()


def test_a_lone_impression_says_so_without_pretending(tmp_path, monkeypatch):
    """⛔ The empty case is the COMMON case at a corpus of five rows, so it reads
    as arrival, not as breakage. Framing is red-proofed in
    tests/test_product_hardening.py."""
    from tlon.product import compat
    a, sa, _ = PS.validate(LEGAL)
    c = compat.compatible_with(a, "x", sa, [])
    assert c.n == 1 and not c.others
    assert "first" in c.reveal().lower()
