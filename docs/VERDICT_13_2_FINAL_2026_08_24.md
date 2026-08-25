# VERDICT 13.2 FINAL — the arc closed, and the one page future-me needs

**Date:** 2026-08-24 · PREREG `4ad552d4` + `d70b3a4f`, both VERIFIED ·
**no further experiment; this is the citable record.**

⛔ **The terminal-fix clause fired.** `d70b3a4f` §2 pre-registered that the
standardisation fix was the last one. It failed — and it failed on the *control*
arm, which is locked-read **branch 4**, so no metric cell was ever interpreted.
**No fifth fix. The result stands.**

---

# 1 · ⭐⭐⭐ THE FINDING — H2, and it is the project's headline

> **A pact forms around a distinction the grammar structurally cannot express.**

| | |
|---|---|
| within-cluster floor (no code possible) | **33.3 %** |
| naive judge | 32.2 % |
| co-adapted | **98.9 %** |
| **gap** | **+66.71 pts** (sd 3.17) — **22× the MDE floor**, all 8 seeds +63.44…+72.67 |
| frozen-listener control | **+14.46** (distribution shift alone) |
| co-adaptation-specific share | **+52.25** (sd 4.30), seed-paired |

⭐⭐ **H2 IS INDEPENDENT OF EVERY CLOSED LEVER BELOW.** It comes from the
**table** cells, which use the *historical* `ChannelPolicy` — no MLP head, no
residue-conditioned trunk, **no input-scale confound**, and R absent from the
reward at λ=0. Nothing that broke the metric arm can reach it.

⛔ **+52.25 is a SEED-level paired difference, not item-level** — the co-adapt
and frozen runs emit different utterances. Report the two means side by side;
never subtract them.

**Supporting build facts:** scenes-per-form **3.000** both arms (the
frontier-relevant quantity, **1** on all four previous sets) · landmine 8/8
clusters, one medoid per mate · **0** generated scenes missing a residue ·
λ=0 table-identity **bit-identical** across arms · expressible component at
ceiling 64/64 (so the specified growth control could not adjudicate; the frozen
arm carried it).

## The other proven claim, carried forward

**The first exactly-invertible testbed isolating pragmatic drift by
construction**, confirmed on **two independently built referent sets**, with the
mask guard 10× more live (0.5 % → 5.0 % rejects).

⛔ **Quote it only in the 13.1 ledger's wording, with the containment clause:**
*structural and semantic drift remain impossible on the **expressible**
component; semantic grounding is set membership — the denotation-set **contains**
the target; the residue is the designated, **contained** exception.* The
pre-13.0 wording is superseded on any residue-bearing set.

---

# 2 · ⛔ THREE LEVERS CLOSED WITH MECHANISM

Stated as bounds so reopening does not re-walk them.

### 2.1 Referent-set lever — **CLOSED**

`f₂` (ambiguity that *exists*) **anti-correlates** with the frontier-relevant
quantity (ambiguity that *survives an optimising speaker*). Four constructions —
archive, Cosmicomics v2, CR, TAO — all failed. CR/TAO cleared f₂ at 36.8 %/39.7 %
with the RSA frontier still **identically zero at every α**.
⛔ **Raising the steering statistic moves away from the target. Never steer a
referent set by f₂ again.**

### 2.2 Gloss auditor — **BOUNDED** (not closed; scope-limited)

**Omission-sensitive only:** 7.9 pts paired on total omission of all dependents.
**Structurally blind to superposition-pacts** — superposition rides alongside
intact description, so *nothing is removed for the auditor to miss*. It detects
the omission class, not the superposition class. Strongest constructible
omission-pact on that set: **0.8 pts**.

### 2.3 Metric-arm head — **CLOSED**

**The MLP head's reading is dominated by an arbitrary input-scale scalar, to a
magnitude exceeding the effect it was built to measure.** Control-arm headroom
swings **0 → 61 pts on identical geometry** purely with scale.

Three mechanisms, each measured and each excluded as a rescue:

1. **Entropy cannot fix between-referent separation.** Metric headroom **0.00 at
   every coefficient across a 100× range** (0.01→1.00), M pinned at chance.
   Entropy is a *per-referent* regulariser: it flattens each referent's
   distribution without making distributions **differ between** referents.
   *(And the incumbent was already 0.01 — this was never "add entropy".)*
2. **RMS-standardisation closed the ratio and killed the magnitude.** Both arms
   to RMS pairwise 1 ⇒ categorical hidden spread fell **8.7×** (3.244 → 0.372),
   into tanh's near-linear zone. **The control broke: 13/15 runs TOTAL COLLAPSE,
   no coefficient passing.** (Treatment likewise 13/15.)
3. **The old consistency check was invalid by construction** (D16): "one-hot into
   a linear layer is a row lookup" holds for a *single* linear layer; the trunk
   is `Linear→Tanh→Linear→Tanh→Linear`, so a one-hot selects a 32-dim
   **embedding** and everything above is **shared across all 24 referents**.

⇒ **The metric-vs-categorical question is not answerable with this
architecture.** It requires an instrument that is **scale-invariant by
construction**, not one standardised after the fact.

---

# 3 · ⏸ OPEN, WITH A SPECIFIED REOPENING CONDITION

> **Does metric structure make an inexpressible residue more conventionable than
> categorical noise?** — **NEVER TESTED.** Not falsified, not supported.

**Reopening condition:** a **scale-invariant-by-construction** policy
parameterisation. Reopen to test whether the pact-around-the-inexpressible (H2)
*replicates* under it, and only then whether metric structure adds anything.

⛔ **Walk straight to the new architecture. Do NOT re-walk:** the entropy sweep
(excluded, 100× range), post-hoc standardisation (excluded, breaks the control),
table-equality as a gate (invalid, D16), or f₂-steered referent sets (closed).

⭐ **The gate to carry forward is sound and reusable:** the **per-cell Bayes
ceiling** (`tlon/harness/ceiling.py`). It reads what the policy *does*, encodes
**no architectural assumption**, and refuses collapse and over-entropy for the
same arithmetic reason (both drive headroom to the floor). It is the one
instrument from this arc that survives the architecture change.

⛔ **Never quote `metric×head ≈ +0.13` from Part A as a result.** It was a
collapsed optimiser *and* an 8.3× input-scale confound; that cell was never
readable.
⛔ **Never write "two distillers agreed."** Per **D11** what exists is **one
human geometry plus one mechanical embedding**. Intersubjectivity remains
Mantel's job and the Mantel test has not run.

---

# 4 · THE ONE PAGE

| | |
|---|---|
| **PROVEN** | **H2** — a pact forms around the inexpressible: 33.3 % floor → 98.9 %, **+66.71 pts**, co-adaptation share **+52.25**. · The **first exactly-invertible testbed isolating pragmatic drift by construction**, two-set confirmed, quoted with the 13.1 containment clause. |
| **CLOSED (mechanism)** | Referent-set lever (f₂ anti-correlates; 4 sets) · Metric-arm head (scale dominates the effect; entropy and standardisation both excluded) |
| **BOUNDED** | Gloss auditor — omission-sensitive (7.9 pts), blind to superposition |
| **OPEN (condition)** | metric-vs-categorical — reopen **only** with a scale-invariant-by-construction instrument |
| **REUSABLE** | the Bayes-ceiling gate · the comparison guard · the standing selection + residue logs · the 24-referent lyric geometry (one distillation) |

**Spend: $0.00.** No pretrained model was ever in the loop; every kill arrived
closed-form or from local runs on the 5070 Ti.

---

# 5 · Artefact hygiene — closed this session

| | |
|---|---|
| `FROZEN ENTROPY COEFFICIENT` printed by the **diagnostic** path | ✅ fixed — diagnostic prints `SELECTS NOTHING` and forces `chosen=None` |
| unparameterised filename in the "wrote …" line | ✅ fixed |
| ambiguous `entropy_sweep_13_2.json` (pre-standardisation) | ✅ renamed `entropy_sweep_PRE_STANDARDISATION_random.json`, `standardised_input: false`, note recording what it is evidence *for* |
| a mean over 3 seeds passing on **one** | ✅ the sweep now flags any coefficient whose mean is carried by a minority of seeds; replayed against banked data it fires on exactly the two affected rows |
| all sweep JSONs self-describing | ✅ `arm`, `selects`, `standardised_input` |

Recorded in full as **D16–D21** in `docs/DEVIATIONS_13_2_2026_08_23.md`.
