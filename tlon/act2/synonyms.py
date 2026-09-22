"""⛔⛔ SYNONYM-SETS: which roots encode the SAME happening.

Tlön has near-synonyms that the exact-root steer cannot see. `from` drips,
`fum` floods and `nur` falls all encode a spill, and the steer that fixed carry
(9% -> 97%) demands the reply reuse P's EXACT root — which may be the wrong form
for the happening in context. That rigidity is the leading suspect for the ~14
points of render the steered corpus cost (82.4% against 96.5% at matched size,
CIs disjoint), because the steered model's failures are overwhelmingly
"some other class -> R": 23 of 23 speak confusions, against arm1's one.

⭐ THE STRUCTURE DOES NOT EXIST IN THE LEXICON. `R` is a flat list of 218 roots
with no grouping key of any kind — searched for synonym/group/happening/sense/
family, all zero. So it is DERIVED here, from measurement rather than taste.

⛔⛔ THIS IS A NEW INSTRUMENT, AND THIS ARC HAS ALREADY SHIPPED TWO WRONG ONES:
a corpus measured with "shares a word" when the product is judged on "shares a
root" (68% that was really 9%), and a documented append guarantee that held for
production and not for comprehension. So the derivation is a PURE FUNCTION of
the distribution, its shape is reported rather than asserted, and every way it
can be wrong is named and guarded.

⛔⛔⛤ A RETRACTION, KEPT BECAUSE THE NUMBER WAS NEARLY LOAD-BEARING. The first
derivation grouped roots by ENGLISH STEM — `waited`/`waiting` share a stem, so
the roots they name are alternatives — and measured **reach 69.2%**. THAT
NUMBER IS RETRACTED. It was computed with NO purity filter, i.e. over words the
carry gate itself rejects as not naming a happening (`above`, purity 0.28).
Re-run at the gate's own threshold of 0.70 it collapses to **2 roots with
alternatives, reach 1.3%** — a no-op. Stem-grouping is dead; it reads SPELLING,
and inflections of one happening already land on ONE root, so the groups it
finds are the ones purity has dissolved anyway.

⭐⭐ THE LIVE DERIVATION IS FROM THE WORD->ROOT DISTRIBUTION, WHICH ALREADY
EXISTS AND IS DISCARDED. `act2_score_happening_words.tally()` builds
`hits[word][root]` and `main()` writes only the modal root plus a purity. The
synonym signal is exactly what it throws away: two roots are alternatives when
ONE English word lands on BOTH with support. This reads the language's own
English->root mapping instead of English orthography, and it is immune to the
tie-break that makes the modal root arbitrary, because it never asks which root
is largest — only which clear the support bar.

⛔ DERIVED FROM THE STEER-FREE CORPORA, ON PURPOSE. `corpus_natural/pairs.jsonl`
plus `corpus_conversations/conversations.jsonl` — the same two sources that
scored the gate's own vocabulary. Deriving from `corpus_conv_steered` would
inherit the steer's own root choices and call the intervention's fingerprint the
language's structure.

⛔⛔ THE SUPPORT THRESHOLD IS A FREE PARAMETER ON THE TREATMENT'S STRENGTH.
Lower support means looser sets, more reach, a stronger intervention — so it is
PRE-REGISTERED BEFORE THE BUILD and not re-picked after seeing carry or render.
Measured against the steered corpus's real carry pairs:

    support>=5    84 roots w/ alts   max set 10   mean 3.4   reach 74.1%
    support>=8    44 roots w/ alts   max set  7   mean 2.5   reach 49.0%
    support>=12   28 roots w/ alts   max set  5   mean 2.4   reach 32.5%

⭐ PRE-REGISTERED: **support >= 8**, signed off before this module was built.
Reach 49.0% is half the constraint, and a max set of 7 of 218 roots is still a
real crib. `>=5`'s max set of 10 was judged the point where "carry any of these"
starts to mean "carry anything".

THE THREE WAYS THIS CAN BE WRONG, EACH WITH ITS GUARD:

  TOO TIGHT   — every set is a singleton, the softened gate equals the exact
                gate, and the experiment measures nothing. Guarded by `reach()`,
                weighted by USE: 91% of groups being singletons reads like a
                no-op, but the roots that actually get carried are
                disproportionately the ones with alternatives.

  TOO LOOSE   — one root ends up synonymous with half the lexicon, the gate is
                vacuous, and "carry" stops meaning anything. A looser gate
                passes MORE and therefore looks HEALTHIER, so this failure is
                silent. Guarded by `max_set_size` in `summary()` and by
                refusing transitive chaining.

  COMPANIONS  — ⛔⛔ THE ONE THE OTHER TWO DO NOT COVER. `hits[w][r]` counts
                turns where the word appears AND the root is in the scene. Two
                roots both attested by one word may be ALTERNATIVES for one
                happening, or they may be two roots that always ride in the
                same scene together. Those are opposite relations and the count
                cannot tell them apart. Guarded by `alternation()`, which asks
                how often a candidate pair appears in the SAME turn: a pair that
                never separates is a companion, not a synonym.

⛔ NO TRANSITIVE CLOSURE. Two roots are synonyms only if ONE word attests both.
Chaining a~b and b~c into a~c merges happenings that share nothing, and each hop
is another chance to merge two unrelated senses. The relation is therefore
ASYMMETRIC — if `a` and `c` are each attested with `b` by different words,
`synonyms(b)` holds both while `synonyms(a)` does not hold `c`. That is the
conservative reading and it is deliberate.
"""
from __future__ import annotations

import collections

#: ⭐ PRE-REGISTERED 2026-09-22, before the instrument was built. Changing this
#: after seeing a carry or render number is tuning the treatment on the
#: outcome; it is a module constant so that a later change shows up in a diff.
SUPPORT = 8

#: The scorer's own floor: a word must be seen this many times to be scored at
#: all. Shared so the synonym population cannot drift from the gate's.
MIN_TURNS = 8

#: ⛔⛔ THE GATE'S OWN BAR, NOT A NEW ONE. `happening_words.json` carries this
#: as `threshold`; `tlon.act2.carry.happening_words()` keeps exactly the words
#: at or above it. A synonym-set derived over words BELOW it is derived over
#: words the gate does not believe name a happening at all — which is the
#: mistake this module has now made twice, once per derivation route.
MIN_PURITY = 0.70

#: ⛔⛔ SUPPORT MUST BE RELATIVE AS WELL AS ABSOLUTE, and the first two versions
#: of this module had only the absolute bar. `waiting` is seen 298 times; a root
#: it touches 12 times clears "support >= 8" while being 4% of the word's turns.
#: That is noise wearing the shape of an alternative, and because frequent words
#: touch many roots it is exactly where the vacuous sets come from. A share bar
#: scales with the word; an absolute one silently loosens as a word gets common.
#: ⛔ Capped in practice by `MIN_PURITY`: a word whose modal root holds 70% has
#: at most 30% left for every alternative combined.
MIN_SHARE = 0.0


def attested(hits: dict, seen: dict, *, min_support: int = SUPPORT,
             min_turns: int = MIN_TURNS, min_purity: float = MIN_PURITY,
             min_share: float = MIN_SHARE,
             vocabulary: dict | None = None) -> dict:
    """`{word: frozenset(roots it lands on with support)}`. Pure.

    ⛔⛔ `min_purity` FILTERS FIRST, AND LEAVING IT OUT IS THE ERROR THIS MODULE
    ALREADY RETRACTED ONCE. The stem derivation was retracted for grouping over
    words the gate rejects; the first distribution derivation then reproduced
    that error on the parallel axis — with no purity filter it returned sets of
    up to 144 of the 218 roots, because `tired` (purity 0.06) co-occurs with
    half the lexicon and every root it touches was called a synonym of every
    other. A word must NAME A HAPPENING before the roots it lands on can be
    called alternatives for one, and "names a happening" is not a judgement
    available here — it is `happening_words.json`'s purity threshold, the same
    bar `tlon.act2.carry` uses to build the gate's vocabulary.

    ⛔ A word must also clear `min_turns`, exactly as in
    `act2_score_happening_words.main()`. The floor is the gate's, not a new one.
    """
    if vocabulary is None:
        from tlon.act2.carry import load_vocabulary
        vocabulary = load_vocabulary()["words"]
    out = {}
    for word, counts in hits.items():
        if seen.get(word, 0) < min_turns:
            continue
        rec = vocabulary.get(word)
        if not rec or rec.get("purity", 0.0) < min_purity:
            continue
        n = seen[word]
        roots = frozenset(r for r, c in counts.items()
                          if c >= min_support and c / n >= min_share)
        if len(roots) >= 2:
            out[word] = roots
    return out


def derive(hits: dict, seen: dict, *, min_support: int = SUPPORT,
           min_turns: int = MIN_TURNS, min_purity: float = MIN_PURITY,
           min_share: float = MIN_SHARE,
           vocabulary: dict | None = None, exclude=()) -> dict:
    """`{root: frozenset(roots that encode the same happening)}`. Pure.

    `exclude` is an iterable of `(r1, r2)` pairs to drop — the companion guard's
    output feeds in here, so the filtering is visible at the call site rather
    than buried in the derivation.
    """
    banned = {frozenset(p) for p in exclude}
    out: dict[str, set[str]] = collections.defaultdict(set)
    for roots in attested(hits, seen, min_support=min_support,
                          min_turns=min_turns, min_purity=min_purity,
                          min_share=min_share,
                          vocabulary=vocabulary).values():
        for a in roots:
            for b in roots:
                if a != b and frozenset((a, b)) not in banned:
                    out[a].add(b)
    # ⛔ Every root is its own synonym. A caller asking `synonyms(r)` for an
    # unseen root must get {r} rather than an empty set, or the softened gate
    # silently becomes UNSATISFIABLE for it.
    return {r: frozenset(s | {r}) for r, s in out.items() if s}


def synonyms(sets: dict, root: str) -> frozenset:
    """The alternatives for `root`, always including `root` itself.

    ⛔ Falls back to the exact root. An unknown root means "no measured
    alternative", which must TIGHTEN to the exact gate — never loosen to
    anything-goes.
    """
    return sets.get(root) or frozenset({root})


def summary(sets: dict) -> dict:
    """Shape of the derived structure — for the TOO LOOSE guard."""
    sizes = sorted(len(v) for v in sets.values())
    return {"roots_with_alternatives": len(sets),
            "max_set_size": sizes[-1] if sizes else 0,
            "mean_set_size": round(sum(sizes) / len(sizes), 3) if sizes else 0.0,
            "size_histogram": dict(collections.Counter(sizes))}


def reach(sets: dict, carry_pairs) -> dict:
    """What fraction of REAL carry pairs the softening could touch.

    ⛔⛔ THE TOO-TIGHT GUARD, AND IT MUST BE WEIGHTED BY USE. An unweighted count
    of how many roots have alternatives understates this badly, because the
    roots that actually get carried are disproportionately the ones with
    alternatives.

    `carry_pairs` is an iterable of the shared-root sets, one per P->T pair.
    """
    n = touched = 0
    for shared in carry_pairs:
        if not shared:
            continue
        n += 1
        if any(len(synonyms(sets, r)) > 1 for r in shared):
            touched += 1
    return {"pairs": n, "touchable": touched,
            "reach": round(touched / n, 4) if n else 0.0}


def alternation(turns, hits: dict, seen: dict, *, min_support: int = SUPPORT,
                min_turns: int = MIN_TURNS, min_purity: float = MIN_PURITY,
                min_share: float = MIN_SHARE,
                vocabulary: dict | None = None) -> dict:
    """⛔⛔ THE COMPANION GUARD. Do candidate synonyms ever appear APART?

    For each candidate pair, over the turns containing the attesting word:

        co_rate = P(both roots present | the rarer of the two is present)

    `co_rate == 1.0` means the rarer root NEVER appears without the other — the
    two are companions in one scene, not alternatives for one happening, and a
    gate that accepts either is not softening the constraint, it is accepting a
    root the reply was going to contain anyway.  `co_rate == 0.0` is clean
    alternation: the word names one happening and the corpus spells it two ways.

    Returns the per-pair table plus the distribution, and `companions`, the
    pairs at `co_rate >= 0.90`, ready to hand to `derive(exclude=...)`.
    """
    cand = attested(hits, seen, min_support=min_support, min_turns=min_turns,
                    min_purity=min_purity, min_share=min_share,
                    vocabulary=vocabulary)
    if not cand:
        return {"pairs": [], "companions": [], "n_pairs": 0}

    wanted = set(cand)
    per_word = collections.defaultdict(collections.Counter)   # w -> pair counts
    for words, rts in turns:
        for w in words & wanted:
            present = cand[w] & rts
            for a in sorted(present):
                for b in sorted(present):
                    if a < b:
                        per_word[w][(a, b)] += 1

    rows = []
    for w, roots in cand.items():
        srt = sorted(roots)
        for i, a in enumerate(srt):
            for b in srt[i + 1:]:
                n_a, n_b = hits[w][a], hits[w][b]
                both = per_word[w].get((a, b), 0)
                rows.append({"word": w, "a": a, "b": b,
                             "n_a": n_a, "n_b": n_b, "both": both,
                             "co_rate": round(both / min(n_a, n_b), 4)})
    rows.sort(key=lambda r: -r["co_rate"])
    companions = sorted({(r["a"], r["b"]) for r in rows
                         if r["co_rate"] >= 0.90})
    buckets = collections.Counter()
    for r in rows:
        buckets["%.1f" % (int(r["co_rate"] * 10) / 10)] += 1
    return {"pairs": rows, "companions": companions, "n_pairs": len(rows),
            "co_rate_histogram": dict(sorted(buckets.items())),
            "companion_share": round(
                sum(1 for r in rows if r["co_rate"] >= 0.90) / len(rows), 4)}
