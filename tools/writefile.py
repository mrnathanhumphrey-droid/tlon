"""Write a file WITHOUT a shell in the loop, and prove what landed.

⛔⛔ THE PAPERCUT THIS KILLS. Composing a file inside a bash heredoc has mangled
this build three times: `\\n` inside the heredoc became a real newline and broke
the Python it was supposed to be writing. And the sibling failure is worse --
`Get-Content | Set-Content` in PowerShell has DESTROYED a source file here by
round-tripping it through BOM + CRLF + cp1252. Both failures share one shape:
the CONTENT PASSED THROUGH A TEXT LAYER THAT FELT ENTITLED TO REWRITE IT.

So this tool never lets content near a text layer:

    write   stdin is read as BYTES and written as BYTES. No newline
            translation, no encoding guess, no escape interpretation.
    check   the census that would have caught both failures -- sha256, byte
            count, LF/CRLF/CR tallies, BOM, and any control character that has
            no business being in source.

⭐ IT DOES NOT MAKE HEREDOCS SAFE, AND PRETENDING OTHERWISE WOULD BE THE SAME
MISTAKE AGAIN. Content still gets mangled before it reaches stdin. What actually
kills the papercut is: author the file with an editor/Write tool (no shell), then
run `check` and read the census. This tool is the VERIFY half; the write half
exists for the cases where content really does arrive as bytes on a pipe.

    python tools/writefile.py check --path tlon/product/chat.py
    python tools/writefile.py write --path out.txt < payload.bin
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys

# Characters that are legal UTF-8 but are almost always damage in a source
# file: NUL, the ANSI escape, and the C0 controls other than tab/newline.
_ALLOWED_CONTROL = {0x09, 0x0A, 0x0D}


def census(data: bytes) -> dict:
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n") - crlf
    cr = data.count(b"\r") - crlf
    text = None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        decode_error = str(exc)
    else:
        decode_error = None
    controls = sorted({f"0x{ord(c):02x}" for c in (text or "")
                       if ord(c) < 0x20 and ord(c) not in _ALLOWED_CONTROL})
    return {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bom": data.startswith(b"\xef\xbb\xbf"),
        "lf": lf, "crlf": crlf, "lone_cr": cr,
        "utf8": decode_error is None, "decode_error": decode_error,
        "stray_controls": controls,
    }


def _report(path: pathlib.Path, c: dict) -> int:
    print(f"{path}")
    print(f"  sha256 {c['sha256']}")
    print(f"  {c['bytes']} bytes · LF {c['lf']} · CRLF {c['crlf']} · "
          f"lone CR {c['lone_cr']}")
    bad = []
    if c["bom"]:
        bad.append("BOM present")
    if not c["utf8"]:
        bad.append(f"not UTF-8: {c['decode_error']}")
    if c["lf"] and c["crlf"]:
        bad.append(f"MIXED line endings ({c['lf']} LF, {c['crlf']} CRLF)")
    if c["lone_cr"]:
        bad.append(f"{c['lone_cr']} lone CR")
    if c["stray_controls"]:
        bad.append("stray control characters: "
                   + ", ".join(c["stray_controls"]))
    for b in bad:
        print(f"  !! {b}")
    if not bad:
        print("  ok — clean UTF-8, consistent line endings, no stray controls")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("write", help="stdin bytes -> path, verbatim")
    w.add_argument("--path", required=True)
    w.add_argument("--from", dest="src", default=None,
                   help="read from this file instead of stdin")
    w.add_argument("--force", action="store_true",
                   help="required to overwrite; the old sha256 is printed first")

    c = sub.add_parser("check", help="census an existing file")
    c.add_argument("--path", required=True)
    c.add_argument("--expect", default=None, help="fail unless sha256 matches")

    a = ap.parse_args(argv)
    path = pathlib.Path(a.path)

    if a.cmd == "check":
        if not path.exists():
            print(f"{path}: does not exist")
            return 2
        return _report(path, census(path.read_bytes()))

    data = (pathlib.Path(a.src).read_bytes() if a.src
            else sys.stdin.buffer.read())
    if path.exists():
        # ⛔ The overwrite is the dangerous direction; say what is being lost.
        old = census(path.read_bytes())
        print(f"  existing: {old['bytes']} bytes · sha256 {old['sha256']}")
        if not a.force:
            print("  refusing to overwrite without --force")
            return 2
    path.parent.mkdir(parents=True, exist_ok=True)
    # ⛔ BINARY. Text mode on Windows would turn every \n into \r\n and the
    # sha256 printed below would not be the sha256 of what was intended.
    with path.open("wb") as fh:
        fh.write(data)
    return _report(path, census(path.read_bytes()))


if __name__ == "__main__":
    raise SystemExit(main())
