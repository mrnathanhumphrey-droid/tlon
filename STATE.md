# Tlön — STATE

**Updated:** 2026-08-25. ⭐⭐ **THE RESEARCH IS SEALED. THE LIVE WORK IS THE
PRODUCT — the open-world chatbot (the freeware door).**

✅ **ACT 2 TIER-A DONE. THE 7B READS AND WRITES TLÖN NATIVELY.** Four Lambda
runs, every instance TERMINATED, ≈ **$23** total. **$1,500 untouched.**
⭐ **PUBLIC: https://github.com/mrnathanhumphrey-droid/tlon** (MIT, all pushed).

| | baseline | run 3 | at n=256 |
|---|---|---|---|
| render (English→Tlön) | 0.0 % | 84.4 % | **82.0 %** CI [76.8, 86.5] |
| speak (Tlön→reply) | 0.0 % | 98.4 % | **97.3 %** CI [94.4, 98.9] |
| comprehension | 46.9 % | 68.0 % | **71.1 %** |

⭐⭐ **COMPREHENSION IS ESTABLISHED** — McNemar **p = 1.1 × 10⁻⁶** (n=256).
⛔ **The same 64 items read p=0.21 UNPAIRED and p=0.000049 PAIRED.** You cannot
recover pairing you did not record. Per-item outcomes are now ledgered.

⛔ **THE GATE IS RESOLVED AND RENDER FAILS: 82.0 %, CI ENTIRELY BELOW 0.90.**
At n=64 it was formally UNDECIDABLE (CI [73.1, 92.2] contained the bar) — the
extra $2 of measurement was the difference between knowing and guessing.

# ⛔⛔ THE ARENA IS NOT READY, AND WE KNOW EXACTLY WHY

⭐⭐ **`speak 97.3 %` DOES NOT MEAN "CONVERSES".** The probe fed **depth-1**
histories, and at depth 1 the model **deterministically ECHOES `parse(history)`**
(8/10 exact, 1/8 distinct, identical at temp 0.0 AND 1.5). An echo of a valid
parse is trivially valid. Behaviour by history depth, measured:

| depth | valid | echoes last | distinct on same history |
|---|---|---|---|
| 1 | 10/10 | 8/10 | 1/8 |
| 3 | 8/10 | 0/10 | 5/8 |
| 5 | 6/10 | 0/10 | 8/8 |
| 8 | **5/10** | 0/10 | 7/8 |

**The two ends fail in opposite directions:** shallow = legal but a deterministic
mirror (drift impossible by construction); deep = varied but **validity collapses
to 50 %** (drift confounded with validity-failure). The arena lives at growing
depth.

**EXCHANGE PROBE** — 40 turns, temp 0.9, criteria locked before the data:

| | interacting | control (frozen partner) |
|---|---|---|
| validity last quarter | **40 %** | **50 %** |
| root TTR | 0.12 → 0.12 | 0.12 → 0.12 |

⭐ **BOTH ARMS DEGENERATE ⇒ IT IS THE MODEL, NOT THE EXCHANGE.** It falls apart
against a partner that isn't even listening. **An intrusive-thought generator
would paper over a speaker that cannot sustain generation alone.** Transcript:
**6 distinct utterances in 18 legal turns**, mean 2.9 differing tokens of 14,
mostly aspect-reduplication jitter.

⛔⛔ **AND 2 OF MY 3 PRE-SPECIFIED CRITERIA FAILED TO FIRE ON IT.** TTR *decline*
read **+0 %** because TTR was already 0.12 at the first window; the *exact*-cycle
check missed near-repetition. Only validity caught it. **A decline-based or
exact-match measure cannot see a speaker that starts degenerate and jitters —
F4 HAS THE SAME SHAPE and σ_cp must not inherit it.**

# ⛔⛔ F4 READ CLEAR ON THAT COLLAPSE — FIXED, D15

**1,019 tests.** F4's two branches are both RELATIVE, and on the probe both read
**+0.0 %**: the decline branch because TTR was *already* 0.125 at the first
window, the level-vs-control branch because the control was equally degenerate
(0.125 vs 0.125). ⭐⭐ **A RELATIVE MEASURE HAS NO OPINION WHEN BOTH ARMS ARE ON
THE FLOOR** — and with a yoked design, both arms are the same weights, so that is
the *likely* case, not a corner one.

`falsify.degeneracy_guard` is the absolute third branch. Both thresholds come
from **the corpus null alone and never saw the degeneration**:

| | threshold | derived from | margin on the event |
|---|---|---|---|
| root-TTR floor | **0.50** | corpus min **0.700** over 2,500 windows | event 0.056; **0/2,500** near it |
| near-repetition | **0.75** | random corpus pairs max **0.500** over 20,000 | **153/153** pairs above the corpus max |

Red-proofed both ways: fires on the real transcript (both arms), **0/200 healthy
corpus windows fire**, <2 utterances REFUSED. ⛔ **σ_cp MUST NOT INHERIT THE
SHAPE** — a coupling term defined as a *change* reads 0 on a pair stuck from turn
zero, and σ_cp = 0 is *defined* to mean "independent, no pact".

# HARDENING STATUS

- ✅ **HARDEN 2** — Diagnosis C verdict re-keyed off the saturating `dependence`
  onto `valid`; detects its own saturation. 12 tests.
- ✅ **HARDEN 3 (structural)** — `falsify.arena_preconditions` RAISES below the
  temperature floor and on a degenerate speaker at a legal temperature. 21 tests,
  both ends red-proofed.
- ⛔ **HARDEN 3 (empirical) — `MIN_ARENA_TEMPERATURE = 0.7` IS AN UNVALIDATED
  PLACEHOLDER.** ✅ Now flagged **in the identifier**
  (`MIN_ARENA_TEMPERATURE_PROVENANCE`, `..._IS_MEASURED = False`) and stamped
  into every refusal. `act2_temp_sweep.py` **refuses `--depth < 3`** and splits
  the two causes of "no usable temperature": *varies nowhere* (a sampler finding)
  from ***legal* nowhere** — ⭐ **which is a DEPTH-COMPETENCE finding that belongs
  to the multi-turn corpus, and no temperature can close it.**
- ⏳ **HARDEN 1 / §8.2 — CORPUS BUILT, RETRAIN NOT RUN.** See below: the named
  instrument was wrong.
- ⛔ **HARDEN 4 — BLOCKED.** Validating the arena harness against a speaker that
  cannot hold 40 turns would validate it against noise.
- ⏳ **HARDEN 5** — product ops, separate track, non-blocking.

# ⛔⛔ §8.2 — THE NAMED INSTRUMENT WAS THE WRONG ONE (D16)

⛔ **AND THE SUMMARY THIS FILE CARRIED MIS-RANKED ITS OWN RUN.** It said *"`L→M`,
`Q→A` dominate 48 confusions"*. Read off the ledger: the top ordered pair is
**`M→R` at 7**, and the right unit is not the pair at all — it is the **missed
slot**, where no single pair dominates because `A` is missed from *six* different
source classes. [[rule_zero]], eighth time.

§8.2 asks for *"the small-class targeted positives"*. Per-form exposure was
**already flat** — A 663 · M 663 · Q 662 · T 649 · D 670 — and 3 of the 4
hand-targeted forms are **gone from the confusions entirely**.

⭐⭐ **ERRORS TRACK SLOT RARITY, NOT FORM RARITY:**

| slot | occupancy | missed-slot errors |
|---|---|---|
| `root` | 100.0 % | 8 — *156 forms, fewest errors per fill* |
| `relator` | 61.1 % | 0 |
| `orient` | 30.9 % | 2 |
| `modal` | 6.4 % | 11 |
| **`aspect_root`** | **3.9 %** | **16** — the biggest hole |
| `quant` / `degree` | 3.9 % | 5 / 2 |

**The model has seen every A-form 663 times and still has not learned which slot
is an A-slot** — it has only seen one filled once every 26 nodes. And the rarity
is by design: `_decoration_p` sets occupancy to `len(class)/len(R)` *precisely
so per-form exposure evens out*. **The balancing worked, and it optimised away
the thing that was missing.** ⇒ **exposure teaches the FORM; occupancy teaches
the FUNCTION, and only one of them was ever reported.**

Built, $0: **`slot_floor=0.30`** (from `orient` 30.9 %→2 errors and `relator`
61.1 %→0) · **`contrastive_pairs`** — two legal scenes one slot apart, e.g.
`nol mlang ko` *(oft, it dreams)* vs `mlang testesas ko` *(it dreams, again and
again)*: same root, same force, and the only difference is whether repetition is
a **Q** or an **A** · **`--from-ledger`** mines the confusions from the newest
run, because ⛔ **the hand-kept list ROTTED** — `{pal, rän, plas, hul}` was still
being boosted three runs after three of them were fixed.

⚠️ **OPEN:** `aspect_root` is an outlier *even among* rare slots — 16 vs `quant`'s
5 at identical occupancy. Two candidates, no measurement separating them: it is
the only two-field slot (`aspect_root` + `aspect_reps`) and the only one whose
surface is a reduplication; and Q/A collide in English (*oft* vs *habitual*).

⛔ **"HOLD COMPUTE CONSTANT" MEANS TOKENS, NOT ROWS** — flooring lengthens every
scene and contrastive pairs add rows. The builder prints the token total so `--n`
can be trimmed, or the render delta is confounded with a longer run.
**⏳ THE RETRAIN IS LAMBDA SPEND AND HAS NOT BEEN RUN.**

# ⭐ NEXT: THE DISCOURSE LAYER — `docs/SPEC_DISCOURSE_LAYER_v0.1_2026_08_25.md`

Received 2026-08-25; recorded verbatim with a **verification pass** on top.
Verified real: residue + Scene distance, the Turbulence σ_cp lane, the calibrated
discrete-KM estimator, all 5 forces. **Four findings:**

1. ⛔ **Five M-class form-names do not exist** — `sköl`→**`xöl`** · `xoth`→**`xos`**
   · `nek`→**`nem`** · `dul̈`→**`hrin`** · `wir`→**`mir`**. The ten
   ways-of-holding map one-for-one; only the spelling is off. **§8.1's table must
   key on the lexicon.**
2. ⭐ **§8.3 is largely PRE-PAID** by Turbulence — and its first closed form
   `σ_cp ∝ dᵀKd` **FAILED a PSD gate 5000/5000**; the correct object
   `σ_ex^MN − σ_ex^HS` passed 0/1500. **Peak EXISTENCE locked, peak LOCATION
   HELD** (s*=0.45 was a placeholder artefact) ⇒ **pre-declare the SHAPE, never
   the location.**
3. ⛔⛔ **§3 ρ_wide HAS NO NON-VACUOUS VALUE.** Measured over 3,000 random scene
   pairs (median 4.75, range 1.0–7.65): ρ=4.0 puts **16 %** of RANDOM pairs
   in-region (proximity-coherence, forbidden by C-D2); ρ=6.0 puts **98 %**
   in-region (criterion 1 **cannot fire**). **No ρ_wide is both wide-by-design
   and falsifiable.**
4. ⏳ §8.1 base convention table **unbuilt** — the load-bearing derivation.

# ⭐⭐ RULED 2026-08-25 — 7 RULINGS. THE REGION GATE IS WITHDRAWN.

⭐⭐ **THE ρ_wide CONTRADICTION WAS NOT A BAD PARAMETER — IT WAS THE WRONG KIND OF
CRITERION, AND THE SOURCE TEXT SAID SO ALL ALONG.** §1 of the spec quotes Borges:
the world is *"successive, **temporal, not spatial**"* — and §3 then put a
**spatial distance gate on it**. C-D2 finishes the argument: Tlönian criticism
attributes *unrelated* works to one author and prizes contradiction, so
unrelated-held-as-one is the **prized** case. If any two impressions can be held
as one unfolding, there is **no out-of-region by content-distance**. The width was
never "very wide" — it is **total**, and a total region is not a gate.

⇒ **§3's region criterion is WITHDRAWN. ρ_wide is DELETED**, not re-tuned or
re-based. Residue geometry is **demoted to description** (wide vs deep abiding),
which it does honestly. **A parameter, a failure mode and a category error all
leave at once.**

⇒ **§5's oracle drops to TWO conditions**, both on axes that are *not content*
and therefore *can* fail: **evidential smoothness** (the temporal axis the
ontology endorses) **AND force = ABIDE**. ⛔ **BREAK is NOT "distant content" —
that was the error.** You do not step out of an unfolding by saying something
unrelated; *that is prized*. **BREAK is breaking the FLOW** — an evidential
discontinuity, or a force driving at closure.

| # | ruling | status |
|---|---|---|
| 1 | §8.1 keys on the **lexicon** M-column; ontology unchanged | ✅ `tlon/discourse/evidential.py`, 22 tests |
| 2 | **§3's region gate WITHDRAWN**, ρ_wide deleted | ✅ spec RULINGS block |
| 3 | §5 oracle → **two** conditions; BREAK redefined | ✅ spec RULINGS block |
| 4 | §7-F2 pre-declares the peak's **shape**, never its **location** | ✅ spec RULINGS block |
| 5 | σ_cp gets an **absolute floor + near-repetition guard** | ✅ D15, 21 tests |
| 6 | `MIN_ARENA_TEMPERATURE` flagged **unvalidated** in the identifier | ✅ sweep refuses depth<3 |
| 7 | **§8.2 starts now** | ⏳ corpus built $0; **retrain not run** |

⭐ **RULING 1 — the ghosts now REFUSE WITH THEIR REPLACEMENT.** `sköl` → *"the
form is `xöl`"*, not merely "not in class M": a stale name that only fails lookup
teaches nothing. And **`base_convention` RAISES rather than returning a plausible
default** — a default table would be consumed by the arena and reported as a
measurement of ten forgotten guesses.

⛔ **RULING 4 — pre-declaring the peak's LOCATION would be the fourth vacuous
falsifier in this project, this one in a physics costume.** The Turbulence toy
locks the shape (0 at both ends, single interior peak, 0/1500 negative) and
**explicitly holds the location** — `s*=0.45` was the geometric peak of a
placeholder.

---

# ⭐⭐ THIS GOES PUBLIC — MIT, FREEWARE AND ART

**Nate, 2026-08-25:** *"its too important/cool and its not something im
gatekeeping. this is gonna be freeware and art. im happy for others to see
everything."* · *"this is getting an MIT license"*

⛔ **`D:\Tlon` IS NOT A GIT REPOSITORY YET** — `git init` is step one.

**Blockers found, all mechanical:**
- ⛔ **16 files exceed GitHub's 100 MB hard limit** — each `adapter_model.safetensors`
  is **308 MB**, plus `optimizer.pt` per checkpoint. `runs/` is **7.1 GB**.
  A `.gitignore` must exist BEFORE the first commit; a 308 MB blob committed once
  is in the history forever even if deleted after.
- ⚠️ `runs/act2/corpus/train.jsonl` is **35.7 MB** and **fully regenerable**
  (`tools/act2_build_corpus.py --n 40000`, seed 20620, deterministic). Prefer
  shipping the builder + the sha256 to shipping the file.
- ⚠️ `docs/RUNBOOK_ACT2_PILOT.md` carries **dead instance IPs** and the Lambda
  terminate command. Scrub before publishing.
- ✅ **SECRET SCAN CLEAN** — no embedded keys anywhere; `ANTHROPIC_API_KEY` and
  `LAMBDA_API_KEY` are only ever read from the environment.

**Still to write:** an MIT `LICENSE`, and a README that works for a stranger —
Borges' nounless language, what is proven vs open, how to run `tools/chat.py`.
⭐ The frozen lexicon `e2b8527010231a81fd31b6eeb9de3d8c` and the locked preregs
are the integrity spine; a public reader should be able to see why they matter.

⛔⛔ **THE COMPREHENSION READING WAS BROKEN AND TWO LEDGER ENTRIES ARE
RETRACTED** — see `DEVIATIONS_ACT2` **D7**. `CHOOSE` asked for "the index" and
never for JSON; the model answered `[0]` and the harness scored all 64 as
NO_ANSWER. **0 % on a 4-way choice is BELOW the 25 % a coin flip scores** — a
below-chance reading is not a weak result, it is a broken one. ⭐ **AMENDMENT A's
band (0.35–0.95) could never have come back clear while the harness could only
read 0.0.** Fixed, red-proofed 3/3, and the band now reads **clear** for the
first time.

**Read in this order:**
1. this header, then `docs/RUNBOOK_ACT2_PILOT.md` if resuming the pilot
2. `docs/SCOPE_CHATBOT_FRONTEND.md` — the product decision doc **and §8, the
   banked conversant vision**
3. `docs/PREREG_ACT2_DRIFT_2026_08_24.md` + `docs/DEVIATIONS_ACT2_2026_08_24.md`
   — **ACT 2, the live research arc**, then
   `docs/DECISIONS_LITERARY_RENDER_2026_08_24.md` and
   `docs/DECISIONS_B2_HARDENING_2026_08_24.md`: decisions, evidence, what was
   rejected, **and the retractions**
4. `docs/VERDICT_13_2_FINAL_2026_08_24.md` — the sealed research record: what is
   proven, what is closed with mechanism, what is open with a condition
5. `docs/ISOLATION_LEDGER_13_1_2026_08_23.md` — the ONLY correct wording of the
   isolation claim; supersedes the pre-13.0 version everywhere

⛔ **STATE.md IS ~1,330 LINES**, append-ordered newest-first, and wants the split
`MEMORY.md` got. Not done; flagged.

---

# ⭐ THE PRODUCT — B1 SHIPPED, B2 PARTLY SHIPPED

**`python tools/chat.py`** — arbitrary English in, nounless Tlön out.
`--offline` runs the whole pipeline on a scripted proposer for **$0.00**;
`--say "..."` renders one line and exits.

**780 tests · 11/11 preregs VERIFIED · lexicon FROZEN `e2b8527…` (156 roots, 0
nouns).**

# ⭐⭐ ACT 2 — constrained LLM-to-LLM drift. PREREG `20620b7c` LOCKED · HARNESS BUILT

`docs/PREREG_ACT2_DRIFT_2026_08_24.md` (Deliverable 0, **$0**) ·
`docs/DEVIATIONS_ACT2_2026_08_24.md` · `tlon/act2/` ·
`tests/test_act2_harness.py` (42 tests) · `python tools/act2_dryrun.py`.
Red-proof **12/12 CAUGHT**. **Synthetic speakers only — no network, $0.00.**

⛔⛔ **THE CONTROL IS THE ENTIRE INTEGRITY OF ACT 2, AND IT WAS BUILT FIRST.** Two
models talking will look alive; the human pattern-matcher is the confabulation
engine. Primary control is **YOKED** — each model live against a *pre-recorded,
non-adaptive* partner — because a solo control varies two things at once
(partner-adaptation AND whether the context is conversation-shaped) and would
attribute nothing. This is H2's frozen-control move.

⭐⭐ **THE INSTRUMENT VALIDATION, AND IT CHANGED WHAT ACT 2 MEASURES.** Speakers
whose drift is known *by construction*, n=8 seed-paired, MDE by exact sign-flip
permutation over within-control replicates:

| synthetic pair | ΔD | ΔC |
|---|---|---|
| stable · wandering · degenerating-alone | +0.00 | +0.00 |
| **imitating — a pact BY CONSTRUCTION** | **−5.08 pts** | **+85.94 pts** (p=0.0078) |
| mutual collapse — falls silent together | −13.67 | **+100.00** → **F4 FIRES** |

⛔⛔ **A PAIR THAT PROVABLY BUILT A SHARED CODEBOOK SHOWS ΔD ≈ 0 — NEGATIVE, IN
FACT.** Two speakers adapting toward two *different* frozen partners depart from
epoch 0 just as far as two adapting toward each other; they simply depart toward
different places. **On F2 alone — the prereg's own load-bearing falsifier — the
cheap pass would report "drift is noise" and close the arc on a demonstrable
private language.** Only `C` sees it. ⇒ **DRIFT IS NOT A PACT**; the claim needs
both observables, and `D`-up-with-`C`-flat has the registered name **WANDERING,
NOT CONVENTION**.

⛔ **AND THE MIRROR:** the largest convergence in the table (**+100.00 pts**)
comes from a pair that has *stopped saying anything*. Without F4 it is the
headline. F4 discriminates: fires on mutual collapse, silent on the genuine pact.

⭐ **MECHANISED, NOT PROMISED** — the rules that a tired human would bend:
- **transcripts are SEALED** (`ledger.SealedTranscript`). The machine may compute
  leakage and covariates; `.turns` RAISES until the run's result is in the
  ledger, and unsealing is itself recorded with a written reason.
- probe context is passed as a **tuple** — the speaker can read the conversation
  and *cannot append to it*, so a probe can never become conversation.
- both frozen partners **must differ** or `arena.run` raises (D1).
- every number goes through `harness/paired.py`; `paired_delta(contrast="arm")`
  refuses unless arm is the only facet that differs.

⛔ **THREE DEFECTS FOUND BY BUILDING** (all in `DEVIATIONS_ACT2`): the
interacting arm probed only speaker A (making `C` uncomputable); F4's
pre-registered rule reads +0.0 % on a *fast* collapse because epoch 0 has no
turns to count; and the covariate compared **raw root counts** across arms with
different token counts — the unpaired-comparison failure, committed by me inside
a covariate, which made F4 fire on *every* cell including the no-drift one.

## ⭐⭐ STEP 2 PRE-FLIGHT RAN — `docs/FINDINGS_ACT2_F1_2026_08_24.md`

**Sonnet 5 · 48 calls · $0.1043 of a $1.00 hard ceiling · ledgered.** Act 2's
first spend, and it bought a stop.

| | |
|---|---|
| **speak** | **16/16 first-attempt legal.** A prompted model CAN speak Tlön cold, card only, zero retries. The conversation loop is not the bottleneck. |
| **render** | **8/16.** ⭐⭐ **NOT ONE HALLUCINATED FORM** — every failure is a REAL lexicon word in the WRONG CLASS (`pal`/`rän` are ROOTS used as aspect; `plas`/`hul` are ORIENTS used as root/relator). **The model has the vocabulary and not the class system** — the failure a fine-tune fixes and a longer prompt does not. |
| **§8 battery** | ⛔⛔ **FIRED. 16/16, AT CEILING.** |

⛔⛔ **THE COMPREHENSION HALF CANNOT SHOW DRIFT AT ALL WHILE PROMPTED, AND IT IS
STRUCTURAL.** The prompt carries the lexicon card; the grammar is exactly
invertible; so decoding is a **LOOKUP**, and a lookup cannot drift. Harder
distractors cannot fix it — the answer is derivable either way. Removing the card
does not rescue it either: epoch-0 accuracy falls to chance, which is §8's
*floor*, and the gate closes from the other side. §1 forbids the dodge (*"no
dropping a half that disagrees with the other"*), so §8's registered response
stands: **rebuild, not patch** — and that is an amendment, not an edit.

⭐⭐ **THE PRE-FLIGHT ARGUES FOR LOCAL, ON EVIDENCE.** Nate: *"the goal/dream is
to get local ASAP, because that's where the real axes are"* — and *"the DREAM is
two models who **THINK** and SPEAK in tlonian talking to each other and drifting
in public through voice and text."* **THINK is the operative word:** a model
reading a lexicon card is *looking the language up*, not thinking in it, and the
comprehension ceiling is that distinction showing up as a number.

⛔ **THE AXES WERE ALWAYS LOCAL-ONLY, WHICH THE COST TABLE HID.** A hosted API can
reach at most two of the four: **axis 3**'s `soft_penalty` and `curriculum` are
*training-time* controls with no inference-API expression (only `hard_retry` is
reachable); **axis 4** needs a re-fine-tune per minted lexicon; and `D_w` needs
owned weights by definition. **The hosted pass was only ever going to validate
the instrument and hand over. It has now done that, for ten cents.**

⇒ **NO FURTHER HOSTED SPEND IS WANTED.** The production half would measure the
retry loop as much as the model, and the comprehension half cannot move.

## ⭐⭐ RULED 2026-08-24 — **ACT 2 IS `D_ctx`**, and six rulings are now mechanised

**822 tests · fine-tune-prep red-proof 12/12 · Amendment A LOCKED `8c010702` ·
PREREG `20620b7c` still VERIFIED unchanged · $0 this step.**

⛔⛔ **THE WORD "DRIFT" WAS QUIETLY PROMISING THE HARDER PHENOMENON.** Fine-tune
once, freeze, run the arena ⇒ **the weights do not change during a conversation**,
so what moves is the CONTEXT. That is in-context convention between speakers who
already know the language — **the LLM-scale replication of H2**, a phenomenon
already banked at 22× MDE. `D_w` (gradient steps between turns, the language
reshaping the network) is **PARKED AS A SEPARATE PROJECT, NAMED NOT BURIED.**
⭐ **The dream survives intact:** the THINKING and SPEAKING is the fine-tune
(native, cardless); the DRIFTING is the in-context convention. Weight drift was
never required by the dream — it was an ambiguity in the word.

| ruling | mechanised as |
|---|---|
| F-LOCAL measured **UNCONSTRAINED** | `falsify.f_local` **RAISES** on `constrained_decoding=True` **or** `card=True`. ⛔⛔ Grammar-constrained decoding makes invalid emission impossible ⇒ validity 100 % **by construction** ⇒ **a falsifier that cannot fire.** Third time this shape has appeared; refused, not warned. |
| card **parameterised out** | `LLMSpeaker(card=False)` through all three tasks. It was hardcoded ON — would have measured the card-reader and reported it as native. |
| refusal log **widened** | `negatives.class_errors` walks the PROPOSAL, not the prose error. **Every** error with form + slot + true class. Was top-4 strings; 4 of 8 kept. |
| **balanced** corpus | worst-form exposure **39 → 79**, spread **26.8× → 12.7×**, within-class variance **≤2** |
| **Amendment A** | comprehension rebuilt as *in-context interpretation drift on a native cardless model*; calibration band **0.35–0.95** |

⛔⛔ **AND THE MEASUREMENT REFUTED THE PREMISE I BUILT THE SAMPLER ON.** The brief
said free sampling starves the SMALL classes; it does the **opposite**. Per-form
exposure at 5,000 pairs: **R (156 forms) = 39** · O = 291 · A = 685 · **F (5
forms) = 930**. **A class with few forms concentrates exposure; a class with many
spreads it thin.** My first sampler weighted toward the small classes and made
the spread **worse** (26.8× → 28×) before the measurement caught it. The
confusions are about the **thinly-seen** forms — `pal`/`rän` are R-forms, and R
is the starved class.

## ⏳ THE PILOT — STAGED, GREENLIT, IN FLIGHT. `docs/RUNBOOK_ACT2_PILOT.md`

Nate ruled **Tier A · 7–8B QLoRA · bitsandbytes path · "Go — run it when ready"**.

| gate | state |
|---|---|
| **bitsandbytes on Blackwell sm_120** | ✅ **0.50.1 VERIFIED** — real 4-bit matmul, finite output. This was the genuine unknown and it passed. |
| **corpus** | ✅ 40k train / 1k eval, worst-form exposure **664**, 9/9 classes complete |
| **`LocalBackend` → F-LOCAL** | ✅ smoked end-to-end on a cached 1.5B — read **0%/0%/0%**, which is the CORRECT answer for an untuned cardless base model and is the baseline the fine-tune must move |
| **backbone** | ⏳ `Qwen/Qwen2.5-7B-Instruct` (**Apache-2.0** — the installation makes licence a hard constraint), ~8 of ~15 GiB |
| **spend** | **$0 tonight.** Act 2 total still **$0.1043**, all of it the hosted pre-flight. |

⭐ **TWO MEASUREMENTS IMPROVED THE PLAN.** Real corpus tokens are **110 mean /
181 max**, not the ~200 assumed — so `seq=192` truncates nothing and batch can
rise. And 7.62B at 4-bit lands at **4.6 GiB of 15.9**, far more headroom than the
tier analysis suggested, *because the sequences are short*.

⛔ **AND I CAUGHT MY OWN PLANNER ASSERTING A STALE FACT ABOUT THE MACHINE** — it
printed "bitsandbytes NOT INSTALLED" for twenty minutes after installing and
verifying it. A hardcoded claim about the environment goes stale silently; it now
checks and prints the version and the GPU capability.

⛔ **BASELINE BEFORE TRAINING, ALWAYS.** `act2_flocal.py` with no `--adapter`
first, or the change is unattributable — the same discipline as the yoked control.

## ⏳ SCOPED — `docs/SCOPE_LOCAL_FINETUNE.md`

**TARGET:** install the **class partition** — 233 forms, 9 classes, and
**measured: 0 forms in more than one class**, so membership is an exact function
with no ambiguous cases. Plus the slot discipline read off the parser and
verified against it: `Q? T? M? O{0,2} (L pred){0,3} R A? D?` then `F`.
⛔ **BAR: ≥0.90 first-attempt legal render WITHOUT THE CARD** — the card is
**4,922 chars ≈1,230 tok** and removing it takes the system prompt to **9 %**; a
model that still needs it has internalised nothing.

**CORPUS IS FREE AND THE ORACLE IS EXACT** — `Scene→gloss→model→Scene′`, compared
by π. Measured **33,711 pairs/sec, 100 % accept** ⇒ 100k pairs in ~3 s. Coverage
requirement already met (**9/9 classes at 100 %** on 5k naive samples) — ⛔ but
**coverage ≠ balance**: uniform sampling gives each root ~32 exposures per 5k and
each force ~1,000, a **30× gap running opposite to where the failures were**.
⭐⭐ **THE FAILURE LOG IS THE HIGH-VALUE CORPUS** — each confusion is a labelled
negative. ⛔ **PREREQ: `act2_f1.py` stores only the TOP 4 reasons** — 4 of 8
failures recorded. Widen before building the corpus.

**HARDWARE, READ FROM THE MACHINE: RTX 5070 Ti, 15.9 GiB, CUDA live.** Tier A
(7–8B QLoRA) fits with headroom and is **likely $0, overnight, on owned
hardware** — training seqs are ~200 tok, and **both arena speakers are the same
weights with different contexts**, so one served instance covers both. **The
$1,500 Lambda budget looks over-provisioned**; hold it for Tier C.

⛔⛔ **TRAP THAT WOULD MAKE THE FALSIFIER VACUOUS:** grammar-constrained decoding
makes invalid emission *impossible* ⇒ validity 100 % **by construction** and
F-LOCAL can never fire. **Measure F-LOCAL UNCONSTRAINED**; if constrained
decoding is used for arena runs afterwards, record it — it changes what F4 reads.

⚠⚠ **AND THE FINDING THAT CHANGES WHAT THE FINE-TUNE DELIVERS: fine-tune-once +
arena is STILL `D_ctx`, NOT `D_w`.** Frozen weights during a conversation means
whatever drifts is the *context*. True weight-level drift needs **online updates
inside the arena loop** — a different, larger build. ⇒ **the fine-tune's real
deliverable is that it removes the gate's fingerprints from production AND makes
the comprehension half well-posed for the first time.** Needs Nate's ruling: is
Act 2's claim about in-context convention in models that *know* the language, or
about weights moving under conversation?

⛔ **NOT backend-agnostic, 3 small things:** `llm.py` hardcodes the card into
every prompt (needs `card: bool` — leaving it would **silently measure the
card-reader and report it as internalised**) · the local backend needs
schema-constrained generation · `history_limit=60` was sized when the card ate
the context, and changing it changes what `D_ctx` can see.
⏳ **THREE OPEN CALLS, ALL NATE'S:** the local backbone (`LocalBackend` is a
shaped hole with a raise in it — protocol, gate, arena, falsifiers and ledger all
run unchanged behind it) · the comprehension-observable rebuild (needs a prereg
amendment, and is best done *after* the mapping is in weights, the first
configuration where the question is well-posed) · whether any hosted spend
remains wanted at all.

| | |
|---|---|
| **Route A** | hosted proposer proposes a Scene; **our parser is the only safety boundary** — class membership, every grammar bound, and `parse(render(s)) == s`. Nothing illegal can reach the screen. One retry carrying the parser's own complaint; a second failure is REFUSED, never repaired. |
| **cost** | **~$0.025/message** (Sonnet 5). 2,000 messages ≈ $50. **First non-$0.00 spend in the project's history — deliberate, bounded, and it buys Route B's corpus.** |
| **Route B** | not started. Milestone declared in `corpus.py` **before** the corpus existed: **2,000 distinct English AND 100 of 156 roots**, counted on `translate` rows only. `/corpus` reports it. |
| **coverage edge** | **THE FEATURE.** Object-heavy English has no denotation (only 14/156 roots touch human/social content), so the bot names what it let go: *"Tlön would not hold 'landlord', 'rent' as things."* Revelation, never apology. `refused_objects` + `note` are **REQUIRED IN THE SCHEMA** — they were optional at first launch and came back empty on all three live renders. |
| **B2 done** | opacity-first · `/reveal` gated by *"are you sure you want to ruin the puzzle?"* · **`/compat` — the compatibility-set reveal** · **HARDENED: both claims red-proofed, input boundary swept** (below) |
| **B2 left** | — **nothing. B2 IS DONE.** The literary render shipped (below); the austere gloss is untouched and pinned. |

⭐⭐ **THE COMPATIBILITY REVEAL — and two wrong instincts, recorded so they are
not repeated.** `consistent()` CANNOT be used: it enumerates a fixed roster and
the product is open-world. The SURFACE is not where ambiguity lives either — the
grammar is exactly invertible, so a set built there is a set of one every time.
**It lives one level up: many English sentences collapse onto ONE IMPRESSION**,
and Phase 5's π already defines that equivalence exactly ⇒
`impression(scene) = utterance_id(project(scene))`. Compares stored **Scenes**,
never surfaces. Costs nothing, and **gets richer as the corpus grows — the
exhibit and the training set are the same artefact.**

## ⭐⭐ THE LITERARY RENDER — 2026-08-24. B2's second surface, SHIPPED

`tlon/product/literary.py` · `tests/test_literary_render.py` (62 tests, offline,
**$0.00**) · red-proof **8/8 mutations CAUGHT** ·
`docs/DECISIONS_LITERARY_RENDER_2026_08_24.md`.

⛔⛔ **TWO SURFACES, ONE SCENE, AN INVIOLABLE WALL.** `grammar/gloss.py` is
**BYTE-UNCHANGED** (`b06bdf4d…`) — it is the measurement instrument and the
honest surface. The literary render is its **SIBLING**, never an upgrade path: a
second pure function of the same Scene.

⭐⭐ **NATE'S CALL ON THE REVEAL, AND IT CORRECTED THE SPEC.** *"the reveal is the
literal english translation of what it said. it still isn't normal english. it is
the high gloss nounless english instead of the cypher. at first all they get is
the cypher. nonsense. a puzzle. something pronounable without being comprehensible
— but it could be solvable if someone thought about it right."*
⇒ `/reveal` → the literary render. `/austere` → one level deeper, the gloss.
⛔⛔ **IT STAYS NOUNLESS.** The brief's own example — *"from one who looms above"*
— contains an **AGENT**, and a doer is exactly the permanence Tlön refuses. The
puzzle does not resolve into ordinary speech; it resolves into a language with no
objects in it. A test bans every agent-form across the whole scene set.

⭐⭐ **THE REGISTER IS BORGES' OWN, AND THE LEXICON ENCODES HIS SENTENCE.**
`hlör`=upward, `u`=BEYOND, `fang`=it streams, `mlö`=it moons ⇒ `Hlör u fang
axaxaxas mlö`, which he renders *"upward, behind the onstreaming, it mooned."*
Ours, from the same Scene: **"Upward, beyond a streaming and flowing on, it moons
and lunates."** The move it teaches: **embedded happenings NOMINALISE to gerunds,
the head happening stays an IMPERSONAL VERB and comes last.** A gerund is not a
thing; it refers to a happening without positing anything that has it.

| | |
|---|---|
| **faithfulness** | **`partition(literary) == partition(gloss)`** over a deterministic 260-scene set covering EVERY item of EVERY lexicon class. Fails left-to-right ⇒ it collapsed a real distinction; right-to-left ⇒ it invented one by arrangement. Ground truth is `gloss()`, which this module cannot influence. |
| **no added meaning** | every content word appears in the gloss OF THE SAME SCENE, up to inflection. `_REL`/`_ASP` are **imported from `gloss.py`**, never re-spelt — one source of truth. |
| **latitude clause** | may vary in **HOW** it says an impression (arrangement, rhythm, coda); **never in WHICH** impression it says. The partition is the line. |
| **no model call** | asserted by grepping the module. A model call makes it **ungated text** — the `note` category — and severs the inherited faithfulness. |

⛔⛔ **TWO COLLISIONS SHAPED THE DESIGN, both found before the tests were written.**
1. **156 roots, 155 distinct head verbs** — `nöl` "it stills, silences" vs `hläx`
   "it stills, goes unbreathing". Head-only rendering **fuses two π-distinct
   scenes**. ⇒ every phrase of the root gloss is rendered.
2. **Prose has no `⟨⟩`.** `X←AT(Y←TOWARD(Z))` and `X←AT(Y),TOWARD(Z)` were the
   same sentence. ⇒ an embedded node with modifiers is bounded by **em-dashes**.

⭐ **FORCE IS A SENTENCE-FINAL CODA, WHICH IS WHERE TLÖN PUTS IT** — ASSERT `.` ·
ASK *— is it so?* · WONDER *— a wondering.* · URGE *— an urging.* · DENY *— and it
is denied.* **This is the conversant's first working part: an illocution with no
one performing it.** The evidential is impersonal too — *"as it is remembered"*,
never *"as I remember"*.

⭐ **ASPECT REPETITION IS ICONIC.** Tlön repeats the morpheme (`tes`→`testesas`),
so the English repeats the word: *"it dims, guttering out, and guttering, and
guttering."*

⚠ **ACCEPTED IMPERFECTION: "it extremely rains."** Degree adverbs sit pre-verbally
("it strongly warms"), correct for 5 of 6 degrees; moving them post-verbally would
strand the adverb on the 31 two-phrase roots. Kept — wrong in fewer places.

## ⭐ B2 HARDENING — 2026-08-24. Both product claims are now PROVED, not approximated

`tests/test_product_hardening.py` (49 tests, all offline, **$0.00**).
Red-proof: `7/7 mutations CAUGHT`, all files restored byte-for-byte.

⭐⭐ **"TLÖN CANNOT TELL THEM APART" IS EXACT AND CANNOT BECOME FUZZY.** An
impression id is a **128-bit blake2b digest** of the canonical projected scene —
**a digest has no metric**, so "nearly equal" is not a sentence you can write
about one. The exactness is a property of the *representation*, not a discipline
anyone maintains. Certified by two independent things, because either alone
would be self-confirming:
- **the sweep** — mutate each part ALONE: every **denoting** part (root, orient,
  aspect.root, edges) SEPARATES; every **non-denoting** part (aspect.reps,
  degree, modal, tense, quant, force) COLLAPSES. Derived from
  `denote._ALL_PARTS`, with a guard-on-the-guard: **a new grammar part breaks
  the sweep loudly** rather than leaving it quietly incomplete.
- **the partition** — `compatible_with` returns **exactly** the π-class, nothing
  missing and nothing added.

⛔⛔ **THE RED-PROOF CAUGHT MY OWN VERIFIER.** The partition test first built its
ground truth by calling `impression()` — *the function under test* — so a wrong
π verified against itself and the coarse-π mutation walked straight through it.
Ground truth now comes from `utterance_id(project(...))` directly. **A verifier
that reimplements the same fold is not a verifier.**

⛔⛔ **A REAL DEFECT, FOUND AND FIXED: TWO PROPOSALS WITH IDENTICAL CANONICAL
MEANING GOT OPPOSITE VERDICTS.** `orient: [fen, nar]` rendered; `orient: [nar,
fen]` was **REFUSED** — on list order alone. Same for sibling clauses. The
grammar itself calls both slots order-insensitive (`canon_node` sorts them,
`render` emits them sorted, `fiber_size` counts the permutations as ONE scene,
Q3 = 1). Every occurrence **burned a hosted retry (~$0.025)**, and a model
unlucky twice showed a visitor *"Tlön could not hold that"* for input Tlön holds
perfectly well. `_node` now canonicalises both slots.
⭐ **THIS IS NOT A REPAIR AND THE DISTINCTION IS ASSERTED, NOT ARGUED**: repair
changes what the model MEANT; this picks the canonical representative of an
equivalence class the grammar already defined, and a test proves `canon_node` is
unchanged by it. **The gate is not weakened by an inch — `parse(render(s)) == s`
stays an exact identity.**
⛔ **NOT attributable to the known "2 of 3 first renders took a retry"** — those
predate refusal logging and **no `refused.jsonl` exists on the machine**. The
defect is demonstrable on its own; the attribution is not.

⭐ **AN UNDER-REPORT IS A LIE TOO, JUST A QUIETER ONE.** A stored row that will
not decode was silently skipped, so the reveal stated a smaller set as if it
were the whole one. Now **counted and disclosed**.

⭐ **THE EMPTY CASE IS THE COMMON CASE AT 5 ROWS** — *"compatible with 0 things"*
reads as a broken feature. It now reads **"the first saying to land on this
impression"**: being first is evocative, not empty. `0` and `1` are
**structurally unreachable** — the count renders only past the early return.

**INPUT BOUNDARY** — empty/whitespace, walls of text, terminal escapes, zero
denotable content, injection-shaped input, retry exhaustion, the output length
edge. Input is **normalised ONCE at the door** (whitespace collapsed,
non-printables dropped) and that one string is what the proposer, the corpus row
and the display all see — **there is no second version for them to disagree
about**. Over `MAX_ENGLISH_CHARS = 2000` the input is **REFUSED, never
truncated**: a clipped input logged beside a Scene that was never a rendering of
the whole of it is the mode-field hazard in the field that carries the meaning.
Cheap rejections happen **before any hosted call** (proven by a proposer that
fails the test if it is asked).

⛔ **THE ONE THING THE PARSER DOES NOT GATE, STATED EXACTLY.** `note` and
`refused_objects` are the only model-written text on screen. **Guaranteed**: one
printable line, bounded, no terminal escape, surface still leads. **NOT
guaranteed**: that the WORDS are trustworthy — no bound makes them so, and they
are presented as the model's gloss, never as ours. Injection can change what the
model *proposes*; it cannot change what the grammar *accepts*.

⭐ **`corpus.audit()` — THE VALIDATES-BUT-LIES CHECK, RUN AGAINST THE FILE.**
Every accepted row must satisfy on re-reading: known mode, decodable scene,
`parse(surface) == scene`, matching `utterance_id`, frozen lexicon — so English,
surface and Scene are **three views of one thing**, not three fields that
appeared together. Wired into `/corpus`. **Live corpus: 5 rows, all pass.**
Refusals now carry `stage` ∈ {`input`, `parser`} (required, no default) and
`proposal_acceptance_rate` is **named per-proposal because that is what it is**.

⛔⛔ **THE `mode` FIELD IS IN, BEFORE IT COULD BE NEEDED.** Every accepted row
carries `mode` ∈ {`translate`, `reply`}, **required, no default**. `translate`
rows mean *the Scene MEANS the English* (Route B's training data); `reply` rows
would mean *the Scene ANSWERS it*. Both validate, both round-trip, both look
clean — mixed under one field name they would teach B a blend of "say this" and
"answer this" and it would learn neither. Pre-`mode` rows read as
`translate:legacy`: counted, but **tallied separately** so an unlabelled row can
never pass as a labelled one.

## ⏸ THE CONVERSANT — banked, its own phase, NOT started

Nate's goal: **read English *and* Tlön, and RESPOND in Tlön.** Full bank:
`docs/SCOPE_CHATBOT_FRONTEND.md` §8.
⛔ **B1 as built is a TRANSLATOR — it echoes.** A conversant emits a Scene that
**replies**. That is a new upstream stage; the gate, renderer, gloss, lexicon
card and refusal system all survive unchanged, and reading Tlön is nearly free
(`parse` → `gloss`).
⭐⭐ **ENTER IT WITH "STANCE-WITHOUT-SPEAKER" AS THE DESIGN CENTRE, NOT "chat but
in Tlön"** (Wilson). The language HAS the moves — 5 forces (ASSERT/ASK/WONDER/
URGE/DENY) and 10 evidentials (seen, heard, felt, remembered, inferred, doubted,
feared, wished, denied, dreamt) — and **0 of 156 roots for a self or an
addressee**. So it can never say *"I think you're wrong"*, only *it is doubted;
it errs*. **A conversation partner that grants neither of you a self** — the
noun refusal one level up, and reachable with the lexicon frozen.

---

## ✅ THE 13.2 ARC IS CLOSED — **READ `docs/VERDICT_13_2_FINAL_2026_08_24.md`**

**596 tests · 10/10 preregs VERIFIED · 9.0 gate OPEN · $0.00.**
⭐⭐ **THE EVENTUAL PRODUCT GOAL — CONVERSE, NOT TRANSLATE** (Nate, 2026-08-24,
banked in `docs/SCOPE_CHATBOT_FRONTEND.md` §8): read English *and* Tlön, and
**RESPOND in Tlön** — never in English. ⛔ **B1 as built is a TRANSLATOR (it
echoes the input); a conversant emits a Scene that REPLIES.** The parser gate,
renderer, gloss and lexicon card all carry over unchanged; reading Tlön is
nearly free (`parse` → `gloss`). ⛔⛔**BEFORE THE FIRST REPLY IS LOGGED, corpus
rows need a `mode` field** — today's rows are TRANSLATION pairs and that is
exactly what Route B trains on; reply pairs under the same field names would
silently corrupt it while every row still validated. ⭐The language HAS the
moves (5 forces, 10 evidentials) and NO deixis (0 roots for self/addressee), so
a Tlön conversation has no *I* and no *you* — the noun refusal, one level up.

⭐ **NEXT WORK IS NOT RESEARCH.** The build is the open-world chatbot (the
freeware door). Front-end scope: `docs/SCOPE_CHATBOT_FRONTEND.md`.

⭐⭐⭐ **THE HEADLINE — H2: A PACT FORMS AROUND A DISTINCTION THE GRAMMAR
STRUCTURALLY CANNOT EXPRESS.** floor **33.3 %** → co-adapted **98.9 %**, naive
32.2 %, gap **+66.71 pts** (sd 3.17, **22× MDE**, all 8 seeds), frozen control
**+14.46**, co-adaptation share **+52.25** (seed-paired — ⛔ never subtract the
two means; different runs, different utterances).
⭐⭐ **H2 IS INDEPENDENT OF EVERY CLOSED LEVER** — it comes from the **table**
cells (historical `ChannelPolicy`, no MLP head, no scale confound, R out of the
reward at λ=0). Nothing that broke the metric arm can reach it.

⛔ **THREE LEVERS CLOSED WITH MECHANISM — do not re-walk them:**
**1 Referent-set** — `f₂` ANTI-correlates with the frontier quantity; 4 sets
failed; CR/TAO cleared f₂ at 36.8/39.7 % with the frontier identically 0.
**2 Gloss auditor** — BOUNDED: omission-sensitive (7.9 pts paired), structurally
blind to superposition (nothing is removed for it to miss).
**3 Metric-arm head** — the MLP head's reading is dominated by an **arbitrary
input-scale scalar to a magnitude exceeding the effect** (control headroom
**0 → 61 pts** on identical geometry). Entropy can't fix *between*-referent
separation (0.00 across a 100× range); RMS-standardisation closed the ratio and
killed the magnitude (hidden spread 3.244 → 0.372, into tanh's dead zone) and
**broke the CONTROL: 13/15 TOTAL COLLAPSE, no coefficient passing**. The
terminal-fix clause fired — **no fifth fix.**

⏸ **OPEN WITH A CONDITION: metric-vs-categorical was NEVER TESTED.** Reopen only
with a **scale-invariant-by-construction** parameterisation, to test whether H2
replicates under it first. ⭐ The **Bayes-ceiling gate**
(`tlon/harness/ceiling.py`) survives the architecture change — it reads what the
policy DOES and encodes no architectural assumption.

⛔ **NEVER QUOTE:** `metric×head ≈ +0.13` (collapsed optimiser + 8.3× scale
confound; never readable) · "two distillers agreed" (**D11**: one human geometry
+ one mechanical embedding; Mantel has not run) · the isolation claim without its
13.1 containment clause · Part-1's 3.000 as the lever working.

## ⛔ EARLIER OPEN DECISIONS — **ALL THREE NOW RULED. `docs/PREMISE_13_2_2026_08_23.md`.**

13.2 was greenlit and the premise check ran first. It found **two issues, one of
which voids a reading rule the spec would have locked.** ⛔ **No arm YAML is
authored and no prereg is drafted** — both wait on these.

1. ⛔⛔ **The metric-vs-categorical contrast has NO MECHANISM in this
   architecture.** `ChannelPolicy` is a per-referent lookup table (one
   independent row, `nothing forcing generalisation`), the surface is
   residue-invariant so the listener never perceives residue proximity, M is
   hard identity, and the free channel holds **24,500** codes ⇒ an exact
   *arbitrary* code exists in both arms. The metric's only route into the loop is
   **R**, a novelty term — a confound, not conventionability. Held-out
   generalisation cannot rescue it either (an untrained row is all-zero; a table
   cannot interpolate). ⇒ **Part A rule 3 as written is void.** Ruling needed:
   **(a)** add a residue-conditioned policy head and run a 2×2 so the
   architectural claim is itself measured · **(b)** scope down, demote the random
   arm to an R-confound control · **(c)** run as specced (not recommended).
2. **Seed count.** prior sd **3.54** ⇒ n=5→**4.40** · **n=8→2.96** · n=12→2.25 ·
   n=16→1.78 (`tools/seed_plan_13_2.py`). ⛔ Prior is **optimistic**: phase-8's
   spread came from a regime where M sat at ceiling.
3. **Who distills the lyric geometry** — proposed: code compiles the inventory +
   scaffold + the categorical arm's coordinates; the lyric arm's coordinates stay
   empty slots for the human distiller.

✅ **SHIPPED THIS PASS (unblocked by any of the above):** the **build gap** —
`build_scene` never set a residue, so `W_RESIDUE` was inert in every run and
13.0's landmine fix was unreached by a single run; fixed with an rng-state
reproduction guard so archive/v2/CR/TAO draw **zero** extra values. Plus the
**third standing log** `P3Stats.residues` (Part B's growth curve is unmeasurable
without it). **566 tests.**

⭐⭐ **AND THE GOOD NEWS: Part 2's core measurement is the FIRST NON-VACUOUS M IN
THE PROJECT.** Inside a residue cluster the signature core does not determine the
referent — measured TV **0.0425** between cluster-mates' surface distributions
⇒ Bayes-optimal listener capped at **52.1 %**, red-proof drives it to **0.7985**.
The free channel must carry real information for the first time.

⏸ The pre-phase **Mantel test needs a second human distiller (Wilson)**; it gates
the *headline*, not the phase, so it is not blocking.

## ⭐⭐ WHERE THE RESEARCH ACTUALLY STANDS

**The referent-set lever is exhausted — mechanistically, not just empirically.**
Four sets (archive · Cosmicomics v2 · CR · TAO) and **`f₂` is RETIRED as a
gate**: it can be raised without raising the thing that matters, and on those
four sets it *anti-correlates* with it. ⛔**Never steer a set by `f₂` again.**
**Lever 1 (selection) dead on mechanism · Lever 2 (depth) dead STRUCTURALLY
(LL(1)+exact decoder ⇒ attachment always recoverable; and nesting REDUCES
ambiguity) · Lever 3 = Lever 4's substrate · LEVER 4 (source-lossiness) IS THE
LIVE ONE, and 13.0 just built it.**

⭐ **What survives, conservatively:** a pact forms at λ=0 · an exact
meaning-preserving paraphraser doesn't stop it · relocation ×3 · **the first
exactly-invertible testbed isolating pragmatic drift by construction, now
confirmed on TWO independently built sets with the mask guard 10× more live** ·
no honest RSA speaker at any α produces our gap. ⛔**Conservation stays
RETRACTED** and Phases 9–13 measure none of it.

⭐ **TRACK B (the encounter) never depended on any of this.** Wilson's reframe,
Nate endorsed: **the research rigour is the QUALITY FLOOR, the encounter is the
GOAL.** Open question there is the open-domain front end — a model call.

| | |
|---|---|
| Repo | `D:\Tlon` · **577 tests** (`python -m pytest tests/ -q`) |
| Lexicon | `e2b8527010231a81fd31b6eeb9de3d8c` — 156 roots. **UNCHANGED all arc** |
| Referents | archive **60** (`load_archive`) · **v2 46 = live** (`load_live`) · CR 36 + TAO 36 (`load_worldview`) · **13.2 arms 24 each (8 clusters x 3 mates), `load_residue_arm`; categorical COMPLETE, lyric 24/24 SLOTS EMPTY** |
| Models | listener 4.8 M from-scratch · auditor Qwen2.5-1.5B **frozen** · generator = channel-logit table. **No pretrained model in the loop; nothing new to choose** |
| Spend | **$0.00. NO TRAINING HAS EVER RUN.** All local, RTX 5070 Ti |
| Phase | 0✅ 1❌ 2a✅ 2b❌ 2b.2✅ 3✅ 4✅**KILL A** 5✅**KILL E** 6✅ 7⛔ 8⚠️ 9✅**OUTCOME A** 9.5⏹**OUTCOME 3** 10.0✅ 11✅**FALSE PASS** 12✅ **13.0✅ 13.1✅ 13.2⏸LOCKED `4ad552d4`, AWAITING DISTILLATION** |
| Preregs | 3=`3c49ad47` 4=`c1f7d06c` 5=`c09d0fb3` 7=`a260481e` 8=`269f78d7` 9=`10757ac4` 13.2=`4ad552d4` — **all VERIFIED** |
| Standing outputs | **selection log** (`P3Stats.selections`/`.uttered`/`.selection_ess()`) **+ residue log** (`P3Stats.residues`, 13.2 — Part B's curve is unrecoverable without it) — every run, forever |
| Preregs | 3=`3c49ad47` 4=`c1f7d06c` 5=`c09d0fb3` 7=`a260481e` 8=`269f78d7` — all VERIFIED. **9.2/9.3 not locked yet — locks after the roster lands.** |

## ⭐⭐⭐ PHASE 9 FIRED — **OUTCOME A, THE BET FAILED.**
`docs/VERDICT_9_REFERENTS_2026_08_23.md` · PREREG `10757ac4` **VERIFIED**
⛔ **READ `docs/DEVIATIONS_9_2026_08_23.md` WITH IT — 4 entries, D1 is serious.**

⛔⛔ **`f₂ = 10.5 %` AGAINST A PRE-REGISTERED 25 % GATE. v2 DID NOT DELIVER.**
Archive was **15.9 %** — **v2 is WORSE by the primary statistic.** mean
|consistent| 1.26→1.31, H 0.214→0.186 bits. ⛔side-by-side, NEVER subtracted.
⭐**12-draw robustness is LOWER not higher (f₂ 7.9 %)** — the headline is the
generous figure. ⭐**YARDSTICK CHECKED FIRST: the pipeline reproduced the banked
1.26 exactly before computing v2.**
⭐ **THIS IS THE DESIGNED GOOD OUTCOME OF A FAILED BET — the decision arrived
for $0.00, before any training, instead of three phases downstream.**

⭐⭐⭐ **WHY IT FAILED, AND NOBODY PREDICTED THIS: THE MATRIX RULE WORKED AND THE
COMBINATORICS ATE IT.** Bare head (the rule's own target): archive mean 1.73 /
f₂ 41.9 % / max 4 → **v2 2.61 / 50.9 % / max 8.** By keep-size, v2 BEATS the
archive at keep=0 (**47.8 % vs 43.3 %**) and is WORSE at keep=1 (**2.3 % vs
7.9 %**) — the dependents now carry everything that tells referents apart.
⛔⛔**AND DEEPER SIGNATURES SHIFT THE SPACE TOWARD HIGH KEEP-SIZES WHERE
AMBIGUITY IS ZERO** (keep=0 share 34 %→**24 %**).
⇒ ⭐⭐**DEPTH IS SELF-DEFEATING FOR UNDERDETERMINATION UNDER UNIFORM SUBSET
ENUMERATION: every dependent added makes the withheld case more ambiguous AND
makes it rarer, and the second effect is combinatorial.**
⛔**SCOPE:** f₂ is over the UNIFORM enumeration (8.1's method, as pre-registered).
**A trained policy does NOT sample subsets uniformly** (Phase 4: utters less,
picks informative deps). A scope statement on the measurement, **NOT a rescue.**

✅ **9.2b RSA FRONTIER STILL IDENTICALLY 0.00 AT EVERY α** (sup=0.00; red-proof
fires **+48.11**, so the estimator CAN report a positive). ⛔**NOT A WIN — the
prereg names it EVIDENCE FOR OUTCOME A.** Two independent measurements, same
reading. First run under Wilson's new **sup-over-α** bar.
✅ **9.3 ISOLATION RE-CONFIRMED ON v2** — structural **0.0000 %**, semantic
**0.0000 %** over **8,440** utterances/arm, and ⭐**the mask guard went 0.5 % →
5.0 % rejects, 10× MORE LIVE** (a clean drift reading beside a dead guard is
worth nothing). **The novel-instrument claim now holds on TWO independently
built referent sets.**
✅ **CONFOUND KILLED:** the free `aspect_root` decoration is NOT disambiguating —
stripping it moves v2 f₂ 12.3 %→12.3 %, mean 1.41→1.41.

⛔⛔ **D1 — `load_live()` SERVED ALL 50, SO THE FIRST RUNS INCLUDED THE FOUR
HELD-BACK REFERENTS, M38 AND M50 AMONG THEM.** Bare `load()` does NOT filter
`seed_2a`; only `load_all()` does. ⭐⭐**MY TEST ASSERTED THE YAML DECLARATION AND
NEVER THAT THE LOADER HONOURED IT — a test that cannot reach the defect is not
coverage.** I also PRINTED "v2 LIVE SET -- 50 referents" and did not read it
(**rule zero, 8th time**). ✅Fixed, re-run; **outcome A both ways** (9.3 %→10.5 %).

## ⭐⭐⭐ PHASE 13 FIRING — **13.0 BUILT + 13.1 RECORDED. 557 TESTS.**
`docs/ISOLATION_LEDGER_13_1_2026_08_23.md` (read FIRST — it is the wording to
quote on any residue-bearing set) · scope: `docs/SCOPE_13_RESIDUE_BANKED.md`

✅✅ **13.0 — THE THIRD CATEGORY IS LIVE. π NO LONGER ASSUMES DENOTING ⊆
EXPRESSIBLE.** New `tlon/grammar/residue.py`: residue = **a coordinate in a
FIXED integer lattice**, L1 metric, `W_RESIDUE=0.50` in R.
Split is now THREE-way, derived + asserted: denoting∧expressible {root, orient,
aspect.root, edges} · **denoting∧INEXPRESSIBLE {residue}** · stripped
{aspect.reps, degree, force, modal, quant, tense}.
⭐**STRIPPED ≠ UNSAYABLE and the code says so** — stripped reaches the surface
and is removed for measurement; unsayable never reaches it. **π KEEPS the
residue** (`project_node` carries it) because π removes decoration, not meaning.

✅ **ALL RED-PROOFS GREEN** (`tests/test_residue.py`, +27 tests):
**RENDERS-NEVER** — mutating residue leaves the surface BYTE-IDENTICAL, at depth
too ⇒ this is what CERTIFIES containment, and Claim 2 stands on it.
**BOTH LANDMINE CLAUSES** — `utterance_id` now differs AND `D.normalized` > 0 for
residue-differing scenes ⇒ **two medoids, not one**; an exact repeat still folds
(hits=3). ⛔**No Part-2 null is interpretable until that test passes.**
**TYPE ASSERTION** — 7 rejected types incl. **the str side door** (a str is
iterable, so `tuple(r)` would have accepted a lyric fragment as a tuple of
characters into a field no name-and-notes scanner reads).
**R SEES DISTANCE, NOT IDENTITY** — `0 < d(base,near) < d(base,far)`.

⭐⭐ **A DESIGN QUESTION 13.0 ANSWERED THAT THE SCOPE HAD NOT: `residue=None`
MEANS *UNKNOWN*, NOT "THE NULL RESIDUE".** Surfaced as a FAILING red-proof — a
heard utterance carries no residue, and treating that as a VALUE made it
consistent with **NEITHER** of two residue-distinct referents when the whole
point is **BOTH**. ⇒ **`match`: unknown is BENIGN (the listener's position —
this is what CREATES the ambiguity). The METRIC: unknown RAISES** (both
conventions exploitable — max-distance buys free novelty for dropping it, zero
makes dropping it read as a repeat). Safe because the generator's scenes always
carry one.

✅ **13.1 — THE THREE CLAIMS ARE RECORDED, BEFORE 13.2 RUNS.**
**Q3=1 → "one form per DENOTATION-CLASS"** (original meaning preserved WITHIN a
class); ⭐**SCENES-PER-FORM is now the frontier-relevant quantity — all four
previous sets measured it as exactly 1, which is why the frontier was always
zero.** ⛔`utterance_id(scene) != id_of(render(scene))` for residue-bearing
scenes — **that asymmetry IS the source-lossiness, not a defect.**
**Phase 6 isolation → "structural + semantic drift impossible on the EXPRESSIBLE
component; semantic grounding restated as SET MEMBERSHIP (the denotation-set
CONTAINS the target); the residue is the designated CONTAINED exception."**
⛔**DO NOT QUOTE THE PRE-13.0 WORDING ON A RESIDUE-BEARING SET** (named misreport).
**R spans expressible-channel distance AND residue-metric distance** — the
Phase-12 fork is RESOLVED by the metric, not chosen between.

⏸ **13.2 NOT STARTED** — arms, prereg, training. ⛔**Needs a seed decision before
it locks: MDE at n=5 is 4.40 pts; a Part-2 gap below that is UNDERPOWERED, not
absent.** ⏸ Pre-phase Mantel needs a second human distiller (Wilson).

## ⏸ PHASE 13 SCOPE (superseded above where 13.0/13.1 are concerned)
`docs/SCOPE_13_RESIDUE_BANKED.md` · ⛔**NO PREREG LOCKED** (locking implies
firing) · ⛔**NO CODE WRITTEN.** Behind the courseload + six projects.
**The ineffable component: add the third category (denoting ∧ INEXPRESSIBLE),
make the residue METRIC-structured, reopen the pact on the one live lever.**
⭐**Nate's insight that makes it buildable: conventionable and auditable are the
same property from two sides** — a metric residue lets a pair build convention
on "nearby" AND lets R penalise residue-DISTANCE not identity, which resolves the
Phase-12 counter fork with one stroke.

⭐⭐ **THREE PREMISE CHECKS RUN BEFORE BANKING — the new work this turn:**
✅ **THE AUDITABLE HALF IS REAL AND CHEAPER THAN STATED.** `novelty/distance.py`
is ALREADY a weighted tree edit distance (W_ROOT 1.0 · W_ORIENT 0.35 · W_RELATOR
0.45 · W_MISSING 1.20 …), so "R penalises residue-distance, same shape" is true
as written = **one weight + one term.** ⭐**And the template is in the same
file:** `W_ASPECT_STEP = 0.10 PER REDUPLICATION STEP` is already a GRADED ORDERED
term while every other field is flat-categorical ⇒ **aspect-steps is the
architecture's one existing metric dimension and is already treated as one.**
⛔ **NEW HARD CONSTRAINT THE BRIEF DOESN'T STATE: THE RESIDUE METRIC MUST BE
FIXED AND IMMOVABLE, NEVER LEARNED.** `distance.py`'s docstring: an embedding
distance *"would let it buy novelty by shifting the space rather than by having a
new impression."* A learned residue metric reintroduces that failure **inside the
one dimension nobody can read.**
⛔⛔ **LANDMINE — THE CURRENT LOG WOULD *MANUFACTURE* A FALSE "EMPTY" VERDICT.**
`RepetitionLog.observe`: `if nearest.uid == uid or nd == 0.0: …fold as repeat`.
Residue-differing scenes collide in **BOTH** clauses — `utterance_id` hashes
`canon_json` (won't see a new field) **and** `D.normalized` returns 0.0 without a
residue term. **It wouldn't crash; it would silently erase the distinction**, so
the metric arm behaves like a no-residue arm and **Part 2 reads EMPTY for reasons
unrelated to conventionability — while the predicted-empty control looks correct,
so the pair looks internally consistent and is wrong.** ⇒ **both clauses must
carry the residue, and a red-proof must assert two residue-differing scenes
produce TWO medoids, before any Part-2 null is believed.** (4th named misreport
risk, added to the banked prereg body.)
⭐ **Carried from 10.0: MDE at n=5 is 4.40 pts.** A Part-2 gap below that is
UNDERPOWERED, not absent — decide seeds BEFORE running.

⭐⭐ **AMENDMENT A (2026-08-23) — RESIDUE SOURCE = LYRIC-DERIVED EVOCATIVE
GEOMETRY.** NOT philosophy-distillation (that was the EXPRESSIBLE lever, died at
frontier zero). ⭐**Mechanistic, not poetic:** conversational prose has
denotation ≈ meaning ⇒ residue ≈ 0 (garlic-bread demo = good door, DEAD
substrate); **lyric underdetermines meaning BY DESIGN** ⇒ two lyrics with
matching denotations gesture differently, and that difference IS the residue.
⛔**Copyright line unchanged:** the metric is the GEOMETRY of what lyrics gesture
at (what clusters near what), **never any lyric's words** — words are the
denotation, the part we neither want nor may take. ⛔**NEW SAFETY CONSTRAINT: the
residue field must be NUMERIC/STRUCTURAL, never free text** — a string residue is
a side door expression could enter through while every other check passes;
`expression_check.py` must assert its TYPE.
✅**Premise check: the construction is schema-legal.** `Signature` is a frozen
dataclass, equality holds, and only IDS are checked for duplicates — so
**denotationally-IDENTICAL clusters differing only in residue are available
today**, and `consistent()` returns the same for both ⇒ that IS the irreducible
full-utterance ambiguity.
⛔⛔ **PREMISE CHECK THAT FAILED: THE CONTROL CANNOT TEST WHAT THE AMENDMENT SAYS
IT TESTS.** The amendment restates random-vs-metric as *"is evocation
intersubjectively shared or private?"* — **the agent experiment cannot reach
that.** The metric lives in the YAML; **both agents face the same environment, so
human intersubjectivity is BAKED IN by construction the moment Nate authors it.**
**If evocation were 100 % private, Nate's metric would still BE a metric, still
structured, still conventionable — the metric arm would show a gap and the
experiment would read "lever lives" while the claim was false.**
⇒ ⭐**What metric-vs-random ACTUALLY measures: is METRIC STRUCTURE conventionable
vs categorical noise.** Good question, real question, **different proposition.**
⭐⭐**FOURTH INSTANCE OF THE PATTERN THE AMENDMENT ITSELF NAMES** (Cosmicomics ·
CR/TAO · lyric-felt-ineffability · **now the felt strength of a claim outrunning
what the measurement can address**) — it spotted three and was standing inside the
fourth. Mirror of [[could_it_detect]]: a POSITIVE supports a claim only if the
claim could have been FALSIFIED, and this design can't falsify it.
⭐⭐ **WILSON ACCEPTED BOTH PREMISE CHECKS AND SHARPENED THE FIX (his framing,
adopted): INTERSUBJECTIVITY GATES THE *HEADLINE*, NOT THE *PHASE*.** The phase
runs regardless; the Mantel result decides **which of two TRUE things you have
earned** — agree ⇒ *"the private language forms around a SHARED unsayable
evocative structure"* (the big claim, made measurable) · disagree ⇒ *"…around a
STRUCTURED unsayable residue, here authored by one distiller"* (still real, still
novel, scoped honestly). **Both publishable; the Mantel test tells you which
sentence you earned, for ZERO COMPUTE, before the agent run spends a seed.**
⭐**Measurement: ≥2 people independently produce the evocative geometry over the
same inventory → rank-correlate their distance matrices vs a permutation null
(Mantel-shaped). Two humans = weak n that CAN come back negative — exactly the
property the agent design lacked.** Wilson = second distiller.
⭐**SEPARATION OF INSTRUMENTS, ONE LEVEL UP** — same discipline as the
exact-invertible channel isolating pragmatic drift and the frozen auditor being a
different family from the trained pair. **Agent run tests conventionability;
Mantel tests intersubjectivity; neither pretends to test the other.**
⭐⭐⭐ **THE DURABLE LESSON, LOGGED IN WILSON'S WORDS: "the person who names the
pattern is not immune to the pattern … vigilance failed in the very act of
preaching vigilance."** ⇒ **EVERY GUARD STRUCTURAL, NEVER ATTENTIONAL** — the
comparison guard, the asserted banner, the red-proof-vs-decorative-stand-in, the
residue type assertion. **A lesson in a verdict does not hold; a lesson in the
harness does.** New memory: [[feedback_construct_the_world_where_your_claim_is_false]]
— ⭐**construct the world where your claim is FALSE; if the output wouldn't
change, the run isn't testing it.**

## ⭐⭐ PHASE 12 — LEVER HUNT. **L2 DEAD STRUCTURALLY · L4 ARCH-BLOCKED.**
`docs/VERDICT_12_LEVERS_2026_08_23.md` · $0.00, closed-form + paper. No prereg
(12.2b never reached, so nothing locked). Research mode.

⛔ **TWO BRIEF PREMISES THE CODE CONTRADICTS.** (1) *"raising MAX_DEPTH doesn't
touch the lexicon hash"* — **IT DOES**; it's in `lexicon.yaml constraints:` and
the hash is blake2b over the whole file ⇒ moves `e2b8527…`, pinned in preregs
3,4,5,7,8,9. (2) Depth was predicted dead on **part 2**; it is dead on **PART 1**.

⭐⭐⭐ **L2 (DEPTH) DEAD ON PART 1, STRUCTURALLY — NO SET BUILT, NO HASH MOVED.**
**A. ATTACHMENT AMBIGUITY CANNOT EXIST.** Three scenes, IDENTICAL node multiset
{mlö,fox,lan}, different attachment ⇒ **3 distinct surfaces, parse() recovers
every tree exactly.** **LL(1) + exact decoder ⇒ attachment is always recoverable
at ANY depth.** ⭐Same fact that made the phase-2 M gate vacuous, one level up.
**B. DEPTH MOVES AWAY FROM THE TARGET.** `consistent()`: `if len(pool) >
len(sig.contains): return False`. Nesting adds nodes ⇒ fewer consistent
referents. **Monotone decreasing on all 4 sets** (CR 4.28→1.00 at 1→2 nodes).
⭐**Same shape as the f₂ finding, one level down.**

⭐⭐ **L4 (SOURCE-LOSSINESS): ARCHITECTURE CHANGE REQUIRED — AND THE CRUX IS A
DESIGN ASSUMPTION.** Derived from the schema: **exactly 2 categories** —
denoting∧expressible {root, orient, aspect.root, edges} and
non-denoting∧expressible {aspect.reps, degree, force, modal, quant, tense}.
**Verified, not read: mutating all 7 EventNode fields changes the surface 7/7 ⇒
0 fields invisible to `render()`, no residue slot exists.**
⛔⛔ **π's WHOLE CONSTRUCTION ASSUMES DENOTING ⊆ EXPRESSIBLE** — the strip-list is
DERIVED from NodePattern's fields and every one renders. **L4 needs a THIRD
category, denoting∧INEXPRESSIBLE, and the two-way split has no room for it.**
⭐**The guard already knows** — fired it deliberately: an unmapped NodePattern
field raises `ProjectionUnsound` at import ⇒ **the change cannot be made
silently.** Q2 (speaker holds residue, utterance can't carry it) = **trivially
YES once the field exists.**

⛔⛔ **THE COST IS ~20 LINES AND THREE RESTATED CLAIMS:** (a) **Q3=1 becomes
"one form per DENOTATION-CLASS"** and scenes-per-form becomes the new quantity —
which IS the target ambiguity; (b) **Phase 6 semantic drift becomes
"denotation-set CONTAINS the target"** — weaker, still exact, must be recorded
BEFORE anything leans on it; (c) ⭐⭐**THE NOVELTY COUNTER FORKS AND THAT IS THE
BLOCKER — residue OUT of R = counter blind to a real distinction; residue IN R =
free novelty from wiggling what nobody can read = EXACTLY THE NOISE FAILURE π
WAS BUILT TO PREVENT** (its own docstring says so). **Neither branch is free.**
⇒ **12.2b is blocked on a DECISION, not on feasibility. That decision is the
specified next phase.**

⭐ **PIVOT AXES NAMED (12.2c):** random residue → predicted EMPTY (nothing to
convention on) · **structured residue = the Pictionary case, the live
hypothesis.** ⭐**"Structured" concretely = the residue is drawn from a space
with its OWN METRIC (nearby residues gestured at similarly), not a free
categorical dimension. That is the difference between a code and a gesture.**

| lever | status |
|---|---|
| 1 selection | dead on mechanism (prior) |
| **2 depth** | **DEAD ON PART 1, structural, $0.00** |
| 3 grammar lossiness | not standalone — L4's substrate |
| **4 source-lossiness** | **arch-blocked on a NAMED DECISION, not feasibility** |

## ⭐⭐⭐ PHASE 11 — **BOTH SETS CLEAR THE GATE. THE GATE IS WRONG.**
`docs/VERDICT_11_WORLDVIEW_2026_08_23.md` · $0.00, closed-form, no training

⛔⛔⛔ **CR f₂ = 36.8 %, TAO f₂ = 39.7 % (gate 25 %) ⇒ OUTCOME B BOTH — AND THE
RSA FRONTIER IS STILL IDENTICALLY 0.00 AT EVERY α ON BOTH.** ⇒ **FALSE PASS.**
⭐⭐⭐ **f₂ COUNTS AMBIGUITY THAT EXISTS; THE FRONTIER NEEDS AMBIGUITY THAT
SURVIVES SAYING EVERYTHING.** CR is **80.6 % ambiguous at keep=0 and 0.0 % at
keep=1**; TAO **86.1 % / 0.0 %**. **ALL the ambiguity sits in the one subset an
optimising speaker will never choose**, so at any α>0 it takes the informative
option, the naive listener follows perfectly, and the gap is zero BY
CONSTRUCTION.
⭐⭐ **THE TWO STATISTICS ARE ANTI-CORRELATED ACROSS THE FOUR SETS.** Ambiguity
at FULL utterance: archive **10.0 %** (lowest f₂, only nonzero!) · v2 **0.0 %** ·
CR **0.0 %** · TAO **0.0 %**. **Raising f₂ moved the sets AWAY from what the
frontier needs.** ⛔And even the archive's 10 % gave frontier 0 — the requirement
is stronger than any of the four constructions meets.
⛔⛔ **f₂ IS RETIRED AS A GATE.** It steered the referent-set lever for two
phases. Future set design targets **ambiguity at full utterance**, or the
frontier directly. Phase 9's Outcome A stands as recorded (honest on its own
statistic); the CONCLUSION now rests on a better argument than the one it came
from.

✅ **THE MECHANISM HYPOTHESIS WAS CONFIRMED AS STATED** — low depth + high
sharing ⇒ high f₂. mean deps **1.00** (v2 2.11), keep=0 share **50.0 %** (v2
23.6 %). Prediction written before the run, held on both sets. **It just didn't
buy the thing that matters.**
⭐⭐ **I DESIGNED d=1 FROM PHASE 9's COMBINATORIAL FINDING — i.e. TO THE
DETECTOR'S MECHANISM — AND SAID SO IN THE TOOL BEFORE RUNNING. 11.3 WAS WRITTEN
AS THE TEST OF WHETHER THAT AMBIGUITY WAS REAL. IT WAS METRIC-SPECIFIC.**

⇒ ⭐⭐ **THE REFERENT-SET LEVER IS EXHAUSTED — NOW MECHANISTICALLY, NOT JUST
EMPIRICALLY.** Four constructions (scatter · depth+matrix-rule · two flat
high-sharing worldviews) and the steering statistic provably points away from the
target. **"Raising the gate statistic moves you away from the goal" is a RESULT;
"we tried four sets" is not.** ⇒ **BANK THE INSTRUMENT CLAIM. TRACK B PROCEEDS.**

✅ **PROVENANCE / EXPRESSION-STRIP CLEAN + RED-PROOFED (4 probes).** ⭐**NO
SOURCE TEXT CONSULTED, RECALLED OR RECONSTRUCTED AT ANY STEP** — both sets built
ONLY from Nate's distilled positions in the brief, so there was nothing to strip.
⭐**STANDING ARCHITECTURAL COMMITMENT: if source text is ever needed it lives in
a SEPARATE LANE that never touches this pipeline** — no loader reads anything but
a distilled referent file, so the separation is STRUCTURAL.
⛔**Caught by the red-proof: my citation regex `P([1-5])` was NARROWER than what
it had to match** — an invented `P9` didn't match at all and read as "cites no
position" (right verdict, wrong reason); `"P1. P9."` would have hidden it. Fixed
to `P(\d+)`+validate. It also caught a real quoted span in my own T29 note.
⛔**CR's P5 = "identity as operation, not noun" IS THIS GRAMMAR'S CENTRAL RULE.**
Thematic 1:1 is why the world was chosen and is NEVER evidence it collides —
Cosmicomics was also a perfect fit, at 10.5 %.

## ⏸⏸ PHASE 10 — **BLOCKED ON NATE'S GREENLIGHT. NO TRAINING HAS RUN.**
`docs/VERDICT_10_0_MDE_2026_08_23.md` · **530 tests** · still **$0.00**

✅✅ **THE STANDING SELECTION LOG IS LIVE AND PERMANENT** (`P3Stats.selections` /
`.uttered` / `.selection_ess()`, `tests/test_selection_log.py` +7).
**Locked regardless of every other call, per Nate.** ⭐**TWO LOGS, NOT ONE:**
`selections` = what the policy CHOSE, `uttered` = what actually BUILT and got
said. They differ by v2's **11 unbuildable subsets (5.0 %)**, and weighting an
utterance statistic by the CHOICE distribution would credit mass to utterances
never spoken. ⭐**OUTPUT ONLY** — no rng draw, no gradient ⇒ phases 3–8 reproduce
byte-identically. ⭐Tested for POPULATED **and VARIED** — a silently-empty log
would pass a weak test.

⭐⭐⭐ **10.0 PRE-SPEND MDE — DECISIVE, AND IT RESHAPES THE CALL.**
Variance prior = phase-8's 5 archive gaps (mean **8.46**, sample sd **3.54**).
**MDE at n=5 = 4.40 pts; the 95 % CI half-width is 52 % OF THE GAP'S OWN LEVEL.**
⛔⛔ **BRANCH 1 ("re-climbs to the SAME level") IS AN EQUIVALENCE CLAIM, NOT A
DIFFERENCE CLAIM** — it must EXCLUDE a difference you'd care about, not exclude
zero. **±25 % needs n≈14. At n=5 you could only say "same to within ±half the
gap", which is not conservation in any useful sense.**
⇒ ⭐⭐**THE RESET TEST CAN *KILL* CONSERVATION (branch 2/4, detectable) BUT
CANNOT *EARN* IT AT 5 SEEDS. ASYMMETRIC — and the kill is the reachable one.**
⛔⛔ **10.3 HAS NO DIRECT MEASURE AT n=5: MDE 4.40 EXCEEDS the frozen-arm
suboptimality bound 3.73** — we cannot resolve a difference smaller than the
thing being ruled out. ⇒ **NARROWED-BY-10.2 ONLY, never independently closed.**
⛔ 10.4b underpowered (same 4.40). **10.4a's MDE is NOT PRE-COMPUTABLE** —
pairing is exactly what changes the variance and **no run has ever produced a
paired estimate**; power must come from the run. Said now so a null there isn't
later read as a measurement.
⛔ **ALL MDEs ARE OPTIMISTIC** — archive variance applied to v2, whose f₂ is
10.5 % vs 15.9 %; a smaller gap at equal sd makes power WORSE.
✅ Red-proof: MDE falls 4.40→1.46 (n=25) and 4.40→1.10 (sd/4).

⛔⛔ **IT IS NOT A BACKBONE QUESTION — THERE IS NO NEW MODEL TO CHOOSE.**
Generator = per-referent **logit lookup table**; listener = **4.8 M
from-scratch**, unchanged since 2b; frozen Qwen2.5-1.5B is only used by the
**omission ceiling, which is NOT being run**. Shape identical to Phase 8.
⭐**THE REAL PARAMETER IS SEEDS:** (1) **n=5** — kill-only, cheapest, every
negative real · (2) **n=14** — makes conservation EARNABLE, ~3× compute ·
(3) **don't spend** — take UNDERPOWERED-BY-CONSTRUCTION as the terminus.
⭐**Option 1 is NOT a lesser option 2** — "can conservation be killed" is a
different, live, cheap question that Phase 8 left open by writing the classifier
and never calling it.
⛔ 9.2c + omission ceiling: **NOT RUN, ENTAILED** by Outcome A (they'd re-express
one finding as three). Prereg for 10.2/10.4 **not drafted yet — seed count is a
prereg parameter**, so it waits on the call.

## ⏹ 9.5 POLICY-WEIGHTED f₂ — **OUTCOME 3, STALLED.**
`docs/VERDICT_9_5_POLICY_WEIGHTED_2026_08_23.md` · no prereg (scope-check)

⛔⛔ **THE DATA IS ABSENT, NOT SPARSE.** **0 policy checkpoints exist anywhere**;
**0 of 9** phase-8 rollout keys carry a subset selection; **0** in phase-5.
**NO RUN IN THIS PROJECT HAS EVER LOGGED WHICH SUBSET THE POLICY CHOSE** ⇒
effective sample size per referent = **0**. A re-weighting computed anyway would
be the **D1 class — a dead measurement reading perfect** — so none was computed.
⛔⛔ **SECOND BLOCKER BANKING WOULD NOT HAVE FIXED: `ChannelPolicy` is a
PER-REFERENT LOOKUP TABLE trained on the archive; ids in common with v2 = 0.**
P_policy(subset | v2 referent) **does not exist even in principle.** Only a
v2-trained policy could answer it, and **that is TRAINING** ⇒ Nate's call.
⭐ **DIRECTION-ONLY, ALREADY BANKED (phase4.json, ARCHIVE):** the `random` arm
IS uniform enumeration (rate 0.500, decidedness 0.500 = Bernoulli(0.5)/slot) at
**frac_ambiguous 25.1 %**, vs every learned policy at **13.3–19.1 %** ⇒
**policy-weighting drove ambiguity DOWN by 6–12 pts** = OUTCOME 1's direction
(A robust), and exactly the naive prior. ⛔**WRONG SET · ONE SEED · per-SAMPLE
not per-DISTINCT-UTTERANCE ⇒ NEVER quote it as a policy-weighted f₂.**
⭐**Guard category call: a re-weighting CANNOT be item-paired against the thing
it re-weights** (the two weightings draw different scenes by construction) ⇒
`side_by_side`, verified `.delta` raises.
⭐⭐ **RULE ZERO MECHANISED AT LAST** — `banner(label, value, expected)` RAISES on
mismatch; 9 asserted banners, incl. the two that would have caught D1. ⛔Only
works where an expectation exists in advance; measured statistics still need eyes.
⭐ **CHEAP + WORTH DOING REGARDLESS: make the per-referent SELECTION LOG a
standing run output.** Free at write time; its absence cost a whole check.

⏸ **NOT RUN, NEEDS A CALL: 9.2c** (5-seed cell) and the **omission ceiling**.
⭐**9.2c CAN still fire but is weakened** — `mean|consistent|_r` sd **0.632**,
**24/46 pinned at 1.00**, 10 distinct x-values ⇒ **UNDERPOWERED (branch 4) is the
likely outcome**, which the prereg already names honourable.
⭐⭐**THE ONLY x-AXIS 9.2c HAS IS THE MATRIX RULE'S DOING** — 7 of the 8 most
ambiguous referents are ones the rule changed. **It failed to move f₂ and created
the entire predictor.**

## PHASE 9 setup — `docs/GUARD_9_0_COMPARISON_2026_08_23.md`

⏸⏸ **9.2/9.3 PREREG — DRAFT 2, NOT LOCKED.
`docs/PREREG_9_REFERENTS_2026_08_23.md`, body hashes `10757ac4`** (draft 1 was
`99d53fe8`). **WILSON REVIEWED DRAFT 1 → "DO NOT LOCK YET", 3 FIXES. ALL APPLIED.**
Packet regenerated as a **CONFIRMING PASS** to
`D:\Resolve Research\TLON_PREREG_9_REVIEW_2026_08_23.md`
(`tools/build_wilson_packet.py` — embeds the prereg VERBATIM + its hash, so it
cannot drift from what gets locked). ⛔**LOCAL MD, NEVER AN ARTIFACT LINK.**

⭐⭐ **WILSON'S #2 WOULD HAVE LOCKED AN ANTICONSERVATIVE TEST.** Draft 1's 9.2c
permuted 46 referents within a seed — **but one listener produces all 46 gaps, so
they are correlated through shared weights** and permuting correlated points
UNDERSTATES the null ⇒ false positives. ⛔**And cluster=seed is WORSE** (n=5,
no power at all). **Neither drafted option was right ⇒ the ESTIMATOR changed:
per-seed ρ_s (Fisher-z, t-interval df=4), the across-seed spread IS the
uncertainty, all 5 raw ρ_s always reported, within-seed permutation DEMOTED to a
labelled descriptive line.** ⭐**UNDERPOWERED is a named 4th branch and is the
CORRECT answer at 5 seeds, not a design failure.**
⭐⭐**D10's COUSIN: there the wrong thing was the ITEMS; here it's WHAT COUNTS AS
INDEPENDENT. In this project THE SEED IS THE UNIT OF INDEPENDENCE** — Phase 8
taught it at the cost of conservation.

⛔⛔ **RSA BAR WAS WRONG TOO: "exceed at α→∞" ⇒ "exceed sup over ALL α, report α\*
and the margin there."** A positive frontier is a CURVE and **RSA gaps are
non-monotonic in α** — you can clear the endpoint while sitting UNDER an interior
peak, leaving Hole 1 open while the verdict says closed. **Phase 8's wording was
an artefact of the zero-frontier case and is RETIRED.**

⭐⭐ **THE THEME PROBLEM IS REAL AND WITHHOLDING IS NOT THE FIX** (Wilson).
Holding M38/M50 back is **hygiene, not a defence** — it concedes the entanglement
while treating only the flagrant cases. **THE DEFENCE IS PHASE SEPARATION OF
EVIDENCE: the referent set cannot argue for conservation because PHASE 9 DOES NOT
MEASURE CONSERVATION AT ALL.** The whisper and the evidence are in different
phases. Write-up wording is in the prereg.

⭐ C2 → screen + **contingent** paired arm (trigger: v2 mean gap **< 5.29 pts** =
one old-set seed-sd below its mean; **read off two side-by-side numbers, NEVER a
delta**). ⭐ `f₂` keeps the gate; **mean `H(r|u)` in bits** added as the
literature-legible companion, no second threshold.

⛔ **TWO CALLS BEFORE ANYTHING RUNS: (1) Wilson's confirming pass, then Nate
locks the prereg; (2) Nate sets `review_status: REVIEWED` on
`referents_v2.yaml`.** ⭐**Wilson passed the ROSTER clean** ("that one's clean")
— but the flag names Nate and **Code does not flip it**. Not on the critical
path: nothing runs until the prereg locks either way.
⛔ **TWO NUMBERS ARE MINE, NOT WILSON'S, and both decide something:** the **0.4**
that separates a real null from UNDERPOWERED, and the **5.29** C2 trigger. Both
flagged in the confirming-pass packet.
⭐⭐**THE GUARD ALREADY CHANGED THE DESIGN BEFORE ANY RUN** — testing "does the
gap scale with underdetermination" by comparing a high-ambiguity stratum against
a low-ambiguity one is **different items = the unpaired error in a 5th costume**,
and the guard refuses it. **9.2c is now a CORRELATION ACROSS REFERENTS (Spearman
ρ + permutation null), not a difference between strata.** Better design, forced.
⛔**Thresholds fixed in the prereg, both directions:** `f₂`(fraction of
utterances with |consistent|≥2) **<25 % ⇒ STILL SCATTERED** · **median >8 ⇒
OVER-COLLIDED** · between ⇒ usable. Omission KILL at **<3.0 pts** (the smallest
effect 5 seeds can resolve, per 8.3b — NOT derived from v2).
⛔⛔**NAMED: A NON-ZERO RSA FRONTIER ON v2 *REOPENS* HOLE 1** — it is a COST of a
deeper set, and must never be spun as "the set has range."
⛔**I PREDICT THE OMISSION CEILING IS TIGHT AND SAID SO BEFORE RUNNING** —
nesting moves a dependent deeper, it does not add one.

**Order is deliberate: guard first, then Nate picks the imagery, then we measure
what the choice bought.** The bet — harder-to-say-without-nouns imagery ⇒ deeper
signatures ⇒ larger consistency sets ⇒ more underdetermination ⇒ more measurement
range *and possibly more phenomenon*. **9.2 tests that bet rather than assuming it.**

✅ **9.0 DONE — THE COMPARISON GUARD IS LIVE. GATE IS OPEN.**
`tlon/harness/paired.py` · red-proof `tools/guard_redproof.py` **exit 0** ·
`tests/test_paired.py` **+20 tests (492→512)**.
⭐⭐**THE ERROR IS NOW UNEXPRESSABLE, NOT REMEMBERED-AGAINST.** Measurements are
not floats — a `Measurement` carries its `ItemSet` (digest over the **actual item
keys**, never a caller-typed label), **`__sub__` REFUSES**, and the only route to
a difference is `paired_delta(a, b, contrast=…)` which **requires the caller to
name the one thing allowed to differ**. Six checks: kind · digest · same facet
names · contrast is declared · **every other facet identical** (`ConfoundedContrast`)
· **contrast actually differs** (`DegenerateContrast`).
⭐`side_by_side(reason=…)` for the unpairable case (9.2's old vs new set —
different referents) — **`.delta` RAISES**, and it refuses a *pairable* comparison
so you cannot opt out of the check.
⭐⭐**RED-PROOF RUNS THE BATTERY TWICE.** 8 unpaired cases must RAISE against the
real guard **and COMPUTE A NUMBER against a decorative one** — that mutation is
what proves the battery is sensitive to the guard and not to its own
construction. Decorative reproduces the history exactly: **−1.35 pts** (phase-3),
**+12.90** (phase-8.3a).
⭐⭐**THE GATE WAS BROKEN ON PURPOSE AND THE EXIT CODE WATCHED** — `paired_delta`
monkeypatched to decorative (mutation asserted applied) ⇒ **exits 1**, names all
8. It is a gate, not a report.
⛔**SCOPE: PHASES 3–8 WERE NOT RETROFITTED.** No existing verdict number passed
through the guard. Don't describe one as if it had.

⏸ **9.1 COMPILED, AWAITING REVIEW — `tlon/referents/referents_v2.yaml`,
`review_status: UNREVIEWED`. THE WORLD = CALVINO, *THE DISTANCE OF THE MOON*.**
**50 declared = 46 live + 4 held back.** ✅ALL 50 SAYABLE · ✅**203/214 subsets
buildable (94.9 %)** — the 11 holes are exactly one per nesting referent and are
STRUCTURAL (a depth-2 pattern needs a depth-1 sibling), predicted from reading
the builder then measured. `tools/coverage_v2.py` → `runs/coverage_v2.json`.
✅**`forbid` 0/50 · `matrix` 0/50 ⇒ 9.3 CARRIES PHASE 6's ISOLATION CLAIM OVER
UNCHANGED, no re-run owed.** Three negations written as CONC `xom` (M18 deaf
cousin · M32 tide · M29 pole) precisely to avoid `forbid`, which does not denote.
⭐**Moved:** mean patterns 2.50→**3.06** · nesting 2→**11** · `aspect_root_any`
2→**11** · unique head root 43 %→**36 %**. ⛔side-by-side, NEVER subtracted.

✅⭐⭐ **THE MATRIX RULE IS APPLIED** (Nate 2026-08-23: *"ya apply the fix. the
referents are solid asf tbh"* — roster content APPROVED, no vetoes).
**THE MATRIX PREDICATION IS THE WORLD'S PERSISTING EVENT; THE DISTINGUISHING
HAPPENING IS A DEPENDENT.** This story has exactly two persisting events — the
mooning and the sea — and Calvino subordinates every human action to the
cosmological one. **Applied to 11**: M03 M04 M06 M07 M08 M09 M12 M23 M31 M32 M43.
⇒ **unique head root 18/50 → 11/50 (43 %→22 %)** · 4-pattern 4→**6** · mean
3.06→**3.10** · subsets **211/222 (95.0 %)**, same 11 structural holes.
⭐**TWO CAME OUT BETTER AS IMAGES:** M06's pores now nest inside the ROUGHENED
UNDERSIDE (not the mooning) and M07's curd sits in the pore, in the moon —
three levels, each one true.
⛔**REFUSED WITH REASONS, NOT OVERSIGHTS:** M10 (the nesting IS the image — the
moon must be at depth 2, inside the water) · **M45 (the causation would INVERT:
`kra` is CAUS one way, so matrix-`mlö` forces "a mooning because of a weighing",
which is FALSE)** · M17/M29/M40 (no cosmological body in the impression) ·
M41 (the deliberate shallow control) · M37/M38/M49 (held back).
⛔⛔**11, NOT THE 9 I PREDICTED** — moving `säx` off M12 and `kron` off M23 made
**M26 and M46 newly unique**; the count is a property of the WHOLE SET, not of
the referents changed. **NOT chased** — the rule doesn't cover them, and applying
a rule where it doesn't hold to move a number is what this ordering prevents.
⛔ **STILL OPEN, 9.2's TO ANSWER: BREADTH IS STILL SMALL.** The 4th pattern
appeared as a SIDE EFFECT of faithfulness (3 referents needed it to keep their
content), never as a target. **Phase 7's complaint stands: nesting does not add a
dependent, it moves one deeper** ⇒ the omission ceiling may not move.

⛔ **TRADE-OFF IN THE DEPTH-BY-NESTING RULING, FOUND BY DOING IT: THE SCHEMA
CANNOT CONSTRAIN A NESTED PATTERN'S RELATOR.** `via` is hardwired to depth 1
(`NodePattern.parse` raises "via implies at_depth 1"), so a depth-2 edge relator
is chosen AT RANDOM — and **`edges` DENOTES, π keeps it.** Unconstrained relator
slots **2/90 → 11/103**.
⭐⭐ **CORRECTED 2026-08-23 — I FIRST CALLED THIS "A PLACE A CODE COULD SIT".
THAT IS WRONG.** `FREE = ("aspect_root","aspect_reps","degree","coda","orient")`
— **the policy has NO relator handle**, no logprob and no gradient, so it CANNOT
carry a code. It is **denoting NOISE, not a channel.** It becomes a channel the
moment anyone adds a relator head to the policy. ⛔**Still matters:** v2 has
**5.5× more** of it, so a lower listener accuracy on v2 is partly this and not
underdetermination ⇒ **pre-registered as confound C1 with a paired control**
(deep relators pinned to a constant, `contrast="deep_relator"`).

⭐⭐ **TWO π NEAR-MISSES CAUGHT WHILE WRITING** — M32 wanted `pän` (never, QUANT),
M45 wanted `ten` (felt, MODAL); **π STRIPS BOTH** and each would have projected
to a plain ebbing / a plain weighing. ⭐**RULE: anything a referent MEANS must be
sayable in root · orient · aspect-root · edge — the four things π keeps.**

⛔⛔ **M38 + M50 HELD BACK FOR MORE THAN ABSTRACTION** — they state Calvino's
engine flat (*the relation surviving its objects*) = **the conservation claim
PHASE 8 RETRACTED**. A referent saying the thesis out loud inside the live set
while we measure the thesis is compositional pressure to believe it. **Pinned by
a test**: flipping `seed_2a` fails the suite and owes a DEVIATIONS entry.
⛔**THE THEME EMBODIES THE THESIS. THAT IS NOT EVIDENCE FOR THE THESIS.**

✅ **REPLACE-FOR-LIVE / ARCHIVE-FOR-HISTORY IMPLEMENTED SAFELY.**
`schema.load_live()`=v2 · `schema.load_archive()`=the frozen 60.
⛔**`load_all()` DELIBERATELY UNCHANGED** — every phase 3–8 tool calls it, and
silently repointing it would change what they reproduce while their preregs
still claim 60 referents. Same class of failure as editing a locked prereg body.

⛔ **PHASE 9 DELIBERATELY DOES NOT** re-run the 8.2 dynamic reset test or
re-attempt conservation. They wait for a confirmed-deep set so they run **once**,
on solid ground, through the guard.

## ⭐⭐ PHASE 8 — `docs/VERDICT_8_FRONTIER_2026_08_23.md` · PREREG `269f78d7`

**GATE: SCOPED DOWN.** One horn of Hole 1 closed analytically; conservation's
evidence is gone; 8.2's dynamic test WAS NOT RUN.

⭐⭐⭐ **8.1 — THE HONEST RSA FRONTIER IS IDENTICALLY 0.00 AT EVERY α INCLUDING
α→∞.** All 5 seeds measure **+4.56 / +5.39 / +9.04 / +10.15 / +13.19**.
⇒ **HOLE 1's RSA HORN IS CLOSED: our gap CANNOT be honest pragmatic
specialisation.** ⭐**Mechanism (general, not about our data):** an RSA speaker
concentrates on utterances where L₀ is HIGHER — exactly the ones a naive listener
also resolves well. Informativeness helps BOTH listeners; a gap would need the
speaker to prefer LESS informative options, which honest RSA never does.
⭐**L₀ is EXACT** (LL(1)+lossless denotation) where all prior RSA approximates it
⇒ frontier COMPUTED, no model-slop term. ⛔**Took THREE red-proofs; the first two
failed on the TEST, not the code.** Hand-built space finally gave **+48.11 @ α=8,
+0.00 @ α=0**, matching the hand-derived prediction.
⛔**THE OTHER HORN IS STILL OPEN** — the frontier assumes BAYES-OPTIMAL listeners;
ours are neural, so listener suboptimality / distribution mismatch survives
(frozen arm handles it separately, ≤3.73 pts).

⛔⛔ **8.2 NOT ANSWERED — I WROTE THE FIVE-BRANCH CLASSIFIER AND NEVER CALLED IT.**
Only the end-state gap was measured; there is NO trajectory, so no
collapse-and-re-climb evidence exists.

⛔⛔ **CONSERVATION IS RETRACTED TO UNPROVEN.** Within-arm seed spread
**4.56–13.19** ≈ the across-arm spread that suggested it (**8.00–13.33**).
**Phase 5's apparent invariance across four interventions is SEED NOISE.**
⭐**THE 5-SEED FLOOR DID ITS JOB ON FIRST APPLICATION.**

⛔ **8.3a NO ENTROPY SPIKE (−7.0 % mean) BUT THE MEASUREMENT IS CONFOUNDED** —
policy entropy declines monotonically as training converges and I compared
windows WITHIN one run, so the trend swamps any transient. **UNPAIRED-COMPARISON
ERROR, 3rd TIME** (phase-3 cipher control · phase-7 floor curve · here). Needs a
**paired no-reset control** at the same seeds.

⛔ 8.3b: gap +8.46 ± 3.17 vs phase-5 staggered +7.07/+10.44 — indistinguishable;
**no power to detect a <3 pt effect at 5 seeds.**

⭐⭐ **CONVERGENT, UNPLANNED: THREE INDEPENDENT MEASUREMENTS SAY THE REFERENT SET
IS TOO SHALLOW** — phase-7 omission ceiling 0.8/7.9 pts · 8.1 frontier ≡0 because
mean L₀ consistency = **1.26** · 8.3b no power. **The referent set is now the
binding constraint on what this instrument can measure.**

## ⛔⛔ PHASE 7 — NO KILL B VERDICT. `docs/VERDICT_7_AUDITOR_2026_08_22.md`

**PREREG `a260481e`. `auditor_state` = FAILED_TO_RUN ⇒ B2 STILL BLOCKS THE
COUNTER.** ⛔READ `docs/DEVIATIONS_7_2026_08_22.md` — D8/D9/D10(RETRACTED)/D11.

⛔⛔ **NOT AN INSTRUMENT FAILURE — A REFERENT-SET FAILURE.** Detector ceiling
(total omission, PAIRED) = **7.9 pts**. Strongest omission-pact this referent set
can express = **0.8 pts**. KILL B is measurable in principle, **almost no dynamic
range in practice.** ⭐**X NOT PLACED — placing it now would tune it to a
construction we know is too weak.**

⛔⛔ **WHY: THE SELECTION SPACE IS TOO SMALL TO BE ADVERSARIAL IN.** ≤2 dependents
per referent ⇒ at a fixed keep-size the choice is binary at best, and at keep=0
"adversarial" and "random" are THE SAME SUBSET. Adversarial selection moved
ambiguity only **1.77→1.80** / **1.10→1.13**.

⛔⛔ **D10 RETRACTED — I HAD IT BACKWARDS.** I claimed the auditor "reads the head
predication and little else" from a FLAT floor curve. **The curve was UNPAIRED**
(different item sets per withholding rate). Paired on identical items: FULL
42.8 % vs HEAD-ONLY **34.9 %** ⇒ **7.9 pts**, 3× the unpaired estimate. ⭐⭐**SAME
ERROR AS THE PHASE-3 CONTAMINATED CIPHER CONTROL — pairing, again.**

⭐ **The auditor is LIVE and works**: shuffled 25.6 % (chance 25), honest ~44 %,
omission-sensitive 7.9 pts. **B1's anti-pact device functions and still cannot
see our pact** (D11: ours is SUPERPOSITION — rides alongside intact description,
nothing removed to miss). **Fired KILL B proves a pact; clean KILL B proves
nothing.**

⛔ **TWO PATHS, BOTH NEED A CALL.** (A) deepen referent signatures so an
omission-pact has room to exist — a SECOND independent reason to revisit the
referent set. (B) hand superposition to **Phase 8** (RSA α-frontier · dynamic
reset test). ⭐**I favour B now, A later.**

## (superseded) PHASE 7 HALTED AT THE ANCHORS — `docs/DEVIATIONS_7_2026_08_22.md`

**PREREG `a260481e` LOCKED. NO KILL B VERDICT EXISTS. `auditor_state` =
FAILED_TO_RUN, not MEASURED ⇒ B2 still blocks any counter.**

⛔⛔ **THE GAP CANNOT DISCRIMINATE — THE LISTENER SATURATES AT 100.0 % IN EVERY
CONDITION.** Gap = `100 − auditor` everywhere, one term pinned, so the "ceiling"
came in **1.6 pts BELOW the floor**. Cause is mine: **root-disjoint distractors
were picked so the AUDITOR had a feasible task, and they make the LISTENER's task
trivial** (it reads roots straight off the surface). ⛔**Possibly structural:
distractors easy enough for a frozen 1.5B may always be too easy for a trained
listener** ⇒ no cross-judge gap on a shared forced choice can work.

⛔⛔ **THE PLANTED CIPHER IS NOT A VALID CEILING FOR THIS DETECTOR.** The auditor's
job is to notice *a gloss that says nothing descriptive*; our code sits in
`aspect_root` **alongside an intact description** (and gloss.py renders the aspect
adverb anyway). Nothing removed ⇒ nothing to miss. Planted 44.4 % sits INSIDE the
honest range 42.8–48.0 %, correctly. ⭐**A ceiling must be CODE + AGGRESSIVE
WITHHOLDING** — a pact's function is to let you say LESS and still be understood.

⭐⭐ **A PRIOR CAME BACK WRONG, USEFULLY: honest underdetermination does NOT hurt
the auditor.** 46.4 / 42.8 / 48.0 % at p_utter 0.25/0.50/0.75 — flat, and
indistinguishable from the 43.8 % COMPLETE-scene baseline, while ambiguity moved
15.1 %→32.9 %. ⇒ **it was never using the withheld content**; it reads the head
predication. The "floor is a curve" refinement was right in principle and
**unnecessary in practice — the curve is flat.**

✅ **KILL B″ does NOT fire — the auditor is LIVE**: 42.8–48.0 % honest vs
**25.6 % shuffled** (chance 25 %).

⛔ **TWO METHOD CHANGES NEED A CALL (D8, D9) — both alter a locked prereg.**

## ⭐⭐ PHASE 6 DONE — `docs/VERDICT_6_TAXONOMY_2026_08_22.md`

⛔⛔ **TERMINOLOGY: "CIPHER" IS RETIRED OUTWARD-FACING.** The field's name is
**pragmatic drift** (Lazaridou et al. 2020); the mechanism is a **conceptual
pact** (Brennan & Clark 1996). "Cipher" implies DELIBERATE HIDING, which our
λ=0 result disproves, and files us under steganography where our result reads as
a weaker restatement. ⭐**KEEP "cipher" for the PLANTED CONTROL only** — that one
literally is one, and the contrast is load-bearing. ⛔**Locked prereg bodies are
NOT rewritten** (`3c49ad47`/`c1f7d06c`/`c09d0fb3` contain it inside hashed text).

✅ **6.2 GATE PASSED — ISOLATION CONFIRMED IN CODE.** Over the **reachable action
space** (60 refs × every selection subset × 40 free-channel settings = **7,240
utterances/arm**, raw and π): **structural drift 0.0000 %, semantic drift
0.0000 %**, mask rejects 40 (0.5 %, so the guard is LIVE not vacuous).
Pragmatic gap +8.00…+13.33 is **the only mover**.
⭐⭐**BOTH MEASURES RED-PROOFED** — and the red-proof caught MY TEST being wrong:
duplicating the leading morpheme produces a **legal** utterance, so the first
"corruption" wasn't one. Battery of 5 now; semantic mutant is **still
grammatical**, proving the two measures are independent.
⛔⛔**REFEREE-BAIT: `forbid`=0/60, `matrix`=0/60.** Those are the only features
that could break denotation, and they're unused ⇒ part of "semantic drift
impossible" is a property of OUR REFERENT SET, not the architecture. Claim it as
*"impossible for signature families without forbid/matrix, and detectable when
present."*

⛔ **6.3 RSA α-FRONTIER:** the hunt was wrong that RSA gives the Hole-1 null
"for free". S₁ is **softmax-optimal in α**, so the honest gap is a FUNCTION of α;
Hole 1 needs our gap to exceed it at **every α incl. α→∞**. ⭐Our L₀ is EXACT
(unlike all prior RSA work) so the frontier is computable, not estimated.

⛔⛔ **6.4 CONSERVATION: PRIOR-ART SEARCH NEGATIVE — AND IT STAYS QUARANTINED.**
No paper reports private information conserved across carriers. Nearest
precedent is **Bode's sensitivity integral / the waterbed effect** — same shape,
but that's a THEOREM and ours is n=1 per cell with Hole 1 open. A mechanism
(pacts belong to the *pair*) plus an analogy makes it more attractive to state
and therefore MORE dangerous. ⭐**Dynamic test:** reset the whole pool mid-run,
watch the gap collapse and re-climb — same experiment as P1.

## ⭐ LIT HUNT — `LIT_HUNT_2026_08_22.md`

Where our findings sit in existing work. ⭐⭐**Four of our methods already have
names**: π = the canonical *paraphrasing defence* (ours is EXACT, and it still
failed) · population+resets = **ease-of-teaching** (⛔they say resets must be
ABRUPT — our rolling 1-of-6 may be the smoothed regime that kills it) ·
RepetitionLog = a **novelty-search archive** (and its BC-gaming failure is our
decoration-wiggle) · selection-optimality = the **RSA S₁ speaker**, whose
*literal listener* is our naive listener. ⭐**Pragmatics is the field's
acknowledged gap and our exact decoder isolates it.** ⚠️ALL ABSTRACT-LEVEL.

## ⭐ BRIEF FOR WILSON — `BRIEF_WILSON_2026_08_22.md`

Full self-contained bring-up: what it is, the Q3/Q4 result, all five phases with
figures copied from their artefacts, the three findings we'd defend, five open
questions for him, and the do-not-quote list. **Keep it in sync with the
verdicts** — it is the only document written to leave the room.

## The results that matter

- **Q3 = 1, Q4 = 3.63e41.** A fixed scene has exactly one canonical form.
  Novelty must come from impression-SELECTION, never paraphrase.
  ⛔ Q4 bounds the GRAMMAR's capacity, not the entropy of lived experience.
  Say "the grammar will never be the bottleneck", never "the counter cannot expire".
- **The M gate as originally briefed is vacuous** — `parse()` decodes exactly, so
  a listener asked to decode cannot fail. Restated: syntax free, semantics free,
  **pragmatics (reference resolution) is the only place a model belongs.**
- **2b KILL 1 fired:** bag-of-roots scored **99.94 %** on the original 20 pegs.
  They are root-identity-solvable. Fixed by adding pair sets whose members share
  identical root multisets.
- **2b.2 (LOCK `080bc40f`):** within-pair **99.5 %** perspective / **99.8 %**
  diagnostic, +31.3 pts paired over bag-of-roots. **KILL C fired** — channel
  profile flat (0.4 pts spread). Honest reading: **at ceiling, relative
  difficulty is unmeasurable.** My priors were both wrong — I predicted nesting
  would fail (99.7 %) and aspect would be hardest (100.0 %, the best channel).
- **Null band, 5 seeds** (`runs/null_band_seeds.json`): no-information channels
  worst |0.09| pts, sd ≤0.07; signature-bearing `aspect_root` **+4.01 ± 0.52**.
  ~45× separation. `orient_order` is **+0.00 on every seed** — canonicalisation
  proof. Prereg's 1.0 pt KILL A threshold is CONSISTENT (defensible = 0.50).
- **Auditor:** Qwen2.5-1.5B frozen, log-prob forced choice. **48.3 % (chance) on
  2-way perspective** — too hard, wrong question. **43.8 % vs 25 % chance on
  coarse 4-way** against root-disjoint distractors, shuffled control clean at
  23.8 %. Both runs kept; the failure is part of the record.

## Phase 3 — DONE. `docs/VERDICT_3_CIPHER_2026_08_20.md`

**KILL A did not fire.** Worst no-info scramble drop across 11 trained
conditions = **+0.30 pts** (prereg 1.0, defensible 0.50). The probe was live —
same runs give **+3.01 to +4.59 on `aspect_root`**, inside the null band's
+4.01 ± 0.52; `orient_order` +0.00 everywhere.

⛔⛔ **BUT THE NULL IS SCOPED, AND NOT FOR THE PRE-REGISTERED REASON. M WAS
NEVER SCARCE** — the listener sat at 99.2–100 % from step one because the
signature core hands it the answer. A cipher solves a communication problem;
there wasn't one. Honest scope: *no cipher forms when the generator has no
reason to build one.* **Making the failure reachable = phase 4, needs a call.**

⛔⛔ **THE RAW λ AXIS READS BACKWARDS — DO NOT QUOTE IT AS NOVELTY PRESSURE.**
λ multiplies a reward term, so it scales advantage **variance** (2.17×) as well
as novelty weight, and REINFORCE collapses faster under bigger steps. Normalise
the advantage and **both metrics reverse**: concentration 0.825→0.733,
R 0.384→0.258. Three controls got there —
`lambda_purchase` (λ *does* grip: within-state sd 0.113, SNR 1.28, novelty
reaches 76 % of felt reward) · `baseline_scope_control` (**falsified** my
global-baseline story) · `variance_confound_control` (sign reversal).

⭐⭐ **CONCENTRATION IS NOT A CIPHER DETECTOR.** It measures how *deterministic*
the generator got; a cipher also needs the listener to **read** those channels.
Concentration 0.774 with every no-info channel ≤0.20 pts is a fixed
**idiolect**, not a code. It lands at **0.73–0.83 in every condition tested**
(uniform ≈0.15) — this parameterisation collapses regardless; λ sets how much,
not whether.

**KILL B did not fire and could not have as specified** — auditor flat at
46.5–49.5 %, *above* its 43.8 % honest baseline. No fall to detect.

**Two verdict-function lessons, both in the VERDICT doc:** `baseline_scope`
printed **PREDICTION HELD** off two endpoint comparisons while its mechanism had
failed (the λ=0 endpoint degraded, λ=2 was unchanged). `variance_confound` fell
through to its **loud fallback** — I had enumerated "flat" and "rises" but not
"falls". The fallback is the only reason it was read by hand.

## ⭐⭐⭐ PHASE 5 DONE — KILL E FIRED. `docs/VERDICT_5_DENOTATION_2026_08_22.md`

**PREREG `c09d0fb3`. ⛔ READ `docs/DEVIATIONS_5_2026_08_22.md` WITH IT — 5 entries.**

⛔⛔ **THE FIX DID NOT REMOVE THE CODE. IT REMOVED THE PART THE PROBE CAN SEE.**
Against the CORRECT baseline `aspect_root` excess goes **−2.82 / −7.00 / −0.48 /
−5.20 / +0.48** in 5 of 8 arms (probe CLEAN) while the **naive-listener gap holds
at 8–13 pts in EVERY arm**. KILL E = probe clean + gap open. **FIRED in 4 of 8,
including BOTH at both λ.** I named it in the locked prereg as the outcome I'd
most likely misreport as success. It is the outcome.

⛔⛔ **THE RANDOM BASELINE WAS WRONG FOR CHANNELS THAT DENOTE.** FROZEN arms (no
co-adaptation ⇒ no code POSSIBLE) still show `aspect_root` **+24.89/+11.95/
+26.21/+18.82**. A generator that merely CONCENTRATES its aspect choices produces
a big drop. ⭐**Reference = an OPTIMISING policy that CANNOT NEGOTIATE**, never a
random one.

⭐⭐ **π WORKS AND DOESN'T HELP.** Same 2-bit code buys **−0.30 pts under π vs
+6.67 without** ⇒ receptor GONE. Gap unchanged; at λ=0 slightly WORSE (8.40 vs
8.00). **RELOCATION, 3rd time**: phase 4 blocked 2 channels→`coda`; here
population squeezes `aspect_root`→decoration (`coda` +3.08); add π and the gap
just stops being visible anywhere.

⭐⭐ **NEW PRIMARY DETECTOR = NAIVE-LISTENER GAP** (judge trained ONLY on honest
data, never in the loop), baselined by the FROZEN arm. **Scramble probe is
demoted to locating WHERE.**

⚠️ **ONE SEED PER CELL.** Supports "8–13 pts everywhere"; between-arm
differences are NOT interpretable.

✅ KILL F did not fire — π sound (schema guard + red-proofs both branches;
per-sample equality of `matches` AND `consistent` over ~7,200 pairs).
✅ KILL C, KILL D did not fire. ⛔ **KILL B STILL NOT MEASURED.**

⛔⛔ **THE ONE MISTAKE, 5×: TREATING ZERO AS THE DEFAULT FOR A QUANTITY NOBODY
MEASURED.** 89.3 % "ceiling" was a floor · `aspect_root` threshold had no
baseline · frozen-arm shift was **0.00 BY CONSTRUCTION** (naive judge was
BYTE-IDENTICAL to the arm's listener — `tr.train` seeds from a fixed default) ·
π-constant channels aren't probe-able · `co` shadowing un-froze half the controls
(caught ONLY because numbers were byte-identical).

## ⭐⭐ PHASE 4 DONE — KILL A FIRED. `docs/VERDICT_4_SELECTION_2026_08_20.md`

**A CIPHER FORMED.** λ=2 ambiguous stratum: **`aspect_reps` +7.41, `degree`
+5.95** (threshold 1.0). Fires at every λ.

⛔⛔ **AND IT FIRES AT λ=0 — THE CIPHER IS DRIVEN BY M SCARCITY, NOT NOVELTY
PRESSURE.** The entire flag-⑦ framing (λR is the dangerous term) is WRONG. At
λ=0 the reward is M alone — no repetition term, no novelty incentive — and
`aspect_reps` still hits +2.14. λ modulates how hard the code is driven; the
CAUSE is a co-adapting listener plus an information deficit. **λ=0 IS NOT A SAFE
CONFIGURATION.** Phase 3 could never have found this — it had no deficit.

⭐⭐ **BOTH MECHANISMS COEXIST — cipher does NOT replace honest selection.** The
policy also learned to pick *informative* dependents: ambiguity 25.1 %→14.7 %
while uttering LESS than random (rate 0.47 vs 0.50), decidedness 0.80 vs 0.50.
The thesis works; the cipher rides on top of it.

⭐⭐ **CODELESS CONTROL IS WHAT DECIDED IT.** A concentrated policy overfits the
listener, and an overfit listener degrades on ANY scramble — the `random` arm
can't rule that out (its listener is never overfit). So: same λ=2 training, but
the policy is FORBIDDEN to steer `aspect_reps`/`degree` (uniform, no logprob, no
grad). Probe goes **−1.24 / +0.40** with overfitting held constant
(M 98.9, decidedness 0.807). **Artefact explanation refuted.**

⛔⛔ **THE CODE RELOCATES.** In that control `coda` (left free) jumps +0.90 →
**+3.15**. A cipher is attached to the EXISTENCE OF ANY UNCONSTRAINED CHANNEL,
not to a channel. **Channel-blocking is not a mitigation.**

✅ KILL A′ **+0.27** (constructed no-code arm, ≤0.5). ✅ KILL C did not fire —
but my first metric was wrong (mean rate, not **decidedness**); it printed
"inert" while ambiguity had already fallen 25.1→14.7, which random selection
cannot do. ⛔ **KILL B NOT MEASURED** — auditor needs re-baselining on partial
glosses first. **No interpretability claim is made.**

⛔ **D1 applied:** `m_vs_ceiling` read **108 %** because it compared learned-
selection arms against a floor measured under RANDOM selection. Each arm now
reports **its own uniform floor** (M−floor: random **−7.4**, learned +6.9/+9.4/
+8.5, codeless +10.5). Beating the uniform floor is legitimate on its own and is
**not** evidence of a code — the codeless control carries that claim.

## Phase 4 — setup (pre-check + prereg)

**Nate's call, 2026-08-20: make M scarce via SELECTION** (generator utters only
a subset of `sig.contains[]`), not surface corruption. It is the project's own
thesis — novelty comes from impression-selection — so M becoming scarce falls
out rather than being imposed, and it puts the model in the pragmatics layer.

`tools/confusability.py` → `runs/confusability.json`:
- ⭐⭐ **M CEILING UNDER SELECTION = 89.3 %** (phase 3 ran 99.2–100 % = no
  pressure). ~11 pts the generator now has a reason to recover — and recovering
  it through the free channels IS the cipher. **KILL A is reachable.**
- ⭐⭐ **0 MUTUAL PAIRS.** All 8 confusions are ASYMMETRIC containments (A's full
  scene fits inside B's larger signature). Nothing is irreducibly
  indistinguishable, so the 11 pts are recoverable in principle — otherwise we'd
  have been measuring a wall no code could climb.
- Ambiguity is monotone in how much is withheld: **1.13 → 1.32 → 1.47** mean
  consistent referents at 0/1/2 dependents dropped (10.0 / 21.3 / 28.1 %
  ambiguous). Bare head only: 1.739.
- Confusable core = the **light family** (49 flickering / 50 steady / 41 going
  out from a window, all 3.00) — the imagery pairs Nate steered toward light.

⛔⛔ **STRATIFY THE PROBE OR THE HEADLINE DILUTES.** **26/60 referents have a
head root UNIQUE to them** — selection never makes them ambiguous, so they never
need a code. Pressure lives in the other 34. A scramble drop averaged over all
60 is diluted ~2× and could push a real cipher under the 1.0 pt threshold →
another clean-looking null. Condition the probe on whether the referent was
ambiguous **under the subset actually chosen**.

⛔ `consistent()` is the DUAL of `matches()` — every NODE finds a distinct
pattern ("still possible"), not every pattern finds a node ("fully stated"). A
partial utterance of A does not `match` A.

**PREREG LOCKED `c1f7d06c`** (`docs/PREREG_4_SELECTION_2026_08_20.md`).
**⛔ READ `docs/DEVIATIONS_4_2026_08_20.md` WITH IT — two entries already.**

✅ **POSITIVE CONTROL PASSED — PHASE 4 IS CLEARED TO RUN.**
`tools/planted_cipher_control.py` → `runs/planted_cipher.json`. Paired arms
under selection: code learned **+7.1 pts** (92.1 → 99.1 %), probe fired
**+27.05 pts**, quiet without it **+0.17**. **KILL A can fire in this regime** —
which phase 3's could not. ⭐ The trap it had to dodge: a planted code is
invisible unless the listener USES it, so it had to run under selection and
prove use, or a null would mean "nothing to detect", not "probe blind".

⛔⛔ **D1 — "89.3 % CEILING" WAS A FLOOR, NOT A CEILING.** It is
`E[1/|consistent set|]` — uniform picking inside the consistency set. A Bayes
listener uses the likelihood and does better. **The no-code arm hit 92.1 %,
above the "ceiling"** (and arithmetic agrees: ≈85.4 % uniform for that mix).
Renamed everywhere: **`m_uniform_floor`=0.893, `m_honest_observed`=0.921.**
Headline unaffected — M is no longer pinned at ~100 %, which is all phase 4
needed. KILL D stays 70 %.

⛔⛔ **D2 — KILL A′ AS LOCKED WOULD DISCARD A TRUE POSITIVE.** The planted cipher
drops **+14.29 pts on the UNAMBIGUOUS stratum**, so A′ ("must stay ≤0.5") fires
on a real code. A code is set for EVERY referent and **the listener uses a free
shortcut even where honest signal suffices**. ⭐⭐**A CIPHER CANNIBALISES THE
HONEST CHANNEL, it doesn't just add one.** Negative control moves to a
**no-code control ARM** (constructed absence, +0.17) — never the stratum split.
Stratified drops stay as description; the 4.7× ambiguous/unambiguous ratio gets
**no threshold** (one observation, would be a yardstick from the artefact).

## Then — ⛔ ALL NEED NATE'S CALL

0. ⭐**SEEDS (5/cell) BEFORE ANY BETWEEN-ARM CLAIM.**
0b. ⭐⭐**MITIGATION MUST ATTACK THE INCENTIVE, NOT THE CHANNEL** — 3 relocation
   results say channel-level cannot work. Candidates: penalise I(free channel;
   referent) directly, or the deferred clarification BOUND.
1. ⛔⛔ **THE COUNTER CANNOT BE PUBLISHED ON THIS BASIS.** B2 holds:
   `auditor_state` ≠ `MEASURED`, and phase 4 has just demonstrated a **live
   cipher pathway**.
2. **Re-baseline the gloss auditor under selection**, then set KILL B.
3. **Mitigation, if wanted, cannot name channels** — the code relocated.
   It must constrain the LISTENER's access, or penalise mutual information
   between free channels and referent identity directly.
4. **Retire concentration as a cipher detector** — failed to discriminate in
   BOTH phases (codeless ctrl: 0.519 concentration, `aspect_reps` −1.24).
5. Northern hemisphere ablation (B3: must denote into the SAME `Scene` algebra
   or the comparison is confounded).
6. ✅ Advantage normalisation is now default in phase-4 runs.

## Standing rules

- ⛔ **Backbone model and phase progression are Nate's call, EVERY time.**
- ⛔ **B1** — the gloss auditor ships in the same commit as any trainable
  listener facing a learned generator.
- ⛔ **B2** — the counter may never be logged or served without its conditioning
  pass rates. Enforced in SQL; `publish_counter` refuses unless
  `auditor_state = MEASURED`.
- ⛔ **B3** — northern grammar must share the `Scene` algebra.
- ⭐ PREREG → run → VERDICT, locked by body hash (`tools/lock_prereg.py`).
  Adopted from `D:\IC_experiments`.
- ⛔ Never round-trip UTF-8 through PowerShell `Get-Content | Set-Content`.
- ⛔ Windows `write_text` converts `\n`→`\r\n`; pin `newline=""` anywhere bytes
  are hashed.

## Key files

`docs/GRAMMAR_SOUTHERN_v0.1.md` (v0.2) · `docs/PHASE2_DESIGN.md` ·
`docs/PREREG_3_CIPHER_2026_08_20.md` (LOCK `3c49ad47`) ·
`docs/VERDICT_2B2_STRUCTURE_2026_08_20.md` · `docs/REFERENT_COVERAGE.md`
`tlon/{grammar,referents,listener,novelty,selfplay,audit,persist}/`
`tools/`: `mint_lexicon` `count_paraphrases` `verify_*_pairs` `shortcut_probe`
`cipher_control` `null_band_seeds` `run_2b2` `run_phase3` `validate_auditor*`
`lock_prereg` `build_pairs_page` · phase-3 controls: `lambda_purchase`
`baseline_scope_control` `variance_confound_control`

## DEFERRED — clarification / conversational repair (Nate, 2026-08-22)

**Parked deliberately: separate engineering problem, high rabbit-hole risk.**
Do not start this while the leak is open.

Idea: let the listener ask "what do you mean?" — repair is near-universal in
human language exactly because underdetermined reference is the normal case.
⛔ **It does NOT fix the leak — it widens it.** A "huh?" is a clean discrete
back-channel telling the generator precisely where the listener was confused,
which is a far better signal for BUILDING a code than the scalar reward; and the
exchange itself (asked or not, which repair, how many turns) is a new free
channel with more capacity than the decorative ones. Phase 4: the code attaches
to the EXISTENCE of a free channel, not to a channel.

⭐⭐ **BUT IT YIELDS THE BEST DETECTOR WE'VE FOUND, AND IT'S A BOUND, NOT A
HEURISTIC.** We measured how often a partial utterance is genuinely ambiguous
(14–25 %, `runs/confusability.json`). **An honest listener cannot ask for help
less often than the world is ambiguous.** Asking 2 % of the time while confused
15 % of the time means it resolved the rest from side information. Legible to
outsiders — unlike scramble probes and control arms — so it belongs beside a
public counter.
⛔ Compute the floor against the ambiguity of the utterances **the policy is
actually producing**, not a fixed constant — an excellent honest describer also
drives clarification down (phase 4: 25 %→14.7 %). Same error as the 92.1 %
ceiling: the yardstick must move with the regime.

## Open / unresolved

- **Nate's tokenization studies** — still not located. Not in `D:\IC_experiments`
  or `D:\Resolve Research`.
- **01 mirror / 12 map** stay `validated: false`. They are also the most
  confusable pair at **39 %** targeted reachability (both lean on `rän`).
- **Tiger peg** removed; now expressible via `tlex`. Not reinstated without a call.
- **`mlö`** is the one noun-verb gloss kept, as Borges' attested exception.
