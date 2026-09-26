"""⛔⛔ RED-PROOF FOR THE IDF-1 INSTRUMENTS — the ones that had no file.

IDF-1's Step 1 AUCs and its O-A/O-B/O-C/O-E lag profiles were cited in a locked
prereg and produced by heredocs that no longer existed anywhere on disk. This
suite exists so that cannot happen twice: the instruments are importable, they
import the shared statistic instead of re-spelling it, and the featuriser can
be shown to read nothing but the surface it is handed.
"""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

import act2_idf1 as I  # noqa: E402

from tlon.discourse import transient as TR  # noqa: E402


def test_the_module_does_NOT_define_its_own_lag_statistic():
    """⛔ A second definition, even an identical one, is a second thing to
    drift. IDF-1b's guards say "same imported instrument"; this is what makes
    that claim checkable rather than a note in a document."""
    src = pathlib.Path(I.__file__).read_text(encoding="utf-8")
    for banned in ("def lag_profile", "def permutation_null",
                   "def resolving_power", "def check_transience"):
        assert banned not in src, \
            "act2_idf1 re-spells %s instead of importing it" % banned


def test_scoring_calls_the_shared_functions():
    """The identity, not just the absence of a redefinition."""
    assert I.TR.lag_profile is TR.lag_profile
    assert I.TR.permutation_null is TR.permutation_null
    assert I.TR.resolving_power is TR.resolving_power


def test_an_OE_Turn_duck_types_for_the_instrument():
    """⭐ O-E walks bare surfaces, so its turns are not TTurns. The shared
    functions read only `.surface` — proven here, not assumed."""
    lex_r = {"fang", "flux"}
    chain = [[I.Turn("fang ka", "ka"), I.Turn("flux ki", "ki"),
              I.Turn("fang ko", "ko")]]
    prof = TR.lag_profile(chain, max_lag=2, lex_r=lex_r)
    assert prof[2] == pytest.approx(1.0), \
        "the lag-2 repeat of `fang` was not seen through the namedtuple"


# ── the featuriser reads the surface and nothing else ──────────────────────

def _some_roots():
    roots = sorted(TR._lex_roots())
    assert len(roots) >= 3
    return roots[:3]


def test_features_depend_only_on_the_surface_and_force():
    """⛔⛔ THE LEAK THIS PROBE WOULD DIE OF. If anything about the chain — its
    position, its inherited set, its successor — reached the feature vector,
    Step 1's AUC would measure the leak instead of window-1 identifiability.
    The function's whole signature is (surface, force), so the only way to
    show it is to hand it the same pair from two different worlds."""
    a, b, c = _some_roots()
    surface = "%s %s %s ka" % (a, b, c)
    M1, r1 = I.featurise_turn(surface, "ka")
    M2, r2 = I.featurise_turn(surface, "ka")
    assert r1 == r2 == [a, b, c]
    assert np.array_equal(M1, M2)


def test_the_force_actually_moves_a_feature():
    """A featuriser that silently ignored an input would pass the test above
    for the wrong reason."""
    a, b, _ = _some_roots()
    M1, _ = I.featurise_turn("%s %s ka" % (a, b), "ka")
    M2, _ = I.featurise_turn("%s %s ka" % (a, b), "ki")
    assert not np.array_equal(M1, M2)


def test_root_identity_is_not_encoded_twice():
    """⭐ The co-occurrence block has SELF removed. Without that, root identity
    appears in two blocks and they stop being separable features."""
    a, b, _ = _some_roots()
    M, roots = I.featurise_turn("%s %s ka" % (a, b), "ka")
    for p, r in enumerate(roots):
        assert M[p, I.R + I.RIDX[r]] == 0.0, \
            "root %s is set in its own co-occurrence slot" % r


def test_a_surface_with_no_roots_is_refused_not_zero_filled():
    """⛔ A failed featurisation returns None. A zero row would be a fabricated
    observation — the same shape as recording a failed fetch as 0."""
    M, roots = I.featurise_turn("ka", "ka")
    assert M is None and roots == []


def test_featurise_drops_turns_with_an_empty_inherited_set():
    """There is no label to predict on those turns. Keeping them would pad the
    negative class with rows the question was never asked of."""
    a, b, _ = _some_roots()
    surf = "%s %s ka" % (a, b)
    chains = [[(surf, "ka", []), (surf, "ka", [a])]]
    X, y, g = I.featurise(chains)
    assert len(y) == 2, "expected the 2 roots of the ONE labelled turn"
    assert list(y) == [1, 0]
    assert set(g) == {0}


def test_groups_are_chain_indices_so_the_split_is_by_chain():
    """⛔ A row-level split leaks chain identity. `groups` is what prevents it,
    so it has to be the chain index and nothing else."""
    a, b, _ = _some_roots()
    surf = "%s %s ka" % (a, b)
    chains = [[(surf, "ka", [a])], [(surf, "ka", [b])], [(surf, "ka", [a])]]
    _, _, g = I.featurise(chains)
    assert list(g) == [0, 0, 1, 1, 2, 2]


# ── the oracle controls are what they are documented to be ─────────────────

class _Prev:
    def __init__(self, surface, force, inherited):
        self.surface, self.force = surface, force
        self.inherited = frozenset(inherited)


def test_O_A_bars_nothing_and_O_C_bars_the_truth():
    """The two red-proofs. O-A must reproduce dose −1 and O-C dose 0; if these
    two are not the empty set and the true set, nothing downstream is read."""
    a, b, _ = _some_roots()
    prev = _Prev("%s %s ka" % (a, b), "ka", {a})
    assert I.barred_blind(None, prev, None) == frozenset()
    assert I.barred_true(None, prev, None) == frozenset({a})


def test_the_threshold_oracle_never_degenerates_to_blind():
    """⛔ With a threshold no root clears, a naive implementation returns the
    empty set — which is O-A wearing O-B's label, on an unknown subset of
    turns. It must fall back to the argmax instead."""
    a, b, _ = _some_roots()

    class _Clf:
        def predict_proba(self, M):
            p = np.linspace(0.01, 0.02, len(M))
            return np.column_stack([1 - p, p])

    fn = I.barred_threshold(_Clf(), 0.99)
    got = fn(None, _Prev("%s %s ka" % (a, b), "ka", set()), None)
    assert len(got) == 1, "a threshold nothing clears collapsed O-B into O-A"


def test_transitions_of_pairs_consecutive_turns_within_a_chain():
    """⛔ A transition list that ran across the chain boundary would hand O-E
    pairs that never happened — fabricated evidence for the kernel."""
    chains = [[("s1", "ka", []), ("s2", "ka", [])],
              [("s3", "ka", []), ("s4", "ka", [])]]
    assert I.transitions_of(chains) == [("s1", "s2"), ("s3", "s4")]


def test_the_train_cut_is_a_chain_count_not_a_row_count():
    assert I.TRAIN_CUT == 1011
    assert I.TRAIN_CUT < I.N_CHAINS
