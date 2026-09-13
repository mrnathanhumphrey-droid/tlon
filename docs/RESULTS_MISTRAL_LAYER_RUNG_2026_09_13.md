# RESULTS — the family axis has its first clean datapoint

**Run 3a, attempt 4** · cell `mis16d-s20624` · `mistralai/Mistral-7B-Instruct-v0.3`
**PREREG** `PREREG_CAMPAIGN_FAMILY_MATRIX_2026_09_09.md`, re-locked **`5f4a554c`**
H100 PCIe · us-west-3 (Utah) · pinned `e533851` · 6,049 s · **~$5.53**

⭐⭐ **A SECOND FAMILY, A FAITHFUL SPEAKER, DOSE-MATCHED TO 99.1 % — AND RELEASE
STILL DOES NOT INSTALL.** Every prior Mistral attempt measured the harness. This
one measured the base.

---

## 1 · The numbers, from the persisted artifacts

```
F-LOCAL          speak  100.0 %  (64/64)      threshold 0.90
                 render  93.8 %  (60/64)
                 diversity  12/12 distinct · repeat 1.00 · response 1.00
                            · dependence +1.00  =>  input-dependent
                 F-LOCAL CLEAR
lag z            1: +18.931   2: +3.972   3: -0.966   4: -0.619
n_pairs               108        96          84          72
resolving_power       69.3       70.6        68.3        57.8
chains           12/12 used, 0 dropped · 120 turns · seed 20624
                 sampling_stream_seeded: TRUE
dose             rms 3.0915e-04  vs rung 1a's 3.1180e-04  =  99.1 % MATCHED
delta            OK · fraction_changed 0.9999457
VERDICT          STOP — floored (b):  release FAIL · perceive PASS · f_local PASS
```

## 2 · The cross-family comparison

| | base | rung | dose (rms) | lag2 z | faithful speaker? |
|---|---|---|---|---|---|
| Qwen 1a | Qwen2.5-7B-Instruct | 14 of 28 | 3.1182e-04 | **+5.785** | yes |
| **Mistral 4** | **Mistral-7B-Instruct-v0.3** | **16 of 32** | **3.0915e-04** | **+3.972** | **yes** |
| OLMo 2a | Olmo-3-7B-Instruct | 16 of 32 | 3.1183e-04 | +8.89 | ⛔ no — F-LOCAL fired |

Both entered rows are top-half, LR 1e-5, dose-matched, and cleared the
speakerhood gate. Both are floored at lag 2 above the 3.00 ceiling.
⭐ **Installation-resistance replicates across families. n=1 → n=2.**

⭐ **Perceive installs on Mistral too** — lag1 **+18.93** against a 6.0 floor. The
fine-tune puts the *perception* half in on every base tried; the failure is
specific to **release**, which is the whole point of the split.

⚠️ **AND THE MARGIN DIFFERS, WHICH IS NOT NOTHING.** Mistral's +3.97 sits much
closer to the 3.00 ceiling than Qwen's +5.785. Both FAIL — the verdict is
identical — but Mistral is the base nearest to clearing, which makes **its
mapping rung more interesting than Qwen's was, not less**. Recorded as an
observation on one run, not as a trend.

## 3 · ⛔ What this does NOT establish

⛔ **NOT YET A SUBSTRATE FINDING**, and the verdict artifact says so itself:
*"§7.1's escalation ladder must be exhausted first (more layers, then
embeddings, then the wall)."* For Mistral **only the layer rung has run**;
Qwen's ladder went further (mapping at 1e-5 **and** 5e-6). The claim is
*at the matched layer rung, a second family also fails to install release* —
never *Mistral cannot learn it*.

⛔ **`choose` is UNSCOREABLE — 0.0 %, 256/256 unanswered.** The harness refuses
it correctly: *"An EMISSION failure, not a comprehension reading; the band does
not apply and the number is not a result."* ⚠️ It was **unchanged by the
chat-template repair**, so it has a separate cause and is OPEN. `choose` accepts
either JSON **or** a bare index (`_bare_index`), so "neither parsed, 256 times"
points at emission format rather than comprehension — the same shape as the
stray-brace finding. Diagnose from the ledger raws before it is called anything
about Mistral.

⛔ Nothing here touches the Qwen findings, the capacity floor, or D6.
⛔ No threshold moved. `Z_LAG1_MIN` 6.0 / `Z_LAGN_MAX` 3.0 imported unchanged.

## 4 · ⭐⭐ Why the previous three attempts were not this

| attempt | cell | speak | render | diversity | cause |
|---|---|---|---|---|---|
| 1 | `mis16` | 0.0 % | 1.6 % | ⛔ collapse | pad==eos masked every real stop |
| 2 | `mis16b` | — | — | — | tokenizer never saved → unreadable object |
| 3 | `mis16c` | 0.0 % | 57.8 % | ⛔ "COLLAPSE, 1 distinct" | chat template dropped `system` in the TRAIN shape |
| **4** | **`mis16d`** | **100.0 %** | **93.8 %** | **12/12, dep +1.00** | — |

⭐ Same base, same seed, same config, same hardware across 3 and 4. The **only**
difference is the chat-template repair, and it moved speak 0 → 100 % and render
57.8 → 93.8 %. ⛔⛔ The diversity guard that reported *"COLLAPSE: 1 distinct
output"* on attempt 3 reports **12/12 distinct with dependence +1.00** here —
confirming, on the same family, that the guard had been measuring the parse and
not the speaker. The ledger's 36 distinct raws were right.

⭐ The scoreability machinery built after Run 0's empty-cell crash earned itself:
`resolving_power` ~70 against thresholds of 3–6 means every cell is genuinely
readable, not a small-n artifact. And `sampling_stream_seeded: true` makes this a
**documented draw** — every profile before `6988d06` was one undocumented sample.

## 5 · ⏭ What this opens

1. **Mistral mapping rung (3b)** — now the live question, and the most
   informative cell in the matrix because Mistral is nearest the ceiling.
   ⚠️ Its locus is **4.1× smaller** than Qwen's (268,435,456 vs 1,089,994,752),
   so the read is verdict-vs-verdict and ruler-free, never a matched budget.
   ⛔ `pipeline_fullft_read.sh` is Qwen-hardcoded and its mapping steps are
   unguarded — de-Qwen it before the mapping rung, not before the layer rung.
2. **`choose` diagnosis** — instrument or base? Unanswered.
3. **The 14B scale rung** — tests whether resistance scales, which is the
   published prediction the direction flag points at.
4. **The art-piece cost decision** now has two datapoints under it instead of
   one. It is still not decided: the ladder is unexhausted on Mistral.
