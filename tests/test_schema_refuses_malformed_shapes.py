"""THE VALIDATOR MUST REFUSE, NEVER CRASH. $0.00, offline.

⛔⛔ THIS COST A LIVE GATE RUN. After a 75-minute fine-tune, `speak` had already
scored **100.0 % (64/64)** when a single `render` proposal carried a nested LIST
under `edges`. `_node` guards its own argument and `validate` guards the
proposal, but the EDGE ELEMENT was assumed to be a dict:

    rel = check("relator", "L", (e or {}).get("relator"))
    AttributeError: 'list' object has no attribute 'get'

The whole 64-probe measurement died. ⭐ **A malformed emission is a FAILED
emission — it must be counted, not thrown.** The gate's job is to refuse
everything that is not legal, and "not legal" includes shapes nobody anticipated.

⛔ The sibling defect: `check()` did `value not in lex[cls]`, which raises
TypeError on an UNHASHABLE value. A list as a root crashed the same way.
"""
from __future__ import annotations

import pytest

from tlon.product import schema as PS

GOOD = {"node": {"root": "klung"}, "force": "ka"}


def _valid(p) -> bool:
    PS.validate(p)
    return True


def test_the_good_proposal_still_validates():
    """The floor: if this ever fails, every refusal below is meaningless."""
    assert _valid(GOOD)


# ══ THE EXACT SHAPE THAT KILLED THE GATE ═════════════════════════════════
def test_a_LIST_edge_is_refused_not_crashed():
    """⛔⛔ THE MEASURED CRASH, replayed. `edges: [[...]]` instead of
    `edges: [{...}]`."""
    bad = {"node": {"root": "klung",
                    "edges": [[{"relator": "hul", "node": {"root": "frem"}}]]},
           "force": "ka"}
    with pytest.raises(PS.ProposalError, match="edge must be an object"):
        PS.validate(bad)


@pytest.mark.parametrize("edge", [
    ["a", "b"], "hul", 3, [], None, [{"relator": "hul"}]])
def test_every_non_object_edge_is_refused(edge):
    """The general form — an edge that is not an object, whatever it is."""
    bad = {"node": {"root": "klung", "edges": [edge]}, "force": "ka"}
    with pytest.raises(PS.ProposalError):
        PS.validate(bad)


# ══ THE UNHASHABLE SIBLING ═══════════════════════════════════════════════
@pytest.mark.parametrize("field,value", [
    ("root", ["klung"]), ("root", {"a": 1}), ("root", 7),
    ("degree", ["sim"]), ("modal", {"x": 1}), ("tense", ["kril"]),
    ("quant", [1, 2]), ("aspect_root", ["pal"])])
def test_an_unhashable_or_non_string_form_is_refused_not_crashed(field, value):
    """⛔ `value not in lex[cls]` raises TypeError on a list or dict. A lookup is
    not a type check, and the validator must not assume its input is sane."""
    bad = {"node": {"root": "klung", field: value}, "force": "ka"}
    with pytest.raises(PS.ProposalError):
        PS.validate(bad)


@pytest.mark.parametrize("orient", [[["fen"]], [{"a": 1}], [3]])
def test_a_non_string_orientation_is_refused(orient):
    bad = {"node": {"root": "klung", "orient": orient}, "force": "ka"}
    with pytest.raises(PS.ProposalError):
        PS.validate(bad)


# ══ NOTHING BELOW MAY RAISE ANYTHING BUT ProposalError ═══════════════════
DEFORMED = [
    {"node": [], "force": "ka"},
    {"node": "klung", "force": "ka"},
    {"node": {"root": "klung", "edges": {"relator": "hul"}}, "force": "ka"},
    {"node": {"root": "klung", "edges": [{"relator": ["hul"]}]}, "force": "ka"},
    {"node": {"root": "klung", "edges": [{"relator": "hul", "node": []}]},
     "force": "ka"},
    {"node": {"root": "klung", "orient": "fen"}, "force": "ka"},
    {"node": {"root": "klung", "aspect_reps": "many", "aspect_root": "pal"},
     "force": "ka"},
    {"node": {"root": "klung"}, "force": ["ka"]},
    {"node": None, "force": "ka"},
    [], "not a proposal", 42,
]


@pytest.mark.parametrize("bad", DEFORMED)
def test_no_deformed_proposal_escapes_as_a_non_ProposalError(bad):
    """⭐⭐ THE PROPERTY THAT MATTERS, not any single shape. Whatever a model
    emits, the validator's answer is legal-or-refused. Any other exception type
    is a crash, and a crash in the gate destroys the run around it."""
    try:
        PS.validate(bad)
    except PS.ProposalError:
        pass
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"{type(exc).__name__} escaped instead of ProposalError: {exc}")


def test_aspect_reps_that_is_not_a_number_is_refused():
    """`int("many")` raises ValueError, which is not a ProposalError either."""
    bad = {"node": {"root": "klung", "aspect_root": "pal", "aspect_reps": "many"},
           "force": "ka"}
    with pytest.raises(PS.ProposalError):
        PS.validate(bad)
