"""⛔⛔ THE PERSIST STAGE'S RED-PROOF — the door the s20620 remediation left open.

`tests/test_provision.py` guards the ORCHESTRATOR's terminate path with
`may_terminate`. On 2026-09-04 that gate held perfectly and two boxes were
terminated with work on them anyway, because **the watchdog terminates over the
Lambda API and has no concept of unpersisted work** — two doors out, one gate.

⭐ AND THE WATCHDOG WAS RIGHT BOTH TIMES. `retrain12` finished, wrote `~/DONE`,
and was terminated within one 300 s poll; the gate box died at `manifest` and was
terminated for a dead process. Both boxes were billing for nothing. The defect
was never the eagerness — it was that **`~/DONE` meant COMPUTED while the
collection it implied lived on another machine.**

So the fix under test here is not a third check. It is that the box persists its
own artifacts as a pipeline stage, per adapter, as soon as they exist — after
which terminate-on-DONE is correct and the two systems need not agree about
anything. These tests hold that stage to the same standard as the kill path:
every refusal must FIRE on a fabricated failure and STAY SILENT on a healthy run.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from act2_box_persist import (CELL_FILES, persist_cell,  # noqa: E402
                             read_ledger, restored_files, solo_logs,
                             tar_solo, unpersisted)
from act2_provision import TransferError  # noqa: E402

CELL = "ct-s20624"
SOLO_N = 14


def fake_push(name, path, repo, *, private=True, subdir=None):
    """A push that succeeds. ⛔ Returns a URI, because the code under test is
    supposed to check for one."""
    return "hf://%s/%s/%s" % (repo, subdir or name, pathlib.Path(path).name)


def build(tmp_path, *, cell=CELL, files=CELL_FILES, n_solo=SOLO_N):
    """A HEALTHY run tree. Each test perturbs exactly one thing, so a test that
    fires proves the thing it changed is what fired it."""
    d = tmp_path / ("adapter_%s" % cell)
    d.mkdir(parents=True)
    for fn in files:
        (d / fn).write_bytes(b"weights-or-json-for-%s" % fn.encode())
    logs = tmp_path / "logs"
    logs.mkdir(exist_ok=True)
    for i in range(1, n_solo + 1):
        (logs / ("%s_solo_%d.json" % (cell, i))).write_text(
            json.dumps({"turn": i}), encoding="utf-8")
    # ⭐ The corpus manifest is part of a HEALTHY cell now — the gap the gate run
    # found. It is required, so the healthy fixture must supply it or every
    # refusal below would fire for the wrong reason.
    cdir = tmp_path / ("corpus_%s" % cell)
    cdir.mkdir(exist_ok=True)
    (cdir / "manifest.json").write_text(
        json.dumps({"recipe": "content-transient",
                    "recipe_suppression_window": 0}), encoding="utf-8")
    return tmp_path


def cmanifest(tmp_path, cell=CELL):
    return tmp_path / ("corpus_%s" % cell) / "manifest.json"


# ── 1 · the healthy case, first ─────────────────────────────────────────────

def test_a_COMPLETE_cell_persists_and_the_ledger_records_every_file(tmp_path):
    """⛔ Prove the stage can succeed before trusting any refusal it makes."""
    build(tmp_path)
    e = persist_cell(tmp_path, CELL, "r/x", solo_n=SOLO_N, corpus_manifest=cmanifest(tmp_path), push=fake_push)
    assert e["solo_n"] == SOLO_N
    for fn in CELL_FILES:
        assert e["files"][fn]["uri"], fn
    assert "%s_solo_logs.tar.gz" % CELL in e["files"]
    assert read_ledger(tmp_path)[CELL]["files"] == e["files"]


# ── 2 · an incomplete cell must never reach durable storage ─────────────────

@pytest.mark.parametrize("drop", CELL_FILES)
def test_a_cell_MISSING_ANY_REQUIRED_FILE_is_REFUSED(tmp_path, drop):
    """⛔⛔ A PARTIAL ADAPTER IN DURABLE STORAGE IS WORSE THAN NONE — it reads as
    saved. ⭐ `factorial.json` is in the required set on purpose: an adapter that
    survives without its cell label is an adapter in no cell of the factorial,
    and the matrix is rebuilt from exactly those labels once the scrollback is
    gone."""
    build(tmp_path, files=[f for f in CELL_FILES if f != drop])
    with pytest.raises(TransferError, match=drop):
        persist_cell(tmp_path, CELL, "r/x", solo_n=SOLO_N, corpus_manifest=cmanifest(tmp_path), push=fake_push)


def test_a_SHORT_solo_set_is_REFUSED(tmp_path):
    """The frozen ruler is computed over the full set. A short set persisted
    without complaint enters the population as if it were complete."""
    build(tmp_path, n_solo=SOLO_N - 1)
    with pytest.raises(TransferError, match="13"):
        persist_cell(tmp_path, CELL, "r/x", solo_n=SOLO_N, corpus_manifest=cmanifest(tmp_path), push=fake_push)


def test_an_OVERLONG_solo_set_is_REFUSED_too(tmp_path):
    """⛔ Not `< solo_n`. Extra transcripts mean a re-run wrote into the same
    tree, and which 14 of the 15 enter the ruler would be decided by a glob."""
    build(tmp_path, n_solo=SOLO_N + 1)
    with pytest.raises(TransferError):
        persist_cell(tmp_path, CELL, "r/x", solo_n=SOLO_N, corpus_manifest=cmanifest(tmp_path), push=fake_push)


# ── 3 · ⛔⛔ THE DEFECT THAT KILLED THE GATE BOX ────────────────────────────

def test_the_transcript_count_is_a_PARAMETER_not_a_batch_size(tmp_path):
    """⛔⛔ `assert len(out) == 6` in the pipeline's `manifest` stage is what
    killed the ct-gate box: a count correct for exactly one run and silently
    wrong for a gate run that trains ONE adapter to test an assumption before
    the batch is bought.

    ⭐ The same shape had been fixed in `act2_retrain_orchestrate.py` ninety
    minutes earlier and no sweep was done for siblings. SWEEP FOR THE CLASS.
    """
    build(tmp_path, n_solo=3)
    e = persist_cell(tmp_path, CELL, "r/x", solo_n=3, corpus_manifest=cmanifest(tmp_path), push=fake_push)
    assert e["solo_n"] == 3


def test_the_module_contains_no_hardcoded_batch_size():
    """⛔⛔ CODE ONLY, AND STRIPPING `#` LINES IS NOT ENOUGH.

    The first version of this fired on this module's own DOCSTRING, which quotes
    `assert len(out) == 6` while explaining why that line was the defect — a
    guard that cannot tell an explanation from the thing it explains. The same
    trap caught `test_the_solo_completeness_check_is_DERIVED_from_the_manifest`,
    which strips comments and would still be fooled by a docstring. ⭐ Parse it.
    """
    import ast
    tree = ast.parse((ROOT / "tools/act2_box_persist.py").read_text("utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and ast.get_docstring(node):
            node.body = node.body[1:]
    code = ast.unparse(tree)
    for literal in ("solo_n=14", "== 14", "== 6", "len(out) == 6"):
        assert literal not in code, literal


# ── 4 · assert the mutation, not the call ──────────────────────────────────

def test_a_push_that_returns_NOTHING_is_a_FAILURE_not_a_record(tmp_path):
    """⛔⛔ A silent no-op and a silent success are the same observation. A push
    that quietly returned None would leave a ledger entry that still READS as a
    record of success, and the next run would skip re-uploading it."""
    build(tmp_path)
    with pytest.raises(TransferError, match="no durable URI"):
        persist_cell(tmp_path, CELL, "r/x", solo_n=SOLO_N, corpus_manifest=cmanifest(tmp_path),
                     push=lambda *a, **k: None)


def test_a_push_that_RAISES_leaves_no_ledger_entry(tmp_path):
    """⛔ A failed persist must not be recorded as one that happened — the
    ledger is what `verify` consults before `~/DONE` is written."""
    build(tmp_path)

    def boom(*a, **k):
        raise TransferError("hub rejected the upload")

    with pytest.raises(TransferError):
        persist_cell(tmp_path, CELL, "r/x", solo_n=SOLO_N, corpus_manifest=cmanifest(tmp_path), push=boom)
    assert CELL not in read_ledger(tmp_path)


# ── 5 · the ledger cannot certify itself ───────────────────────────────────

def test_unpersisted_is_EMPTY_after_a_real_persist(tmp_path):
    build(tmp_path)
    persist_cell(tmp_path, CELL, "r/x", solo_n=SOLO_N, corpus_manifest=cmanifest(tmp_path), push=fake_push)
    assert unpersisted(tmp_path, [CELL]) == []


def test_a_cell_that_was_never_persisted_is_REPORTED(tmp_path):
    build(tmp_path)
    assert unpersisted(tmp_path, [CELL]) == [CELL]


def test_a_HALF_WRITTEN_ledger_entry_does_NOT_count_as_persisted(tmp_path):
    """⛔⛔ MEMBERSHIP IS NOT ENOUGH. Checking `cell in ledger` lets an entry
    whose weights failed to upload certify itself on the strength of its own
    key."""
    build(tmp_path)
    persist_cell(tmp_path, CELL, "r/x", solo_n=SOLO_N, corpus_manifest=cmanifest(tmp_path), push=fake_push)
    led = read_ledger(tmp_path)
    led[CELL]["files"]["adapter_model.safetensors"]["uri"] = None
    (tmp_path / "persist_ledger.json").write_text(json.dumps(led),
                                                  encoding="utf-8")
    assert unpersisted(tmp_path, [CELL]) == [CELL]


def test_verify_REFUSES_AN_EMPTY_CELL_LIST(tmp_path):
    """⛔⛔ THE VACUOUS PASS, AGAIN. `all([])` is True, so the obvious `verify`
    certifies a run whose seed list failed to expand — and `~/DONE` is written
    on the strength of it. Same trap `may_terminate` refuses on an empty
    ledger."""
    import subprocess
    r = subprocess.run([sys.executable, str(ROOT / "tools/act2_box_persist.py"),
                        "--root", str(tmp_path), "verify", "--cells", "   "],
                       capture_output=True, text=True)
    assert r.returncode != 0
    assert "empty run" in (r.stdout + r.stderr)


def test_verify_REFUSES_when_a_named_cell_is_absent(tmp_path):
    import subprocess
    build(tmp_path)
    persist_cell(tmp_path, CELL, "r/x", solo_n=SOLO_N, corpus_manifest=cmanifest(tmp_path), push=fake_push)
    r = subprocess.run([sys.executable, str(ROOT / "tools/act2_box_persist.py"),
                        "--root", str(tmp_path), "verify",
                        "--cells", "%s cf-s20624" % CELL],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "cf-s20624" in (r.stdout + r.stderr)


# ── 6 · the archive ────────────────────────────────────────────────────────

def test_the_archive_holds_THIS_cells_transcripts_and_no_others(tmp_path):
    """⛔ A glob that caught a neighbouring cell's logs would put one arm's
    transcripts into the other arm's durable copy — a factorial mislabelled at
    the only place the label survives."""
    build(tmp_path)
    build(tmp_path, cell="cf-s20624")
    import tarfile
    t = tar_solo(tmp_path, CELL, tmp_path / "t.tar.gz")
    with tarfile.open(t) as tf:
        names = tf.getnames()
    assert len(names) == SOLO_N
    assert all(n.startswith(CELL + "_solo_") for n in names)
    assert len(solo_logs(tmp_path, "cf-s20624")) == SOLO_N


def test_the_archive_is_DETERMINISTIC(tmp_path):
    """⭐ Byte-identical across builds, so re-running the stage is a VERIFIED
    SKIP rather than a second upload. Without zeroed mtimes the sha changes
    every run and `already_persisted` never fires."""
    from act2_provision import sha256_local
    build(tmp_path)
    a = sha256_local(tar_solo(tmp_path, CELL, tmp_path / "a.tar.gz"))
    b = sha256_local(tar_solo(tmp_path, CELL, tmp_path / "b.tar.gz"))
    assert a == b


# ── 7 · ⛔⛔ THE STRUCTURAL CLAIM: ~/DONE MEANS PERSISTED ──────────────────

def self_terminating_pipelines():
    """⭐ THE GUARD DISCOVERS ITS OWN CLASS MEMBERS.

    Naming `pipeline_retrain.sh` here would be the instance, not the class — and
    the lesson of 2026-09-04 is that both losses were classes already met and
    fixed in ONE place. Any pipeline that arms the watchdog is a pipeline that
    terminates its own box, so a new one is held to this the day it is written.
    """
    return [p for p in sorted((ROOT / "tools").glob("pipeline_*.sh"))
            if "act2_watchdog" in p.read_text(encoding="utf-8")]


def test_there_are_self_terminating_pipelines_to_check():
    """⛔ Non-vacuity. If the discovery ever returns nothing, every test below
    passes over an empty list and proves nothing at all."""
    assert len(self_terminating_pipelines()) >= 2


@pytest.mark.parametrize("p", self_terminating_pipelines(), ids=lambda p: p.name)
def test_a_self_terminating_pipeline_writes_DONE_only_AFTER_persisting(p):
    """⛔⛔ THIS IS THE WHOLE FIX, AND IT IS AN ORDERING CLAIM.

    The watchdog terminates within one poll of seeing `~/DONE` — correctly, since
    a finished run that keeps billing is pure waste. So the marker must mean
    PERSISTED. If a later edit moves `touch ~/DONE` above the persist stage, the
    five-minute window that took 84 solo transcripts silently reopens and nothing
    else in this suite would notice.
    """
    src = p.read_text(encoding="utf-8")
    assert "act2_box_persist.py" in src, (
        "%s terminates its own box but never persists — `~/DONE` would mean "
        "COMPUTED, and the only copy of the work would be on a box that is "
        "already ending itself" % p.name)
    assert src.index("act2_box_persist.py") < src.index("touch ~/DONE")


@pytest.mark.parametrize("p", self_terminating_pipelines(), ids=lambda p: p.name)
def test_a_self_terminating_pipeline_flushes_before_it_is_killed(p):
    """⛔ The persist stage covers the SUCCESS path. A box killed for a stall or
    a dead process never reaches it, and its run log — the record of WHY — is
    the one artifact re-running cannot regenerate."""
    assert "--flush-cmd" in p.read_text(encoding="utf-8")


def test_the_retrain_pipeline_persists_INSIDE_the_loop():
    """⛔⛔ AN END-OF-RUN PERSIST STAGE WOULD STILL HAVE LOST THE GATE ADAPTER.

    It died at `manifest`, which sits BETWEEN the last adapter and the end, with
    a trained and F-LOCAL-cleared adapter on disk. Work has to become durable as
    soon as it exists, not when the run is pleased with itself.
    """
    src = (ROOT / "tools/pipeline_retrain.sh").read_text(encoding="utf-8")
    assert src.index("step persist_$CELL") < src.index("step manifest")
    assert src.index("step verify_persisted") < src.index("touch ~/DONE")


def test_the_pipelines_manifest_count_is_DERIVED_not_a_batch_size():
    """⛔⛔ THE LINE THAT KILLED THE GATE BOX, and its quieter twin: the glob
    `adapter_s*` matched NOTHING once the cell went into the directory name
    (`adapter_ct-s20624`), so the manifest was empty for every run under the new
    naming — not only the single-adapter one."""
    src = (ROOT / "tools/pipeline_retrain.sh").read_text(encoding="utf-8")
    code = "\n".join(l for l in src.splitlines()
                     if not l.lstrip().startswith("#"))
    assert "expected 6 adapters" not in code
    assert "len(out) == 6" not in code
    assert 'glob("adapter_s*")' not in code
    assert 'glob("adapter_*")' in code


# ── 8 · the generic tree archive (the transcript-only pipelines) ───────────

def test_an_EMPTY_tree_is_REFUSED(tmp_path):
    """⛔⛔ AN ARCHIVE OF NOTHING UPLOADS SUCCESSFULLY, and a successful upload of
    nothing is the most convincing form of a lost run — the same shape as the
    `scp -r` that made a directory, moved no file, and said nothing."""
    import subprocess
    (tmp_path / "logs").mkdir()
    r = subprocess.run([sys.executable, str(ROOT / "tools/act2_box_persist.py"),
                        "--root", str(tmp_path), "tree", "--dir", "logs",
                        "--name", "x"], capture_output=True, text=True)
    assert r.returncode != 0 and "empty archive" in (r.stdout + r.stderr)


def test_the_tree_archive_is_DETERMINISTIC_and_complete(tmp_path):
    import tarfile
    from act2_box_persist import tar_tree
    from act2_provision import sha256_local
    d = tmp_path / "logs"
    d.mkdir()
    for i in range(5):
        (d / ("r_%d.json" % i)).write_text('{"i": %d}' % i, encoding="utf-8")
    (d / "notes.txt").write_text("ignored", encoding="utf-8")
    a, n = tar_tree(d, tmp_path / "a.tar.gz")
    b, _ = tar_tree(d, tmp_path / "b.tar.gz")
    assert n == 5
    assert sha256_local(a) == sha256_local(b)
    with tarfile.open(a) as tf:
        assert sorted(tf.getnames()) == ["r_%d.json" % i for i in range(5)]


@pytest.mark.parametrize("p", self_terminating_pipelines(), ids=lambda p: p.name)
def test_a_self_terminating_pipeline_never_APPENDS_to_another_runs_log(p):
    """⛔⛔ SOME RUN LOGS ARE COMMITTED, so a fresh clone arrives holding a
    previous run's file and every `tee -a` writes into it.

    The gate box did exactly that on 2026-09-04: its log opened with a stage line
    from the run that DIED, an hour before that box existed. Nothing is lost that
    way — but two runs share one record, and a reader can attribute one run's
    numbers to the other. That is caveat decay with the caveat simply absent, and
    these pipelines PERSIST their logs, so the merged file is what survives.

    ⭐ Rotate rather than delete: the old record is still somebody's evidence.
    """
    src = p.read_text(encoding="utf-8")
    assert '.prev' in src and 'mv "$LOG"' in src, (
        "%s appends to whatever log is already there" % p.name)
    # ⛔ Before anything WRITES, or the rotation moves a file this run has
    # already appended to. ⛔⛔ NOT "before the first `tee -a`" — that landmark is
    # inside the EXIT trap at the top of every one of these files, which fires
    # at exit rather than where it is written. A source-order guard has to
    # anchor on something whose position means what it looks like; `step()` is
    # the first thing that actually emits.
    assert src.index('mv "$LOG"') < src.index("step() {")


# ── 9 · the recovery path's own emptiness guard ────────────────────────────

def test_restored_files_EXCLUDES_the_hubs_own_bookkeeping(tmp_path):
    """⛔⛔ A GUARD THAT IS RIGHT BY COINCIDENCE IS NOT A GUARD.

    `snapshot_download(local_dir=...)` writes `.cache/huggingface/` entries of
    its own. A real restore of 5 tarballs reported "12 files". Today a zero-match
    pattern happens to write no cache either, so the emptiness check fires — but
    because of how the library behaves this week, not because of anything the
    code checks. ⭐ The recovery path is the whole point of persist-before-DONE;
    it cannot rest on a coincidence.
    """
    (tmp_path / ".cache/huggingface/download/solo_regen").mkdir(parents=True)
    (tmp_path / ".cache/huggingface/.gitignore").write_text("*", encoding="utf-8")
    (tmp_path / ".cache/huggingface/CACHEDIR.TAG").write_text("x", encoding="utf-8")
    (tmp_path / ".cache/huggingface/download/solo_regen/a.tar.gz.metadata"
     ).write_text("m", encoding="utf-8")
    assert restored_files(tmp_path) == [], (
        "a restore that produced ONLY hub bookkeeping must read as empty")

    (tmp_path / "solo_regen").mkdir()
    (tmp_path / "solo_regen/a.tar.gz").write_bytes(b"real")
    assert restored_files(tmp_path) == ["solo_regen/a.tar.gz"]


def test_restored_files_reports_paths_not_bare_names(tmp_path):
    """⛔ Two builds can hold a same-named file. A bare-name listing would show
    the same line twice and read as a duplicate rather than as two artifacts."""
    for cell in ("ct-s20624", "cf-s20624"):
        (tmp_path / cell).mkdir(parents=True)
        (tmp_path / cell / "adapter_config.json").write_text("{}", encoding="utf-8")
    assert restored_files(tmp_path) == ["cf-s20624/adapter_config.json",
                                        "ct-s20624/adapter_config.json"]


# ── 10 · the corpus manifest is REQUIRED (the gap the gate run found) ───────

def test_a_MISSING_corpus_manifest_is_REFUSED(tmp_path):
    """⛔⛔ THE GATE RUN PERSISTED EVERYTHING EXCEPT THIS. Weights, config, cell
    label, transcripts and the run log all went to the hub; the corpus manifest
    — which carries the recipe lag profile the model is COMPARED AGAINST — did
    not. It was noticed with the box already terminating and the pull returned
    0 bytes.

    ⭐ It was recoverable that time by deterministic rebuild plus a sha check,
    and rebuild-plus-sha is a fine RECOVERY but a bad PLAN: it works only while
    the corpus is deterministic and only while its sha was written down. So the
    manifest is a required argument with no default, and its absence refuses.
    """
    build(tmp_path)
    with pytest.raises(TransferError, match="corpus manifest"):
        persist_cell(tmp_path, CELL, "r/x", solo_n=SOLO_N,
                     corpus_manifest=tmp_path / "nope.json", push=fake_push)


def test_the_corpus_manifest_is_in_the_REQUIRED_set_verify_checks(tmp_path):
    """⛔ Persisting it is not enough — `verify` gates `~/DONE`, so the manifest
    must be one of the files it demands. An entry whose corpus provenance failed
    to upload must not certify the run."""
    from act2_box_persist import CORPUS_MANIFEST, REQUIRED_PERSISTED
    assert CORPUS_MANIFEST in REQUIRED_PERSISTED
    build(tmp_path)
    persist_cell(tmp_path, CELL, "r/x", solo_n=SOLO_N,
                 corpus_manifest=cmanifest(tmp_path), push=fake_push)
    assert unpersisted(tmp_path, [CELL]) == []
    led = read_ledger(tmp_path)
    led[CELL]["files"][CORPUS_MANIFEST]["uri"] = None
    (tmp_path / "persist_ledger.json").write_text(json.dumps(led),
                                                  encoding="utf-8")
    assert unpersisted(tmp_path, [CELL]) == [CELL]


def test_the_corpus_manifest_is_stored_under_a_NON_COLLIDING_name(tmp_path):
    """⛔⛔ Both files are called `manifest.json` — the corpus one and the run's
    ADAPTER manifest. `push_durable` derives its destination from the source
    filename, so pushing the corpus manifest as-is would put two different
    manifests under one name in one prefix, and the one overwritten would be the
    provenance."""
    build(tmp_path)
    e = persist_cell(tmp_path, CELL, "r/x", solo_n=SOLO_N,
                     corpus_manifest=cmanifest(tmp_path), push=fake_push)
    from act2_box_persist import CORPUS_MANIFEST
    assert CORPUS_MANIFEST in e["files"]
    assert "manifest.json" not in [k for k in e["files"] if k != CORPUS_MANIFEST]
    assert e["files"][CORPUS_MANIFEST]["uri"].endswith(
        "%s_corpus_manifest.json" % CELL)
