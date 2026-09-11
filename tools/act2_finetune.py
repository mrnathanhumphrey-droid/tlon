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

#: ⛔⛔ WAS HARDCODED, AND THE MULTI-TURN PIPELINE WOULD HAVE DIED ON IT AFTER
#: THE TOKEN GATE PASSED — burning box time to discover a missing flag. The
#: trainer, the token counter and the pipeline must all point at the SAME
#: corpus, and the only way to guarantee that is to make it an argument.
_DEFAULT_CORPUS = (pathlib.Path(__file__).resolve().parents[1]
                   / "runs" / "act2" / "corpus")
CORPUS = _DEFAULT_CORPUS

#: ⛔⛔ ONE PROMPT PER DIRECTION. Training both tasks under a single instruction
#: would force the model to GUESS which one it is on from the input alone, and
#: the two inputs are the two languages — exactly the discrimination that failed.
from tlon.act2.full_weight import apply_scope as _apply_scope
from tlon.act2.full_weight import apply_mapping_scope as _apply_mapping_scope
from tlon.act2.collator import PositionMaskedCollator
from tlon.act2.weight_delta import INSTRUMENT_FAULT as _FAULT
from tlon.act2.weight_delta import OK as _DELTA_OK
from tlon.act2.weight_delta import measure as _delta_measure
from tlon.act2.weight_delta import snapshot as _delta_snapshot
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
         grad_ckpt: bool, vocab: int = 152064, *,
         trainable_b: float | None = None, moment_bytes: float = 2) -> dict:
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
    # ⛔⛔ THE FULL-WEIGHT ARM HAS A DIFFERENT FIXED COST BY TWO ORDERS OF
    # MAGNITUDE, AND A PLANNER THAT QUIETLY ANSWERS FOR THE LoRA ONE IS WORSE
    # THAN NO PLANNER. The LoRA optimizer term is 0.381 GiB; full-weight AdamW
    # over 6.53 B in fp32 is 91.44 -- 240x. PREREG a0450b36 §5 sizes the run on
    # THIS arithmetic, so it lives here where it can be checked, not in a
    # session's scratch script.
    if trainable_b is None:
        weights = params_b * bytes_per
        # LoRA params are ~0.5 % of base; Adam keeps 2 fp32 moments each.
        lora = params_b * 0.005 * (2 + 8)
        master = grads = moments = 0.0
    else:
        if not 0 < trainable_b <= params_b:
            raise ValueError("trainable_b %r outside (0, %r]"
                             % (trainable_b, params_b))
        # ⭐ Frozen weights stay in the resident dtype (they take no update, so
        # their precision buys nothing); trainable weights are the fp32 MASTER,
        # which is what lets a 1e-5 step land at all -- see §4.1.
        master = trainable_b * 4
        weights = (params_b - trainable_b) * bytes_per + master
        grads = trainable_b * 4
        moments = trainable_b * moment_bytes
        lora = 0.0
    # Hidden-state activations. With checkpointing only layer boundaries are kept.
    act_per_tok = params_b * 0.00002 * (0.25 if grad_ckpt else 1.0)
    activations = act_per_tok * seq * batch
    # ⭐ THE TERM THAT WAS MISSING. logits + fp32 upcast + gradient ≈ 3 copies.
    logits = batch * seq * vocab * 4 * 3 / 1024 ** 3
    overhead = 1.6                      # cuda context + cuBLAS workspaces
    live_variable = lora + activations + logits + overhead
    # ⛔ Gradients and optimizer moments are FLAT allocations, like weights, so
    # the slack (which models fragmentation of the churning terms) must not
    # multiply them. Folding them into `live_variable` would inflate the full-
    # weight estimate by 2.35x and reject configurations that fit.
    total = weights + grads + moments + live_variable * RUNTIME_SLACK
    return {"weights_GiB": weights, "lora_optim_GiB": lora,
            "master_GiB": master, "grads_GiB": grads, "moments_GiB": moments,
            "trainable_b": trainable_b,
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


def probe_optim(*, lr: float = 1e-5, steps: int = 20) -> int:
    """⛔⛔ PROVE THE OPTIMIZER CAN WRITE, BEFORE ANY GPU TIME IS BOUGHT.

    PREREG a0450b36 §5 declares `adamw_bnb_8bit` over an fp32 master, and §4.1
    records the arithmetic for why: under a bf16 master a 1e-5 Adam step is
    0.08 ulp at a typical Qwen weight and rounds to zero, so the optimizer
    writes nothing while appearing to train. That claim is arithmetic on paper.
    This runs it ON THE BOX, on two tensors, in under a second:

      * fp32 master  — the declared config. The value MUST change.
      * bf16 master  — the rejected one. Expected NOT to change, which is the
        on-hardware confirmation that the dead zone is real here and not just
        in a docstring.

    ⭐ It also fails if `bitsandbytes` is missing or its wheel will not load —
    the thing that would otherwise be discovered after the model has downloaded
    and the first step is attempted, hours into a paid run.

    ⛔ THIS IS `assert_the_mutation` AS A PRE-FLIGHT. The probe does not check
    that an optimizer object was constructed; it checks that a number moved.
    """
    import torch
    print("⭐ OPTIMIZER WRITE PROBE — PREREG a0450b36 §4.1/§5, lr=%g" % lr)
    try:
        import bitsandbytes as bnb
    except Exception as exc:                                     # noqa: BLE001
        print("⛔⛔ bitsandbytes will not import: %r\n"
              "   §5 declares adamw_bnb_8bit and fp32 moments DO NOT FIT on 80 "
              "GiB. Without this wheel there is no declared config to run."
              % (exc,))
        return 1
    print("   bitsandbytes %s" % getattr(bnb, "__version__", "?"))

    # ⭐ 0.02 is Qwen's own `initializer_range`, read from its config.json — the
    # magnitude §4.1's arithmetic is about, not a round number chosen here.
    results = {}
    for name, dtype in (("fp32 (declared)", torch.float32),
                        ("bf16 (rejected)", torch.bfloat16)):
        p = torch.nn.Parameter(torch.full((256,), 0.02, dtype=dtype))
        before = p.detach().clone().float()
        try:
            opt = bnb.optim.AdamW8bit([p], lr=lr)
        except Exception as exc:                                 # noqa: BLE001
            print("⛔⛔ AdamW8bit would not instantiate on %s: %r" % (name, exc))
            return 1
        for _ in range(steps):
            opt.zero_grad()
            # A constant gradient: Adam normalises it, so the step size is ~lr
            # regardless of the magnitude here. That is exactly why the ulp
            # comparison in §4.1 is against `lr` and not against the gradient.
            p.grad = torch.full_like(p, 1e-3)
            opt.step()
        moved = int((p.detach().float() != before).sum().item())
        results[name] = moved
        print("   %-16s %3d/256 values changed after %d steps"
              % (name, moved, steps))

    ok_fp32 = results["fp32 (declared)"] > 0
    dead_bf16 = results["bf16 (rejected)"] == 0
    if not ok_fp32:
        print("⛔⛔ THE DECLARED CONFIG CANNOT WRITE AN UPDATE ON THIS BOX. "
              "Training would produce a zero weight delta and §4.1 would "
              "correctly refuse to read any verdict. Do not train.")
        return 1
    print("   ✅ the declared fp32-master config writes the update")
    if dead_bf16:
        print("   ✅ and the bf16 dead zone is CONFIRMED ON THIS HARDWARE — "
              "the rejected config writes nothing, exactly as §4.1 predicts")
    else:
        # ⚠️ NOT A FAILURE. The declared config is what runs; a bf16 that moves
        # here only means this box rounds more favourably than the worst case.
        # Reported rather than silently passed, because it is evidence about
        # §4.1's arithmetic and evidence is not discarded for being convenient.
        print("   ⚠️ bf16 moved %d values — the dead zone is narrower on this "
              "hardware than §4.1's worst case. Does not affect the declared "
              "run; recorded because it bears on the §4.1 reasoning."
              % results["bf16 (rejected)"])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="HF id or local path. NO DEFAULT — Nate's call.")
    ap.add_argument("--out", default="runs/act2/adapter")
    ap.add_argument("--corpus", default=str(_DEFAULT_CORPUS),
                    help="corpus directory holding train.jsonl / eval.jsonl")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--params", type=float, default=7.0, help="billions, for --plan")
    ap.add_argument("--dtype", default="bf16", choices=["bf16", "fp16", "4bit"])
    ap.add_argument("--seq", type=int, default=256)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--accum", type=int, default=4)
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--rank", type=int, default=32)
    # ⛔⛔ THE FULL-WEIGHT ARM. PREREG a0450b36 §5. Neither of the two flags it
    # needs has a default: the layer scope is what a STOP-floored would be ABOUT
    # (§7.1's ladder is written in terms of it) and the optimizer is the choice
    # that decides whether the update can be written at all (§4.1). A default on
    # either would be that decision taken quietly, in the file whose own
    # docstring refuses to default the backbone for the same reason.
    ap.add_argument("--full", action="store_true",
                    help="FULL-WEIGHT fine-tune (no LoRA), per PREREG a0450b36 "
                         "§5. Requires --unfreeze-top and --optim.")
    ap.add_argument("--scope-mode", choices=("layers", "mapping"),
                    default="layers",
                    help="WHICH weights may move. 'layers' = the top "
                         "--unfreeze-top transformer layers (rungs 1a/1b/1b', "
                         "mapping frozen). 'mapping' = embed_tokens + lm_head "
                         "ONLY with every layer frozen (rung 2: does release "
                         "live in the token mapping?).")
    ap.add_argument("--stack", default=None,
                    help="prefix of the transformer-layer stack to train, "
                         "e.g. language_model.model. REQUIRED on a base "
                         "with more than one stack: a multimodal "
                         "checkpoint carries a vision tower whose layer "
                         "indices pool with the text model's into a set "
                         "that looks perfectly contiguous, and the scope "
                         "then trains an image encoder as if it were part "
                         "of the language model. Refused rather than "
                         "guessed; single-stack bases need no value.")
    ap.add_argument("--unfreeze-top", type=int, default=None,
                    help="train the top N transformer layers; everything below, "
                         "plus embed_tokens and lm_head, is frozen. §5 = 14.")
    ap.add_argument("--optim", default=None,
                    help="HF optimizer id. §5 = adamw_bnb_8bit (fp32 master "
                         "params, 8-bit moments -- fp32 moments do not fit).")
    # ⛔ WITHOUT THIS, `--plan` ANSWERS FOR THE OTHER ARM. The planner prints
    # LoRA rows by default, so sizing a full-weight run with it would report
    # 26 GiB for a job that needs 51 -- the wrong number, in the confident shape
    # of a right one. Billions of TRAINABLE parameters; §5 = 3.263.
    ap.add_argument("--trainable-params", type=float, default=None,
                    help="billions of trainable params, for --plan on the "
                         "full-weight arm. §5 = 3.263 (top 14 of 28 layers).")
    ap.add_argument("--moment-bytes", type=float, default=2,
                    help="optimizer moment bytes per param: 2 = 8-bit m+v "
                         "(§5), 8 = fp32 m+v.")
    # ⛔⛔ THE DELTA IS MEASURED FROM THE BASE MODEL, ACROSS EVERY LEG. §5's
    # epoch-1 early-stop means epoch 2 starts from the epoch-1 model, so a
    # snapshot taken at the start of leg 2 would measure ONE EPOCH of movement
    # and call it the total. A run whose first epoch moved the weights and whose
    # second did not would then read INSTRUMENT FAULT — the guard firing on a
    # run that worked. The snapshot is carried instead.
    ap.add_argument("--delta-snapshot-out", default=None,
                    help="write the §4.1 init snapshot here (leg 1)")
    # ⛔⛔ THE DIAGNOSTIC PAIR. `--max-steps` buys the TRACE, not the model:
    # the collapse hit by ~50 last time, so a few hundred steps captures it for a
    # fraction of a full epoch. `--trace-out` records loss + per-module
    # finiteness on grad/weight/moment every step, which is the only thing that
    # separates the three causes that all look like loss->0 from outside.
    ap.add_argument("--max-steps", type=int, default=0,
                    help="stop after N optimizer steps (0 = full epochs). "
                         "Diagnostic runs buy the trace, not the model.")
    # ⛔⛔ THE PRIME-SUSPECT ABLATION. Gradient checkpointing on a
    # partially-frozen stack is what forced `enable_input_require_grads()`, and
    # the two come off together: without checkpointing there is no reentrant
    # segment whose input must be made to require grad. The memory case for
    # keeping them is 0.5 GiB (51.4 -> 51.8 planner at seq 384 batch 4), because
    # the activation term is tiny at these sequence lengths -- the footprint is
    # optimizer state and 152k-vocab logits. Half a gigabyte was not worth the
    # hazard.
    # ⛔⛔ THE ONE MAJOR COMPONENT THAT HAS NEVER BEEN A VARIABLE. Every run of
    # this arm loaded the model without `attn_implementation`, so every run used
    # the transformers default — the fused SDPA kernel — and it has been a
    # CONSTANT across all four failures rather than a thing under test.
    # ⭐ It is where the contradiction points. The textbook attention backward
    # says dQ = dS @ K, so `grad_K` finite implies dS finite, and dS and K both
    # finite should leave dQ finite. The measurement says dQ is NaN anyway. When
    # the math and the observation disagree the answer is in what the kernel
    # actually does, so the kernel has to be ablatable.
    ap.add_argument("--attn-impl", default=None,
                    choices=("eager", "sdpa", "flash_attention_2"),
                    help="attention implementation. Omit to take the "
                         "transformers default (sdpa), which is what every run "
                         "of this arm has silently used. `eager` is the "
                         "unfused reference path.")
    # ⛔⛔ THE COMPARISON NO RUN-VS-RUN CAN MAKE. Every kernel comparison so far
    # differed in trajectory as well as in kernel. At `on_pre_optimizer_step`
    # the optimizer has not stepped yet, so the same weights and the same
    # micro-batches can be pushed through twice with nothing changed but the
    # attention implementation.
    ap.add_argument("--kernel-duel-at", type=int, default=0,
                    help="at this optimizer step, re-run the step's own "
                         "micro-batches under BOTH attention implementations "
                         "from identical weights, then stop. 0 = off.")
    ap.add_argument("--duel-against", default="eager",
                    choices=("eager", "sdpa", "flash_attention_2"),
                    help="the implementation to duel the running one against")
    ap.add_argument("--no-grad-checkpointing", action="store_true",
                    help="disable gradient checkpointing AND the "
                         "enable_input_require_grads() it necessitates")
    ap.add_argument("--trace-window-from", type=int, default=10,
                    help="first step to capture per-module ACTIVATION "
                         "magnitudes (expensive; the break is known to be at 13)")
    ap.add_argument("--trace-window-to", type=int, default=14)
    ap.add_argument("--trace-out", default=None,
                    help="JSONL per-step trace: loss, per-module finiteness on "
                         "gradient AND weight AND optimizer moment, in order.")
    ap.add_argument("--delta-snapshot-in", default=None,
                    help="measure against THIS snapshot instead of the weights "
                         "at the start of this leg (leg 2+)")
    # ⛔⛔ WAS HARDCODED `seed=20620`. That made "run the recipe again" impossible
    # to express: the reproducibility probe needs to RE-ROLL what the recipe
    # re-rolls, and a welded seed silently pins the trainer while the caller
    # believes they varied it. Discovered when B-fresh and adapter_mt turned out
    # to share a seed yet differ by 0.133 on ki-emission — the divergence was the
    # CORPUS DRAW, not the seed, and the seed could not have been varied anyway.
    ap.add_argument("--seed", type=int, default=20620,
                    help="drives the trainer (init, shuffle, dropout). Pair it "
                         "with act2_build_multiturn.py --seed to re-roll the "
                         "whole recipe.")
    ap.add_argument("--vram", type=float, default=15.9)
    # ⭐ DIAGNOSIS C IS ONLY ANSWERABLE IF THE CURVE EXISTS. Saving per-epoch
    # gives 2 points, which cannot distinguish "rose then fell" (overtrained,
    # stop earlier) from "never rose" (not a training problem at all). The
    # diversity number is measured at each of these and plotted against step.
    ap.add_argument("--save-steps", type=int, default=0,
                    help="checkpoint every N steps for the diversity-vs-step curve")
    ap.add_argument("--probe-optim", action="store_true",
                    help="$0 pre-flight: prove the declared optimizer can "
                         "actually WRITE an update on this box. No model, no "
                         "download, no training.")
    a = ap.parse_args()
    global CORPUS
    CORPUS = pathlib.Path(a.corpus)

    if a.probe_optim:
        return probe_optim(lr=a.lr if a.lr != 1e-4 else 1e-5)

    if a.plan:
        print(f"VRAM PLAN — {a.params}B params, budget {a.vram} GiB "
              f"(1 GiB held back for fragmentation)\n")
        if a.trainable_params:
            # ⭐ THE FULL-WEIGHT ROWS, AND THE +28 % ALONGSIDE. The planner is a
            # documented LOWER BOUND that under-predicted its closest anchor by
            # 28 %; printing only the raw figure invites someone to read a bound
            # as an estimate and launch on 3 GiB of margin.
            print(f"  FULL-WEIGHT arm: {a.trainable_params}B trainable of "
                  f"{a.params}B, moments {a.moment_bytes} B/param\n")
            for gc in (False, True):
                p = plan(a.params, "bf16", a.seq, a.batch, gc,
                         trainable_b=a.trainable_params,
                         moment_bytes=a.moment_bytes)
                tag = "grad-ckpt" if gc else "no ckpt  "
                print(f"  {tag} bf16  seq {p['seq']:<4} batch {p['batch']:<3} "
                      f"master {p['master_GiB']:5.1f} + grads "
                      f"{p['grads_GiB']:5.1f} + moments {p['moments_GiB']:4.1f} "
                      f"+ frozen "
                      f"{p['weights_GiB'] - p['master_GiB']:5.1f} + var "
                      f"{p['live_variable_GiB'] * p['slack']:5.1f} "
                      f"= {p['total_GiB']:5.1f} GiB   "
                      f"+28% -> {p['total_GiB'] * 1.28:5.1f}   "
                      f"{'FITS' if p['total_GiB'] * 1.28 <= a.vram else '⛔ DOES NOT FIT'}")
            print("\n⛔ nothing loaded, nothing downloaded, nothing trained.")
            return 0
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

    # ⛔⛔ THE TWO SCOPES TAKE DIFFERENT ARGUMENTS, AND MIXING THEM MUST NOT BE
    # SILENT. `--unfreeze-top` on a mapping run would name a layer count that
    # nothing applies, so the log would describe a scope the run did not have --
    # and on a floor-hunting rung that is a mislabelled finding, not a typo.
    if a.full and a.scope_mode == "mapping":
        if a.unfreeze_top is not None:
            raise SystemExit(
                "⛔ --scope-mode mapping trains embed_tokens + lm_head with "
                "ALL layers frozen, so --unfreeze-top names nothing. Passing "
                "both would log a layer scope this run does not have.")
        if not a.optim:
            raise SystemExit("⛔ --full requires --optim (§4.1).")
    elif a.full and (a.unfreeze_top is None or not a.optim):
        raise SystemExit(
            "⛔ --full requires BOTH --unfreeze-top and --optim, neither of "
            "which has a default. The layer scope is what a STOP-floored "
            "verdict would be about (PREREG a0450b36 §7.1) and the optimizer "
            "decides whether the update can be written at all (§4.1). §5 "
            "declares --unfreeze-top 14 --optim adamw_bnb_8bit.")
    if not a.full and a.scope_mode != "layers":
        raise SystemExit(
            "⛔ --scope-mode is a full-weight flag and does nothing on the "
            "LoRA path. Silently ignoring it would let a caller believe they "
            "had set a scope that was never applied.")
    if not a.full and (a.unfreeze_top is not None or a.optim):
        raise SystemExit(
            "⛔ --unfreeze-top / --optim are full-weight flags and do nothing "
            "on the LoRA path. Silently ignoring them would let a caller "
            "believe they had set a scope that was never applied.")

    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model
    from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer,
                              TrainingArguments)

    tok = AutoTokenizer.from_pretrained(a.model)
    # ⛔⛔ SAY SO WHEN IT FIRES. This substitution never happened once while Qwen
    # was the only base (Qwen has a distinct pad token), so nothing in any log
    # of this arc records it — and on Mistral-7B-v0.3 it silently made pad and
    # eos the same token, which the by-id collator then masked wholesale. A
    # default that is never printed is a decision nobody made.
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
        print("⚠️ this base has NO pad token — pad := eos (%r, id %s). Labels "
              "are masked BY POSITION, so genuine end-of-sequence tokens are "
              "still trained." % (tok.eos_token, tok.eos_token_id))
    print("⭐ pad %r (%s) · eos %r (%s) · pad_is_eos=%s"
          % (tok.pad_token, tok.pad_token_id, tok.eos_token, tok.eos_token_id,
             tok.pad_token_id == tok.eos_token_id))

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
    if a.attn_impl:
        kw["attn_implementation"] = a.attn_impl
    if a.dtype == "4bit":
        from transformers import BitsAndBytesConfig
        kw["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
        kw.pop("dtype")
    model = AutoModelForCausalLM.from_pretrained(a.model, **kw)
    # ⛔⛔ RECORD THE RESOLVED KERNEL, ALWAYS, ASKED FOR OR NOT. Four runs used
    # the fused SDPA path and not one of them said so anywhere, which is how a
    # load-bearing component stays a constant nobody notices. A default that is
    # never printed is a decision nobody made.
    print("⭐ attention implementation RESOLVED TO: %r (requested: %r)"
          % (getattr(model.config, "_attn_implementation", "unknown"),
             a.attn_impl))
    snap = scope = None
    if a.full:
        if a.dtype == "4bit":
            raise SystemExit(
                "⛔ --full with 4-bit weights is not the declared arm. §5 is an "
                "fp32 master over bf16-resident frozen weights; quantised base "
                "weights cannot hold an fp32 update.")
        if a.scope_mode == "mapping":
            # ⛔⛔ RUNG 2. Trainable = `embed_tokens` + `lm_head` ONLY, every
            # transformer layer frozen. The selection is POSITIVE and per-leaf
            # because this rung's expected outcome is a FLOOR: a selector that
            # matched nothing would train a frozen model, report a zero delta,
            # and read as exactly the finding being tested for.
            scope = _apply_mapping_scope(model, stack=a.stack)
            print("⭐ FULL-WEIGHT scope — MAPPING ONLY (embed_tokens + lm_head), "
                  "all %d transformer layers FROZEN: %s trainable / %s frozen"
                  % (scope["n_layers"],
                     f"{scope['n_trainable_params']:,}",
                     f"{scope['n_frozen_params']:,}"))
            print("   trainable tensors: %s" % sorted(scope["trainable"]))
        else:
            scope = _apply_scope(model, unfreeze_top=a.unfreeze_top,
                                 stack=a.stack)
            print("⭐ FULL-WEIGHT scope — top %d of %d layers trainable: "
                  "%s trainable / %s frozen params"
                  % (scope["unfreeze_top"], scope["n_layers"],
                     f"{scope['n_trainable_params']:,}",
                     f"{scope['n_frozen_params']:,}"))
        # ⛔⛔ FROZEN EMBEDDINGS + GRADIENT CHECKPOINTING = SILENTLY NO GRADIENTS.
        # With embed_tokens frozen, the input to the first checkpointed block
        # does not require grad, and reentrant checkpointing then skips the
        # backward through that segment entirely -- every trainable layer gets
        # NO gradient, training "succeeds", and the weights do not move. That is
        # the §4.1 failure arriving through a completely different door, which
        # is why the precondition is on the table rather than on the optimizer.
        if a.no_grad_checkpointing:
            # ⭐ NOT CALLED, and that is the point of the ablation. This exists
            # solely so a reentrant checkpoint segment has an input requiring
            # grad; with checkpointing off it would instead force autograd to
            # build a graph through the FROZEN bottom 14 layers, storing
            # activations nothing will ever use.
            print("⭐ ABLATION: gradient checkpointing OFF, and "
                  "enable_input_require_grads() NOT called")
        else:
            model.enable_input_require_grads()
        if a.delta_snapshot_in:
            # ⭐ CARRIED FROM LEG 1, so the delta stays "movement from the BASE
            # model" no matter how many legs §5's early-stop rule produces.
            snap = torch.load(a.delta_snapshot_in, weights_only=False)
            print("⭐ §4.1 snapshot LOADED from %s (%d tensors) — the delta is "
                  "measured from the base model, not from this leg's start"
                  % (a.delta_snapshot_in, len(snap)))
        else:
            # ⭐ Taken AFTER the fp32 cast and BEFORE the first step: the
            # snapshot must describe the tensors the optimizer will write to.
            snap = _delta_snapshot(model.named_parameters(), seed=a.seed)
            print("⭐ §4.1 snapshot: %d trainable tensors sampled" % len(snap))
        if a.delta_snapshot_out:
            pathlib.Path(a.delta_snapshot_out).parent.mkdir(parents=True,
                                                            exist_ok=True)
            torch.save(snap, a.delta_snapshot_out)
            print("⭐ §4.1 snapshot -> %s" % a.delta_snapshot_out)
    else:
        model = get_peft_model(model, LoraConfig(
            r=a.rank, lora_alpha=a.rank * 2, lora_dropout=0.05, bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                            "gate_proj", "up_proj", "down_proj"]))
        model.print_trainable_parameters()

    trainer = Trainer(
        model=model, train_dataset=ds["train"], eval_dataset=ds["eval"],
        # ⛔⛔ BY POSITION, NOT BY TOKEN ID. `DataCollatorForLanguageModeling`
        # masks `labels[labels == pad_token_id] = -100`, which on a base whose
        # pad IS its eos masks every genuine end-of-sequence and never trains
        # the model to STOP. That destroyed run 3a. See tlon/act2/collator.py.
        data_collator=PositionMaskedCollator(tok),
        args=TrainingArguments(
            output_dir=a.out, per_device_train_batch_size=a.batch,
            gradient_accumulation_steps=a.accum, num_train_epochs=a.epochs,
            learning_rate=a.lr, bf16=True,
            gradient_checkpointing=not a.no_grad_checkpointing,
            # ⛔ ONE SOURCE FOR THIS VALUE. It was `logging_steps=25` here PLUS a
            # conditional `**{"logging_steps": 1}` below, which is a duplicate
            # keyword and a TypeError — caught only on the box, after the model
            # had loaded. A conditional that ADDS a key a literal already sets
            # is not a conditional, it is a collision.
            logging_steps=(1 if a.trace_out else 25),
            eval_strategy="steps", eval_steps=500,
            save_strategy=("steps" if a.save_steps else "epoch"),
            save_steps=(a.save_steps or 500),
            save_total_limit=(None if a.save_steps else 2),
            report_to=[], seed=a.seed,
            # ⛔⛔ OFF WHEN TRACING. Default True makes transformers SUBSTITUTE
            # the running average whenever the loss is NaN or Inf, which is why
            # the failing run logged "loss -> 0" and never once logged nan.
            **({"logging_nan_inf_filter": False} if a.trace_out else {}),
            **({"max_steps": a.max_steps} if a.max_steps else {}),
            **({"optim": a.optim} if a.full else {})))
    trace = None
    if a.trace_out:
        from tlon.act2.step_trace import (ForwardProbe, PreClipGradProbe,
                                          StepTrace, make_callback)
        trace = StepTrace(a.trace_out)
        # ⛔⛔ THE RAW LOSS, FROM THE MODEL OUTPUT. `logging_nan_inf_filter` is
        # off above, but that only un-masks what the LOGGER prints; the arbiter
        # is the value the model returned, captured here before anything can
        # substitute for it. The founding symptom of this whole investigation —
        # "loss 7.548 -> 0" — was that substitution, and the first version of
        # this trace read the logged number and inherited the mask.
        holder = {"raw": None}
        _orig_compute_loss = trainer.compute_loss

        def _capture(model, inputs, *args, **kw):
            out = _orig_compute_loss(model, inputs, *args, **kw)
            loss = out[0] if isinstance(out, tuple) else out
            try:
                holder["raw"] = float(loss.detach().float())
            except Exception:                                    # noqa: BLE001
                holder["raw"] = None
            return out

        trainer.compute_loss = _capture
        # ⭐ Windowed around the KNOWN break. The failure is deterministic at
        # step 13 across two runs with different assemblies, so the instrument
        # is pointed rather than swept.
        window = set(range(max(0, a.trace_window_from), a.trace_window_to + 1))
        probe = ForwardProbe(model, window=window)
        # ⛔⛔ THE SCAN THIS RUN EXISTS FOR. Everything the trace has said about
        # gradients so far was measured AFTER `clip_grad_norm_`, whose norm is
        # GLOBAL — one tensor's overflow becomes a non-finite coefficient on all
        # 168. `register_post_accumulate_grad_hook` fires inside the backward,
        # before any clip exists, so this is the first look at the origin rather
        # than at what the origin was spread onto.
        preclip = PreClipGradProbe(model, window=window)
        trainer.add_callback(make_callback(trace, probe=probe, preclip=preclip,
                                           loss_holder=holder))
        print("⭐ per-step trace -> %s (magnitude window %s)"
              % (a.trace_out, sorted(window)))
        print("⭐ PRE-CLIP gradient hook armed on %d trainable tensors"
              % len(preclip.names))

    if a.kernel_duel_at:
        from transformers import TrainerCallback

        from tlon.act2.kernel_duel import (compare, flip_attn_implementation,
                                           run_leg)
        # ⛔ CAPTURE THE STEP'S OWN MICRO-BATCHES. The duel is worthless on a
        # freshly drawn batch: the whole point is that THIS batch, at THIS step,
        # is the one the fused kernel fails on.
        duel = {"batches": [], "step": 0, "done": False}
        _orig_training_step = trainer.training_step

        def _capture_step(model, inputs, *args, **kw):
            if duel["step"] == a.kernel_duel_at and not duel["done"]:
                duel["batches"].append({k: v for k, v in inputs.items()})
            return _orig_training_step(model, inputs, *args, **kw)

        trainer.training_step = _capture_step

        class _Duel(TrainerCallback):
            def on_step_end(self, args_, state, control, **kw):
                duel["step"] += 1
                return control

            def on_pre_optimizer_step(self, args_, state, control, **kw):
                if duel["step"] != a.kernel_duel_at or duel["done"]:
                    return control
                duel["done"] = True
                m = kw.get("model")
                # ⛔ THE TRAINER'S OWN READING IS PRE-CLIP AND COMES FROM THE
                # PROBE. `p.grad` here is POST-clip -- the clip ran three lines
                # earlier in the trainer and its norm is global.
                tr = (preclip.snapshot()[0] if a.trace_out else None)
                tr = (None if tr is None
                      else {n: (r, f, None) for n, (r, f, _) in tr.items()})
                running = m.config._attn_implementation
                print("\n⭐⭐ KERNEL DUEL at step %d — %d micro-batches, "
                      "identical weights (the optimizer has NOT stepped)"
                      % (a.kernel_duel_at, len(duel["batches"])))
                l_sd, g_sd = run_leg(m, duel["batches"], accum=a.accum)
                flip_attn_implementation(m, a.duel_against)
                l_eg, g_eg = run_leg(m, duel["batches"], accum=a.accum)
                flip_attn_implementation(m, running)
                m.zero_grad(set_to_none=True)
                rep = compare(tr, g_sd, g_eg)
                rep.update({"step": a.kernel_duel_at, "running_impl": running,
                            "duel_impl": a.duel_against,
                            "loss_%s" % running: l_sd,
                            "loss_%s" % a.duel_against: l_eg})
                print("   losses %-6s: %s" % (running, [round(x, 4) for x in l_sd]))
                print("   losses %-6s: %s" % (a.duel_against, [round(x, 4) for x in l_eg]))
                print("   %-6s non-finite grads: %d %s"
                      % (running, rep["our_sdpa_nonfinite_n"], rep["our_sdpa_first"]))
                print("   %-6s non-finite grads: %d %s"
                      % (a.duel_against, rep["our_eager_nonfinite_n"], rep["our_eager_first"]))
                print("   trainer's own pre-clip non-finite: %s"
                      % rep["trainer_sdpa_nonfinite_n"])
                print("\n   ⭐ VERDICT: %s" % rep["verdict"])
                print("      %s" % rep["why"])
                if a.trace_out:
                    import json as _json
                    import pathlib as _pl
                    p = _pl.Path(a.trace_out).with_name("kernel_duel.json")
                    p.write_text(_json.dumps(rep, indent=2), encoding="utf-8")
                    print("   ⭐ duel -> %s" % p)
                control.should_training_stop = True
                return control

        trainer.add_callback(_Duel())
        print("⭐ kernel duel armed at step %d: %s vs %s"
              % (a.kernel_duel_at, "running impl", a.duel_against))

    trainer.train()
    if trace is not None:
        trace.close({"first_nonfinite": trace.first_nonfinite,
                     "steps_recorded": trace.step})
        print("⭐ trace closed: %d steps, first non-finite = %s"
              % (trace.step, trace.first_nonfinite))
    # ⛔ A capped diagnostic run still saves, because the weight_delta needs
    # real weights to compare -- but it is NOT a usable model and nothing
    # downstream should read it as one.
    trainer.save_model(a.out)

    if a.full:
        # ⛔⛔ THE §4.1 PRECONDITION, COMPUTED HERE AND NOWHERE ELSE. It is
        # written beside the weights it describes, in the process that trained
        # them, because the comparison is against tensors that exist only here.
        rep = _delta_measure(model.named_parameters(), snap, lr=a.lr)
        rep["scope"] = {k: v for k, v in scope.items()
                        if k not in ("trainable", "frozen")}
        out = pathlib.Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "weight_delta.json").write_text(
            json.dumps(rep, indent=2), encoding="utf-8")
        print("\n%s §4.1 WEIGHT DELTA: %s" % (
            "⭐" if rep["verdict"] == _DELTA_OK else "⛔⛔", rep["verdict"]))
        print("   fraction changed %.4f · working predicts 1.0 · bf16 dead "
              "zone predicts %.4f" % (rep["fraction_changed"],
                                      rep["prediction_bf16_dead_zone"]))
        print("   " + rep["why"])
        if rep["verdict"] == _FAULT:
            # ⛔ NON-ZERO EXIT. The pipeline's `step` wrapper stops on it, so a
            # faulted run cannot walk on to F-LOCAL and the lag read and arrive
            # at a verdict table that §4.1 says may not be read.
            print("⛔⛔ NO ROW OF THE VERDICT TABLE MAY BE READ. The weights "
                  "did not move; this is not evidence about the substrate.")
            return 3
        print(f"\n⭐ full-weight model → {a.out}")
    else:
        print(f"\n⭐ adapter → {a.out}")
    print("⛔ NOT a result. Next: tools/act2_flocal.py measures F-LOCAL "
          "unconstrained and cardless. That is the gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
