"""THE BENCH'S OWN FRAMING — and the one sentence it must overturn.

⛔⛔ THE PUZZLE AND THE RESEARCH WANT OPPOSITE THINGS FROM CONTENT-CARRY, AND
THE RESEARCH'S ANSWER WAS LEAKING INTO THE PRODUCT'S SERVE PROMPT.

`act2_finetune.SYSTEM["provoke"]` contains, verbatim:

    "What you paint is yours. It need not be about what you were shown, it need
     not follow from it, and it need not stay on any subject. Only the force
     carries across."

That is the content-transient ontology — correct for the research, which exists
to ask whether content persists and must not smuggle persistence in through an
instruction, and correct for the art piece. It is an **explicit instruction not
to carry content**, and the puzzle was measuring "does the reply reuse the
provoking line's roots" while the system prompt told the model not to. The model
was obeying. Measured: root-reuse 1/22 under this prompt.

⭐ The capability is very likely present. The corpus this speaker was retrained
on carries content forward at 68% (against the old corpus's 27.1% = chance), so
the lesson is in the weights; the prompt is suppressing it. That is a $0
hypothesis and it is tested before any retrain is bought.

⛔⛔ THIS IS A DECLARED DIVERGENCE FROM THE TRAINED PROMPT AND IS THEREFORE
OFF-DISTRIBUTION BY CONSTRUCTION. Run 3 of this project was trained on one
framing and prompted under another and 27/27 green tests said nothing. The
difference is that there it was an accident nobody had written down; here it is
the experiment, and it is why the check must measure LEGALITY as well as reuse —
a prompt that raises content-carry by degrading the speaker is not a win.

⭐ DERIVED BY SUBSTITUTION, NEVER RE-SPELT. Everything else — no nouns, emit
only the JSON Scene, every form from the lexicon, do not translate or explain —
is the trainer's own text, imported. If the trainer's prompt ever moves, the
assertion below fails loudly instead of serving a stale copy that merely looks
right.
"""
from __future__ import annotations

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from act2_finetune import SYSTEM as TRAINED_SYSTEM           # noqa: E402
from tlon.discourse.provocation import DIRECTION as PROVOKE  # noqa: E402

#: The exact sentence the bench must overturn. ⛔ Matched in full rather than by
#: keyword: a partial match could silently replace a different sentence.
CONTENT_FREE = (
    "What you paint is yours. It need not be about what you were shown, it "
    "need not follow from it, and it need not stay on any subject. Only the "
    "force carries across.")

#: ⭐ What replaces it. Two things it deliberately does NOT do: it does not ask
#: the speaker to answer, explain or stay on topic (that would make a chatbot
#: out of a Tlönian), and it does not name a mechanism like "reuse a root"
#: (that would teach a tic that reads as repetitive collapse). It licenses
#: connection and leaves the form of the connection to the speaker.
CONTENT_CONNECTED = (
    "What you paint is yours, and it is painted in the same present as what "
    "you were shown. Let something of that moment carry into yours — a "
    "happening, a turning, a way the light or the weight of it falls. You are "
    "not answering and not explaining; you are still in the same now, and what "
    "is still going on may go on in what you paint.")


class BenchPromptError(RuntimeError):
    pass


def bench_system(direction: str = PROVOKE) -> str:
    """The provoke prompt with content-freedom replaced by content-connection.

    ⛔ RAISES IF THE SENTENCE IS ABSENT. A substitution that quietly matched
    nothing would return the trained prompt unchanged, the check would measure
    the control twice, and the two arms would agree — which reads exactly like
    "the framing was not the cause".
    """
    trained = TRAINED_SYSTEM[direction]
    if CONTENT_FREE not in trained:
        raise BenchPromptError(
            "⛔⛔ the content-freedom sentence is not in SYSTEM[%r]. The "
            "trainer's prompt has moved, so this substitution is operating on "
            "text that no longer exists and would return the trained prompt "
            "unchanged. Re-read the trainer before serving the bench." % direction)
    if trained.count(CONTENT_FREE) != 1:
        raise BenchPromptError("the sentence appears %d times, expected 1"
                               % trained.count(CONTENT_FREE))
    return trained.replace(CONTENT_FREE, CONTENT_CONNECTED)


def system_for(direction: str) -> str:
    """What the bench actually sends.

    ⛔ ONLY `provoke` DIVERGES. `write` turns the reader's English into Tlön and
    has no content-carry instruction to overturn — substituting there would be a
    change nobody argued for.
    """
    if direction != PROVOKE or not enabled():
        return TRAINED_SYSTEM[direction]
    return bench_system(direction)


def enabled() -> bool:
    """⛔ OFF BY DEFAULT while it is a hypothesis under test. It is turned on by
    evidence, not by being written."""
    return os.environ.get("TLON_BENCH_PROMPT", "0") not in ("0", "", "false", "no")


__all__ = ["bench_system", "system_for", "enabled", "BenchPromptError",
           "CONTENT_FREE", "CONTENT_CONNECTED"]
