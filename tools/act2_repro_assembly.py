"""WHICH ELEMENT OF THE ASSEMBLY BREAKS THE FULL-WEIGHT RUN — an ablation, not a repro.

    python tools/act2_repro_assembly.py            # the full grid
    python tools/act2_repro_assembly.py --steps 80

⛔⛔ A REPRO THAT ONLY REPRODUCES CONFIRMS THE REGION AND NAMES NOTHING. The
`fw-s20624` run (2026-09-06) collapsed to ~0 loss within ~50 steps and finished
with NaN in all 70 of its 1-D trainable tensors and none of its 98 weight
matrices. Four mechanisms were excluded by positive test — 8-bit quantisation
(those tensors never used 8-bit state; `min_8bit_size` is 4096), size-dependent
NaN propagation, the label path, and second-moment underflow. Every isolated
component is clean, which localises the fault to an INTERACTION, and
interactions do not appear in component tests by construction.

⭐ So this varies the assembly instead of rebuilding it. Four elements were
introduced by `apply_scope` and the full-weight branch, none of them standard
HF, and each is toggled independently:

    mixed_dtype  frozen params bf16 while trainable are fp32
    grad_ckpt    gradient checkpointing on a partially-frozen stack
    input_grads  enable_input_require_grads(), needed because embeddings froze
    autocast     bf16 autocast around an fp32-master model

⛔⛔ AND THE SUCCESS SIGNAL IS NOT "NO NaN". The 98 undamaged matrices moved a
median 3.25e-3 relative over 3,760 steps — even the healthy part barely trained,
so the loss collapse is the ROOT event and the NaN is downstream. A
configuration that stays finite while the loss sits at zero has fixed a symptom.
HEALTHY means the loss DESCENDS from its start and the trainable weights MOVE.

⭐ And the fingerprint is what to watch: the real failure poisoned every 1-D
parameter and no 2-D one. This reports `nan_1d` and `nan_2d` separately, because
the toggle that makes the 1-D params survive is the culprit.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.act2.full_weight import full_weight_scope

#: ⭐ THE REAL ARCHITECTURE AT TOY SCALE, not a Linear stack. The failure is
#: 1-D-specific and Qwen2's 1-D params are RMSNorm weights and q/k/v biases —
#: a generic model without biased attention and RMSNorm cannot express the bug.
TINY = dict(vocab_size=512, hidden_size=64, intermediate_size=128,
            num_hidden_layers=4, num_attention_heads=4,
            num_key_value_heads=2, max_position_embeddings=128)


def build(mixed_dtype: bool, unfreeze_top: int = 2):
    import torch
    from transformers import Qwen2Config, Qwen2ForCausalLM

    torch.manual_seed(20624)
    cfg = Qwen2Config(tie_word_embeddings=False, **TINY)
    model = Qwen2ForCausalLM(cfg)
    # ⭐ The production path loads bf16 then casts the trainable set up to fp32.
    # With mixed_dtype off, everything stays fp32 — the ablation.
    model = model.to(torch.bfloat16 if mixed_dtype else torch.float32)

    names = [n for n, _ in model.named_parameters()]
    scope = full_weight_scope(names, unfreeze_top=unfreeze_top)
    train = set(scope["trainable"])
    for name, p in model.named_parameters():
        if name in train:
            p.requires_grad_(True)
            if p.dtype != torch.float32:
                p.data = p.data.to(torch.float32)
        else:
            p.requires_grad_(False)
    return model, scope


def run_case(*, mixed_dtype, grad_ckpt, input_grads, autocast,
             steps=60, lr=1e-5, batch=4, seq=32):
    import torch
    import bitsandbytes as bnb

    model, scope = build(mixed_dtype)
    if grad_ckpt:
        model.gradient_checkpointing_enable()
    if input_grads:
        model.enable_input_require_grads()

    trainable = [p for p in model.parameters() if p.requires_grad]
    init = {n: p.detach().clone().float()
            for n, p in model.named_parameters() if p.requires_grad}
    opt = bnb.optim.AdamW8bit(trainable, lr=lr)

    # ⛔⛔ LEARNABLE DATA, OR "DID THE LOSS DESCEND" IS UNANSWERABLE. The
    # first version drew uniform random tokens, whose optimal loss IS
    # ln(vocab)=6.238 -- so every configuration sat at 6.25 and read BROKEN for
    # a reason that had nothing to do with the assembly. A test whose control
    # condition cannot pass measures nothing. These are short repeating cycles:
    # a working setup memorises them within tens of steps, so descent is a real
    # signal and its absence is a real finding.
    g = torch.Generator().manual_seed(7)
    period = 8
    losses = []
    for _ in range(steps):
        start = torch.randint(0, TINY["vocab_size"], (batch, 1), generator=g)
        ids = (start + torch.arange(seq) % period) % TINY["vocab_size"]
        opt.zero_grad()
        # ⭐ `autocast` is the toggle; without it the forward runs in the
        # parameters' own dtypes, which is what "autocast off" means here.
        if autocast:
            with torch.autocast(device_type="cpu", dtype=torch.bfloat16):
                out = model(input_ids=ids, labels=ids)
        else:
            out = model(input_ids=ids, labels=ids)
        loss = out.loss
        losses.append(float(loss.detach().float()))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        opt.step()

    # ⛔ THE FINGERPRINT, SPLIT BY RANK. The real failure was 1-D NaN / 2-D
    # finite; a summary "any NaN" would erase the one fact that localises it.
    nan_1d = nan_2d = tot_1d = tot_2d = 0
    moved = []
    for n, p in model.named_parameters():
        if not p.requires_grad:
            continue
        cur = p.detach().float()
        one_d = cur.dim() == 1
        bad = bool(torch.isnan(cur).any() or torch.isinf(cur).any())
        if one_d:
            tot_1d += 1
            nan_1d += bad
        else:
            tot_2d += 1
            nan_2d += bad
        if not bad:
            d = (cur - init[n]).norm().item()
            base = init[n].norm().item()
            if base > 0:
                moved.append(d / base)
    med = sorted(moved)[len(moved) // 2] if moved else float("nan")
    # ⭐⭐ HEALTHY IS TWO CONDITIONS. Finiteness alone passed the broken run.
    # ⭐ Calibrated to the task: a working run memorises an 8-cycle fast, so a
    # 20 % drop is a low bar for health and far above the ~0 a collapsed or
    # frozen run shows. Reported alongside the raw numbers so the threshold is
    # checkable rather than trusted.
    descended = len(losses) > 10 and losses[-1] < losses[0] * 0.80
    return {
        "loss_first": losses[0], "loss_last": losses[-1],
        "loss_min": min(losses),
        "nan_1d": "%d/%d" % (nan_1d, tot_1d),
        "nan_2d": "%d/%d" % (nan_2d, tot_2d),
        "median_rel_move": med,
        "descended": descended,
        "healthy": (nan_1d == 0 and nan_2d == 0 and descended and med > 1e-4),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    print("⭐ ASSEMBLY ABLATION — which introduced element breaks the run?")
    print("   healthy = no NaN (1-D or 2-D) AND loss descends AND weights move")
    print("   ⛔ finiteness alone is NOT health: the broken run stayed finite in")
    print("      its 98 matrices while the loss sat at zero.\n")
    print("   %-6s %-6s %-6s %-6s | %-9s %-9s %-7s %-7s %-10s %s"
          % ("mixed", "ckpt", "ingrad", "autocast", "loss0", "lossN",
             "nan_1d", "nan_2d", "rel_move", "VERDICT"))

    rows = []
    for mixed, ck, ig, ac in itertools.product((True, False), repeat=4):
        # ⛔⛔ ONE CELL MUST NOT KILL THE GRID. A sweep that aborts on the first
        # configuration that cannot run has measured the cells before it and
        # nothing after — the same silent-gap shape as a guard that dies partway
        # through its files. A cell that raises IS a result: "this assembly does
        # not even execute" is exactly the kind of thing being looked for.
        try:
            r = run_case(mixed_dtype=mixed, grad_ckpt=ck, input_grads=ig,
                         autocast=ac, steps=a.steps, lr=a.lr)
        except Exception as exc:                                 # noqa: BLE001
            r = {"loss_first": float("nan"), "loss_last": float("nan"),
                 "loss_min": float("nan"), "nan_1d": "-", "nan_2d": "-",
                 "median_rel_move": float("nan"), "descended": False,
                 "healthy": False,
                 "error": "%s: %s" % (type(exc).__name__, str(exc)[:120])}
        r.update(mixed_dtype=mixed, grad_ckpt=ck, input_grads=ig, autocast=ac)
        rows.append(r)
        note = ("✅ healthy" if r["healthy"]
                else ("⛔ CANNOT RUN — " + r["error"]) if r.get("error")
                else "⛔ BROKEN")
        print("   %-6s %-6s %-6s %-6s | %-9.4f %-9.4f %-7s %-7s %-10.3e %s"
              % (mixed, ck, ig, ac, r["loss_first"], r["loss_last"],
                 r["nan_1d"], r["nan_2d"], r["median_rel_move"], note))

    ok = [r for r in rows if r["healthy"]]
    bad = [r for r in rows if not r["healthy"]]
    print("\n   %d healthy / %d broken" % (len(ok), len(bad)))
    for flag in ("mixed_dtype", "grad_ckpt", "input_grads", "autocast"):
        on_bad = sum(1 for r in bad if r[flag])
        on_ok = sum(1 for r in ok if r[flag])
        print("   %-12s ON in %d/%d broken · %d/%d healthy"
              % (flag, on_bad, len(bad) or 1, on_ok, len(ok) or 1))
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(rows, indent=2),
                                       encoding="utf-8")
        print("\n   -> %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
