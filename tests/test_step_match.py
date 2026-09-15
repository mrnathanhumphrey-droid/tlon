"""⛔⛔ THE HELD-FIXED VARIABLE IS MATCHED TO A PRE-DECLARED BOUND, OR THE RUN REFUSES.

The epochs-lever arm varies ONE thing — repetition — and holds LR, dose and
optimizer steps fixed. Arm A's total can only land on multiples of `repeat`, so
exact equality with arm B is not available on demand; the row count is whatever
the generator emits against the pinned sha. Demanding exactness would make the
run un-fireable on an unlucky count; accepting any mismatch would let a
step-count difference masquerade as a repetition effect.

⭐ So the criterion is BOUNDED AND DECLARED — `STEP_MATCH_TOL`, registered in the
prereg before the corpus rebuilds. The tests below fix BOTH directions, because a
tolerance guard that only ever proceeds is not a guard:

  1. inside the bound  -> proceed, and RECORD BOTH EXACT COUNTS
  2. outside the bound -> REFUSE
  3. the tolerance itself cannot be quietly widened

⛔ And the numbers the derivation produces are PREDICTIONS. `check_match` is
written to be run again on the trainer's real `state.max_steps`, because
re-deriving a total the system already knows is what put `3,759` in a prereg for
a run whose trainer reported `3,760`.
"""
import pathlib
import re
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

from tlon.act2 import step_match as SM                        # noqa: E402

B, A, R = 4, 4, 4          # the gate's shape: batch 4, accum 4, repeat 4


# ── 1 · the trainer's arithmetic, mirrored ─────────────────────────────────

def test_hf_max_steps_is_the_CEIL_formula_not_the_curves_floor():
    """⛔⛔ THE OFF-BY-ONE THAT REACHED A PREREG. The dose curve computes
    `len(dataloader) // accum * epochs` (floor); the trainer computes
    `ceil(len(dataloader) / accum) * epochs`. On a loader length that is not a
    multiple of `accum` they differ by one — 3,759 vs 3,760 on the pinned
    corpus. This mirrors the TRAINER."""
    rows = 60150                      # -> 15038 batches, not a multiple of 4
    batches = -(-rows // B)
    assert batches % A != 0, "fixture no longer exercises the remainder case"
    assert batches // A == 3759                       # the curve's floor
    assert SM.hf_max_steps(rows, batch=B, accum=A, epochs=1) == 3760


def test_a_tiny_corpus_still_takes_at_least_one_step():
    assert SM.hf_max_steps(1, batch=B, accum=A, epochs=1) == 1


@pytest.mark.parametrize("bad", [0, -1])
def test_nonpositive_inputs_are_refused_not_silently_clamped(bad):
    with pytest.raises(ValueError):
        SM.hf_max_steps(bad, batch=B, accum=A, epochs=1)
    with pytest.raises(ValueError):
        SM.hf_max_steps(100, batch=B, accum=bad, epochs=1)


# ── 2 · ⛔ BOTH DIRECTIONS OF THE BOUND ────────────────────────────────────

def test_inside_the_bound_it_PROCEEDS_and_records_both_exact_counts():
    """⭐ At the real corpus scale the match is EXACT, but the guard must report
    the numbers either way — `ok: True` alone hides the match QUALITY."""
    r = SM.derive_subsample(60150, batch=B, accum=A, repeat=R)
    assert r["ok"] is True
    assert r["s_b"] == 3760 and r["s_a"] == 3760
    assert r["delta_steps"] == 0
    assert r["m"] == 15040
    # ⛔ the exact counts must be IN the result, not summarised as "matched"
    for field in ("s_a", "s_b", "delta_steps", "delta_frac", "tol", "m",
                  "per_epoch", "repeat"):
        assert field in r, "the manifest cannot show match quality without %r" % field


def test_outside_the_bound_it_REFUSES():
    """⛔⛔ THE DIRECTION A PERMISSIVE GUARD NEVER EXERCISES. Δsteps is
    structurally ≤ `repeat`//2 rounded — so the bound binds only on a SMALL
    corpus, where two steps are a large fraction. That case must refuse."""
    r = SM.derive_subsample(4000, batch=B, accum=A, repeat=R)
    assert r["s_b"] == 250
    assert r["delta_steps"] == 2
    assert r["delta_frac"] == pytest.approx(0.008)
    assert r["ok"] is False
    assert "REFUSING" in r["why"]
    # the refusal must name the numbers, not just say no
    assert "250" in r["why"] and "tolerance" in r["why"]


def test_the_refusal_is_raisable_for_callers_that_must_not_continue():
    ok = SM.derive_subsample(60150, batch=B, accum=A, repeat=R)
    assert SM.require_match(ok) is ok
    with pytest.raises(SM.StepMatchRefused):
        SM.require_match(SM.derive_subsample(4000, batch=B, accum=A, repeat=R))


def test_the_boundary_is_where_the_declared_tolerance_says_it_is():
    """⭐ SWEPT, not asserted at one point. Δsteps ≤ 2 always, so the run
    refuses exactly when 2/S_B exceeds the tolerance — i.e. below S_B ≈ 1000."""
    seen = {}
    for n in range(600, 90000, 137):
        r = SM.derive_subsample(n, batch=B, accum=A, repeat=R)
        assert r["delta_steps"] <= 2, (
            "Δsteps %d at N=%d — arm A should only land on multiples of repeat"
            % (r["delta_steps"], n))
        if r["m"] is not None:
            assert r["ok"] == (r["delta_frac"] <= SM.STEP_MATCH_TOL)
        seen[r["ok"]] = seen.get(r["ok"], 0) + 1
    # ⛔ a sweep that only ever saw one answer would prove nothing
    assert seen.get(True, 0) > 0 and seen.get(False, 0) > 0, seen


def test_the_real_corpus_scale_is_comfortably_inside():
    """⭐ Recorded for the reader: on this corpus the bound is INSURANCE, not a
    constraint that was needed. miscurve's loader gave S_B = 3760."""
    r = SM.derive_subsample(60150, batch=B, accum=A, repeat=R)
    assert r["delta_frac"] <= SM.STEP_MATCH_TOL / 10


# ── 3 · ⛔ the tolerance cannot be quietly widened ─────────────────────────

def test_the_declared_tolerance_is_the_registered_number():
    """⛔⛔ A tolerance edited after a mismatch is seen is the `resolution_match`
    trap — "matched" would quietly mean "as matched as it came out". This value
    is registered in PREREG_EPOCHS_LEVER §2.1 BEFORE the corpus rebuilds."""
    assert SM.STEP_MATCH_TOL == 0.002


def test_the_prereg_declares_the_same_tolerance_the_code_enforces():
    """⛔⛔ A BOUND DECLARED IN PROSE AND ENFORCED AT A DIFFERENT VALUE IS NOT
    PRE-REGISTERED. Both must move together or neither moves."""
    p = _ROOT / "docs" / "PREREG_EPOCHS_LEVER_2026_09_14.md"
    assert p.exists(), "the prereg this tolerance is registered in is missing"
    src = p.read_text(encoding="utf-8")
    # ⛔⛔ THE BINDING, NOT TWO INDEPENDENT TOKENS. Asserting `"STEP_MATCH_TOL" in
    # src` and `"0.002" in src` separately passes a document that names the
    # constant in one place and the number in another, unrelated one — the
    # `guard_searches` failure, which already let a neutered `resolving_power`
    # through in this repo once. Require NAME = VALUE, adjacently.
    binding = re.search(r"STEP_MATCH_TOL[`\s]*=[`\s]*([0-9.]+)", src)
    assert binding, (
        "the prereg never binds STEP_MATCH_TOL to a value; a bound named but "
        "not stated is not pre-registered")
    assert float(binding.group(1)) == SM.STEP_MATCH_TOL, (
        "the prereg declares STEP_MATCH_TOL = %s but the code enforces %r — a "
        "bound declared in prose and enforced at a different value is not a "
        "pre-registration" % (binding.group(1), SM.STEP_MATCH_TOL))


def test_check_match_is_reusable_on_the_trainers_REAL_numbers():
    """⭐⭐ THE POINT OF SPLITTING IT OUT. The derivation predicts; the trainer
    records. `check_match` must take whatever pair it is handed so the same
    criterion runs again on `state.max_steps` per arm."""
    assert SM.check_match(3760, 3760)["ok"] is True
    assert SM.check_match(3752, 3760)["ok"] is False      # 0.21 % — over
    assert SM.check_match(3754, 3760)["ok"] is True       # 0.16 % — under
    r = SM.check_match(3754, 3760)
    assert r["delta_steps"] == 6 and r["s_a"] == 3754 and r["s_b"] == 3760


def test_a_subsample_larger_than_the_corpus_refuses_rather_than_clamping():
    """⛔ A silent clamp would change the REPEAT FACTOR — the one variable the
    design varies — while still reporting success."""
    r = SM.derive_subsample(20, batch=B, accum=A, repeat=1)
    if r["m"] is not None and r["m"] > r["n_rows"]:
        pytest.fail("m exceeds the corpus and was not refused")
    if not r["ok"]:
        assert r["why"]
