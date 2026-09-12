"""⛔⛔ A GUARD THAT READS A TRANSFORMED VALUE MEASURES THE TRANSFORMATION.

The subtlest failure class in this project, and it just cost a verdict. The
diversity guard keys on the PARSED proposal:

    def _key(proposal): return json.dumps(proposal, ...) if proposal else "<none>"

Every parse in run 3a's re-fire failed, so every proposal was `None`, so every
key was `"<none>"`, so `var_distinct == 1`, so the guard raised

    COLLAPSE: 1 distinct output for 12 DIFFERENT inputs.
    A constant is not a speaker...

about a speaker that had emitted **36 distinct near-valid Tlön scenes**, all 64
of which parse cleanly after dropping one stray trailing brace. The guard was
right that the run was unscoreable and wrong about why — and "why" was the
difference between a fact about Mistral and a bug in the harness.

⭐ The repair is not a looser guard. It is a guard that is ALSO handed the
untransformed value, so it can separate:

    the speaker emitted one thing          -> COLLAPSE, about the MODEL
    the parser rejected many things        -> NOTHING PARSED, about the HARNESS

and a third state that must never be silently folded into either:

    nothing parsed AND no raws recorded    -> an INSTRUMENT GAP, not a finding
"""
from __future__ import annotations

import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

from tlon.act2 import diversity as DV                            # noqa: E402

N = 12


def _varied(k):
    """k distinct parsed scenes, padded to N with repeats."""
    out = [{"root": "r%d" % i} for i in range(k)]
    return (out + [out[-1]] * N)[:N]


def test_a_GENUINELY_constant_speaker_is_still_COLLAPSE():
    """⭐ The original bug this guard was built for must still fire. Repairing
    the misdiagnosis must not cost the diagnosis."""
    const = [{"root": "san"}] * N
    with pytest.raises(DV.DegenerateSpeaker, match="COLLAPSE"):
        DV.measure(repeated=const, varied=const)


def test_ALL_PARSES_FAILED_with_DISTINCT_raws_is_NOT_collapse():
    """⛔⛔ RUN 3a's RE-FIRE, REPRODUCED. 36 distinct generations, 0 parsed."""
    none = [None] * N
    raws = ['{"root": "r%d"}}' % i for i in range(N)]     # the real shape
    with pytest.raises(DV.NothingParsed) as e:
        DV.measure(repeated=none, varied=none,
                   repeated_raw=raws, varied_raw=raws)
    msg = str(e.value)
    assert "NOTHING PARSED" in msg
    assert "%d DISTINCT" % N in msg
    assert "PARSER is rejecting" in msg
    assert "COLLAPSE" not in msg, "the misdiagnosis must be gone"


def test_NothingParsed_is_STILL_refused_by_existing_handlers():
    """⭐ It subclasses `DegenerateSpeaker` on purpose. The run IS unscoreable —
    only the explanation changes — so every `except DegenerateSpeaker` in the
    pipeline keeps refusing to score it."""
    assert issubclass(DV.NothingParsed, DV.DegenerateSpeaker)
    none = [None] * N
    with pytest.raises(DV.DegenerateSpeaker):
        DV.measure(repeated=none, varied=none,
                   repeated_raw=['{"a":1}}'] * N, varied_raw=['{"a":%d}}' % i
                                                              for i in range(N)])


def test_ALL_PARSES_FAILED_with_IDENTICAL_raws_says_it_really_looks_constant():
    """⛔ The repair must not swing the other way. If the raws agree too, the
    honest report is that it does look constant."""
    none = [None] * N
    with pytest.raises(DV.NothingParsed, match="raws agree"):
        DV.measure(repeated=none, varied=none,
                   repeated_raw=["same"] * N, varied_raw=["same"] * N)


def test_ALL_PARSES_FAILED_with_NO_RAWS_is_an_INSTRUMENT_GAP():
    """⛔⛔ THE THIRD STATE, AND THE ONE MOST EASILY LOST. With no raws the guard
    CANNOT tell collapse from a broken parser — and it must say exactly that
    rather than pick the reading that happens to be arithmetically available."""
    none = [None] * N
    with pytest.raises(DV.NothingParsed, match="INSTRUMENT GAP"):
        DV.measure(repeated=none, varied=none)


def test_a_PARTIAL_parse_failure_is_scored_normally():
    """⭐ The new branch fires only when NOTHING parsed. A run where some parses
    succeeded is a real sample and must still be measured."""
    varied = _varied(8)
    varied[0] = None
    d = DV.measure(repeated=[{"root": "san"}] * N, varied=varied)
    assert d.distinct > 1 and d.n == N


def test_the_NOISE_end_still_fires():
    d_repeated = _varied(N)          # same input -> N different outputs
    d_varied = _varied(N)
    with pytest.raises(DV.DegenerateSpeaker, match="NOISE"):
        DV.measure(repeated=d_repeated, varied=d_varied)


# ══ THE CONSUMER ACTUALLY HANDS OVER THE RAWS ═══════════════════════════════

def test_FLOCAL_passes_the_raws_into_the_guard():
    """⛔⛔ DEFECT-Q AGAIN. A guard that CAN read the raws but is never given
    them is the same bug with an extra step, and the suite would be green."""
    src = (_ROOT / "tools" / "act2_flocal.py").read_text(encoding="utf-8")
    assert "varied_raw=speak[\"raws\"]" in src
    assert "repeated_raw=repeated[\"raws\"]" in src


def test_RATE_keeps_raws_INDEX_ALIGNED_with_produced():
    """⛔ The guard indexes `varied_raw` against `varied`. If `raws` only held
    the failures, index k would describe a different call than proposal k — a
    silent off-by-many that would make the new diagnosis wrong instead of
    missing."""
    src = (_ROOT / "tools" / "act2_flocal.py").read_text(encoding="utf-8")
    i = src.index("ok, failures, produced, raws = 0, [], [], []")
    body = src[i:src.index("    n = len(stimuli)", i)]
    # one append per path through the loop: the failure path and the parse path
    assert body.count("raws.append(") == 2, \
        "every iteration must append exactly once, or the lists misalign"
