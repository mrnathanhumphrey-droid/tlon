"""SAME WEIGHTS, SAME BATCH, ONLY THE KERNEL DIFFERS.

⛔⛔ THREE RUNS COULD NOT SAY THIS. The fused-SDPA arm breaks at step 13; the
eager arm on the SAME batch order runs 60 steps clean; a third arm, SDPA with a
different batch order, also runs 60 clean. Read together they say the trigger is
data-dependent AND that the kernel matters — but eager is itself a ~1% numerical
perturbation, so "the fused backward is wrong on this batch" and "any small
perturbation dodges a knife edge on this batch" remain unseparated. Every
comparison so far differed in trajectory as well as in kernel.

⭐⭐ THIS REMOVES THE TRAJECTORY ENTIRELY. At `on_pre_optimizer_step` the
optimizer has NOT yet stepped, so the weights are still the previous step's. The
micro-batches of the current step are in hand. So the same tensors can be pushed
through the same weights twice, changing nothing but the attention
implementation:

    leg 1  trainer's own backward, SDPA     (read from the pre-clip probe)
    leg 2  our backward, SDPA               <- validates the harness
    leg 3  our backward, eager              <- the comparison

⛔ LEG 2 IS NOT OPTIONAL. Without it, "eager was finite" could just mean the
re-run harness differs from the trainer in some way that has nothing to do with
attention. Leg 2 must reproduce leg 1; if it does not, legs 1 and 3 are not
comparable and the duel reports INSTRUMENT_FAULT rather than a verdict.

⛔ Both readings are taken BEFORE any clipping. `clip_grad_norm_` computes one
global norm across every parameter, so a post-clip read cannot distinguish one
bad tensor from all of them.
"""
from __future__ import annotations

#: Verdicts. ⛔ Named so a caller cannot mistake "we could not tell" for "the
#: kernel is fine" — the two have opposite consequences for what gets bought
#: next.
KERNEL_IMPLICATED = "KERNEL_IMPLICATED"
KERNEL_EXONERATED = "KERNEL_EXONERATED"
INSTRUMENT_FAULT = "INSTRUMENT_FAULT"
NO_FAULT_TO_EXPLAIN = "NO_FAULT_TO_EXPLAIN"


def flip_attn_implementation(model, impl: str) -> str:
    """Set the attention implementation for every subsequent forward.

    ⭐ Safe at runtime because transformers 5.8.1 resolves BOTH the attention
    interface and the causal mask inside `forward`, from
    `config._attn_implementation` — `Qwen2Attention.forward` calls
    `ALL_ATTENTION_FUNCTIONS.get_interface(self.config._attn_implementation,
    ...)` and `create_causal_mask` reads the same field. Verified by reading the
    installed source, not assumed.

    ⛔ Walks submodules too: a config held by reference would follow the top
    level anyway, but a copy would not, and a half-flipped model would run the
    new kernel against the old mask format and report a numerical difference
    that is really a wiring bug.
    """
    old = model.config._attn_implementation
    model.config._attn_implementation = impl
    for m in model.modules():
        cfg = getattr(m, "config", None)
        if cfg is not None and hasattr(cfg, "_attn_implementation"):
            cfg._attn_implementation = impl
    seen = {m.config._attn_implementation for m in model.modules()
            if getattr(m, "config", None) is not None
            and hasattr(m.config, "_attn_implementation")}
    if seen and seen != {impl}:
        raise RuntimeError(
            "attention implementation did not flip everywhere: %s" % sorted(seen))
    return old


def scan_grads(model):
    """{name: (rank, finite, absmax)} over trainable params, PRE-clip."""
    import torch
    out = {}
    for n, p in model.named_parameters():
        if not p.requires_grad:
            continue
        rank = "1d" if p.dim() == 1 else "2d"
        if p.grad is None:
            out[n] = (rank, True, None)
            continue
        g = p.grad.detach().float()
        fin = bool(torch.isfinite(g).all())
        out[n] = (rank, fin, float(g.abs().max()) if fin else None)
    return out


def run_leg(model, batches, *, accum):
    """One forward+backward over the captured micro-batches, from clean grads.

    ⛔ Returns the RAW per-micro-batch losses as the model produced them. The
    division by `accum` mirrors the trainer so gradient magnitudes are
    comparable between legs; the reported loss is undivided so it can be
    compared to a trace row.
    """
    model.zero_grad(set_to_none=True)
    losses = []
    for b in batches:
        out = model(**b)
        losses.append(float(out.loss.detach().float()))
        (out.loss / accum).backward()
    return losses, scan_grads(model)


def _bad(scan):
    return sorted(n for n, (_, fin, _) in scan.items() if not fin)


def compare(trainer_sdpa, our_sdpa, our_eager):
    """The verdict. Pure, so it is testable without a GPU.

    `trainer_sdpa` may be None when the pre-clip probe was not installed.
    """
    b_tr = None if trainer_sdpa is None else _bad(trainer_sdpa)
    b_sd, b_eg = _bad(our_sdpa), _bad(our_eager)
    rep = {"our_sdpa_nonfinite_n": len(b_sd), "our_sdpa_first": b_sd[:4],
           "our_eager_nonfinite_n": len(b_eg), "our_eager_first": b_eg[:4],
           "trainer_sdpa_nonfinite_n": (None if b_tr is None else len(b_tr))}
    # ⛔⛔ THE HARNESS CHECK FIRST. If our own SDPA leg does not reproduce the
    # trainer's, the eager leg is not comparable to anything and no verdict is
    # available -- reporting one anyway would be the whole failure this file
    # exists to avoid.
    if b_tr is not None and set(b_sd) != set(b_tr):
        rep["verdict"] = INSTRUMENT_FAULT
        rep["why"] = ("our SDPA re-run did not reproduce the trainer's SDPA "
                      "backward (%d vs %d non-finite tensors), so the eager leg "
                      "is not comparable to it and the difference measured "
                      "would not be the kernel" % (len(b_sd), len(b_tr)))
        return rep
    if not b_sd and not b_eg:
        rep["verdict"] = NO_FAULT_TO_EXPLAIN
        rep["why"] = ("neither kernel produced a non-finite gradient on this "
                      "batch, so this batch is not the trigger and the duel has "
                      "nothing to adjudicate")
    elif b_sd and not b_eg:
        rep["verdict"] = KERNEL_IMPLICATED
        rep["why"] = ("SDPA produced %d non-finite gradients and eager produced "
                      "NONE, from identical weights on identical inputs. No "
                      "trajectory, data or weight difference remains to explain "
                      "it away." % len(b_sd))
    elif b_sd and b_eg:
        rep["verdict"] = KERNEL_EXONERATED
        rep["why"] = ("both kernels produced non-finite gradients on this batch "
                      "(%d vs %d), so the fault is in the computation both "
                      "share, not in the fused path. The earlier clean eager RUN "
                      "was the ~1%% perturbation, not the kernel."
                      % (len(b_sd), len(b_eg)))
    else:
        rep["verdict"] = KERNEL_EXONERATED
        rep["why"] = ("eager produced %d non-finite gradients where SDPA "
                      "produced none -- the opposite of the hypothesis, and a "
                      "result that would need its own investigation"
                      % len(b_eg))
    return rep
