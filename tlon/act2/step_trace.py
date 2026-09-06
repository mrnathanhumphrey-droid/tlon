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
               raw_loss=None, activations=None, preclip=None,
               grad_norm_hf=None, preclip_absmax=None, arrivals=None):
        """`grads`/`weights`/`moments`: {name: (rank, finite: bool, norm|None)}.

        ⛔⛔ `loss` IS THE FRAMEWORK'S FILTERED VALUE AND IS NAMED SO. It is
        recorded only to show the divergence; `raw_loss` comes from the model
        output and is the arbiter. The first version of this trace had one field
        called `loss`, holding the filtered number, and it read finite at the
        step every gradient in the model had already died.

        ⛔⛔ AND `grads` IS THE **POST-CLIP** GRADIENT, WHICH IS WHY IT NAMES 168
        CASUALTIES AND NOT ONE CAUSE. `on_pre_optimizer_step` fires at
        trainer.py:1762; `_clip_grad_norm` ran at 1759. `clip_grad_norm_`
        computes ONE GLOBAL NORM over every parameter, so a single overflowing
        tensor makes the total norm non-finite, the clip coefficient non-finite,
        and multiplies EVERY gradient by it. A scan positioned after that point
        can only ever see the aftermath. `preclip` comes from
        `register_post_accumulate_grad_hook`, which fires as each parameter's
        gradient is finalised inside the backward — upstream of the clip — and
        is therefore the only one of the two that can name an origin.
        """
        row = {"step": self.step,
               "loss_LOGGED_FILTERED": loss,
               "loss_raw": raw_loss,
               "loss_raw_finite": (None if raw_loss is None
                                   else bool(raw_loss == raw_loss
                                             and abs(raw_loss) != float("inf")))}
        # ⛔ THE PRE-CLIP SCAN IS FIRST IN THE ORDERING so that `first_nonfinite`
        # resolves to the cause rather than to the globalised effect that
        # follows it in the same step.
        quantities = ([("grad_PRECLIP", preclip)] if preclip is not None else [])
        quantities += [("grad_POSTCLIP", grads), ("weight", weights),
                       ("moment", moments)]
        for label, d in quantities:
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
        row["grad_norm_total_POSTCLIP"] = (sum(n * n for n in norms) ** 0.5
                                           if norms else None)
        row["grad_norm_max_POSTCLIP"] = max(norms) if norms else None
        if preclip is not None:
            pn = [v[2] for v in preclip.values() if v[2] is not None and v[1]]
            # ⭐ OUR OWN pre-clip global norm, computed from the per-parameter
            # squared norms captured inside the backward. This is the same
            # quantity transformers logs as `grad_norm`, arrived at by a
            # different route -- so the two either corroborate or the
            # disagreement is itself the finding.
            row["grad_norm_total_PRECLIP_ours"] = (
                sum(n * n for n in pn) ** 0.5 if pn else None)
            row["grad_norm_max_PRECLIP"] = max(pn) if pn else None
        # ⛔ HF's OWN VALUE, CARRIED WITH THE STEP IT BELONGS TO. `on_log` fires
        # AFTER `on_step_end`, so the number available while writing row N was
        # computed for a different step. Recording the pair rather than the
        # scalar makes any misalignment visible instead of silently absorbed.
        row["grad_norm_HF_preclip"] = grad_norm_hf
        # ⛔⛔ THE ANSWER, RECORDED THE INSTANT IT EXISTS. Which quantity went
        # non-finite first, and on which tensor, is the whole deliverable; a
        # trace that requires post-hoc reconstruction to answer it can be
        # mis-reconstructed.
        if self.first_nonfinite is None:
            for label, d in quantities:
                bad = sorted(n for n, (_, fin, _) in d.items() if not fin)
                if bad:
                    self.first_nonfinite = {
                        "step": self.step, "quantity": label,
                        "tensors": bad[:8], "n": len(bad),
                        "rank": d[bad[0]][0],
                    }
                    row["FIRST_NONFINITE"] = self.first_nonfinite
                    break
        # ⭐⭐ MAGNITUDE PER TENSOR, PRE-CLIP, ACROSS THE APPROACH. Finiteness
        # says WHICH tensor; the absmax trajectory across 11 -> 12 -> 13 says
        # whether it grew into the overflow (compounding) or jumped into it
        # (triggered) -- and that distinction selects the fix class.
        if preclip_absmax:
            row["grad_absmax_PRECLIP"] = dict(sorted(preclip_absmax.items()))
        # ⛔ ARRIVAL ORDER INSIDE THE BACKWARD. Gradients finalise in reverse
        # topological order, so the earliest-arriving non-finite tensor is the
        # one closest to where the backward first produced a non-finite value.
        if arrivals:
            row["preclip_arrival_order"] = arrivals
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


def make_callback(trace: StepTrace, *, probe=None, preclip=None,
                  loss_holder=None):
    """A `TrainerCallback` writing into `trace`. Imported lazily so this module
    stays importable (and testable) without transformers."""
    import torch
    from transformers import TrainerCallback

    class _Trace(TrainerCallback):
        def __init__(self):
            self.model = None
            self.optimizer = None
            self.pending_grads = None
            self.pending_preclip = None
            self.last_loss = None
            self.last_grad_norm = None

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
            # ⭐ Arm the probes only inside their window, before the
            # micro-batches of this step run.
            if probe is not None:
                probe.arm(trace.step)
            if preclip is not None:
                preclip.arm(trace.step)
            return control

        def on_pre_optimizer_step(self, args, state, control, **kw):
            self.model = kw.get("model", self.model)
            self.optimizer = kw.get("optimizer", self.optimizer)
            # ⛔⛔ THIS SCAN IS POST-CLIP AND THE FIELD NAMES SAY SO. The clip
            # ran three lines earlier in the trainer and its norm is GLOBAL, so
            # what this sees at the break step is 168 tensors carrying one
            # tensor's overflow. `preclip` below was filled during the backward,
            # upstream of that.
            self.pending_grads = self._scan("grad")
            self.pending_preclip = (preclip.snapshot()
                                    if preclip is not None else None)
            return control

        def on_step_end(self, args, state, control, **kw):
            self.model = kw.get("model", self.model)
            self.optimizer = kw.get("optimizer", self.optimizer)
            if self.model is None:
                return control
            grads = self.pending_grads or {}
            pc = self.pending_preclip
            trace.record(loss=self.last_loss,
                         raw_loss=(loss_holder or {}).get("raw"),
                         activations=(probe.snapshot() if probe is not None
                                      else None),
                         grads=grads,
                         preclip=(pc[0] if pc else None),
                         preclip_absmax=(pc[1] if pc else None),
                         arrivals=(pc[2] if pc else None),
                         grad_norm_hf=self.last_grad_norm,
                         weights=self._scan("weight"),
                         moments=self._scan("moment"))
            self.pending_grads = None
            self.pending_preclip = None
            return control

        def on_log(self, args, state, control, logs=None, **kw):
            if logs and "loss" in logs:
                self.last_loss = logs["loss"]
            # ⭐ HF's `grad_norm` IS THE PRE-CLIP TOTAL — `clip_grad_norm_`
            # returns the norm it measured BEFORE scaling, and the trainer logs
            # that. It should read inf/nan at the break step, which corroborates
            # the pre-clip hook from a source the hook has nothing to do with.
            # Carried WITH its own step because `on_log` runs after
            # `on_step_end`, so the alignment must be checked, not assumed.
            if logs and "grad_norm" in logs:
                self.last_grad_norm = {"hf_global_step": state.global_step,
                                       "value": logs["grad_norm"]}
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
        # ⛔⛔ RETURNS NOTHING OUTSIDE THE WINDOW, AND THAT IS A BUG FIX. This
        # used to return `dict(self.records)` unconditionally, so every step
        # after the window re-emitted the LAST ARMED STEP's numbers under the
        # current step's number. In the raw-loss trace, rows 15-19 are that:
        # five identical "measurements" of step 14, which read as a stable
        # post-break plateau and were not measurements at all. An instrument
        # that keeps answering after it stops looking reports its own memory as
        # data.
        return dict(self.records) if self.active else None

    def close(self):
        for h in self.handles:
            h.remove()


class PreClipGradProbe:
    """Per-parameter gradient magnitude AS EACH GRADIENT IS FINALISED.

    ⛔⛔ THE INSTRUMENT WAS DOWNSTREAM OF THE THING IT WAS WATCHING, FOR THE
    SECOND TIME. First `logging_nan_inf_filter` replaced a NaN loss with a
    running average, so the trace read the mask. Then `clip_grad_norm_` — which
    computes ONE norm across ALL parameters — turned one tensor's overflow into
    a non-finite coefficient applied to all 168 gradients, and the scan at
    `on_pre_optimizer_step` (trainer.py:1762) runs after that clip
    (trainer.py:1759). Both times the probe was reading a value the framework
    had already transformed, and both times the transformation destroyed exactly
    the signal being looked for.

    ⭐⭐ `register_post_accumulate_grad_hook` fires as each parameter's `.grad`
    is finalised inside the backward pass, BEFORE any clipping exists to
    homogenise it. So this names the originating tensor instead of the
    casualties, and its absmax across the approach says whether the overflow was
    COMPOUNDING (growing step over step) or TRIGGERED (flat, then a jump).

    ⛔ NO SYNCHRONISATION INSIDE THE BACKWARD. The hook writes a 0-dim device
    tensor into a preallocated buffer; 168 tensors times 4 micro-batches would
    otherwise be 672 device-to-host stalls per step. Everything is read once, at
    the optimizer step.
    """

    def __init__(self, model, *, window):
        import torch
        params = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
        if not params:
            raise ValueError("no trainable parameters to probe")
        p0 = params[0][1]
        if not hasattr(p0, "register_post_accumulate_grad_hook"):
            raise RuntimeError(
                "torch %s has no register_post_accumulate_grad_hook; the "
                "pre-clip reading is not available on this build and a "
                "post-clip scan CANNOT substitute for it" % torch.__version__)
        self.window = window
        self.active = False
        self.names = [n for n, _ in params]
        self._idx = {n: i for i, n in enumerate(self.names)}
        self._rank = {n: rank_of(p) for n, p in params}
        n = len(params)
        dev = p0.device
        self._absmax = torch.zeros(n, dtype=torch.float32, device=dev)
        self._sqnorm = torch.zeros(n, dtype=torch.float32, device=dev)
        self._bad = torch.zeros(n, dtype=torch.float32, device=dev)
        self._arrivals = []
        self._seen = set()
        self._micro = 0
        self.handles = [p.register_post_accumulate_grad_hook(self._make(nm))
                        for nm, p in params]

    def _make(self, name):
        import torch

        def hook(p):
            g = p.grad
            if g is None:
                return
            i = self._idx[name]
            f = g.detach().float()
            self._absmax[i] = f.abs().max()
            self._sqnorm[i] = (f * f).sum()
            self._bad[i] = (~torch.isfinite(f)).any().to(torch.float32)
            if self.active:
                # ⭐ A NAME ARRIVING TWICE MEANS A NEW MICRO-BATCH's backward
                # began — there is no callback for that boundary, and with
                # accumulation 4 the step contains four of them.
                if name in self._seen:
                    self._micro += 1
                    self._seen = set()
                self._seen.add(name)
                self._arrivals.append((self._micro, name))
        return hook

    def arm(self, step):
        self.active = step in self.window
        self._arrivals = []
        self._seen = set()
        self._micro = 0
        self._absmax.zero_()
        self._sqnorm.zero_()
        self._bad.zero_()

    def snapshot(self):
        """-> ({name: (rank, finite, l2norm)}, {name: absmax}|None, arrivals|None)

        ⛔ ONE host transfer for the whole step, here and nowhere else.
        """
        import torch
        stacked = torch.stack([self._absmax, self._sqnorm, self._bad]).cpu()
        am, sq, bad = (stacked[0].tolist(), stacked[1].tolist(),
                       stacked[2].tolist())
        out = {}
        for nm, i in self._idx.items():
            fin = bad[i] == 0.0
            out[nm] = (self._rank[nm], fin,
                       (sq[i] ** 0.5 if fin else None))
        dense = ({nm: am[i] for nm, i in self._idx.items()}
                 if self.active else None)
        return out, dense, (list(self._arrivals) if self.active else None)

    def close(self):
        for h in self.handles:
            h.remove()
