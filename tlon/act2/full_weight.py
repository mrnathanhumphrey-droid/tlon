"""WHICH WEIGHTS THIS FINE-TUNE MAY MOVE — the §5 scope, as a pure function.

PREREG `PREREG_FULL_FINETUNE_RELEASE_2026_09_05` (LOCK `a0450b36`) §5 declares:
`embed_tokens` and `lm_head` frozen (1.090 B, 14.3 % — two separate matrices,
`tie_word_embeddings: false`), the **top 14 of 28** transformer layers trainable
(3.263 B). That scope is not a runbook detail: it is what a STOP-floored would
be *about*, and §7.1's escalation ladder is written in terms of it.

⛔⛔ A SELECTOR THAT MATCHES NOTHING FREEZES EVERYTHING, AND A MODEL THAT TRAINS
NOTHING REPORTS A PERFECT ZERO DELTA. That is the exact shape of the failure the
§4.1 precondition exists to catch, arriving one step earlier: a renamed
parameter scheme, a different architecture, an off-by-one in the layer index,
and the run trains a frozen model to no effect and calls it a substrate floor.
So this refuses an empty or short selection rather than returning it.

⭐ NAME-BASED AND PURE. It takes parameter NAMES, not a model, so the scope can
be tested against the real Qwen2 naming without a GPU, a download, or torch.
"""
from __future__ import annotations

import re

#: `model.layers.<i>.self_attn.q_proj.weight` — the Qwen2 / Llama scheme.
_LAYER_RE = re.compile(r"(?:^|\.)layers\.(\d+)\.")

#: ⭐ Frozen by §5, matched on the leaf name so a wrapper prefix cannot hide one.
#: `lm_head` is listed explicitly BECAUSE it is untied — on a tied model it does
#: not appear as its own parameter and freezing `embed_tokens` covers both, but
#: this model is untied and the two must each be named.
FROZEN_LEAVES = ("embed_tokens", "lm_head")


class ScopeError(RuntimeError):
    """⛔ Raised, never warned."""


def layer_indices(names) -> set:
    """Every transformer-layer index present in the parameter names."""
    out = set()
    for n in names:
        m = _LAYER_RE.search(n)
        if m:
            out.add(int(m.group(1)))
    return out


def full_weight_scope(names, *, unfreeze_top: int,
                      frozen_leaves=FROZEN_LEAVES) -> dict:
    """Split parameter names into trainable and frozen per §5.

    ⛔ `model.norm` (the final RMSNorm, outside the layer stack) stays FROZEN.
    §5 says "top 14 of 28 transformer layers" and the 3.263 B it quotes is
    exactly 14 layers; folding in a tensor that is not one of them would make
    the trained set disagree with the locked number, by a little, silently.
    """
    names = list(names)
    if not names:
        raise ScopeError("no parameter names given")
    idx = layer_indices(names)
    if not idx:
        raise ScopeError(
            "no parameter name matched the transformer-layer pattern %r. A "
            "selector that matches nothing freezes the whole model, which "
            "trains to a perfect zero delta and reads as a substrate floor."
            % _LAYER_RE.pattern)
    n_layers = max(idx) + 1
    if sorted(idx) != list(range(n_layers)):
        raise ScopeError(
            "layer indices are not contiguous 0..%d (got %d distinct); the "
            "naming scheme is not what this scope assumes."
            % (n_layers - 1, len(idx)))
    if not 1 <= unfreeze_top <= n_layers:
        raise ScopeError(
            "unfreeze_top=%d outside 1..%d. Zero trains nothing and would "
            "report a zero delta; more than %d is not a subset."
            % (unfreeze_top, n_layers, n_layers))

    cutoff = n_layers - unfreeze_top
    trainable, frozen = [], []
    for n in names:
        # ⭐ Component match, not substring: a substring test would catch a
        # hypothetical `lm_head_proj` and freeze it by accident.
        parts = n.split(".")
        leaf_frozen = any(f in parts for f in frozen_leaves)
        m = _LAYER_RE.search(n)
        if m and not leaf_frozen and int(m.group(1)) >= cutoff:
            trainable.append(n)
        else:
            frozen.append(n)
    if not trainable:
        raise ScopeError(
            "scope selected 0 trainable tensors out of %d" % len(names))
    return {
        "n_layers": n_layers,
        "unfreeze_top": unfreeze_top,
        "cutoff_layer": cutoff,
        "trainable": trainable,
        "frozen": frozen,
    }


def apply_scope(model, *, unfreeze_top: int) -> dict:
    """Set `requires_grad` per §5 and cast the trainable set to fp32.

    ⛔⛔ THE fp32 CAST IS THE POINT, NOT AN OPTIMISATION. §4.1: under a bf16
    master a 1e-5 Adam step is 0.08 ulp at a typical Qwen weight and rounds to
    zero, so the optimizer writes nothing while appearing to train. The trainable
    tensors are therefore held in fp32 (where the same step is ~5,369 ulps) and
    the frozen ones stay bf16 — they receive no update, so their precision costs
    nothing and buys 11 GiB of the budget back.
    """
    import torch

    names = [n for n, _ in model.named_parameters()]
    scope = full_weight_scope(names, unfreeze_top=unfreeze_top)
    train = set(scope["trainable"])
    n_train = n_frozen = 0
    for name, p in model.named_parameters():
        if name in train:
            p.requires_grad_(True)
            if p.dtype != torch.float32:
                p.data = p.data.to(torch.float32)
            n_train += p.numel()
        else:
            p.requires_grad_(False)
            n_frozen += p.numel()
    # ⛔ ASSERT THE MUTATION, DO NOT ASSUME IT. `requires_grad_` on a tensor that
    # is a non-leaf, or a model wrapped in a way that re-creates parameters,
    # silently does nothing -- and the next observation would be a zero delta.
    live = sum(p.numel() for p in model.parameters() if p.requires_grad)
    if live != n_train:
        raise ScopeError(
            "requires_grad did not take: set %d trainable, model reports %d"
            % (n_train, live))
    non_fp32 = [n for n, p in model.named_parameters()
                if p.requires_grad and p.dtype != torch.float32]
    if non_fp32:
        raise ScopeError(
            "%d trainable tensor(s) are not fp32 (first: %s). A bf16 master "
            "rounds the update to zero -- see PREREG a0450b36 §4.1."
            % (len(non_fp32), non_fp32[0]))
    scope["n_trainable_params"] = n_train
    scope["n_frozen_params"] = n_frozen
    return scope
