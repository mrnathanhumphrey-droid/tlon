# PRE-REG — 3: under novelty pressure, does the generator describe or does it cipher?

- **Date:** 2026-08-20
- **Status:** LOCKED — pre-registered. Not fired.
- **LOCK:** `3c49ad47` (sha256[:8] of draft body at lock, 2026-08-20T20:51Z)
- **Arc:** Tlön phase 3. Extends `VERDICT_2B2_STRUCTURE_2026_08_20.md` (LOCK `080bc40f`)
  and the null band in `runs/cipher_null_band.json`.
- **Lexicon:** `e2b8527010231a81fd31b6eeb9de3d8c` · **Referents:** 60, REVIEWED.

## What changes, and why it is the dangerous phase

Every phase so far had a **random** generator. Nothing was optimising against
the listener, so no private code could form — that is why the 2b.2 null band is
trustworthy. Phase 3 makes the generator **learned**, and points it at
`L = M_gate + λ·R`.

That is the exact configuration flag ⑦ describes: a lossless channel, an exact
decoder, and a listener the generator can co-adapt with. The generator's
cheapest route to high M and high novelty is **not** to describe better. It is
to agree with the listener on an arbitrary code — "aspect reps = 3 means moon" —
and then vary everything else freely. **A cipher scores excellently on M.** No
rejection-rate alarm can see it.

## One-line hypothesis

Under λR pressure the generator will find genuinely different impressions rather
than a code: M holds, R falls, and **every channel carrying no referent
information stays inside the 2b.2 null band** (≤0.03 pts scramble cost, against
4.05 pts for a signature-bearing channel).

I am pre-registering the expectation that **this fails at some λ**. The
interesting quantity is not whether a cipher forms but **the λ at which it
starts**.

## Falsifier (pre-registered kill conditions)

- **KILL A — CIPHER FORMED.** Any no-information channel (`orient_order`,
  `coda`, `degree`, `aspect_reps`) shows a scramble-drop **> 1.0 pt**, i.e.
  ≳30× the measured honest band. Report the λ and the channel.
- **KILL B — INTERPRETABILITY COLLAPSE.** Gloss-auditor agreement falls by
  **> 10 pts** from its phase-2 value **while** M pass-rate stays ≥ 95 %. This
  is the divergence that matters: **track the gap, not either number.**
- **KILL C — NO NOVELTY EFFECT.** Mean R at the end of training is within 5 % of
  its value at λ=0. The repetition pressure does nothing and the whole framework
  is inert at this scale.
- **KILL D — M COLLAPSE.** Listener within-pair accuracy drops below 80 %. The
  gate stopped meaning anything and every other number is uninterpretable.

## Priors to lose (pre-register against)

- That the gloss auditor will catch a cipher **before** the scramble probe does.
  I expect the scramble probe to be the sharper instrument; if the auditor fires
  first, my model of the failure is wrong.
- That a cipher will look like noise. It will look like **excellent
  performance**. If I find myself pleased with the numbers, that is the moment
  to run the controls, not to report.
- That λ has a safe value. There may be no λ where R is effective and no code
  forms; that would be a real and publishable negative.

## Must-beat baselines / controls

1. **λ = 0 control run** — same everything, no repetition pressure. All deltas
   are measured against this, paired.
2. **The 2b.2 null band** — `runs/cipher_null_band.json`. ⚠️ Single seed;
   **must be re-run at ≥5 seeds before it is quoted as a threshold.** That
   re-run is a prerequisite of this phase, not an optional extra.
3. **Frozen 2b.2 listener** as a held-out judge — never trained in this loop, so
   it cannot co-adapt. Divergence between it and the co-trained listener is
   independent evidence of a private code.
4. **Gloss auditor** — see below. Audit only; **never** in the accept/regenerate
   loop, or it becomes a yardstick derived from the artefact it audits.

## Method

1. Generator: a small from-scratch policy over the scene space (same class as
   the listener; not a backbone decision). Best-of-N under the grammar mask,
   scored by `M_gate + λ·R`.
2. Listener: the 2b.2 encoder, **trainable**, co-adapting.
3. λ sweep: 0, 0.25, 0.5, 1.0, 2.0. Every measurement repeated per λ.
4. After each λ: run the scramble probe on all five channels, paired, same rows.
5. Log every utterance to the audit store with its M margin, R, orbit spend and
   collision status.

## Confound controls (pre-registered)

- Scramble probe is **paired on identical rows** — the un-paired version
  produced a spurious 1.35 pt drop on a channel that is provably a no-op.
- The auditor sees the **English gloss**, never the morphemes, and is frozen.
- The λ=0 control uses the same seed and data budget.
- The counter may not be published: `auditor_state` must be `MEASURED`, and
  phase 3 is the first phase where it can be.

## Cost / lane

Local. Generator and listener are both ~5 M params; the λ sweep is 5 runs of
roughly a minute each plus probes. Auditor inference is the only new cost and it
is 2-way forced choice over short glosses. Ledger row regardless.

## Standing floor (reportable regardless)

- **No cipher at any λ:** the framework survives adversarial pressure, with a
  measured band and an independent judge. That is the result the project exists
  to produce.
- **Cipher forms at λ\*:** we have located the boundary, with two independent
  detectors and a null band to calibrate them. **This is the more interesting
  outcome** and it is what the whole instrument was built to catch.
- **KILL C (R inert):** the repetition framework does not bite at this scale;
  redirect before spending on a bigger one.

## ⛔ BLOCKED — needs Nate's call

**B1 binds here:** the gloss auditor ships in the same commit as a trainable
listener facing a learned generator. It requires a **frozen, general model of
different provenance from anything trained in the loop.** That is a model
decision and therefore Nate's, every time.

**Recommendation: `Qwen2.5-1.5B-Instruct`, local, already in the HF cache.**
- Task is **2-way forced choice** — "here are two referent names and one English
  gloss; which is it?" — not 60-way. That matches the within-pair metric, is
  well within 1.5B, and keeps the signal low-variance.
- Local, $0, no API, no data leaving the machine.
- Our in-loop models are from-scratch, so any external model is of different
  provenance by construction; the requirement is only that it is **frozen** and
  never trained here.
- A weak auditor is acceptable. It needs to be better than chance and
  **immovable**, not accurate.
