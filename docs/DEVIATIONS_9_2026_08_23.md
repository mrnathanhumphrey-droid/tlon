# DEVIATIONS — Phase 9. PREREG `10757ac4`.

Read with `PREREG_9_REFERENTS_2026_08_23.md`. ⛔ The locked body is never
rewritten; corrections live here.

---

## D1 — `load_live()` served all 50, so the first runs of 9.2a, 9.2b and 9.3 included the four HELD-BACK referents

**Found:** 2026-08-23, by a failing test, immediately after `review_status` was
set to `REVIEWED`.

`load_live()` called bare `load()`. Unlike `load_all()`, `load()` does **not**
filter on `seed_2a` — so it returned **50 referents, not 46**, and
**M37 / M38 / M49 / M50 entered the live measurement set.**

⛔⛔ **M38 and M50 are the two referents that state the RETRACTED conservation
claim as an image.** They are withheld *specifically* so they cannot whisper into
a measurement, and they were in the first run of every 9.2/9.3 measurement.

### The tests did not catch it, and the reason is the general lesson

`test_held_back_referents_are_the_conservation_whisper_plus_abstractions`
existed, passed throughout, and asserted the **YAML declaration** —
`seed_2a: false` is set on those four. It never asserted that **the loader
honours it**. ⭐ **A test that cannot reach the defect is not coverage.** The
assertion now sits on `load_live()`'s *output*, which is what every measurement
actually consumes, and additionally checks that no held-back id appears in it.

I also **printed the count and did not read it**: 9.2a's own output said
`1. v2 LIVE SET -- 50 referents` while the prereg header says *50 declared / 46
live*. That is rule zero — a labelled value not cross-checked against its run —
for the eighth time in this project.

### Impact: the conclusion did not change, and here is the evidence

| | first run (50, wrong) | **corrected (46)** |
|---|---|---|
| distinct utterances | 204 | **191** |
| **f₂** | 9.3 % | **10.5 %** |
| mean \|consistent\| | 1.28 | **1.31** |
| H(r\|u) | 0.165 bits | **0.186 bits** |
| RSA frontier, sup over α | 0.00 | **0.00** |
| outcome | A | **A** |

**Both runs give OUTCOME A and both are far below the 25 % gate.** The corrected
numbers are the ones of record; the wrong-set numbers appear here only so the
size of the error is visible rather than asserted to be small.

### Fixes

- `schema.load_live(seeded_only=True)` filters `seed_2a`, with the failure
  written into the docstring.
- `tests/test_referents_v2.py::test_the_loader_ACTUALLY_withholds_them` asserts
  the loader's output and that no held-back id reaches it.
- 9.2a, 9.2b and 9.3 re-run; `runs/*.json` overwritten with the corrected runs.

---

## D2 — `drift_taxonomy.py --v2` printed the ARCHIVE's pragmatic gap inside a v2 report

**Found:** 2026-08-23, reading the 9.3 output.

The tool reports pragmatic drift from `runs/phase5.json` to complete the
three-way taxonomy. Under `--v2` that line printed **+8.00 to +13.33 pts** —
which is the **archive set's** gap — inside a report headed *v2*. Nothing was
mislabelled in the file, but a reader would take it as v2's number, and the two
sets are **unpairable** so there is no sense in which one substitutes for the
other.

**Fix:** under `--v2` the line now refuses, names the number as the archive's,
and states that v2's gap is 9.2c and unmeasured. ⭐ The taxonomy claim survives
in its structural form — *pragmatic drift is the sole possible mover on v2,
because the other two are pinned at zero* — while its **magnitude on v2 stays
unmeasured**, which is the honest split.

---

## D3 — `--v2` output filename collided with the arm variable

Minor. My `tag = "v2" if v2 else "archive"` was shadowed by the arm loop's
`tag = "pi" if use_pi else "raw"`, so the first v2 run wrote
`runs/drift_taxonomy_pi.json`. Renamed to `setname`; the file is
`runs/drift_taxonomy_v2.json`. Caught by reading the written path, which is why
tools print it.

---

## D4 — scope note: `drift_taxonomy.py`'s default is unchanged on purpose

`--v2` is opt-in and the default still loads the archived 60. Repointing the
default would silently change what Phase 6's locked verdict reproduces.
Confirmed after the change: the default path still reports **7,240 built, 40
rejected (0.5 %), structural 0.0000 %, semantic 0.0000 %** — byte-identical to
the Phase 6 record.
