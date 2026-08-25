# VERDICT — 2a: structural self-play loop (PLUMBING SOUND; three headline metrics were VACUOUS)

- **Date:** 2026-08-18
- **Pre-reg:** ⚠️ **NONE.** 2a was built before the PREREG discipline was adopted
  from `D:\IC_experiments`. Every falsifier below was written *after* seeing the
  first run, which is exactly the weakness pre-registration exists to prevent.
  **Recorded as a limitation, not glossed.** From 2b on, locked pre-reg first.
- **Artifacts:** `runs/2a.db`, `runs/2a_stress.db`; `tools/run_2a.py`,
  `tools/ambiguity_report.py`; `tlon/selfplay/`, `tlon/novelty/`, `tlon/audit/`,
  `tlon/persist/`.
- **Lexicon:** `49475a61a308a2beeb7434693eff5c44` (156 roots) ·
  **Referents:** 20 Tier-1, REVIEWED 2026-08-18
- **Compute:** local CPU. **$0.00.** No GPU, no model, no Lambda. Wall < 30 s.
- **Tests:** 480 passing.

## Claim tested

That every mechanism which can fail for a **non-neural** reason works before a
model is introduced: referent-keyed buckets, decay, bounded medoid storage,
orbit arithmetic, tree-edit novelty, the audit schema's B2 constraint, and the
canonical-AST collision counter.

## Result — headline run (600 turns, 20 referents)

| | |
|---|---|
| proposals made | 600 |
| utterances accepted | 595 |
| rejected by M gate | **0** |
| rejected as too repetitive | **0** |
| distinct meanings | 595 |
| exact canonical repeats | **0** |
| matching >1 referent | **0 (0.0%)** |
| medoids held | 160 (cap 8 × 20 buckets) |
| orbits closed | 5 |

## ⛔ Three of those figures are VACUOUS, and that is the main finding

The sampler **builds** each scene from the signature and then verifies it, so
the M gate **could not have fired**. A 100 % pass rate from a gate with no
reachable failure mode is not evidence. The same argument voids the 0 %
ambiguity and the 0 novelty rejections. Reported as green, all three would have
been the [[could_it_detect]] error.

Replaced with probes that **can** come back negative:

| probe | result | verdict |
|---|---|---|
| M rejects a mismatched referent | **200 / 200** | gate discriminates |
| 03/15 overlap reachable at all | `mil flex sen fang u fang mlö ka` → `['03','15']` | reachable |
| R binds under low entropy (3 referents, no decoration) | **4 321** novelty rejections, **98** orbits closed, 302 accepted, 21 medoids | R and orbit engage |
| B2: can 2a publish a counter? | refused — `auditor_state=ABSENT_BY_PHASE` | constraint holds |

## Result — natural vs targeted ambiguity

The 0 % above measured the **sampler**, not the signatures. Separating the two:

| | scenes | matching >1 referent |
|---|---|---|
| untargeted, no blending | 8 000 | 5 (**0.06 %**) |
| untargeted, blending on | 8 000 | 30 (**0.38 %**) |

Targeted (120 attempts per ordered pair, 190 unordered pairs):

| pair | reachable | reading |
|---|---|---|
| 06+08 | 53 % | pond at dawn × ice on a lake — both `fox` |
| 14+15 | 46 % | lit window at night × river at night — both `flex` |
| 05+11 | 43 % | gold coin × knife — both `flix` |
| **01+12** | **39 %** | **mirror × map — both `rän`** |
| 03+15 | 12 % | the overlap Nate ruled in |

**10 of 190 pairs reachable; 180 not reached.**
⚠️ "Not reached" is **not** "disjoint": the probe blends exactly one donor node,
so a pair needing two reads as unreachable when it is not. Lower bound only.

### ⭐ The one substantive finding about the referent set

**01 (mirror) and 12 (map) are the most confusable pair in the set at 39 %**, and
they are independently the two pegs already flagged `validated: false`. Both
lean on `rän` (it repeats) because option C renders each as an
encounter-impression, and encounters-of-recurrence resemble one another. This is
independent evidence — arriving from a different direction than the original
concern — that the option-C renderings are **less individuated than the concrete
pegs**, and it predicts precisely where 2b's listener will struggle. Keeps
narrowed option A justified as a reserve.

## Falsifier check (written AFTER the fact — see pre-reg note)

- **KILL "loop does not run":** not fired. 595/600 turns produced legal,
  parseable, canonicalised, logged utterances.
- **KILL "R never engages":** not fired under stress (4 321 rejections), **but
  it did not engage at all** in the headline configuration. R is only reachable
  at low entropy; at full decoration the space is too large for repetition to
  bind. Honest scope limit.
- **KILL "the counter can be published unconditioned":** not fired. Refused at
  the SQL layer and again at the serving layer.

## Verdict

**PLUMBING SOUND.** Every non-neural mechanism works and each is now covered by
a test that could fail. The B2 constraint, canonical-AST collision detection,
decay, boundedness, orbit arithmetic, and ledger/experiment separation all hold
under adversarial probing.

⚠️ **2a PROVES PLUMBING, NEVER PRAGMATICS.** Structural compat cannot tell a
vivid impression from a barely relevant one. Nothing here is evidence that the
system communicated anything. That question is 2b's and cannot be asked without
a listener.

## Scope / open rungs

- **No pre-registration.** The single largest methodological weakness of this
  arc. Fixed from 2b.
- **R does not bind at full entropy.** Whether that matters depends on how much
  a learned generator concentrates its distribution — unknown until 2b.
- **Ambiguity is rare (0.38 %).** The signatures are nearly disjoint under
  natural generation, so 2b's ranking task has a clean decision boundary and a
  small model will likely solve it. Solving it would demonstrate little.
- **Northern hemisphere** untouched; B3 requires it to denote into the same
  `Scene` algebra or the ablation is confounded.

## Infra notes (cost the debugging)

- **A path that never executes is not tested.** The headline run never rejected
  a proposal, so the accepted-after-rejection path never ran — hiding a UNIQUE
  constraint violation (`run_id, seq, attempt`) where the winning attempt was
  logged as `attempt=1`, colliding with the rejected row already written for
  that seq. Only the stress config surfaced it. Identical failure class to
  `alibi_multi_cf/VERDICT_TIER1_REALTEXT_2026_07_11.md:38` (local validation ran
  only the ALiBi cell, never the RoPE+pretrain path).
- **Windows newline translation breaks content addressing.** `write_text`
  converts `\n` to `\r\n`, so hashed bytes ≠ file bytes. Every ledger and
  lexicon write now pins `newline=""`. This had already silently desynced the
  mint and load lexicon hashes.
- **Do not round-trip UTF-8 through PowerShell** (`Get-Content | Set-Content`)
  — it re-encoded a test file and turned every `ö` into `Ã¶`.
