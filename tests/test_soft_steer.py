"""⛔⛔ THE SOFTENED STEER — carry the HAPPENING, not the exact root.

The exact steer bought carry (9% -> 97%) and cost ~14 points of render
(82.4% against 96.5% at matched rows, CIs disjoint). This arm tests whether the
EXACTNESS was the cost, by requiring a root from the prior happening's
gloss-derived family instead of the prior root itself.

⛔ The families are a hand-made semantic judgment over the root glosses — see
`tools/act2_build_gloss_synonyms.py`. The co-occurrence derivation that
preceded them measured scene TOPIC and is retracted.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

from tlon.act2.carry import (expand_roots, gloss_synonyms,  # noqa: E402
                             scene_carry, scene_carry_soft)


@pytest.fixture(autouse=True)
def expanded_lexicon(monkeypatch):
    from tlon.grammar import classes as C
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.load.cache_clear()
    yield
    C.load.cache_clear()


# ── 1 · the widening itself ─────────────────────────────────────────────────

def test_a_familied_root_expands_to_its_happening():
    fam = expand_roots(["flöx"])            # it dims
    assert {"flöx", "pön", "flex", "flax"} == set(fam)


def test_an_unfamilied_root_expands_to_ITSELF_and_so_TIGHTENS():
    """⛔⛔ THE FALLBACK MUST NARROW, NEVER WIDEN. 110 of the 218 roots stand
    alone; if those expanded to nothing the requirement would be unsatisfiable,
    and if they expanded to everything the gate would be vacuous exactly where
    the judgment declined to group.
    """
    assert "hram" not in gloss_synonyms()   # it breathes — stands alone
    assert expand_roots(["hram"]) == frozenset({"hram"})


# ── 2 · the gate ────────────────────────────────────────────────────────────

def test_the_softened_gate_accepts_a_synonym_the_exact_gate_REFUSES():
    """⭐ The whole point of the arm, stated as one case."""
    prior, reply = ["flöx"], ["pön", "hlun"]        # dims -> darkens + waits
    assert not scene_carry(prior, reply).ok
    assert scene_carry_soft(prior, reply).ok


def test_the_softened_gate_still_REFUSES_a_synonym_ECHO():
    """⛔⛔ `added` IS MEASURED AGAINST THE EXPANDED SET. If it were measured
    against the raw prior roots, a reply that merely restates the prior
    happening in a sibling root would count that sibling as BOTH carried and
    new, and pass. The echo clause means nothing unless a synonym cannot be its
    own novelty.
    """
    v = scene_carry_soft(["flöx"], ["pön", "flex"])
    assert not v.ok and "echo" in v.reason


def test_the_softened_gate_is_NOT_strictly_more_permissive():
    """⛔⛤ A CLAIM OF MINE THAT THE CONTROL RUN REFUTED, PINNED SO IT STAYS
    REFUTED. The softened gate reads as "the exact gate but looser", and on the
    exactly steered sample it scored BELOW it — 95.1% against 97.0%.

    It widens CARRIED and narrows NEW, because `added` is measured against the
    expanded family. Here the reply carries `flöx` and its only other root is
    `pön`, a sibling — so it restated one happening twice and said nothing
    further. The exact gate cannot see that echo and accepts it.

    ⛔ Anyone "fixing" the softened rate up to meet the exact one would be
    deleting the synonym-echo guard, which is the reason the gate exists.
    """
    prior, reply = ["flöx"], ["flöx", "pön"]
    assert scene_carry(prior, reply).ok
    assert not scene_carry_soft(prior, reply).ok


def test_the_softened_gate_REFUSES_an_unrelated_root():
    v = scene_carry_soft(["flöx"], ["hlun", "mim"])
    assert not v.ok and "naming the prior turn" in v.reason


def test_the_two_gates_AGREE_when_no_root_has_a_family():
    """⛔ Non-vacuity in the other direction: the softened gate must not be a
    blanket loosening. Where the judgment grouped nothing, it IS the exact gate.
    """
    for reply in (["mläng", "hlun"], ["hram", "hlun"], ["hram"], []):
        assert (scene_carry(["hram"], reply).ok
                == scene_carry_soft(["hram"], reply).ok), reply


def test_an_empty_reply_is_refused_by_both():
    assert not scene_carry_soft(["flöx"], []).ok


# ── 3 · the switch that drives prompt, gate and stamp together ──────────────

def test_steer_mode_moves_all_three_together():
    import act2_build_conversations as B
    assert B.steer_mode(True, True) == ("synonym", scene_carry_soft,
                                        "puzzle_softsteer")
    assert B.steer_mode(True, False) == ("exact", scene_carry,
                                         "puzzle_steered")
    assert B.steer_mode(False, False) == ("exact", scene_carry,
                                          "puzzle_unsteered")


def test_soft_steer_without_steer_is_REFUSED():
    """⛔ Not quietly resolved: either reading runs an arm nobody asked for."""
    import act2_build_conversations as B
    with pytest.raises(SystemExit) as e:
        B.steer_mode(False, True)
    assert "incoherent" in str(e.value)


def test_the_softsteer_recipe_is_distinct_from_the_steered_one():
    """⛔ The stamp is what keeps this corpus out of the research pool, and a
    softened corpus is a DIFFERENT poison from the exactly steered one.
    """
    import act2_build_conversations as B
    recipes = {B.steer_mode(*a)[2] for a in ((True, True), (True, False),
                                             (False, False))}
    assert len(recipes) == 3


# ── 4 · the prompt must not say both things at once ─────────────────────────

def test_the_two_carry_prompts_are_DIFFERENT_and_do_not_contradict():
    """⛔⛔ The exact prompt says "do not choose a near-synonym". Sending that
    sentence alongside a synonym FAMILY would instruct the model both ways, and
    the corpus would measure the confusion rather than the softening.
    """
    from tlon.product import proposer as P

    seen = {}

    class Spy:
        def __init__(self):
            self.name = "spy"
            self.usage = []

    def capture(mode):
        import tlon.product.schema as PS          # noqa: F401
        holder = {}

        class FakeMessages:
            def create(self, **kw):
                holder["user"] = kw["messages"][0]["content"]
                raise RuntimeError("stop after prompt capture")

        class FakeClient:
            messages = FakeMessages()

        p = P.AnthropicProposer.__new__(P.AnthropicProposer)
        p._client = FakeClient()
        p.model, p.name, p.max_tokens, p.usage = "m", "m", 10, []
        p._card = ""
        with pytest.raises(RuntimeError):
            p.propose("the light goes", require_roots=["flöx", "pön"],
                      carry_mode=mode)
        return holder["user"]

    exact, soft = capture("exact"), capture("synonym")
    assert exact != soft
    assert "SAME ROOT" in exact and "do not choose a near-synonym" in exact
    assert "SAME ROOT" not in soft
    assert "near-synonym" not in soft
    assert "WHICHEVER" in soft
    # ⛔ and the softened one must still demand something from OUTSIDE the
    # family, or it licenses a pure echo.
    assert "OUTSIDE" in soft
