"""THE CORPUS — Route A's standing output, and Route B's training set.

⛔⛔ EVERY ACCEPTED PAIR IS LOGGED FROM MESSAGE ONE. This is not telemetry, it
is the deliverable: Route A exists to bootstrap the corpus that trains the local
model, and an unlogged pair is a pair B can never train on. That is the 9.5
stall -- effective sample size 0, not merely small -- applied to the product, and
it is the one failure here that cannot be repaired after the fact.

⭐ REFUSALS ARE LOGGED TOO, separately. A proposal the parser rejected is not
training data for B, but the RATE and the SHAPE of rejection is how we know
whether the front end is healthy, and the refused ENGLISH is exactly the input
distribution B will have to cover.

Append-only JSONL. Never rewritten.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib

from ..grammar import classes as C
from ..grammar.canon import canon_json, utterance_id
from ..grammar.parse import Scene, parse

ROOT = pathlib.Path(__file__).resolve().parents[2] / "runs" / "corpus"
ACCEPTED = ROOT / "accepted.jsonl"
REFUSED = ROOT / "refused.jsonl"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append(path: pathlib.Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


MODES = ("translate", "reply")


class ModeError(ValueError):
    """An unlabelled or unknown corpus mode. Raised, never defaulted."""


def log_accepted(english: str, scene: Scene, surface: str, *,
                 proposer: str, mode: str, refused_objects=(),
                 note: str = "") -> dict:
    """One (arbitrary-English, validated-Scene) pair.

    ⛔⛔ `mode` IS REQUIRED AND HAS NO DEFAULT, AND THAT IS THE WHOLE POINT.

      translate -- the Scene MEANS the English. This is Route B's training row.
      reply     -- the Scene ANSWERS the English. A different relation entirely.

    Those two are indistinguishable once written: both validate, both
    round-trip, both look like clean pairs. Mixed under one field name they
    would teach Route B a blend of "say this" and "answer this" and it would
    learn neither -- a corpus poisoned in the way that is hardest to see.

    ⭐ Added BEFORE the conversant exists, on purpose. A label retro-fitted
    after the fact is a guess about rows nobody can re-examine; the same reason
    the residue log went in before the arms did.
    """
    if mode not in MODES:
        raise ModeError(
            f"mode={mode!r} must be one of {MODES}. It has no default: an "
            "unlabelled row cannot be told apart from a mislabelled one later.")
    row = {"ts": _now(), "mode": mode, "english": english, "surface": surface,
           "scene": json.loads(canon_json(scene)),
           "utterance_id": utterance_id(scene),
           "refused_objects": list(refused_objects), "note": note,
           "proposer": proposer, "lexicon": C.load()["_hash"]}
    _append(ACCEPTED, row)
    return row


REFUSAL_STAGES = ("input", "parser")


class StageError(ValueError):
    """An unlabelled or unknown refusal stage. Raised, never defaulted."""


def log_refused(english: str, reason: str, *, proposer: str, stage: str,
                proposal: dict | None = None, rescued_on_retry: bool = False,
                attempt: int = 1) -> dict:
    """⭐ `rescued_on_retry` separates "the front end failed" from "the first
    proposal was illegal and the grammar's own complaint fixed it". Both are
    worth knowing and they mean opposite things about health.

    ⛔⛔ `stage` IS REQUIRED FOR THE SAME REASON `mode` IS.

      input  -- rejected BEFORE any proposal existed (empty, over-bound). No
                model was asked, nothing was spent, and the parser never saw it.
      parser -- a proposal existed and the grammar refused it.

    Only the second says anything about whether the front end is healthy.
    Pooled under one count they would silently drag the acceptance rate around
    with the amount of junk typed at the door, which is a fact about visitors,
    not about the translator.
    """
    if stage not in REFUSAL_STAGES:
        raise StageError(
            f"stage={stage!r} must be one of {REFUSAL_STAGES}. It has no "
            "default: an input rejection and a parser refusal mean opposite "
            "things about the front end's health.")
    row = {"ts": _now(), "stage": stage, "english": english, "reason": reason,
           "proposer": proposer, "proposal": proposal, "attempt": attempt,
           "rescued_on_retry": rescued_on_retry,
           "lexicon": C.load()["_hash"]}
    _append(REFUSED, row)
    return row


def _read(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def scene_from_canon(d: dict) -> Scene:
    """Rebuild a Scene from a stored canonical dict. Raises on a malformed row.

    ⛔ Lives here, not with the reveal that consumes it: the shape being decoded
    is a CORPUS ROW, and anything that reads the corpus needs the same decoder.
    Two decoders would be two chances to disagree about what a stored row means.
    """
    from ..grammar.parse import EventNode

    def node(n: dict) -> EventNode:
        asp = n.get("aspect")
        return EventNode(
            root=n["root"],
            aspect=(asp[0], asp[1]) if asp else None,
            degree=n.get("degree"), modal=n.get("modal"),
            tense=n.get("tense"), quant=n.get("quant"),
            orient=list(n.get("orient") or []),
            edges=[(e[0], node(e[1])) for e in (n.get("edges") or [])],
            residue=tuple(n["residue"]) if n.get("residue") else None)

    return Scene(node=node(d["node"]), force=d["force"])


def audit(rows: list[dict] | None = None) -> dict:
    """⛔⛔ THE VALIDATES-BUT-LIES CHECK, RUN AGAINST THE ACTUAL FILE.

    A corpus row is dangerous in exactly one way that no schema catches: it is
    well-formed AND misrepresents its own contents. The mode field is one
    instance of that shape; these are the rest of them. Every accepted row must
    satisfy, on re-reading:

      · it declares a mode we know (or is provably pre-mode legacy)
      · its stored Scene decodes at all
      · `parse(surface)` reproduces that Scene EXACTLY -- so the English, the
        surface and the Scene are three views of one thing, not three fields
        that merely appeared together
      · its stored `utterance_id` is the id of that Scene
      · it was written against the frozen lexicon

    ⭐ The round-trip is the load-bearing one. It is the same guarantee the gate
    uses at write time, re-applied at read time, which is what makes it a check
    on the FILE rather than a restatement of the code that wrote it.
    """
    from ..grammar.parse import ParseError, render

    if rows is None:
        rows = _read(ACCEPTED)
    problems: list[dict] = []

    def flag(i: int, row: dict, why: str) -> None:
        problems.append({"row": i, "english": row.get("english"), "why": why})

    for i, row in enumerate(rows):
        mode = row.get("mode")
        if mode is not None and mode not in MODES:
            flag(i, row, f"mode={mode!r} is not one of {MODES}")
        for key in ("english", "surface", "scene"):
            if key not in row:
                flag(i, row, f"missing {key!r}")
        if "scene" not in row or "surface" not in row:
            continue
        try:
            scene = scene_from_canon(row["scene"])
        except Exception as exc:                    # noqa: BLE001
            flag(i, row, f"stored scene will not decode: {exc}")
            continue
        try:
            back = parse(row["surface"])
        except ParseError as exc:
            flag(i, row, f"stored surface will not parse: {exc}")
            continue
        if back != scene:
            flag(i, row, "the stored surface does not parse back to the stored "
                         "scene -- the row's three views disagree")
            continue
        if render(scene) != row["surface"]:
            flag(i, row, "the stored scene does not render to the stored "
                         "surface")
        if row.get("utterance_id") not in (None, utterance_id(scene)):
            flag(i, row, "the stored utterance_id is not the id of the stored "
                         "scene")
        if row.get("lexicon") not in (None, C.load()["_hash"]):
            flag(i, row, f"written against lexicon {row.get('lexicon')}, not "
                         f"the frozen {C.load()['_hash']}")

    return {"rows": len(rows), "problems": problems, "ok": not problems}


# ⛔ THE MILESTONE IS DECLARED HERE, BEFORE THE CORPUS EXISTS, so it cannot be
# moved to wherever the corpus happens to have got to.
#
# Route B has to learn a map into a 156-root space with ~24,500 free-channel
# combinations per node. The gloss corpus (Scene -> austere English) is free and
# unlimited and covers the STRUCTURE; what only Route A can supply is the
# ARBITRARY-English side -- the paraphrase distribution. So the milestone is set
# on distinct human inputs, not on total rows.
B_MILESTONE = {
    "distinct_english": 2000,
    "distinct_roots_covered": 100,
    "rationale": "2,000 distinct human inputs is where the paraphrase "
                 "distribution starts to be represented rather than sampled; "
                 "100 of 156 roots exercised means the corpus is not "
                 "concentrated in one semantic field. Free gloss pairs supply "
                 "the structure; only Route A can supply these two.",
}


def status() -> dict:
    """⛔ THE MILESTONE COUNTS TRANSLATION ROWS ONLY.

    Reply rows are a different relation and must never advance a milestone that
    gates a TRANSLATOR's training. Rows written before the mode field existed
    are counted as `translate:legacy` -- provably from the translation era, but
    tallied separately so a row that merely LACKS a label can never be confused
    with one that declared its mode.

    ⭐ NOTHING A VISITOR TYPES CAN MOVE THE MILESTONE EXCEPT AN ACCEPTED
    TRANSLATION. Refusals -- of either stage -- live in a different file and are
    never counted here, so garbage, hostile input and over-long input advance
    `distinct_english` by exactly zero.

    ⛔ `proposal_acceptance_rate` IS PER-PROPOSAL, NOT PER-MESSAGE, AND THE NAME
    SAYS SO. One message that is refused once and accepted on retry contributes
    one acceptance AND one refusal. Input-stage rejections are excluded: no
    proposal ever existed for them, so counting them would measure how much junk
    was typed at the door rather than how well the front end translates.
    """
    acc, ref = _read(ACCEPTED), _read(REFUSED)
    ref_by_stage: dict[str, int] = {}
    for r in ref:
        key = r.get("stage", "parser:legacy")
        ref_by_stage[key] = ref_by_stage.get(key, 0) + 1
    parser_ref = [r for r in ref if r.get("stage", "parser") != "input"]
    legacy = [r for r in acc if "mode" not in r]
    by_mode: dict[str, int] = {}
    for r in acc:
        key = r.get("mode", "translate:legacy")
        by_mode[key] = by_mode.get(key, 0) + 1
    train = [r for r in acc if r.get("mode", "translate") == "translate"]
    english = {r["english"] for r in train}
    roots: set[str] = set()

    def walk(n: dict) -> None:
        roots.add(n.get("root"))
        for e in n.get("edges") or []:
            walk(e[1] if isinstance(e, list) else e.get("node", {}))

    for r in train:
        try:
            walk(r["scene"]["node"])
        except Exception:                          # noqa: BLE001
            pass
    proposals = len(acc) + len(parser_ref)
    return {
        "accepted": len(acc), "refused": len(ref),
        "refused_by_stage": ref_by_stage,
        "by_mode": by_mode, "legacy_rows": len(legacy),
        "translate_rows": len(train),
        "proposal_acceptance_rate": (len(acc) / proposals) if proposals else None,
        "distinct_english": len(english),
        "distinct_roots_covered": len(roots - {None}),
        "milestone": B_MILESTONE,
        "b_trainable": (len(english) >= B_MILESTONE["distinct_english"]
                        and len(roots - {None}) >= B_MILESTONE["distinct_roots_covered"]),
    }
