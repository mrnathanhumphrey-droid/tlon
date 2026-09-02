"""§4.2 — the CONFIRMATORY decomposition. AMENDMENT A `8f3024fb` §3.

⛔⛔ THIS TOOL CANNOT DISCRIMINATE COUPLING FROM REGRESSION, AND MUST NEVER BE
READ AS IF IT COULD. The algebra is in the amendment: if each speaker moves a
fraction `λ` toward the store value `S`, the gap becomes `(1−λ)|A−B|` — so
*independent* store-tracking closes the between-speaker gap by exactly `(1−λ)`,
with no coupling whatsoever. `force:ka` is a single axis, so there is no
direction orthogonal to the store on which to leave a residual. **Coupling and
common-attractor regression are observationally equivalent from endpoint
positions alone.**

⇒ The **matched SHARED-YOKED null** does the discriminating. This module reports
the quantities that let a reader *see* the co-movement, and names it when it
dominates. It confirms; it does not decide.

⭐ The observable is injectable so the planted cases here are EXACT. Testing this
through the real grammar would measure the parser, not the decomposition.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

from act2_decompose import CO_MOVEMENT, INCONCLUSIVE, decompose, quarters  # noqa: E402


def fake_ka(surfaces):
    """Synthetic observable: each 'surface' is its own numeric ka value."""
    vals = [float(s) for s in surfaces]
    return sum(vals) / len(vals) if vals else None


def log_of(a_vals, b_vals):
    """An alternating transcript with A and B emitting given ka values."""
    out = []
    for i in range(max(len(a_vals), len(b_vals))):
        for who, vals in (("A", a_vals), ("B", b_vals)):
            if i < len(vals):
                out.append({"turn": len(out), "speaker": who, "valid": True,
                            "injected": False, "surface": "%f" % vals[i]})
    return out


# ── quarters ────────────────────────────────────────────────────────────────

def test_quarters_are_contiguous_and_cover_everything():
    """⛔ A split that drops a remainder would quietly discard the END of the
    conversation — the half the whole measure is about."""
    qs = quarters(list(range(10)), 4)
    assert len(qs) == 4
    assert [x for q in qs for x in q] == list(range(10))
    assert all(qs)


def test_quarters_refuses_a_series_too_short_to_split():
    assert quarters([1, 2], 4) is None


# ── the recorded quantities ─────────────────────────────────────────────────

def test_it_records_BOTH_speakers_and_THE_STORE_per_quarter():
    """The store's own running value is the third series, and it is what makes
    the co-movement visible at all."""
    d = decompose(log_of([0.1] * 8, [0.9] * 8), ka=fake_ka)
    assert len(d["ka_a"]) == len(d["ka_b"]) == len(d["ka_store"]) == 4
    # the store holds BOTH speakers, so it sits between them
    assert 0.1 < d["ka_store"][-1] < 0.9


def test_the_store_series_is_CUMULATIVE_not_per_quarter():
    """⛔ Algorithm 1's `C` is append-only: the store at quarter q is everything
    said up to q, not just that quarter's turns."""
    d = decompose(log_of([0.0] * 8, [1.0] * 8), ka=fake_ka)
    assert d["store_is_cumulative"] is True
    assert len(d["ka_store"]) == 4


# ── the named outcome ───────────────────────────────────────────────────────

def test_PURE_CO_MOVEMENT_is_named_not_reported_as_convergence():
    """⛔⛔ THE CASE THE AMENDMENT EXISTS FOR. Both speakers march in the same
    direction by the same amount: the gap NEVER CLOSES, yet both have moved a
    long way. A measure that called this convergence would be reading motion as
    coupling."""
    a = [0.10, 0.10, 0.20, 0.20, 0.30, 0.30, 0.40, 0.40]
    b = [0.50, 0.50, 0.60, 0.60, 0.70, 0.70, 0.80, 0.80]
    d = decompose(log_of(a, b), ka=fake_ka)
    assert abs(d["gap_closure"]) < 1e-6, "the gap must not have closed"
    assert d["co_movement"] > 0.2
    assert d["reading"] == CO_MOVEMENT


def test_gap_closure_WITHOUT_co_movement_is_not_named_co_movement():
    """The mirror case: the two move TOWARD each other, so the mean shift is
    ~zero while the gap closes. Must not be flagged."""
    a = [0.10, 0.10, 0.20, 0.20, 0.30, 0.30, 0.40, 0.40]
    b = [0.90, 0.90, 0.80, 0.80, 0.70, 0.70, 0.60, 0.60]
    d = decompose(log_of(a, b), ka=fake_ka)
    assert d["gap_closure"] > 0.2, "the gap should have closed"
    assert abs(d["co_movement"]) < 1e-6
    assert d["reading"] != CO_MOVEMENT


def test_a_flat_conversation_is_INCONCLUSIVE_not_a_verdict():
    """⛔ Nothing moved. The tool must say so rather than emit a reading — a
    measure that always returns a verdict has no way to say 'no signal'."""
    d = decompose(log_of([0.4] * 8, [0.6] * 8), ka=fake_ka)
    assert d["reading"] == INCONCLUSIVE


def test_it_REFUSES_rather_than_guessing_on_a_transcript_too_short():
    d = decompose(log_of([0.4] * 2, [0.6] * 2), ka=fake_ka)
    assert d["reading"] == INCONCLUSIVE and d["ka_a"] is None


# ── the standing caveat is carried in the output, not only in prose ─────────

def test_the_output_CARRIES_its_own_non_discrimination_caveat():
    """⛔⛔ THE CAVEAT GOES IN THE ARTEFACT. A note in a docstring separates from
    the number the moment anyone copies the number. This field is what a later
    reader sees beside the result."""
    d = decompose(log_of([0.1] * 8, [0.9] * 8), ka=fake_ka)
    assert "cannot discriminate" in d["caveat"].lower()
    assert "matched" in d["caveat"].lower()


def test_injected_and_invalid_turns_never_enter_any_series():
    """Same exclusion the estimand uses — an injected surface is not the
    speaker's, and the store must not count it either."""
    log = log_of([0.1] * 8, [0.9] * 8)
    log.append({"turn": 99, "speaker": "A", "valid": True, "injected": True,
                "surface": "5.0"})
    log.append({"turn": 100, "speaker": "B", "valid": False, "injected": False,
                "surface": None})
    d = decompose(log, ka=fake_ka)
    assert max(d["ka_store"]) < 1.0, "an injected 5.0 leaked into the store"


def test_a_WIDENING_gap_is_not_labelled_closed():
    """⛔⛔ CAUGHT ON THIS TOOL'S FIRST REAL RUN: rows with gap_closure −0.7000
    were printed as "gap closed without a common shift". A label that
    contradicts its own number is worse than no label — the sign IS the meaning,
    so the name has to carry it."""
    from act2_decompose import DIVERGED
    a = [0.40, 0.40, 0.30, 0.30, 0.20, 0.20, 0.10, 0.10]
    b = [0.60, 0.60, 0.70, 0.70, 0.80, 0.80, 0.90, 0.90]
    d = decompose(log_of(a, b), ka=fake_ka)
    assert d["gap_closure"] < 0, "this fixture must WIDEN the gap"
    assert abs(d["co_movement"]) < 1e-6
    assert d["reading"] == DIVERGED
    assert "widen" in d["reading"].lower()
