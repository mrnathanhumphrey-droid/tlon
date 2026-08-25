"""Scoring exactly as PREREG 080bc40f specifies.

Overall accuracy is context only. The headline numbers are WITHIN-PAIR accuracy
on each set and the per-channel breakdown -- because the original 20 pegs are
root-solvable and would inflate any average they entered.
"""
from __future__ import annotations
import collections
import random

from .data import Example


def bootstrap_ci(hits: list[int], n_boot: int = 2000, seed: int = 7,
                 alpha: float = 0.05) -> tuple[float, float, float]:
    """Returns (mean, lo, hi). Empty input yields nan."""
    if not hits:
        return (float("nan"),) * 3
    rng = random.Random(seed)
    n = len(hits)
    mean = sum(hits) / n
    if n == 1:
        return mean, mean, mean
    boots = []
    for _ in range(n_boot):
        boots.append(sum(hits[rng.randrange(n)] for _ in range(n)) / n)
    boots.sort()
    return mean, boots[int(alpha / 2 * n_boot)], boots[int((1 - alpha / 2) * n_boot)]


def within_pair(rows: list[Example], preds: list[int], refs, pair_ids: set[str]
                ) -> dict:
    """Binary accuracy between the two members of each pair.

    The model emits a 60-way prediction; we score only whether it put more mass
    on the correct member than on its partner, so class priors over the other 58
    cannot carry the number.
    """
    by_label = {i: r for i, r in enumerate(refs)}
    partner = {}
    groups = collections.defaultdict(list)
    for i, r in enumerate(refs):
        if r.minimal_pair:
            groups[r.minimal_pair].append(i)
    for pid, idxs in groups.items():
        if len(idxs) == 2:
            partner[idxs[0]] = idxs[1]
            partner[idxs[1]] = idxs[0]

    hits, per_pair, per_channel = [], collections.defaultdict(list), collections.defaultdict(list)
    for row, p in zip(rows, preds):
        ref = by_label[row.label]
        if not ref.minimal_pair or ref.minimal_pair not in pair_ids:
            continue
        other = partner.get(row.label)
        if other is None:
            continue
        hit = 1 if p == row.label else (0 if p == other else None)
        if hit is None:
            continue                       # predicted outside the pair entirely
        hits.append(hit)
        per_pair[ref.minimal_pair].append(hit)
        per_channel[ref.contrast].append(hit)

    mean, lo, hi = bootstrap_ci(hits)
    return {
        "n": len(hits), "acc": mean, "lo": lo, "hi": hi,
        "per_pair": {k: bootstrap_ci(v) for k, v in per_pair.items()},
        "per_channel": {k: bootstrap_ci(v) for k, v in per_channel.items()},
    }


def paired_diff(rows: list[Example], a: list[int], b: list[int]) -> tuple[float, float, float]:
    """Model minus baseline on the SAME items, with CI — not two independent
    numbers subtracted."""
    d = [(1 if pa == r.label else 0) - (1 if pb == r.label else 0)
         for r, pa, pb in zip(rows, a, b)]
    return bootstrap_ci(d)


def off_pair_rate(rows: list[Example], preds: list[int], refs) -> float:
    """How often the model picks something outside the pair. High values mean
    within-pair accuracy is computed on a thin, self-selected slice."""
    groups = collections.defaultdict(list)
    for i, r in enumerate(refs):
        if r.minimal_pair:
            groups[r.minimal_pair].append(i)
    partner = {}
    for idxs in groups.values():
        if len(idxs) == 2:
            partner[idxs[0]], partner[idxs[1]] = idxs[1], idxs[0]
    tot = off = 0
    for row, p in zip(rows, preds):
        if row.label not in partner:
            continue
        tot += 1
        if p != row.label and p != partner[row.label]:
            off += 1
    return off / max(1, tot)
