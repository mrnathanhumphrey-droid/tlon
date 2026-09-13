"""THE DOSE CURVE — and the reads that must not disturb the run they measure.

⛔ The tests that matter here are the CONTAMINATION ones. A wrong checkpoint
schedule gives a coarse curve; a read that leaves the model in `eval()` gives a
clean-looking curve OF A DIFFERENT RUN, and nothing downstream can tell.
"""
import math

import pytest

from tlon.act2.dose_curve import (EvalContaminatedTraining, checkpoint_steps,
                                  crossed, isolated_read, rms_per_param)


# ── the schedule ────────────────────────────────────────────────────────────

def test_checkpoints_are_geometric_and_land_on_the_run_this_was_built_for():
    assert checkpoint_steps(3760, 5) == [235, 470, 940, 1880, 3760]


def test_half_the_reads_sit_in_the_first_quarter():
    """⭐ The low end is where 'destroyed immediately' and 'decays with dose'
    make different predictions. Even spacing would spend the budget where they
    agree."""
    steps = checkpoint_steps(3760, 5)
    early = [s for s in steps if s <= 3760 / 4]
    assert len(early) >= len(steps) / 2


def test_the_final_step_is_always_read():
    """⛔ Without the endpoint the curve cannot be tied to the full-epoch
    readings every other run in the campaign produced."""
    for total in (3760, 1000, 17):
        assert checkpoint_steps(total, 5)[-1] == total


def test_colliding_halvings_are_deduplicated():
    """⛔ A repeated step would enter the curve as two points that cannot
    disagree — a fake corroboration."""
    steps = checkpoint_steps(3, 6)
    assert len(steps) == len(set(steps))
    assert all(s >= 1 for s in steps)


@pytest.mark.parametrize("bad", [0, -1])
def test_a_nonsense_total_refuses(bad):
    with pytest.raises(ValueError):
        checkpoint_steps(bad, 5)


# ── the dose itself ─────────────────────────────────────────────────────────

def test_rms_is_per_parameter_so_it_compares_across_scopes():
    """The mapping is 268,435,456 params and the layer rung 4,428,098,048; a
    raw delta norm would compare sizes, not doses."""
    got = rms_per_param({"n_trainable_params": 268435456,
                         "delta_norm_estimated": 8.503311313368224})
    assert math.isclose(got, 5.1900e-04, rel_tol=1e-3)


def test_a_nonfinite_delta_has_no_dose():
    """⛔⛔ NaN is not a small number. A diverged run must yield None, not a
    dose that propagates into the curve."""
    assert rms_per_param({"n_trainable_params": 100,
                          "delta_norm_estimated": float("nan")}) is None


def test_a_missing_delta_has_no_dose():
    assert rms_per_param({"n_trainable_params": 100}) is None
    assert rms_per_param({"delta_norm_estimated": 1.0}) is None


# ── the crossing that replaces the early halt ───────────────────────────────

def test_the_matched_dose_is_read_when_the_run_passes_through_it():
    """⭐ THE POINT OF THE WHOLE DESIGN. The layer-rung dose is observed in
    passing, and training continues — so no examples are given up to reach it."""
    assert crossed(2.9e-4, 3.2e-4, 3.118e-4) is True


def test_a_dose_already_past_the_target_does_not_re_trigger():
    """⛔ Otherwise every later checkpoint re-reads the matched dose and the
    curve fills with duplicates of one point."""
    assert crossed(3.2e-4, 4.0e-4, 3.118e-4) is False


def test_the_first_measurement_above_target_counts_as_a_crossing():
    assert crossed(None, 3.2e-4, 3.118e-4) is True
    assert crossed(None, 2.0e-4, 3.118e-4) is False


def test_an_unmeasurable_dose_never_triggers_a_read():
    """⛔ `None` is 'we could not measure', which is not 'we crossed'."""
    assert crossed(2.9e-4, None, 3.118e-4) is False


# ── contamination: the tests this module exists for ────────────────────────

class _FakeModel:
    """Stands in for the trainable model. No GPU, no weights — the contract
    under test is mode/RNG/grad restoration, which is framework state."""

    def __init__(self):
        self.training = True
        self.zeroed = 0

    def eval(self):
        self.training = False

    def train(self):
        self.training = True

    def zero_grad(self, set_to_none=False):
        self.zeroed += 1


def test_training_mode_is_restored_after_a_read():
    """⛔⛔ THE QUIET KILLER. Left in eval(), the remaining steps run without
    dropout — the run finishes, reports a clean loss, and is a different
    experiment than the one the prereg describes."""
    import torch
    m = _FakeModel()
    with isolated_read(m, torch_mod=torch):
        assert m.training is False        # the read needs eval()
    assert m.training is True


def test_a_model_already_in_eval_is_left_in_eval():
    """⛔ Restoring to 'training' unconditionally would START training a model
    the caller had deliberately put in eval."""
    import torch
    m = _FakeModel()
    m.eval()
    with isolated_read(m, torch_mod=torch):
        pass
    assert m.training is False


def test_the_rng_stream_is_byte_identical_across_a_read():
    """⭐ F-LOCAL decodes greedily and SHOULD draw nothing — but 'should draw
    nothing' is precisely the assumption this project keeps paying for."""
    import torch
    torch.manual_seed(20624)
    m = _FakeModel()
    before = torch.get_rng_state().clone()
    with isolated_read(m, torch_mod=torch):
        torch.randn(64)               # a read that DOES consume the stream
    assert torch.equal(torch.get_rng_state(), before)


def test_the_draw_after_a_read_is_the_draw_that_would_have_come_next():
    """⭐⭐ THE ONE THAT ACTUALLY MATTERS. State equality is a proxy; this
    asserts the training stream continues exactly where it would have."""
    import torch
    torch.manual_seed(20624)
    expected = torch.randn(4)

    torch.manual_seed(20624)
    m = _FakeModel()
    with isolated_read(m, torch_mod=torch):
        torch.randn(1000)
    assert torch.equal(torch.randn(4), expected)


def test_grads_left_by_a_read_are_cleared():
    """⛔ A grad produced by a read would be added to the next optimizer step,
    moving the weights by an amount no dose accounts for."""
    import torch
    m = _FakeModel()
    with isolated_read(m, torch_mod=torch):
        pass
    assert m.zeroed == 1


def test_an_exception_inside_the_read_still_restores_the_run():
    """⛔ A read that raises must not leave training contaminated — that would
    turn a recoverable error into a silently different experiment."""
    import torch
    torch.manual_seed(20624)
    m = _FakeModel()
    before = torch.get_rng_state().clone()
    with pytest.raises(ValueError):
        with isolated_read(m, torch_mod=torch):
            torch.randn(8)
            raise ValueError("the backend refused a malformed generation")
    assert m.training is True
    assert torch.equal(torch.get_rng_state(), before)


def test_a_broken_restore_is_raised_not_warned():
    """⛔⛔ The failure mode is a SILENT restore-that-did-not. If the guard
    cannot restore, it must stop the run rather than let the curve be measured
    against a perturbed one."""
    import torch

    class _Stuck(_FakeModel):
        def train(self):            # refuses to leave eval
            pass

    m = _Stuck()
    with pytest.raises(EvalContaminatedTraining):
        with isolated_read(m, torch_mod=torch):
            pass
