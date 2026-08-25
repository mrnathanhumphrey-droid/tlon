"""THE FOUR RE-DECOMPOSITION AXES — PREREG §6. Pre-committed, in order.

⛔⛔ THE ORDER IS FIXED AND IS NOT A PREFERENCE. On a firing the protocol says
re-decompose from a BOUNDED, PRE-COMMITTED set with a stopping rule -- because an
unbounded search for an axis that moves is how a null becomes a result. The set
is these four, the order is 1→2→3→4, and both were locked before any harness line
existed.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..grammar import classes as C

PRODUCT_LEXICON = "e2b8527010231a81fd31b6eeb9de3d8c"


class AxisError(RuntimeError):
    pass


@dataclass(frozen=True)
class Axis:
    key: str
    order: int
    setting: str
    hypothesis: str
    allowed_forces: tuple[str, ...] | None = None    # None = all
    allowed_modals: tuple[str, ...] | None = None    # () = none permitted
    residue_on: bool = False
    validity_mode: str = "hard_retry"                # hard_retry|soft_penalty|curriculum
    lexicon: str = PRODUCT_LEXICON
    expensive: bool = False

    def permits(self, force: str, modal: str | None) -> bool:
        if self.allowed_forces is not None and force not in self.allowed_forces:
            return False
        if self.allowed_modals is not None and modal is not None \
                and modal not in self.allowed_modals:
            return False
        return True

    def check_lexicon(self) -> None:
        """⛔ AXIS 4 FORKS THE LEXICON, SO EVERY OTHER AXIS MUST PROVE IT DID
        NOT. A run that silently used a different lexicon than it declared is a
        result about a different language."""
        live = C.load()["_hash"]
        if self.lexicon != live:
            raise AxisError(
                f"axis {self.key!r} declares lexicon {self.lexicon} but the "
                f"loaded lexicon is {live}. Act-2 lexicons are frozen per "
                "setting and must never be confused with each other, and no "
                "Act-2 lexicon may reach tlon/product/.")


BASELINE = Axis(
    key="baseline", order=0, setting="as shipped",
    hypothesis="drift is measurable with the product's own configuration")

# 1 — the pragmatic subspace. Stance-deployment is where the apparatus gives the
#     most room for convention, and 0 of 156 roots name a self or an addressee.
AXIS_1_RESTRICTED = Axis(
    key="force_evidential", order=1, setting="restricted",
    hypothesis="drift lives in stance-deployment first",
    allowed_forces=("ka",), allowed_modals=())
AXIS_1_FULL = Axis(
    key="force_evidential", order=1, setting="full",
    hypothesis="drift lives in stance-deployment first")

# 2 — ⭐ WHERE THE SEALED RESEARCH SAYS TO LOOK. H2's headline is that a pact
#     formed around a distinction the grammar STRUCTURALLY COULD NOT EXPRESS.
AXIS_2_OFF = Axis(key="residue", order=2, setting="off",
                  hypothesis="the private dialect forms in the unsayable (H2)")
AXIS_2_ON = Axis(key="residue", order=2, setting="on", residue_on=True,
                 hypothesis="the private dialect forms in the unsayable (H2)")

# 3 — how the constraint is enforced changes whether drift is measurable at all
#     or entangled with validity-failure.
AXIS_3 = tuple(
    Axis(key="validity_mode", order=3, setting=m, validity_mode=m,
         hypothesis="retry dynamics either enable or mask drift")
    for m in ("hard_retry", "soft_penalty", "curriculum"))

# 4 — the expensive one; each setting needs its own frozen, hashed lexicon and a
#     re-fine-tune. Registered now so it cannot be invented later.
AXIS_4_PLACEHOLDER = Axis(
    key="lexicon_tightness", order=4, setting="(unbuilt)",
    hypothesis="constraint-tightness has a sweet spot for drift",
    lexicon="(a separate frozen lexicon per setting — not yet minted)",
    expensive=True)

ORDER = ("force_evidential", "residue", "validity_mode", "lexicon_tightness")


def contrast_pair(key: str) -> tuple[Axis, Axis]:
    """The two settings whose difference IS the axis test."""
    if key == "force_evidential":
        return AXIS_1_RESTRICTED, AXIS_1_FULL
    if key == "residue":
        return AXIS_2_OFF, AXIS_2_ON
    if key == "validity_mode":
        return AXIS_3[0], AXIS_3[1]
    raise AxisError(
        f"axis {key!r} has no runnable contrast pair yet. `lexicon_tightness` "
        "needs a minted lexicon per setting (PREREG §6, expensive) and must not "
        "be faked with the product's.")
