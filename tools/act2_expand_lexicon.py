"""BUILD `lexicon_expanded.yaml` — the puzzle's language, one dose at a time.

⛔⛔ THE FROZEN LEXICON IS NOT TOUCHED. `tlon/grammar/lexicon.yaml`
(blake2b-16 `e2b8527010231a81fd31b6eeb9de3d8c`) was the measuring instrument for
every number in the research campaign; every artifact records that hash. Growing
it in place would silently invalidate all of them — the verdicts would still
read fine and would no longer be about the language they claim. So the expansion
is written to a SEPARATE file with its own hash, and the research keeps pointing
at the frozen one.

⭐ WHY A GENERATOR AND NOT A HAND-EDITED FILE. Nate's spec: "build so a second
expansion is a config bump, not a rewrite." Dose 2 is a new `EXPANSION_V*` dict
below and a bump to `DOSES`; nothing else moves. It also means the expanded file
is reproducible from the frozen one plus this table, which is a stronger artifact
than the file itself.

⛔ TEXT INSERTION, NOT A YAML ROUND-TRIP. `yaml.safe_load` then `yaml.dump`
would reformat all 400 lines, reorder keys and drop any comment — and the
resulting diff would be unreadable, so nobody could see that only the R block
grew. The frozen bytes are copied through untouched and the new roots are
spliced into the R block.

Usage:
    python tools/act2_expand_lexicon.py            # write + verify
    python tools/act2_expand_lexicon.py --check    # verify only, no write
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.grammar import classes as C                       # noqa: E402

FROZEN = pathlib.Path(C.__file__).with_name("lexicon.yaml")
EXPANDED = pathlib.Path(C.__file__).with_name("lexicon_expanded.yaml")

#: ⭐ DOSE 1 — 62 roots, +40% on the frozen 156.
#:
#: WHAT GAP THESE FILL. The frozen 156 are rich in weather, light, colour,
#: texture and interior state, and thin on exactly what a bench conversation is
#: made of: someone arriving, waiting, giving, carrying, working, tiring,
#: looking for something, saying something back. A speaker asked about a
#: person's day had almost nothing to reach for.
#:
#: ⛔⛔ NOTHING HERE NAMES. An earlier draft had a root "it names, calls by" and
#: it was cut: naming installs reference, and reference is the one thing Tlön
#: refuses. The moon in the story is not called — "axaxaxas mlö" is a fresh
#: impression each time, never a second mention of a first thing.
#:
#: ⛔ NOTHING HERE IS A SELF. No I, no you, no mine. `mlar` "it accompanies" is
#: as close as the language comes to another person, and it is still impersonal.
#:
#: ⭐ SOUND MATCHED TO THE EXISTING 156, NOT JUST TO LEGALITY. The first draft
#: was legal and surface-disjoint and still wrong: 1 of 62 used ö and none used
#: ä, against 26% umlaut in the frozen roots, so they read as a bolt-on. Coda
#: and nucleus distributions are now within a few points of the original.
EXPANSION_V1 = {
    # ── presence, company, coming and going ──────────────────────────────
    "tran":  "it arrives, comes to hand",
    "frox":  "it departs, goes from",
    "hlun":  "it waits, abides",
    "mlar":  "it accompanies, goes alongside",
    "krim":  "it parts from, leaves off",
    "plux":  "it meets, falls in with",
    "xen":   "it is wanting, is absent",
    "hröng": "it lingers, tarries",
    "kreng": "it returns, comes again",
    "lox":   "it greets, hails",
    # ── exchange ─────────────────────────────────────────────────────────
    "pran":  "it gives, hands over",
    "tlöng": "it receives, takes in hand",
    "flöm":  "it offers, holds out",
    "nör":   "it withholds, keeps back",
    "hläng": "it shares, divides among",
    "mrix":  "it owes, is beholden",
    "präng": "it repays, makes even",
    # ── holding and carrying ─────────────────────────────────────────────
    "klär":  "it carries, bears along",
    "trix":  "it grasps, takes hold",
    "frön":  "it releases, lets go",
    "pris":  "it lifts, raises",
    "näm":   "it sets down, lays",
    "tlos":  "it binds, ties fast",
    "mren":  "it loosens, unties",
    # ── labour, making, mending ──────────────────────────────────────────
    "kros":  "it labours, works at",
    "fläm":  "it wearies, tires",
    "hrax":  "it strains, bears down",
    "nul":   "it slackens, eases off",
    "höng":  "it tends, cares for",
    "plax":  "it fashions, makes",
    "träng": "it mends, repairs",
    # ── seeking, hiding, showing ─────────────────────────────────────────
    "fror":  "it seeks, searches",
    "klix":  "it finds, comes upon",
    "pron":  "it loses, lets slip",
    "hlem":  "it hides, conceals",
    "tlar":  "it shows, discloses",
    "xin":   "it watches, keeps vigil",
    "flen":  "it guards, keeps safe",
    # ── speech — acts, never reference ───────────────────────────────────
    "klis":  "it asks, inquires",
    "mras":  "it answers, replies",
    "tros":  "it tells, recounts",
    "hlis":  "it listens, attends",
    "fex":   "it hushes, falls silent",
    "prel":  "it assents, agrees",
    # ── mind and feeling ─────────────────────────────────────────────────
    "krox":  "it disputes, gainsays",
    "mlix":  "it wonders, marvels",
    "tröng": "it hesitates, wavers",
    "hlöng": "it hopes",
    "fris":  "it regrets, rues",
    "mlöm":  "it forgives, absolves",
    "xäm":   "it shames",
    # ── weather the frozen set never had ─────────────────────────────────
    "löm":   "it snows",
    # ── body and the passing day ─────────────────────────────────────────
    "hrel":  "it hungers",
    "klor":  "it thirsts",
    "päm":   "it eats, takes in",
    "tlen":  "it drinks",
    "mrax":  "it ages, grows old",
    "lin":   "it is new, is fresh",
    "hlur":  "it stirs, rouses",
    "frang": "it stretches, extends itself",
    "mrön":  "it comforts, soothes",
    "nang":  "it belongs, is at home",
}

#: ⛔ Every dose that has been applied, in order. Dose 2 appends here.
DOSES = (EXPANSION_V1,)


def expansion() -> dict[str, str]:
    out: dict[str, str] = {}
    for i, dose in enumerate(DOSES, 1):
        for form, meaning in dose.items():
            if form in out:
                raise SystemExit("⛔ %r appears in two doses" % form)
            out[form] = meaning
    del i
    return out


def build_text(frozen_text: str, new_roots: dict[str, str]) -> str:
    """Splice the new roots into the R block. Everything else is byte-identical.

    ⛔ THE INSERTION POINT IS THE END OF `  R:`, FOUND BY THE NEXT SIBLING KEY —
    not by a line number, which would rot the first time the frozen file gained
    a root, and not by appending at EOF, which would put roots under whatever
    class happens to be last.
    """
    lines = frozen_text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line == "  R:":
            start = i
            break
    if start is None:
        raise SystemExit("⛔ no '  R:' key in the frozen lexicon")

    end = None
    for i in range(start + 1, len(lines)):
        stripped = lines[i]
        # the next two-space key ends the R block
        if stripped and not stripped.startswith("    "):
            end = i
            break
    if end is None:
        raise SystemExit("⛔ could not find the end of the R block")

    block = ["    %s: %s" % (f, m) for f, m in new_roots.items()]
    return "\n".join(lines[:end] + block + lines[end:])


def verify(path: pathlib.Path, new_roots: dict[str, str]) -> dict:
    """Load the built file THROUGH THE REAL LOADER and check it.

    ⭐ `classes.load()` runs `_validate`, which is what enforces the two
    invariants that matter — every form is a legal syllable, and all classes are
    surface-disjoint for LL(1). Re-implementing those checks here would be a
    verifier that agrees with itself; using the loader means the expanded file
    is proved acceptable to the same code the app will run.
    """
    import os

    prior = os.environ.get("TLON_LEXICON")
    os.environ["TLON_LEXICON"] = str(path)
    try:
        C.load.cache_clear()
        lex = C.load()
        roots = lex["classes"]["R"]
        frozen_roots = _frozen_roots()
        missing = sorted(set(frozen_roots) - set(roots))
        if missing:
            raise SystemExit("⛔⛔ the expansion DROPPED frozen roots: %s" % missing)
        changed = sorted(f for f in frozen_roots
                         if roots.get(f) != frozen_roots[f])
        if changed:
            raise SystemExit("⛔⛔ the expansion REDEFINED frozen roots: %s" % changed)
        added = sorted(set(roots) - set(frozen_roots))
        if set(added) != set(new_roots):
            raise SystemExit("⛔ added set does not match the expansion table")
        return {"hash": lex["_hash"], "roots": len(roots), "added": len(added)}
    finally:
        C.load.cache_clear()
        if prior is None:
            os.environ.pop("TLON_LEXICON", None)
        else:
            os.environ["TLON_LEXICON"] = prior
        C.load.cache_clear()


def _frozen_roots() -> dict[str, str]:
    import yaml

    return yaml.safe_load(FROZEN.read_bytes())["classes"]["R"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="verify the existing expanded file; write nothing")
    args = ap.parse_args()

    frozen_text = FROZEN.read_text(encoding="utf-8")
    frozen_hash = hashlib.blake2b(FROZEN.read_bytes(), digest_size=16).hexdigest()
    new_roots = expansion()
    built = build_text(frozen_text, new_roots)

    if args.check:
        if not EXPANDED.exists():
            print("⛔ %s does not exist" % EXPANDED.name)
            return 1
        on_disk = EXPANDED.read_text(encoding="utf-8")
        if on_disk != built:
            print("⛔⛔ %s does NOT match what this table builds — it was "
                  "hand-edited, or a dose landed without a rebuild." % EXPANDED.name)
            return 1
    else:
        # ⛔ TEMP FILE, VERIFY, REPLACE. `open(p, "w")` truncates before the
        # write can fail, and this project has already lost a file to exactly
        # that — MEMORY.md left at 0 bytes.
        tmp = EXPANDED.with_suffix(".yaml.tmp")
        tmp.write_text(built, encoding="utf-8", newline="\n")
        if len(tmp.read_text(encoding="utf-8")) <= len(frozen_text):
            raise SystemExit("⛔ built file is not larger than the frozen one")
        tmp.replace(EXPANDED)

    info = verify(EXPANDED, new_roots)
    print("frozen   %s  %d roots  (UNTOUCHED)"
          % (frozen_hash, len(_frozen_roots())))
    print("expanded %s  %d roots  (+%d)"
          % (info["hash"], info["roots"], info["added"]))
    print("file     %s  %d bytes" % (EXPANDED.name, len(EXPANDED.read_bytes())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
