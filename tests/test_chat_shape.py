"""⛔⛔ RED-PROOF: NO MESSAGE MAY VANISH INTO A CHAT TEMPLATE.

Run 3a was fired twice at Mistral-7B-Instruct-v0.3 and produced no datapoint
either time. The second cause: its chat template drops the system message in the
TRAIN shape `(system, user, assistant)` and keeps it in the READ shape
`(system, user)` + generation prompt. So the model trained with no instruction
and was read with one — a train/read DISTRIBUTION MISMATCH, not merely a missing
prompt.

Measured on the real tokenizers:

    Qwen      train 399 chars   system present    prefix-compatible
    OLMo      train 401 chars   system present    prefix-compatible
    Mistral   train 251 chars   SYSTEM ABSENT     read prompt NOT a prefix

⭐ THE TWO CLAIMS THE REPAIR MUST HOLD, and they pull against each other:
  A. a base whose template is faithful is left BYTE-IDENTICAL, so no standing
     run's training text moves and the cross-family comparison survives;
  B. a base whose template is lossy is rebuilt so the read prompt is a literal
     PREFIX of the training text — by construction, which is the only version
     that also protects the next base nobody has tried.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

from tlon.act2.chat_shape import (PromptShapeRefused,              # noqa: E402
                                  prefix_compatible, read_prompt,
                                  template_drops, train_text)

pytest.importorskip("transformers")

SYS, USR, ANS = "INSTRUCTION-MARKER: emit only JSON.", "USER-MARKER", '{"a":1}'
MSGS = [{"role": "system", "content": SYS},
        {"role": "user", "content": USR},
        {"role": "assistant", "content": ANS}]

#: A Mistral-shaped template: no native system role, and it merges the system
#: text into the first `[INST]` ONLY when the conversation ends with the user.
#: ⭐ Shape-dependent on purpose — that is the whole bug.
LOSSY = (
    "{% for m in messages %}"
    "{% if m['role'] == 'user' %}"
    "{% if loop.last and messages[0]['role'] == 'system' %}"
    "[INST] {{ messages[0]['content'] }}\n\n{{ m['content'] }}[/INST]"
    "{% else %}[INST] {{ m['content'] }}[/INST]{% endif %}"
    "{% elif m['role'] == 'assistant' %} {{ m['content'] }}{{ eos_token }}"
    "{% endif %}{% endfor %}")

FAITHFUL = (
    "{% for m in messages %}<|{{ m['role'] }}|>\n{{ m['content'] }}<|end|>\n"
    "{% endfor %}"
    "{% if add_generation_prompt %}<|assistant|>\n{% endif %}")

#: A template that loses the system message in EVERY shape — the repair cannot
#: recover it, and training must be refused rather than attempted.
HOPELESS = (
    "{% for m in messages %}{% if m['role'] != 'system' %}"
    "<|{{ m['role'] }}|>{{ m['content'] }}{% endif %}{% endfor %}"
    "{% if add_generation_prompt %}<|assistant|>{% endif %}")

BASES = {
    "Qwen2.5-7B-Instruct": "Qwen/Qwen2.5-7B-Instruct",
    "Olmo-3-7B-Instruct": r"D:\models\allenai__Olmo-3-7B-Instruct",
    "Mistral-7B-Instruct-v0.3":
        r"D:\models\mistralai__Mistral-7B-Instruct-v0.3",
}


def _tok(template):
    from tokenizers import Tokenizer, models, pre_tokenizers
    from transformers import PreTrainedTokenizerFast
    vocab = {w: i for i, w in enumerate(
        ["<pad>", "</s>", "a", "b", "c"]
        + sorted(set((SYS + " " + USR + " " + ANS).split())))}
    tk = Tokenizer(models.WordLevel(vocab, unk_token="a"))
    tk.pre_tokenizer = pre_tokenizers.Whitespace()
    t = PreTrainedTokenizerFast(tokenizer_object=tk, eos_token="</s>",
                                pad_token="<pad>")
    t.chat_template = template
    return t


def _base(name):
    from transformers import AutoTokenizer
    try:
        return AutoTokenizer.from_pretrained(BASES[name])
    except Exception as exc:                                   # pragma: no cover
        pytest.skip("%s unavailable: %s" % (name, exc))


# ══ THE BUG, REPRODUCED SYNTHETICALLY ═══════════════════════════════════════

def test_a_shape_dependent_template_DROPS_the_system_message_in_the_train_shape():
    """⛔⛔ RUN 3a, CAUSE #2. And note the shape-dependence: the same template
    is faithful for (system, user), which is why a single-shape probe would have
    passed and proved nothing."""
    tok = _tok(LOSSY)
    assert template_drops(tok, MSGS) == ["system"]
    assert SYS in read_prompt(tok, SYS, USR), "the READ shape keeps it"


def test_the_repair_recovers_the_system_message_and_makes_the_prompt_a_PREFIX():
    """⭐ CLAIM B."""
    tok = _tok(LOSSY)
    text = train_text(tok, MSGS)
    assert SYS in text and USR in text and ANS in text
    assert text.startswith(read_prompt(tok, SYS, USR))
    assert prefix_compatible(tok, MSGS)


def test_a_FAITHFUL_template_is_returned_BYTE_IDENTICAL():
    """⛔⛔ CLAIM A. If the repair rewrote a working base's training text, every
    standing run would stop being comparable to the re-run — which is the whole
    reason the family axis exists."""
    tok = _tok(FAITHFUL)
    assert template_drops(tok, MSGS) == []
    assert train_text(tok, MSGS) == tok.apply_chat_template(MSGS, tokenize=False)


def test_a_template_that_loses_content_EVERYWHERE_is_REFUSED_not_trained():
    """⛔⛔ THE THIRD OUTCOME, AND THE ONE THAT MATTERS MOST. Falling back to
    "train on whatever survived" is exactly how this was lost twice. A prompt
    that has quietly forgotten its instruction must stop the run."""
    tok = _tok(HOPELESS)
    assert template_drops(tok, MSGS) == ["system"]
    with pytest.raises(PromptShapeRefused, match="DROPS system"):
        train_text(tok, MSGS)


def test_no_template_at_all_falls_back_to_plain_concatenation():
    tok = _tok(FAITHFUL)
    tok.chat_template = None
    text = train_text(tok, MSGS)
    assert SYS in text and USR in text and ANS in text


# ══ THE REAL BASES ══════════════════════════════════════════════════════════

@pytest.mark.parametrize("name", ["Qwen2.5-7B-Instruct", "Olmo-3-7B-Instruct"])
def test_the_STANDING_bases_training_text_DOES_NOT_MOVE(name):
    """⛔⛔ Qwen and OLMo have already produced findings. Their training text
    must be what it was, to the byte."""
    from act2_finetune import row_messages
    tok = _base(name)
    row = {"english": "the cold is heaping", "direction": "write",
           "scene": {"classes": ["cold"], "rel": "heap"}}
    m = row_messages(row)
    assert template_drops(tok, m) == []
    assert train_text(tok, m) == tok.apply_chat_template(m, tokenize=False)


def test_MISTRAL_was_broken_and_is_now_prefix_compatible():
    """⭐ The base the family axis rests on, on the real tokenizer."""
    from act2_finetune import row_messages
    tok = _base("Mistral-7B-Instruct-v0.3")
    row = {"english": "the cold is heaping", "direction": "write",
           "scene": {"classes": ["cold"], "rel": "heap"}}
    m = row_messages(row)
    legacy = tok.apply_chat_template(m, tokenize=False)
    assert m[0]["content"] not in legacy, "the template really does drop it"
    assert not legacy.startswith(read_prompt(tok, m[0]["content"],
                                             m[1]["content"])), \
        "and the legacy text really was NOT prefix-compatible"
    fixed = train_text(tok, m)
    assert m[0]["content"] in fixed
    assert prefix_compatible(tok, m)


@pytest.mark.parametrize("name", sorted(BASES))
def test_EVERY_direction_the_pipeline_emits_is_prefix_compatible(name):
    """⛔ Three system prompts exist (write / read / provoke) and the pipeline
    emits all three. Checking one shape is how a shape-dependent template
    passes."""
    from act2_finetune import SYSTEM, row_messages
    tok = _base(name)
    for direction in SYSTEM:
        row = {"english": "the cold is heaping", "direction": direction,
               "prompt": "tlix sen pon", "scene": {"root": "flix"}}
        m = row_messages(row)
        t = train_text(tok, m)
        assert m[0]["content"] in t, "%s/%s lost the system message" % (name, direction)
        assert prefix_compatible(tok, m), "%s/%s not prefix-compatible" % (name, direction)


# ══ THE READER AND THE TRAINER SHARE ONE FOLD ═══════════════════════════════

def test_the_BACKEND_uses_the_shared_read_prompt():
    """⛔⛔ The construction was spelled twice — once in `row_to_text`, once in
    `LocalBackend._prompt` — and the two disagreed on Mistral. Two spellings of
    one procedure are free to drift, and this pair did."""
    src = (_ROOT / "tools" / "act2_backends.py").read_text(encoding="utf-8")
    assert "return read_prompt(self.tok, system, user)" in src
    assert "add_generation_prompt=True" not in src, \
        "the backend must not re-spell the prompt construction"


def test_the_TRAINER_uses_train_text():
    src = (_ROOT / "tools" / "act2_finetune.py").read_text(encoding="utf-8")
    assert "return train_text(tok, row_messages(row))" in src
    # ⛔ A CALL, not the word. The first spelling of this assertion matched the
    # docstring that explains why the call is gone — a test that a comment can
    # satisfy is not a test.
    assert ".apply_chat_template(" not in src, \
        "the trainer must not call the template directly any more"
