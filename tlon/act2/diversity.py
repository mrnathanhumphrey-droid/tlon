"""THE TWO-SIDED DIVERSITY GUARD. A validity rate alone cannot see a degenerate
speaker, and the degenerate speakers sit at BOTH ends of the scale.

⛔⛔ WHY THIS EXISTS. F-LOCAL scored `speak 100 % (64/64)` on **one output
repeated sixty-four times**. Two separate defects produced that number:

  1. `_rate(speaker, [None] * 64, "speak")` issues a BYTE-IDENTICAL prompt every
     call, and `LocalBackend` decodes at temperature 0 -- greedy. A deterministic
     function of a constant input returns a constant. **The effective sample size
     was 1, reported as 64.**
  2. The metric had no distinctness term, so a constant scores the maximum.

⭐ MEASURED, ON THE PULLED ADAPTER, AT $0: same prompt greedy = **1/12 distinct**;
same prompt at temperature 0.8 = **11/12**; twelve DIFFERENT inputs greedy =
**12/12**. The weights were never collapsed -- greedy was taking the mode of a
diverse distribution. That is why this module measures a NUMBER: a binary
pass/fail cannot tell those three situations apart.

⛔⛔ AND IT MUST BE TWO-SIDED. Raw diversity is not the target:

    a CONSTANT speaker      -> 1 distinct        degenerate (collapse)
    a UNIFORM-RANDOM speaker-> N distinct        degenerate (noise)
    a NATIVE speaker        -> diverse AND INPUT-DEPENDENT

A model emitting uniformly random legal scenes maxes any naive distinctness check
while being no more native than the broken record. **The signal is not entropy,
it is INPUT-DEPENDENCE**: different meanings must give different scenes, and the
same meaning must give the same scene. Both halves are required, and the second
is the half a raw-entropy metric silently discards.
"""
from __future__ import annotations

import json
from dataclasses import dataclass


class DegenerateSpeaker(RuntimeError):
    """The sample cannot be scored: it is constant, or it is noise."""


def _key(proposal) -> str:
    return json.dumps(proposal, sort_keys=True, ensure_ascii=False) if proposal \
        else "<none>"


@dataclass(frozen=True)
class Diversity:
    """A measurement, not a verdict. ⭐ Every field is a number so the guard can
    be driven, compared across checkpoints, and plotted against training step."""
    n: int
    distinct: int
    repeat_rate: float          # same input -> same output (determinism)
    response_rate: float        # different inputs -> different outputs
    dependence: float           # response_rate - (1 - repeat_rate)
    verdict: str

    @property
    def ratio(self) -> float:
        return self.distinct / self.n if self.n else 0.0


def measure(*, repeated: list, varied: list) -> Diversity:
    """Score a speaker from two samples of EQUAL size.

    `repeated` -- N outputs for the SAME input. A native speaker is largely
        consistent here: the same meaning should give the same scene.
    `varied`   -- N outputs for N DIFFERENT inputs. A native speaker is diverse
        here: different meanings should give different scenes.

    ⛔ Both samples must be drawn the same way. Comparing a greedy `repeated`
    against a sampled `varied` measures the decoder, not the speaker -- which is
    precisely the confound that produced the original 64/64.
    """
    if len(repeated) != len(varied):
        raise ValueError(
            f"samples must be the same size ({len(repeated)} vs {len(varied)}); "
            "an unequal comparison measures the sample sizes, not the speaker")
    n = len(repeated)
    if n < 4:
        raise ValueError(f"n={n} is too small to distinguish collapse from noise")

    rep_distinct = len({_key(p) for p in repeated})
    var_distinct = len({_key(p) for p in varied})
    repeat_rate = 1.0 - (rep_distinct - 1) / max(1, n - 1)
    response_rate = (var_distinct - 1) / max(1, n - 1)
    dependence = response_rate - (1.0 - repeat_rate)

    # ⛔ THE COLLAPSE END — this run's `san` x12. Refused, not warned.
    if var_distinct <= 1:
        raise DegenerateSpeaker(
            f"COLLAPSE: {var_distinct} distinct output for {n} DIFFERENT inputs. "
            "A constant is not a speaker, and a validity rate would score it "
            "1.00. ⛔ Check the decoder before the weights: greedy decoding on a "
            "constant prompt is constant BY CONSTRUCTION.")
    # ⛔ THE NOISE END — uniform-random legal scenes. Also refused.
    if repeat_rate < 0.5 and response_rate > 0.9:
        raise DegenerateSpeaker(
            f"NOISE: the same input gives {rep_distinct}/{n} different outputs "
            f"(repeat_rate {repeat_rate:.2f}) while different inputs give "
            f"{var_distinct}/{n}. Output varies as much WITHOUT a change of "
            "meaning as WITH one, so it is not tracking meaning at all. "
            "Diversity is necessary and nowhere near sufficient.")

    verdict = ("input-dependent" if dependence >= 0.5 else
               "weakly input-dependent" if dependence >= 0.2 else
               "⛔ output barely tracks input")
    return Diversity(n=n, distinct=var_distinct, repeat_rate=repeat_rate,
                     response_rate=response_rate, dependence=dependence,
                     verdict=verdict)
