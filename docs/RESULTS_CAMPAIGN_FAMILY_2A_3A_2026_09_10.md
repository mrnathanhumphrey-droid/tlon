# RESULTS — family matrix, runs 2a and 3a

**PREREG** `PREREG_CAMPAIGN_FAMILY_MATRIX_2026_09_09.md`, LOCK **`91956dbe`**,
re-locked **`5f4a554c`** by AMENDMENT A before 3a fired.

| run | base | rung | outcome |
|---|---|---|---|
| **2a** | Olmo-3-7B-Instruct | layer, top-16 of 32 | ⛔ **NOT ESTABLISHED** — F-LOCAL fired |
| **3a** | Mistral-7B-Instruct-v0.3 | layer, top-16 of 32 | ⛔ **INSTRUMENT FAULT** — not a base verdict |

⛔⛔ **The family axis is still UN-RUN.** One base is out on a real verdict; the
other's run was destroyed by a harness bug. Neither produced a release datapoint.

---

## 1 · Run 2a — OLMo is NOT ESTABLISHED, and the gate is why we know

`olmo16-s20624` · H100 PCIe us-west-3 · pinned `b6bfd46` · ~115 min · **~$6.30**.

**It trained perfectly.**

```
scope   top 16 of 32, 3,238,264,832 trainable / 4,059,746,304 frozen
dose    rms 3.1183e-04   vs Qwen rung 1a's 3.1180e-04   = 100.0% MATCHED
lag z   +23.38   +8.89   +1.71   +0.99
n_pairs    108      96      84      72      <- every cell resolvable
chains  12 used / 0 dropped · 120 turns
```

⭐ The dose landing at **100.0%** of Qwen's rung 1a per-parameter is coincidence,
and it makes this the tightest cross-family comparison the campaign could have
asked for. Perceive holds at **+23.38**, the same magnitude as Qwen's 23–24.

### ⛔⛔ And its release number is MEANINGLESS, which is the point

```
speak   100.0%  (64/64)     free generation
render   51.6%  (33/64)     directed production, threshold 0.90
choose   37.1%              comprehension, in band
F-LOCAL FIRED
```

**OLMo produces free-form legal Tlön at 100% and renders an imposed meaning only
51.6% of the time.** Not "hears but cannot speak" — it **speaks fluently and
cannot translate on demand**. The class system holds when OLMo chooses what to
say and breaks when the meaning comes from outside.

⛔ So lag2 **+8.89** — release failing *worse* than Qwen's 5.785/5.966 — is not a
release result. Measuring release requires faithful production *in response to a
provocation*, which is directed production, the exact thing OLMo fails. The
number conflates release-failure with render-failure and cannot separate them.

⭐ **THE GATE'S PLACEMENT IS WHAT MAKES THIS A BASE VERDICT.** §2 puts speakerhood
at the LAYER rung — the *forgiving* config, the one Qwen clears — precisely
because one run cannot distinguish "this base cannot speak Tlön" from "this
config breaks this base". OLMo failed at the forgiving rung, at matched dose, on
a config Qwen clears. That is a fact about the base.

⭐ Had the gate not existed, 2a would have entered the matrix as *cross-family
confirmation that release does not install, and worse than Qwen* — a false
datapoint from a non-speaker, on the first base the gate was ever applied to.

### A separate finding, filed on its own terms

**Faithful directed Tlön production is substrate-dependent across capable 7B
families at matched config and matched dose.** Qwen clears both axes; OLMo
clears free generation at 100% and fails directed rendering at 51.6%. Whether a
model can *become* a native speaker of the nounless language is not given by
capability or scale.

⚠️ It rhymes with the Qwen mapping finding — both point at the meaning↔form
mapping as the fragile locus — but they are two observations, not one. Recorded
as a rhyme, not a claim.

---

## 2 · Run 3a — an INSTRUMENT FAULT, and the cause is this campaign's own thesis

`mis16-s20624` · H100 PCIe us-west-3 · pinned `2d202ad` · ~100 min · **~$6**.

```
speak    0.0%  (0/64)
render   1.6%  (1/64)
choose   0.0%  (0/256), 256 unanswered
⛔⛔ DIVERSITY GUARD REFUSED TO SCORE — 1 distinct output for 12 DIFFERENT inputs
F-LOCAL: UNSCOREABLE (degenerate), NOT "fired"
lag_epoch1: every chain refused before turn 3
```

⭐ **The weights were fine.** `weight_delta.json`: verdict **OK**,
`fraction_changed` **0.99995**, `delta_norm` **18.697** over 3,489,792,000 →
rms **3.166e-04**, against Qwen's 3.118e-04. Training worked. **Stopping** was
destroyed.

### The mechanism, verified rather than asserted

```
Qwen2.5-7B       pad <|endoftext|> (151643)  !=  eos <|im_end|>    (151645)
Olmo-3-7B        pad <|pad|>       (100277)  !=  eos <|endoftext|> (100257)
Mistral-7B-v0.3  pad None  ->  act2_finetune.py:556 sets pad = eos = </s> (2)
```

`DataCollatorForLanguageModeling` masks labels **by token id**. When pad *is*
eos it masks every genuine end-of-sequence as well. Confirmed on CPU against
both tokenizers:

```
Olmo-3-7B        label at the REAL eos = 100257   trained to stop normally
Mistral-7B-v0.3  label at the REAL eos =   -100   NEVER TRAINED TO STOP
```

So the model generated to `max_new_tokens` with no stop, nothing parsed as the
schema, and the diversity guard saw one degenerate output for twelve inputs.

⛔⛔ **`if tok.pad_token is None: tok.pad_token = tok.eos_token` WAS WRITTEN WHEN
QWEN WAS THE ONLY BASE.** Qwen has a distinct pad token, so the line never fired
in the entire arc. **A held constant became a variable and nothing said so** —
which is the exact thesis of the campaign this harness was running, reproduced
one level down inside the harness itself.

⭐ **OLMo's verdict is unaffected and that was checked, not assumed**: it has a
distinct pad token, so 2a never hit this path.

### The fix

Mask labels by **position** (`attention_mask == 0`), never by token id. Correct
for every base, and it leaves Qwen's and OLMo's runs comparable because neither
was ever affected.

⛔ **3a must be RE-RUN. It is not a Mistral verdict and must never be recorded
as one.**

---

## 3 · What the matrix says now

| cell | state |
|---|---|
| Qwen layers | release does not install (incumbent, unchanged) |
| Qwen mapping | untouchable at 1e-5 and 5e-6 (incumbent, unchanged) |
| OLMo layers | ⛔ NOT ESTABLISHED — cannot render faithfully |
| OLMo mapping | not fired; cell EMPTY, never a collapse |
| Mistral layers | ⛔ INSTRUMENT FAULT — re-run pending |
| Mistral mapping | gated on 3a |

⛔ **Zero cross-family release datapoints so far.** The "Qwen fact or LLM fact"
question is open and now rests entirely on Mistral's re-run: if it clears
F-LOCAL, the family axis gets its one datapoint on the live locus. If it fails
the way OLMo did, faithful Tlön-speakerhood is *rare* across families, the
release finding is Qwen-establishable-only, and OLMo-recovery becomes the live
path to any second datapoint.

⚠️ **The mapping locus is not the same size across the matrix** (5f4a554c §4.1):
Qwen 1,089,994,752 · OLMo 821,477,376 · Mistral 268,435,456 — Mistral's is
**4.1× smaller**, driven by vocabulary (32,768 vs 152,064). The read stays valid
because it is verdict-vs-verdict and ruler-free, but a cross-family mapping
result is a claim about the LOCUS, never about a matched parameter budget.

---

## 4 · ⛔ What these runs do NOT establish

- ⛔ Nothing about Mistral. 3a measured the harness, not the base.
- ⛔ OLMo's +8.89 is **not** a release datapoint and must not be pooled as one.
- ⛔ Neither run touches the Qwen findings, the capacity floor, or D6.
- ⛔ No threshold changed. `Z_LAG1_MIN` 6.0 / `Z_LAGN_MAX` 3.0 imported unchanged.
