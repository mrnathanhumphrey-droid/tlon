"""THE OBSERVABLE — `D` (departure) and `C` (convergence). PREREG §1.

⛔⛔ DRIFT IS NOT "THE TRANSCRIPTS LOOK DIFFERENT". Surface novelty is free under
this grammar, so a surface-level observable measures the freedom of the channel,
not a change of mind. `D` and `C` are computed in IMPRESSION SPACE against a
fixed held-out battery, and nothing here ever touches a transcript.

⛔⛔ EVERY NUMBER GOES THROUGH `harness/paired.py`. A bare float carries no record
of what it was measured over, and this project has manufactured effects five
times by subtracting two floats from different item sets. `Measurement.__sub__`
refuses; the only way to a difference is `paired_delta(..., contrast="arm")`,
which checks that the item sets are identical and that ARM is the only facet
that differs.

⭐ WHY BOTH OBSERVABLES, AND WHY `C` IS NOT OPTIONAL (PREREG §0.1). Two speakers
each adapting toward a DIFFERENT frozen partner depart from epoch 0 just as far
as two speakers adapting toward each other. `D` cannot tell those apart. `C` can:
only the second pair ends up in the same place. Drift is wandering; a pact is
wandering TOGETHER, and the claim is about a pact.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..harness.paired import Measurement, measure, paired_delta
from .arena import RunResult

HALVES = ("production", "comprehension")


class ObservableError(RuntimeError):
    pass


def _mapping(rec, model: str) -> dict[str, object]:
    """One model's whole meaning↔form mapping at one epoch, both halves, keyed
    so that a production probe and a comprehension probe can never collide."""
    out: dict[str, object] = {}
    for pid, form in rec.production.get(model, {}).items():
        out[f"prod:{pid}"] = form
    for pid, choice in rec.comprehension.get(model, {}).items():
        out[f"comp:{pid}"] = choice
    return out


def _items(run: RunResult, exclude: frozenset[str]) -> list[str]:
    base = _mapping(run.epochs[0], run.models[0])
    return sorted(k for k in base if k.split(":", 1)[1] not in exclude)


def _facets(run: RunResult, epoch: int) -> dict:
    return {"arm": run.arm, "seed": run.seed, "epoch": epoch,
            "axis": f"{run.axis.key}:{run.axis.setting}",
            "battery": run.battery, "replicate": run.replicate}


def departure(run: RunResult, epoch: int, *,
              exclude: frozenset[str] = frozenset()) -> Measurement:
    """`D` — the fraction of (model, probe) mappings that differ from epoch 0.

    ⛔ Items are (model, probe) pairs so that BOTH models enter one number and
    the arms stay pairable. Excluding a leaked probe from one arm only would
    change the item digest and `paired_delta` would refuse the comparison --
    which is the guard working, not an obstacle.
    """
    if epoch >= len(run.epochs):
        raise ObservableError(f"epoch {epoch} not in run {run.run_id}")
    base = {m: _mapping(run.epochs[0], m) for m in run.models}
    now = {m: _mapping(run.epochs[epoch], m) for m in run.models}
    keys = _items(run, exclude)
    items = [f"{m}|{k}" for m in run.models for k in keys]

    def score(seq):
        return sum(base[i.split("|", 1)[0]][i.split("|", 1)[1]]
                   != now[i.split("|", 1)[0]][i.split("|", 1)[1]]
                   for i in seq) / len(seq)

    return measure(f"D[{run.arm} s{run.seed} e{epoch}]", "probe_x_model",
                   items, score, key=str, **_facets(run, epoch))


def convergence(run: RunResult, epoch: int, *,
                exclude: frozenset[str] = frozenset()) -> Measurement:
    """`C` — the fraction of probes on which the two models agree WITH EACH OTHER.

    ⛔ A refusal is an outcome, not a missing value: two models that both refuse
    a probe agree about it. Dropping refusals would let a pair look more
    convergent by answering less.
    """
    if epoch >= len(run.epochs):
        raise ObservableError(f"epoch {epoch} not in run {run.run_id}")
    a, b = run.models
    ma = _mapping(run.epochs[epoch], a)
    mb = _mapping(run.epochs[epoch], b)
    keys = _items(run, exclude)

    def score(seq):
        return sum(ma[k] == mb[k] for k in seq) / len(seq)

    return measure(f"C[{run.arm} s{run.seed} e{epoch}]", "probe",
                   keys, score, key=str, **_facets(run, epoch))


def delta(interacting: Measurement, control: Measurement):
    """⭐ THE ONLY WAY TO A DIFFERENCE. `contrast="arm"` is not decoration: it
    names the one facet allowed to differ, and every other facet -- seed, epoch,
    axis, battery -- must match or this refuses."""
    return paired_delta(interacting, control, contrast="arm")


# ── the secondary estimator, DECLARED EXPLORATORY ─────────────────────────
@dataclass(frozen=True)
class Exploratory:
    """⛔⛔ CANNOT ENTER A VERDICT (PREREG §1). Wrapped in a type with no
    comparison operators so it cannot be quietly differenced into one; it is
    registered so that computing it later is not a post-hoc choice."""
    value: float
    note: str = ("graded π-slot disagreement — SECONDARY and EXPLORATORY. "
                 "Pre-registered so it is not a post-hoc estimator, and barred "
                 "from every decision rule.")


_SLOTS = ("root", "orient", "aspect", "edges")


def slot_distance(form_a: str | None, form_b: str | None) -> float:
    """Normalised disagreement over π-kept slots. Structural mismatch is maximal."""
    if form_a is None or form_b is None:
        return 1.0 if form_a != form_b else 0.0
    a, b = json.loads(form_a)["node"], json.loads(form_b)["node"]
    if len(a.get("edges") or []) != len(b.get("edges") or []):
        return 1.0
    return sum(a.get(s) != b.get(s) for s in _SLOTS) / len(_SLOTS)


def graded_departure(run: RunResult, epoch: int) -> Exploratory:
    base, now = run.epochs[0], run.epochs[epoch]
    vals = [slot_distance(base.production[m][pid], now.production[m][pid])
            for m in run.models for pid in base.production[m]]
    return Exploratory(value=sum(vals) / len(vals) if vals else 0.0)
