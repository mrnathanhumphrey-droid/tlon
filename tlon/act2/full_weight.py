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


def layer_stacks(names) -> dict:
    """-> {prefix before `layers.<i>.`: {indices}}. ⭐ ONE ENTRY PER STACK.

    ⛔⛔ A MULTIMODAL BASE HAS TWO LAYER STACKS AND THE OLD CODE POOLED THEM.
    `Ministral-3-8B-Instruct-2512-BF16` carries
    `language_model.model.layers.0..33` AND `vision_tower.transformer.layers.
    0..23`; `_LAYER_RE` matches both, so the pooled index set was 0..33 --
    CONTIGUOUS, so every existing guard passed -- and `unfreeze_top=14`
    unfroze text layers 20-33 plus **36 vision-tower tensors**, training an
    image encoder as if it were part of the language model.

    ⭐ Nothing was wrong with the regex. The scope WIDENED to bases with more
    than one stack and the rule needed re-deriving, not stretching -- the same
    lesson `scope_mode` learned when the locus widened.
    """
    out = {}
    for n in names:
        m = _LAYER_RE.search(n)
        if m:
            out.setdefault(n[:m.start()], set()).add(int(m.group(1)))
    return out


def layer_indices(names, *, stack: str | None = None) -> set:
    """Every transformer-layer index in ONE stack.

    ⛔ With more than one stack present this REFUSES rather than pooling. A
    pooled set silently mixes an image encoder into the language model's layer
    count, and the resulting union can look perfectly contiguous.
    """
    stacks = layer_stacks(names)
    if not stacks:
        return set()
    if stack is not None:
        if stack not in stacks:
            raise ScopeError("no layer stack with prefix %r; found %s"
                             % (stack, sorted(stacks)))
        return set(stacks[stack])
    if len(stacks) > 1:
        raise ScopeError(
            "MORE THAN ONE TRANSFORMER-LAYER STACK: %s. This base is not a "
            "plain causal LM, and pooling the stacks would train one module's "
            "layers as if they belonged to another -- on a multimodal "
            "checkpoint the pooled indices can even look contiguous, so no "
            "existing guard fires. Name the stack explicitly."
            % ", ".join("%r(%d layers)" % (p, len(v))
                        for p, v in sorted(stacks.items())))
    return set(next(iter(stacks.values())))


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


# ═══ RUNG 2 — THE MAPPING SCOPE ════════════════════════════════════════════
#
# ⛔⛔ THIS IS THE MOST DANGEROUS SCOPE IN THE FILE TO GET WRONG, AND THE REASON
# IS THE RUNG'S OWN HYPOTHESIS. Rung 2 unfreezes `embed_tokens` + `lm_head` to
# ask whether release lives in the token mapping, and the outcome it is most
# likely to find is a FLOOR. A selector that silently matches nothing trains a
# frozen model, moves no weight, and produces exactly the reading the run is
# hunting -- "the mapping did not install release" -- with no symptom anywhere.
# The false floor and the finding are the same observation.
#
# ⭐ So every check here is POSITIVE and NAMED. Not "everything except layers",
# which is satisfied by matching nothing; but "these two tensors, by name, are
# trainable, and no layer tensor is."

#: ⭐ The token<->vector mapping, selected POSITIVELY. Deliberately the same two
#: leaves `FROZEN_LEAVES` names: rung 2 is exactly the inversion of §5's freeze,
#: and writing the pair twice would let the two definitions drift apart.
MAPPING_LEAVES = FROZEN_LEAVES


def mapping_scope(names, *, mapping_leaves=MAPPING_LEAVES) -> dict:
    """Trainable = the token mapping ONLY. Every transformer layer frozen.

    ⛔ Refuses unless BOTH leaves are present. `tie_word_embeddings` is false on
    this model, so `embed_tokens` and `lm_head` are separate matrices and the
    scope is 1.090 B. On a TIED model `lm_head` would not appear as its own
    parameter, the selection would silently be half the declared scope, and the
    run would answer a smaller question than the prereg locked.
    """
    names = list(names)
    if not names:
        raise ScopeError("no parameter names given")

    idx = layer_indices(names)
    if not idx:
        raise ScopeError(
            "no parameter name matched the transformer-layer pattern %r, so "
            "'the layers are frozen' cannot be verified -- and an unverifiable "
            "freeze is what makes a false floor look like a finding."
            % _LAYER_RE.pattern)

    trainable, frozen = [], []
    for n in names:
        parts = n.split(".")
        if any(f in parts for f in mapping_leaves) and not _LAYER_RE.search(n):
            trainable.append(n)
        else:
            frozen.append(n)

    # ⛔⛔ POSITIVE, PER-LEAF. An empty selection is refused by the generic
    # check below, but a HALF selection is not empty -- it is a quietly smaller
    # experiment. Each declared leaf must have matched something.
    for leaf in mapping_leaves:
        if not any(leaf in n.split(".") for n in trainable):
            raise ScopeError(
                "mapping scope selected nothing for %r. The declared scope is "
                "%s; a scope missing one of them trains a different experiment "
                "than the one pre-registered." % (leaf, list(mapping_leaves)))
    if not trainable:
        raise ScopeError(
            "mapping scope selected 0 trainable tensors out of %d" % len(names))

    # ⛔ AND NO LAYER MAY LEAK IN. A single layer tensor in the trainable set
    # turns this into "mapping + some layers" -- Option B by accident -- and
    # re-confounds the run with the layer capacity that already tested flat.
    leaked = [n for n in trainable if _LAYER_RE.search(n)]
    if leaked:
        raise ScopeError(
            "%d transformer-layer tensor(s) leaked into the mapping scope "
            "(first: %s). That is mapping+layers, not the isolated mapping "
            "test." % (len(leaked), leaked[0]))

    return {
        "scope_mode": "mapping",
        "n_layers": max(idx) + 1,
        "unfreeze_top": 0,          # ⭐ layers frozen, stated not implied
        "cutoff_layer": None,
        "trainable": trainable,
        "frozen": frozen,
    }


def apply_mapping_scope(model) -> dict:
    """`requires_grad` for rung 2, with the layer freeze ASSERTED on the model.

    ⛔ The name-level checks in `mapping_scope` prove the SELECTION; this proves
    the MODEL agrees. `requires_grad_` on a re-created or non-leaf parameter
    silently does nothing, and the next observation would be a zero delta read
    as a substrate floor.
    """
    import torch

    names = [n for n, _ in model.named_parameters()]
    scope = mapping_scope(names)
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

    live = sum(p.numel() for p in model.parameters() if p.requires_grad)
    if live != n_train:
        raise ScopeError(
            "requires_grad did not take: set %d trainable, model reports %d"
            % (n_train, live))
    if n_train == 0:
        raise ScopeError(
            "0 trainable parameters after applying the mapping scope. This "
            "would train nothing, report a perfect zero delta, and read as a "
            "substrate floor -- which is the very verdict rung 2 is testing "
            "for.")

    # ⛔⛔ THE LAYER FREEZE, ASSERTED ON THE MODEL ITSELF.
    hot = [n for n, p in model.named_parameters()
           if p.requires_grad and _LAYER_RE.search(n)]
    if hot:
        raise ScopeError(
            "%d transformer-layer tensor(s) are trainable (first: %s). Option A "
            "is layers-FROZEN; this run would silently be Option B."
            % (len(hot), hot[0]))

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


#: Returned by `mapping_moved` -- a floor may only be read on MOVED.
MAPPING_MOVED = "MAPPING_MOVED"
MAPPING_FROZEN = "MAPPING_FROZEN"
MAPPING_UNVERIFIED = "MAPPING_UNVERIFIED"

#: ⭐ How much of the PREDICTED movement a leaf must actually show. Set at half
#: because the prediction itself is sampled: at 4,096 sampled values and ~0.6%
#: coverage the expected count is ~25, whose Poisson sd is ~5, so a healthy run
#: can land 20% low by chance alone. Half is comfortably outside that and still
#: an order of magnitude above the `> 0` test it replaces.
MOVED_TOLERANCE = 0.5


def expected_moved_fraction(leaf: str, *, vocab_coverage: float) -> float:
    """What fraction of a leaf's sampled values SHOULD change in a healthy run.

    ⛔⛔ THE TWO MAPPING TENSORS HAVE DIFFERENT PREDICTIONS, AND THAT IS THE
    WHOLE POINT. `lm_head` produces logits over the entire vocabulary on every
    step, so every row receives gradient and ~all sampled values move.
    `embed_tokens` receives gradient ONLY on rows for tokens that actually
    appear, so its expected fraction is the corpus's VOCABULARY COVERAGE --
    about 0.6% on the content-transient corpus, not 100%.

    ⭐ Measured on rung 2 (2026-09-08): coverage 921/152,064 = 0.61% predicted
    ~25 of 4,096 sampled values; the run produced **20**. Comparing that against
    `> 0` said "moved" and told you nothing; comparing it against the PREDICTION
    says "moved as much as a working run should", which is the claim a floor
    verdict actually rests on.
    """
    if leaf == "embed_tokens":
        return vocab_coverage
    return 1.0


def mapping_moved(delta: dict, *, mapping_leaves=MAPPING_LEAVES,
                  vocab_coverage: float | None = None,
                  tolerance: float = MOVED_TOLERANCE):
    """Did the MAPPING TENSORS THEMSELVES move? -> (verdict, why)

    ⛔⛔ THIS IS WHAT SEPARATES THE FINDING FROM THE BUG. Rung 2's expected
    outcome is a floor, and two very different states produce one:

        the mapping trained and release still did not install   <- THE FINDING
        the mapping never trained and the delta was zero        <- A BUG

    The global §4.1 precondition cannot tell them apart, because on this scope
    the mapping IS almost the whole trainable set -- a frozen mapping makes the
    global delta zero, which §4.1 already catches, but a mapping that moved only
    in `lm_head` while `embed_tokens` sat still would pass §4.1 on the strength
    of the half that worked. So the movement is asserted PER DECLARED LEAF.

    ⛔ A floor verdict must not be read unless this returns MAPPING_MOVED.
    """
    per = (delta or {}).get("per_module") or {}
    if not per:
        return MAPPING_FROZEN, (
            "weight_delta carries no per_module record, so per-tensor movement "
            "cannot be checked. REFUSING to certify: an unmeasured mapping is "
            "not a moved one.")
    if vocab_coverage is None:
        return MAPPING_UNVERIFIED, (
            "no vocab_coverage given, so the expected movement of "
            "`embed_tokens` cannot be predicted. REFUSING to certify on a bare "
            "non-zero test: that is the threshold that passed 20/4096 on rung 2 "
            "and could not say whether it was healthy sparsity or a dead "
            "tensor.")
    if not 0.0 < vocab_coverage <= 1.0:
        return MAPPING_UNVERIFIED, (
            "vocab_coverage=%r is not a fraction in (0, 1]." % (vocab_coverage,))

    detail, short = [], []
    for leaf in mapping_leaves:
        rows = {n: r for n, r in per.items() if leaf in n.split(".")}
        if not rows:
            return MAPPING_FROZEN, (
                "no per_module row for %r -- the delta never sampled the "
                "tensor this run exists to move." % leaf)
        want = expected_moved_fraction(leaf, vocab_coverage=vocab_coverage)
        floor = want * tolerance
        for n, r in sorted(rows.items()):
            got = r.get("fraction_changed")
            dn = r.get("delta_norm_estimated") or 0
            if got is None:
                return MAPPING_FROZEN, (
                    "%s has no fraction_changed; movement is unmeasured." % n)
            detail.append("%s observed %.4f vs predicted %.4f (floor %.4f), "
                          "delta_norm %.4g" % (leaf, got, want, floor, dn))
            if dn <= 0 or got < floor:
                short.append(
                    "%s moved %.4f of sampled values against a prediction of "
                    "%.4f (floor %.4f, delta_norm %.4g)"
                    % (leaf, got, want, floor, dn))
    if short:
        return MAPPING_FROZEN, (
            "UNDER-MOVED: " + "; ".join(short)
            + ". A floor read here would be a partly-untrained mapping wearing "
              "the shape of the finding. `lm_head` is dense (predicted 1.0); "
              "`embed_tokens` is sparse (predicted = corpus vocabulary "
              "coverage), so each leaf is judged against its OWN prediction.")
    return MAPPING_MOVED, ("every declared mapping leaf moved AS PREDICTED: "
                           + "; ".join(detail))
