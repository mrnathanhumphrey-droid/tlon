"""The counter must be unrepresentable without its conditioning rates (B2).

Every test here tries to BREAK the constraint. A schema test that only checks
the happy path proves nothing -- it would pass against a schema with no
constraints at all.
"""
from __future__ import annotations
import pathlib
import sqlite3
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tlon.audit import log                                    # noqa: E402
from tlon.grammar.canon import canon_json, utterance_id       # noqa: E402
from tlon.grammar.gloss import gloss                          # noqa: E402
from tlon.grammar.parse import parse                          # noqa: E402


@pytest.fixture()
def con(tmp_path):
    c = log.connect(tmp_path / "audit.db")
    log.start_run(c, run_id="r1", phase="2a", grammar_family="southern",
                  lexicon_hash="deadbeef", referents_hash="cafebabe")
    yield c
    c.close()


def _rec(**kw):
    s = parse(kw.pop("text", "hlör u fang axaxaxas mlö ka"))
    base = dict(run_id="r1", seq=1, referent_id="03", surface="x",
                canon_json=canon_json(s), utterance_id=utterance_id(s),
                gloss=gloss(s), morphs=6, depth=1, m_pass=True,
                m_kind="STRUCTURAL", resolved_to=["03"], bucket="03",
                accepted=True)
    base.update(kw)
    return log.UtteranceRecord(**base)


# ── B2: the counter cannot be written unconditioned ────────────────────────
def test_counter_requires_auditor_state(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            "INSERT INTO counter_record (run_id, as_of, utterances_total,"
            " days_without_repeat, m_pass_rate, m_sample_n)"
            " VALUES ('r1','now',10,5.0,0.9,100)")


def test_measured_without_a_rate_is_rejected(con):
    """The null trap: MEASURED must carry real numbers."""
    with pytest.raises(sqlite3.IntegrityError):
        log.record_counter(con, run_id="r1", utterances_total=10,
                           days_without_repeat=5.0, m_pass_rate=0.9,
                           m_sample_n=100, auditor_state=log.AUDITOR_MEASURED)


def test_absent_auditor_may_not_carry_a_rate(con):
    """And the reverse: a stale rate cannot ride along on a non-measurement."""
    with pytest.raises(sqlite3.IntegrityError):
        log.record_counter(con, run_id="r1", utterances_total=10,
                           days_without_repeat=5.0, m_pass_rate=0.9,
                           m_sample_n=100, auditor_state=log.AUDITOR_ABSENT,
                           gloss_agreement_rate=0.95, gloss_sample_n=50)


def test_2a_can_log_but_cannot_publish(con):
    log.record_counter(con, run_id="r1", utterances_total=10,
                       days_without_repeat=5.0, m_pass_rate=0.9,
                       m_sample_n=100, auditor_state=log.AUDITOR_ABSENT)
    with pytest.raises(log.AuditError, match="vacuous"):
        log.publish_counter(con, "r1")


def test_failed_auditor_also_cannot_publish(con):
    log.record_counter(con, run_id="r1", utterances_total=10,
                       days_without_repeat=5.0, m_pass_rate=0.9,
                       m_sample_n=100, auditor_state=log.AUDITOR_FAILED)
    with pytest.raises(log.AuditError):
        log.publish_counter(con, "r1")


def test_measured_publishes(con):
    """Red-proof for the four tests above: if publish_counter refused
    everything they would pass vacuously."""
    log.record_counter(con, run_id="r1", utterances_total=10,
                       days_without_repeat=5.0, m_pass_rate=0.9,
                       m_sample_n=100, auditor_state=log.AUDITOR_MEASURED,
                       gloss_agreement_rate=0.93, gloss_sample_n=50)
    out = log.publish_counter(con, "r1")
    assert out["days_without_repeat"] == 5.0
    assert out["gloss_agreement_rate"] == 0.93
    assert out["m_pass_rate"] == 0.9


def test_view_hides_unmeasured_rows(con):
    log.record_counter(con, run_id="r1", utterances_total=1,
                       days_without_repeat=1.0, m_pass_rate=1.0, m_sample_n=1,
                       auditor_state=log.AUDITOR_ABSENT)
    assert con.execute("SELECT COUNT(*) c FROM counter_record").fetchone()["c"] == 1
    assert con.execute("SELECT COUNT(*) c FROM publishable_counter").fetchone()["c"] == 0


# ── collision detection keys on the canonical id, not the surface ──────────
def test_permuted_surface_is_logged_as_a_collision(con):
    a = log.log_utterance(con, _rec(seq=1, text="hlör nar mlö ka", surface="hlör nar mlö ka"))
    b = log.log_utterance(con, _rec(seq=2, text="nar hlör mlö ka", surface="nar hlör mlö ka"))
    rows = {r["row_id"]: r for r in con.execute("SELECT * FROM utterance")}
    assert rows[a]["collision"] == 0
    assert rows[b]["collision"] == 1, "different string, same meaning — must collide"
    assert rows[b]["collides_with"] == a


def test_different_meanings_do_not_collide(con):
    """Red-proof: if everything collided the test above would be meaningless."""
    log.log_utterance(con, _rec(seq=1, text="hlör mlö ka"))
    b = log.log_utterance(con, _rec(seq=2, text="nar mlö ka"))
    row = con.execute("SELECT * FROM utterance WHERE row_id=?", (b,)).fetchone()
    assert row["collision"] == 0


# ── structural/learned bookkeeping cannot be fudged ────────────────────────
def test_structural_m_may_not_carry_a_margin(con):
    with pytest.raises(sqlite3.IntegrityError):
        log.log_utterance(con, _rec(m_kind="STRUCTURAL", m_margin=0.8))


def test_learned_m_must_carry_a_margin(con):
    with pytest.raises(sqlite3.IntegrityError):
        log.log_utterance(con, _rec(m_kind="LEARNED", m_margin=None))


def test_rejection_must_state_a_reason(con):
    with pytest.raises(sqlite3.IntegrityError):
        log.log_utterance(con, _rec(accepted=False, reject_reason=None))


def test_ambiguity_is_recorded(con):
    """03/15 overlap by Nate's ruling — the store must show it, not hide it."""
    r = log.log_utterance(con, _rec(resolved_to=["03", "15"]))
    row = con.execute("SELECT * FROM utterance WHERE row_id=?", (r,)).fetchone()
    assert row["ambiguity"] == 2
