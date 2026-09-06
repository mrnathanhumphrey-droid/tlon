"""THE KERNEL DUEL'S VERDICT LOGIC — especially its refusals.

⛔⛔ THE POINT OF THIS FILE IS THE HARNESS CHECK. If our own SDPA re-run does not
reproduce the trainer's SDPA backward, then the eager leg is not comparable to
anything, and a duel that reports a verdict anyway would be measuring its own
harness and calling it the kernel. That branch must fire BEFORE any comparison
between the two legs is made.
"""
import pytest

from tlon.act2.kernel_duel import (INSTRUMENT_FAULT, KERNEL_EXONERATED,
                                   KERNEL_IMPLICATED, NO_FAULT_TO_EXPLAIN,
                                   compare, flip_attn_implementation)


def _scan(bad=(), names=("a", "b", "c")):
    return {n: ("2d", n not in bad, None if n in bad else 1.0) for n in names}


def test_sdpa_breaks_and_eager_does_not_implicates_the_kernel():
    r = compare(_scan(bad=("a", "b")), _scan(bad=("a", "b")), _scan())
    assert r["verdict"] == KERNEL_IMPLICATED
    assert "identical weights on identical inputs" in r["why"]


def test_both_kernels_break_exonerates_the_fused_path():
    r = compare(_scan(bad=("a",)), _scan(bad=("a",)), _scan(bad=("a",)))
    assert r["verdict"] == KERNEL_EXONERATED
    assert "not in the fused path" in r["why"]


def test_neither_breaks_is_not_a_verdict_about_the_kernel():
    """⛔ The trigger is data-dependent, so landing on the wrong batch is a live
    outcome. It must not read as 'eager fixed it'."""
    r = compare(_scan(), _scan(), _scan())
    assert r["verdict"] == NO_FAULT_TO_EXPLAIN
    assert "not the trigger" in r["why"]


def test_harness_disagreement_refuses_a_verdict():
    """⛔⛔ Our SDPA leg found something the trainer's did not (or vice versa):
    the two legs are then not measuring the same thing and no kernel claim is
    available."""
    r = compare(_scan(bad=("a", "b")), _scan(bad=("a",)), _scan())
    assert r["verdict"] == INSTRUMENT_FAULT
    assert "not comparable" in r["why"]
    assert r["verdict"] != KERNEL_IMPLICATED


def test_harness_check_precedes_the_kernel_comparison():
    """⛔ The ordering matters: a disagreeing harness with a clean eager leg
    looks exactly like the headline result, so the fault branch must win."""
    r = compare(_scan(bad=("a",)), _scan(bad=("a", "b", "c")), _scan())
    assert r["verdict"] == INSTRUMENT_FAULT


def test_no_probe_means_no_harness_check_but_still_a_verdict():
    r = compare(None, _scan(bad=("a",)), _scan())
    assert r["verdict"] == KERNEL_IMPLICATED
    assert r["trainer_sdpa_nonfinite_n"] is None


def test_eager_breaking_where_sdpa_does_not_is_reported_not_swallowed():
    r = compare(None, _scan(), _scan(bad=("c",)))
    assert r["verdict"] == KERNEL_EXONERATED
    assert "opposite of the hypothesis" in r["why"]


def test_counts_are_reported_for_every_leg():
    r = compare(_scan(bad=("a",)), _scan(bad=("a",)), _scan(bad=("b", "c")))
    assert r["our_sdpa_nonfinite_n"] == 1
    assert r["our_eager_nonfinite_n"] == 2
    assert r["trainer_sdpa_nonfinite_n"] == 1


def test_flip_refuses_a_half_flipped_model():
    """⛔ A model left half on one kernel would run the new attention against
    the old mask format and report a difference that is a wiring bug."""
    class _Cfg:
        def __init__(self): self._attn_implementation = "sdpa"

    class _Stubborn:
        """A submodule whose config refuses to change — stands in for a copied
        config that does not follow the top level."""
        def __init__(self):
            self.config = _Cfg()
            object.__setattr__(self.config, "_locked", True)

    class _Model:
        def __init__(self):
            self.config = _Cfg()
            self._sub = _Stubborn()

        def modules(self):
            return [self, self._sub]

    m = _Model()
    assert flip_attn_implementation(m, "eager") == "sdpa"
    assert m.config._attn_implementation == "eager"
    assert m._sub.config._attn_implementation == "eager"

    # and the refusal itself, with a submodule that genuinely cannot follow
    class _Frozen(_Cfg):
        def __setattr__(self, k, v):
            if k == "_attn_implementation" and getattr(self, k, None) is not None:
                return
            object.__setattr__(self, k, v)

    m2 = _Model()
    m2._sub.config = _Frozen()
    with pytest.raises(RuntimeError, match="did not flip everywhere"):
        flip_attn_implementation(m2, "eager")
