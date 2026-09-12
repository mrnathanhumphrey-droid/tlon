# AUDIT — every Qwen-shaped assumption a different base can trip silently

**Instrument:** `tools/act2_base_audit.py` · **report:** `runs/act2/base_audit.json`
**Red-proof:** `tests/test_base_audit.py`, `tests/test_chat_shape.py`,
`tests/test_guard_reads_the_raw.py` · suite 1808 → **1840**

⭐ **THE AUDIT IS NOT A BUG HUNT.** The brief was: enumerate every point where
the harness touches a base-specific behaviour, and for each, assert it is *read
off the actual base* rather than assumed Qwen-shaped. Four instances of that one
class had already cost GPU time, each found only when a non-Qwen base tripped it.
So the deliverable is a runnable instrument, not a memo — it is wired in as
`step base_audit`, before `train_leg1`, and it fires on every future run.

```
                    OK   FAIL  WARN  UNKNOWN
Qwen2.5-7B           19     0     1        1
Olmo-3-7B            25     0     0        0
Mistral-7B-v0.3      20     0     5        0
Ministral-3-8B       18     2     1        0
TOTAL                82     2     7        1
```

⛔ **`UNKNOWN` IS NOT A PASS** and is counted separately. Qwen's weights were
archived off this machine, so its tensor-level scope checks have nothing to read.
A summary folding "could not check" into "checked and fine" is the same vacuous
pass as an empty lag cell rendering as a failed one.

---

## The four known landmines — now found by the instrument, not by a run

| path | assumption | base that tripped it | cost |
|---|---|---|---|
| load | it's a causal LM | Ministral-3 is `Mistral3ForConditionalGeneration` | ~$0.45 |
| tokenizer | pad ≠ eos | Mistral has no pad token → pad := eos | ~$6 |
| template | native ChatML system role | Mistral v0.3 drops `system` in the **train** shape only | ~$5 |
| scope | one layer stack | a multimodal base pools two into a contiguous-looking set | 36 vision tensors trained |

⭐ All four are now detected **at minute zero from the config and tokenizer
alone** — no weights, no GPU, seconds. The Ministral loader fault reproduces as a
`FAIL` from `AutoConfig` without downloading anything.

---

## 1 · The tokenizer path

✅ pad/eos read per base, `genuine eos survives label masking` measured on the
real corpus text at the real `--seq`, special tokens resolve, vocabulary numbers
reconciled.

⚠️ **NEW FINDING — BOS IS DOUBLED on both Mistral bases.**

```
Qwen        leading BOS: train=0 read=0
OLMo        leading BOS: train=0 read=0
Mistral     leading BOS: train=2 read=2   head [1, 1, 3, 1763]
Ministral   leading BOS: train=2 read=2   head [1, 1, 17, 4568]
```

The chat template emits a literal `<s>` **and** the fast tokenizer's
post-processor prepends another. ⛔ `add_bos_token` reads **`False`** on both —
the attribute the harness would have been asked does not describe what happens.

⚠️ Recorded as WARN, not FAIL, and the reason matters: **train and read agree**
(2 and 2), so this is not a distribution mismatch like the system-message bug. It
is a malformed prompt fed *consistently*. The model never sees a single-BOS
sequence, which is a real difference from how Qwen and OLMo were trained, and it
was never checked. The audit FAILs if the two counts ever diverge.

⚠️ **NEW FINDING — Qwen has 399 embedding rows its tokenizer cannot reach.**

```
Qwen      tok 151,665 vs config.vocab_size 152,064  ->  399 UNREACHABLE ROWS
OLMo      100,278 == 100,278
Mistral    32,768 ==  32,768
Ministral 131,072 == 131,072
```

⭐ This bears on **the mapping rung specifically**, which trains `embed_tokens`
whose height is the *config's*. 399 of Qwen's rows can never receive a gradient.
Not a bug — but a cross-family mapping comparison where one base has 399 dead
rows and another has none is comparing two slightly different objects, and that
now has to be said out loud rather than discovered later. ⚠️ It does **not**
disturb the standing Qwen mapping finding, which is verdict-vs-verdict and
ruler-free.

## 2 · The chat-template path

⛔ **The template is checked on EVERY shape the pipeline emits** — all three
directions (`write`, `read`, `provoke`), in the train shape and the read shape.
That is the point: Mistral's template is *faithful* for `(system, user)` and
*lossy* for `(system, user, assistant)`, so a single-shape probe passes and
proves nothing. Shape-dependence was the bug.

Three assertions per shape: content survival, **the read prompt is a literal
prefix of the training text**, and the read shape keeps the system message.

⭐ The prefix check is the deep one. `speak`, `render` and `choose` all send
`read_prompt(...)` and expect the answer to continue it; if the training text
does not *begin* with that string, the model is read out-of-distribution however
good it is. `tlon/act2/chat_shape.py` now makes it hold by construction for a
lossy base, and leaves a faithful base **byte-identical** so no standing run
moves — both halves asserted against the real tokenizers.

## 3 · The model-load path

✅ config loads · `AutoModelForCausalLM` supports the `model_type` ·
`tie_word_embeddings` false (the mapping rung needs two addressable tensors) ·
layer/vocab/hidden recorded.

⛔ **Ministral-3 FAILS here**, as it should: `model_type 'mistral3' is NOT in the
causal-LM mapping — the training leg would die on 'Unrecognized configuration
class'`. This is the check that was banked as "a preflight that LOADS the model";
it turns out the *config* is enough for this fault, at zero cost.

## 4 · The scope path

✅ Per base, against **real tensor names** from the safetensors headers: exactly
one layer stack, tensor layer count matches the config, top-half selection,
mapping addresses both leaves, `embed_tokens` rows match `config.vocab_size`.

```
OLMo      1 stack {model: 32}   top-16 = 3,238,264,832   mapping = 821,477,376
Mistral   1 stack {model: 32}   top-16 = 3,489,792,000   mapping = 268,435,456
Ministral ⛔ {language_model.model: 34, vision_tower.transformer: 24}
```

❔ **Qwen: UNKNOWN** — weights archived off this machine. Stated, not passed over.

## 5 · The parse/verdict path — the subtlest class, and it just bit

⛔⛔ **A GUARD THAT READS A TRANSFORMED VALUE MEASURES THE TRANSFORMATION.**

`diversity._key` reads the **parsed** proposal. Every parse in run 3a's re-fire
failed, so every proposal was `None`, so every key was `"<none>"`, so
`var_distinct == 1`, so the guard raised:

> `COLLAPSE: 1 distinct output for 12 DIFFERENT inputs. A constant is not a speaker…`

about a speaker that had emitted **36 distinct near-valid Tlön scenes**, 64/64 of
which parse cleanly after dropping one stray trailing brace.

⭐ The guard was **right that the run was unscoreable and wrong about why** — and
"why" was the difference between a fact about Mistral and a bug in the harness.
Left alone it would have been filed as a second non-speaker, and "faithful Tlön
speakerhood is rare across families" would have rested on a parser.

**The repair is not a looser guard.** `NothingParsed` subclasses
`DegenerateSpeaker` — so every existing handler still refuses to score the run,
which is correct — and separates three states that were one:

```
the model emitted one thing                    COLLAPSE        about the MODEL
the parser rejected many distinct things        NOTHING PARSED  about the HARNESS
nothing parsed AND no raws were recorded        INSTRUMENT GAP  not a finding at all
```

`_rate` now carries raws **index-aligned** with `produced`, and a test asserts
exactly one append per loop path — a `raws` list holding only failures would make
the new diagnosis *wrong* instead of *missing*.

---

## ⏭ Residue — what this audit did NOT settle

1. ❔ **Qwen's tensor-level scope checks never ran.** Needs its weights back on
   disk, or the same audit run against the hub object.
2. ⚠️ **BOS doubling is recorded, not fixed.** Harmless-looking because train and
   read agree, but it is a real difference from how the standing findings were
   produced. Fixing it would change Mistral's training text again; deciding that
   is a separate call.
3. ⚠️ **The audit checks the paths it knows.** It is an enumeration of the
   *touch points*, so a base-specific behaviour at a touch point nobody has named
   is still unguarded. The generation/decoding path (stop criteria, sampling,
   `max_new_tokens` per base) is the most likely next one and is **not** covered.
4. ⛔ **`pipeline_fullft_read.sh` is not audited and is Qwen-hardcoded** —
   `MODEL=Qwen/Qwen2.5-7B-Instruct` at line 35, and its `vocab_coverage` /
   `mapping_moved` steps sit unguarded, so a layers-rung cell would refuse. The
   `lint_step_scope.py` guard does not police that file because it declares no
   `SCOPE_MODE`. Found during this audit, not fixed.
5. ⛔ **Mistral still has no datapoint.** Three attempts, ~$17, three distinct
   harness faults. What the audit changes is that the fourth is not being run on
   hope.
