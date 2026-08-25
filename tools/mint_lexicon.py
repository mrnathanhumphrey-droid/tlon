"""Mint grammar/lexicon.yaml from hand-authored glosses + reserved forms.

Forms are NEVER hand-typed for roots. Glosses are (semantics needs judgement);
surface forms are allocated deterministically from the legal syllable space so
that collisions and phonotactic violations are impossible by construction.

Run once; the resulting lexicon.yaml is checked in and is the source of truth.
Re-running with the same inputs is bit-identical (no RNG, fixed order).
"""
from __future__ import annotations
import hashlib
import pathlib
import sys

import yaml

# ── Phonotactics (spec §2.1) ────────────────────────────────────────────────
_SIMPLE = ["p", "t", "k", "f", "s", "x", "h", "m", "n", "l", "r"]      # 11
_CLUSTERABLE = ["p", "t", "k", "f", "x", "h", "m"]                     # 7
# Clusters are the full {p t k f x h m} x {l r} series, not an ad hoc list.
ONSETS = ([""] + _SIMPLE
          + [c + liq for c in _CLUSTERABLE for liq in ("l", "r")])     # 1+11+14 = 26
NUCLEI = ["a", "e", "i", "o", "u", "ö", "ä"]                            # 7
CODAS = ["", "n", "ng", "m", "r", "s", "l", "x"]                       # 8


def legal_syllables() -> list[str]:
    out = []
    for o in ONSETS:
        for v in NUCLEI:
            for c in CODAS:
                out.append(o + v + c)
    return out


def is_legal(form: str) -> bool:
    return form in _LEGAL_SET


_LEGAL_SET = set(legal_syllables())

# ── Reserved forms: attested (Borges) + hand-chosen particles ───────────────
# Every particle form below was checked against the phonotactic table above.
# Deviations from GRAMMAR_SOUTHERN_v0.1.md are recorded in DEVIATIONS.

ORIENT = {
    "hlör": "upward", "nar": "downward", "tim": "inward", "pox": "outward",
    "krel": "across", "sung": "around", "flar": "under", "tex": "over",
    "hren": "in_front", "ung": "behind_beyond", "mix": "within",
    "lang": "along", "kon": "against", "sir": "between", "hlan": "hither",
    "xun": "thither", "tro": "atop", "fen": "beneath", "plas": "through",
    "nong": "past", "har": "amid", "sil": "apart", "hul": "together",
    "tlas": "askew",
}
RELATOR = {
    "u": "BEYOND", "sen": "AT", "tan": "ERE", "pos": "POST", "kra": "CAUS",
    "xom": "CONC", "mil": "SIM", "hlin": "CMP", "fro": "INSTR", "nix": "PART",
    "sul": "TOWARD", "hlim": "AMID",
}
ASPECT_ROOT = {
    "ax": "unceasing", "tes": "punctual_iterated", "hun": "inceptive",
    "mel": "terminative", "sor": "habitual", "nim": "momentary",
}
ASPECT_CLOSER = "as"
MODAL = {
    "xöl": "seen", "hrix": "heard", "ten": "felt", "plun": "inferred",
    "mar": "remembered", "xos": "dreamt", "nem": "denied", "hrin": "doubted",
    "mir": "wished", "frax": "feared",
}
DEGREE = {
    "fim": "faint", "les": "slight", "ron": "marked", "tos": "strong",
    "kral": "extreme", "xar": "overwhelming",
}
QUANT = {"sim": "once", "tur": "twice", "tren": "thrice",
         "nol": "oft", "fer": "ever", "pän": "never"}
TEMPORAL = {"nu": "now", "pral": "then_past", "krin": "then_future",
            "tar": "ere", "song": "since", "hres": "until",
            "ol": "always", "kim": "momentarily"}
ILLOC = {"ka": "ASSERT", "ki": "ASK", "ko": "WONDER", "ku": "URGE", "kä": "DENY"}

# Roots whose form is fixed (attested or published in spec v0.1 and legal).
ROOT_PINNED = {
    "mlö": "it moons, lunates", "fang": "it streams, flows on",
    "hrun": "it endures cold and unyielding", "xel": "it greens, vegetates",
    "pön": "it darkens", "lir": "it lightens, dawns",
    "tlan": "it winds, blows", "kris": "it cracks, fissures",
    "mun": "it warms", "fes": "it chills",
    "hlax": "it sounds, resonates", "nöl": "it stills, silences",
    "tris": "it burns", "mör": "it wets, damps",
    "klung": "it hollows, voids", "fral": "it crowds, teems",
    "säx": "it bounds, ends abruptly", "hom": "it rounds, curves",
    "pel": "it rises", "nur": "it falls",
    "xir": "it moves, displaces", "tang": "it rests, holds",
    "nel": "it sweetens", "krax": "it sharpens, is acute",
}

# Glosses awaiting a minted form. IMPERATIVE (spec §3.1): if a gloss can be
# pluralized, it is a noun and it is WRONG. Every entry here is a happening.
ROOT_GLOSSES_TO_MINT = [
    # light / celestial
    "it blazes overhead", "it stars, pricks brightly", "it dawns",
    "it dusks", "it darkens to night", "it gleams", "it shimmers",
    "it shades, cools without touching", "it dazzles", "it dims",
    # water
    "it pools, lies still and level", "it rains", "it waves, undulates",
    "it drips", "it freezes", "it thaws", "it mists", "it floods",
    "it drains, ebbs", "it laps",
    # earth / mineral
    "it sands, granulates", "it sifts fine and dry", "it clings wet and heavy",
    "it heaps",
    "it slopes", "it splits open", "it grinds", "it settles",
    # air
    "it stills, goes unbreathing", "it gusts", "it breathes", "it whirls",
    "it drifts",
    # fire / heat
    "it smokes", "it crumbles grey", "it glows", "it smoulders", "it flares",
    # growth / decay
    "it blooms", "it withers", "it sows", "it rots", "it sprouts",
    "it ripens", "it ferments",
    # motion
    "it leaps", "it crawls", "it flies", "it swims", "it trembles",
    "it flees", "it hunts", "it turns", "it approaches", "it recedes",
    "it scatters", "it converges", "it circles", "it halts",
    # perception / expression (impersonal — no perceiver is named)
    "it sees, is beheld", "it hears", "it touches", "it speaks",
    "it sings", "it weeps", "it laughs", "it sleeps", "it wakes",
    "it dreams", "it forgets", "it recalls",
    # vital
    "it dies", "it is born", "it breathes its last", "it quickens",
    "it heals", "it sickens",
    # sound
    "it rings", "it thuds", "it hisses", "it whispers", "it roars",
    "it echoes", "it creaks",
    # texture / substance
    "it roughens", "it smooths", "it softens", "it hardens",
    "it weighs, is heavy", "it buoys, unburdens", "it thickens",
    "it thins", "it dries", "it slicks",
    # shape
    "it lengthens", "it flattens", "it twists", "it bends", "it opens",
    "it closes", "it narrows", "it widens", "it points",
    # colour (as events, never as properties of things)
    "it reddens", "it blackens", "it whitens", "it blues", "it yellows",
    "it browns", "it silvers",
    # change / time
    "it begins", "it ends", "it persists", "it vanishes", "it appears",
    "it changes", "it repeats", "it interrupts",
    # affect
    "it aches", "it eases", "it dreads", "it longs", "it calms",
    "it rages", "it gladdens", "it grieves", "it startles",
    # pattern / marking — APPENDED 2026-08-18 on Nate's go.
    # APPEND ONLY. The allocator zips this list against a fixed syllable
    # ordering, so inserting anywhere but the end reshuffles every root after
    # the insertion point and silently rewrites the language.
    # Allowed under the option-C reasoning: banding is an impersonal happening
    # like "it greens", not a standing-for relation. No object is presupposed.
    "it stripes, runs barred", "it bands, girdles", "it mottles, blotches",
    "it dapples, flecks", "it veins, threads through",
]

DEVIATIONS = [
    # --- Two principled spec changes to the phonotactic table itself. ---
    ("codas {n ng r s l x}", "codas {n ng m r s l x}",
     "SPEC CHANGE: admitted 'm' to complete the nasal natural class n/ng/m. "
     "Rescues tim/sim/hom/fim. Stop codas p/t/k stay ILLEGAL: no attested "
     "Borges form has one (hlör, fang, mlö all end in sonorant or nothing)."),
    ("clusters {hl ml tl kl fl xl hr tr kr}",
     "clusters {p t k f x h m} x {l r}",
     "SPEC CHANGE: the 9-cluster list was ad hoc. Made it the full "
     "obstruent+liquid series (14). Rescues plas/plun/frax/fro/fral/pral. "
     "Syllable space 21*7*7=1029 -> 26*7*8=1456."),
    ("onsets: add d, v?", "REFUSED",
     "Voiced obstruents are absent from every attested form. The inventory "
     "is deliberately voiceless; dul/dur/ver were fixed instead of the table."),
    # --- Forms fixed against the (now final) table. ---
    ("sköl", "xöl", "MODAL seen: 'sk' is not a legal onset"),
    ("nok", "nong", "ORIENT past: 'k' is not a legal coda"),
    ("dul", "hul", "ORIENT together: 'd' is not an onset"),
    ("tek", "tes", "ASPECT punctual: 'k' is not a legal coda"),
    ("nif", "nim", "ASPECT momentary: 'f' is not a legal coda"),
    ("nek", "nem", "MODAL denied: 'k' is not a legal coda"),
    ("lek", "les", "DEGREE slight: 'k' is not a legal coda"),
    ("dur", "tur", "QUANT twice: 'd' is not an onset"),
    ("ver", "fer", "QUANT ever: 'v' is not an onset"),
    ("brek", "hres", "TEMPORAL until: 'b' is not an onset, 'k' not a coda"),
    ("sonk", "song", "TEMPORAL since: 'nk' is not a legal coda"),
    ("tref", "tren", "QUANT thrice: 'f' is not a legal coda"),
    ("kip", "kim", "TEMPORAL momentarily: 'p' is not a legal coda"),
    ("wex", "tlas", "ORIENT askew: 'w' is not an onset"),
    ("wir", "mir", "MODAL wished: 'w' is not an onset"),
    ("zir", "sir", "ORIENT between: 'z' is not an onset"),
    ("zul", "sul", "RELATOR TOWARD: 'z' is not an onset"),
    ("zor", "sor", "ASPECT habitual: 'z' is not an onset"),
    ("pök", "pön", "ROOT darkens: 'k' is not a legal coda"),
    ("tosk", "tos", "DEGREE strong: 'sk' is not a legal coda"),
    ("xarr", "xar", "DEGREE overwhelming: 'rr' is not a legal coda"),
    ("xoth", "xos", "MODAL dreamt: 'th' is not a legal coda"),
    # --- Collisions (LL(1) requires surface-disjoint classes). ---
    ("u (ORIENT)", "ung", "spec §9 Q1 resolved: split the dual-class u; "
                          "RELATOR keeps the attested 'u'"),
    ("hom̈", "hlim", "RELATOR AMID: diacritic hack removed (collided with ROOT hom)"),
    ("dul̈", "hrin", "MODAL doubted: diacritic hack removed"),
    ("sim̈", "song", "TEMPORAL since: diacritic hack removed (collided with QUANT sim)"),
    ("hlan̈", "pral", "TEMPORAL then_past: collided with ORIENT hlan"),
    ("xun̈", "krin", "TEMPORAL then_future: collided with ORIENT xun"),
    ("mel (ROOT)", "nel", "ROOT sweetens: collided with ASPECT root 'mel'"),
]


def main() -> int:
    reserved: dict[str, str] = {}
    errors: list[str] = []

    def claim(form: str, owner: str) -> None:
        if not is_legal(form):
            errors.append(f"PHONOTACTIC VIOLATION: {form!r} ({owner})")
            return
        if form in reserved:
            errors.append(f"COLLISION: {form!r} in {reserved[form]} and {owner}")
            return
        reserved[form] = owner

    for tbl, name in [(ORIENT, "O"), (RELATOR, "L"), (ASPECT_ROOT, "A"),
                      (MODAL, "M"), (DEGREE, "D"), (QUANT, "Q"),
                      (TEMPORAL, "T"), (ILLOC, "F"), (ROOT_PINNED, "R")]:
        for form in tbl:
            claim(form, name)
    claim(ASPECT_CLOSER, "A-closer")
    if errors:
        print(f"{len(errors)} problem(s) in the hand-authored tables:")
        for e in errors:
            print("  " + e)
        return 1

    # Deterministic allocator for the remaining roots.
    # Roots take a substantial shape: onset required, coda preferred. We walk
    # the syllable table in a fixed interleaved order so minted roots are
    # phonetically spread rather than clustered on one onset.
    pool = [s for s in legal_syllables() if s not in reserved]
    def shape_rank(s: str) -> tuple[int, int, str]:
        has_onset = any(s.startswith(o) and o for o in
                        sorted(ONSETS, key=len, reverse=True) if o)
        has_coda = any(s.endswith(c) and c for c in
                       sorted(CODAS, key=len, reverse=True) if c)
        return (0 if has_onset else 1, 0 if has_coda else 1, s)
    pool.sort(key=shape_rank)
    stride = 7  # coprime with 7*? -> interleave across nuclei, deterministic
    ordered = [pool[(i * stride) % len(pool)] for i in range(len(pool))]
    seen, spread = set(), []
    for s in ordered:
        if s not in seen:
            seen.add(s)
            spread.append(s)

    if len(ROOT_GLOSSES_TO_MINT) > len(spread):
        sys.exit("not enough syllables left to mint roots")

    minted = {}
    for form, gloss in zip(spread, ROOT_GLOSSES_TO_MINT):
        claim(form, "R")
        minted[form] = gloss

    roots = {**ROOT_PINNED, **minted}

    lex = {
        "spec_version": "0.1",
        "hemisphere": "southern",
        "phonotactics": {"onsets": ONSETS, "nuclei": NUCLEI, "codas": CODAS,
                         "legal_syllable_count": len(_LEGAL_SET)},
        "constraints": {"MAX_DEPTH": 3, "MAX_MORPHS": 24, "MIN_MORPHS": 2,
                        "MAX_CLAUSES_PER_PRED": 3, "MAX_ORIENT_PER_PRED": 2,
                        "MAX_ASPECT_REPS": 4},
        "classes": {
            "R": roots, "O": ORIENT, "L": RELATOR, "A": ASPECT_ROOT,
            "M": MODAL, "D": DEGREE, "Q": QUANT, "T": TEMPORAL, "F": ILLOC,
        },
        "aspect_closer": ASPECT_CLOSER,
        "deviations_from_spec_v0_1": [
            {"was": a, "now": b, "why": c} for a, b, c in DEVIATIONS
        ],
    }

    out = pathlib.Path(__file__).resolve().parents[1] / "tlon" / "grammar" / "lexicon.yaml"
    body = yaml.safe_dump(lex, allow_unicode=True, sort_keys=False, width=100)
    # newline="" defeats Windows \n -> \r\n translation. Without it the file
    # bytes differ from the bytes hashed here, and mint's hash disagrees with
    # classes.load()'s -- which matters now that docs pin the hash.
    out.write_text(body, encoding="utf-8", newline="")
    digest = hashlib.blake2b(body.encode("utf-8"), digest_size=16).hexdigest()

    counts = {k: len(v) for k, v in lex["classes"].items()}
    print(f"wrote {out}")
    print(f"lexicon_hash {digest}")
    print(f"legal syllable space {len(_LEGAL_SET)}   claimed {len(reserved)}"
          f"   free {len(_LEGAL_SET) - len(reserved)}")
    print("class sizes " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
