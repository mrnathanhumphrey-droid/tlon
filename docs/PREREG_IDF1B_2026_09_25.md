# PREREG — IDF-1b: replay versus readable provenance

- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `904b85df` (sha256[:8] of draft body at lock, 2026-09-25T22:09Z)
- **Date:** 2026-09-25
- **Fires on:** CPU-only local analysis. ⛔ **No GPU, no remote box, no spend.**
  If any step tries to launch one, stop.
- **Relationship to IDF-1:** `docs/PREREG_IDF1_2026_09_25.md`, LOCK `413efed0`,
  is **untouched**. This is a second pre-registration, not an amendment.

---

## 0 · Why there is a second probe

IDF-1's O-E — an empirical Markov kernel keyed on exact surface identity —
reached lag-2 **0.2600** at dose 0 while the D6 model sits at **0.3850**. A
speaker with a window of one turn beat the model by a wide margin, which
contradicts IDF-1's locked secondary prediction that O-E would be flat across
doses. It was not flat: 0.4498 / 0.2600 / 0.2427 across doses −1 / 0 / +1.

IDF-1's R1 conditions held and IDF-1's secondary prediction failed, in the same
run. **That conflict is why IDF-1's verdict was not declared**, and resolving it
is the only thing this probe is for.

**H-REPLAY:** O-E's suppression comes from surface identity acting as a
**pointer into specific corpus chains** — replaying the chains that carry the
hidden state — rather than from provenance that is readable off the surface.

If H-REPLAY holds, O-E is not a window-1 speaker in any sense that generalises,
and IDF-1's R1 reading is restored for the property as `read_lag` measures it.
If it fails, provenance is partly readable from the surface, the model's gap to
the best generalising window-1 speaker becomes the quantity every past release
read is restated against, and rung 1 returns as a capacity question.

---

## 1 · Step 0 — the precondition gate, ALREADY RUN, reported before anything else

**Verdict: instrument 2 is constructible. The probe is not void.**

Instrument 2 (O-E-noreplay) draws successors only from corpus chains **other
than** the one that supplied the transition into the current surface. Were
surfaces unique to a single chain, that candidate set would be empty at every
step, O-E-noreplay would collapse into the blind fallback for structural
reasons, and H-REPLAY would be unfalsifiable rather than tested. Measured on
the cached per-dose rebuilds (1,445 chains × 12 turns each):

| | dose −1 | dose 0 | dose +1 |
|---|---|---|---|
| distinct surfaces | 5,338 | 5,384 | 5,365 |
| surfaces in exactly 1 chain | 1,072 (20.1 %) | 1,081 (20.1 %) | 1,068 (19.9 %) |
| **occurrences on multi-chain surfaces** | **93.7 %** | **93.8 %** | **93.8 %** |
| distinct transitions | 15,751 | 15,768 | 15,766 |
| **transitions in exactly 1 chain** | **99.1 %** | **99.2 %** | **99.2 %** |
| max chains sharing a surface | 14 | 14 | 14 |
| max chains sharing a transition | 3 | 3 | 3 |

⭐ **The second bold row is the structure H-REPLAY needed in order to be
testable at all.** A surface recurs across as many as 14 chains, yet the
transition *out of* it belongs to exactly one chain better than 99 % of the
time. Surface underdetermines the successor; the kernel is choosing among
observed continuations. So excluding the source chain does not cripple the
arm — it turns it into a clean "given this surface, continue the way a
**different** chain continued", which is the generalising window-1 speaker the
reading table is about.

⚠️ 6.2 % of surface-occurrences sit on single-chain surfaces, where the
exclusion leaves nothing. Instrument 2 therefore has a fallback rate and it is
**logged per arm**, the way O-E's already is.

---

## 2 · Provenance repaired before the lock, in this order

IDF-1's verdict-relevant numbers came from code that no longer existed on disk.
That is the same exposure class as a lost adapter, and it is fixed here rather
than noted.

**2a — the trained-on corpus is persisted.** Dose-0 `16abeb8d27e4ccd3` survived
only on this laptop. Uploaded to `keyzersoze04/tlon-act2-adapters` under
`corpus_ct-s20624_16abeb8d27e4ccd3/` — `train.jsonl` (60,158 rows), `eval.jsonl`,
`manifest.json`, `token_budget.json`. ⭐ Verified independently of the uploader:
the hub's own stored LFS digest for `train.jsonl` reads
`16abeb8d27e4ccd357f843e19a294874a2c460e4b58c9c50b024bbcdee5befab`, so the
checksum the hub holds **is** the scope identifier the pipeline pins.
⛔ The ∓1 corpora remain unretrievable; IDF-1 §3 records why.

**2b — the instruments are on disk.** Recovered from the session transcript into
`tools/act2_idf1.py`, with `tests/test_idf1_instruments.py` pinning that the
module imports `lag_profile` / `permutation_null` / `resolving_power` from
`tlon.discourse.transient` and re-spells none of them. One featuriser serves
Step 1 and every oracle; the recovered scripts each carried their own copy.

**2c — IDF-1's headline numbers reproduce from that committed code. RUN BEFORE
THIS PREREG LOCKED. No deviation.**

| | IDF-1 cited | reproduced |
|---|---|---|
| Step 1 dose-0 logreg | 0.5437 [0.5351, 0.5518] | identical |
| Step 1 dose-0 gbt | 0.5511 [0.5416, 0.5600] | identical |
| A4′ transfer logreg / gbt | 0.5566 / 0.5607 | identical |
| O-C true lag-2 | 0.0285 z −16.565 | identical |
| O-A blind lag-2 | 0.4456 z +361.629 | identical |
| O-B top-1 lag-2 | 0.4009 z +313.186 | identical |
| O-B F1-thr lag-1 | 0.0000 z −42.911 | identical |
| F1 threshold | 0.230 (F1 = 0.5276) | identical |
| O-E lag-2, doses −1 / 0 / +1 | 0.4498 / 0.2600 / 0.2427 | identical |
| O-E exact-hit, doses −1 / 0 / +1 | 99.4 / 99.4 / 99.5 % | identical |

All eight arms and all three fallback rows match to the last reported digit.
Artefacts: `runs/act2/idf1/repro_step1.txt`, `repro_step2.txt`, checked against
the surviving `step2a.txt` / `step2b.txt` by `tools/act2_idf1_repro_check.py`.

⛔ The check reads **both** sides from files. Its first draft hand-typed the
O-A/O-B/O-C block from the record, put O-B's lag-4 into O-A's row, and reported
a deviation that did not exist. A comparison is only as trustworthy as the
weaker of its two sides.

**2d — then, and only then, IDF-1b's five instruments land in `tools/` and this
document locks.**

---

## 3 · The instruments

All five run on CPU. The kernel source is the dose-0 rebuild, whose chain
identity is the chain's index in the cached rebuild.

**1 · Replay rate.** For every O-E chain, the fraction of consecutive triples
`(t−2, t−1, t)` that occur as a real consecutive triple inside one corpus chain.
Reported per dose.

**2 · O-E-noreplay.** The same kernel, but at each step successors are drawn
only from corpus chains other than the one that supplied the transition into the
current surface. Large-n lag profile, same instrument, fallback rate logged.

**3 · O-E-heldout.** Build the kernel from rebuild seed A; seed and score O-E
chains from rebuild seed B's surfaces — the situation `read_lag` is actually in.
Report the exact-hit rate and the lag profile.

**4 · Step 1 re-run with surface identity.** Features are the Step 1 set plus
**surface identity** and **per-root index-bucket size**. Chain-split, held-out
AUC with a chain-bootstrap interval. Then an O-B built from it, large-n lag
profile.

> **The estimand, stated here so it is not reinterpreted later.** Under a chain
> split, 20.1 % of distinct surfaces occur in exactly one chain and are
> therefore guaranteed absent from the training fold. This AUC measures
> **surface identity as far as it transfers across chains** — which is the
> generalising speaker's quantity, and the right one for a reading table about
> whether provenance is readable rather than memorised.
>
> ⭐ To keep "unseen surfaces dragged the AUC down" from becoming an argument
> instead of a number, the held-out AUC is **also reported stratified by
> whether the test surface appeared in the training fold**, with an interval on
> each stratum.

**The encoding, declared here rather than chosen later.** Surface identity is a
one-hot over the **training fold's** surface vocabulary plus a single shared
out-of-vocabulary column. ⛔ A vocabulary built over all chains would give every
test surface a column fitted on rows from its own chain — the chain-identity
leak the split exists to prevent, re-entering through the feature block.
"Per-root index-bucket size" is `len(index_by_root[force][root])`, how many
surfaces that root can produce under that force (range 7-37, median 20); both
halves of its key are readable from the surface.

⚠️ **Instrument 4 reports logistic regression only, and the capacity check
changes shape.** The one-hot runs to some four thousand columns and is held
sparse; the gradient-boosted tree IDF-1 used as its capacity check does not
accept that representation, and re-encoding the surface for it would make the
tree answer a different question than the number beside it. The one-hot already
gives the linear model a per-surface intercept, which is the most a model can
extract from identity alone. **The seen/unseen stratification is the capacity
diagnostic in its place**, and it is the more direct one here: it measures how
much of the AUC rests on surfaces the model had memorised.

**5 · Matched-fidelity floor** (carried from IDF-1's deviation note). O-A,
O-B(4) and O-E-noreplay with `responsiveness` tuned so their lag-1 matches the
model's measured lag-1 per dose; report lag-2 against the model's D6 values
within the matched-read distribution (12 × 10).
**Descriptive under every reading. It does not gate.**

⭐ **Why this one is worth running even though it gates nothing.** The model's
lag-1 is **1.0278** at dose 0, parsed from `retrain12_ct/model_lag_ct-s20624.json`.
IDF-1's O-E sat at **0.9580** and O-B top-1 at **0.9350** — both *below* the
model. A speaker that carries less forward has less to suppress at lag-2, so
some unknown part of O-E's lower lag-2 is lower carry rather than better
release. Matching lag-1 first is what turns the comparison into a floor.

⚠️ **`responsiveness` does not exist for the kernel arm, and the substitute is
declared here.** O-A and O-B(4) come out of `build_transient`, which takes
`responsiveness` directly. O-E-noreplay is a walk over memorised transitions and
has no such parameter. Its matched knob is instead a **mixing weight toward the
blind reseed**, tuned to the same lag-1 target. This is my substitution, not
Wilson's spec, and it is recorded here so it is visible before the number
exists rather than defended after it.

---

## 4 · Pre-declared reading table — LOCKED BEFORE ANY INSTRUMENT RUNS

⭐ **Both thresholds are expressed as a fraction of the blind-to-true gap, not
as a raw lag-2 value.** The two red-proofs anchor the scale: **O-A = 0.4456**
closes 0 % of the gap, **O-C = 0.0285** closes 100 %, so the gap is **0.4171**.
Stating the thresholds this way makes plain that both gates are on **oracles**,
and that neither was set against the model — 0.383 sitting a thousandth away
from the model's 0.385 is a coincidence of scale, not a chosen anchor. For
orientation, on this scale O-B top-1 closes 10.7 %, the D6 model closes 14.5 %,
and IDF-1's O-E closes 44.5 %.

- **REPLAY** — O-E-noreplay **and** O-E-heldout each close **at most 15 %** of
  the gap (lag-2 ≥ **0.383**), **and** O-B(4)'s AUC interval upper bound is
  below 0.60.
  ⇒ O-E's 0.26 is replay off a finite corpus. **IDF-1's R1 reading is restored**
  for the property as `read_lag` measures it, and the DEVIATIONS entry names
  memorised-draw suppression as a non-generalising exception.

- **READABLE** — O-E-noreplay **or** O-E-heldout closes **at least 35 %** of the
  gap (lag-2 ≤ **0.300**), **or** O-B(4)'s AUC interval lower bound is above
  0.65.
  ⇒ Provenance is partly readable from the surface. **R3.** The model's gap to
  the best generalising window-1 speaker becomes the quantity every past release
  read is restated against, and rung 1 returns as a capacity question.

- **Between 15 % and 35 %** — **no verdict, deliberately.** Report all five
  instruments and name which one disagrees with which.
  ⭐ At n = 5,000 the oracle values are precise, so a result landing in this band
  reflects **the effect being intermediate, not the estimate being noisy**. It
  is not an invitation to re-read the band as one of the two verdicts.

- **Anything else** — report all five, no verdict, same disclosure.

---

## 5 · Guards

- The statistic is the **imported** one — `lag_profile`, `permutation_null`,
  `resolving_power` from `tlon.discourse.transient`, never re-spelt.
  `tests/test_idf1_instruments.py` enforces this structurally.
- ⛔ **Vacuous passes are flagged, never read as release.** Any arm whose lag-1
  z falls below 6.0 is reported as **perceive-collapsed**. This is not
  hypothetical: IDF-1's O-B F1-threshold variant drove lag-1 to 0.0000 at
  z −42.911 — it "passed release" by perceiving nothing at all.
- **Chain-level splits everywhere.** A row-level split leaks chain identity.
- ⛔ **No GPU, no remote box, no spend.**
- Walk-backs go in a **DEVIATIONS file beside this prereg**; nothing here is
  rewritten after the fact.

---

## 6 · Deliverables

`docs/RESULTS_IDF1B_2026_09_25.md` carrying: the Step 0 table above, the
reproduction of IDF-1's numbers, all five instruments, the stratified AUC, and
the **REPLAY / READABLE / no-verdict** reading.

**And, whatever the reading, IDF-1's two `MEASUREMENTS.md` entries are still
owed** — `release_ctx` and `release_w`, which currently have zero entries
between them despite carrying a campaign.
