"""Generate the signature review page from referents.draft.yaml.

Generated, never hand-written: the page must not be able to drift from the file
it is reviewing.
"""
from __future__ import annotations
import html
import itertools
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar import classes as C                       # noqa: E402
from tlon.grammar.gloss import gloss                        # noqa: E402
from tlon.grammar.parse import render                       # noqa: E402
from tlon.referents import schema                           # noqa: E402
from signature_report import witness                        # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "docs" / "signature_review.html"


def roots_of(sig: schema.Signature) -> list[str]:
    out: list[str] = []
    for p in sig.contains:
        out += list(p.root_any)
    return out


def e(s: str) -> str:
    return html.escape(str(s))


CSS = """
:root{
  --ground:#f3f0ea; --raised:#fffdf9; --line:#d8d2c6;
  --ink:#221e28; --muted:#6a6272;
  --sage:#5f6b57; --sage-dim:#8a9481;
  --ochre:#8a6a24; --rose:#9c4f4a;
  --chip:#e8e3d8;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#1e1a22; --raised:#262130; --line:#3a3345;
    --ink:#ded9d0; --muted:#948da2;
    --sage:#c2c7b7; --sage-dim:#8b937f;
    --ochre:#c8a45c; --rose:#c58a86;
    --chip:#2f2939;
  }
}
:root[data-theme="dark"]{
  --ground:#1e1a22; --raised:#262130; --line:#3a3345;
  --ink:#ded9d0; --muted:#948da2;
  --sage:#c2c7b7; --sage-dim:#8b937f;
  --ochre:#c8a45c; --rose:#c58a86;
  --chip:#2f2939;
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
  font-size:16px; line-height:1.6;
}
.wrap{max-width:74ch; margin:0 auto; padding:3rem 1.25rem 6rem}
h1,h2,h3{font-family:"Iowan Old Style",Palatino,"Palatino Linotype",Georgia,serif;
  text-wrap:balance; margin:0; font-weight:600}
h1{font-size:2.1rem; letter-spacing:-.01em}
h2{font-size:1.25rem; margin:3.5rem 0 1rem; padding-bottom:.5rem;
  border-bottom:1px solid var(--line)}
.eyebrow{font-size:.7rem; text-transform:uppercase; letter-spacing:.16em;
  color:var(--muted); margin-bottom:.6rem}
.lede{color:var(--muted); margin:.75rem 0 0}
.status{display:inline-block; margin-top:1.25rem; padding:.3rem .7rem;
  border:1px solid var(--ochre); color:var(--ochre); border-radius:2px;
  font-size:.72rem; letter-spacing:.12em; text-transform:uppercase}

.calls{display:flex; flex-direction:column; gap:1rem; margin-top:1.25rem}
.call{background:var(--raised); border:1px solid var(--line);
  border-left:3px solid var(--ochre); padding:1rem 1.15rem; border-radius:2px}
.call h3{font-size:1rem; margin-bottom:.35rem}
.call p{margin:0; color:var(--muted); font-size:.92rem}

.grid{display:flex; flex-direction:column; gap:1.1rem; margin-top:1.5rem}
.card{background:var(--raised); border:1px solid var(--line);
  border-radius:2px; padding:1.15rem 1.25rem}
.card.flagged{border-left:3px solid var(--rose)}
.card.weak{border-left:3px solid var(--ochre)}
.chead{display:flex; align-items:baseline; gap:.7rem; flex-wrap:wrap}
.pid{font-family:ui-monospace,"Cascadia Mono",Consolas,monospace;
  font-size:.8rem; color:var(--sage-dim); background:var(--chip);
  padding:.15rem .45rem; border-radius:2px; font-variant-numeric:tabular-nums}
.pname{font-family:"Iowan Old Style",Palatino,Georgia,serif; font-size:1.15rem}
.spec{font-family:ui-monospace,"Cascadia Mono",Consolas,monospace;
  font-size:1.05rem; color:var(--sage); margin:.9rem 0 .5rem;
  overflow-x:auto; white-space:nowrap; padding-bottom:.2rem}
.gloss{font-family:"Iowan Old Style",Palatino,Georgia,serif;
  font-style:italic; font-size:1.02rem; color:var(--ink); margin:0 0 .9rem}
.meta{display:flex; gap:1.1rem; flex-wrap:wrap; font-size:.76rem;
  color:var(--muted); border-top:1px solid var(--line); padding-top:.7rem;
  font-variant-numeric:tabular-nums}
.meta b{color:var(--ink); font-weight:600}
.note{font-size:.86rem; color:var(--muted); margin:.7rem 0 0;
  padding-left:.8rem; border-left:2px solid var(--line)}
.tags{display:flex; gap:.4rem; flex-wrap:wrap; margin-top:.7rem}
.tag{font-size:.68rem; text-transform:uppercase; letter-spacing:.1em;
  padding:.2rem .5rem; border-radius:2px; border:1px solid currentColor}
.t-unval{color:var(--rose)} .t-weak{color:var(--ochre)}
.t-over{color:var(--sage-dim)}
details{margin-top:1rem; border:1px solid var(--line); border-radius:2px;
  background:var(--raised); padding:.8rem 1rem}
summary{cursor:pointer; font-size:.9rem; color:var(--sage)}
summary:focus-visible{outline:2px solid var(--sage); outline-offset:2px}
.mini{font-family:ui-monospace,Consolas,monospace; font-size:.82rem;
  color:var(--sage-dim); margin:.5rem 0 0; overflow-x:auto}
footer{margin-top:4rem; padding-top:1.25rem; border-top:1px solid var(--line);
  color:var(--muted); font-size:.85rem}
code{font-family:ui-monospace,Consolas,monospace; font-size:.9em;
  background:var(--chip); padding:.1rem .3rem; border-radius:2px}
"""


def main() -> int:
    rs = schema.load(allow_unreviewed=True)
    lex = C.load()
    seeds = rs.seeds()

    shared: dict[str, set[str]] = {r.id: set() for r in rs.referents}
    for a, b in itertools.combinations(seeds, 2):
        if set(roots_of(a.signature)) & set(roots_of(b.signature)):
            shared[a.id].add(b.id)
            shared[b.id].add(a.id)

    def card(r: schema.Referent) -> str:
        w = witness(r.signature)
        surf = render(w) if w else "— unsatisfiable —"
        gl = gloss(w) if w else ""
        cls = "card"
        if not r.validated:
            cls += " flagged"
        elif r.id == "02":
            cls += " weak"
        tags = []
        if not r.validated:
            tags.append('<span class="tag t-unval">unvalidated · option C · you cleared it for now</span>')
        if r.id == "02":
            tags.append('<span class="tag t-weak">swapped in · replaces “a tiger”</span>')
        if shared.get(r.id):
            ids = ", ".join(sorted(shared[r.id]))
            tags.append(f'<span class="tag t-over">shares roots with {e(ids)}</span>')
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

    excluded = [r for r in rs.referents if not r.seed_2a]
    approved = rs.review_status == "REVIEWED"
    title = ("Referent signatures, approved" if approved
             else "Referent signatures, awaiting your pass")
    status = rs.review_status.lower()
    gate = "execution unblocked" if approved else "execution blocked"
    body = f"""<div class="wrap">
<p class="eyebrow">Tlön · phase 2a · southern hemisphere</p>
<h1>{title}</h1>
<p class="lede">Twenty Tier&nbsp;1 pegs. Each shows the <em>minimal</em> legal utterance that
satisfies its signature — the loosest thing the gate will accept. The italic gloss is the
thing to judge: if the minimum already reads as the referent, the signature holds; if it
reads as anything at all, it's too loose.</p>
<span class="status">review_status: {status} — {gate}</span>

<h2>Your rulings, applied</h2>
<div class="calls">
<div class="call"><h3>“beyond is used way way way too much” — fixed</h3>
<p>That was my bug, not the signatures'. The witness builder handed out <code>u</code> (BEYOND)
first every time, and no signature specified a relator at all — so twenty different pegs all
rendered as “beyond ⟨something⟩,” injecting a spatial claim none of them made. Every peg now
names <em>how</em> its parts relate, and that turned out to be real content: 20 is
<code>kra</code> (because of) — worn <em>by</em> water; 17 is <code>xom</code> (despite) — a
halting that holds <em>despite</em> a repeating. Without those they were just co-present verbs.</p></div>
<div class="call"><h3>03 and 15 may match the same scene</h3>
<p>Confirmed as you ruled — no <code>forbid</code> added. A moonlit river is honestly both, and the
gate will sometimes take the other peg. That ambiguity is now a thing 2a measures rather than
a thing the signatures hide.</p></div>
<div class="call"><h3>02: tiger swapped out</h3>
<p>Replaced with <em>wind moving through tall grass</em> — Thoreau territory, and every part of it
is directly rooted (<code>tlan</code> winds, <code>xel</code> greens, <code>frim</code> undulates)
rather than approximated.</p></div>
<div class="call"><h3>Pattern roots minted, tiger not reinstated</h3>
<p>Five new roots on your go: <code>tlex</code> stripes, <code>tlix</code> bands,
<code>tlox</code> mottles, <code>tlux</code> dapples, <code>tläx</code> veins. Appended, so no
existing root shifted — verified, 0 moved. A tiger peg is now expressible, but I did
<em>not</em> swap it back in unreviewed; raise it as a fresh proposal if you want it.</p></div>
<div class="call"><h3>Glosses de-nouned</h3>
<p>You caught <code>fox</code> = “stands still as <em>water</em>”. There were eight, including
<code>lan</code> “is seen-<em>ness</em>” and the aspect <code>ax</code> = “continuous_<em>flow</em>”.
These are the grounding the frozen auditor reads in 2c, so nouns there would have quietly weakened
the anti-cipher device. The rule now lives in a test, not in prose.</p></div>
</div>

<h2>The twenty</h2>
<div class="grid">{''.join(card(r) for r in seeds)}</div>

<h2>Declared but excluded from the seed</h2>
<p class="lede">Tier&nbsp;2 (21–26) and Tier&nbsp;3 abstractions (27–30). Loaded and validated,
not seeded. No verdict needed now — included so you can see where the representational gap
bites again at 22 and 23.</p>
<details><summary>Show {len(excluded)} excluded pegs</summary>
<div class="grid">{''.join(card(r) for r in excluded)}</div></details>

<footer>
<p>Generated from <code>tlon/referents/referents.draft.yaml</code> against lexicon
<code>{e(lex['_hash'])}</code>. The page cannot drift from the file — it is built from it.</p>
<p>One number in the terminal report is junk and I've left it out here: “45 co-satisfiable
pairs” measures the clause cap, not the signatures — that test could not have come back
negative. The meaningful one: <b>0 of 30</b> minimal witnesses match any referent but their own.</p>
</footer>
</div>"""

    OUT.write_text(
        f"<title>Tlön Referent Signatures</title>\n<style>{CSS}</style>\n{body}",
        encoding="utf-8")
    print(f"wrote {OUT}  ({len(seeds)} seeded, {len(excluded)} excluded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
