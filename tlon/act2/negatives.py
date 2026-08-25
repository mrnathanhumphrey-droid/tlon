"""HARD NEGATIVES — mining class confusions out of refused proposals.

⛔⛔ THE FAILURE LOG IS THE HIGHEST-VALUE PART OF THE TRAINING CORPUS AND IT WAS
BEING SAMPLED. `tools/act2_f1.py` recorded only the top 4 refusal reasons, so 4
of 8 measured failures were kept. Negatives that are a sample of a sample
under-train exactly the discipline the fine-tune exists to install.

⭐ AND STRING-PARSING THE ERROR MESSAGE WOULD BE THE SAME MISTAKE ONE LEVEL DOWN.
A refusal message is prose written for a human; it can be reworded and the miner
would silently stop finding anything. This walks the PROPOSAL against the frozen
lexicon and reports every misassignment directly: which form, which slot it was
put in, and which class it actually belongs to.

⭐⭐ THE SLOT→CLASS MAP IS DERIVED FROM THE PRODUCT SCHEMA, NOT RE-SPELT. For each
field, the class whose form-set is exactly that field's enum. A hand-written
second copy of the mapping is the Ohtani-61 shape -- two spellings of one rule,
free to disagree -- and this one cannot go stale because it is recomputed from
the schema the gate actually enforces.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..grammar import classes as C
from ..product import schema as PS


class MiningError(RuntimeError):
    pass


def slot_class_map() -> dict[str, str]:
    """field name -> lexicon class, derived by matching enum sets."""
    lex = C.load()["classes"]
    by_forms = {frozenset(v): k for k, v in lex.items()}
    schema = PS.json_schema()
    node = schema["properties"]["node"]["properties"]
    out: dict[str, str] = {}

    def take(name: str, spec: dict) -> None:
        enum = spec.get("enum")
        if enum is None:
            enum = (spec.get("items") or {}).get("enum")
        if enum is None:
            return
        forms = frozenset(e for e in enum if e is not None)
        cls = by_forms.get(forms)
        if cls is not None:
            out[name] = cls

    for name, spec in node.items():
        take(name, spec)
    take("force", schema["properties"]["force"])
    edge = node.get("edges", {}).get("items", {}).get("properties", {})
    if "relator" in edge:
        take("relator", edge["relator"])

    missing = set(C.load()["classes"]) - set(out.values())
    if missing:
        raise MiningError(
            f"no schema field maps to lexicon class(es) {sorted(missing)}. The "
            "schema moved under this derivation, so a whole class of confusion "
            "would go unmined and the hard negatives would be silently partial.")
    return out


@dataclass(frozen=True)
class ClassError:
    """One form in the wrong box. The unit of the contrastive signal."""
    form: str
    used_as: str          # the slot it was put in
    expected: str         # the class that slot requires
    actual: str | None    # the class it really belongs to; None = not a form

    @property
    def invented(self) -> bool:
        """⭐ THE DISTINCTION THE PRE-FLIGHT TURNED UP: a misassignment is a
        class error and is trainable; an invented form is a different failure
        entirely. Measured hosted: 4 misassignments, 0 inventions."""
        return self.actual is None

    def as_negative(self) -> str:
        if self.invented:
            return f"{self.form!r} is not a Tlön form at all."
        return (f"{self.form!r} is class {self.actual}, not {self.expected} — "
                f"it cannot fill the {self.used_as} slot.")


def _where(form: str, lex) -> str | None:
    for cls, items in lex.items():
        if form in items:
            return cls
    return None


def class_errors(proposal: dict) -> list[ClassError]:
    """Every misassignment in a proposal. Walks the tree; does not stop at the
    first, because the gate raises on the first and that is what truncated the
    record in the first place."""
    lex = C.load()["classes"]
    slots = slot_class_map()
    found: list[ClassError] = []

    def check(slot: str, value) -> None:
        if value is None or slot not in slots:
            return
        expected = slots[slot]
        if isinstance(value, list):
            for v in value:
                check(slot, v)
            return
        if not isinstance(value, str) or value in lex[expected]:
            return
        found.append(ClassError(form=value, used_as=slot, expected=expected,
                                actual=_where(value, lex)))

    def node(n) -> None:
        if not isinstance(n, dict):
            return
        for slot in ("root", "orient", "aspect_root", "degree", "modal",
                     "tense", "quant"):
            check(slot, n.get(slot))
        for e in (n.get("edges") or []):
            if isinstance(e, dict):
                check("relator", e.get("relator"))
                node(e.get("node"))

    if not isinstance(proposal, dict):
        return found
    check("force", proposal.get("force"))
    node(proposal.get("node"))
    return found


def mine(records) -> dict:
    """Aggregate class errors across many refused proposals.

    ⛔ EVERY error from every record. No top-N, no truncation: the whole point of
    this module is that the previous version kept a sample.
    """
    errors: list[ClassError] = []
    for r in records:
        errors.extend(class_errors(r))
    by_pair: dict[str, int] = {}
    by_class: dict[str, int] = {}
    for e in errors:
        by_pair[f"{e.actual or '∅'}→{e.expected}"] = (
            by_pair.get(f"{e.actual or '∅'}→{e.expected}", 0) + 1)
        by_class[e.expected] = by_class.get(e.expected, 0) + 1
    return {"n_errors": len(errors),
            "invented": sum(e.invented for e in errors),
            "misassigned": sum(not e.invented for e in errors),
            "by_confusion": dict(sorted(by_pair.items(), key=lambda kv: -kv[1])),
            "by_slot_class": dict(sorted(by_class.items(), key=lambda kv: -kv[1])),
            "negatives": [e.as_negative() for e in errors]}
