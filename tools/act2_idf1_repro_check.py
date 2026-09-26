"""Does the committed code still produce IDF-1's cited numbers?

⛔⛔ THIS FILE EXISTS FOR THE SAME REASON `act2_idf1.py` DOES. IDF-1's numbers
were produced by heredocs that left no artefact, and the check that they still
reproduce was itself nearly a throwaway script. A verification that lives only
in a scrollback verifies nothing the next time anyone asks.

⛔⛔ BOTH SIDES ARE READ FROM ARTEFACTS ON DISK. The first draft of this
comparison hand-typed the O-A/O-B/O-C block from the record and put O-B's lag-4
(0.1185) into O-A's row (0.1163). It then reported a DEVIATION against IDF-1
that did not exist. A number retyped while writing is not a number from the run,
and a comparison is only as trustworthy as the weaker of its two sides.

    python tools/act2_idf1_repro_check.py       # exit 0 iff every arm matches

Regenerate the right-hand side first:
    python tools/act2_idf1.py step2 > runs/act2/idf1/repro_step2.txt
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1] / "runs" / "act2" / "idf1"

#: The surviving IDF-1 artefacts. `step2a` is the O-C/O-A/O-B block, `step2b`
#: the O-B variants and the per-dose O-E kernel.
CITED = ("step2a.txt", "step2b.txt")
REPRO = "repro_step2.txt"

ROW = re.compile(
    r"^\s*(?P<tag>\S.*?)\s{2,}"
    r"lag1 prof (?P<p1>[-\d.]+) z\s*(?P<z1>[-+\d.]+)\s*\|\s*"
    r"lag2 prof (?P<p2>[-\d.]+) z\s*(?P<z2>[-+\d.]+)\s*\|\s*"
    r"lag3 prof (?P<p3>[-\d.]+) z\s*(?P<z3>[-+\d.]+)\s*\|\s*"
    r"lag4 prof (?P<p4>[-\d.]+) z\s*(?P<z4>[-+\d.]+)\s*$")

EXACT = re.compile(
    r"^\s*(?P<tag>\S.*?)\s{2,}exact (?P<e>[\d.]+)% · root-set (?P<r>[\d.]+)% "
    r"· blind (?P<b>[\d.]+)%\s*$")

LAGS = ("p1", "z1", "p2", "z2", "p3", "z3", "p4", "z4")


def parse(text: str):
    prof, fallback = {}, {}
    for line in text.splitlines():
        m = ROW.match(line)
        if m:
            d = m.groupdict()
            prof[d["tag"].strip()] = tuple(float(d[k]) for k in LAGS)
            continue
        m = EXACT.match(line)
        if m:
            d = m.groupdict()
            fallback[d["tag"].strip()] = (float(d["e"]), float(d["r"]),
                                          float(d["b"]))
    return prof, fallback


def main(argv=None) -> int:
    missing = [n for n in CITED + (REPRO,) if not (ROOT / n).exists()]
    if missing:
        # ⛔ A missing artefact is reported as MISSING, never silently treated
        # as "nothing to compare, therefore fine".
        print("⛔ ABSENT, so nothing was compared: %s" % ", ".join(missing))
        return 2

    cited, cited_fb = parse("\n".join(
        (ROOT / n).read_text(encoding="utf-8", errors="replace")
        for n in CITED))
    repro, repro_fb = parse(
        (ROOT / REPRO).read_text(encoding="utf-8", errors="replace"))

    if not cited:
        print("⛔ parsed ZERO arms out of the cited artefacts — the format "
              "changed and this check is measuring its own regex")
        return 2

    bad = 0
    print("IDF-1 reproduction — %s  vs  %s\n" % (" + ".join(CITED), REPRO))
    for tag in sorted(cited):
        if tag not in repro:
            print("  ⛔ MISSING FROM REPRO: %s" % tag)
            bad += 1
            continue
        a, b = cited[tag], repro[tag]
        if a == b:
            print("  %-14s IDENTICAL" % tag)
            continue
        bad += 1
        print("  %-14s ⛔ DIFFERS" % tag)
        for lbl, x, y in zip(LAGS, a, b):
            if x != y:
                print("        %s cited %s repro %s" % (lbl, x, y))
    print()
    for tag in sorted(cited_fb):
        if tag not in repro_fb:
            print("  ⛔ MISSING FALLBACK ROW: %s" % tag)
            bad += 1
            continue
        if cited_fb[tag] == repro_fb[tag]:
            print("  %-14s fallback IDENTICAL" % tag)
        else:
            bad += 1
            print("  %-14s fallback ⛔ DIFFERS: cited %s repro %s"
                  % (tag, cited_fb[tag], repro_fb[tag]))

    extra = sorted(set(repro) - set(cited))
    if extra:
        print("\n  (also produced, nothing cited to compare: %s)"
              % ", ".join(extra))
    print("\n%s" % ("⛔ %d MISMATCH(ES) — a DEVIATION against IDF-1, resolve "
                    "before IDF-1b fires" % bad if bad else
                    "✅ EVERY CITED ARM REPRODUCES IDENTICALLY. No deviation."))
    return 1 if bad else 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
