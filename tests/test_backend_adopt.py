"""⭐ THE IN-PROCESS BACKEND — reading a model the trainer owns.

⛔ The contract under test is what `adopt` must NOT do. It borrows a live model
mid-training, so any state it changes and does not restore is a change to the
run being measured.
"""
import importlib.util
import pathlib

import pytest


def _backends():
    p = (pathlib.Path(__file__).resolve().parents[1] / "tools"
         / "act2_backends.py")
    spec = importlib.util.spec_from_file_location("_be", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Model:
    def __init__(self):
        self.training = True
        self.eval_calls = 0

    def eval(self):
        self.eval_calls += 1
        self.training = False


class _Tok:
    pad_token_id = 0
    eos_token_id = 1


def test_adopt_does_not_touch_training_mode():
    """⛔⛔ `__init__` calls `.eval()` because it OWNS a freshly loaded model.
    `adopt` borrows one the trainer owns: flipping mode here would disable
    dropout for every remaining step of the run."""
    be = _backends()
    m = _Model()
    be.LocalBackend.adopt(m, _Tok(), name="mismap-s20624")
    assert m.eval_calls == 0
    assert m.training is True


def test_adopt_loads_nothing():
    """⭐ The whole point: no checkpoint on disk, no second copy in VRAM. If
    this ever starts loading, the 72 GB storage problem is back."""
    be = _backends()
    m, t = _Model(), _Tok()
    b = be.LocalBackend.adopt(m, t, name="x")
    assert b.model is m
    assert b.tok is t


def test_the_adopted_backend_is_named_so_a_reading_cannot_be_mistaken():
    """⛔ A mid-run reading and a reading of the persisted object are different
    measurements of different weights. They must not share a name."""
    be = _backends()
    b = be.LocalBackend.adopt(_Model(), _Tok(), name="mismap-s20624")
    assert b.name.startswith("live:")
    assert b.name != "local:mismap-s20624"


def test_it_defaults_to_greedy_and_unconstrained_like_the_gate_requires():
    """⛔⛔ Constrained decoding would make an illegal emission impossible and
    F-LOCAL would read 1.00 by construction. Greedy (temperature 0) also means
    the read draws nothing from the training RNG stream."""
    be = _backends()
    b = be.LocalBackend.adopt(_Model(), _Tok(), name="x")
    assert b.constrained is False
    assert b.temperature == 0.0


def test_a_constrained_adopted_backend_still_declares_itself():
    """⭐ `falsify.f_local` refuses to score a constrained run. The flag has to
    survive this construction path too, or the refusal cannot fire."""
    be = _backends()
    b = be.LocalBackend.adopt(_Model(), _Tok(), name="x", constrained=True)
    assert b.constrained is True


def test_adopt_starts_with_an_empty_cost_log():
    """⛔ Sharing a call log across reads would attribute one checkpoint's
    generations to another's."""
    be = _backends()
    a = be.LocalBackend.adopt(_Model(), _Tok(), name="x")
    b = be.LocalBackend.adopt(_Model(), _Tok(), name="y")
    a.calls.append({"n": 1})
    assert b.calls == []


def test_adopt_and_init_expose_the_same_surface():
    """⛔ A second constructor that omits an attribute fails at the first call
    site that uses it — mid-run, on a rented box, with the reading lost."""
    be = _backends()
    adopted = be.LocalBackend.adopt(_Model(), _Tok(), name="x")
    import inspect
    src = inspect.getsource(be.LocalBackend.__init__)
    assigned = {ln.split("self.", 1)[1].split(" ")[0].split(":")[0]
                for ln in src.splitlines() if "self." in ln and "=" in ln
                and ln.strip().startswith("self.")}
    missing = {a for a in assigned if not hasattr(adopted, a)}
    assert not missing, "adopt() omits %s" % sorted(missing)
