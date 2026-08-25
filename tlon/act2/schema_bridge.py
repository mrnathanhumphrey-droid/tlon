"""The Scene schema for Act 2, DERIVED from the product's — never re-spelt.

⛔⛔ ONE SCHEMA, ONE LEXICON, ONE GATE. `product/schema.py` builds its structured
-output schema from the frozen lexicon and validates against it; Act 2 uses THE
SAME object so a drift run cannot silently be measuring a different language than
the product speaks. A second hand-written schema here would be the Ohtani-61
shape: two spellings of one rule, free to disagree.

⭐ THE ONE DIFFERENCE, AND WHY. The product's schema requires `refused_objects`
and `note` -- the coverage-edge reveal, which exists because a HUMAN is being
told what the language let go. In Act 2 the audience is another model and there
is no English input to refuse anything FROM, so those two fields are dropped for
the `speak` task. They are kept for `render`, which is the product's own
translate task with the conversation in context.
"""
from __future__ import annotations

from ..product import schema as PS

#: Fields that exist to tell a human what was let go. Not applicable to a turn.
_HUMAN_FACING = ("refused_objects", "note")


def scene_schema() -> dict:
    """A Scene proposal with no human-facing reveal fields."""
    base = PS.json_schema()
    props = {k: v for k, v in base["properties"].items()
             if k not in _HUMAN_FACING}
    required = [r for r in base["required"] if r not in _HUMAN_FACING]
    missing = set(_HUMAN_FACING) - set(base["properties"])
    if missing:
        raise RuntimeError(
            f"the product schema no longer has {sorted(missing)}, so this "
            "derivation is stale and Act 2 would be validating against a shape "
            "the product does not use.")
    return {"type": "object", "required": required, "properties": props}


def translate_schema() -> dict:
    """The product's own schema, unchanged — used for production probes."""
    return PS.json_schema()


def scene_to_proposal(scene) -> dict:
    """`Scene` -> a dict in the PROPOSAL schema. The inverse of `PS.validate`.

    ⛔⛔ THIS FUNCTION DID NOT EXIST, AND ITS ABSENCE COST A WHOLE FINE-TUNE.
    `canon()` was the only Scene->dict in the codebase, so the corpus builder
    used it -- but `canon()` is the CANONICAL HASHING FORM behind the impression
    digest, not the proposal schema. It spells an edge `["nix", {…}]` and an
    aspect `["sor", 2]`, where the gate and the model-facing schema require
    `{"relator": …, "node": …}` and `aspect_root`/`aspect_reps`.

    **The model learned the hashing dialect and the gate rejected it: 39 of 44
    render failures.** The two shapes agree on a bare scene, which is why the
    defect stayed invisible until edges appeared.

    ⭐ IT LIVES BESIDE `scene_schema()` ON PURPOSE. The schema that DECLARES the
    shape and the writer that PRODUCES it are now one module, so they cannot
    drift the way the trainer and the gate did.
    """
    return {"force": scene.force, "node": _node_to_proposal(scene.node)}


def _node_to_proposal(n) -> dict:
    out: dict = {"root": n.root}
    if n.aspect:
        out["aspect_root"], out["aspect_reps"] = n.aspect[0], int(n.aspect[1])
    for field in ("degree", "modal", "tense", "quant"):
        v = getattr(n, field, None)
        if v is not None:
            out[field] = v
    if n.orient:
        out["orient"] = sorted(n.orient)
    if n.edges:
        out["edges"] = [{"relator": rel, "node": _node_to_proposal(child)}
                        for rel, child in n.edges]
    return out
