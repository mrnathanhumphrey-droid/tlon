"""⛔⛔ RED-PROOF FOR THE MODEL-SIDE LAG INSTRUMENT — the gate before the army.

The content-transient CORPUS is responsive at lag 1 (+120 sigma, measured). That
is a property of the DATA. Whether it survives into the MODEL is untested, and
the content-free arm shows the transmission is real in the other direction: a
corpus with no content-connection produced a model with none.

⭐⭐ SO ONE ADAPTER IS THE UNIT TEST FOR TWELVE. These tests guard the instrument
that reads it, because a broken instrument here does not fail loudly -- it
returns a plausible profile and authorises ~26-52 GPU-h against a false premise.

⛔⛔ THE LOAD-BEARING GUARANTEE IS THAT BOTH SIDES USE ONE INSTRUMENT. If the
model-side statistic were re-spelt, "the model matches the corpus" would be a
claim about two implementations rather than about the model.
"""
from __future__ import annotations

import pathlib
import random
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

import act2_model_lag as ML                                       # noqa: E402
from tlon.discourse import transient as TR                        # noqa: E402


# ── 1 · ⛔⛔ one instrument, both sides ─────────────────────────────────────

def test_the_model_side_IMPORTS_the_corpus_side_statistic():
    """⛔⛔ Not a re-implementation. These must be the SAME function objects the
    corpus was gated on, or a match between them is a coincidence of two
    codebases rather than a fact about the model."""
    assert ML.lag_profile is TR.lag_profile
    assert ML.permutation_null is TR.permutation_null
    assert ML.check_transience is TR.check_transience
    assert ML.Z_LAG1_MIN is TR.Z_LAG1_MIN
    assert ML.Z_LAGN_MAX is TR.Z_LAGN_MAX


def test_the_module_does_NOT_define_its_own_lag_statistic():
    """⛔ A second definition, even an identical one, is a second thing to drift."""
    src = pathlib.Path(ML.__file__).read_text(encoding="utf-8")
    for banned in ("def lag_profile", "def permutation_null",
                   "def check_transience"):
        assert banned not in src, \
            "act2_model_lag re-spells %s instead of importing it" % banned


def test_a_ModelTurn_duck_types_the_corpus_Turn_for_the_instrument():
    """⭐ The shared functions read only `.surface`. Proven, not assumed."""
    chain = [[ML.ModelTurn("fang ka"), ML.ModelTurn("flux ki"),
              ML.ModelTurn("fang ko")]]
    lex_r = {"fang", "flux"}
    prof = TR.lag_profile(chain, max_lag=2, lex_r=lex_r)
    assert prof[1] >= 0.0 and prof[2] == 1.0   # fang at positions 0 and 2


# ── 2 · ⛔⛔ a refusal must not manufacture adjacency ───────────────────────

def test_a_REFUSED_turn_ENDS_the_chain_and_is_not_skipped():
    """⛔⛔ Splicing turn t-1 to turn t+1 across a refusal reports an adjacency
    the model never produced — it manufactures lag-1 evidence out of a gap, in
    the direction that flatters the hypothesis."""
    chain = [ML.ModelTurn("a ka"), ML.ModelTurn("b ki"),
             ML.ModelTurn(None, refused=True), ML.ModelTurn("c ko")]
    good = ML.usable(chain)
    assert [t.surface for t in good] == ["a ka", "b ki"]


def test_usable_stops_at_the_FIRST_refusal_not_the_last():
    chain = [ML.ModelTurn("a ka"), ML.ModelTurn(None, refused=True),
             ML.ModelTurn("b ki"), ML.ModelTurn(None, refused=True)]
    assert len(ML.usable(chain)) == 1


def test_a_surface_of_None_counts_as_refused_even_without_the_flag():
    chain = [ML.ModelTurn("a ka"), ML.ModelTurn(None), ML.ModelTurn("b ki")]
    assert len(ML.usable(chain)) == 1


# ── 3 · the chain is built in the TRAINED shape ────────────────────────────

def test_the_chain_provokes_on_a_BARE_SURFACE_under_the_provoke_direction():
    """⛔⛔ Every provoke row in the corpus is `prev.surface` and nothing else.
    A scaffolded prompt here would measure a shape the model never trained on,
    and the number would describe the prompt."""
    from tlon.act2.llm import ScriptedBackend
    from tlon.discourse.provocation import DIRECTION as PROVOKE
    back = ScriptedBackend([{"node": {"root": "flux"}, "force": "ki"},
                            {"node": {"root": "fang"}, "force": "ko"}])
    chain = ML.model_chain(back, "klung ka", turns=3)
    assert [c["kind"] for c in back.calls] == [PROVOKE, PROVOKE]
    # the first provocation is the seed itself, bare
    assert back.calls[0]["user"] == "klung ka"
    # the second is the FIRST GENERATED surface, bare — not the seed again
    assert back.calls[1]["user"] == chain[1].surface
    assert "conversation so far" not in back.calls[1]["user"]


def test_the_seed_turn_is_included_in_the_chain():
    """⭐ The seed is turn 0 and its content is what turn 1 must respond to;
    dropping it would delete exactly the lag-1 pair the gate reads."""
    from tlon.act2.llm import ScriptedBackend
    back = ScriptedBackend([{"node": {"root": "flux"}, "force": "ki"}])
    chain = ML.model_chain(back, "klung ka", turns=2)
    assert chain[0].surface == "klung ka"
    assert len(chain) == 2


# ── 4 · a model that cannot sustain a chain is a RESULT, not a crash ───────

def test_a_chain_that_refuses_immediately_yields_too_few_turns_to_score():
    from tlon.act2.llm import ScriptedBackend
    back = ScriptedBackend([{"node": {"root": "NOT_A_ROOT"}, "force": "ka"}])
    chain = ML.model_chain(back, "klung ka", turns=6)
    assert len(ML.usable(chain)) == 1


def test_short_chains_are_DROPPED_not_padded():
    """⛔ A chain of 2 has no lag-2 cell. Including it would reweight the profile
    toward chains that refused early — the ones least able to show persistence."""
    good = ML.usable([ML.ModelTurn("a ka"), ML.ModelTurn("b ki"),
                      ML.ModelTurn(None, refused=True)])
    assert len(good) < 3


# ── 5 · the thresholds are the corpus's, not new ones ─────────────────────

def test_the_GO_thresholds_are_the_SAME_NUMBERS_the_corpus_was_gated_on():
    """⛔⛔ A model-side threshold invented here would let the gate be tuned
    after seeing the model — the definition of post-hoc."""
    assert TR.Z_LAG1_MIN == 6.0 and TR.Z_LAGN_MAX == 3.0
    assert ML.Z_LAG1_MIN == TR.Z_LAG1_MIN
    assert ML.Z_LAGN_MAX == TR.Z_LAGN_MAX


def test_the_verdict_comes_from_check_transience_not_a_local_comparison():
    src = pathlib.Path(ML.__file__).read_text(encoding="utf-8")
    assert "check_transience(chains" in src, \
        "the verdict is computed locally instead of by the shared gate"
