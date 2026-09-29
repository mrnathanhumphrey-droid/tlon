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

## D7 · RUN 1 LOST ITS ADAPTERS TO A TYPO — and its numbers are FROZEN here as a prediction

**2026-09-28.** Run 1 trained M and C1, cleared every gate, took all eighteen
reads — and then died at `rc=2` on `act2_box_persist.py persist --cells`, a
subcommand that does not exist. The watchdog correctly terminated a box holding
~7 GPU-h of weights that were in no other place. **Only the log survived.**

⛔ The correct call was already in `pipeline_retrain.sh:215`, and so was the
ordering rule beside it — *"the adapter is already durable, so a fault in the
read costs the read and not the weights."* Neither was copied. The single
persist step sat AFTER all eighteen reads, so the failure landed at the
most expensive possible moment instead of four minutes after M finished.

### ⛔⛔ THESE NUMBERS ARE FROZEN BEFORE THE RE-RUN, SO THE RE-RUN IS A REPLICATION

*(Wilson's condition. Recovered by regex from `pipeline_idf2_train.log` into
`runs/act2/idf2/train/recovered_reads.json` — stdout, not artefacts.)*

| arm | n | lag-1 | lag-2 | closes |
|---|---|---|---|---|
| **M** | 5 | 1.0305 | 0.0485 | **93.8 %** |
| **C1** | 5 | 1.0370 | 0.4453 | **0.1 %** |
| **M-strip** | 5 | 1.0606 | 0.4141 | **7.5 %** |
| **M-shuffle** | 3 | 1.0293 | 0.6545 | **−49.4 %** |

Per-seed `closes(M)`: 91.8 · 91.8 · 91.8 · 96.7 · 97.3.
`M − C1` = **93.8** points, 95 % CI **[88.4, 99.1]**.
`M − M-strip` = **86.4** points, CI **[79.7, 93.1]**.
Perceive guard **0.994**. Between-seed SD **2.87 / 3.22** against Step P's 5.79.

⛔⛔ **NO VERDICT IS DECLARED FROM THESE.** Three reasons, and the first is
sufficient on its own:

1. **§6's PARTIAL and FLOORS cells require the per-root readout**, which needs
   the read transcripts, which needs the adapters. All gone.
2. The provenance is a **regex over stdout** — no `marker_fn` field, no
   `n_pairs`, no recorded decoder. The weakest evidence class in this campaign.
3. **§0's own warning stands:** M closing 93.8 % means the model followed an
   explicit avoid-list. The prereg calls that the near-trivial branch, and
   FLOORS was always the informative one.

⭐ **Their value is as a PREDICTION.** The re-run is now a replication against a
frozen table rather than a fresh look, and a re-run that lands far from these
numbers is itself a finding.

---

## D8 · W2 enters the re-run — it is now the arm that matters most

**Wilson, 2026-09-28.** W2 was deferred under option (b) and is absent from all
eighteen recovered reads. With M's result reading as *"the model can follow an
explicit avoid-list"*, W2 — `t−2` and `t−1` as real chat turns, no marker, the
model deriving the intersection itself — is the only arm in the design that
asks the art piece's question. It goes in.

---

## D9 · Three mechanical enforcements, because writing the rule down did nothing

**Wilson, 2026-09-28:** *"Writing the rule down again does nothing if nothing
forces it."* The persist call had a rule, a working example and a test, and
still shipped broken. So:

1. **One `persist_cell()`, imported, never spelt.** Every pipeline calls one
   function from one module. ⭐ There is no command string left to mistype and a
   new pipeline cannot invent its own call.
2. **The launcher refuses without a smoke receipt.** A CPU dry run writes a
   file carrying the git sha and the exit code of every step; no receipt, or a
   receipt for a different sha, and the launch aborts before a box exists.
3. **The monitor alarms on STALENESS, not silence.** The box writes a heartbeat
   timestamp; older than N minutes *or unreadable* is an alert. ⛔ Run 1's
   monitor printed blank lines for two hours after the box died, and the last
   number it ever saw was reported as live progress.

---

## ⛔⛔ D10 · THE ESTIMAND'S TWO HALVES SPLIT ON F-LOCAL — M CLEARS, C1 FIRES

**Run 3, 2026-09-28.** Both gating adapters trained, dose-matched and persisted.
Their F-LOCAL gates disagree, and the disagreement lands on the estimand.

### What the gate reported, both arms, verbatim

Same battery `d9ecdf9fbf2caa8a`, `n=64`, cardless and unconstrained — the only
configuration the gate accepts.

| | **M** (marked) `20:47:46` | **C1** (unmarked) `00:32:27` |
|---|---|---|
| speak | 100.0 % (64/64) | 100.0 % (64/64) |
| **render** | **92.2 %** (59/64) | **65.6 %** (42/64) |
| **verdict vs 0.90** | **CLEAR** | **FIRED** |
| force | `ka` 83 % · `kä` 17 % | `kä` 50 % · `ka` 31 % · `ku` 19 % |
| force read | ⛔ `ka` is 82.8 % of 64, cap 60 %; 2 distinct, need 3 | ✅ `kä` leads at 50.0 %, 3 forces present |
| choose | 35.9 % (23/64) | 45.3 % (29/64), 0 unanswered |
| render confusions | 2 · `{'D→M': 1, 'D→Q': 1}` | 1 · `{'A→Q': 1}` |
| diversity | distinct 12/12 · repeat 1.00 · response 1.00 · dependence +1.00 ⇒ input-dependent | identical |
| Amendment A (0.35–0.95) | 35.9 % ⇒ clear | 45.3 % ⇒ clear |

- **M:** *"render 0.922, speak 1.000 vs threshold 0.90 — clear; drift is
  measurable on a native speaker."*
- **C1:** *"render 0.656, speak 1.000 vs threshold 0.90 — the class system is
  not internalised at this scale; drift would be confounded with
  validity-failure."*

### What it changes

§4 of the locked prereg: **"F-LOCAL must clear on each new adapter before any
lag read of it is interpreted."** C1's did not clear. The estimand is
`closes(M) − closes(C1)`, so **the pre-registered consequence falls on the
estimand itself, not on one arm's side reading.**

⛔ **THIS IS NOT RESOLVED HERE.** Whether C1's reads may be interpreted, and on
what terms, is Nate's and Wilson's call. The run continues — the reads are
taken and recorded either way, because a reading that may not *decide* can
still *describe*, and both adapters are already durable on the hub.

The prereg named the recovery set before it could be needed: (1) more
contrastive negatives · (2) curriculum fine-tune · (3) bigger backbone. ⛔ The
third is a sign-off item and never mine.

### What it does NOT change — checked, not assumed

- ⭐ **This is not the dose confound.** `dose_w` M `0.00556983`, C1
  `0.00548976`, **both ✅ WITHIN BAND**, and they sit closer to each other than
  the band's width. §4's "M and C1 must match each other at least as closely as
  either matches `ct-s20624`" is satisfied. The spread the C1 redesign existed
  to remove is not what fired.
- **Neither adapter is at risk.** Both persisted to the hub *before* F-LOCAL
  ran — the red team's reordering, working as intended on its first live
  outing. A gate about whether a reading may be interpreted no longer decides
  whether weights survive.
- **W2 is untouched by this.** It trains after C1 and carries its own F-LOCAL.

### ⭐ The two readouts point opposite ways

M renders the class system well and collapses onto one force (`ka`, 82.8 %, two
forces where three are wanted). C1 spreads all three forces and renders poorly.
Both force lines are stamped **"⭐ read, not a gate"** in the instrument, and
neither is a result. ⛔ **No direction is inferred here** — it is recorded so
that whoever reads the lag numbers has both diagnostics in front of them.

---

## ⛔⛔ D11 · §7'S PER-ROOT READOUT HAD NEITHER A TOOL NOR AN INPUT — FOUND BEFORE THE READS, NOT AFTER

**2026-09-28, during a pre-read audit of the analysis path.** §7 defines it:

> `P(root of t−1 reappears in t | marked)` vs `P(… | unmarked)`, with a CI,
> **computed from the M read transcripts** (no extra generation).

Two independent failures, both verified before anything was changed:

1. **No implementation.** `grep -rn "per_root|per-root" --include=*.py` returns
   nothing outside `runs/`. Checked under `reappear`, `avoidance`, `by_root`
   and `root_level` as well — the readout was never written.
2. **No input, and unrecoverable after the fact.** `_read_lag_inner` returned
   aggregates only — `lag_profile`, `z`, `null`, `n_pairs`, `resolving_power`,
   counts, verdict. The chains it built were **never serialised**; the pipeline
   persisted `corpus_diff.json`, `dose_*.json`, `lag_*.json` and nothing else.
   The generated surfaces existed only inside the process that made them.

⭐ **Why it survived the whole campaign: runs 1 and 2 died before the read
phase.** A defect at the END of a pipeline is invisible to every run that never
reaches the end. This is [[feedback_use_the_harness_whole]]'s shape again — a
precondition that only fails after the expensive part — arriving this time in
the analysis rather than in the persist.

### ⛔ §6 AND §7 DISAGREE ABOUT WHICH CELLS NEED IT

§7 says it *"appears as a conjunct in all three cells of §6."* **It does not.**
§6's INSTALLS lists four conjuncts — `closes(M)` ≥ 35 on all seeds, the
difference CI, M-strip's drop, the perceive guard — and this is not among them.
PARTIAL and FLOORS both name it. **Two of three.** Recorded, not resolved: the
discrepancy is inside a locked body.

⇒ Without transcripts a completed run can decide **INSTALLS** and cannot decide
**PARTIAL or FLOORS** — the two branches a null lands in.

### The decision, and why the instrument was NOT changed mid-run

**Nate, 2026-09-28: option 2.** Run 3 finishes on its pinned commit, untouched.
The capture read is taken afterwards against the adapters, which are already
durable on the hub, so it costs generation and no retraining.

⛔ **The rejected option was patching the reader and pushing to the box before
the read phase began** — a change to the measuring instrument, mid-flight, on a
pinned commit, unreceipted, against a ~2-hour clock. Those are the exact
conditions that produced both previous losses, and the smoke receipt exists to
refuse precisely that launch.

### What was built instead

- **`--save-transcripts` on `act2_model_lag.py`.** Off by default, so no
  historical row changes shape (`C2` is the record of what a silent payload
  change costs). ⭐ It records the **marker line shown at each turn**, not just
  the surfaces: `held` is recoverable from two surfaces, but **`marker_shuffle`
  is not** — it draws non-held roots from an RNG, so what the M-shuffle arm
  actually showed the model exists nowhere else. Surfaces alone would have left
  one arm permanently unreadable.
- **`tools/act2_idf2_per_root.py`** — §7's quantity, with §8's requirement met
  (a committed tool, never a heredoc).
- **`tests/test_idf2_per_root.py`** — 13 tests.

### ⛔⛔ THE INTERVAL IS MEASURED LIBERAL, AND THE NUMBER TRAVELS WITH IT

The CI is a **cluster bootstrap over chains, not roots** — the chain is what the
experiment re-rolls ([[feedback_find_the_real_unit_of_independence]]). That was
not enough. Simulated against a **true null** (independent `reappears`, no
marker effect at all), 300 trials per cell:

| chains | percentile | t-corrected |
|---|---|---|
| 12 | **9.0 %** | 6.3 % |
| 24 | 8.7 % | 7.3 % |
| **48** — the pipeline's `RCHAINS` | **7.3 %** | **7.0 %** |

Against a nominal **5 %**. ⛔ `USES-MARKER-PARTIAL` fires on *"CI excludes 0"*,
so a liberal interval **manufactures the very cell it is a conjunct of.** The
t-correction is applied — never worse, much better at small n — and it does
**not** reach nominal at 48 chains. So the measured rate is **printed beside
every number the tool emits** and pinned by a test, because calling it a "95 %
CI" without that is [[feedback_the_numbers_resolution_must_match_the_decisions]].

⭐ On a fixture with a planted effect (marked roots kept at 0.15, unmarked at
0.50, 48 chains) it recovers `−0.3627`, CI `[−0.4116, −0.3139]`.

### Two smaller findings from the same pass

- **`sys.stdout.encoding` is `cp1252` on the laptop**, so the tool's own
  refusal message — the one that says *"re-read with `--save-transcripts`"* —
  raised `UnicodeEncodeError` on being printed. Every other analysis in the
  campaign runs on the box where stdout is UTF-8; this one needs no GPU, so it
  is the one that gets run on Windows. ⭐ A refusal that cannot be printed is a
  refusal nobody receives.
- ⛔ **A full-suite run reported `exit code 0` having executed zero tests.**
  `pytest --timeout=…` is rejected by an installed `seleniumbase` plugin during
  `pytest_addoption`; pytest aborts before collection **and still exits 0**.
  Reading the status line rather than the output would have produced a "full
  gate green" claim on a run that never happened —
  [[feedback_summary_fields_must_be_checked_against_their_run]] through a
  plugin nobody knew was in the environment.

---

## ⛔⛔ D12 · RUN 3 TOOK ZERO OF ITS 21 READS — W2's DOSE GATE ABORTED THE WHOLE RUN

**2026-09-29, 04:57:52 UTC.** All three arms trained, persisted and gated.
Then, on the last per-arm step of the last arm:

```
=== [dose_heldW2-s20624] 04:57:52 ===
  dose_w         0.0058099
  reference      0.00544947   band [0.005177, 0.00572194]
  ⛔ OUT OF BAND
⛔ FAILED at stage: dose_heldW2-s20624 (rc=2)
```

`set -e`, and `step reads` sits **after** the arm loop. The watchdog then did
its job exactly right — `KILL · process 2932 is gone and the run did not
complete` — flushed the run log, the watchdog log, all three `factorial.json`
and all three `dose_*.json` to the hub, and terminated the box.

### ⛔ THE PREREG DECLARED THE OPPOSITE, IN ADVANCE

§4: *"If the second attempt also misses, the arm **trains anyway and reads
anyway**, and its rows are reported with the miss stated beside every number —
but `dose_w` joins the confound list and no §6 cell may be declared on that
arm."*

That is a rule about **one arm's interpretation**. It was implemented as a
non-zero exit under `set -e`, which is a rule about **the whole run** — and it
stopped M and C1, whose doses were fine, from being read at all.

### ⛔⛤ THE MISS WAS PREDICTED IN WRITING AND HALF-MITIGATED

`pipeline_idf2_train.sh` says, at the persist reorder: *"The dose gate exits
NON-ZERO by design, and **W2's rows carry a prior turn each — more tokens, so a
genuinely different training trajectory and an rms that may legitimately miss
the ±5 % band.**"*

⭐ That foresight moved PERSIST ahead of the gates, which is the only reason all
three adapters survived. It never stopped the gate from **aborting the run**.
The blast radius was shrunk from the weights to the reads and the job was
called done — [[feedback_a_named_confound_must_be_guarded_at_the_point_of_use]]
with the guard placed one step short of where it fires, for the second time in
the same file.

### What run 3 actually produced

| arm | render | F-LOCAL | forces | dose vs reference |
|---|---|---|---|---|
| **M** | 0.922 | CLEAR | 2 (`ka` 83 %) | **+2.2 %** ✅ |
| **C1** | 0.656 | **FIRED** (D10) | 3 (`kä` 50 %) | **+0.7 %** ✅ |
| **W2** | **0.953** | CLEAR | **4** (`ku` 39 %) | **+6.6 %** ⛔ |

⭐ **W2 is the healthiest speaker of the three** — best render, four forces
present, `choose` 54.7 %. The arm D8 called *"the only arm in the design that
asks the art piece's question"* trained well and cleared its validity gate.

⭐ §4's cross-condition holds: M and C1 sit **1.5 points apart**, closer to each
other than M is to the reference. The spread the C1 redesign existed to remove
is not present.

### The fix: `tools/pipeline_idf2_reads.sh`

The adapters are durable, so the reads cost generation and no retraining.

- **The dose gate is RECORDED, NEVER FATAL.** It still runs on every arm and
  writes `dose_confounds.txt`; it cannot stop a read.
- ⛔ **And the swallowed exit is guarded.** `cmd_dose`'s own comment says the
  non-zero exit exists so *"that is a decision, so it is not taken silently
  inside a loop"* — which is precisely what `|| true` would be. So the expected
  confound set is **pinned** (`heldW2-s20624`); any other arm going out of band
  raises a banner and marks the run `UNEXPECTED`. Still not fatal, because
  twenty-one readings must not die for a gate about interpretation.
- ⛔⛤ **Reads persist PER ARM, not at the end.** `pipeline_idf2_train.sh` ran
  `step persist` once after all 21, so a death at read 20 would have lost 20
  paid-for readings — the same "durable only at the end" shape that cost run 2
  its adapter, surviving in the one place the fix did not reach.
- **`--save-transcripts` on every read**, so D11's per-root readout has an input.
- W2 **reads anyway**, per §4, with `dose_w` on the confound list and **no §6
  cell declarable on that arm**. The retrain §4 permits is *permitted*, not
  required, and remains Nate's and Wilson's call.

---

## ⏭ What Step 0 does NOT clear

⛔ **Step P has not run, and no GPU has been touched.** Step 0 was the CPU
gate; §3A's power check is the first GPU step and it requires Nate's sign-off
per §4. Until Step P reports `2 × SD ≤ 15 points`, the reading table is not
known to resolve its own boundaries and **no adapter may be trained**.

⛔ **D2 is unresolved** and is a decision for Nate and Wilson, not a blocker
I may clear by editing a locked body.
