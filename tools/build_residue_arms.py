"""PHASE 13.2 -- compile the two arms of the 2x2.

WHAT CODE OWNS AND WHAT IT DOES NOT.

  Code compiles ...... the referent INVENTORY and SCAFFOLD (shared byte-for-byte
                       between the arms) and the CATEGORICAL arm's coordinates.
  A human distils .... the LYRIC arm's coordinates. They are written as EMPTY
                       SLOTS (`residue_any: []`) and the 13.2 runner REFUSES a
                       set with an unfilled slot.

⭐ THE EXPRESSIBLE SIGNATURES ARE DELIBERATELY PLAIN, AND THAT IS REQUIRED
RATHER THAN LAZY. The hypothesis is that the distinguishing content lives in the
INEXPRESSIBLE residue. An evocative name or an elaborate signature would put
evocation into the expressible part -- exactly the leak the whole phase is built
to prevent -- and would also hand the listener a sayable shortcut, collapsing the
non-vacuous M back to the 100% saturation every earlier phase suffered.

⛔ BOTH ARMS SHARE ONE GENERATED SCAFFOLD. They are emitted from the same
in-memory inventory in one run, so the arms cannot drift apart in the expressible
dimension. The only difference between the files is the residue block.

── THE CLUSTER CONSTRUCTION ──────────────────────────────────────────────
8 clusters x 3 mates = 24 referents. Within a cluster every mate has a
byte-identical expressible signature and differs ONLY in residue, so their
shared surface is consistent with all three and the listener's ceiling inside a
cluster is 1/3. Across clusters the (head, dependent) root pair is distinct, so
the signature core still identifies the CLUSTER -- the free channel has to carry
only the within-cluster index, which is the factorisation a shared head can
learn and a per-referent table cannot.

── THE LATTICE ───────────────────────────────────────────────────────────
3-D integer lattice, each axis 0..4. The bound is `residue.normalized`'s span
(4): normalised distance is L1/(span*dim) = L1/12, so it lands in [0,1] with NO
clipping. A coordinate outside would silently saturate at 1.0 and destroy the
gradation the metric arm exists to provide.

⛔ 3-D, NOT 2-D. 24 referents in a 5x5 grid is 96% occupancy -- 25 points for 24
things -- so nearly every placement is forced and graded judgment is
INEXPRESSIBLE however good the judgment is. 5x5x5 is 125 points, 19% occupied,
and 12 distinct distance levels instead of 8.
"""
from __future__ import annotations

import argparse
import itertools
import pathlib
import random
import statistics as S
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.grammar import classes as C                            # noqa: E402
from tlon.grammar import residue as R                            # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "tlon" / "referents"
N_CLUSTERS, N_MATES = 8, 3
AXIS = 5                      # coordinates 0..4 on each axis
SPAN = 4                      # == residue.normalized's span; do not decouple
LATTICE_DIM = 3   # 3-D: 125 points for 24 referents (2-D was 96% occupied)


class BannerMismatch(RuntimeError):
    pass


def banner(label: str, value, expected, fmt="{}") -> None:
    if value != expected:
        raise BannerMismatch(f"{label}: printed {value!r}, expected {expected!r}")
    print(f"    {label:<52} {fmt.format(value)}")


# ── THE INVENTORY, compiled from Nate's distilled brief (2026-08-23) ──────
#
# PROVENANCE, and it is the whole of it: SOURCE CONSULTED — NONE. Compiled only
# from the distilled positions Nate wrote in the 13.2 brief ("choosing not to go
# hollow", the five tension-axes, the eight happenings and their three readings
# each). No lyric was read, recalled or reconstructed at the compilation step,
# so there was no expression to strip. Same discipline as the CR and TAO sets.
# The artists Nate named fix the REGISTER; no referent derives from any of them.
#
# ⭐ THE DENOTATIONS ARE REAL NOW. The first scaffold took roots in alphabetical
# order and ignored the lexicon's glosses entirely, so "a fal, fro a fang" meant
# nothing and there was nothing for a distiller to place. Each happening now
# carries a root pair whose gloss IS the happening -- `klung` is literally
# "it hollows, voids", which is the brief's central image.
#
# ⛔ The three mates of a cluster share a BYTE-IDENTICAL expressible signature.
# The reading is carried ONLY by the name+notes (human-facing, never parsed,
# never rendered, never seen by the listener) and by the residue coordinate.
HAPPENINGS = [
    # (head, via, dep, gloss, [(reading, notes, coord) x3])
    ("klung", "sen", "lan", "a hollowing, AT a beholding", [
        ("tender-holding", "H1 anchor. Witnessing someone you love slip toward "
         "the hollow, held soft. Nearest the attractor.", (0, 1, 0)),
        ("the ache without resolution", "H1 anchor. The same witnessing, pulled "
         "to pressed-down; no turn, no relief.", (3, 1, 1)),
        ("the systemic gaze", "H1 anchor. The same witnessing, turned outward "
         "at what is taking them; pulled to material and outward.", (1, 4, 3))]),
    ("lan", "mil", "plung", "a beholding, LIKE an opening", [
        ("as refuge", "Really seeing another person, and the seeing is where "
         "you go to be safe.", (0, 0, 1)),
        ("as revelation", "The recognition lands as light — lit-up, and the "
         "ineffable is what is real in it.", (1, 2, 0)),
        ("as gift to the other", "The seeing is given away; tenderness aimed "
         "outward rather than kept.", (0, 3, 1))]),
    ("lus", "hlim", "tang", "a singing, AMID a holding", [
        ("solitary refuge", "The record as the room they cannot enter. Inward, "
         "un-takeable.", (1, 0, 0)),
        ("shared communion", "The same refuge, but it is a cipher — the "
         "holding is collective.", (0, 3, 0)),
        ("defiant joy", "Craft as gladness thrown back at the pressure; "
         "outward, lit, with force behind it.", (2, 4, 1))]),
    ("los", "xom", "nin", "a speaking, THOUGH a hardening", [
        ("for the collective", "Naming the machine on behalf of the room; "
         "outward, confronting the material.", (2, 4, 3)),
        ("as personal defiance", "The same naming, but it is one person's "
         "refusal; intimate and force-side.", (3, 2, 3)),
        ("as grief at what it costs", "Naming it and counting the cost; "
         "pressed-down, tender, inward.", (3, 1, 2))]),
    ("mling", "hlim", "nos", "a recalling, AMID a weighing", [
        ("the gift", "Inheritance received as knowledge; tender, ineffable.",
         (0, 2, 0)),
        ("the weight", "The same inheritance as trauma carried; furthest "
         "pressed-down, and the material is undeniable.", (4, 1, 2)),
        ("the duty to pass it on", "Inheritance as obligation forward; "
         "collective, outward.", (2, 3, 1))]),
    ("mim", "kra", "rom", "a waking, CAUSED-BY an appearing", [
        ("liberation", "Knowledge of self as the thing that frees. The "
         "attractor itself.", (0, 0, 0)),
        ("the loneliness of it", "Becoming who you are, and being alone in it; "
         "inward, and the material presses.", (2, 0, 2)),
        ("the discipline it demands", "Self-recognition as daily work; force "
         "turned on oneself, still intimate.", (2, 1, 0))]),
    ("tir", "sul", "run", "a grieving, TOWARD a changing", [
        ("the raw loss", "Before the turn. Furthest from the attractor on the "
         "gross axis.", (4, 2, 3)),
        ("the turn", "The hinge itself, mid-way in every axis.", (3, 3, 2)),
        ("the resolve", "Grief metabolised into refusal; moving back toward "
         "the attractor.", (2, 2, 1))]),
    ("sun", "hlin", "six", "a longing, MORE-THAN a dreading", [
        ("love as strength", "Choosing the soft thing because it is the strong "
         "thing.", (1, 1, 1)),
        ("love as risk", "The ledger is real and loving costs; nearest the "
         "material pole.", (2, 2, 4)),
        ("love as the only un-takeable thing", "The ledger is real and love is "
         "outside it anyway.", (0, 2, 2))]),
]


def inventory() -> list[dict]:
    """The shared scaffold, from HAPPENINGS. Both arms are emitted from this."""
    lex = C.load()["classes"]
    out = []
    for c, (head, via, dep, gloss, mates) in enumerate(HAPPENINGS):
        for r in (head, dep):
            if r not in lex["R"]:
                raise RuntimeError(f"{r!r} is not a root in the lexicon")
        if via not in lex["L"]:
            raise RuntimeError(f"{via!r} is not a relator")
        for m, (reading, notes, coord) in enumerate(mates):
            out.append({
                "id": f"C{c + 1}M{m + 1}", "cluster": c + 1, "mate": m + 1,
                "head": head, "dep": dep, "via": via, "gloss": gloss,
                "coord": coord,
                "name": f"{gloss} — {reading}",
                "notes": notes,
            })
    return out


def categorical_coords(n: int, scale: int) -> list[tuple[int, ...]]:
    """One-hot, so every pair of distinct residues is EQUIDISTANT.

    ⭐ This is what makes the categorical arm a real categorical arm inside an
    integer-lattice type: L1 between two distinct one-hots is 2*scale whatever
    the pair, so the space has no 'nearby' at all.

    ⭐⭐ AND IT REDUCES THE HEAD TO A TABLE, WHICH IS A PREDICTION THE DESIGN
    MAKES RATHER THAN A CONVENIENCE: a one-hot input into a linear layer IS a
    row lookup, so `categorical x head` should land on `categorical x table`.
    If those two cells disagree, something in the 2x2 is wrong and the metric
    cells cannot be read yet.
    """
    return [tuple(scale if j == i else 0 for j in range(n)) for i in range(n)]


def mean_normalised(coords: list[tuple[int, ...]]) -> float:
    return S.fmean(R.normalized(a, b, span=SPAN)
                   for a, b in itertools.combinations(coords, 2))


def lattice_expected_mean() -> float:
    """Mean normalised L1 over the FULL 5x5 lattice.

    The match target is computed from the LATTICE, not from a realised
    assignment, because the lyric coordinates do not exist yet. It is the
    distiller's brief that is fixed, so the target derived from it is available
    now -- and `--rematch` re-derives it from the real coordinates once they
    land, which is the number that actually goes in the verdict.
    """
    import itertools as _it
    pts = list(_it.product(range(AXIS), repeat=LATTICE_DIM))
    return mean_normalised(pts)


def scale_matching(target: float, n: int) -> int:
    """Smallest one-hot scale whose constant distance best matches `target`.

    ⛔ WHY MATCH AT ALL. At lambda=0 -- the R-ISOLATED primary -- R is not in
    the reward and this is cosmetic. At lambda>0 it is not: if the arms carry
    different mean residue distance, they face different novelty pressure and a
    metric-vs-categorical difference is attributable to R rather than to the
    head. Matching the MEAN leaves the STRUCTURE (graded vs constant) as the
    only difference, which is the manipulation.
    """
    best, err = 1, None
    for s in range(1, 4 * SPAN * n):
        got = min(1.0, (2 * s) / (SPAN * n))
        e = abs(got - target)
        if err is None or e < err:
            best, err = s, e
    return best


def emit(rows: list[dict], coords: list[tuple[int, ...]] | None,
         path: pathlib.Path, *, arm: str, header: str) -> None:
    """`coords=None` writes EMPTY SLOTS for the human distiller."""
    L: list[str] = [header, "",
                    "review_status: UNREVIEWED     "
                    "# ⛔ Nate sets this. Nothing runs until then.",
                    "schema_version: 2",
                    "grammar_family: southern",
                    f"residue_arm: {arm}",
                    "", "referents:", ""]
    last = None
    for i, r in enumerate(rows):
        if r["cluster"] != last:
            last = r["cluster"]
            L.append(f"  # ═══ CLUSTER {r['cluster']} — head `{r['head']}`, "
                     f"dependent `{r['dep']}` via `{r['via']}` "
                     f"({N_MATES} mates, one expressible signature) ═══")
        c = coords[i] if coords is not None else None
        L += [f'  - id: "{r["id"]}"',
              f'    name: {r["name"]}',
              f'    notes: >-',
              f'      {r["notes"]}',
              "    tier: 1",
              "    signature:",
              "      contains:",
              f'        - root_any: ["{r["head"]}"]',
              ("          residue_any: []"
               "            # ⛔ SLOT — the distiller fills this"
               if c is None else
               f'          residue_any: [{list(c)}]'),
              f'        - root_any: ["{r["dep"]}"]',
              f'          via: ["{r["via"]}"]',
              ""]
    path.write_text("\n".join(L), encoding="utf-8", newline="\n")
    print(f"    wrote {path.name}  ({len(rows)} referents)")


LYRIC_HEADER = """\
# Tlön referent set — 13.2 METRIC ARM (lyric-derived evocative geometry).
#
# ⛔⛔ THIS FILE IS INCOMPLETE BY DESIGN. Every `residue_any: []` is an EMPTY
# SLOT awaiting the human distiller. `tools/check_residue_slots.py` reports
# what is unfilled and the 13.2 runner REFUSES to run against an unfilled set —
# an empty residue_any means build_scene sets residue=None, which would make
# this arm behave exactly like a no-residue arm and manufacture a null.
#
# ─── THE DISTILLER'S BRIEF ────────────────────────────────────────────────
#
# Place each of the 24 referents at an integer coordinate (x, y, z) with
# 0 <= x, y, z <= 4 — a 5x5x5 lattice, 125 points. L1 distance between two
# coordinates IS their evocative dissimilarity: near = gestures at something
# similar, far = something other.
#
# ⛔ THE BOUND IS NOT DECORATION. `residue.normalized` divides by span*dim =
# 4*3 = 12, so L1 lands in [0,1] with no clipping; a coordinate outside 0..4
# silently saturates at 1.0 and destroys the gradation this arm exists for.
#
# ⛔ 3-D, NOT 2-D. 24 referents in a 5x5 GRID is 96% occupancy — 25 points for
# 24 things — so nearly every placement is forced and graded judgment is
# INEXPRESSIBLE however good the judgment is. 5x5x5 is 19% occupied with 12
# distinct distance levels instead of 8. (PREREG 4ad552d4 §2 still says 2-D;
# that is a recorded deviation, DEVIATIONS_13_2 D10, never a prereg edit.)
#
# ⭐ THE AXES AS BUILT, so a second distiller places on the same frame:
#   origin (0,0,0) IS the attractor — love-held-against-loss
#   x = departure toward pressed-down + force          (Nate's axes 1 x 2)
#   y = departure toward collective + confront-outward (axes 3 x 4)
#   z = departure toward the material ledger           (axis 5, gross position)
# ⛔ The 5-axis -> 3-axis projection is CODE'S, not the brief's (D11). A second
# distiller may reject the frame; say so rather than forcing a placement into it.
#
# ⛔⛔ WORDS STAY AT THE DOOR. The geometry is of WHAT LYRICS GESTURE AT —
# which evocations cluster near, which fall far — NEVER of any lyric's words.
# The words are the denotation: sayable, parser-recoverable, and the part we
# neither want nor may take. No source text may enter this file, and
# `tools/expression_check.py` audits names and notes as well as the residue
# TYPE (coordinates only — a string residue is the side door).
#
# ⭐ Coordinates may repeat across CLUSTERS (two unrelated referents may evoke
# similarly) but must DIFFER WITHIN a cluster — mates are denotationally
# identical, so an identical residue would make them the same referent.
#
# ⭐ THE EXPRESSIBLE SIGNATURES ARE PLAIN ON PURPOSE. Everything that
# distinguishes a mate from its cluster-mates lives in the residue. That is the
# hypothesis, so it must also be the construction."""

RANDOM_HEADER = """\
# Tlön referent set — 13.2 CATEGORICAL ARM (the unstructured null).
#
# ⛔ GENERATED. Do not hand-edit — regenerate with
#    `python tools/build_residue_arms.py`. Both arms are emitted from ONE
#    in-memory inventory in a single run, so the expressible scaffold is shared
#    byte-for-byte with the lyric arm and the arms cannot drift apart.
#
# ─── WHAT THIS ARM IS FOR ─────────────────────────────────────────────────
#
# The residue here is ONE-HOT, so every pair of distinct residues is exactly
# EQUIDISTANT: the space has no 'nearby' at all. That is a free CATEGORICAL
# residue expressed inside the integer-lattice type, so no second code path and
# no second metric are needed — the arms differ only in their coordinates.
#
# ⭐⭐ AND IT MAKES A PREDICTION, WHICH IS BETTER THAN A CONVENIENCE: a one-hot
# input into a linear layer IS a row lookup, so the residue-conditioned HEAD
# degenerates to exactly the per-referent TABLE on this arm. `categorical x
# head` should therefore land on `categorical x table`. If those two cells
# disagree, the 2x2 is not measuring what it claims and the metric cells cannot
# be read yet — an internal consistency check the design gets for free."""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rematch", metavar="LYRIC_YAML",
                    help="recompute the one-hot scale from REAL lyric "
                         "coordinates once the slots are filled")
    args = ap.parse_args()

    rows = inventory()
    n = len(rows)
    print("\n  13.2 ARM COMPILATION")
    banner("clusters", N_CLUSTERS, 8)
    banner("mates per cluster", N_MATES, 3)
    banner("referents", n, 24)
    banner("distinct head roots", len({r["head"] for r in rows}), 8)
    banner("distinct dependent roots", len({r["dep"] for r in rows}), 8)
    banner("within-cluster expressible signatures", len({
        (r["cluster"], r["head"], r["dep"], r["via"]) for r in rows}), 8)
    print(f"    {'listener ceiling inside a cluster':<52} "
          f"{100 / N_MATES:.1f}%")

    # ⛔ D7 RESOLVED: the lyric coordinates now EXIST, so the one-hot scale is
    # matched to the REALISED geometry, not to the lattice expectation. The
    # lattice figure was only ever a stand-in for coordinates that did not
    # exist yet; quoting it now would match the categorical arm to a set nobody
    # placed.
    target = mean_normalised([r["coord"] for r in rows])
    src = "the REALISED lyric coordinates (D7 resolved)"
    if args.rematch:
        import yaml
        raw = yaml.safe_load(pathlib.Path(args.rematch).read_text(encoding="utf-8"))
        got = [tuple(p["residue_any"][0])
               for row in raw["referents"]
               for p in row["signature"]["contains"] if p.get("residue_any")]
        if len(got) != n:
            raise RuntimeError(f"{len(got)}/{n} slots filled; cannot rematch")
        target = mean_normalised(got)
        src = f"the REALISED lyric coordinates in {pathlib.Path(args.rematch).name}"
    scale = scale_matching(target, n)
    cat = categorical_coords(n, scale)
    got = mean_normalised(cat)
    print(f"\n    {'mean normalised residue distance, target':<52} "
          f"{target:.4f}")
    print(f"    {'  ...derived from':<52} {src}")
    print(f"    {'one-hot scale chosen':<52} {scale}")
    print(f"    {'mean normalised residue distance, categorical':<52} "
          f"{got:.4f}  (|Δ| {abs(got - target):.4f})")
    print(f"    {'categorical pairwise distances are constant':<52} "
          f"{len({R.normalized(a, b, span=SPAN) for a, b in itertools.combinations(cat, 2)}) == 1}")

    print()
    emit(rows, [r["coord"] for r in rows],
         OUT / "referents_residue_lyric.yaml",
         arm="metric-lyric", header=LYRIC_HEADER)
    emit(rows, cat, OUT / "referents_residue_random.yaml",
         arm="categorical", header=RANDOM_HEADER)
    print("\n  ⛔ Both files are UNREVIEWED — Nate sets review_status.")
    print("     ⛔⛔ The lyric arm's coordinates are CODE'S PROJECTION of Nate's")
    print("     briefed 5-axis geometry into 3-D, NOT an independent human")
    print("     distillation. The Mantel test still needs two human matrices.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
