"""⛔⛔ THE RED-PROOF FOR THE SHARED-MEMORY ARM — WRITTEN BEFORE THE MODE.

`PREREG_POSITIVE_CONTROL_KA` `c0de41c7` §4, arm 1: Parfenova Algorithm 1 —
a shared, append-only store that **both speakers read in full**.

⛔⛔ THE FAILURE THIS FILE EXISTS TO MAKE IMPOSSIBLE. The rest of this harness
implements the ASYMMETRIC rule (your own chain accumulates; the partner provokes
and is released). Shared memory is its opposite. If the shared arm silently falls
back to the asymmetric path — a mode string that does not match, a default that
routes to `LIVE`, a copy-paste that keeps `own + _last_other` — then:

    the arm runs self-accumulation, `force:ka` does not move, the run reads as a
    STOP, and the recorded conclusion is **"Tlön shows no convergence even under
    shared memory"** — which is FALSE, and false in the one direction that closes
    the whole line of inquiry.

That is the vacuous-guard shape this project has hit repeatedly: a mechanism that
did nothing and a mechanism that ran and found nothing leave the SAME trace. So
these tests do not check that shared mode "works". They check that shared mode is
**distinguishable from the fallback**, positively, on every axis that separates
them — and `test_the_red_proof_BITES_against_the_self_accumulation_path` asserts
that these very checks FAIL on `LIVE`. A check that passes on both arms is
decoration.

⭐ Note the inversion. `test_two_speaker_harness.py` proves a speaker does NOT
hold the partner's past turns. This file proves it DOES. Same discipline, opposite
target, and both are load-bearing — for different arms of different runs.

⚠️ Shared memory knowingly violates the Tlön ontology (a retained past utterance
is a thing that endures unperceived — a noun, in a nounless language). That is
deliberate and it is the point: the positive control imports the memory model
known to produce convergence in natural language, to ask whether THIS INSTRUMENT
can see convergence at all. It is not a claim about how Tlön speakers should
converse.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

from act2_two_speaker import (COLD, LIVE, SEED_SPEAKER, SHARED,  # noqa: E402
                              visible_history)

#: A history where B has spoken MORE THAN ONCE. That is the whole discriminator:
#: the asymmetric rule shows exactly one of the partner's turns, so any history
#: in which the partner spoke once cannot tell the two modes apart.
HIST = [(SEED_SPEAKER, "s0"),
        ("A", "a1"), ("B", "b1"),
        ("A", "a2"), ("B", "b2"),
        ("A", "a3"), ("B", "b3")]


# ─────────────────────────────────────────────────────────────────────────────
# 1 · what SHARED must be
# ─────────────────────────────────────────────────────────────────────────────

def test_shared_shows_every_turn_by_both_speakers_and_the_seed():
    """Append-only, everyone reads everything. Nothing is dropped."""
    shown = visible_history(HIST, "A", mode=SHARED)
    assert list(shown) == ["s0", "a1", "b1", "a2", "b2", "a3", "b3"]


def test_shared_is_CHRONOLOGICAL_not_own_then_partner():
    """⛔ Order is part of the memory model, not cosmetic.

    The asymmetric rule emits `own + last_other`, which is NOT the order the
    turns happened in. A shared store that reordered into own-then-partner would
    be feeding a different object than Algorithm 1's `C`, while passing any test
    that only checked membership.
    """
    shown = list(visible_history(HIST, "A", mode=SHARED))
    assert shown == [s for _speaker, s in HIST]
    # and the interleave is genuinely alternating, not blocked by speaker
    assert shown.index("b1") < shown.index("a2") < shown.index("b2")


def test_both_speakers_are_handed_the_SAME_store():
    """⭐ THE CLEANEST DISCRIMINATOR. "Both read everything" means A's view and
    B's view are identical objects. Under any per-speaker rule they differ."""
    assert (visible_history(HIST, "A", mode=SHARED)
            == visible_history(HIST, "B", mode=SHARED))


def test_A_can_see_MULTIPLE_of_Bs_turns():
    """The asymmetric rule releases all but the partner's last turn. This is the
    positive assertion that the release is NOT happening."""
    shown = visible_history(HIST, "A", mode=SHARED)
    assert sum(s in shown for s in ("b1", "b2", "b3")) == 3


def test_B_can_see_MULTIPLE_of_As_turns():
    """Stated separately, because a bug that fixed one seat only would pass the
    test above. The arm is symmetric or it is not the arm."""
    shown = visible_history(HIST, "B", mode=SHARED)
    assert sum(s in shown for s in ("a1", "a2", "a3")) == 3


def test_the_seed_is_in_the_store_for_both():
    """Algorithm 1 initialises `C` before round 1; the seed is shared material,
    not partner material to be released."""
    for me in ("A", "B"):
        assert "s0" in visible_history(HIST, me, mode=SHARED)


# ─────────────────────────────────────────────────────────────────────────────
# 2 · ⛔⛔ THE BITE — these same checks must FAIL on the fallback path
# ─────────────────────────────────────────────────────────────────────────────

def test_the_red_proof_BITES_against_the_self_accumulation_path():
    """⛔⛔ IF THIS TEST EVER PASSES TRIVIALLY, THE FILE ABOVE IS DECORATION.

    Runs the discriminating assertions against `LIVE` — the exact path a silent
    fallback would take — and requires every one of them to FAIL. This is what
    makes the suite able to catch `mode="shared"` quietly routing to the
    asymmetric rule.
    """
    live_a = visible_history(HIST, "A", mode=LIVE)
    live_b = visible_history(HIST, "B", mode=LIVE)

    # (a) LIVE is NOT the full chronological store
    assert list(live_a) != [s for _sp, s in HIST]

    # (b) LIVE hands the two speakers DIFFERENT views
    assert live_a != live_b

    # (c) LIVE shows exactly ONE of the partner's turns, not three
    assert sum(s in live_a for s in ("b1", "b2", "b3")) == 1
    assert sum(s in live_b for s in ("a1", "a2", "a3")) == 1

    # (d) and the one it shows is the most recent
    assert "b3" in live_a and "b1" not in live_a


def test_shared_and_live_disagree_on_this_history():
    """The blunt instrument: same history, same speaker, different modes MUST
    produce different context. A mode that is not distinguishable from LIVE is
    not a second arm."""
    assert (visible_history(HIST, "A", mode=SHARED)
            != visible_history(HIST, "A", mode=LIVE))


def test_shared_and_cold_disagree_on_this_history():
    """COLD is own-chain-only. Shared is everything. If a wiring error routed
    shared to the baseline the run would compare a thing to itself."""
    assert (visible_history(HIST, "A", mode=SHARED)
            != visible_history(HIST, "A", mode=COLD))


def test_shared_shows_STRICTLY_MORE_than_live():
    """Direction matters. A shared store that showed *less* would be a truncation
    wearing the wrong name."""
    shared = visible_history(HIST, "A", mode=SHARED)
    live = visible_history(HIST, "A", mode=LIVE)
    assert len(shared) > len(live)
    assert set(live) <= set(shared)


# ─────────────────────────────────────────────────────────────────────────────
# 3 · edges that would otherwise fail silently
# ─────────────────────────────────────────────────────────────────────────────

def test_an_unknown_mode_RAISES_rather_than_defaulting():
    """⛔⛔ THE SILENT-FALLBACK BUG ITSELF, MADE IMPOSSIBLE.

    A typo'd mode string must not quietly take the `else` branch and run the
    asymmetric rule. This is the single assertion that would have caught the
    whole failure class at its source.
    """
    with pytest.raises(ValueError, match="mode"):
        visible_history(HIST, "A", mode="shraed")


def test_injection_still_lands_last_under_shared():
    """Injections are yoked identically into every condition; under shared they
    append to the store like any other turn."""
    shown = visible_history(HIST, "A", mode=SHARED, injected="x9")
    assert shown[-1] == "x9"
    assert list(shown[:-1]) == [s for _sp, s in HIST]


def test_empty_history_is_empty_under_shared_not_a_crash():
    assert visible_history([], "A", mode=SHARED) == ()


def test_shared_at_turn_zero_shows_only_the_seed():
    """⛔ The rule applies FROM TURN 0. Algorithm 1's `C⁽⁰⁾` is the seed and
    nothing else — an arm that showed more at turn 0 has invented history."""
    assert visible_history([(SEED_SPEAKER, "s0")], "A", mode=SHARED) == ("s0",)


def test_shared_keeps_duplicate_surfaces_rather_than_collapsing_them():
    """⛔ Append-only means append-only. De-duplicating would quietly change the
    force distribution the arm is measured on — the observable is a RATE over
    scenes, so dropping a repeat moves `force:ka` itself."""
    hist = [("A", "same"), ("B", "same"), ("A", "same")]
    assert list(visible_history(hist, "A", mode=SHARED)) == ["same"] * 3


# ─────────────────────────────────────────────────────────────────────────────
# 4 · ⛔⛔ END-TO-END THROUGH `exchange_two` — the WIRING, not the function
# ─────────────────────────────────────────────────────────────────────────────
# A correct `visible_history` proves nothing if the harness never routes the arm
# through it with the right mode. These run the real `exchange_two` and read what
# the speakers were ACTUALLY HANDED, rather than trusting the call site.

class Spy:
    """⭐ RECORDS WHAT IT ACTUALLY RECEIVED. A knob that silently no-ops returns
    'the mechanism holds' for the worst possible reason."""

    def __init__(self, label):
        self.label, self.seen = label, []

    def speak(self, history, turn):
        self.seen.append(tuple(history))
        return "%s%d" % (self.label, turn)


def _run(mode, turns=8):
    from act2_two_speaker import exchange_two
    a, b = Spy("A"), Spy("B")
    exchange_two(a, b, turns=turns, seed_history=["s0"], mode=mode)
    return a, b


def test_end_to_end_both_speakers_are_handed_the_partners_EARLIER_turns():
    """⛔⛔ THE ONE THAT MATTERS. If this passes while the arm is secretly
    self-accumulating, nothing else in this file protects the run."""
    a, b = _run(SHARED)
    assert sum(s.startswith("B") for s in a.seen[-1]) >= 2, (
        "speaker A never received more than one of B's turns — that is the "
        "asymmetric rule, not shared memory")
    assert sum(s.startswith("A") for s in b.seen[-1]) >= 2, (
        "speaker B never received more than one of A's turns")


def test_end_to_end_the_store_is_APPEND_ONLY():
    """Each successive view extends the previous one. ⛔ This is the property the
    asymmetric rule CANNOT satisfy — `own + last_other` reorders as it grows, so
    an earlier view is not a prefix of a later one."""
    a, _b = _run(SHARED)
    for earlier, later in zip(a.seen, a.seen[1:]):
        assert later[:len(earlier)] == earlier, \
            "the store was reordered or truncated between turns"


def test_end_to_end_append_only_FAILS_under_the_asymmetric_rule():
    """⛔ The bite, at the wiring level: the prefix property must NOT hold for
    LIVE. If it did, the test above would pass on a silent fallback."""
    a, _b = _run(LIVE)
    assert any(later[:len(earlier)] != earlier
               for earlier, later in zip(a.seen, a.seen[1:])), \
        "LIVE looked append-only — the discriminator above is decoration"


def test_end_to_end_shared_grows_by_exactly_one_turn_at_a_time():
    """No turn is dropped and none is duplicated into the store."""
    a, b = _run(SHARED)
    lengths = sorted(len(v) for v in a.seen + b.seen)
    assert lengths == list(range(1, len(lengths) + 1))


# ─────────────────────────────────────────────────────────────────────────────
# 5 · the aliasing trap, found by a mutation experiment that misfired
# ─────────────────────────────────────────────────────────────────────────────

def test_every_mode_constant_has_a_DISTINCT_value():
    """⛔⛔ FOUND THE HARD WAY. An attempt to fake the fallback bug by setting
    `SHARED = LIVE` did the OPPOSITE of what was intended: `visible_history`
    compares `mode == SHARED` first, so the alias routed **LIVE** into the shared
    branch. The asymmetric arm would have run shared memory while reporting
    itself as the control — the null and the treatment swapped, invisibly.

    ⭐ The module refuses this at import; this test asserts the refusal exists,
    because a guard nothing exercises is a guard nobody notices removing.
    """
    from act2_two_speaker import MODES
    assert len(set(MODES)) == len(MODES), (
        "two exchange modes share a value: %s" % (MODES,))
    assert SHARED not in (LIVE, COLD), "SHARED must not alias another arm"


def test_each_mode_produces_a_DISTINCT_view_on_the_same_history():
    """The stronger form: distinct *values* are necessary but not sufficient —
    two modes could still compute the same thing. On a history where they must
    differ, all three views are pairwise different."""
    views = {m: visible_history(HIST, "A", mode=m)
             for m in (LIVE, COLD, SHARED)}
    assert len(set(views.values())) == 3, (
        "two modes computed the same view: %r" % (views,))


# ─────────────────────────────────────────────────────────────────────────────
# 6 · ⛔⛔ THE ARM IS NAMED IN THE DATA — the two runs must not pool
# ─────────────────────────────────────────────────────────────────────────────
# The positive control and the drift run use DIFFERENT MEMORY MODELS under the
# same estimand. If a shared-memory transcript can be read as `live`, the two
# pool silently and the pooled number looks like an ordinary result. The caveat
# goes in the KEY, never in a note beside it.

def test_reading_a_shared_transcript_as_live_RAISES():
    from act2_drift import ARM_LIVE, assert_arm
    with pytest.raises(ValueError, match="different memory models"):
        assert_arm({"arm_mode": "shared"}, ARM_LIVE)


def test_reading_a_live_transcript_as_shared_RAISES():
    from act2_drift import ARM_SHARED, assert_arm
    with pytest.raises(ValueError, match="different memory models"):
        assert_arm({"arm_mode": "live"}, ARM_SHARED)


def test_a_legacy_transcript_without_arm_mode_is_LIVE_by_construction():
    """⛔ Not permissive — explicit. Files predating this key were written when
    SHARED did not exist, so `live` is the only thing they can be."""
    from act2_drift import ARM_LIVE, ARM_SHARED, assert_arm
    assert_arm({}, ARM_LIVE)                      # fine
    with pytest.raises(ValueError):
        assert_arm({}, ARM_SHARED)                # never silently upgraded


def test_each_arm_reads_its_own_transcript():
    from act2_drift import ARM_LIVE, ARM_SHARED, assert_arm
    assert_arm({"arm_mode": "shared"}, ARM_SHARED)
    assert_arm({"arm_mode": "live"}, ARM_LIVE)


def test_an_unknown_arm_RAISES_rather_than_defaulting():
    from act2_drift import assert_arm
    with pytest.raises(ValueError, match="unknown arm"):
        assert_arm({"arm_mode": "live"}, "shraed")


# ─────────────────────────────────────────────────────────────────────────────
# 7 · ⛔⛔ THE MATCHED NULL — AMENDMENT A to PREREG c0de41c7
# ─────────────────────────────────────────────────────────────────────────────
# The registered arm 2 ran `mode=YOKED` (own chain + the partner's single most
# recent turn) against a treatment arm running SHARED (the full store). That
# contrast varies TWO things — partner-adaptivity AND memory model — so a
# negative delta could be entirely "long context changes the force rate".
# PREREG_ACT2_DRIFT §4 rejects a solo control in exactly those words. The null
# must run the SAME memory model as the treatment; only adaptivity may differ.

class Recording:
    """A deaf partner that emits from a fixed list — the shape `Replay` has.

    ⛔ NOT `Replay` itself: that one parses each surface through the real
    grammar, so it needs valid Tlön. What is under test here is `exchange_two`'s
    STORE behaviour, which is a property of the harness and not of the partner —
    and `Replay` is deliberately deaf to `history`, so it behaves identically
    under any mode by construction.
    """

    def __init__(self, surfaces, label="B_rec"):
        self._s, self.label = list(surfaces), label
        self.backend = object()

    def speak(self, history, turn):      # noqa: ARG002 — deliberately deaf
        i = (turn - 1) // 2
        return self._s[i] if i < len(self._s) else None


def test_a_replayed_partner_under_SHARED_fills_the_store():
    """The matched null: the recording still ENTERS the store, so the live
    speaker reads the same shape of context it reads in the treatment arm."""
    from act2_two_speaker import exchange_two
    a = Spy("A")
    exchange_two(a, Recording(["r1", "r2", "r3", "r4"]),
                 turns=8, seed_history=["s0"], mode=SHARED)
    assert sum(s.startswith("r") for s in a.seen[-1]) >= 2, (
        "the yoked speaker saw at most one recorded turn — that is the "
        "ASYMMETRIC null, not a null matched to a shared-memory treatment")


def test_the_matched_null_DIFFERS_from_the_asymmetric_null():
    """⛔ The bite. Same recording, same speaker: the two nulls must not be the
    same object, or the amendment changed nothing."""
    from act2_two_speaker import exchange_two
    seen = {}
    for mode in (SHARED, LIVE):
        sp = Spy("A")
        exchange_two(sp, Recording(["r1", "r2", "r3", "r4"]),
                     turns=8, seed_history=["s0"], mode=mode)
        seen[mode] = sp.seen[-1]
    assert seen[SHARED] != seen[LIVE]
    assert len(seen[SHARED]) > len(seen[LIVE])


def test_the_asymmetric_null_shows_exactly_one_recorded_turn():
    """States the defect positively, so the amendment's reason stays legible."""
    from act2_two_speaker import exchange_two
    a = Spy("A")
    exchange_two(a, Recording(["r1", "r2", "r3", "r4"]),
                 turns=8, seed_history=["s0"], mode=LIVE)
    assert sum(s.startswith("r") for s in a.seen[-1]) == 1


def test_store_share_check_PASSES_on_a_shared_transcript():
    """⛔⛔ ASSERT THE ARM RAN, FROM ITS OWN DATA. `n_shown` is recorded per
    turn, so the transcript itself says how much context each turn received —
    no need to trust the call site."""
    from act2_two_speaker import exchange_two, store_was_shared
    log = exchange_two(Spy("A"), Recording(["r%d" % i for i in range(6)]),
                       turns=10, seed_history=["s0"], mode=SHARED)
    assert store_was_shared(log, turns=10) is True


def test_store_share_check_FAILS_on_an_asymmetric_transcript():
    """The same check on the old null must return False, or it is decoration."""
    from act2_two_speaker import exchange_two, store_was_shared
    log = exchange_two(Spy("A"), Recording(["r%d" % i for i in range(6)]),
                       turns=10, seed_history=["s0"], mode=LIVE)
    assert store_was_shared(log, turns=10) is False


# ─────────────────────────────────────────────────────────────────────────────
# 8 · ⛔⛔ THE MATCHED NULL RESTS ON `Replay` BEING MODE-AGNOSTIC — MEASURE IT
# ─────────────────────────────────────────────────────────────────────────────
# AMENDMENT A §5 recorded this as an ARGUMENT: "Replay ignores `history`, so it
# emits identically under SHARED and asymmetric." That was reasoned from reading
# the code. The entire validity of the matched null rests on it, so it is not
# allowed to stay an argument.
#
# ⛔ If Replay's emissions differed by mode, the two arms would no longer be
# yoked on what the partner says, and SHARED-LIVE minus SHARED-YOKED would stop
# subtracting the store-regression — the one thing the amendment exists to do.

def _real_surfaces(n=6):
    """⭐ REAL surfaces from a committed drift transcript, not synthesised ones.
    `Replay` parses every surface through the actual grammar, so a placeholder
    would test a parse failure rather than the replay mechanism."""
    import glob
    import json
    for f in sorted(glob.glob("runs/act2/drift/logs/*.json")):
        d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        got = [e["surface"] for e in d["conditions"]["live"]["log"]
               if e.get("valid") and e.get("surface")]
        if len(got) >= n:
            return got[:n]
    pytest.skip("no committed drift transcript with enough valid surfaces")


def _replay_emissions(mode, surfaces):
    from act2_two_speaker import Replay, exchange_two
    log = exchange_two(Spy("A"), Replay(surfaces, label="B_rec"),
                       turns=2 * len(surfaces), seed_history=["seed"],
                       mode=mode)
    return [e["proposal"] for e in log if e["speaker"] == "B_rec"]


def test_MEASURED_replay_emits_identically_under_shared_and_asymmetric():
    """⛔⛔ THE ARGUMENT, TURNED INTO A MEASUREMENT. Same recording, same turns,
    two memory models — the replayed partner must produce the same thing."""
    surfaces = _real_surfaces()
    shared = _replay_emissions(SHARED, surfaces)
    asym = _replay_emissions(LIVE, surfaces)
    assert shared, "Replay emitted nothing — this test would pass vacuously"
    assert len(shared) == len(asym) == len(surfaces)
    assert shared == asym, (
        "Replay's emissions depend on the memory model. The matched null is "
        "broken: the two arms are no longer yoked on what the partner says.")


def test_MEASURED_replay_emissions_match_the_recording_it_was_given():
    """⛔ Non-vacuity, stated separately: identical-but-empty, or
    identical-but-wrong, would satisfy the test above. This pins the content to
    the recording rather than merely to itself."""
    from tlon.act2 import schema_bridge as SB
    from tlon.grammar.parse import parse
    surfaces = _real_surfaces()
    expected = [SB.scene_to_proposal(parse(s)) for s in surfaces]
    assert _replay_emissions(SHARED, surfaces) == expected


def test_MEASURED_replay_is_deaf_to_the_history_it_is_handed():
    """The mechanism behind the mode-agnosticism, measured directly: hand the
    same Replay wildly different histories and it must not care."""
    from act2_two_speaker import Replay
    surfaces = _real_surfaces(3)
    a, b = Replay(surfaces), Replay(surfaces)
    assert a.speak((), 1) == b.speak(("x",) * 50, 1)
    assert a.speak(("one",), 3) == b.speak(tuple("abcdefghij"), 3)


# ─────────────────────────────────────────────────────────────────────────────
# 9 · ⛔⛔ HANDED IS NOT ATTENDED — the history window silently truncates
# ─────────────────────────────────────────────────────────────────────────────
# `LLMSpeaker.history_limit` defaults to 60 and `transcript_block` drops the
# OLDEST turns beyond it. At the registered TURNS=80 the shared store holds 81
# entries, so 26% of it never reaches the model: the arm would implement
# "shared store, last 60" rather than Algorithm 1's C.
#
# ⛔ The limit has never bound before — the asymmetric rule hands only ~41 at 80
# turns — so this is the first arm where it bites, and no prior result changes.
# `llm.py` says it plainly: changing the window "CHANGES WHAT D_ctx CAN SEE, so
# it is a pre-registration-adjacent decision, not a tuning knob." Which is why
# it is asserted rather than quietly raised.

def test_the_default_window_would_TRUNCATE_the_shared_store_at_80_turns():
    """States the defect as a measurement, so the fix cannot be mistaken for a
    preference."""
    from tlon.act2.llm import LLMSpeaker, transcript_block
    hist = ["t%d" % i for i in range(81)]
    kept = transcript_block(hist, LLMSpeaker.history_limit).strip().split("\n")
    assert len(kept) == 60
    assert "t0" not in kept[0], "the OLDEST turns are the ones dropped"


def test_store_was_shared_FAILS_when_the_model_could_not_attend_to_it():
    """⛔⛔ A CHECK ON WHAT WAS HANDED IS NOT A CHECK ON WHAT WAS USED. Given the
    window, `store_was_shared` must refuse a transcript whose store outgrew it."""
    from act2_two_speaker import exchange_two, store_was_shared
    log = exchange_two(Spy("A"), Recording(["r%d" % i for i in range(40)]),
                       turns=80, seed_history=["s0"], mode=SHARED)
    assert store_was_shared(log, turns=80) is True          # handed in full
    assert store_was_shared(log, turns=80, attended_limit=60) is False
    assert store_was_shared(log, turns=80, attended_limit=200) is True


def test_the_attended_check_does_not_fire_when_the_window_is_wide_enough():
    """Non-vacuity: the check must be able to PASS, or it just blocks the run."""
    from act2_two_speaker import exchange_two, store_was_shared
    log = exchange_two(Spy("A"), Recording(["r%d" % i for i in range(6)]),
                       turns=12, seed_history=["s0"], mode=SHARED)
    assert store_was_shared(log, turns=12, attended_limit=60) is True
