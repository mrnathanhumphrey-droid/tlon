"""THE ASYMMETRIC TWO-SPEAKER HARNESS — the first one that can be what it claims.

Spec: docs/SPEC_TWO_SPEAKER_DRIFT_2026_08_30.md §4
Red-proof: tests/test_two_speaker_harness.py (written BEFORE this module)

⛔⛔ TWO FAULTS IN THE OLD HARNESS, BOTH LOAD-BEARING, BOTH INVISIBLE:

1. `act2_exchange_probe.exchange()` was given ONE `LocalBackend` and two labels,
   so speaker A and speaker B were the SAME ADAPTER. Every "interacting"
   exchange in Act 2 was one impression talking to itself, and identical weights
   make the two MARGINAL distributions coincide — so a distance between marginals
   was mechanically zero, whatever the observable or the regime.
   ⛔ CORRECTED 2026-08-31: the reason is NOT that identical things cannot
   converge. They never hold each other's words, so they are two individuated
   trajectories that could in principle converge; the statistic is blind to it. ⇒ `_assert_two()` below REFUSES that arrangement
   instead of trusting it.

2. Its `hist` was ONE SHARED LIST with no speaker attribution, so the only two
   regimes expressible were "everyone sees everything" (full accumulation) and
   "everyone sees one turn" (window-1). Both are wrong:

   - Full accumulation retains the PARTNER'S past turns. That is
     object-persistence, and the ontology forbids it — the discourse spec says
     so twice, and the grammar says *"There is no persisting moon."* A retained
     past utterance is a thing that endures unperceived and can be pointed at
     again. That is a noun, and Tlön is nounless BECAUSE nothing persists so.
   - Window-1 denies a speaker its OWN memory, which is not required by the
     ontology at all: your memory is a present state of yours, not the
     persistence of the object. The spec already flags depth-1 as
     artifact-producing (*"the model is a deterministic echo"*).

⭐ THE RULE, THEREFORE, IS ASYMMETRIC:

      YOUR OWN CHAIN ACCUMULATES.   THE PARTNER PROVOKES AND IS RELEASED.

   You may hold what you said. You may not hold what they said. The coins
   ceased to exist when they were lost.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

#: Surfaces that seeded the exchange belong to nobody. They are PARTNER material
#: for every speaker — you cannot have remembered what you never said — so only
#: the most recent one is ever visible, from turn 0, including into the seed.
SEED_SPEAKER = "seed"

LIVE = "live"       #: own chain + the partner's single most recent turn
COLD = "cold"       #: own chain only — no interlocutor at all (the baseline)
YOKED = "yoked"     #: same visibility as LIVE; the partner is a recording

#: ⛔⛔ SHARED DELIBERATELY VIOLATES THE ASYMMETRIC RULE ABOVE, AND THAT IS ITS
#: ENTIRE PURPOSE. One append-only store; **both speakers read all of it**, in
#: the order it happened. This is Parfenova Algorithm 1's `C`, imported wholesale
#: — the memory model that produces strong convergence in natural language.
#:
#: ⚠️ It is ontologically wrong for Tlön, on this module's own argument: a
#: retained past utterance is a thing that endures unperceived and can be pointed
#: at again, which is a noun, in a nounless language. That is not an oversight
#: being tolerated. `PREREG_POSITIVE_CONTROL_KA` `c0de41c7` asks whether the A1
#: instrument can detect convergence **at all** on real data, and answering it
#: requires a memory model already known to produce convergence. **SHARED is the
#: positive control's arm and belongs to no other run** — it is not a candidate
#: for how Tlön speakers should converse, and a result from it says nothing about
#: the asymmetric regime.
#:
#: ⛔ Red-proof: `tests/test_shared_memory_arm.py`, written BEFORE this and
#: demonstrated to FAIL (10 of 15) against `SHARED = LIVE`, the silent fallback.
SHARED = "shared"

#: ⛔⛔ EVERY VALID MODE, ENUMERATED — so an unrecognised one RAISES instead of
#: taking an `else` branch. The old code routed anything-not-COLD to the
#: asymmetric rule, which meant a typo'd `"shraed"` would have run
#: self-accumulation, produced a null, and been reported as *"Tlön does not
#: converge even under shared memory."* A mechanism that did nothing and a
#: mechanism that ran and found nothing leave the same trace.
MODES = (LIVE, COLD, YOKED, SHARED)

if len(set(MODES)) != len(MODES):
    # ⛔⛔ TWO MODE NAMES SHARING ONE VALUE, REFUSED AT IMPORT. Found by a
    # mutation experiment that set `SHARED = LIVE` to fake the fallback bug: it
    # did the OPPOSITE of what was intended. `visible_history` tests
    # `mode == SHARED` first, so aliasing the constants routed *LIVE* into the
    # shared branch — the asymmetric arm would have silently run shared memory,
    # and the run's own null control would have been the treatment.
    # ⭐ Same shape as `_assert_two`: one thing wearing two labels. Refused, not
    # warned. A raise at import cannot be skipped by a code path that is not
    # exercised.
    raise RuntimeError(
        "two exchange modes share one value: %s. The mode constants are "
        "compared by equality, so an alias silently routes one arm into "
        "another's branch — and each arm would then be measuring the other."
        % (MODES,))


@dataclass(frozen=True)
class InjectionPlan:
    """Pseudo-random fresh material, at pseudo-random turns, from a fixed seed.

    ⛔⛔ IT MUST BE YOKED IDENTICALLY INTO EVERY CONDITION. An injection that
    lands in LIVE but not in the null *is* the difference being measured. Build
    ONE plan per pair and pass the same object to COLD, YOKED and LIVE.

    ⛔ Content neutrality is a separate obligation the plan cannot enforce:
    material drawn from the training corpus drags every distribution toward the
    corpus baseline and would manufacture apparent convergence. Verify the pool
    on the panel axes before use — see `injection_neutrality()`.
    """

    seed: int
    turns: tuple[int, ...]
    surfaces: tuple[str, ...]

    def at(self, turn: int) -> str | None:
        try:
            return self.surfaces[self.turns.index(turn)]
        except ValueError:
            return None


def plan_injections(*, seed: int, turns: int, n: int, pool) -> InjectionPlan:
    pool = tuple(pool)
    if not pool:
        raise ValueError("an empty injection pool would silently inject nothing "
                         "— a no-op that looks like a running mechanism")
    if n > turns:
        raise ValueError("cannot inject at %d of %d turns" % (n, turns))
    rng = random.Random(seed)
    ts = tuple(sorted(rng.sample(range(turns), n)))
    return InjectionPlan(seed=seed, turns=ts,
                         surfaces=tuple(rng.choice(pool) for _ in ts))


def _last_other(hist, me) -> tuple:
    """The single most recent surface NOT said by `me`, or nothing."""
    for speaker, surface in reversed(hist):
        if speaker != me:
            return (surface,)
    return ()


def visible_history(hist, me: str, *, mode: str = LIVE,
                    injected: str | None = None) -> tuple:
    """What `me` is handed, given an attributed history.

    `hist` is a list of `(speaker, surface)`. ⭐ The attribution is the whole
    point: without it the two correct regimes are inexpressible.

    ⛔ The rule applies FROM TURN 0, including into the seed history. A version
    that truncated only after the seed had accumulated would silently give early
    turns full context, and the run would be uninterpretable in exactly the
    direction that flatters the hypothesis. (Carried from the window-1 guard.)
    """
    if mode not in MODES:
        # ⛔⛔ RAISE, NEVER DEFAULT. See MODES: an unrecognised mode silently
        # taking the asymmetric branch is how a shared-memory arm becomes a
        # self-accumulation arm that reports a null.
        raise ValueError("unknown mode %r; valid modes are %s"
                         % (mode, ", ".join(MODES)))
    if mode == SHARED:
        # ⛔ Everything, in the order it happened, identically for both speakers
        # — `me` is deliberately unused. Not `own + others`: that would reorder
        # the store into own-then-partner and stop being Algorithm 1's `C`.
        # No de-duplication: the observable is a RATE over scenes, so collapsing
        # a repeated surface would move `force:ka` itself.
        shown = tuple(s for _speaker, s in hist)
    else:
        own = tuple(s for speaker, s in hist if speaker == me)
        if mode == COLD:
            # No interlocutor. The seed provokes the first turn only — a speaker
            # provoked by nothing is not a self-accumulator, it is a cold start.
            shown = own if own else _last_other(hist, me)
        else:
            shown = own + _last_other(hist, me)
    return shown + (injected,) if injected is not None else shown


def _assert_two(a, b) -> None:
    """⛔⛔ REFUSE ONE IMPRESSION WEARING TWO LABELS.

    This is not defensive coding. It is the exact arrangement that produced
    every prior Act 2 'interaction', and it looked correct the whole time.
    """
    if a is b:
        raise ValueError(
            "speaker A and speaker B are the same object — that is one speaker "
            "and a mirror: their marginals coincide, so any distance between "
            "marginals is mechanically zero")
    ba, bb = getattr(a, "backend", None), getattr(b, "backend", None)
    if ba is not None and ba is bb:
        raise ValueError(
            "both speakers share one backend — this is the fault that made "
            "every prior coupling measurement mechanically zero; load two "
            "distinct adapters")


def _label(sp, fallback: str) -> str:
    """⛔ `LLMSpeaker` calls it `name`, not `label`.

    Falling through to the positional fallback would give BOTH speakers the
    label of whichever seat they sat in, and speaker-attribution is the entire
    mechanism — a mis-attributed history silently restores the shared-list
    behaviour this module exists to remove.
    """
    for attr in ("label", "name"):
        v = getattr(sp, attr, None)
        if v:
            return str(v)
    return fallback


def exchange_two(a, b, *, turns: int, seed_history, injections=None,
                 mode: str = LIVE, validate=None):
    """Alternating turns between TWO speakers under the asymmetric rule."""
    _assert_two(a, b)
    hist = [(SEED_SPEAKER, s) for s in seed_history]
    log = []
    for t in range(turns):
        sp = a if t % 2 == 0 else b
        me = _label(sp, "A" if t % 2 == 0 else "B")
        shown = visible_history(hist, me, mode=mode,
                                injected=injections.at(t) if injections else None)
        proposal = sp.speak(shown, t + 1)
        entry = {"turn": t, "speaker": me, "proposal": proposal,
                 "valid": False, "surface": None,
                 "injected": bool(injections and injections.at(t) is not None),
                 "n_shown": len(shown)}
        if proposal is not None:
            try:
                surface = validate(proposal) if validate else proposal
                entry.update(valid=True, surface=surface)
                hist.append((me, surface))
            except Exception:                                      # noqa: BLE001
                pass
        log.append(entry)
    return log


def solo(speaker, *, turns: int, seed_history, injections=None, validate=None):
    """The COLD baseline: one speaker, its own chain, no interlocutor.

    ⭐ Both speakers of a pair are run through this with the SAME seed history
    and the SAME injection plan, so the distance between the two solo
    transcripts is where they START — before any exchange. That is the
    baseline, NOT the null. The null is YOKED.
    """
    me = _label(speaker, "A")
    hist = [(SEED_SPEAKER, s) for s in seed_history]
    log = []
    for t in range(turns):
        shown = visible_history(hist, me, mode=COLD,
                                injected=injections.at(t) if injections else None)
        proposal = speaker.speak(shown, t + 1)
        entry = {"turn": t, "speaker": me, "proposal": proposal,
                 "valid": False, "surface": None,
                 "injected": bool(injections and injections.at(t) is not None),
                 "n_shown": len(shown)}
        if proposal is not None:
            try:
                surface = validate(proposal) if validate else proposal
                entry.update(valid=True, surface=surface)
                hist.append((me, surface))
            except Exception:                                      # noqa: BLE001
                pass
        log.append(entry)
    return log


class Replay:
    """A partner that emits a RECORDING and cannot adapt back — the YOKED null.

    ⭐ WHY THIS AND NOT 'TWO ADAPTERS THAT NEVER INTERACT': a never-interact pair
    receives DIFFERENT INPUT from the live pair, so a distance change confounds
    mutuality with what each speaker was given. Replay hands the identical
    partner turns while removing the partner's ability to respond — input held,
    mutuality removed.

    ⚠️ KNOWN LIMIT, STATED BEFORE THE RUN: once the live speaker's own outputs
    diverge from its LIVE trajectory, its accumulated self-chain differs, so
    "identical input" holds for the PARTNER STREAM ONLY. The yoke is exact on
    what the partner says and partial thereafter.
    """

    def __init__(self, surfaces, label: str = "B"):
        self._s = list(surfaces)
        self.label = label
        self.backend = object()          # never shared: it is not a model

    def speak(self, history, turn):      # noqa: ARG002 — deliberately deaf
        i = (turn - 1) // 2
        if i >= len(self._s):
            return None
        # ⛔⛔ MUST RETURN A PROPOSAL, NOT A SURFACE. The probe validates every
        # turn with `PS.validate`, which takes a proposal dict. Returning the
        # raw surface made EVERY replayed turn invalid, so it never entered
        # `hist`, so the live speaker fell back to the seed surface and heard
        # the SAME provocation on every turn. YOKED was silently "A talking to
        # a stale seed" rather than "A talking to a recording of B" — which
        # turns LIVE − YOKED into "partner present vs absent" instead of
        # "partner responsive vs not", the exact confound the yoked null exists
        # to remove. Caught by a smoke test; it would have produced a large,
        # clean, entirely spurious coupling signal.
        from tlon.act2 import schema_bridge as SB
        from tlon.grammar.parse import parse
        return SB.scene_to_proposal(parse(self._s[i]))


def store_was_shared(log, *, turns=None, threshold=0.75,
                     attended_limit=None) -> bool:
    """⛔⛔ DID THE ARM ACTUALLY RUN SHARED? ASKED OF THE TRANSCRIPT, NOT THE
    CALL SITE.

    `exchange_two` records `n_shown` per turn — how much context that turn was
    handed. Under SHARED it is the whole store (seed + every valid turn so far);
    under the asymmetric rule it is roughly the speaker's own half plus one. So
    the transcript itself states which memory model produced it, and no one has
    to trust the flag that was passed.

    ⭐ This is the guard the drift run did not have, in the form it needed: the
    arm that silently self-accumulates and the arm that ran and found nothing
    leave the same *result*, but they do not leave the same `n_shown`.

    `turns` is accepted for call-site readability and deliberately unused — the
    denominator comes from the VALID turns actually in the log, because invalid
    turns never enter the store and would otherwise make a healthy shared arm
    look short.
    """
    shown = [e.get("n_shown", 0) for e in log]
    if not shown:
        return False
    n_valid = sum(1 for e in log if e.get("valid"))
    if attended_limit is not None and max(shown) > attended_limit:
        # ⛔⛔ HANDED IS NOT ATTENDED. `LLMSpeaker.history_limit` drops the
        # OLDEST turns beyond the window, so a store larger than the window
        # reaches the model with its head missing. `n_shown` records what the
        # harness handed over; this is the only place that asks whether the
        # model could actually read it. Without it the check passes on an arm
        # running "shared store, last N" — a different memory model wearing the
        # right name.
        return False
    return max(shown) >= threshold * (n_valid + 1)


def measurable_turns(log):
    """⛔⛔ THE PRIMARY DEFENCE AGAINST A BIASED INJECTION POOL: never measure a
    turn the pool was visible for.

    A pool that pulls both speakers toward itself manufactures apparent
    convergence. Neutrality checking (`act2_injection_gate.py`) reduces that
    risk; EXCLUSION removes it from the measured surfaces entirely, and the two
    are complementary — the gate can only bound a bias it can see on the panel
    axes, whereas exclusion drops the contaminated turns whatever the bias is.

    ⭐ AND THE INJECTION DOES NOT PERSIST. `visible_history()` appends it to what
    is SHOWN, never to `hist`, so an injected surface provokes exactly one turn
    and is then gone — the same provoke-and-release rule the partner's turns
    obey. That is what makes turn-level exclusion sufficient rather than
    cosmetic: there is no injected material sitting in anybody's self-chain.
    """
    return [e for e in log if e.get("valid") and not e.get("injected")]


def injection_neutrality(pool, panel, speaker_scenes):
    """⛔ Is the injection pool a THIRD SPEAKER?

    Returns, per panel observable, the pool's value beside each speaker's, so a
    pool whose panel values sit outside both speakers can be rejected BEFORE it
    manufactures convergence by dragging both toward itself.
    """
    out = {}
    for name, fn in panel.items():
        out[name] = {"pool": fn(pool),
                     "speakers": [fn(s) for s in speaker_scenes]}
    return out
