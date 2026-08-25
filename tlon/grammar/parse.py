"""LL(1) recursive-descent parser for Sur, plus the compositional denotation.

Syntax is a deterministic FUNCTION. Any failure here is a generator bug, never
a listener disagreement -- that separation is what makes the M gate a test of
semantics rather than of grammar (spec §4.3).
"""
from __future__ import annotations
from dataclasses import dataclass, field

from . import classes as C


class ParseError(RuntimeError):
    pass


@dataclass
class EventNode:
    root: str
    aspect: tuple[str, int] | None = None
    degree: str | None = None
    modal: str | None = None
    tense: str | None = None
    quant: str | None = None
    orient: list[str] = field(default_factory=list)
    edges: list[tuple[str, "EventNode"]] = field(default_factory=list)

    # ⛔⛔ PHASE 13.0 -- THE THIRD CATEGORY: DENOTING ∧ INEXPRESSIBLE.
    # A coordinate in a fixed integer lattice (see grammar/residue.py). A
    # signature CAN constrain it and π KEEPS it -- it is meaning, not
    # decoration -- but `render()` structurally cannot emit it, so two scenes
    # differing only here produce the SAME surface. That is the irreducible
    # full-utterance ambiguity every previous lever failed to produce.
    #
    # ⛔ `parse()` CANNOT RECOVER IT, BY DESIGN. So for a residue-bearing scene
    #    utterance_id(scene) != id_of(render(scene)).
    #    That asymmetry IS the source-lossiness; it is not a bug to fix.
    residue: tuple[int, ...] | None = None


@dataclass
class Scene:
    node: EventNode
    force: str


class _Parser:
    def __init__(self, tokens: list[str]):
        self.toks = tokens
        self.i = 0
        self.k = C.constraints()
        self.cost = 0

    def _peek(self):
        if self.i >= len(self.toks):
            return None, None
        return C.classify(self.toks[self.i])

    def _take(self, expect: str):
        cls, payload = self._peek()
        if cls != expect:
            raise ParseError(f"expected {expect} at token {self.i}, got {cls}")
        self.i += 1
        self.cost += C.morph_cost(cls, payload)
        return payload

    def predication(self, depth: int) -> EventNode:
        quant = tense = modal = None
        orient: list[str] = []
        edges: list[tuple[str, EventNode]] = []

        if self._peek()[0] == "Q":
            quant = self._take("Q")
        if self._peek()[0] == "T":
            tense = self._take("T")
        if self._peek()[0] == "M":
            modal = self._take("M")
        while self._peek()[0] == "O":
            if len(orient) >= self.k["MAX_ORIENT_PER_PRED"]:
                raise ParseError("too many orientation particles")
            orient.append(self._take("O"))
        while self._peek()[0] == "L":
            if len(edges) >= self.k["MAX_CLAUSES_PER_PRED"]:
                raise ParseError("too many clauses")
            if depth <= 0:
                raise ParseError("clause nesting exceeds MAX_DEPTH")
            rel = self._take("L")
            edges.append((rel, self.predication(depth - 1)))

        root = self._take("R")
        aspect = self._take("A") if self._peek()[0] == "A" else None
        degree = self._take("D") if self._peek()[0] == "D" else None

        # Structurally vacuous: two identical sibling edges say nothing twice.
        keys = [(r, canon_node(n)) for r, n in edges]
        if len(set(map(str, keys))) != len(keys):
            raise ParseError("duplicate sibling clauses")

        return EventNode(root=root, aspect=aspect, degree=degree, modal=modal,
                         tense=tense, quant=quant, orient=orient, edges=edges)


def parse(text: str) -> Scene:
    toks = text.split()
    k = C.constraints()
    p = _Parser(toks)
    node = p.predication(k["MAX_DEPTH"])
    force = p._take("F")
    if p.i != len(toks):
        raise ParseError(f"trailing tokens from {p.i}")
    if not (k["MIN_MORPHS"] <= p.cost <= k["MAX_MORPHS"]):
        raise ParseError(f"utterance length {p.cost} outside "
                         f"[{k['MIN_MORPHS']}, {k['MAX_MORPHS']}]")
    return Scene(node=node, force=force)


def canon_node(n: EventNode):
    """Canonical, order-insensitive structure (spec §6). Defined here to keep
    the duplicate-sibling check self-contained; canon.py wraps it."""
    d = {"root": n.root}
    if n.aspect is not None:
        d["aspect"] = list(n.aspect)
    for k in ("degree", "modal", "tense", "quant"):
        v = getattr(n, k)
        if v is not None:
            d[k] = v
    if n.orient:
        d["orient"] = sorted(n.orient)
    # ⛔⛔ THE RESIDUE MUST BE IN THE CANONICAL FORM, AND THIS IS LOAD-BEARING.
    # `utterance_id` hashes canon_json, and RepetitionLog folds a new scene into
    # an existing medoid when `nearest.uid == uid`. Omit the residue here and
    # two residue-DIFFERING scenes share a uid, get folded as "an exact
    # canonical repeat", and the distinction is silently erased -- which would
    # make a metric-residue arm behave exactly like a no-residue arm and
    # MANUFACTURE an empty Part-2 result. Scenes differing in residue are
    # different SCENES; they merely share a SURFACE.
    if n.residue is not None:
        d["residue"] = list(n.residue)
    if n.edges:
        d["edges"] = sorted(([r, canon_node(c)] for r, c in n.edges),
                            key=lambda e: (e[0], repr(e[1])))
    return d


def render(scene: Scene) -> str:
    """Scene -> one surface form (the canonical ordering). Inverse of parse up
    to the order-insensitive slots."""
    def pred(n: EventNode) -> list[str]:
        out = []
        for v in (n.quant, n.tense, n.modal):
            if v is not None:
                out.append(v)
        out += sorted(n.orient)
        for rel, child in sorted(n.edges, key=lambda e: (e[0], repr(canon_node(e[1])))):
            out.append(rel)
            out += pred(child)
        out.append(n.root)
        if n.aspect is not None:
            out.append(n.aspect[0] * n.aspect[1] + C.load()["aspect_closer"])
        if n.degree is not None:
            out.append(n.degree)
        return out
    return " ".join(pred(scene.node) + [scene.force])
