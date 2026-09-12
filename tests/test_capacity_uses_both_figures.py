"""⛔⛔ RED-PROOF: THE CAPACITY GUARD MUST NOT TRUST ONE SUMMARY FIELD.

`used_storage_bytes` read `usedStorage` alone, and the docstring gave a good
reason: this repo's live files once totalled 50.72 GB while it was charged
94.21 GB, because 43.49 GB was superseded LFS history. Summing the current files
would have under-reported by 46 % and admitted a run that cannot persist.

⛔⛔ THEN IT INVERTED. On 2026-09-12 the live files totalled **90.43 GB** while
`usedStorage` reported **68.88 GB** — stale by exactly one 21.48 GB model, the
cell that had just been pushed. The guard computed 68.88 + 21.69 = 90.57 against
a 94.21 ceiling and said **FITS**. The truth was 90.43 + 21.69 = **112.12 GB**.
A fourth Mistral attempt would have trained ~62 minutes and died at
`persist_leg1` on "storage limit reached" — rung 1b''s exact death, twice.

⭐ SO NEITHER FIGURE IS SAFE ALONE, AND THEY FAIL IN OPPOSITE DIRECTIONS:

    usedStorage > live files    dead LFS history is being charged
    live files > usedStorage    the summary field has not caught up

Two independent paths to one quantity. When they disagree, take the conservative
one and say so — never the one that happens to let the run start.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

from tlon.act2.hub_capacity import (live_file_bytes,               # noqa: E402
                                    used_storage_bytes)

GB = 1_000_000_000


class _Sib:
    def __init__(self, size, lfs=None, sha=None, name="x"):
        self.size = size
        self.lfs = lfs if lfs is not None else ({"sha256": sha} if sha else None)
        self.rfilename = name


class _Api:
    """A hub that reports `reported` as usedStorage and `live` as its files."""

    def __init__(self, reported, live, *, listing=True):
        self._r, self._live, self._listing = reported, live, listing

    def model_info(self, repo, expand=None):
        return type("I", (), {"used_storage": self._r})()

    def repo_info(self, repo, files_metadata=False):
        if not self._listing:
            raise RuntimeError("listing unavailable")
        sibs = None if self._live is None else [_Sib(self._live)]
        return type("I", (), {"siblings": sibs})()


def test_a_STALE_summary_field_cannot_understate_usage():
    """⛔⛔ THE 2026-09-12 STATE, EXACTLY. The bug that would have cost a fourth
    run."""
    got = used_storage_bytes("r", api=_Api(68.88 * GB, 90.43 * GB))
    assert got == pytest.approx(90.43 * GB), \
        "the guard took the stale summary and would have admitted the run"


def test_DEAD_LFS_HISTORY_is_still_counted():
    """⭐ The ORIGINAL reason the field was trusted must not be broken by the
    fix. When history is charged, `usedStorage` is the larger figure and wins."""
    got = used_storage_bytes("r", api=_Api(94.21 * GB, 50.72 * GB))
    assert got == pytest.approx(94.21 * GB), \
        "summing live files under-reports by 46% when history is charged"


def test_the_guard_takes_the_MAXIMUM_not_the_average_or_the_latest():
    for rep, live in ((10 * GB, 90 * GB), (90 * GB, 10 * GB)):
        assert used_storage_bytes("r", api=_Api(rep, live)) == max(rep, live)


def test_a_MISSING_usedStorage_still_RAISES_and_never_becomes_zero():
    """⛔ An unmeasured quota is not an empty one."""
    with pytest.raises(RuntimeError, match="REFUSING to guess"):
        used_storage_bytes("r", api=_Api(None, 50 * GB))


def test_an_UNREADABLE_LISTING_falls_back_to_the_reported_figure():
    """⛔ No second opinion is not the same as agreement — but it must not make
    the guard refuse a repo it could otherwise size."""
    assert used_storage_bytes("r", api=_Api(60 * GB, None, listing=False)) \
        == 60 * GB


def test_live_file_bytes_returns_NONE_not_ZERO_when_it_cannot_look():
    """⛔⛔ A failed fetch records MISSING, never 0. Zero here would be the
    largest possible lie: it would make every repo look empty."""
    assert live_file_bytes("r", api=_Api(1 * GB, None, listing=False)) is None
    assert live_file_bytes("r", api=_Api(1 * GB, None)) is None


def test_IDENTICAL_BLOBS_ARE_COUNTED_ONCE():
    """⛔⛔ THE DEFECT I ACTUALLY HAD, AND IT FAKED THE BUG I THOUGHT I'D FOUND.

    LFS is content-addressed: two paths holding identical bytes cost storage
    ONCE. Summing filenames reported 90.43 GB where the truth was 68.96 GB,
    because `mis16b-s20624/model.safetensors` and `mis16c-s20624/model.safetensors`
    are byte-identical. That 21.48 GB phantom is what made `usedStorage` look
    "stale by exactly one model" — it was not stale, my second opinion was wrong,
    and the guard would then have refused a run that fits.
    """
    class _A(_Api):
        def repo_info(self, repo, files_metadata=False):
            return type("I", (), {"siblings": [
                _Sib(21 * GB, sha="aaa", name="mis16b/model.safetensors"),
                _Sib(21 * GB, sha="aaa", name="mis16c/model.safetensors"),
                _Sib(21 * GB, sha="bbb", name="mis16/model.safetensors"),
            ]})()
    assert live_file_bytes("r", api=_A(1 * GB, None)) == 42 * GB, \
        "the shared blob must be counted once, not twice"


def test_a_file_with_NO_sha_is_counted_in_full():
    """⭐ Small non-LFS files carry no sha to dedupe on. Counting them in full
    can only OVER-state, which is the safe direction for a floor — but it must
    not be silently treated as a duplicate of the previous shaless file."""
    class _A(_Api):
        def repo_info(self, repo, files_metadata=False):
            return type("I", (), {"siblings": [
                _Sib(3, name="a.json"), _Sib(5, name="b.json")]})()
    assert live_file_bytes("r", api=_A(1 * GB, None)) == 8


def test_the_two_figures_AGREE_once_dedup_is_correct():
    """⭐ THE STATE THAT MAKES EITHER FIGURE TRUSTWORTHY. Deduplicated, the live
    sum and `usedStorage` landed within 0.08 GB of each other on the real repo.
    Agreement is only evidence when both paths measure the same quantity."""
    class _A(_Api):
        def repo_info(self, repo, files_metadata=False):
            return type("I", (), {"siblings": [
                _Sib(21 * GB, sha="aaa", name="b/model.safetensors"),
                _Sib(21 * GB, sha="aaa", name="c/model.safetensors"),
                _Sib(47 * GB, sha="bbb", name="rest")]})()
    api = _A(68 * GB, None)
    assert live_file_bytes("r", api=api) == 68 * GB
    assert used_storage_bytes("r", api=api) == 68 * GB, \
        "no spurious disagreement, so no spurious refusal"


def test_live_file_bytes_reads_the_LFS_size_when_size_is_absent():
    """⭐ LFS files report their size under `lfs`, and a missing `size` there
    would silently drop the only large files in the repo."""
    class _A(_Api):
        def repo_info(self, repo, files_metadata=False):
            return type("I", (), {"siblings": [_Sib(None, {"size": 7 * GB})]})()
    assert live_file_bytes("r", api=_A(1 * GB, None)) == 7 * GB


def test_the_TOOL_prints_BOTH_figures_and_flags_disagreement():
    """⛔ A discrepancy nobody prints is a discrepancy nobody acts on. The whole
    failure was that one number was shown and it was the wrong one."""
    src = (_ROOT / "tools" / "act2_hub_capacity.py").read_text(encoding="utf-8")
    assert "live_file_bytes" in src
    assert "THEY DISAGREE" in src
    assert "live files" in src
