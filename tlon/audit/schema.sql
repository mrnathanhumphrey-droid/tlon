-- Tlön audit store. Structured and queryable from day one: this is the thing
-- that has to be publicly inspectable later, so the constraints live here in
-- the schema rather than in the code that writes to it.
--
-- BOUND CONSTRAINT B2 (PHASE2_DESIGN §6b): the collision counter may never be
-- logged or served alone. It is vacuous without its conditioning pass rates --
-- a counter drawn from a 3.6e41 space proves nothing by itself. The CHECK
-- constraints below make an unaccompanied counter UNREPRESENTABLE, not merely
-- discouraged.
--
-- THE NULL TRAP this avoids: in 2a there is no gloss auditor at all. A nullable
-- column would sit empty through 2a and later be indistinguishable from a
-- MEASURED pass. So auditor_state is NOT NULL with an explicit ABSENT_BY_PHASE
-- value: 2a logs freely, it simply cannot publish.

PRAGMA foreign_keys = ON;

-- ─── provenance ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS run (
    run_id          TEXT PRIMARY KEY,
    started_at      TEXT    NOT NULL,          -- ISO-8601 UTC
    phase           TEXT    NOT NULL,          -- '2a', '2b', ...
    grammar_family  TEXT    NOT NULL,          -- 'southern' | 'northern' (B3)
    lexicon_hash    TEXT    NOT NULL,
    referents_hash  TEXT    NOT NULL,
    ledger_snapshot TEXT,                      -- which ledger this forked from
    notes           TEXT    NOT NULL DEFAULT ''
);

-- ─── every utterance the system produced, accepted or not ──────────────────
CREATE TABLE IF NOT EXISTS utterance (
    row_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT    NOT NULL REFERENCES run(run_id),
    seq             INTEGER NOT NULL,
    emitted_at      TEXT    NOT NULL,
    referent_id     TEXT    NOT NULL,          -- GROUND TRUTH, not inferred
    surface         TEXT    NOT NULL,
    canon_json      TEXT    NOT NULL,
    utterance_id    TEXT    NOT NULL,          -- blake2b of canon_json
    gloss           TEXT    NOT NULL,
    morphs          INTEGER NOT NULL,
    depth           INTEGER NOT NULL,

    -- M gate
    m_pass          INTEGER NOT NULL CHECK (m_pass IN (0, 1)),
    m_kind          TEXT    NOT NULL CHECK (m_kind IN ('STRUCTURAL', 'LEARNED')),
    m_margin        REAL,                      -- NULL iff m_kind = 'STRUCTURAL'
    resolved_to     TEXT    NOT NULL,          -- JSON list of matching referents
    ambiguity       INTEGER NOT NULL,          -- len(resolved_to); 1 == unambiguous

    -- R / novelty
    bucket          TEXT    NOT NULL,          -- ground-truth referent bucket
    nearest_dist    REAL,                      -- tree-edit distance to nearest centroid
    decay_weight    REAL,
    novelty_cost    REAL,

    -- orbit
    orbit_id        TEXT,
    orbit_spent     REAL,

    -- monitoring, decoupled from the R loss on purpose
    collision       INTEGER NOT NULL CHECK (collision IN (0, 1)),
    collides_with   INTEGER REFERENCES utterance(row_id),

    accepted        INTEGER NOT NULL CHECK (accepted IN (0, 1)),
    reject_reason   TEXT,
    attempt         INTEGER NOT NULL DEFAULT 1,

    CHECK ((m_kind = 'STRUCTURAL') = (m_margin IS NULL)),
    CHECK ((accepted = 1) OR (reject_reason IS NOT NULL)),
    CHECK ((collision = 0) = (collides_with IS NULL)),
    UNIQUE (run_id, seq, attempt)
);

CREATE INDEX IF NOT EXISTS ix_utt_uid    ON utterance(utterance_id);
CREATE INDEX IF NOT EXISTS ix_utt_bucket ON utterance(run_id, bucket);
CREATE INDEX IF NOT EXISTS ix_utt_run    ON utterance(run_id, seq);

-- ─── the coupled counter record — B2 lives here ────────────────────────────
-- One row IS the counter plus everything needed to interpret it. There is no
-- way to write the counter without declaring what the auditor was doing.
CREATE TABLE IF NOT EXISTS counter_record (
    row_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                TEXT    NOT NULL REFERENCES run(run_id),
    as_of                 TEXT    NOT NULL,
    utterances_total      INTEGER NOT NULL,
    days_without_repeat   REAL    NOT NULL,
    last_collision_at     TEXT,

    -- conditioning rates. The counter is meaningless without these.
    m_pass_rate           REAL    NOT NULL CHECK (m_pass_rate BETWEEN 0 AND 1),
    m_sample_n            INTEGER NOT NULL CHECK (m_sample_n > 0),

    auditor_state         TEXT    NOT NULL CHECK (
                              auditor_state IN ('ABSENT_BY_PHASE',
                                                'MEASURED',
                                                'FAILED_TO_RUN')),
    gloss_agreement_rate  REAL    CHECK (gloss_agreement_rate BETWEEN 0 AND 1),
    gloss_sample_n        INTEGER,

    -- MEASURED requires real numbers; anything else forbids them, so a stale
    -- value can never masquerade as a fresh measurement.
    CHECK ((auditor_state = 'MEASURED')
           = (gloss_agreement_rate IS NOT NULL AND gloss_sample_n IS NOT NULL))
);

-- ─── the only thing the public endpoint may read ───────────────────────────
-- Non-MEASURED rows are not merely flagged here; they are absent. A serving
-- layer that forgets to filter still cannot leak an unconditioned counter.
CREATE VIEW IF NOT EXISTS publishable_counter AS
SELECT run_id, as_of, utterances_total, days_without_repeat,
       last_collision_at, m_pass_rate, m_sample_n,
       gloss_agreement_rate, gloss_sample_n
FROM counter_record
WHERE auditor_state = 'MEASURED';
