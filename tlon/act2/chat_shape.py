"""⛔⛔ ONE FOLD FOR THE PROMPT, AND NO MESSAGE MAY VANISH INTO A TEMPLATE.

Run 3a was fired twice against Mistral-7B-Instruct-v0.3 and neither attempt
produced a datapoint. The second failure was this: **Mistral's chat template
silently drops the system message — but only in the TRAIN shape.**

    TRAIN  (system, user, assistant)        '<s>[INST] USER[/INST] ASSIST</s>'
    READ   (system, user, +gen prompt)      '<s>[INST] SYSTEM\\n\\nUSER[/INST]'

⭐ Measured, not inferred. Qwen and OLMo are ChatML and carry a native `system`
role in every shape. Mistral v0.3 has no system role at all and its template
IMPROVISES — merging the system text into the first `[INST]` when the last
message is the user's, and discarding it when an assistant turn follows.

⛔ So the model was TRAINED on prompts with no instruction and READ with prompts
carrying an instruction it had never seen. That is not a missing instruction, it
is a train/read DISTRIBUTION MISMATCH, and it explains every number in the run:
`choose` 256/256 unanswered (the whole task lives in the system message),
`speak` 0 % (trained without "Emit ONLY a JSON Scene object", and 64/64 outputs
parse after dropping one stray brace — 36 distinct, a fluent speaker), `render`
57.8 % (the only axis whose content sits in the USER turn, so it survives).

⛔⛔ AND IT IS THE THIRD INSTANCE OF ONE CLASS. The loader assumed a causal LM
(Ministral-3), the tokenizer assumed pad != eos (Mistral), the template assumed
a native ChatML system role (Mistral). Every one is a Qwen-shaped assumption
that a different base trips in silence.

THE REPAIR, AND WHY IT IS SHAPED THIS WAY:

  1. A base whose template carries every message is left ALONE — byte-identical.
     Qwen and OLMo's standing runs must not move, and the cross-family
     comparison rests on that, so it is asserted rather than argued.
  2. A base whose template DROPS content has its training text rebuilt as
     `read_prompt + answer + eos`, so the training text CONTAINS the read prompt
     as a literal prefix. Prefix-compatibility then holds BY CONSTRUCTION rather
     than by luck — which is the only version of this fix that also protects the
     fourth base nobody has tried yet.
  3. A base where even that loses content is REFUSED. A prompt that quietly
     forgets its instruction is the failure this module exists to end, and
     falling back to "train on whatever survived" is how it happened twice.
"""
from __future__ import annotations


class PromptShapeRefused(RuntimeError):
    """⛔ Raised rather than training on a prompt that lost its instruction."""


def _missing(text: str, msgs) -> list[str]:
    """-> roles whose content does NOT appear in `text`.

    ⭐ Substring containment, deliberately weak. A template may re-wrap, indent
    or re-order content and still be faithful; what it may NOT do is drop it.
    The check is for LOSS, not for layout.
    """
    out = []
    for m in msgs:
        c = (m.get("content") or "").strip()
        if c and c not in text:
            out.append(m.get("role", "?"))
    return out


def template_drops(tok, msgs) -> list[str]:
    """-> the roles this tokenizer's template loses for THIS message shape.

    ⭐ Shape-dependent by design: Mistral's template is faithful for
    `(system, user)` and lossy for `(system, user, assistant)`, so a single
    probe on one shape would have passed and proved nothing.
    """
    if not getattr(tok, "chat_template", None):
        return []
    return _missing(tok.apply_chat_template(msgs, tokenize=False), msgs)


def read_prompt(tok, system: str, user: str) -> str:
    """The string a READ sends to the model, before its answer.

    ⛔ Unchanged behaviour for every base — this is the construction
    `LocalBackend._prompt` already used, lifted here so the trainer and the
    reader cannot drift apart again.
    """
    msgs = [{"role": "system", "content": system},
            {"role": "user", "content": user}]
    if getattr(tok, "chat_template", None):
        return tok.apply_chat_template(msgs, tokenize=False,
                                       add_generation_prompt=True)
    return "%s\n\n%s\n\n" % (system, user)


def train_text(tok, msgs) -> str:
    """The literal string a training row becomes. Loss-free or it raises.

    `msgs` is `(system, user, assistant)`.
    """
    if len(msgs) != 3:
        raise PromptShapeRefused(
            "expected (system, user, assistant), got %d messages" % len(msgs))
    system, user, answer = (m.get("content") or "" for m in msgs)

    if not getattr(tok, "chat_template", None):
        return "%s\n\n%s\n\n%s" % (system, user, answer)

    native = tok.apply_chat_template(msgs, tokenize=False)
    lost = _missing(native, msgs)
    if not lost:
        # ⭐ THE BASE IS ALREADY FAITHFUL — RETURN ITS OWN TEMPLATE OUTPUT,
        # BYTE FOR BYTE. Qwen's differs from the reconstruction below by a
        # single trailing newline, and OLMo's is identical; rebuilding either
        # would move a standing run's training text for no reason. Repair only
        # what is broken.
        return native

    # ⛔ The template lost something. Rebuild so the READ PROMPT IS A PREFIX.
    repaired = read_prompt(tok, system, user) + answer + (tok.eos_token or "")
    still = _missing(repaired, msgs)
    if still:
        raise PromptShapeRefused(
            "⛔⛔ THIS TOKENIZER'S CHAT TEMPLATE DROPS %s AND THE REPAIR DOES "
            "NOT RECOVER %s. Training on what survived is exactly how run 3a "
            "was lost twice: the model would learn a prompt shape the reader "
            "never sends. Fix the template or give this base an explicit "
            "formatter — do not train." % (", ".join(lost), ", ".join(still)))
    return repaired


def prefix_compatible(tok, msgs) -> bool:
    """⭐ Does training see, as a literal prefix, what the reader will send?

    The deep invariant. `speak`, `render` and `choose` all send
    `read_prompt(...)` and expect the answer to continue it; if the training
    text does not begin with that string, the model is being read
    out-of-distribution no matter how good it is.
    """
    system, user = (m.get("content") or "" for m in msgs[:2])
    return train_text(tok, msgs).startswith(read_prompt(tok, system, user))
