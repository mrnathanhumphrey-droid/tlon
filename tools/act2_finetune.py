"""THE CLASS-PARTITION FINE-TUNE — LoRA/QLoRA on owned hardware.

⛔⛔ NO BACKBONE IS NAMED IN THIS FILE. `--model` is required and has no default,
because the backbone is Nate's call every time and a default here would be that
decision taken quietly.

⛔ `--plan` computes the VRAM arithmetic and the schedule WITHOUT LOADING
ANYTHING — $0, no download, no GPU. Run that first; it is the honest answer to
"will this fit" and it needs no commitment.

    python tools/act2_finetune.py --plan --params 7 --dtype bf16
    python tools/act2_finetune.py --model <id> --out runs/act2/adapter
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "runs" / "act2" / "corpus"

#: ⛔⛔ ONE PROMPT PER DIRECTION. Training both tasks under a single instruction
#: would force the model to GUESS which one it is on from the input alone, and
#: the two inputs are the two languages — exactly the discrimination that failed.
from tlon.discourse.provocation import DIRECTION as _PROVOKE
from tlon.discourse.provocation import PROVOCATION as _PROVOCATION

SYSTEM = {
    "write": ("You render English into Tlön. Tlön has no nouns. Emit ONLY a "
              "JSON Scene object."),
    # ⭐ THE HALF THAT WAS MISSING. Measured: render (write) 81.2 %, speak (read)
    # 9.4 %, and 90 % of the offending forms were lifted VERBATIM off the Tlön
    # the model had just been shown — it was copying tokens it could not parse.
    "read":  ("You read Tlön. Tlön has no nouns. Given a Tlön utterance, emit "
              "ONLY the JSON Scene object it means."),
    # ⛔⛔ THE THIRD DIRECTION, AND THE ONE THE ARENA ACTUALLY SERVES UNDER.
    # Before this, the trainer knew "write"/"read" and the arena spoke under a
    # prompt in another module that was NEVER a training direction — run 3 is
    # prompted at arena time under a framing it has never seen. Imported, not
    # re-spelled, so trainer and arena cannot drift apart again.
    _PROVOKE: _PROVOCATION,
}

# ⛔ NO LEXICON CARD IN THE TRAINING PROMPT. The whole bar is cardless emission;
# training with the table in context would teach the model to expect it, and
# F-LOCAL would then be measuring a crutch that was installed on purpose.


def row_messages(row) -> list[dict]:
    """The exact chat messages a training row becomes.

    ⛔⛔ MODULE-LEVEL ON PURPOSE, SO THE TOKEN BUDGET AND THE TRAINER SHARE ONE
    FOLD. This lived inside `main()`, which meant anything wanting to count the
    corpus's tokens had to re-spell the formatting — and a counter that
    reimplements the thing it measures verifies itself. The project has already
    shipped that shape twice (a partition test that called `impression()`; four
    name-folds sharing a constant instead of a rule). `act2_token_budget.py`
    imports THIS function, so if it drifts they drift together.
    """
    direction = row.get("direction") or "write"
    return [{"role": "system", "content": SYSTEM[direction]},
            {"role": "user", "content": row.get("prompt") or row["english"]},
            {"role": "assistant",
             "content": json.dumps(row["scene"], ensure_ascii=False,
                                   sort_keys=True)}]


def row_to_text(row, tok) -> str:
    """Messages → the literal string that gets tokenized."""
    msgs = row_messages(row)
    if getattr(tok, "chat_template", None):
        return tok.apply_chat_template(msgs, tokenize=False)
    return (f"{msgs[0]['content']}\n\n{msgs[1]['content']}\n\n"
            f"{msgs[2]['content']}")


#: ⛔⛔ MEASURED ON REAL RUNS. The first version of `plan()` predicted 4.6 GiB for
#: the local job and the job used 15.5 of a 16 GiB card. These are the anchors any
#: change to the arithmetic must still reproduce; a planner is only worth having
#: if it is checked against what actually happened.
MEASURED = (
    # (params_b, dtype, seq, batch, vocab, measured_GiB, where)
    (7.62, "4bit", 192, 8, 152064, 15.5, "local RTX Blackwell 16 GiB, 97 % full"),
    (7.62, "bf16", 192, 16, 152064, 31.8, "TLON A100 40 GiB"),
    # ⛔⛔ THE THIRD ANCHOR DISAGREES, AND THE DOCSTRING SAID TO SAY SO.
    (7.62, "bf16", 256, 8, 152064, 36.1, "TLON A100 40 GiB, run 4 — PLANNER "
                                         "UNDER-PREDICTED BY 28 %"),
)

#: ⛔⛔ `RUNTIME_SLACK` IS NOT A CONSTANT, AND THREE POINTS ARE ENOUGH TO SHOW IT.
#: Implied slack per anchor: **2.43 · 2.26 · 3.77**. The fitted 2.35 reproduces
#: the first two within 3 % (ratios 1.03 and 0.98) and under-predicts the third
#: by **28 %** — 28.3 GiB predicted against **36.1 GiB** measured, which left
#: ~4 GiB of headroom on a 40 GiB card where ~12 was expected.
#:
#: ⚠️ NOT REFITTED TO 3.77. That would over-predict both other anchors; it is a
#: one-parameter model against three disagreeing points, and forcing it would
#: trade a visible error for a hidden one. **The planner is therefore a LOWER
#: BOUND, not an estimate** — treat every figure it prints as "at least this
#: much", and never quote one as though it were measured.
#:
#: ⭐ THE PATTERN WORTH TESTING NEXT: both good anchors are seq 192 and the bad
#: one is seq 256, so the slack may scale with sequence length rather than being
#: flat. One more measurement at (bf16, 256, 16) would separate that from a
#: measurement-timing artefact — the readings are high-water marks and were not
#: all taken at the same point in training. Recorded as open, not guessed.
PLANNER_IS_A_LOWER_BOUND = True

#: ⚠️ AN EMPIRICAL FACTOR, NOT PHYSICS, AND IT IS NAMED THAT WAY ON PURPOSE.
#: The two anchors are **`nvidia-smi` RESERVED** memory, which is what a card must
#: actually hold: PyTorch's caching allocator keeps freed blocks, backward makes
#: transient copies, and fragmentation is real. Summing live tensors under-predicts
#: both runs by the same ratio once weights are set aside --
#: **2.43× (4-bit) and 2.26× (bf16)** -- so the slack multiplies the VARIABLE terms
#: only; quantized weights are a flat allocation and do not fragment.
#:
#: ⛔ FITTED TO TWO POINTS. It is a straight line through two measurements, not a
#: model. Re-anchor it the moment a third run disagrees, and never quote a plan
#: figure as though it were measured.
RUNTIME_SLACK = 2.35


def plan(params_b: float, dtype: str, seq: int, batch: int,
         grad_ckpt: bool, vocab: int = 152064) -> dict:
    """VRAM arithmetic, stated so it can be checked rather than trusted.

    ⛔⛔ THE ORIGINAL FORMULA OMITTED THE LOGITS AND WAS WRONG BY ~3.4x. It
    modelled activations as `params × seq × batch × constant` and predicted
    **4.6 GiB** for a job that used **15.5**. The missing term is the LM head
    output, which does not scale with parameter count at all -- it scales with
    **VOCABULARY**, and Qwen's is 152,064:

        batch 16 × seq 192 × 152,064 = 467 M logits

    Cross-entropy upcasts those to fp32 and keeps a gradient of the same shape,
    so the head alone costs ~5.6 GiB at batch 16 -- larger than everything the
    old formula counted. ⛔ A planner blind to vocab will under-size every
    large-vocab model in exactly the same way.

    ⚠️ Calibrated against two points and CONTRADICTED BY A THIRD (see
    `MEASURED`). It under-predicted run 4 by 28 %. **Treat the output as a LOWER
    BOUND**, not an estimate, and never quote it as though it were measured.
    """
    bytes_per = {"bf16": 2, "fp16": 2, "4bit": 0.55}[dtype]
    weights = params_b * bytes_per
    # LoRA params are ~0.5 % of base; Adam keeps 2 fp32 moments each.
    lora = params_b * 0.005 * (2 + 8)
    # Hidden-state activations. With checkpointing only layer boundaries are kept.
    act_per_tok = params_b * 0.00002 * (0.25 if grad_ckpt else 1.0)
    activations = act_per_tok * seq * batch
    # ⭐ THE TERM THAT WAS MISSING. logits + fp32 upcast + gradient ≈ 3 copies.
    logits = batch * seq * vocab * 4 * 3 / 1024 ** 3
    overhead = 1.6                      # cuda context + cuBLAS workspaces
    live_variable = lora + activations + logits + overhead
    total = weights + live_variable * RUNTIME_SLACK
    return {"weights_GiB": weights, "lora_optim_GiB": lora,
            "activations_GiB": activations, "logits_GiB": logits,
            "overhead_GiB": overhead, "slack": RUNTIME_SLACK,
            "live_variable_GiB": live_variable, "total_GiB": total,
            "dtype": dtype, "seq": seq, "batch": batch, "vocab": vocab,
            "grad_checkpointing": grad_ckpt}


def _fmt(p: dict, budget: float) -> str:
    # ⛔ The margin is against a LOWER BOUND, so "FITS" needs real room. Run 4
    # was predicted to fit with ~12 GiB spare and fit with ~4.
    fits = p["total_GiB"] <= budget - 1.0
    # ⛔ THE PRINTED EQUATION MUST BALANCE. A first version showed the live terms
    # and the slack-inflated total on one line, so it read "15.2 + 0.4 + 0.1 +
    # 5.2 + 1.6 = 32.4" — a sum that is off by 10 GiB in plain sight. A displayed
    # arithmetic that does not add up teaches the reader to stop checking it.
    return (f"  {p['dtype']:<5} seq {p['seq']:<4} batch {p['batch']:<3} "
            f"weights {p['weights_GiB']:5.1f} + (lora {p['lora_optim_GiB']:4.1f} "
            f"+ act {p['activations_GiB']:4.1f} + logits {p['logits_GiB']:4.1f} "
            f"+ oh {p['overhead_GiB']:3.1f}) × {p['slack']:.2f} "
            f"= {p['total_GiB']:5.1f} GiB   "
            f"{'FITS' if fits else '⛔ DOES NOT FIT'}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="HF id or local path. NO DEFAULT — Nate's call.")
    ap.add_argument("--out", default="runs/act2/adapter")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--params", type=float, default=7.0, help="billions, for --plan")
    ap.add_argument("--dtype", default="bf16", choices=["bf16", "fp16", "4bit"])
    ap.add_argument("--seq", type=int, default=256)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--accum", type=int, default=4)
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--rank", type=int, default=32)
    ap.add_argument("--vram", type=float, default=15.9)
    # ⭐ DIAGNOSIS C IS ONLY ANSWERABLE IF THE CURVE EXISTS. Saving per-epoch
    # gives 2 points, which cannot distinguish "rose then fell" (overtrained,
    # stop earlier) from "never rose" (not a training problem at all). The
    # diversity number is measured at each of these and plotted against step.
    ap.add_argument("--save-steps", type=int, default=0,
                    help="checkpoint every N steps for the diversity-vs-step curve")
    a = ap.parse_args()

    if a.plan:
        print(f"VRAM PLAN — {a.params}B params, budget {a.vram} GiB "
              f"(1 GiB held back for fragmentation)\n")
        for dt in ("bf16", "4bit"):
            for gc in (False, True):
                p = plan(a.params, dt, a.seq, a.batch, gc)
                tag = "grad-ckpt" if gc else "no ckpt  "
                print(f"  {tag} " + _fmt(p, a.vram)[2:])
        # ⛔ CHECKED ON THE MACHINE, NOT ASSERTED. This line said "NOT
        # INSTALLED" for twenty minutes after bitsandbytes was installed and a
        # 4-bit matmul verified on sm_120 — a hardcoded claim about the
        # environment is a claim that goes stale silently.
        try:
            import bitsandbytes as _bnb
            import torch as _t
            cap = _t.cuda.get_device_capability(0) if _t.cuda.is_available() else None
            print(f"\n  4bit: bitsandbytes {_bnb.__version__} present · "
                  f"GPU capability {cap}")
        except ImportError:
            print("\n⛔ 4bit needs bitsandbytes and it is NOT INSTALLED here.")
        print("⭐ Training sequences here are SHORT — a gloss (~100 tok) plus a "
              "Scene JSON (~80) — which is why the activation term is small.")
        meta = CORPUS / "meta.json"
        if meta.exists():
            m = json.loads(meta.read_text(encoding="utf-8"))
            steps = m["n_train"] * a.epochs / (a.batch * a.accum)
            print(f"\n  corpus {m['n_train']:,} pairs · worst-form exposure "
                  f"{m['exposure']['worst_form_exposure']}")
            print(f"  {a.epochs} epochs at batch {a.batch}×{a.accum} "
                  f"⇒ {steps:,.0f} optimizer steps")
        print("\n⛔ nothing loaded, nothing downloaded, nothing trained.")
        return 0

    if not a.model:
        raise SystemExit(
            "⛔ --model is required and has no default. The backbone is Nate's "
            "call every time; run --plan first to size the options.")

    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              DataCollatorForLanguageModeling, Trainer,
                              TrainingArguments)

    tok = AutoTokenizer.from_pretrained(a.model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    def fmt(row):
        # ⛔ Back-compatible: a corpus written before the read direction existed
        # has neither field, and must still train as it did. The formatting
        # itself lives in `row_to_text` so the token budget measures THIS fold.
        return tok(row_to_text(row, tok), truncation=True, max_length=a.seq)

    ds = load_dataset("json", data_files={
        "train": str(CORPUS / "train.jsonl"),
        "eval": str(CORPUS / "eval.jsonl")})
    ds = ds.map(fmt, remove_columns=ds["train"].column_names)

    kw: dict = {"dtype": torch.bfloat16, "device_map": "cuda"}
    if a.dtype == "4bit":
        from transformers import BitsAndBytesConfig
        kw["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
        kw.pop("dtype")
    model = AutoModelForCausalLM.from_pretrained(a.model, **kw)
    model = get_peft_model(model, LoraConfig(
        r=a.rank, lora_alpha=a.rank * 2, lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"]))
    model.print_trainable_parameters()

    trainer = Trainer(
        model=model, train_dataset=ds["train"], eval_dataset=ds["eval"],
        data_collator=DataCollatorForLanguageModeling(tok, mlm=False),
        args=TrainingArguments(
            output_dir=a.out, per_device_train_batch_size=a.batch,
            gradient_accumulation_steps=a.accum, num_train_epochs=a.epochs,
            learning_rate=a.lr, bf16=True, gradient_checkpointing=True,
            logging_steps=25, eval_strategy="steps", eval_steps=500,
            save_strategy=("steps" if a.save_steps else "epoch"),
            save_steps=(a.save_steps or 500),
            save_total_limit=(None if a.save_steps else 2),
            report_to=[], seed=20620))
    trainer.train()
    trainer.save_model(a.out)
    print(f"\n⭐ adapter → {a.out}")
    print("⛔ NOT a result. Next: tools/act2_flocal.py measures F-LOCAL "
          "unconstrained and cardless. That is the gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
