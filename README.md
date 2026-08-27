# Tlön

**A working language with no nouns — and a 7B model that learned to speak it.**

**Weights:** [`keyzersoze04/tlon-7b-lora`](https://huggingface.co/keyzersoze04/tlon-7b-lora)
· LoRA adapter for `Qwen2.5-7B-Instruct`, MIT.
⛔ That published adapter is **run 3**, which does *not* clear the project's own
gate — see [the results](#can-a-model-learn-it). A later model does clear it and
is not published.

> *"There are no nouns in the conjectural Ursprache of Tlön, from which its
> present-day languages and dialects derive: there are impersonal verbs, modified
> by monosyllabic suffixes or prefixes which have the force of adverbs."*
> — Jorge Luis Borges, *Tlön, Uqbar, Orbis Tertius* (1940)

Borges described the language in a paragraph and left it there. This is an
attempt to actually build it, and then to find out whether a language model can
learn to think in it.

It has **233 words**, no word for any *thing*, and a grammar strict enough that
every sentence can be mechanically checked for legality. You can talk to it.

```
nix hul kra rän pal sorsoras rän ka
```

means

> out of ⟨together, because of ⟨it repeats⟩, it thins, habitually (×2)⟩, it repeats.

There is no "it" in the Tlön. There is no thing that repeats. There is only
*repeating*, qualified by other repeatings.

---

## What this actually is

Three things in one repository:

1. **A complete constructed language** — 233 forms in 9 grammatical classes, with
   a parser, a renderer, and an exact round-trip guarantee.
2. **A chatbot** you can run locally that translates English into Tlön and shows
   you what survived the translation and what didn't.
3. **A research record** — pre-registered experiments, with the failures and
   retractions left in.

---

## The language in ninety seconds

Every Tlön utterance is one **happening** — a verb with no subject — decorated by
other happenings.

| class | n | what it does | examples |
|---|---|---|---|
| **R** root | 156 | the happening itself | `rän` *it repeats* · `pal` *it thins* |
| **O** orient | 24 | direction, relation | `hul` *together* · `xom` *behind* |
| **L** relator | 12 | binds a clause to another | `kra` *because of* · `nix` *out of* |
| **A** aspect | 6 | how it unfolds; **repeated for intensity** | `sor` → `sorsoras` *habitually (×2)* |
| **M** modal | 10 | stance | `hrix` · `mar` |
| **D** degree | 6 | strength | `les` · `ron` |
| **Q** quant | 6 | how much / how often | `sim` *once* · `nol` *oft* |
| **T** tense | 8 | when | `nu` · `kril` |
| **F** force | 5 | what the utterance *does* | `ka` states · `ki` asks · `kä` denies |

The nine classes are **surface-disjoint** — no form belongs to two classes — and
the grammar fixes the order: `Q? T? M? O{0,2} (L clause){0,3} R A? D?` then `F`.

**A sentence is legal or it is refused.** There is no partial credit and no
repair: `parse(render(scene)) == scene` is an exact identity, checked at runtime.

### Nouns are the hard part

English can't say most things without objects. Tlön has to render the
*impression underneath* the object. "A dog barks" has no dog in it — it becomes
a barking, qualified. The chatbot tells you honestly when something didn't
survive; that refusal is the interesting part, not a bug.

---

## Talk to it

```bash
pip install -r requirements.txt
python tools/chat.py
```

Real translation sends your English to a hosted model to *propose* a Scene, so it
needs `ANTHROPIC_API_KEY` and costs a fraction of a cent per line. **The model
only ever proposes — the Tlön grammar gate decides what is legal, and it refuses
far more than it accepts.**

You get the Tlön first: pronounceable, opaque, solvable if you think about it the
right way. The literal translation comes only when you ask for it. That order is
deliberate — the cipher is the experience, the gloss is the answer key.

### Without an API key

`--offline` runs the whole pipeline — schema gate, renderer, round-trip check,
literary gloss — against **one fixed canned proposal**. It is a smoke test of the
machinery, not a translator: the output below is the same whatever you type.

```
$ python tools/chat.py --offline --say "a dog barks"

nar sen lan klung testesas ka

  Tlön would not hold "landlord" as a thing.
  → a hollowing that recurs, witnessed

  Downward, at a seeing and being beheld, it hollows and voids,
  again and again, and again.
  austere: downward, at ⟨it sees, is beheld⟩, it hollows, voids,
  again and again (×2).
```

Even canned, it shows the thing worth seeing: the translator **refused to turn a
landlord into a thing** and said so out loud. Tlön has no word for an object, so
"landlord" survives only as *a hollowing that recurs, witnessed*. That refusal is
the language working, not failing.

---

## Can a model learn it?

That was the research question, and the answer is **yes, in both directions.**

A **Qwen2.5-7B** fine-tuned with LoRA on 80,000 examples, evaluated
**without the lexicon in context** and **without grammar-constrained decoding** —
so it is speaking from its weights, not reading a table and not being forced into
legality by the sampler:

| | untuned | **fine-tuned** |
|---|---|---|
| **writes** legal Tlön from English | 0.0 % | **84.4 %** |
| **reads** Tlön and replies legally | 0.0 % | **98.4 %** |
| **comprehends** (4-way forced choice) | 46.9 % | **68.0 %** |

Comprehension is significant by a paired McNemar test, **p = 1.1 × 10⁻⁶** over
256 items.

### The gate has since been cleared — by a later model that is not the one published

The table above is **run 3** — the adapter published at [`keyzersoze04/tlon-7b-lora`](https://huggingface.co/keyzersoze04/tlon-7b-lora) — measured at n = 64. It
does **not** clear the formal gate: reading passes, writing sits 5.6 points short.

A later model, trained on a **multi-turn** corpus, does clear it — measured at
n = 256, still cardless and unconstrained:

| | run 3 (published) | multi-turn model |
|---|---|---|
| **writes** legal Tlön from English | 84.4 % *(n=64)* | **96.1 %** *(n=256)* |
| **reads** Tlön and replies legally | 98.4 % *(n=64)* | **100.0 %** *(n=256)* |
| **comprehends** (4-way forced choice) | 68.0 % | 57.0 % |

⚠️ **Comprehension fell as the other two rose.** That is a real trade, not a
rounding — and it is the direction a human conversation actually needs. Reported
because it cuts against the headline.

⛔ **The published adapter is still run 3, the one that does not clear.** Nothing
that clears the gate has been published.

### And a result that cuts against all of the above

Two adapters built by the **same recipe** — same map, same hyperparameters,
corpora matched to 0.19 % on tokens — disagree by **0.133** on how often the model
asks questions rather than asserts. A pre-registered probe **halted at its own
reproduction check** when it found this: the *measurement* reproduces (t +0.62 on
re-serving the same weights), but the *pipeline's output* does not (t +6.89
between two builds).

So several numbers on this page describe **one training run**, not the method.
Whether the recipe determines the model at all is an open question with a
pre-registered probe running against it. Written down here rather than left for
someone else to find.

Cost of the fine-tuning research to date: **about $92** of rented A100 time.

---

## What's proven, what isn't

Kept deliberately separate, because the difference is the whole point.

**Established**
- The class system is learnable from weights, both directions, cardless and
  unconstrained.
- Comprehension improves significantly (paired test, n=256).

**Open**
- The 90 % gate is not cleared on the write direction.
- Whether two such models, talking only in Tlön, drift into a private dialect —
  the actual experiment this was all built for. Pre-registered, not yet run.

**Retracted** — left in the record on purpose
- Comprehension was called "clean" after one run. The replication did not reach
  significance, so it was downgraded to *suggestive* and only became established
  later, by the correct test at adequate n. The direction was right the whole
  time; the confidence was not.

If you want the failures, `docs/DEVIATIONS_ACT2_2026_08_24.md` is the honest
version: instrument bugs, wrong diagnoses, and the measurements that overturned
them.

---

## Repository map

| path | what's in it |
|---|---|
| `tlon/grammar/` | the language — parser, renderer, frozen lexicon |
| `tlon/product/` | the chatbot: schema gate, translation, literary render |
| `tlon/act2/` | the drift experiment — probes, falsifiers, corpus, diversity guard |
| `tlon/harness/` | comparison guards that make bad statistics *unexpressable* |
| `tools/` | `chat.py`, corpus builder, fine-tune, evaluation gates |
| `docs/` | pre-registrations, deviations, decision records |
| `tests/` | 928 tests |

### Two things worth knowing before reading the code

**The lexicon is frozen** at `e2b8527010231a81fd31b6eeb9de3d8c` and verified by
test. It was the measuring instrument for every experiment here; changing it
would silently invalidate every number.

**The pre-registrations are content-hashed and never rewritten.** When a
prediction turned out wrong, the correction goes in a `DEVIATIONS` file beside
it. That is why the mistakes are still visible — they were not allowed to be
edited away.

---

## Reproducing it

```bash
python -m pytest -q                              # 928 tests, no GPU needed
python tools/act2_build_corpus.py --n 40000      # deterministic, seed 20620
python tools/act2_finetune.py --model <backbone> --dtype bf16 --seq 192 \
    --batch 16 --accum 1 --epochs 1 --out runs/act2/adapter
python tools/act2_flocal.py --model <backbone> --adapter runs/act2/adapter
```

The corpus isn't committed — it's 36 MB and regenerates byte-identically from the
builder, which is a better artifact than the file. Adapter weights aren't
committed either (308 MB, over GitHub's limit).

`tools/act2_finetune.py --plan` sizes the VRAM before you rent anything.

---

## License

MIT. Use it, fork it, teach it to something.

Tlön was a hoax invented by a secret society to infiltrate reality. It seemed
unfair to gatekeep it.
