# PRE-REG — 2b.2: can a from-scratch listener read structure, and which channels?

- **Date:** 2026-08-20
- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `080bc40f` (sha256[:8] of draft body at lock, 2026-08-20T17:32Z)
- **Arc:** Tlön 2b, replacing `PREREG_2B_LISTENER_2026_08_19.md` (LOCK `612f37ba`,
  **KILL 1 fired**: bag-of-roots scored 99.94 % on the original 20 pegs).
- **Lexicon:** `e2b8527010231a81fd31b6eeb9de3d8c` · **Referents:** 20 Tier-1 +
  20 perspective (J1–J10) + 20 diagnostics (P1–P10), all REVIEWED 2026-08-20.

## One-line hypothesis

A from-scratch encoder (~5 M params, morpheme-per-token) trained on all 60
referents will **read structure** — scoring above chance within perspective
pairs *and* within the diagnostic pairs — and its **per-channel profile will be
uneven in a way we can name**: relator and orientation legible, nesting and
aspect weaker.

## ⚠️ Why two pair sets, established by measurement not by taste

Neither set is a test alone. `tools/shortcut_probe.py`:

| feature | perspective J1–J10 | diagnostics P1–P10 |
|---|---|---|
| bag-of-roots | 50.8 % | 49.0 % |
| **matrix-root-only** | **100.0 %** | 60.0 % (only P1/P8, where direction *is* matrix swap) |
| first-morpheme | 76.6 % | 70.1 % |

Sur is head-final, so the matrix sits at a fixed position and a perspective flip
*is* a matrix swap — "read the last root" sweeps all ten perspective pairs. The
diagnostics are immune to that on 8 of 10. **Perspective pairs ask whether the
model can find the matrix; diagnostics ask whether it reads what modifies one.**

## Falsifier (pre-registered kill conditions)

- **KILL A — NO STRUCTURE READ.** Diagnostic within-pair accuracy ≤ **55 %**
  (bootstrap CI lower bound below 50 %). The model cannot read modifying
  structure at all; a perspective-pair score would then be the positional
  shortcut and must be reported as such.
- **KILL B — SHORTCUT ONLY.** Perspective accuracy ≥ 95 % **while** diagnostic
  accuracy ≤ 60 %. The model learned "look at the end" and nothing else. Report
  as a positional heuristic, not comprehension.
- **KILL C — FLAT PROFILE.** All five channels (relator, orientation, direction,
  nesting, aspect) within **5 points** of each other. The "uneven profile" half
  of the hypothesis is false and per-channel claims are unsupported.
- **KILL D — LEAKAGE.** >10 point drop when the split is deduplicated by
  canonical `utterance_id`.

## Priors to lose (pre-register against)

- That nesting (P5) will be readable. It is the deepest structural dependency
  and the likeliest failure. If it works I should be surprised.
- That aspect (P10) is easy because it is one root. Reduplication count may be
  the hardest channel precisely because nothing else disambiguates.
- That a high perspective score means anything on its own. It does not — KILL B
  exists because I would otherwise be tempted to report it.

## Must-beat baselines

Every one measured on the **same** test items, reported as paired differences
with CI:

1. **Chance** — 50 % within pair.
2. **Bag-of-roots** — 50.8 % / 49.0 %. Already measured.
3. **Matrix-root-only** — 100 % / 60.0 %. The ceiling on perspective pairs;
   beating it there is impossible, which is the point of KILL B.
4. **First-morpheme** — 76.6 % / 70.1 %.
5. **Shuffled-label null** — must land at chance.

## Method

1. **Data.** All 60 referents, balanced, `blend_p=0.6`, dedupe by canonical
   `utterance_id` before splitting. Random split and novel-decoration split,
   both reported.
2. **Model.** Transformer encoder, d_model 256, 6 layers, 8 heads, ≤26 tokens,
   `[CLS]` → 60-way head. Random init, no pretraining.
3. **Metric.** Overall accuracy is context only. The headline numbers are
   **within-pair accuracy** on each set, and the **per-channel breakdown** over
   relator ×3, orientation ×3, direction ×2, nesting ×1, aspect ×1.
4. **Train local**, RTX 5070 Ti, AdamW, early stop on val.

## Confound controls (pre-registered)

- Within-pair scoring is binary between the two members, so class priors cannot
  carry it.
- The 20 original Tier-1 pegs stay in training so the model faces a realistic
  mixture, but are **excluded from every headline number** — they are
  root-solvable and would inflate any average they entered.
- **Cipher-control null band.** No cipher can form here (the generator is the
  random sampler, nothing optimises against the listener), so this is the clean
  chance to measure what channel-scrambling costs an honest system. Scramble
  aspect reps, coda, and orientation order in turn; record each drop. Those
  numbers are the reference for phase 3.
- Nesting is a single pair (P5); its estimate is weak and must be reported with
  its CI, never as a bare point.

## Stats

Bootstrap 95 % CI on every accuracy. Paired differences against each baseline on
identical items. Per-channel accuracies with CIs; KILL C judged on overlap, not
on point estimates.

## Cost / lane

Local, ≈ $0, minutes. Ledger row regardless.

## Standing floor (reportable regardless)

- **Hypothesis holds:** a 5 M-param model reads relational structure in a
  nounless impression language, with a named per-channel profile and a measured
  null band for the phase-3 control.
- **KILL A or B fires:** structure is not learnable at this scale from this
  data. That is a real result and it redirects phase 3 before any spend.
- **KILL C fires:** channels are uniformly legible or uniformly opaque; either
  way the per-channel framing is wrong and should be dropped.

## Not in scope

- Backbone selection for later phases. ⛔ Nate's call, every time.
- The gloss auditor (B1 — required the moment a *learned generator* faces a
  trainable listener; not this phase).
- `MAX_DEPTH` revisit — needs this phase's output.
