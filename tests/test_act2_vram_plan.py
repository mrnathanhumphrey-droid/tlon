"""THE VRAM PLANNER, ANCHORED TO RUNS THAT ACTUALLY HAPPENED. $0.00, offline.

⛔⛔ THE PLANNER WAS WRONG BY ~3.4x AND NOBODY WOULD HAVE KNOWN. It predicted
**4.6 GiB** for the local fine-tune; the job ran at **15.5 of a 16 GiB card**. It
did not OOM, so the error would have gone unrecorded -- and this is the tool a
**Tier-B backbone decision** gets sized with, where the same error means renting
the wrong GPU or declaring a model untrainable that is not.

⭐ THE MISSING TERM DOES NOT SCALE WITH PARAMETERS. It is the LM head output, and
it scales with **VOCABULARY**: 16 × 192 × 152,064 = 467 M logits, upcast to fp32
by cross-entropy and kept again as a gradient. ~5.6 GiB at batch 16, larger than
everything the old formula counted.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

import act2_finetune as FT                                       # noqa: E402


@pytest.mark.parametrize("params,dtype,seq,batch,vocab,measured,where", FT.MEASURED)
def test_the_plan_reproduces_every_run_that_actually_happened(
        params, dtype, seq, batch, vocab, measured, where):
    """⭐⭐ THE ONLY CHECK THAT MATTERS. Two real jobs, their real peaks. A formula
    that cannot reproduce what already happened cannot predict what has not."""
    got = FT.plan(params, dtype, seq, batch, grad_ckpt=True, vocab=vocab)["total_GiB"]
    assert 0.7 * measured <= got <= 1.3 * measured, (
        f"{where}: measured {measured} GiB, plan says {got:.1f} GiB")


def test_the_OLD_formula_would_FAIL_this_and_that_is_the_point():
    """⛔ The red-proof, written as a test. Drop the logits and overhead terms —
    the two things that were missing — and the local anchor is under-predicted by
    more than half. This is what shipped."""
    p, dtype, seq, batch, vocab, measured, _ = FT.MEASURED[0]
    full = FT.plan(p, dtype, seq, batch, grad_ckpt=True, vocab=vocab)
    old = full["weights_GiB"] + full["lora_optim_GiB"] + full["activations_GiB"]
    assert old < 0.5 * measured, (
        "the old three-term formula should badly under-predict the measured run")
    assert full["total_GiB"] >= 0.7 * measured


def test_the_slack_is_declared_as_fitted_and_not_hidden_in_a_constant():
    """⚠️ It is a straight line through TWO points. Anyone reading a plan figure
    must be able to find that out from the module, not by re-deriving it."""
    import inspect
    src = inspect.getsource(FT)
    assert "RUNTIME_SLACK" in src and "FITTED TO TWO POINTS" in src


def test_the_slack_applies_to_the_VARIABLE_terms_not_to_the_weights():
    """⛔ Quantized weights are a flat allocation; inflating them would make 4-bit
    look falsely expensive and could flip a dtype decision."""
    q4 = FT.plan(7.62, "4bit", 192, 8, grad_ckpt=True)
    assert q4["total_GiB"] == pytest.approx(
        q4["weights_GiB"] + q4["live_variable_GiB"] * FT.RUNTIME_SLACK)


def test_the_planner_is_not_blind_to_VOCABULARY():
    """⛔⛔ THE ROOT CAUSE, stated as a property. A large-vocab model costs
    materially more at the head, and a planner that ignores vocab under-sizes
    every one of them identically."""
    small = FT.plan(7.62, "bf16", 192, 16, grad_ckpt=True, vocab=32000)
    large = FT.plan(7.62, "bf16", 192, 16, grad_ckpt=True, vocab=152064)
    assert large["total_GiB"] > small["total_GiB"] + 3.0


def test_the_head_dominates_the_hidden_state_activations_at_this_shape():
    """⭐ The surprise that made the old formula plausible: at seq 192 the
    activations really ARE small. The head is not, and only one of them was
    counted."""
    p = FT.plan(7.62, "bf16", 192, 16, grad_ckpt=True)
    assert p["logits_GiB"] > 5 * p["activations_GiB"]


@pytest.mark.parametrize("batch", [1, 4, 8, 16, 32])
def test_the_total_rises_monotonically_with_batch(batch):
    """A sizing tool that is not monotone in batch cannot be used to choose one."""
    p = FT.plan(7.62, "bf16", 192, batch, grad_ckpt=True)
    bigger = FT.plan(7.62, "bf16", 192, batch * 2, grad_ckpt=True)
    assert bigger["total_GiB"] > p["total_GiB"]


def test_weights_still_dominate_at_bf16_so_the_dtype_call_stays_readable():
    """4-bit must remain visibly cheaper on weights, or the plan stops answering
    the question it exists for."""
    bf16 = FT.plan(7.62, "bf16", 192, 8, grad_ckpt=True)
    q4 = FT.plan(7.62, "4bit", 192, 8, grad_ckpt=True)
    assert bf16["weights_GiB"] > 3 * q4["weights_GiB"]
    assert q4["total_GiB"] < bf16["total_GiB"]
