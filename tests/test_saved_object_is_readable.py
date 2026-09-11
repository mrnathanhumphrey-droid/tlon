"""⛔⛔ A TRAINED OBJECT THAT CANNOT BE RE-OPENED IS NOT A RESULT.

Run 3a's re-run trained 62 clean minutes on an H100 — `verdict OK`,
`fraction_changed` 0.99995, dose 101.2 % of Qwen — and then died at F-LOCAL
because the saved model directory contained NO TOKENIZER. The error surfaced
two stages downstream as a sentencepiece complaint that named nothing to do
with the cause.

THE MECHANISM, from `Trainer._save`:

    if self.processing_class is not None:
        self.processing_class.save_pretrained(output_dir)
    elif (self.data_collator is not None
          and hasattr(self.data_collator, "tokenizer")
          and self.data_collator.tokenizer is not None):
        self.data_collator.tokenizer.save_pretrained(output_dir)

`processing_class` is never set by `act2_finetune.py`. So for this entire arc
the tokenizer was saved as a SIDE EFFECT of `DataCollatorForLanguageModeling`
happening to expose `.tokenizer` — an unrecorded dependency with the collator
doubling as the tokenizer's carrier. Swapping the collator broke it silently.

⛔⛔ AND THE EXISTING RED-PROOF DID NOT CATCH IT. `test_pad_eos_collator.py`
asserts the trainer CONSTRUCTS the new collator — the "assert the consumer uses
the fix" discipline — but stopped one level short of "assert the run still
produces what the next stage needs". A fix can be correctly wired and still
break the artifact. So the test below trains a real (tiny) model through a real
`Trainer` and re-opens what it wrote, rather than inspecting source.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

from tlon.act2.collator import PositionMaskedCollator                # noqa: E402

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

VOCAB = {"<pad>": 0, "</s>": 1, "a": 2, "b": 3, "c": 4, "d": 5}


def _tok(pad_is_eos=True):
    from tokenizers import Tokenizer, models, pre_tokenizers
    from transformers import PreTrainedTokenizerFast
    tk = Tokenizer(models.WordLevel(VOCAB, unk_token="a"))
    tk.pre_tokenizer = pre_tokenizers.Whitespace()
    return PreTrainedTokenizerFast(
        tokenizer_object=tk, eos_token="</s>",
        pad_token=("</s>" if pad_is_eos else "<pad>"))


def _tiny_model():
    from transformers import LlamaConfig, LlamaForCausalLM
    return LlamaForCausalLM(LlamaConfig(
        vocab_size=len(VOCAB), hidden_size=32, intermediate_size=64,
        num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=2,
        max_position_embeddings=32))


def _train(out, tok, collator):
    """A real `Trainer`, on CPU, for two steps. ⭐ The point is the SAVE PATH,
    which no amount of source-reading can settle."""
    from transformers import Trainer, TrainingArguments
    rows = ["a b c </s>", "b c d </s>", "a d </s>", "c c b </s>"]
    ds = [tok(r, truncation=True, max_length=16) for r in rows]
    ds = [{k: v for k, v in e.items()} for e in ds]
    trainer = Trainer(
        model=_tiny_model(), train_dataset=ds, data_collator=collator,
        args=TrainingArguments(
            output_dir=str(out), max_steps=2, per_device_train_batch_size=2,
            report_to=[], save_strategy="no", logging_strategy="no",
            use_cpu=True, learning_rate=1e-4))
    trainer.train()
    trainer.save_model(str(out))
    return trainer


def test_the_OLD_collator_saved_the_tokenizer_as_a_SIDE_EFFECT(tmp_path):
    """⛔⛔ THE DEPENDENCY, MADE VISIBLE. This is why it worked for the whole
    arc and why nothing recorded that it was working by accident."""
    from transformers import DataCollatorForLanguageModeling
    tok = _tok()
    out = tmp_path / "old"
    _train(out, tok, DataCollatorForLanguageModeling(tok, mlm=False))
    assert (out / "tokenizer.json").exists(), \
        "the upstream collator carries .tokenizer and Trainer saves it"


def test_a_collator_WITHOUT_a_tokenizer_attribute_saves_NO_TOKENIZER(tmp_path):
    """⛔⛔ RUN 3a's RE-RUN, REPRODUCED IN TWO SECONDS ON A CPU. The exact
    failure that cost 62 H100-minutes, and the shape of it: training succeeds,
    the save succeeds, and the directory is unreadable."""
    tok = _tok()
    c = PositionMaskedCollator(tok)
    del c.tokenizer                       # the `.tok`-only version of the class
    assert not hasattr(c, "tokenizer")
    out = tmp_path / "broken"
    _train(out, tok, c)
    assert (out / "model.safetensors").exists(), "the WEIGHTS still save fine"
    assert not (out / "tokenizer.json").exists(), \
        "and the tokenizer silently does not — trained, saved, unreadable"


def test_the_FIXED_collator_saves_a_tokenizer_that_RE_OPENS(tmp_path):
    """⭐ THE CLAIM THAT MATTERS, end to end: train, save, re-open."""
    from transformers import AutoTokenizer
    tok = _tok()
    out = tmp_path / "fixed"
    _train(out, tok, PositionMaskedCollator(tok))
    back = AutoTokenizer.from_pretrained(str(out))
    assert back.eos_token_id == tok.eos_token_id
    assert back("a b c </s>")["input_ids"] == tok("a b c </s>")["input_ids"]


def test_the_collator_exposes_tokenizer_and_tok_as_ONE_object():
    tok = _tok()
    c = PositionMaskedCollator(tok)
    assert c.tokenizer is tok and c.tok is tok


# ══ THE EXPLICIT SAVE, WHICH IS THE REAL REPAIR ═════════════════════════════

def test_the_TRAINER_TOOL_saves_the_tokenizer_EXPLICITLY_and_READS_IT_BACK():
    """⛔ Defence in depth is not the fix. `.tokenizer` restores the upstream
    behaviour, but the run must not DEPEND on what Trainer infers — so the tool
    saves it itself and proves the directory re-opens before going further."""
    src = (_ROOT / "tools" / "act2_finetune.py").read_text(encoding="utf-8")
    i = src.index("trainer.save_model(a.out)")
    after = src[i:i + 1600]
    assert "tok.save_pretrained(a.out)" in after
    assert "AutoTokenizer" in after and "from_pretrained(a.out)" in after
    assert "CANNOT BE RE-OPENED" in after


# ══ PERSIST MUST REFUSE A TOKENIZER-LESS OBJECT ═════════════════════════════

def _stage(d, *, tokenizer: bool):
    d.mkdir(parents=True, exist_ok=True)
    (d / "config.json").write_text("{}", encoding="utf-8")
    (d / "factorial.json").write_text("{}", encoding="utf-8")
    (d / "weight_delta.json").write_text(
        json.dumps({"verdict": "OK", "fraction_changed": 0.99}),
        encoding="utf-8")
    (d / "model.safetensors").write_bytes(b"0")
    if tokenizer:
        (d / "tokenizer_config.json").write_text("{}", encoding="utf-8")
        (d / "tokenizer.json").write_text("{}", encoding="utf-8")


def test_persist_REFUSES_a_full_weight_object_with_no_tokenizer(tmp_path):
    """⛔⛔ THE VACUOUS PASS THAT LET IT THROUGH. `persist_leg1` reported
    '✅ persisted: 6 files' for a model nothing could open, because the
    tokenizer sat in the OPTIONAL set beside `generation_config.json`."""
    import act2_box_persist as B
    root = tmp_path / "run"
    _stage(root / "model_cellx", tokenizer=False)
    with pytest.raises(B.TransferError, match="NO TOKENIZER"):
        B.full_weight_preflight(root, "cellx")


def test_persist_ACCEPTS_the_same_object_once_it_has_one(tmp_path):
    """⭐ The refusal must be about the tokenizer and nothing else."""
    import act2_box_persist as B
    root = tmp_path / "run"
    _stage(root / "model_celly", tokenizer=True)
    B.full_weight_preflight(root, "celly")


def test_a_base_that_writes_a_SENTENCEPIECE_vocab_is_accepted(tmp_path):
    """⛔ The requirement is CONFIG + ANY vocabulary file. Demanding
    `tokenizer.json` by name would refuse a readable object from a family that
    spells its vocabulary differently — a guard that fails the thing it is
    supposed to protect."""
    import act2_box_persist as B
    root = tmp_path / "run"
    d = root / "model_cellz"
    _stage(d, tokenizer=False)
    (d / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (d / "tokenizer.model").write_bytes(b"0")
    B.full_weight_preflight(root, "cellz")
