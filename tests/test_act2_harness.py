"""ACT 2 HARNESS — PREREG `20620b7c`, step 1. Control first.

⛔ EVERY TEST HERE IS OFFLINE AND COSTS $0.00. No hosted model, no network, no
key. The speakers are synthetic and their drift is known BY CONSTRUCTION, which
is the entire point: an observable that has never been shown a known quantity is
not an instrument, and Act 2's integrity is the control, not the transcript.

WHAT THESE CERTIFY
  1. `D` reads 0 on a speaker that provably does not drift, and reads the right
     sign on ones that do.
  2. ⭐⭐ `C` SEES A PACT THAT `D` CANNOT. Two speakers that provably converge on
     a shared codebook show ΔD ≈ 0 and ΔC large. Without the second observable
     Act 2's cheap pass would report "drift is noise" on a pair that has
     demonstrably built a private convention. This is PREREG §0.1, measured.
  3. The control cannot silently contain the treatment.
  4. A probe never becomes conversation, and never runs without the
     conversation in context.
  5. A transcript cannot be read before its result is banked.
"""
from __future__ import annotations

import pytest

from tlon.act2 import arena, falsify, observe, probes
from tlon.act2.axes import BASELINE
from tlon.act2.ledger import Ledger, LedgerError, TranscriptSealed
from tlon.act2.speaker import (DegeneratingSpeaker, FrozenPartner,
                               ImitatingSpeaker, MutualCollapseSpeaker,
                               StableSpeaker, WanderingSpeaker)
from tlon.harness.paired import (DegenerateContrast, UnpairedComparison,
                                 measure)

TURNS, EVERY = 40, 10


@pytest.fixture(scope="module")
def battery():
    return probes.build(seed=7, n_prod=8, n_comp=8)


@pytest.fixture(scope="module")
def frozen():
    """Two DIFFERENT pre-recorded partners — see the control-integrity tests."""
    return (arena.record_frozen_transcript(StableSpeaker("f1", 900), turns=TURNS),
            arena.record_frozen_transcript(StableSpeaker("f2", 901), turns=TURNS))


def _pair(cls, seed, **kw):
    return cls("A", seed, **kw), cls("B", seed + 1000, **kw)


def _both_arms(cls, battery, frozen, *, seed=5, **kw):
    a1, b1 = _pair(cls, seed, **kw)
    inter = arena.run("interacting", speaker_a=a1, speaker_b=b1,
                      battery=battery, seed=seed, turns=TURNS, epoch_every=EVERY)
    a2, b2 = _pair(cls, seed, **kw)
    yoked = arena.run("yoked", speaker_a=a2, speaker_b=b2, battery=battery,
                      seed=seed, turns=TURNS, epoch_every=EVERY,
                      frozen_a=frozen[0], frozen_b=frozen[1])
    return inter, yoked


def _last(run):
    return len(run.epochs) - 1


# ══ THE BATTERY (PREREG §3) ══════════════════════════════════════════════
def test_the_battery_is_the_specified_size_and_reproducible_from_its_seed():
    """⛔ The battery is the anchor everything is measured against. If it can
    move, drift can be manufactured by moving it."""
    a, b = probes.build(seed=7, n_prod=8, n_comp=8), probes.build(
        seed=7, n_prod=8, n_comp=8)
    assert a.digest == b.digest
    assert len(a.production) == 8 and len(a.comprehension) == 8
    assert probes.build(seed=8, n_prod=8, n_comp=8).digest != a.digest


def test_every_distractor_is_pi_DISTINCT_from_the_answer_and_from_each_other(
        battery):
    """The invariant on the produced artefact. ⛔ NOTE THIS IS NOT A GUARD TEST —
    see the next two. Distinctness is guaranteed upstream, so this can only fail
    if something further up already broke."""
    for c in battery.comprehension:
        assert len(set(c.option_impressions)) == len(c.option_impressions)
        assert c.option_impressions[c.answer] == c.target_impression


def test_a_single_part_mutation_ALWAYS_separates_the_impression():
    """⭐⭐ THE PROPERTY THE WHOLE COMPREHENSION HALF RESTS ON, tested with power
    rather than assumed. Every near-miss distractor is a single denoting-part
    mutation; if one could leave the impression unchanged, the true gloss and a
    distractor would be the same answer.

    ⛔ THIS TEST REPLACES ONE THAT COULD NOT COME BACK POSITIVE. The red-proof
    removed the distinctness check in `build()` and every test still passed —
    because across 14,799 mutations there is not one collision to catch. That
    branch was unreachable, so a battery-level assertion was checking a
    guarantee, not enforcing one."""
    import random
    from tlon.grammar import classes as C
    lex, k = C.load()["classes"], C.constraints()
    rng = random.Random(3)
    checked = 0
    for _ in range(400):
        node = probes._random_node(rng, lex, k)          # noqa: SLF001
        got = probes._validate(node, "ka")               # noqa: SLF001
        if not got:
            continue
        answer = probes.impression(got[0])
        for part in probes._DISTRACTOR_PARTS:            # noqa: SLF001
            mutated = probes._mutate(node, part, rng, lex)   # noqa: SLF001
            if mutated is None:
                continue
            got_m = probes._validate(mutated, "ka")      # noqa: SLF001
            if not got_m:
                continue
            checked += 1
            assert probes.impression(got_m[0]) != answer, (
                f"a {part!r} mutation left the impression unchanged")
    assert checked > 500, f"only {checked} mutations exercised; too weak to mean much"


def test_a_colliding_distractor_RAISES_rather_than_being_skipped():
    """⛔ The tripwire itself, tested directly — the only way to reach a branch
    that the generator cannot produce. A silent skip here would hand out a
    battery built on a broken π and nothing downstream would notice."""
    with pytest.raises(probes.BatteryError, match="unchanged"):
        probes.assert_distinct("same", "same", [], "root")
    with pytest.raises(probes.BatteryError, match="collided"):
        probes.assert_distinct("x", "answer", ["x"], "orient")
    probes.assert_distinct("x", "answer", ["y"], "orient")     # the normal case


def test_the_battery_never_probes_one_impression_twice(battery):
    targets = [p.target_impression for p in battery.production]
    targets += [c.target_impression for c in battery.comprehension]
    assert len(set(targets)) == len(targets)


def test_a_short_battery_RAISES_rather_than_being_returned():
    """⛔ A battery quietly smaller than specified changes the power of every
    test computed on it, and nothing downstream would notice."""
    with pytest.raises(probes.BatteryError, match="short"):
        probes.build(seed=1, n_prod=100000, n_comp=1)


# ══ INSTRUMENT VALIDATION — known ground truth ═══════════════════════════
def test_a_speaker_that_does_not_drift_reads_EXACTLY_zero(battery, frozen):
    inter, _ = _both_arms(StableSpeaker, battery, frozen)
    assert observe.departure(inter, _last(inter)).value == 0.0


def test_a_WANDERING_pair_drifts_but_the_control_drifts_just_as_much(
        battery, frozen):
    """⛔⛔ THIS IS WHAT F2 EXISTS FOR. Each speaker mutates its own codebook and
    ignores its partner entirely. `D` is large — and identical in the control,
    because the wandering was never communication-driven."""
    inter, yoked = _both_arms(WanderingSpeaker, battery, frozen, rate=0.3)
    e = _last(inter)
    d_int = observe.departure(inter, e)
    d_yok = observe.departure(yoked, e)
    assert d_int.value > 0.2, "the wandering speaker did not wander"
    delta = observe.delta(d_int, d_yok)
    assert abs(delta.value) < 0.10
    assert falsify.f2_drift_is_noise(delta, mde=0.10).fired


def test_C_SEES_A_PACT_THAT_D_CANNOT(battery, frozen):
    """⭐⭐ THE TEST THAT JUSTIFIES THE SECOND OBSERVABLE (PREREG §0.1).

    Two imitating speakers, live, converge on a SHARED codebook — a private
    convention, by construction. Yoked to two DIFFERENT frozen partners they
    depart from epoch 0 just as far, they simply depart toward different places.

    So ΔD is ≈ 0 on a pair that has demonstrably built a private language, and
    F2 alone would report "drift is noise" and close the arc. Only ΔC sees it.
    """
    inter, yoked = _both_arms(ImitatingSpeaker, battery, frozen, adopt=0.9)
    e = _last(inter)
    dd = observe.delta(observe.departure(inter, e), observe.departure(yoked, e))
    dc = observe.delta(observe.convergence(inter, e),
                       observe.convergence(yoked, e))

    assert abs(dd.value) < 0.15, (
        "departure separated the arms; this test no longer demonstrates the "
        "gap it exists to demonstrate")
    assert dc.value > 0.30, "the interacting pair did not converge"
    mde = 0.15
    assert falsify.f2_drift_is_noise(dd, mde).fired, "F2 should fire here"
    assert not falsify.f3_pact(dc, mde).fired, "F3 must NOT fire — this is a pact"


def _f4(inter, yoked):
    return falsify.f4_degeneration([e.covariates for e in inter.epochs[1:]],
                                   [e.covariates for e in yoked.epochs[1:]])


def test_a_pair_that_FALLS_SILENT_TOGETHER_is_caught_by_F4(battery, frozen):
    """⭐⭐ CONFABULATED DRIFT, MANUFACTURED ON PURPOSE — and it is the most
    dangerous shape, because it produces ΔC ≈ +100 pts. Two speakers collapsing
    onto one root agree about everything: it looks like the strongest private
    language in the study and it is the opposite, a pair that has stopped saying
    anything. F4 is the only thing standing between that and a headline."""
    inter, yoked = _both_arms(MutualCollapseSpeaker, battery, frozen, rate=0.9)
    e = _last(inter)
    assert observe.convergence(inter, e).value > 0.9, "the pair did not collapse"
    fired = _f4(inter, yoked)
    assert fired.fired, fired.detail


def test_F4_does_NOT_fire_on_a_GENUINE_pact(battery, frozen):
    """⛔⛔ THE DISCRIMINATION IS THE WHOLE VALUE. A degeneration detector that
    also fires on real convention would veto the finding it exists to protect.
    An earlier version compared raw distinct-root COUNTS across arms — the yoked
    arm pools two lanes, so the control always looked twice as diverse and F4
    fired on EVERY cell including the one with no drift at all. Type/token over
    live speakers only, exactly as §2 specifies."""
    inter, yoked = _both_arms(ImitatingSpeaker, battery, frozen, adopt=0.9)
    assert not _f4(inter, yoked).fired, _f4(inter, yoked).detail
    stable_i, stable_y = _both_arms(StableSpeaker, battery, frozen)
    assert not _f4(stable_i, stable_y).fired, "F4 fired on a pair with no drift"


def test_solo_degeneration_is_NOT_communication_driven_and_F4_says_so(
        battery, frozen):
    """A pair that each collapse independently degenerate in BOTH arms, so the
    collapse is not attributable to the interaction — and F2 has already fired,
    so no drift claim is being made about them anyway."""
    inter, yoked = _both_arms(DegeneratingSpeaker, battery, frozen, rate=0.5)
    assert not _f4(inter, yoked).fired


def test_the_covariates_never_count_a_frozen_partners_replayed_turns(
        battery, frozen):
    """⛔ A frozen partner is REPLAYING, not speaking. Counting its turns would
    put the pre-recorded transcript's diversity into the control's covariate."""
    _, yoked = _both_arms(StableSpeaker, battery, frozen)
    # Two lanes × 20 live turns each; a stable speaker uses N_CONCEPTS roots.
    assert yoked.epochs[-1].covariates["root_ttr"] <= 1.0
    assert yoked.epochs[-1].covariates["valid_rate"] == 1.0


def test_the_secondary_estimator_cannot_be_differenced_into_a_verdict(
        battery, frozen):
    """⛔ EXPLORATORY, and held in a type with no comparison operators so it
    cannot quietly become a decision."""
    inter, _ = _both_arms(WanderingSpeaker, battery, frozen, rate=0.3)
    g = observe.graded_departure(inter, _last(inter))
    assert isinstance(g, observe.Exploratory)
    with pytest.raises(TypeError):
        _ = g < 0.5                       # type: ignore[operator]


# ══ CONTROL INTEGRITY (PREREG §4) ════════════════════════════════════════
def test_yoking_BOTH_speakers_to_THE_SAME_transcript_is_refused(battery, frozen):
    """⛔⛔ A CONTROL THAT CONTAINS THE TREATMENT ATTRIBUTES NOTHING. Yoked to one
    shared transcript, both speakers adapt toward one attractor and therefore
    toward each other — `C(control)` rises and ΔC is biased toward zero. The
    prereg leaves this open; the harness refuses it. (DEVIATIONS_ACT2 D1)"""
    a, b = _pair(StableSpeaker, 3)
    with pytest.raises(arena.ArenaError, match="SAME transcript"):
        arena.run("yoked", speaker_a=a, speaker_b=b, battery=battery, seed=3,
                  turns=4, epoch_every=4, frozen_a=frozen[0], frozen_b=frozen[0])


def test_the_yoked_arm_REFUSES_to_run_without_a_frozen_partner(battery):
    a, b = _pair(StableSpeaker, 3)
    with pytest.raises(arena.ArenaError):
        arena.run("yoked", speaker_a=a, speaker_b=b, battery=battery, seed=3,
                  turns=4, epoch_every=4)


def test_a_frozen_partner_with_nothing_to_say_is_refused():
    """Silence is not a control: the live speaker would have nothing to adapt
    to and the yoked arm would silently become the solo arm."""
    with pytest.raises(ValueError, match="silence"):
        FrozenPartner("empty", [])


def test_EVERY_arm_measures_BOTH_models(battery, frozen):
    """⛔ A REAL BUG THIS CATCHES. With B treated only as A's partner, the
    interacting arm probed A alone — `C` is agreement between A and B, so it
    became uncomputable, and the item sets stopped matching across arms."""
    inter, yoked = _both_arms(StableSpeaker, battery, frozen)
    for run in (inter, yoked):
        for rec in run.epochs:
            assert set(rec.production) == set(run.models)
            assert set(rec.comprehension) == set(run.models)


def test_arms_are_pairable_because_they_share_an_item_set(battery, frozen):
    inter, yoked = _both_arms(StableSpeaker, battery, frozen)
    e = _last(inter)
    assert (observe.departure(inter, e).items.digest
            == observe.departure(yoked, e).items.digest)


# ══ PROBE HYGIENE (PREREG §3.4) ══════════════════════════════════════════
class _Watcher(StableSpeaker):
    """Records the context length it was probed with, and tries to append."""
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.probe_ctx_lengths = []

    def render(self, stimulus, history):
        self.probe_ctx_lengths.append(len(history))
        with pytest.raises((AttributeError, TypeError)):
            history.append("mil ol frem ka")     # type: ignore[attr-defined]
        return super().render(stimulus, history)


def test_a_probe_is_answered_WITH_the_conversation_in_context(battery):
    """⛔⛔ PREREG §0.3. In a prompted pass the context window is the ONLY thing
    that can differ between epoch 0 and epoch t — the weights are identical. A
    probe run in a clean context therefore returns epoch-0 behaviour by
    construction, `D_ctx ≡ 0`, and F2 fires for a reason unrelated to the claim."""
    a, b = _Watcher("A", 1), _Watcher("B", 2)
    run = arena.run("interacting", speaker_a=a, speaker_b=b, battery=battery,
                    seed=1, turns=TURNS, epoch_every=EVERY)
    assert a.probe_ctx_lengths[0] == 0, "epoch 0 should see an empty history"
    assert a.probe_ctx_lengths[-1] > 0, "a later probe saw no conversation"
    assert len(run.epochs) > 2


def test_a_probe_never_BECOMES_conversation(battery):
    """The branch is discarded. An immutable history is the mechanism: the
    speaker can read it and cannot append to it."""
    a, b = _Watcher("A", 1), _Watcher("B", 2)
    run = arena.run("interacting", speaker_a=a, speaker_b=b, battery=battery,
                    seed=1, turns=TURNS, epoch_every=EVERY)
    # TURNS turns, every one emitted by a stable speaker -> exactly TURNS turns.
    assert len(run.transcript) == TURNS


# ══ THE COMPARISON GUARD ═════════════════════════════════════════════════
def test_comparing_an_arm_with_ITSELF_is_refused(battery, frozen):
    inter, _ = _both_arms(StableSpeaker, battery, frozen)
    e = _last(inter)
    with pytest.raises(DegenerateContrast):
        observe.delta(observe.departure(inter, e), observe.departure(inter, e))


def test_comparing_arms_measured_over_DIFFERENT_probe_sets_is_refused(
        battery, frozen):
    """⛔ Excluding a leaked probe from one arm only changes the item digest.
    The guard refusing is the guard working — leakage exclusions must be applied
    identically to both arms, before unblinding."""
    inter, yoked = _both_arms(StableSpeaker, battery, frozen)
    e = _last(inter)
    with pytest.raises(UnpairedComparison, match="UNPAIRED"):
        observe.delta(observe.departure(inter, e),
                      observe.departure(yoked, e, exclude=frozenset({"P00"})))


def test_a_bare_float_cannot_enter_a_comparison(battery, frozen):
    inter, _ = _both_arms(StableSpeaker, battery, frozen)
    with pytest.raises(UnpairedComparison):
        observe.delta(observe.departure(inter, 1), 0.5)      # type: ignore[arg-type]


# ══ MDE AND THE HEADROOM GATE (PREREG §5.1, §5.2) ════════════════════════
def _fake_deltas(values):
    out = []
    for i, v in enumerate(values):
        left = measure("l", "probe", ["x"], lambda s, v=v: v, replicate=0, seed=i)
        right = measure("r", "probe", ["x"], lambda s: 0.0, replicate=1, seed=i)
        from tlon.harness.paired import paired_delta
        out.append(paired_delta(left, right, contrast="replicate"))
    return out


def test_the_MDE_is_an_EXACT_sign_flip_permutation_over_the_control():
    """⛔ The MDE comes from the control arm alone and is computed before the
    interacting arm is unblinded. An MDE estimated with the treatment in view is
    a threshold chosen to clear."""
    band = falsify.null_band(_fake_deltas([0.10] * 8))
    assert band.n == 8
    # every |mean| under sign-flips of a constant vector is a multiple of 0.025
    assert 0.0 < band.mde <= 0.10
    assert band.p_value == pytest.approx(2 / 256)


def test_an_MDE_cannot_be_estimated_from_one_difference():
    with pytest.raises(falsify.FalsifierError, match="not an estimate"):
        falsify.null_band(_fake_deltas([0.1]))


def test_a_cell_without_headroom_is_UNINFORMATIVE_NOT_A_NULL():
    """⛔⛔ THE PROJECT'S HARDEST-WON RULE, BINDING HERE. If re-sampling alone
    moves the mapping almost as much as an effect could, the cell CANNOT show
    the effect and its firing says nothing about the claim."""
    noisy = measure("nf", "probe", ["x"], lambda s: 0.97, arm="yoked", seed=0)
    gate = falsify.headroom(noisy, mde=0.10)
    assert not gate.open
    assert "UNINFORMATIVE, NOT A NULL" in gate.describe()

    quiet = measure("nf", "probe", ["x"], lambda s: 0.02, arm="yoked", seed=0)
    assert falsify.headroom(quiet, mde=0.10).open


def test_the_noise_floor_is_measured_between_INDEPENDENT_REPLICATES(
        battery, frozen):
    a, b = _pair(StableSpeaker, 11)
    r1 = arena.run("yoked", speaker_a=a, speaker_b=b, battery=battery, seed=11,
                   turns=TURNS, epoch_every=EVERY, frozen_a=frozen[0],
                   frozen_b=frozen[1], replicate=0)
    a, b = _pair(StableSpeaker, 11)
    r2 = arena.run("yoked", speaker_a=a, speaker_b=b, battery=battery, seed=11,
                   turns=TURNS, epoch_every=EVERY, frozen_a=frozen[0],
                   frozen_b=frozen[1], replicate=1)
    # deterministic speakers re-sample identically: the floor is exactly 0
    assert falsify.noise_floor(r1, r2).value == 0.0


# ══ THE STOPPING RULE (PREREG §5.4, §5.5, §6) ════════════════════════════
def _axis(name, *, dd=0.30, mde=0.10, headroom_open=True, replicated=True,
          holm_pass=True, dc=0.30, p=0.001):
    return falsify.AxisResult(axis=name, delta_d=dd, delta_c=dc, mde=mde,
                              p_value=p, headroom_open=headroom_open,
                              replicated=replicated, holm_pass=holm_pass)


def test_recovery_requires_ALL_THREE_conditions():
    """⭐ The strictness is deliberate: the falsifier is built to fire on
    CONFABULATED drift as much as on absent drift, so a single-block result is a
    candidate, never a finding."""
    assert _axis("residue").recovered
    assert not _axis("residue", dd=0.05).recovered          # under MDE
    assert not _axis("residue", headroom_open=False).recovered
    assert not _axis("residue", replicated=False).recovered
    assert not _axis("residue", replicated=None).recovered  # block not yet run
    assert not _axis("residue", holm_pass=False).recovered


def test_a_boundary_result_needs_EVERY_cell_to_have_been_informative():
    """⛔⛔ A boundary claim resting partly on cells that could not have shown an
    effect is a false negative wearing a verdict's clothes."""
    fired = [_axis(k, dd=0.01) for k in ("force_evidential", "residue")]
    assert falsify.verdict(fired).outcome == "BOUNDARY"

    fired[1] = _axis("residue", dd=0.01, headroom_open=False)
    v = falsify.verdict(fired)
    assert v.outcome == "WITHHELD"
    assert "UNINFORMATIVE, NOT" in v.detail and "residue" in v.detail


def test_a_cleared_axis_names_WHERE_the_drift_lives():
    v = falsify.verdict([_axis("force_evidential", dd=0.01), _axis("residue")])
    assert v.outcome == "RECOVERED" and "residue" in v.detail


def test_holm_bonferroni_is_applied_across_the_four_axes():
    """Registered in advance so the correction cannot be chosen after seeing
    which axis moved."""
    out = falsify.holm({"a": 0.001, "b": 0.20, "c": 0.30, "d": 0.40})
    assert out["a"] and not out["b"] and not out["c"] and not out["d"]
    assert all(falsify.holm({"a": 0.001, "b": 0.002}).values())


def test_the_prompted_pass_is_barred_from_a_weight_level_claim():
    f = falsify.f1_internalizability(1.0, prompted=True)
    assert f.fired and "D_ctx" in f.detail and "no `D_w` claim" in f.detail
    assert not falsify.f1_internalizability(0.95, prompted=False).fired
    assert falsify.f1_internalizability(0.80, prompted=False).fired


# ══ LEAKAGE (F5) ═════════════════════════════════════════════════════════
def test_a_probe_spoken_in_the_conversation_is_caught_and_excluded(battery):
    """⛔ Agreement on a leaked probe is RECALL, NOT CONVENTION, and it inflates
    C in exactly the direction the claim wants."""
    said = {battery.production[0].target_impression}
    rep = probes.leakage(battery, said)
    assert rep.leaked == ("P00",) and not rep.void
    assert not falsify.f5_leakage(rep).fired


def test_a_run_that_leaks_more_than_a_fifth_of_its_battery_is_VOID(battery):
    rep = probes.leakage(battery, battery.impressions())
    assert rep.rate == 1.0 and rep.void
    assert falsify.f5_leakage(rep).fired


def test_a_clean_run_leaks_nothing(battery, frozen):
    inter, _ = _both_arms(StableSpeaker, battery, frozen)
    assert probes.leakage(battery, inter.transcript.impressions()).leaked == ()


# ══ THE NO-TRANSCRIPT RULE (PREREG §5.6) ═════════════════════════════════
def test_a_transcript_CANNOT_BE_READ_before_its_result_is_banked(
        battery, frozen, tmp_path):
    """⛔⛔ A rule that lives in a document is a rule someone follows until the
    evening they are curious. Once you have watched two models chatter in Tlön
    you will see drift whether it is there or not."""
    inter, _ = _both_arms(StableSpeaker, battery, frozen)
    with pytest.raises(TranscriptSealed, match="SEALED"):
        _ = inter.transcript.turns
    with pytest.raises(TranscriptSealed):
        inter.transcript.text()


def test_the_machine_may_measure_a_sealed_transcript(battery, frozen):
    """The seal stops a HUMAN reading a story into it; the leakage check and the
    covariates are numbers and must still be computable."""
    inter, _ = _both_arms(StableSpeaker, battery, frozen)
    assert len(inter.transcript.impressions()) > 0
    assert "distinct_roots" in inter.transcript.covariates()


def test_unsealing_REQUIRES_the_ledger_entry_to_already_exist(
        battery, frozen, tmp_path):
    inter, _ = _both_arms(StableSpeaker, battery, frozen)
    led = Ledger(path=tmp_path / "l.jsonl")
    with pytest.raises(LedgerError, match="no ledger entry"):
        inter.transcript.unseal(led, reason="curiosity")

    led.record(inter.run_id, arm=inter.arm, seed=inter.seed, axis="baseline",
               battery=inter.battery, prereg=falsify.PREREG, delta_d=0.0)
    inter.transcript.unseal(led, reason="post-hoc interpretation, EXPLORATORY")
    assert inter.transcript.turns
    events = [r["event"] for r in led.rows()]
    assert events == ["result", "unseal"], "the unsealing was not recorded"


def test_unsealing_without_a_written_reason_is_refused(battery, frozen, tmp_path):
    inter, _ = _both_arms(StableSpeaker, battery, frozen)
    led = Ledger(path=tmp_path / "l.jsonl")
    with pytest.raises(LedgerError, match="written reason"):
        inter.transcript.unseal(led, reason="   ")


def test_a_result_cannot_be_ledgered_without_its_arm_seed_and_battery(tmp_path):
    """A result that does not say which arm it came from cannot be paired with
    anything later."""
    led = Ledger(path=tmp_path / "l.jsonl")
    with pytest.raises(TypeError):
        led.record("abc", seed=1, axis="baseline")           # no arm/battery


# ══ $0.00 ════════════════════════════════════════════════════════════════
def test_nothing_in_act2_can_reach_a_network():
    import pathlib
    import tlon.act2 as pkg
    for path in pathlib.Path(pkg.__file__).parent.glob("*.py"):
        body = "\n".join(l for l in path.read_text(encoding="utf-8").splitlines()
                         if not l.strip().startswith(("#", '"', "'")))
        for forbidden in ("anthropic", "requests", "urllib", "socket", "openai",
                          "api_key", "http"):
            assert forbidden not in body, f"{forbidden!r} in {path.name}"
