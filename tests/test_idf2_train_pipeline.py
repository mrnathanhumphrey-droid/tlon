"""IDF-2's treatment pipeline — the guards that make `M − C1` the marker.

`PREREG_IDF2_2026_09_26.md`, LOCK `37363296`.

⛔⛔ THE ESTIMAND IS ONE SUBTRACTION AND EVERY ASSERTION HERE PROTECTS IT.
`closes(M) − closes(C1)` is the marker's effect only if the two arms differ in
the marker and in nothing else. Two things nearly broke that before any GPU
time, and both are pinned below: the builder never applied the `held` bar, and
two separate builds produced different row counts because the compute-based mix
solves rows against token cost.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from tlon.discourse import transient as TR              # noqa: E402

SH = ROOT / "tools" / "pipeline_idf2_train.sh"


@pytest.fixture(scope="module")
def script():
    return SH.read_text(encoding="utf-8")


# ── C1 is DERIVED, not rebuilt ─────────────────────────────────────────────

def test_C1_is_derived_from_M_not_built_separately(script):
    """⛔⛔ THE CONFOUND THE CORPUS-DIFF GATE CAUGHT. `--multiturn-fraction` is
    by COMPUTE and rows are solved for, so a marked provoke row costs more
    tokens and the marked build needs FEWER singleturn rows to hit the same
    split — 2,190 vs 2,168 at 80 chains. The arms would have differed in how
    much write/read training they saw."""
    assert "act2_idf2.py unmark" in script
    # ⛔ Exactly ONE corpus is built by the generator; the other is derived.
    assert script.count("act2_build_multiturn.py") == 1, (
        "a second build reintroduces the row-count divergence")


def test_the_corpus_diff_gate_runs_before_any_training(script):
    i_gate = script.index("act2_idf2_corpus_diff.py")
    i_train = script.index("act2_finetune.py")
    assert i_gate < i_train, (
        "the marker-only proof must precede the first GPU-hour of training")


def test_unmark_preserves_every_non_provoke_row(tmp_path):
    """⭐ Behavioural, not structural: the derivation must touch provoke rows
    and nothing else."""
    import act2_idf2 as I
    src = tmp_path / "m"
    src.mkdir()
    rows = [
        {"direction": "provoke", "prompt": "aa bb\n%s cc" % TR.MARKER_PREFIX,
         "surface": "x"},
        {"direction": "write", "prompt": "hello", "surface": "y"},
        {"direction": "read", "prompt": "zz", "surface": "z"},
    ]
    (src / "train.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    (src / "manifest.json").write_text(json.dumps({"recipe": "x"}),
                                       encoding="utf-8")
    out = tmp_path / "c1"
    I.main(["unmark", "--marked", str(src), "--out", str(out)])
    got = [json.loads(l) for l in
           (out / "train.jsonl").read_text(encoding="utf-8").splitlines()]
    assert got[0]["prompt"] == "aa bb", "the marker line must be gone"
    assert got[1]["prompt"] == "hello" and got[2]["prompt"] == "zz"
    assert all(TR.MARKER_PREFIX not in r["prompt"] for r in got)
    # ⛔ The derivation is RECORDED, or the corpus's provenance is "a script ran".
    man = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert man["DERIVED_FROM"] == str(src) and man["marker"] is False


def test_unmark_REFUSES_an_unmarked_corpus(tmp_path):
    """⛔ Pointing it at C1 would silently produce a copy, and the diff gate
    would then compare a corpus with itself and pass."""
    import act2_idf2 as I
    src = tmp_path / "m"
    src.mkdir()
    (src / "train.jsonl").write_text(
        json.dumps({"direction": "provoke", "prompt": "aa bb"}) + "\n",
        encoding="utf-8")
    (src / "manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        I.main(["unmark", "--marked", str(src), "--out", str(tmp_path / "o")])


# ── the diff gate itself ───────────────────────────────────────────────────

def _corpus(d, rows):
    d.mkdir(parents=True, exist_ok=True)
    (d / "train.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n",
        encoding="utf-8")
    return d


def test_the_diff_gate_catches_a_difference_beyond_the_marker(tmp_path):
    """⛔⛔ THE BRANCH THAT SAVES THE ESTIMAND. A target surface that differs
    between the arms is not the marker's effect, and nothing downstream could
    separate the two."""
    import act2_idf2_corpus_diff as D
    m = _corpus(tmp_path / "m", [
        {"direction": "provoke", "prompt": "aa\n%s x" % TR.MARKER_PREFIX,
         "surface": "TARGET_A"}])
    c = _corpus(tmp_path / "c", [
        {"direction": "provoke", "prompt": "aa", "surface": "TARGET_B"}])
    with pytest.raises(SystemExit, match="BEYOND THE MARKER"):
        D.main(["--marked", str(m), "--unmarked", str(c)])


def test_the_diff_gate_catches_a_row_count_difference(tmp_path):
    """⛔ The exact failure it fired on for real, at 2,190 vs 2,168."""
    import act2_idf2_corpus_diff as D
    m = _corpus(tmp_path / "m", [
        {"direction": "provoke", "prompt": "aa\n%s x" % TR.MARKER_PREFIX},
        {"direction": "write", "prompt": "b"}])
    c = _corpus(tmp_path / "c", [{"direction": "provoke", "prompt": "aa"}])
    with pytest.raises(SystemExit, match="ROW COUNT DIFFERS"):
        D.main(["--marked", str(m), "--unmarked", str(c)])


def test_the_diff_gate_passes_a_marker_only_difference(tmp_path):
    import act2_idf2_corpus_diff as D
    m = _corpus(tmp_path / "m", [
        {"direction": "provoke", "prompt": "aa\n%s x" % TR.MARKER_PREFIX,
         "surface": "t"},
        {"direction": "write", "prompt": "b", "surface": "u"}])
    c = _corpus(tmp_path / "c", [
        {"direction": "provoke", "prompt": "aa", "surface": "t"},
        {"direction": "write", "prompt": "b", "surface": "u"}])
    assert D.main(["--marked", str(m), "--unmarked", str(c)]) == 0


# ── the arms, the gates, the ordering ──────────────────────────────────────

def test_each_arm_is_read_with_its_own_marker(script):
    """⛔⛔ M, M-strip and M-shuffle are the SAME WEIGHTS under three markers.
    C1 is read BARE, because C1 never trained with one. A swap here would put
    one arm's numbers under another arm's name."""
    for label, marker, adapter in (
            ("M", "held", "adapter_heldM"),
            ("C1", "none", "adapter_heldC1"),
            ("M-strip", "strip", "adapter_heldM"),
            ("M-shuffle", "shuffle", "adapter_heldM")):
        line = [l for l in script.splitlines()
                if l.startswith("read_arm %s " % label)
                or l.startswith("read_arm %s" % label)]
        assert line, "no read_arm line for %s" % label
        assert marker in line[0], "%s must be read with marker=%s" % (label,
                                                                      marker)
        assert adapter in line[0], "%s must read %s" % (label, adapter)


def test_the_gating_arms_get_five_seeds_and_shuffle_keeps_three(script):
    g = [l for l in script.splitlines() if l.startswith("GATING_SEEDS=")][0]
    d = [l for l in script.splitlines() if l.startswith("DESC_SEEDS=")][0]
    assert len(g.split('"')[1].split()) == 5
    assert len(d.split('"')[1].split()) == 3


def test_step_P_seeds_are_not_reused(script):
    """⛔ Step P read C0 at 20624-20631. Reusing those seeds here would make the
    treatment reads correlated with the gate that certified the design."""
    used = set(range(20624, 20632))
    for line in script.splitlines():
        if line.startswith(("GATING_SEEDS=", "DESC_SEEDS=")):
            for s in line.split('"')[1].split():
                assert int(s) not in used, "seed %s was used by Step P" % s


def test_flocal_and_dose_gate_before_any_read(script):
    """⛔ §4: F-LOCAL must clear before a lag read is interpreted, and an arm
    whose dose is out of band may describe but not decide."""
    assert script.index("act2_flocal.py") < script.index("step reads")
    assert script.index("act2_idf2.py dose") < script.index("step reads")


def test_the_weights_are_persisted_before_the_analysis(script):
    """⛔⛔ `s20620` was lost because persistence waited for the end of a run.
    Two adapters at ~4.5 GPU-h each are not re-derivable from this box."""
    assert script.index("persist --cells") < script.index("tlon_mark_done")


def test_W2_is_absent_rather_than_half_present(script):
    """⛔ Nathan chose (b): M and C1 now, W2 on a later box. A pipeline with a
    W2 label and no W2 row builder would produce an arm that looks read."""
    assert "W2" not in script.replace("# ⛔ W2 IS NOT IN THIS RUN", "").replace(
        "# it — its row shape and reader history do not exist yet.", "") or \
        "NOT IN THIS RUN" in script


def test_the_pipeline_is_allowlisted():
    import act2_retrain_orchestrate as O
    assert "pipeline_idf2_train.sh" in O.PIPELINES
    assert "pipeline_idf2_train.sh" not in O.NEEDS_RECIPE


def test_it_does_not_write_the_done_marker_itself(script):
    assert "touch ~/DONE" not in script
    assert script.index("tlon_persist_run_files") < script.index(
        "tlon_mark_done")
