"""The glosses are grounding, not documentation.

Spec §3.1: "if a gloss can be pluralized, it is wrong." The glosses are what the
frozen gloss-grounded auditor reads (PHASE2_DESIGN §4) -- they are the one place
the generator cannot move, and therefore the one place English semantics enter
the system. A noun in a gloss grounds a nounless language on nouns.

Nate caught `fox` = "it pools, stands still as water" on 2026-08-18. This test
exists so the next one is caught by CI instead of by him.

Heuristic screen, not a parser: a curated list of nominal tokens plus the
`-ness` nominaliser. Anything it flags gets hand-judged and either rewritten or
added to ALLOWED with a reason.
"""
from __future__ import annotations
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tlon.grammar import classes as C   # noqa: E402

# Concrete and abstract nouns that could plausibly appear in a gloss of a
# happening. Every one of these names a THING; Sur has none.
BANNED = {
    "water", "light", "weight", "event", "thing", "things", "object",
    "sound", "noise", "air", "earth", "fire", "smoke", "ash", "dust",
    "sand", "stone", "wood", "blood", "time", "moment", "place", "space",
    "shape", "colour", "color", "form", "image", "word", "story", "path",
    "way", "life", "death", "breath", "heart", "mind", "body", "surface",
    "flow", "edge", "point", "line", "mass", "matter", "substance",
}
# Judged acceptable with a reason. Nothing goes here without one.
ALLOWED: dict[str, str] = {}

_NESS = re.compile(r"\b\w+-?ness\b", re.I)
_WORD = re.compile(r"[a-zäöü]+", re.I)


def offences(text: str) -> list[str]:
    hits = [w for w in _WORD.findall(text.lower()) if w in BANNED]
    hits += _NESS.findall(text)
    return hits


def test_no_nouns_in_root_glosses():
    bad: list[str] = []
    for form, g in C.load()["classes"]["R"].items():
        if form in ALLOWED:
            continue
        hit = offences(g)
        if hit:
            bad.append(f"  {form} = {g!r}  ← {sorted(set(hit))}")
    assert not bad, (
        "root glosses naming a THING (Sur has no nouns):\n" + "\n".join(bad))


def test_no_nouns_in_particle_glosses():
    lex = C.load()["classes"]
    bad: list[str] = []
    for cls in ("O", "L", "A", "M", "D", "Q", "T", "F"):
        for form, g in lex[cls].items():
            hit = offences(g.replace("_", " "))
            if hit:
                bad.append(f"  [{cls}] {form} = {g!r}  ← {sorted(set(hit))}")
    assert not bad, "particle glosses naming a THING:\n" + "\n".join(bad)


# Concrete things whose NAME must not stand in for the happening. Nate,
# 2026-08-19: "'it stones' to describe a stone is cheating." Naming the event
# after the object smuggles the object back into a language built to refuse it.
# Only nouns that are NOT already genuine verbs. "it rains" and "it pools"
# describe happenings; "it stones" and "it ashes" only relabel the object.
# ⚠️ TRIPWIRE, NOT A PROOF. The distinction is semantic and cannot be fully
# regexed — this catches the clear cases so a human catches the rest.
OBJECT_NOUNS = {
    "stone", "dust", "mud", "ash", "seed", "shadow", "sand", "star", "sun",
    "moon", "edge", "vein", "band", "stripe", "web", "knot", "coal", "bone",
    "salt", "wing", "eye", "hand", "leaf", "root",
}
# Attested exception. Borges' own word; the golden conformance test anchors on it.
NOUN_VERB_ALLOWED = {"mlö": "attested — Borges' translator gives 'it mooned'"}

_NV = re.compile(r"^it (\w+)(?P<tail>.*)$", re.I)


def _stems(verb: str) -> set[str]:
    v = verb.lower()
    out = {v}
    if v.endswith("es"):
        out.add(v[:-2])
    if v.endswith("s"):
        out.add(v[:-1])
    return out


def noun_verb_offence(gloss: str) -> str | None:
    """Flag `it <object-noun>s` unless a real PROCESS clause rescues it.

    A stative rescue ('is mineral', 'is solar') does not count -- it renames the
    object as an adjective instead of saying what happens.
    """
    m = _NV.match(gloss.strip())
    if not m:
        return None
    if not (_stems(m.group(1)) & OBJECT_NOUNS):
        return None
    tail = m.group("tail").strip()
    rest = tail[1:].strip() if tail.startswith(",") else tail
    if rest and not rest.lower().startswith("is "):
        return None                     # a genuine process clause rescues it
    return f"'{gloss}' names the object, not the happening"


def test_no_root_gloss_names_its_object():
    bad = []
    for form, g in C.load()["classes"]["R"].items():
        if form in NOUN_VERB_ALLOWED:
            continue
        hit = noun_verb_offence(g)
        if hit:
            bad.append(f"  {form}: {hit}")
    assert not bad, (
        "roots glossed by verbing their own noun (Sur has no nouns):\n"
        + "\n".join(bad))


def test_the_noun_verb_screen_can_actually_fire():
    """Red-proof. Without this the test above could be passing vacuously."""
    assert noun_verb_offence("it stones, is mineral")
    assert noun_verb_offence("it dusts")
    assert noun_verb_offence("it suns, is solar")
    # rescued by a real process clause
    assert noun_verb_offence("it sands, granulates") is None
    assert noun_verb_offence("it stars, pricks brightly") is None
    # not object-nouns at all
    assert noun_verb_offence("it endures cold and unyielding") is None
    assert noun_verb_offence("it startles") is None
    # genuine impersonal verbs must NOT be flagged
    assert noun_verb_offence("it rains") is None
    assert noun_verb_offence("it pools, lies still and level") is None


def test_every_root_gloss_is_a_predication():
    """A gloss must read as something HAPPENING: it starts with 'it'."""
    bad = [f"  {f} = {g!r}" for f, g in C.load()["classes"]["R"].items()
           if not g.lower().startswith("it ")]
    assert not bad, "root glosses that are not predications:\n" + "\n".join(bad)


def test_the_screen_can_actually_fire():
    """Red-proof: a null from a screen that cannot detect is worthless."""
    assert offences("it pools, stands still as water") == ["water"]
    assert offences("it sees, is seen-ness") == ["seen-ness"]
    assert offences("it moons, lunates") == []
