"""⭐ MATCHING THE HELD-FIXED VARIABLE: steps, to a PRE-DECLARED tolerance.

The epochs-lever arm varies ONE thing — repetition — and holds LR, dose and
optimizer steps fixed:

    arm B (control)   full corpus,      1 epoch
    arm A (repeat)    a 1/repeat slice, `repeat` epochs

⛔⛔ EXACT STEP EQUALITY IS NOT ACHIEVABLE ON DEMAND, AND DEMANDING IT MAKES THE
RUN UN-FIREABLE ON AN UNLUCKY ROW COUNT. Arm A's total is `repeat x` a
steps-per-epoch integer, so it can only land on multiples of `repeat`; if arm B's
own total is not such a multiple, no subsample reaches it exactly. The row count
is whatever the corpus generator emits against the pinned sha -- not a dial.

⭐ So the criterion is BOUNDED AND DECLARED, never "close enough" decided after
the number is seen. `STEP_MATCH_TOL` below is registered in the prereg BEFORE the
corpus rebuilds, with its reasoning: the effect under test is miscurve's epoch-2
movement of **lag2 by 1.34**, and a fraction of a percent of dose moves release
by far less than that. The mismatch is orders below the resolution the comparison
needs. ⛔ Over the bound the run REFUSES -- an awkward row count must block a
confounded run, not be waved through.

⛔⛔ AND THE NUMBERS HERE ARE PREDICTIONS, NOT THE RECORD. `hf_max_steps` mirrors
the trainer's own arithmetic so a subsample can be chosen BEFORE any GPU time is
bought, but the authoritative totals are the trainer's `state.max_steps` on each
arm. Re-deriving a total the system already knows is how `3,759` (the curve's
floor-based `_total`) got mistaken for `3,760` (the trainer's ceil) once already.
`check_match` exists to be run AGAIN on the real numbers.
"""
from __future__ import annotations

#: ⭐ PRE-DECLARED, and registered in PREREG_EPOCHS_LEVER §2.1 before the corpus
#: rebuilds. 0.2 % of arm B's step count. NOT a knob to widen once a mismatch is
#: seen: a tolerance chosen after the measurement is the `resolution_match` trap,
#: where "matched" quietly means "as matched as it happened to come out".
STEP_MATCH_TOL = 0.002


class StepMatchRefused(Exception):
    """⛔ The arms cannot be matched inside the declared bound on this corpus."""


def hf_max_steps(rows: int, *, batch: int, accum: int, epochs: int) -> int:
    """The trainer's own step arithmetic, mirrored — a PREDICTION, not a record.

    ⛔ Two different formulas are live in this repo and they differ by one:
    the dose curve computes `len(dataloader) // accum * epochs` (floor), while
    the trainer computes `ceil(len(dataloader) / accum) * epochs`. On a corpus
    whose loader length is not a multiple of `accum` those disagree, which is
    exactly how a prereg came to state 3,759 for a run whose `state.max_steps`
    was 3,760. This mirrors the TRAINER.
    """
    if rows <= 0:
        raise ValueError("rows must be positive, got %r" % (rows,))
    if batch <= 0 or accum <= 0 or epochs <= 0:
        raise ValueError("batch, accum and epochs must all be positive")
    # len(dataloader) with drop_last=False
    batches = -(-rows // batch)
    per_epoch = max(-(-batches // accum), 1)
    return per_epoch * epochs


def check_match(s_a: int, s_b: int, *, tol: float = STEP_MATCH_TOL) -> dict:
    """⭐ THE CRITERION, ON WHATEVER NUMBERS YOU HAND IT — predicted or real.

    Run once on the prediction to refuse before buying GPU time, and AGAIN on the
    trainer's actual `state.max_steps` for each arm, because the prediction is
    not the record.

    -> {s_a, s_b, delta_steps, delta_frac, tol, ok}
    """
    if s_b <= 0:
        raise ValueError("arm B step count must be positive, got %r" % (s_b,))
    delta = abs(int(s_a) - int(s_b))
    frac = delta / s_b
    return {"s_a": int(s_a), "s_b": int(s_b), "delta_steps": delta,
            "delta_frac": frac, "tol": tol, "ok": frac <= tol}


def derive_subsample(n_rows: int, *, batch: int, accum: int, repeat: int,
                     tol: float = STEP_MATCH_TOL) -> dict:
    """Choose arm A's row count M so its total steps land nearest arm B's.

    ⭐ M IS DERIVED FROM THE CORPUS THAT WAS ACTUALLY SHA-VERIFIED, never
    hardcoded. A row count copied from a file on a developer's disk is a number
    about a DIFFERENT corpus: the pinned corpus is rebuilt on the box and no copy
    of it need exist locally at all.

    Arm A's per-epoch step count `p` gives `S_A = p * repeat`, and every M in
    `(batch*accum*(p-1), batch*accum*p]` yields that same `p`. The LARGEST such M
    is taken -- it wastes the fewest rows, and it lands naturally at ~n_rows/repeat
    because `S_B ~= n_rows/(batch*accum)`.

    -> a manifest-shaped dict; `ok` False means REFUSE.
    """
    if repeat < 1:
        raise ValueError("repeat must be >= 1, got %r" % (repeat,))
    s_b = hf_max_steps(n_rows, batch=batch, accum=accum, epochs=1)

    # the per-epoch count for arm A whose `repeat` epochs land nearest S_B
    per_epoch = max(int(round(s_b / repeat)), 1)
    span = batch * accum
    m = span * per_epoch                       # largest M giving this per_epoch

    why = ""
    if m > n_rows:
        # ⛔ Cannot subsample more rows than exist. Only reachable at repeat=1 or
        # a degenerate corpus, but a silent clamp here would quietly change the
        # repeat factor -- the one variable the design varies.
        why = ("the derived subsample needs %d rows but the corpus has %d; "
               "arm A cannot be built without changing the repeat factor"
               % (m, n_rows))
        return {"m": None, "per_epoch": per_epoch, "n_rows": n_rows,
                "repeat": repeat, "batch": batch, "accum": accum,
                "s_a": None, "s_b": s_b, "delta_steps": None,
                "delta_frac": None, "tol": tol, "ok": False, "why": why}

    s_a = hf_max_steps(m, batch=batch, accum=accum, epochs=repeat)
    res = check_match(s_a, s_b, tol=tol)
    if not res["ok"]:
        why = ("arm A reaches %d steps against arm B's %d -- a mismatch of %d "
               "steps (%.4f%%) above the pre-declared tolerance of %.4f%%. The "
               "arms are not matched well enough to attribute a difference to "
               "repetition rather than to a step-count difference. REFUSING."
               % (s_a, s_b, res["delta_steps"], 100 * res["delta_frac"],
                  100 * tol))
    return {"m": m, "per_epoch": per_epoch, "n_rows": n_rows, "repeat": repeat,
            "batch": batch, "accum": accum, "s_a": s_a, "s_b": s_b,
            "delta_steps": res["delta_steps"], "delta_frac": res["delta_frac"],
            "tol": tol, "ok": res["ok"], "why": why}


def require_match(result: dict) -> dict:
    """⛔ The refusal, as an exception, for callers that must not continue."""
    if not result.get("ok"):
        raise StepMatchRefused(result.get("why") or "step match refused")
    return result
