"""Lexicon loading, validation, and morpheme classification.

The lexicon is the single source of truth. Everything downstream (FSM tables,
parser, tokenizer manifest, enumeration) derives from it and from its hash.
"""
from __future__ import annotations
import functools
import hashlib
import pathlib
import re

import yaml

LEXICON_PATH = pathlib.Path(__file__).with_name("lexicon.yaml")

# Class labels, in the order they must appear in a predication (spec §4.1).
SLOT_ORDER = ("Q", "T", "M", "O", "CLAUSE")
CLASSES = ("R", "O", "L", "A", "M", "D", "Q", "T", "F")


class LexiconError(RuntimeError):
    pass


@functools.lru_cache(maxsize=1)
def load() -> dict:
    body = LEXICON_PATH.read_bytes()
    lex = yaml.safe_load(body)
    lex["_hash"] = hashlib.blake2b(body, digest_size=16).hexdigest()
    _validate(lex)
    return lex


def _validate(lex: dict) -> None:
    onsets = lex["phonotactics"]["onsets"]
    nuclei = lex["phonotactics"]["nuclei"]
    codas = lex["phonotactics"]["codas"]
    legal = {o + v + c for o in onsets for v in nuclei for c in codas}
    if len(legal) != lex["phonotactics"]["legal_syllable_count"]:
        raise LexiconError("declared syllable count does not match the table")

    seen: dict[str, str] = {}
    for cls, table in lex["classes"].items():
        for form in table:
            if form not in legal:
                raise LexiconError(f"{form!r} ({cls}) is not a legal syllable")
            if form in seen:
                raise LexiconError(
                    f"{form!r} is in both {seen[form]} and {cls}; "
                    "classes must be surface-disjoint for LL(1)")
            seen[form] = cls
    closer = lex["aspect_closer"]
    if closer in seen:
        raise LexiconError(f"aspect closer {closer!r} collides with {seen[closer]}")

    # Reduplication must be uniquely decomposable: no aspect root may be a
    # repetition of another, or 'axaxas' could parse two ways.
    roots = list(lex["classes"]["A"])
    for a in roots:
        for b in roots:
            if a != b and len(a) % len(b) == 0 and a == b * (len(a) // len(b)):
                raise LexiconError(f"aspect roots {a!r}/{b!r} are not uniquely decomposable")


@functools.lru_cache(maxsize=1)
def form_class() -> dict[str, str]:
    """Surface form -> class label, for the single-syllable classes."""
    lex = load()
    return {f: c for c, tbl in lex["classes"].items() for f in tbl}


@functools.lru_cache(maxsize=1)
def _aspect_re() -> re.Pattern:
    lex = load()
    roots = sorted(lex["classes"]["A"], key=len, reverse=True)
    alt = "|".join(re.escape(r) for r in roots)
    closer = re.escape(lex["aspect_closer"])
    return re.compile(rf"^(?P<reps>(?:{alt})+){closer}$")


def classify(token: str) -> tuple[str, object]:
    """Return (class_label, payload). Payload is the form, or (root, count) for A."""
    fc = form_class()
    if token in fc:
        return fc[token], token
    m = _aspect_re().match(token)
    if m:
        reps = m.group("reps")
        lex = load()
        for r in sorted(lex["classes"]["A"], key=len, reverse=True):
            if reps.startswith(r) and len(reps) % len(r) == 0 and reps == r * (len(reps) // len(r)):
                count = len(reps) // len(r)
                if 1 <= count <= lex["constraints"]["MAX_ASPECT_REPS"]:
                    return "A", (r, count)
                raise LexiconError(f"aspect {token!r} exceeds MAX_ASPECT_REPS")
    raise LexiconError(f"unknown morpheme {token!r}")


def morph_cost(cls: str, payload: object) -> int:
    """Length in syllables (spec §4.2: reduplicated aspect costs its syllables)."""
    if cls == "A":
        return payload[1] + 1          # k repetitions + the closer
    return 1


def constraints() -> dict:
    return load()["constraints"]


def class_sizes() -> dict[str, int]:
    return {c: len(t) for c, t in load()["classes"].items()}
