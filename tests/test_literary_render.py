"""THE LITERARY RENDER — faithfulness, and the wall around the instrument.

⛔ EVERY TEST HERE IS OFFLINE AND COSTS $0.00. The literary render never calls a
model; that is asserted, not assumed.

The literary render is allowed to be beautiful because it is a PURE FUNCTION of
the Scene, exactly like the gloss. Its faithfulness is inherited, not earned by
review — so what has to be proved is that the inheritance actually holds:

  1. IT SAYS THE SAME IMPRESSION AS THE GLOSS. The partition induced by
     `literary()` must EQUAL the partition induced by `gloss()`: if the gloss can
     tell two scenes apart, so must the literary render (no collapsing a real
     distinction into one pretty sentence), and if the gloss cannot, neither may
     the literary render (no asserting a distinction that is not there).
  2. IT ADDS NO MEANING. Every content word it emits appears in the gloss of the
     SAME scene, up to inflection. Anything else is a lie dressed as craft.
  3. IT STAYS NOUNLESS. No agents, no doers — a gerund refers to a happening
     without positing anything that has it.
  4. THE INSTRUMENT IS UNTOUCHED. `gloss()` output is pinned on golden scenes so
     the literary work cannot drift into the thing that measures it.

⭐ THE LATITUDE CLAUSE, POLICED HERE. The render may vary in HOW it says an
impression — arrangement, rhythm, which coda voices the force. It may never vary
in WHICH impression it says. (1) is the line, and it is mechanical.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict

import pytest

from tlon.grammar import classes as C
from tlon.grammar.gloss import gloss
from tlon.grammar.parse import EventNode, Scene
from tlon.product import schema as PS
from tlon.product.literary import (FUNCTION_WORDS, gerund, literary, nominal)

LEX = C.load()["classes"]


def _scene(node: dict, force: str = "ka") -> Scene:
    scene, _, _ = PS.validate(
        {"node": node, "force": force, "refused_objects": [], "note": ""})
    return scene


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def _walk(n: EventNode):
    yield n
    for _, child in n.edges:
        yield from _walk(child)


# ── the scene set every partition claim is measured on ────────────────────
def scene_set() -> list[Scene]:
    """Deterministic and WIDE: every lexicon item in every class, plus the
    structural pairs that are the hard cases. No RNG — a faithfulness claim
    measured on a random sample is a claim about that sample."""
    out: list[Scene] = []

    def add(node, force="ka"):
        try:
            out.append(_scene(node, force))
        except PS.ProposalError:
            pass                      # over a grammar bound; not this test's job

    for r in sorted(LEX["R"]):
        add({"root": r})
    for o in sorted(LEX["O"]):
        add({"root": "klung", "orient": [o]})
    for rel in sorted(LEX["L"]):
        add({"root": "klung", "edges": [{"relator": rel, "node": {"root": "frem"}}]})
    for a in sorted(LEX["A"]):
        for reps in (1, 2, 3, 4):
            add({"root": "klung", "aspect_root": a, "aspect_reps": reps})
    for d in sorted(LEX["D"]):
        add({"root": "klung", "degree": d})
    for m in sorted(LEX["M"]):
        add({"root": "klung", "modal": m})
    for t in sorted(LEX["T"]):
        add({"root": "klung", "tense": t})
    for q in sorted(LEX["Q"]):
        add({"root": "klung", "quant": q})
    for f in sorted(LEX["F"]):
        add({"root": "klung", "orient": ["nar"]}, f)

    # ⭐ THE HARD CASES: same parts, different STRUCTURE. These are where a
    # prose surface loses what ⟨...⟩ keeps.
    add({"root": "klung", "edges": [{"relator": "sen", "node": {
        "root": "frem", "edges": [{"relator": "sul", "node": {"root": "lan"}}]}}]})
    add({"root": "klung", "edges": [{"relator": "sen", "node": {"root": "frem"}},
                                    {"relator": "sul", "node": {"root": "lan"}}]})
    add({"root": "klung", "edges": [{"relator": "sen", "node": {
        "root": "frem", "orient": ["fen"]}}]})
    add({"root": "klung", "orient": ["fen"],
         "edges": [{"relator": "sen", "node": {"root": "frem"}}]})
    add({"root": "klung", "edges": [{"relator": "sen", "node": {
        "root": "frem", "aspect_root": "tes", "aspect_reps": 2}}]})
    add({"root": "klung", "aspect_root": "tes", "aspect_reps": 2,
         "edges": [{"relator": "sen", "node": {"root": "frem"}}]})
    add({"root": "klung", "edges": [{"relator": "sen", "node": {
        "root": "frem", "orient": ["fen"], "edges": [{"relator": "sul", "node": {
            "root": "lan", "orient": ["mix"], "aspect_root": "mel",
            "aspect_reps": 2}}]}}]})
    # the two roots that share a head verb — see test below
    add({"root": "nöl"})
    add({"root": "hläx"})
    return out


def _partition(scenes, fn):
    cells = defaultdict(set)
    for i, s in enumerate(scenes):
        cells[fn(s)].add(i)
    return {frozenset(v) for v in cells.values()}


# ══ 1. THE CERTIFICATE — two descriptions of one impression ══════════════
def test_the_partition_induced_by_LITERARY_equals_the_one_induced_by_GLOSS():
    """⭐⭐ THE WHOLE FAITHFULNESS CLAIM, IN ONE ASSERTION.

    Ground truth is `gloss()` — a function this module does not implement and
    cannot influence — so this cannot verify the literary render against itself.
    (The B2 hardening pass shipped exactly that mistake and a mutation caught it.)

    Failing LEFT-to-RIGHT would mean the literary render collapses a distinction
    the gloss keeps: two different impressions, one pretty sentence.
    Failing RIGHT-to-LEFT would mean it asserts a distinction the gloss does not
    make: meaning invented by arrangement.
    """
    scenes = scene_set()
    assert len(scenes) > 200, "the scene set stopped being wide"
    assert _partition(scenes, gloss) == _partition(scenes, literary)


def test_the_scene_set_actually_exercises_every_class_of_the_lexicon():
    """⛔ THE GUARD ON THE GUARD. A partition claim measured on a set that never
    varies (say) the evidential is silent about the evidential — and looks
    identical to a claim that covers it."""
    scenes = scene_set()
    seen = {k: set() for k in ("R", "O", "L", "A", "D", "M", "T", "Q", "F")}
    for s in scenes:
        seen["F"].add(s.force)
        for n in _walk(s.node):
            seen["R"].add(n.root)
            seen["O"].update(n.orient)
            seen["L"].update(rel for rel, _ in n.edges)
            for key, val in (("A", n.aspect[0] if n.aspect else None),
                             ("D", n.degree), ("M", n.modal), ("T", n.tense),
                             ("Q", n.quant)):
                if val is not None:
                    seen[key].add(val)
    for cls, got in seen.items():
        assert got == set(LEX[cls]), (
            f"class {cls}: {sorted(set(LEX[cls]) - got)} never exercised")


def test_the_two_roots_that_SHARE_a_head_verb_still_render_distinctly():
    """⛔⛔ THE COLLISION THAT SHAPED THE DESIGN. `nöl` is "it stills, silences"
    and `hläx` is "it stills, goes unbreathing" — 156 roots, 155 distinct head
    verbs. Rendering only the head phrase would have fused two pi-DISTINCT
    scenes into one identical sentence. So the render emits EVERY phrase of the
    root gloss, not just the first."""
    a, b = _scene({"root": "nöl"}), _scene({"root": "hläx"})
    assert gloss(a) != gloss(b)
    assert literary(a) != literary(b)


def test_a_NESTED_edge_does_not_render_like_two_FLAT_edges():
    """⛔⛔ THE SECOND COLLISION, AND WHY THE EM-DASHES ARE THERE. The gloss
    marks embedding with ⟨...⟩; prose has no brackets. Without a scope boundary
    "Z hangs off Y" and "Y and Z both hang off X" are the same sentence."""
    nested = _scene({"root": "klung", "edges": [{"relator": "sen", "node": {
        "root": "frem", "edges": [{"relator": "sul", "node": {"root": "lan"}}]}}]})
    flat = _scene({"root": "klung",
                   "edges": [{"relator": "sen", "node": {"root": "frem"}},
                             {"relator": "sul", "node": {"root": "lan"}}]})
    assert gloss(nested) != gloss(flat)
    assert literary(nested) != literary(flat)


@pytest.mark.parametrize("mutation", [
    {"root": "frem"},
    {"orient": ["fen"]},
    {"aspect_root": "mel"},
    {"edges": [{"relator": "fro", "node": {"root": "lan"}}]},
])
def test_pi_DISTINCT_scenes_get_distinguishable_literary_renders(mutation):
    """Every denoting part, mutated alone against a base that exercises all of
    them — the near-miss form. A render that cannot separate these would let the
    reveal claim Tlön hears one impression where it hears two."""
    from tlon.grammar.canon import utterance_id
    from tlon.grammar.denote import project
    base_node = {"root": "klung", "orient": ["nar", "sil"],
                 "aspect_root": "tes", "aspect_reps": 2,
                 "edges": [{"relator": "sen", "node": {"root": "lan"}}]}
    base = _scene(base_node)
    other = _scene(dict(base_node, **mutation))
    assert utterance_id(project(base)) != utterance_id(project(other)), (
        "the mutation is not pi-distinct; this test would prove nothing")
    assert literary(base) != literary(other)


# ══ 2. NO ADDED MEANING ══════════════════════════════════════════════════
def _justified_words(scene: Scene) -> set[str]:
    """Every word the render is ENTITLED to say, derived from this scene's own
    gloss — plus the gerund of each root verb, which is the one inflection the
    literary surface performs that the gloss does not."""
    allowed = set(_words(gloss(scene))) | set(FUNCTION_WORDS)
    for n in _walk(scene.node):
        for phrase in LEX["R"][n.root][3:].split(","):
            allowed.add(gerund(phrase.strip().split()[0]))
    return allowed


@pytest.mark.parametrize("i", range(0, 260, 7))
def test_every_content_word_is_JUSTIFIED_BY_THE_GLOSS_of_the_same_scene(i):
    """⛔⛔ THE LINE BETWEEN CRAFT AND LYING. The literary render may rearrange,
    subordinate and voice what the Scene contains. It may not name anything the
    Scene does not. A word here that the gloss cannot account for IS added
    meaning, however well it reads."""
    scenes = scene_set()
    if i >= len(scenes):
        pytest.skip("index past the scene set")
    scene = scenes[i]
    unjustified = set(_words(literary(scene))) - _justified_words(scene)
    assert not unjustified, (
        f"{sorted(unjustified)} appear in the literary render but cannot be "
        f"justified from the gloss of the same scene:\n  {gloss(scene)}")


def test_no_word_is_unjustified_ANYWHERE_in_the_whole_scene_set():
    """The sampled test above catches drift fast; this one is the exhaustive
    statement of the same claim."""
    bad = {}
    for scene in scene_set():
        extra = set(_words(literary(scene))) - _justified_words(scene)
        if extra:
            bad[gloss(scene)] = sorted(extra)
    assert not bad, bad


def test_a_gerund_is_an_INFLECTION_of_its_source_never_a_new_lexeme():
    """⛔ Without this, the justified-words test has a hole: it admits whatever
    `gerund()` produces, so a `gerund()` that returned a different word entirely
    would license that word. Every gerund must still be recognisably its verb."""
    for form, gl in sorted(LEX["R"].items()):
        for phrase in gl[3:].split(","):
            verb = phrase.strip().split()[0]
            g = gerund(verb)
            assert g.endswith("ing"), f"{form}: {verb!r} -> {g!r}"
            # ⛔ A PREFIX TEST IS THE WRONG TEST: 'die' -> 'dying' changes the
            # second letter. Instead require the gerund to be the stem under one
            # of the DOCUMENTED transformations and nothing else — which is what
            # "inflection, not invention" actually means.
            from tlon.product.literary import _base                # noqa: PLC2701
            stem = _base(verb)
            legal = {stem,                       # hollow -> hollowing
                     stem[:-1],                  # blaze  -> blazing
                     stem + stem[-1:],           # dim    -> dimming
                     stem[:-2] + "y"}            # die    -> dying
            assert g[:-3] in legal, (
                f"{form}: gerund {g!r} is not an inflection of {stem!r}")


def test_the_gerund_exceptions_are_all_LOAD_BEARING():
    """⛔ A stale exception is a hardcoded answer nobody re-derives. Each one
    must actually differ from what the rule alone produces."""
    from tlon.product import literary as L
    for word, expected in L._GERUND_EXCEPTIONS.items():        # noqa: SLF001
        stem = L._base(word)                                   # noqa: SLF001
        naive = stem + "ing"
        assert naive != expected, f"{word!r}: the rule already gives {expected!r}"


def test_every_aspect_echo_reuses_a_word_from_its_own_gloss_phrase():
    """The repetition is iconic — Tlön repeats the morpheme, so the English
    repeats the word. It must repeat THAT aspect's word, not a new one."""
    from tlon.grammar.gloss import _ASP                        # noqa: PLC2701
    from tlon.product import literary as L
    for name, echo in L._ASPECT_ECHO.items():                  # noqa: SLF001
        source = set(_words(_ASP[name])) | {"and", "an"}
        assert set(_words(echo)) <= source, (
            f"echo {echo!r} for {name} says something {_ASP[name]!r} does not")


# ══ 3. IT STAYS NOUNLESS ═════════════════════════════════════════════════
AGENT_WORDS = ("one who", "someone", "somebody", "a person", "the person",
               " he ", " she ", " they ", " him ", " her ", " them ",
               "thing that", "that which", "whoever", "anyone")


def test_the_render_NEVER_supplies_an_agent():
    """⛔⛔ NATE'S CORRECTION, AND THE POINT OF THE WHOLE SURFACE. The reveal is
    not normal English — it is high-gloss NOUNLESS English. English badly wants
    to give a happening a doer ("one who looms", "a landlord"), and that would
    smuggle back exactly the permanence the language refuses. A gerund refers to
    a happening without positing anything that has it."""
    for scene in scene_set():
        text = " " + literary(scene).lower() + " "
        for agent in AGENT_WORDS:
            assert agent not in text, f"{agent!r} in: {literary(scene)}"


def test_an_embedded_happening_is_a_GERUND():
    node = EventNode(root="fang")
    assert nominal(node).startswith(("a ", "an "))
    assert "ing" in nominal(node)


def test_the_evidential_is_IMPERSONAL_and_grants_no_speaker():
    """⭐ THE SEED OF STANCE-WITHOUT-SPEAKER. The language has 0 of 156 roots for
    a self or an addressee, so the English must not quietly supply one: "as it is
    remembered", never "as I remember"."""
    for m in sorted(LEX["M"]):
        text = literary(_scene({"root": "klung", "modal": m}))
        assert f"as it is {LEX['M'][m]}" in text.lower()
        assert " i " not in " " + text.lower() + " "
        assert "you" not in text.lower()


# ══ 4. FORCE IS VOICE, NOT A PARENTHETICAL ═══════════════════════════════
def test_each_force_gets_its_own_voice_and_none_is_a_parenthetical():
    """The gloss appends "(wondering)". The literary render lets the force close
    the sentence — which is where Tlön puts the force morpheme, so the shape of
    the English mirrors the shape of the utterance."""
    seen = {}
    for f in sorted(LEX["F"]):
        text = literary(_scene({"root": "klung"}, f))
        assert "(" not in text and ")" not in text
        seen[LEX["F"][f]] = text
    assert len(set(seen.values())) == len(LEX["F"]), "two forces sound alike"
    assert seen["ASK"].endswith("?")
    assert seen["ASSERT"].endswith(".") and "—" not in seen["ASSERT"]


@pytest.mark.parametrize("reps", [1, 2, 3, 4])
def test_the_repetition_count_is_RECOVERABLE_from_the_prose(reps):
    """Reps are iconic in Tlön (tes -> testesas). The English repeats too, so a
    reader can count them back — which is also what keeps the literary partition
    equal to the gloss partition, since the gloss shows (×n)."""
    text = literary(_scene({"root": "klung", "aspect_root": "tes",
                            "aspect_reps": reps}))
    assert text.count("again") == reps + 1     # "again and again" + (reps-1)


# ══ 5. THE WALL AROUND THE INSTRUMENT ════════════════════════════════════
GOLDEN_GLOSS = [
    ({"root": "klung"}, "ka", "it hollows, voids."),
    ({"root": "klung", "orient": ["nar"], "aspect_root": "tes",
      "aspect_reps": 2,
      "edges": [{"relator": "sen", "node": {"root": "lan"}}]}, "ka",
     "downward, at ⟨it sees, is beheld⟩, it hollows, voids, again and again (×2)."),
    ({"root": "frem", "modal": "mar", "tense": "pral", "quant": "nol",
      "orient": ["fen", "har"]}, "ko",
     "oft, then past, remembered, beneath, amid, it rains (wondering)"),
    ({"root": "frum", "degree": "xar"}, "ku", "it freezes, overwhelmingly (urging)"),
    ({"root": "fang", "aspect_root": "ax"}, "ki",
     "it streams, flows on, unceasingly?"),
]


def test_the_GLOSS_IS_FROZEN_and_this_work_has_not_touched_it():
    """⛔⛔ THE INSTRUMENT MUST NOT MOVE. `gloss.py` is the honest, morpheme-
    faithful surface AND the auditor's input; making it beautiful would destroy
    it for any future research. The literary render is a SIBLING, never an
    upgrade path. These are pinned outputs, not a file hash: what must not drift
    is the BEHAVIOUR."""
    for node, force, expected in GOLDEN_GLOSS:
        assert gloss(_scene(node, force)) == expected


def test_the_gloss_of_the_whole_scene_set_is_pinned():
    digest = hashlib.sha256(
        "\n".join(gloss(s) for s in scene_set()).encode("utf-8")).hexdigest()
    assert digest == "f333cc4392e9f816ff0f1cf689d601e93511d2013e724bad35aabeeaef0f8a30"


def test_the_literary_render_CANNOT_call_a_model():
    """⛔⛔ THE MOMENT IT ASKS A MODEL TO MAKE IT PRETTIER it becomes ungated
    text — the `note` / `refused_objects` category, the one surface the parser
    cannot vouch for — and it can drift from the Scene. Its faithfulness is
    inherited from being a pure function of the Scene; a model call severs the
    inheritance."""
    import pathlib
    import tlon.product.literary as L
    src = pathlib.Path(L.__file__).read_text(encoding="utf-8")
    body = "\n".join(l for l in src.splitlines()
                     if not l.strip().startswith(("#", '"', "'")))
    for forbidden in ("anthropic", "requests", "urllib", "http", "socket",
                      "openai", "propose", "Proposer", "api_key"):
        assert forbidden not in body, f"{forbidden!r} reachable from the render"


def test_the_render_is_DETERMINISTIC():
    for scene in scene_set()[:60]:
        assert literary(scene) == literary(scene)
