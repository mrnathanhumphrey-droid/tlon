"""⛔⛔ THE KILL SWITCH'S OWN GUARDS.

This tool decides whether ~$67 is spent. Two ways it could lie, both of which
this arc has already been bitten by in some form:

  · reading only the SURVIVORS, which scores ~100% BY CONSTRUCTION because the
    gate is what put them in that file;
  · certifying a corpus in which the softening was never exercised, which is a
    relabelled copy of a run already paid for and scores identically on every
    rate.
"""
import json
import pathlib
import subprocess
import sys

import pytest

TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import act2_softsteer_carry_check as K            # noqa: E402


@pytest.fixture(autouse=True)
def expanded_lexicon(monkeypatch):
    from tlon.grammar import classes as C
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.load.cache_clear()
    yield
    C.load.cache_clear()


def _scene(root):
    return {"node": {"root": root}}


def _write(tmp_path, survivors, missed):
    (tmp_path / "conversations.jsonl").write_text(
        "".join(json.dumps({"id": "c%d" % i, "turns": [
            {"voice": "P", "scene": _scene(p)},
            {"voice": "T", "scene": _scene(t)}]},
            ensure_ascii=False) + "\n"
            for i, (p, t) in enumerate(survivors)), encoding="utf-8")
    (tmp_path / "scene_gate_missed.jsonl").write_text(
        "".join(json.dumps({"id": "m%d" % i, "turns": [
            {"voice": "P", "scene": _scene(p)},
            {"voice": "T", "scene": _scene(t)}]},
            ensure_ascii=False) + "\n"
            for i, (p, t) in enumerate(missed)), encoding="utf-8")
    return tmp_path


def test_the_denominator_INCLUDES_the_gate_misses(tmp_path):
    """⛔⛔ THE SURVIVORS-ONLY TRAP. If the misses were dropped, a corpus with
    one pass and nine failures would read as 100%.
    """
    from tlon.act2.carry import scene_roots
    from tlon.grammar import classes as C
    roots = frozenset(C.load()["classes"]["R"])
    _write(tmp_path, [("flöx", "pön")], [("flöx", "hlun")] * 9)

    surv = K.pairs_from_survivors(tmp_path / "conversations.jsonl", roots,
                                  scene_roots)
    missed = K.pairs_from_missed(tmp_path / "scene_gate_missed.jsonl", roots,
                                 scene_roots)
    assert len(surv) == 1 and len(missed) == 9


def test_a_corpus_where_the_softening_was_never_exercised_is_REFUSED(tmp_path):
    """⛔⛔ THE RELABELLED-COPY CASE. Every pair carries its EXACT root, so
    every rate looks healthy and the corpus is worth nothing new.
    """
    _write(tmp_path, [("flöx", "flöx"), ("hlun", "hlun")] * 20, [])
    # every reply also adds a root of its own, so carry is perfect
    (tmp_path / "conversations.jsonl").write_text(
        "".join(json.dumps({"id": "c%d" % i, "turns": [
            {"voice": "P", "scene": _scene("flöx")},
            {"voice": "T", "scene": {"node": {"root": "flöx", "edges": [
                {"node": {"root": "hlun"}}]}}}]}) + "\n"
            for i in range(20)), encoding="utf-8")
    rc = subprocess.run(
        [sys.executable, str(TOOLS / "act2_softsteer_carry_check.py"),
         "--run", str(tmp_path)],
        cwd=str(pathlib.Path(__file__).resolve().parents[1]),
        capture_output=True, text=True, encoding="utf-8",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    assert rc.returncode == 1, rc.stdout
    assert "never exercised" in rc.stdout


def test_a_corpus_that_DOES_exercise_the_softening_is_accepted(tmp_path):
    """⛔ Non-vacuity: the stop must not fire on the case it is meant to pass.
    Every reply carries a SIBLING of the prior root plus something outside it.
    """
    (tmp_path / "conversations.jsonl").write_text(
        "".join(json.dumps({"id": "c%d" % i, "turns": [
            {"voice": "P", "scene": _scene("flöx")},
            {"voice": "T", "scene": {"node": {"root": "pön", "edges": [
                {"node": {"root": "hlun"}}]}}}]}) + "\n"
            for i in range(20)), encoding="utf-8")
    (tmp_path / "scene_gate_missed.jsonl").write_text("", encoding="utf-8")
    rc = subprocess.run(
        [sys.executable, str(TOOLS / "act2_softsteer_carry_check.py"),
         "--run", str(tmp_path)],
        cwd=str(pathlib.Path(__file__).resolve().parents[1]),
        capture_output=True, text=True, encoding="utf-8",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    assert rc.returncode == 0, rc.stdout
    assert "SOFTENING EXERCISED" in rc.stdout
    assert "100.0% of pairs" in rc.stdout


def test_an_empty_run_directory_is_REFUSED(tmp_path):
    rc = subprocess.run(
        [sys.executable, str(TOOLS / "act2_softsteer_carry_check.py"),
         "--run", str(tmp_path)],
        cwd=str(pathlib.Path(__file__).resolve().parents[1]),
        capture_output=True, text=True, encoding="utf-8",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    assert rc.returncode != 0
    assert "no P->T pairs" in (rc.stdout + rc.stderr)
