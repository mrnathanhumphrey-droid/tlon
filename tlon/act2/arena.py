"""THE ARENA — the three arms, the epoch loop, the covariates. PREREG §3.4, §4.

⛔⛔ THE CONTROL IS THE POINT OF THIS MODULE, NOT A SIDE ARM. `interacting` is
three lines different from `yoked`, and that difference -- whether the partner is
ADAPTING TO YOU -- is the entire attributable claim of Act 2.

    interacting   A and B both live, shared history
    yoked         A live against a frozen transcript; B live against a
                  DIFFERENT frozen transcript  (PRIMARY control, §4)
    solo          each speaker alone, no partner turns  (SECONDARY control)

⛔⛔ THE TWO FROZEN PARTNERS MUST DIFFER, AND THE PREREG DOES NOT SAY SO.
§4 fixes "a pre-recorded, non-adaptive partner transcript" and leaves open
whether A and B get the SAME one. They must not. Yoked to one shared transcript,
both speakers adapt toward one attractor and therefore toward each other -- the
control would then contain a synthetic version of the very convergence the
interacting arm is supposed to have exclusively, `C(control)` would rise, and
`ΔC` would be biased toward zero. A control that contains the treatment cannot
attribute anything. Recorded as DEVIATIONS_ACT2 D1; enforced below by raising.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Sequence

from ..grammar.canon import canon_json
from ..grammar.denote import project
from ..grammar.parse import Scene
from ..product import schema as PS
from ..product.compat import impression

from .axes import BASELINE, Axis
from .ledger import SealedTranscript
from .probes import Battery

ARMS = ("interacting", "yoked", "solo")
HORIZON = 200
EPOCH_EVERY = 25


def projected_form(scene: Scene) -> str:
    """π(scene) as its canonical JSON — the pre-image of the impression.

    ⛔ `impression(s) == impression(t)` iff `projected_form(s) ==
    projected_form(t)`, because the impression is exactly the digest of this
    string. Storing the pre-image keeps the primary estimator identical while
    leaving the secondary graded one computable from the same record.
    """
    return canon_json(project(scene))


class ArenaError(RuntimeError):
    pass


@dataclass(frozen=True)
class EpochRecord:
    """What a model's meaning↔form mapping looked like at one epoch."""
    epoch: int
    turn: int
    #: model -> probe id -> the PROJECTED CANONICAL FORM of what it produced
    #: (None = refused). ⭐ The pre-image of the impression, not the digest:
    #: string equality on it IS impression equality (the impression is its
    #: hash), and the secondary graded estimator can be computed from the same
    #: stored object. One artefact, both pre-registered estimators, no risk of
    #: the two disagreeing about what was measured.
    production: dict[str, dict[str, str | None]]
    #: model -> probe id -> index chosen
    comprehension: dict[str, dict[str, int]]
    covariates: dict[str, float] = field(default_factory=dict)


@dataclass
class RunResult:
    run_id: str
    arm: str
    seed: int
    axis: Axis
    battery: str
    epochs: tuple[EpochRecord, ...]
    transcript: SealedTranscript
    models: tuple[str, str]
    #: ⭐ WHICH INDEPENDENT REPEAT OF THIS CELL THIS IS. The MDE is a sign-flip
    #: permutation over WITHIN-CONTROL replicate differences (PREREG §5.1), and
    #: a difference needs a facet that differs -- so replicate is recorded on
    #: every run, not just on control ones.
    replicate: int = 0


def _run_id(arm: str, seed: int, axis: Axis, battery: str) -> str:
    blob = f"{arm}|{seed}|{axis.key}:{axis.setting}|{battery}"
    return hashlib.blake2b(blob.encode("utf-8"), digest_size=6).hexdigest()


# ── one turn, through the product's own validity gate ─────────────────────
def _emit(speaker, history: Sequence[str], turn: int, axis: Axis,
          retries: int = 1) -> tuple[Scene | None, str | None, int]:
    """Returns (scene, surface, attempts). ⛔ The speaker proposes; the GATE
    decides -- the same boundary the product uses, reused so a transcript can
    never contain an utterance the grammar would refuse."""
    attempts = 0
    for _ in range(retries + 1):
        attempts += 1
        proposal = speaker.speak(tuple(history), turn)
        if proposal is None:
            return None, None, attempts
        if "replay" in proposal:                       # a frozen partner's turn
            surface = proposal["replay"]
            from ..grammar.parse import ParseError, parse
            try:
                return parse(surface), surface, attempts
            except ParseError as exc:
                raise ArenaError(
                    f"a frozen transcript contains an illegal utterance "
                    f"({exc}). It was recorded through the gate; if it no "
                    "longer parses the lexicon moved under it.") from exc
        try:
            scene, surface, _ = PS.validate(proposal)
        except PS.ProposalError:
            continue
        if not axis.permits(scene.force, scene.node.modal):
            continue                                   # axis restriction
        return scene, surface, attempts
    return None, None, attempts


def _covariates(scenes: Sequence[Scene], attempts: Sequence[int],
                emitted: int, offered: int) -> dict[str, float]:
    """F4's pre-committed covariates (PREREG §2). ⭐ Logged EVERY epoch whether
    or not anyone expects them to matter -- a covariate computed after seeing
    the result is a covariate chosen to explain it.

    ⛔⛔ COUNTED OVER LIVE SPEAKERS ONLY, AND AS A RATIO. Two defects lived here.
    A raw distinct-root COUNT is not comparable across arms, because the yoked
    arm runs two lanes and pooled twice as many turns -- so the control looked
    twice as "diverse" and F4 fired on every cell including the one with no
    drift at all. And a frozen partner's REPLAYED turns were pooled in, so part
    of the control's diversity was the pre-recorded transcript's rather than the
    speaker's. §2 says type/token over R; a count is not that. Live-only,
    ratio-valued, the token counts match across arms exactly.
    """
    if not scenes:
        return {"valid_rate": 0.0, "retry_rate": 0.0, "distinct_roots": 0.0,
                "root_ttr": 0.0, "mean_nodes": 0.0, "mean_edges": 0.0}

    def walk(n):
        yield n
        for _, c in n.edges:
            yield from walk(c)

    roots, nodes, edges = set(), 0, 0
    for s in scenes:
        for n in walk(s.node):
            roots.add(n.root)
            nodes += 1
            edges += len(n.edges)
    return {
        "valid_rate": emitted / offered if offered else 0.0,
        "retry_rate": (sum(attempts) - len(attempts)) / len(attempts) if attempts else 0.0,
        "distinct_roots": float(len(roots)),
        "root_ttr": len(roots) / len(scenes),      # ⭐ the pre-registered form
        "mean_nodes": nodes / len(scenes),
        "mean_edges": edges / nodes if nodes else 0.0,
    }


# ── probing: a BRANCHED context that is thrown away ───────────────────────
def _probe(speaker, battery: Battery, history: Sequence[str]) -> tuple[dict, dict]:
    """⛔⛔ THE HISTORY IS PASSED AS A TUPLE, AND THAT IS THE MECHANISM, NOT A
    STYLE CHOICE (PREREG §3.4). A probe must be answered WITH the conversation in
    context -- in a prompted pass the context window is the only thing that can
    have changed, so a clean-context probe returns epoch-0 behaviour by
    construction and `D_ctx ≡ 0` for a reason unrelated to the claim. But probe
    exchanges must never BECOME conversation. An immutable history gives both:
    the speaker can read it and cannot append to it."""
    ctx = tuple(history)
    prod: dict[str, str | None] = {}
    for p in battery.production:
        proposal = speaker.render(p.stimulus, ctx)
        try:
            scene, _, _ = PS.validate(proposal) if proposal else (None, None, None)
        except PS.ProposalError:
            scene = None
        prod[p.pid] = projected_form(scene) if scene is not None else None
    comp: dict[str, int] = {}
    for c in battery.comprehension:
        comp[c.pid] = int(speaker.choose(c.surface, c.options, ctx))
    return prod, comp


# ── the arms ──────────────────────────────────────────────────────────────
def run(arm: str, *, speaker_a, speaker_b, battery: Battery, seed: int,
        axis: Axis = BASELINE, frozen_a: Sequence[str] | None = None,
        frozen_b: Sequence[str] | None = None, turns: int = HORIZON,
        epoch_every: int = EPOCH_EVERY, replicate: int = 0) -> RunResult:
    """One paired run. Every arm measures BOTH models, so items pair across arms."""
    if arm not in ARMS:
        raise ArenaError(f"arm={arm!r} must be one of {ARMS}")
    axis.check_lexicon()

    from .speaker import FrozenPartner

    if arm == "yoked":
        if frozen_a is None or frozen_b is None:
            raise ArenaError(
                "the yoked arm needs a frozen transcript for EACH live speaker.")
        if list(frozen_a) == list(frozen_b):
            raise ArenaError(
                "the two frozen partners are the SAME transcript. Both speakers "
                "would then adapt toward one attractor and therefore toward each "
                "other -- the control would contain a synthetic copy of the very "
                "convergence the interacting arm is supposed to have "
                "exclusively, and ΔC would be biased toward zero. A control that "
                "contains the treatment attributes nothing. (DEVIATIONS_ACT2 D1)")

    # ⛔ WHO SPEAKS and WHO IS PROBED are DIFFERENT LISTS, and conflating them
    # was a real bug: in the interacting arm B is A's partner, so a single
    # (live, partner) lane probes only A and `C` -- agreement between A and B --
    # becomes uncomputable. Both models are measured in EVERY arm, which is also
    # what keeps the item sets identical across arms so they can be paired.
    if arm == "interacting":
        shared: list[str] = []
        turn_lanes = [(speaker_a, speaker_b, shared)]
        probe_lanes = [(speaker_a, shared), (speaker_b, shared)]
    elif arm == "yoked":
        ha, hb = [], []
        turn_lanes = [(speaker_a, FrozenPartner("frozen_a", frozen_a), ha),
                      (speaker_b, FrozenPartner("frozen_b", frozen_b), hb)]
        probe_lanes = [(speaker_a, ha), (speaker_b, hb)]
    else:
        ha, hb = [], []
        turn_lanes = [(speaker_a, None, ha), (speaker_b, None, hb)]
        probe_lanes = [(speaker_a, ha), (speaker_b, hb)]

    all_surfaces: list[str] = []
    all_imps: list[str] = []
    all_scenes: list[Scene] = []
    all_attempts: list[int] = []
    total_offered = total_emitted = 0
    scenes_since: list[Scene] = []
    attempts_since: list[int] = []
    offered = emitted = 0
    epochs: list[EpochRecord] = []

    def take_epoch(turn: int) -> None:
        nonlocal scenes_since, attempts_since, offered, emitted
        prod, comp = {}, {}
        for live, hist in probe_lanes:
            p, c = _probe(live, battery, hist)
            prod[live.name], comp[live.name] = p, c
        epochs.append(EpochRecord(
            epoch=len(epochs), turn=turn, production=prod, comprehension=comp,
            covariates=_covariates(scenes_since, attempts_since,
                                   emitted, offered)))
        scenes_since, attempts_since = [], []
        offered = emitted = 0

    take_epoch(0)
    for turn in range(1, turns + 1):
        for live, partner, hist in turn_lanes:
            # The live speaker takes odd turns and its partner (if any) the
            # even ones, in EVERY arm -- so turn count and history shape are
            # held constant and the only thing the yoked arm removes is whether
            # that partner is adapting to you.
            who = live if turn % 2 else partner
            if who is None:
                continue
            # ⛔ A frozen partner is REPLAYING, not speaking. Its turns belong in
            # the history (the live speaker must see them) and NOT in the
            # covariates, or part of the control's measured diversity would be
            # the pre-recorded transcript's rather than the speaker's.
            is_live = who is live
            if is_live:
                offered += 1
                total_offered += 1
            scene, surface, n = _emit(who, hist, turn, axis)
            if is_live:
                attempts_since.append(n)
                all_attempts.append(n)
            if surface is None:
                continue
            hist.append(surface)
            all_surfaces.append(surface)
            all_imps.append(impression(scene))
            if not is_live:
                continue
            emitted += 1
            total_emitted += 1
            scenes_since.append(scene)
            all_scenes.append(scene)
        if turn % epoch_every == 0:
            take_epoch(turn)

    run_id = _run_id(arm, seed, axis, battery.digest)
    return RunResult(
        run_id=run_id, arm=arm, seed=seed, axis=axis, battery=battery.digest,
        epochs=tuple(epochs), models=(speaker_a.name, speaker_b.name),
        replicate=replicate,
        transcript=SealedTranscript(
            run_id=run_id, _turns=tuple(all_surfaces),
            _impressions=tuple(all_imps),
            _stats=_covariates(all_scenes, all_attempts,
                               total_emitted, total_offered)))


def record_frozen_transcript(speaker, *, turns: int = HORIZON,
                             axis: Axis = BASELINE) -> tuple[str, ...]:
    """Pre-record a non-adaptive partner. ⭐ Recorded THROUGH THE GATE, so a
    frozen transcript is legal Tlon by exactly the standard a live turn is."""
    hist: list[str] = []
    for turn in range(1, turns + 1):
        _, surface, _ = _emit(speaker, hist, turn, axis)
        if surface is not None:
            hist.append(surface)
    if not hist:
        raise ArenaError(
            "the recorded transcript is empty -- a frozen partner that says "
            "nothing is silence, and the yoked arm would silently become solo.")
    return tuple(hist)
