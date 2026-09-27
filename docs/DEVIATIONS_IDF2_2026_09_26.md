# DEVIATIONS — IDF-2 (`docs/PREREG_IDF2_2026_09_26.md`, LOCK `37363296`)

The prereg is not rewritten. Every walk-back is recorded here, in the order it
was found, with the state of knowledge at the time it was written.

⛔ Step 0a–0c and 0f have run (CPU only, no GPU, no spend). Nothing downstream
of Step 0 has been trained or read.

---

## C1 · `verify_recipe` had no branch for the probe recipe — caught before 0a ran

**Not a deviation from the prereg. A construction fault in the code the prereg
specifies, found by reading rather than by data, and recorded because the
failure it would have produced points at the wrong cause.**

`transient.verify_recipe` dispatches on the recipe string and **falls through
to the content-FREE verifier** for anything it does not name. That verifier
refuses when lag-1 is responsive:

> `CONTROL IS CONTAMINATED: lag-1 z=%.2f exceeds the chance ceiling`

`content-transient-held` is responsive by construction — 0a measured lag-1 z
**+488.15** — so the first build of IDF-2's corpus would have aborted with a
message saying the **control** was contaminated. The treatment arm, refused for
being the treatment, under the control's name, before any adapter was priced.

**Fixed** by an explicit branch that verifies the probe recipe exactly as
`content-transient` is verified (same two claims: responsive at lag 1, at
chance at every longer lag) and then **restamps the verdict** to
`content-transient-held`. The restamp matters on its own: `check_transience`
returns the string `content-transient`, which the builder writes into the
manifest as `recipe_VERIFIED`, and that is the field `factorial` matches on —
so `PROBE_RECIPES` would have been undone by a manifest field.

Pinned by `tests/test_idf2_instruments.py::test_a_probe_recipe_is_not_verified_as_a_control`.

⭐ **The lesson is where it was found.** The branches were all correct; the
**fall-through** was the bug. Reading what a dispatch does with an unlisted
value is a different act from reading what it does with the listed ones.

---

## D1 · §1's gap-compression warning was wrong, and wrong in the direction that mattered

**Written the moment 0a and 0c reported, before any downstream number existed.**

### What the prereg says

> ⚠️ **That compresses the denominator.** `ct-s20624`'s corpus lag-2 is
> **0.0271** […] If the held corpus lands materially higher, the 0c gap shrinks
> and a "15 point" band becomes a smaller raw difference — harder to resolve.

The reasoning: a root in `roots(t−2)` but absent from `roots(t−1)` is not barred
under `held`, so the held corpus should carry **more** lag-2 residue than one
built on the generator's `inherited`.

### What was measured

| | lag-1 | lag-2 |
|---|---|---|
| `ct-s20624` corpus (`inherited`) | 0.9622 | **0.0271** |
| **held corpus (0a)** | **0.9653** | **0.0224** |
| 0c blind oracle | 1.0357 | 0.4456 |
| 0b marker oracle | 0.9620 | 0.0216 |

**The held corpus's lag-2 is LOWER, not higher: 0.0224 against 0.0271.** The
0c gap is **0.4239**, which is **101.6 %** of IDF-1's 0.4171. The denominator
did not compress; it is marginally wider.

⭐ Why, stated as the mechanism rather than as a save: `held` bars the roots
that `t−1` and `t−2` **both** carry, which is precisely the set most likely to
be carried a third time. The unbarred residue the prereg worried about is
smaller than the extra suppression the intersection buys.

### What it changes

**Nothing in the reading table.** §6's thresholds are fractions of the 0c gap
and were never denominated in a raw value, which is why they survive a wrong
prediction about that gap's size. In the gap this recipe actually has:

- **15 points** = raw lag-2 **0.3820**
- **35 points** = raw lag-2 **0.2972**

⛔ §3A's resolvability check is unaffected in form and is still owed: it runs on
Step P's measured SD in these units, not on this prediction.

⚠️ **This is a refuted warning, not a refuted result.** It is recorded because
a caveat that turned out to be false is exactly the kind of sentence that
otherwise survives into a results document as though it had been confirmed.

---

## D2 · The prereg body trips the settled-claim linter and has NOT been edited

`tests/test_settled_claim_lint.py::test_the_live_decision_documents_are_currently_clean`
fails on `PREREG_IDF2_2026_09_26.md` for the keyword **`arithmetic`**, in:

> *"What is true is narrower and matters for §6's arithmetic: …"*

This is a false positive on the linter's own terms — it is not a
settled-property diagnosis, and the linter judges **form, not content** by
design. But every available fix — rephrasing, or an inline
`settled-claim-ok:` waiver — **edits the locked body.**

⛔ **The body is not edited, and the reason is the lock's whole purpose.**
Step 0a–0c and 0f have run. A prereg whose text can be adjusted after results
exist is not a pre-registration, and "the change was only cosmetic" is exactly
the judgment the lock is built not to trust. §8: *"Walk-backs go in a
DEVIATIONS file beside this prereg; nothing here is rewritten after the fact."*

⭐ The sentence the linter caught is **the same sentence D1 refutes**, so the
record already carries the correction the linter was asking for — one level up,
in the place that survives.

⚠️ **Consequence, stated plainly:** the suite has a standing failure on this
file until Nate and Wilson decide otherwise.
`PREREG_IDF1_2026_09_25.md` already fails the same lint for the same reason,
so this is the second instance of one class, not a new one.

**Three options, none taken unilaterally:**
1. Leave both failing and treat the lint as advisory for locked pre-regs.
2. Exempt `docs/PREREG_*.md` from `LIVE_GLOBS` **once locked** — the linter's
   purpose is live decision documents, and a locked prereg is the one kind of
   document that must not be edited in response to it.
3. Re-lock with `--force` after a rephrase, accepting the loss of the
   guarantee. ⛔ Not recommended: results already exist.

---

## D3 · `dose_w` is recomputed on a different parameter population than the briefs' rms

0f recovered the number §4's gate points at, which was recorded nowhere
(`INSTANCE.json`, `factorial.json`, `persist_ledger.json`,
`model_lag_ct-s20624.json` — all silent; no committed tool computed it):

| | |
|---|---|
| source | `hf://keyzersoze04/tlon-act2-adapters/ct-s20624/adapter_model.safetensors` |
| tensors | **392** = 28 layers × 7 targets × 2 — the shard tripwire passed |
| modules | 196, every `lora_A` paired with its `lora_B` |
| `delta_norm` | **48.9665** |
| `n_trainable` | **80,740,352** |
| **`dose_w`** | **0.00544947** · §4 band ±5 % = **[0.005177, 0.005722]** |

⛔⛔ **This number is denominated in LoRA A/B parameters and must never be
compared to the campaign's full-finetune rms.** `01_OUR_FRONTIER.md` records
rung 1a at `3.1180e-04` and a matched dose at `3.0915e-04`; those are computed
over transformer-layer parameters, a different population.
`PREREG_CAMPAIGN_RUN0_MAPPING_5E6_2026_09_09.md` §3 already says
rms-matching does not transfer across populations. The two differ by more than
an order of magnitude, so the comparison would look like a finding.

⭐ `n_delta` (6,525,288,448 — the entries of the reconstructed ΔW) is recorded
beside `n_trainable` in `runs/act2/idf2/step0.json` so a later reader can tell
which denominator was used without re-deriving it.

---

## C2 · `read_lag`'s default payload was one edit away from redefining every past read

**Not a deviation. A hazard created by implementing §0e, and guarded at the
point it would have fired.**

§0e asks for a reader that **shares** `read_lag`'s fold. The implementation is
one optional argument — `marker_fn`, default `None` — threaded through
`read_lag` → `_read_lag_inner` → `model_chain`, where the payload becomes
`marker_stimulus(surface, line)`.

⛔⛔ **`marker_stimulus(surface, None)` must return the surface byte for byte**,
because that path is every pre-IDF-2 caller: the dose curve, the CLI,
`act2_model_carry`. A single character added there would silently redefine
every release read in the campaign into a different measurement than the one
its number was recorded under, and nothing downstream would notice.

Pinned by `test_marker_none_sends_the_bare_surface_byte_for_byte` and
`test_the_row_builder_default_is_byte_identical`. **Mutation-proofed**: making
the default path append `(none)` turns both red, on the assertion that names
the bug.

⭐ The same hazard exists on the builder side and has the same guard.
`rows_from(chains)` — no marker — reproduces its previous output exactly, so
every existing corpus stays reproducible from its own manifest.

---

## Step 0 is COMPLETE — 0a, 0b, 0c, 0d, 0e, 0f all report

| step | result |
|---|---|
| **0a** corpus | `content-transient-held`, lag-1 **0.9653** (band 0.9141–1.0103 ✅), lag-2 **0.0224** |
| **0b** marker oracle | lag-2 **0.0216**, shortfall **−0.0008** — red-proof passes |
| **0c** blind anchor | lag-2 **0.4456** — reproduces IDF-1's O-A to four decimals |
| **gap** | **0.4239** = 101.6 % of IDF-1's 0.4171 |
| **0d** row audit | **15,895** provoke rows, **0 malformed**, every marker equal to the independently recomputed `held` |
| **0e** reader | `read_lag_held`, sharing the fold; 13 tests incl. the byte-for-byte default and the greedy refusal |
| **0f** dose | `dose_w` **0.00544947**, 392 tensors, shard tripwire passed |

**0d's `(none)` rate is 13.3 %** (2,113 of 15,895). 1,445 are each chain's
first transition, where there is no `t−2`; the other **668** are turns whose
`t−1` and `t−2` genuinely share no roots. ⭐ So `(none)` is a token the model
meets constantly during training, which is what makes **M-strip
in-distribution** — the property Wilson's §7 ruling depends on.

In this recipe's gap, §6's bands are **15 points = raw lag-2 0.3820** and
**35 points = 0.2972**.

**Suite: 2,664 pass, 1 fails — D2 only.**

---

## C3 · 0a built the corpus in memory and threw it away — fixed

**Caught by Wilson, 2026-09-26.** §3-0a says *"Record its lag profile, its
`n_pairs` per lag, and its **sha**. **Push it to the hub** before anything else
runs."* The first implementation recorded the profile and the pairs, and then
**discarded the object that produced them**: no rows on disk, no sha, no hub.

⛔ Every number in the first Step 0 report was real and the corpus behind it
did not survive the process. That is the `s20620` shape and the IDF-1 shape at
once — a lost artefact, and instruments whose output existed only in a
terminal.

**Fixed.** `_persist_corpus` writes the rows **with the marker already in
them**, so the file on disk is the training text rather than a chain dump a
later step would re-derive the marker from. Temp-then-replace, because
`open(p, "w")` truncates before the write can fail.

| | |
|---|---|
| rows | **15,895** |
| `train_sha256` | `d0c022b688444f8717f96a6dfb1102b4e718e3c4946845da6a8a1fa9b7b015f0` |
| local | `runs/act2/idf2/corpus_held-s20624/` |
| hub | `corpus_held-s20624_d0c022b688444f87` |
| round-trip | ⭐ **re-downloaded and re-hashed: matches** |

The manifest carries `recipe_VERIFIED: content-transient-held` and an explicit
`NOT_IN_FACTORIAL` field, so the quarantine is stated in the place a later
reader actually looks.

---

## C4 · `marker_fn` now rides in every lag reading

**Wilson, 2026-09-26.** `read_lag` records its decoder so that no lag row can
exist without saying how it was read. The marker is part of the measurement in
exactly the same way: **M and M-strip are identical in weights, seeds, chains
and decoder, and differ only in which `marker_fn` provoked each turn.**

Without the field those two arms produce rows distinguishable only by the
**filename they were written to** — the precise failure `temperature` was added
to prevent, one argument along.

`read_lag` now writes `marker_fn: "<module>.<qualname>"`, or **`null`** for the
unmarked reader — a positive claim that the read used a bare surface, which is
what every pre-IDF-2 row means. The M-shuffle closure carries its **seed** in
that name, since two shuffle arms at different seeds mark different roots.

`tests/test_readings_carry_their_config.py` extended by four tests, including
that M, M-strip and bare produce three distinct values.
⭐ The serialisation test needed no change: it already asserts the curve row
takes the **whole dict**, never a hand-written list of keys — which is why this
field travelled on its own.

---

## C5 · D2's process fix — the lint no longer collides with the lock

**Wilson, 2026-09-26.** Twice now a settled-claim keyword has been found in a
body that was **already locked** (IDF-1, then IDF-2), where every fix is an
edit to a pre-registration after results exist. The document was not changed
either time; the **process** was.

1. **The suite exempts a locked prereg by hash.**
   `tests/test_settled_claim_lint.py::_locked_exempt` — exempt only while the
   body still matches its recorded sha. ⭐ The first later edit moves the sha
   and the lint fires again on the edited text, so nothing is silently waived,
   and the exemption is keyed on the **hash, not the filename**. A non-prereg
   live document such as `MEASUREMENTS.md` is never exempt.
2. **`lock_prereg.py --lock` runs the lint and refuses to hash a failing
   body.** The keywords are caught while they can still be rewritten, which is
   the only moment they can be. `--force` overrides, and the refusal stamps
   nothing.

Both halves red-proofed: a violating body is refused, a qualified one locks
normally, and the exemption dies the moment the body moves.

✅ **Suite: 2,673 pass, 0 fail.** All three preregs verify against their locks
and no locked body was edited. **D2 above is closed by this entry.**

---

## ✅ STEP P — RAN, PASSED, AND THE MARGIN IS THIN

2026-09-27. Box `a6f08ed3a91b4eee8797493cdf9757cc`, A100-SXM4, pinned at
`32d43cf`, total wall **13,034 s (3.6 h)**. The watchdog was armed before any
GPU time, the box persisted all eleven artefacts to the hub and then
**terminated itself on `~/DONE`**. Artefacts: `hf://…/stepP/`, local copies in
`runs/act2/idf2/stepP/`.

### The gate

| | |
|---|---|
| reads | **8** (7 df), every one at `n_pairs` **384** except seed 20630 at 377 |
| dropped chains | **0** across all eight |
| mean `closes` | **9.98 points** |
| between-seed SD | **5.79 points** |
| **2 × SD** | **11.59** vs the 15-point boundary |
| **verdict** | ✅ **PASS** — the table resolves its own boundaries |

⚠️ **It passes at 1.29× the boundary, which is not comfortable**, and §3A's
rule is met by the letter. The consequences are below and they are Nate's and
Wilson's to rule on, not mine.

### ⭐⭐ F1 · `closes(M) − closes(C1)` has good power for INSTALLS and MARGINAL power for FLOORS

At 3 seeds per treatment arm and the measured SD:

- `SE(difference) = 5.79 × √(2/3)` = **4.73 points**
- 95 % CI half-width (t, 4 df) = **13.13 points**

So if the marker's true effect is **zero**, the CI upper bound lands at
**~13.1** against FLOORS' requirement of **< 15**. Reachable — by 1.9 points.
A 35-point effect sits **7.4 SE** from zero, so INSTALLS is comfortable.

⛔ **The branch with the least power is the informative one.** §0 says so in
the prereg's own words: INSTALLS means "the model can follow an explicit
avoid-list", while **FLOORS is the result that bears on the weights**. Any
inflation of the treatment arms' variance over C0's — plausible, since M's
marker introduces a source of variation C0 does not have — pushes that upper
bound past 15 and makes the informative cell **undeclarable**.

⭐ **This is exactly the decision §3A exists to place here.** Raising the
treatment arms from 3 seeds to 5 gives `SE = 3.66` and a CI half-width of
**8.4 points**, a comfortable margin, for **4 extra reads ≈ 1.9 GPU-h** on M
and C1. Changing it now, before any treatment exists, is a **re-lock**;
changing it after M has read is retrofitting. ⛔ Not taken unilaterally.

### ⭐⭐ F2 · the published `0.3854` was one draw, and its spread is now measured

C0 re-read at 48 × 10, eight seeds:

    0.3750  0.3776  0.3854  0.3854  0.4193  0.4244  0.4271  0.4323
    mean 0.4033 · SD 0.0245

The **0.3854** carried through D6, IDF-1 and IDF-1b is a single read at 120
turns. It sits **2nd-lowest of these eight** — inside the spread, on the low
side, and not a central estimate.

⚠️ At 120 turns the lag-2 cell holds 96 pairs against 384 here, so the
single-read SD at that size is roughly **2 × 0.0245 ≈ 0.049**.
`RESULTS_IDF1B` §5 reports *"model 0.3854 · best generalising window-1 speaker
0.4238 … model-minus-floor is negative, by 0.0384."* **That difference is
about 0.8 × the model's own single-read SD at the size it was measured at.**

⭐ IDF-1b said the two were not distinguishable — *"0.3854 lies comfortably
inside O-B(4)'s 95 % band"* — so this does not contradict it. What is new is
that the **model's own** read-to-read spread is now measured rather than
unknown, and it is of the same order as the difference that was reported.
⛔ **No IDF-1b verdict is declared here.** This is a measurement that bears on
one of its three conflicting facts; choosing among them remains Nate's and
Wilson's.

---

## D4 · Five seeds per gating arm, not three — re-locked on Step P's measured SD

**Wilson, 2026-09-27, on F1 above.** The prereg body says three seeds per
object (§5, sign-off #4). ⛔ **The body is LOCKED and is not edited**; the
change is recorded here and the operative constants live in
`tools/act2_idf2.py` (`SEEDS_PER_GATING_ARM`), where a pipeline reads them
rather than a default someone has to remember.

| | 3 seeds | **5 seeds** |
|---|---|---|
| `SE(closes(M) − closes(C1))` | 4.73 points | **3.66** |
| 95 % CI half-width | 13.13 (t, 4 df) | **~8.4** (t, 8 df) |
| FLOORS' `< 15` margin at a true zero effect | **1.9 points** | ~6.6 points |

⭐ **The reason is FLOORS specifically, not precision in general.** INSTALLS
was never at risk — a 35-point effect is 7.4 SE from zero. But §0 says in the
prereg's own words that INSTALLS only means *"the model can follow an explicit
avoid-list"*, while **FLOORS is the branch that bears on the weights**. At
three seeds a marker that does nothing would land within two points of being
undeclarable, and any variance the marker adds over C0's — plausible, since it
introduces a source of variation C0 does not have — pushes it over. ⛔ A design
whose most informative branch is the one it cannot declare is exactly the
"failure that teaches nothing" §3A was written to remove.

**Applies to the arms that gate a cell: M, C1, M-strip.**
⚠️ **W2 and M-shuffle stay at three** — my reading of *"keep W2 and M-shuffle
at the same count"* as the count they already had. Both are descriptive and
neither gates a cell. Flagged rather than absorbed; it is +4 reads if five was
meant everywhere.

⭐ **This is legitimate and the reason it is legitimate is the timing.** It is
based on a measured SD, and it is made **before any treatment adapter exists**.
§3A: widening after M has read is retrofitting. **Nothing in the reading table
changes — only its power.**

**Cost:** 21 reads instead of 15 → ≈ **+2.8 GPU-h**.

---

## D5 · C0's lag-2 is the 8-seed mean from now on, not the single draw

**Wilson, 2026-09-27, on F2 above.** `0.3854` was one 120-turn read and it came
in **2nd-lowest of eight**. The campaign cited it through D6, IDF-1 and IDF-1b
as though it were central.

> **C0 lag-2 = 0.4033 ± 0.0245** (8 seeds, 48 × 10, 384 pairs each)
> — cite this wherever C0's lag-2 appears, including as IDF-2's bridge.

⭐ **And it corroborates a floor already on record, from a different
measurement.** Scaling the measured SD from 384 pairs to 96 gives **0.0490**
for a single 120-turn read; the difference between two such reads is
`√2 × 0.0490 =` **0.0693**, against the **0.073** same-object floor recorded in
`RESULTS_EPOCHS_LEVER_2026_09_17.md`. **94.9 % agreement**, and the two were
arrived at by unrelated routes.

⚠️ So the spread is not news — what is new is that it is now attached to the
specific numbers people quote. Recorded as a **dated descriptive addendum** to
`RESULTS_IDF1B_2026_09_25.md` §5. ⛔ **No IDF-1b verdict is declared**, and its
three conflicting facts remain open.

---

## ⏭ What Step 0 does NOT clear

⛔ **Step P has not run, and no GPU has been touched.** Step 0 was the CPU
gate; §3A's power check is the first GPU step and it requires Nate's sign-off
per §4. Until Step P reports `2 × SD ≤ 15 points`, the reading table is not
known to resolve its own boundaries and **no adapter may be trained**.

⛔ **D2 is unresolved** and is a decision for Nate and Wilson, not a blocker
I may clear by editing a locked body.
