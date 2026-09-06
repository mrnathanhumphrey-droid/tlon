"""THE PRE-CLIP GRADIENT PROBE — does it name the CAUSE where the old scan named
168 CASUALTIES?

⛔⛔ THE INSTRUMENT WAS TWICE POSITIONED DOWNSTREAM OF A TRANSFORMATION THAT
DESTROYED THE SIGNAL. `logging_nan_inf_filter` replaced a NaN loss with a running
average, so the trace read a mask and called it a measurement. Then
`clip_grad_norm_` — one GLOBAL norm over every parameter — turned a single
tensor's overflow into a non-finite coefficient applied to all 168 gradients,
and the existing scan runs after it.

⭐ SO THE TEST THAT MATTERS IS THE DISCRIMINATING ONE: build a model where
exactly ONE tensor's gradient is non-finite, run the real `clip_grad_norm_` over
it, and assert that the post-clip view says "everything" while the pre-clip view
says the one name. A probe that cannot separate those has not been tested, it
has been exercised.
"""
import pytest

torch = pytest.importorskip("torch")

from tlon.act2.step_trace import (ForwardProbe, PreClipGradProbe,  # noqa: E402
                                  StepTrace)


class _Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.a = torch.nn.Linear(4, 4, bias=False)
        self.b = torch.nn.Linear(4, 4, bias=False)
        self.c = torch.nn.Linear(4, 2, bias=False)

    def forward(self, x):
        return self.c(self.b(self.a(x)))


def _probe_a_backward(scale_on=None, scale=1.0):
    m = _Tiny()
    probe = PreClipGradProbe(m, window={0})
    probe.arm(0)
    x = torch.randn(8, 4)
    out = m(x)
    if scale_on is not None:
        # ⭐ INJECT THE OVERFLOW INTO EXACTLY ONE TENSOR, via a hook that runs
        # after the real backward has produced a real gradient. Multiplying a
        # genuine gradient keeps every other tensor's value untouched, which is
        # the condition the test exists to check.
        dict(m.named_parameters())[scale_on].register_hook(lambda g: g * scale)
        probe.close()
        probe = PreClipGradProbe(m, window={0})
        probe.arm(0)
        out = m(x)
    out.sum().backward()
    return m, probe


def test_probe_sees_every_trainable_tensor():
    m, probe = _probe_a_backward()
    scan, absmax, arrivals = probe.snapshot()
    names = {n for n, _ in m.named_parameters()}
    assert set(scan) == names
    assert all(fin for _, fin, _ in scan.values())
    assert set(absmax) == names
    # ⭐ The absmax is a real magnitude, not a placeholder.
    assert all(v >= 0.0 for v in absmax.values())
    assert arrivals and {n for _, n in arrivals} == names
    probe.close()


def test_arrival_order_is_reverse_topological():
    """⭐ THE ORDERING IS THE LOCALISER. Gradients finalise from the loss
    backwards, so `c` completes before `a`. Without that the pre-clip set names
    a group of tensors and nothing says which end of it the fault entered."""
    _, probe = _probe_a_backward()
    _, _, arrivals = probe.snapshot()
    order = [n for _, n in arrivals]
    assert order.index("c.weight") < order.index("b.weight")
    assert order.index("b.weight") < order.index("a.weight")
    probe.close()


def test_one_NAN_gradient_makes_every_gradient_nan_through_the_clip():
    """⛔⛔ THE WHOLE POINT, WITH THE REAL `clip_grad_norm_` IN THE LOOP."""
    m, probe = _probe_a_backward(scale_on="b.weight", scale=float("nan"))
    pre, _, _ = probe.snapshot()
    bad_pre = sorted(n for n, (_, fin, _) in pre.items() if not fin)
    assert bad_pre == ["b.weight"], bad_pre

    total = torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
    assert torch.isnan(total), "the GLOBAL norm must go NaN"

    bad_post = sorted(n for n, p in m.named_parameters()
                      if not torch.isfinite(p.grad).all())
    # ⛔ Every tensor, from one tensor. This is the 168.
    assert bad_post == ["a.weight", "b.weight", "c.weight"], bad_post
    assert len(bad_post) > len(bad_pre)
    probe.close()


def test_one_INF_gradient_does_NOT_spread_and_leaves_a_different_fingerprint():
    """⭐⭐ THE POST-CLIP SIGNATURE DISCRIMINATES inf FROM NaN, AND THE RUN THAT
    BROKE LEFT THE NaN ONE.

    total_norm is inf  -> clip_coef = 1/inf = 0 -> every FINITE gradient is
    multiplied to exactly 0 (still finite) and only the offender, inf * 0,
    becomes NaN. total_norm is NaN -> clip_coef is NaN -> ALL of them go NaN.

    The failing run reported 168 of 168 non-finite AFTER the clip. That is the
    NaN branch, so the originating value was a NaN and NOT a magnitude overflow
    to infinity — which matches bf16 carrying the same exponent range as fp32,
    and points at inf-inf, 0*inf or 0/0 inside the backward rather than at a
    number simply growing too large."""
    m, probe = _probe_a_backward(scale_on="b.weight", scale=float("inf"))
    pre, _, _ = probe.snapshot()
    assert sorted(n for n, (_, fin, _) in pre.items() if not fin) == ["b.weight"]

    total = torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
    assert torch.isinf(total) and not torch.isnan(total)

    grads = dict(m.named_parameters())
    assert torch.isnan(grads["b.weight"].grad).any()
    # ⛔ The others are ZEROED, not poisoned — a finite, and very distinguishable,
    # outcome. Had the run produced this, the reading would be a different one.
    for n in ("a.weight", "c.weight"):
        assert torch.isfinite(grads[n].grad).all()
        assert float(grads[n].grad.abs().max()) == 0.0
    probe.close()


def test_probe_refuses_a_model_with_nothing_trainable():
    m = _Tiny()
    for p in m.parameters():
        p.requires_grad_(False)
    with pytest.raises(ValueError):
        PreClipGradProbe(m, window={0})


def test_forward_probe_returns_nothing_outside_its_window():
    """⛔⛔ THE STALENESS BUG, PINNED. `snapshot()` used to return the last armed
    step's records forever, so rows 15-19 of the raw-loss trace were five
    identical copies of step 14 wearing later step numbers — a plateau that was
    the instrument's memory, not the model's behaviour."""
    m = _Tiny()
    fp = ForwardProbe(m, window={0})
    fp.arm(0)
    m(torch.randn(2, 4))
    inside = fp.snapshot()
    assert inside and "c" in inside
    fp.arm(1)
    assert fp.snapshot() is None
    fp.close()


def test_row_carries_preclip_and_postclip_under_distinct_names(tmp_path):
    """⛔ CAVEAT IN THE KEY, NOT THE PROSE. A field called `grad_norm_total`
    that silently held a post-clip number is how the last reading was built on
    the wrong quantity."""
    t = StepTrace(tmp_path / "t.jsonl")
    one = {"x": ("2d", True, 2.0)}
    bad = {"x": ("2d", False, None), "y": ("1d", False, None)}
    t.record(loss=1.0, raw_loss=1.0, grads=bad, preclip=one,
             weights=one, moments=one,
             grad_norm_hf={"hf_global_step": 0, "value": float("nan")},
             preclip_absmax={"x": 3.0})
    t.close()
    import json
    row = json.loads((tmp_path / "t.jsonl").read_text().splitlines()[0])
    assert row["grad_PRECLIP_nonfinite_n"] == 0
    assert row["grad_POSTCLIP_nonfinite_n"] == 2
    assert row["grad_norm_total_PRECLIP_ours"] == pytest.approx(2.0)
    assert row["grad_absmax_PRECLIP"] == {"x": 3.0}
    assert row["grad_norm_HF_preclip"]["hf_global_step"] == 0
    assert "grad_norm_total" not in row, "the un-suffixed name must not exist"


def test_first_nonfinite_prefers_the_preclip_cause(tmp_path):
    """⭐ ORDERING DECIDES THE VERDICT. In the same step the pre-clip cause and
    the post-clip spread are both present; the summary must resolve to the one
    that can be acted on."""
    t = StepTrace(tmp_path / "t.jsonl")
    ok = {"x": ("2d", True, 1.0), "y": ("1d", True, 1.0)}
    t.record(loss=1.0, raw_loss=1.0, grads=ok, preclip=ok,
             weights=ok, moments=ok)
    t.record(loss=1.0, raw_loss=1.0,
             grads={"x": ("2d", False, None), "y": ("1d", False, None)},
             preclip={"x": ("2d", True, 1.0), "y": ("1d", False, None)},
             weights=ok, moments=ok)
    t.close()
    assert t.first_nonfinite["quantity"] == "grad_PRECLIP"
    assert t.first_nonfinite["step"] == 1
    assert t.first_nonfinite["tensors"] == ["y"]
    assert t.first_nonfinite["n"] == 1
