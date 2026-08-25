# PREREG — the `aspect_root` outlier. LOCKED BEFORE RUN 4's RESULT.

**2026-08-25, written while the instance boots and before any run-4 number
exists.** Nate's instruction: *"Do NOT let the retrain 'fix' it and call it
explained... record aspect_root's result as measured-against-prediction, not as
closed. The question stays open unless the data separates the mechanisms."*

## The observation

At n=256, run 3, `aspect_root` is an outlier **even among the rare slots**:

| slot | occupancy | errors | errors per point of occupancy |
|---|---|---|---|
| **`aspect_root`** | **3.9 %** | **16** | **4.1** |
| `quant` | 3.9 % | 5 | 1.3 |
| `degree` | 3.9 % | 2 | 0.5 |
| `modal` | 6.4 % | 11 | 1.7 |
| `tense` | 5.1 % | 3 | 0.6 |

Same occupancy as `quant` and `degree`; **3.2× and 8× their error count.**

## The two candidate mechanisms — NEITHER is currently separated

- **H-REDUP** — `aspect_root` is the only **two-field** slot (`aspect_root` +
  `aspect_reps`) and the only one whose surface is a **reduplication**
  (`tes` → `testesas`) rather than the bare morpheme. Structural difficulty.
- **H-COLLIDE** — **Q and A collide in English.** `nol` "oft" (Q) was placed in
  the aspect slot **4×**, where the wanted form is `sor` "habitual" (A). The two
  classes carve up repetition/frequency differently from English.

## The prediction, fixed now

Run 4 floors all five modifier slots to ~30 % occupancy. If **slot rarity alone**
is the mechanism, every floored slot should improve by a common factor.

1. Estimate `k` = fractional error reduction across the floored **non-aspect**
   slots (`modal`, `tense`, `quant`, `degree`), pooled. **`aspect_root` is held
   out of the fit**, so its prediction is out-of-sample.
2. **PREDICTED** `aspect_root` errors ≈ `16 × (1 − k)`.
3. **Reading, pre-declared:**
   - observed **≈ predicted** ⇒ slot-rarity was sufficient; **H-REDUP and
     H-COLLIDE both STAY OPEN.** Nothing is closed.
   - observed **well below** predicted ⇒ something aspect-specific worked, which
     is evidence *for* H-COLLIDE, since the minimal pairs isolate exactly the
     Q-vs-A distinction.
   - observed **above** predicted ⇒ aspect resisted the fix; H-REDUP gains
     support, because structural difficulty would survive an occupancy increase.

⭐ **THE CONFOUND THAT ISN'T ONE.** "Aspect improved more because the contrastive
pairs favoured it" is ruled out in advance by the mined boundary counts:
**M receives 21 units of contrastive attention and A receives 16.** `modal` gets
*more* help than `aspect_root`, not less. So aspect outperforming modal cannot be
explained by preferential targeting.

## ⛔⛔ THE HONEST PART: THIS TEST IS UNDERPOWERED AND THAT IS DECLARED NOW

Poisson sd on the baseline counts:

| slot | errors | sd | smallest change that is not noise |
|---|---|---|---|
| `aspect_root` | 16 | 4.0 | ~8 |
| `modal` | 11 | 3.3 | ~7 |
| `quant` | 5 | 2.2 | ~4 |
| `tense` | 3 | 1.7 | ~3 |
| `degree` | 2 | 1.4 | ~3 |

**`quant`, `tense` and `degree` carry 5, 3 and 2 errors. They cannot show
anything.** `k` will therefore be estimated almost entirely from `modal`
(n=11, sd 3.3), against `aspect_root` (n=16, sd 4.0).

⛔ **This is §5.2's uninformative-cell rule, applied to my own test before it
runs: a cell whose headroom is below the MDE may not contribute to a verdict.**
A "no difference" outcome here means **UNDERPOWERED**, not "the mechanism is
absent" — and it must be written up with that word.

## The observable that IS informative at this N

The **composition** of the residual `aspect_root` errors is categorical, and
does not need large counts to be read:

- **H-COLLIDE predicts** the `Q → A` errors specifically vanish (the minimal
  pairs put `nol`/`sor` side by side) while `R → A`, `T → A`, `M → A` persist in
  proportion.
- **H-REDUP predicts** residual aspect errors persist **across all source
  classes** roughly uniformly, because the difficulty is the slot's shape rather
  than any one neighbouring class. It further predicts `aspect_reps` — the
  second field — remains a source of refusals.

⛔ `aspect_reps` is an **integer**, not a form, so it produces no `class_error`
row. It appears only in the refusal `reason` string. **Count it separately from
the reason buckets**; a mechanism test that can only see the field the miner
happens to walk is a test shaped by its instrument.

## What a properly powered version would cost

A count-based test needs ~4× the errors to halve the relative noise ⇒ **n≈1024**
rather than 256. On the run-3 gate's measured rate that is roughly **4× the gate
time (~$1–2 more)**. ⭐ **Not spent now, and named so it is a decision rather
than an omission.**

## Locked

Nothing below this line may be edited after run 4's numbers land; corrections go
to `DEVIATIONS_ACT2_2026_08_24.md`.

- baseline: `aspect_root` **16**, `modal` **11**, `quant` **5**, `tense` **3**,
  `degree` **2** — of 48 class errors, n=256, battery `8d21aa635d5729fd`
- run-4 corpus: `train.jsonl` sha256 `7ee9c98a…`, 63,603 rows, 9,527,752 tokens
- contrastive attention: M 21 · R 19 · **A 16** · Q 11 · L 10 · O 9 · T 6 · D 3
