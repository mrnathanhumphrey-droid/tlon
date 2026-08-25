"""The discourse layer — what coheres one utterance to the next.

⛔ SPEC: `docs/SPEC_DISCOURSE_LAYER_v0.1_2026_08_25.md`, and read the RULINGS
block at the top of it before building here — §3's residue-distance region gate
was WITHDRAWN as a category error and ρ_wide no longer exists as a parameter.

Nothing in this package may re-spell a lexicon form. `evidential.EVIDENTIALS` is
sourced from the frozen lexicon at import and is the only admissible key.
"""
