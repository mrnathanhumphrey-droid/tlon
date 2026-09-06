"""THE FULL-WEIGHT SCOPE AND THE §4.1 PRECONDITION.

PREREG `PREREG_FULL_FINETUNE_RELEASE_2026_09_05` (LOCK `a0450b36`). Both modules
under test exist to stop the same failure: a run that trains nothing, or writes
nothing, and whose zero movement then reads as (b) -- the terminal substrate
finding. So the tests that matter here are the ones that check the REFUSALS.
"""
import math

import pytest

torch = pytest.importorskip("torch")

from tlon.act2.full_weight import (ScopeError, apply_scope,  # noqa: E402
                                   full_weight_scope, layer_indices)
from tlon.act2.weight_delta import (INSTRUMENT_FAULT, OK,  # noqa: E402
                                    UNDISCRIMINATING, WeightDeltaError,
                                    absorbable_ceiling, measure, snapshot)

LEAVES = ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj",
          "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj")


def qwen_names(n_layers=28):
    """The real Qwen2.5-7B-Instruct parameter naming, including the two
    SEPARATE embedding matrices (`tie_word_embeddings: false`)."""
    names = []
    for i in range(n_layers):
        for leaf in LEAVES:
            names.append("model.layers.%d.%s.weight" % (i, leaf))
        names.append("model.layers.%d.input_layernorm.weight" % i)
    return names + ["model.embed_tokens.weight", "model.norm.weight",
                    "lm_head.weight"]


# ── the scope ────────────────────────────────────────────────────────────────

def test_top_14_of_28_is_the_locked_scope():
    s = full_weight_scope(qwen_names(), unfreeze_top=14)
    assert s["n_layers"] == 28
    assert s["cutoff_layer"] == 14
    trained = layer_indices(s["trainable"])
    assert trained == set(range(14, 28))


def test_both_embedding_matrices_and_the_final_norm_are_frozen():
    """⛔ `lm_head` is UNTIED on this model, so freezing `embed_tokens` does not
    cover it and it must be named separately. §5 counts 2 x 544,997,376."""
    s = full_weight_scope(qwen_names(), unfreeze_top=14)
    for n in ("model.embed_tokens.weight", "lm_head.weight",
              "model.norm.weight"):
        assert n in s["frozen"], n
        assert n not in s["trainable"], n


def test_a_selector_that_matches_nothing_is_refused_not_returned():
    """⛔⛔ THE FAILURE THIS MODULE EXISTS FOR. A renamed parameter scheme makes
    the layer pattern match nothing; returning that would freeze the whole model,
    train to a perfect zero delta, and read as a substrate floor."""
    with pytest.raises(ScopeError, match="matched the transformer-layer"):
        full_weight_scope(["encoder.block.0.attn.weight", "wte.weight"],
                          unfreeze_top=14)


def test_unfreeze_top_zero_is_refused():
    with pytest.raises(ScopeError, match="trains nothing"):
        full_weight_scope(qwen_names(), unfreeze_top=0)


def test_unfreeze_top_beyond_the_stack_is_refused():
    with pytest.raises(ScopeError, match="not a subset"):
        full_weight_scope(qwen_names(), unfreeze_top=29)


def test_non_contiguous_layer_indices_are_refused():
    names = ["model.layers.0.mlp.up_proj.weight",
             "model.layers.7.mlp.up_proj.weight"]
    with pytest.raises(ScopeError, match="not contiguous"):
        full_weight_scope(names, unfreeze_top=1)


def test_frozen_leaf_match_is_by_component_not_substring():
    """⭐ A substring test would freeze a hypothetical `lm_head_proj` inside a
    trainable layer, silently shrinking the scope below the locked count."""
    names = qwen_names() + ["model.layers.27.mlp.lm_head_proj.weight"]
    s = full_weight_scope(names, unfreeze_top=14)
    assert "model.layers.27.mlp.lm_head_proj.weight" in s["trainable"]


# ── apply_scope on a real module ─────────────────────────────────────────────

class _Tiny(torch.nn.Module):
    """A 4-layer stand-in with the Qwen naming, so `apply_scope` is exercised
    against `named_parameters()` rather than a list of strings."""

    def __init__(self):
        super().__init__()
        self.model = torch.nn.Module()
        self.model.embed_tokens = torch.nn.Embedding(8, 4)
        self.model.layers = torch.nn.ModuleList(
            [torch.nn.Linear(4, 4) for _ in range(4)])
        self.model.norm = torch.nn.LayerNorm(4)
        self.lm_head = torch.nn.Linear(4, 8, bias=False)


def test_apply_scope_sets_requires_grad_and_casts_only_the_trainable_set():
    m = _Tiny().to(torch.bfloat16)
    s = apply_scope(m, unfreeze_top=2)
    live = {n for n, p in m.named_parameters() if p.requires_grad}
    assert layer_indices(live) == {2, 3}
    for n, p in m.named_parameters():
        if p.requires_grad:
            assert p.dtype == torch.float32, n
        else:
            # ⭐ Frozen stays bf16 -- that is the 11 GiB the budget is bought with.
            assert p.dtype == torch.bfloat16, n
    assert s["n_trainable_params"] == sum(
        p.numel() for p in m.parameters() if p.requires_grad)


def test_apply_scope_refuses_a_model_with_no_layers():
    m = torch.nn.Linear(4, 4)
    with pytest.raises(ScopeError):
        apply_scope(m, unfreeze_top=1)


# ── the §4.1 precondition ────────────────────────────────────────────────────

def test_absorbable_ceiling_is_the_locked_arithmetic():
    """§4.1: at lr 1e-5 the largest weight that can absorb one bf16 step is
    2.56e-3. That number is in the hashed body; this is where it stays true."""
    assert absorbable_ceiling(1e-5) == pytest.approx(2.56e-3, rel=1e-9)
    # ⭐ And it HALVES at the dial-back LR -- the reason 5e-6 is not "gentler"
    # under a bf16 master, recorded in §5.
    assert absorbable_ceiling(5e-6) == pytest.approx(1.28e-3, rel=1e-9)


# ── the §5 VRAM arithmetic, reproducible from the repo ───────────────────────

def _plan():
    import importlib.util
    import pathlib
    p = pathlib.Path(__file__).resolve().parents[1] / "tools" / "act2_finetune.py"
    spec = importlib.util.spec_from_file_location("_ft", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_locked_section_5_fit_is_reproducible():
    """⛔⛔ §5's 51.4 GiB was computed in a session scratch script. A number that
    only exists in scrollback cannot be re-checked when someone later asks
    whether the run should have fitted. This is where it lives now.

    ⚠️ The locked body quotes 65.7 for the +28 % figure and this gives 65.8 --
    rounding, from 7.62 vs 7.616 B in the activation term. Recorded rather than
    reconciled: the locked text is not editable and the 0.1 GiB does not move
    the decision (14.2 GiB of margin against 80, not 14.3)."""
    m = _plan()
    p = m.plan(7.616, "bf16", 384, 4, True, trainable_b=3.263, moment_bytes=2)
    assert p["total_GiB"] == pytest.approx(51.4, abs=0.05)
    assert p["total_GiB"] * 1.28 == pytest.approx(65.8, abs=0.05)
    # ⭐ fp32 moments are the config that does NOT fit -- the reason §5 declares
    # 8-bit as forced rather than preferred.
    q = m.plan(7.616, "bf16", 384, 4, True, trainable_b=3.263, moment_bytes=8)
    assert q["total_GiB"] * 1.28 > 80


def test_the_lora_path_is_untouched_by_the_full_weight_terms():
    """⛔ The gate's numbers must not move because a new arm was added."""
    m = _plan()
    p = m.plan(7.62, "bf16", 256, 8, True)
    assert p["total_GiB"] == pytest.approx(28.3, abs=0.05)
    assert p["lora_optim_GiB"] == pytest.approx(0.381, abs=0.001)
    assert p["grads_GiB"] == 0.0 and p["moments_GiB"] == 0.0


def _params(sd):
    return [(n, torch.nn.Parameter(v)) for n, v in sd.items()]


def _init(n=20000, std=0.02, seed=0):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(n, generator=g) * std


def test_nothing_moved_is_instrument_fault_never_a_floor():
    """⛔⛔ THE CENTRAL CASE. A run whose optimizer wrote nothing must not be
    readable as (b)."""
    p = _params({"model.layers.0.mlp.up_proj.weight": _init()})
    snap = snapshot(p)
    rep = measure(p, snap, lr=1e-5)
    assert rep["verdict"] == INSTRUMENT_FAULT
    assert rep["fraction_changed"] == 0.0


def test_everything_moved_reads_ok():
    w = _init()
    p = _params({"model.layers.0.mlp.up_proj.weight": w})
    snap = snapshot(p)
    with torch.no_grad():
        p[0][1].add_(1e-4)
    rep = measure(p, snap, lr=1e-5)
    assert rep["verdict"] == OK
    assert rep["fraction_changed"] == 1.0


def test_the_bf16_dead_zone_signature_is_caught():
    """⛔⛔ THE SUBTLE CASE, AND THE ONE A THRESHOLD WOULD MISS. A bf16 master
    does not freeze everything -- it moves only the weights small enough to
    absorb a step and leaves the rest. The observed fraction then lands on the
    dead-zone prediction, not on zero, and a `fraction > 0` check would pass it."""
    w = _init()
    p = _params({"model.layers.0.mlp.up_proj.weight": w})
    snap = snapshot(p)
    ceiling = absorbable_ceiling(1e-5)
    with torch.no_grad():
        small = p[0][1].abs() <= ceiling
        p[0][1][small] += 1e-4
    rep = measure(p, snap, lr=1e-5)
    assert 0.0 < rep["fraction_changed"] < 0.5
    assert rep["verdict"] == INSTRUMENT_FAULT
    assert rep["prediction_bf16_dead_zone"] == pytest.approx(
        rep["fraction_changed"], abs=0.02)


def test_it_refuses_to_discriminate_when_both_hypotheses_predict_the_same():
    """⛔ A test that cannot fail has not been passed. With weights small enough
    that even bf16 absorbs every step, a working run and a dead one predict the
    same fraction, so the answer is UNDISCRIMINATING -- never OK."""
    p = _params({"model.layers.0.mlp.up_proj.weight": _init(std=1e-4)})
    snap = snapshot(p)
    with torch.no_grad():
        p[0][1].add_(1e-6)
    rep = measure(p, snap, lr=1e-5)
    assert rep["prediction_bf16_dead_zone"] > 0.5
    assert rep["verdict"] == UNDISCRIMINATING


def test_no_trainable_parameters_is_refused_not_reported_as_zero():
    frozen = [("model.layers.0.mlp.up_proj.weight",
               torch.nn.Parameter(_init(), requires_grad=False))]
    with pytest.raises(WeightDeltaError, match="no trainable parameters"):
        snapshot(frozen)


def test_a_tensor_missing_at_measure_time_is_refused():
    """⛔ Skipping it would lower the denominator, moving the fraction toward
    whichever answer the missing tensor would have contradicted."""
    p = _params({"a.layers.0.w": _init(), "b.layers.0.w": _init(seed=1)})
    snap = snapshot(p)
    with pytest.raises(WeightDeltaError, match="absent at measure time"):
        measure(p[:1], snap, lr=1e-5)


def test_a_resized_tensor_is_refused():
    p = _params({"model.layers.0.w": _init()})
    snap = snapshot(p)
    smaller = _params({"model.layers.0.w": _init(n=10)})
    with pytest.raises(WeightDeltaError, match="changed size"):
        measure(smaller, snap, lr=1e-5)


def test_the_delta_norm_is_scaled_to_the_full_tensor_not_a_partial_sum():
    """⛔⛔ A partial sum reported as a total understates by sqrt(n/sampled) --
    here ~2.2x -- and understating the movement is the direction that fakes a
    fault. Every element moves by exactly d, so the true norm is d*sqrt(n)."""
    n, d = 20000, 1e-3
    p = _params({"model.layers.0.w": torch.zeros(n)})
    snap = snapshot(p)
    with torch.no_grad():
        p[0][1].add_(d)
    rep = measure(p, snap, lr=1e-5)
    assert rep["delta_norm_estimated"] == pytest.approx(d * math.sqrt(n),
                                                        rel=1e-6)


# ── the NaN hole, found in production ────────────────────────────────────────

def test_nan_weights_are_DIVERGED_not_OK():
    """⛔⛔ THE HOLE `fw-s20624` FOUND. That run finished an epoch with NaN in all
    70 of its 1-D trainable tensors and this module returned OK with
    fraction_changed 0.9999982 — because `NaN != NaN` is True, so every destroyed
    value counted as movement. The guard written to tell "did not move" from
    "moved" could not tell either from "became NaN"."""
    w = _init()
    p = _params({"model.layers.0.mlp.up_proj.weight": w})
    snap = snapshot(p)
    with torch.no_grad():
        p[0][1].fill_(float("nan"))
    rep = measure(p, snap, lr=1e-5)
    assert rep["verdict"] == "DIVERGED"
    assert rep["fraction_nonfinite"] == 1.0
    # ⭐ AND THE FRACTION NO LONGER LIES. Non-finite values are excluded from
    # `changed`, so it reports weights that moved TO A NUMBER.
    assert rep["fraction_changed"] == 0.0


def test_a_partially_diverged_model_is_DIVERGED_even_though_most_moved():
    """⛔⛔ THE PRODUCTION SHAPE EXACTLY: 98 weight matrices trained fine, 70
    biases and layernorms went NaN. A majority-healthy model is still unreadable
    — release, perceive and fluency cannot be scored through a NaN."""
    good = _params({"model.layers.0.mlp.up_proj.weight": _init()})
    bad = _params({"model.layers.0.input_layernorm.weight": _init(n=3584)})
    both = good + bad
    snap = snapshot(both)
    with torch.no_grad():
        good[0][1].add_(1e-4)
        bad[0][1].fill_(float("nan"))
    rep = measure(both, snap, lr=1e-5)
    assert rep["verdict"] == "DIVERGED"
    assert 0.0 < rep["fraction_nonfinite"] < 1.0
    per = rep["per_module"]
    assert per["model.layers.0.mlp.up_proj.weight"]["fraction_nonfinite"] == 0.0
    assert per["model.layers.0.input_layernorm.weight"]["fraction_nonfinite"] == 1.0


def test_inf_counts_as_divergence_too():
    """⛔ Not only NaN. An Inf weight is equally unreadable and equally != init."""
    p = _params({"model.layers.0.w": _init()})
    snap = snapshot(p)
    with torch.no_grad():
        p[0][1].fill_(float("inf"))
    assert measure(p, snap, lr=1e-5)["verdict"] == "DIVERGED"


def test_the_delta_norm_stays_readable_on_a_diverged_tensor():
    """⭐ Computed over the finite values only. A NaN norm would just be a second
    unreadable field instead of a diagnosis — and the NaN norm this module DID
    produce was written to the artifact and never read by the verdict."""
    good = _params({"a.layers.0.w": torch.zeros(20000)})
    bad = _params({"b.layers.0.w": _init(seed=3)})
    both = good + bad
    snap = snapshot(both)
    with torch.no_grad():
        good[0][1].add_(1e-3)
        bad[0][1].fill_(float("nan"))
    rep = measure(both, snap, lr=1e-5)
    assert math.isfinite(rep["delta_norm_estimated"])
    assert math.isfinite(rep["per_module"]["a.layers.0.w"]["delta_norm_estimated"])


def test_a_healthy_run_is_unaffected_by_the_new_branch():
    """⛔ The fix must not move the verdict on a run that worked."""
    w = _init()
    p = _params({"model.layers.0.mlp.up_proj.weight": w})
    snap = snapshot(p)
    with torch.no_grad():
        p[0][1].add_(1e-4)
    rep = measure(p, snap, lr=1e-5)
    assert rep["verdict"] == OK
    assert rep["fraction_nonfinite"] == 0.0
