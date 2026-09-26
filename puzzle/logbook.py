"""THE LOG — what happened on the bench, written down where it survives.

⛔⛔ UNTIL THIS FILE EXISTED THE ONLY RECORD WAS MODAL'S STDOUT, WHICH DIES WITH
THE CONTAINER. `scaledown_window` is 300 seconds: five quiet minutes and every
error, every refusal and every turn that ever happened is gone. `/healthz` was
the only instrument, and its counters (`proxy_signed`, `turns_today`) are
per-container too — so a question as basic as "did anyone speak to it
yesterday" had no answer anywhere.

⛔⛔⛔ IT IS NOT SERVED, AND THE REASON IS NOT THE ONE I FIRST WROTE DOWN.

I claimed this file was the answer key. It is not, and a test caught me: a row
holds the reader's English and the reply it DREW — which is the same two things
`/conversation` already shows that reader. The aligned pair is the reader's own
line rendered into Tlön, and this log does not store it.

⭐ THAT IS A DECISION, NOT AN ACCIDENT. `speaker.turn` returns the reader's
surface; `bench.sqlite3` keeps it because the translate button needs it, and
this file has no use for it, so it does not get a copy. A log that holds less is
a log that can leak less.

⛔⛔ WHAT MAKES IT UNSERVABLE IS THE AGGREGATE, NOT THE ROW. All of it at once is
every reader's conversation beside a stable id for each — a privacy artifact
outright, and in a puzzle whose difficulty IS how much Tlön one person has seen,
a substantial shortcut. So:

  * it lives OUTSIDE `puzzle/static/`, on the bench volume;
  * no route returns its contents — the admin endpoints only WRITE (a ban) or
    make a snapshot FILE; reading is done offline, after `modal volume get`;
  * `test_puzzle_log_is_not_served.py` walks the route table and fails if that
    ever stops being true.

⭐ ANONYMOUS TO WHOEVER READS THE LOG. No IP, no user agent, no cookie value
and no email is stored — the only identity is `reader`, an HMAC of the address
under a server-side pepper. Someone holding this file learns what was said and
that two lines came from the same person; they cannot learn who, and they
cannot brute-force the address space without the pepper.

⛔⛔ AND THE BAN IS WHY THE HASH IS KEYED RATHER THAN SALTED PER ROW. A per-row
salt would be more anonymous and completely useless: banning requires that the
same address hash to the same string tomorrow.

⛔⛔⛔ A BAN IS ONLY MEANINGFUL WHEN THE ADDRESS WAS TRUSTWORTHY. `guard.client_ip`
falls through to Cloudflare's egress address whenever `TLON_PROXY_SECRET` is
wrong on either side — the SAME STRING FOR EVERY READER ON EARTH. Ban that and
you have banned the internet, and it would present as the puzzle simply being
broken for everybody at once. It is not hypothetical: that secret was stored as
a single non-printable character for days. So every row records `ip_trusted`,
`ban()` REFUSES a reader who has ever been seen untrusted, and the enforcement
side only consults the ban list when the CURRENT request's address is signed.

⭐ NOTHING HERE MAY TAKE THE BENCH DOWN. Every write is wrapped: a full disk or
a locked file loses the log line, never the reader's turn. ⛔ But the failure is
COUNTED and reported by `/healthz`, because a logger that silently stops is
worse than no logger — it answers "nothing happened" to every question.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import pathlib
import sqlite3
import threading
import time

#: ⭐ The pepper, in order of preference. A DEDICATED secret first, because the
#: other two exist for their own reasons and may be rotated for their own
#: reasons — and rotating the pepper silently invalidates every ban, since the
#: same address then hashes to a different reader.
#: ⛔ `TURNSTILE_SECRET_KEY` is last but it is the safety net that makes this
#: work with no new configuration at all: `turnstile.preflight()` refuses to
#: start a deployment without it, so in production at least one of these three
#: is always present.
PEPPER_SOURCES = ("TLON_LOG_PEPPER", "TLON_PROXY_SECRET", "TURNSTILE_SECRET_KEY")

#: ⛔ USED ONLY WHERE NONE OF THE ABOVE EXISTS, WHICH IS A LAPTOP. It is a
#: literal in a public repository on purpose: a RANDOM per-boot pepper would be
#: the worse failure, because bans would stop working on every restart and
#: nothing would say so. `/healthz` reports which source was used, so "dev" in
#: production is visible rather than inferred.
DEV_PEPPER = "tlon-dev-pepper-not-a-secret"

#: ⛔ Domain separation. The pepper is usually a secret that also signs
#: something else (the proxy header, the session pass); tagging the message
#: means a reader id can never be replayed as one of those.
_DOMAIN = "tlon-reader-v1|"

#: How much of the digest to keep. 64 bits: collision-free at any traffic this
#: bench will ever see, and short enough to paste into a ban command.
_ID_CHARS = 16

#: Caps, so one pathological request cannot write a megabyte row.
MAX_TEXT = 4000
MAX_TRACEBACK = 8000

#: ⛔⛔ `CREATE TABLE IF NOT EXISTS` DOES NOTHING TO A TABLE THAT ALREADY EXISTS.
#: The production log is live and holds real turns, so a column added to
#: `_SCHEMA` reaches a fresh database and no other — every existing bench would
#: keep the old shape and every insert naming the new column would fail. These
#: run after the schema, are guarded by what the table actually has, and are
#: idempotent.
#:
#: ⭐ Each entry is (table, column, DDL). Index creation that depends on a
#: migrated column belongs here too, AFTER the column exists — in `_SCHEMA` it
#: would run first and raise "no such column" on every live database.
_MIGRATIONS = (
    ("turns", "route", "ALTER TABLE turns ADD COLUMN route TEXT NOT NULL "
                       "DEFAULT ''"),
    ("turns", "force_model", "ALTER TABLE turns ADD COLUMN force_model TEXT "
                             "NOT NULL DEFAULT ''"),
    ("turns", "force_sent", "ALTER TABLE turns ADD COLUMN force_sent TEXT "
                            "NOT NULL DEFAULT ''"),
)

_POST_MIGRATION = (
    "CREATE INDEX IF NOT EXISTS ix_turns_route ON turns (route)",
)


def _migrate(conn) -> None:
    """Bring an existing database up to `_SCHEMA`'s shape. Idempotent."""
    for table, column, ddl in _MIGRATIONS:
        have = {r[1] for r in conn.execute("PRAGMA table_info(%s)" % table)}
        if column not in have:
            conn.execute(ddl)
    for ddl in _POST_MIGRATION:
        conn.execute(ddl)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS turns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    at              REAL NOT NULL,
    request_id      TEXT,
    reader          TEXT NOT NULL,
    ip_trusted      INTEGER NOT NULL,
    conversation_id TEXT,
    turn            INTEGER,
    english         TEXT,          -- what the reader typed
    -- ⛔ THE REPLY'S surface, NEVER THE READER'S OWN. Their line rendered into
    -- Tlön is the aligned pair `server._public()` exists to withhold; this
    -- table has no use for it and deliberately keeps no copy.
    surface         TEXT,
    refused         TEXT,
    seconds         REAL,
    flags           TEXT NOT NULL DEFAULT '',
    severity        INTEGER NOT NULL DEFAULT 0,
    -- ⭐ Which door the line went through: tlon · force · tagged · english ·
    -- english.roots · nothing. Without it a refusal cannot be attributed to a
    -- route, and `english.roots` is the only record of the rows a future write
    -- corpus needs. ⛔ Added to a table that already holds production turns —
    -- see `_MIGRATIONS`, which is what makes that safe.
    route           TEXT NOT NULL DEFAULT '',
    -- ⭐ The force the MODEL chose and the force actually SERVED. They differ
    -- only when the product force dial is on (`TLON_FORCE_TABLE`), and both
    -- are written either way so a later comparison does not depend on the flag
    -- having been set when the row was recorded.
    force_model     TEXT NOT NULL DEFAULT '',
    force_sent      TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_turns_at ON turns (at);
CREATE INDEX IF NOT EXISTS ix_turns_reader ON turns (reader, at);
CREATE INDEX IF NOT EXISTS ix_turns_sev ON turns (severity, at);

CREATE TABLE IF NOT EXISTS errors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    at          REAL NOT NULL,
    request_id  TEXT,
    reader      TEXT,
    ip_trusted  INTEGER,
    method      TEXT,
    route       TEXT,
    status      INTEGER,
    kind        TEXT,              -- exception class name, or 'http'
    detail      TEXT,
    traceback   TEXT,
    seconds     REAL
);
CREATE INDEX IF NOT EXISTS ix_errors_at ON errors (at);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    at          REAL NOT NULL,
    reader      TEXT,
    ip_trusted  INTEGER,
    kind        TEXT NOT NULL,     -- refused.rate | refused.turnstile | probe | ban.*
    detail      TEXT
);
CREATE INDEX IF NOT EXISTS ix_events_at ON events (at);
CREATE INDEX IF NOT EXISTS ix_events_kind ON events (kind, at);

CREATE TABLE IF NOT EXISTS bans (
    reader  TEXT PRIMARY KEY,
    at      REAL NOT NULL,
    until   REAL,                  -- NULL = no expiry
    note    TEXT
);
"""


def pepper() -> tuple[str, str]:
    """The keying secret and the name of where it came from.

    ⛔ Read per call, not at import. A module-level constant would freeze
    whatever the environment happened to be when something first imported this,
    which in the test suite is another test's monkeypatch.
    """
    for name in PEPPER_SOURCES:
        value = os.environ.get(name, "")
        if value:
            return value, name
    return DEV_PEPPER, "dev"


def reader_id(ip: str) -> str:
    """⭐ THE ONLY IDENTITY THIS LOG HAS. HMAC, not a plain hash: the address
    space is 2^32 and a bare SHA of every IPv4 address is a rainbow table
    somebody can build in an afternoon. With a secret pepper it is not
    reversible by anyone holding the file."""
    key, _ = pepper()
    msg = (_DOMAIN + (ip or "")).encode("utf-8")
    return hmac.new(key.encode("utf-8"), msg, hashlib.sha256).hexdigest()[:_ID_CHARS]


def _clip(text, limit: int):
    if text is None:
        return None
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "…[clipped]"


class Logbook:
    """One SQLite file on the bench volume. Separate from `bench.sqlite3` on
    purpose: retention differs, and a log that is locked, corrupt or full must
    not be able to take conversations down with it."""

    def __init__(self, path, *, plain_days: int = 30, flagged_days: int = 90,
                 prune_every: int = 200):
        self.path = pathlib.Path(path)
        self.plain_days = plain_days
        self.flagged_days = flagged_days
        self.prune_every = prune_every
        self.failures = 0
        self.last_failure = ""
        self._lock = threading.Lock()
        self._since_prune = 0
        self._bans: set[str] | None = None
        self._bans_at = 0.0
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            conn = self._conn()
            try:
                conn.executescript(_SCHEMA)
                _migrate(conn)
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:                                  # noqa: BLE001
            self._failed("open", exc)

    # ── plumbing ───────────────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        # ⛔ The busy timeout is the same reason `window.py` has one: uvicorn
        # runs turns on worker threads, so two writers can meet on this file.
        conn = sqlite3.connect(self.path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _failed(self, what: str, exc: BaseException) -> None:
        """⛔ COUNTED, NOT SWALLOWED. A logger that fails quietly answers
        "nothing happened" to every question anyone ever asks it."""
        self.failures += 1
        self.last_failure = "%s: %s" % (what, exc)
        print("⛔ logbook %s failed: %s" % (what, exc), flush=True)

    def _write(self, sql: str, params: tuple) -> None:
        try:
            conn = self._conn()
            try:
                conn.execute(sql, params)
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:                                  # noqa: BLE001
            self._failed("write", exc)
            return
        self._maybe_prune()

    def _maybe_prune(self) -> None:
        with self._lock:
            self._since_prune += 1
            if self._since_prune < self.prune_every:
                return
            self._since_prune = 0
        self.prune()

    # ── writes ─────────────────────────────────────────────────────────────

    def record_turn(self, *, reader: str, ip_trusted: bool,
                    english: str | None, surface: str | None = None,
                    refused: str | None = None, conversation_id: str | None = None,
                    turn: int | None = None, seconds: float | None = None,
                    flags: str = "", severity: int = 0,
                    request_id: str | None = None, route: str = "",
                    force_model: str | None = None,
                    force_sent: str | None = None) -> None:
        self._write(
            "INSERT INTO turns (at, request_id, reader, ip_trusted, "
            "conversation_id, turn, english, surface, refused, seconds, "
            "flags, severity, route, force_model, force_sent) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (time.time(), request_id, reader, 1 if ip_trusted else 0,
             conversation_id, turn, _clip(english, MAX_TEXT),
             _clip(surface, MAX_TEXT), _clip(refused, 500), seconds,
             flags, int(severity), route, force_model or "",
             force_sent or ""))

    def record_error(self, *, kind: str, detail: str, reader: str | None = None,
                     ip_trusted: bool | None = None, method: str | None = None,
                     route: str | None = None, status: int | None = None,
                     traceback: str | None = None, seconds: float | None = None,
                     request_id: str | None = None) -> None:
        self._write(
            "INSERT INTO errors (at, request_id, reader, ip_trusted, method, "
            "route, status, kind, detail, traceback, seconds) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (time.time(), request_id, reader,
             None if ip_trusted is None else (1 if ip_trusted else 0),
             method, route, status, kind, _clip(detail, 2000),
             _clip(traceback, MAX_TRACEBACK), seconds))

    def record_event(self, *, kind: str, reader: str | None = None,
                     ip_trusted: bool | None = None,
                     detail: str | None = None) -> None:
        self._write(
            "INSERT INTO events (at, reader, ip_trusted, kind, detail) "
            "VALUES (?,?,?,?,?)",
            (time.time(), reader,
             None if ip_trusted is None else (1 if ip_trusted else 0),
             kind, _clip(detail, 1000)))

    # ── the ban list ───────────────────────────────────────────────────────

    def is_banned(self, reader: str) -> bool:
        """⛔⛔ THE CALLER MUST ALREADY HAVE CHECKED THAT THE ADDRESS WAS
        TRUSTED. This function cannot see the request, so it cannot enforce
        that itself — `server._say` does, and `test_puzzle_logbook.py` pins it.
        Consulting the list on an untrusted address would apply one person's
        ban to everybody sharing Cloudflare's egress identity, which is
        everybody."""
        bans = self._ban_set()
        if reader not in bans:
            return False
        until = bans[reader]
        # ⭐ An expired ban is simply not a ban; the row is left in place so the
        # operator can still see that it happened.
        return until is None or until > time.time()

    def _ban_set(self) -> dict:
        """⭐ Cached for 30s. This is read on every request to `/say`, and this
        process is the only thing that ever writes the table — so a write
        invalidates it directly and the TTL is only a backstop."""
        now = time.time()
        if self._bans is None or now - self._bans_at > 30:
            try:
                conn = self._conn()
                try:
                    rows = conn.execute(
                        "SELECT reader, until FROM bans").fetchall()
                finally:
                    conn.close()
                self._bans = {r["reader"]: r["until"] for r in rows}
                self._bans_at = now
            except Exception as exc:                              # noqa: BLE001
                self._failed("ban-read", exc)
                # ⛔ FAIL OPEN, DELIBERATELY. A reader who cannot be checked is
                # let through: the alternative is a locked database refusing
                # every visitor on the planet, which is a worse outage than an
                # abuser getting a few more turns before the file recovers.
                return {}
        return self._bans

    def ban(self, reader: str, *, days: int | None = None, note: str = "",
            force: bool = False) -> dict:
        """⛔⛔⛔ REFUSES A READER WHO HAS EVER BEEN SEEN ON AN UNTRUSTED
        ADDRESS. That reader id is not a person — it is whatever `client_ip`
        fell back to when the proxy signature was missing, which is Cloudflare's
        egress address and therefore everybody. Banning it takes the bench off
        the internet and looks exactly like a crash.

        ⭐ `force` exists because the operator may know better (a signature
        broke for an hour and the abuse is unambiguous), but it has to be typed.
        """
        reader = (reader or "").strip().lower()
        if len(reader) != _ID_CHARS or any(c not in "0123456789abcdef"
                                           for c in reader):
            return {"ok": False, "reason": "not a reader id",
                    "detail": "expected %d hex characters" % _ID_CHARS}
        try:
            conn = self._conn()
            try:
                untrusted = conn.execute(
                    "SELECT COUNT(*) AS n FROM turns "
                    "WHERE reader=? AND ip_trusted=0",
                    (reader,)).fetchone()["n"]
                untrusted += conn.execute(
                    "SELECT COUNT(*) AS n FROM events "
                    "WHERE reader=? AND ip_trusted=0",
                    (reader,)).fetchone()["n"]
                if untrusted and not force:
                    return {
                        "ok": False, "reason": "untrusted address",
                        "detail": "%d rows for this reader were recorded while "
                                  "the proxy signature was missing, so this id "
                                  "is Cloudflare's egress address — shared by "
                                  "every reader. Banning it bans everyone. Pass "
                                  "force=true only if you are certain."
                                  % untrusted}
                until = None if days is None else time.time() + days * 86400
                conn.execute(
                    "INSERT INTO bans (reader, at, until, note) VALUES "
                    "(?,?,?,?) ON CONFLICT(reader) DO UPDATE SET "
                    "at=excluded.at, until=excluded.until, note=excluded.note",
                    (reader, time.time(), until, _clip(note, 500)))
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:                                  # noqa: BLE001
            self._failed("ban", exc)
            return {"ok": False, "reason": "write failed", "detail": str(exc)}
        self._bans = None
        self.record_event(kind="ban.applied", reader=reader,
                          detail="days=%s note=%s" % (days, note))
        return {"ok": True, "reader": reader, "until": until}

    def unban(self, reader: str) -> dict:
        reader = (reader or "").strip().lower()
        try:
            conn = self._conn()
            try:
                cur = conn.execute("DELETE FROM bans WHERE reader=?", (reader,))
                conn.commit()
                gone = cur.rowcount
            finally:
                conn.close()
        except Exception as exc:                                  # noqa: BLE001
            self._failed("unban", exc)
            return {"ok": False, "reason": "write failed", "detail": str(exc)}
        self._bans = None
        self.record_event(kind="ban.lifted", reader=reader)
        return {"ok": True, "reader": reader, "removed": gone}

    # ── housekeeping ───────────────────────────────────────────────────────

    def prune(self) -> None:
        """⛔ THE VOLUME IS NOT INFINITE AND NOTHING ELSE WOULD EVER NOTICE.
        Flagged turns are kept three times longer: they are the ones somebody
        may want to look at weeks later, and there are very few of them."""
        now = time.time()
        plain = now - self.plain_days * 86400
        flagged = now - self.flagged_days * 86400
        try:
            conn = self._conn()
            try:
                conn.execute("DELETE FROM turns WHERE severity=0 AND at<?",
                             (plain,))
                conn.execute("DELETE FROM turns WHERE severity>0 AND at<?",
                             (flagged,))
                conn.execute("DELETE FROM errors WHERE at<?", (plain,))
                # ⭐ Ban bookkeeping outlives ordinary events — "why is this
                # reader banned" is a question asked long after the fact.
                conn.execute("DELETE FROM events WHERE at<? AND kind NOT LIKE "
                             "'ban.%'", (plain,))
                conn.execute("DELETE FROM events WHERE at<? AND kind LIKE "
                             "'ban.%'", (flagged,))
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:                                  # noqa: BLE001
            self._failed("prune", exc)

    def snapshot(self, name: str = "log-snapshot.sqlite3") -> dict:
        """A consistent copy to download.

        ⛔ `modal volume get` ON THE LIVE FILE CAN TEAR. It is in WAL mode and
        being written to; pulling it without the `-wal` sidecar can hand you a
        database that is missing the most recent turns or will not open at all.
        `VACUUM INTO` writes a single settled file, which is what the operator
        actually wants to carry home.
        """
        target = self.path.with_name(name)
        try:
            if target.exists():
                # ⛔ VACUUM INTO refuses to overwrite.
                target.unlink()
            conn = self._conn()
            try:
                conn.execute("VACUUM INTO ?", (str(target),))
            finally:
                conn.close()
        except Exception as exc:                                  # noqa: BLE001
            self._failed("snapshot", exc)
            return {"ok": False, "detail": str(exc)}
        return {"ok": True, "path": str(target), "bytes": target.stat().st_size}

    # ── reads (OPERATOR-SIDE ONLY — nothing here is ever served) ────────────

    def stats(self, *, full: bool = False) -> dict:
        """⛔ `full=False` IS WHAT `/healthz` GETS, AND THE DIFFERENCE IS NOT
        COSMETIC. A public count of FLAGGED turns lets an attacker binary-search
        the tripwire: send a probe, refresh `/healthz`, learn whether it fired.
        The public half answers only "is the log working"."""
        out = {"ok": self.failures == 0, "write_failures": self.failures,
               "pepper": pepper()[1]}
        if self.last_failure:
            out["last_failure"] = self.last_failure
        try:
            conn = self._conn()
            try:
                out["turns"] = conn.execute(
                    "SELECT COUNT(*) AS n FROM turns").fetchone()["n"]
                if full:
                    day = time.time() - 86400
                    out["flagged"] = conn.execute(
                        "SELECT COUNT(*) AS n FROM turns WHERE severity>0"
                    ).fetchone()["n"]
                    out["flagged_24h"] = conn.execute(
                        "SELECT COUNT(*) AS n FROM turns WHERE severity>0 "
                        "AND at>?", (day,)).fetchone()["n"]
                    out["errors"] = conn.execute(
                        "SELECT COUNT(*) AS n FROM errors").fetchone()["n"]
                    out["errors_24h"] = conn.execute(
                        "SELECT COUNT(*) AS n FROM errors WHERE at>?",
                        (day,)).fetchone()["n"]
                    out["readers"] = conn.execute(
                        "SELECT COUNT(DISTINCT reader) AS n FROM turns"
                    ).fetchone()["n"]
                    out["bans"] = conn.execute(
                        "SELECT COUNT(*) AS n FROM bans").fetchone()["n"]
                    # ⛔⛔ THE NUMBER THAT SAYS THE PER-IP LIMIT AND THE SESSION
                    # PASS ARE BOTH INERT. `/healthz`'s counters reset with the
                    # container; this one does not.
                    out["untrusted_turns"] = conn.execute(
                        "SELECT COUNT(*) AS n FROM turns WHERE ip_trusted=0"
                    ).fetchone()["n"]
            finally:
                conn.close()
        except Exception as exc:                                  # noqa: BLE001
            self._failed("stats", exc)
            out["ok"] = False
        return out
