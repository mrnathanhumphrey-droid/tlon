"""Lexicon loading, validation, and morpheme classification.

The lexicon is the single source of truth. Everything downstream (FSM tables,
parser, tokenizer manifest, enumeration) derives from it and from its hash.
"""
from __future__ import annotations
import functools
import hashlib
import os
import pathlib
import re

import yaml

LEXICON_PATH = pathlib.Path(__file__).with_name("lexicon.yaml")

#: ⛔⛔ THE FROZEN LEXICON IS THE DEFAULT AND STAYS THE DEFAULT. Every number in
#: the research campaign was measured against `lexicon.yaml`
#: (blake2b-16 e2b8527010231a81fd31b6eeb9de3d8c) and every artifact records that
#: hash. With `TLON_LEXICON` unset this module behaves byte-for-byte as it
#: always has — `test_lexicon_expanded.py` asserts exactly that, because an
#: override that leaked into the default path would re-point the instrument
#: under every standing verdict without changing a single line of their prose.
#:
#: ⭐ The override exists so the PUZZLE can speak a larger language without the
#: research having to agree. Set it to a filename beside this module, or to an
#: absolute path.
LEXICON_ENV = "TLON_LEXICON"

# Class labels, in the order they must appear in a predication (spec §4.1).
SLOT_ORDER = ("Q", "T", "M", "O", "CLAUSE")
CLASSES = ("R", "O", "L", "A", "M", "D", "Q", "T", "F")


class LexiconError(RuntimeError):
    pass


def lexicon_path() -> pathlib.Path:
    """Which lexicon this process speaks.

    ⛔ A MISSING OVERRIDE RAISES; IT DOES NOT FALL BACK. Silently reverting to
    the frozen lexicon because a path was mistyped would run the puzzle on 156
    roots while every log line said "expanded" — the run would look healthy and
    be measuring a different language.
    """
    override = os.environ.get(LEXICON_ENV)
    if not override:
        return LEXICON_PATH
    p = pathlib.Path(override)
    if not p.is_absolute():
        p = pathlib.Path(__file__).with_name(override)
    if not p.exists():
        raise LexiconError(
            "%s=%r does not exist (resolved to %s). Refusing to fall back to "
            "the frozen lexicon: a run that quietly speaks a different "
            "language than it reports is worse than one that stops."
            % (LEXICON_ENV, override, p))
    return p


@functools.lru_cache(maxsize=1)
def load() -> dict:
    body = lexicon_path().read_bytes()
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
