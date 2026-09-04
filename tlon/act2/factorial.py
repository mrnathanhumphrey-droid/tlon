"""THE FACTORIAL'S BOOKKEEPING — which cell is an adapter in, and how well paired.

⛔⛔ AN ARMY OF ADAPTERS IS ONLY ANALYSABLE IF EVERY CONTRAST CHANGES ONE KNOB.
The design is {content-free, content-transient} × {memory model} × {seeds}, and
what makes it a matrix rather than a pile is that `content-free-seed-X` and
`content-transient-seed-X` differ in recipe and in nothing else. This module is
where "and in nothing else" is recorded, checked, and refused when false.

⭐⭐ PAIRING IS A PROPERTY OF THE PAIR, NOT OF AN ADAPTER. Two adapters are
matched only if BOTH came off the split-stream generator. One legacy side is
enough to make the whole pair `seed`-only, because the force sequence the legacy
side painted was perturbed by its own content draws and no longer matches its
partner's. Taking the better of the two regimes -- or reading one side's label
as the pair's -- would silently promote a high-variance pair into the
low-variance cell.

⛔⛔ AND A MISSING LABEL MEANS LEGACY, NEVER MATCHED. Every corpus built before
the split-stream generator existed has no regime field at all. Defaulting an
absent field to the *better* regime is the vacuous pass this project keeps
finding: it would take exactly the adapters whose pairing is unknown and file
them as the ones whose pairing is best.
"""
from __future__ import annotations

from collections import Counter

from ..discourse.transient import (CONTENT_FREE, CONTENT_TRANSIENT,  # noqa: F401
                                   GENERATOR_LEGACY, GENERATOR_SPLIT_STREAM,
                                   PAIRED_SEED_AND_FORCE, PAIRED_SEED_ONLY,
                                   RECIPES)

#: Short codes for filenames. ⭐ Derived from the recipe names, never re-spelt.
RECIPE_CODE = {CONTENT_FREE: "cf", CONTENT_TRANSIENT: "ct"}


class FactorialError(RuntimeError):
    """A cell that cannot be attributed. ⛔ Raised, never warned."""


def generator_of(manifest) -> str:
    """Which generator built this corpus.

    ⛔⛔ ABSENT MEANS LEGACY. A corpus manifest with no `generator` field predates
    the split-stream path, so its force sequence is coupled to its content draws.
    Returning the split-stream id for an unlabelled corpus would file an
    unknown-pairing adapter into the matched cell.
    """
    if not isinstance(manifest, dict):
        raise FactorialError("manifest must be an object, got %s"
                             % type(manifest).__name__)
    return manifest.get("generator") or GENERATOR_LEGACY


def recipe_of(manifest) -> str:
    """⛔ The recipe is NOT inferable and has no default. An adapter whose recipe
    is unknown belongs to no cell, and guessing one would place it in a
    contrast it was never part of."""
    r = (manifest or {}).get("recipe")
    if r not in RECIPES:
        raise FactorialError(
            "manifest has no usable `recipe` (got %r; valid are %s). An adapter "
            "whose recipe is unknown belongs to no cell of the factorial."
            % (r, ", ".join(RECIPES)))
    return r


def pairing_regime(*manifests) -> str:
    """The regime for a PAIR (or for one side, conservatively).

    ⭐ The rule is the WORST of the sides, not the best: a matched pair requires
    every side to have come off the split-stream generator.
    """
    if not manifests:
        raise FactorialError("no manifests given; a regime describes a pair")
    gens = [generator_of(m) for m in manifests]
    if all(g == GENERATOR_SPLIT_STREAM for g in gens):
        return PAIRED_SEED_AND_FORCE
    return PAIRED_SEED_ONLY


def adapter_label(recipe: str, seed: int,
                  suppression_window: int | None = None) -> str:
    """`ct-s20624` / `cf-s20624` / `ctw1-s20624`. ⭐ The cell, in the filename.

    ⛔ A directory called `adapter_s20624` cannot say which arm it is in, and the
    matrix is reconstructed from exactly these strings once the terminal
    scrollback is gone.

    ⛔⛔ AND THE DOSE IS PART OF THE CELL. This ignored `suppression_window`, so
    `ctw1-s20624` — window 1 — wrote `"cell": "ct-s20624"`, the GATE's cell, with
    the gate's pair key. Two different treatments claiming one cell: the run
    directory and the hub prefix were right, and the field every pooling routine
    actually reads was wrong. Caught by reading the artifact off the hub instead
    of trusting that it said what the directory said.

    ⭐ Window 0 keeps the bare label so every existing cell name is unchanged
    (`ct-s20624` IS the window-0 gate); only a non-default dose adds `w<n>`.
    """
    if recipe not in RECIPES:
        raise FactorialError("unknown recipe %r" % (recipe,))
    if suppression_window is not None and suppression_window < 0:
        raise FactorialError(
            "suppression_window=%d bars nothing and PERSISTS; it has no cell"
            % suppression_window)
    tag = ("w%d" % suppression_window) if suppression_window else ""
    return "%s%s-s%d" % (RECIPE_CODE[recipe], tag, seed)


def dose_arm_entry(name: str, *, recipe: str, seed: int,
                   suppression_window: int, manifest=None) -> dict:
    """The fields that ride with a DOSE ARM. ⛔⛔ IT IS NOT A CELL.

    A dose arm is a measurement probe: `content-persistent` exists only to anchor
    the low end of the release-suppression slope (prereg `765b6787`). It must
    never enter the factorial population, so this returns **no `cell`, no
    `factorial_pair_key` and no `pairing_capability_side`** — the three fields
    every pooling and pairing routine reads. An arm that carried them could be
    pooled by a later analysis that simply forgot; without them it cannot be,
    whether or not anyone remembers.

    ⭐ Same discipline as the drift run's self-pair arm: control, not data, and
    structurally un-poolable rather than merely labelled as such.
    """
    if recipe in RECIPES:
        raise FactorialError(
            "%r is a factorial recipe, not a dose arm — build it with `entry()` "
            "so it gets a cell and a pair key" % (recipe,))
    return {
        "name": name,
        "recipe": recipe,
        "seed": seed,
        "suppression_window": suppression_window,
        "DOSE_ARM": True,
        "cell": None,
        "factorial_cell": None,
        "generator": generator_of(manifest or {}),
        "NOT_A_FACTORIAL_MEMBER": (
            "measurement probe for the dose-response slope; it has no cell and "
            "no pair key on purpose and must never enter the population"),
    }


def entry(name: str, *, recipe: str, seed: int, manifest=None,
          generator: str | None = None,
          suppression_window: int | None = None) -> dict:
    """The factorial fields that ride WITH an adapter into the ledger."""
    gen = generator or generator_of(manifest or {})
    if recipe not in RECIPES:
        raise FactorialError("unknown recipe %r" % (recipe,))
    if suppression_window is not None and suppression_window < 0:
        # ⛔⛔ A NEGATIVE WINDOW IS THE BAR-NOTHING DOSE, WHICH PERSISTS BY
        # CONSTRUCTION. It cannot be a content-transient cell no matter what
        # label was typed on the command line.
        raise FactorialError(
            "suppression_window=%d bars nothing, so this corpus PERSISTS and "
            "cannot be a %r cell. Use dose_arm_entry()."
            % (suppression_window, recipe))
    return {
        "name": name,
        "recipe": recipe,
        "seed": seed,
        "cell": adapter_label(recipe, seed, suppression_window),
        "generator": gen,
        # ⭐ THE DOSE RIDES WITH THE ADAPTER. Two content-transient adapters at
        # different suppression windows are different treatments; an adapter
        # that cannot say its dose is one that will be pooled with the other.
        "suppression_window": suppression_window,
        # ⛔ One side alone can never be `seed+force` -- pairing needs a partner.
        # This records what the side CAN support, and `pair_regimes` decides the
        # pair. Named `_side` so it is never read as the pair's regime.
        "pairing_capability_side": (PAIRED_SEED_AND_FORCE
                                    if gen == GENERATOR_SPLIT_STREAM
                                    else PAIRED_SEED_ONLY),
        # ⛔⛔ THE DOSE IS PART OF THE PAIR KEY TOO. A pair is a contrast that
        # differs in ONE variable. `ct-s20624` (window 0) and `ctw1-s20624`
        # (window 1) are both content-transient at seed 20624, so a key of
        # `seed20624` alone would make them each other's partner — pairing two
        # cells of the SAME arm that differ in the dose, which is not a
        # cross-recipe contrast at all. The matched pair for a dosed adapter is
        # the control at the SAME dose, and there is not one yet.
        "factorial_pair_key": ("seed%d" % seed if not suppression_window
                               else "seed%d/w%d" % (seed, suppression_window)),
    }


def pair_regimes(entries) -> dict:
    """{seed: regime} over seeds present in BOTH arms.

    ⛔⛔ A seed present in only one arm is NOT a pair and is excluded -- counting
    it would inflate the matched-cell count with contrasts that do not exist.
    """
    by = {}
    for e in entries:
        by.setdefault(e["seed"], {})[e["recipe"]] = e
    out = {}
    for seed, arms in by.items():
        if set(arms) != set(RECIPES):
            continue
        gens = [a["generator"] for a in arms.values()]
        out[seed] = (PAIRED_SEED_AND_FORCE
                     if all(g == GENERATOR_SPLIT_STREAM for g in gens)
                     else PAIRED_SEED_ONLY)
    return out


def unpaired(entries) -> dict:
    """{recipe: [seeds]} that have no partner in the other arm. ⭐ Reported, not
    hidden: an unpartnered adapter is real training that buys no contrast, and
    that is a fact the design should have to look at."""
    by = {}
    for e in entries:
        by.setdefault(e["seed"], set()).add(e["recipe"])
    out = {r: [] for r in RECIPES}
    for seed, arms in sorted(by.items()):
        if set(arms) != set(RECIPES):
            for r in arms:
                out[r].append(seed)
    return out


def check_balanced(entries, *, require_pairs: int = 1) -> dict:
    """⛔⛔ REFUSE AN UNANALYSABLE MATRIX.

    The failure mode of "train everything and measure it all" is 4 adapters in
    one arm, 6 in the other, uneven seeds, and no two cells differing by exactly
    one variable. This refuses that at the point it can still be fixed by
    training, rather than at analysis time when the GPU money is spent.
    """
    entries = list(entries)
    if not entries:
        raise FactorialError(
            "no adapters tracked — an empty factorial is indistinguishable "
            "from one whose entries were never recorded.")
    counts = Counter(e["recipe"] for e in entries)
    regimes = pair_regimes(entries)
    orphans = unpaired(entries)
    report = {
        "n_by_recipe": {r: counts.get(r, 0) for r in RECIPES},
        "pairs": len(regimes),
        "pairs_by_regime": dict(Counter(regimes.values())),
        "matched_seeds": sorted(s for s, v in regimes.items()
                                if v == PAIRED_SEED_AND_FORCE),
        "seed_only_seeds": sorted(s for s, v in regimes.items()
                                  if v == PAIRED_SEED_ONLY),
        "unpaired": orphans,
    }
    missing = [r for r in RECIPES if counts.get(r, 0) == 0]
    if missing:
        raise FactorialError(
            "ARM EMPTY: %s has no adapters. A one-armed factorial has no "
            "contrast in it — the control exists to be measured against."
            % ", ".join(missing))
    if len(regimes) < require_pairs:
        raise FactorialError(
            "NO MATCHED SEEDS: %d seed-pair(s) span both arms, %d required. "
            "Adapters exist in both arms but at different seeds, so every "
            "contrast changes recipe AND identity at once."
            % (len(regimes), require_pairs))
    return report
