"""⛔⛔ RED-PROOF FOR THE PAD/EOS COLLATOR — the bug that cost run 3a.

Two claims, and BOTH have to hold or the fix is worse than the bug:

  A. With pad == eos, a genuine end-of-sequence must NOT be masked.
     (The fix works. Mistral-7B-v0.3 can be trained to stop.)

  B. With pad != eos, the labels must be BYTE-IDENTICAL to what the old
     by-id collator produced.
     (The standing runs are untouched. If position-masking moved a single
     label for Qwen or OLMo, their runs would no longer be comparable to a
     re-run Mistral and the whole cross-family comparison would break — the
     comparability claim is load-bearing, so it is asserted, not reasoned.)

⭐ Both are checked against the REAL tokenizers of the three campaign bases,
not stand-ins, wherever those tokenizers are on disk. A synthetic pad==eos
tokenizer covers the mechanism on any machine so the class can never go
unproven.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

from tlon.act2.collator import (LABEL_IGNORE, CollatorRefused,   # noqa: E402
                                EosMaskingRefused,
                                PositionMaskedCollator, eos_label_probe)

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

TEXTS = ["a b c </s>", "a </s>", "b b b b c </s>"]

#: The three campaign bases, by where they actually sit on this machine.
BASES = {
    "Qwen2.5-7B-Instruct": "Qwen/Qwen2.5-7B-Instruct",
    "Olmo-3-7B-Instruct": r"D:\models\allenai__Olmo-3-7B-Instruct",
    "Mistral-7B-Instruct-v0.3": r"D:\models\mistralai__Mistral-7B-Instruct-v0.3",
}


def _tiny(pad_is_eos: bool):
    """A real `PreTrainedTokenizerFast` over a five-word vocabulary."""
    from tokenizers import Tokenizer, models, pre_tokenizers
    from transformers import PreTrainedTokenizerFast
    vocab = {"<pad>": 0, "</s>": 1, "a": 2, "b": 3, "c": 4}
    tk = Tokenizer(models.WordLevel(vocab, unk_token="a"))
    tk.pre_tokenizer = pre_tokenizers.Whitespace()
    return PreTrainedTokenizerFast(
        tokenizer_object=tk, eos_token="</s>",
        pad_token=("</s>" if pad_is_eos else "<pad>"))


def _base(name):
    from transformers import AutoTokenizer
    src = BASES[name]
    try:
        return AutoTokenizer.from_pretrained(src)
    except Exception as exc:                                   # pragma: no cover
        pytest.skip("%s tokenizer unavailable here: %s" % (name, exc))


def _encode(tok, texts, max_length=64):
    return [tok(t, truncation=True, max_length=max_length) for t in texts]


def _old_labels(tok, enc):
    """Labels exactly as `DataCollatorForLanguageModeling(mlm=False)` built
    them — the code that shipped every run in the arc."""
    from transformers import DataCollatorForLanguageModeling
    return DataCollatorForLanguageModeling(tok, mlm=False).torch_call(
        [dict(e) for e in enc])["labels"]


# ══ A · THE FIX WORKS ═══════════════════════════════════════════════════════

def test_with_pad_EQUAL_eos_the_OLD_collator_masks_every_genuine_stop():
    """⛔⛔ RUN 3a, REPRODUCED. This is the test asserting the BUG is real —
    without it, claim A could pass against a collator that never had anything
    to fix."""
    tok = _tiny(pad_is_eos=True)
    enc = _encode(tok, TEXTS)
    old = _old_labels(tok, enc)
    ids = PositionMaskedCollator(tok).torch_call(enc)["input_ids"]
    am = PositionMaskedCollator(tok).torch_call(enc)["attention_mask"]
    genuine = (ids == tok.eos_token_id) & (am == 1)
    assert int(genuine.sum()) == 3, "one genuine eos per text"
    assert int((old[genuine] == LABEL_IGNORE).sum()) == 3, \
        "the old collator masked ALL THREE — the model is never taught to stop"


def test_with_pad_EQUAL_eos_the_NEW_collator_TRAINS_every_genuine_stop():
    """⭐ CLAIM A."""
    tok = _tiny(pad_is_eos=True)
    enc = _encode(tok, TEXTS)
    b = PositionMaskedCollator(tok).torch_call(enc)
    genuine = (b["input_ids"] == tok.eos_token_id) & (b["attention_mask"] == 1)
    assert int((b["labels"][genuine] == LABEL_IGNORE).sum()) == 0
    assert (b["labels"][genuine] == tok.eos_token_id).all()


def test_pad_POSITIONS_are_still_all_ignored():
    """⛔ The fix must not swing the other way and train padding as content."""
    tok = _tiny(pad_is_eos=True)
    b = PositionMaskedCollator(tok).torch_call(_encode(tok, TEXTS))
    pad = b["attention_mask"] == 0
    assert int(pad.sum()) > 0, "the batch must actually contain padding"
    assert (b["labels"][pad] == LABEL_IGNORE).all()


def test_a_pad_id_that_appears_as_REAL_CONTENT_is_trained_not_masked():
    """⭐ THE DIFFERENCE BETWEEN THE TWO RULES, ISOLATED. By-id masks the token
    wherever it occurs; by-position masks only what the mask says is padding.
    This is the ONE case where the two genuinely disagree, and the by-position
    answer is the correct one."""
    tok = _tiny(pad_is_eos=True)
    enc = _encode(tok, ["a </s> b", "a b c"])       # eos in the MIDDLE
    new = PositionMaskedCollator(tok).torch_call(enc)["labels"]
    old = _old_labels(tok, enc)
    assert old[0][1] == LABEL_IGNORE
    assert new[0][1] == tok.eos_token_id


def test_a_batch_without_an_attention_mask_is_REFUSED_not_degraded():
    """⛔⛔ NEVER FALL BACK TO THE BY-ID PATH. The fallback is the bug."""
    tok = _tiny(pad_is_eos=True)
    c = PositionMaskedCollator(tok)
    inner = c._inner.torch_call

    def _strip(examples):
        b = inner(examples)
        b.pop("attention_mask")
        return b

    c._inner.torch_call = _strip
    with pytest.raises(CollatorRefused, match="PADDING POSITION"):
        c.torch_call(_encode(tok, TEXTS))


# ══ B · THE STANDING RUNS DO NOT MOVE ═══════════════════════════════════════

@pytest.mark.parametrize("name", ["Qwen2.5-7B-Instruct", "Olmo-3-7B-Instruct"])
def test_labels_are_BYTE_IDENTICAL_for_the_bases_that_were_never_affected(name):
    """⛔⛔ CLAIM B, ON THE REAL TOKENIZERS. Qwen and OLMo have distinct pad
    tokens whose ids never occur inside their formatted text, so by-id and
    by-position already agreed for them. The cross-family comparison rests on
    that, so it is MEASURED rather than argued."""
    from act2_finetune import row_to_text
    tok = _base(name)
    assert tok.pad_token_id != tok.eos_token_id, \
        "this base was never affected — that is the premise being tested"
    rows = [{"english": "the cold is heaping", "direction": d,
             "scene": {"classes": ["cold"], "rel": "heap"}}
            for d in ("write", "read", "write")]
    enc = _encode(tok, [row_to_text(r, tok) for r in rows], max_length=192)
    new = PositionMaskedCollator(tok).torch_call(enc)["labels"]
    old = _old_labels(tok, enc)
    assert torch.equal(new, old), "%s labels MOVED — the standing run is no " \
                                  "longer comparable" % name


def test_the_synthetic_unaffected_case_is_also_identical():
    """⭐ Claim B without needing any base on disk."""
    tok = _tiny(pad_is_eos=False)
    enc = _encode(tok, TEXTS)
    assert torch.equal(PositionMaskedCollator(tok).torch_call(enc)["labels"],
                       _old_labels(tok, enc))


# ══ THE PROBE ═══════════════════════════════════════════════════════════════

def test_the_probe_REFUSES_when_there_is_no_genuine_eos_to_test():
    """⛔⛔ AN UNMEASURED CELL MUST NEVER RENDER AS A PASSING ONE. "0 genuine
    eos, 0 masked" is arithmetically a pass and describes a corpus that never
    teaches the model to stop. Same rule that made an empty lag cell a named
    diagnosis instead of a `nan`."""
    tok = _tiny(pad_is_eos=True)
    with pytest.raises(EosMaskingRefused, match="NOT ONE GENUINE eos"):
        eos_label_probe(tok, ["a b c", "b c"], max_length=64)


def test_the_probe_catches_truncation_eating_the_eos():
    """⛔ An eos the corpus HAS but `--seq` cuts off is the same failure with a
    different cause, and the probe must see it at the training max_length."""
    tok = _tiny(pad_is_eos=True)
    with pytest.raises(EosMaskingRefused, match="max_length=2"):
        eos_label_probe(tok, ["a b c </s>", "b b b </s>"], max_length=2)


def test_the_probe_reports_the_evidence_not_a_boolean():
    tok = _tiny(pad_is_eos=True)
    ev = eos_label_probe(tok, TEXTS, max_length=64)
    assert ev["ok"] and ev["pad_is_eos"]
    assert ev["n_genuine_eos"] == 3 and ev["n_genuine_eos_MASKED"] == 0
    assert ev["label_at_first_genuine_eos"] == tok.eos_token_id
    assert ev["n_pad_positions"] == ev["n_pad_positions_masked"] > 0


@pytest.mark.parametrize("name", sorted(BASES))
def test_every_campaign_base_passes_the_probe_on_REAL_corpus_FORMATTING(name):
    """⭐ The end-to-end claim, per base: the string training actually
    tokenizes, through the collator training actually uses."""
    from act2_finetune import row_to_text
    tok = _base(name)
    rows = [{"english": "the cold is heaping", "direction": "write",
             "scene": {"classes": ["cold"], "rel": "heap"}},
            {"english": "it moons", "direction": "read",
             "scene": {"classes": ["moon"], "rel": "shine"}}]
    ev = eos_label_probe(tok, [row_to_text(r, tok) for r in rows],
                         max_length=192)
    assert ev["n_genuine_eos_MASKED"] == 0, \
        "%s: %d genuine eos masked — %s" % (name, ev["n_genuine_eos_MASKED"], ev)


# ══ THE TOOL ACTUALLY USES IT ═══════════════════════════════════════════════

def test_the_TRAINER_ACTUALLY_USES_the_position_masked_collator():
    """⛔⛔ DEFECT-Q, THE SECOND TIME. Deleting the resolving-power check from
    `act2_model_lag.py` once left this suite GREEN because every test exercised
    the library module directly. A fix that lives only in `tlon/` and is not
    wired into the tool is not a fix — so the wiring itself is asserted."""
    src = (_ROOT / "tools" / "act2_finetune.py").read_text(encoding="utf-8")
    assert "data_collator=PositionMaskedCollator(tok)" in src
    assert "DataCollatorForLanguageModeling(" not in src, \
        "the by-id collator is constructed somewhere in the trainer path"


def test_the_pad_eos_substitution_is_no_longer_SILENT():
    """⭐ The line never fired while Qwen was the only base, so no log in the
    arc records it. A default that is never printed is a decision nobody made."""
    src = (_ROOT / "tools" / "act2_finetune.py").read_text(encoding="utf-8")
    i = src.index("tok.pad_token = tok.eos_token")
    assert "print(" in src[i:i + 400]
    assert "pad_is_eos" in src


def test_the_preflight_guard_is_wired_into_the_pipeline():
    """⛔ Every preflight passed before 3a died because none of them touched the
    tokenizer. This one must actually run, and BEFORE the training leg."""
    pipe = (_ROOT / "tools" / "pipeline_fullft.sh").read_text(encoding="utf-8")
    assert "step eos_guard" in pipe
    assert pipe.index("step eos_guard") < pipe.index("step train_leg1"), \
        "a preflight after the training leg is not a preflight"
    assert "act2_eos_guard.py" in pipe


@pytest.mark.skipif(
    not (_ROOT / "runs/act2/retrain12_ct/corpus_ct-s20624/train.jsonl").exists(),
    reason="no built corpus on this machine")
def test_the_GUARD_TOOL_passes_on_a_real_corpus_with_the_MISTRAL_tokenizer():
    """⭐⭐ THE WHOLE THING, END TO END, ON THE BASE THAT DIED: real corpus rows,
    real `row_to_text`, real Mistral tokenizer with no pad token of its own."""
    import act2_eos_guard
    _base("Mistral-7B-Instruct-v0.3")            # skip early if unavailable
    rc = act2_eos_guard.main([
        "--model", BASES["Mistral-7B-Instruct-v0.3"],
        "--corpus", str(_ROOT / "runs/act2/retrain12_ct/corpus_ct-s20624"),
        "--seq", "192", "--rows", "16"])
    assert rc == 0
