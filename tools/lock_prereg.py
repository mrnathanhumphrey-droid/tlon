"""Lock a pre-registration by hashing its body.

Adopted from D:\\IC_experiments (`LOCK: b5c3929a (sha256[:8] of draft body at
lock)`). The point is that you cannot retrofit a hypothesis to a result once the
body is hashed -- so the mechanism has to be mechanical, not a note-to-self.

    python tools/lock_prereg.py docs/PREREG_X.md            # verify
    python tools/lock_prereg.py docs/PREREG_X.md --lock     # stamp
"""
from __future__ import annotations
import datetime as _dt
import hashlib
import pathlib
import re
import sys

LOCK_RE = re.compile(r"^- \*\*LOCK:\*\* .*$", re.M)
STATUS_RE = re.compile(r"^- \*\*Status:\*\* .*$", re.M)


def body_hash(text: str) -> str:
    """Hash everything EXCEPT the LOCK and Status lines, so stamping the file
    does not change its own hash."""
    stripped = STATUS_RE.sub("", LOCK_RE.sub("", text))
    # normalise line endings so a Windows checkout hashes like a Linux one
    stripped = stripped.replace("\r\n", "\n").strip()
    return hashlib.sha256(stripped.encode("utf-8")).hexdigest()[:8]


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    path = pathlib.Path(argv[0])
    text = path.read_text(encoding="utf-8")
    digest = body_hash(text)
    m = LOCK_RE.search(text)
    if m is None:
        print(f"{path.name}: no LOCK line found")
        return 2
    current = m.group(0)
    locked = "_(unset" not in current

    if "--lock" in argv:
        if locked and "--force" not in argv:
            print(f"{path.name}: already locked — {current.strip()}")
            print("Re-locking discards the guarantee. Pass --force if the body "
                  "genuinely changed before firing.")
            return 1
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M")
        line = (f"- **LOCK:** `{digest}` (sha256[:8] of draft body at lock, "
                f"{stamp}Z)")
        text = LOCK_RE.sub(line, text, count=1)
        text = STATUS_RE.sub("- **Status:** LOCKED — pre-registered. Not fired.",
                             text, count=1)
        path.write_text(text, encoding="utf-8", newline="")
        print(f"{path.name}: LOCKED {digest}")
        return 0

    if not locked:
        print(f"{path.name}: UNLOCKED (body hash would be {digest})")
        return 1
    found = re.search(r"`([0-9a-f]{8})`", current)
    stamped = found.group(1) if found else "?"
    if stamped == digest:
        print(f"{path.name}: VERIFIED {digest} — body unchanged since lock")
        return 0
    print(f"{path.name}: ⛔ TAMPERED — stamped {stamped}, body now hashes {digest}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
