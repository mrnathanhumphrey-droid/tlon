# KI-ATTRIBUTION — the Q2 "collapse" re-analysed. $0, no box.

**Question put to the re-analysis:** the Q2 finding said *"the substrate cannot
hold a flat prior on 3 of 4 uniform rows."* Is that a **substrate defect to fix**
(Reading A) or a **real finding about Tlön the typology missed** (Reading B)?

**Answer: neither.** It is one force, it is context-dependent, and every
context-free cause is refuted. The probe that was about to be built — a
two-stage *characterise the three collapse-targets, then fix the junk ones* —
would have been answering a question the data does not pose, because **the three
rows did not collapse to three targets. They collapsed to one.**

---

## 1 · The Q2 table was four separately-underpowered rows

`kä` was the load-bearing observation: the row that *didn't* collapse, taken as
the free clue that the collapse is content-structured rather than generic.
It does not survive pooling.

| | n | d_uniform | band | verdict |
|---|---|---|---|---|
| `kä` alone | 111 | 0.112 | 0.124 | fails to reject |
| **POOLED `ko`+`ku`+`kä`** | **319** | **0.137** | **0.074** | **REJECTS** |

Pairwise total variation between the four uniform rows:

```
ko vs kä  0.036      ka vs ku  0.110
ko vs ku  0.056      ka vs kä  0.131
ku vs kä  0.091      ka vs ko  0.157
```

`ko`, `ku` and `kä` **are one distribution.** `kä` did not resist the collapse —
it collapsed onto the identical target as its two twins and then failed to clear
its own band at n=111. The band moved, not the data.

⛔⛔ **A PER-ROW VERDICT TABLE CANNOT SAY THIS.** Every row was separately
underpowered, so the table could only report the sampling noise of its own
stratification. One of those four cells read as a finding.

## 2 · The collapse is one force, not three targets

```
POOLED ko+ku+kä          deviation from uniform
  ka  0.298                     +0.098
  ki  0.066                     -0.134   <--
  ko  0.197                     -0.003
  ku  0.216                     +0.016
  kä  0.223                     +0.023
```

Against the corpus the model actually saw, it is sharper still — the model
reproduces its training marginal on every force **except one**:

| | corpus (response share) | arena (realised) |
|---|---|---|
| `ka` | 0.3315 | 0.326 |
| `ko` | 0.1642 | 0.168 |
| `ku` | 0.1695 | 0.209 |
| `kä` | 0.1711 | 0.212 |
| **`ki`** | **0.1637** | **0.084** |

**The model will not ask.** That is the whole of Q2.

## 3 · The two hypotheses, and the asymmetry

| | claim | prediction |
|---|---|---|
| **H_prompt** (GLOBAL-FLAT) | the provocation's *"paint a scene that holds together on its own"* suppresses interrogatives | a system prompt is present on **every** turn ⇒ its effect **cannot** depend on context |
| **H_forced** (KA-COUPLED) | the single forced cell `ki→ka` built a ki/ka coupling | suppression **varies** with the prior force |
| **H_substrate** | the base model / Tlön conditioning will not ask, regardless | global by construction — same shape as H_prompt |

⭐ **The logic is asymmetric and the tool does not overclaim it.** Global-flat is
the falsifiable one. Refuting it does **not** confirm H_forced, because *"assert,
then question the assertion"* is an ordinary discourse move that is also
prior-conditional. Verdicts read `GLOBAL-FLAT REFUTED`, never `H_forced
CONFIRMED`.

## 4 · Results — `tools/act2_ki_attribution.py`

### TEST A · substrate baseline — ⛔ VOID, and that is a result

Attributing the suppression to the substrate needs run 3 generating freely.
**Every candidate on disk fails a stated precondition:**

- `harden/exchange_probe.json` — **DEGENERATE**: 7 distinct surfaces in 40 turns,
  TTR 0.125, cycle period 1, validity 0.45. Every round-tripping surface reads
  force `ki` — 18/18 and 25/25 — **because the seed history ends in `ki`**. Its
  force marginal would have been a spectacular and completely false baseline
  ("run 3 asks 100 % of the time"). The distinct-ratio gate is what caught it,
  and that gate now runs on our own arms too.
- `arm3_run3_w1_*.json` — illegal force `"u"`, validity 0.000 (diagnosed prior).
- `temp_floor_depth3.json` — counts only, no surfaces retained.
- flocal / speak_recon generations — the force is fixed by the **English
  prompt**, so the model never chose it. Void for a force-*preference* question.

### TEST B · ka-coupling — ⚠️ POST-HOC (discovery sample)

```
P(ki | prior=ka)                = 25/181 = 0.1381
P(ki | prior in [ko,ku,kä])     = 21/319 = 0.0658
permutation p (prior labels shuffled within uniform rows, 20 000 trials) = 0.00945
MDE at 80 % power, declared from n:  0.0800      observed |Δ| = 0.0723
⇒ GLOBAL-FLAT REFUTED
```

⚠️ **The observed effect sits below the declared MDE.** A permutation test and a
crude two-proportion power sweep are different statistics, so this is not a
contradiction — but it does mean the sample is at the edge of its resolution.
**Direction is supported; magnitude is not pinned.**

⚠️⚠️ **POST-HOC.** The 0.138-vs-0.066 contrast was *seen* during the re-analysis
that motivated the tool. No split of these same 546 transitions can launder that.
TEST C is what keeps it honest.

### TEST C · cross-exchange consistency — ✅ FAILABLE, PASSED

Pre-declared bar: ≥ 10/14 exchanges in the same direction. **Observed 12/14
(85.7 %).** An effect carried by one or two of fourteen independent exchanges is
a fluke wearing a p-value; this one is not.

### TEST D · held-out replication — ⛔ UNDERPOWERED **BY CONSTRUCTION**

```
MDE DECLARED BEFORE READING: 0.4800 at n=(9,16). The arm2 effect is 0.0723.
P(ki|ka) = 2/9    P(ki|other) = 8/16    direction DIFFERS
```

⭐ **The MDE was computed and printed before the rates were read**, precisely so
this arm's disagreement could not be mistaken for a refutation. It cannot detect
an effect of the size arm2 shows. **A null — or a reversal — here means nothing.**

### TEST E · window dependence — ⭐⭐ NOT IN THE SPEC, and the strongest result

Fell out of TEST D. arm1 and arm2 differ in **exactly one thing**: the history
window. Same weights, same provocation, same temperature, same 40 turns.

```
arm2 (window=1, 14 exchanges):  mean 0.0965  sd 0.0747  range [0.000, 0.258]
arm1 (accumulating, 1 exchange):        10/25 = 0.4000
⇒ +4.1 SD from the arm2 mean, and OUTSIDE the full observed range of all 14
   binomial P(X ≥ 10 | n=25, p=0.092) = 3.86e-05
```

⚠️ **POST-HOC and SINGLE-EXCHANGE.** arm1 is n=1, so its between-exchange
variance is unmeasured. The bar used is therefore a **range test**, not a
p-value — a p-value alone ignores the clustering and overstates it.

⭐⭐ **THE PROMPT IS IDENTICAL IN BOTH ARMS.** A cause that does not vary with
context cannot produce a 4× swing in `ki`-emission. **Every context-free cause is
refuted — which covers H_prompt AND the simple form of H_substrate**, since both
are global by construction. TEST A being void matters far less than expected: it
was only ever needed to test a *global* substrate story, and that story is dead
by a different route.

### CONFOUND · is `ki` simply harder to emit?

Target-surface length by force, in the corpus the model saw:

```
ka  n=5157  mean 28.5      ku  n=2643  mean 28.7
ki  n=2542  mean 29.0      kä  n=2670  mean 28.5
ko  n=2561  mean 29.4
```

`ki` is neither longer nor rarer than its peers. **"Harder to emit" is not
carrying the suppression.** And no turn was ever dropped: n = 546 = 14 × 39
exactly, and `exchange()` has no retry loop — it samples once, records
`valid: False`, and moves on. **Nothing was filtered or resampled.**

## 5 · What survives, and what it does to the original fork

**Surviving explanation:** a cause that depends on **the prior force** and on
**the serving window** — which is the shape of a *learned transition structure*,
not a prior and not a prompt.

The mechanism that fits every number: the corpus's rows are *exactly* depth-1
(`prompt = prev.surface`, `target = cur.surface`), and `ki` is **the only force
whose prompt-position identity fully determines the target** — every `ki`-prompt
row has target `ka`. That gives `ki` a strong *"I am the thing being answered"*
signature. A model carrying that would under-emit `ki` **as its own output**, and
would relax that specifically after `ka` — the forced cell's other endpoint.
Both are observed.

It also explains the window result: **arm2 (window=1) is the *matched* serving
condition** — the model was trained on exactly one prior surface — while arm1
(accumulating) is out-of-distribution, and the learned transition structure
stops dominating.

⇒ **Reading A is wrong** — the model holds its training marginal on 4 of 5
forces. It has no trouble with distributions, so a uniformity-enforcer would be
treating a symptom that isn't there.

⇒ **Reading B is wrong** — the undetermined cells are *interchangeable*
(pairwise TV 0.036–0.091). There is no per-cell convention to harvest, so
amending the force map to encode "discovered structure" would be encoding noise.

⇒ **It is our own design.** One forced cell, pointing one way, in an otherwise
uniform map, is enough to bend the marginal of its source force by half. The fix
belongs in the map/corpus, not in the substrate and not in the typology.

## 6 · OPEN

1. **The mechanism above is the surviving hypothesis, not a confirmed one.**
   Refuting global-flat does not confirm it. The sharp test is a design change: a
   map with **zero** forced cells, or with forced cells that do **not** all point
   at one target, should show no `ki`-suppression. That is a corpus rebuild plus
   a train — **a box**, and the first thing on it.
2. **Magnitude is not pinned** (observed |Δ| below the declared MDE). More
   exchanges at window=1 would settle it and cost almost nothing on a box that
   is up for (1).
3. **`ki`-emission at 0.40 under accumulation is itself unexplained** and is
   *above* the corpus's 0.164, not merely un-suppressed. Single exchange. Worth
   more than one arm next time.
4. ⛔ **Q2's headline in `RESULTS_MULTITURN_LOCALITY_2026_08_26.md` is superseded
   by this file** — "the substrate cannot hold a flat prior" is not what the data
   shows, and RULING 12's emergent-convention measurement is **not** blocked on a
   substrate fix. It is blocked on the map design, which is ours to change.
