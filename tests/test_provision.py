"""⛔⛔ THE PROVISIONER'S RED-PROOF — the tooling whose absence lost an adapter.

`s20620` existed only on a Lambda box. The runbook's recovery step was
`scp -r ubuntu@box:~/tlon/runs/act2/adapter runs/act2/`, and
**`runs/act2/adapter/` on this machine is an empty directory created 2026-08-24
and never populated.** The copy produced a directory and no file, said nothing,
and the box was terminated. The adapter is unrecoverable: not in git (weights are
gitignored, so it was never committed to lose), not on HF, not on any disk here.

⭐ THE LESSON IS NOT "BE CAREFUL WITH scp". It is that **a transfer with no
verification and a termination with no persistence gate will eventually lose
something**, and that the loss is silent — an empty directory and a directory
that was never asked for look identical afterwards.

So this module's guards are:

  1. **verify a transfer by checksum on BOTH ends** — a truncated or empty
     arrival must fail loudly, before anything downstream consumes it;
  2. **refuse to terminate** while any artifact is not confirmed local AND
     confirmed in durable storage.

Each is red-proofed to FIRE on a fabricated version of its failure and to stay
silent on a healthy one. ⛔ A gate that has never refused in testing is
unexecuted code standing between you and a permanent loss.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))

from act2_provision import (TransferError, may_terminate,  # noqa: E402
                            verify_checksum, verify_pulled_set)

OK = "c1c6d9c2b2ad5aa16a2c0e5c2ce6d67c"
OTHER = "71faf13540101bf4f57222eb2bc0cb47"


# ── 1 · checksum verification, both directions ──────────────────────────────

def test_a_matching_checksum_passes():
    """⛔ First prove the gate does not fire on the healthy case, or every later
    'it fired' means nothing."""
    verify_checksum("s20624", local=OK, remote=OK)


def test_a_MISMATCHED_checksum_RAISES():
    with pytest.raises(TransferError, match="s20624"):
        verify_checksum("s20624", local=OK, remote=OTHER)


def test_a_MISSING_remote_checksum_RAISES_rather_than_passing():
    """⛔⛔ THE VACUOUS-PASS TRAP. `None == None` is true, so a comparison of two
    absent checksums would 'verify' a transfer that never happened."""
    with pytest.raises(TransferError):
        verify_checksum("s20624", local=None, remote=None)
    with pytest.raises(TransferError):
        verify_checksum("s20624", local=OK, remote=None)
    with pytest.raises(TransferError):
        verify_checksum("s20624", local=None, remote=OK)


def test_an_EMPTY_string_checksum_is_not_a_checksum():
    with pytest.raises(TransferError):
        verify_checksum("s20624", local="", remote="")


# ── 2 · ⛔⛔ THE EXACT FAILURE THAT LOST s20620 ─────────────────────────────

def test_an_EMPTY_pulled_directory_is_REFUSED():
    """⛔⛔ THIS IS HOW s20620 DIED. `scp -r` created the directory and copied no
    file; nothing raised; the box was terminated. Set comparison, not existence
    of a folder."""
    with pytest.raises(TransferError, match="s20620"):
        verify_pulled_set(expected=["s20620"], found=[])


def test_a_PARTIAL_pull_names_the_ones_that_are_missing():
    """A pull that got 5 of 7 must say WHICH two — 'some failed' sends you
    hunting, and the box is on a meter."""
    with pytest.raises(TransferError) as e:
        verify_pulled_set(expected=["a", "b", "c"], found=["a", "c"])
    assert "b" in str(e.value)


def test_a_COMPLETE_pull_passes():
    verify_pulled_set(expected=["a", "b"], found=["b", "a"])


def test_an_UNEXPECTED_extra_artifact_is_reported_not_ignored():
    """⛔ Something arrived that was not asked for — a stale adapter from a prior
    run would silently enter the population and change the ruler."""
    with pytest.raises(TransferError, match="unexpected"):
        verify_pulled_set(expected=["a"], found=["a", "b"])


# ── 3 · the persist-before-terminate gate ──────────────────────────────────

def rec(name, *, local=OK, box=OK, durable="hf://keyzersoze04/tlon-adapters/x"):
    return {"name": name, "local_md5": local, "box_md5": box,
            "durable_uri": durable}


def test_terminate_is_ALLOWED_when_every_adapter_is_verified_and_persisted():
    """⛔ Non-vacuity: the gate must be able to say yes, or it is not a gate,
    it is a wall."""
    ok, why = may_terminate([rec("s20624"), rec("s20625")])
    assert ok is True, why


def test_terminate_is_REFUSED_when_an_adapter_never_reached_this_machine():
    ok, why = may_terminate([rec("s20624"), rec("s20625", local=None)])
    assert ok is False and "s20625" in why


def test_terminate_is_REFUSED_on_a_CHECKSUM_MISMATCH():
    ok, why = may_terminate([rec("s20624", local=OTHER)])
    assert ok is False and "s20624" in why


def test_terminate_is_REFUSED_when_an_adapter_is_NOT_IN_DURABLE_STORAGE():
    """⛔⛔ VERIFIED-LOCAL IS NOT ENOUGH. A file that exists only on this laptop
    is one disk failure from the same loss. No artifact may exist solely on a
    live box — and 'solely on one machine' is the same class of exposure."""
    ok, why = may_terminate([rec("s20624", durable=None)])
    assert ok is False and "durable" in why.lower()


def test_terminate_is_REFUSED_on_an_EMPTY_record_list():
    """⛔⛔ THE MOST DANGEROUS VACUOUS PASS. `all([])` is True, so a gate written
    the obvious way would permit termination when NOTHING was tracked — the
    exact state in which s20620 was lost."""
    ok, why = may_terminate([])
    assert ok is False and "no artifact" in why.lower()


def test_the_refusal_names_EVERY_failing_adapter_not_just_the_first():
    ok, why = may_terminate([rec("a", local=None), rec("b", durable=None),
                             rec("c")])
    assert ok is False
    assert "a" in why and "b" in why


def test_a_record_missing_its_name_is_refused_rather_than_skipped():
    ok, why = may_terminate([{"local_md5": OK, "box_md5": OK,
                              "durable_uri": "hf://x"}])
    assert ok is False


# ── 4 · the collection planner — the box manifest is the source of truth ────

def test_plan_collection_marks_a_MISSING_local_file_as_absent(tmp_path):
    """⛔ A build that never arrived must show `local_md5: None`, which
    `may_terminate` then refuses. Not an exception here — the planner's job is
    to describe reality, and the gate's job is to refuse it."""
    from act2_retrain_orchestrate import plan_collection
    manifest = {"s20624": {"md5": OK, "bytes": 1, "remote_path": "/x"}}
    recs = plan_collection(manifest, tmp_path)
    assert recs[0]["local_md5"] is None
    ok, why = may_terminate(recs)
    assert ok is False and "s20624" in why


def test_plan_collection_reads_the_BOX_md5_not_a_recomputed_one(tmp_path):
    """⛔⛔ The remote checksum must come from the manifest the box wrote BEFORE
    the pull. A checksum taken from the copy, after the copy, verifies the copy
    against itself."""
    from act2_retrain_orchestrate import plan_collection
    d = tmp_path / "adapter_s20624"
    d.mkdir()
    (d / "adapter_model.safetensors").write_bytes(b"hello")
    manifest = {"s20624": {"md5": OTHER, "bytes": 5, "remote_path": "/x"}}
    r = plan_collection(manifest, tmp_path)[0]
    assert r["box_md5"] == OTHER              # straight from the manifest
    assert r["local_md5"] not in (None, OTHER)  # actually hashed on disk
    with pytest.raises(TransferError):
        verify_checksum(r["name"], local=r["local_md5"], remote=r["box_md5"])


def test_plan_collection_covers_EVERY_build_the_box_reported(tmp_path):
    from act2_retrain_orchestrate import plan_collection
    manifest = {n: {"md5": OK, "bytes": 1, "remote_path": "/x"}
                for n in ("s20624", "s20625", "s20626")}
    assert [r["name"] for r in plan_collection(manifest, tmp_path)] == \
        ["s20624", "s20625", "s20626"]


# ── 5 · the run root is a parameter, not a constant ────────────────────────

def test_the_orchestrator_has_NO_hardcoded_run_root():
    """⛔⛔ `REMOTE_ROOT`/`LOCAL_ROOT` were module constants pinned to
    `retrain12` — correct for exactly one run and silently wrong for the next.
    The stage it would have broken is `collect`, whose entire job is not to lose
    an adapter: it would have read a manifest from a directory that does not
    exist on the box."""
    import pathlib as _p
    src = (_p.Path(__file__).resolve().parents[1]
           / "tools/act2_retrain_orchestrate.py").read_text(encoding="utf-8")
    assert "REMOTE_ROOT" not in src and "LOCAL_ROOT" not in src


def test_the_root_helper_refuses_a_path_escape():
    """⛔ The root is interpolated into an ssh command and a local path."""
    import sys as _s
    import pathlib as _p
    _s.path.insert(0, str(_p.Path(__file__).resolve().parents[1] / "tools"))
    from act2_retrain_orchestrate import _roots
    # ⛔ r-strings. A plain "a\b" is `a` + BACKSPACE, not a path separator — a
    # heredoc ate the escape and the test asserted against a control character.
    for bad in ("", r"../etc", r"a/b", "a" + chr(92) + "b", r".hidden"):
        with pytest.raises(TransferError):
            _roots(bad)
    assert _roots("retrain12_ct")[0].endswith("runs/act2/retrain12_ct")


def test_the_solo_completeness_check_is_DERIVED_from_the_manifest():
    """⛔⛔ It read `6 * 14` — a hardcoded batch size. A single-adapter gate run
    would have been refused as a PARTIAL PULL of a batch it was never part of,
    at the one stage that must not be argued with."""
    import ast
    import pathlib as _p
    src = (_p.Path(__file__).resolve().parents[1]
           / "tools/act2_retrain_orchestrate.py").read_text(encoding="utf-8")
    # ⛔ CODE ONLY. The first version of this test asserted against the whole
    # file and fired on the COMMENT that explains the fix — a guard that cannot
    # tell an explanation from the thing it explains.
    # ⛔⛔ AND STRIPPING `#` LINES IS NOT ENOUGH: a DOCSTRING quoting the defect
    # survives that filter intact. Caught on 2026-09-04 when the identically
    # shaped guard in `test_box_persist.py` fired on its own module's docstring.
    # ⭐ Sweeping the class, not the instance — which is the lesson this whole
    # arc is about.
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and ast.get_docstring(node):
            node.body = node.body[1:]
    code = ast.unparse(tree)
    assert "6 * 14" not in code, "the solo check is still coupled to a batch size"
    assert "len(manifest) * SOLO_PER_BUILD" in code
