"""THE MOCK SPEAKER — the whole shape, with no model and no GPU.

⭐⭐ THE POINT IS TO REACT TO THE SHAPE BEFORE SPENDING ANYTHING. The agreed
next step has been "stand up the skeleton with a MOCK speaker — real server,
real window, real translate button, no model — so the shape can be reacted to
before anything is spent". This is that speaker. It satisfies `Speaker`'s
contract exactly: `ready`, `load()`, and
`turn(english, write_pairs, provoke_pairs) -> {you, tlon, seconds, shape,
context_turns}`.

⛔⛔ THE TLÖN IT EMITS IS REAL, NOT LOREM IPSUM. Every surface is drawn from
`tlon.act2.probes`, which generates scenes and VALIDATES them against the
frozen grammar before yielding them — the same generator the F-LOCAL battery is
built from. So `parse(surface)` succeeds, the translate button returns a true
gloss, and the round trip the whole project rests on is exercised. A mock that
emitted placeholder text would let every one of those paths go untested while
the page looked finished.

⭐⭐ AND IT CARRIES AT v1's MEASURED RATE, WHICH IS THE WHOLE VALUE OF IT.
`dosed-s20624` carries a root from the provoking line 27.5% of the time
[22.3, 33.2], measured at n=256. So this reproduces 27.5%, not 100%. The crib
density on the page is therefore the density a reader will actually meet, and
the UI gets designed against the real thing rather than against a wish. A mock
that carried every turn would make the puzzle look solvable when it is not, and
the first person to find out otherwise would be a stranger on the public URL.

⛔⛔ IT MUST NEVER SERVE A STRANGER. `TLON_MOCK_SPEAKER=1` is required AND a
deployed environment is refused outright, because the failure mode is silent:
fake Tlön is still legal Tlön, so a mock left on in production would answer
every visitor plausibly and nothing on the page would say the speaker was not
the trained model.
"""
from __future__ import annotations

import os
import random
import time

from .speaker import CONTEXT_TURNS, SHAPE, SpeakerError

#: ⛔ The measured carry rate of the shipped v1 adapter, not a guess and not a
#: target. `carrysweep` 2026-09-23, battery c0e011637df51c1b, n=256:
#: dosed-s20624 = 70/255 = 27.5% [22.3, 33.2]. If v1 changes, this moves with
#: it — a mock whose crib density has drifted from the speaker's is a UI built
#: against a puzzle that does not exist.
V1_CARRY_RATE = 0.275

#: ⛔ The gate refuses real English too, and a skeleton that never refuses hides
#: the refusal copy from review entirely. `chat.py` and `server.py` both treat a
#: refusal as an OUTCOME, not an error; the page has to show one.
REFUSAL_RATE = 0.08

#: Deployment markers. Any of these present means this is not a laptop.
_DEPLOYED = ("FLY_APP_NAME", "FLY_MACHINE_ID", "KUBERNETES_SERVICE_HOST",
             "DYNO", "RENDER", "AWS_EXECUTION_ENV")


def enabled() -> bool:
    """Whether the mock is switched on — and refuses loudly if it must not be."""
    on = os.environ.get("TLON_MOCK_SPEAKER", "0") in ("1", "true", "yes")
    if not on:
        return False
    live = [k for k in _DEPLOYED if os.environ.get(k)]
    if live:
        raise SpeakerError(
            "⛔⛔ TLON_MOCK_SPEAKER is set on what looks like a DEPLOYED "
            "environment (%s). The mock emits legal Tlön, so it would answer "
            "every visitor plausibly and nothing on the page would say the "
            "speaker was not the trained model. Refusing to start."
            % ", ".join(live))
    return True


class MockSpeaker:
    """Shape-identical to `Speaker`, backed by the probe generator."""

    def __init__(self, seed: int = 20624, carry_rate: float = V1_CARRY_RATE,
                 refusal_rate: float = REFUSAL_RATE):
        self._seed = seed
        self._carry = carry_rate
        self._refuse = refusal_rate
        self._pool = None
        self._rng = random.Random(seed)
        self.load_seconds: float | None = None
        self.is_mock = True

    @property
    def ready(self) -> bool:
        return self._pool is not None

    def load(self):
        """Fill the pool of pre-validated scenes. Cheap, but not free."""
        if self._pool is not None:
            return self._pool
        # ⛔ `from tlon.act2.probes import build`, NOT `from tlon.act2 import
        # probes`. The boundary test records the FROM module, so the latter
        # registers as `tlon.act2` and would allow-list the ENTIRE research
        # package for every file in `puzzle/`. Import the leaf.
        from tlon.act2.probes import build as build_battery
        from tlon.grammar.parse import parse
        t0 = time.perf_counter()
        # ⛔ COMPREHENSION PROBES ONLY. A `ProductionProbe` carries the ENGLISH
        # a model is asked to render, not a Tlön surface — only the
        # comprehension half holds `surface`, and it holds one that
        # `PS.validate` already passed.
        # ⛔⛤ 768, NOT 128, AND THE REASON IS THE PUZZLE'S OWN PREMISE. At 128 lines
        # over 218 roots, 58% of roots appeared exactly ONCE — so for most lines
        # the only other line sharing a root was itself, and a carry could not be
        # drawn at all. The dial stalled at 0.67 and every setting below it was
        # quietly understated. At 768 that falls to 2%. A language is decodable
        # only because it repeats; a pool too thin to repeat cannot model one.
        battery = build_battery(seed=self._seed, n_prod=8, n_comp=768)
        # ⛔ The scene comes back through `parse`, which is the same round trip
        # the translate button makes. If a probe surface ever failed to re-parse
        # this would raise here, loudly, instead of the page quietly showing a
        # line whose gloss could not be produced.
        self._pool = [(parse(p.surface), p.surface)
                      for p in battery.comprehension]
        # ⛔⛤ AN INDEX, NOT A REDRAW LOOP. The first version re-drew at random
        # until a scene happened to share a root, capped at 80 tries — and at
        # carry_rate 1.0 it reached only 72%, because most pairs in the pool
        # share nothing and the budget ran out. A dial that cannot reach its own
        # endpoint silently understates every setting below it, which is exactly
        # the defect the dosing blender had. This makes the draw exact.
        from collections import defaultdict
        from tlon.grammar import classes as C
        roots = frozenset(C.load()["classes"]["R"])
        self._by_root = defaultdict(list)
        for item in self._pool:
            for w in set(item[1].split()) & roots:
                self._by_root[w].append(item)
        self.load_seconds = time.perf_counter() - t0
        return self._pool

    # ── the turn ────────────────────────────────────────────────────────────

    def turn(self, english: str, write_pairs, provoke_pairs) -> dict:
        from tlon.grammar.gloss import gloss
        from tlon.product.literary import literary
        from tlon.grammar import classes as C

        self.load()
        t0 = time.perf_counter()
        roots = frozenset(C.load()["classes"]["R"])

        # ⛔⛤ ROOTS COME OFF THE SURFACE, NOT THE SCENE. `scene_roots` walks a
        # dict tree; `parse()` returns a `Scene` OBJECT, so calling it here
        # returned an empty set for every line and the carry dial read 0% at
        # every setting — silently, because an empty set intersects nothing and
        # "no carry" is a legal outcome. Splitting the surface is what
        # `act2_model_carry.score` already does for the provoking line, so this
        # is the established path rather than a third one.
        def surface_roots(surface):
            return frozenset(w for w in surface.split() if w in roots)

        def pick():
            return self._rng.choice(self._pool)

        def row(item, *, english_text=None):
            scene, surface = item
            return {"english": english_text, "surface": surface,
                    "gloss": gloss(scene), "literary": literary(scene),
                    "let_go": [], "refused": None, "seconds": 0.0}

        # ── your English becomes Tlön ────────────────────────────────────────
        if self._rng.random() < self._refuse:
            yours = {"english": english, "surface": None, "gloss": None,
                     "literary": None, "let_go": [],
                     "refused": "the gate would not pass it", "seconds": 0.0}
            # ⛔ No reply when the first step is refused — a provocation built
            # from a line the gate rejected is not a turn. Same rule as the
            # real speaker.
            return {"you": yours, "tlon": None,
                    "seconds": round(time.perf_counter() - t0, 2),
                    "shape": SHAPE, "context_turns": 0}

        you_item = pick()
        yours = row(you_item, english_text=english)

        # ── the reply, carrying at v1's rate ────────────────────────────────
        # ⭐ The carry is APPLIED, not hoped for: a scene is drawn until one
        # shares a root with the provoking line (or the budget runs out). That
        # is what makes the crib density on the page equal the measured rate
        # rather than whatever the generator happens to produce.
        want_carry = self._rng.random() < self._carry
        prior = surface_roots(you_item[1])
        if want_carry and prior:
            # ⭐ Draw DIRECTLY from the lines that share a root. Exact, so the
            # dial reaches 1.0 instead of stalling near 0.7.
            shared = [it for r in sorted(prior) for it in self._by_root.get(r, ())
                      if it is not you_item]
            reply = self._rng.choice(shared) if shared else pick()
        else:
            # ⛔ And the NOT-carrying branch must be exact too, or the measured
            # rate drifts UP from whatever the pool happens to overlap on.
            reply = pick()
            for _ in range(80):
                if not (surface_roots(reply[1]) & prior):
                    break
                reply = pick()

        return {"you": yours, "tlon": row(reply),
                "seconds": round(time.perf_counter() - t0, 2),
                "shape": SHAPE,
                "context_turns": min(len(list(provoke_pairs)), CONTEXT_TURNS)}


__all__ = ["MockSpeaker", "enabled", "V1_CARRY_RATE", "REFUSAL_RATE"]
