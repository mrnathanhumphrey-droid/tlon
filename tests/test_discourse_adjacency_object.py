"""THE OBJECT IS A DIRECTED RELATION, AND THE SPATIAL MODEL IS REFUSED. $0.

⛔⛔ THREE DERIVATIONS OF M-ADJACENCY HAVE NOW FAILED THE SAME WAY — a distance
gate (ρ_wide, deleted by RULING 2), a contact AXIS (a line; generated 7 cells,
failed 5), and ORTHOGONAL REGISTERS (a coordinate system; decided 16 of 25 block
cells by a geometric theorem nothing in Tlön licenses). Each announced itself in
VOCABULARY before it announced itself in cells.

⭐ SO THE GUARD IS ON THE NAMES, NOT THE PROSE. It walks the AST of every module
in `tlon/discourse/` and refuses any *identifier* built from spatial vocabulary.
Prose is deliberately NOT scanned: the refusal has to be explainable, and a guard
that forbids the words needed to explain it would be uninstallable. **Naming is
where an intuition becomes structure**, and that is the surface worth holding.

⛔ LIMITATION, STATED RATHER THAN PAPERED OVER: a synonym evades this ("register",
"proximity", "field"). It is a tripwire on the known failure, not a proof of
absence.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from tlon.discourse import adjacency as A
from tlon.discourse.evidential import EVIDENTIALS

PKG = pathlib.Path(A.__file__).parent


def _identifiers(path: pathlib.Path) -> set[str]:
    """Every name this module DEFINES or BINDS. Not string contents, not prose."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.update(a.arg for a in node.args.args)
                names.update(a.arg for a in node.args.kwonlyargs)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names


def _offences(names: set[str]) -> list[tuple[str, str]]:
    return [(n, w) for n in names for w in A.BANNED_METRIC_VOCABULARY
            if w.replace(" ", "_") in n.lower()]


# ══ THE GUARD ════════════════════════════════════════════════════════════
def test_no_module_in_the_discourse_package_NAMES_anything_spatial():
    """⛔⛔ THE WHOLE POINT. `contact_axis`, `orthogonal_register`,
    `residue_distance` — every failed derivation would have had to name one."""
    bad = {}
    for p in sorted(PKG.glob("*.py")):
        off = _offences(_identifiers(p))
        if off:
            bad[p.name] = off
    assert not bad, f"spatial vocabulary in identifiers: {bad}"


def test_the_guard_ACTUALLY_FIRES_on_a_planted_offender(tmp_path):
    """⛔ RED-PROOF. A guard that has never come back positive is not known to
    work — and the mutation must be asserted to have applied, not assumed."""
    p = tmp_path / "planted.py"
    p.write_text("def orthogonal_register(axis_of_contact):\n    return 1\n",
                 encoding="utf-8")
    names = _identifiers(p)
    assert "orthogonal_register" in names, "the mutation did not apply"
    off = _offences(names)
    assert off, "the guard did not fire on a planted offender"
    assert {w for _, w in off} >= {"orthogonal", "axis"}


def test_a_clean_module_does_NOT_trip_the_guard(tmp_path):
    """⭐ The other half of the red-proof: a guard that fires on everything is
    equally useless."""
    p = tmp_path / "clean.py"
    p.write_text("def reachable_from(frm, to):\n    return True\n",
                 encoding="utf-8")
    assert not _offences(_identifiers(p))


def test_the_refusal_marker_is_greppable_and_countable():
    """An exemption nobody can find is not an exemption, it is a hole."""
    src = pathlib.Path(A.__file__).read_text(encoding="utf-8")
    assert src.count(A.REFUSAL_MARKER) >= 1


# ══ THE OBJECT IS A RELATION, NOT A SPACE ════════════════════════════════
def test_the_module_exposes_NO_distance_like_callable():
    """⛔ If a d(·,·) ever appears, the object has silently become a space."""
    assert not _offences(set(dir(A)))


def test_adjacency_is_asked_DIRECTIONALLY():
    """⭐ `smooth(a, b)` takes an ordered pair. A symmetric call signature would
    make the directedness unstateable."""
    import inspect
    args = list(inspect.signature(A.smooth).parameters)
    assert args == ["frm", "to"], args


# ══ THE DERIVATION IS NOT SHIPPED UNTIL IT CONVERGES ═════════════════════
def test_smooth_RAISES_because_the_cells_have_not_converged():
    a, b = "xöl", "plun"
    with pytest.raises(NotImplementedError, match="NOT CONVERGED"):
        A.smooth(a, b)


def test_the_diagonal_refuses_with_RULING_8s_reason():
    with pytest.raises(A.AdjacencyError, match="DIAGONAL"):
        A.smooth("xöl", "xöl")


@pytest.mark.parametrize("form", ["xöl", "ten", "plun", "mar", "hrin", "nem",
                                  "mir", "frax"])
def test_a_forced_membership_returns_its_category(form):
    assert A.category(form)


@pytest.mark.parametrize("form,why", [("hrix", "sensory"), ("xos", "idealist")])
def test_an_unforced_membership_REFUSES_rather_than_returning(form, why):
    """⛔⛔ THE MARKED-BECOMES-SHIPPED FAILURE, BLOCKED AT THE CALL SITE. `hrix`
    ("heard") is category-ambiguous between non-visual sensory and hearsay
    reportative — DIFFERENT Aikhenvald categories. `xos` is off-map in Earth
    typology and arguably on-map in an idealist world."""
    with pytest.raises(A.AdjacencyError, match="NOT forced"):
        A.category(form)


def test_the_refusal_points_at_the_record():
    with pytest.raises(A.AdjacencyError) as e:
        A.category("hrix")
    assert "GROUPING_MUTATION_TEST" in str(e.value)


def test_unsettled_names_exactly_the_two_open_memberships():
    assert set(A.unsettled()) == {"hrix", "xos"}


# ══ MEMBERSHIP IS KEYED ON THE FROZEN LEXICON ════════════════════════════
def test_every_M_form_has_a_membership_and_no_ghosts():
    """⭐ RULING 1 held once; it holds structurally here."""
    assert set(A.MEMBERSHIP) == set(EVIDENTIALS)


def test_the_categories_are_the_five_from_the_typology():
    assert {c for c, _ in A.MEMBERSHIP.values()} == {
        "evidential-proper", "marginal", "judgement", "volition", "off-map"}


def test_the_evidential_proper_core_is_four_forms():
    core = [f for f, (c, _) in A.MEMBERSHIP.items() if c == "evidential-proper"]
    assert sorted(core) == sorted(["xöl", "hrix", "ten", "plun"])
