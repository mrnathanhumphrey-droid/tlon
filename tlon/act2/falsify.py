"""THE FALSIFIERS AND THE DECISION RULES — PREREG §2, §5, §6.

⛔⛔ EVERY THRESHOLD HERE WAS FIXED BEFORE ANY RUN AND IS READ FROM THE PREREG,
NOT CHOSEN HERE. This module computes; it does not decide what counts.

The one that matters most is not F2 but §5.2. A cell whose available headroom is
below the MDE **cannot show an effect**, so its firing says nothing about the
claim -- it is UNINFORMATIVE, NOT A NULL -- and it may not contribute to a
boundary result. That distinction is the project's hardest-won rule and it is
what stops a tired instrument being reported as a finding about the world.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass

from ..harness.paired import Delta, Measurement, paired_delta

PREREG = "20620b7c"
VALID_EMISSION_THRESHOLD = 0.90      # F1  (§2)
ROOT_DIVERSITY_DECLINE = 0.25        # F4  (§2)
LEAKAGE_VOID = 0.20                  # F5  (§2)
ALPHA = 0.05                         # §5.5
PERMUTATION_QUANTILE = 0.95          # §5.1


class FalsifierError(RuntimeError):
    pass


@dataclass(frozen=True)
class Firing:
    name: str
    fired: bool
    detail: str

    def __bool__(self) -> bool:
        return self.fired


# ── §5.1 — MDE by sign-flip permutation, computed from the CONTROL ────────
@dataclass(frozen=True)
class NullBand:
    mde: float
    observed_mean: float
    p_value: float
    n: int

    def describe(self) -> str:
        return (f"MDE {self.mde:.4f} from {2 ** self.n} sign assignments over "
                f"n={self.n} within-control replicate differences "
                f"(control mean {self.observed_mean:+.4f}, p={self.p_value:.4f})")


def null_band(control_deltas: list[Delta], *,
              quantile: float = PERMUTATION_QUANTILE) -> NullBand:
    """⛔⛔ THE MDE COMES FROM THE CONTROL ARM ALONE AND IS COMPUTED BEFORE THE
    INTERACTING ARM IS UNBLINDED (§5.1). An MDE estimated with the treatment in
    view is a threshold chosen to clear.

    The null is exact, not asymptotic: under H0 the sign of each seed's
    within-control replicate difference is arbitrary, so enumerating all 2^n
    sign assignments gives the exact permutation distribution of the mean. With
    n = 8 that is 256 assignments -- cheap, and no distributional assumption.
    """
    if len(control_deltas) < 2:
        raise FalsifierError(
            f"an MDE from {len(control_deltas)} paired difference(s) is not an "
            "estimate of anything. The control needs replicate pairs per seed.")
    d = [x.value for x in control_deltas]
    n = len(d)
    means = [abs(sum(s * v for s, v in zip(signs, d)) / n)
             for signs in itertools.product((1, -1), repeat=n)]
    means.sort()
    mde = means[min(int(quantile * len(means)), len(means) - 1)]
    obs = sum(d) / n
    p = sum(m >= abs(obs) for m in means) / len(means)
    return NullBand(mde=mde, observed_mean=obs, p_value=p, n=n)


def permutation_p(deltas: list[Delta]) -> float:
    """Exact two-sided sign-flip p-value for a set of paired differences."""
    d = [x.value for x in deltas]
    n = len(d)
    obs = abs(sum(d) / n)
    hits = sum(abs(sum(s * v for s, v in zip(signs, d)) / n) >= obs
               for signs in itertools.product((1, -1), repeat=n))
    return hits / (2 ** n)


# ── §5.2 — THE HEADROOM GATE ──────────────────────────────────────────────
@dataclass(frozen=True)
class Headroom:
    noise_floor: float
    available: float
    mde: float
    open: bool

    def describe(self) -> str:
        verdict = "OPEN" if self.open else "CLOSED — UNINFORMATIVE, NOT A NULL"
        return (f"noise floor {self.noise_floor:.4f}, headroom "
                f"{self.available:.4f} vs MDE {self.mde:.4f} ⇒ {verdict}")


def headroom(noise_floor: Measurement, mde: float) -> Headroom:
    """⛔⛔ CAN THIS CELL SHOW AN EFFECT AT ALL?

    `noise_floor` is epoch-0 disagreement between two independent replicates of
    the SAME speaker on the SAME probes -- the departure you measure from
    re-sampling alone. What is left above it is all `D` can ever move. If that
    is not more than the MDE the cell is incapable of demonstrating the effect,
    and its firing is uninformative about the claim rather than evidence
    against it.
    """
    available = 1.0 - noise_floor.value
    return Headroom(noise_floor=noise_floor.value, available=available,
                    mde=mde, open=available > mde)


def noise_floor(rep_a, rep_b, *, epoch: int = 0,
                exclude: frozenset[str] = frozenset()) -> Measurement:
    """Epoch-0 disagreement between two independent replicates."""
    from .observe import _mapping, _items                      # noqa: PLC2701
    from ..harness.paired import measure

    keys = _items(rep_a, exclude)
    ma = {m: _mapping(rep_a.epochs[epoch], m) for m in rep_a.models}
    mb = {m: _mapping(rep_b.epochs[epoch], m) for m in rep_b.models}
    items = [f"{m}|{k}" for m in rep_a.models for k in keys]

    def score(seq):
        return sum(ma[i.split("|", 1)[0]][i.split("|", 1)[1]]
                   != mb[i.split("|", 1)[0]][i.split("|", 1)[1]]
                   for i in seq) / len(seq)

    return measure(f"noise_floor[{rep_a.arm} s{rep_a.seed}]", "probe_x_model",
                   items, score, key=str, arm=rep_a.arm, seed=rep_a.seed,
                   epoch=epoch, axis=f"{rep_a.axis.key}:{rep_a.axis.setting}",
                   battery=rep_a.battery, replicate=-1)


# ── the falsifiers ────────────────────────────────────────────────────────
def f1_internalizability(valid_rate: float, *, prompted: bool) -> Firing:
    """⛔ In the prompted pass F1 is FIRED BY CONSTRUCTION -- a prompted model
    reaches validity only through reject-and-retry, so the measured mapping is
    partly the GATE's. That is exactly why the prompted pass may report `D_ctx`
    and is barred from any `D_w` claim."""
    if prompted:
        return Firing("F1", True,
                      "prompted pass: validity comes from reject-and-retry, so "
                      "F1 is fired by construction. `D_ctx` only; no `D_w` "
                      "claim may be made from this pass.")
    fired = valid_rate < VALID_EMISSION_THRESHOLD
    return Firing("F1", fired,
                  f"native valid-emission {valid_rate:.3f} vs threshold "
                  f"{VALID_EMISSION_THRESHOLD:.2f}"
                  + (" — retry dominates; drift is confounded with "
                     "validity-failure" if fired else " — clear"))


NATIVE_THRESHOLD = 0.90              # F-LOCAL (SCOPE_LOCAL_FINETUNE §3)


class VacuousFalsifier(RuntimeError):
    """A falsifier that structurally cannot fire. Refused, never reported."""


def f_local(*, render_rate: float, speak_rate: float, card: bool,
            constrained_decoding: bool) -> Firing:
    """THE INTERNALIZABILITY GATE FOR OWNED WEIGHTS. Gates the drift measurement.

    ⛔⛔ TWO WAYS THIS COULD BE MADE VACUOUS, AND BOTH ARE REFUSED RATHER THAN
    DISCOURAGED. A falsifier that cannot come back positive is not a falsifier;
    it is a green light with ceremony, and this project has already shipped that
    shape twice (a self-confirming partition test, an unreachable distractor
    guard). Here it would be one level further down, in the sampler.

      constrained_decoding -- grammar-constrained generation makes an invalid
          emission STRUCTURALLY IMPOSSIBLE. Validity is then 100 % by
          construction, F-LOCAL can never fire, and the number measures the
          decoder rather than the model. Constrained decoding is legitimate as a
          PRODUCT feature; it is poison to this MEASUREMENT.
      card -- with the 233-form table in context, decoding is a lookup. The bar
          is explicitly "without the card", because a model that needs it has
          internalised nothing.

    Recovery set, bounded and pre-committed (SCOPE §3), in order:
      1. more contrastive negatives from the widened failure log
      2. curriculum fine-tune -- class discipline before composition
      3. bigger backbone (Tier B)
    Persistent firing ⇒ BOUNDARY: the constraint is not internalizable at this
    scale, which is a real finding about the grammar's learnability.
    """
    if constrained_decoding:
        raise VacuousFalsifier(
            "F-LOCAL cannot be measured under grammar-constrained decoding: "
            "invalid emission is impossible by construction, so the falsifier "
            "could never fire and the rate would describe the sampler, not the "
            "model. Measure it on raw, unconstrained generation.")
    if card:
        raise VacuousFalsifier(
            "F-LOCAL cannot be measured with the lexicon card in context: "
            "decoding becomes a lookup and the result would describe the card. "
            "The bar is native, cardless emission -- run with card=False.")
    worst = min(render_rate, speak_rate)
    fired = worst < NATIVE_THRESHOLD
    return Firing(
        "F-LOCAL", fired,
        f"native no-card first-attempt legal: render {render_rate:.3f}, speak "
        f"{speak_rate:.3f} vs threshold {NATIVE_THRESHOLD:.2f}"
        + (" — the class system is not internalised at this scale; drift would "
           "be confounded with validity-failure" if fired
           else " — clear; drift is measurable on a native speaker"))


def f2_drift_is_noise(delta_d: Delta, mde: float) -> Firing:
    """⛔⛔ THE LOAD-BEARING BRICK. Fires when the measured drift is
    indistinguishable from what the same models produce with no partner
    adapting to them."""
    fired = delta_d.value <= mde
    return Firing("F2", fired,
                  f"ΔD = {delta_d.pts()} pts vs MDE {100 * mde:+.2f} pts"
                  + (" — drift is the constraint's own generation variance; "
                     "unattributable" if fired else " — drift exceeds control"))


def f3_pact(delta_c: Delta, mde: float) -> Firing:
    """Fires when the pair departed but did not converge. ⭐ Registered outcome
    name: WANDERING, NOT CONVENTION -- a distinct, honest, publishable result,
    never a qualified success."""
    fired = delta_c.value <= mde
    return Firing("F3", fired,
                  f"ΔC = {delta_c.pts()} pts vs MDE {100 * mde:+.2f} pts"
                  + (" — WANDERING, NOT CONVENTION" if fired
                     else " — the pair converged beyond control"))


def f4_degeneration(interacting_cov: list[dict], control_cov: list[dict]) -> Firing:
    """⭐ THE FALSIFIER THAT FIRES ON CONFABULATED DRIFT. A pair collapsing into
    repetition shows a large `D` -- and a huge `C` -- for the opposite of the
    claimed reason: they have not agreed on a language, they have stopped saying
    anything.

    ⛔⛔ TWO TESTS, BECAUSE THE PRE-REGISTERED ONE ALONE MISSES THE WORST CASE.

    §2 says "the interacting arm's root-diversity declines by more than 25 %
    from epoch 0 while the control's does not". Measured on a pair that falls
    silent together, that rule reads **+0.0 %** and F4 stays clear -- because
    epoch 0 has no emitted turns to count, so the first measurable window is
    already the collapsed one and there is no decline left to see. The rule as
    written can only catch a SLOW collapse. A fast one -- the more dangerous one,
    since it produces ΔC = +100 pts -- walks straight past it.

    So the within-arm decline is kept exactly as pre-registered, and a LEVEL
    comparison against the control at the same epoch is added beside it. Either
    signature fires. Recorded as DEVIATIONS_ACT2 D2; the pre-registered test is
    not weakened, only supplemented, and the supplement is the paired form the
    rest of the design already uses.
    """
    def decline(cov: list[dict]) -> float:
        first = cov[0].get("root_ttr", 0.0)
        last = cov[-1].get("root_ttr", 0.0)
        return (first - last) / first if first else 0.0

    di, dc = decline(interacting_cov), decline(control_cov)
    slow = di > ROOT_DIVERSITY_DECLINE and dc <= ROOT_DIVERSITY_DECLINE

    lvl_i = interacting_cov[-1].get("root_ttr", 0.0)
    lvl_c = control_cov[-1].get("root_ttr", 0.0)
    shortfall = (lvl_c - lvl_i) / lvl_c if lvl_c else 0.0
    fast = shortfall > ROOT_DIVERSITY_DECLINE

    fired = slow or fast
    why = ("collapse within the arm" if slow else
           "impoverished relative to control" if fast else "")
    return Firing("F4", fired,
                  f"root diversity — decline: interacting {di:+.1%}, control "
                  f"{dc:+.1%}; final TTR: {lvl_i:.3f} vs control {lvl_c:.3f} "
                  f"({shortfall:+.1%} shortfall), threshold "
                  f"{ROOT_DIVERSITY_DECLINE:.0%}"
                  + (f" — DEGENERATION, not convention ({why})" if fired
                     else " — no degeneration signature"))


def f5_leakage(report) -> Firing:
    return Firing("F5", report.void,
                  f"leakage {report.rate:.1%} ({len(report.leaked)}/"
                  f"{report.checked})"
                  + (" — run VOID, re-run with a fresh battery" if report.void
                     else " — leaked probes excluded before unblinding"))


# ── §5.4 / §5.5 — recovery, multiplicity, verdict ─────────────────────────
def holm(p_values: dict[str, float], *, alpha: float = ALPHA) -> dict[str, bool]:
    """Holm–Bonferroni over the four axis tests. ⛔ Registered in advance so the
    correction cannot be picked after seeing which axis moved."""
    ordered = sorted(p_values.items(), key=lambda kv: kv[1])
    m, out, rejected_so_far = len(ordered), {}, True
    for i, (key, p) in enumerate(ordered):
        threshold = alpha / (m - i)
        rejected_so_far = rejected_so_far and p <= threshold
        out[key] = rejected_so_far
    return out


@dataclass(frozen=True)
class AxisResult:
    axis: str
    delta_d: float
    delta_c: float
    mde: float
    p_value: float
    headroom_open: bool
    replicated: bool | None          # None = held-out block not yet run
    holm_pass: bool = False

    @property
    def recovered(self) -> bool:
        """⭐ ALL THREE CONDITIONS, AND THE STRICTNESS IS DELIBERATE (§5.4). The
        falsifier is built to fire on CONFABULATED drift as much as on absent
        drift, so a single-block result is a candidate, never a finding."""
        return bool(self.delta_d > self.mde and self.headroom_open
                    and self.holm_pass and self.replicated)


@dataclass(frozen=True)
class Verdict:
    outcome: str
    detail: str
    axes: tuple[AxisResult, ...]


def verdict(results: list[AxisResult]) -> Verdict:
    """§6's stopping rule, with the uninformative-cell rule binding."""
    if not results:
        raise FalsifierError("no axis results; there is nothing to conclude.")
    for r in results:
        if r.recovered:
            return Verdict(
                "RECOVERED",
                f"constrained LLM communication drifts, and the drift lives in "
                f"{r.axis} (ΔD {r.delta_d:+.4f} > MDE {r.mde:.4f}, headroom "
                f"open, Holm-corrected, replicated on the held-out block)",
                tuple(results))

    uninformative = [r.axis for r in results if not r.headroom_open]
    if uninformative:
        return Verdict(
            "WITHHELD",
            "every axis fired, but "
            f"{len(uninformative)} could not have shown an effect "
            f"({', '.join(uninformative)}). Those cells are UNINFORMATIVE, NOT "
            "NULLS, and a boundary claim resting partly on them would be a "
            "false negative wearing a verdict's clothes. The boundary result is "
            "WITHHELD until they are re-run with headroom.",
            tuple(results))

    return Verdict(
        "BOUNDARY",
        "constrained LLM-to-LLM communication does not drift beyond the "
        "constraint's own generation variance, across every pre-committed "
        "decomposition — every cell informative. A real finding about the "
        "constraint's expressive geometry.",
        tuple(results))


# ── HARDEN 3 · THE ARENA TEMPERATURE FLOOR (a VACUITY PRECONDITION) ───────
#: ⛔⛔ GREEDY DECODING MAKES DRIFT IMPOSSIBLE BY CONSTRUCTION. Two deterministic
#: speakers, given a history, each emit exactly one thing. They can be identical
#: or not, but they cannot DRIFT — there is no distribution for a convention to
#: move within. This is not theoretical: it is precisely why `speak` read 1/12
#: distinct on a constant prompt while the same prompt at temperature 0.8 read
#: 11/12. The weights were never collapsed; the decoder was.
#:
#: ⛔⛔ AND THE FAILURE LOOKS LIKE THE MOST HONEST RESULT AVAILABLE. A drift run
#: at temperature 0 returns a CLEAN NULL — ΔD ≈ 0, ΔC ≈ 0, no pact — which is
#: indistinguishable from the pre-registered BOUNDARY FINDING ("the constraint is
#: not internalizable / no private language forms"). A null produced by the
#: sampler would be written up as a discovery. That is the worst failure this
#: project can produce, so it is refused STRUCTURALLY rather than remembered.
#:
#: ⚠️ THE VALUE IS A PRE-REGISTERED PARAMETER, NOT A KNOB. It is locked before
#: the arena runs and must not be tuned after seeing arena results. It is set
#: from a measured sweep (`tools/act2_temp_sweep.py`), not from taste.
MIN_ARENA_TEMPERATURE = 0.7

#: How many samples of ONE history the precondition draws, and how many must
#: differ. ⭐ THE TEMPERATURE NUMBER ALONE IS NOT ENOUGH: a correctly-configured
#: temperature on a degenerate model still cannot drift, so the guard measures
#: the actual variability instead of trusting the setting.
PRECONDITION_SAMPLES = 12
PRECONDITION_MIN_DISTINCT = 3


def arena_preconditions(*, temperature: float,
                        same_history_samples: list | None = None) -> None:
    """Refuse to measure drift in a configuration where drift cannot appear.

    ⛔ RAISES `VacuousFalsifier`; it never returns a null. A null from a
    too-cold sampler and a null from a real boundary are the same number, and
    only one of them is a finding.

    `same_history_samples` — optional, and it is the half that actually bites:
    N continuations of ONE identical history at the configured temperature. If
    they are all the same, this speaker cannot drift no matter what the
    temperature says.
    """
    if temperature is None:
        raise VacuousFalsifier(
            "no decoding temperature was recorded for the arena. It is a "
            "pre-registered parameter and an unrecorded one cannot be checked.")
    if temperature < MIN_ARENA_TEMPERATURE:
        raise VacuousFalsifier(
            f"arena temperature {temperature} is below the pre-registered floor "
            f"{MIN_ARENA_TEMPERATURE}. At this temperature the speakers are "
            "effectively deterministic, so D_ctx is VACUOUS: the run would "
            "return a clean null that is indistinguishable from the boundary "
            "finding. Refused rather than reported.")

    if same_history_samples is None:
        return
    n = len(same_history_samples)
    if n < PRECONDITION_SAMPLES:
        raise VacuousFalsifier(
            f"the variability precondition needs {PRECONDITION_SAMPLES} samples "
            f"of one history, got {n}. Too few to tell a stuck speaker from a "
            "varying one.")
    import json as _json
    distinct = len({_json.dumps(s, sort_keys=True, ensure_ascii=False)
                    if not isinstance(s, str) else s
                    for s in same_history_samples})
    if distinct < PRECONDITION_MIN_DISTINCT:
        raise VacuousFalsifier(
            f"the speaker produced {distinct} distinct continuation(s) from "
            f"{n} samples of the SAME history at temperature {temperature}. "
            "The temperature is above the floor but this speaker still cannot "
            "vary, so it cannot drift — the setting was right and the speaker "
            "is degenerate anyway. This is the check the temperature number "
            "alone would have passed.")
