"""Structural compat: does a scene match a referent signature?

This is 2a's entire M gate -- exact, free, no model. Its stand-in status is not
negotiable: structural compat cannot tell a vivid impression from a barely
relevant one. Scoring well here is evidence the pipes do not leak, nothing more.
"""
from __future__ import annotations
import itertools

from ..grammar.parse import EventNode, Scene
from .schema import NodePattern, Referent, Signature


def nodes(n: EventNode) -> list[EventNode]:
    out = [n]
    for _, child in n.edges:
        out += nodes(child)
    return out


def depths(n: EventNode, d: int = 0) -> dict[int, int]:
    """id(node) -> nesting depth below the matrix."""
    out = {id(n): d}
    for _, child in n.edges:
        out.update(depths(child, d + 1))
    return out


def node_matches(n: EventNode, p: NodePattern) -> bool:
    if n.root not in p.root_any:
        return False
    # ⛔⛔ PHASE 13.0: the residue constraint, and `None` MEANS UNKNOWN.
    #
    # This is the only clause whose part never reaches the surface, so it is
    # the only one a listener CANNOT check by reading the utterance. A heard
    # scene therefore carries residue=None -- not "the null residue", but "this
    # dimension was not transmitted" -- and an unknown cannot violate a
    # constraint. Treating None as a value instead would make a heard utterance
    # consistent with NEITHER of two residue-distinct referents, when the whole
    # point is that it is consistent with BOTH. That IS the irreducible
    # full-utterance ambiguity; deleting it here would delete the lever.
    #
    # The speaker's own scene always carries a residue, so the constraint bites
    # exactly where it should: on the scene, never on the utterance.
    if p.residue_any and n.residue is not None and n.residue not in p.residue_any:
        return False
    if p.orient_any and not (set(n.orient) & set(p.orient_any)):
        return False
    if p.aspect_root_any and (n.aspect is None or n.aspect[0] not in p.aspect_root_any):
        return False
    if p.edge_relator_any and not ({r for r, _ in n.edges} & set(p.edge_relator_any)):
        return False
    return True


def matches(scene: Scene, sig: Signature) -> bool:
    """Every `contains` pattern must match a DISTINCT node; no `forbid` pattern
    may match any node. A pattern carrying `via` must additionally be a direct
    child of the matrix through one of its named relators."""
    pool = nodes(scene.node)
    for f in sig.forbid:
        if any(node_matches(n, f) for n in pool):
            return False
    if sig.matrix and not node_matches(scene.node, sig.matrix):
        return False
    k = len(sig.contains)
    if k > len(pool):
        return False
    # relator by which each node hangs off the matrix (None if not a direct child)
    attach = {id(child): rel for rel, child in scene.node.edges}
    depth_of = depths(scene.node)
    cands = []
    for p in sig.contains:
        ok = []
        for i, n in enumerate(pool):
            if not node_matches(n, p):
                continue
            if p.via and attach.get(id(n)) not in p.via:
                continue
            if p.at_depth is not None and depth_of.get(id(n)) != p.at_depth:
                continue
            ok.append(i)
        cands.append(ok)
    if any(not c for c in cands):
        return False
    # injective assignment; k <= 4 and |pool| <= 13 under the caps
    for combo in itertools.product(*cands):
        if len(set(combo)) == k:
            return True
    return False


def consistent(scene: Scene, sig: Signature) -> bool:
    """THE DUAL OF `matches`: is this referent STILL POSSIBLE?

      matches(scene, sig)     every PATTERN finds a distinct node -- "fully stated"
      consistent(scene, sig)  every NODE finds a distinct pattern -- "still possible"

    Under impression-selection the speaker utters only part of the scene, so a
    partial utterance of A does NOT match A -- it has not said enough. It is
    still consistent with A, and with every other referent whose signature could
    be completed the same way. That set is what a listener must choose between,
    so that set is the ambiguity.
    """
    pool = nodes(scene.node)
    for f in sig.forbid:
        if any(node_matches(n, f) for n in pool):
            return False
    if sig.matrix and not node_matches(scene.node, sig.matrix):
        return False
    if len(pool) > len(sig.contains):
        return False        # said more distinct happenings than this referent has
    attach = {id(child): rel for rel, child in scene.node.edges}
    depth_of = depths(scene.node)
    cands = []
    for n in pool:
        ok = []
        for j, p in enumerate(sig.contains):
            if not node_matches(n, p):
                continue
            if p.via and attach.get(id(n)) not in p.via:
                continue
            if p.at_depth is not None and depth_of.get(id(n)) != p.at_depth:
                continue
            ok.append(j)
        if not ok:
            return False
        cands.append(ok)
    for combo in itertools.product(*cands):
        if len(set(combo)) == len(pool):
            return True
    return False


def compat(scene: Scene, ref: Referent) -> bool:
    return matches(scene, ref.signature)


def resolve(scene: Scene, refs: list[Referent]) -> list[Referent]:
    """Every referent this scene is compatible with. len() > 1 is a COLLISION:
    the M gate cannot tell those referents apart from this scene."""
    return [r for r in refs if compat(scene, r)]
