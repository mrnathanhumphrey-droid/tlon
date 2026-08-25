"""The PROPOSER — Route A. A hosted model proposes; the parser decides.

⛔ THE MODEL IS NEVER TRUSTED. It emits a proposal against `schema.json_schema()`
and `schema.validate()` is the boundary. Nothing here can put an illegal
utterance on screen, because nothing here renders -- validation does.

⭐ ROUTE A IS ROUTE B'S DATA COLLECTION. Every accepted (arbitrary-English,
validated-Scene) pair is logged by `corpus.py` from message one. An unlogged
pair is a pair the local model can never train on -- the 9.5 stall (effective
sample size 0, not merely small) applied to the product.

The Proposer protocol is the swap point: when B is trained, a LocalProposer
implements the same two methods and the hosted dependency comes out.
"""
from __future__ import annotations

import json
import os
from typing import Protocol

from ..grammar import classes as C
from . import schema as PS

MODEL_DEFAULT = "claude-sonnet-5"


class ProposerError(RuntimeError):
    pass


class Proposer(Protocol):
    name: str

    def propose(self, english: str, *, feedback: str | None = None) -> dict:
        ...


def lexicon_card() -> str:
    """The whole expressible world, derived from the frozen lexicon.

    ⛔ DERIVED, NEVER HARDCODED. If the lexicon moves this moves with it.
    """
    lex = C.load()["classes"]
    k = C.constraints()

    def block(cls: str, label: str) -> str:
        items = sorted(lex[cls].items())
        return f"{label}\n" + "\n".join(f"  {f} = {g}" for f, g in items)

    return "\n\n".join([
        f"LEXICON {C.load()['_hash']} — FROZEN. Nothing outside it exists.",
        block("R", f"ROOTS ({len(lex['R'])}) — every one is an IMPERSONAL VERB. "
                   "There are no nouns:"),
        block("L", "RELATORS (how one happening attaches to another):"),
        block("O", "ORIENTATIONS:"),
        block("A", "ASPECTS:"), block("D", "DEGREES:"), block("M", "EVIDENTIALS:"),
        block("T", "TENSES:"), block("Q", "QUANTS:"), block("F", "FORCES:"),
        f"LIMITS: depth <= {k['MAX_DEPTH']} · <= {k['MAX_CLAUSES_PER_PRED']} "
        f"clauses per predication · <= {k['MAX_ORIENT_PER_PRED']} orientations "
        f"per predication · aspect reps 1..{k['MAX_ASPECT_REPS']}",
    ])


SYSTEM = """You translate English into Tlön, the language of Borges' southern \
hemisphere. You do not answer the user; you RENDER what they said.

THE ONE THING THAT GOVERNS EVERYTHING: Tlön has no nouns. Its speakers do not \
believe in persistent objects, only in happenings. Every root is an impersonal \
verb — "it hollows", "it streams", "it endures cold and unyielding". There is \
no word for landlord, for bread, for a team, for a self.

So you never translate the OBJECTS in a sentence. You render the IMPRESSION \
underneath them — what is happening, to what it tends, how it is known.

  "my landlord raised the rent again"
      -> a pressing that recurs, from above, enduring, and it does not relent
  "my girlfriend made garlic bread"
      -> a warming that gladdens, out of a tending-toward, amid a nearness

⛔ NAME WHAT YOU LET GO. Every noun you could not hold as a thing goes in \
`refused_objects`. This is shown to the user and it is the point, not an \
apology: it is where they see that the language cannot grant objects \
permanence. Do not apologise for it and do not smuggle objects back in by \
choosing roots that merely sound like them.

`note` is a BARE PHRASE naming the impression you reached — no leading "Rendered \
as", no sentence, no full stop, and do NOT restate the refused objects (they are \
already shown). Write it as the thing itself: "a warming that gladdens, arising \
near a longing".

Choose the FEWEST parts that carry the impression. A bare happening with one \
dependent is usually truer than a crowded tree. Use the evidential when the \
English marks how it was known, the tense when it is anchored in time, the \
force when it is a question or a wondering rather than an assertion.

Emit ONLY the JSON object. Every form must come from the lexicon below."""


class AnthropicProposer:
    """Route A. Hosted proposer, bounded and temporary."""

    def __init__(self, model: str = MODEL_DEFAULT, max_tokens: int = 1400):
        try:
            import anthropic
        except ImportError as exc:                 # pragma: no cover
            raise ProposerError("pip install anthropic") from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ProposerError(
                "ANTHROPIC_API_KEY is not set. Route A needs it; this is the "
                "project's first non-$0.00 dependency and it is deliberate.")
        self._client = anthropic.Anthropic()
        self.model = model
        self.name = f"anthropic:{model}"
        self.max_tokens = max_tokens
        self.usage: list[dict] = []
        self._card = lexicon_card()

    def propose(self, english: str, *, feedback: str | None = None) -> dict:
        tool = {"name": "render_scene",
                "description": "Render the impression underneath the English.",
                "input_schema": PS.json_schema()}
        user = f"Render this into Tlön:\n\n{english}"
        if feedback:
            # ⛔ The retry carries the PARSER's refusal verbatim. The model is
            # being corrected by the grammar, not by a paraphrase of it.
            user += (f"\n\nYour previous proposal was REFUSED by the Tlön "
                     f"parser:\n  {feedback}\nPropose a legal Scene.")
        msg = self._client.messages.create(
            model=self.model, max_tokens=self.max_tokens,
            system=SYSTEM + "\n\n" + self._card,
            tools=[tool], tool_choice={"type": "tool", "name": "render_scene"},
            messages=[{"role": "user", "content": user}])
        self.usage.append({"input": msg.usage.input_tokens,
                           "output": msg.usage.output_tokens})
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use":
                return dict(block.input)
        raise ProposerError(f"no proposal returned: {msg.content!r}")

    def cost_report(self) -> dict:
        """Legible bill. Prices are per million tokens and are declared here so
        a wrong figure is visible rather than buried in a spreadsheet."""
        inp = sum(u["input"] for u in self.usage)
        out = sum(u["output"] for u in self.usage)
        price_in, price_out = 3.00, 15.00
        usd = inp / 1e6 * price_in + out / 1e6 * price_out
        n = max(1, len(self.usage))
        return {"calls": len(self.usage), "input_tokens": inp,
                "output_tokens": out, "usd_total": usd, "usd_per_message": usd / n,
                "prices_per_mtok": {"input": price_in, "output": price_out}}


class ScriptedProposer:
    """A proposer that replays fixed proposals. For tests and for offline demos;
    costs nothing and exercises the whole gate."""

    def __init__(self, proposals: list[dict]):
        self.name = "scripted"
        self._q = list(proposals)
        self.usage: list[dict] = []

    def propose(self, english: str, *, feedback: str | None = None) -> dict:
        if not self._q:
            raise ProposerError("scripted proposer exhausted")
        return self._q.pop(0)

    def cost_report(self) -> dict:
        return {"calls": 0, "input_tokens": 0, "output_tokens": 0,
                "usd_total": 0.0, "usd_per_message": 0.0}


def default_proposer() -> Proposer:
    return AnthropicProposer(os.environ.get("TLON_MODEL", MODEL_DEFAULT))
