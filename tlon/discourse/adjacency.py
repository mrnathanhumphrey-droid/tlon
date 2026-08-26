"""THE M-ADJACENCY OBJECT — A DIRECTED, NON-METRIC REACHABILITY RELATION.

⛔⛔ WHAT THIS OBJECT IS NOT, AND WHY THE REFUSAL IS STRUCTURAL.

Three separate derivations of M-adjacency have now failed by importing a spatial
model, each time in better clothes:

  1. §3's residue-distance region gate — deleted by RULING 2 as a category error
     against *"successive, temporal, not spatial"*.
  2. the "contact axis" — a LINE, which generated 7 cells and failed 5.
  3. "orthogonal registers off the axis" — a COORDINATE SYSTEM, which decided
     16 of 25 block cells by a geometric theorem nothing in Tlön licenses.

The lit recon (`docs/LIT_RECON_M_ADJACENCY_2026_08_26.md`) settled the formal
object and it is not spatial in any of those senses: an epistemic accessibility
relation is **a directed binary relation over states, specified by relational
properties** (serial / transitive / Euclidean / reflexive / symmetric), and
**there is no d(·,·) anywhere in it.** Aikhenvald's evidential structure is a
**subsumption hierarchy — a partial order**, not a scale.

⇒ ADJACENCY MEANS *REACHABLE-FROM*, DIRECTED. IT NEVER MEANS *NEAR*.

⭐ THE VOCABULARY IS THE TELL, so it is guarded lexically rather than by
intention. Every prior failure announced itself in words before it announced
itself in cells — "axis", "orthogonal", "region", "turn not traversal". A guard
on the words catches the next one at the moment it is typed instead of after a
table is built on it. It is a LEXICAL guard and can be evaded by a synonym; it is
a tripwire, not a proof, and `# METRIC-REFUSAL` is the visible opt-out.
"""
from __future__ import annotations

from .evidential import EVIDENTIALS, EvidentialError, resolve

#: ⛔ Words that mean a SPACE. Their presence in this package is the deleted
#: model returning. Enforced by tests/test_discourse_no_metric_vocabulary.py.
BANNED_METRIC_VOCABULARY: tuple[str, ...] = (           # METRIC-REFUSAL
    "orthogonal", "axis", "axes", "dimension", "distance",   # METRIC-REFUSAL
    "coordinate", "perpendicular", "metric space", "nearness",  # METRIC-REFUSAL
)                                                        # METRIC-REFUSAL

#: The marker that makes a line exempt. Typed deliberately, greppable, and
#: countable — an invisible exemption would defeat the guard.
REFUSAL_MARKER = "# METRIC" + "-REFUSAL"


class AdjacencyError(RuntimeError):
    pass


# ══ THE CATEGORIES — MODAL TYPOLOGY, NOT GEOMETRY ════════════════════════
#: ⭐ Verdicts from the grouping mutation test, 2026-08-26. A membership that is
#: not FORCED **must not be used as though it were**; it is recorded here so the
#: next reader inherits the doubt instead of the conclusion.
FORCED = "forced"
DEFENSIBLE = "defensible-either-way"        # ⛔ picked. Marked, not shipped.
UNDETERMINED = "undetermined"

#: form → (category, verdict). Categories are typological, from the lit recon:
#: evidentiality proper (information-source) · judgement modality (commitment)
#: · volitive modality (desire) — three DIFFERENT semantic domains, per
#: Chung & Timberlake and Bybee, not three positions on one scale.
MEMBERSHIP: dict[str, tuple[str, str]] = {
    "xöl":  ("evidential-proper", FORCED),        # visual sensory
    "ten":  ("evidential-proper", FORCED),        # non-visual sensory
    "plun": ("evidential-proper", FORCED),        # inferential
    "hrix": ("evidential-proper", UNDETERMINED),  # ⛔ "heard" is sensory OR hearsay
    "mar":  ("marginal", FORCED),                 # memory is not a SOURCE
    "hrin": ("judgement", FORCED),
    "nem":  ("judgement", FORCED),
    "mir":  ("volition", FORCED),
    "frax": ("volition", FORCED),
    "xos":  ("off-map", DEFENSIBLE),              # ⛔ idealist world; see the doc
}


def category(form: str) -> str:
    """The typological category of `form`. ⛔ REFUSES when the membership is not
    FORCED — an undetermined membership returned as a plain string is how a
    marked claim becomes a shipped one."""
    resolve(form)
    cat, verdict = MEMBERSHIP[form]
    if verdict is not FORCED:
        raise AdjacencyError(
            f"{form!r} ({EVIDENTIALS[form]}) is provisionally {cat!r}, verdict "
            f"{verdict!r} — NOT forced. Reading it as a settled category is the "
            "failure this record exists to prevent. See "
            "docs/GROUPING_MUTATION_TEST_2026_08_26.md.")
    return cat


def unsettled() -> dict[str, tuple[str, str]]:
    """Every membership still carrying doubt. ⭐ A list that can be printed is a
    list that gets closed; a caveat in prose is one that decays."""
    return {f: v for f, v in MEMBERSHIP.items() if v[1] is not FORCED}


def smooth(frm: str, to: str) -> bool:
    """Is `to` reachable from `frm` as a continuation of the unfolding?

    ⛔⛔ RAISES ON PURPOSE — same discipline as `base_convention`. The cells are
    DERIVED but NOT CONVERGED: the independent-derivation check against the
    held-back reasons has not run. Encoding a table before that check is exactly
    the plausible-default-measured-as-a-result failure the §8.1 refusal has
    prevented for eight days, and the last table to look finished failed its own
    mutation test on half its cells.

    ⭐ The derivation, pending convergence, is in
    docs/GROUPING_MUTATION_TEST_2026_08_26.md — 6 core cells derived (all six
    asymmetric on `plun`), 6 core cells UNDETERMINED.
    """
    resolve(frm)
    resolve(to)
    if frm == to:
        raise AdjacencyError(
            f"{frm!r} → {frm!r} is the DIAGONAL, excluded by RULING 8: a series "
            "in which nothing changes is not a succession. It is neither ABIDE, "
            "CLOSE nor BREAK — it is the degenerate non-move.")
    raise NotImplementedError(
        "M-adjacency is DERIVED but NOT CONVERGED. The evidential-proper core "
        "has 6 cells derived and 6 undetermined; the peripheral forms are not "
        "derived at all. See docs/GROUPING_MUTATION_TEST_2026_08_26.md.")
