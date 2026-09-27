# RESULTS — IDF-1b: replay versus readable provenance

- **Prereg:** `docs/PREREG_IDF1B_2026_09_25.md`, LOCK `904b85df`, verified.
- **Deviations:** `docs/DEVIATIONS_IDF1B_2026_09_25.md` (D1, D2). Both were
  found by data and both were written before the corrected numbers existed.
- **Date:** 2026-09-25. CPU only, no GPU, no remote box, no spend.
- ⛔ **No verdict is declared here.** §6 says why.

---

## 0 · What IDF-1b was for

IDF-1's O-E — an empirical kernel keyed on exact surface identity — reached
lag-2 0.2600 at dose 0 while the D6 model sits at 0.3854, contradicting IDF-1's
locked secondary prediction. **H-REPLAY** said O-E's suppression was surface
identity acting as a pointer into specific corpus chains rather than provenance
readable off the surface. Instruments 1-3 take the pointer away; instrument 4
asks whether identity is readable at all; instrument 5 removes the fidelity
confound.

---

## 1 · Reproduction of IDF-1 first

Before anything new ran, IDF-1's own numbers were reproduced from committed
code (`tools/act2_idf1.py`, recovered from the session transcript — the
originals were heredocs that left no file). All eight arms and all three
fallback rows match to the last reported digit, checked by
`tools/act2_idf1_repro_check.py` reading both sides from artefacts.
**No deviation against IDF-1.**

The trained-on corpus `16abeb8d27e4ccd3`, which survived only on one laptop, is
now persisted to the hub; the hub's own stored digest for `train.jsonl` **is**
the scope identifier the pipeline pins.

---

## 2 · The five instruments

All at dose 0 unless stated. "Closes" is the fraction of the blind-to-true gap,
anchored on the two red-proofs O-A = 0.4456 (0 %) and O-C = 0.0285 (100 %),
gap 0.4171.

| | lag-1 | lag-2 | closes |
|---|---|---|---|
| O-A blind *(red-proof)* | 1.0357 | 0.4456 | 0.0 % |
| **2 · O-E-noreplay** | 0.8973 | **0.3254** | **28.8 %** |
| **model D6** | 1.0278 | **0.3854** | **14.5 %** |
| O-E *(IDF-1 reference)* | 0.9580 | 0.2600 | 44.5 % |
| **3 · O-E-heldout** | 0.9457 | **0.2608** | **44.3 %** |
| O-C true *(red-proof)* | 0.9651 | 0.0285 | 100.0 % |

**1 · Replay rate.** 30.5 % of O-E's consecutive triples occur as real
consecutive triples inside one corpus chain (30.3 / 30.5 / 30.6 % across doses
−1 / 0 / +1). About a third of the walk is literal chain replay.

**2 · O-E-noreplay.** Denied its own source chain, the kernel's suppression
falls from 44.5 % of the gap to **28.8 %** (dose −1: 10.2 %, dose +1: 31.8 %).
Fallback ladder: 91.8 % exact-from-another-chain, 2.0 % root-set, 6.2 % reseed.
So same-chain replay accounts for roughly a third of O-E's effect, and the rest
survives without it.

**3 · O-E-heldout.** A kernel built on draw A, continuing draw B's surfaces,
is essentially unchanged: 98.2 % exact hits, lag-2 **0.2608**, closing 44.3 %
against O-E's own 44.5 %. Suppression transfers across draws intact.
⛔ The first run of this instrument was confounded and is **D1**.

**4 · Identifiability with surface identity.**

| dose | ALL | seen surfaces | unseen surfaces |
|---|---|---|---|
| −1 | 0.5944 [0.5833, 0.6053] | 0.5857 [0.5736, 0.5972] | **0.6463 [0.6242, 0.6681]** |
| **0** | **0.6034 [0.5930, 0.6133]** | 0.5961 [0.5847, 0.6069] | **0.6414 [0.6181, 0.6650]** |
| +1 | 0.6099 [0.5995, 0.6196] | 0.6037 [0.5921, 0.6153] | **0.6445 [0.6194, 0.6673]** |

Adding surface identity and per-root index-bucket size lifts dose-0 AUC from
IDF-1's **0.5437** to **0.6034**.

⭐⭐ **The stratification answers backwards from the worry it was added to
settle.** Unseen surfaces — those absent from the training fold, and so
impossible to have memorised — score **higher**, at every dose. The lift is not
memorisation. Whatever the classifier reads off a surface generalises to
surfaces it has never encountered.

**5 · Matched-fidelity floor (descriptive, gates nothing).** Each arm's knob
tuned so its lag-1 matches the model's, then lag-2 read at the model's own read
size, 12 chains × 10 turns, 500 independent reads.

**Dose 0 — the pin, and the only dose where the knob brackets the target:**

| arm | knob | lag-1 | lag-2 mean | 95 % band | model's 0.3854 sits above |
|---|---|---|---|---|---|
| O-A | responsiveness 0.9941 | 1.0304 | 0.4363 | [0.3333, 0.5471] | 16.6 % of reads |
| **O-B(4)** | **bar-rate 0.127** | 1.0246 | **0.4238** | [0.3125, 0.5417] | **23.6 % of reads** |
| O-E-noreplay | ⛔ unreachable | 0.8996 | 0.3235 | [0.2188, 0.4375] | 83.8 % |

⛔ At doses −1 and +1 the model's lag-1 (1.0495, 1.0463) is **above O-A's
ceiling of 1.0303**, so no arm can be matched there and O-B(4) degenerates to
O-A at bar-rate 0. Those rows are reported, and are not comparisons.
⛔ O-E-noreplay could not be matched at **any** dose: its lag-1 tops out near
0.90. Its lower lag-2 is therefore never cleanly attributable to better release
rather than to carrying less forward. See **D2**.

---

## 3 · What the locked reading table says

- **REPLAY** requires O-E-noreplay **and** O-E-heldout each to close ≤ 15 %,
  and O-B(4)'s AUC upper bound below 0.60. Observed: 28.8 %, 44.3 %, and an
  upper bound of 0.6133. **REPLAY does not fire.**
- **READABLE** requires either arm to close ≥ 35 %, or the AUC lower bound above
  0.65. O-E-heldout closes **44.3 %**. The AUC lower bound is 0.5930.
  **READABLE's condition is met, through the OR, on one arm.**

**By the letter of the table the reading is READABLE → R3.**

---

## 4 · Why H-REPLAY is half-right, which the table has no cell for

The two instruments built to remove the pointer disagree about what the pointer
was:

- Removing the **same chain** costs 16 points of gap (44.5 % → 28.8 %).
- Removing the **draw** costs nothing (44.5 % → 44.3 %).

So the suppression is not tied to the individual chain — it survives being
asked to continue a corpus it never saw. But it does lean on being able to
consult *that* chain, worth about a third of the effect, consistent with
instrument 1's 30.5 % literal replay rate.

⭐ Both facts hold at once because **the pool is shared**. Draw B's surfaces are
in draw A's kernel 98.2 % of the time. "Generalising across draws" here still
means "having seen these surfaces", and the vocabulary is the thing held
constant. That is the right control — D1 shows what happens when it is not —
but it bounds what instrument 3 can establish.

---

## 5 · The number that cuts against R3's consequence

READABLE's locked consequence reads: *"The model's gap to the best generalising
window-1 speaker becomes the quantity every past release read is restated
against, and rung 1 returns as a capacity question."*

Instrument 5 measures that gap directly, and its sign is the opposite of what
that sentence anticipates. At matched fidelity at dose 0:

> **model 0.3854 · best generalising window-1 speaker 0.4238**

The model suppresses **more** than the best window-1 speaker once both carry the
same amount forward, sitting at roughly the 24th percentile of that speaker's
own read distribution. **Model-minus-floor is negative, by 0.0384.**

⚠️ Stated with its width: 0.3854 lies comfortably inside O-B(4)'s 95 % band of
[0.3125, 0.5417]. At the model's read size of 120 turns the two are **not
distinguishable**. The honest statement is that the model is at or slightly
past the matched window-1 floor, not that it beats it.

---

## 6 · ⛔ No verdict is declared

Three things are true together and no locked cell covers the combination:

1. **READABLE's condition is met**, through an OR, on the single instrument
   that had to be corrected mid-run (D1).
2. **Instrument 2 sits at 28.8 %**, inside the band the prereg deliberately
   declared no-verdict, and the prereg says that band means the effect is
   intermediate rather than the estimate noisy.
3. **Instrument 5 contradicts R3's stated consequence.** Model-minus-floor is
   negative, so "rung 1 returns as a capacity question" does not follow from
   the quantity R3 nominates.

⛔ This is the same shape as the conflict that stopped IDF-1's verdict, and
resolving it by choosing which of the three to privilege would be retrofitting.
It goes to Nate and Wilson.

**Also open, from D1:** the locked §5 vacuous-pass guard flags lag-1 **z** below
6.0. The confounded instrument 3 had lag-1 of 0.4961 against the model's 1.0278
— under half the fidelity — and passed at z = **+439**, because z scales with n.
⭐ **A z-floor cannot detect a half-collapsed speaker at large n; only the raw
profile can.** That guard sits inside a locked document and has not been
touched.

---

## 7 · Artefacts

| | |
|---|---|
| instruments | `tools/act2_idf1.py`, `tools/act2_idf1b.py` |
| IDF-1 reproduction check | `tools/act2_idf1_repro_check.py` |
| red-proofs | `tests/test_idf1_instruments.py` (13), `tests/test_idf1b_instruments.py` (20) |
| IDF-1 originals | `runs/act2/idf1/step2a.txt`, `step2b.txt` |
| IDF-1 reproduced | `runs/act2/idf1/repro_step1.txt`, `repro_step2.txt` |
| instruments 1-5 | `runs/act2/idf1/i1_replay.txt` … `i5_matched_floor.txt` |
| the confounded instrument 3 | `runs/act2/idf1/i3_heldout_FREEPOOL_confounded.txt` |

---

## 8 · ADDENDUM 2026-09-27 — the model's own read-to-read spread, measured

⛔ **Descriptive. No verdict is declared and §6 is unchanged** — the three
conflicting facts remain open for Nate and Wilson. Nothing above this line has
been edited.

**Source:** IDF-2 Step P (`docs/PREREG_IDF2_2026_09_26.md`, LOCK `37363296`
§3A; `runs/act2/idf2/stepP/power.json`). The D6 adapter `ct-s20624` was re-read
at **48 × 10 across eight independent seeds** — 384 lag-2 pairs per read, no
chains dropped — for a purpose unrelated to this document: to check that
IDF-2's reading table could resolve its own bands.

    0.3750  0.3776  0.3854  0.3854  0.4193  0.4244  0.4271  0.4323
    mean 0.4033 · SD 0.0245 · 8 seeds

**§2 and §5 cite `0.3854`. That was a single 120-turn read, and it ranks
2nd-lowest of the eight.** It is inside the spread; it is not a central
estimate.

### What it does to §5, which is where it matters

§5 reports *"model 0.3854 · best generalising window-1 speaker 0.4238 …
model-minus-floor is negative, by 0.0384."*

| | model | O-B(4) floor | difference |
|---|---|---|---|
| as reported (single draw) | 0.3854 | 0.4238 | **−0.0384** |
| with the 8-seed mean | **0.4033** | 0.4238 | **−0.0205** |

⭐ **§5's stated reading survives, and gets firmer rather than weaker.** It
already said the two were *"not distinguishable"* and that the honest
statement was *"the model is at or slightly past the matched window-1 floor,
not that it beats it."* With the mean in place of the low draw the model is
still at or below that floor, by half as much, and still well inside noise.
**What is new is that the model's own read-to-read spread is now measured
instead of assumed.**

### It also corroborates a noise floor already on record

Scaling the measured SD from 384 pairs to the 96 a 120-turn read holds gives
**0.0490** for a single read at §5's size. The difference between two such
reads is `√2 × 0.0490 =` **0.0693**, against the **0.073** same-object floor in
`RESULTS_EPOCHS_LEVER_2026_09_17.md` — **94.9 % agreement**, reached by an
unrelated route.

⚠️ So the size of the spread is not news. What is new is that it is attached to
the specific value this document quotes. **From 2026-09-27, cite
`0.4033 ± 0.0245` wherever C0's lag-2 appears.**
