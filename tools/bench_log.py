"""READ THE BENCH LOG — offline, on your own machine.

⛔⛔ THIS PRINTS EVERY READER'S CONVERSATION. Not the answer key — the log never
stores a reader's own line rendered into Tlön, which is the pair the puzzle
exists to withhold — but all of it at once is still everybody's bench beside a
stable id for each of them. That is why no route serves this file and why this
is a local script rather than an admin page: the half that could publish it
never gets a URL.

THE OPERATOR'S ROUND TRIP

    # 1 · settle a consistent copy on the volume (WAL means a live pull can tear)
    curl -sX POST -H "Authorization: Bearer $TLON_ADMIN_TOKEN" \\
         https://tlon.resolveresearcher.com/admin/snapshot

    # 2 · carry it home
    modal volume get tlon-bench-db log-snapshot.sqlite3 .

    # 3 · read it
    python tools/bench_log.py log-snapshot.sqlite3 --flagged --since 7d
    python tools/bench_log.py log-snapshot.sqlite3 --errors --since 24h
    python tools/bench_log.py log-snapshot.sqlite3 --reader a1b2c3d4e5f60718

    # 4 · if it warrants one, ban the reader (30 days, with a note)
    curl -sX POST -H "Authorization: Bearer $TLON_ADMIN_TOKEN" \\
         -H "content-type: application/json" \\
         -d '{"reader":"a1b2c3d4e5f60718","days":30,"note":"prompt injection"}' \\
         https://tlon.resolveresearcher.com/admin/ban

⭐ `reader` IS THE ONLY IDENTITY IN THE FILE — an HMAC of the address under a
server-side pepper. You cannot get an IP back out of it, and you do not need
one: the ban takes the same string.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sqlite3
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from puzzle import tripwire                                    # noqa: E402

_SINCE = re.compile(r"^(\d+)\s*([dhm])$", re.I)


def since_seconds(text: str) -> float:
    """`7d`, `24h`, `30m`. ⛔ Raises rather than defaulting: a mistyped window
    that silently became "everything" would make a quiet week look like a busy
    one."""
    m = _SINCE.match((text or "").strip())
    if not m:
        raise SystemExit("--since wants something like 7d, 24h or 30m; got %r"
                         % text)
    n, unit = int(m.group(1)), m.group(2).lower()
    return n * {"d": 86400, "h": 3600, "m": 60}[unit]


def when(at: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(at))


def connect(path: pathlib.Path) -> sqlite3.Connection:
    if not path.exists():
        raise SystemExit("no log at %s — snapshot it and `modal volume get` it "
                         "first (see this file's docstring)" % path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _floor(args) -> float:
    return 0.0 if args.since is None else time.time() - since_seconds(args.since)


def show_turns(conn, args, *, min_severity: int) -> None:
    sql = "SELECT * FROM turns WHERE at>=? AND severity>=? "
    params: list = [_floor(args), min_severity]
    if args.reader:
        sql += "AND reader=? "
        params.append(args.reader)
    sql += "ORDER BY at DESC LIMIT ?"
    params.append(args.limit)
    rows = conn.execute(sql, tuple(params)).fetchall()
    if not rows:
        print("no turns matched.")
        return
    for r in rows:
        mark = "!" * r["severity"] if r["severity"] else " "
        print("%s %-3s %s  turn %s  %s" % (
            when(r["at"]), mark, r["reader"], r["turn"],
            "" if r["ip_trusted"] else "⛔ADDRESS UNTRUSTED — NOT BANNABLE"))
        if r["flags"]:
            print("    flags : %s" % r["flags"])
            print("            (%s)" % tripwire.explain(r["flags"]))
        print("    said  : %s" % (r["english"] or "").replace("\n", " ⏎ "))
        if r["surface"]:
            print("    tlön  : %s" % r["surface"])
        if r["refused"]:
            print("    refused: %s" % r["refused"])
        print()
    print("%d row(s). Ban one with its reader id — see this file's docstring."
          % len(rows))


def show_errors(conn, args) -> None:
    rows = conn.execute(
        "SELECT * FROM errors WHERE at>=? ORDER BY at DESC LIMIT ?",
        (_floor(args), args.limit)).fetchall()
    if not rows:
        print("no errors. ⭐ Check `--stats` too: a log that stopped writing "
              "also has no errors.")
        return
    for r in rows:
        print("%s  %s %s -> %s  [%s]  %.2fs  req=%s" % (
            when(r["at"]), r["method"], r["route"], r["status"], r["kind"],
            r["seconds"] or 0.0, r["request_id"]))
        print("    %s" % (r["detail"] or ""))
        if r["traceback"] and args.traceback:
            for line in (r["traceback"] or "").rstrip().splitlines():
                print("      " + line)
        print()
    print("%d error(s). Add --traceback for the stacks." % len(rows))


def show_events(conn, args) -> None:
    sql = "SELECT * FROM events WHERE at>=? "
    params: list = [_floor(args)]
    if args.kind:
        sql += "AND kind LIKE ? "
        params.append(args.kind.replace("*", "%"))
    if args.reader:
        sql += "AND reader=? "
        params.append(args.reader)
    sql += "ORDER BY at DESC LIMIT ?"
    params.append(args.limit)
    rows = conn.execute(sql, tuple(params)).fetchall()
    for r in rows:
        print("%s  %-20s %s  %s" % (when(r["at"]), r["kind"],
                                    r["reader"] or "-", r["detail"] or ""))
    print("%d event(s)." % len(rows))


def show_bans(conn) -> None:
    rows = conn.execute("SELECT * FROM bans ORDER BY at DESC").fetchall()
    if not rows:
        print("nobody is banned.")
        return
    now = time.time()
    for r in rows:
        state = ("forever" if r["until"] is None
                 else ("until %s" % when(r["until"]) if r["until"] > now
                       else "EXPIRED %s" % when(r["until"])))
        print("%s  %s  %-22s %s" % (when(r["at"]), r["reader"], state,
                                    r["note"] or ""))


def show_stats(conn, args) -> None:
    floor = _floor(args)
    q = lambda sql, *p: conn.execute(sql, p).fetchone()[0]           # noqa: E731
    print("turns          : %d  (%d in window)"
          % (q("SELECT COUNT(*) FROM turns"),
             q("SELECT COUNT(*) FROM turns WHERE at>=?", floor)))
    print("distinct readers: %d"
          % q("SELECT COUNT(DISTINCT reader) FROM turns WHERE at>=?", floor))
    print("errors         : %d  (%d in window)"
          % (q("SELECT COUNT(*) FROM errors"),
             q("SELECT COUNT(*) FROM errors WHERE at>=?", floor)))
    untrusted = q("SELECT COUNT(*) FROM turns WHERE ip_trusted=0")
    print("untrusted turns: %d%s" % (
        untrusted,
        "   ⛔⛔ the proxy signature is broken — every reader shares one "
        "identity, the per-IP limit is a second global limit, and NONE of "
        "these rows can be banned" if untrusted else ""))
    print("bans           : %d" % q("SELECT COUNT(*) FROM bans"))
    print()
    print("flags in window:")
    rows = conn.execute("SELECT flags, COUNT(*) AS n FROM turns "
                        "WHERE at>=? AND flags<>'' GROUP BY flags "
                        "ORDER BY n DESC", (floor,)).fetchall()
    if not rows:
        print("  (none)")
    for r in rows:
        print("  %4d  %s" % (r["n"], r["flags"]))
    print()
    print("events in window:")
    for r in conn.execute("SELECT kind, COUNT(*) AS n FROM events WHERE at>=? "
                          "GROUP BY kind ORDER BY n DESC", (floor,)):
        print("  %4d  %s" % (r["n"], r["kind"]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", nargs="?", default="log-snapshot.sqlite3",
                    type=pathlib.Path)
    ap.add_argument("--since", default=None,
                    help="window, e.g. 7d / 24h / 30m (default: everything)")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--reader", default=None, help="one reader id")
    ap.add_argument("--flagged", action="store_true",
                    help="turns the tripwire marked (severity >= 2)")
    ap.add_argument("--min-severity", type=int, default=tripwire.INJECTION,
                    help="1 includes boundary probing (asking for English, "
                         "asking for the word list) — expected, not abuse")
    ap.add_argument("--turns", action="store_true", help="all turns")
    ap.add_argument("--errors", action="store_true")
    ap.add_argument("--traceback", action="store_true")
    ap.add_argument("--events", action="store_true")
    ap.add_argument("--kind", default=None, help="event kind, * allowed")
    ap.add_argument("--bans", action="store_true")
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    conn = connect(args.path)
    try:
        did = False
        if args.stats:
            show_stats(conn, args); did = True
        if args.bans:
            show_bans(conn); did = True
        if args.errors:
            show_errors(conn, args); did = True
        if args.events:
            show_events(conn, args); did = True
        if args.flagged or args.turns or args.reader:
            show_turns(conn, args,
                       min_severity=0 if (args.turns or args.reader)
                       else args.min_severity)
            did = True
        if not did:
            # ⭐ The useful default, not a usage error: the two questions an
            # operator actually arrives with are "is it healthy" and "is
            # anybody attacking it".
            show_stats(conn, args)
            print()
            show_turns(conn, args, min_severity=tripwire.INJECTION)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
