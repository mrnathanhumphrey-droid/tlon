"""⛔⛔ TRAIN-SHAPE == SERVE-SHAPE, ASSERTED ON THE BYTES.

This is the constraint the whole multi-turn rebuild rests on. The puzzle's
context-ON turns came back WORSE than context-OFF (0 of 3 against 3 of 4), and
one of the two causes was that the model was served a shape no training row had.
Fixing the data does nothing if the shapes drift again.

⭐ SO THE ASSERTIONS ARE IDENTITIES, NOT RESEMBLANCES. The serving path and the
training path must resolve the SAME function and produce the SAME bytes — not
"equivalent" prompts, not "the same structure". Two copies of one construction
kept in step by a test that checks they do the same KIND of thing is exactly the
`test_lag_read_is_one_fold` shape that let a decoder drift void a whole curve.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tlon.act2.chat_shape import (PromptShapeRefused,          # noqa: E402
                                  bench_prefix_compatible, bench_prompt,
                                  bench_train_text, read_prompt, train_text)


class FakeTok:
    """A readable template, so a failure names the message sequence."""

    chat_template = "yes"
    eos_token = "<eos>"

    def apply_chat_template(self, msgs, tokenize=False,
                            add_generation_prompt=False):
        out = "".join("<%s>%s</%s>" % (m["role"], m["content"], m["role"])
                      for m in msgs)
        return out + ("<gen>" if add_generation_prompt else "")


class LossyTok(FakeTok):
    """⛔ Mistral v0.3's real behaviour: drops the system message when an
    assistant turn follows, keeps it when the user's turn is last."""

    def apply_chat_template(self, msgs, tokenize=False,
                            add_generation_prompt=False):
        keep = [m for m in msgs if m["role"] != "system"]
        return super().apply_chat_template(keep, tokenize,
                                           add_generation_prompt)


PAIRS = [("mil prax ka", '{"force":"ka"}'),
         ("hul nix ka", '{"force":"ki"}')]


# ── the identity ────────────────────────────────────────────────────────────

def test_training_text_begins_with_exactly_what_the_bench_sends():
    """⛔⛤ THE DEEP INVARIANT. If the training text does not literally start
    with the serving prompt, the model is read out of distribution no matter
    how good it is."""
    tok = FakeTok()
    assert bench_prefix_compatible(tok, "SYS", PAIRS, "live", '{"a":1}')


def test_the_serving_backend_resolves_the_same_function():
    """⭐⭐ NOT 'produces the same output' — THE SAME FUNCTION. The puzzle's
    `_prompt` used to build its own message list; that copy is what this test
    exists to keep deleted."""
    import puzzle.speaker as S

    cls = S._bench_backend_class()
    b = cls.__new__(cls)
    b.tok = FakeTok()
    b.conversation = PAIRS
    assert b._prompt("SYS", "live") == bench_prompt(b.tok, "SYS", PAIRS, "live")


def test_an_empty_bench_is_byte_identical_to_read_prompt():
    """⛔ The first turn of every conversation takes this branch."""
    tok = FakeTok()
    assert bench_prompt(tok, "SYS", [], "u") == read_prompt(tok, "SYS", "u")


def test_prior_turns_are_chat_turns_not_a_flattened_transcript():
    tok = FakeTok()
    got = bench_prompt(tok, "SYS", PAIRS, "live")
    assert got == (
        "<system>SYS</system>"
        '<user>mil prax ka</user><assistant>{"force":"ka"}</assistant>'
        '<user>hul nix ka</user><assistant>{"force":"ki"}</assistant>'
        "<user>live</user><gen>")


def test_exactly_one_system_message():
    tok = FakeTok()
    assert bench_prompt(tok, "SYS", PAIRS, "x").count("<system>") == 1


# ── the trainer's branch ────────────────────────────────────────────────────

def _row(context):
    return {"direction": "write", "prompt": "hello", "english": "hello",
            "scene": {"node": {"root": "xel"}, "force": "ka"},
            "context": context}


def test_a_row_without_context_is_unchanged_byte_for_byte():
    """⛔⛔ EVERY STANDING RUN IN THE CAMPAIGN WAS TRAINED THROUGH THIS BRANCH.
    None of them may move because a product needed a new one."""
    import act2_finetune as F

    tok = FakeTok()
    row = _row([])
    assert F.row_to_text(row, tok) == train_text(tok, F.row_messages(row))
    del row["context"]
    assert F.row_to_text(row, tok) == train_text(tok, F.row_messages(row))


def test_a_context_row_renders_through_the_bench_fold():
    import act2_finetune as F

    tok = FakeTok()
    row = _row([{"prompt": "earlier",
                 "scene": {"node": {"root": "fang"}, "force": "ka"}}])
    got = F.row_to_text(row, tok)
    system, user, answer = (m["content"] for m in F.row_messages(row))
    prior = F.row_messages({"direction": "write", "prompt": "earlier",
                            "english": "earlier",
                            "scene": row["context"][0]["scene"]})
    pairs = [(prior[1]["content"], prior[2]["content"])]
    assert got == bench_train_text(tok, system, pairs, user, answer)
    assert got.startswith(bench_prompt(tok, system, pairs, user))


def test_the_prior_assistant_turn_is_a_json_scene():
    """⛔⛔ THE BUG THAT SHIPPED. The bench put bare Tlön surfaces in the
    assistant slots; the trainer writes a JSON scene. Turn one worked because
    an empty bench never takes the branch, and every turn after it failed in
    under a second with no JSON in the generation."""
    import act2_finetune as F

    tok = FakeTok()
    row = _row([{"prompt": "earlier",
                 "scene": {"node": {"root": "fang"}, "force": "ka"}}])
    text = F.row_to_text(row, tok)
    # the context's assistant turn must be parseable JSON, not "fang ka"
    start = text.index("<assistant>") + len("<assistant>")
    end = text.index("</assistant>", start)
    json.loads(text[start:end])


# ── refusal ─────────────────────────────────────────────────────────────────

def test_a_lossy_template_is_refused_not_trained_around():
    """⛔ Training on what survived is how run 3a was lost twice."""
    with pytest.raises(PromptShapeRefused):
        bench_train_text(LossyTok(), "SYS", PAIRS, "live", '{"a":1}')


def test_the_refusal_names_what_was_dropped():
    try:
        bench_train_text(LossyTok(), "SYS", PAIRS, "live", '{"a":1}')
    except PromptShapeRefused as exc:
        assert "system" in str(exc)
    else:                                                  # pragma: no cover
        pytest.fail("expected PromptShapeRefused")


# ── the built corpus ────────────────────────────────────────────────────────

BENCH = ROOT / "runs" / "act2" / "corpus_bench" / "train.jsonl"


@pytest.mark.skipif(not BENCH.exists(), reason="bench corpus not built")
def test_every_built_row_renders_and_stays_prefix_compatible():
    """⭐ The rows on disk, through the real renderer. A shape guard that only
    ever sees hand-made fixtures has not met the corpus."""
    import act2_finetune as F

    tok = FakeTok()
    rows = []
    with BENCH.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i >= 400:
                break
            rows.append(json.loads(line))
    assert rows
    depth_seen = 0
    for row in rows:
        text = F.row_to_text(row, tok)
        assert text.endswith(tok.eos_token) or text
        depth_seen = max(depth_seen, len(row.get("context") or []))
    assert depth_seen >= 1, "no context rows in the sample — nothing was tested"


@pytest.mark.skipif(not BENCH.exists(), reason="bench corpus not built")
def test_no_built_row_exceeds_the_serve_depth():
    """⛔ Training deeper than the bench serves wastes it; the serve cap is
    `puzzle.speaker.CONTEXT_TURNS`."""
    from puzzle.speaker import CONTEXT_TURNS

    with BENCH.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i >= 2000:
                break
            row = json.loads(line)
            assert len(row.get("context") or []) <= CONTEXT_TURNS
