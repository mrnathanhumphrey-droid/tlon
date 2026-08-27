# PREREG — the `ki`-as-target mechanism probe

**Locked 2026-08-26, BEFORE any treatment corpus is generated and BEFORE the box
comes up.** Everything below — the primary measure, the required N, the MDE, the
stratification, the readings, the fallbacks — is fixed at this commit. Changes
after this point are amendments and must be labelled as such.

⭐⭐ **THIS IS THE CONFIRMING TEST, AND THAT IS THE WHOLE POINT.** Limit #3 of the
last analysis was that Test B was **post-hoc** — the `.138`-vs-`.066` contrast was
seen before the tool was built. No split of that data could launder it. This
probe fixes that by locking the prediction before the data exists.

---

## 1 · THE CLAIM UNDER TEST

The surviving mechanism from `KI_ATTRIBUTION_2026_08_26.md`, which is
**REFUTED-ALTERNATIVES, not CONFIRMED**:

> `ki` is the only force whose prompt-position identity fully determines its
> target — every `ki`-prompt row has target `ka`. That gives it an *"I am the
> thing being answered, never the thing answered"* asymmetry, and a model
> carrying it under-emits `ki` as its own output.

**THE TEST:** make `ki` a **target** as well as a source. If the asymmetry causes
the suppression, adding a forced cell where `ki` is the *response* should relieve
it. If suppression persists, the asymmetry mechanism is wrong.

## 2 · THE STIPULATION — explicit, labelled, and guarded in code

One second cell of the form `X → ki`, so `ki` becomes a target.

**`STIPULATED_KI_TARGET_v1` = { `ki`→`ka`, `ko`→`ki` }**

⛔⛔ **NOT DERIVED. NOT CLAIMED FORCED. NOT A MAP PROPOSAL. DISCARDED AFTER THE
PROBE REGARDLESS OF OUTCOME.** The forced-map derivation — whether any second
cell is genuinely forced — is separate, deferred work.

⭐ **The caveat is a FIELD, not a comment.** `ForceMap.stipulated` is a real
attribute and `assert_derived(use)` raises `StipulationLeak` at every non-probe
site. [caveat_in_name]: prose beside a value decays; a guard that raises does
not. The failure this prevents is not a crash — it is a stipulated cell quietly
becoming "the map" three sessions from now because it was in a corpus once.

### Why `ko`, and what was ruled out

| candidate | ruling |
|---|---|
| `ka` | ⛔ `ki`→`ka` already exists, so `ka`→`ki` closes a **2-cycle** and confounds asymmetry-relief with cycle-formation |
| `ki` | ⛔ its row is already forced to `ka`; a source cannot have two forced targets, and `ki`→`ki` absorbs |
| **`ko`** | ✅ **CHOSEN.** `ki`-emission at the observed floor (0.054, vs `ku` 0.052, `kä` 0.090) so relief has maximum headroom. Of the two floor candidates it has the **smaller prior count** (92 vs 116) — the conservative pick, removing less data from the stratum the primary measure lives on |
| `ku` | ⏸ **HELD AS THE PRE-NAMED REPLICATION.** Named here, before the run, so a later `ku` probe is a replication and not a second bite at the apple |

## 3 · ⛔⛔ THE CONFOUND THAT WOULD HAVE MANUFACTURED A CLEAN CONFIRMATION

**The obvious measure — the global `ki` marginal — measures the stipulation
itself.** Forcing `ko`→`ki` means `ko` emits `ki` **100 % of the time by
construction**. The global marginal therefore rises in the treatment arm whether
or not one atom of suppression was relieved, and it would look exactly like the
result we are hoping for.

⇒ **PRIMARY MEASURE: `P(ki | prior ∈ COMMON_UNIFORM_ROWS)` where
`COMMON_UNIFORM_ROWS = {ka, ku, kä}`** — the rows uniform in **both** maps.

Clean for a second reason: those rows are uniform in both maps, so their **corpus
expectation is 0.20 in both arms.** Same rows, same expectation, only the map
differs. The stipulated row `ko` is **excluded** from the primary measure; it is
a design zero in the treatment arm.

| | baseline | treatment |
|---|---|---|
| forced cells | `ki`→`ka` | `ki`→`ka`, `ko`→`ki` |
| uniform rows | ka, ko, ku, kä | ka, ku, kä |
| **common stratum** | **ka, ku, kä** | **ka, ku, kä** |
| corpus expectation on stratum | 0.20 | 0.20 |
| stationary | ka .333 ki .167 ko .167 ku .167 kä .167 | ka .375 ki .250 ko .125 ku .125 kä .125 |
| separation | 0.2222 | 0.3906 |

## 4 · MEASURED BASELINE, AND THE EFFECT SIZE TO BEAT

From the 14 committed baseline exchanges (`runs/act2/logs/mt_run/arm2_*.json`):

```
P(ki | prior ∈ {ka,ku,kä}) = 41/408 = 0.1005
common-stratum transitions per exchange: 29.1   (at 40 turns)
FULL relief would move it to 0.2000 — a shift of +0.0995
```

⚠️ **Two different numbers, named apart so they cannot be swapped**
([caveat_in_name]): the **global** `ki` marginal is **0.084**; the
**common-stratum** rate is **0.1005**. The primary measure is the
common-stratum one. The reproduction check tests both.

## 5 · POWER — declared before the box (limit #2 paid down)

⛔⛔ **TRANSITIONS ARE CLUSTERED WITHIN EXCHANGE AND THE NAÏVE CALCULATION
PRETENDS THEY ARE NOT.** Measured per-exchange rates last run ran **0.000 to
0.259, sd 0.0689**. The unit of independence is the **exchange**, so power is
computed by resampling whole exchanges and testing exchange-level means.

```
   Δ      naïve-indep     CLUSTERED (governs)    overstatement
  0.10       8 exch            15 exch               1.9×
  0.08      11 exch            23 exch               2.1×
  0.06      19 exch            38 exch               2.0×
  0.04      38 exch            82 exch               2.2×   <- TARGET
  0.03      66 exch           143 exch               2.2×
  0.02     143 exch           317 exch               2.2×
```

⭐⭐ **DECLARED: 82 exchanges per arm, 40 turns ⇒ MDE 0.040.**

Sizing on the naïve 38 would have **reproduced last run's failure one level
down** — a declared MDE the run cannot actually reach.

**Why 0.040 and not 0.060** (which would cost 38/arm): full relief is ≈ +0.0995,
so 0.060 resolves only the full-relief branch. **PARTIAL RELIEF is a
pre-declared branch** and at MDE 0.060 a genuine +0.05 relief would read
UNDERPOWERED. Pinning magnitude was limit #2; 0.040 is what pins it.

### ⛔ PRE-COMMITTED FALLBACK (declared now, not chosen after seeing data)

Inference throughput is **unknown** — the mt_run pipeline log was never pulled
before that box was terminated, so there is no defensible on-record estimate and
none is invented here. ⇒ **Throughput is a MEASURED GATE on the box**: time the
first 3 exchanges, project the full 164, and print it.

- projected inference ≤ 4 h → **run the declared 82/arm**
- projected inference > 4 h → **fall back to 38/arm, MDE 0.060**, and the
  verdict language changes with it: only FULL relief is resolvable, PARTIAL
  becomes UNDERPOWERED by declaration.

Both branches are fixed here. Choosing between them after seeing the *relief*
would be optional stopping; choosing on *throughput* is not, because throughput
is independent of the outcome.

## 6 · ARMS

| arm | weights | map | purpose | cost |
|---|---|---|---|---|
| **B-fresh** | trained | `DERIVED_v1` | ⛔ the control. **Must reproduce the known suppression before the treatment arm is read** | train + 82 exch |
| **T** | trained | `STIPULATED_KI_TARGET_v1` | ⭐ the test | train + 82 exch |
| **B-prior** | `adapter_mt` (existing) | `DERIVED_v1` | ⭐⭐ **run-to-run variance control** — same map, different training run | 14 exch, **no training** |

⭐ **B-prior is an addition to the spec'd design and it is nearly free.** B-fresh
and T share a corpus seed and differ **only in the map**, which is the clean
single-variable contrast. But two training runs are never identical, and without
B-prior the size of run-to-run noise on the *same* map is assumed rather than
measured. **B-fresh vs B-prior measures exactly that**, inference-only.
⚠️ B-prior was trained at an earlier commit, so it is a *conservative upper
bound* on run-to-run noise, not a pure seed contrast.

## 7 · PRE-DECLARED READINGS — locked, all branches

Read on the **common stratum**, B-fresh vs T, exchange-level means:

- **Relief ≥ MDE and reaches ≈ 0.20** → ⭐ **ASYMMETRY MECHANISM CONFIRMED.**
  Limit #1 paid down. The map-design constraint is known and real: *forced cells
  must not create source-only forces.* Arena design proceeds under it.
- **Relief < MDE, T ≈ 0.1005 unchanged** → ⛔ **ASYMMETRY MECHANISM REFUTED.**
  Pre-named alternatives: `ki`'s **content** (questions intrinsically harder to
  emit well), or **forced-cell determinism itself** regardless of direction.
  Re-open the mechanism; do **not** proceed to arena assuming asymmetry.
- **Relief ≥ MDE but short of 0.20** → **PARTIAL.** Asymmetry is *a* cause, not
  *the* cause. Report magnitude, name the residual, do not over-claim.
- **Relief below MDE** → ⛔ **UNDERPOWERED**, never "no relief." Locked.
- ⛔⛔ **B-fresh fails the reproduction check** → **the instrument is suspect and
  the treatment arm is NOT READ.** Halt and diagnose.
- ⛔ **|B-fresh − B-prior| exceeds the B-fresh−T difference** → run-to-run noise
  dominates the effect; the contrast is uninterpretable regardless of direction.

### Declared NEUTRAL in advance

**Force-fidelity will differ between arms and that is EXPECTED, not evidence.**
Separation is 0.2222 baseline vs 0.3906 treatment — the treatment map is simply
more learnable. A fidelity gain in T is predicted by the map's geometry and says
nothing about relief.

⚠️ **I broke my last neutrality declaration** (render/speak, pre-declared neutral,
moved +14.1 points). So this one is stated with its escape clause: if fidelity
moves in a direction or magnitude the separation difference does **not** explain,
that is flagged as an unexpected observation — **not** promoted to a primary
reading.

### Stratification — the mechanism is tested where it is predicted

Per-prior-force `ki`-emission is reported for every row in both arms, not only
the pooled stratum. The relief prediction is directional, and a pooled number can
hide a row moving the wrong way.

## 8 · CARRIED DISCIPLINE — non-negotiable, all from prior burns

- **Token-match gate FIRST.** Training starts only if both corpora match on
  compute at 2 % — against each other **and** against run 3. Counted by
  `act2_token_budget.py`, which imports the trainer's own `row_to_text`; **no
  second counter** (the self-confirming-counter shape, shipped twice).
- **Compute is the held variable; rows are the dial.** 0.5-by-rows was
  0.737-by-compute last time.
- **Seq cap checked, truncation pruned-and-logged**, one `SEQ` shell variable
  used at gate and trainer sites, verified by **counting** the sites.
- **VRAM measured against anchors with the WORST observed planner factor**, never
  an averaged constant (it ranged ×0.955–×1.253 and sign-flipped).
- **Raw dump on parse failure. No `tail -N` on attribution-relevant output** —
  that decapitated a traceback last run.
- **Both raw arms committed alongside any summary JSON.** No summary in the repo
  without its run behind it (fixed at `ba82a4c`; do not regress).
- **Degeneracy tripwire + force-fidelity gate carried**, per-map bands simulated
  at observed row sizes.
- **Pull-and-kill at DONE. Zero analysis on a live box.** Checkpoints survive
  until their diagnostics bank. ⭐ **Pull the pipeline log this time** — its
  absence is why §5's throughput had to become a gate.

## 9 · WHAT THIS PROBE DOES NOT DO

It does **not** claim the stipulated cell is forced. It does **not** propose the
final map. It does **not** touch the σ_cp arena (downstream, gated on this
result). It does **not** build the forced-map derivation (deferred). **It
produces no drift number** — there is still no drift measurement in this project
and this run does not create one. It unblocks the map-design question that gates
the arena.

---

**Locked before any treatment corpus exists.** The hash of this file at commit
time is the pre-registration; any later edit is an amendment and says so.
