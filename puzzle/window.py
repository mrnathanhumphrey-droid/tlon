"""THE WINDOW — the conversation, held server-side and re-fed each turn.

⭐⭐ THE ONTOLOGY, AND IT IS NATE'S: *"the window holds the moment; that is the
ontology, not a workaround."* A bench conversation is a series of infinitely
connected nows, and the context window IS that. Nothing here tries to make the
model remember. The model is stateless per call; this file is the memory.

⛔ THIS IS THE PUZZLE'S STORE, NOT THE ORACLE'S. The mechanism is lifted from
`D:\\SportsThought\\oracle\\conversations.py` — stdlib sqlite3, WAL, a
`history(conversation_id, max_turns=...)` read — because that store has already
survived two real corruptions in production and the repair ladder in it was paid
for. What is deliberately NOT lifted:

  * `user_email` / `owner()` — the puzzle is anonymous and public. A column that
    must never be filled is a privacy surface with no upside, so it does not
    exist. There is nothing here to leak.
  * `conversation_cost` / `user_spend` — those meter an API bill. This app runs
    its own weights; the ceiling it needs is compute, and that lives in
    `guard.py` where it can see the whole process rather than one row.

⛔ A TURN IS TWO ROWS, NOT ONE, and they are stored separately on purpose. The
user's English becomes a Tlön line (`you`), and THAT line provokes the reply
(`tlon`). Both are real Tlön surfaces a reader may want translated, so both
carry their own gloss. Collapsing them into one row would make the translate
button unable to name what it is translating.
"""
from __future__ import annotations

import pathlib
import sqlite3
import time
import uuid

#: ⛔ Roles are a CLOSED set and `append` refuses anything else. A typo'd role
#: would silently vanish from `history()`'s ordering and read as a dropped turn.
YOU, TLON = "you", "tlon"
ROLES = (YOU, TLON)

#: How many Tlön surfaces the window hands back by default. ⭐ This bounds the
#: prompt under the arena shape and bounds nothing under the trained shape —
#: see `speaker.py` for why the default shape ignores it.
DEFAULT_MAX_TURNS = 60

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    created_at      REAL NOT NULL,
    last_at         REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    turn            INTEGER NOT NULL,
    role            TEXT NOT NULL,          -- 'you' | 'tlon'
    english         TEXT,                   -- only the 'you' row has one
    surface         TEXT,                   -- the Tlön line; NULL if refused
    gloss           TEXT,                   -- austere render, pure function
    literary        TEXT,                   -- Borges-register render
    refused         TEXT,                   -- why the gate would not pass it
    created_at      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_messages_cid
    ON messages (conversation_id, turn, id);
"""


class ConversationStore:
    """The bench. One SQLite file, WAL, no ORM, no server."""

    def __init__(self, db_path: str | pathlib.Path):
        self.db_path = pathlib.Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._conn()
        try:
            conn.executescript(_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def _conn(self) -> sqlite3.Connection:
        # ⛔ `timeout` is the BUSY timeout, and it is not optional. Uvicorn runs
        # the turn in a worker thread, so two requests can reach the same file;
        # without it the second one raises "database is locked" and the user
        # loses a turn that actually generated.
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    # ── writes ──────────────────────────────────────────────────────────────

    def new_conversation(self) -> str:
        cid = uuid.uuid4().hex
        now = time.time()
        conn = self._conn()
        try:
            conn.execute("INSERT INTO conversations "
                         "(conversation_id, created_at, last_at) VALUES (?,?,?)",
                         (cid, now, now))
            conn.commit()
        finally:
            conn.close()
        return cid

    def append(self, conversation_id: str, turn: int, role: str, *,
               english: str | None = None, surface: str | None = None,
               gloss: str | None = None, literary: str | None = None,
               refused: str | None = None) -> None:
        if role not in ROLES:
            # ⛔ RAISE, NEVER DEFAULT. An unrecognised role quietly stored would
            # read back as a gap in the conversation and look like data loss.
            raise ValueError("unknown role %r; valid roles are %s"
                             % (role, ", ".join(ROLES)))
        now = time.time()
        conn = self._conn()
        try:
            conn.execute(
                "INSERT INTO messages (conversation_id, turn, role, english, "
                "surface, gloss, literary, refused, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (conversation_id, turn, role, english, surface, gloss,
                 literary, refused, now))
            conn.execute("UPDATE conversations SET last_at=? "
                         "WHERE conversation_id=?", (now, conversation_id))
            conn.commit()
        finally:
            conn.close()

    # ── reads ───────────────────────────────────────────────────────────────

    def exists(self, conversation_id: str) -> bool:
        conn = self._conn()
        try:
            row = conn.execute("SELECT 1 FROM conversations WHERE "
                               "conversation_id=?", (conversation_id,)).fetchone()
        finally:
            conn.close()
        return row is not None

    def idle_seconds(self, conversation_id: str) -> float | None:
        """How long since anything was said. None if there is no such bench.

        ⭐ THE OTHER HALF OF THE CONTEXT TIME-OUT. A bench that has gone cold is
        over: the next thing said starts a new moment rather than resuming one
        neither party remembers the shape of.
        """
        conn = self._conn()
        try:
            row = conn.execute("SELECT last_at FROM conversations WHERE "
                               "conversation_id=?", (conversation_id,)).fetchone()
        finally:
            conn.close()
        return None if row is None else time.time() - float(row["last_at"])

    def next_turn(self, conversation_id: str) -> int:
        conn = self._conn()
        try:
            row = conn.execute("SELECT MAX(turn) AS m FROM messages WHERE "
                               "conversation_id=?", (conversation_id,)).fetchone()
        finally:
            conn.close()
        return 0 if row is None or row["m"] is None else int(row["m"]) + 1

    def history(self, conversation_id: str,
                max_turns: int | None = DEFAULT_MAX_TURNS) -> list[dict]:
        """Every row, oldest first — the thing the page renders.

        ⭐ `max_turns` counts TURNS, not rows, because a turn is two rows and a
        row cap would cut a reply away from the line that provoked it.
        """
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT turn, role, english, surface, gloss, literary, refused,"
                " created_at FROM messages WHERE conversation_id=? "
                "ORDER BY turn ASC, id ASC", (conversation_id,)).fetchall()
        finally:
            conn.close()
        out = [dict(r) for r in rows]
        if max_turns is not None and out:
            keep = sorted({r["turn"] for r in out})[-max_turns:]
            out = [r for r in out if r["turn"] in keep]
        return out

    def surfaces(self, conversation_id: str,
                 max_turns: int | None = DEFAULT_MAX_TURNS) -> list[str]:
        """The Tlön surfaces alone, in order — what `exchange()` calls history.

        ⛔ REFUSED ROWS ARE ABSENT, not rendered as an empty string. A blank
        surface in this list would be handed to the model as a provocation the
        corpus never contains.
        """
        return [r["surface"] for r in self.history(conversation_id, max_turns)
                if r["surface"]]

    def threads(self, conversation_id: str,
                max_turns: int | None = DEFAULT_MAX_TURNS
                ) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        """The bench as two homogeneous (user, assistant) threads.

        ⭐⭐ THIS IS HOW THE WINDOW REACHES THE MODEL, AND WHY IT IS TWO LISTS
        AND NOT ONE. A turn runs the model twice under two DIFFERENT system
        prompts — `write` turns English into Tlön, `provoke` answers a Tlön
        line — and a chat template carries exactly one system message. Mixing
        both directions into a single thread would put half the exchanges under
        a framing that does not govern them. So each thread is homogeneous:
        every pair in it is an example of the same direction, taken from THIS
        conversation.

            write    (english_i, your_surface_i)
            provoke  (your_surface_i, its_surface_i)

        ⛔ Incomplete turns are dropped from BOTH. A pair whose assistant half
        is missing — a refusal, or a turn interrupted between its two rows —
        would enter the prompt as a question the model never answered, and the
        model's next move is to notice the gap rather than continue the bench.
        """
        rows = self.history(conversation_id, max_turns)
        by_turn: dict[int, dict[str, dict]] = {}
        for r in rows:
            by_turn.setdefault(r["turn"], {})[r["role"]] = r

        write: list[tuple[str, str]] = []
        provoke: list[tuple[str, str]] = []
        for turn in sorted(by_turn):
            you = by_turn[turn].get(YOU) or {}
            tlon = by_turn[turn].get(TLON) or {}
            if you.get("english") and you.get("surface"):
                write.append((you["english"], you["surface"]))
            if you.get("surface") and tlon.get("surface"):
                provoke.append((you["surface"], tlon["surface"]))
        return write, provoke
