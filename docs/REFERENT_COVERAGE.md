# Referent coverage audit — Tier 1 (20 pegs) against the 151-root lexicon

**Date:** 2026-08-17 · **Lexicon hash:** `61ad847f450e0c48c6cabff076b41421`
**Status:** JUDGEMENT CALL, needs Nate/Wilson review. This is a semantic
assessment, not a computed result — it cannot be unit-tested, so it is written
down to be argued with rather than asserted in conversation.

**Why this audit exists:** the 151 roots were minted *before* any referent set
existed. Nothing ever checked that the language can say these things.

Every root gloss quoted below is copied from `tlon/grammar/lexicon.yaml`.

---

## Verdicts

| ID | Peg | Verdict | Roots that carry it |
|---|---|---|---|
| 01 | a mirror | ❌ **GAP** | — see below |
| 02 | a tiger | ⚠️ weak | `kril` it hunts · `klun` it crawls · `sör` it rages · `präx` it yellows · `prix` it blackens — **no root for striping/banding** |
| 03 | the moon over water | ✅ strong | `mlö` it moons · `fang` it streams · `fox` it pools |
| 04 | a labyrinth | ✅ ok | `kron` it turns · `plin` it twists · `säx` it edges, is bounded · `rän` it repeats |
| 05 | a single gold coin | ✅ ok | `hom` it rounds, curves · `flix` it gleams · `präx` it yellows |
| 06 | a pond at dawn | ✅ strong | `fox` it pools, stands still as water · `fis` it dawns |
| 07 | a train whistle heard from far off | ⚠️ ok | `mreng` it rings · `mräng` it roars · `leng` it hears + ORIENT `xun` thither |
| 08 | ice cracking on a lake | ✅ strong | `frum` it freezes · `kris` it cracks, fissures · `fox` it pools |
| 09 | a woodpile | ⚠️ ok | `hlang` it heaps · `pem` it dries · `xel` it greens, vegetates |
| 10 | an hourglass | ✅ ok | `ham` it sands, granulates · `nur` it falls · `plöng` it narrows |
| 11 | a knife | ✅ ok | `krax` it sharpens, is acute · `prax` it points · `pux` it silvers |
| 12 | a map the size of its territory | ❌ **GAP** | — see below |
| 13 | a spider's web strung with dew | ⚠️ weak | `plam` it lengthens · `from` it drips · `flox` it shimmers + ORIENT `sir` between — **no root for weaving/netting** |
| 14 | a lit window seen from outside at night | ✅ strong | `flex` it darkens to night · `hräx` it glows · `lan` it sees, is seen-ness · `säx` it edges |
| 15 | a river at night | ✅ strong | `fang` it streams, flows on · `flex` it darkens to night |
| 16 | a candle burning down | ✅ strong | `tris` it burns · `nur` it falls · `plöng` it narrows · `hräx` it glows |
| 17 | a stopped clock | ⚠️ ok | `kön` it halts · `rän` it repeats · `rem` it persists + ASPECT `tes` punctual-iterated |
| 18 | a road forking in a wood | ⚠️ ok | `hlix` it splits open · `xel` it greens · + ORIENT `lang` along |
| 19 | a moth at a lamp | ✅ strong | `kläng` it flies · `kän` it circles · `hräx` it glows · `tris` it burns |
| 20 | a stone worn smooth by water | ✅ strong | `hrun` it stones, is mineral · `mös` it smooths · `mör` it wets, damps |

**Tally: 10 strong · 8 workable · 2 gaps.**

---

## The two gaps are the same gap

**01 a mirror** — nothing in the inventory reflects, doubles, faces, or returns
a look. Nearest are `flix` (it gleams), `flox` (it shimmers), `prox` (it
whitens), `lan` (it sees, is seen-ness). A mirror rendered from those is
indistinguishable from a puddle or a pane of ice.

**12 a map the size of its territory** — nothing represents, stands for,
corresponds to, or scales. Nearest are `rän` (it repeats), `plen` (it flattens),
`säx` (it edges, is bounded). "Flattened, bounded, repeating" describes a
tablecloth.

**These are one gap, not two: the representational family is entirely absent.**
The root inventory was authored around physical happenings — light, water,
earth, motion, sound, growth, affect. Nothing about one thing standing for
another.

⚠️ **And these are the two most Borgesian images on the roster.** Mirrors and
maps are his signature figures; "Del rigor en la ciencia" *is* peg 12. So the
lexicon is weakest exactly where the referent set is most load-bearing.

---

## Options (needs a call — do not proceed on my choice)

**A. Mint a representational root family.** ~6–10 roots: *it doubles / it
reflects / it stands-for / it corresponds / it repeats-another / it faces*.
1227 syllables are free, so minting is cheap and the allocator makes it safe.
- ✅ Fixes 01, 12, and unblocks Tier 2's 22 (a book of every book) and 23
  (a word that acts like a virus), which need the same family.
- ⚠️ **Costs a spec revision and a new lexicon hash**, invalidating nothing
  built but requiring the Phase 0 counts to be re-run (instant).
- ⚠️ **The real objection, and it is a Tlön-metaphysics one:** Tlön's idealism
  is precisely a world where nothing persists independent of perception. A root
  meaning "it stands for another thing" smuggles in exactly the object-permanence
  the language is built to refuse. **This may be philosophically wrong rather
  than merely inconvenient**, and that is Nate's call, not mine.

**B. Drop 01 and 12 from the Tier 1 twenty.** Seed 2a with 18.
- ✅ Zero cost, zero spec churn, 2a starts immediately.
- ❌ Loses the two most Borges-canonical pegs, and defers the same problem to
  Tier 2 where 22 and 23 hit it again.

**C. Express them as *impressions of an encounter*, not as objects.** A mirror
is not a reflecting thing; it is *a seeing that comes back*. `lan` (it sees, is
seen-ness) with a `u` BEYOND edge to another `lan`, oriented `kon` (against).
A map is *a bounded flattening that repeats an extent*.
- ✅ **No new roots, no spec revision, and it is the most Tlönian answer** —
  it refuses the object exactly as the metaphysics demands.
- ⚠️ Leans hard on the signature being a *graph pattern* (§6d), not a root.
- ⚠️ Untested: whether these render legibly is an empirical question, and 2a's
  structural compat **cannot answer it** — that needs a calibrated listener.

**My read: C, with A held in reserve.** C is free, is philosophically correct
for Tlön, and is the option the Q3/Q4 result already pushes toward — novelty and
identity both living in graph structure rather than in lexical items. But C is
the option that most needs a real listener to validate, and 2a cannot provide
one. So C should be adopted *provisionally*, with 01 and 12 flagged in the
audit log as **unvalidated pegs** until 2b can score them.

**Not proceeding on this. Nate's call.**
