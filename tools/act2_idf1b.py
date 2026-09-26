"""IDF-1b — replay versus readable provenance.

Pre-registered in `docs/PREREG_IDF1B_2026_09_25.md`. Five instruments, all CPU.

⛔ The statistic is IMPORTED from `tlon.discourse.transient`, and the featuriser,
the oracle factories and the scorer are imported from `tools/act2_idf1.py`.
Nothing here re-spells any of them; `tests/test_idf1b_instruments.py` pins that.

The question. IDF-1's O-E — an empirical kernel keyed on exact surface identity
— reached lag-2 0.2600 at dose 0 while the D6 model sits at 0.3850. H-REPLAY
says that suppression is surface identity acting as a POINTER INTO SPECIFIC
CORPUS CHAINS, replaying the chains that carry the hidden state, rather than
provenance readable off the surface. Instruments 1-3 take the pointer away.

Usage:
    python tools/act2_idf1b.py i1      # replay rate
    python tools/act2_idf1b.py i2      # O-E-noreplay
    python tools/act2_idf1b.py i3      # O-E-heldout
    python tools/act2_idf1b.py i4      # Step 1 with surface identity
    python tools/act2_idf1b.py i5      # matched-fidelity floor (descriptive)
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import random
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import act2_idf1 as I                            # noqa: E402

from tlon.act2 import corpus as C1               # noqa: E402
from tlon.discourse import force_map as FM       # noqa: E402
from tlon.discourse import transient as TR       # noqa: E402

DOSES = ("-1", "0", "+1")

#: Parsed from the D6 cells' own artefacts, not recalled:
#: runs/act2/retrain12_{cp,ct,ctw1}/model_lag_*.json
MODEL_LAG1 = {"-1": 1.0495049504950495,
              "0": 1.0277777777777777,
              "+1": 1.0462962962962963}
MODEL_LAG2 = {"-1": 0.33707865168539325,
              "0": 0.3854166666666667,
              "+1": 0.3333333333333333}

#: The two red-proofs that anchor the reading table's gap scale.
O_A_BLIND, O_C_TRUE = 0.4456, 0.0285
GAP = O_A_BLIND - O_C_TRUE

#: ⛔ Below this, an arm is PERCEIVE-COLLAPSED and is never read as release.
#: IDF-1's O-B F1-threshold variant drove lag-1 to 0.0000 at z −42.911 and would
#: otherwise have looked like a spectacular release result.
Z_LAG1_FLOOR = 6.0


def closes(lag2: float) -> float:
    """Fraction of the blind-to-true gap an arm closes."""
    return (O_A_BLIND - lag2) / GAP


# ── instrument 1 · replay rate ─────────────────────────────────────────────

def corpus_triples(chains) -> set:
    """Every consecutive surface triple that really occurs inside one chain.

    ⛔ Within a chain only. A triple assembled across a chain boundary never
    happened, and counting it would inflate the replay rate with evidence the
    corpus does not contain.
    """
    out = set()
    for ch in chains:
        for i in range(len(ch) - 2):
            out.add((ch[i][0], ch[i + 1][0], ch[i + 2][0]))
    return out


def replay_rate(walk_chains, triples) -> tuple[float, int, int]:
    """-> (fraction, hits, total) over consecutive triples of the walked chains."""
    hits = total = 0
    for ch in walk_chains:
        for i in range(len(ch) - 2):
            total += 1
            if (ch[i].surface, ch[i + 1].surface, ch[i + 2].surface) in triples:
                hits += 1
    return (hits / total if total else float("nan")), hits, total


# ── instrument 2 · O-E-noreplay ────────────────────────────────────────────

def kernel_sourced(chains):
    """Like `act2_idf1.kernel`, but every successor remembers WHICH CHAIN
    supplied it. That chain id is the whole instrument: without it there is no
    way to decline to replay."""
    by_prev = collections.defaultdict(list)
    by_roots = collections.defaultdict(list)
    lex_r = TR._lex_roots()
    for cid, ch in enumerate(chains):
        for a, b in zip(ch, ch[1:]):
            by_prev[a[0]].append((cid, b[0]))
            by_roots[TR.roots_of(a[0], lex_r)].append((cid, b[0]))
    return by_prev, by_roots


def run_oe_noreplay(chains, *, tag, n=5000, turns=10, seed=I.SEED, quiet=False,
                    blind_w=0.0, km=None):
    """O-E with the pointer removed.

    At every step the successor is drawn only from chains OTHER than the one
    that supplied the transition into the current surface. The seed turn counts
    as supplied by the chain it was drawn from, so the walk cannot begin by
    replaying its own source.

    ⭐ The fallback ladder is logged in full. 6.2% of surface-occurrences sit on
    single-chain surfaces where the exclusion leaves nothing; an unlogged
    fallback there would quietly turn this arm back into the thing it exists to
    exclude.
    """
    by_prev, by_roots = km if km is not None else kernel_sourced(chains)
    lex_r = TR._lex_roots()
    rng = random.Random(seed)
    fb = [0, 0, 0, 0]          # exact-other | root-set-other | blind | reseed
    walked = []
    for _ in range(n):
        cid = rng.randrange(len(chains))
        cur = chains[cid][0][0]
        src = cid
        ch = [I.Turn(cur, "ka")]
        for _ in range(turns - 1):
            # ⛔ SHORT-CIRCUIT, DELIBERATELY. At blind_w == 0.0 no rng call is
            # made here, so the draw sequence is byte-identical to the run that
            # produced i2_noreplay.txt before this parameter existed.
            if blind_w and rng.random() < blind_w:
                nc = rng.randrange(len(chains))
                src, cur = nc, chains[nc][0][0]
                fb[2] += 1
                ch.append(I.Turn(cur, "ka"))
                continue
            cand = [(c, s) for (c, s) in by_prev.get(cur, ()) if c != src]
            if cand:
                src, cur = rng.choice(cand); fb[0] += 1
            else:
                rs = [(c, s) for (c, s) in by_roots.get(
                    TR.roots_of(cur, lex_r), ()) if c != src]
                if rs:
                    src, cur = rng.choice(rs); fb[1] += 1
                else:
                    nc = rng.randrange(len(chains))
                    src, cur = nc, chains[nc][0][0]
                    fb[2] += 1
            ch.append(I.Turn(cur, "ka"))
        walked.append(ch)
    tot = sum(fb)
    if not quiet:
        print("  %-18s exact-other %.1f%% · root-set-other %.1f%% · reseed %.1f%%"
              % (tag, 100 * fb[0] / tot, 100 * fb[1] / tot, 100 * fb[2] / tot))
    return walked, I.score(walked, tag, width=18, quiet=quiet)


# ── instrument 3 · O-E-heldout ─────────────────────────────────────────────

def run_oe_heldout(kernel_chains, seed_chains, *, tag, n=5000, turns=10,
                   seed=I.SEED, quiet=False):
    """The `read_lag` situation: a kernel built from draw A, asked to continue
    surfaces it never saw, drawn from an independent draw B.

    ⭐ The exact-hit rate is the number that matters here. If it collapses, the
    kernel's 0.26 was a property of having the corpus in hand.
    """
    by_prev, by_roots = I.kernel(I.transitions_of(kernel_chains))
    lex_r = TR._lex_roots()
    seeds = [ch[0][0] for ch in seed_chains]
    rng = random.Random(seed)
    fb = [0, 0, 0]
    walked = []
    for _ in range(n):
        cur = rng.choice(seeds)
        ch = [I.Turn(cur, "ka")]
        for _ in range(turns - 1):
            if by_prev.get(cur):
                cur = rng.choice(by_prev[cur]); fb[0] += 1
            elif by_roots.get(TR.roots_of(cur, lex_r)):
                cur = rng.choice(by_roots[TR.roots_of(cur, lex_r)]); fb[1] += 1
            else:
                cur = rng.choice(seeds); fb[2] += 1
            ch.append(I.Turn(cur, "ka"))
        walked.append(ch)
    tot = sum(fb)
    if not quiet:
        print("  %-18s exact %.1f%% · root-set %.1f%% · blind %.1f%%"
              % (tag, 100 * fb[0] / tot, 100 * fb[1] / tot, 100 * fb[2] / tot))
    return walked, I.score(walked, tag, width=18, quiet=quiet)


# ── instrument 4 · Step 1 with surface identity ────────────────────────────

def root_buckets(seed=I.SEED):
    """{(force, root): how many surfaces that root can produce under it}.

    Readable from the `t−1` surface: the force is in the surface and the root
    is the row's own root. Sizes run 7-37, median 20.
    """
    pool = TR._pool_by_force(C1.build(6000, seed=seed))
    idx = TR.index_by_root(pool, TR._lex_roots())
    return {(f, r): len(v) for f in idx for r, v in idx[f].items()}


def featurise_plus(chains, vocab, buckets):
    """Step 1's features, plus surface identity and the index-bucket size.

    ⛔⛔ THE VOCABULARY IS BUILT ON THE TRAINING FOLD ONLY. A vocabulary built
    over all chains would give every test surface its own column fitted on
    rows from its own chain — the chain-identity leak the split exists to stop,
    re-entering through the feature block.

    Surface identity is a one-hot over the training vocabulary with a single
    shared OUT-OF-VOCABULARY column. That encoding is the estimand: it measures
    surface identity AS FAR AS IT TRANSFERS ACROSS CHAINS, which is what a
    generalising speaker could actually use.
    """
    from scipy import sparse
    base, ys, groups, seen = [], [], [], []
    si_rows, si_cols = [], []
    extra = []
    nrow = 0
    V = len(vocab)
    for gi, ch in enumerate(chains):
        for (surf, force, inher) in ch:
            if not inher or not surf:
                continue
            M, roots = I.featurise_turn(surf, force)
            if M is None:
                continue
            inh = set(inher)
            col = vocab.get(surf, V)           # V == the shared OOV column
            base.append(M)
            for r in roots:
                si_rows.append(nrow); si_cols.append(col)
                extra.append([buckets.get((force, r), 0)])
                ys.append(1 if r in inh else 0)
                groups.append(gi)
                seen.append(1 if surf in vocab else 0)
                nrow += 1
    X0 = sparse.csr_matrix(np.vstack(base))
    SI = sparse.csr_matrix((np.ones(nrow, dtype=np.float32),
                            (si_rows, si_cols)), shape=(nrow, V + 1))
    EX = sparse.csr_matrix(np.asarray(extra, dtype=np.float32))
    X = sparse.hstack([X0, SI, EX]).tocsr()
    return X, np.array(ys), np.array(groups), np.array(seen)


def train_vocab(chains):
    """Surfaces of the TRAIN fold, in a fixed order."""
    out = {}
    for ch in chains:
        for (surf, _f, inher) in ch:
            if inher and surf and surf not in out:
                out[surf] = len(out)
    return out


def auc_ci(y, p, g, *, reps=2000, seed=I.SEED):
    """Held-out AUC with a CHAIN bootstrap."""
    from sklearn.metrics import roc_auc_score
    if len(np.unique(y)) < 2:
        return float("nan"), float("nan"), float("nan")
    auc = roc_auc_score(y, p)
    rng = np.random.default_rng(seed)
    chs = np.unique(g)
    boot = []
    for _ in range(reps):
        pick = rng.choice(chs, size=len(chs), replace=True)
        m = np.concatenate([np.flatnonzero(g == c) for c in pick])
        if len(np.unique(y[m])) < 2:
            continue
        boot.append(roc_auc_score(y[m], p[m]))
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return auc, lo, hi


#: Instrument 5 needs instrument 4's fitted speaker. Persisted rather than
#: refitted, so O-B(4) in the floor is provably the same object whose AUC the
#: reading table gates on — a refit is a second thing to drift.
OB4 = "runs/act2/idf1/ob4_dose0.pkl"


def cmd_i4(a):
    import pickle
    from sklearn.linear_model import LogisticRegression
    data = I.load_chains(a.chains)
    buckets = root_buckets()
    for dose in DOSES:
        chains = data[dose]
        tr_ch, te_ch = chains[:I.TRAIN_CUT], chains[I.TRAIN_CUT:]
        vocab = train_vocab(tr_ch)
        Xtr, ytr, _gtr, _ = featurise_plus(tr_ch, vocab, buckets)
        Xte, yte, gte, seen = featurise_plus(te_ch, vocab, buckets)
        print("dose %-3s  train surfaces %d   test rows %d   "
              "test rows on a SEEN surface %.1f%%"
              % (dose, len(vocab), len(yte), 100 * seen.mean()))
        clf = LogisticRegression(max_iter=2000, C=1.0).fit(Xtr, ytr)
        p = clf.predict_proba(Xte)[:, 1]
        auc, lo, hi = auc_ci(yte, p, gte)
        print("   ALL        AUC %.4f   chain-bootstrap 95%% CI [%.4f, %.4f]"
              % (auc, lo, hi))
        # ⭐ Stratified, so "unseen surfaces dragged it down" is a number and
        # not an argument.
        for name, mask in (("seen", seen == 1), ("unseen", seen == 0)):
            if mask.sum() == 0:
                print("   %-10s (no rows)" % name)
                continue
            s_auc, s_lo, s_hi = auc_ci(yte[mask], p[mask], gte[mask])
            print("   %-10s AUC %.4f   chain-bootstrap 95%% CI [%.4f, %.4f]"
                  "   n=%d" % (name, s_auc, s_lo, s_hi, mask.sum()))
        if dose == "0":
            with open(OB4, "wb") as f:
                pickle.dump({"clf": clf, "vocab": vocab, "buckets": buckets},
                            f)
            print("   → speaker persisted to %s" % OB4)
        print()
    return 0


def barred_ob4(clf, vocab, buckets):
    """O-B(4) — the top-1 root under instrument 4's classifier.

    ⛔ The feature block must be assembled EXACTLY as at fit time: base
    features, then the train-fold surface one-hot with its shared OOV column,
    then the bucket size. A column out of order here is a speaker answering a
    different question than the AUC beside it.
    """
    from scipy import sparse
    V = len(vocab)

    def fn(out, prev, lex_r):
        M, roots = I.featurise_turn(prev.surface, prev.force)
        if M is None:
            return frozenset()
        n = len(roots)
        col = vocab.get(prev.surface, V)
        SI = sparse.csr_matrix((np.ones(n, dtype=np.float32),
                                (np.arange(n), np.full(n, col))),
                               shape=(n, V + 1))
        EX = sparse.csr_matrix(
            np.array([[buckets.get((prev.force, r), 0)] for r in roots],
                     dtype=np.float32))
        X = sparse.hstack([sparse.csr_matrix(M), SI, EX]).tocsr()
        return frozenset({roots[int(np.argmax(clf.decision_function(X)))]})
    return fn


# ── instrument 5 · matched-fidelity floor (descriptive, does not gate) ─────

def lag1_of(chains):
    return TR.lag_profile(chains, max_lag=1, lex_r=TR._lex_roots())[1]


def tune(make, target, *, iters=9, lo=0.0, hi=1.0):
    """Bisect a scalar knob in [lo, hi] so an arm's lag-1 matches the model's.

    -> (knob, achieved_lag1, bracketed). `make(k)` returns chains.

    ⛔⛔ THE BRACKETING FLAG IS THE POINT. A bisection always returns SOMETHING;
    returning an endpoint and calling it "matched" is how an unreachable target
    becomes a silent lie in a table. If the target lies outside what the knob
    can reach, that is reported and the closest endpoint is labelled as such.

    ⛔ Comparing lag-2 between speakers whose lag-1 differs compares two things
    at once: a speaker carrying less forward has less to suppress. Matching
    first is what makes the comparison a floor rather than a coincidence.
    """
    f_lo, f_hi = lag1_of(make(lo)), lag1_of(make(hi))
    span = (min(f_lo, f_hi), max(f_lo, f_hi))
    if not span[0] <= target <= span[1]:
        end, got = (lo, f_lo) if abs(f_lo - target) < abs(f_hi - target) \
            else (hi, f_hi)
        return end, got, False
    a, b, fa = lo, hi, f_lo
    for _ in range(iters):
        mid = (a + b) / 2.0
        got = lag1_of(make(mid))
        if (got < target) == (fa < target):
            a, fa = mid, got
        else:
            b = mid
    return mid, got, True


def barred_at_rate(inner, rate, *, seed=I.SEED):
    """Bar with probability `rate`, otherwise bar nothing.

    ⭐ THE KNOB THAT ACTUALLY REACHES THE TARGET. `responsiveness` cannot: the
    D6 model's lag-1 (1.0278 at dose 0) is ABOVE every suppressing oracle —
    O-C 0.9651, O-E 0.9580, O-B 0.9350, O-E-noreplay 0.8973 — and below only
    O-A blind's 1.0357. Barring is what removes carry, so the dial that spans
    the model's fidelity runs from "bar nothing" (exactly O-A) to "bar always"
    (exactly the arm). Recorded as a deviation.
    """
    rng = random.Random(seed)

    def fn(out, prev, lex_r):
        if rng.random() < rate:
            return inner(out, prev, lex_r)
        return frozenset()
    return fn


def read_chains(pool_pairs, *, n, turns, seed, responsiveness, barred_fn):
    """`build_transient`'s chains WITHOUT its corpus-level gate.

    ⛔⛔ DO NOT "FIX" THIS BY LOOSENING `check_force_pair_fairness`. That gate is
    unconditional on purpose and it is correct: a generated CORPUS that starves
    a force pair cannot measure that transition. But a matched READ is 12
    chains of 10 turns — 120 turns — and at that size some force pair is
    routinely unrepresented by chance. The model's own read was 12 chains too,
    and it was read off a trained speaker, never gated this way. Applying a
    corpus invariant to a read would silently discard exactly the unlucky draws
    that make the distribution a distribution.

    ⭐ The rng derivation is `build_transient`'s, byte for byte, so the chains
    are the same chains — only the corpus gate is not applied to a non-corpus.
    """
    rng = random.Random(seed)
    rng_content = random.Random(seed ^ 0x5F5E100)
    lex_r = TR._lex_roots()
    pool = TR._pool_by_force(pool_pairs)
    idx = TR.index_by_root(pool, lex_r)
    return [TR.chain_transient(pool, idx, turns=turns, rng=rng,
                               responsiveness=responsiveness, lex_r=lex_r,
                               fmap=FM.DERIVED_v1, rng_content=rng_content,
                               barred_fn=barred_fn)
            for _ in range(n)]


def matched_reads(make, *, reps=500, tag="", seed=I.SEED):
    """The model's read size: 12 chains x 10 turns, `reps` independent reads.

    -> (lag2 array, lag1 array). Raw profiles only: at n=120 turns a
    permutation z is noise, which is why the prereg compares RAW lag-2.
    """
    l2, l1 = [], []
    for r in range(reps):
        ch = make(seed + r)
        prof = TR.lag_profile(ch, max_lag=2, lex_r=TR._lex_roots())
        l1.append(prof[1]); l2.append(prof[2])
    return np.array(l2), np.array(l1)


def cmd_i5(a):
    import pickle
    data = I.load_chains(a.chains)
    pool = C1.build(6000, seed=I.SEED)
    with open(OB4, "rb") as f:
        saved = pickle.load(f)
    ob4 = barred_ob4(saved["clf"], saved["vocab"], saved["buckets"])

    print("INSTRUMENT 5 — matched-fidelity floor (DESCRIPTIVE, GATES NOTHING)\n")
    print("Each arm's knob is tuned so its lag-1 matches the D6 model's, then")
    print("lag-2 is read at the model's own read size: 12 chains x 10 turns,")
    print("%d independent reads.\n" % a.reps)

    def gen(barred_fn, resp=1.0):
        def make(seed):
            return read_chains(pool, n=12, turns=10, seed=seed,
                               responsiveness=resp, barred_fn=barred_fn)
        return make

    for dose in DOSES:
        target = MODEL_LAG1[dose]
        print("── dose %s · model lag-1 %.4f · model lag-2 %.4f"
              % (dose, target, MODEL_LAG2[dose]))

        arms = []
        # O-A: the knob the prereg names, on the one arm it can reach.
        k, got, ok = tune(lambda r: TR.build_transient(
            400, turns=10, pairs=pool, seed=I.SEED, responsiveness=r,
            fmap=FM.DERIVED_v1, verify=False, barred_fn=I.barred_blind),
            target)
        arms.append(("O-A", "responsiveness", k, got, ok,
                     gen(I.barred_blind, resp=k)))
        # O-B(4): bar-rate, because responsiveness cannot reach the target.
        k, got, ok = tune(lambda p: TR.build_transient(
            400, turns=10, pairs=pool, seed=I.SEED, responsiveness=1.0,
            fmap=FM.DERIVED_v1, verify=False,
            barred_fn=barred_at_rate(ob4, p)), target)
        arms.append(("O-B(4)", "bar-rate", k, got, ok,
                     gen(barred_at_rate(ob4, k))))
        # O-E-noreplay: the kernel arm, blind-mix knob.
        chains = data[dose]
        # ⛔ Built ONCE. Rebuilding it inside the bisection would re-index 1,445
        # chains on every probe and turn a cheap tune into an hour.
        km = kernel_sourced(chains)

        def kmake(seed, w=0.0):
            walked, _ = run_oe_noreplay(chains, tag="", n=12, turns=10,
                                        seed=seed, quiet=True, blind_w=w,
                                        km=km)
            return walked
        k, got, ok = tune(lambda w: [c for s in range(34)
                                     for c in kmake(I.SEED + s, w)], target)
        arms.append(("O-E-noreplay", "blind-mix", k, got, ok,
                     lambda seed, _k=k: kmake(seed, _k)))

        for name, knob, k, got, ok, make in arms:
            l2, l1 = matched_reads(make, reps=a.reps)
            mark = "" if ok else "  ⛔ TARGET NOT REACHABLE — knob at its limit"
            print("  %-13s %s %.4f -> lag-1 %.4f%s" % (name, knob, k, got,
                                                       mark))
            lo, hi = np.percentile(l2, [2.5, 97.5])
            pct = 100.0 * (l2 < MODEL_LAG2[dose]).mean()
            print("       matched-read lag-1 mean %.4f · lag-2 mean %.4f "
                  "[%.4f, %.4f]" % (l1.mean(), l2.mean(), lo, hi))
            print("       the model's lag-2 %.4f sits above %.1f%% of this "
                  "arm's reads" % (MODEL_LAG2[dose], pct))
        print()
    return 0


# ── runners for instruments 1-3 ────────────────────────────────────────────

def cmd_i1(a):
    data = I.load_chains(a.chains)
    print("INSTRUMENT 1 — replay rate of the O-E walk, per dose\n")
    for dose in DOSES:
        chains = data[dose]
        walked, _prof, _fb = I.run_oe(I.transitions_of(chains),
                                      [ch[0][0] for ch in chains],
                                      tag="O-E dose %s" % dose, n=a.n,
                                      turns=a.turns, quiet=True)
        rate, hits, tot = replay_rate(walked, corpus_triples(chains))
        print("  dose %-3s  replayed triples %6d / %6d = %.4f"
              % (dose, hits, tot, rate))
    return 0


def cmd_i2(a):
    data = I.load_chains(a.chains)
    print("INSTRUMENT 2 — O-E-noreplay, large n (%d x %d)\n" % (a.n, a.turns))
    for dose in DOSES:
        _w, prof = run_oe_noreplay(data[dose], tag="noreplay %s" % dose,
                                   n=a.n, turns=a.turns)
        print("            closes %.1f%% of the blind-to-true gap\n"
              % (100 * closes(prof[2])))
    return 0


def cmd_i3(a):
    data = I.load_chains(a.chains)
    pool_seed = None if a.free_pool else I.SEED
    print("INSTRUMENT 3 — O-E-heldout: kernel from draw A (seed %d), surfaces "
          "from draw B (seed %d)" % (I.SEED, I.SEED_B))
    print("  pool seed: %s\n"
          % ("resampled with the draw — MEASURES THE VOCABULARY SWAP"
             if a.free_pool else "held at %d, so only the DRAW varies"
             % I.SEED))
    _chB, redB = I.rebuild(I.SEED_B, pool_seed=pool_seed)
    _w, prof = run_oe_heldout(data["0"], redB, tag="heldout dose 0",
                              n=a.n, turns=a.turns)
    print("            closes %.1f%% of the blind-to-true gap\n"
          % (100 * closes(prof[2])))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chains", default=I.CHAINS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("i1", cmd_i1), ("i2", cmd_i2), ("i3", cmd_i3),
                     ("i4", cmd_i4), ("i5", cmd_i5)):
        q = sub.add_parser(name); q.set_defaults(fn=fn)
        if name == "i5":
            q.add_argument("--reps", type=int, default=500)
        if name not in ("i4", "i5"):
            q.add_argument("--n", type=int, default=5000)
            q.add_argument("--turns", type=int, default=10)
        if name == "i3":
            q.add_argument("--free-pool", action="store_true",
                           help="resample the pool with the draw — the "
                                "original, confounded form; kept runnable so "
                                "the deviation can be reproduced")
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
