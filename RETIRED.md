<!-- settled-claim-ok: a removal log; it records what was deleted and where the
     current version lives, and asserts no measurement result of its own. -->
# RETIRED — every removal, logged before it happened

**Deletion is the last resort.** The default is to mark `SUPERSEDED` /
`RETRACTED` / `PARKED` in [`MEASUREMENTS.md`](MEASUREMENTS.md) and leave the text
in place, because a visibly-retracted claim is more useful than a deleted one —
it prevents the claim being re-made. A false lemma once propagated through 7
files in this project, and **the retractions are what killed it.**

## ⛔⛔ NEVER REMOVED, UNDER ANY CLEANUP

- **retractions, corrections, and caveats** — load-bearing by construction
- `STATE.md` line 426 `⏮ HISTORICAL` and everything under it — an explicitly
  marked record of what was true when written
- the in-place corrections in `RESULTS_VARIANCE_DECOMPOSE` §2, `RESULTS_DRIFT`,
  `PRICING` §7, and the `MEMORY.md` retraction entries
- any prereg body (`PREREG_*.md`) — hashed and locked; amendments are appended,
  never applied to the body

## REMOVALS

### R1 · `STATE.md` — duplicated block, 2026-09-01

**Removed:** the second copy of `## ⭐ THREE BUGS THE SMOKE TESTS CAUGHT (none
would have crashed)`, formerly lines 225–233.

**Justification:** a **verbatim, byte-identical duplicate** of the block at lines
215–223, produced by a section being appended twice. No content is unique to the
removed copy — verified by exact string comparison before removal, not by eye.

**Current version lives:** `STATE.md`, the surviving copy (the three bugs:
cumulative-alternation guard; silent `--skip-cold` no-op; `Replay` returning a
surface instead of a proposal).

**Reversible:** `git show 6cf7681:STATE.md` and any earlier revision.

## RETIREMENTS — requirements, not files

⛔ A retirement removes an **obligation**, not text. Nothing is deleted here; the
requirement stays readable in its source document and is marked retired beside
it. A locked prereg's requirement being retired needs a visible record even
though nothing was removed — otherwise "retired" and "quietly ignored" leave
identical traces.

### R2 · `PREREG_ACT2_DRIFT` §0.2 — the `D_ctx` / `D_w` subscript discipline, 2026-09-01

**Requirement retired:** *"Every number, table and filename carries its
subscript"*, separating `D_ctx` (in-context, prompted) from `D_w` (weight-level,
post-fine-tune).

**Retired as TRIVIALLY SATISFIED — not abandoned, and the arc was not out of
compliance.** Every Act-2 measurement to date is inference-only: no weights
change in any arm of any run, so every number in the arc is `_ctx` by
construction. The subscript partitions nothing, and a marker taking the same
value on every row teaches readers to skip a marker meant to be load-bearing.

**What is NOT retired**, and this is the whole reason the retirement is logged
rather than assumed: **the distinction itself.** The moment a fine-tune enters an
Act-2 measurement, `D_w` becomes a live category, §0.2 is back in force
unamended, and the subscripts return. §0.2's actual prohibition — *the two must
never be reported under one word* — stands unconditionally and was never in
question.

**How it was landed:** a note appended above the prereg body. **This retirement
did not edit the body.**

**Current version lives:** [`MEASUREMENTS.md`](MEASUREMENTS.md) A5 § "C8".
**Reversible:** the requirement was never deleted; un-retiring it is deleting the
two notes.

### R3 · PREREG `20620b7c` — cost redaction and relock, 2026-09-01

**Private research costs were removed from the public repository, then the prereg
was relocked.** Commit `7420a11` (2026-08-28), *"Remove the cost ledger from the
public repo"*, took a dollar figure out of §0.2 and §7. **No hypothesis,
estimator, threshold or falsifier changed** — reviewable in full at
`git diff 249cdd7 7420a11`.

| | lock |
|---|---|
| 2026-08-24 → 2026-08-28 | `20620b7c` |
| **from 2026-09-01** | **`b96902b3`** |

The redaction was correct and the relock is the right close. ⚠️ **What the relock
does not do is certify the intervening window**, so the honest reading of the
prereg is: *locked 08-24, redacted 08-28 for costs, relocked 09-01, science
untouched throughout.* Addendum stating exactly that sits at the head of the
prereg. Sentences elsewhere reading *"prereg `20620b7c` VERIFIED unchanged"*
(`SCOPE_LOCAL_FINETUNE` :6 · `DEVIATIONS_ACT2` :9 · `STATE.md` :967) were true
when written and refer to the pre-redaction lock.

⛔⛔ **THE ACTUAL LESSON, AND IT IS NOT ABOUT THE LOCK: SPEND FIGURES WERE
WRITTEN INTO A PUBLIC REPOSITORY IN THE FIRST PLACE.** The scrub was cleanup
after that mistake, and the broken lock was a *side effect of cleaning up*. Cost
ledgers are gitignored precisely so this cannot happen; a dollar figure typed
into prose sidesteps the ignore file entirely. **Never put a spend number in
committed prose.**

⚠️ Second-order: **nothing runs the lock verifier.** No test in the suite calls
`lock_prereg`, and `tools/build_wilson_packet.py` *embeds and prints*
`body_hash(text)` without ever comparing it to the stamped value — the same shape
as the `cold_pin` guard that printed two hashes and compared nothing. A test that
asserts every stamped LOCK verifies is **proposed, not written.**

## ✅ THE FIVE FLAGGED ITEMS — DECIDED 2026-09-01

⛔ **These A-numbers are THIS FILE'S OWN flag list. They are NOT
[`MEASUREMENTS.md`](MEASUREMENTS.md) entries A1–A5** — the dictionary's A1 is the
W2 drift delta and its A5 is the probe battery. Same labels, different lists; the
mapping is given in the last column where it applies.

⭐ **Nothing was deleted in resolving any of the five.** Four were resolved by
marking, one needed no action at all.

| # | item | why it was ambiguous | ✅ decision |
|---|---|---|---|
| **A1** | `STATE.md`, then lines 321 / 329: `# Tlön — STATE / Updated 2026-08-27` and `WHERE THINGS ACTUALLY STAND` | Read as the document's title block but was 5 days stale. Marked in place, not moved — reordering 2,000 lines of a live file is riskier than the confusion it fixes. | **RESOLVED — no further action.** The pointer-not-reorder fix worked: current state is now `STATE.md`:25 `# ✅ WHERE THINGS ACTUALLY STAND — 2026-09-01`, and the old block sits at :348 demoted and marked `# ⏮ Tlön — STATE (SNAPSHOT OF 2026-08-27, superseded)`. Verified 2026-09-01; no stale reference remains in `STATE.md`. The line numbers in this row's left column are the **pre-fix** ones and are kept as the record. |
| **A2** | the `D_ctx` / `D_w` subscript discipline (`PREREG_ACT2_DRIFT` §0.2) | Mandated *"every number, table and filename carries its subscript"*; abandoned in practice since 2026-08-24. Either the discipline was dead and needed formal retirement, or the current work was out of compliance with a locked prereg. | **RETIRED FORMALLY — moot, not abandoned.** All Act-2 measurements are `_ctx` by construction, so the subscript carries no information. Logged in full above as **R2**; the distinction returns with any fine-tune. |
| **A3** | the F1–F5 falsifier scheme | Unreferenced by any current doc. F4 separately recorded as having fired and been fixed (D15). Whether the scheme still governs Act 2 is a scientific decision, not a cleanup one. | ⭐ **REMAPPED, NOT RETIRED.** The falsifiers are live; the *estimators* changed. Mapping table: [`MEASUREMENTS.md`](MEASUREMENTS.md) **§H**. F1 CLEARED · F4 ACTIVE/PASSING · F2 and F3 **not adjudicated** (underpowered; §5.2 binds) · F5 PARKED with the battery. No falsifier's meaning was altered. |
| **A4** | the probe-battery apparatus (dictionary [`A5`](MEASUREMENTS.md#a5)) | Fully built, synthetically validated, and unused. Retiring it would discard the only instrument that has ever fired on a constructed pact; leaving it unmarked implies it is in use. | ⏸ **PARKED — as the UPGRADE PATH**, with a forward note now in the dictionary. It measures the meaning↔form mapping, a stronger convergence claim than a free-transcript `force:ka` rate. Held pending the positive control; if `force:ka` moves, this is how *"the force rate converged"* upgrades to *"the mapping converged."* |
| **A5** | `runs/act2/cold_table.json` (2-axis, `frozen: false`, sha `ca1ab5e9…`) | Superseded by `cold_table_ka.json` but not deleted — it is the baseline `RESULTS_STAGE2_DISTANCE` was written against. | **KEEP, marked `SUPERSEDED` with a forward pointer** to `cold_table_ka.json` (sha `84c2a1b5…`) — see dictionary [`B4`](MEASUREMENTS.md#b4). Retained because `RESULTS_STAGE2_DISTANCE`'s locatability HALT analysis depends on it **and** because it documents *why* the panel switched to `force:ka` alone. ⛔ Never a current baseline. |

## WHAT THIS PASS DID NOT REMOVE

Any prereg, any retraction, any caveat, any historical section, any results doc,
any run artefact, any test. **One removal total**, and it was an exact duplicate;
**one requirement retirement**, and nothing was deleted to effect it.
