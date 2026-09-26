"""IDF-1 — the window-1 identifiability instruments, on disk at last.

⛔⛔ WHY THIS FILE EXISTS. IDF-1's verdict-relevant numbers — the Step 1 AUCs,
the O-A/O-B/O-C/O-E lag profiles — were produced by heredocs piped to `python -`
and were never written anywhere. The prereg is locked, the results are cited,
and the code that made them existed only in a terminal scrollback. That is the
same exposure class as a lost adapter: an artefact whose provenance cannot be
re-derived because the thing that derived it is gone. Recovered from the session
transcript and landed here so IDF-1b can build on something that can be re-run.

⛔ The statistic is IMPORTED, never re-spelt. `lag_profile`, `permutation_null`
and `resolving_power` live in `tlon.discourse.transient` and have exactly one
definition in this campaign. `tests/test_idf1_instruments.py` pins that.

⭐ ONE FEATURISER, THREE CONSUMERS. The recovered scripts each carried their own
copy of the feature builder (`vec` in one, an inlined loop in another). Three
spellings of "what the classifier can see" is precisely the drift that has
already cost this campaign a voided curve. There is one here and the oracles
call it.

Usage:
    python tools/act2_idf1.py step1      # identifiability + A4' transfer
    python tools/act2_idf1.py step2      # the oracle speakers, large n
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import random
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.act2 import corpus as C1              # noqa: E402
from tlon.discourse import force_map as FM      # noqa: E402
from tlon.discourse import transient as TR      # noqa: E402

#: The cached per-dose rebuilds. Each dose is 1,445 chains of 12 turns, each
#: turn reduced to `(surface, force, sorted(inherited))` — `inherited` is the
#: generator bookkeeping that never reaches a training row, which is the whole
#: object of the probe.
CHAINS = "runs/act2/idf1/chains.pkl"

#: Fixed everywhere. A seed that differs between arms makes the arms differ in
#: two variables.
SEED = 20624
#: A4' evaluates transfer onto an independent draw; this is that draw's seed.
SEED_B = 90210
#: Chain-level split. 1,445 chains, 70% train — `int(0.7 * 1445)`.
N_CHAINS = 1445
TRAIN_CUT = int(0.7 * N_CHAINS)

LEX = sorted(TR._lex_roots())
RIDX = {r: i for i, r in enumerate(LEX)}
FORCES = ["ka", "ki", "ko", "ku", "kä"]
FIDX = {f: i for i, f in enumerate(FORCES)}
R = len(LEX)
#: root identity | co-occurring roots | force | position, relative position,
#: root count, token count
D = 2 * R + len(FORCES) + 4


# ── the one featuriser ─────────────────────────────────────────────────────

def featurise_turn(surface: str, force: str):
    """-> (M, roots), one row per root of this surface.

    ⛔ ONLY what is readable from the `t−1` SURFACE. Root identity, position,
    co-occurring roots, force, length. No chain position, no `inherited`, no
    successor. The moment something else enters here the probe stops measuring
    window-1 identifiability and starts measuring the leak.
    """
    toks = surface.split()
    roots = [t for t in toks if t in RIDX]
    if not roots:
        return None, []
    bag = np.zeros(R, dtype=np.float32)
    for r in roots:
        bag[RIDX[r]] = 1.0
    M = np.zeros((len(roots), D), dtype=np.float32)
    for p, r in enumerate(roots):
        M[p, RIDX[r]] = 1.0
        M[p, R:2 * R] = bag
        # ⭐ Self removed from the co-occurrence block, or root identity is
        # encoded twice and the two blocks stop being separable features.
        M[p, R + RIDX[r]] = 0.0
        if force in FIDX:
            M[p, 2 * R + FIDX[force]] = 1.0
        b = 2 * R + len(FORCES)
        M[p, b] = p
        M[p, b + 1] = p / max(1, len(roots) - 1) if len(roots) > 1 else 0.0
        M[p, b + 2] = len(roots)
        M[p, b + 3] = len(toks)
    return M, roots


def featurise(chains):
    """-> (X, y, groups). `groups` is the CHAIN index.

    ⛔ Turns with an EMPTY inherited set are dropped: there is no label to
    predict. Keeping them would inflate the negative class with rows the
    question was never asked of.
    """
    blocks, ys, groups = [], [], []
    for gi, ch in enumerate(chains):
        for (surf, force, inher) in ch:
            if not inher or not surf:
                continue
            M, roots = featurise_turn(surf, force)
            if M is None:
                continue
            inh = set(inher)
            blocks.append(M)
            ys.extend(1 if r in inh else 0 for r in roots)
            groups.extend(gi for _ in roots)
    return np.vstack(blocks), np.array(ys), np.array(groups)


def load_chains(path=CHAINS):
    import pickle
    with open(path, "rb") as f:
        return pickle.load(f)


def rebuild(seed: int, *, n_chains=N_CHAINS, turns=12, suppression_window=0,
            pool_seed=None):
    """An independent draw under the same generator law. Returns the reduced
    `(surface, force, sorted(inherited))` shape `featurise` expects, plus the
    live chains for scoring.

    ⛔⛔ `pool_seed` EXISTS BECAUSE "INDEPENDENT DRAW" MEANS TWO DIFFERENT
    THINGS AND ONE OF THEM BREAKS A KERNEL. Left unset, the pool is resampled
    with the chain seed, so the second draw speaks a nearly disjoint
    vocabulary — pools at seeds 20624 and 90210 share 3.2% of their surfaces.
    For a classifier over ROOTS (A4′) that is harmless and is the stronger
    test. For anything keyed on exact SURFACES it is fatal: the instrument
    stops measuring transfer and starts measuring the vocabulary swap.
    Pass `pool_seed` to hold the vocabulary fixed and vary only the draw.
    """
    pool = C1.build(6000, seed=seed if pool_seed is None else pool_seed)
    chains = TR.build_transient(n_chains, turns=turns, pairs=pool, seed=seed,
                                responsiveness=1.0,
                                suppression_window=suppression_window,
                                fmap=FM.DERIVED_v1, verify=False)
    reduced = [[(t.surface, t.force, sorted(t.inherited)) for t in ch]
               for ch in chains]
    return chains, reduced


# ── scoring: the IMPORTED instrument, never a second definition ────────────

def score(chains, tag, *, shuffles=200, seed=SEED, width=14, quiet=False):
    """Raw lag profile 1-4 plus the permutation-null z for each.

    ⛔ ONE rng for all four lags, drawn in order 1,2,3,4. Re-seeding per lag
    would silently change every z in the campaign's tables.
    """
    rng = random.Random(seed)
    prof = TR.lag_profile(chains, max_lag=4, lex_r=TR._lex_roots())
    line = []
    for lag in (1, 2, 3, 4):
        mu, sd = TR.permutation_null(chains, lag=lag, shuffles=shuffles,
                                     rng=rng, lex_r=TR._lex_roots())
        z = (prof[lag] - mu) / sd if sd else float("nan")
        line.append("lag%d prof %.4f z %+9.3f" % (lag, prof[lag], z))
    if not quiet:
        print("  %-*s %s" % (width, tag, " | ".join(line)))
    return prof


# ── the oracle speakers ────────────────────────────────────────────────────

def barred_true(out, prev, lex_r):
    """O-C. The positive control: must reproduce the dose-0 corpus."""
    return prev.inherited


def barred_blind(out, prev, lex_r):
    """O-A. The negative control: must reproduce the dose −1 corpus."""
    return frozenset()


def barred_top1(clf):
    """O-B. The single root the classifier is most confident is inherited."""
    def fn(out, prev, lex_r):
        M, roots = featurise_turn(prev.surface, prev.force)
        if M is None:
            return frozenset()
        return frozenset({roots[int(np.argmax(clf.decision_function(M)))]})
    return fn


def barred_threshold(clf, thr):
    """O-B, the F1-maximising threshold variant.

    ⛔ Falls back to the argmax when the threshold selects nothing, so the arm
    never silently degenerates into O-A on a subset of turns.
    """
    def fn(out, prev, lex_r):
        M, roots = featurise_turn(prev.surface, prev.force)
        if M is None:
            return frozenset()
        p = clf.predict_proba(M)[:, 1]
        chosen = {r for r, q in zip(roots, p) if q >= thr}
        return frozenset(chosen or {roots[int(np.argmax(p))]})
    return fn


def speak(barred_fn, *, n=5000, turns=10, pool=None, seed=SEED):
    """Run the generator with one argument varied and nothing else."""
    if pool is None:
        pool = C1.build(6000, seed=seed)
    return TR.build_transient(n, turns=turns, pairs=pool, seed=seed,
                              responsiveness=1.0, fmap=FM.DERIVED_v1,
                              verify=False, barred_fn=barred_fn)


#: O-E walks surfaces, not scenes, so it needs something that duck-types a turn
#: for the instrument. The shared functions read only `.surface`.
Turn = collections.namedtuple("Turn", "surface force")


def kernel(transitions):
    """-> (by_prev, by_roots). The empirical Markov kernel of a corpus."""
    by_prev = collections.defaultdict(list)
    by_roots = collections.defaultdict(list)
    for a, b in transitions:
        by_prev[a].append(b)
        by_roots[TR.roots_of(a, TR._lex_roots())].append(b)
    return by_prev, by_roots


def run_oe(transitions, seeds, *, tag, n=5000, turns=10, seed=SEED,
           quiet=False):
    """O-E — a speaker with no model and no classifier, only memorised draws.

    ⭐ The fallback rate is LOGGED, not assumed. An exact-match rate near 100%
    means this arm is choosing among successors it has literally seen, which is
    what makes it a bound on memorisation rather than on generalisation.
    """
    by_prev, by_roots = kernel(transitions)
    rng = random.Random(seed)
    fb = [0, 0, 0]
    chains = []
    lex_r = TR._lex_roots()
    for _ in range(n):
        cur = rng.choice(seeds)
        ch = [Turn(cur, "ka")]
        for _ in range(turns - 1):
            if by_prev.get(cur):
                nxt = rng.choice(by_prev[cur]); fb[0] += 1
            elif by_roots.get(TR.roots_of(cur, lex_r)):
                nxt = rng.choice(by_roots[TR.roots_of(cur, lex_r)]); fb[1] += 1
            else:
                nxt = rng.choice(seeds); fb[2] += 1
            ch.append(Turn(nxt, "ka"))
            cur = nxt
        chains.append(ch)
    tot = sum(fb)
    if not quiet:
        print("  %-14s exact %.1f%% · root-set %.1f%% · blind %.1f%%"
              % (tag, 100 * fb[0] / tot, 100 * fb[1] / tot, 100 * fb[2] / tot))
    return chains, score(chains, tag, quiet=quiet), [x / tot for x in fb]


def transitions_of(chains):
    """Consecutive surface pairs, flattened across chains."""
    return [(a[0], b[0]) for ch in chains for a, b in zip(ch, ch[1:])]


# ── Step 1 ─────────────────────────────────────────────────────────────────

def _classifiers():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    return (("logreg", LogisticRegression(max_iter=2000, C=1.0)),
            ("gbt", HistGradientBoostingClassifier(max_iter=200,
                                                   random_state=0)))


def fit_eval(Xtr, ytr, Xte, yte, gte, *, reps=2000, seed=SEED):
    """Held-out AUC with a CHAIN-bootstrap 95% CI.

    ⛔ The bootstrap resamples CHAINS, not rows. A row bootstrap would treat
    the roots of one surface as independent draws and shrink the interval by
    a factor that has nothing to do with the evidence.
    """
    from sklearn.metrics import roc_auc_score
    out = {}
    for name, clf in _classifiers():
        clf.fit(Xtr, ytr)
        p = clf.predict_proba(Xte)[:, 1]
        auc = roc_auc_score(yte, p)
        rng = np.random.default_rng(seed)
        chs = np.unique(gte)
        boot = []
        for _ in range(reps):
            pick = rng.choice(chs, size=len(chs), replace=True)
            m = np.concatenate([np.flatnonzero(gte == c) for c in pick])
            if len(np.unique(yte[m])) < 2:
                continue
            boot.append(roc_auc_score(yte[m], p[m]))
        lo, hi = np.percentile(boot, [2.5, 97.5])
        out[name] = (auc, lo, hi, clf)
        print("   %-6s AUC %.4f   chain-bootstrap 95%% CI [%.4f, %.4f]"
              % (name, auc, lo, hi))
    return out


def cmd_chains(a):
    """Rebuild `chains.pkl`, the input every instrument reads.

    ⛔⛔ IT EXISTS BECAUSE THE CACHE HAD NO RECIPE. `chains.pkl` is where every
    IDF-1 and IDF-1b number starts, and for a whole session nothing on disk
    could produce it — the same defect as the instruments themselves, one level
    further up. A cache whose derivation is lost is not a cache, it is an
    artefact of unknown provenance.

    ⭐ Deterministic: seed 20624, 1,445 chains of 12 turns, responsiveness 1.0,
    `DERIVED_v1`, and the ONLY thing that varies across the three doses is
    `recipe_suppression_window` = −1 / 0 / +1.
    """
    import pickle
    out = {}
    for dose, window in (("-1", -1), ("0", 0), ("+1", 1)):
        chains, reduced = rebuild(SEED, suppression_window=window)
        prof = TR.lag_profile(chains, max_lag=4, lex_r=TR._lex_roots())
        print("dose %-3s  %d chains  lag profile %s"
              % (dose, len(reduced),
                 {k: round(v, 6) for k, v in sorted(prof.items())}))
        out[dose] = reduced
    path = pathlib.Path(a.chains)
    path.parent.mkdir(parents=True, exist_ok=True)
    # ⛔ TEMP FILE THEN REPLACE. `open(p, "wb")` truncates before the write can
    # fail, and a half-written pickle here silently poisons every instrument.
    tmp = path.with_suffix(".pkl.tmp")
    with open(tmp, "wb") as f:
        pickle.dump(out, f)
    tmp.replace(path)
    print("\nwrote %s" % path)
    return 0


def cmd_step1(a):
    from sklearn.metrics import roc_auc_score
    data = load_chains(a.chains)
    print("STEP 1 — identifiability of inherited-ness from the t-1 surface "
          "alone")
    print("(rows = one per root of a turn with a non-empty inherited set; "
          "split BY CHAIN)\n")
    res = {}
    for dose in ("-1", "0", "+1"):
        X, y, g = featurise(data[dose])
        tr, te = g < TRAIN_CUT, g >= TRAIN_CUT
        print("dose %-3s  rows %6d   positives %.3f   train chains %d / test %d"
              % (dose, len(y), y.mean(), TRAIN_CUT, N_CHAINS - TRAIN_CUT))
        res[dose] = fit_eval(X[tr], y[tr], X[te], y[te], g[te])
        print()

    print("A4' — cross-draw stability: fit on the dose-0 rebuild (seed %d),"
          % SEED)
    print("      evaluate on an INDEPENDENT rebuild at a different seed.\n")
    Xa, ya, _ = featurise(data["0"])
    chB, redB = rebuild(SEED_B)
    Xb, yb, _ = featurise(redB)
    print("draw A (seed %d) rows %d   draw B (seed %d) rows %d"
          % (SEED, len(ya), SEED_B, len(yb)))
    print("draw B lag profile:", {k: round(v, 6) for k, v in
                                  sorted(TR.lag_profile(
                                      chB, max_lag=4,
                                      lex_r=TR._lex_roots()).items())})
    print()
    for name, clf in _classifiers():
        clf.fit(Xa, ya)
        aucA = roc_auc_score(ya, clf.predict_proba(Xa)[:, 1])
        aucB = roc_auc_score(yb, clf.predict_proba(Xb)[:, 1])
        print("   %-6s  in-sample(draw A) %.4f   TRANSFER to draw B %.4f   "
              "Δ %+.4f" % (name, aucA, aucB, aucB - aucA))
    return 0


# ── Step 2 ─────────────────────────────────────────────────────────────────

def fit_ob(data0):
    """The O-B classifier: logreg on the dose-0 TRAIN chains only."""
    from sklearn.linear_model import LogisticRegression
    X, y, _ = featurise(data0[:TRAIN_CUT])
    clf = LogisticRegression(max_iter=2000).fit(X, y)
    return clf, X, y


def cmd_step2(a):
    from sklearn.metrics import f1_score
    data = load_chains(a.chains)
    clf, X, y = fit_ob(data["0"])
    print("O-B classifier fitted on the dose-0 TRAIN chains (n=%d rows)\n"
          % len(y))

    pool = C1.build(6000, seed=SEED)
    print("STEP 2 — oracles, LARGE n (%d chains x %d turns)\n" % (a.n, a.turns))
    for tag, fn in (("O-C true", barred_true),
                    ("O-A blind", barred_blind),
                    ("O-B clf", barred_top1(clf))):
        score(speak(fn, n=a.n, turns=a.turns, pool=pool), tag, width=10)
    print()
    print("  model D6 lag-2 raw profile: dose−1 0.337 · dose0 0.385 · "
          "dose+1 0.333")

    # The threshold variant needs a held-out F1, so it needs the test fold.
    Xte, yte, _ = featurise(data["0"][TRAIN_CUT:])
    pte = clf.predict_proba(Xte)[:, 1]
    F1, THR = max((f1_score(yte, (pte >= t).astype(int)), t)
                  for t in np.linspace(0.05, 0.95, 91))
    print("\nO-B threshold maximising held-out F1: %.3f  (F1=%.4f)\n"
          % (THR, F1))
    print("O-B VARIANTS, large n (%d x %d)\n" % (a.n, a.turns))
    for tag, fn in (("O-B top1", barred_top1(clf)),
                    ("O-B F1-thr", barred_threshold(clf, THR))):
        score(speak(fn, n=a.n, turns=a.turns, pool=pool), tag)

    print("\nO-E — empirical Markov kernel per dose (fallback rate logged)\n")
    for dose in ("-1", "0", "+1"):
        run_oe(transitions_of(data[dose]),
               [ch[0][0] for ch in data[dose]],
               tag="O-E dose %s" % dose, n=a.n, turns=a.turns)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chains", default=CHAINS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("chains"); q.set_defaults(fn=cmd_chains)
    q = sub.add_parser("step1"); q.set_defaults(fn=cmd_step1)
    q = sub.add_parser("step2"); q.set_defaults(fn=cmd_step2)
    q.add_argument("--n", type=int, default=5000)
    q.add_argument("--turns", type=int, default=10)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
