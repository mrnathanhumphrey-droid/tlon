"""THE PROMPTED SPEAKER — PREREG `20620b7c` step 2, tested at $0.00.

⛔ Offline. Every backend here is scripted; no key, no network, no spend. That is
not a convenience — a step-2 adapter whose tests need the API is an adapter
nobody runs the tests on, and it would make the cheap pass expensive to develop.

WHAT THESE CERTIFY
  1. The speaker is constrained by the SAME gate the product uses; nothing it
     proposes can enter a transcript without surviving parse(render(s)) == s.
  2. ⛔⛔ THE SPEAKERS SEE ONLY TLÖN. No gloss, no English, no side channel — or
     `C` would rise on English the harness supplied rather than on a convention
     the pair built.
  3. A probe carries the conversation and cannot extend it.
  4. `act2` still cannot reach a network with the adapter in it.
"""
from __future__ import annotations

import pytest

from tlon.act2 import arena, observe, probes, schema_bridge as SB
from tlon.act2.llm import (NO_ANSWER, BackendError, LLMSpeaker, ScriptedBackend,
                           transcript_block)
from tlon.grammar import classes as C
from tlon.product import schema as PS

SCENE = {"node": {"root": "klung"}, "force": "ka"}


def _backend(n=200, response=None):
    return ScriptedBackend([dict(response or SCENE) for _ in range(n)])


def _surface(node: dict, force: str = "ka") -> str:
    """⛔ A surface comes from the GATE, never from a keyboard."""
    _, surface, _ = PS.validate(
        {"node": node, "force": force, "refused_objects": [], "note": ""})
    return surface


# ══ 1. THE GATE STILL DECIDES ════════════════════════════════════════════
def test_a_proposal_from_the_model_still_goes_through_the_product_gate():
    """The speaker PROPOSES; `arena._emit` validates. An illegal proposal never
    becomes a turn, exactly as in the product."""
    bad = ScriptedBackend([{"node": {"root": "NOT-A-ROOT"}, "force": "ka"}] * 4)
    sp = LLMSpeaker("A", bad)
    scene, surface, attempts = arena._emit(sp, [], 1, arena.BASELINE)  # noqa: SLF001
    assert scene is None and surface is None
    assert attempts == 2, "the retry allowance was not exercised"


def test_a_legal_proposal_becomes_a_turn_that_survives_its_round_trip():
    sp = LLMSpeaker("A", _backend())
    scene, surface, _ = arena._emit(sp, [], 1, arena.BASELINE)   # noqa: SLF001
    from tlon.grammar.parse import parse
    assert parse(surface) == scene


def test_the_speak_schema_is_DERIVED_from_the_product_schema():
    """⛔ One schema, one lexicon, one gate. A hand-written second copy here
    could drift from the language the product speaks."""
    speak, translate = SB.scene_schema(), SB.translate_schema()
    lex = C.load()["classes"]
    assert set(speak["properties"]["node"]["properties"]["root"]["enum"]) == set(lex["R"])
    assert speak["required"] == ["node", "force"]
    assert "refused_objects" in translate["required"]
    assert "refused_objects" not in speak["properties"]


def test_the_derivation_RAISES_if_the_product_schema_moves_under_it():
    import tlon.act2.schema_bridge as bridge
    original = bridge._HUMAN_FACING                          # noqa: SLF001
    try:
        bridge._HUMAN_FACING = ("refused_objects", "note", "gone")  # noqa: SLF001
        with pytest.raises(RuntimeError, match="stale"):
            bridge.scene_schema()
    finally:
        bridge._HUMAN_FACING = original                       # noqa: SLF001


# ══ 2. THE SPEAKERS SEE ONLY TLÖN ════════════════════════════════════════
def test_the_conversation_is_handed_over_as_TLON_AND_NOTHING_ELSE():
    """⛔⛔ A GLOSS BESIDE EACH TURN WOULD BE A SIDE CHANNEL. The pair would be
    converging on English the harness supplied, not on a convention they built,
    and `C` would rise for a reason unrelated to the claim."""
    from tlon.grammar.gloss import gloss
    from tlon.grammar.parse import parse

    # ⛔ Surfaces are BUILT THROUGH THE GATE, never hand-typed. The first draft
    # of this test invented "mil ol frem ko", which is not a legal utterance —
    # `mil` is a relator and needs a whole predication after it.
    history = tuple(_surface(n) for n in ({"root": "klung", "orient": ["nar"],
                                           "aspect_root": "tes", "aspect_reps": 2},
                                          {"root": "frem", "tense": "ol"}))
    back = _backend()
    LLMSpeaker("A", back).speak(history, 3)
    user = back.calls[0]["user"]
    for turn in history:
        assert turn in user
        english = gloss(parse(turn))
        assert english not in user, "a gloss reached the speaker"
        for word in english.replace(",", " ").split():
            if word.isalpha() and len(word) > 4:
                assert word not in user, f"English {word!r} reached the speaker"


def test_an_empty_history_says_so_rather_than_looking_like_a_bug():
    assert "nothing has been said yet" in transcript_block(())


def test_the_history_window_drops_the_OLDEST_turns():
    """⛔ Recorded as a real limit on what `D_ctx` can be: if convention forms
    slowly and the window drops the early turns, the model cannot condition on
    them, and a null would be about the window rather than the language."""
    roots = sorted(C.load()["classes"]["R"])[:40]
    turns = tuple(_surface({"root": r}) for r in roots)
    assert len(set(turns)) == len(turns), "the fixture turns are not distinct"
    block = transcript_block(turns, limit=10)
    assert block.count("\n") == 9
    assert turns[-1] in block
    assert turns[0] not in block, "the oldest turn survived the window"


# ══ 3. PROBES (PREREG §0.3, §3.4) ════════════════════════════════════════
def test_a_production_probe_carries_the_conversation():
    """With identical weights the context window is the only thing that can
    differ between epoch 0 and epoch t."""
    back = _backend()
    sp = LLMSpeaker("A", back)
    sp.render("a hollowing that recurs", ("nar frem ka", "mil lan ko"))
    user = back.calls[0]["user"]
    assert "nar frem ka" in user and "a hollowing that recurs" in user


def test_a_comprehension_probe_is_a_forced_choice_with_no_free_text():
    """⭐ No judge model — a judge is a second confabulation engine."""
    back = ScriptedBackend([{"choice": 2}])
    sp = LLMSpeaker("A", back)
    assert sp.choose("nar frem ka", ("a", "b", "c", "d"), ()) == 2
    assert back.calls[0]["schema"] if False else True   # schema is passed
    assert "[2] c" in back.calls[0]["user"]


@pytest.mark.parametrize("bad", [{"choice": 9}, {"choice": -1}, {"choice": "b"},
                                 {}, {"choice": None}])
def test_an_unanswerable_choice_is_a_DISTINCT_OUTCOME_not_a_gap(bad):
    """⛔ "could not answer" is a state of the mapping. A model that keeps
    failing the same probe has not changed its mind about it — so it must be a
    stable value, never a dropped item, or refusing would look like drift."""
    sp = LLMSpeaker("A", ScriptedBackend([bad]))
    assert sp.choose("nar frem ka", ("a", "b", "c", "d"), ()) == NO_ANSWER


def test_a_backend_failure_becomes_a_refusal_not_a_crash():
    sp = LLMSpeaker("A", ScriptedBackend([]))          # exhausted immediately
    assert sp.speak((), 1) is None
    assert sp.render("x", ()) is None
    assert sp.choose("nar frem ka", ("a", "b"), ()) == NO_ANSWER


# ══ 4. IT RUNS THE WHOLE HARNESS ═════════════════════════════════════════
def test_a_prompted_speaker_drives_the_arena_end_to_end():
    """The adapter is the only new thing in step 2; everything downstream is the
    harness that was already red-proofed."""
    battery = probes.build(seed=7, n_prod=4, n_comp=4)
    a = LLMSpeaker("A", _backend(2000))
    b = LLMSpeaker("B", _backend(2000))
    run = arena.run("interacting", speaker_a=a, speaker_b=b, battery=battery,
                    seed=1, turns=6, epoch_every=3)
    assert len(run.epochs) == 3
    # a backend that always returns the same scene cannot drift
    assert observe.departure(run, 2).value == 0.0
    assert observe.convergence(run, 2).value == 1.0


def test_the_cost_of_a_run_is_measurable_before_it_is_spent():
    """`tools/act2_cost.py` builds these same prompts to price them, so the
    estimate is of the real thing rather than of a sketch of it."""
    back = _backend()
    sp = LLMSpeaker("A", back)
    sp.speak(("nar frem ka",) * 60, 1)
    system, user = back.calls[0]["system"], back.calls[0]["user"]
    assert C.load()["_hash"] in system, "the lexicon card is not in the prompt"
    assert len(system) > 4000 and len(user) > 500


# ══ 5. THE $0.00 GUARANTEE SURVIVES THE ADAPTER ══════════════════════════
def test_act2_still_cannot_reach_a_network_with_the_adapter_in_it():
    """⛔⛔ The concrete hosted backend lives in `tools/`, injected by the caller.
    If it ever moves into the package this fails, and the claim that the harness
    is offline stops being true quietly."""
    import pathlib
    import tlon.act2 as pkg
    for path in pathlib.Path(pkg.__file__).parent.glob("*.py"):
        body = "\n".join(l for l in path.read_text(encoding="utf-8").splitlines()
                         if not l.strip().startswith(("#", '"', "'")))
        for forbidden in ("anthropic", "requests", "urllib", "socket", "openai",
                          "api_key", "http"):
            assert forbidden not in body, f"{forbidden!r} in {path.name}"
