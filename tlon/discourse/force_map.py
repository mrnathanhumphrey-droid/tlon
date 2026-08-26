"""THE FORCE→FORCE RESPONSE MAP — THE ONLY STRUCTURE THE CORPUS CARRIES.

⭐⭐ THE PROPERTY THAT MAKES THIS ARCHITECTURE SURVIVE WHERE SIX DIED:
**UNDETERMINED DEGRADES TO UNIFORM, NOT TO EMPTY.** Every previous derivation
(ρ_wide, the contact axis, orthogonal registers, the tree-sibling read,
grounding, undirected category-coherence) died because a cell we could not force
was a cell we could not generate. Here a cell we cannot force becomes a **flat
row**, which generates fine, is an honest *we don't know*, and lets the arena
measure whether two models SHARPEN it — convention emerging against a genuinely
flat prior, which is exactly what RULING 12 wanted and could not previously have.

⛔ A GUESSED ROW WOULD BE THE `base_convention` TRAP AT A NEW LEVEL. So only cells
that survive the mutation test are non-uniform. Everything else is flat, and
which is which is LOGGED, not remembered.

⛔ RULING 10 IS SUBSUMED HERE. ABIDE/CLOSE/BREAK dissolve into this map: CLOSE was
`ku`, BREAK was `kä`, and those are two of the five forces. There is no separate
move taxonomy beside the map — it is ONE object. The three-move framing is
retired.
"""
from __future__ import annotations

from ..grammar import classes as _classes

FORCES: dict[str, str] = _classes.load()["classes"]["F"]
ORDER: tuple[str, ...] = tuple(sorted(FORCES))

FORCED = "forced"
UNIFORM = "uniform"


class ForceMapError(RuntimeError):
    pass


#: ⭐ THE ONE SURVIVING CELL. `ki` (ASK) ↦ `ka` (ASSERT) — question/answer is the
#: canonical adjacency pair in conversation analysis, and illocution genuinely
#: constrains the second position: a question makes an answer *conditionally
#: relevant*, and its absence is HEARABLE as absent. That is a real second-pair
#: constraint, not a preference.
#:
#: ⛔ THE CELL THAT LOOKED FORCED AND IS NOT: `ku` (URGE) ↦ {`ka`, `kä`}.
#: Adjacency-pair theory does cover offer/accept-or-decline, so a two-option row
#: looked derivable. It inverts cleanly: a *dispreferred* response to a request is
#: canonically a DELAY or a hedge, which is `ko` (WONDER) — "you urge; I wonder."
#: Conversation analysis names that move, so `ku`↦`ko` is as defensible as
#: `ku`↦{`ka`,`kä`}. **PICKED. Left uniform.**
#:
#: Greeting/greeting does not map: Tlön has no greeting force.
FORCED_CELLS: dict[str, str] = {"ki": "ka"}

#: ⚠️ A DELIBERATE, PARAMETER-FREE CHOICE, NAMED SO IT CAN BE ARGUED WITH. A
#: forced row is **deterministic**, not merely dominant. Real adjacency pairs are
#: strong tendencies, so a "strength" parameter would be more faithful — and it
#: would be a KNOB, picked by taste, coupled to nothing, exactly the family of
#: object this project keeps getting burned by. Deterministic has no knob.
#: The alternative is recorded here rather than in prose that decays.
FORCED_ROWS_ARE_DETERMINISTIC = True


def row(prior: str) -> dict[str, float]:
    """The response-force distribution given `prior`. Sums to 1."""
    if prior not in FORCES:
        raise ForceMapError(
            f"{prior!r} is not in lexicon class F. The five forces are: "
            + ", ".join(f"{f} ({g})" for f, g in FORCES.items()))
    if prior in FORCED_CELLS:
        target = FORCED_CELLS[prior]
        return {f: (1.0 if f == target else 0.0) for f in ORDER}
    return {f: 1.0 / len(ORDER) for f in ORDER}


def verdict(prior: str) -> str:
    """`forced` or `uniform` — which is which, callable rather than remembered."""
    if prior not in FORCES:
        raise ForceMapError(f"{prior!r} is not in lexicon class F")
    return FORCED if prior in FORCED_CELLS else UNIFORM


def matrix() -> list[list[float]]:
    return [[row(p)[r] for r in ORDER] for p in ORDER]


def stationary(tol: float = 1e-12, max_iter: int = 10_000) -> dict[str, float]:
    """The long-run force distribution of the Markov chain the map induces.

    ⭐ NEEDED FOR THE GATE, NOT FOR DECORATION. Force-fidelity is measured against
    INDEPENDENCE, and the independence null is built from these marginals. A
    chance baseline assumed to be uniform would be wrong: the `ki`→`ka` row makes
    `ka` twice as common as anything else in the stationary state.
    """
    p = {f: 1.0 / len(ORDER) for f in ORDER}
    for _ in range(max_iter):
        nxt = {f: 0.0 for f in ORDER}
        for i in ORDER:
            ri = row(i)
            for j in ORDER:
                nxt[j] += p[i] * ri[j]
        if max(abs(nxt[f] - p[f]) for f in ORDER) < tol:
            return nxt
        p = nxt
    raise ForceMapError("stationary distribution did not converge")


def describe() -> str:
    lines = [f"FORCE→FORCE RESPONSE MAP · {len(FORCED_CELLS)} forced, "
             f"{len(ORDER) - len(FORCED_CELLS)} uniform",
             "  prior │ " + " ".join(f"{r:>6}" for r in ORDER) + "   verdict"]
    for p in ORDER:
        r = row(p)
        lines.append(f"  {p:>5} │ " + " ".join(f"{r[c]:6.2f}" for c in ORDER)
                     + f"   {verdict(p)}")
    st = stationary()
    lines.append("  stationary: "
                 + ", ".join(f"{f} {st[f]:.3f}" for f in ORDER))
    return "\n".join(lines)


def separation() -> float:
    """d(MAP, INDEPENDENCE) — the MAXIMUM row-mass-weighted total variation a
    perfectly faithful model can achieve against the independence null.

    ⛔⛔ THIS EXISTS BECAUSE A PICKED THRESHOLD FAILED A PERFECT CORPUS. The
    first version of the fidelity gate used hand-chosen bands (near 0.15 / far
    0.30) and read ⚠️UNRESOLVED on a corpus generated FROM THE MAP ITSELF, whose
    forced row scored a literal 0.000. The cause: **the map is mostly uniform, so
    it sits CLOSE to independence by construction**, and the achievable ceiling
    is ~0.22 — a `far` threshold of 0.30 was unreachable, a gate that could never
    pass. The mirror image of the noise-maxes-extent failure, built into the very
    tool written to fix it.

    ⇒ THRESHOLDS ARE FRACTIONS OF THIS NUMBER, NEVER ABSOLUTES.

    ⭐ AND IT PRICES THE HONESTY. Uniform-where-undetermined is the right call —
    a guessed row is the `base_convention` trap — but it is not free: every cell
    left flat shrinks the separation, and therefore the gate's power. With one
    forced cell of twenty-five the whole test lives in a band of width ~0.22 out
    of a possible 1.0. That is the measurable price of refusing to guess.
    """
    st = stationary()
    marg = {j: sum(st[i] * row(i)[j] for i in ORDER) for j in ORDER}
    total = 0.0
    for i in ORDER:
        ri = row(i)
        tv = 0.5 * sum(abs(ri[j] - marg[j]) for j in ORDER)
        total += st[i] * tv
    return total
