"""THE LITERARY RENDER — Scene -> English. The second surface, where craft lives.

⛔⛔ THIS IS NOT A PRETTIER GLOSS PIPELINE. It is a SIBLING of `grammar/gloss.py`:
a second pure function of the same Scene, reading the same EventNode structure
and the same frozen lexicon. `gloss.py` IS NEVER TOUCHED -- it is the
measurement instrument and the honest surface, and a test asserts its output is
unchanged on a fixed scene set so this work cannot drift into it.

⛔⛔ NO MODEL CALL, EVER. The moment this asks a model to "make it prettier" it
becomes ungated text -- the `note` / `refused_objects` category, the one surface
the parser cannot vouch for -- and it can drift from the Scene. Faithfulness here
is INHERITED BY CONSTRUCTION: every content word it emits comes from a lexicon
gloss the Scene actually contains, up to inflection. That claim is mechanical and
it is tested, not asserted.

⭐⭐ THE REGISTER IS BORGES' OWN, AND THE LEXICON ENCODES HIS SENTENCE.
`Hlör u fang axaxaxas mlö` -- `hlör` = upward, `u` = BEYOND, `fang` = it streams,
`mlö` = it moons -- which he renders:

    "upward, behind the onstreaming, it mooned."

That line is the whole specification. Read what it does:
  · orientations lead, as bare adverbs                        -> "upward"
  · an embedded happening NOMINALISES to a gerund             -> "the onstreaming"
  · the head happening stays an IMPERSONAL VERB, and is last  -> "it mooned"

⭐ SO IT STAYS NOUNLESS, AND THAT IS THE POINT (Nate). The reveal is not normal
English -- it is high-gloss NOUNLESS English. No agents, no "one who looms", no
"a landlord": those would smuggle back exactly the permanence the language
refuses. A gerund is not a thing; it is a happening being referred to, which is
the only kind of reference Tlon has. Every embedded node becomes "a streaming",
"a hollowing and voiding" -- never a doer.

⭐ THE LATITUDE CLAUSE, PRE-REGISTERED. This render may vary in HOW it says an
impression -- arrangement, rhythm, which coda voices the force. It may never vary
in WHICH impression it says. The latitude is in the music, never in the meaning,
and `tests/test_literary_render.py` polices that line by requiring the partition
induced by `literary()` to equal the partition induced by `gloss()`.
"""
from __future__ import annotations

from ..grammar import classes as C
from ..grammar.gloss import _ASP, _REL          # noqa: PLC2701
from ..grammar.parse import EventNode, Scene

# ⛔ `_REL` AND `_ASP` ARE IMPORTED FROM THE GLOSS, NOT RE-SPELT HERE. Two tables
# of relator English would be two chances to disagree about what a Scene means,
# and the whole faithfulness claim is that these two surfaces describe one thing.
# Importing also makes every relator and aspect word gloss-justified for free.

VOWELS = "aeiou"

# ── the renderer's own closed vocabulary ──────────────────────────────────
# ⛔⛔ THIS LIST IS THE FAITHFULNESS BOUNDARY AND IT IS DELIBERATELY TINY. Every
# word the render emits is either drawn from a lexicon gloss the Scene contains
# (up to inflection) or is one of these -- function words and frame words that
# carry no meaning of their own. A content word appearing here that is not in
# the Scene would be ADDED MEANING: a lie dressed as craft.
FUNCTION_WORDS = frozenset("""
a an and as at be being but by does in is it its let means not of or out so the
then to up until since ere for
""".split())


# ── English inflection, applied to lexicon glosses ────────────────────────
# ⛔ INFLECTION, NOT INVENTION. These turn a lexeme the Scene already contains
# into another form of THE SAME lexeme. A test asserts every produced gerund
# shares a stem with its source, so this can never quietly become a thesaurus.
_GERUND_EXCEPTIONS = {"begins": "beginning", "forgets": "forgetting"}


def _base(word: str) -> str:
    """3rd-person singular -> bare stem. 'hollows' -> 'hollow'."""
    if word == "is":
        return "be"
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    # ⛔ 'zzes' NOT 'zes': 'buzzes' -> 'buzz', but 'blazes' -> 'blaze'. The loose
    # rule produced "blazzing" for `fal` (it blazes overhead).
    for suffix in ("sses", "shes", "ches", "xes", "zzes", "oes"):
        if word.endswith(suffix):
            return word[:-2]
    return word[:-1] if word.endswith("s") else word


def gerund(word: str) -> str:
    """'hollows' -> 'hollowing'. 'is' -> 'being'. 'dies' -> 'dying'."""
    if word in _GERUND_EXCEPTIONS:
        return _GERUND_EXCEPTIONS[word]
    stem = _base(word)
    if stem == "be":
        return "being"
    if stem.endswith("ie"):
        return stem[:-2] + "ying"
    if stem.endswith("e") and not stem.endswith(("ee", "oe", "ye")):
        return stem[:-1] + "ing"
    # single-syllable consonant-vowel-consonant doubles: 'drip' -> 'dripping'.
    # Restricted to one vowel so 'gather' does not become 'gatherring'.
    if (len(stem) >= 3 and stem[-1] not in VOWELS + "wxy"
            and stem[-2] in VOWELS and stem[-3] not in VOWELS
            and sum(c in VOWELS for c in stem) == 1):
        return stem + stem[-1] + "ing"
    return stem + "ing"


def _article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in VOWELS else "a"


# ── force as VOICE, not as a parenthetical ────────────────────────────────
# ⭐ EVERY CODA IS SENTENCE-FINAL, WHICH IS WHERE TLON PUTS THE FORCE MORPHEME --
# the shape of the English mirrors the shape of the utterance. And every content
# word here ("wondering", "urging", "denied") is the gloss's OWN force word, so
# the coda voices the force without naming anything new.
_FORCE_CODA = {"ASSERT": ".", "ASK": " — is it so?",
               "WONDER": " — a wondering.", "URGE": " — an urging.",
               "DENY": " — and it is denied."}

# ⭐ ASPECT AS TEXTURE. The repetition count is ICONIC in Tlon -- the morpheme is
# literally repeated (tes -> testesas) -- so the English repeats too. A guttering
# thing fades in the prose; an unceasing thing runs on. Each echo reuses a word
# from the aspect's own gloss phrase, asserted by test, so reps stay recoverable
# from the render and no new word enters.
_ASPECT_ECHO = {"unceasing": "and unceasingly",
                "punctual_iterated": "and again",
                "inceptive": "and beginning",
                "terminative": "and guttering",
                "habitual": "and habitually",
                "momentary": "and an instant"}

# ⭐ TENSE AS A TEMPORAL PHRASE. Built from the gloss word plus function words
# only -- 'then future' -> 'then in the future'. Nothing is named that the gloss
# does not already name.
_TENSE_PROSE = {"now": "now", "always": "always", "until": "until then",
                "since": "since then", "ere": "ere then",
                "momentarily": "momentarily",
                "then_past": "then in the past",
                "then_future": "then in the future"}


def _aspect_phrase(aspect_root: str, reps: int, lex) -> str:
    name = lex["A"][aspect_root]
    phrase = _ASP.get(name, name)
    if reps <= 1:
        return phrase
    return ", ".join([phrase] + [_ASPECT_ECHO[name]] * (reps - 1))


def _frames(n: EventNode, lex) -> list[str]:
    """quant, tense and evidential -- how often, when, and how it is known."""
    out = []
    if n.quant is not None:
        out.append(lex["Q"][n.quant])
    if n.tense is not None:
        name = lex["T"][n.tense]
        out.append(_TENSE_PROSE.get(name, name.replace("_", " ")))
    if n.modal is not None:
        # ⭐ IMPERSONAL PASSIVE — "as it is remembered", never "as I remember".
        # The language has 0 roots for a self or an addressee, so the English
        # must not quietly supply one. This is the seed of stance-without-
        # speaker the conversant will be built on.
        out.append(f"as it is {lex['M'][n.modal]}")
    return out


def _orientations(n: EventNode, lex) -> str:
    words = [lex["O"][o].replace("_", " ") for o in sorted(n.orient)]
    return " and ".join(words)


def _edges(n: EventNode, lex) -> list[str]:
    out = []
    for rel, child in sorted(n.edges, key=lambda e: e[0]):
        name = _REL.get(lex["L"][rel], lex["L"][rel].lower())
        out.append(f"{name} {nominal(child)}")
    return out


def _verbs(n: EventNode, lex) -> list[str]:
    """The root gloss, split into its phrases.

    ⛔⛔ EVERY PHRASE, NOT JUST THE HEAD, AND A COLLISION PROVES WHY. Two roots
    share a head verb -- `nöl` "it stills, silences" and `hläx` "it stills, goes
    unbreathing". Rendering only the head would collapse two pi-DISTINCT scenes
    into one identical sentence, which is exactly the failure the reveal must
    never commit.
    """
    return [p.strip() for p in lex["R"][n.root][3:].split(",")]


def nominal(n: EventNode) -> str:
    """A node in EMBEDDED position: a gerund phrase. "a streaming and flowing on".

    ⛔ NOT A DOER. English wants to give an embedded happening an agent -- "one
    who streams" -- and that would grant exactly the permanence Tlon refuses. A
    gerund refers to a happening without positing anything that has it.
    """
    lex = C.load()["classes"]
    core = " and ".join(gerund(p.split()[0]) + "".join(f" {w}" for w in p.split()[1:])
                        for p in _verbs(n, lex))
    if n.degree is not None:
        core = f"{lex['D'][n.degree]}ly {core}"
    head = f"{_article(core)} {core}"
    mods = []
    if n.aspect is not None:
        mods.append(_aspect_phrase(n.aspect[0], n.aspect[1], lex))
    orient = _orientations(n, lex)
    if orient:
        mods.append(orient)
    mods += _edges(n, lex)
    mods += _frames(n, lex)
    if not mods:
        return head
    # ⛔⛔ THE EMBEDDED NODE'S SCOPE MUST BE BOUNDED, AND A REAL COLLISION PROVES
    # IT. The gloss marks embedding with ⟨...⟩; prose has no brackets, and
    # without a boundary these two DIFFERENT scenes render identically:
    #     head X, edges=[(AT, Y{edges=[(TOWARD, Z)]})]   -- Z hangs off Y
    #     head X, edges=[(AT, Y), (TOWARD, Z)]           -- both hang off X
    # Both would be "at a Y-ing, toward a Z-ing, it Xs." -- the literary surface
    # collapsing a structural distinction the gloss keeps. Em-dashes restore the
    # boundary and read as prose rather than as notation.
    return f"{head} — " + ", ".join(mods) + " —"


def clause(n: EventNode) -> str:
    """A node in HEAD position: an impersonal verb, and it comes last.

    Order follows the gloss, which follows the Tlon surface: how often / when /
    how known, then where, then what it attaches to, then the happening itself.
    """
    lex = C.load()["classes"]
    parts = _frames(n, lex)
    orient = _orientations(n, lex)
    if orient:
        parts.append(orient)
    parts += _edges(n, lex)

    phrases = _verbs(n, lex)
    core = "it " + " and ".join(phrases)
    if n.degree is not None:
        core = f"it {lex['D'][n.degree]}ly " + " and ".join(phrases)
    parts.append(core)
    if n.aspect is not None:
        parts.append(_aspect_phrase(n.aspect[0], n.aspect[1], lex))
    return ", ".join(parts)


def literary(scene: Scene) -> str:
    """Scene -> the surface a visitor experiences. Deterministic. No model call."""
    lex = C.load()["classes"]
    body = clause(scene.node)
    # A dash that closes an embedded scope already separates; a comma after it
    # would be punctuation stacked on punctuation.
    body = body.replace("—, ", "— ")
    body = body[:1].upper() + body[1:]
    return body + _FORCE_CODA.get(lex["F"][scene.force], ".")
