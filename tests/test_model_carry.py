"""⛔⛔ MODEL-SIDE CARRY — the scoring, provable without a GPU.

The generation path needs a card and cannot be exercised here. The SCORING can,
and it is where the interesting mistakes live: what counts as a failure, what is
merely excluded, and the parrot that a bare-overlap number would score perfect.
"""
import pathlib
import sys

import pytest

TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import act2_model_carry as MC                       # noqa: E402


@pytest.fixture(autouse=True)
def expanded_lexicon(monkeypatch):
    from tlon.grammar import classes as C
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.load.cache_clear()
    yield
    C.load.cache_clear()


@pytest.fixture
def roots():
    from tlon.grammar import classes as C
    return frozenset(C.load()["classes"]["R"])


def scene(*rs):
    node = {"root": rs[0]}
    if len(rs) > 1:
        node["edges"] = [{"node": {"root": r}} for r in rs[1:]]
    return {"node": node}


# ── what the band accepts and refuses ───────────────────────────────────────

def test_a_reply_that_carries_and_adds_is_CARRIED(roots):
    r = MC.score("flöx ka", scene("flöx", "hlun"), roots)
    assert r["parsed"] and r["carried"] is True
    assert r["overlap"] == ["flöx"] and r["added"] == ["hlun"]


def test_a_reply_sharing_no_root_is_a_NON_SEQUITUR(roots):
    r = MC.score("flöx ka", scene("hlun", "mim"), roots)
    assert r["carried"] is False and "no root carried" in r["reason"]


def test_a_PARROT_is_refused_as_an_echo(roots):
    """⛔⛔ THE FAILURE A FORCED-CARRY STEER PRODUCES. The reply repeats the
    prompt's root and says nothing else. Bare overlap calls this perfect; the
    band calls it an echo, which is why the band is the headline number.
    """
    r = MC.score("flöx ka", scene("flöx"), roots)
    assert r["carried"] is False and "echo" in r["reason"]
    assert r["overlap"] == ["flöx"]          # overlap is still 1.0 here


# ── exclusions, which must not be scored as failures ────────────────────────

def test_an_unparseable_emission_is_EXCLUDED_not_failed(roots):
    r = MC.score("flöx ka", None, roots)
    assert r["parsed"] is False and r["carried"] is None


def test_a_prompt_with_no_root_is_EXCLUDED(roots):
    """⛔ Nothing to carry FROM. Scoring it would charge the model for the
    probe's shape rather than its own behaviour."""
    r = MC.score("ka nu", scene("flöx", "hlun"), roots)
    assert r["carried"] is None and "no root" in r["reason"]


def test_exclusions_leave_the_denominator(roots):
    rows = [MC.score("flöx ka", scene("flöx", "hlun"), roots),   # carried
            MC.score("flöx ka", None, roots),                    # unparseable
            MC.score("ka nu", scene("flöx"), roots)]             # rootless
    s = MC.summarise(rows)
    assert s["n_probes"] == 3
    assert s["scorable"] == 1 and s["carried"] == 1
    assert s["carry_rate"] == 1.0
    assert s["unparseable"] == 1 and s["excluded_rootless_prompt"] == 1


# ── the discriminator: band vs bare overlap ─────────────────────────────────

def test_a_pure_parrot_scores_100_on_OVERLAP_and_0_on_the_BAND(roots):
    """⛔⛔ THE WHOLE REASON THE BAND IS REPORTED. A model that answers every
    line by repeating its root is the degenerate end state of forcing carry —
    and it is indistinguishable from perfect carry on any overlap measure.
    """
    rows = [MC.score("flöx ka", scene("flöx"), roots) for _ in range(20)]
    s = MC.summarise(rows)
    assert s["bare_overlap_rate"] == 1.0
    assert s["carry_rate"] == 0.0
    assert s["refused_echo"] == 20 and s["refused_non_sequitur"] == 0


def test_a_total_non_sequitur_scores_0_on_BOTH(roots):
    rows = [MC.score("flöx ka", scene("hlun", "mim"), roots) for _ in range(20)]
    s = MC.summarise(rows)
    assert s["bare_overlap_rate"] == 0.0 and s["carry_rate"] == 0.0
    assert s["refused_non_sequitur"] == 20 and s["refused_echo"] == 0


def test_the_two_refusal_kinds_are_never_conflated(roots):
    rows = ([MC.score("flöx ka", scene("flöx"), roots)] * 3
            + [MC.score("flöx ka", scene("hlun", "mim"), roots)] * 5
            + [MC.score("flöx ka", scene("flöx", "hlun"), roots)] * 2)
    s = MC.summarise(rows)
    assert s["refused_echo"] == 3
    assert s["refused_non_sequitur"] == 5
    assert s["carried"] == 2 and s["scorable"] == 10
    assert s["carry_rate"] == 0.2


def test_the_ci_is_reported_and_brackets_the_rate(roots):
    rows = [MC.score("flöx ka", scene("flöx", "hlun"), roots)] * 7 + \
           [MC.score("flöx ka", scene("hlun"), roots)] * 3
    s = MC.summarise(rows)
    lo, hi = s["carry_ci95"]
    assert lo < s["carry_rate"] < hi
    assert 0.0 <= lo and hi <= 1.0


def test_an_empty_run_does_not_divide_by_zero(roots):
    s = MC.summarise([])
    assert s["scorable"] == 0 and s["carry_rate"] == 0.0
