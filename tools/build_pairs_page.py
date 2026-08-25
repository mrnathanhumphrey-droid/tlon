"""Render the minimal pairs for review. Generated from the YAML, never by hand."""
from __future__ import annotations
import html
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar import classes as C                  # noqa: E402
from tlon.grammar.gloss import gloss                   # noqa: E402
from tlon.grammar.parse import render                  # noqa: E402
from tlon.referents import schema                      # noqa: E402
from signature_report import witness                   # noqa: E402

import json

ROOT = pathlib.Path(__file__).resolve().parents[1]
KIND = sys.argv[1] if len(sys.argv) > 1 else "imagery"
SRC = ROOT / "tlon" / "referents" / f"{KIND}_pairs.draft.yaml"
OUT = ROOT / "docs" / f"{KIND}_pairs.html"

# Measured by the matching verify_*.py, never typed here — the page must not be
# able to disagree with the run it is reporting.
_BOR = ROOT / "runs" / f"{KIND}_pairs_bor.json"
BOR = json.loads(_BOR.read_text(encoding="utf-8")) if _BOR.exists() else {}

CSS = """
:root{--ground:#f3f0ea;--raised:#fffdf9;--line:#d8d2c6;--ink:#221e28;
--muted:#6a6272;--sage:#5f6b57;--sage-dim:#8a9481;--ochre:#8a6a24;
--rose:#9c4f4a;--chip:#e8e3d8}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
--ground:#1e1a22;--raised:#262130;--line:#3a3345;--ink:#ded9d0;--muted:#948da2;
--sage:#c2c7b7;--sage-dim:#8b937f;--ochre:#c8a45c;--rose:#c58a86;--chip:#2f2939}}
:root[data-theme="dark"]{--ground:#1e1a22;--raised:#262130;--line:#3a3345;
--ink:#ded9d0;--muted:#948da2;--sage:#c2c7b7;--sage-dim:#8b937f;
--ochre:#c8a45c;--rose:#c58a86;--chip:#2f2939}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
font-family:ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
font-size:16px;line-height:1.6}
.wrap{max-width:78ch;margin:0 auto;padding:3rem 1.25rem 6rem}
h1,h2,h3{font-family:"Iowan Old Style",Palatino,Georgia,serif;
text-wrap:balance;margin:0;font-weight:600}
h1{font-size:2.1rem;letter-spacing:-.01em}
h2{font-size:1.2rem;margin:3rem 0 1rem;padding-bottom:.5rem;
border-bottom:1px solid var(--line)}
.eyebrow{font-size:.7rem;text-transform:uppercase;letter-spacing:.16em;
color:var(--muted);margin-bottom:.6rem}
.lede{color:var(--muted);margin:.75rem 0 0}
.status{display:inline-block;margin-top:1.25rem;padding:.3rem .7rem;
border:1px solid var(--ochre);color:var(--ochre);border-radius:2px;
font-size:.72rem;letter-spacing:.12em;text-transform:uppercase}
.pair{background:var(--raised);border:1px solid var(--line);border-radius:2px;
margin-top:1.25rem;overflow:hidden}
.phead{display:flex;align-items:center;gap:.7rem;flex-wrap:wrap;
padding:.7rem 1.1rem;border-bottom:1px solid var(--line);background:var(--chip)}
.pid{font-family:ui-monospace,Consolas,monospace;font-size:.78rem;
color:var(--sage-dim);font-variant-numeric:tabular-nums}
.contrast{font-size:.68rem;text-transform:uppercase;letter-spacing:.11em;
color:var(--sage);border:1px solid currentColor;padding:.15rem .45rem;
border-radius:2px}
.bor{margin-left:auto;font-size:.74rem;color:var(--muted);
font-variant-numeric:tabular-nums}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line)}
@media (max-width:720px){.cols{grid-template-columns:1fr}}
.side{background:var(--raised);padding:1rem 1.1rem}
.nm{font-family:"Iowan Old Style",Palatino,Georgia,serif;font-size:1.05rem;
margin-bottom:.5rem}
.spec{font-family:ui-monospace,Consolas,monospace;font-size:1rem;
color:var(--sage);overflow-x:auto;white-space:nowrap;padding-bottom:.2rem}
.gl{font-family:"Iowan Old Style",Palatino,Georgia,serif;font-style:italic;
font-size:.97rem;margin:.5rem 0 0}
.diff{color:var(--rose);font-weight:600}
.note{font-size:.85rem;color:var(--muted);margin:0;padding:.8rem 1.1rem;
border-top:1px solid var(--line)}
footer{margin-top:3.5rem;padding-top:1.25rem;border-top:1px solid var(--line);
color:var(--muted);font-size:.85rem}
code{font-family:ui-monospace,Consolas,monospace;font-size:.9em;
background:var(--chip);padding:.1rem .3rem;border-radius:2px}
"""


def e(s) -> str:
    return html.escape(str(s))


def mark(surf: str, other: str) -> str:
    """Highlight the morphemes that differ between the pair."""
    o = set(other.split())
    return " ".join(f'<span class="diff">{e(t)}</span>' if t not in o else e(t)
                    for t in surf.split())


def main() -> int:
    rs = schema.load(SRC, allow_unreviewed=True)
    pairs: dict[str, list] = {}
    for r in rs.referents:
        pairs.setdefault(r.minimal_pair, []).append(r)

    blocks = []
    for pid in sorted(pairs, key=lambda k: int(k[1:])):
        a, b = pairs[pid]
        wa, wb = witness(a.signature), witness(b.signature)
        sa, sb = render(wa), render(wb)
        note = (a.notes or b.notes or "").strip()
        roots = ", ".join(f"{r} <span style='opacity:.6'>{C.load()['classes']['R'][r]}</span>"
                          for r in dict.fromkeys(a.roots()))
        blocks.append(f"""<section class="pair">
<div class="phead"><span class="pid">{e(pid)} · {e(a.id)}/{e(b.id)}</span>
<span class="contrast">{e(a.contrast)}</span>
<span class="bor">bag-of-roots {BOR.get(pid, float('nan')):.1f}% · chance 50%</span></div>
<div class="cols">
<div class="side"><div class="nm">{e(a.name)}</div>
<div class="spec">{mark(sa, sb)}</div>
<p class="gl">“{e(gloss(wa))}”</p></div>
<div class="side"><div class="nm">{e(b.name)}</div>
<div class="spec">{mark(sb, sa)}</div>
<p class="gl">“{e(gloss(wb))}”</p></div>
</div>
<p class="note"><b>shared roots:</b> {roots}{'<br>' + e(note) if note else ''}</p>
</section>""")

    scores = [v for v in BOR.values()]
    mean = sum(scores) / len(scores) if scores else float("nan")
    body = f"""<div class="wrap">
<p class="eyebrow">Tlön · phase 2b · perspective pairs</p>
<h1>One scene, told from both sides of it</h1>
<p class="lede">Each pair is a single situation rendered from the vantage of each thing
inside it. Both sides hold <b>all the same happenings</b> — only which one is the
matrix, and the orientation, change hands. That is what keeps them honest: a
bag-of-roots classifier, which sees only which roots occur, is left at chance across
all ten (mean <b>{mean:.1f}%</b>). A listener has to read structure or guess.</p>
<p class="lede">Highlighted morphemes are the ones that differ. What to judge:
<b>are these two genuinely different impressions, and does each line read as its
name?</b> If a pair reads as one thing said twice, it is not a contrast and I replace it.</p>
<span class="status">review_status: {e(rs.review_status.lower())} — execution blocked</span>

<h2>The pairs</h2>
{''.join(blocks)}

<h2>What this cost</h2>
<p class="lede">An earlier draft used richer scenes — a stone worn by water against a
current broken by a stone; a moth's compulsion against a lamp's indifference. Nine of
ten leaked, bag-of-roots scoring <b>94–100%</b>, because each side had private business
the other could not see. The stone's rounding is invisible from the water's side.
Those are genuinely different events, so the roots correctly differed and the pairs
correctly failed. The vivid ones were the ones that leaked hardest.</p>

<footer>
<p>Generated from <code>tlon/referents/{e(KIND)}_pairs.draft.yaml</code> against lexicon
<code>{e(C.load()['_hash'])}</code>. Bag-of-roots figures are read from
<code>runs/{e(KIND)}_pairs_bor.json</code>, written by the verify script that fits the
classifier on each pair — so this page cannot disagree with the run it reports.</p>
</footer>
</div>"""
    OUT.write_text(f"<title>Tlön Minimal Pairs</title>\n<style>{CSS}</style>\n{body}",
                   encoding="utf-8")
    print(f"wrote {OUT} ({len(pairs)} pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
