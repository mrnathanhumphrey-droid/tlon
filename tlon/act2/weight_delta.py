"""DID THE OPTIMIZER ACTUALLY WRITE? — the §4.1 precondition, measured.

⛔⛔ A SILENT NO-OP AND A SILENT SUCCESS ARE THE SAME OBSERVATION. A fine-tune
whose optimizer cannot write its update produces weights that did not move, and
"the weights did not move" is *observationally identical* to the finding this
run exists to test — (b), the persistence survived. Reading a no-op as (b) would
declare a substrate wall the run never pushed on. PREREG
`PREREG_FULL_FINETUNE_RELEASE_2026_09_05` (LOCK `a0450b36`) §4.1 makes the
answer a precondition on the WHOLE verdict table: near-zero movement is
INSTRUMENT FAULT, and no row of that table may be read.

⭐⭐ THE TRIGGER IS THE MEANING, NOT A THRESHOLD. The tempting implementation is
`fault if fraction_changed < 0.05` — a number somebody picks, which then needs
re-checking every time the config moves. Instead this compares the observation
against TWO PREDICTIONS THE CONFIG ITSELF MAKES, both computed at runtime from
the actual initial weights:

  * **working** — an fp32 master absorbs every Adam step, so essentially every
    trainable parameter changes: predicted fraction ~ 1.0.
  * **dead zone** — a bf16 master can only absorb a step into weights small
    enough that `lr >= 0.5 * ulp(theta)`, i.e. `|theta| <= lr * 2**8`. The
    predicted fraction is then just the share of initial weights under that
    ceiling, which this module MEASURES off the init sample rather than assuming
    a distribution.

The verdict is whichever prediction the observation sits closer to, on a log
scale. There is no tunable constant in that comparison.

⛔ AND IT REFUSES TO DISCRIMINATE WHEN IT CANNOT. If the weights are small
enough that the dead-zone prediction is itself near 1.0, the two hypotheses make
the same prediction and no observation separates them. That returns
`UNDISCRIMINATING`, never `OK` — a test that cannot fail has not been passed.

⭐ SAMPLED, AND THE SAMPLING IS THE POINT. Holding a full fp32 copy of 3.263 B
trainable parameters costs ~13 GiB of the very budget the run is tight on. A
fixed deterministic subsample per tensor answers both questions — a fraction and
a norm — at a few hundred KiB, and the norm is a proper scaled estimator rather
than a partial sum quietly reported as a total.
"""
from __future__ import annotations

import math

#: ⭐ The bf16 significand carries 8 bits, so `ulp(theta) ~ theta * 2**-8` and a
#: step is absorbed when it reaches half an ulp. Named, because this exact
#: constant is the arithmetic in the locked §4.1 and re-deriving it by hand at a
#: call site is how the two drift apart.
BF16_ULP_RATIO = 2.0 ** -8

#: Per-tensor sample size. Large enough that a true fraction of 1e-3 is seen
#: with probability > 98 %, small enough to be free.
SAMPLE_K = 4096

OK = "OK"
INSTRUMENT_FAULT = "INSTRUMENT_FAULT"
UNDISCRIMINATING = "UNDISCRIMINATING"
#: ⛔⛔ THE VERDICT THIS MODULE DID NOT HAVE, AND THE RUN THAT PROVED IT NEEDED IT.
#: `fw-s20624` (2026-09-06) finished one epoch with **NaN in all 70 of its 1-D
#: trainable tensors** — every bias and every layernorm in the trained layers —
#: and this module returned `OK` with `fraction_changed = 0.9999982`.
#:
#: The hole is one line of IEEE semantics: **`NaN != NaN` is True**, so a
#: destroyed value counts as "the stored value changed". A guard written to tell
#: *the weights did not move* from *the weights moved* could not tell either
#: from *the weights became NaN* — the same vacuous pass it exists to prevent,
#: inside the thing preventing it.
#:
#: ⭐ And the evidence was already in the artifact: `delta_norm_estimated` came
#: out `NaN`, was written to `weight_delta.json`, printed, and never read by the
#: verdict. A summary field not checked against its own run.
DIVERGED = "DIVERGED"


class WeightDeltaError(RuntimeError):
    """⛔ Raised, never warned. A delta that cannot be computed is not a delta
    of zero, and the difference decides whether a verdict may be read."""


def absorbable_ceiling(lr: float) -> float:
    """The |theta| below which a step of size `lr` is certain to register under
    a bf16 master. Above it the update rounds away and the weight sits frozen
    while appearing to train.

    ⭐ `lr * 2**8`, which is the arithmetic in the locked §4.1: 2.56e-3 at
    lr 1e-5, halving to 1.28e-3 at the 5e-6 dial-back. ⚠️ It is a bound, not a
    boundary — bf16's relative ulp runs in (2**-8, 2**-7] depending on where a
    weight sits in its binade, so a little above this some weights still absorb
    and most do not. Taking the generous end keeps the dead-zone PREDICTION
    conservative, which is the direction that makes the fault verdict harder to
    reach rather than easier.
    """
    if lr <= 0:
        raise WeightDeltaError("lr must be positive, got %r" % (lr,))
    return lr / BF16_ULP_RATIO


def snapshot(named_params, *, k: int = SAMPLE_K, seed: int = 20624) -> dict:
    """Record enough of the INITIAL weights to answer §4.1 later.

    ⛔⛔ MUST BE TAKEN INSIDE THE TRAINING PROCESS, BEFORE THE FIRST STEP. A
    snapshot bolted on afterwards has nothing to compare against, and a
    re-loaded "initial" checkpoint is a different tensor layout on a different
    device — the comparison would measure the reload, not the training.

    Only parameters with `requires_grad` are recorded: a frozen tensor that did
    not move is the configuration working as declared, and mixing those into the
    fraction would dilute exactly the signal this exists to detect.
    """
    import torch

    g = torch.Generator(device="cpu").manual_seed(seed)
    out: dict = {}
    for name, p in named_params:
        if not p.requires_grad:
            continue
        n = p.numel()
        if n == 0:
            continue
        take = min(k, n)
        idx = torch.randperm(n, generator=g)[:take]
        flat = p.detach().reshape(-1).to("cpu", torch.float32)
        out[name] = {
            "n": int(n),
            "idx": idx,
            "init": flat[idx].clone(),
            # ⭐ The full-tensor norm is exact and costs nothing; only the DELTA
            # norm has to be estimated, and reporting both keeps the estimate
            # honest about what it is.
            "norm_init_exact": float(torch.linalg.vector_norm(flat).item()),
        }
    if not out:
        raise WeightDeltaError(
            "no trainable parameters found — a fine-tune with nothing to train "
            "would report a perfect zero delta and pass for a substrate floor.")
    return out


def measure(named_params, snap: dict, *, lr: float) -> dict:
    """Compare the CURRENT weights against the snapshot. Returns the §4.1 record.

    ⛔ Every trainable tensor in the snapshot must still be present and the same
    size. A silently skipped tensor lowers the denominator, which moves the
    fraction toward whichever answer the missing tensors would have contradicted.
    """
    import torch

    current = {n: p for n, p in named_params if p.requires_grad}
    missing = [n for n in snap if n not in current]
    if missing:
        raise WeightDeltaError(
            "%d snapshotted tensor(s) absent at measure time (first: %s). The "
            "delta cannot be computed over a different parameter set."
            % (len(missing), missing[0]))

    ceiling = absorbable_ceiling(lr)
    per_module = {}
    n_sampled = n_changed = 0
    n_under_ceiling = n_nonfinite_total = 0
    sq_total = 0.0
    n_params_total = 0

    for name, rec in snap.items():
        p = current[name]
        if p.numel() != rec["n"]:
            raise WeightDeltaError(
                "%s changed size (%d -> %d); the snapshot does not describe "
                "this tensor." % (name, rec["n"], p.numel()))
        flat = p.detach().reshape(-1).to("cpu", torch.float32)
        now = flat[rec["idx"]]
        init = rec["init"]
        diff = now - init
        take = int(now.numel())
        # ⛔⛔ NON-FINITE IS COUNTED SEPARATELY AND NEVER AS "CHANGED". Without
        # this, `NaN != init` is True and a destroyed tensor reports perfect
        # movement. Excluding non-finite values from `changed` means the fraction
        # describes weights that actually moved TO A NUMBER.
        finite = torch.isfinite(now)
        n_nonfinite = int((~finite).sum().item())
        changed = int(((now != init) & finite).sum().item())
        # ⭐ SCALED ESTIMATOR, NOT A PARTIAL SUM. sum(diff^2) over a sample of
        # `take` from `n` estimates the full sum as n/take * sum. Reporting the
        # raw partial sum as "the norm" would understate it by sqrt(n/take) --
        # here about 240x -- which is the direction that fakes a fault.
        # ⭐ The norm is computed over the FINITE values only, so it stays a
        # readable number even on a diverged tensor -- a NaN norm would just be
        # a second unreadable field rather than a diagnosis.
        sq_sample = float((diff.double()[finite] ** 2).sum().item())
        sq_est = sq_sample * (rec["n"] / take)
        under = int((init.abs() <= ceiling).sum().item())

        per_module[name] = {
            "n": rec["n"],
            "sampled": take,
            "changed": changed,
            "fraction_changed": changed / take,
            "delta_norm_estimated": math.sqrt(sq_est),
            "norm_init_exact": rec["norm_init_exact"],
            "relative_delta_estimated": (
                math.sqrt(sq_est) / rec["norm_init_exact"]
                if rec["norm_init_exact"] > 0 else None),
            "fraction_under_bf16_ceiling": under / take,
            # ⛔ RECORDED PER MODULE, so a diverged run says WHICH tensors went
            # and the shape of the failure is legible. On `fw-s20624` this would
            # have read 1.0 for every bias and layernorm and 0.0 for every weight
            # matrix -- a systematic 1-D pathology, visible at a glance.
            "fraction_nonfinite": n_nonfinite / take,
        }
        n_sampled += take
        n_changed += changed
        n_nonfinite_total += n_nonfinite
        n_under_ceiling += under
        sq_total += sq_est
        n_params_total += rec["n"]

    observed = n_changed / n_sampled
    dead_zone = n_under_ceiling / n_sampled
    nonfinite = n_nonfinite_total / n_sampled
    verdict, why = _verdict(observed, dead_zone, nonfinite)

    return {
        "PRECONDITION": "PREREG a0450b36 §4.1",
        "lr": lr,
        "bf16_absorbable_ceiling": ceiling,
        "n_trainable_params": n_params_total,
        "n_sampled": n_sampled,
        "fraction_changed": observed,
        "fraction_nonfinite": nonfinite,
        "prediction_working_fp32_master": 1.0,
        "prediction_bf16_dead_zone": dead_zone,
        "delta_norm_estimated": math.sqrt(sq_total),
        "verdict": verdict,
        "why": why,
        "per_module": per_module,
    }


def _verdict(observed: float, dead_zone: float,
             nonfinite: float = 0.0) -> tuple:
    """Which of the two predictions the observation sits closer to, in log
    distance. ⛔ No free constant: both predictions are computed, not chosen."""
    # ⛔⛔ DIVERGENCE IS CHECKED BEFORE EITHER PREDICTION, because a diverged
    # run is not a point on the axis those predictions describe. Any non-finite
    # trainable weight means the training produced a model that cannot be read
    # for anything -- and it must never reach the `observed` comparison, where a
    # tensor full of NaN would have looked like perfect movement.
    if nonfinite > 0:
        return (DIVERGED,
                "%.4f of sampled trainable weights are NOT FINITE. The training "
                "produced NaN/Inf, so the model cannot be read for release, "
                "perceive or fluency, and this is a TRAINING FAULT -- never a "
                "substrate finding. ⛔ `NaN != NaN` is True, so without this "
                "branch every destroyed value would have counted as movement "
                "and the verdict would have been OK." % nonfinite)
    # ⛔⛔ THE UNDISCRIMINATING BRANCH COMES FIRST. If the dead-zone prediction
    # is itself close to 1.0 -- weights small enough that even bf16 would absorb
    # most steps -- then a working run and a dead one predict the SAME
    # observation, and returning OK there would be a test that cannot fail.
    if dead_zone >= 0.5:
        return (UNDISCRIMINATING,
                "the bf16 dead-zone prediction is %.3f, close enough to the "
                "working prediction of 1.0 that no observed fraction separates "
                "them. This run cannot answer §4.1 by fraction alone; read the "
                "delta norms per module before any verdict." % dead_zone)
    if observed <= 0.0:
        return (INSTRUMENT_FAULT,
                "not one sampled trainable parameter changed. The optimizer "
                "wrote nothing; no row of the verdict table may be read.")
    eps = 1e-12
    d_working = abs(math.log(max(observed, eps)) - math.log(1.0))
    d_dead = abs(math.log(max(observed, eps)) - math.log(max(dead_zone, eps)))
    if d_dead < d_working:
        return (INSTRUMENT_FAULT,
                "fraction changed %.4f sits closer to the bf16 dead-zone "
                "prediction %.4f than to the working prediction 1.0. The "
                "weights that did not move are the ones too large to absorb a "
                "step -- the optimizer under-wrote, and a floor read off this "
                "run would be an artefact of the optimizer, not the substrate."
                % (observed, dead_zone))
    return (OK,
            "fraction changed %.4f sits closer to the working prediction 1.0 "
            "than to the bf16 dead-zone prediction %.4f; the optimizer wrote "
            "the update." % (observed, dead_zone))
