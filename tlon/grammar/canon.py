"""Canonical form and utterance_id (spec §6).

The repetition counter is only as honest as this module. Dedupe keys on the
canonical AST hash, NEVER on the surface string -- permuting the
order-insensitive slots yields a different string and the same meaning.
"""
from __future__ import annotations
import hashlib
import json
import math

from .parse import Scene, parse, canon_node


def canon(scene: Scene) -> dict:
    return {"force": scene.force, "node": canon_node(scene.node)}


def canon_json(scene: Scene) -> str:
    return json.dumps(canon(scene), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def utterance_id(scene: Scene) -> str:
    return hashlib.blake2b(canon_json(scene).encode("utf-8"),
                           digest_size=16).hexdigest()


def id_of(text: str) -> str:
    return utterance_id(parse(text))


def fiber_size(scene: Scene) -> int:
    """|{surface forms u : canon(parse(u)) == canon(scene)}|  -- spec Q3.

    The only surface freedom a fixed scene permits is permutation of the
    order-insensitive slots: orientation particles within a predication, and
    sibling clauses within a predication. Exact, not estimated.
    """
    def walk(n) -> int:
        total = math.factorial(len(n.orient)) * math.factorial(len(n.edges))
        for _, child in n.edges:
            total *= walk(child)
        return total
    return walk(scene.node)
