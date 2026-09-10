"""⛔⛔ A MULTIMODAL BASE HAS TWO LAYER STACKS, AND POOLING THEM IS SILENT.

The campaign varies the BASE MODEL, and the scope doc pre-declared that the
scope "must be verified against each base's real tensors". This is that check,
and it caught a live one on the first candidate.

`mistralai/Ministral-3-8B-Instruct-2512-BF16` carries TWO stacks:

    language_model.model.layers.0..33      (the text model)
    vision_tower.transformer.layers.0..23  (an image encoder)

`_LAYER_RE` matches both, so the pooled index set was **0..33 — contiguous**.
Every existing guard passed: non-empty, contiguous, `unfreeze_top` in range. And
`full_weight_scope(unfreeze_top=14)` then unfroze text layers 20-33 **plus 36
vision-tower tensors**, training an image encoder as part of the language model.

⭐ The regex was never wrong. The SCOPE WIDENED to bases with more than one
stack and the rule needed re-deriving rather than stretching — the same lesson
`scope_mode` learned when the training locus widened to a second site.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from tlon.act2.full_weight import (ScopeError, full_weight_scope,   # noqa: E402
                                   layer_indices, layer_stacks)


#: ⭐ The REAL tensor names, copied from each base's `model.safetensors.index`.
#: Shapes only — enough to exercise the selector without a 17 GB download.
def _causal(prefix, n_layers):
    out = ["%s.embed_tokens.weight" % prefix, "lm_head.weight",
           "%s.norm.weight" % prefix]
    for i in range(n_layers):
        for leaf in ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj",
                     "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj",
                     "mlp.down_proj"):
            out.append("%s.layers.%d.%s.weight" % (prefix, i, leaf))
    return out


QWEN = _causal("model", 28)
OLMO = _causal("model", 32)
#: ⛔ The real index puts `lm_head` at `language_model.lm_head.weight` -- one
#: level ABOVE `embed_tokens`. Copied, not guessed: the first version of this
#: fixture used the bare `lm_head.weight` that Qwen and OLMo have, and it made
#: the leaf-depth test pass for the wrong reason.
MISTRAL3 = ([n for n in _causal("language_model.model", 34)
             if n != "lm_head.weight"]
            + ["language_model.lm_head.weight"]
            + ["vision_tower.transformer.layers.%d.attention.%s.weight" % (i, p)
               for i in range(24)
               for p in ("q_proj", "k_proj", "v_proj", "o_proj")]
            + ["multi_modal_projector.linear_1.weight"])


def test_a_single_stack_base_is_unchanged():
    """⛔⛔ THE REGRESSION GUARD. Qwen is the arc's whole substrate; if this
    moved, every fired run's scope moved with it."""
    assert layer_stacks(QWEN) == {"model": set(range(28))}
    assert layer_indices(QWEN) == set(range(28))
    sc = full_weight_scope(QWEN, unfreeze_top=14)
    assert len(sc["trainable"]) == 14 * 7
    assert all("layers." in n for n in sc["trainable"])


def test_the_two_stacks_are_reported_SEPARATELY():
    """⭐ One entry per stack, keyed by the prefix that precedes `layers.N.`."""
    st = layer_stacks(MISTRAL3)
    assert set(st) == {"language_model.model", "vision_tower.transformer"}
    assert st["language_model.model"] == set(range(34))
    assert st["vision_tower.transformer"] == set(range(24))


def test_the_POOLED_indices_LOOK_CONTIGUOUS_which_is_why_this_was_silent():
    """⛔⛔ THE REASON NO EXISTING GUARD FIRED. 0..33 union 0..23 is 0..33 — a
    perfectly contiguous run starting at zero. The contiguity check, the
    non-empty check and the range check all PASS on a pooled set that mixes an
    image encoder into the language model."""
    pooled = set()
    for v in layer_stacks(MISTRAL3).values():
        pooled |= v
    assert sorted(pooled) == list(range(34)), "the pooled set is contiguous"


def test_more_than_one_stack_is_REFUSED_not_pooled():
    with pytest.raises(ScopeError) as exc:
        layer_indices(MISTRAL3)
    msg = str(exc.value)
    assert "MORE THAN ONE TRANSFORMER-LAYER STACK" in msg
    # ⭐ Both stacks named with their sizes — a refusal that does not say WHICH
    # stacks it found leaves the reader to re-derive it.
    assert "language_model.model" in msg and "vision_tower.transformer" in msg
    assert "34 layers" in msg and "24 layers" in msg


def test_full_weight_scope_REFUSES_a_multimodal_base():
    """⛔⛔ THE BUG, AS IT WOULD HAVE SHIPPED: 36 vision tensors trained as text
    layers, with a green scope and a plausible parameter count."""
    with pytest.raises(ScopeError):
        full_weight_scope(MISTRAL3, unfreeze_top=14)


def test_naming_the_stack_makes_a_multimodal_base_usable():
    """⭐ The refusal is a demand for a decision, not a dead end — the text
    stack can be selected explicitly once someone has looked at it."""
    idx = layer_indices(MISTRAL3, stack="language_model.model")
    assert idx == set(range(34))
    with pytest.raises(ScopeError):
        layer_indices(MISTRAL3, stack="nope")


def test_OLMo_is_a_DROP_IN_for_the_Qwen_scope():
    """⭐ `Olmo3ForCausalLM` uses byte-for-byte the Qwen/Llama naming —
    `model.layers.N.`, `model.embed_tokens.weight`, `lm_head.weight` — so the
    layer rung needs no new code. Recorded because 'same family of names' is
    exactly the kind of thing that gets assumed and turns out false."""
    assert layer_stacks(OLMO) == {"model": set(range(32))}
    sc = full_weight_scope(OLMO, unfreeze_top=14)
    assert len(sc["trainable"]) == 14 * 7
    assert not [n for n in sc["trainable"] if "vision" in n]


def test_naming_the_stack_restricts_the_SELECTION_not_only_the_COUNT():
    """⛔⛔ THE HALF-FIX, GUARDED. Widening `layer_indices` alone fixed which
    layers were COUNTED and left the selection loop matching `_LAYER_RE` across
    every name — so `stack=` gave the right `n_layers` and STILL put 36
    vision-tower tensors in the trainable set. A correct count with a wrong
    scope is worse than an outright refusal, because it looks right.

    ⭐ Same shape as the pipeline branch that ignored a correct verdict: a guard
    the consumer does not apply is not a guard.
    """
    sc = full_weight_scope(MISTRAL3, unfreeze_top=14,
                           stack="language_model.model")
    assert sc["n_layers"] == 34
    assert not [n for n in sc["trainable"] if "vision" in n], \
        "vision-tower tensors leaked into the trainable set"
    assert all(n.startswith("language_model.model.layers.")
               for n in sc["trainable"])
    # 14 layers x 7 leaves in this fixture
    assert len(sc["trainable"]) == 14 * 7


def test_the_mapping_leaves_are_NOT_filtered_by_the_stack_prefix():
    """⛔ On Mistral 3 the two leaves sit at DIFFERENT depths —
    `language_model.model.embed_tokens.weight` but
    `language_model.lm_head.weight`. Filtering leaves by the layer stack's
    prefix would drop `lm_head` and quietly halve the declared scope."""
    from tlon.act2.full_weight import mapping_scope
    sc = mapping_scope(MISTRAL3, stack="language_model.model")
    got = sorted(sc["trainable"])
    assert got == ["language_model.lm_head.weight",
                   "language_model.model.embed_tokens.weight"]
    assert not [n for n in sc["trainable"] if "vision" in n]


def test_a_base_with_no_layers_at_all_still_refuses_the_old_way():
    """⛔ The empty case must not be swallowed by the new multi-stack path."""
    assert layer_indices(["embed_tokens.weight"]) == set()
    with pytest.raises(ScopeError):
        full_weight_scope(["embed_tokens.weight"], unfreeze_top=1)
