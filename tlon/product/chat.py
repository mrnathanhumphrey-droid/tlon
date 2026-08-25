"""THE PIPELINE. Arbitrary English -> validated Scene -> nounless Tlon.

    english --> proposer (hosted, Route A) --> proposal
             --> schema.validate()  [THE GATE: class membership, every grammar
                                     bound, and parse(render(s)) == s]
             --> Scene --> surface, austere gloss, refused objects
             --> corpus.log_accepted()   [Route B's training row]

⛔ ONE RETRY, CARRYING THE PARSER'S OWN REFUSAL. If a proposal is illegal the
grammar's complaint goes back verbatim and the model tries once more. A second
failure is REFUSED and logged; nothing is repaired silently, because a repaired
proposal is not the model's output and would poison B's corpus with rows no
model ever produced.

⭐ THE COVERAGE EDGE IS THE PRODUCT. Tlon has no nouns, so object-heavy English
cannot be denoted. What the language let go is surfaced as REVELATION -- these
are the objects it would not grant permanence -- never as an apology.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..grammar import gloss as _gloss
from ..grammar.parse import Scene
from . import corpus
from . import literary as _literary
from . import schema as PS
from .proposer import Proposer


@dataclass
class Rendering:
    english: str
    scene: Scene
    surface: str
    # ⭐ TWO SURFACES, ONE SCENE, AND AN INVIOLABLE WALL BETWEEN THEM.
    #   austere  -- `grammar/gloss.py`, morpheme-faithful and comma-spliced. The
    #               MEASUREMENT INSTRUMENT and the honest surface. FROZEN.
    #   literary -- `product/literary.py`, the same Scene composed as prose. What
    #               a visitor actually experiences behind /reveal.
    # Both are pure functions of the Scene; neither calls a model.
    austere: str
    literary: str = ""
    refused_objects: tuple[str, ...] = ()
    note: str = ""
    attempts: int = 1
    parser_refusals: tuple[str, ...] = field(default=())

    def speak(self) -> str:
        """What the visitor sees. Opacity-first: the Tlon, and what it let go."""
        out = [self.surface]
        if self.refused_objects:
            objs = ", ".join(f"“{o}”" for o in self.refused_objects)
            thing = "a thing" if len(self.refused_objects) == 1 else "things"
            out.append(f"\n  Tlön would not hold {objs} as {thing}.")
        # ⛔ THE NOTE IS SHOWN ON ITS OWN, NEVER SPLICED INTO A SENTENCE OF
        # MINE. The first version wrote "It rendered {note} instead." and the
        # model's notes began "Rendered as ..." — so the first live output read
        # "It rendered Rendered as a warming that gladdens". Never build a
        # sentence half-written by a model and half by a template.
        if self.note:
            out.append(f"  → {self.note}")
        return "\n".join(out)


class Refused(RuntimeError):
    """The front end could not render this. Said plainly, not papered over."""


# ⛔ THE INPUT BOUND. The door is open to strangers, so the first thing that
# touches arbitrary English is a bound, not a model call. Over the bound the
# input is REFUSED, never truncated: a truncated input would be logged beside a
# Scene that was never a rendering of the whole of it -- a row that validates,
# round-trips, and lies. Refusing costs a visitor one retype; truncating costs
# Route B a poisoned pair nobody can find later.
MAX_ENGLISH_CHARS = 2000


def render_english(english: str, proposer: Proposer, *,
                   log: bool = True, retries: int = 1) -> Rendering:
    # ⭐ NORMALISED ONCE, AT THE DOOR, AND USED EVERYWHERE AFTER. The proposer,
    # the corpus row and the display all see this exact string, so the logged
    # pair is true by construction -- there is no second version of the input
    # for them to disagree about. Whitespace collapses and non-printables
    # (terminal escapes among them) are dropped; no words are lost.
    english = PS.flatten(english)
    if not english:
        # Not logged. An empty line is not part of the input distribution B has
        # to cover, and logging every stray keypress would bury the refusals
        # that mean something.
        raise Refused("nothing to render")
    if len(english) > MAX_ENGLISH_CHARS:
        if log:
            corpus.log_refused(
                english[:200], f"input is {len(english)} characters; the bound "
                f"is {MAX_ENGLISH_CHARS}", proposer=proposer.name,
                stage="input")
        raise Refused(
            f"Tlön takes one saying at a time. That was {len(english):,} "
            f"characters; it holds {MAX_ENGLISH_CHARS:,}.")
    feedback, refusals = None, []
    for attempt in range(1, retries + 2):
        proposal = proposer.propose(english, feedback=feedback)
        try:
            scene, surface, refusal = PS.validate(proposal)
        except PS.ProposalError as exc:
            feedback = str(exc)
            refusals.append(feedback)
            # ⛔ LOG EVERY REFUSAL, INCLUDING THE ONES A RETRY LATER RESCUES.
            # The first version logged only FINAL failures, so a proposal that
            # was refused once and accepted on retry left no trace -- and the
            # refusal SHAPE is exactly what says whether the front end is
            # healthy. Two of the first three live renders took a retry and
            # none of it was recorded.
            if log:
                corpus.log_refused(english, feedback, proposer=proposer.name,
                                   stage="parser", proposal=proposal,
                                   rescued_on_retry=attempt <= retries,
                                   attempt=attempt)
            if attempt <= retries:
                continue
            # ⭐ THE EVOCATIVE LINE FIRST, THE DIAGNOSIS AFTER. This is the one
            # failure a visitor can actually hit, and "Tlön could not hold that"
            # is both true and in the voice of the thing. The parser's own words
            # follow because a silent failure is worse than a technical one.
            raise Refused(
                f"Tlön could not hold that — nothing legal was proposed for it. "
                f"The parser's last word: {feedback}") from exc
        if log:
            corpus.log_accepted(english, scene, surface,
                                proposer=proposer.name, mode="translate",
                                refused_objects=refusal.objects,
                                note=refusal.note)
        return Rendering(english=english, scene=scene, surface=surface,
                         austere=_gloss.gloss(scene),
                         literary=_literary.literary(scene),
                         refused_objects=refusal.objects, note=refusal.note,
                         attempts=attempt, parser_refusals=tuple(refusals))
    raise Refused("unreachable")
