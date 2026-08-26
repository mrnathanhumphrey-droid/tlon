"""THE HARNESS MUST NEVER DESTROY A FAILURE. $0, offline.

⛔⛔ RUN 4 LOST ITS LARGEST RESULT TO THIS. **60 of 61 `speak` failures were
"no parseable JSON" and the ledger stored `proposal: null` with no text** — so
the mode responsible for 98 % of a 21-point regression was the one the record
kept the least about. Two hypotheses were formed and refuted against other data
(output density 1.38 vs 1.39 slots/node; `max_new_tokens=220` against a longest
target of 163). The third could not be tested at any price, because the subject
of the measurement had been thrown away.

⭐ THIRD TIME THIS SHAPE HAS COST SOMETHING:
    · the comprehension parser scored 64 REAL answers as NO_ANSWER and discarded
      them, reading 0/64 — below the 25 % a coin flip scores
    · the greedy-decoding probe reported n=1 as n=64
    · here

**A failure is the most information-dense event in a run.** These tests make that
structural instead of remembered.
"""
from __future__ import annotations

import pytest

from tlon.act2 import llm
from tlon.act2.llm import BackendError, LLMSpeaker, NO_ANSWER

UNPARSEABLE = "mlang testesas ko  <- this is Tlon, not JSON, and it has no brace"
HALF_JSON = '{"force": "ko", "node": {"root": "mlang"'          # truncated


class _Backend:
    """A backend that emits exactly what it is told to, and never parses."""
    name = "stub"

    def __init__(self, gen: str, *, attach_raw: bool = True):
        self.gen, self.attach_raw = gen, attach_raw

    def call(self, *, system, user, schema, kind):
        if self.attach_raw:
            raise BackendError(f"no JSON object in the generation for {kind}",
                               raw=self.gen, kind=kind)
        raise BackendError("legacy backend with no raw attached")

    def cost_report(self):
        return {"calls": 1, "usd_total": 0.0}


def _speaker(gen: str, **kw) -> LLMSpeaker:
    return LLMSpeaker("t", _Backend(gen, **kw), card=False)


# ══ THE EXCEPTION CARRIES THE TEXT ═══════════════════════════════════════
def test_BackendError_carries_the_raw_generation():
    e = BackendError("boom", raw=UNPARSEABLE, kind="speak")
    assert e.raw == UNPARSEABLE and e.kind == "speak"


def test_BackendError_still_works_without_a_raw():
    """⛔ Back-compatible: a backend that does not attach one must not crash."""
    e = BackendError("boom")
    assert e.raw is None


@pytest.mark.parametrize("kind,call", [
    ("speak", lambda s: s.speak((), 1)),
    ("render", lambda s: s.render("a stone falls", ())),
])
def test_the_speaker_records_the_raw_when_the_turn_fails(kind, call):
    """⛔⛔ THE CORE. The turn still returns None — the CONTRACT is unchanged —
    but the text now survives beside it."""
    sp = _speaker(UNPARSEABLE)
    assert call(sp) is None
    assert sp.last_failure["raw"] == UNPARSEABLE
    assert sp.last_failure["kind"] == kind
    assert sp.last_failure["raw_recorded"] is True


def test_choose_records_it_too_and_still_returns_NO_ANSWER():
    """The comprehension path is where this class of bug FIRST cost a reading."""
    sp = _speaker(UNPARSEABLE)
    assert sp.choose("mlang ko", ["a", "b", "c", "d"], ()) == NO_ANSWER
    assert sp.last_failure["raw"] == UNPARSEABLE


def test_the_raw_is_NOT_truncated():
    """⛔ A 400-char clip cannot show a generation that RAN LONG, which is one of
    the live hypotheses about why this fires. Truncating here would reproduce
    the defect one level down."""
    long_gen = "mlang testesas ko " * 500          # ~9,000 chars
    sp = _speaker(long_gen)
    sp.speak((), 1)
    assert sp.last_failure["raw"] == long_gen
    assert len(sp.last_failure["raw"]) > 400


def test_a_backend_with_NO_raw_is_flagged_not_silently_empty():
    """⛔⛔ 'the model emitted nothing' and 'the instrument did not record it'
    are DIFFERENT FACTS and must not share a representation. An empty field
    that reads like the first when it means the second is how run 4's
    diagnosis died."""
    sp = _speaker(UNPARSEABLE, attach_raw=False)
    assert sp.speak((), 1) is None
    assert sp.last_failure["raw"] is None
    assert sp.last_failure["raw_recorded"] is False


# ══ THE LEDGER ROW, WHICH IS WHAT ACTUALLY GETS BANKED ═══════════════════
def _rate_row(gen: str, **kw) -> dict:
    """Run the real `_rate` over one stimulus and return its failure row."""
    import sys
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
    import act2_flocal as F
    sp = _speaker(gen, **kw)
    out = F._rate(sp, [None], "speak", histories=[()])
    assert out["valid"] == 0 and len(out["failures"]) == 1
    return out["failures"][0]


def test_the_LEDGER_ROW_carries_the_raw_not_a_bare_null():
    """⛔⛔ THE RED-PROOF THE BRIEF ASKED FOR: feed the harness a known-
    unparseable generation and assert the raw is RECORDED, not discarded."""
    row = _rate_row(UNPARSEABLE)
    assert row["proposal"] is None            # contract unchanged
    assert row["raw"] == UNPARSEABLE          # and the evidence survives
    assert row["raw_len"] == len(UNPARSEABLE)


def test_a_TRUNCATED_json_generation_is_also_captured():
    """The shape most likely to be behind run 4's collapse: output that starts
    like JSON and stops. Indistinguishable from 'emitted nothing' without the
    raw."""
    row = _rate_row(HALF_JSON)
    assert row["raw"] == HALF_JSON
    assert row["raw"].startswith("{")


def test_the_row_SHOUTS_when_no_raw_was_available():
    row = _rate_row(UNPARSEABLE, attach_raw=False)
    assert row["raw"] is None
    assert "INSTRUMENT gap" in row["raw_unavailable"]


def test_run4s_exact_ledger_shape_can_no_longer_be_produced():
    """⛔ THE REGRESSION PIN. Run 4's rows were exactly
    `{kind, reason, proposal: null, class_errors: []}` — four keys, no text. If
    a row ever looks like that again, this fails."""
    row = _rate_row(UNPARSEABLE)
    assert set(row) > {"kind", "reason", "proposal", "class_errors"}, (
        "the failure row has gained no evidence over run 4's")
    assert "raw" in row
