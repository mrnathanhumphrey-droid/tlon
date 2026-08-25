"""Scene -> English gloss.

Two jobs. Today: make signatures reviewable by a human without reading morpheme
tables. Later (Phase 2c): this is the exact input to the frozen gloss-grounded
auditor, which is the anti-cipher device -- so the glosses in lexicon.yaml are
grounding, not documentation.
"""
from __future__ import annotations

from . import classes as C
from .parse import EventNode, Scene

_REL = {"BEYOND": "beyond", "AT": "at", "ERE": "before", "POST": "after",
        "CAUS": "because of", "CONC": "despite", "SIM": "while",
        "CMP": "as", "INSTR": "by means of", "PART": "out of",
        "TOWARD": "toward", "AMID": "amid"}
_ASP = {"unceasing": "unceasingly", "punctual_iterated": "again and again",
        "inceptive": "beginning", "terminative": "guttering out",
        "habitual": "habitually", "momentary": "for an instant"}
_FORCE = {"ASSERT": ".", "ASK": "?", "WONDER": " (wondering)",
          "URGE": " (urging)", "DENY": " (denied)"}


def gloss_node(n: EventNode) -> str:
    lex = C.load()["classes"]
    bits: list[str] = []
    for cls, field in (("Q", "quant"), ("T", "tense"), ("M", "modal")):
        v = getattr(n, field)
        if v is not None:
            bits.append(lex[cls][v].replace("_", " "))
    bits += [lex["O"][o].replace("_", " ") for o in sorted(n.orient)]
    for rel, child in sorted(n.edges, key=lambda e: e[0]):
        name = _REL.get(lex["L"][rel], lex["L"][rel].lower())
        bits.append(f"{name} ⟨{gloss_node(child)}⟩")
    core = lex["R"][n.root]
    if n.aspect is not None:
        root, reps = n.aspect
        adv = _ASP.get(lex["A"][root], lex["A"][root])
        core += ", " + (adv if reps == 1 else f"{adv} (×{reps})")
    if n.degree is not None:
        core += f", {lex['D'][n.degree]}ly"
    bits.append(core)
    return ", ".join(bits)


def gloss(scene: Scene) -> str:
    lex = C.load()["classes"]
    body = gloss_node(scene.node)
    return body + _FORCE.get(lex["F"][scene.force], "")
