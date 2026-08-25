"""The denotation projection π — PREREG c09d0fb3.

π(scene) keeps exactly what can bear on WHICH REFERENT is meant, and normalises
everything else away. The listener never sees anything but π(scene), and the
repetition cost R is computed on π(scene) too.

WHY, IN ONE LINE. Phase 4 built a private code and channel-blocking only moved
it (`coda` +0.90 -> +3.15). A code is pathological precisely when it lives
somewhere novelty is FREE: decoration costs nothing to vary, so a code hidden
there buys perfect comprehension AND endless novelty without perceiving
anything. Forced into meaning-bearing structure, reusing a code IS repeating
yourself and R punishes it. So π does not block channels -- it removes the
class.

THIS IS NOT `canon`. `canon()` sorts order-insensitive slots: same meaning,
different word order. π is strictly stronger and discards information.

R MOVES ONTO π TOO, AND THAT IS NOT A CONVENIENCE. Projecting only the
listener's view would trade the cipher failure for the noise failure -- free
novelty from wiggling decoration nobody can read. It is also what phase 0
already forces: Q3 = 1 means a fixed scene has exactly one form, so two
utterances differing only in non-denoting decoration are THE SAME IMPRESSION and
must not count as novel. This makes the code match the result.

⛔ THE STRIP-LIST IS DERIVED FROM THE SCHEMA, NEVER HARDCODED. A signature is a
conjunction of `NodePattern`s, so a field no `NodePattern` can reference cannot
possibly pick out a referent. `denoting_parts()` walks `NodePattern`'s dataclass
fields through an explicit mapping; an unmapped field raises. Add
`degree_any` to NodePattern one day and this module fails LOUDLY at import-time
in CI, instead of silently rotting every number computed under it.
"""
from __future__ import annotations
import dataclasses

from ..referents.schema import NodePattern
from .parse import EventNode, Scene

# Which EventNode part each NodePattern field can constrain. The KEYS must stay
# exhaustive over NodePattern's fields -- that is the whole guard.
_PATTERN_TO_PART: dict[str, tuple[str, ...]] = {
    "root_any": ("root",),
    "orient_any": ("orient",),
    "aspect_root_any": ("aspect.root",),      # the ROOT half only, never reps
    "edge_relator_any": ("edges",),
    "via": ("edges",),                        # attachment relator
    "at_depth": ("edges",),                   # nesting structure
    "residue_any": ("residue",),              # PHASE 13.0 -- see _INEXPRESSIBLE
}

# Every addressable part of an EventNode / Scene.
_ALL_PARTS = ("root", "orient", "aspect.root", "aspect.reps", "edges",
              "degree", "modal", "tense", "quant", "force", "residue")

# ⛔⛔ PHASE 13.0 -- THE THIRD CATEGORY. π's original construction assumed
# DENOTING ⊆ EXPRESSIBLE: the strip-list was derived from NodePattern's fields
# and every one of them rendered. `residue` breaks that assumption on purpose.
# It is DENOTING (a signature constrains it, π keeps it, it picks out which
# referent is meant) and INEXPRESSIBLE (render() structurally cannot emit it).
#
# ⭐ STRIPPED and UNSAYABLE are different things and must not be conflated:
#   stripped   -- reaches the surface, removed for measurement (degree, modal…)
#   unsayable  -- never reaches the surface at all (residue)
# So the residue is NOT in nondenoting_parts() and π does NOT normalise it away.
_INEXPRESSIBLE = frozenset({"residue"})


class ProjectionUnsound(RuntimeError):
    """π can no longer be justified from the schema. KILL F."""


def denoting_parts() -> frozenset[str]:
    """Parts a signature can actually constrain. Raises if the schema moved."""
    fields = {f.name for f in dataclasses.fields(NodePattern)}
    unmapped = fields - set(_PATTERN_TO_PART)
    if unmapped:
        raise ProjectionUnsound(
            f"NodePattern gained {sorted(unmapped)}, which π does not know how "
            "to interpret. Re-derive _PATTERN_TO_PART before trusting any "
            "number computed under the projection (PREREG c09d0fb3, KILL F).")
    stale = set(_PATTERN_TO_PART) - fields
    if stale:
        raise ProjectionUnsound(
            f"_PATTERN_TO_PART maps {sorted(stale)}, which NodePattern no "
            "longer has. The mapping is out of date.")
    parts: set[str] = set()
    for f in fields:
        parts.update(_PATTERN_TO_PART[f])
    return frozenset(parts)


def nondenoting_parts() -> frozenset[str]:
    """What π normalises away. Derived, so it tracks the schema."""
    return frozenset(_ALL_PARTS) - denoting_parts()


def inexpressible_parts() -> frozenset[str]:
    """Denoting parts the SURFACE cannot carry. PHASE 13.0's third category.

    Must be a subset of denoting_parts(): an inexpressible part that no
    signature can constrain would be neither meaning nor decoration -- just
    unreachable state, and a place for something to hide.
    """
    den = denoting_parts()
    if not _INEXPRESSIBLE <= den:
        raise ProjectionUnsound(
            f"_INEXPRESSIBLE {sorted(_INEXPRESSIBLE - den)} is not denoting. An "
            "inexpressible part no signature can constrain is unreachable "
            "state, not a third category.")
    return frozenset(_INEXPRESSIBLE)


def expressible_denoting_parts() -> frozenset[str]:
    """Denoting AND sayable -- what Phase 6's isolation claim still covers."""
    return denoting_parts() - inexpressible_parts()


# A fixed, legal value for the illocutionary coda. `force` is required by Scene
# and by render(), so it is normalised to a constant rather than dropped.
CANON_FORCE = "ka"


def project_node(n: EventNode) -> EventNode:
    return EventNode(
        root=n.root,
        # The aspect ROOT denotes (signatures use aspect_root_any); the
        # repetition COUNT never does, so it collapses to 1.
        aspect=(n.aspect[0], 1) if n.aspect is not None else None,
        degree=None, modal=None, tense=None, quant=None,
        orient=sorted(n.orient),
        edges=[(rel, project_node(c)) for rel, c in n.edges],
        # ⛔ KEPT, NOT STRIPPED. The residue is meaning the surface cannot
        # carry; π removes DECORATION, not meaning. Dropping it here would
        # delete the very ambiguity Phase 13 exists to create.
        residue=n.residue,
    )


def project(scene: Scene, *, force: str | None = None) -> Scene:
    """π. Raises ProjectionUnsound if the schema no longer justifies it."""
    denoting_parts()          # guard runs on every projection; it is cheap
    return Scene(node=project_node(scene.node), force=force or CANON_FORCE)
