"""Referent signatures: partial graph patterns, loading, and validation.

A signature is NOT a root. Single-root signatures collapse reference resolution
to a one-token lookup and make 2a degenerate (PHASE2_DESIGN §6d). A signature is
a conjunction of node patterns that must each match a DISTINCT node somewhere in
the scene, plus optional forbidden patterns.

Nothing may RUN on an unreviewed file. `load()` refuses `review_status:
UNREVIEWED` unless a caller explicitly asks for it (the review tooling does; the
self-play loop must not).
"""
from __future__ import annotations
import pathlib
from dataclasses import dataclass, field

import yaml

from ..grammar import classes as C
from ..grammar import residue as _residue

DRAFT_PATH = pathlib.Path(__file__).with_name("referents.draft.yaml")
VALID_STATUS = ("UNREVIEWED", "REVIEWED", "REJECTED")


class ReferentError(RuntimeError):
    pass


@dataclass(frozen=True)
class NodePattern:
    root_any: tuple[str, ...]
    orient_any: tuple[str, ...] = ()
    aspect_root_any: tuple[str, ...] = ()
    edge_relator_any: tuple[str, ...] = ()
    via: tuple[str, ...] = ()
    """Relators by which this node may attach to the matrix. When set, the node
    must be a DIRECT child of the matrix via one of them. Unset means the
    signature does not care how the two relate -- which is a real claim, not a
    default, so leave it unset only on purpose."""
    at_depth: int | None = None
    """Exact nesting depth below the matrix (0 = the matrix itself). Lets a
    signature distinguish SCOPE -- "a glow beyond a raining, and a seeing" from
    "a glow beyond ⟨a raining that is seen⟩" -- which is the one contrast the
    grammar's recursion buys and nothing else could express."""

    residue_any: tuple[tuple[int, ...], ...] = ()
    """PHASE 13.0 -- the DENOTING ∧ INEXPRESSIBLE constraint.

    Allowed residue coordinates (see grammar/residue.py). This is the only
    NodePattern field whose part NEVER reaches the surface, so two referents
    may share a byte-identical expressible signature and differ only here.

    ⛔ COORDINATES ONLY, TYPE-ASSERTED AT PARSE. A text-valued residue is how
    source expression would reach a field no name-and-notes scanner reads."""

    @staticmethod
    def parse(d: dict) -> "NodePattern":
        unknown = set(d) - {"root_any", "orient_any", "aspect_root_any",
                            "edge_relator_any", "via", "at_depth", "residue_any"}
        if unknown:
            raise ReferentError(f"unknown node-pattern keys: {sorted(unknown)}")
        if not d.get("root_any"):
            raise ReferentError("node pattern needs a non-empty root_any")
        depth = d.get("at_depth")
        if depth is not None and d.get("via") and depth != 1:
            raise ReferentError("via implies at_depth 1; both given and they disagree")
        res = []
        for coord in d.get("residue_any", ()):
            res.append(_residue.validate(tuple(coord)
                                         if isinstance(coord, list) else coord))
        dims = {len(c) for c in res}
        if len(dims) > 1:
            raise ReferentError(
                f"residue_any mixes lattice dimensions {sorted(dims)}; the "
                "metric is only defined within one space")
        return NodePattern(
            tuple(d["root_any"]), tuple(d.get("orient_any", ())),
            tuple(d.get("aspect_root_any", ())),
            tuple(d.get("edge_relator_any", ())),
            tuple(d.get("via", ())),
            None if depth is None else int(depth),
            tuple(res))


@dataclass(frozen=True)
class Signature:
    contains: tuple[NodePattern, ...]
    forbid: tuple[NodePattern, ...] = ()
    matrix: NodePattern | None = None

    @staticmethod
    def parse(d: dict) -> "Signature":
        unknown = set(d) - {"contains", "forbid", "matrix"}
        if unknown:
            raise ReferentError(f"unknown signature keys: {sorted(unknown)}")
        if not d.get("contains"):
            raise ReferentError("signature needs a non-empty `contains`")
        return Signature(
            tuple(NodePattern.parse(p) for p in d["contains"]),
            tuple(NodePattern.parse(p) for p in d.get("forbid", ())),
            NodePattern.parse(d["matrix"]) if d.get("matrix") else None)


@dataclass(frozen=True)
class Referent:
    id: str
    name: str
    tier: int
    signature: Signature
    notes: str = ""
    validated: bool = True          # False => flagged pending a real listener
    seed_2a: bool = True
    minimal_pair: str | None = None  # pair id; its partner shares the SAME roots
    contrast: str | None = None      # what the pair differs by

    def roots(self) -> tuple[str, ...]:
        """Every root this signature can require. Two members of a minimal pair
        must return the same multiset, or bag-of-roots could tell them apart."""
        out: list[str] = []
        for p in self.signature.contains:
            out += sorted(p.root_any)
        return tuple(sorted(out))


@dataclass
class ReferentSet:
    review_status: str
    grammar_family: str
    referents: list[Referent] = field(default_factory=list)

    def tier1(self) -> list[Referent]:
        return [r for r in self.referents if r.tier == 1]

    def seeds(self) -> list[Referent]:
        return [r for r in self.referents if r.seed_2a]


def load(path: pathlib.Path | None = None, *, allow_unreviewed: bool = False) -> ReferentSet:
    path = path or DRAFT_PATH
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    status = raw.get("review_status")
    if status not in VALID_STATUS:
        raise ReferentError(f"review_status must be one of {VALID_STATUS}, got {status!r}")
    if status != "REVIEWED" and not allow_unreviewed:
        raise ReferentError(
            f"{path.name} is {status}; nothing may run on it until Nate marks it "
            "REVIEWED. Pass allow_unreviewed=True only from review tooling.")

    lex = C.load()["classes"]
    seen_ids: set[str] = set()
    out: list[Referent] = []
    for row in raw["referents"]:
        sig = Signature.parse(row["signature"])
        rid = str(row["id"])
        if rid in seen_ids:
            raise ReferentError(f"duplicate referent id {rid}")
        seen_ids.add(rid)
        for p in sig.contains + sig.forbid + ((sig.matrix,) if sig.matrix else ()):
            for form in p.root_any:
                if form not in lex["R"]:
                    raise ReferentError(f"{rid}: {form!r} is not a root")
            for form in p.orient_any:
                if form not in lex["O"]:
                    raise ReferentError(f"{rid}: {form!r} is not an orientation")
            for form in p.aspect_root_any:
                if form not in lex["A"]:
                    raise ReferentError(f"{rid}: {form!r} is not an aspect root")
            for form in p.edge_relator_any:
                if form not in lex["L"]:
                    raise ReferentError(f"{rid}: {form!r} is not a relator")
        k = C.constraints()
        if len(sig.contains) - 1 > k["MAX_CLAUSES_PER_PRED"]:
            raise ReferentError(f"{rid}: {len(sig.contains)} contains-patterns "
                                "cannot fit the clause cap")
        out.append(Referent(id=rid, name=row["name"], tier=int(row["tier"]),
                            signature=sig, notes=row.get("notes", ""),
                            validated=bool(row.get("validated", True)),
                            seed_2a=bool(row.get("seed_2a", True)),
                            minimal_pair=row.get("minimal_pair"),
                            contrast=row.get("contrast")))
    return ReferentSet(review_status=status,
                       grammar_family=raw.get("grammar_family", "southern"),
                       referents=out)


ALL_PATHS = ("referents.draft.yaml", "imagery_pairs.draft.yaml",
             "minimal_pairs.draft.yaml")
V2_PATH = pathlib.Path(__file__).with_name("referents_v2.yaml")

# PHASE 11 — worldview sets. Both compiled ONLY from Nate's distilled
# philosophical positions; no source text was consulted at any step.
#
# ⛔⛔ STANDING ARCHITECTURAL COMMITMENT (Nate, 2026-08-23): if source lyrics or
# text are ever needed, they live in a SEPARATE LANE that never touches this
# pipeline. No loader here reads anything but a distilled referent file, so
# expression cannot reach the referent set by accident -- the separation is
# structural, not a habit.
CR_PATH = pathlib.Path(__file__).with_name("referents_cr.yaml")
TAO_PATH = pathlib.Path(__file__).with_name("referents_tao.yaml")
WORLDVIEW_PATHS = {"cr": CR_PATH, "tao": TAO_PATH, "v2": V2_PATH}


def load_all(*, allow_unreviewed: bool = False,
             seeded_only: bool = True) -> ReferentSet:
    """Every reviewed referent: 20 Tier-1 pegs + 20 perspective + 20 diagnostic.

    seeded_only drops referents flagged seed_2a: false -- the Tier-2/3 pegs that
    are declared but deliberately held back. PREREG 080bc40f said 60 referents;
    an earlier version of this returned 70 because it did not filter, so the ten
    held-back pegs silently entered training. They carry no minimal_pair and so
    never touched a headline number, but the deviation is recorded in
    docs/VERDICT_2B2_STRUCTURE_2026_08_20.md.
    """
    here = pathlib.Path(__file__).parent
    merged: list[Referent] = []
    family = None
    for name in ALL_PATHS:
        rs = load(here / name, allow_unreviewed=allow_unreviewed)
        if seeded_only:
            rs.referents = [r for r in rs.referents if r.seed_2a]
        if family and rs.grammar_family != family:
            raise ReferentError("mixing grammar families would confound the ablation")
        family = rs.grammar_family
        merged += rs.referents
    ids = [r.id for r in merged]
    if len(set(ids)) != len(ids):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        raise ReferentError(f"duplicate referent ids across files: {dupes}")
    return ReferentSet(review_status="REVIEWED", grammar_family=family,
                       referents=merged)


# ── PHASE 9: replace for live, archive for history (Nate's ruling 2026-08-23) ──
#
# `load_all()` IS the archive and is deliberately left untouched. Every phase
# 3-8 tool calls it, and silently repointing it at v2 would change what those
# tools reproduce while their preregs still claim 60 referents -- the same class
# of failure as editing a locked prereg body. So the switch is EXPLICIT: new
# work asks for `load_live()`, old work keeps getting exactly what it got.

def load_archive(*, allow_unreviewed: bool = False) -> ReferentSet:
    """The frozen 60 (20 Tier-1 + 20 perspective + 20 diagnostic).

    Archived, not deleted: it stays runnable against the listener for
    continuity checks, and it is the only place the 2b.2 minimal-pair history
    lives (PREREG 080bc40f, within-pair 99.5 % / 99.8 %). v2 carries no
    minimal_pair fields, so this set is not reconstructible from it.
    """
    return load_all(allow_unreviewed=allow_unreviewed)


def load_live(*, allow_unreviewed: bool = False,
              seeded_only: bool = True) -> ReferentSet:
    """The LIVE measurement set: v2, The Distance of the Moon. 46 of 50.

    Replacing rather than extending is deliberate. Mixing deep Cosmicomics
    referents with the shallow old geometry would measure the average of the
    two, consistency-set size would barely move, and the whole point of the
    referent-set decision -- an UNDILUTED deep-set effect -- would be lost.

    Refuses while v2 is UNREVIEWED, via the same gate as every other file.

    ⛔⛔ seeded_only IS NOT OPTIONAL IN PRACTICE -- IT IS THE WHOLE HOLD-BACK.
    The first version of this function called bare `load()`, which -- unlike
    `load_all()` -- does NOT filter on seed_2a, so it served all 50 including
    M37/M38/M49/M50. M38 and M50 state the RETRACTED conservation claim as an
    image and are withheld precisely so they cannot whisper into a measurement;
    they were in 9.2a, 9.2b and 9.3's first runs. Recorded as DEVIATIONS_9 D1
    and re-run.

    ⭐ The lesson is not "remember the filter". `tests/test_referents_v2.py`
    already asserted the YAML flags were set, and that test passed the entire
    time -- it checked the DECLARATION and never that the LOADER honoured it.
    A test that cannot reach the defect is not coverage. The assertion that
    matters is now on this function's OUTPUT.
    """
    rs = load(V2_PATH, allow_unreviewed=allow_unreviewed)
    if seeded_only:
        rs.referents = [r for r in rs.referents if r.seed_2a]
    return rs


# ── PHASE 13.2 — the 2x2's two arms ──────────────────────────────────────
LYRIC_PATH = pathlib.Path(__file__).with_name("referents_residue_lyric.yaml")
RANDOM_PATH = pathlib.Path(__file__).with_name("referents_residue_random.yaml")
RESIDUE_PATHS = {"lyric": LYRIC_PATH, "random": RANDOM_PATH}


def load_residue_arm(name: str, *, allow_unreviewed: bool = False,
                     seeded_only: bool = True) -> ReferentSet:
    """A 13.2 arm, with the UNFILLED-SLOT REFUSAL.

    ⛔⛔ THE REFUSAL IS THE POINT OF THIS FUNCTION. The lyric arm ships with
    `residue_any: []` on every referent because its coordinates are the human
    distiller's, not code's. An empty residue_any is not an error the schema can
    see -- it parses fine, it just means "no residue constraint" -- so
    build_scene would set residue=None, R's residue term would be inert, every
    cluster-mate would fold to one medoid, and the arm would behave EXACTLY like
    a no-residue arm while looking healthy. That is a manufactured null of the
    D1 class: a dead measurement reading perfect.

    So an unfilled slot RAISES here rather than anywhere downstream, and the
    message says who fills it.
    """
    if name not in RESIDUE_PATHS:
        raise ReferentError(
            f"unknown residue arm {name!r}; have {sorted(RESIDUE_PATHS)}")
    rs = load(RESIDUE_PATHS[name], allow_unreviewed=allow_unreviewed)
    if seeded_only:
        rs.referents = [r for r in rs.referents if r.seed_2a]
    empty = [r.id for r in rs.referents
             if not any(p.residue_any for p in r.signature.contains)]
    if empty:
        raise ReferentError(
            f"{name}: {len(empty)}/{len(rs.referents)} referents have an "
            f"UNFILLED residue slot ({', '.join(empty[:5])}"
            f"{' …' if len(empty) > 5 else ''}). This arm cannot run: an empty "
            "residue_any makes build_scene emit residue=None, which collapses "
            "every cluster-mate into one medoid and manufactures a null. The "
            "lyric arm's coordinates are the human distiller's — see the "
            "brief at the top of the file, and tools/check_residue_slots.py.")
    # A mate whose residue matched its cluster-mate's would not be a distinct
    # referent at all: identical expressible signature AND identical residue.
    by_sig: dict[tuple, list] = {}
    for r in rs.referents:
        key = tuple(tuple(sorted(p.root_any)) for p in r.signature.contains)
        by_sig.setdefault(key, []).append(r)
    for key, mates in by_sig.items():
        coords = [p.residue_any for m in mates for p in m.signature.contains
                  if p.residue_any]
        flat = [c for cs in coords for c in cs]
        if len(set(flat)) != len(flat):
            raise ReferentError(
                f"{name}: cluster {key[0]} has two mates at the SAME residue. "
                "They share an expressible signature, so an identical residue "
                "makes them the same referent and the cluster is smaller than "
                "it reports.")
    return rs


def load_worldview(name: str, *, allow_unreviewed: bool = False,
                   seeded_only: bool = True) -> ReferentSet:
    """A PHASE 11 worldview set: 'cr', 'tao' (or 'v2' for the comparison).

    Applies the seed_2a filter, which `load()` alone does NOT -- that omission
    is exactly what let four held-back referents into 9.2a/9.2b/9.3's first
    runs (DEVIATIONS_9 D1). Every set-level accessor filters; none calls bare
    `load()`.
    """
    if name not in WORLDVIEW_PATHS:
        raise ReferentError(
            f"unknown worldview {name!r}; have {sorted(WORLDVIEW_PATHS)}")
    rs = load(WORLDVIEW_PATHS[name], allow_unreviewed=allow_unreviewed)
    if seeded_only:
        rs.referents = [r for r in rs.referents if r.seed_2a]
    return rs
