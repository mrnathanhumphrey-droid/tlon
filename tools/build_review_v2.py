"""Generate the v2 (Cosmicomics) signature review page.

Generated, never hand-written: the page must not be able to drift from the file
it is reviewing. Reuses `build_review_page`'s CSS so the review surface keeps
one look, and `witness()` so what is shown is the SAME minimal utterance the
gate would accept -- the loosest thing that counts as the referent.

⛔ NO MEASUREMENT NUMBERS ON THIS PAGE beyond satisfiability. Consistency-set
size, omission ceiling and the RSA frontier are 9.2's, prereg-locked. Putting
them in front of the artistic review is how the detector ends up choosing the
imagery.
"""
from __future__ import annotations

import html
import itertools
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar import classes as C                       # noqa: E402
from tlon.grammar.gloss import gloss                        # noqa: E402
from tlon.grammar.parse import render                       # noqa: E402
from tlon.referents import schema                           # noqa: E402
from build_review_page import CSS, e, roots_of              # noqa: E402
from signature_report import witness                        # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "signature_review_v2.html"
COV = ROOT / "runs" / "coverage_v2.json"

SECTIONS = [
    ("I. The standing world",
     "The moon so low the sea humps up under it. Most concrete, most "
     "interlocking, and the vocabulary every later section reuses. Nine of the "
     "eleven matrix-rule changes are here.",
     [f"M{i:02d}" for i in range(1, 13)]),
    ("II. The climb",
     "Orientation-heavy. Up and down exchange places; weight leaves the body.",
     [f"M{i:02d}" for i in range(13, 25)]),
    ("III. The recession",
     "The distance stops holding. This is the section the theme makes "
     "dangerous — it is a story about an invariant failing, and it is not a "
     "measurement.",
     [f"M{i:02d}" for i in range(25, 34)]),
    ("IV. What remains",
     "Abstractions. Concrete-weighted first was the ruling, so the four most "
     "abstract are declared and held back until the listener is calibrated.",
     [f"M{i:02d}" for i in range(34, 42)]),
    ("V. The water and the waiting",
     "More of section I's world, added for collision density: every root here "
     "already appears above, which is the point.",
     [f"M{i:02d}" for i in range(42, 51)]),
]


def main() -> int:
    rs = schema.load(schema.V2_PATH, allow_unreviewed=True)
    refs = {r.id: r for r in rs.referents}
    lex = C.load()
    cov = json.loads(COV.read_text(encoding="utf-8")) if COV.exists() else None
    reach = {r["id"]: r for r in cov["referents"]} if cov else {}

    shared: dict[str, set[str]] = {r.id: set() for r in rs.referents}
    for a, b in itertools.combinations(rs.referents, 2):
        if set(roots_of(a.signature)) & set(roots_of(b.signature)):
            shared[a.id].add(b.id)
            shared[b.id].add(a.id)

    def card(r: schema.Referent) -> str:
        w = witness(r.signature)
        surf = render(w) if w else "— unsatisfiable —"
        gl = gloss(w) if w else ""
        nested = [p for p in r.signature.contains if p.at_depth and p.at_depth > 1]
        cls = "card" + ("" if r.seed_2a else " flagged")
        tags = []
        if not r.seed_2a:
            tags.append('<span class="tag t-unval">held back · '
                        'seed_2a: false</span>')
        if nested:
            tags.append('<span class="tag t-weak">nested · at_depth 2</span>')
        if len(r.signature.contains) == 4:
            tags.append('<span class="tag t-weak">4 patterns · clause cap</span>')
        if any(p.aspect_root_any for p in r.signature.contains):
            asp = [x for p in r.signature.contains for x in p.aspect_root_any]
            tags.append(f'<span class="tag t-weak">signature aspect · '
                        f'{e(", ".join(asp))}</span>')
        n_sh = len(shared.get(r.id, ()))
        tags.append(f'<span class="tag t-over">shares roots with '
                    f'{n_sh} others</span>')
        rc = reach.get(r.id)
        if rc and rc["reachable"] < rc["subsets"]:
            tags.append('<span class="tag t-over">'
                        f'{rc["reachable"]}/{rc["subsets"]} subsets buildable'
                        '</span>')
        rootlist = ", ".join(
            f"{e(x)} <span style='opacity:.65'>{e(lex['classes']['R'][x])}</span>"
            for x in dict.fromkeys(roots_of(r.signature)))
        note = f'<p class="note">{e(r.notes.strip())}</p>' if r.notes.strip() else ""
        return f"""<article class="{cls}">
<div class="chead"><span class="pid">{e(r.id)}</span>
<span class="pname">{e(r.name)}</span></div>
<div class="spec">{e(surf)}</div>
<p class="gloss">“{e(gl)}”</p>
{note}
<div class="tags">{''.join(tags)}</div>
<div class="meta"><span><b>{len(surf.split())}</b> morphemes</span>
<span><b>{len(r.signature.contains)}</b> required nodes</span></div>
<details><summary>signature roots</summary><p class="mini">{rootlist}</p></details>
</article>"""

    secs = ""
    for title, lede, ids in SECTIONS:
        cards = "".join(card(refs[i]) for i in ids if i in refs)
        secs += (f'<h2>{e(title)}</h2><p class="lede">{e(lede)}</p>'
                 f'<div class="grid">{cards}</div>')

    n_live = sum(1 for r in rs.referents if r.seed_2a)
    reach_line = ("" if not cov else
                  f'{cov["subsets_reachable"]}/{cov["subsets_total"]} '
                  f'selection subsets buildable')

    body = f"""<div class="wrap">
<p class="eyebrow">Tlön · phase 9.1 · The Distance of the Moon</p>
<h1>Referent set v2, awaiting your pass</h1>
<p class="lede">Fifty referents from one Calvino story. Each shows the
<em>minimal</em> legal utterance satisfying its signature — the loosest thing the
gate accepts. <b>The italic gloss is the thing to judge:</b> if the minimum
already reads as the referent, the signature holds; if it reads as anything at
all, it is too loose.</p>
<span class="status">review_status: {e(rs.review_status.lower())} — execution
blocked · {n_live} live + {len(rs.referents)-n_live} held back · {e(reach_line)}</span>

<h2>The matrix rule, applied</h2>
<p class="lede">You approved the fix. <b>The matrix predication is the world's
persisting event; the distinguishing happening is a dependent.</b> This story
has exactly two persisting events — the mooning and the sea — and Calvino
narrates every human action as subordinate to the cosmological one. Applied to
eleven: M03 M04 M06 M07 M08 M09 M12 M23 M31 M32 M43.</p>
<div class="calls">
<div class="call"><h3>Two came out better as images, not just as structure</h3>
<p>M06's pores used to nest inside the mooning; they now nest inside the
<em>roughened underside</em>, which is where they are. M07's curd now sits in
the pore, in the moon — three levels, and each one true. The linguistic reason
came first: the matrix verb is <em>what is happening</em>, everything else is
<em>how</em>. The collision gain follows from it.</p></div>
<div class="call"><h3>Where I refused it, and why</h3>
<p><b>M10</b> — the nesting <em>is</em> the image; the referent is that the moon
sits at depth 2, inside the water, and matrix-<code>mlö</code> puts it at depth 0.
<b>M45</b> — the causation would <em>invert</em>: <code>kra</code> is CAUS one
way only, so “a weighing because of a mooning” is true and matrix-<code>mlö</code>
forces “a mooning because of a weighing,” which is false. <b>M17, M29, M40</b> —
no cosmological body is in the impression; the unburdening, the bending and the
recalling are the events. <b>M41</b> — the deliberate shallow control.</p></div>
<div class="call"><h3>Eleven, not the nine I predicted</h3>
<p>Moving <code>säx</code> off M12's head and <code>kron</code> off M23's made
<b>M26 and M46 — previously shared — newly unique</b>. The count is a property of
the whole set, not of the referents changed. I did not chase them: neither has a
cosmological body in its impression, and applying a rule where it does not hold
in order to move a number is the thing this ordering exists to prevent.
<b>11/50 = 22 %, down from 26/60 = 43 %.</b></p></div>
<div class="call"><h3>Still open: breadth, and it is 9.2's to answer</h3>
<p>Three of the eleven needed a fourth pattern to keep their content once the
head moved, so 4-pattern referents went 4 → 6 and mean breadth 3.06 → 3.10. That
fell out of faithfulness, not targeting. It is still small, so <b>Phase 7's
complaint stands</b>: nesting does not add a dependent, it moves one deeper, and
the omission ceiling may not move much.</p></div>
</div>

<h2>What I ruled on myself, and why</h2>
<div class="calls">
<div class="call"><h3>No <code>forbid</code>, three negations written as “despite”</h3>
<p>The deaf cousin (M18), the tide that does not return (M32), the pole that
bends anyway (M29). <code>forbid</code> was the obvious encoding and it does
<em>not</em> denote — using it would have narrowed Phase 6's isolation claim for
the whole set. Written as CONC <code>xom</code> instead, which denotes and is
truer: he does not lack the senses, he does not need them.</p></div>
<div class="call"><h3>Two near-misses where the meaning would have evaporated at π</h3>
<p>M32 wanted <code>pän</code> (never) and M45 wanted the modal <code>ten</code>
(felt). <b>π strips quant and modal.</b> Both referents would have projected down
to something indistinguishable from a plain ebbing and a plain weighing — a
silent semantic leak, caught while writing rather than in a verdict. Carried by
<code>xom</code> and <code>lis</code> instead.</p></div>
<div class="call"><h3>M38 and M50 are held back for a reason beyond abstraction</h3>
<p>They state Calvino's engine flat — the relation surviving its objects — which
is the conservation claim <b>Phase 8 retracted</b>. A referent that says the
thesis out loud, sitting in the live set while we measure the thesis, is a
compositional pressure toward believing it. Declared so the world is complete,
withheld so they cannot whisper into a measurement.</p></div>
<div class="call"><h3>The ladder is the hardest thing here</h3>
<p>M05, M22. Tlön has no way to say “carrying” that does not imply a carried
thing; M22 uses the instrumental <code>fro</code> and the strain is real. If the
gloss reads as mush, that is the one I would cut first.</p></div>
</div>

{secs}

<footer>
<p>Generated from <code>tlon/referents/referents_v2.yaml</code> against lexicon
<code>{e(lex['_hash'])}</code>. The page cannot drift from the file — it is built
from it. Coverage from <code>runs/coverage_v2.json</code>.</p>
<p>Not on this page, deliberately: consistency-set size, the omission ceiling,
the RSA frontier. Those are 9.2 under a locked prereg. Showing a detector
reading next to an artistic choice is how the detector ends up making it.</p>
</footer>
</div>"""

    OUT.write_text(
        f"<title>Tlön Referents v2</title>\n<style>{CSS}</style>\n{body}",
        encoding="utf-8")
    print(f"wrote {OUT}  ({len(rs.referents)} referents, {n_live} live)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
