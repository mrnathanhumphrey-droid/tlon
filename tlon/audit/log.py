"""Audit store: open, write, and the one guarded read.

The invariants live in schema.sql as CHECK constraints, so they hold even if
something writes to this database without going through this module. What is
added here is `publish_counter`, which refuses to hand out a counter that is not
conditioned on a real auditor measurement.
"""
from __future__ import annotations
import datetime as _dt
import json
import pathlib
import sqlite3
from dataclasses import dataclass

SCHEMA = pathlib.Path(__file__).with_name("schema.sql")

AUDITOR_ABSENT = "ABSENT_BY_PHASE"
AUDITOR_MEASURED = "MEASURED"
AUDITOR_FAILED = "FAILED_TO_RUN"


class AuditError(RuntimeError):
    pass


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def connect(path: str | pathlib.Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    return con


@dataclass
class UtteranceRecord:
    run_id: str
    seq: int
    referent_id: str
    surface: str
    canon_json: str
    utterance_id: str
    gloss: str
    morphs: int
    depth: int
    m_pass: bool
    m_kind: str
    resolved_to: list[str]
    bucket: str
    accepted: bool
    m_margin: float | None = None
    nearest_dist: float | None = None
    decay_weight: float | None = None
    novelty_cost: float | None = None
    orbit_id: str | None = None
    orbit_spent: float | None = None
    reject_reason: str | None = None
    attempt: int = 1


def start_run(con: sqlite3.Connection, *, run_id: str, phase: str,
              grammar_family: str, lexicon_hash: str, referents_hash: str,
              ledger_snapshot: str | None = None, notes: str = "") -> None:
    con.execute(
        "INSERT INTO run (run_id, started_at, phase, grammar_family, "
        "lexicon_hash, referents_hash, ledger_snapshot, notes) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (run_id, utcnow(), phase, grammar_family, lexicon_hash,
         referents_hash, ledger_snapshot, notes))
    con.commit()


def log_utterance(con: sqlite3.Connection, rec: UtteranceRecord) -> int:
    """Insert an utterance, resolving the collision check against the whole
    store. Collision is exact on utterance_id -- the canonical AST hash, never
    the surface string (spec §6)."""
    prior = con.execute(
        "SELECT row_id FROM utterance WHERE utterance_id = ? "
        "ORDER BY row_id LIMIT 1", (rec.utterance_id,)).fetchone()
    cur = con.execute(
        "INSERT INTO utterance (run_id, seq, emitted_at, referent_id, surface,"
        " canon_json, utterance_id, gloss, morphs, depth, m_pass, m_kind,"
        " m_margin, resolved_to, ambiguity, bucket, nearest_dist, decay_weight,"
        " novelty_cost, orbit_id, orbit_spent, collision, collides_with,"
        " accepted, reject_reason, attempt)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (rec.run_id, rec.seq, utcnow(), rec.referent_id, rec.surface,
         rec.canon_json, rec.utterance_id, rec.gloss, rec.morphs, rec.depth,
         int(rec.m_pass), rec.m_kind, rec.m_margin,
         json.dumps(sorted(rec.resolved_to)), len(rec.resolved_to), rec.bucket,
         rec.nearest_dist, rec.decay_weight, rec.novelty_cost, rec.orbit_id,
         rec.orbit_spent, int(prior is not None),
         prior["row_id"] if prior else None, int(rec.accepted),
         rec.reject_reason, rec.attempt))
    con.commit()
    return int(cur.lastrowid)


def record_counter(con: sqlite3.Connection, *, run_id: str,
                   utterances_total: int, days_without_repeat: float,
                   m_pass_rate: float, m_sample_n: int, auditor_state: str,
                   gloss_agreement_rate: float | None = None,
                   gloss_sample_n: int | None = None,
                   last_collision_at: str | None = None) -> int:
    if auditor_state not in (AUDITOR_ABSENT, AUDITOR_MEASURED, AUDITOR_FAILED):
        raise AuditError(f"unknown auditor_state {auditor_state!r}")
    cur = con.execute(
        "INSERT INTO counter_record (run_id, as_of, utterances_total,"
        " days_without_repeat, last_collision_at, m_pass_rate, m_sample_n,"
        " auditor_state, gloss_agreement_rate, gloss_sample_n)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        (run_id, utcnow(), utterances_total, days_without_repeat,
         last_collision_at, m_pass_rate, m_sample_n, auditor_state,
         gloss_agreement_rate, gloss_sample_n))
    con.commit()
    return int(cur.lastrowid)


def publish_counter(con: sqlite3.Connection, run_id: str) -> dict:
    """The ONLY read a public endpoint may use.

    Refuses anything the gloss auditor has not actually measured. In 2a this
    always raises, and that is correct: 2a proves plumbing, never pragmatics,
    so it has nothing publishable to say about whether the system communicates.
    """
    row = con.execute(
        "SELECT * FROM publishable_counter WHERE run_id = ? "
        "ORDER BY as_of DESC LIMIT 1", (run_id,)).fetchone()
    if row is None:
        latest = con.execute(
            "SELECT auditor_state FROM counter_record WHERE run_id = ? "
            "ORDER BY as_of DESC LIMIT 1", (run_id,)).fetchone()
        state = latest["auditor_state"] if latest else "NO_RECORD"
        raise AuditError(
            f"no publishable counter for run {run_id!r}: auditor_state={state}. "
            "A counter without a measured gloss-agreement rate is vacuous — "
            "the birthday-problem objection applies. Not served.")
    return dict(row)
