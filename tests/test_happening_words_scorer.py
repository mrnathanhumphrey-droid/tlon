"""The scorer that builds the carry gate's vocabulary must be DETERMINISTIC.

⛔⛔ THIS FILE EXISTS BECAUSE THE SCORER WAS NOT. `happening_words.json` is the
instrument every carry number in this arc was measured with, and it was built
with `Counter.most_common(1)`, which breaks ties by insertion order. The counts
are accumulated by iterating a `set` of roots, so the order followed
PYTHONHASHSEED: two runs over the same corpus disagreed on 10 of 1110 words,
every one an exact tie, THREE of them above the 0.70 threshold and therefore
inside the live vocabulary. Nothing in the suite noticed, because every run
agreed with itself.
"""
import collections
import pathlib
import subprocess
import sys

import pytest

TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import act2_score_happening_words as S           # noqa: E402


def test_modal_root_breaks_ties_by_name_not_insertion_order():
    """⛔ THE BUG ITSELF. Same counts, opposite insertion order, one answer."""
    a = collections.Counter()
    a["zun"] = 4
    a["flox"] = 4
    b = collections.Counter()
    b["flox"] = 4
    b["zun"] = 4

    assert S.modal_root(a) == S.modal_root(b) == ("flox", 4)
    # and the old implementation is what this pins against
    assert a.most_common(1)[0][0] == "zun"
    assert b.most_common(1)[0][0] == "flox"


def test_modal_root_lets_the_count_decide_first():
    """⛔⛔ NON-VACUITY, AND THE PREDICATE BREAKS BOTH WAYS.

    A fix that sorted by name would pass the tie test and be catastrophically
    wrong: the name is the tie-break, never the criterion. `zun` sorts last and
    must still win when it is the most common.
    """
    counts = collections.Counter({"flox": 3, "aal": 1, "zun": 9})
    assert S.modal_root(counts) == ("zun", 9)


def test_modal_root_is_stable_under_every_permutation():
    counts = {"nur": 5, "flox": 5, "zun": 5, "aal": 2}
    import itertools
    answers = {S.modal_root(collections.Counter(
        {k: counts[k] for k in perm}))
        for perm in itertools.permutations(counts)}
    assert answers == {("flox", 5)}


def test_tally_counts_word_root_cooccurrence():
    turns = [({"dims"}, frozenset({"flox"})),
             ({"dims", "waited"}, frozenset({"flox", "hlun"}))]
    hits, seen = S.tally(turns)
    assert seen["dims"] == 2 and seen["waited"] == 1
    assert hits["dims"]["flox"] == 2
    assert hits["dims"]["hlun"] == 1
    assert hits["waited"]["hlun"] == 1


@pytest.fixture
def borrowed_lexicon(monkeypatch):
    """⛔⛔ `bind_lexicon` IS PROCESS-WIDE AND MUST BE PUT BACK.

    It sets `TLON_LEXICON` in `os.environ` and clears `tlon.grammar.classes`'s
    load cache, so a test that calls it and walks away hands the EXPANDED
    lexicon to whatever runs next. That is exactly what it did: this file went
    green on its own and turned 3 tests in `test_transient.py` red and 8 in
    `test_ki_target_ordering_lock.py` into errors, purely by running before
    them under the suite's random ordering.
    """
    from tlon.grammar import classes as C
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.load.cache_clear()
    yield S.bind_lexicon("lexicon_expanded.yaml")
    C.load.cache_clear()          # monkeypatch restores the var; the cache is
                                  # ours to clear, and it outlives the env var


def test_load_turns_refuses_a_corpus_with_no_scorable_rows(tmp_path,
                                                           borrowed_lexicon):
    """⛔ A surface-only corpus must REFUSE, not contribute silently."""
    p = tmp_path / "surface_only.jsonl"
    p.write_text('{"english": "the sky darkens"}\n', encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        S.load_turns([str(p)], frozenset({"flox"}))
    assert "0 scorable turns" in str(e.value)


def test_scorer_output_does_not_depend_on_the_hash_seed(tmp_path):
    """⛔⛔ THE END-TO-END ARM. The unit tests above pin the tie-break; this
    pins that nothing ELSE in the path reintroduces hash-order dependence.
    Two interpreters, two hash seeds, one vocabulary.
    """
    repo = pathlib.Path(__file__).resolve().parents[1]
    corpus = repo / "runs" / "act2" / "corpus_natural" / "pairs.jsonl"
    if not corpus.exists():
        pytest.skip("corpus_natural is not present in this checkout")

    outs = []
    for seed in ("1", "2"):
        out = tmp_path / ("hw_%s.json" % seed)
        env = {**__import__("os").environ, "PYTHONHASHSEED": seed,
               "PYTHONIOENCODING": "utf-8"}
        subprocess.run(
            [sys.executable, str(TOOLS / "act2_score_happening_words.py"),
             "--corpus", str(corpus), "--out", str(out)],
            cwd=str(repo), env=env, check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        outs.append(out.read_text(encoding="utf-8"))

    import json
    a, b = (json.loads(o)["words"] for o in outs)
    differing = [w for w in set(a) | set(b) if a.get(w) != b.get(w)]
    assert not differing, (
        "the scorer disagreed with itself across hash seeds on %d words: %s"
        % (len(differing), sorted(differing)[:10]))
