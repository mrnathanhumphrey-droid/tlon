"""WHICH DOOR THE READER'S LINE GOES THROUGH.

⛔⛔ THE BUG THIS EXISTS FOR. The bench has two models behind it: `write` turns
English into Tlön, `provoke` answers a Tlön line with another. They were trained
on inputs that are disjoint on exactly two surface features —

    write   prompts: punctuation 95.9%, the token `ka`  0.0%  (12,680 rows)
    provoke prompts: punctuation  0.0%, the token `ka` 31.9%

— so a reader who types `Are you there ka` has written the perfect signature of
a *provoke* input and posted it through the *English* door. The write model,
which has never once seen `ka` in its training English, tries to speak the input
instead of rendering it: it puts `ka` into a root slot and the gate refuses,
`root='ka' is not in lexicon class R`. Five of six such lines were refused in
production. A question mark rescued the sixth, because punctuation drags the
string back into the write distribution.

⭐ SAYING A WORD BACK IS THE FIRST THING ANYONE DOES with a language whose
vocabulary is on screen. It is an honest attempt at the puzzle and it has to be
answered, so this module decides the door before either model is asked.

⛔ A bare force word is a READING OF THE LANGUAGE, not a fallback: `ka` is "it
is so", `ki` "is it so?", `ko` a wondering at it, `ku` an urging of it, `kä` "it
is not so" — each applied to the Tlönian's own last line. That is why route
`force` re-renders the prior surface under the reader's force rather than
inventing a scene.

⛔ NO MODEL, NO I/O, NO STATE. Everything here is `parse`/`render` against the
frozen lexicon, so it is testable on a laptop and cannot cost a GPU second.
"""
from __future__ import annotations

import dataclasses

from tlon.grammar import classes as C
from tlon.grammar.parse import ParseError, Scene, parse, render

#: (a) the whole line is already legal Tlön — the reader pasted a surface.
TLON = "tlon"
#: (b) the line is nothing but force words — a speech act aimed at the last line.
FORCE = "force"
#: (c) English with force words hung off the end — strip them, keep the force.
TAGGED = "tagged"
#: (d) ordinary English. The write step, exactly as before.
ENGLISH = "english"
#: (d) with Tlön roots embedded. ⭐ Routed identically — roots are NEVER
#: stripped — but recorded apart, because these are the rows a future write
#: corpus needs and there is currently no way to find them again.
ENGLISH_ROOTS = "english.roots"
#: (b) with nothing to aim at: the reader's first line is a bare force.
NOTHING = "nothing"


class RouterError(RuntimeError):
    pass


def _lex():
    return C.load()["classes"]


def is_force(token: str) -> bool:
    """⛔ EXACT FORMS ONLY — no case folding, no punctuation stripping. `Ka?`
    is not a force word, it is English, and it already renders correctly
    through the write door. Widening this to catch it would start guessing at
    which language a reader is writing in, which is the fault being fixed."""
    return token in _lex()["F"]


def is_root(token: str) -> bool:
    return token in _lex()["R"]


@dataclasses.dataclass(frozen=True)
class Decision:
    """Where the line goes, and what it carries there."""
    route: str
    #: routes `tlon` and `force`: the provocation, already a legal surface.
    surface: str | None = None
    #: routes `tagged`, `english`: what the write step should be handed.
    english: str | None = None
    #: route `tagged`: the force to stamp on the rendered scene.
    force: str | None = None

    @property
    def skips_write(self) -> bool:
        return self.route in (TLON, FORCE)


def refocus(surface: str, force: str) -> str:
    """The same scene under a different speech act.

    ⛔⛔ RE-VALIDATED, NOT TRUSTED. `render` puts the force last, so swapping it
    looks like a one-token edit and it would be easy to return the string
    unchecked. It is parsed back and compared to the scene it came from, which
    is the same proof the gate makes: `parse(render(scene)) == scene`.
    """
    if force not in _lex()["F"]:
        raise RouterError("%r is not an illocutionary force" % (force,))
    try:
        scene = parse(surface)
    except Exception as exc:                                   # noqa: BLE001
        raise RouterError("not a legal surface to refocus: %s" % exc) from exc
    moved = Scene(node=scene.node, force=force)
    out = render(moved)
    if parse(out) != moved:
        raise RouterError(
            "refocus did not round-trip: %r under %r" % (surface, force))
    return out


def looks_like_tlon(text: str) -> Scene | None:
    """-> the Scene if the whole line is legal Tlön, else None.

    ⛔⛔ TWO EXCEPTION TYPES, AND THEY ARE NOT RELATED. `LexiconError` derives
    from `RuntimeError`, NOT from `ParseError` — `issubclass` is False. English
    raises the first ("unknown morpheme 'Are'") and malformed Tlön the second,
    so a router catching only `ParseError` would crash on the single most
    common input the bench receives.
    """
    try:
        return parse(text)
    except (ParseError, C.LexiconError):
        return None


def classify(text: str, prior_surface: str | None = None) -> Decision:
    """Which door, given what the reader typed and the Tlönian's last line."""
    stripped = (text or "").strip()
    tokens = stripped.split()
    if not tokens:
        return Decision(ENGLISH, english=stripped)

    # (a) ── already a surface.
    if looks_like_tlon(stripped) is not None:
        return Decision(TLON, surface=stripped)

    # (b) ── nothing but force words.
    # ⭐ ONE OR MORE, not exactly one. `ka ka` is the same speech act said
    # twice; treating it as English would send it back through the door that
    # cannot read it. The LAST word wins, which is also (c)'s rule, so the two
    # routes cannot disagree about a line that sits between them.
    if all(is_force(t) for t in tokens):
        if not prior_surface:
            return Decision(NOTHING)
        try:
            moved = refocus(prior_surface, tokens[-1])
        except RouterError:
            # ⛔ FALL THROUGH, DO NOT RAISE. Prior surfaces come from our own
            # gate and should always re-parse — but "should" is what the
            # lexicon-hash change would break, and a router that raises here
            # turns a stored line from an older lexicon into a 500 for a
            # reader who typed one word.
            return Decision(ENGLISH, english=stripped)
        return Decision(FORCE, surface=moved, force=tokens[-1])

    # (c) ── English with force words hung off the end.
    body = list(tokens)
    tail = []
    while body and is_force(body[-1]):
        tail.append(body.pop())
    if tail and body:
        return Decision(TAGGED, english=" ".join(body), force=tokens[-1])

    # (d) ── English. Roots inside are left exactly where they are.
    route = ENGLISH_ROOTS if any(is_root(t) for t in tokens) else ENGLISH
    return Decision(route, english=stripped)
