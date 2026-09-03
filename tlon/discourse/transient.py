"""THE CONTENT-TRANSIENT GENERATOR — perceive, respond, release.

⛔⛔ THE MISTAKE THIS MODULE EXISTS TO CORRECT. `multiturn.py` builds chains that
are *content-FREE*: `_pool_by_force` draws "from the WHOLE compatible space,
never from near the prior", so a response is statistically independent of what
provoked it. Measured on `runs/act2/corpus_mt/train.jsonl`, n=15,573 provoke
rows: **mean within-pair shared roots 0.0457 against a permutation null of
0.0424** — chance plus a hair (z=+2.22), which at that n is detectable and, in
magnitude, nothing.

⭐ AND THAT IS NOT WHAT THE ONTOLOGY SAYS. Tlön denies that content *persists* --
there are no objects, the coins were lost. It does not deny that content is
*apprehended*. An impression is HAD, in the moment, and then released. A mind
that never perceives its input at all is not Tlönian; it is deaf. The corpus
conflated **content-free** with **content-transient** and trained the first.

    content-free       the response ignores the provocation          (control)
    content-transient  the response is provoked BY the provocation,
                       and that content dies at the end of the turn  (the fix)
    content-carrying   the content propagates forward                (un-Tlön:
                                                                      persistence)

⛔⛔ THE LEAK, AND IT IS THE WHOLE DESIGN PROBLEM. Make each response responsive
to its provocation naively and content becomes persistent ANYWAY, by transitivity:
A and B share a root, B and C share a root, and the root walks the whole chain.
"Ingest and release" silently becomes "hold, through my own history" -- which is
object permanence rebuilt out of parts that each looked innocent.

⭐⭐ THE RULE THAT BREAKS IT: **A RESPONSE MAY ECHO WHAT ITS PROVOCATION
CONTRIBUTED ITSELF, NEVER WHAT ITS PROVOCATION INHERITED.** Each turn carries an
`inherited` set -- the roots it took from the turn before it -- and those roots
are barred from being the echo the *next* turn picks up. The content a speaker
passes on is its own; the content it received dies with the turn that received it.
That is "you hold your past selves, not the things that provoked them", made
mechanical.

⭐ AND IT IS MEASURABLE, WHICH IS THE POINT. The claim becomes a lag profile:

    lag 1  (provocation -> response)   ELEVATED above the permutation null
    lag ≥2 (including the speaker's own previous turn) AT the null

In a two-speaker alternating exchange a speaker's own previous turn is **lag 2**,
so "the own-chain does not carry content" is not a separate check -- it is the
lag-2 cell, and `check_transience` refuses a corpus that fails it.

⛔ THE NULL IS THE ACCEPTANCE CRITERION, NOT ZERO. Chance already yields ~0.042
shared roots per pair; a target of "> 0" is passed by doing nothing.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from ..grammar.parse import parse, render
from . import force_map as FM
from .multiturn import MultiturnError, Turn, _pool_by_force

#: ⛔⛔ THE FACTORIAL'S CORPUS AXIS, NAMED ONCE. Every consumer imports these
#: rather than spelling the strings, so a recipe label cannot drift between the
#: builder, the manifest, the adapter filename and the analysis -- which is the
#: only thing making the matrix reconstructable after the fact.
CONTENT_FREE = "content-free"
CONTENT_TRANSIENT = "content-transient"
RECIPES = (CONTENT_FREE, CONTENT_TRANSIENT)

#: ⛔⛔ THE GENERATOR'S IDENTITY, VERSIONED, WRITTEN INTO EVERY MANIFEST. The
#: legacy path (`multiturn.build`) draws force and content from ONE stream, so
#: its force sequence moves with its content draws. The split-stream path holds
#: the force sequence identical across recipes at a seed. Those are DIFFERENT
#: VARIANCE REGIMES for the factorial and an analysis has to know which it has.
GENERATOR_SPLIT_STREAM = "transient.build_transient/2-stream/v1"
GENERATOR_LEGACY = "multiturn.build/1-stream/legacy"

#: How well two adapters at the same seed are paired.
PAIRED_SEED_AND_FORCE = "seed+force"   # matched pair — the low-variance regime
PAIRED_SEED_ONLY = "seed"              # unpaired-but-unbiased — higher variance
PAIRING_REGIMES = (PAIRED_SEED_AND_FORCE, PAIRED_SEED_ONLY)

#: ⛔ How often a response is required to echo its provocation. REQUIRED at the
#: call site for corpus builds -- a responsiveness with a default is a held
#: variable nobody wrote down, which is the boost bug's shape.
RESPONSIVENESS_LEDGERED = 1.0

#: Acceptance thresholds for `check_transience`, in units of the permutation
#: null's own sd. ⭐ Stated against the NULL because chance is not zero.
Z_LAG1_MIN = 6.0     # the response must actually be responsive
Z_LAGN_MAX = 3.0     # every longer lag must be indistinguishable from chance


@dataclass(frozen=True)
class TTurn:
    """A turn that remembers WHAT IT INHERITED, so the next turn can refuse it.

    ⛔ `inherited` is generator bookkeeping and never reaches a training row --
    a row that carried it would be handing the model a memory the ontology
    forbids. It exists to be *subtracted*, not to be learned.
    """
    surface: str
    force: str
    prior_force: str | None
    inherited: frozenset = frozenset()
    echoed: str | None = None       # which root this turn picked up, if any


def roots_of(surface: str, lex_r) -> frozenset:
    return frozenset(t for t in surface.split() if t in lex_r)


def _lex_roots():
    from ..grammar import classes as C
    return C.load()["classes"]["R"]


def index_by_root(pool: dict[str, list[str]], lex_r) -> dict:
    """{force: {root: [surfaces]}} — so a responsive draw is O(1), not a scan.

    ⭐ Built once per corpus. A per-turn scan over a 6,000-surface pool would make
    the generator quadratic in corpus size and the build would silently get slower
    with n, which is the kind of thing nobody notices until a box is on a meter.
    """
    idx: dict[str, dict[str, list[str]]] = {f: {} for f in pool}
    for force, surfaces in pool.items():
        for s in surfaces:
            for r in roots_of(s, lex_r):
                idx[force].setdefault(r, []).append(s)
    return idx


def responsive_choice(idx_force, pool_force, provocation_roots, barred,
                      rng: random.Random, lex_r=None) -> tuple[str, str | None]:
    """Pick a surface that echoes ONE root the provocation contributed itself.

    ⛔⛔ `barred` IS THE TRANSITIVITY BREAK, AND IT BARS THE WHOLE SURFACE, NOT
    JUST THE ECHO SLOT. Removing the inherited root from the *echo-able set* is
    NOT sufficient and the first implementation here failed its own gate at
    **lag-2 z=29.65**. The reason: roots co-occur in clusters, so a surface
    chosen for containing `W` very often also contains `X` — and `X` walks the
    chain regardless of which root was nominally echoed. The candidate must
    contain NO barred root at all.

    ⭐ THAT DISTINCTION IS THE WHOLE MODULE. "Do not pass this on" is a property
    of the utterance, not of the intent behind choosing it.

    Returns `(surface, echoed_root)`. `echoed_root` is None when no echo was
    possible -- a real outcome, recorded, never retried until it looks like a
    success.
    """
    def clean(s: str) -> bool:
        # ⛔ The bar is on CONTAINMENT. Without `lex_r` there is no way to read
        # a surface's roots, so refuse rather than silently skip the check.
        if lex_r is None:
            raise MultiturnError(
                "responsive_choice needs `lex_r` to enforce the containment "
                "bar; without it the transitivity break is a no-op that "
                "reports success")
        return not (roots_of(s, lex_r) & barred)

    offerable = [r for r in (provocation_roots - barred) if r in idx_force]
    fallback = [s for s in pool_force if clean(s)] or pool_force
    if not offerable:
        return rng.choice(fallback), None
    rng.shuffle(offerable)
    for r in offerable:
        cands = [s for s in idx_force.get(r, ()) if clean(s)]
        if cands:
            return rng.choice(cands), r
    return rng.choice(fallback), None


def chain_transient(pool, idx, *, turns: int, rng: random.Random,
                    responsiveness: float, lex_r,
                    seed_force: str | None = None, fmap=None,
                    rng_content: random.Random | None = None) -> list[TTurn]:
    """One exchange: force-connected AND content-responsive, without persistence.

    ⛔⛔ TWO RANDOM STREAMS, AND THAT IS A FACTORIAL REQUIREMENT, NOT TIDINESS.
    `rng` draws FORCES; `rng_content` draws SURFACES. With one stream the
    responsive branch consumes a different amount of randomness than the flat
    branch, so the force sequence *diverges between recipes at the same seed* --
    and content-free-seed-X vs content-transient-seed-X would then differ in TWO
    variables, which is precisely the confound the matched-seed rule exists to
    prevent. Split, the force sequence is byte-identical across the arms and the
    contrast is one knob. This was caught by its own test.

    ⭐ Otherwise the force machinery is untouched: `prior_force` still drives the
    map exactly as in `multiturn.chain`.
    """
    from .multiturn import _resolve
    m = _resolve(fmap)
    if turns < 2:
        raise MultiturnError("a chain shorter than 2 turns has no transition")
    if not 0.0 <= responsiveness <= 1.0:
        raise MultiturnError("responsiveness must be in [0, 1], got %r"
                             % (responsiveness,))
    rc = rng_content if rng_content is not None else rng
    f = seed_force or rng.choice(FM.ORDER)
    out = [TTurn(rc.choice(pool[f]), f, None, frozenset(), None)]
    for _ in range(turns - 1):
        dist = m.row(f)
        nxt = rng.choices(FM.ORDER, weights=[dist[x] for x in FM.ORDER])[0]
        prev = out[-1]
        if rc.random() < responsiveness:
            surface, echoed = responsive_choice(
                idx[nxt], pool[nxt], roots_of(prev.surface, lex_r),
                prev.inherited, rc, lex_r=lex_r)
        else:
            # ⭐ The un-responsive draw is the control's behaviour, reachable on
            # purpose so `responsiveness` is a real dial and not a boolean.
            surface, echoed = rc.choice(pool[nxt]), None
        out.append(TTurn(surface, nxt, f,
                         frozenset({echoed}) if echoed else frozenset(), echoed))
        f = nxt
    return out


# ── measurement ─────────────────────────────────────────────────────────────

def lag_profile(chains, *, max_lag: int, lex_r) -> dict[int, float]:
    """Mean shared roots between turns `lag` apart. ⭐ THE CLAIM, AS A NUMBER.

    lag 1 is provocation->response. lag 2 is, in an alternating exchange, a
    SPEAKER'S OWN PREVIOUS TURN -- so the own-chain persistence guard is this
    function's lag-2 cell and not a separate instrument that could disagree.
    """
    sums = {k: 0 for k in range(1, max_lag + 1)}
    ns = {k: 0 for k in range(1, max_lag + 1)}
    for ch in chains:
        rs = [roots_of(t.surface, lex_r) for t in ch]
        for k in range(1, max_lag + 1):
            for i in range(len(rs) - k):
                sums[k] += len(rs[i] & rs[i + k])
                ns[k] += 1
    return {k: (sums[k] / ns[k] if ns[k] else float("nan"))
            for k in range(1, max_lag + 1)}


def permutation_null(chains, *, lag: int, shuffles: int, rng: random.Random,
                     lex_r) -> tuple[float, float]:
    """(mean, sd) of the lag statistic when the pairing is destroyed.

    ⛔⛔ THE ACCEPTANCE CRITERION IS STATED AGAINST THIS, NEVER AGAINST ZERO.
    Chance overlap between two short utterances drawn from 156 roots is ~0.042
    shared roots, so a generator that does nothing at all already "passes" a
    `> 0` test. Measured, not assumed.
    """
    flat = [roots_of(t.surface, lex_r) for ch in chains for t in ch]
    a = [roots_of(ch[i].surface, lex_r)
         for ch in chains for i in range(len(ch) - lag)]
    means = []
    for _ in range(shuffles):
        b = rng.sample(flat, len(a)) if len(a) <= len(flat) else \
            [rng.choice(flat) for _ in a]
        means.append(sum(len(x & y) for x, y in zip(a, b)) / len(a))
    mu = sum(means) / len(means)
    sd = (sum((x - mu) ** 2 for x in means) / (len(means) - 1)) ** 0.5
    return mu, sd


def check_transience(chains, *, lex_r, max_lag: int = 4, shuffles: int = 200,
                     seed: int = 20620, z_lag1_min: float = Z_LAG1_MIN,
                     z_lagn_max: float = Z_LAGN_MAX) -> dict:
    """⛔⛔ REFUSE BEFORE WRITING. Both halves of the claim, or neither.

    A corpus passes only if it is responsive at lag 1 **and** indistinguishable
    from chance at every longer lag. Failing either way is a different, named
    error:

      * lag 1 at chance          -> it is content-FREE; this is the control
                                    recipe wearing the treatment's name.
      * lag ≥2 above chance      -> content PERSISTS through the chain; the
                                    transitivity break failed and "ingest and
                                    release" has become "hold through my own
                                    history". ⭐ lag 2 IS the own-chain.
    """
    prof = lag_profile(chains, max_lag=max_lag, lex_r=lex_r)
    rng = random.Random(seed)
    report = {"lag_profile": prof, "z": {}, "null": {}}
    for k in range(1, max_lag + 1):
        mu, sd = permutation_null(chains, lag=k, shuffles=shuffles, rng=rng,
                                  lex_r=lex_r)
        z = (prof[k] - mu) / sd if sd else float("nan")
        report["null"][k] = {"mean": mu, "sd": sd}
        report["z"][k] = z
    z1 = report["z"][1]
    if not (z1 >= z_lag1_min):
        raise MultiturnError(
            "NOT RESPONSIVE: lag-1 z=%.2f is below the floor %.2f. The response "
            "is independent of what provoked it -- this is the CONTENT-FREE "
            "recipe, and labelling it content-transient would put the control "
            "arm in the treatment cell." % (z1, z_lag1_min))
    leaks = {k: report["z"][k] for k in range(2, max_lag + 1)
             if report["z"][k] > z_lagn_max}
    if leaks:
        raise MultiturnError(
            "CONTENT PERSISTS: lag(s) %s exceed the chance ceiling z=%.2f "
            "(%s). Content is walking the chain, so the corpus trains "
            "persistence -- object permanence rebuilt from local choices. "
            "⛔ lag 2 is the speaker's OWN previous turn."
            % (sorted(leaks), z_lagn_max,
               ", ".join("lag%d z=%.2f" % (k, v) for k, v in sorted(leaks.items()))))
    report["verdict"] = "content-transient"
    return report


def verify_recipe(chains, recipe: str, *, lex_r, shuffles: int = 200,
                  seed: int = 20620) -> dict:
    """⛔⛔ THE LABEL MUST BE EARNED, IN BOTH DIRECTIONS.

    A content-transient build that is not responsive is the control wearing the
    treatment's name. A content-FREE build that IS responsive is the treatment
    wearing the control's name -- and that one is worse, because the control arm
    is what every contrast in the factorial is measured against. A contaminated
    control does not produce a null result; it produces a *shrunken effect* that
    looks like an honest small finding.

    ⭐ So both arms are verified against the same instrument, and the recipe
    string in the manifest is a measured claim rather than a command-line flag
    that was typed correctly.
    """
    if recipe not in RECIPES:
        raise MultiturnError("unknown recipe %r; valid recipes are %s"
                             % (recipe, ", ".join(RECIPES)))
    if recipe == CONTENT_TRANSIENT:
        return check_transience(chains, lex_r=lex_r, shuffles=shuffles,
                                seed=seed)
    prof = lag_profile(chains, max_lag=2, lex_r=lex_r)
    rng = random.Random(seed)
    mu, sd = permutation_null(chains, lag=1, shuffles=shuffles, rng=rng,
                              lex_r=lex_r)
    z1 = (prof[1] - mu) / sd if sd else float("nan")
    if z1 > Z_LAGN_MAX:
        raise MultiturnError(
            "CONTROL IS CONTAMINATED: lag-1 z=%.2f exceeds the chance ceiling "
            "%.2f, so this 'content-free' corpus is responsive. A contaminated "
            "control does not yield a null -- it yields a SHRUNKEN effect that "
            "reads as an honest small finding." % (z1, Z_LAGN_MAX))
    return {"lag_profile": prof, "z": {1: z1},
            "null": {1: {"mean": mu, "sd": sd}}, "verdict": CONTENT_FREE}


def build_transient(n_chains: int, *, turns: int, pairs, seed: int,
                    responsiveness: float, fmap=None, verify: bool = True):
    """Generate, then REFUSE if it is not actually transient — before writing."""
    from .multiturn import check_force_pair_fairness
    # ⛔ Derived, not two arbitrary seeds: the FORCE stream must depend only on
    # `seed`, so both recipes at seed X paint the same force sequence.
    rng = random.Random(seed)
    rng_content = random.Random(seed ^ 0x5F5E100)
    lex_r = _lex_roots()
    pool = _pool_by_force(pairs)
    idx = index_by_root(pool, lex_r)
    chains = [chain_transient(pool, idx, turns=turns, rng=rng,
                              responsiveness=responsiveness, lex_r=lex_r,
                              fmap=fmap, rng_content=rng_content)
              for _ in range(n_chains)]
    # ⭐ The force gate is UNCHANGED and still runs. The recipes differ in one
    # variable; they do not differ in which invariants they must satisfy.
    check_force_pair_fairness(chains, fmap=fmap)
    if verify:
        check_transience(chains, lex_r=lex_r)
    return chains
