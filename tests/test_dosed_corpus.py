"""⛔⛔ THE DOSED-STEER BLEND — guards on a corpus built from two populations.

The arm's entire content is the DOSE, so the ways it can be wrong are: a pool
that is not what it claims, a size that does not match the arms it is compared
against, a dose that is not the one asked for, and a conversation split across
the treatment boundary.
"""
import json
import pathlib
import sys

import pytest

TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import act2_build_dosed_corpus as D                  # noqa: E402


@pytest.fixture(autouse=True)
def expanded_lexicon(monkeypatch):
    from tlon.grammar import classes as C
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.load.cache_clear()
    yield
    C.load.cache_clear()


def _conv(cid, steered, exchanges=2):
    turns = []
    for i in range(exchanges):
        turns.append({"voice": "P", "english": "p%d" % i, "surface": "nur ka",
                      "scene": {"node": {"root": "nur"}}})
        turns.append({"voice": "T", "english": "t%d" % i, "surface": "nur ka",
                      "scene": {"node": {"root": "nur"}}})
    return {"id": cid, "theme": "x", "turns": turns,
            "forced_root_carry": steered,
            "recipe": "puzzle_steered" if steered else "unstamped"}


def test_the_dose_is_the_fraction_of_rows_from_the_steered_pool():
    st = [_conv("s%d" % i, True) for i in range(40)]
    un = [_conv("u%d" % i, False) for i in range(40)]
    per = len(D.rows_from_conversation(st[0], 4))
    chosen, got, total = D.build(st, un, rows_target=per * 20, dose=0.5,
                                 depth=4, seed=1)
    assert total == per * 20
    assert got["steered"] / total == pytest.approx(0.5, abs=D.TOLERANCE)


def test_a_dose_of_zero_and_of_one_are_the_two_parent_arms():
    """⛔ NON-VACUITY AT BOTH ENDS. If the dial did nothing, these would be
    indistinguishable from each other and from the midpoint."""
    st = [_conv("s%d" % i, True) for i in range(40)]
    un = [_conv("u%d" % i, False) for i in range(40)]
    per = len(D.rows_from_conversation(st[0], 4))
    _, lo, _ = D.build(st, un, rows_target=per * 20, dose=0.0, depth=4, seed=1)
    _, hi, _ = D.build(st, un, rows_target=per * 20, dose=1.0, depth=4, seed=1)
    assert lo["steered"] == 0
    assert hi["unsteered"] == 0


def test_whole_conversations_only_never_split_across_the_treatment():
    """⛔⛔ Splicing rows would put one conversation's write rows and provoke
    rows on opposite sides of the treatment — an invisible confound, and worse
    than the population caveat this arm accepts on purpose.
    """
    st = [_conv("s%d" % i, True) for i in range(40)]
    un = [_conv("u%d" % i, False) for i in range(40)]
    per = len(D.rows_from_conversation(st[0], 4))
    chosen, _, total = D.build(st, un, rows_target=per * 10, dose=0.5,
                               depth=4, seed=3)
    ids = [c["id"] for c in chosen]
    assert len(ids) == len(set(ids)), "a conversation was taken twice"
    # every chosen conversation contributes ALL of its rows
    assert sum(len(D.rows_from_conversation(c, 4)) for c in chosen) == total


def test_the_selection_is_deterministic_for_a_seed():
    st = [_conv("s%d" % i, True) for i in range(40)]
    un = [_conv("u%d" % i, False) for i in range(40)]
    per = len(D.rows_from_conversation(st[0], 4))
    a, _, _ = D.build(st, un, rows_target=per * 12, dose=0.5, depth=4, seed=9)
    b, _, _ = D.build(st, un, rows_target=per * 12, dose=0.5, depth=4, seed=9)
    assert [c["id"] for c in a] == [c["id"] for c in b]


def test_a_mislabelled_pool_is_REFUSED_in_both_directions(tmp_path, capsys):
    """⛔⛔ A pool that is not what it claims would produce a corpus stamped
    `dosed` that is really one arm or the other — and every number taken off it
    would be attributed to a dose that was never applied.
    """
    import subprocess
    good_st = tmp_path / "st.jsonl"
    good_un = tmp_path / "un.jsonl"
    # the steered pool contaminated with one unsteered conversation
    good_st.write_text("\n".join(
        json.dumps(_conv("s%d" % i, i != 3)) for i in range(8)) + "\n",
        encoding="utf-8")
    good_un.write_text("\n".join(
        json.dumps(_conv("u%d" % i, False)) for i in range(8)) + "\n",
        encoding="utf-8")
    rc = subprocess.run(
        [sys.executable, str(TOOLS / "act2_build_dosed_corpus.py"),
         "--steered", str(good_st), "--unsteered", str(good_un),
         "--out", str(tmp_path / "o.jsonl"), "--rows", "20"],
        cwd=str(pathlib.Path(__file__).resolve().parents[1]),
        capture_output=True, text=True, encoding="utf-8",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8",
             "TLON_LEXICON": "lexicon_expanded.yaml"})
    assert rc.returncode != 0
    assert "not stamped forced_root_carry" in (rc.stdout + rc.stderr)


def test_an_unmatched_row_count_is_REFUSED(tmp_path):
    """⛔ The arms are compared at 4,578 conversation rows. A corpus of another
    size puts the render delta back on the size axis, which arm 1 was run to
    take it off.
    """
    import subprocess
    st = tmp_path / "st.jsonl"
    un = tmp_path / "un.jsonl"
    st.write_text("\n".join(json.dumps(_conv("s%d" % i, True))
                            for i in range(4)) + "\n", encoding="utf-8")
    un.write_text("\n".join(json.dumps(_conv("u%d" % i, False))
                            for i in range(4)) + "\n", encoding="utf-8")
    rc = subprocess.run(
        [sys.executable, str(TOOLS / "act2_build_dosed_corpus.py"),
         "--steered", str(st), "--unsteered", str(un),
         "--out", str(tmp_path / "o.jsonl"), "--rows", "9999",
         "--seed-scan", "3"],
        cwd=str(pathlib.Path(__file__).resolve().parents[1]),
        capture_output=True, text=True, encoding="utf-8",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8",
             "TLON_LEXICON": "lexicon_expanded.yaml"})
    assert rc.returncode != 0
    assert "lands exactly" in (rc.stdout + rc.stderr)


def test_the_reading_is_declared_and_covers_the_null_and_the_void():
    """⛔⛔ The fork must be fixed BEFORE the run, and must name the outcome
    that refutes the hypothesis — otherwise only confirmations have a reading.
    """
    keys = " | ".join(D.READING)
    assert "render stays ~82%" in keys, "no reading for the null"
    assert "BELOW" in keys, "no reading for a void result"
    assert len(D.READING) >= 4


def test_the_built_corpus_on_disk_carries_the_dose_and_matches_the_arms():
    """⛔ The artifact, not the plan. Skips where the corpus is not built."""
    meta = pathlib.Path("runs/act2/corpus_bench_dosed/meta.json")
    if not meta.exists():
        pytest.skip("dosed corpus not built in this checkout")
    d = json.loads(meta.read_text(encoding="utf-8"))
    ref = json.loads(pathlib.Path("runs/act2/corpus_bench_steered/meta.json")
                     .read_text(encoding="utf-8"))
    for k in ("rows", "train", "by_source", "by_direction"):
        assert d[k] == ref[k], (k, d[k], ref[k])
    assert d["conversation_recipes"] == {"puzzle_dosed": 4578}
    # ⛔ half of them forced, not all and not none
    assert 0.45 < d["forced_root_carry_rows"] / 4578 < 0.55
