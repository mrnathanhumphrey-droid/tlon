"""Ledger/experiment separation.

The property being defended: two experiments must be able to prove they started
from identical history. Everything here tries to violate that -- by writing back
into the ledger, by forking from tampered history, or by letting two forks share
state.
"""
from __future__ import annotations
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tlon.grammar.parse import parse                  # noqa: E402
from tlon.novelty.centroids import RepetitionLog      # noqa: E402
from tlon.persist.store import LedgerError, Store     # noqa: E402

MOON = "u fang mlö ka"
RIVER = "mil flex fang ka"
CLOCK = "xom rän kön ka"


def _log(*texts):
    lg = RepetitionLog()
    for t in texts:
        lg.observe("03", parse(t), t)
    return lg


@pytest.fixture()
def store(tmp_path):
    return Store(tmp_path / "persist")


def test_snapshot_is_content_addressed(store):
    a = store.snapshot(_log(MOON), note="one")
    b = store.snapshot(_log(MOON), note="one again")
    assert a == b, "identical history must yield one snapshot id"
    assert len(list(store.snapshots.glob("*.json"))) == 1


def test_different_history_gets_a_different_id(store):
    """Red-proof for the test above: if ids collapsed, dedup would be a lie."""
    assert store.snapshot(_log(MOON)) != store.snapshot(_log(MOON, RIVER))


def test_snapshot_roundtrip_preserves_scores(store):
    lg = _log(MOON, RIVER, CLOCK)
    sid = store.snapshot(lg)
    back = store.read_snapshot(sid)
    probe = parse("hlör u fang axaxaxas mlö ka")
    assert back.score("03", probe) == lg.score("03", probe)


def test_tampering_with_the_ledger_is_detected(store):
    sid = store.snapshot(_log(MOON))
    p = store.snapshots / f"{sid}.json"
    p.write_text(p.read_text(encoding="utf-8").replace('"hits":1', '"hits":9'),
                 encoding="utf-8", newline="")
    assert store.verify() == [sid]
    with pytest.raises(LedgerError, match="altered"):
        store.read_snapshot(sid)


def test_clean_ledger_verifies(store):
    """Red-proof: verify() must not flag an untouched ledger."""
    store.snapshot(_log(MOON))
    store.snapshot(_log(MOON, RIVER))
    assert store.verify() == []


# ── the property that makes A/B legitimate ────────────────────────────────
def test_forks_are_independent_on_disk(store):
    sid = store.snapshot(_log(MOON))
    a = store.fork(sid, "runA")
    b = store.fork(sid, "runB")

    la = a.load_log()
    for _ in range(5):
        la.observe("03", parse(RIVER), RIVER)
    a.save_log(la)

    assert b.load_log().total_medoids() == 1, "runB saw runA's writes"
    assert store.read_snapshot(sid).total_medoids() == 1, "ledger was mutated"


def test_same_origin_detects_a_confound(store):
    s1 = store.snapshot(_log(MOON))
    s2 = store.snapshot(_log(MOON, RIVER))
    store.fork(s1, "a")
    store.fork(s1, "b")
    store.fork(s2, "c")
    assert store.same_origin("a", "b")
    assert not store.same_origin("a", "c"), (
        "forks from different history must not read as comparable")


def test_fork_will_not_silently_clobber(store):
    sid = store.snapshot(_log(MOON))
    store.fork(sid, "runA")
    with pytest.raises(LedgerError, match="already exists"):
        store.fork(sid, "runA")
    store.fork(sid, "runA", overwrite=True)      # explicit is fine


def test_fork_from_tampered_history_is_refused(store):
    sid = store.snapshot(_log(MOON))
    p = store.snapshots / f"{sid}.json"
    p.write_text(p.read_text(encoding="utf-8").replace('"seq":1', '"seq":7'),
                 encoding="utf-8", newline="")
    with pytest.raises(LedgerError):
        store.fork(sid, "runX")


def test_promote_appends_rather_than_mutating(store):
    sid = store.snapshot(_log(MOON))
    exp = store.fork(sid, "runA")
    lg = exp.load_log()
    lg.observe("03", parse(CLOCK), CLOCK)
    exp.save_log(lg)

    new_sid = store.promote(exp)
    assert new_sid != sid
    assert store.read_snapshot(sid).total_medoids() == 1      # original intact
    assert store.read_snapshot(new_sid).total_medoids() == 2
    assert len(store.history()) == 2


def test_manifest_is_append_only_and_ordered(store):
    store.snapshot(_log(MOON), note="first")
    store.snapshot(_log(MOON, RIVER), note="second")
    rows = store.history()
    assert [r["note"] for r in rows] == ["first", "second"]
    assert rows[0]["medoids"] == 1 and rows[1]["medoids"] == 2
