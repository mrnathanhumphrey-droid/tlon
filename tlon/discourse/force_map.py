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

from dataclasses import dataclass, field
from typing import Mapping

from ..grammar import classes as _classes

FORCES: dict[str, str] = _classes.load()["classes"]["F"]
ORDER: tuple[str, ...] = tuple(sorted(FORCES))

FORCED = "forced"
UNIFORM = "uniform"


class ForceMapError(RuntimeError):
    pass


class StipulationLeak(ForceMapError):
    """⛔⛔ A STIPULATED MAP REACHED SOMETHING THAT IS NOT THE MECHANISM PROBE.

    A stipulated cell is a probe instrument, not a claim about Tlön. The failure
    mode this guards is not a crash — it is a stipulated cell quietly becoming
    "the map" three sessions from now because it was in a corpus once and nobody
    re-read the label. **The caveat lives in the object, not in prose beside it.**
    """


@dataclass(frozen=True)
class ForceMap:
    """A force→force response map. ⭐ AN OBJECT, SO TWO CAN EXIST AT ONCE.

    Was module-level state, which is exactly what a two-map experiment cannot
    have: the baseline and the treatment must be constructible side by side and
    must be unable to be confused for one another.
    """

    forced_cells: Mapping[str, str]
    label: str
    #: ⛔⛔ SOURCES WHOSE FORCED CELL IS **STIPULATED, NOT DERIVED**. Non-empty
    #: makes this map a probe instrument. [caveat_in_name]: the caveat is a
    #: FIELD, checked by code, never a comment someone stops reading.
    stipulated: frozenset = field(default_factory=frozenset)

    def __post_init__(self):
        for src, tgt in self.forced_cells.items():
            if src not in FORCES:
                raise ForceMapError(f"forced source {src!r} is not in class F")
            if tgt not in FORCES:
                raise ForceMapError(f"forced target {tgt!r} is not in class F")
            if src == tgt:
                raise ForceMapError(
                    f"{src!r}→{src!r} is a deterministic self-loop: the chain "
                    "absorbs and every later turn carries one force")
        unknown = set(self.stipulated) - set(self.forced_cells)
        if unknown:
            raise ForceMapError(
                f"stipulated sources {sorted(unknown)} have no forced cell — a "
                "label with nothing under it")
        cyc = self._forced_cycle()
        if cyc:
            raise ForceMapError(
                f"FORCED CYCLE {' → '.join(cyc)} — every cell on it is "
                "deterministic, so the chain ABSORBS: once a turn lands on the "
                "cycle every later force is fixed and the uniform rows are never "
                "reached again. Beyond breaking the chain, a 2-cycle would "
                "confound any asymmetry effect with cycle-formation.")

    def _forced_cycle(self) -> list[str] | None:
        """A cycle using only deterministic cells, or None.

        ⛔ NOT DECORATION. `ki`→`ka` plus `ka`→`ki` is the specific confound the
        mechanism probe has to avoid, and 'we chose not to' is a decision that
        lives in prose. This makes it unconstructible.
        """
        for start in self.forced_cells:
            seen, cur = [], start
            while cur in self.forced_cells:
                if cur in seen:
                    return seen[seen.index(cur):] + [cur]
                seen.append(cur)
                cur = self.forced_cells[cur]
        return None

    @property
    def is_stipulated(self) -> bool:
        return bool(self.stipulated)

    def assert_derived(self, use: str) -> None:
        """⛔⛔ CALL THIS AT EVERY SITE THAT IS NOT THE MECHANISM PROBE."""
        if self.is_stipulated:
            raise StipulationLeak(
                f"map {self.label!r} carries STIPULATED cell(s) "
                f"{sorted(self.stipulated)} and cannot be used for {use}. A "
                "stipulated cell is a mechanism-probe instrument: it is not "
                "claimed forced, it is not a map proposal, and it is discarded "
                "after the probe REGARDLESS OF OUTCOME.")

    def row(self, prior: str) -> dict[str, float]:
        if prior not in FORCES:
            raise ForceMapError(
                f"{prior!r} is not in lexicon class F. The five forces are: "
                + ", ".join(f"{f} ({g})" for f, g in FORCES.items()))
        if prior in self.forced_cells:
            t = self.forced_cells[prior]
            return {f: (1.0 if f == t else 0.0) for f in ORDER}
        return {f: 1.0 / len(ORDER) for f in ORDER}

    def verdict(self, prior: str) -> str:
        if prior not in FORCES:
            raise ForceMapError(f"{prior!r} is not in lexicon class F")
        return FORCED if prior in self.forced_cells else UNIFORM

    def uniform_rows(self) -> tuple[str, ...]:
        return tuple(f for f in ORDER if self.verdict(f) == UNIFORM)

    def matrix(self) -> list[list[float]]:
        return [[self.row(p)[r] for r in ORDER] for p in ORDER]

    def stationary(self, tol: float = 1e-12,
                   max_iter: int = 10_000) -> dict[str, float]:
        p = {f: 1.0 / len(ORDER) for f in ORDER}
        for _ in range(max_iter):
            nxt = {f: 0.0 for f in ORDER}
            for i in ORDER:
                ri = self.row(i)
                for j in ORDER:
                    nxt[j] += p[i] * ri[j]
            if max(abs(nxt[f] - p[f]) for f in ORDER) < tol:
                return nxt
            p = nxt
        raise ForceMapError("stationary distribution did not converge")

    def separation(self) -> float:
        st = self.stationary()
        marg = {j: sum(st[i] * self.row(i)[j] for i in ORDER) for j in ORDER}
        return sum(st[i] * 0.5 * sum(abs(self.row(i)[j] - marg[j])
                                     for j in ORDER) for i in ORDER)

    def describe(self) -> str:
        tag = ("  ⛔⛔ STIPULATED (mechanism probe only): "
               + ", ".join(f"{s}→{self.forced_cells[s]}"
                           for s in sorted(self.stipulated)) + "\n"
               if self.is_stipulated else "")
        lines = [f"FORCE→FORCE RESPONSE MAP [{self.label}] · "
                 f"{len(self.forced_cells)} forced, "
                 f"{len(ORDER) - len(self.forced_cells)} uniform",
                 "  prior │ " + " ".join(f"{r:>6}" for r in ORDER)
                 + "   verdict"]
        for p in ORDER:
            r = self.row(p)
            mark = " ⚠️STIP" if p in self.stipulated else ""
            lines.append(f"  {p:>5} │ "
                         + " ".join(f"{r[c]:6.2f}" for c in ORDER)
                         + f"   {self.verdict(p)}{mark}")
        st = self.stationary()
        lines.append("  stationary: "
                     + ", ".join(f"{f} {st[f]:.3f}" for f in ORDER))
        lines.append(f"  separation: {self.separation():.4f}")
        return tag + "\n".join(lines)


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


# ── THE TWO MAPS OF THE MECHANISM PROBE ───────────────────────────────────────
#: ⭐ THE REAL MAP. One derived cell. This is what `row()`/`verdict()`/etc. below
#: delegate to, so every existing caller keeps the derived map by DEFAULT and a
#: stipulated map can only ever be reached by asking for it BY NAME.
DERIVED_v1 = ForceMap({"ki": "ka"}, label="DERIVED_v1")

#: ⛔⛔ THE STIPULATED SOURCE, AND WHY IT IS THIS ONE.
#:
#: The probe asks whether `ki`-suppression is caused by `ki` being SOURCE-ONLY —
#: the only force whose prompt-position identity fully determines its target,
#: never itself a forced response ("I am the thing answered, never the answer").
#: Testing that needs exactly one cell of the form X→`ki`.
#:
#:   ⛔ NOT `ka`  — `ki`→`ka` already exists, so `ka`→`ki` closes a 2-CYCLE and
#:                 confounds asymmetry-relief with cycle-formation. Ruled out by
#:                 the spec and by construction.
#:   ⛔ NOT `ki`  — `ki`'s row is already forced to `ka`; a source cannot have two
#:                 forced targets, and `ki`→`ki` is an absorbing self-loop.
#:   ✅ `ko`      — CHOSEN. Its `ki`-emission was at the observed FLOOR (0.054,
#:                 tied with `ku` at 0.052 and below `kä` at 0.090), so it has
#:                 the most headroom for relief to be visible. Of the two floor
#:                 candidates `ko` has the SMALLER prior count (92 vs 116), which
#:                 is the conservative pick: it removes less data from the
#:                 common-uniform stratum the primary measure lives on.
#:   ⏸ `ku`      — HELD AS THE PRE-NAMED REPLICATION. Named here, before the run,
#:                 so a later `ku` probe is a replication and not a second bite.
STIPULATED_SOURCE = "ko"
REPLICATION_SOURCE_HELD = "ku"

#: ⛔⛔ NOT DERIVED. NOT A MAP PROPOSAL. DISCARDED AFTER THE PROBE REGARDLESS OF
#: OUTCOME. `assert_derived()` raises on it at every non-probe site.
STIPULATED_KI_TARGET_v1 = ForceMap(
    {"ki": "ka", STIPULATED_SOURCE: "ki"},
    label="STIPULATED_KI_TARGET_v1",
    stipulated=frozenset({STIPULATED_SOURCE}))

#: ⭐⭐ THE ROWS THE PRIMARY MEASURE LIVES ON — uniform in BOTH maps.
#:
#: ⛔⛔ THIS EXISTS BECAUSE THE OBVIOUS MEASURE MANUFACTURES FAKE RELIEF. Making
#: `ko`→`ki` forced means `ko`'s row emits `ki` 100 % of the time BY
#: CONSTRUCTION. The GLOBAL `ki` marginal therefore RISES in the treatment arm
#: whether or not any suppression was relieved — the stipulation would be
#: measuring itself, and it would look exactly like a clean confirmation.
#:
#: ⇒ The primary measure is `P(ki | prior ∈ COMMON_UNIFORM_ROWS)`, and it is
#:   clean for a second reason worth stating: those rows are uniform in BOTH
#:   maps, so their corpus expectation is **0.20 in both arms**. Same rows, same
#:   expectation, only the map differs.
COMMON_UNIFORM_ROWS: tuple[str, ...] = tuple(
    f for f in DERIVED_v1.uniform_rows()
    if f in STIPULATED_KI_TARGET_v1.uniform_rows())

#: The corpus expectation on those rows, in both arms. Derived, never typed.
COMMON_UNIFORM_EXPECTATION = 1.0 / len(ORDER)


def row(prior: str) -> dict[str, float]:
    """The response-force distribution given `prior`, on the DERIVED map."""
    return DERIVED_v1.row(prior)


def verdict(prior: str) -> str:
    """`forced` or `uniform` — which is which, callable rather than remembered."""
    return DERIVED_v1.verdict(prior)


def matrix() -> list[list[float]]:
    return DERIVED_v1.matrix()


def stationary(tol: float = 1e-12, max_iter: int = 10_000) -> dict[str, float]:
    """The long-run force distribution of the Markov chain the map induces.

    ⭐ NEEDED FOR THE GATE, NOT FOR DECORATION. Force-fidelity is measured against
    INDEPENDENCE, and the independence null is built from these marginals. A
    chance baseline assumed to be uniform would be wrong: the `ki`→`ka` row makes
    `ka` twice as common as anything else in the stationary state.
    """
    return DERIVED_v1.stationary(tol=tol, max_iter=max_iter)


def describe() -> str:
    return DERIVED_v1.describe()


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
    return DERIVED_v1.separation()
