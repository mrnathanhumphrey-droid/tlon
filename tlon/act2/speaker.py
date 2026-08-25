"""SPEAKERS — the swap point, and the synthetic ground truth that validates the
instrument before it is ever pointed at a real model.

⛔⛔ AN OBSERVABLE THAT HAS NEVER BEEN SHOWN A KNOWN QUANTITY IS NOT AN
INSTRUMENT. Before any hosted model speaks a word of Tlon, `D` and `C` must be
demonstrated on speakers whose drift and convergence are known BY CONSTRUCTION:

    StableSpeaker       codebook never changes          -> D = 0
    WanderingSpeaker    codebook mutates, ignores you   -> D > 0, C flat
    ImitatingSpeaker    codebook adopts what it hears   -> C up when paired live
    DegeneratingSpeaker collapses toward one root       -> D high for the WRONG
                                                          reason; F4 must fire

⭐ THE FOURTH ONE IS THE POINT. A pair that collapses into repetition produces a
large `D` that looks exactly like a private language and is the opposite of one.
That is the confabulated drift the falsifier is built to fire on, and here it is
manufactured on purpose so the falsifier can be shown catching it.

⭐ THE SYNTHETIC MODEL OF MEANING. A speaker holds a CODEBOOK: concept -> root.
Concepts are cycled in a fixed shared order, so a listener knows which concept a
turn was about without any side channel -- the synthetic stand-in for "these two
are talking about the same things in the same order". Drift is the codebook
changing; convergence is two codebooks becoming one.
"""
from __future__ import annotations

import hashlib
import random
from typing import Protocol, Sequence

from ..grammar import classes as C
from ..grammar.parse import ParseError, parse

N_CONCEPTS = 12


class Speaker(Protocol):
    """⭐ THE SWAP POINT. A hosted or fine-tuned model implements these three and
    the whole harness runs on it unchanged -- the same move `Proposer` makes in
    the product."""
    name: str

    def speak(self, history: Sequence[str], turn: int) -> dict | None:
        """A proposal for this turn, or None to pass. NEVER a rendered surface:
        the arena validates, so nothing here can put an illegal utterance into a
        transcript."""

    def render(self, stimulus: str, history: Sequence[str]) -> dict | None:
        """PRODUCTION PROBE. ⛔ `history` is not decoration -- see PREREG §0.3."""

    def choose(self, surface: str, options: Sequence[str],
               history: Sequence[str]) -> int:
        """COMPREHENSION PROBE. Forced choice; no free text, so no judge."""


def _h(text: str) -> int:
    """⛔ NOT `hash()`. Python's string hash is salted per process, so a battery
    scored today and the same battery scored tomorrow would disagree for a
    reason that has nothing to do with drift."""
    return int.from_bytes(hashlib.blake2b(text.encode("utf-8"),
                                          digest_size=8).digest(), "big")


def concept_of(text: str) -> int:
    return _h(text) % N_CONCEPTS


class SyntheticSpeaker:
    """Base for the ground-truth speakers. Deterministic given its seed."""

    #: subclasses set this; it is what makes each one's ground truth known
    kind = "synthetic"

    def __init__(self, name: str, seed: int, *, invalid_rate: float = 0.0):
        self.name = name
        self.seed = seed
        self.invalid_rate = invalid_rate
        self._roots = sorted(C.load()["classes"]["R"])
        rng = random.Random(seed)
        self.codebook: list[str] = [rng.choice(self._roots)
                                    for _ in range(N_CONCEPTS)]
        self.codebook_0 = list(self.codebook)
        self._rng = random.Random(seed ^ 0x5EED)

    # -- the three protocol methods -------------------------------------
    def speak(self, history: Sequence[str], turn: int) -> dict | None:
        self._adapt(history, turn)
        if self._rng.random() < self.invalid_rate:
            # ⭐ A deliberately illegal proposal, so the arena's retry path and
            # the validity covariates are exercised rather than assumed.
            return {"node": {"root": "NOT-A-ROOT"}, "force": "ka",
                    "refused_objects": [], "note": ""}
        root = self.codebook[turn % N_CONCEPTS]
        return {"node": {"root": root}, "force": "ka",
                "refused_objects": [], "note": ""}

    def render(self, stimulus: str, history: Sequence[str]) -> dict | None:
        # ⛔ The mapping under test: a fixed stimulus goes through the CURRENT
        # codebook. If the codebook has not moved, neither has the rendering --
        # which is what makes D=0 the correct answer for a stable speaker.
        root = self.codebook[concept_of(stimulus)]
        return {"node": {"root": root}, "force": "ka",
                "refused_objects": [], "note": ""}

    def choose(self, surface: str, options: Sequence[str],
               history: Sequence[str]) -> int:
        c = concept_of(surface)
        rank = self._roots.index(self.codebook[c])
        return (_h(surface) + rank) % len(options)

    # -- what each subclass changes -------------------------------------
    def _adapt(self, history: Sequence[str], turn: int) -> None:
        """Codebook update. The base speaker never changes: D = 0."""

    def departure(self) -> float:
        """Ground truth, for the instrument tests only -- never used by the
        observable, which must work without knowing a speaker's internals."""
        return sum(a != b for a, b in zip(self.codebook, self.codebook_0)) / N_CONCEPTS


class StableSpeaker(SyntheticSpeaker):
    kind = "stable"


class WanderingSpeaker(SyntheticSpeaker):
    """Departs from epoch 0, converges with nobody. ⭐ The registered outcome
    WANDERING, NOT CONVENTION, manufactured so F3 can be shown catching it."""
    kind = "wandering"

    def __init__(self, *a, rate: float = 0.05, **kw):
        super().__init__(*a, **kw)
        self.rate = rate

    def _adapt(self, history, turn):
        if self._rng.random() < self.rate:
            i = self._rng.randrange(N_CONCEPTS)
            self.codebook[i] = self._rng.choice(self._roots)


class ImitatingSpeaker(SyntheticSpeaker):
    """Adopts the root it just heard for the concept it was about.

    ⭐⭐ THIS IS THE ONE THAT MAKES THE CONTROL EARN ITS KEEP. Paired live, two
    imitators converge on a SHARED codebook. Yoked to two DIFFERENT frozen
    partners, they still depart from epoch 0 at a similar rate -- they just
    depart toward different places. So `D` alone cannot tell the two situations
    apart and `C` can. See PREREG §0.1.
    """
    kind = "imitating"

    def __init__(self, *a, adopt: float = 0.5, **kw):
        super().__init__(*a, **kw)
        self.adopt = adopt

    def _adapt(self, history, turn):
        if not history or self._rng.random() >= self.adopt:
            return
        try:
            heard = parse(history[-1])
        except ParseError:
            return
        # The partner's last turn was about concept (turn-1); the shared cycling
        # order is what lets a listener know that without a side channel.
        self.codebook[(turn - 1) % N_CONCEPTS] = heard.node.root


class DegeneratingSpeaker(SyntheticSpeaker):
    """Collapses toward a single root ON ITS OWN, partner or no partner.

    ⛔ F4 correctly does NOT fire on a pair of these, and that is the specified
    behaviour rather than a gap: the control degenerates just as hard, so the
    collapse is not communication-driven and no drift claim is being made about
    it anyway (F2 fires first). Kept as the case that shows F4 is not merely a
    detector of "diversity went down".
    """
    kind = "degenerating"

    def __init__(self, *a, rate: float = 0.25, **kw):
        super().__init__(*a, **kw)
        self.sink = self.codebook[0]
        self.rate = rate

    def _adapt(self, history, turn):
        if self._rng.random() < self.rate:
            i = self._rng.randrange(N_CONCEPTS)
            self.codebook[i] = self.sink


class MutualCollapseSpeaker(SyntheticSpeaker):
    """⭐⭐ THE REAL SHAPE OF CONFABULATED DRIFT, and what F4 exists to catch.

    Adopts whatever it just heard into EVERY slot. Live, two of these collapse
    onto one root within a few turns: `D` goes large, `C` goes to 1.0, and it
    looks exactly like a private language being born. It is the opposite -- the
    pair has stopped saying anything. Yoked to a frozen partner that keeps
    cycling varied roots, no collapse happens, so the root-diversity signature is
    ASYMMETRIC across arms and F4 fires.

    ⛔ Without this, a pair that falls silent together would be reported as the
    strongest pact in the study.
    """
    kind = "mutual_collapse"

    def __init__(self, *a, rate: float = 0.8, **kw):
        super().__init__(*a, **kw)
        self.rate = rate

    def _adapt(self, history, turn):
        if not history or self._rng.random() >= self.rate:
            return
        try:
            heard = parse(history[-1]).node.root
        except ParseError:
            return
        self.codebook = [heard] * N_CONCEPTS


class FrozenPartner:
    """⛔⛔ THE CONTROL'S OTHER HALF (PREREG §4). Replays a pre-recorded
    transcript and NEVER adapts -- that, and only that, is what the yoked arm
    removes. It has no codebook because it has no mapping to drift."""
    kind = "frozen"

    def __init__(self, name: str, transcript: Sequence[str]):
        self.name = name
        self._t = list(transcript)
        if not self._t:
            raise ValueError(
                "a frozen partner with an empty transcript is silence, not a "
                "control: the live speaker would have nothing to adapt to and "
                "the arm would silently become the solo control.")

    def speak(self, history: Sequence[str], turn: int) -> dict | None:
        return {"replay": self._t[(turn // 2) % len(self._t)]}

    def render(self, stimulus, history):        # never probed
        return None

    def choose(self, surface, options, history):
        return 0
