"""THE M-SPINE — the evidential inventory, KEYED ON THE FROZEN LEXICON.

⛔⛔ THE SPEC MISSPELLED FIVE OF THE TEN FORMS, AND THE ONTOLOGY WAS FINE. The
ten ways-of-holding map one-for-one; `sköl` `xoth` `nek` `dul̈` `wir` simply do
not exist. They came from the grammar doc's §3.5 illustrative table, which the
lexicon corrected during minting — so the failure was reading the illustration
instead of the normative file, and it is the same failure every time: **bind to
`classes.py`, never to prose.**

⭐ IT WOULD HAVE FAILED LOUDLY, NOT SILENTLY — `PS.validate` refuses a form that
is not in class M — but it would have failed after a table was built on it. This
module makes the binding structural so the question cannot come up again:
`EVIDENTIALS` is READ FROM THE FROZEN LEXICON AT IMPORT. There is no literal list
of M forms anywhere in this package.

⛔ WHAT THIS MODULE DELIBERATELY DOES NOT CONTAIN: the base convention table
(§8.1) — what each way-of-holding conventionally calls for as an abiding
response. That is unbuilt design work, and each of its ten rows must be
red-teamed against the spec's own test (*"is it forced by the ontology or picked?
The picked ones are duct tape"*). A plausible-looking default table shipped here
would be ten pieces of duct tape that nobody ever revisits, so `base_convention`
RAISES instead of returning one.
"""
from __future__ import annotations

from ..grammar import classes as _classes


class EvidentialError(RuntimeError):
    pass


def _load() -> dict[str, str]:
    table = _classes.load()["classes"]["M"]
    return {form: gloss for form, gloss in table.items()}


#: form → gloss, straight from the frozen lexicon. THE ONLY ADMISSIBLE KEYS.
EVIDENTIALS: dict[str, str] = _load()

#: gloss → form, for callers that think in English (the spec does).
BY_GLOSS: dict[str, str] = {gloss: form for form, gloss in EVIDENTIALS.items()}

#: ⛔ THE SPEC'S FIVE WRONG SPELLINGS, RECORDED SO THE NEXT READER OF v0.1 GETS A
#: POINTER INSTEAD OF A MISS. A stale name that merely fails lookup teaches
#: nothing; one that names its replacement closes the loop.
SPEC_v0_1_MISSPELLINGS: dict[str, str] = {
    "sköl": "xöl",      # seen
    "xoth": "xos",      # dreamt
    "nek": "nem",       # denied
    "dul̈": "hrin",      # doubted
    "wir": "mir",       # wished
}


def resolve(form: str) -> str:
    """Return `form` if it is a real evidential; refuse — with the fix — if it is
    one of the spec's five ghosts.

    ⭐ THE REFUSAL CARRIES THE REPLACEMENT. "Not in class M" is true and useless;
    "you mean `xöl`" is what stops the same table being rebuilt wrong twice.
    """
    if form in EVIDENTIALS:
        return form
    if form in SPEC_v0_1_MISSPELLINGS:
        right = SPEC_v0_1_MISSPELLINGS[form]
        raise EvidentialError(
            f"{form!r} is SPEC v0.1's spelling and does not exist in the frozen "
            f"lexicon — the form is {right!r} ({EVIDENTIALS[right]}). The ten "
            "ways-of-holding are correct in the spec; five of the surface forms "
            "are not. Key on tlon.discourse.evidential.EVIDENTIALS.")
    raise EvidentialError(
        f"{form!r} is not in lexicon class M. The ten evidentials are: "
        + ", ".join(f"{f} ({g})" for f, g in EVIDENTIALS.items()))


def base_convention(form: str) -> dict:
    """§8.1 — what this way-of-holding conventionally calls for. **UNBUILT.**

    ⛔⛔ RAISES ON PURPOSE. This is the load-bearing derivation of the whole
    discourse layer and it is the one thing v0.1 does not contain. Returning a
    reasonable-looking default would be the worst available outcome: the arena
    would run, σ_cp would have a number, and the number would be measuring ten
    guesses that nobody remembered were guesses.

    ⭐ WHEN IT IS BUILT, EACH ROW CARRIES ITS OWN VERDICT — forced by the
    ontology, or picked. The picked ones are duct tape and must be labelled as
    such in the row itself, not in a footnote.
    """
    resolve(form)
    raise NotImplementedError(
        "§8.1 (the base convention table) is UNBUILT. Ten rows of "
        "way-of-holding → conventional abiding response, each red-teamed "
        "'forced by the ontology, or picked?'. It is deliberately absent rather "
        "than defaulted: a plausible default here would be measured by the "
        "arena and reported as a result. See the RULINGS block in "
        "docs/SPEC_DISCOURSE_LAYER_v0.1_2026_08_25.md.")
