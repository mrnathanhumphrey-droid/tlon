"""The comparison guard. PHASE 9.0.

⛔⛔ THE PROJECT'S RECURRING ERROR, FIVE TIMES, THREE COSTUMES:

  1. phase 3   the contaminated cipher control -- a SCRAMBLED SUBSET compared
               against a FULL-SET baseline. Manufactured a 1.35 pt drop on a
               channel that is provably a no-op.
  2. phase 7   the auditor "floor curve" -- one point per withholding rate, and
               each rate is a DIFFERENT ITEM SET. Read flat; I concluded the
               auditor ignored the withheld content. Paired on identical items
               it is 42.8 % vs 34.9 %, a 7.9 pt effect, 3x the unpaired
               estimate. The conclusion was RETRACTED (D10).
  3. phase 8.3a the teachability "spike" -- windows BEFORE and AFTER an event
               WITHIN ONE RUN. Policy entropy declines monotonically as
               training converges, so the trend swamped the transient and the
               spike read -7 %. Uninterpretable.

It has been written into two verdicts as a lesson and committed again after
both. So it moves into tooling, the way root allocation moved from hand-typing
to deterministic generation: the goal is that the error becomes UNEXPRESSABLE,
not that it is remembered against.

⭐ HOW THE ERROR IS MADE UNEXPRESSABLE

A bare float carries no record of what it was measured over, so `a - b` can
always be typed. Therefore measurements are not bare floats. A `Measurement`
carries its `ItemSet`; `Measurement.__sub__` REFUSES; and the only way to get a
difference is `paired_delta(a, b, contrast=...)`, which requires the caller to
NAME the one thing allowed to differ. Five conditions are then checked:

    kind identical  ·  item digest identical  ·  the named contrast is a
    declared facet of both  ·  every OTHER facet identical  ·  the contrast
    facet actually differs

The digest is computed from the ACTUAL item keys, never from a label the caller
types, so two genuinely different sets cannot be declared paired by naming them
the same thing. `measure()` goes one better: it iterates the item list itself
and hands that same list to the scoring function, so the recorded set is
provably the set that was scored.

⭐ AND THE COMPARISON THAT CANNOT BE PAIRED

Some comparisons are unpairable by construction -- Phase 9.2's old referent set
vs the new one is over different referents, so no pairing exists. Those are not
forced through the guard and they are not quietly subtracted either: they go to
`side_by_side()`, which holds both measurements, demands a written reason, and
whose `.delta` RAISES. Reporting them next to each other is legitimate;
differencing them is not.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence


class UnpairedComparison(RuntimeError):
    """A difference was requested between two non-comparable measurements."""


class ConfoundedContrast(UnpairedComparison):
    """More than one thing differs, so the delta cannot be attributed."""


class DegenerateContrast(UnpairedComparison):
    """The named contrast does not actually differ -- this compares a thing
    with itself and will report 0.00 as though that were a result."""


class ItemIdentityError(RuntimeError):
    """The item keys do not identify the items (empty, or not distinct)."""


def _fmt(v: Any) -> str:
    """Facet values are compared as text so that 0.5 and 0.50 cannot disagree
    while looking identical in a printout."""
    if isinstance(v, float):
        return repr(round(v, 12))
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


@dataclass(frozen=True)
class ItemSet:
    """WHAT a measurement was computed over, as an identity that can be
    compared -- not a description of it.

    `digest` is over the sorted item keys, so it is a property of the items.
    `facets` are the declared conditions (seed, withholding rate, arm, gloss
    mode, step window ...). Two measurements are paired iff their digests AND
    all their facets but one agree.
    """
    kind: str
    n: int
    digest: str
    facets: tuple[tuple[str, str], ...]
    keys: frozenset[str] = field(default=frozenset(), compare=False, repr=False)

    @staticmethod
    def of(kind: str, keys: Iterable[Any], **facets: Any) -> "ItemSet":
        ks = [str(k) for k in keys]
        if not ks:
            raise ItemIdentityError(
                f"{kind}: empty item set. Two empty sets compare EQUAL, so this "
                "would silently pair two vacuous measurements.")
        uniq = set(ks)
        if len(uniq) != len(ks):
            dupes = sorted({k for k in ks if ks.count(k) > 1})[:5]
            raise ItemIdentityError(
                f"{kind}: {len(ks) - len(uniq)} duplicate item keys "
                f"(e.g. {dupes}). A key that repeats does not identify an item, "
                "so 'the same items' cannot be established. Make the key unique "
                "-- include the index or the subset -- or the pairing is fiction.")
        blob = kind + "\n" + "\n".join(sorted(ks))
        return ItemSet(
            kind=kind, n=len(ks),
            digest=hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16],
            facets=tuple(sorted((k, _fmt(v)) for k, v in facets.items())),
            keys=frozenset(uniq))

    def facet(self, name: str) -> str | None:
        return dict(self.facets).get(name)

    def facet_names(self) -> frozenset[str]:
        return frozenset(k for k, _ in self.facets)

    def label(self) -> str:
        f = " ".join(f"{k}={v}" for k, v in self.facets)
        return f"{self.kind}[n={self.n} {self.digest}]{(' ' + f) if f else ''}"


@dataclass(frozen=True)
class Measurement:
    """A number that remembers what it was measured over."""
    name: str
    value: float
    items: ItemSet

    def __sub__(self, other: Any) -> Any:
        raise UnpairedComparison(
            f"refusing to subtract measurements directly ({self.name!r} - "
            f"{getattr(other, 'name', other)!r}). Use "
            "paired_delta(a, b, contrast='<the one thing that differs>'), "
            "which checks the item sets, or side_by_side(a, b, reason=...) "
            "when no pairing exists.")

    __rsub__ = __sub__

    def pct(self) -> str:
        return f"{100 * self.value:.2f}"


@dataclass(frozen=True)
class Delta:
    """A difference that survived the guard. Carries the contrast it is
    attributable to, because a delta without one is not interpretable."""
    value: float
    contrast: str
    left: Measurement
    right: Measurement

    @property
    def contrast_values(self) -> tuple[str | None, str | None]:
        return (self.left.items.facet(self.contrast),
                self.right.items.facet(self.contrast))

    def pts(self) -> str:
        return f"{100 * self.value:+.2f}"

    def describe(self) -> str:
        lo, hi = self.contrast_values
        return (f"{self.left.name} - {self.right.name} = {self.pts()} pts "
                f"[paired on {self.left.items.kind} n={self.left.items.n} "
                f"{self.left.items.digest}; {self.contrast}: {lo} vs {hi}]")


def _diff_sample(a: ItemSet, b: ItemSet, k: int = 4) -> str:
    only_a = sorted(a.keys - b.keys)[:k]
    only_b = sorted(b.keys - a.keys)[:k]
    if not only_a and not only_b:
        return "(same keys, different kind or ordering-independent digest clash)"
    return (f"only in left: {only_a}{' ...' if len(a.keys - b.keys) > k else ''}; "
            f"only in right: {only_b}"
            f"{' ...' if len(b.keys - a.keys) > k else ''}")


def paired_delta(a: Measurement, b: Measurement, *, contrast: str) -> Delta:
    """a - b, but only if they are the same items differing in ONE named thing.

    `contrast` is required and is not decoration: it names the facet under test.
    Every other facet must be identical (or the delta is confounded) and the
    contrast facet must actually differ (or the delta is a zero dressed as a
    result).
    """
    if not isinstance(a, Measurement) or not isinstance(b, Measurement):
        raise UnpairedComparison(
            "paired_delta takes two Measurements. A bare float has no record of "
            "what it was measured over, which is the whole failure mode.")

    if a.items.kind != b.items.kind:
        raise UnpairedComparison(
            f"item KINDS differ: {a.items.kind!r} vs {b.items.kind!r}. "
            f"({a.name!r} vs {b.name!r}) These are not the same population; "
            "report them with side_by_side(), never subtracted.")

    if a.items.digest != b.items.digest:
        raise UnpairedComparison(
            f"UNPAIRED: {a.name!r} was measured over {a.items.n} items "
            f"({a.items.digest}) and {b.name!r} over {b.items.n} "
            f"({b.items.digest}).\n  {_diff_sample(a.items, b.items)}\n"
            "  Between-set variation will absorb the effect -- it can hide a "
            "real one entirely or manufacture one, and it looks like a clean\n"
            "  measurement either way (phase-3 cipher control, phase-7 floor "
            "curve, phase-8.3a entropy windows). Measure both terms over the\n"
            "  SAME items, or report with side_by_side() if no pairing exists.")

    names_a, names_b = a.items.facet_names(), b.items.facet_names()
    if names_a != names_b:
        raise UnpairedComparison(
            f"the two measurements declare different facets: "
            f"{sorted(names_a ^ names_b)}. A facet declared on one side and not "
            "the other is a condition nobody checked.")

    if contrast not in names_a:
        raise UnpairedComparison(
            f"contrast {contrast!r} is not a declared facet. Declared: "
            f"{sorted(names_a)}. Name the facet under test; if it is not "
            "recorded on the measurements, it was not controlled.")

    fa, fb = dict(a.items.facets), dict(b.items.facets)
    others = sorted(n for n in names_a
                    if n != contrast and fa[n] != fb[n])
    if others:
        detail = ", ".join(f"{n}: {fa[n]} vs {fb[n]}" for n in others)
        raise ConfoundedContrast(
            f"CONFOUNDED: contrast is {contrast!r} but {len(others)} other "
            f"facet(s) also differ -- {detail}. The delta cannot be attributed "
            "to the contrast. Hold the others fixed, or make the differing one "
            "the contrast.")

    if fa[contrast] == fb[contrast]:
        raise DegenerateContrast(
            f"DEGENERATE: contrast {contrast!r} is {fa[contrast]!r} on BOTH "
            "sides, so nothing under test differs. This would report a "
            "difference between a thing and itself as a result.")

    return Delta(value=a.value - b.value, contrast=contrast, left=a, right=b)


@dataclass(frozen=True)
class SideBySide:
    """Two measurements that CANNOT be paired, reported without subtraction.

    Phase 9.2's old-set vs new-set comparison is the motivating case: different
    referents, so no pairing exists and no delta is meaningful. Holding them in
    a type that has no difference operator is what stops the number being
    computed anyway three paragraphs later.
    """
    reason: str
    left: Measurement
    right: Measurement

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError(
                "side_by_side needs a written reason why no pairing exists. "
                "If you cannot state one, the comparison is probably pairable.")
        if self.left.items == self.right.items:
            raise ValueError(
                "these measurements ARE paired (identical items and facets) -- "
                "use paired_delta(), which gives you the difference and checks "
                "the contrast. side_by_side is for the unpairable case only.")

    @property
    def delta(self) -> float:
        raise UnpairedComparison(
            f"there is no delta here, by construction: {self.reason}\n"
            f"  left  {self.left.name} = {self.left.pct()} over "
            f"{self.left.items.label()}\n"
            f"  right {self.right.name} = {self.right.pct()} over "
            f"{self.right.items.label()}\n"
            "  Report the two numbers next to each other. Subtracting them "
            "would be the unpaired comparison with extra steps.")

    def describe(self) -> str:
        return (f"SIDE BY SIDE (no pairing: {self.reason})\n"
                f"    {self.left.name:<34} {self.left.pct():>8}   "
                f"{self.left.items.label()}\n"
                f"    {self.right.name:<34} {self.right.pct():>8}   "
                f"{self.right.items.label()}")


def side_by_side(a: Measurement, b: Measurement, *, reason: str) -> SideBySide:
    return SideBySide(reason=reason, left=a, right=b)


def measure(name: str, kind: str, items: Sequence[Any],
            fn: Callable[[Sequence[Any]], float], *,
            key: Callable[[Any], Any] = repr, **facets: Any) -> Measurement:
    """Score `items` with `fn` and record THAT list as the item set.

    The point of routing through here rather than building the ItemSet by hand:
    the same list object is both keyed and scored, so the recorded identity
    cannot drift from what was actually measured. Anything built by hand can.
    """
    seq = list(items)
    iset = ItemSet.of(kind, [key(i) for i in seq], **facets)
    return Measurement(name=name, value=float(fn(seq)), items=iset)


# ── McNEMAR: the paired test for PER-ITEM BINARY outcomes ─────────────────
@dataclass(frozen=True)
class McNemar:
    """An exact paired test on two runs of the SAME battery.

    ⛔⛔ THE UNPAIRED DISEASE, ONE LAYER DOWN — IN THE RECORDING. The
    comprehension battery is byte-identical across runs, so the items ARE
    paired. But the ledger stored only the ACCURACY, never the per-item
    outcomes, so the pairing was thrown away at write time and only the weaker
    unpaired test remained available. Measured cost: baseline 39.1 % vs run 2
    51.6 % read **p = 0.21 unpaired** at n=64 and could not be resolved either
    way. **You cannot recover pairing you did not record.**

    ⭐ McNemar ignores the items both runs agree on -- they carry no information
    about a DIFFERENCE -- and tests only the DISCORDANT pairs, which is why it
    has power the unpaired test cannot reach at the same n.
    """
    b: int              # right in A, wrong in B
    c: int              # wrong in A, right in B
    n: int
    p: float
    concordant: int

    def verdict(self, alpha: float = 0.05) -> str:
        if self.b + self.c == 0:
            return ("⛔ NO DISCORDANT PAIRS — the two runs agree on every item, "
                    "so there is nothing for a paired test to see.")
        d = "B better" if self.c > self.b else "A better"
        return (f"{d} on {max(self.b, self.c)}/{self.b + self.c} discordant "
                f"pairs, p={self.p:.4f} "
                f"{'SIGNIFICANT' if self.p < alpha else 'not significant'}")


def mcnemar(a_correct: dict, b_correct: dict, *, require_same_items: bool = True
            ) -> McNemar:
    """Exact McNemar on `{item_key: bool}` outcomes from two runs.

    ⛔ Refuses mismatched item sets rather than intersecting them silently: an
    intersection is a THIRD item set neither run reported, and comparing over it
    is the unpaired error wearing a paired costume.
    """
    ka, kb = set(a_correct), set(b_correct)
    if require_same_items and ka != kb:
        only_a, only_b = sorted(ka - kb)[:4], sorted(kb - ka)[:4]
        raise UnpairedComparison(
            f"item sets differ: {len(ka - kb)} only in A (e.g. {only_a}), "
            f"{len(kb - ka)} only in B (e.g. {only_b}). Intersecting them "
            "would invent a third item set that neither run reported.")
    keys = sorted(ka & kb)
    if not keys:
        raise ItemIdentityError("no shared items: nothing to pair.")
    b = sum(1 for k in keys if a_correct[k] and not b_correct[k])
    c = sum(1 for k in keys if not a_correct[k] and b_correct[k])
    n = b + c
    if n == 0:
        p = 1.0
    else:
        # exact two-sided binomial on the discordant pairs, H0: p = 1/2
        tail = sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n
        p = min(1.0, 2 * tail)
    return McNemar(b=b, c=c, n=len(keys), p=p,
                   concordant=len(keys) - b - c)
