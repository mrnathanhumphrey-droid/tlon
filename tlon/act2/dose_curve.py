"""⭐⭐ READ THE SPEAKER *DURING* THE RUN, SO DOSE IS A CURVE AND NOT A SCALAR.

WHY THIS EXISTS, STATED AS THE EXPERIMENT IT REPLACES. Three mapping runs have
now cratered directed production — Qwen `render` 0.0 % at 176.9 % dose and
0.0 % again at 143.9 %, Mistral 26.6 % at 166.5 %, all three on the identical
F-LOCAL battery `a2b318d6d2e6b98a`. ⛔ But NO mapping run has ever been
dose-matched to the layer rungs (3.1180e-04), so "the mapping touch craters the
speaker" is confounded with "every mapping run was over-dosed".

⛔⛔ AND THE OBVIOUS FIX MAKES THE CONFOUND WORSE. To land on 3.1180e-04 by
halting early you stop at roughly 60 % of the epoch — about 40 % fewer examples
than any layer rung saw. The fine-tune is what *installs* Tlön (the layer rung's
render 93.8 % was LEARNED, not native), so a crater in that run is explained
equally well by "the mapping touch breaks render" and by "we showed it 40 % less
data". **The matching mechanism becomes a rival cause of the measured outcome.**
A confound you introduce while controlling a variable is not a caveat to record.

⭐ SO DO NOT MATCH A SCALAR — MEASURE THE WHOLE CURVE. Train the full epoch,
changing nothing, and read F-LOCAL at several points along the way. The
dose-matched reading is then simply ONE POINT on that curve, taken while the
epoch still completes, so nothing was traded away to reach it. And every point
shares one base, one corpus, one battery and one seed, so the comparison is
within-run and there is no cross-run difference left to defend.

  render already destroyed at low dose  -> the MAPPING TOUCH, settled
  render degrades as dose rises         -> DOSE, and the curve says where
                                           the usable dose ends

⭐ It also yields this base's own rms-vs-steps points as a by-product — the
second dose point that made the LR question answerable. That question was
UNANSWERABLE from one point: one measurement fixes an intercept, never a slope,
so every exponent "predicted" Mistral's single point exactly while implying
dose-matched learning rates from 6e-8 to 6e-6, a 98x spread.
"""
from __future__ import annotations

import math


class EvalContaminatedTraining(RuntimeError):
    """⛔ Raised, never warned. A curve measured by perturbing the run it is
    measuring is a curve of a different run, and nothing downstream could tell."""


def checkpoint_steps(total_steps: int, k: int = 5) -> list[int]:
    """Where to read, spaced GEOMETRICALLY and deliberately so.

    ⭐ The question this run exists to answer is *"is render destroyed
    immediately, or does it decay with dose?"* — which is a question about the
    LOW end. Even spacing spends most of its reads where both hypotheses already
    predict the same thing. Halving back from the end puts half the reads in the
    first quarter of the run, where the hypotheses separate.

    >>> checkpoint_steps(3760, 5)
    [235, 470, 940, 1880, 3760]
    """
    if total_steps < 1:
        raise ValueError("total_steps must be >= 1, got %r" % (total_steps,))
    if k < 1:
        raise ValueError("k must be >= 1, got %r" % (k,))
    out: list[int] = []
    for i in range(k):
        s = int(round(total_steps / (2 ** i)))
        if s >= 1:
            out.append(s)
    # ⛔ De-duplicated: on a short run the halvings collide, and reading the same
    # step twice would enter the curve as two points that cannot disagree.
    return sorted(set(out))


def rms_per_param(delta: dict) -> float | None:
    """The dose, denominated the way every dose in this arm is denominated.

    ⛔ `fraction_changed` is NOT a dose — it saturates, and §4.1 uses it as a
    precondition only. `delta_norm` alone is not a dose either: it grows with
    the number of parameters, so comparing it across scopes compares sizes.
    """
    n = delta.get("n_trainable_params")
    dn = delta.get("delta_norm_estimated")
    if not n or dn is None:
        return None
    # ⛔ NaN is not a dose. `dn != dn` catches the diverged run, whose delta
    # norm is non-finite and whose rms would otherwise propagate silently.
    if isinstance(dn, float) and dn != dn:
        return None
    return dn / math.sqrt(n)


def crossed(previous: float | None, current: float | None,
            target: float) -> bool:
    """Did the dose cross `target` between these two measurements?

    ⭐ THIS IS WHAT REPLACES THE EARLY HALT. The dose-matched point is read when
    the run passes through it — and then training CONTINUES. That is the whole
    difference between this design and the one it replaces: the matched dose is
    observed rather than arranged, so no examples are given up to reach it and
    the epoch that produced every other campaign reading still completes.
    """
    if current is None:
        return False
    if previous is None:
        return current >= target
    return previous < target <= current


class isolated_read:
    """⛔⛔ A READ THAT PERTURBS THE RUN IT MEASURES INVALIDATES THE WHOLE CURVE.

    Generation mid-training touches three things that belong to the training
    process, and all three are restored here rather than assumed harmless:

      1. **Module mode.** `generate` needs `eval()`; leaving it there silently
         disables dropout for the REST OF TRAINING. The run would finish, report
         a clean loss, and be a different experiment.
      2. **RNG state.** F-LOCAL decodes greedily (`temperature=0.0`, so
         `do_sample=False`) and should draw nothing — ⛔ but "should draw
         nothing" is exactly the assumption this project keeps paying for, so
         the state is saved and restored regardless, and the restore is asserted
         rather than trusted.
      3. **Gradients.** Any grad left on a trainable leaf by a read would be
         added to the next optimizer step, moving weights by an amount no dose
         accounts for.

    ⭐ It ASSERTS on the way out. A silent restore-that-did-not is the failure
    mode, so the check runs on exit and raises `EvalContaminatedTraining`.
    """

    def __init__(self, model, *, torch_mod=None):
        self._m = model
        self._torch = torch_mod
        self._was_training = None
        self._cpu_state = None
        self._cuda_states = None

    def _t(self):
        if self._torch is None:
            import torch
            self._torch = torch
        return self._torch

    def __enter__(self):
        t = self._t()
        self._was_training = bool(self._m.training)
        self._cpu_state = t.get_rng_state()
        if t.cuda.is_available():
            self._cuda_states = t.cuda.get_rng_state_all()
        self._m.eval()
        return self

    def __exit__(self, exc_type, exc, tb):
        t = self._t()
        # ⛔ ORDER MATTERS: restore BEFORE asserting, or a raised assertion
        # leaves the run in the contaminated state it was complaining about.
        t.set_rng_state(self._cpu_state)
        if self._cuda_states is not None:
            t.cuda.set_rng_state_all(self._cuda_states)
        if self._was_training:
            self._m.train()
        # ⛔ Grads produced by a read are not the run's. Cleared unconditionally:
        # `generate` runs under no_grad, so there should be none — and "should"
        # is not a guarantee that survives a backend change.
        self._m.zero_grad(set_to_none=True)

        if exc_type is None:
            if bool(self._m.training) != self._was_training:
                raise EvalContaminatedTraining(
                    "the model's training mode was not restored (was %s, now "
                    "%s). The remaining steps would run with different dropout "
                    "than the ones before the read."
                    % (self._was_training, self._m.training))
            if not t.equal(t.get_rng_state(), self._cpu_state):
                raise EvalContaminatedTraining(
                    "the CPU RNG state was not restored by the read. Every "
                    "draw after this point belongs to a different run than the "
                    "one before it.")
        return False
