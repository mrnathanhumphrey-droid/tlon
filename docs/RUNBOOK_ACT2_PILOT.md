# RUNBOOK — Act 2 Tier-A pilot. ✅ **COMPLETE. NO METER RUNNING.**

**Three runs, all instances terminated, ~$14.60 of A100 time.** Kept as the
operational record of how the results in the README were produced, and as the
procedure for the next rented run.

**Final:** speak **98.4 %** · render **84.4 %** · comprehension **68.0 %**
(McNemar **p = 1.1 × 10⁻⁶**, n=256). F-LOCAL still fires on render vs the 0.90
bar. Full account in `DEVIATIONS_ACT2_2026_08_24.md` **D8–D14**.

⛔ **Sections below are the LIVE-RUN procedure and are written in the present
tense.** Everything about a running instance applies only while one exists.

---

## 0 · ⛔⛔ IF A METER IS RUNNING, READ THIS FIRST.

| | |
|---|---|
| **instance** | **TLON** · `<INSTANCE-ID>` · `<INSTANCE-IP>` |
| **type** | `gpu_1x_a100_sxm4` — 1× A100 40 GB SXM4, us-east-1 |
| **rate** | **$1.99/hr — ~$48/day if it is left up** |
| **key** | `~/.ssh/tlon` (ed25519, generated for this; registered with Lambda as `tlon`) |
| **login** | `ssh -i ~/.ssh/tlon ubuntu@<INSTANCE-IP>` |

**KILL IT WHEN THE RUN IS DONE:**

```bash
curl -s -X POST https://cloud.lambdalabs.com/api/v1/instance-operations/terminate \
  -H "Authorization: Bearer $LAMBDA_API_KEY" -H "Content-Type: application/json" \
  -d '{"instance_ids":["<INSTANCE-ID>"]}'
```

⛔ **Pull the adapter and the ledger off the box BEFORE terminating.** Terminating
destroys local disk; there is no attached persistent filesystem.

```bash
scp -i ~/.ssh/tlon -r ubuntu@<INSTANCE-IP>:~/tlon/runs/act2/adapter  runs/act2/
scp -i ~/.ssh/tlon    ubuntu@<INSTANCE-IP>:~/tlon/runs/act2/ledger.jsonl runs/act2/ledger_tlon.jsonl
scp -i ~/.ssh/tlon -r ubuntu@<INSTANCE-IP>:~/tlon/runs/act2/logs     runs/act2/
```

⛔ **A separate instance `rsna-bakeoff` (A100 SXM4) is also running** on this
account. It belongs to another project. **Do not terminate it.**

⛔ **`curl`, NOT python-urllib, for the Lambda API.** urllib is blocked at the
Cloudflare edge with **403 / error 1010** — a client-fingerprint ban that looks
exactly like an auth failure. The key is fine; the client was the problem.

---

## 1 · What the three runs established

| stage | state |
|---|---|
| **corpus** | ✅ shipped, **sha256 verified byte-identical** both sides, every run |
| **locked docs** | ✅ PREREG + AMENDMENT A **sha256 verified byte-identical** both sides |
| **suite** | ✅ **928 passed**, same on the box as locally — lexicon and locks intact across the wire |
| **BEFORE baseline (bf16)** | speak **0.0 %** · render **0.0 %** · comprehension **46.9 %** (n=256) · F-LOCAL FIRED, as expected |
| **run 1** | ⛔ **UNINFORMATIVE** — corpus was serialized in the canonical HASHING dialect, not the proposal schema (39 of 44 render failures) |
| **run 2** | render **81.2 %** · speak **9.4 %** — dialect fixed; the corpus trained a WRITER and the gate tested a READER |
| **run 3** | ⭐ render **84.4 %** · speak **98.4 %** · comprehension **68.0 %** — read direction added |
| **spend** | hosted **$0.1043** + Lambda **≈ $14.60**. **The $1,500 contingency was never touched.** |

**Pipeline:** `~/pipeline.sh` on the box, `nohup`, logs to
`~/tlon/runs/act2/logs/`. It writes **`DONE` only on success** and **`FAILED`
with the stage name** otherwise.

---

## 2 · What changed by moving to Lambda, and what did NOT

**CHANGED — and it removes a confound:**
- **4-bit QLoRA → bf16 LoRA.** 16 GiB forced quantization locally. On 40 GiB it is
  unnecessary. ⭐ **If F-LOCAL had fired on the local run, "we quantized it to 4
  bits" would have sat permanently inside the boundary claim.** It does not now.
- **batch 8 × accum 2 → batch 16 × accum 1.** ⛔ **Effective batch is 16 either
  way and the step count is 5,000 either way** — same optimizer trajectory, one
  forward instead of two.
- **The baseline was RE-MEASURED in bf16.** ⛔ A bf16 after-reading against a
  4-bit before-reading is unattributable. Measured cost of quantization on the
  untuned model: comprehension **34.4 % at 4-bit vs 39.1 % at bf16**.

**NOT CHANGED — all of it is Nate's call, not a side effect of changing hosts:**
- backbone **`Qwen/Qwen2.5-7B-Instruct`** · lr `1e-4` · rank 32 · 2 epochs · seq 192
- ⛔ **Tier B (12–14B) is now cheap on a 40 GB card. It is still a backbone
  decision and it has not been taken.**

---

## 3 · What the numbers mean when they land

**F-LOCAL clears (render ≥ 0.90 AND speak ≥ 0.90, cardless, unconstrained)**
⇒ ⭐ **the first native Tlön speaker** — emitting from weights, not reading a
table. `D_ctx` becomes well-posed. Act 2 is live.

**F-LOCAL fires** ⇒ the pre-registered recovery set, **in this order**:
1. more contrastive negatives from the widened failure log
2. curriculum fine-tune — class discipline before composition
3. bigger backbone (Tier B — now trivially affordable here)

Persistent across all three ⇒ **BOUNDARY: not internalizable at this scale.** A
real finding about the grammar's learnability, reported as one.

⛔ **KNOWN SCOPE LIMIT, FLAGGED BEFORE THE RESULT:** the corpus is
`(English → Scene)` pairs, so **training covers `render` and never `speak`**.
F-LOCAL takes the **worst** of the two. If `speak` lags `render` after training,
that is the diagnosis, not a mystery — and it is a corpus-composition question,
which is Nate's call.

---

## 4 · Rules that bind this run

- ⛔⛔ **F-LOCAL is measured UNCONSTRAINED and CARDLESS.** `falsify.f_local`
  **raises** on either violation. Neither warns; both refuse.
- ⛔ **Act 2 is `D_ctx`**, not `D_w`. `D_w` is parked as a separate project.
- ⛔ Nothing is a result until **ledgered**; transcripts stay sealed until then.
- ⛔ **Locked prereg bodies are never rewritten** — corrections go to
  `DEVIATIONS_ACT2_2026_08_24.md`.

---

## 5 · If something looks wrong

- **`FAILED` sentinel exists** → `cat runs/act2/logs/FAILED` names the stage.
- **F-LOCAL reads exactly 1.00** → suspect constrained decoding. It cannot be
  scored that way and `f_local` should have raised; if it did not, that is a bug
  in the guard, **not a result**.
- **Lambda API 403** → see §0. It is Cloudflare, not the key.
- **Environment drift** → the venv at `~/venv` is pinned to the versions the code
  demonstrably ran on locally: torch **2.11.0+cu128**, transformers **5.8.1**,
  peft **0.19.1**, datasets **4.8.5**, numpy **2.2.6**, jinja2 **3.1.6**.
  ⛔ The image's **system** torch/scipy are built against numpy 1.x — upgrading
  numpy outside a venv breaks them. ⛔ The default torch wheel is **cu130** and
  the driver is **12.8**; the cu128 index is required.

---

## 6 · ✅ THE VRAM PLANNER WAS WRONG BY 3.4× AND IS NOW FIXED

`tools/act2_finetune.py --plan` predicted **4.6 GiB**. Measured:

| | predicted | measured |
|---|---|---|
| 4-bit, batch 8 × 192 (local) | 4.6 GiB | **15.5 GiB** (97 % of a 16 GiB card) |
| bf16, batch 16 × 192 (TLON) | ~15 GiB | **31.8 GiB** of 40 |

**The omitted term does not scale with parameters at all.** It is the LM head
output, which scales with **VOCABULARY** — 16 × 192 × 152,064 = 467 M logits,
upcast to fp32 by cross-entropy and kept again as a gradient, ~5.6 GiB at batch
16. Larger than everything the old formula counted.

✅ Fixed and anchored to both measured runs (±2.5 %). ⚠️ The slack factor is
**fitted to two points** and labelled as such in the source — re-anchor it the
moment a third run disagrees.

---

**Verification at close:** **928 tests** · red-proofs 4/4 plus the comprehension
red-proof **3/3 mutations applied and CAUGHT** · PREREG `20620b7c` and AMENDMENT A
`8c010702` **sha256-verified byte-identical on every machine used**.
