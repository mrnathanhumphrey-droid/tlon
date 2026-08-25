"""THE FINE-TUNE CORPUS — (English, Scene) pairs with an exact free oracle.

⛔⛔ NAIVE SAMPLING TRAINS HARDEST ON WHAT THE MODEL ALREADY KNOWS. Measured: 5,000
freely sampled pairs cover 9/9 classes at 100 % of forms -- coverage is satisfied
by construction and is NOT the problem. The problem is EXPOSURE, and it runs
backwards:

    R has 156 forms, so each root appears ~32× per 5,000 pairs.
    F has 5 forms, so each force appears ~1,000× per 5,000 pairs.

A ~30× gap, and it points AWAY from the failures. Every recorded class confusion
involved the SMALL classes -- `pal`/`rän` (R) shoved into A (6 forms), `plas`/
`hul` (O) used as root and relator -- while R, at 67 % of the lexicon, caused
NONE. Free sampling would spend the fine-tune reinforcing R and starving the
boxes the model actually gets wrong.

⭐ SO EXPOSURE IS WEIGHTED TOWARD THE SMALL CLASSES AND TOWARD MEASURED FAILURES,
which is the opposite of what free sampling gives.

⭐ THE ORACLE IS EXACT AND COSTS NOTHING. `gloss()` is deterministic Scene→English
and π gives equality, so every pair carries its own ground truth:
`Scene → gloss → model → Scene′`, accept iff `impression(s′) == impression(s)`.
No judge, no labelling. Measured generation: ~33,700 pairs/sec, 100 % accept.
"""
from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass

from ..grammar import classes as C
from ..grammar.gloss import gloss
from ..grammar.parse import render
from ..grammar.parse import Scene
from ..product import schema as PS
from ..product.compat import impression
from . import probes
from .negatives import ClassError, slot_class_map

CLASSES = ("R", "O", "L", "A", "M", "D", "Q", "T", "F")


@dataclass(frozen=True)
class Pair:
    """One training example, in ONE of the two directions.

    ⛔⛔ THE CORPUS TRAINED A WRITER AND THE GATE TESTED A READER. Measured on the
    fixed-dialect run: **render 81.2 %** (write, trained) against **speak 9.4 %**
    (read, never trained once), and **118 of the 131 offending forms — 90 % —
    appeared VERBATIM in the Tlön history the model had just been shown.** It was
    lifting tokens off the page with no idea what class they belonged to, because
    it had never been asked to read a single one.

    ⭐ THE READ DIRECTION HAS A FREE EXACT ORACLE, which is why it can be trained
    at all: `parse(render(s)) == s` is an identity, so every scene yields a
    `surface -> Scene` pair with ground truth and no labelling.

    ⛔ WHAT IS **NOT** TRAINABLE, AND IS DELIBERATELY ABSENT: "given a history,
    what comes NEXT". Any legal scene may follow any other -- there is no oracle,
    and inventing one would teach an arbitrary continuation policy and call it
    competence. F-LOCAL scores VALIDITY, not appropriateness, so reading plus
    writing is exactly what the gate requires.
    """
    english: str            # the austere gloss — deterministic, from the Scene
    scene: Scene
    impression: str
    source: str             # "sampled" | "accepted" | "negative"
    direction: str = "write"        # "write" = English -> Scene · "read" = Tlön -> Scene
    surface: str = ""               # the Tlön surface; the INPUT for a read pair

    def prompt(self) -> str:
        """What the model is shown. The only thing that differs between the two
        directions -- the target is a Scene either way."""
        return self.surface if self.direction == "read" else self.english

    def verify(self, produced: Scene) -> bool:
        """The free oracle. ⛔ Compared in IMPRESSION space, not on the surface:
        two renderings can differ on the surface and mean the same thing."""
        return impression(produced) == self.impression


def _walk(n):
    yield n
    for _, c in n.edges:
        yield from _walk(c)


def class_exposure(pairs) -> dict[str, Counter]:
    """Per-class FORM-FREQUENCY, not coverage. ⛔ Coverage says every box was
    touched; exposure says how often, and exposure is what training sees."""
    out = {c: Counter() for c in CLASSES}
    for p in pairs:
        s = p.scene if isinstance(p, Pair) else p
        out["F"][s.force] += 1
        for n in _walk(s.node):
            out["R"][n.root] += 1
            for o in n.orient:
                out["O"][o] += 1
            for rel, _ in n.edges:
                out["L"][rel] += 1
            if n.aspect:
                out["A"][n.aspect[0]] += 1
            for cls, v in (("M", n.modal), ("D", n.degree), ("Q", n.quant),
                           ("T", n.tense)):
                if v is not None:
                    out[cls][v] += 1
    return out


def exposure_report(pairs) -> dict:
    """What must be printed BEFORE training. ⭐ `min_form_exposure` is the number
    that matters: the least-seen form in a class is the one the fine-tune will
    fail on, and an average hides it."""
    lex = C.load()["classes"]
    exp = class_exposure(pairs)
    rows = {}
    for c in CLASSES:
        counts = [exp[c].get(f, 0) for f in lex[c]]
        rows[c] = {"forms": len(lex[c]),
                   "covered": sum(1 for v in counts if v),
                   "total": sum(counts),
                   "min_form_exposure": min(counts) if counts else 0,
                   "max_form_exposure": max(counts) if counts else 0}
    least = min(rows.values(), key=lambda r: r["min_form_exposure"])
    spread = (max(r["max_form_exposure"] for r in rows.values())
              / max(1, least["min_form_exposure"]))
    return {"n_pairs": len(list(pairs)), "by_class": rows,
            "worst_form_exposure": least["min_form_exposure"],
            "exposure_spread": spread}


def _weights(focus: dict[str, float] | None) -> dict[str, float]:
    """⭐ INVERSE TO CLASS SIZE BY DEFAULT. A 5-form class needs the same
    per-form exposure as a 156-form one, so it needs proportionally more of the
    sampler's attention, not less."""
    lex = C.load()["classes"]
    base = {c: 1.0 for c in CLASSES}
    if focus:
        for c, w in focus.items():
            if c not in base:
                raise ValueError(f"{c!r} is not a lexicon class")
            base[c] = float(w)
    return base


def build(n: int, *, seed: int = 20620, balanced: bool = True,
          focus: dict[str, float] | None = None,
          focus_forms: dict[str, int] | None = None) -> list[Pair]:
    """Sample `n` pairs. `balanced=True` forces per-form exposure to even out
    across classes instead of following the lexicon's own shape.

    ⭐⭐ `focus_forms` IS HOW THE HARD NEGATIVES ENTER SUPERVISED FINE-TUNING.
    A causal LM cannot be shown "`pal` is not an aspect" as a negative example --
    there is no loss for a token you did not emit. The contrastive signal has to
    arrive as TARGETED POSITIVES: extra sightings of the confused form IN ITS
    CORRECT SLOT. `{"pal": 40}` starts `pal` 40 exposures in credit, so the
    least-exposed round-robin hands it out first and keeps handing it out until
    the debt clears.

    ⛔ This is the mechanism that makes the mined failures matter. Without it the
    failure log is a diagnosis nobody acts on.
    """
    lex, k = C.load()["classes"], C.constraints()
    rng = random.Random(seed)
    weights = _weights(focus)
    bal = _Balancer(lex)
    for form, boost in (focus_forms or {}).items():
        cls = next((c for c in CLASSES if form in lex[c]), None)
        if cls is None:
            raise ValueError(
                f"{form!r} is not a Tlön form, so it has no correct slot to be "
                "shown in. An invented form is a different failure from a "
                "misassignment and is not fixed by more exposure.")
        bal.counts[cls][form] -= int(boost)
    probs = _decoration_p(lex)
    out: list[Pair] = []
    guard = 0
    while len(out) < n and guard < n * 50:
        guard += 1
        if balanced:
            node = _balanced_node(rng, lex, k, bal, probs, weights)
            force = bal.pick("F", rng)
        else:
            node = probes._random_node(rng, lex, k)      # noqa: SLF001
            force = rng.choice(sorted(lex["F"]))
        got = probes._validate(node, force)
        if got is None:
            continue
        scene, _ = got
        out.append(Pair(english=gloss(scene), scene=scene,
                        impression=impression(scene), source="sampled",
                        direction="write", surface=render(scene)))
    if len(out) < n:
        raise RuntimeError(
            f"corpus short: {len(out)}/{n}. A corpus quietly smaller than asked "
            "for changes every exposure figure computed on it.")
    return out


class _Balancer:
    """Round-robin over the LEAST-EXPOSED forms of each class.

    ⛔⛔ THE FIRST VERSION OF THIS RAISED THE SMALL CLASSES AND MADE THE SPREAD
    WORSE (27× → 28×), because it was built on a premise the measurement
    refutes. The stated worry was that free sampling starves the small classes.
    It does the opposite:

        naive, 5,000 pairs — per-form exposure
          R (156 forms):   39      ← the starved class
          A (6 forms):    685
          F (5 forms):    930

    A class with FEW forms concentrates its exposure; a class with MANY spreads
    it thin. R holds 67 % of the lexicon in ONE slot per node, so each root is
    seen ~39 times while each force is seen ~930. **The starvation runs with
    class size, not against it**, and the fix is the opposite of the intuition.

    ⭐ The failures are still consistent with this: `pal`/`rän` are R-forms
    (39 exposures each) misfiled into A, and `plas`/`hul` are O-forms put in
    R and L slots. The confusions are about the THINLY-SEEN forms, which are
    exactly the R and O ones.
    """

    def __init__(self, lex):
        self.counts = {c: Counter({f: 0 for f in lex[c]}) for c in CLASSES}

    def pick(self, cls: str, rng: random.Random) -> str:
        items = self.counts[cls]
        floor = min(items.values())
        pool = sorted(f for f, v in items.items() if v == floor)
        form = rng.choice(pool)
        items[form] += 1
        return form

    def sample(self, cls: str, k: int, rng: random.Random) -> list[str]:
        out: list[str] = []
        while len(out) < k:
            f = self.pick(cls, rng)
            if f not in out:
                out.append(f)
        return out


def _balanced_node(rng, lex, k, bal: "_Balancer", probs, weights,
                   depth: int = 1) -> dict:
    """A node whose every form is drawn from the least-exposed pool."""
    node: dict = {"root": bal.pick("R", rng)}
    if rng.random() < probs["O"] * weights["O"] * k["MAX_ORIENT_PER_PRED"]:
        node["orient"] = bal.sample(
            "O", rng.randint(1, k["MAX_ORIENT_PER_PRED"]), rng)
    if rng.random() < probs["A"] * weights["A"]:
        node["aspect_root"] = bal.pick("A", rng)
        node["aspect_reps"] = rng.randint(1, k["MAX_ASPECT_REPS"])
    for slot, cls in (("degree", "D"), ("modal", "M"), ("tense", "T"),
                      ("quant", "Q")):
        if rng.random() < probs[cls] * weights[cls]:
            node[slot] = bal.pick(cls, rng)
    # ⭐ Edges are what give R more slots per pair, which is the only way the
    # 156 roots catch up with the 5 forces.
    if depth < k["MAX_DEPTH"] and rng.random() < 0.85:
        node["edges"] = [{"relator": bal.pick("L", rng),
                          "node": _balanced_node(rng, lex, k, bal, probs,
                                                 weights, depth + 1)}]
    return node


def _decoration_p(lex) -> dict[str, float]:
    """How often a class should decorate a node, so that PER-FORM exposure
    evens out: a class with n forms needs n times the slot-occupancy of a
    one-form class to give each of its forms the same number of sightings.
    Normalised against R, the class that sets the pace."""
    r = len(lex["R"])
    return {c: min(1.0, len(lex[c]) / r) for c in CLASSES}


def negative_examples(errors: list[ClassError]) -> list[dict]:
    """Turn mined class confusions into contrastive training items.

    ⭐ Each carries the CORRECTION as well as the error, because "not A" alone
    does not say where the form does belong -- and the failure is a
    misassignment, so the correction is exactly the thing to teach.
    """
    lex = C.load()["classes"]
    slots = {v: k for k, v in slot_class_map().items()}
    out = []
    for e in errors:
        item = {"form": e.form, "wrong_slot": e.used_as,
                "wrong_class": e.expected, "true_class": e.actual,
                "statement": e.as_negative()}
        if e.actual and e.actual in slots:
            item["correct_slot"] = slots[e.actual]
            item["gloss"] = lex[e.actual][e.form]
        out.append(item)
    return out
