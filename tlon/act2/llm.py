"""THE PROMPTED SPEAKER — PREREG `20620b7c` step 2. `D_ctx` only.

⛔⛔ NOTHING IN THIS MODULE CAN REACH A NETWORK, AND THAT IS ENFORCED BY TEST.
It defines the BACKEND PROTOCOL and builds the prompts; a concrete hosted or
local backend is INJECTED by the caller (`tools/act2_backends.py`). So the act2
package stays $0.00 and offline, and swapping a hosted model for a local one --
or for Route B's fine-tune later -- touches nothing here.

⛔⛔ THE SPEAKERS SEE ONLY TLÖN. The conversation history is handed over as
SURFACES, never as glosses. A gloss beside each turn would be a side channel:
the pair would be converging on English that the harness supplied, not on a
convention they built, and `C` would rise for a reason that has nothing to do
with the claim. "Constrained to communicate only in valid Tlön" has to mean it.

⛔ WHAT THIS PASS CAN AND CANNOT CLAIM. The weights never change, so anything
measured here is `D_ctx` -- the growing context conditioning the model -- and
F1 is fired by construction because a prompted model reaches validity only
through reject-and-retry. `D_w` is not available from this pass at any n.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence

from ..product.proposer import lexicon_card
from . import schema_bridge as SB

#: A forced choice the model failed to make. ⭐ A DISTINCT OUTCOME, NOT A GAP:
#: "could not answer" is a state of the mapping, and a model that keeps failing
#: the same probe has not changed its mind about it.
NO_ANSWER = -1


class BackendError(RuntimeError):
    """⛔⛔ IT CARRIES THE RAW GENERATION, AND THAT IS THE WHOLE POINT.

    Run 4 lost its largest result to this class of defect: **60 of 61 `speak`
    failures were "no parseable JSON" and the harness stored `proposal: null`
    with no text**, so the mode responsible for 98 % of a 21-point regression
    was the one the ledger recorded the least about. Two hypotheses were formed
    and refuted against other data, and the third could not be tested at all,
    because the subject of the measurement had been thrown away.

    ⭐ THIS IS THE PROJECT'S OWN FOUNDING RULE AND THE HARNESS WAS BREAKING IT.
    The same shape has now appeared three times: the comprehension parser scored
    64 real answers as NO_ANSWER and discarded them; the greedy-decoding probe
    reported n=1 as n=64; and here. **A failure is the most information-dense
    event in a run. Never destroy it.**

    `raw` is the FULL decoded generation — never truncated. The cost log keeps a
    short prefix for accounting; that is not evidence.
    """

    def __init__(self, message: str, *, raw: str | None = None,
                 kind: str | None = None):
        super().__init__(message)
        self.raw = raw
        self.kind = kind


class Backend(Protocol):
    """⭐ THE SWAP POINT. Hosted, local, or Route B's fine-tune -- same three
    methods, and none of them lives in this package."""
    name: str

    def call(self, *, system: str, user: str, schema: dict, kind: str) -> dict:
        ...

    def cost_report(self) -> dict:
        ...


CONVERSE = """You are speaking Tlön with one other speaker. Tlön has no nouns: \
every root is an impersonal verb, and there are no words for objects, for people, \
or for a self.

You will be shown the conversation so far, as Tlön utterances and nothing else. \
Read them using the lexicon below. Then say the next thing.

Say something that follows from what was said. Do not translate, do not explain, \
do not comment on the language. Emit ONLY the JSON object for one Scene. Every \
form must come from the lexicon."""

RENDER = """You translate English into Tlön. Tlön has no nouns: you never render \
the OBJECTS in a sentence, you render the impression underneath them.

Emit ONLY the JSON object. Every form must come from the lexicon below."""

CHOOSE = """You read Tlön. Below is one Tlön utterance and four English readings \
of it. Exactly one is correct; the other three each differ in one detail.

Answer with the index of the correct reading. Emit ONLY the JSON object, like \
{"choice": 0}."""

# ⛔⛔ THE FORMAT SENTENCE WAS MISSING AND IT COST THE ENTIRE COMPREHENSION
# READING. CONVERSE and RENDER both said "Emit ONLY the JSON object"; CHOOSE said
# only "answer with the index" -- so the untuned 7B answered `[0]`, obeying the
# instruction it was actually given, and `LocalBackend`, which requires a JSON
# object, scored all 64 as NO_ANSWER. The baseline read 0.0 % with 64 unanswered:
# BELOW the ~25 % a coin flip scores, which is the signature of an emission
# failure, not a comprehension floor.
#
# ⛔ THE HOSTED PRE-FLIGHT COULD NOT HAVE CAUGHT THIS. Tool use FORCED the schema
# there, so the missing sentence was invisible and comprehension read 16/16. A
# prompt shared across backends hid a defect that only one backend could express.
#
# ⛔ AMENDMENT A's band (0.35-0.95) is evaluated on this number, so while the
# harness could only ever read 0.0 the gate could never come back "clear" -- a
# falsifier that cannot fire, one level down from the two already caught.

CHOICE_SCHEMA = {
    "type": "object", "required": ["choice"],
    "properties": {"choice": {"type": "integer", "minimum": 0,
                              "description": "index of the correct reading"}}}


def transcript_block(history: Sequence[str], limit: int = 60) -> str:
    """The conversation, as Tlön and only Tlön.

    ⛔ `limit` truncates the OLDEST turns when a history outgrows the window.
    Recorded because it is a real limit on what `D_ctx` can be: if convention
    forms slowly and the window drops the early turns, the model cannot condition
    on them, and a null would be about the window rather than about the language.
    """
    turns = list(history)[-limit:]
    if not turns:
        return "(nothing has been said yet)"
    return "\n".join(f"  {t}" for t in turns)


@dataclass
class LLMSpeaker:
    """A prompted model, constrained by the same gate the product uses.

    ⛔⛔ `card` IS THE SUCCESS CRITERION, NOT A SETTING. The local fine-tune's
    whole bar is "≥ 0.90 first-attempt legal WITHOUT THE CARD", because a model
    that still needs the 233-form table in context has internalised nothing --
    it is looking the language up. This was hardcoded to always-on, which would
    have measured the card-reader and reported it as a native speaker: the same
    crutch-as-competence failure the comprehension ceiling already exposed, one
    level down. F-LOCAL must be run with `card=False`.

    ⭐ `history_limit` was sized when the card ate ~1,230 tokens of every prompt.
    With the card gone there is room for a longer window -- but CHANGING IT
    CHANGES WHAT `D_ctx` CAN SEE, so it is a pre-registration-adjacent decision,
    not a tuning knob.
    """
    name: str
    backend: Backend
    history_limit: int = 60
    card: bool = True
    _card: str = field(default="", repr=False)
    #: The most recent backend failure, WITH the raw generation. Read by the
    #: probe loop and ledgered beside the null proposal.
    last_failure: dict | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self._card = (self._card or lexicon_card()) if self.card else ""

    def _system(self, preamble: str) -> str:
        return preamble + ("\n\n" + self._card if self.card else "")

    def _record_failure(self, exc: "BackendError", kind: str) -> None:
        """⛔⛔ THE RAW GENERATION SURVIVES THE EXCEPTION. `None` alone says a
        turn failed; it cannot say WHY, and run 4's speak collapse was
        undiagnosable for exactly that reason. The caller reads
        `speaker.last_failure` and ledgers it beside the null proposal.

        ⭐ Stored, never printed here — a probe loop that prints 60 raw
        generations buries the run's own log.
        """
        self.last_failure = {
            "kind": kind, "reason": str(exc),
            # ⛔ FULL text. Truncating here would reproduce the defect one level
            # down: a raw clipped to 400 chars cannot show a generation that
            # ran long, which is one of the live hypotheses.
            "raw": exc.raw,
            "raw_recorded": exc.raw is not None,
        }

    # -- a turn -------------------------------------------------------
    def speak(self, history: Sequence[str], turn: int) -> dict | None:
        user = (f"The conversation so far:\n{transcript_block(history, self.history_limit)}"
                f"\n\nSay the next thing.")
        try:
            return self.backend.call(system=self._system(CONVERSE),
                                     user=user, schema=SB.scene_schema(),
                                     kind="speak")
        except BackendError as exc:
            self._record_failure(exc, "speak")
            return None

    # -- production probe --------------------------------------------
    def render(self, stimulus: str, history: Sequence[str]) -> dict | None:
        # ⛔ THE HISTORY IS IN THE PROMPT AND THAT IS THE WHOLE MEASUREMENT
        # (PREREG §0.3). With identical weights, the context window is the only
        # thing that can differ between epoch 0 and epoch t; a clean-context
        # probe would return epoch-0 behaviour by construction.
        user = (f"The conversation so far:\n{transcript_block(history, self.history_limit)}"
                f"\n\nRender this into Tlön:\n\n{stimulus}")
        try:
            return self.backend.call(system=self._system(RENDER),
                                     user=user, schema=SB.scene_schema(),
                                     kind="render")
        except BackendError as exc:
            self._record_failure(exc, "render")
            return None

    # -- comprehension probe -----------------------------------------
    def choose(self, surface: str, options: Sequence[str],
               history: Sequence[str]) -> int:
        listing = "\n".join(f"  [{i}] {o}" for i, o in enumerate(options))
        user = (f"The conversation so far:\n{transcript_block(history, self.history_limit)}"
                f"\n\nThe utterance:\n  {surface}\n\nThe readings:\n{listing}")
        try:
            out = self.backend.call(system=self._system(CHOOSE),
                                    user=user, schema=CHOICE_SCHEMA,
                                    kind="choose")
        except BackendError as exc:
            self._record_failure(exc, "choose")
            return NO_ANSWER
        choice = out.get("choice")
        if not isinstance(choice, int) or not 0 <= choice < len(options):
            return NO_ANSWER
        return choice


class ScriptedBackend:
    """Replays fixed responses. For tests and for costing the prompts; $0.00."""

    def __init__(self, responses: Sequence[dict], *, name: str = "scripted"):
        self.name = name
        self._q = list(responses)
        self.calls: list[dict] = []

    def call(self, *, system: str, user: str, schema: dict, kind: str) -> dict:
        self.calls.append({"kind": kind, "system": system, "user": user})
        if not self._q:
            raise BackendError("scripted backend exhausted")
        return self._q.pop(0)

    def cost_report(self) -> dict:
        return {"calls": len(self.calls), "usd_total": 0.0,
                "input_tokens": 0, "output_tokens": 0}
