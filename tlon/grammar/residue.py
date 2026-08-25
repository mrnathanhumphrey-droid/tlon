"""The residue: the DENOTING ∧ INEXPRESSIBLE component. PHASE 13.0.

WHAT IT IS. A coordinate in a fixed integer lattice. The scene carries it, a
signature can constrain it, π keeps it -- and `render()` structurally cannot
emit it. Two scenes differing only in residue produce the SAME full utterance,
which is the irreducible full-utterance ambiguity every previous lever failed to
produce.

⛔⛔ WHY IT MUST BE A COORDINATE AND NEVER A STRING. A string-valued residue is
a side door expression walks through while every other check passes: you would
have a "coordinate" that is secretly a lyric fragment -- denotation-carrying,
unstripped, and invisible to a scanner that only reads names and notes. So the
type is asserted, not assumed, and `validate()` raises on anything that is not a
tuple of ints. That single constraint is the copyright line and the
expression-leak defence made MECHANICAL rather than disciplinary.

⛔⛔ WHY THE METRIC IS FIXED AND IMMOVABLE, NEVER LEARNED. From
`novelty/distance.py`'s own docstring: an embedding distance "would let it buy
novelty by shifting the space rather than by having a new impression". A LEARNED
residue metric reintroduces exactly that failure inside the one dimension nobody
can read -- the generator could manufacture novelty by moving a space no auditor
can see. L1 on an integer lattice is exact, cheap, auditable and immovable, and
it is the same property that made tree-edit distance the right choice for R.

⭐ THE METRIC DOES DOUBLE DUTY, and that is the whole reason the phase is
buildable: it makes the residue CONVENTIONABLE (nearby residues can be gestured
at similarly, so a pair can build shared convention -- the Pictionary property)
and AUDITABLE (R penalises residue-DISTANCE, not residue-identity) with one
stroke. A free categorical residue is neither.
"""
from __future__ import annotations

Residue = tuple[int, ...]


class ResidueTypeError(TypeError):
    """The residue is not a coordinate. Raised, never warned."""


def validate(r) -> Residue | None:
    """Assert the residue is a coordinate. ⛔ THIS IS A SECURITY CHECK.

    A str is iterable and would otherwise pass a casual `tuple(r)`, arriving as
    a tuple of characters and carrying text into a field nothing else scans.
    """
    if r is None:
        return None
    if isinstance(r, (str, bytes)):
        raise ResidueTypeError(
            f"residue must be a coordinate, got {type(r).__name__} {r!r:.40}. "
            "A text-valued residue is how source expression reaches a field no "
            "name-and-notes scanner reads.")
    if not isinstance(r, tuple):
        raise ResidueTypeError(
            f"residue must be a tuple of ints, got {type(r).__name__}")
    for x in r:
        if isinstance(x, bool) or not isinstance(x, int):
            raise ResidueTypeError(
                f"residue coordinates must be ints, got "
                f"{type(x).__name__} {x!r:.20}")
    return r


def distance(a: Residue | None, b: Residue | None) -> float:
    """L1 on the lattice. Fixed, exact, immovable -- see the module docstring.

    ⛔ `None` MEANS UNKNOWN, AND MIXING KNOWN WITH UNKNOWN IS AN ERROR HERE.
    In `match`, unknown is benign -- it is the listener's position and cannot
    violate a constraint. In the METRIC it is not benign, because either
    convention is exploitable: call it maximally distant and dropping the
    residue buys free novelty; call it zero and dropping it makes everything
    read as a repeat. So it RAISES.

    This is safe because the generator's own scenes always carry a residue (π
    keeps it), so a known-vs-unknown comparison here means something upstream
    dropped it -- which is a bug worth hearing about rather than absorbing.
    Both-unknown is the legacy case and is 0.0.
    """
    if a is None and b is None:
        return 0.0
    if a is None or b is None:
        raise ResidueTypeError(
            "comparing a known residue with an unknown one. In the metric that "
            "is a bug, not a value: either convention for it is exploitable. "
            "Something upstream dropped a residue π should have kept.")
    if len(a) != len(b):
        raise ResidueTypeError(
            f"residues live in different spaces: dim {len(a)} vs {len(b)}. "
            "The metric is only defined within one lattice.")
    return float(sum(abs(x - y) for x, y in zip(a, b)))


def normalized(a: Residue | None, b: Residue | None, span: int = 4) -> float:
    """distance scaled to ~[0,1] so it composes with the tree-edit weights.

    `span` is the lattice's per-axis extent and is a FIXED parameter of the
    residue space, not a learned scale.
    """
    d = distance(a, b)          # raises on known-vs-unknown, by design
    if a is None:
        return 0.0              # both unknown: the legacy, residue-free case
    denom = span * len(a)
    return min(1.0, d / denom) if denom else 0.0
