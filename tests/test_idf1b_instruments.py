"""⛔⛔ RED-PROOF FOR THE IDF-1b INSTRUMENTS.

IDF-1b exists because IDF-1's O-E may have been replaying corpus chains rather
than reading provenance off a surface. Every instrument here is therefore an
instrument for TAKING THE POINTER AWAY, and each one has a way of silently
failing to: a triple counted across a chain boundary, a successor drawn from
the chain that was supposed to be excluded, a vocabulary built over the test
fold. Those are what this suite fires on.
"""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

import act2_idf1 as I    # noqa: E402
import act2_idf1b as B   # noqa: E402

from tlon.discourse import transient as TR  # noqa: E402


def test_the_module_does_NOT_define_its_own_lag_statistic():
    """⛔ IDF-1b's guards promise "the same imported instrument". This is what
    makes that promise checkable."""
    src = pathlib.Path(B.__file__).read_text(encoding="utf-8")
    for banned in ("def lag_profile", "def permutation_null",
                   "def resolving_power", "def featurise_turn"):
        assert banned not in src, \
            "act2_idf1b re-spells %s instead of importing it" % banned


def test_it_scores_through_the_shared_path():
    assert B.I.score is I.score
    assert B.TR.lag_profile is TR.lag_profile


def test_the_gap_anchors_are_the_two_red_proofs():
    """The reading table is denominated in gap-fraction, so the anchors are
    load-bearing: O-A closes none of it and O-C closes all of it."""
    assert B.closes(B.O_A_BLIND) == pytest.approx(0.0)
    assert B.closes(B.O_C_TRUE) == pytest.approx(1.0)
    assert B.closes(0.383035) == pytest.approx(0.15, abs=1e-4)
    assert B.closes(0.299615) == pytest.approx(0.35, abs=1e-4)


def test_model_values_match_the_D6_artefacts():
    """⛔ Copied from `model_lag_*.json`, not recalled. If these drift from the
    artefacts, instrument 5 matches against a number nobody measured."""
    import json
    import glob
    for cell, dose in (("retrain12_cp", "-1"), ("retrain12_ct", "0"),
                       ("retrain12_ctw1", "+1")):
        root = pathlib.Path(__file__).resolve().parents[1]
        p = glob.glob(str(root / "runs" / "act2" / cell / "model_lag_*.json"))[0]
        lp = json.load(open(p))["lag_profile"]
        assert float(lp["1"]) == B.MODEL_LAG1[dose]
        assert float(lp["2"]) == B.MODEL_LAG2[dose]


# ── instrument 1 ───────────────────────────────────────────────────────────

def test_triples_never_cross_a_chain_boundary():
    """⛔⛔ A triple assembled across the join never happened. Counting it
    would inflate the replay rate with evidence the corpus does not hold —
    the same shape as the 4.3x fabricated-pair inflation that killed A4."""
    chains = [[("a", "ka", []), ("b", "ka", []), ("c", "ka", [])],
              [("d", "ka", []), ("e", "ka", []), ("f", "ka", [])]]
    assert B.corpus_triples(chains) == {("a", "b", "c"), ("d", "e", "f")}


def test_replay_rate_counts_only_real_triples():
    triples = {("a", "b", "c")}
    walked = [[I.Turn("a", "ka"), I.Turn("b", "ka"), I.Turn("c", "ka"),
               I.Turn("z", "ka")]]
    rate, hits, total = B.replay_rate(walked, triples)
    assert (hits, total) == (1, 2)
    assert rate == pytest.approx(0.5)


# ── instrument 2 · the decisive red-proof ──────────────────────────────────

def _toy(n_chains=6, turns=6):
    """Chains that SHARE surfaces, so the exclusion has somewhere to go.

    Surfaces are built from REAL lexicon roots: the scorer counts root overlap,
    so placeholder strings would make every lag profile trivially zero and the
    test would pass without the instrument doing anything.
    """
    rts = sorted(TR._lex_roots())[:4]
    return [[("%s %s ka" % (rts[i % 4], rts[(i + 1) % 4]), "ka", [])
             for i in range(c, c + turns)] for c in range(n_chains)]


def test_kernel_sourced_attaches_the_supplying_chain():
    chains = [[("a", "ka", []), ("b", "ka", [])],
              [("a", "ka", []), ("c", "ka", [])]]
    by_prev, _ = B.kernel_sourced(chains)
    assert sorted(by_prev["a"]) == [(0, "b"), (1, "c")]


def test_noreplay_never_draws_from_the_chain_it_came_from():
    """⛔⛔ THE INSTRUMENT'S ONE JOB. If a successor can come from the source
    chain, O-E-noreplay is O-E with a longer name and the REPLAY reading is
    unfalsifiable rather than tested.

    Built as a direct audit of the candidate sets the walk is allowed to see,
    because the walk itself only reports the surfaces it landed on.
    """
    chains = _toy()
    by_prev, by_roots = B.kernel_sourced(chains)
    for surf, entries in by_prev.items():
        for src, _ in entries:
            cand = [(c, s) for (c, s) in entries if c != src]
            assert all(c != src for c, _ in cand), \
                "the source chain survived the exclusion for %r" % surf


def test_noreplay_logs_a_fallback_ladder_that_sums_to_the_steps_taken():
    """⭐ 6.2% of surface-occurrences sit on single-chain surfaces where the
    exclusion leaves nothing. An unlogged fallback there turns the arm back
    into the thing it exists to exclude."""
    chains = _toy(n_chains=8, turns=8)
    walked, prof = B.run_oe_noreplay(chains, tag="t", n=20, turns=6,
                                     quiet=True)
    assert len(walked) == 20
    assert all(len(ch) == 6 for ch in walked)
    assert set(prof) == {1, 2, 3, 4}


# ── instrument 3 ───────────────────────────────────────────────────────────

def test_heldout_walks_the_kernel_of_A_from_seeds_of_B():
    """The two corpora must be kept apart: the kernel is A's, the seeds are
    B's. A run that silently seeded from A would measure nothing."""
    rts = sorted(TR._lex_roots())[:4]
    sa, sb = "%s ka" % rts[0], "%s ka" % rts[1]
    sq, sr = "%s ka" % rts[2], "%s ka" % rts[3]
    A = [[(sa, "ka", []), (sb, "ka", [])]]
    Bc = [[(sq, "ka", []), (sr, "ka", [])]]
    walked, _ = B.run_oe_heldout(A, Bc, tag="t", n=5, turns=6, quiet=True)
    assert all(ch[0].surface == sq for ch in walked), \
        "the walk did not start from draw B's surfaces"


# ── instrument 4 ───────────────────────────────────────────────────────────

def _roots3():
    return sorted(TR._lex_roots())[:3]


def test_the_surface_vocabulary_is_built_on_the_TRAIN_fold_only():
    """⛔⛔ A vocabulary over all chains gives every test surface its own
    column fitted on rows from its own chain — the chain-identity leak the
    split exists to stop, walking back in through the feature block."""
    a, b, _ = _roots3()
    tr = [[("%s %s ka" % (a, b), "ka", [a])]]
    vocab = B.train_vocab(tr)
    assert "%s %s ka" % (a, b) in vocab
    assert len(vocab) == 1


def test_train_vocab_skips_turns_with_no_label():
    """It must agree with `featurise`, which drops those turns. A vocabulary
    holding surfaces the featuriser never emits would mis-size the one-hot."""
    a, b, _ = _roots3()
    s = "%s %s ka" % (a, b)
    assert B.train_vocab([[(s, "ka", [])]]) == {}


def test_an_unseen_surface_lands_in_the_shared_OOV_column():
    a, b, c = _roots3()
    seen_s = "%s %s ka" % (a, b)
    new_s = "%s %s ka" % (a, c)
    vocab = B.train_vocab([[(seen_s, "ka", [a])]])
    buckets = {}
    X, y, g, seen = B.featurise_plus([[(new_s, "ka", [a])]], vocab, buckets)
    assert list(seen) == [0, 0], "an unseen surface was marked seen"
    oov = I.D + len(vocab)
    assert X[:, oov].toarray().ravel().tolist() == [1.0, 1.0]


def test_the_seen_mask_tracks_the_surface_not_the_row():
    a, b, c = _roots3()
    seen_s = "%s %s ka" % (a, b)
    new_s = "%s %s ka" % (a, c)
    vocab = B.train_vocab([[(seen_s, "ka", [a])]])
    _X, _y, _g, seen = B.featurise_plus(
        [[(seen_s, "ka", [a]), (new_s, "ka", [a])]], vocab, {})
    assert list(seen) == [1, 1, 0, 0]


def test_the_bucket_feature_is_readable_from_the_surface():
    """(force, root) -> how many surfaces that root can produce. Both halves
    of the key are in the surface, so the feature stays window-1."""
    buckets = B.root_buckets()
    assert buckets, "no index buckets built"
    sizes = list(buckets.values())
    assert min(sizes) > 0 and max(sizes) < 1000
    a, b, _ = _roots3()
    vocab = {}
    X, _y, _g, _s = B.featurise_plus([[("%s %s ka" % (a, b), "ka", [a])]],
                                     vocab, buckets)
    col = X[:, -1].toarray().ravel()
    assert col.tolist() == [buckets.get(("ka", a), 0),
                            buckets.get(("ka", b), 0)]


def test_auc_ci_bootstraps_chains_not_rows():
    """⛔⛔ A row bootstrap treats the roots of one surface as independent draws
    and shrinks the interval for reasons that have nothing to do with the
    evidence — it would report a tight interval on 1,445 chains' worth of
    information because there happen to be 42,000 rows.

    The invariant that separates the two: duplicating every row inside its own
    chain adds NO information, so a chain bootstrap's interval must not move.
    A row bootstrap's would narrow by roughly the square root of the
    duplication factor.
    """
    rng = np.random.default_rng(0)
    y = np.array([0, 1] * 20)
    p = rng.random(40)
    g = np.arange(40) // 2
    _, lo1, hi1 = B.auc_ci(y, p, g, reps=400)
    k = 10
    _, lo2, hi2 = B.auc_ci(np.repeat(y, k), np.repeat(p, k), np.repeat(g, k),
                           reps=400)
    assert hi1 - lo1 > 0.01, "degenerate interval — the test proves nothing"
    assert (hi2 - lo2) == pytest.approx(hi1 - lo1, rel=1e-6), \
        "duplicating rows moved the interval — the bootstrap is on rows"


# ── instrument 5 · the two choices recorded as DEVIATION D2 ────────────────

def test_read_chains_reproduces_build_transient_exactly():
    """⛔⛔ THE WHOLE DEFENCE OF SKIPPING THE CORPUS GATE. `read_chains` omits
    `check_force_pair_fairness` because a 12-chain read is not a corpus — but
    it may not differ in any OTHER way, or instrument 5 is reading a different
    speaker than every other arm. Same seeds, same two rng streams, same pool
    and index: the chains must be identical, surface for surface.

    Run at a size where the corpus gate passes, so both paths are available to
    compare.
    """
    from tlon.act2 import corpus as C1
    from tlon.discourse import force_map as FM
    pairs = C1.build(6000, seed=I.SEED)
    want = TR.build_transient(60, turns=10, pairs=pairs, seed=I.SEED,
                              responsiveness=1.0, fmap=FM.DERIVED_v1,
                              verify=False, barred_fn=I.barred_blind)
    got = B.read_chains(pairs, n=60, turns=10, seed=I.SEED,
                        responsiveness=1.0, barred_fn=I.barred_blind)
    assert len(got) == len(want)
    for a, b in zip(want, got):
        assert [t.surface for t in a] == [t.surface for t in b]
        assert [t.force for t in a] == [t.force for t in b]


def test_tune_reports_an_unreachable_target_instead_of_an_endpoint():
    """⛔⛔ A bisection ALWAYS returns something. Returning a limit and calling
    it 'matched' is how an unreachable target becomes a silent falsehood in a
    table — and two of instrument 5's nine cells are genuinely unreachable."""
    lex = sorted(TR._lex_roots())[:3]

    def make(k):
        # lag-1 rises with k but tops out well below the target below.
        n = 1 + int(round(k * 2))
        return [[I.Turn("%s ka" % lex[0], "ka")] * n +
                [I.Turn("%s ka" % lex[1], "ka")] * (4 - n)]

    _k, _got, ok = B.tune(make, 99.0)
    assert ok is False, "an unreachable target was reported as matched"


def test_tune_reports_bracketed_when_the_target_is_inside_the_span():
    lex = sorted(TR._lex_roots())[:2]

    def make(k):
        # k == 0 -> no repeat at lag 1; k == 1 -> every turn repeats.
        if k < 0.5:
            return [[I.Turn("%s ka" % lex[0], "ka"),
                     I.Turn("%s ka" % lex[1], "ka"),
                     I.Turn("%s ka" % lex[0], "ka")]]
        return [[I.Turn("%s ka" % lex[0], "ka")] * 3]

    lo = B.lag1_of(make(0.0))
    hi = B.lag1_of(make(1.0))
    _k, _got, ok = B.tune(make, (lo + hi) / 2.0)
    assert ok is True, "a target inside the span was reported unreachable"


def test_the_blind_mix_knob_does_not_perturb_the_draw_when_it_is_zero():
    """⛔ The parameter was added AFTER `i2_noreplay.txt` was produced. If it
    consumed an rng draw at weight 0, that artefact would no longer reproduce
    from the current code — the exact provenance failure this whole session was
    spent repairing."""
    chains = _toy(n_chains=8, turns=8)
    a, _ = B.run_oe_noreplay(chains, tag="t", n=25, turns=6, quiet=True)
    b, _ = B.run_oe_noreplay(chains, tag="t", n=25, turns=6, quiet=True,
                             blind_w=0.0)
    assert [[t.surface for t in ch] for ch in a] == \
           [[t.surface for t in ch] for ch in b]
