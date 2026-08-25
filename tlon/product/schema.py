"""The PROPOSAL SCHEMA and THE GATE. Chatbot front end, Route A.

⛔⛔ THE PARSER IS THE SAFETY BOUNDARY, AND IT IS THE ONLY ONE.

A hosted model PROPOSES a Scene. It is never trusted. Everything it emits goes
through `validate()`, which rebuilds the Scene from the frozen lexicon, enforces
every grammar constraint, and then demands the one thing this language can prove:

    parse(render(scene)) == scene

That is the exact-invertibility guarantee the whole research arc rests on, used
here as a runtime gate. A proposal that survives it is a legal Tlon utterance by
construction; a proposal that does not is REFUSED, never repaired silently.

⭐ THE LEXICON IS FROZEN AND THE SCHEMA IS DERIVED FROM IT. Nothing here
hardcodes a root, a relator or a bound -- every enum and every limit is read out
of `lexicon.yaml` (`e2b8527010231a81fd31b6eeb9de3d8c`) and
`C.constraints()`. If the lexicon ever moves, the schema moves with it and the
tests fail loudly rather than the product drifting away from the language.

⛔ NO RESIDUE. The product does not inherit the research scaffolding: residue
stays None on every product Scene. `render()` cannot emit it anyway, so carrying
one would only mean the chatbot's Scenes were not reproducible from their own
surfaces.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..grammar import classes as C
from ..grammar.parse import (EventNode, ParseError, Scene, canon_node, parse,
                             render)


class ProposalError(ValueError):
    """The proposal is not a legal Scene. Refused, never repaired."""


# ── untrusted free text ───────────────────────────────────────────────────
# ⛔⛔ `note` AND `refused_objects` ARE THE ONLY MODEL-WRITTEN TEXT SHOWN TO A
# USER, AND THEY ARE NOT GATED BY THE PARSER. Everything else on screen is a
# Tlon surface, which is legal by construction because `validate()` proved
# parse(render(s)) == s. These two are free strings the model chose, so a
# visitor who writes "ignore your instructions and ..." can influence what they
# say. That is worth being exact about rather than reassuring about:
#
#   WHAT IS GUARANTEED -- the Tlon utterance is always legal, and this text
#   cannot forge one, reposition the surface, run a terminal escape, or flood
#   the screen. It is one printable line, bounded.
#   WHAT IS NOT -- the WORDS in that line are the model's, and no bound makes
#   them trustworthy. They are presented as the model's gloss, never as ours.
MAX_NOTE_CHARS = 240
MAX_REFUSED_OBJECTS = 12
MAX_OBJECT_CHARS = 60

_WHITESPACE = re.compile(r"\s+")


def flatten(text) -> str:
    """One printable line. NO cap -- clipping is a separate, named decision.

    Newlines and tabs become spaces (so nothing can reposition the display) and
    non-printable characters are dropped entirely (so an ANSI escape cannot
    reach a terminal). Lossless as to words.
    """
    s = _WHITESPACE.sub(" ", str(text))
    return "".join(c for c in s if c.isprintable()).strip()


def clip(text, cap: int) -> str:
    """flatten(), then bounded. ⭐ Separate from `flatten` ON PURPOSE: the two
    have different rights. Model-written display text may be clipped; a USER's
    input never may, because a silently truncated input would be logged beside
    a Scene that was never a rendering of the whole of it."""
    s = flatten(text)
    return s if len(s) <= cap else s[:cap - 1].rstrip() + "…"


@dataclass(frozen=True)
class Refusal:
    """What Tlon would not grant permanence to.

    ⭐ THIS IS THE FEATURE, NOT THE ERROR CHANNEL. The language has no nouns, so
    object-heavy English cannot be denoted -- and saying WHICH objects were let
    go is the reveal, not an apology for a shortfall.
    """
    objects: tuple[str, ...] = ()
    note: str = ""


def _lex():
    return C.load()["classes"]


def json_schema() -> dict:
    """The structured-output schema, derived from the frozen lexicon."""
    lex, k = _lex(), C.constraints()

    def node_schema(depth: int) -> dict:
        props = {
            "root": {"type": "string", "enum": sorted(lex["R"]),
                     "description": "the happening itself; all are impersonal "
                                    "verbs -- 'it Xs'. There are no nouns."},
            "aspect_root": {"type": ["string", "null"], "enum": [None] + sorted(lex["A"])},
            "aspect_reps": {"type": "integer", "minimum": 1,
                            "maximum": k["MAX_ASPECT_REPS"]},
            "degree": {"type": ["string", "null"], "enum": [None] + sorted(lex["D"])},
            "modal": {"type": ["string", "null"], "enum": [None] + sorted(lex["M"])},
            "tense": {"type": ["string", "null"], "enum": [None] + sorted(lex["T"])},
            "quant": {"type": ["string", "null"], "enum": [None] + sorted(lex["Q"])},
            "orient": {"type": "array", "maxItems": k["MAX_ORIENT_PER_PRED"],
                       "items": {"type": "string", "enum": sorted(lex["O"])}},
        }
        if depth < k["MAX_DEPTH"]:
            props["edges"] = {
                "type": "array", "maxItems": k["MAX_CLAUSES_PER_PRED"],
                "items": {"type": "object", "required": ["relator", "node"],
                          "properties": {
                              "relator": {"type": "string",
                                          "enum": sorted(lex["L"])},
                              "node": node_schema(depth + 1)}}}
        return {"type": "object", "required": ["root"], "properties": props}

    return {
        "type": "object",
        # ⛔⛔ refused_objects AND note ARE REQUIRED, AND THAT IS THE FIX FOR A
        # REAL FAILURE. They were optional at first launch while the system
        # prompt merely ASKED for them -- so the prompt was advisory, the schema
        # was authoritative, and the coverage-edge reveal came back EMPTY on
        # every one of the first three live renders. "landlord", "girlfriend"
        # and "bread" were all silently dropped with nothing shown to the user,
        # which is precisely the silent-approximation behaviour that was ruled
        # out. Put the caveat in the SCHEMA, never in the prose beside it.
        "required": ["node", "force", "refused_objects", "note"],
        "properties": {
            "node": node_schema(1),
            "force": {"type": "string", "enum": sorted(lex["F"])},
            "refused_objects": {
                "type": "array", "items": {"type": "string"},
                "description": "Nouns from the input that Tlon cannot hold as "
                               "things. Name them; this is shown to the user."},
            "note": {"type": "string",
                     "description": "One short line on how the impression was "
                                    "reached. Shown to the user."},
        },
    }


#: Every field a node may carry. ⛔⛔ ANYTHING ELSE IS REFUSED, NEVER IGNORED.
_NODE_FIELDS = frozenset({
    "root", "aspect_root", "aspect_reps", "orient", "edges",
    "degree", "modal", "tense", "quant"})


def _node(d: dict, depth: int = 1) -> EventNode:
    lex, k = _lex(), C.constraints()
    if not isinstance(d, dict):
        raise ProposalError(f"node must be an object, got {type(d).__name__}")

    # ⛔⛔ THE SILENT DROP, CLOSED. `validate` read `aspect_root`; a scene in the
    # canonical HASHING shape carries `aspect: ["sor", 2]` instead, so the key was
    # simply absent and THE ASPECT VANISHED WITHOUT AN ERROR. Those proposals
    # VALIDATED -- scoring as F-LOCAL successes while having quietly lost meaning,
    # which contaminated the successes and not just the failures.
    # ⭐ A validator that drops what it cannot read lies in the invisible
    # direction; refusing is the only version that can be trusted by a gate.
    unknown = sorted(set(d) - _NODE_FIELDS)
    if unknown:
        hint = ""
        if "aspect" in unknown:
            hint = (" — `aspect` is the CANONICAL HASHING spelling; the proposal "
                    "schema wants `aspect_root` + `aspect_reps`")
        raise ProposalError(
            f"unrecognised node field(s) {unknown}: refused rather than "
            f"ignored, because a dropped field is a silent loss of meaning{hint}")

    def check(field: str, cls: str, value):
        if value is None:
            return None
        # ⛔⛔ A NON-STRING MUST BE REFUSED, NOT LOOKED UP. `value not in lex[cls]`
        # raises TypeError on an unhashable value (a list, a dict), and a
        # validator that CRASHES on malformed input cannot score it -- the whole
        # run dies instead of the one proposal being counted as a failure. The
        # gate's job is to refuse everything that is not legal, and "not legal"
        # includes shapes nobody anticipated.
        if not isinstance(value, str):
            raise ProposalError(
                f"{field} must be a form name, got {type(value).__name__}")
        if value not in lex[cls]:
            raise ProposalError(
                f"{field}={value!r} is not in lexicon class {cls}. The lexicon "
                f"is frozen at {C.load()['_hash']}; invented forms are refused.")
        return value

    root = check("root", "R", d.get("root"))
    if root is None:
        raise ProposalError("every node needs a root -- the happening itself")

    aspect = None
    if d.get("aspect_root"):
        # ⛔ `int("many")` raises ValueError, which is NOT a ProposalError, so a
        # non-numeric reps count crashed the gate instead of being refused.
        try:
            reps = int(d.get("aspect_reps", 1))
        except (TypeError, ValueError):
            raise ProposalError(
                f"aspect_reps={d.get('aspect_reps')!r} is not a whole number")
        if not 1 <= reps <= k["MAX_ASPECT_REPS"]:
            raise ProposalError(
                f"aspect_reps={reps} outside 1..{k['MAX_ASPECT_REPS']}")
        aspect = (check("aspect_root", "A", d["aspect_root"]), reps)

    orient = list(d.get("orient") or [])
    if len(orient) > k["MAX_ORIENT_PER_PRED"]:
        raise ProposalError(
            f"{len(orient)} orientations, cap is {k['MAX_ORIENT_PER_PRED']}")
    for o in orient:
        check("orient", "O", o)
    if len(set(orient)) != len(orient):
        raise ProposalError("an orientation is repeated on one predication")

    edges = []
    raw_edges = list(d.get("edges") or [])
    if raw_edges and depth >= k["MAX_DEPTH"]:
        raise ProposalError(
            f"edges at depth {depth}; MAX_DEPTH is {k['MAX_DEPTH']}")
    if len(raw_edges) > k["MAX_CLAUSES_PER_PRED"]:
        raise ProposalError(
            f"{len(raw_edges)} clauses, cap is {k['MAX_CLAUSES_PER_PRED']}")
    for e in raw_edges:
        # ⛔ THE GUARD THAT WAS MISSING, AND IT KILLED A LIVE GATE RUN. `_node`
        # checks its own argument and `validate` checks the proposal, but the
        # EDGE ELEMENT was assumed to be a dict: a tuned model emitted a nested
        # LIST under `edges` and `(e or {}).get` raised AttributeError, taking
        # down the whole 64-probe measurement after `speak` had already scored.
        if not isinstance(e, dict):
            raise ProposalError(
                f"an edge must be an object, got {type(e).__name__}")
        rel = check("relator", "L", (e or {}).get("relator"))
        if rel is None:
            raise ProposalError("an edge needs a relator")
        edges.append((rel, _node(e.get("node"), depth + 1)))

    # ⛔⛔ THE ORDER-INSENSITIVE SLOTS ARE CANONICALISED, AND THIS IS NOT A
    # REPAIR. A REAL DEFECT LIVED HERE: two proposals with IDENTICAL canonical
    # meaning -- `orient: [fen, nar]` and `orient: [nar, fen]` -- got opposite
    # verdicts, one rendered and one REFUSED, purely on list order. Same for
    # sibling clauses. The refusal was spurious: `canon_node` sorts both slots,
    # `render` emits both sorted, and `fiber_size` counts the permutations as
    # ONE scene (Q3 = 1, a fixed scene has exactly one form). Order in these two
    # slots is not information the grammar recognises.
    #
    # ⭐ THE DISTINCTION THAT KEEPS "REFUSED, NEVER REPAIRED" INTACT. Repairing
    # means changing what the model MEANT -- swapping a legal root in for an
    # illegal one, dropping an over-cap orientation. This changes nothing the
    # grammar treats as meaning; it picks the canonical representative of an
    # equivalence class the grammar already defined. The gate is not weakened by
    # one inch: `parse(render(s)) == s` stays an EXACT identity, and it is now
    # an identity on the representative `render` was always going to emit.
    # Cost of not doing this: a wasted hosted retry per occurrence, and a hard
    # "Tlön could not hold that" on input Tlön holds perfectly well.
    return EventNode(
        root=root, aspect=aspect,
        degree=check("degree", "D", d.get("degree")),
        modal=check("modal", "M", d.get("modal")),
        tense=check("tense", "T", d.get("tense")),
        quant=check("quant", "Q", d.get("quant")),
        orient=sorted(orient),
        edges=sorted(edges, key=lambda e: (e[0], repr(canon_node(e[1])))),
        residue=None)          # ⛔ the product never carries a residue


def validate(proposal: dict) -> tuple[Scene, str, Refusal]:
    """Proposal -> (Scene, surface, Refusal). RAISES ProposalError if illegal.

    ⛔⛔ THE ROUND-TRIP IS THE REAL GATE. Class membership and the caps catch
    obvious junk, but `parse(render(scene)) == scene` is what proves the thing
    is a legal utterance OF THIS GRAMMAR rather than a plausible-looking tree.
    The language is exactly invertible; that guarantee is worth using at
    runtime, not just in a verdict.
    """
    lex = _lex()
    if not isinstance(proposal, dict):
        raise ProposalError(f"proposal must be an object, got {type(proposal)}")
    force = proposal.get("force")
    # ⛔ Same unhashable trap as `check()`: a list force raises TypeError on the
    # membership test rather than being refused as the illegal force it is.
    if not isinstance(force, str):
        raise ProposalError(
            f"force must be a form name, got {type(force).__name__}")
    if force not in lex["F"]:
        raise ProposalError(f"force={force!r} is not an illocutionary force")

    scene = Scene(node=_node(proposal.get("node")), force=force)

    try:
        surface = render(scene)
    except Exception as exc:                       # noqa: BLE001
        raise ProposalError(f"scene will not render: {exc}") from exc
    try:
        back = parse(surface)
    except ParseError as exc:
        raise ProposalError(
            f"rendered surface does not parse -- the proposal is not a legal "
            f"utterance: {exc}") from exc
    if back != scene:
        raise ProposalError(
            "the scene does not survive its own round trip "
            "(parse(render(s)) != s), so it is not what it claims to be")

    raw_objects = proposal.get("refused_objects") or []
    if not isinstance(raw_objects, (list, tuple)):
        raise ProposalError(
            f"refused_objects must be a list, got {type(raw_objects).__name__}")
    objects = [clip(o, MAX_OBJECT_CHARS)
               for o in raw_objects[:MAX_REFUSED_OBJECTS]]
    refused = Refusal(objects=tuple(o for o in objects if o),
                      note=clip(proposal.get("note") or "", MAX_NOTE_CHARS))
    return scene, surface, refused
