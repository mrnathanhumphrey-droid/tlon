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

## FLAGGED FOR HUMAN REVIEW — ambiguous, so KEPT AND MARKED

Nothing here was touched. Each is genuinely unclear and the rule is *when in
doubt, keep and mark.*

| # | item | why it is ambiguous |
|---|---|---|
| **A1** | `STATE.md` line 321 `# Tlön — STATE / Updated 2026-08-27` and line 329 `WHERE THINGS ACTUALLY STAND` | Reads as the document's title block but is 5 days stale. **Marked in place**, not moved — reordering 2,000 lines of a live file is riskier than the confusion it fixes. Nate's call. |
| **A2** | the `D_ctx` / `D_w` subscript discipline (`PREREG_ACT2_DRIFT` §0.2) | Mandated *"every number, table and filename carries its subscript"*; abandoned in practice since 2026-08-24. Either the discipline is dead and should be formally retired, or the current work is out of compliance with a locked prereg. **Not my call to make.** |
| **A3** | the F1–F5 falsifier scheme | Unreferenced by any current doc. F4 is separately recorded as having fired and been fixed (D15). `PARKED` in the dictionary, but whether the scheme still governs Act 2 is a scientific decision, not a cleanup one. |
| **A4** | the probe-battery apparatus (`A5` in the dictionary) | Fully built, synthetically validated, and unused. Retiring it would discard the only instrument in the project that has ever fired on a constructed pact; keeping it unmarked implies it is in use. Marked `PARKED`. |
| **A5** | `runs/act2/cold_table.json` (2-axis, `frozen: false`, sha `ca1ab5e9…`) | Superseded by `cold_table_ka.json` but **not deleted** — it is the baseline `RESULTS_STAGE2_DISTANCE` was written against, and deleting it would orphan that document's numbers. |

## WHAT THIS PASS DID NOT REMOVE

Any prereg, any retraction, any caveat, any historical section, any results doc,
any run artefact, any test. **One removal total**, and it was an exact duplicate.
