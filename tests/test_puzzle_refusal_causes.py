"""⛔⛔ A REFUSAL MUST NAME ITS OWN CAUSE, AND FOR MONTHS ONE SENTENCE NAMED THREE.

On 2026-09-25 the live bench refused five lines containing the Tlön word `ka`
and told the reader **"The language would not hold that."** Four of the five
were nothing of the kind: the model emitted a malformed object — a null node, a
string where a list belongs, once JSON that would not decode — and the bench
attributed its own speaker's bad afternoon to the language, in the one
interaction a curious reader reaches first. The fifth was genuine.

The split is `tlon/product/schema.py`'s own convention: a TYPE violation reports
`... got {type(x).__name__}`, a VALUE violation does not. This file pins that
convention **against schema.py's source**, so that if the messages drift the
test fires instead of the blame quietly moving back onto Tlön.
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puzzle import server as S            # noqa: E402

#: Verbatim from the production log, 2026-09-25 19:17-19:20.
FROM_THE_BENCH = {
    # genuine: `ka` is a force, and no force is a root. Tlön really cannot.
    "gate refused: root='ka' is not in lexicon class R. The lexicon is frozen "
    "at 08c03b0a81330e4ba42883fa8b08c873; invented forms are refused.":
        "language",
    "gate refused: node must be an object, got NoneType": "speaker",
    "gate refused: refused_objects must be a list, got str": "speaker",
    "malformed JSON for provoke: Expecting ',' delimiter: line 1 column 295 "
    "(char 294)": "speaker",
}

_WANT = {"language": "_REFUSAL_LANGUAGE", "speaker": "_REFUSAL_SPEAKER"}


@pytest.mark.parametrize("raw,cause", sorted(FROM_THE_BENCH.items()))
def test_every_refusal_the_bench_actually_produced_is_attributed_right(raw,
                                                                       cause):
    assert S._reader_refusal(raw) == getattr(S, _WANT[cause]), (
        "%r was blamed on the wrong party" % raw[:60])


def test_three_of_the_four_used_to_read_as_the_languages_fault():
    """⭐ The regression this file exists to prevent, stated as a count."""
    blamed = [r for r, c in FROM_THE_BENCH.items() if c == "speaker"]
    assert len(blamed) == 3
    for raw in blamed:
        assert S._reader_refusal(raw) != S._REFUSAL_LANGUAGE


def test_the_sentences_are_distinct_and_fixed():
    """⛔ Nothing derived from the raw error may reach a reader — these are
    constants, and they must not collapse into one another."""
    sentences = {S._REFUSAL_LANGUAGE, S._REFUSAL_SPEAKER, S._REFUSAL_TROUBLE,
                 S._NOTHING_TO_ANSWER}
    assert len(sentences) == 4


@pytest.mark.parametrize("raw", sorted(FROM_THE_BENCH))
def test_no_refusal_leaks_a_fragment_of_itself(raw):
    """⛔⛔ THE SANITISER'S CARDINAL RULE. A reader-facing sentence that carried
    any substring of the real error would put arbitrary English — possibly the
    reader's own injected text — on a face whose whole claim is that nothing
    here translates anything."""
    out = S._reader_refusal(raw)
    for word in re.findall(r"[A-Za-z_']{4,}", raw):
        if word.lower() in {"that", "there", "speaker", "list", "object"}:
            continue          # ordinary English that the fixed sentences own
        assert word not in out, "the refusal echoed %r from the raw error" % word


def test_an_empty_reason_is_not_a_refusal():
    assert S._reader_refusal(None) is None
    assert S._reader_refusal("") is None


def test_an_unreachable_backend_is_still_its_own_sentence():
    assert S._reader_refusal("connection reset") == S._REFUSAL_TROUBLE


# ── the coupling, checked against schema.py itself ─────────────────────────

def _raise_messages() -> list[str]:
    """Every `ProposalError` message literal in the gate, as written."""
    src = (ROOT / "tlon" / "product" / "schema.py").read_text(encoding="utf-8")
    body = src[src.index("def "):]
    out = []
    for m in re.finditer(r"raise ProposalError\((.*?)\)\n", body, re.S):
        out.append(m.group(1))
    return out


def test_the_gate_still_reports_type_violations_the_way_the_split_assumes():
    """⛔⛔ THE BRITTLE JOINT, MADE LOUD. `server._MALFORMED_MARK` is the string
    `", got "`, and it only sorts the causes correctly while schema.py keeps
    reporting a wrong TYPE that way and a wrong VALUE some other way. If that
    convention drifts, every malformed scene silently goes back to being the
    language's fault — so the convention is asserted here against the source.
    """
    msgs = _raise_messages()
    assert msgs, "no ProposalError raises found — the parse above broke"

    typed = [m for m in msgs if "type(" in m]
    assert typed, "schema.py no longer reports any type violation"
    for m in typed:
        assert S._MALFORMED_MARK.strip() in m or ", got " in m, (
            "a type violation that does not carry %r: %s"
            % (S._MALFORMED_MARK, m[:70]))


def test_the_lexicon_refusal_is_not_swept_up_as_malformed():
    """⭐ The one genuine case must survive the split. `is not in lexicon class`
    carries no `got`, so it stays with the language."""
    msgs = " ".join(_raise_messages())
    assert "is not in lexicon class" in msgs
    lex = ("gate refused: root='ka' is not in lexicon class R. The lexicon is "
           "frozen at deadbeef; invented forms are refused.")
    assert S._MALFORMED_MARK not in lex
    assert S._reader_refusal(lex) == S._REFUSAL_LANGUAGE
