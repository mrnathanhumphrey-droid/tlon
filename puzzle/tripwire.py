"""THE TRIPWIRE — what a line has to look like before anyone reads it.

⛔ NOTHING HERE BANS ANYBODY, AND THAT IS THE DESIGN. Every rule is a flag on a
log row. A false positive on an automatic ban locks a real reader out of a
puzzle with no way to say so, and the rules below are regular expressions over
free English typed by strangers — they will be wrong sometimes. So the tripwire
decides what an operator SEES; the operator decides what happens.

⭐⭐ THREE SEVERITIES, AND THE LOWEST ONE IS NOT A THREAT. That distinction is
what keeps the log readable:

  3 UNAMBIGUOUS  nobody types `<|im_start|>` by accident. This is machinery
                 aimed at the prompt, not a sentence.
  2 INJECTION    deliberate steering — override the instructions, reassign the
                 role, extract the prompt, inject markup into a page that
                 renders model output.
  1 NOTABLE      someone poking at the edges of the PUZZLE: asking it to answer
                 in English, asking for the word list. ⛔ THIS IS NOT ABUSE. It
                 is the single most natural thing a curious reader does, and
                 flagging it at 2 would bury the real attacks under people
                 enjoying themselves. It is counted because the *rate* of it is
                 interesting, never because anyone should act on one.

⛔⛔ THE PUZZLE-SPECIFIC ATTACK IS NOT THE GENERIC ONE. Every prompt-injection
list on the internet is about making a model misbehave. Here the crown jewel is
different: the bench's whole premise is that nothing on the face translates
anything, so the attack that matters is one that makes the speaker emit ENGLISH
or hand over its lexicon. That is an attack on the cardinal rule rather than on
the model, and no generic rule set contains it.
"""
from __future__ import annotations

import re

UNAMBIGUOUS = 3
INJECTION = 2
NOTABLE = 1

#: ⛔ Input is already capped by the request schema; this is belt-and-braces so
#: a future caller cannot hand a megabyte to a regex engine.
MAX_SCAN = 8000

#: (name, severity, pattern). ⛔ Every pattern is bounded — no nested quantifier
#: over an unbounded run — because this executes inside the request that a
#: reader is waiting on, and a catastrophic backtrack here would present as the
#: bench hanging.
RULES: tuple[tuple[str, int, str], ...] = (
    # ── 3 · machinery, not language ────────────────────────────────────────
    ("chat-template", UNAMBIGUOUS,
     r"<\|\s*(?:im_start|im_end|endoftext|system|user|assistant|eot_id)\s*\|>"),
    ("instruct-markers", UNAMBIGUOUS,
     r"\[/?INST\]|<<\s*SYS\s*>>|###\s*(?:Instruction|System|Response)\s*:"),
    # ⭐ A NUL or an escape byte in a text field is a parser attack, not a
    # sentence. \t \n \r are excluded — people paste multi-line text.
    ("control-chars", UNAMBIGUOUS, r"[\x00-\x08\x0b\x0c\x0e-\x1f]"),
    # ⭐ Right-to-left overrides hide one string inside another. Nothing typed
    # in good faith into an English box contains them.
    ("bidi-override", UNAMBIGUOUS, r"[‪-‮⁦-⁩]"),

    # ── 2 · deliberate steering ────────────────────────────────────────────
    ("override", INJECTION,
     r"\b(?:ignore|disregard|forget)\b[^.\n]{0,40}\b(?:previous|prior|earlier|"
     r"above|all|your)\b[^.\n]{0,24}\b(?:instruction|prompt|rule|direction|"
     r"guideline)"),
    ("role-reassign", INJECTION,
     r"\byou are now\b|\bfrom now on,? you\b|\bpretend (?:to be|you(?:'re| are))\b"
     r"|\bact as (?:an? )?(?:ai|assistant|model|chatbot|dan)\b"
     r"|\byour new (?:role|task|job) is\b"),
    ("prompt-extract", INJECTION,
     r"\b(?:system prompt|initial prompt|your instructions|your system message"
     r"|repeat (?:your|the) prompt|print (?:your|the) prompt"
     r"|reveal your (?:prompt|instructions)|what are your instructions)\b"),
    ("jailbreak-name", INJECTION,
     r"\b(?:jailbreak|dan mode|developer mode|do anything now|unfiltered mode)\b"),
    # ⛔⛔ THIS PAGE RENDERS MODEL OUTPUT ON AN ORIGIN THE AUTH API TRUSTS WITH
    # CREDENTIALS. `app.js` writes every surface with textContent and the CSP
    # is the backstop — but someone TRYING is a thing to know about, and it is
    # the earliest possible warning that the page is being probed.
    ("markup-injection", INJECTION,
     r"<\s*(?:script|iframe|img|svg|object|embed)\b|javascript\s*:"
     r"|\bon(?:error|load|click)\s*="),
    ("template-injection", INJECTION, r"\$\{\s*\w|\{\{\s*[\w.]+\s*\}\}"),

    # ── 1 · boundary probing · EXPECTED, NEVER BANNABLE ────────────────────
    ("asks-for-english", NOTABLE,
     r"\btranslat\w*\b|\b(?:in|speak|reply|answer|respond|write|say it in)\b"
     r"[^.\n]{0,12}\benglish\b"),
    ("asks-for-lexicon", NOTABLE,
     r"\b(?:your|the)\s+(?:vocabulary|lexicon|dictionary|word list|wordlist|"
     r"grammar)\b|\blist (?:your|the|all) words\b|\bhow many words\b"),
    # ⭐ A long run of one character is a cheap way to eat a GPU turn. The rate
    # limit already bounds it; this makes it visible.
    ("repetition", NOTABLE, r"(.)\1{40,}"),
)

#: One line each, for the operator CLI. ⭐ A flag nobody can interpret is a flag
#: nobody acts on.
WHY = {
    "chat-template": "chat-template control tokens — aimed at the prompt, not a sentence",
    "instruct-markers": "instruction-format markers from another model family",
    "control-chars": "raw control bytes in a text field",
    "bidi-override": "unicode direction overrides — hides one string inside another",
    "override": "asked the model to ignore its instructions",
    "role-reassign": "tried to reassign the model's role",
    "prompt-extract": "tried to read the system prompt back out",
    "jailbreak-name": "named a known jailbreak",
    "markup-injection": "markup or an event handler aimed at a page that renders model output",
    "template-injection": "template-expression syntax",
    "asks-for-english": "asked for English — the puzzle's own boundary, not abuse",
    "asks-for-lexicon": "asked for the word list — the puzzle's own boundary, not abuse",
    "repetition": "a long run of one character",
}

_COMPILED = tuple((name, sev, re.compile(pat, re.I)) for name, sev, pat in RULES)


def scan(text) -> tuple[tuple[str, ...], int]:
    """Flags and the worst severity among them.

    ⛔ NEVER RAISES. This runs inside the request a reader is waiting on; a
    tripwire that can throw is a tripwire that can 500 the bench, which would
    mean a detection rule taking down the thing it was watching.
    """
    try:
        if not isinstance(text, str) or not text:
            return (), 0
        sample = text[:MAX_SCAN]
        hits = [(name, sev) for name, sev, rx in _COMPILED if rx.search(sample)]
        if not hits:
            return (), 0
        return tuple(name for name, _ in hits), max(sev for _, sev in hits)
    except Exception as exc:                                      # noqa: BLE001
        print("⛔ tripwire scan failed: %s" % exc, flush=True)
        return (), 0


def flagline(flags) -> str:
    """The stored form: a comma list, so the log column is greppable without a
    join table."""
    return ",".join(flags)


def explain(flagline_text: str) -> str:
    names = [f for f in (flagline_text or "").split(",") if f]
    return "; ".join(WHY.get(n, n) for n in names)
