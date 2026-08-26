"""THE PROVOCATION — ONE STRING, IMPORTED BY THE TRAINER AND THE ARENA.

⛔⛔ THIS MODULE EXISTS BECAUSE TWO CONTRACTS WERE NEVER CHECKED AGAINST EACH
OTHER. `act2_finetune.SYSTEM` had exactly two directions (`write`, `read`) and
the arena spoke under `llm.CONVERSE` — a different string in a different module
that **was never a training direction**. Run 3 was trained on write/read and
prompted at arena time under a framing it had never seen, and 27/27 green said
nothing because no test crossed the boundary. That mismatch is a live candidate
for the depth-1 echo the whole locality prereg is built around.

⭐ THE FIX IS STRUCTURAL, NOT CLERICAL. Both sides import THIS constant. They
cannot drift, in the same way `row_to_text` cannot drift from the trainer's fold
now that the counter imports it instead of re-spelling it.

⛔⛔ AND THE OLD STRING WAS SEMANTICALLY WRONG, NOT MERELY MISPLACED. `CONVERSE`
said *"Say something that FOLLOWS FROM what was said"* — a request for **content
continuity**, which is exactly what **C-D1** denies (*"a later utterance does not
follow from an earlier one; it succeeds and associates with it"*) and exactly
what a content-free corpus refuses to supply. Training content-free painting
under that prompt would have the supervision contradict the instruction, and a
force-fidelity result would be uninterpretable: you could not tell whether the
model learned force-transmission or learned to resolve a prompt/data conflict in
some direction nobody measured.

⭐⭐ SO THE REPLACEMENT MUST *ACTIVELY LICENSE* CONTENT-FREEDOM, not merely omit
the request for continuity. Every LLM prior pulls toward staying on topic; a
prompt that is silent on content gets the content-adjacency ghost back through
the instruction after six rounds of killing it in the oracle. The licensing
clause is load-bearing, and `tests/test_provocation_string.py` mutation-tests
each clause for covert two-place requests.
"""
from __future__ import annotations

#: ⛔ Words that request a TWO-PLACE relation between this turn and the prior.
#: Each is permitted ONLY inside a negating clause — the string is allowed to say
#: "it need not follow from it", never "it should follow from it".
CONTINUITY_WORDS: tuple[str, ...] = (
    "follow", "about what", "related", "relate", "topic", "subject",
    "continue", "the next thing", "answer", "reply", "respond", "same",
    "consistent", "coheres with", "connected",
)

#: Tokens that make a clause a licence rather than a request.
NEGATORS: tuple[str, ...] = ("need not", "do not", "does not", "never",
                             "nothing", "no ", "not ")

PROVOCATION = """You are speaking Tlön with one other speaker. Tlön has no \
nouns: every root is an impersonal verb, and there are no words for objects, \
for people, or for a self.

You will be shown one Tlön utterance and nothing else.

Paint a scene that holds together on its own. Let the force of what you were \
shown provoke the force of what you say — assert, ask, wonder, urge, deny.

What you paint is yours. It need not be about what you were shown, it need not \
follow from it, and it need not stay on any subject. Only the force carries \
across.

Do not translate what you were shown. Do not explain, and do not comment on the \
language. Emit ONLY the JSON object for one Scene. Every form must come from \
the lexicon below."""

#: The trainer's direction key for rows built from this prompt.
DIRECTION = "provoke"
