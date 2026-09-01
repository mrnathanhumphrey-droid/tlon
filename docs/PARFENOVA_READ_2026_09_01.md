<!-- settled-claim-ok: reports measured levels and quotes source values; the
     "-limited" mentions below are quoted retractions from earlier docs. -->
# Parfenova et al. — read from source, and what it means for the replication

**Emergent Convergence in Multi-Agent LLM Annotation.** Angelina Parfenova
(Lucerne UAS / TUM), Alexander Denzler, Juergen Pfeffer. arXiv **2512.00047v1**,
20 pp. Read 2026-09-01. ⛔ The PDF is not committed (third-party copyright); this
file is my own notes, and every quoted number below was copied from the source at
the time of writing, not recalled.

## What they actually did

- **7,500 discussions**, ~125,000 utterances. Group size **2, 3, or 5 agents** ×
  discussion depth **1–5 rounds**, 500 discussions per configuration.
- Task: **inductive coding** — assign a short qualitative code to a text segment.
- **Five prompt templates**, rotated (Table 1).
- ⭐⭐ **The agents are FIVE DIFFERENT MODEL FAMILIES**: Llama4 Maverick,
  Llama3.3 70B, Deepseek-R1 70B, Gemma, Mistral.
- Metrics: ROUGE-1/2/L; **TwoNN intrinsic dimensionality** on 384-d MiniLM
  sentence embeddings; sentiment; certainty/hedging lexicons (65 certainty
  expressions + a hedging list).

**Algorithm 1** (Appendix A), three phases — the memory model is the thing we
would be contrasting against:

1. *Initial code generation* — each agent independently produces `c⁽⁰⁾ᵢ`, then
   **summarises it to one sentence** `s⁽⁰⁾ᵢ`. Memory initialised
   `C⁽⁰⁾ = [s⁽⁰⁾₁ … s⁽⁰⁾ₖ]`.
2. *Iterative refinement* — for each round, each agent in fixed turn order reads
   **`C⁽ʳ⁻¹⁾` plus the item**, generates a refinement, summarises it, and
   **appends the summary to the shared memory**.
3. *Final synthesis* — each agent produces a final code given the full `C⁽ᴿ⁾`.

⇒ **Shared, append-only, everyone reads everything, mediated by one-sentence
summaries.** That is precisely the opposite of our self-accumulation rule, so the
contrast the brief wants is real and well-defined.

## Table 4, copied from source

| Setup | Initial Id | Final Id | ΔId | Steepest drop | Drop round |
|---|---|---|---|---|---|
| 2-Model | 13.55 | 13.11 | −0.44 | −1.72 | Final |
| 3-Model | 7.94 | 0.64 | −7.30 | −4.63 | R1 |
| 5-Model | 7.66 | 0.42 | −7.24 | −3.75 | R1 |

The brief's characterisation — *2-agent barely converges, 3/5-agent collapse* —
**is accurate.** ⚠️ But note Table 4 is **intrinsic dimensionality**, not ROUGE;
the ROUGE evidence is Table 2 and is reported per prompt.

## Two observations about their design, one of which is our contribution

⭐⭐ **1. Group size is confounded with model composition.** The 2-agent setup is
a specific pair drawn from five *different architectures, trained by different
organisations on different data*; the 5-agent setup is all five. A group-size
effect and a which-models-are-present effect are not separable in this design.
**Our substrate removes exactly this**: seven adapters, same base, same recipe,
differing only by trainer seed. That is the clean contribution, and it is a
contribution to *their* open question rather than a criticism.

⚠️ **2. The R0 baselines are not level.** The 2-Model setup starts at Id **13.55**
against **7.94 / 7.66** for 3- and 5-Model — a ~1.7× difference *before any
interaction*, since Phase 1 codes are generated independently. The paper does not
account for this, and it complicates reading ΔId across setups. It does not
explain away their result (starting higher means more room to fall, and the
2-model group did not fall), but it is unexplained.

⛔ **A confound I tested and REJECTED:** I hypothesised that TwoNN Id is
sample-size biased and that the setups have different cloud sizes (~1000 / 1500 /
2500 points if codes are pooled over 500 discussions). Measured on clouds of
known dimension:

| n points | true d=5 | true d=8 | true d=13 |
|---|---|---|---|
| 1000 | 5.09 | 7.98 | 11.91 |
| 2500 | 5.06 | 7.90 | 12.15 |

Bias is ~2% and runs the **wrong way** — larger n gives slightly *higher* Id,
while their larger groups show *lower* Id. **The sample-size explanation is not
supported and should not be raised.**

## ⛔⛔ Their metrics mostly do not transfer to Tlön

| their metric | on our substrate |
|---|---|
| ROUGE-1/2/L | ⛔ **DEAD — saturated.** Unrelated Tlön speakers already score 0.667 (ROUGE-1) across a 244-token vocabulary; partners score 0.661. Cannot show convergence or its absence. |
| certainty / hedging lexicons | ⛔ **Inapplicable.** 65 English epistemic expressions; Tlön has no such lexicon and no translation of one. |
| sentiment | ⛔ Inapplicable for the same reason. |
| TwoNN Id on MiniLM embeddings | ⚠️ **Validity unestablished.** MiniLM is English-trained; embeddings of Tlön surfaces would need to be shown to carry Tlön structure before any Id computed from them means anything. |
| TwoNN Id on a Tlön-native representation | ⭐ **Plausible** — Id over parse-derived features is ours to define, and is the closest honest analogue of their headline measure. |

⛔ **And Algorithm 1 needs an operation Tlön may not have:** its memory is
composed of **one-sentence summaries**, and there is no summarisation operator in
the Tlön grammar/product layer that I know of. Substituting the full surface as
its own summary is a deviation from their algorithm and must be declared as one,
not glossed.

## What this means for the run

The replication as briefed — *faithful reproduction on their metrics* — **is not
available**, and the reason is a property of our substrate, not a shortfall of
effort. What remains available and worth doing:

1. **A conceptual replication of the group-size × memory contrast**, on a
   substrate where architecture, training data, and recipe are held constant and
   only the trainer seed varies — which is the confound their design cannot
   remove. Measured on a Tlön-valid convergence metric.
2. **The metric question must be settled first**, and it is the same
   prove-the-instrument arm the brief already asks for: any candidate metric must
   pass the unrelated-pair test (does it separate partners from strangers at all?)
   before it is used. ROUGE fails that test today.

⛔ Still not a spend recommendation. The next decision is *which convergence
metric is valid on Tlön*, and that is answerable at $0 on the 105 transcripts
already on disk.
