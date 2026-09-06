"""PER-STEP, PER-MODULE TRACE OF A COLLAPSE — grad, weight, and moment, in order.

⛔⛔ THE ORIGINAL RUN LOGGED EVERY 25 STEPS AND THAT IS WHY NOTHING IS KNOWN. Its
first sample was 7.548 and its second was ~0, so the collapse is bracketed
between step 1 and step 25 and nothing narrows it further. Five mechanisms were
then excluded by positive test, and every one of them was excluded *in
isolation* — because from the outside a degenerate objective, a forward/backward
numerical failure, and an optimizer-path failure all look identical: loss goes
to zero and a model comes out broken.

⭐⭐ WHAT SEPARATES THEM IS ORDERING, AND ORDERING NEEDS TWO HOOKS. The three
causes make different predictions about WHICH quantity goes bad FIRST:

    gradient non-finite first      -> forward/backward numerical
    weight/moment non-finite first -> optimizer path
    everything finite, grad -> 0   -> degenerate objective, no NaN at all

So this records the gradients BEFORE the optimizer runs and the weights and
optimizer state AFTER it, every step, per module. A single post-step snapshot
cannot tell those apart: by then the weight is NaN either way.

⛔ SAMPLED NOWHERE, REDUCED EVERYWHERE. `isfinite(x).all()` is one pass over the
tensor and answers the question exactly; the estimate-from-a-subsample trick
that `weight_delta` needs for a norm is not needed for a boolean and would add
a false-negative rate to the one signal this exists to catch.

⭐ The trace is JSONL, one row per optimizer step, flushed every row — a trace
buffered in memory is a trace that dies with the process it was watching, which
is precisely the failure mode being investigated.
"""
from __future__ import annotations

import json
import pathlib


def _module_of(name: str) -> str:
    """`model.layers.14.self_attn.q_proj.weight` -> itself. Kept whole on
    purpose: the production fingerprint was per-TENSOR (all 1-D NaN, all 2-D
    finite), so collapsing to a layer would erase the distinction that
    localises the fault."""
    return name


def rank_of(p) -> str:
    return "1d" if p.dim() == 1 else "2d"


class StepTrace:
    """Collects one row per optimizer step. Framework-free so it is testable."""

    def __init__(self, path, *, dense_until: int = 100):
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = self.path.open("w", encoding="utf-8")
        #: ⭐ Dense early, thinner later. The collapse hit by ~50 last time, so
        #: the diagnostic value is front-loaded; recording every module every
        #: step for 300 steps would make a trace nobody opens.
        self.dense_until = dense_until
        self.step = 0
        self.first_nonfinite = None

    def record(self, *, loss, grads, weights, moments,
               raw_loss=None, activations=None):
        """`grads`/`weights`/`moments`: {name: (rank, finite: bool, norm|None)}.

        ⛔⛔ `loss` IS THE FRAMEWORK'S FILTERED VALUE AND IS NAMED SO. It is
        recorded only to show the divergence; `raw_loss` comes from the model
        output and is the arbiter. The first version of this trace had one field
        called `loss`, holding the filtered number, and it read finite at the
        step every gradient in the model had already died.
        """
        row = {"step": self.step,
               "loss_LOGGED_FILTERED": loss,
               "loss_raw": raw_loss,
               "loss_raw_finite": (None if raw_loss is None
                                   else bool(raw_loss == raw_loss
                                             and abs(raw_loss) != float("inf")))}
        for label, d in (("grad", grads), ("weight", weights),
                         ("moment", moments)):
            bad = sorted(n for n, (_, fin, _) in d.items() if not fin)
            row["%s_nonfinite_n" % label] = len(bad)
            row["%s_nonfinite_1d" % label] = sum(
                1 for n in bad if d[n][0] == "1d")
            row["%s_nonfinite_2d" % label] = sum(
                1 for n in bad if d[n][0] == "2d")
            # ⛔ NAME THE FIRST OFFENDERS, not just the count. "3 tensors went
            # NaN" does not say whether they were layernorms or matrices, and
            # that distinction is the fingerprint.
            row["%s_nonfinite_first" % label] = bad[:3]
        norms = [v[2] for v in grads.values() if v[2] is not None and v[1]]
        row["grad_norm_total"] = (sum(n * n for n in norms) ** 0.5
                                  if norms else None)
        row["grad_norm_max"] = max(norms) if norms else None
        # ⛔⛔ THE ANSWER, RECORDED THE INSTANT IT EXISTS. Which quantity went
        # non-finite first, and on which tensor, is the whole deliverable; a
        # trace that requires post-hoc reconstruction to answer it can be
        # mis-reconstructed.
        if self.first_nonfinite is None:
            for label, d in (("grad", grads), ("weight", weights),
                             ("moment", moments)):
                bad = sorted(n for n, (_, fin, _) in d.items() if not fin)
                if bad:
                    self.first_nonfinite = {
                        "step": self.step, "quantity": label,
                        "tensors": bad[:8], "n": len(bad),
                        "rank": d[bad[0]][0],
                    }
                    row["FIRST_NONFINITE"] = self.first_nonfinite
                    break
        if self.step < self.dense_until:
            row["per_module_grad_norm"] = {
                n: v[2] for n, v in sorted(grads.items()) if v[2] is not None}
        # ⭐⭐ MAGNITUDES ACROSS THE APPROACH TO A KNOWN CLIFF. Determinism is
        # what makes this worth recording: the break is at the same step in two
        # runs with different assemblies, so this is a quantity crossing a
        # threshold at a fixed count, and the absmax at 11 -> 12 -> 13 names
        # WHAT was growing. Finiteness alone only says that it broke.
        if activations:
            row["activation_absmax"] = {
                n: v[1] for n, v in sorted(activations.items())}
            row["activation_nonfinite"] = sorted(
                n for n, v in activations.items() if not v[0])
        self.fh.write(json.dumps(row) + "\n")
        # ⛔ FLUSHED EVERY ROW. A buffered trace dies with the process it was
        # watching, and dying processes are the subject.
        self.fh.flush()
        self.step += 1

    def close(self, extra=None):
        if extra:
            self.fh.write(json.dumps({"SUMMARY": extra}) + "\n")
        self.fh.flush()
        self.fh.close()


def make_callback(trace: StepTrace, *, probe=None, loss_holder=None):
    """A `TrainerCallback` writing into `trace`. Imported lazily so this module
    stays importable (and testable) without transformers."""
    import torch
    from transformers import TrainerCallback

    class _Trace(TrainerCallback):
        def __init__(self):
            self.model = None
            self.optimizer = None
            self.pending_grads = None
            self.last_loss = None

        def _scan(self, which):
            out = {}
            for n, p in self.model.named_parameters():
                if not p.requires_grad:
                    continue
                if which == "grad":
                    t = p.grad
                    if t is None:
                        out[n] = (rank_of(p), True, None)
                        continue
                    fin = bool(torch.isfinite(t).all())
                    out[n] = (rank_of(p), fin,
                              float(t.detach().float().norm()) if fin else None)
                elif which == "weight":
                    out[n] = (rank_of(p), bool(torch.isfinite(p).all()), None)
                else:
                    st = (self.optimizer.state.get(p, {})
                          if self.optimizer is not None else {})
                    tensors = [v for v in st.values()
                               if isinstance(v, torch.Tensor)
                               and v.is_floating_point()]
                    fin = all(bool(torch.isfinite(v).all()) for v in tensors)
                    out[n] = (rank_of(p), fin, None)
            return out

        def on_step_begin(self, args, state, control, **kw):
            # ⭐ Arm the forward probe only inside its window, before the
            # micro-batches of this step run.
            if probe is not None:
                probe.arm(trace.step)
            return control

        def on_pre_optimizer_step(self, args, state, control, **kw):
            self.model = kw.get("model", self.model)
            self.optimizer = kw.get("optimizer", self.optimizer)
            # ⭐ GRADIENTS ARE ONLY ALIVE HERE. After the step they are zeroed
            # or stale, so a post-step scan cannot see a NaN gradient at all —
            # which is exactly the branch that would name a forward/backward
            # cause.
            self.pending_grads = self._scan("grad")
            return control

        def on_step_end(self, args, state, control, **kw):
            self.model = kw.get("model", self.model)
            self.optimizer = kw.get("optimizer", self.optimizer)
            if self.model is None:
                return control
            grads = self.pending_grads or {}
            trace.record(loss=self.last_loss,
                         raw_loss=(loss_holder or {}).get("raw"),
                         activations=(probe.snapshot() if probe is not None
                                      else None),
                         grads=grads,
                         weights=self._scan("weight"),
                         moments=self._scan("moment"))
            self.pending_grads = None
            return control

        def on_log(self, args, state, control, logs=None, **kw):
            if logs and "loss" in logs:
                self.last_loss = logs["loss"]
            return control

    return _Trace()


#: ⛔⛔ THE FOUNDING NUMBER OF THIS INVESTIGATION WAS A MASK. `logging_nan_inf_filter`
#: defaults to True, so when the loss is NaN or Inf transformers SUBSTITUTES the
#: running average and logs that. The full-weight run's "loss 7.548 -> 0" never
#: happened: the loss went NaN at step 13 and the substituted average decayed
#: toward zero. Hours of hypotheses were spent explaining a logging artifact.
#:
#: ⭐ And the first version of THIS module inherited the same flaw — it read the
#: loss from `on_log`, which is the filtered value, so its row 13 showed
#: `loss=0.6404, finite=True` while every gradient in the model was already
#: gone. The trace was showing the mask.
#:
#: ⭐⭐ SO: THE RAW LOSS COMES FROM THE MODEL OUTPUT AND NOWHERE ELSE. A
#: framework's logged value is a proxy; the value the model returned is the
#: arbiter, and the two diverge exactly when something is wrong — which is
#: precisely when anyone is looking.
RAW_LOSS_ONLY = True


class ForwardProbe:
    """Per-module forward-output finiteness AND MAGNITUDE, inside a step window.

    ⭐⭐ MAGNITUDES, NOT ONLY FINITENESS, AND THAT IS WHAT DETERMINISM BUYS. The
    failure fires at exactly step 13 in two runs with different assemblies, so
    it is not stochastic — it is a deterministic quantity crossing a threshold
    at a fixed count. Finiteness alone says "it broke at 13"; magnitude across
    11 -> 12 -> 13 says WHAT WAS GROWING. There is no need to sample a flaky
    event, so the instrument can be pointed exactly where it will fire.

    ⛔ Windowed. A hook on every Linear recording an absmax every step of a
    300-step run would cost more than the run; the window is the few steps
    around a break whose location is already known.
    """

    def __init__(self, model, *, window):
        import torch
        self.window = window
        self.active = False
        self.records = {}
        self.handles = []
        for name, mod in model.named_modules():
            if isinstance(mod, torch.nn.Linear) or name.endswith("norm"):
                self.handles.append(
                    mod.register_forward_hook(self._make(name)))

    def _make(self, name):
        import torch

        def hook(_mod, _inp, out):
            if not self.active:
                return
            t = out[0] if isinstance(out, tuple) else out
            if not torch.is_tensor(t) or not t.is_floating_point():
                return
            f = t.detach().float()
            self.records[name] = (bool(torch.isfinite(f).all()),
                                  float(f.abs().max()))
        return hook

    def arm(self, step):
        self.active = step in self.window
        if self.active:
            self.records = {}

    def snapshot(self):
        return dict(self.records)

    def close(self):
        for h in self.handles:
            h.remove()
