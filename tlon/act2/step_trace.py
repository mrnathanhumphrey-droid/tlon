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

    def record(self, *, loss, grads, weights, moments):
        """`grads`/`weights`/`moments`: {name: (rank, finite: bool, norm|None)}."""
        row = {"step": self.step, "loss": loss}
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


def make_callback(trace: StepTrace):
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
