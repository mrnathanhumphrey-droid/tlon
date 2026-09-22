"""⛔⛔ THE CARRY PREDICATE — ONE DEFINITION, AND IT IS ENFORCED, NOT ASKED FOR.

⛔⛤ THIS MODULE REVERSES A DECISION RECORDED IN
`tools/act2_build_conversations.py`, AND THE RETRACTION IS THE POINT.
That builder's docstring says:

    "SO THE CONTINUITY IS INHERITED, NOT IMPOSED. A rule of mine ('the reply
     must reuse a root') would teach the model my tic and it would surface as
     repetitive collapse."

The reasoning was sound and the premise was false. What the English dialogue
inherited was not neutral continuity — it was ANTI-continuity, measured at
**root recurrence 5.3% within a conversation against a 7.5% shuffled null,
p=0.000, BELOW CHANCE over 500 shuffles**. The prompt had asked the writer for
"a FRESH impression ... answering an image with an image", and in a language
whose roots ARE happenings, a fresh impression is by construction a different
happening. Inheriting that relation inherited its absence.

⭐ The old worry is still real and is why this is a BAND, not a maximum.
Forcing maximum reuse would produce the repetitive collapse that decision
feared — and separately, the English pairs with the highest overlap measured as
near-PARAPHRASES ("Relieved it went okay" / "Relieved it worked out okay"), an
echo that breaks the puzzle from the other side by letting a player solve a
turn without learning anything. So the predicate demands BOTH DIRECTIONS:
**at least one happening carried, and at least one happening new.**

⛔⛔ WHERE THIS MAY AND MAY NOT BE APPLIED. The builder translates each English
line through `prop.propose(english)`, which never sees the prior turn — the
scene is a faithful, context-free function of its English line, which is why
the English->root map measured deterministic (`dims`->`flöx` 59/59,
`waited`->`hlun` 44/44, `breathing`->`hram` 49/49). Therefore:

    STAGE 1, the English dialogue   STEER here. Rejecting costs one call and
                                    a regenerated conversation can differ.
    STAGE 2, the rendered scene     VERIFY here only. A resample CANNOT
                                    conjure a happening the English does not
                                    name, so retrying here exhausts the retry
                                    budget, truncates, and drops the
                                    conversation. Measured: only 0.1% of
                                    existing P->T pairs share a happening-word
                                    in English, so a stage-2 gate would reject
                                    essentially everything, forever.

`scene_carry` therefore returns a verdict for recording and dropping. It must
never be wired to a resample loop.
"""
from __future__ import annotations

import functools
import json
import pathlib
import re
from typing import NamedTuple

VOCAB_PATH = pathlib.Path(__file__).with_name("happening_words.json")

# ⭐ PRE-REGISTERED, and they are written down HERE rather than in the run that
# reports them, so the run cannot be read against a threshold chosen after
# seeing it. The sample build is judged on these three numbers.
#
# ⛔⛔ NOT MOVED AFTER THE FIRST SAMPLE, AND THE DISTINCTION MATTERS.
# That sample measured english_carry at 19.7%/32.1% against the 0.60 bar. The
# INSTRUMENT was then found invalid — a closed vocabulary from the old corpus
# reading new English, see `english_carry` — and it was replaced by one whose
# recall is 76.6% on the same sentences. Replacing a broken instrument is
# legitimate; relaxing a bar to clear a number is not, so no value below has
# changed. `scene_band_min`, the exact vocabulary-free criterion and the one
# that actually decides whether to fund a build, is untouched at 0.50.
#
# ⭐ `scene_band_target` was RAISED from 0.50 to 0.65 for the steered recipe,
# and the direction is the whole justification: raising a bar after a run
# missed it is legitimate, lowering one is not. The unsteered arm measured
# 40.9% [26.4, 55.4] against a 0.50 bar and was UNDECIDED, so the steer has to
# clear a bar that the thing it replaces could not have cleared by luck.
#
# ⛔⛤ AND n IS PART OF THE RULE NOW. The first sample printed "VERDICT:
# ACCEPTED" off 22 pairs and the next identical run printed NOT ACCEPTED —
# 50.0% then 31.8%, one recipe. Calling that thin was not enough; a verdict
# that a rerun can flip is not a verdict. So `min_pairs_to_decide` and a CI
# that must not straddle the floor are conditions for printing a verdict AT
# ALL, not commentary underneath one.
ACCEPTANCE = {
    "english_carry_min": 0.60,   # P->T pairs where the reply takes a happening up
    "scene_band_target": 0.65,   # the steered recipe's point estimate
    "scene_band_ci_floor": 0.50,  # and its 95% CI lower bound must clear this
    "min_pairs_to_decide": 150,  # below this the run reports UNDECIDED, always
    "echo_max": 0.10,            # pairs carrying every root and adding none
}

_WORD = re.compile(r"[a-z']+")


class CarryError(RuntimeError):
    """The vocabulary is missing or malformed."""


class Carry(NamedTuple):
    """⭐ `ok` is never read without `reason` being available to log.

    A gate that returns a bare boolean gets debugged by rerunning it, which
    for this gate means paying the proposer again.
    """

    ok: bool
    carried: frozenset
    added: frozenset
    reason: str

    @property
    def echo(self) -> bool:
        """Carried everything and brought nothing — the paraphrase trap."""
        return bool(self.carried) and not self.added


@functools.lru_cache(maxsize=1)
def load_vocabulary() -> dict:
    """The measured happening-word scores, with their provenance.

    ⛔ RAISES if absent. A silent fallback to "every word counts" would make
    the gate pass everything and the build would look like it worked — the
    exact failure mode this whole arc has been about.
    """
    if not VOCAB_PATH.exists():
        raise CarryError(
            "⛔⛔ %s is missing. It is generated by "
            "`tools/act2_score_happening_words.py` from a corpus that pairs "
            "english with scene; without it the carry gate cannot tell a "
            "happening from a mood and MUST NOT run." % VOCAB_PATH.name)
    body = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
    for key in ("words", "threshold", "baseline", "provenance"):
        if key not in body:
            raise CarryError("⛔ %s lacks %r" % (VOCAB_PATH.name, key))
    if not body["words"]:
        raise CarryError("⛔ %s scores no words" % VOCAB_PATH.name)
    return body


@functools.lru_cache(maxsize=1)
def happening_words() -> dict:
    """Word -> the root it reliably lands on.

    ⭐ Data-derived, not a guessed part of speech. `feels` is a verb and has
    no dominant root at all (purity 0.11); `dims` lands on `flöx` every time.
    The distinction the gate needs is not grammatical, and naming it "verbs"
    would have been me supplying an answer the measurement already gave.

    ⭐⭐ AND IT NEEDS NO STEMMER. Inflections of one happening land on one
    root — `waited`/`waiting`/`wait` are all `hlun` — so comparing predicted
    ROOTS handles the morphology that comparing word strings could not.
    """
    v = load_vocabulary()
    thr = v["threshold"]
    return {w: s["root"] for w, s in v["words"].items()
            if s["purity"] >= thr}


def english_happenings(line: str) -> frozenset:
    """The scored happening-words present in one English line."""
    return frozenset(_WORD.findall((line or "").lower())) & frozenset(
        happening_words())


def english_roots(line: str) -> frozenset:
    """The roots this English line is predicted to land on.

    ⛔⛤ THE GATE COMPARES THESE, NOT WORDS. An earlier version compared word
    strings and a test caught it: "I waited far too long" / "A waiting
    stretches out" shares no word, yet both land on `hlun`. That is the exact
    shape the carry instruction produces, because the Tlönian names a
    happening by nominalising it — so a string comparison would have rejected
    precisely the replies the new prompt is for, and the regeneration cost
    would have looked like the prompt failing.
    """
    table = happening_words()
    return frozenset(table[w] for w in _WORD.findall((line or "").lower())
                     if w in table)


_SUFFIXES = ("iness", "ness", "ingly", "ing", "edly", "ed", "es", "s", "en")
_STEM_STOP = frozenset("""a an the and or but so then than that this those
these it its is are was were be been being am i me my we our you your he she
they them his her their of in on at to for from with by as if not no nor do
does did done have has had will would can could should may might must just
about into over under again very too much more most some any all own same don
now there here when where how what who whom which while up down out off once
got get""".split())


def stem(word: str) -> str:
    """⭐ DELIBERATELY CRUDE, AND APPLIED TO BOTH SIDES.

    It need not be linguistically right, only to map a word and its
    nominalisation onto one token — `stuck`/`stuck-ness`, `rolled`/`rolling`,
    `dark`/`darkening`. Applied to both lines, a wrong-but-consistent stem
    still matches correctly.

    ⛔ ITERATIVE, because the suffixes STACK. `darkening` is `dark` + `en` +
    `ing`, and stripping one layer leaves `darken`, which does not match the
    `dark` in the line it answers — a real miss found by a test built from the
    sample's own sentences.
    """
    word = word.strip("-")
    for _ in range(3):
        for suf in _SUFFIXES:
            if word.endswith(suf) and len(word) - len(suf) >= 3:
                base = word[: -len(suf)]
                if (len(base) > 3 and base[-1] == base[-2]
                        and base[-1] not in "aeiou"):
                    base = base[:-1]             # stirring -> stirr -> stir
                word = base
                break
        else:
            break
    return word


def stems(line: str) -> frozenset:
    return frozenset(stem(w) for w in _WORD.findall((line or "").lower())
                     if w not in _STEM_STOP and len(w) > 2)


def english_carry(provoking: str, reply: str) -> Carry:
    """Does the reply take up a happening the provoking line named?

    ⛔⛤ TUNED FOR RECALL ON PURPOSE, AND THE FIRST VERSION WAS NOT.
    A closed vocabulary measured on the OLD corpus was used to judge English
    written under the NEW prompt, and it scored 23.4% where the writer was in
    fact complying almost every time — `I got stuck in traffic` answered by
    `A stuck-ness is spreading`, `the wind picked up` by `A picking-up stirs`.
    51 of 72 "failures" had no scored word in the PROVOKING line at all. That
    number was vocabulary coverage wearing compliance's clothes: an instrument
    built on one distribution and read against another.

    ⭐ THE ASYMMETRY THAT SETS THE TUNING. This gate exists only to avoid
    paying to translate a dialogue that will not carry. A false PASS costs one
    translation and is then caught exactly, and for free, by `scene_carry`
    downstream. A false REJECT throws away compliant material AND pays to
    generate a replacement. So the two errors are not equal and the gate
    should lean permissive: it is a drift-catcher, not the acceptance test.

    Measured over both corpora — recall on English the new prompt wrote,
    against pass-rate on the shipped corpus known to teach anti-carry:

        vocabulary alone   23.4% recall    1.1% on the old corpus
        stem alone         69.1% recall    4.1%
        union (this)       76.6% recall    4.9%     <- 15.6x separation
    """
    carried = (english_roots(provoking) & english_roots(reply)) or (
        stems(provoking) & stems(reply))
    p_words = frozenset(_WORD.findall((provoking or "").lower()))
    r_words = frozenset(_WORD.findall((reply or "").lower()))
    added = r_words - p_words
    if not carried:
        return Carry(False, carried, added,
                     "no happening carried: the reply names none of the "
                     "happenings the line named")
    if not added:
        return Carry(False, carried, added,
                     "echo: the reply adds no word the line did not have")
    return Carry(True, carried, added, "ok")


def scene_carry(prior_roots, reply_roots) -> Carry:
    """The exact band, on roots. ⛔ VERIFICATION ONLY — never a resample loop.

    See the module docstring: the proposer cannot see the prior turn, so a
    failure here is a fact about the English that was already written, not
    something a retry can repair.
    """
    prior = frozenset(prior_roots or ())
    reply = frozenset(reply_roots or ())
    carried, added = prior & reply, reply - prior
    if not reply:
        return Carry(False, carried, added, "the reply has no root at all")
    if not carried:
        return Carry(False, carried, added, "no root carried from the prior turn")
    if not added:
        return Carry(False, carried, added,
                     "echo: every root is carried and none is new")
    return Carry(True, carried, added, "ok")


GLOSS_SYNONYMS_PATH = pathlib.Path(__file__).with_name("gloss_synonyms.json")


@functools.lru_cache(maxsize=1)
def gloss_synonyms() -> dict:
    """`{root: frozenset(its happening-family)}`, from the gloss judgment.

    ⛔ PUZZLE-ONLY. See `tools/act2_build_gloss_synonyms.py`: these families are
    a hand-made SEMANTIC reading of the root glosses, appropriate for a product
    crib and not a measured claim. A root with no family is simply absent, and
    every caller must then fall back to the exact root.
    """
    if not GLOSS_SYNONYMS_PATH.exists():
        return {}
    body = json.loads(GLOSS_SYNONYMS_PATH.read_text(encoding="utf-8"))
    out = {}
    for members in body["families"].values():
        fam = frozenset(members)
        for r in members:
            out[r] = fam
    return out


def expand_roots(roots) -> frozenset:
    """Every root that names the same happening as one of `roots`.

    ⛔⛔ THE FALLBACK TIGHTENS. An unfamilied root expands to ITSELF, so the
    softened gate degenerates to the exact gate for the 110 roots that stand
    alone rather than loosening to anything-goes.
    """
    sets = gloss_synonyms()
    out: set = set()
    for r in roots or ():
        out |= sets.get(r) or {r}
    return frozenset(out)


def scene_carry_soft(prior_roots, reply_roots) -> Carry:
    """The SOFTENED band: carry the HAPPENING, not necessarily the exact root.

    ⛔⛔ `added` IS COMPUTED AGAINST THE EXPANDED SET, NOT THE PRIOR SET, and
    this is the whole subtlety. If the reply answers P's `flöx` (it dims) with
    `pön` (it darkens), then `pön` is CARRIED. Measuring `added` against the
    raw prior roots would also count `pön` as new, so a pure echo-in-synonyms
    — a reply that restates the prior happening and says nothing else — would
    pass both the "something carried" and the "something new" tests at once.
    The echo clause only means anything if a synonym cannot be its own novelty.

    ⛔ The exact gate is the special case where every family is a singleton, so
    `scene_carry` and this function agree whenever no root has an alternative.
    """
    prior = frozenset(prior_roots or ())
    reply = frozenset(reply_roots or ())
    wide = expand_roots(prior)
    carried, added = reply & wide, reply - wide
    if not reply:
        return Carry(False, carried, added, "the reply has no root at all")
    if not carried:
        return Carry(False, carried, added,
                     "no root naming the prior turn's happening")
    if not added:
        return Carry(False, carried, added,
                     "echo: every root restates the prior happening and none "
                     "is new")
    return Carry(True, carried, added, "ok")


def wilson(hits: int, n: int, z: float = 1.96) -> tuple:
    """95% CI for a proportion, Wilson rather than normal-approximation.

    ⛔ The normal approximation is wrong exactly where this gets used — small
    n and rates far from 0.5 — and it can hand back a lower bound below zero,
    which reads as "we measured nothing" instead of "we measured too little".
    """
    if n <= 0:
        return (0.0, 1.0)
    p = hits / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def decide(scene_passed: int, scene_pairs: int) -> tuple:
    """-> (verdict, detail). ⛔ THE ONLY PLACE A VERDICT IS ALLOWED TO FORM.

    Returns UNDECIDED — not a pass, not a fail — whenever the evidence cannot
    support either. That is the shape of the mistake this encodes: a verdict
    was printed off 22 pairs and the next identical run reversed it.
    """
    lo, hi = wilson(scene_passed, scene_pairs)
    rate = scene_passed / scene_pairs if scene_pairs else 0.0
    floor = ACCEPTANCE["scene_band_ci_floor"]
    need = ACCEPTANCE["min_pairs_to_decide"]
    if scene_pairs < need:
        return ("UNDECIDED",
                "only %d pairs; %d are needed before a verdict may be printed"
                % (scene_pairs, need))
    if lo > floor and rate >= ACCEPTANCE["scene_band_target"]:
        return ("ACCEPTED",
                "%.1f%% [%.1f, %.1f], CI floor %.0f%% cleared"
                % (100 * rate, 100 * lo, 100 * hi, 100 * floor))
    if hi <= floor:
        return ("REJECTED",
                "%.1f%% [%.1f, %.1f] lies entirely below the %.0f%% floor"
                % (100 * rate, 100 * lo, 100 * hi, 100 * floor))
    return ("UNDECIDED",
            "%.1f%% [%.1f, %.1f] straddles the %.0f%% floor or misses the "
            "%.0f%% target — the CI must decide, not straddle"
            % (100 * rate, 100 * lo, 100 * hi, 100 * floor,
               100 * ACCEPTANCE["scene_band_target"]))


def scene_roots(scene, roots) -> frozenset:
    """Every R-class form in a proposal/scene tree.

    ⛔ Walks the tree rather than splitting the surface: `aspect_root` and a
    nested node's `root` are roots too, and a surface split would also collect
    any R form that happens to sit in another slot.
    """
    found: set = set()

    def walk(node):
        if not isinstance(node, dict):
            return
        for key in ("root", "aspect_root"):
            value = node.get(key)
            if isinstance(value, str) and value in roots:
                found.add(value)
        for edge in node.get("edges") or ():
            if isinstance(edge, dict):
                walk(edge.get("node"))

    if isinstance(scene, dict):
        walk(scene.get("node") if "node" in scene else scene)
    return frozenset(found)


def gate_dialogue(turns) -> tuple[list, list]:
    """Truncate an English dialogue at its first non-carrying exchange.

    `turns` is `[("P", line), ("T", line), ...]` as `parse_dialogue` returns.

    ⭐ TRUNCATE, DO NOT DROP. The whole conversation costs one call, and its
    early exchanges are usually fine; discarding them would pay for material
    that was already good. ⛔ And truncate rather than SKIP the bad exchange —
    splicing turn 1 to turn 3 teaches a jump that never happened, which is the
    same reasoning `one()` already applies to gate refusals.
    """
    kept: list = []
    verdicts: list = []
    for i in range(0, len(turns) - 1, 2):
        (pv, pline), (tv, tline) = turns[i], turns[i + 1]
        if pv != "P" or tv != "T":
            break
        verdict = english_carry(pline, tline)
        verdicts.append(verdict)
        if not verdict.ok:
            break
        kept.extend([(pv, pline), (tv, tline)])
    return kept, verdicts
