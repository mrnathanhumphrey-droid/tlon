<!-- settled-claim-ok: an inventory of what other documents claim; it quotes their
     phrasing verbatim in order to surface collisions and asserts nothing itself. -->
# PHASE 1 — MEASUREMENT INVENTORY, and the collisions

$0 documentation pass. **Judges nothing, resolves nothing.** Scope: `STATE.md`
(2,340 lines) + 76 docs (16,664 lines total). The core set was read in full, not
sampled — a first pass built from regex context windows was discarded because an
inventory made of fragments reproduces the exact mixing this audit exists to stop.

Resolutions live in [`MEASUREMENTS.md`](../MEASUREMENTS.md). Removals live in
[`RETIRED.md`](../RETIRED.md).

## 14 COLLISIONS FOUND

### ⛔⛔ C1 — `D` is two different symbols

| doc | `D` means | scope |
|---|---|---|
| `PREREG_ACT2_DRIFT_2026_08_24.md` §1 | `D(M,t)` **departure** — fraction of probes where model M's mapping at epoch t differs from *its own* at epoch 0 | **within**-speaker |
| `SPEC_TWO_SPEAKER_DRIFT_2026_08_30.md` §3 | `D(A,B)` **distance** between two speakers' transcripts | **between**-speaker |

Same letter, opposite scope, both live in the same arc.

### ⛔⛔ C2 — "drift" names four distinct objects

1. **departure in impression space** vs a fixed held-out probe battery (`PREREG_ACT2_DRIFT` §1)
2. **`D(A,B)` shrinking in LIVE relative to YOKED** (`SPEC_TWO_SPEAKER` §5) — a *coupling* claim
3. **`W2(LIVE) − W2(YOKED)` on `force:ka`** (`RESULTS_DRIFT_2026_08_31`)
4. **drift capacity** — observed half-to-half movement ÷ movement expected under a frozen rate (`runs/act2/drift_capacity.json`, `tools/act2_drift_capacity.py`)

(2) and (3) are the same *intent*, different estimators. (1) and (4) are different objects entirely.

### ⛔⛔ C3 — the admitted panel changed three times and the switch has no RESULTS doc

| doc | panel | force:ka |
|---|---|---|
| `RESULTS_STAGE1_…_08_30` (window-1) | root TTR · force:ka · nodes/scene | ⭐ admitted (contam 0.27) |
| `RESULTS_ASYMMETRIC_RECERT_…_08_30` (in-regime) | **tokens/surface · nodes/scene** | ⛔ **excluded, contam 1.59, "the single worst-behaved force in the set"** |
| `RESULTS_STAGE2_DISTANCE_…_08_30` §4 | two axes; *"`root TTR` and `force:ka` are **not reintroduced**"* | ⛔ excluded |
| `RESULTS_DRIFT_…_08_31` + `runs/act2/cold_table_ka.json` | **`force:ka` ALONE, frozen sha `84c2a1b5…`** | ⭐ **sole axis** |

⇒ **A reader following `docs/` builds the two-axis panel and never finds the
switch.** The re-admission of `force:ka` on *separability + capacity +
locatability* (replacing *contamination*) is recorded in `STATE.md` and in code,
**and in no RESULTS document.**

### ⛔⛔ C4 — two admission criteria that select oppositely

*Contamination* (between-build sd ÷ within-conversation movement) and
*separability/ICC* are near-inverses; ranking by ascending contamination ranks
approximately by ascending separability. Both appear as **the** admission rule, in
different docs, with opposite selections. Neither doc names the other.

### ⛔⛔ C5 — locatability returns opposite verdicts

- `RESULTS_STAGE2_DISTANCE` §2: **all 7 builds FAIL** at n=14 (need 23–29); *"a HALT on the whole table"*; cold table `frozen: false`, sha `ca1ab5e9…`
- `runs/act2/cold_table_ka.json`: **all 7 locatable**, `unlocatable: []`, `frozen: true`, sha `84c2a1b5…`

Both are correct *for their own panel*. Nothing says so.

### ⛔⛔ C6 — "more conversations" vs "more speakers", four positions

1. `RESULTS_STAGE2_DISTANCE` §2: *"The fix is more conversations per speaker, **not more speakers**."*
2. `RESULTS_DRIFT_…_08_31`: adapter-limited ⇒ *"needs more independently-trained speakers first"* — **since retracted in place**
3. `PRICING_ADAPTER_COUNT_…_08_31` §1: adapter-limited **not established**, h CI [0.0000, 0.4033]
4. `PREFLIGHT_H_DIAGNOSTIC_…_08_31` §4: n and N are levers on **different problems**

### ⛔ C7 — the unit-of-independence counter disagrees with itself

*"Third time this unit has moved"* (`SPEC_TWO_SPEAKER` §6) · *"Fourth move"*
(`RESULTS_STAGE2` §4) · *"Sixth move"* (`STATE`, drift block). Same lineage,
three counts.

### ⛔ C8 — the `D_ctx` / `D_w` subscript discipline was abandoned

`PREREG_ACT2_DRIFT` §0.2 requires *"Every number, table and filename carries its
subscript."* **No later document uses either subscript.**

### ⛔⛔ C9 — `MDE` is two different estimators

| doc | definition |
|---|---|
| `PREREG_ACT2_DRIFT` §5.1 | 95th percentile of \|ΔD\| under **seed-label permutation within the control arm**, computed before unblinding |
| `PRICING_…`, `PREFLIGHT_…`, `STATE` | **2.802 × se** — minimum detectable effect at 80% power, α=0.05 |

### ⛔ C10 — the F1–F5 falsifier scheme is unreferenced by any current doc

F1 internalizability · F2 drift-is-noise · F3 pact · F4 degeneration · F5
leakage. Status (parked / superseded) is stated nowhere. **F4 is separately
recorded as having fired and been fixed** ("F4 READ CLEAR ON THAT COLLAPSE —
FIXED, D15", `STATE` line 567).

### ⛔⛔ C11 — probe battery vs free-transcript measurement, never reconciled

The prereg's apparatus is a **64-probe held-out battery** (32 production / 32
comprehension, forced-choice with mutation distractors, administered in a
*branched, discarded* context). The entire `force:ka` line measures **free-running
transcripts with no battery**. The battery machinery still exists (`probes.build`,
used in `act2_two_speaker_probe.py` only to build *seed history*).

### ⛔⛔ C12 — `σ_cp` is not the quantity the drift run measured

`SPEC_DISCOURSE_LAYER_v0.1` defines σ_cp as a **stochastic-thermodynamics
coupling power** — `σ_cp ∝ dᵀKd`, diffusion matrix, Sylvester gradient
projection, IFT, entropy production; recorded as *sign-indefinite in 5000/5000
on-shell 2-DOF draws*, with the corrected object `σ_ex^MN − σ_ex^HS` passing
0/1500. This is **mathematically unrelated** to `W2(LIVE) − W2(YOKED)`.

⇒ Four documents close with *"σ_cp remains unmeasured"* — `RESULTS_VARIANCE_DECOMPOSE`,
`RESULTS_ASYMMETRIC_RECERT`, `RESULTS_STAGE2_DISTANCE`, `STATE` — in a context
that reads as though the drift run were attempting it. **It never was.**

### ⛔ C13 — `STATE.md` has two "current state" headers

Line 1 `# ✅ THE DRIFT RUN LANDED` (2026-08-31/09-01) sits **above** line 321
`# Tlön — STATE / Updated 2026-08-27` and line 329 `# ⭐⭐ WHERE THINGS ACTUALLY
STAND`. The document's apparent title block is four days stale.

### ⛔ C14 — literal duplication in `STATE.md`

`## ⭐ THREE BUGS THE SMOKE TESTS CAUGHT` appears **twice, verbatim**, at lines
215–223 and 225–233.

## WHAT IS *NOT* A COLLISION (checked, and clean)

- `STATE.md` line 426 already carries `⏮ HISTORICAL — everything below predates
  2026-08-27 and is kept as the record`, with an explicit note that statements
  below were true when written. **That is correct practice and stays.**
- `RESULTS_VARIANCE_DECOMPOSE` §2 carries its own in-place correction about the
  4-vs-7 build set, cross-referenced from `RESULTS_STAGE1`. Both sides agree.
- The retractions added 2026-08-31 (false lemma, adapter-limited, units error)
  are consistent across the files that carry them.

## WHAT PHASE 1 DID NOT DO

Resolve anything; rank the collisions by severity; delete or edit any file;
judge which side of a collision is correct. All of that is Phase 2 onward.
