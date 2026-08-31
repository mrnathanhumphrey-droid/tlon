"""⛔⛔ RED-PROOF: CAN THE PAIRING STATISTIC FIRE AT ALL?

A tight CI around zero means one of two things — "no effect" or "the instrument
cannot move" — and they look identical in the output. This project has already
been burned by exactly that: `distinct-surface` was killed for build-variance
0.0000, an inert axis that reported a beautiful null.

So before `Δ pairing gain = +0.0024, CI [−0.0075, +0.0130]` may be read as a
tight null on conversation-specific convention, the statistic must be shown to
FIRE on a planted convention, at the real experiment's n and noise level, and to
stay silent on the things it is NOT supposed to detect.
"""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

from act2_drift import pairing_gain  # noqa: E402

#: The real experiment: 7 replicates per pair, per-speaker sd ~0.10 on force:ka.
N_REPS = 7
NOISE = 0.10


def _pair(rng, *, gap=0.2, convention=0.0, common=0.0, n=N_REPS, noise=NOISE):
    """Two speakers over n conversations.

    `convention` = sd of a per-conversation offset SHARED by both speakers —
    the thing the statistic exists to detect. `common` = a constant shift
    applied to both, which must NOT fire.
    """
    c = convention * rng.standard_normal(n)
    a = 0.0 + c + common + noise * rng.standard_normal(n)
    b = gap + c + common + noise * rng.standard_normal(n)
    return a, b


# ── ⛔⛔ THE ONE THAT MATTERS: IT MUST FIRE ─────────────────────────────────
def test_a_planted_convention_FIRES():
    rng = np.random.default_rng(1)
    gains = [pairing_gain(*_pair(rng, convention=0.15)) for _ in range(200)]
    assert np.mean(gains) > 0.05, "the statistic is INERT on a real convention"


def test_no_convention_gives_approximately_zero():
    rng = np.random.default_rng(2)
    gains = [pairing_gain(*_pair(rng, convention=0.0)) for _ in range(200)]
    assert abs(np.mean(gains)) < 0.02


def test_the_response_is_GRADED_in_the_convention_size():
    """Not just on/off — a bigger shared groove must give a bigger gain."""
    rng = np.random.default_rng(3)
    means = []
    for conv in (0.0, 0.05, 0.10, 0.20, 0.40):
        means.append(np.mean([pairing_gain(*_pair(rng, convention=conv))
                              for _ in range(200)]))
    assert all(x < y for x, y in zip(means, means[1:])), means


# ── specificity: it must stay silent on what it does NOT measure ───────────
def test_a_common_shift_does_NOT_fire():
    """⭐ Both speakers moving together is the CO-DRIFT channel, not this one.
    If a common shift fired here, a tight null would be uninterpretable."""
    rng = np.random.default_rng(4)
    gains = [pairing_gain(*_pair(rng, convention=0.0, common=0.30))
             for _ in range(200)]
    assert abs(np.mean(gains)) < 0.02


def test_it_is_insensitive_to_the_gap_between_the_speakers():
    """A pair that simply starts far apart must not read as convention."""
    rng = np.random.default_rng(5)
    near = np.mean([pairing_gain(*_pair(rng, gap=0.02)) for _ in range(200)])
    far = np.mean([pairing_gain(*_pair(rng, gap=0.60)) for _ in range(200)])
    assert abs(near - far) < 0.02, (near, far)


# ── guards on the guard ────────────────────────────────────────────────────
def test_too_few_conversations_returns_None_rather_than_a_number():
    assert pairing_gain([1.0, 2.0], [1.0, 2.0]) is None


def test_mismatched_lengths_refuse():
    assert pairing_gain([1.0, 2.0, 3.0], [1.0, 2.0]) is None


# ── ⭐⭐ POWER: what size of convention would this run have CAUGHT? ─────────
def test_the_run_could_have_detected_a_convention_of_a_stated_size():
    """Converts "tight null" into "tight null on effects at or above X".

    12 pairs, 7 replicates, noise 0.10 — the real design. Find the smallest
    planted convention whose 12-pair mean gain clears the observed CI half-width
    (0.0103). Pinned so a later change that quietly costs power fails here.
    """
    rng = np.random.default_rng(6)
    OBSERVED_CI_HALF_WIDTH = 0.0103
    detectable = None
    for conv in (0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20):
        runs = []
        for _ in range(300):
            runs.append(np.mean([pairing_gain(*_pair(rng, convention=conv))
                                 for _ in range(12)]))
        if np.percentile(runs, 5) > OBSERVED_CI_HALF_WIDTH:
            detectable = conv
            break
    assert detectable is not None, "no convention size was detectable — INERT"
    # A convention of this sd on force:ka, against a between-build sd of 0.2454.
    assert detectable <= 0.10, (
        "the run could only have detected a convention larger than 0.10 in ka "
        "units; the null is much weaker than reported (got %r)" % detectable)
