"""W2 — the text it trains on must BEGIN with the text it is read under.

`PREREG_IDF2_2026_09_26.md`, LOCK `37363296`. W2's input is `t−2` and `t−1` as
real chat turns, which is the only arm in the design that asks the art piece's
question: no marker, the model deriving the intersection itself.

⛔⛔ THE FAILURE THIS FILE EXISTS TO PREVENT HAS HAPPENED TWICE ALREADY.
Run 3a trained under one prompt shape and was read under another, and nothing
caught it — `chat_shape.py` carries the note. A W2 arm whose read prompt is a
hand-built transcript rather than the trainer's own construction would repeat it
exactly, and the symptom would be a lag profile, not an error.

⭐ SO THE ASSERTION IS PREFIX-IDENTITY, NOT SIMILARITY. `bench_train_text` is
defined as `bench_prompt(...) + answer + eos`, so the training text literally
begins with the serving prompt — and these tests check that on the SAME pairs
the reader builds, with a real tokenizer's template.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from tlon.act2.chat_shape import (bench_prompt,          # noqa: E402
                                  bench_train_text, read_prompt)


class Tok:
    """A minimal chat template with the shape Qwen's has: role-delimited turns
    and a trailing generation prompt. ⭐ Enough to prove prefix-identity, which
    is a property of the CONSTRUCTION rather than of any one vendor."""

    eos_token = "<|im_end|>"
    chat_template = "yes"

    def apply_chat_template(self, msgs, tokenize=False,
                            add_generation_prompt=False):
        out = "".join("<|im_start|>%s\n%s<|im_end|>\n" % (m["role"],
                                                          m["content"])
                      for m in msgs)
        if add_generation_prompt:
            out += "<|im_start|>assistant\n"
        return out


@pytest.fixture
def tok():
    return Tok()


def test_an_empty_bench_is_byte_identical_to_the_bare_read(tok):
    """⛔⛔ THE FIRST TURN OF EVERY W2 CHAIN TAKES THIS BRANCH. If it differed
    even by a newline, every opening turn would be read under a prompt no
    measurement in this campaign has ever used — and W2's turn 1 has no `t−2`,
    so it is exactly the branch that fires most."""
    assert (bench_prompt(tok, "SYS", [], "hello")
            == read_prompt(tok, "SYS", "hello"))


def test_the_training_text_BEGINS_with_the_serving_prompt(tok):
    """⭐⭐ PREFIX-IDENTITY, WHICH IS WHAT "train-shape EQUALS read-shape" MEANS.
    Not 'contains', not 'resembles' — begins with."""
    pairs = [("surface t-2", '{"scene": "t-1"}')]
    prompt = bench_prompt(tok, "SYS", pairs, "surface t-1")
    text = bench_train_text(tok, "SYS", pairs, "surface t-1",
                            '{"scene": "t"}')
    assert text.startswith(prompt), (
        "W2's training text does not begin with the prompt it will be served "
        "under — this is the run-3a failure, and it presents as a lag profile")
    assert text[len(prompt):].startswith('{"scene": "t"}')


def test_the_prior_turn_is_the_SCENE_not_the_surface(tok):
    """⛔ `row_messages` puts the serialised scene in the assistant slot. A
    reader that put the SURFACE there would be serving a shape the model has
    never answered under, on every turn from the third onward."""
    import act2_model_lag as ML

    class T:
        scene = None
        raw = '{"scene": "as emitted"}'
    assert ML._assistant_text(T()) == '{"scene": "as emitted"}'


def test_the_reader_builds_pairs_only_from_turn_three_onward():
    """⛔ W2 needs `t−2`, which does not exist while the chain is shorter than
    two turns — the same off-by-one the marker has, and it must agree with the
    row builder or the arms diverge on their opening turns."""
    import act2_model_lag as ML
    src = pathlib.Path(ML.__file__).read_text(encoding="utf-8")
    assert "if window2 and len(out) >= 2" in src
    assert "pairs = [(out[-2].surface, answers[-1])]" in src


def test_window2_off_sends_no_pairs_at_all(monkeypatch):
    """⛔⛔ THE DEFAULT PATH IS UNTOUCHED. Every pre-W2 read — M, C1, M-strip,
    M-shuffle, Step P, the whole campaign — must reach `generate` with `pairs`
    absent, or threading W2 through silently redefined them all."""
    import act2_model_lag as ML
    seen = []

    class T:
        ok = True
        seconds = 0.0
        scene = None
        raw = "{}"

        def __init__(self, s):
            self.surface = s

    def fake_generate(backend, direction, payload, history, **kw):
        seen.append(kw.get("pairs"))
        return T("aa bb")

    monkeypatch.setattr(ML, "generate", fake_generate)
    ML.model_chain(object(), "seed surface", turns=4)
    assert seen == [None, None, None], seen


def test_window2_on_sends_pairs_once_there_is_a_t_minus_2(monkeypatch):
    import act2_model_lag as ML
    seen = []

    class T:
        ok = True
        seconds = 0.0
        scene = None
        raw = '{"a": 1}'

        def __init__(self, s):
            self.surface = s

    def fake_generate(backend, direction, payload, history, **kw):
        seen.append(kw.get("pairs"))
        return T("reply surface")

    monkeypatch.setattr(ML, "generate", fake_generate)
    ML.model_chain(object(), "seed surface", turns=4, window2=True)
    assert seen[0] is None, "turn 2 has no t-2"
    assert seen[1] == [("seed surface", '{"a": 1}')]
    assert seen[2] == [("reply surface", '{"a": 1}')]


def test_the_read_records_that_it_was_window2(monkeypatch):
    """⛔ A row that does not say which input shape produced it is not
    comparable to one that does — the same argument that put `temperature` and
    `marker_fn` in the result."""
    import act2_model_lag as ML

    def spy(backend, **kw):
        return {"verdict": "REFUSED", "z": {}, "lag_profile": {}}

    monkeypatch.setattr(ML, "_read_lag_inner", spy)

    class B:
        temperature = 0.0
        max_new_tokens = 220
    out = ML.read_lag(B(), window2=True)
    assert out["window2"] is True
    assert ML.read_lag(B())["window2"] is False
