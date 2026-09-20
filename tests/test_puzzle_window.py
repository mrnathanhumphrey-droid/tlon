"""THE WINDOW — the conversation held server-side and re-fed each turn.

⭐ Nate's framing: *"the window holds the moment; that is the ontology, not a
workaround."* Everything here is about that store being trustworthy, because it
is the only memory in the system — the model is stateless per call and cannot
be asked what it said.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puzzle.window import TLON, YOU, ConversationStore      # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return ConversationStore(tmp_path / "bench.sqlite3")


def test_a_bench_starts_empty_and_is_findable(store):
    cid = store.new_conversation()
    assert store.exists(cid)
    assert store.history(cid) == []
    assert store.next_turn(cid) == 0


def test_two_benches_do_not_see_each_other(store):
    """⛔ The app is public and anonymous. A leak here is one reader reading
    another reader's conversation."""
    a, b = store.new_conversation(), store.new_conversation()
    store.append(a, 0, YOU, english="mine", surface="mil prax ka")
    assert store.history(b) == []
    assert store.surfaces(b) == []


def test_a_turn_is_two_rows_in_order(store):
    cid = store.new_conversation()
    store.append(cid, 0, YOU, english="hello", surface="mil prax ka")
    store.append(cid, 0, TLON, surface="sen fes kä")
    rows = store.history(cid)
    assert [r["role"] for r in rows] == [YOU, TLON]
    assert rows[0]["english"] == "hello"
    assert store.next_turn(cid) == 1


def test_refused_lines_are_kept_but_never_handed_to_the_model(store):
    """⛔⛔ THE TWO HALVES OF THIS ARE BOTH LOAD-BEARING AND THEY PULL APART.

    The refusal is KEPT because a failure is the most information-dense event
    in a run and run 4 lost its largest result by storing failures as null. It
    is EXCLUDED from `surfaces()` because a blank line handed back as a
    provocation is input the corpus never contains.
    """
    cid = store.new_conversation()
    store.append(cid, 0, YOU, english="x", surface=None,
                 refused="gate refused: unknown root")
    store.append(cid, 1, YOU, english="y", surface="mil prax ka")
    assert len(store.history(cid)) == 2
    assert store.history(cid)[0]["refused"]
    assert store.surfaces(cid) == ["mil prax ka"]


def test_the_window_is_bounded_by_turns_not_rows(store):
    """⭐ A row cap would cut a reply away from the line that provoked it,
    leaving the model conditioned on half an exchange."""
    cid = store.new_conversation()
    for t in range(10):
        store.append(cid, t, YOU, english="e%d" % t, surface="you%d" % t)
        store.append(cid, t, TLON, surface="it%d" % t)
    rows = store.history(cid, max_turns=3)
    assert len({r["turn"] for r in rows}) == 3
    assert len(rows) == 6
    assert [r["role"] for r in rows] == [YOU, TLON] * 3


def test_an_unknown_role_raises_rather_than_storing(store):
    """⛔ RAISE, NEVER DEFAULT. A typo'd role stored quietly would vanish from
    the ordering and read back as a dropped turn — data loss that looks like a
    model failure."""
    cid = store.new_conversation()
    with pytest.raises(ValueError):
        store.append(cid, 0, "assistant", surface="mil prax ka")


def test_the_store_has_no_column_for_who_you_are(store):
    """⛔⛔ THE ORACLE'S STORE IS KEYED ON `user_email`. This app is anonymous
    and public, so that column must not exist — a field that must never be
    filled is a privacy surface with no upside, and the way to guarantee it is
    never filled is for there to be nowhere to put it."""
    import sqlite3

    conn = sqlite3.connect(store.db_path)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(messages)")}
        cols |= {r[1] for r in conn.execute("PRAGMA table_info(conversations)")}
    finally:
        conn.close()
    for banned in ("user_email", "email", "user_id", "ip", "ip_address"):
        assert banned not in cols, "⛔⛔ the bench stores %r" % banned


def test_it_survives_being_reopened(store, tmp_path):
    """The bench outlives the process — a reader who comes back tomorrow finds
    the conversation where they left it."""
    cid = store.new_conversation()
    store.append(cid, 0, YOU, english="hello", surface="mil prax ka")
    again = ConversationStore(tmp_path / "bench.sqlite3")
    assert again.exists(cid)
    assert again.surfaces(cid) == ["mil prax ka"]
