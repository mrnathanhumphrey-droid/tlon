"""⛔⛔ MASK LABELS BY POSITION, NEVER BY TOKEN ID.

`DataCollatorForLanguageModeling(mlm=False)` builds its labels like this
(transformers 5.8.1, `torch_call`, verbatim):

    labels = batch["input_ids"].clone()
    if self.tokenizer.pad_token_id is not None:
        labels[labels == self.tokenizer.pad_token_id] = -100

That is a TOKEN-ID test standing in for a POSITION test. The two agree only
while the pad token is a token that never legitimately appears in the text.
`act2_finetune.py` does `if tok.pad_token is None: tok.pad_token = tok.eos_token`
— so on any base with no pad token of its own, pad BECOMES eos, and the line
above masks **every genuine end-of-sequence** along with the padding.

⛔ That destroyed run 3a (~$6): Mistral-7B-v0.3 has no pad token, so every real
`</s>` in the corpus was labelled -100, the model was never trained to STOP, it
generated to `max_new_tokens`, nothing parsed, and the diversity guard saw one
degenerate output for twelve different inputs. The weights were fine —
`fraction_changed` 0.99995, rms 3.166e-04 against Qwen's 3.118e-04. Training
worked; stopping was destroyed.

⭐⭐ AND THE LINE HAD NEVER FIRED. Qwen has a distinct pad token, so while Qwen
was the only base the substitution never happened. A held constant became a
variable the moment the base varied, and nothing said so — the exact thesis of
the campaign this harness was running, reproduced one level down inside the
harness itself.

⭐ THE FIX IS GENERAL, NOT A MISTRAL SPECIAL CASE. Padding is a fact about
POSITION, and the position is already known exactly: `attention_mask == 0`. Ask
the mask, not the vocabulary. This is correct whether or not pad equals eos, for
every base, and it leaves the standing runs comparable — Qwen and OLMo both have
distinct pad tokens whose ids never occur inside their formatted text, so by-id
and by-position already coincided for them and their labels do not move. That
last claim is not reasoned, it is asserted against the real tokenizers in
`tests/test_pad_eos_collator.py`.
"""
from __future__ import annotations

from typing import Sequence

#: The label value `CrossEntropyLoss(ignore_index=-100)` drops.
LABEL_IGNORE = -100


class CollatorRefused(RuntimeError):
    """⛔ Raised instead of falling back to the by-id path.

    The by-id path is the bug. A collator that cannot establish POSITION must
    refuse, never quietly degrade to the thing that cost a run.
    """


class EosMaskingRefused(RuntimeError):
    """⛔⛔ Raised when the eos probe cannot find a genuine eos to test.

    ⭐ THE REASON THIS IS AN ERROR AND NOT A PASS: "0 genuine end-of-sequence
    tokens found, 0 of them masked" reads as a clean bill of health while
    describing a corpus in which the model is not being taught to stop AT ALL.
    An unmeasured cell must never render as a passing one — the same rule that
    made an empty lag cell a named diagnosis rather than a `nan`.
    """


class PositionMaskedCollator:
    """`DataCollatorForLanguageModeling(mlm=False)`, with labels by POSITION.

    Delegates every bit of padding and tensor assembly to the upstream collator
    — the only thing overridden is the label construction, so nothing else
    about the batch can drift from what the standing runs saw.
    """

    #: ⛔⛔ THE ATTRIBUTE NAME IS LOAD-BEARING AND NOTHING SAID SO. `Trainer._save`
    #: reads it when no `processing_class` was passed:
    #:
    #:     elif (self.data_collator is not None
    #:           and hasattr(self.data_collator, "tokenizer")
    #:           and self.data_collator.tokenizer is not None):
    #:         self.data_collator.tokenizer.save_pretrained(output_dir)
    #:
    #: So every run in this arc saved its tokenizer ONLY because
    #: `DataCollatorForLanguageModeling` happens to expose `.tokenizer`. The
    #: first version of this class stored it as `.tok`, and run 3a's re-run
    #: trained for 62 minutes and then died at F-LOCAL on a model directory
    #: with no tokenizer in it — the collator had been doubling as the
    #: tokenizer's carrier, and swapping the collator broke a dependency
    #: nothing named. ⭐ The real repair is `act2_finetune.py` saving the
    #: tokenizer EXPLICITLY; this attribute is defence in depth, so the
    #: upstream path keeps working for any other caller.
    def __init__(self, tok, *, pad_to_multiple_of=None):
        from transformers import DataCollatorForLanguageModeling
        self.tokenizer = tok
        self._inner = DataCollatorForLanguageModeling(
            tok, mlm=False, pad_to_multiple_of=pad_to_multiple_of)

    @property
    def tok(self):
        """Alias — the internal name this class used before the save path
        above was understood. Kept so both spellings mean one object."""
        return self.tokenizer

    def __call__(self, examples, return_tensors=None):
        return self.torch_call(examples)

    def torch_call(self, examples):
        batch = self._inner.torch_call(examples)
        am = batch.get("attention_mask")
        if am is None:
            raise CollatorRefused(
                "⛔⛔ no `attention_mask` in the batch, so PADDING POSITION is "
                "not knowable. Refusing rather than falling back to masking by "
                "token id — that fallback is the bug this class exists to "
                "retire (run 3a, Mistral-7B-v0.3, ~$6).")
        labels = batch["input_ids"].clone()
        labels[am == 0] = LABEL_IGNORE
        batch["labels"] = labels
        return batch


def eos_label_probe(tok, texts: Sequence[str], *, max_length: int,
                    collator=None) -> dict:
    """⭐ Does a genuine end-of-sequence survive masking? Return the EVIDENCE.

    Not a boolean — the caller gets the token ids, the counts, and the per-text
    verdict, so a refusal can say which text and which token.

    `texts` must be the SAME strings training tokenizes (`row_to_text`), and
    `max_length` the SAME `--seq`: an eos that survives masking in a probe but
    is truncated away in training is not the thing being asked about.
    """
    import torch

    if tok.pad_token is None:                     # exactly what training does
        tok.pad_token = tok.eos_token
    eos_id = tok.eos_token_id
    if eos_id is None:
        raise EosMaskingRefused(
            "⛔⛔ tokenizer has no eos_token_id — there is no stop token to "
            "train, and no claim about stopping can be made.")

    enc = [tok(t, truncation=True, max_length=max_length) for t in texts]
    batch = (collator or PositionMaskedCollator(tok)).torch_call(enc)
    ids, am, lab = batch["input_ids"], batch["attention_mask"], batch["labels"]

    genuine = (ids == eos_id) & (am == 1)
    n_genuine = int(genuine.sum())
    if n_genuine == 0:
        raise EosMaskingRefused(
            "⛔⛔ NOT ONE GENUINE eos (%r, id %s) IN %d TEXTS AT max_length=%d. "
            "This is not a pass — it describes a corpus that never teaches the "
            "model to stop, either because the chat template emits no eos or "
            "because truncation cuts it off. An unmeasured cell must never "
            "render as a passing one."
            % (tok.eos_token, eos_id, len(texts), max_length))

    masked = genuine & (lab == LABEL_IGNORE)
    per_text = [int(genuine[i].sum()) for i in range(ids.shape[0])]
    return {
        "pad_token": tok.pad_token, "pad_token_id": tok.pad_token_id,
        "eos_token": tok.eos_token, "eos_token_id": eos_id,
        "pad_is_eos": tok.pad_token_id == eos_id,
        "n_texts": len(texts),
        "n_genuine_eos": n_genuine,
        "n_genuine_eos_MASKED": int(masked.sum()),
        "texts_with_no_genuine_eos": [i for i, n in enumerate(per_text) if not n],
        "label_at_first_genuine_eos": int(lab[genuine][0]),
        "n_pad_positions": int((am == 0).sum()),
        "n_pad_positions_masked": int((lab[am == 0] == LABEL_IGNORE).sum()),
        "ok": int(masked.sum()) == 0,
    }
