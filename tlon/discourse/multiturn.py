"""THE MARKOV DEPTH-1 GENERATOR — a blindfolded painter, force-connected.

Each turn: read ONLY the prior turn's force, sample a response force from the
force-map, paint a FRESH well-formed scene carrying that force, emit, release.
No accumulation, no content relation, no direction, no category.

⛔⛔ EXTENT IS A TRIPWIRE HERE, NOT A GATE. Measured this session: a painter that
ignores the prior turn entirely scores **0/200 guard-fires** at depths 8/20/40
(mean TTR 0.937 / 0.856 / 0.738 against a floor of 0.50). `degeneracy_guard`
cannot fail on noise, and this generator is approximately i.i.d. by construction,
so extent has **zero discriminating power** — it is the dual of the
pass-maxed-by-a-constant failure. If the tripwire fires during generation that is
a SAMPLER BUG, not a caught exemplar.

⇒ **THE GATE IS FORCE-FIDELITY** (`tools/act2_force_fidelity.py`), which a random
painter fails.
"""
from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass

from ..grammar.parse import parse, render
from . import force_map as FM


class MultiturnError(RuntimeError):
    pass


#: ⛔ REQUIRED, NO DEFAULT — a mix fraction with a default is a held variable
#: nobody wrote down, which is how the boost bug happened. Ledgered at 0.5.
MULTITURN_FRACTION_LEDGERED = 0.5

#: Per-cell coverage floor as a FRACTION of the corpus's transitions, never a
#: count (a count couples to corpus size — the boost bug one level down).
FORCE_PAIR_FLOOR_FRACTION = 0.25 / (len(FM.ORDER) ** 2)


@dataclass(frozen=True)
class Turn:
    surface: str
    force: str
    prior_force: str | None


def _pool_by_force(pairs) -> dict[str, list[str]]:
    """Surfaces indexed by their force. ⭐ Content-free means the painting is
    drawn from the WHOLE compatible space, never from near the prior."""
    pool: dict[str, list[str]] = {f: [] for f in FM.ORDER}
    for p in pairs:
        s = getattr(p, "surface", None)
        if not s:
            continue
        try:
            scene = parse(s)
        except Exception:                                      # noqa: BLE001
            continue
        if render(scene) != s:                 # the one-place oracle, enforced
            continue
        if scene.force in pool:
            pool[scene.force].append(s)
    missing = [f for f, v in pool.items() if not v]
    if missing:
        raise MultiturnError(
            f"no well-formed surface in the pool carries force(s) {missing} — "
            "the generator cannot paint a force it has no exemplar of")
    return pool


def chain(pool: dict[str, list[str]], *, turns: int, rng: random.Random,
          seed_force: str | None = None) -> list[Turn]:
    """One Markov depth-1 exchange. ⭐ `prior_force` is the ONLY thing carried."""
    if turns < 2:
        raise MultiturnError("a chain shorter than 2 turns has no transition")
    f = seed_force or rng.choice(FM.ORDER)
    out = [Turn(rng.choice(pool[f]), f, None)]
    for _ in range(turns - 1):
        dist = FM.row(f)
        nxt = rng.choices(FM.ORDER, weights=[dist[x] for x in FM.ORDER])[0]
        out.append(Turn(rng.choice(pool[nxt]), nxt, f))
        f = nxt
    return out


def transition_counts(chains) -> Counter:
    c: Counter = Counter()
    for ch in chains:
        for t in ch:
            if t.prior_force is not None:
                c[(t.prior_force, t.force)] += 1
    return c


def check_force_pair_fairness(chains, *,
                              floor: float = FORCE_PAIR_FLOOR_FRACTION) -> dict:
    """⛔⛔ REFUSES BEFORE WRITING, AND STRATIFIES BY ROW.

    RULING 11's lesson, carried up: **flat marginals hide starved joint cells.**
    But a *global* floor over the joint is wrong here too, because the map itself
    makes cells legitimately unequal — a `forced` row puts zero in four of its
    five cells ON PURPOSE, and a floor that fired on those would be demanding the
    corpus contradict its own map.

    ⇒ Each cell is floored **against its own row's expected share**, and cells the
    map assigns probability zero are exempt because they are a DESIGN ZERO, not a
    starved cell. ⭐ A legitimate no-op must not be red.
    """
    counts = transition_counts(chains)
    total = sum(counts.values())
    if not total:
        raise MultiturnError("no transitions to check")
    worst = (None, 1.0)
    for prior in FM.ORDER:
        r = FM.row(prior)
        n_prior = sum(counts[(prior, x)] for x in FM.ORDER)
        if not n_prior:
            raise MultiturnError(
                f"force {prior!r} never appears as a prior — its whole row is "
                "untrained and the arena cannot measure what was never shown")
        for resp in FM.ORDER:
            if r[resp] == 0.0:
                continue                       # design zero, not a starved cell
            got = counts[(prior, resp)] / n_prior
            ratio = got / r[resp]
            if ratio < worst[1]:
                worst = ((prior, resp), ratio)
    report = {"total_transitions": total, "worst_cell": worst[0],
              "worst_ratio": worst[1], "floor": floor,
              "counts": {f"{a}->{b}": n for (a, b), n in sorted(counts.items())}}
    if worst[1] < floor:
        raise MultiturnError(
            f"FORCE-PAIR STARVATION in cell {worst[0]}: observed {worst[1]:.3f} "
            f"of its row-expected share, below the floor {floor:.3f}. The arena "
            "cannot measure a transition the corpus barely showed.")
    return report


def build(n_chains: int, *, turns: int, pairs, seed: int) -> list[list[Turn]]:
    """Generate, then REFUSE if the coverage is starved — before anything writes."""
    rng = random.Random(seed)
    pool = _pool_by_force(pairs)
    chains = [chain(pool, turns=turns, rng=rng) for _ in range(n_chains)]
    check_force_pair_fairness(chains)
    return chains


#: ⛔⛔ THE DIRECTIONS A MIXED CORPUS MUST CONTAIN. Not a style preference — a
#: corpus missing `read` measures a writer as a reader (render 81.2 %, speak
#: 9.4 %, measured), and one missing `provoke` trains under a contract the arena
#: does not serve.
EXPECTED_DIRECTIONS: frozenset = frozenset({"write", "read", "provoke"})

#: A direction present but starved is a direction absent with extra steps.
MIN_DIRECTION_SHARE = 0.05


def check_direction_coverage(rows, *, expected=EXPECTED_DIRECTIONS,
                             minimum: float = MIN_DIRECTION_SHARE) -> dict:
    """⛔⛔ REFUSE BEFORE WRITING IF A DIRECTION IS MISSING OR STARVED.

    **THE STANDING RULE, MADE MECHANICAL.** Three times this session the same
    failure: *a builder produces something a downstream tool post-processes, and
    reimplementing the builder drops the post-processing invisibly.* The read
    rows exist only because `act2_build_corpus.py` DUPLICATES every row with
    `direction="read"`; the provoke prompt exists only because trainer and arena
    import one string; the token count is only honest because the counter imports
    the trainer's fold. Each time, re-deriving the builder silently dropped the
    transformation.

    ⭐ AND THE COST IS NOT A CRASH, IT IS A FALSE FINDING THAT LOOKS REAL. A
    corpus with no `read` rows produces speak ≈ 9 %, which reads as *"multi-turn
    training destroyed speak"* — plausible, clean, and completely wrong. This
    catches it at WRITE time instead of at speak-9.4 %.
    """
    counts = Counter(r.get("direction") for r in rows)
    total = sum(counts.values())
    if not total:
        raise MultiturnError("no rows to check")
    missing = sorted(expected - set(counts))
    if missing:
        raise MultiturnError(
            f"DIRECTION MISSING: {missing}. Expected {sorted(expected)}, got "
            f"{sorted(counts)}. A corpus without `read` measures a writer as a "
            "reader (render 81.2 %, speak 9.4 % — measured); one without "
            "`provoke` trains under a contract the arena does not serve.")
    starved = {d: counts[d] / total for d in expected
               if counts[d] / total < minimum}
    if starved:
        raise MultiturnError(
            f"DIRECTION STARVED: {starved} below the {minimum:.0%} floor. "
            "A direction present but starved is a direction absent with extra "
            "steps.")
    return {"counts": dict(counts), "total": total,
            "shares": {d: counts[d] / total for d in sorted(counts)}}
