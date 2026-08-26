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
from .negatives import ClassError, MiningError, slot_class_map

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


#: ⛔⛔ THE INVARIANT IS THE **TOTAL** BOOST, NOT THE PER-FORM BOOST — AND THIS IS
#: A NEW ENTRY IN THIS PROJECT'S FAILURE CATALOG, NOT A REPEAT.
#:
#: Run 5 held tokens (+0.03 %), steps (+3.3 %), seq, batch, battery, decoding and
#: hardware — every variable that LOOKS like a variable — and was still
#: confounded, because `focus = {form: 60 × times_confused}` **is not a
#: constant.** It is a FUNCTION OF THE CORPUS. Going from run 3's 4 hand-picked
#: forms to run 5's 89 mined confusions multiplied the total boost **22×**:
#:
#:      run 3   4 forms ·   240 total · per-form exposure FLAT 663–664 (1.002×)
#:      run 5  42 forms · 5,340 total · `nem` 2,563 = 34.9 % of ALL M exposure
#:
#: ⭐⭐ THAT IS THE HARDEST CONFOUND TO CATCH: not a variable someone forgot to
#: hold, but a "constant" SECRETLY COUPLED TO THE THING THAT CHANGED. It moved
#: because the DATA moved. Nothing in the held-variable list named it, so nothing
#: could notice. A knob safe at 4 forms was a wrecking ball at 89.
#:
#: ⇒ The budget is fixed and DISTRIBUTED proportionally, so mining more
#: confusions sharpens the targeting without inflating the distortion.
#: ⛔⛔ AND THE FIRST VERSION OF THIS FIX HAD THE SAME BUG ONE LEVEL DOWN. I set
#: an absolute cap of 240 — run 3's total — and the fairness test FAILED at
#: n=1,500, because 240 is harmless against 41,000 pairs and enormous against
#: 1,500. **An absolute total is a constant coupled to CORPUS SIZE**, exactly as
#: `60 × count` was a constant coupled to LIST LENGTH. The lesson did not
#: generalise on the first try; the test caught it.
#:
#: ⇒ The budget is expressed as a FRACTION OF THE CORPUS, so it is invariant to
#: both the size of the mined list AND the size of the corpus. Run 3's ratio:
#: 240 boost over 41,000 pairs.
FOCUS_BOOST_FRACTION = 240 / 41_000      # ≈ 0.0059 boosts per pair

#: The worst per-form exposure may not fall below this fraction of the mean.
#: Run 3 sat at ~1.00; run 5 fell to 0.18 for the least-seen M form.
MIN_EXPOSURE_FAIRNESS = 0.40


class CorpusError(RuntimeError):
    pass


def focus_budget(counts: dict[str, int], *, n_pairs: int,
                 fraction: float = FOCUS_BOOST_FRACTION) -> dict[str, int]:
    """Distribute a boost budget PROPORTIONAL TO THE CORPUS, split by how often
    each form was actually misplaced.

    ⭐ Keeps the mechanism run 3 proved — targeted positives weighted by measured
    confusion — and removes BOTH couplings: the total grows with neither the
    length of the mined list (run 5's 22× break) nor the size of the corpus (the
    break in my first attempt at this fix).

    ⛔ `n_pairs` is REQUIRED and has no default. A default here would be a third
    hidden constant, which is the whole thing this function exists to stop.
    """
    if not counts:
        return {}
    total = max(1, round(fraction * n_pairs))
    denom = sum(counts.values())
    return {f: max(1, round(total * c / denom)) for f, c in counts.items()}


def check_exposure_fairness(pairs, *, minimum: float = MIN_EXPOSURE_FAIRNESS) -> dict:
    """⛔⛔ REFUSES a corpus whose per-form exposure has collapsed.

    The flat-exposure invariant is what the whole corpus design rests on, and run
    5 broke it SILENTLY — nothing measured it, so nothing complained, and a
    confounded corpus trained for 93 minutes. This is that check, made
    structural.
    """
    lex = C.load()["classes"]
    exp = class_exposure(pairs)
    worst = None
    for cls in CLASSES:
        counts = [exp[cls].get(f, 0) for f in lex[cls]]
        if not counts or not sum(counts):
            continue
        mean = sum(counts) / len(counts)
        ratio = min(counts) / mean if mean else 0.0
        if worst is None or ratio < worst[1]:
            worst = (cls, ratio, min(counts), max(counts), mean)
    if worst and worst[1] < minimum:
        cls, ratio, lo, hi, mean = worst
        raise CorpusError(
            f"⛔ EXPOSURE COLLAPSE in class {cls}: least-seen form has {lo} "
            f"sightings against a mean of {mean:.0f} (ratio {ratio:.2f} < "
            f"{minimum}). Most-seen has {hi}. Run 3's classes were flat at "
            "~1.00; run 5 fell to 0.18 and the run was confounded without "
            "anyone noticing. Reduce FOCUS_BOOST_TOTAL or widen the corpus.")
    return {"worst_class": worst[0] if worst else None,
            "worst_ratio": worst[1] if worst else 1.0}


def build(n: int, *, seed: int = 20620, balanced: bool = True,
          focus: dict[str, float] | None = None,
          focus_forms: dict[str, int] | None = None,
          slot_floor: float | None = None) -> list[Pair]:
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
    probs = _decoration_p(lex, slot_floor=slot_floor)
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


#: ⭐ THE SLOT-OCCUPANCY FLOOR, DERIVED FROM THE SLOTS THE MODEL GETS RIGHT.
#: `relator` sits at 61.1 % occupancy and produced 0 missed-slot errors at n=256;
#: `orient` at 30.9 % produced 2. `aspect_root` at 3.9 % produced 16. 0.30 is the
#: lowest occupancy at which the model demonstrably learns a slot, taken from the
#: measurement rather than chosen.
SLOT_OCCUPANCY_FLOOR = 0.30

#: ⛔ APPLIED TO THE SINGLE-FILL MODIFIER SLOTS ONLY. `O` is excluded because it
#: is already at 30.9 % EFFECTIVE occupancy (its probability is multiplied by
#: MAX_ORIENT_PER_PRED) and accounts for 2 of 48 errors — it does not need help,
#: and raising it would spend tokens on a slot that is already learned.
FLOORED_CLASSES = ("A", "M", "D", "Q", "T")


def _decoration_p(lex, *, slot_floor: float | None = None) -> dict[str, float]:
    """How often a class should decorate a node.

    ⛔⛔ THE DEFAULT OPTIMISES PER-FORM EXPOSURE, AND THAT IS WHY THE RARE SLOTS
    ARE RARE. A class with n forms is given `n/|R|` decoration probability so
    that each of its forms is seen as often as each root — which lands a 6-form
    class at 3.9 % slot occupancy. It worked: A/M/Q/T/D all landed within 3 % of
    663 sightings per form. It also meant the model saw an aspect slot filled
    once every 26 nodes, and 16 of 48 render errors are aspect-slot errors.

    ⭐ `slot_floor` decouples the two: per-form exposure stays balanced by the
    round-robin, and the SLOT gets exercised often enough to be learnable.
    """
    r = len(lex["R"])
    out = {c: min(1.0, len(lex[c]) / r) for c in CLASSES}
    if slot_floor is not None:
        for c in FLOORED_CLASSES:
            out[c] = max(out[c], slot_floor)
    return out


# ══ §8.2 — CLOSING THE RENDER GAP ════════════════════════════════════════
# ⛔⛔ THE INSTRUMENT THE BRIEF NAMED IS THE WRONG ONE, AND THE CORPUS SAYS SO.
# §8.2 asks for "the small-class targeted positives". Measured on the corpus that
# actually trained run 3:
#
#     per-form exposure   A 663 · M 663 · Q 662 · T 649 · D 670
#
# The balancing WORKED — exposure is flat to within 3 %, and the four forms
# targeted after the hosted pre-flight (`pal` `rän` `plas` `hul`) appear NOWHERE
# in the n=256 confusions. More positives on forms that already have 663
# sightings apiece cannot be what is missing.
#
# ⭐⭐ WHAT IS MISSING IS SLOT OCCUPANCY, WHICH THE PER-FORM BALANCING OPTIMISED
# AWAY BY CONSTRUCTION. `_decoration_p` sets a class's decoration probability to
# `len(class)/len(R)` precisely so that per-form exposure evens out — which means
# a 6-form class fills its slot in 3.9 % of nodes. Errors track slot RARITY, not
# form rarity:
#
#     slot        occupancy   missed-slot errors (n=256)
#     root           100.0 %    8      ← 156 forms and the FEWEST errors per fill
#     relator         61.1 %    0
#     orient          30.9 %    2
#     modal            6.4 %   11
#     tense            5.1 %    3
#     aspect_root      3.9 %   16      ← the single biggest hole
#     quant            3.9 %    5
#     degree           3.9 %    2
#
# ⛔ The model has seen every A-form 663 times and has still not learned WHICH
# SLOT IS AN A-SLOT, because it has only seen an A-slot filled once every 26
# nodes. Exposure teaches the form; occupancy teaches the function.
#
# ⚠️ `aspect_root` is an outlier even among the rare slots — 16 errors against
# `quant`'s 5 at identical occupancy — so occupancy is not the whole story. Two
# candidates, NOT distinguished by any measurement we have: aspect is the only
# two-field slot (`aspect_root` + `aspect_reps`) and the only one whose surface
# form is a reduplication rather than the bare morpheme; and Q/A collide
# semantically in English (`nol` "oft" was put in the aspect slot 4×, where the
# wanted form is `sor` "habitual"). Recorded as open, not resolved.


def mined_confusions(ledger_path) -> list[ClassError]:
    """Read the class confusions out of a run ledger. ⭐ THE CORPUS IS DRIVEN BY
    THE LAST RUN'S EVIDENCE, NOT BY A LIST SOMEBODY MAINTAINS.

    ⛔⛔ THE HAND-KEPT LIST WENT STALE AND NOBODY NOTICED. `CONFUSED = {"pal",
    "rän", "plas", "hul"}` was mined from the hosted pre-flight and was still
    being boosted three runs later — by which point all four were fixed and the
    live offenders were `nol` `nem` `xom` `sen` `fral` `hrix`. The boost was
    spending itself on solved problems. A list read from the newest ledger cannot
    do that.
    """
    import json
    import pathlib

    path = pathlib.Path(ledger_path)
    if not path.exists():
        raise MiningError(
            f"no ledger at {path}. The confusions must come from a run; "
            "inventing them would train against a guess.")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    runs = [r for r in rows if r.get("event") == "f_local"]
    if not runs:
        raise MiningError(f"{path} has no f_local rows to mine.")
    latest = runs[-1]
    out: list[ClassError] = []
    for kind in ("render", "speak"):
        for failure in latest.get("results", {}).get(kind, {}).get("failures", []):
            for e in failure.get("class_errors", []):
                if not e.get("actual") or not e.get("form"):
                    continue          # an absent field has no true class to teach
                out.append(ClassError(form=e["form"], used_as=e["used_as"],
                                      expected=e["expected"], actual=e["actual"]))
    return out


def boundaries(errors: list[ClassError]) -> Counter:
    """The class boundaries the model actually confuses, most-confused first.

    ⛔ Unordered pairs: `M` used where `R` belongs and `R` used where `M` belongs
    are one boundary seen from two sides, and a contrastive pair teaches both
    directions at once.
    """
    out: Counter = Counter()
    for e in errors:
        if e.actual and e.expected and e.actual != e.expected:
            out[tuple(sorted((e.actual, e.expected)))] += 1
    return out


def contrastive_pairs(errors: list[ClassError], *, per_confusion: int = 24,
                      seed: int = 20620) -> list[Pair]:
    """⭐⭐ THE MINIMAL PAIR — the contrastive signal a causal LM CAN receive.

    The module used to assert that targeted positives are *"the only form a
    contrastive signal can take in supervised fine-tuning"*. That is true of a
    negative — there is no loss for a token you did not emit — but it is NOT true
    of a **pair**. Two rows whose scenes are byte-identical except for one slot
    put the two competing readings side by side, and the only thing that varies
    between them is the class assignment. That is contrast, and it is exactly the
    distinction the model is failing to draw.

    For a confusion "`form` (really class X) was put in slot S, which wants Y":

        row A — an otherwise-identical scene with `form` in ITS OWN slot
        row B — an otherwise-identical scene with a real Y-form in slot S

    ⛔ Both rows are legal Tlön with a true gloss. Nothing here is a negative
    example, an error string, or a repair; they are two correct sentences chosen
    so that the difference between them is the lesson.
    """
    lex = C.load()["classes"]
    slots = {v: k for k, v in slot_class_map().items()}
    rng = random.Random(seed)
    k = C.constraints()
    out: list[Pair] = []

    for err in errors:
        if not err.actual or err.actual not in slots or err.expected not in slots:
            continue
        own_slot, wrong_slot = slots[err.actual], err.used_as
        if own_slot == wrong_slot:
            continue
        for _ in range(per_confusion):
            base = {"root": rng.choice(sorted(lex["R"]))}
            if rng.random() < 0.5:
                base["edges"] = [{"relator": rng.choice(sorted(lex["L"])),
                                  "node": {"root": rng.choice(sorted(lex["R"]))}}]
            force = rng.choice(sorted(lex["F"]))

            for slot, form in ((own_slot, err.form),
                               (wrong_slot, rng.choice(sorted(lex[err.expected])))):
                node = {kk: (list(vv) if isinstance(vv, list) else vv)
                        for kk, vv in base.items()}
                if slot == "root":
                    node["root"] = form
                elif slot == "force":
                    force = form
                elif slot == "relator":
                    node["edges"] = [{"relator": form,
                                      "node": {"root": rng.choice(sorted(lex["R"]))}}]
                elif slot == "orient":
                    node["orient"] = [form]
                elif slot == "aspect_root":
                    node["aspect_root"] = form
                    node["aspect_reps"] = rng.randint(1, k["MAX_ASPECT_REPS"])
                else:
                    node[slot] = form
                got = probes._validate(node, force)            # noqa: SLF001
                if got is None:
                    continue
                scene, _ = got
                out.append(Pair(english=gloss(scene), scene=scene,
                                impression=impression(scene), source="contrastive",
                                direction="write", surface=render(scene)))
    return out


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
