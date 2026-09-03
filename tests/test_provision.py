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
