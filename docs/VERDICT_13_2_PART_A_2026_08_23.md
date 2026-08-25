# VERDICT 13.2 PART A — ⛔ **THE CONSISTENCY CHECK FAILED. THE METRIC CELLS ARE UNREADABLE.**

**Date:** 2026-08-23 · PREREG **`4ad552d4` VERIFIED** · n=8 · λ=0 · 4000 steps ·
64 runs · `runs/phase13_2_partA.json` · both arms `REVIEWED`
(`docs/REVIEW_13_2_ARMS_2026_08_23.md`)

---

## ⛔⛔ THE HEADLINE, AND IT IS THE LOCKED BRANCH-4 OUTCOME

> **categorical×head did NOT land on categorical×table: −30.60 pts, Welch
> t = −7.94.** The locked rule is *"metric cells unreadable; stop, diagnose."*
> **Stopped. Diagnosed. No metric cell is interpreted below.**

⛔ **THIS IS NOT "H3 FALSIFIED."** The falsification branch requires
metric×head and categorical×head to gap *identically*. They do not — they differ
by 36 pts. And the diagnosis (§4) shows the metric head **never produced a code
at all**, so its ≈0 gap measures an optimiser collapse, not the conventionability
of a metric residue. Reading `metric×head = +0.13` as *"the metric is not
conventionable"* is the single most available wrong conclusion here.

---

## 1 · Build checks and carried confirmations — **all pass**

| | lyric | random |
|---|---|---|
| **scenes-per-form** (via `consistent()`) | **3.000**, max 3, 100 % of utterances | **3.000**, max 3, 100 % |
| landmine: one medoid per mate | **8/8 clusters** | **8/8 clusters** |
| scenes missing a residue | **0** | **0** |
| residue log populated from turn one | ✅ | ✅ |

⛔ **Part 1 is true by construction and is not evidence the lever works** — it is
the frontier quantity that read exactly **1** on all four previous sets, and it
reads 3 here because the cluster is 3 wide. Part 2 is the test.

✅ **λ=0 TABLE-IDENTITY CHECK PASSES, both co-adapt and frozen** — metric×table
and categorical×table are **bit-identical**. In table mode the policy never sees
a coordinate and R is out of the reward, so this is the expected exact result;
divergence would have meant the residue reaches the loop by an unknown route.

⚠️ **Expressible component at ceiling on 64/64 runs** (1.0000, both listeners).
Confirms D5: that control cannot adjudicate; the frozen arm carries the role.

---

## 2 · The 2×2, per cell (residue-component gap, pts, n=8)

| arm | param | co-adapt | frozen | co-adapt accuracy |
|---|---|---|---|---|
| lyric (metric) | **table** | **+66.71** (sd 3.17) | +14.46 (sd 3.84) | 98.9 % |
| random (categorical) | **table** | **+66.71** (sd 3.17) | +14.46 (sd 3.84) | 98.9 % |
| lyric (metric) | **head** | **+0.13** (sd 1.62) | −0.60 (sd 1.33) | 33.8 % |
| random (categorical) | **head** | **+36.11** (sd 10.43) | +0.88 (sd 3.94) | 72.1 % |

Naive judge ≈ 32–36 % throughout; the within-cluster ceiling without a code is
**33.3 %**. MDE floor at n=8 is **2.96 pts**.

---

## 3 · ⭐⭐ WHAT *IS* READABLE: **H2 HOLDS, AND IT IS THE PROJECT'S FIRST NON-VACUOUS M**

The consistency check gates the **metric cells** (H3). It does not gate the
**table** cells, which are the unchanged historical `ChannelPolicy` and are
bit-identical across arms.

> **A pact forms around a distinction the grammar structurally cannot express.**
> Within-cluster residue accuracy rises from a **33.3 % ceiling** to
> **98.9 %** co-adapted, against a naive judge at **32.2 %** — a gap of
> **+66.71 pts (sd 3.17)**, more than **22×** the MDE floor, every one of 8
> seeds between **+63.44** and **+72.67**.

**And the frozen arm does real work here.** Frozen: **+14.46 pts** (46.7 %
accuracy) — the generator shifts its distribution toward a listener that cannot
co-adapt, and that alone buys 14 pts. Seed-paired (same seed, only
`train_listener` differs): **+52.25 pts (sd 4.30)** attributable to
co-adaptation.

⛔ The **+52.25** is a *seed-level* paired difference, not an item-level one —
the two runs emit different utterances, so no item pairing exists. Reported as
seed-paired, and the two means are reported side by side above.

⭐ This is what the whole lever hunt was for: an ambiguity an optimising speaker
cannot talk its way out of, and a pair that builds a convention across it.

---

## 4 · ⛔ THE DIAGNOSIS — why the consistency check failed

`tools/diag_13_2_consistency.py`. Two questions, measured.

### The prediction that failed, in my own words

> *"one-hot into a linear layer IS a row lookup, so the residue-conditioned head
> degenerates to exactly the per-referent table on this arm."*

**True of a single linear layer. The head is not one.** The trunk is
`one_hot → Linear(d,32) → Tanh → Linear(32,32) → Tanh → Linear(32,|vals|)`.
A one-hot input selects a row of the **first** weight matrix — but that row is a
32-dim **embedding**, not an output. The second trunk layer and every channel
head are **shared across all 24 referents**. A per-referent embedding through a
shared nonlinear map is not a free per-referent output.

⭐⭐ **And the two design requirements were in direct tension, written into the
same prereg, and I did not notice.** The trunk was made an MLP *on purpose* so
the falsifying cell stayed reachable — a linear trunk could not memorise an
arbitrary code, which would have made the 2×2 self-confirming. **That same depth
is exactly what breaks the "one-hot == table" equivalence the consistency check
assumed.** Both requirements are in `4ad552d4`; they cannot both hold.

### Q1 — capacity or optimisation? **Capacity is fine.**

Supervised, at the real scale (24 referents × 5 channels, same 4000-step
budget), the head fits an **arbitrary** code to **100.0 %** on *both* arms.
The architecture can express any code we need.

### Q2 — what did REINFORCE actually converge to?

| arm × head | distinct codes | mates separated per cluster | concentration |
|---|---|---|---|
| **lyric (metric)** | **1 / 24** | `[1,1,1,1,1,1,1,1]` | 1.00 all channels |
| **random (categorical)** | **7 / 24** | `[2,3,2,3,3,3,1,2]` | 1.00 all channels |

> ⛔⛔ **The metric head collapsed to ONE code for all 24 referents.** The
> listener has nothing whatsoever to read. `metric×head = +0.13` is a policy
> collapse, not a statement about metric residues.

This is the collapse `phase3.py` already documents — *"plain REINFORCE pushes up
the log-prob of every sampled action and the policy collapses onto whatever it
saw first… concentration hit 0.92 even at lambda=0"* — reappearing far worse in
a **shared-parameter** architecture, where a gradient for one referent moves
every other referent's output too. The metric arm's coordinates sit close
together in a 5×5×5 lattice, so their embeddings are close and the bleed is
severe; one-hot coordinates are mutually orthogonal, so the categorical arm
partially resists it (7 codes rather than 1).

⇒ **The ordering table (24 codes) > categorical-head (7) > metric-head (1)
tracks how much code diversity survived the optimiser**, which is a property of
REINFORCE-through-shared-weights, not of conventionability.

---

## 5 · What this run does and does not license

**Licensed:**
- **H1** ✅ scenes-per-form 3.000; the residue is contained and the build is right.
- **H2** ✅ **a pact forms around an inexpressible distinction**: 33.3 % ceiling →
  98.9 %, gap **+66.71 pts**, frozen control **+14.46**, seed-paired **+52.25**.
- The **λ=0 table-identity** and **landmine/unknown-as-ignorance** confirmations.

**NOT licensed — do not write any of these:**
- ⛔ *"H3 falsified / the head permits but does not use the metric."* The
  falsification branch needs the two head cells to gap **identically**; they
  differ by 36 pts, and the metric head emitted no code at all.
- ⛔ *"A metric residue is not conventionable."* Never tested — the optimiser
  collapsed before the question was posed.
- ⛔ *"Categorical beats metric."* A comparison between a 7-code policy and a
  1-code policy is a comparison of collapse severity.
- ⛔ *Part 1's 3.000 as the lever working.* True by construction.
- ⛔ *The isolation claim without its containment clause* — quote the 13.1 ledger.
- ⛔ *Any evocation-is-intersubjective reading.* Per **D11** what exists is **one
  human geometry plus one mechanical embedding, not two distillations.** Nobody
  writes "two distillers agreed."

---

## 6 · Effect sizes, for whatever comes next

| cell | mean | sd | MDE at n=8 |
|---|---|---|---|
| table, co-adapt | +66.71 | 3.17 | 2.65 |
| table, frozen | +14.46 | 3.84 | 3.21 |
| categorical×head, co-adapt | +36.11 | **10.43** | 8.72 |
| metric×head, co-adapt | +0.13 | 1.62 | 1.35 |

⭐ **The realised sd on the table cells (3.17) closely matches the phase-8 prior
(3.54)**, so the n=8 sizing was sound — for the table. The categorical×head cell
is **3× noisier** (sd 10.43), which is itself a symptom of partial collapse: how
many codes survive varies a lot by seed.

⛔ **Nothing here is a Part-B power input yet.** Part B's quantity is a growth
curve, and a curve measured on a collapsing policy would inherit the collapse.

---

## 7 · ⏸ STOPPED — Part B is Nate's trigger, and it is not the obvious next step

Per the brief, no auto-proceed. And the honest reading is that **the head
parameterisation needs fixing before either H3 or Part B is worth spending on**:
a growth curve over a policy that converges to one code would measure the
collapse, not the convention.

The collapse is a known, addressable class — the codebase already carries
`entropy_bonus`, `normalize_advantage` and `per_ref_baseline` for exactly this,
and Q1 proves the architecture can hold the code. **But which fix, and whether to
re-run Part A at all, is a decision, not a default.** Nothing is being changed
without it.
