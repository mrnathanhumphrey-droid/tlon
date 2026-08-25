"""WHAT STEP 2 COSTS — measured from the ACTUAL prompts, before anything spends.

⛔ The prompt sizes below are not guessed. Every one is built by the real
`LLMSpeaker` against the real frozen lexicon card and measured, so the only
estimate left is tokens-per-character.

    python tools/act2_cost.py            # full pre-registered spec, and a pilot
    python tools/act2_cost.py --turns 40 --epochs 5 --probes 16 --seeds 8
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.act2 import probes                                  # noqa: E402
from tlon.act2.llm import LLMSpeaker, ScriptedBackend         # noqa: E402

# ⛔ DECLARED HERE SO A WRONG FIGURE IS VISIBLE RATHER THAN BURIED, the same way
# the product's cost_report declares its prices. Per million tokens.
PRICES = {
    "claude-sonnet-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-opus-5": (15.00, 75.00),
}
CACHE_WRITE, CACHE_READ = 1.25, 0.10      # multipliers on the input price
CHARS_PER_TOKEN = 4.0                     # the one real estimate; ±25 %


def measure_prompts(history_turns: int, n_options: int = 4) -> dict[str, tuple[int, int]]:
    """Build one of each prompt and measure it. Returns kind -> (system, user)."""
    back = ScriptedBackend([{"node": {"root": "klung"}, "force": "ka"},
                            {"node": {"root": "klung"}, "force": "ka"},
                            {"choice": 0}])
    sp = LLMSpeaker("A", back)
    hist = tuple(["nar sen lan klung testesas ka"] * history_turns)
    battery = probes.build(seed=7, n_prod=1, n_comp=1)
    sp.speak(hist, 1)
    sp.render(battery.production[0].stimulus, hist)
    c = battery.comprehension[0]
    sp.choose(c.surface, c.options[:n_options], hist)
    return {call["kind"]: (len(call["system"]), len(call["user"]))
            for call in back.calls}


def cost(model: str, *, turns: int, epochs: int, probes_n: int, seeds: int,
         cells: int, cached: bool, retry_rate: float = 0.10) -> dict:
    price_in, price_out = PRICES[model]
    sizes = measure_prompts(history_turns=min(turns, 60))

    # Per RUN: `turns` live turns, and epochs × 2 models × probes probe calls.
    # Every arm emits the same number of live turns by construction (the arena
    # holds turn count and history shape constant), so this is one number.
    probe_calls = epochs * 2 * probes_n
    per_run = {"speak": turns,
               "render": probe_calls // 2,
               "choose": probe_calls - probe_calls // 2}

    # 3 runs per seed: interacting, yoked, and the yoked REPLICATE the MDE needs.
    runs = 3 * seeds * cells
    usd = 0.0
    tok_in = tok_out = 0
    for kind, n in per_run.items():
        sys_c, usr_c = sizes[kind]
        s_tok, u_tok = sys_c / CHARS_PER_TOKEN, usr_c / CHARS_PER_TOKEN
        out_tok = 10 if kind == "choose" else 80
        calls = n * runs * (1 + retry_rate)
        if cached:
            # The system prompt is identical across every call of a kind, so it
            # is written to cache once per run and read thereafter.
            in_cost = ((s_tok * CACHE_READ + u_tok) * price_in / 1e6)
            in_cost += (s_tok * CACHE_WRITE * price_in / 1e6) * runs / max(calls, 1)
        else:
            in_cost = (s_tok + u_tok) * price_in / 1e6
        usd += calls * (in_cost + out_tok * price_out / 1e6)
        tok_in += calls * (s_tok + u_tok)
        tok_out += calls * out_tok
    return {"model": model, "runs": int(runs),
            "calls": int(sum(per_run.values()) * runs * (1 + retry_rate)),
            "input_tokens": int(tok_in), "output_tokens": int(tok_out),
            "usd": usd, "cached": cached}


def show(label: str, cfg: dict) -> None:
    print(f"\n── {label}")
    print(f"   {cfg['turns']} turns · {cfg['epochs']} epochs · "
          f"{cfg['probes_n']} probes · n={cfg['seeds']} seeds · "
          f"{cfg['cells']} cell(s) → {3 * cfg['seeds'] * cfg['cells']} runs")
    for model in PRICES:
        plain = cost(model, cached=False, **cfg)
        cache = cost(model, cached=True, **cfg)
        print(f"   {model:20} {plain['calls']:>9,} calls   "
              f"${plain['usd']:>10,.2f}   cached ${cache['usd']:>9,.2f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int)
    ap.add_argument("--epochs", type=int)
    ap.add_argument("--probes", type=int, dest="probes_n")
    ap.add_argument("--seeds", type=int)
    ap.add_argument("--cells", type=int)
    a = ap.parse_args()

    print("ACT 2 STEP 2 — cost, measured from the real prompts")
    print(f"⛔ estimate: {CHARS_PER_TOKEN} chars/token (±25 %). Prices per Mtok "
          f"declared in this file. 3 runs/seed (interacting + yoked + the yoked")
    print("   replicate the MDE needs). Retry allowance 10 %.")

    if any(v is not None for v in vars(a).values()):
        cfg = {"turns": a.turns or 200, "epochs": a.epochs or 9,
               "probes_n": a.probes_n or 64, "seeds": a.seeds or 8,
               "cells": a.cells or 1}
        show("as requested", cfg)
        return 0

    show("FULL PRE-REGISTERED SPEC, one cell (baseline only)",
         {"turns": 200, "epochs": 9, "probes_n": 64, "seeds": 8, "cells": 1})
    show("FULL SPEC across baseline + the 3 runnable axes (7 cells)",
         {"turns": 200, "epochs": 9, "probes_n": 64, "seeds": 8, "cells": 7})
    show("BOUNDED PILOT — baseline only, reduced horizon",
         {"turns": 40, "epochs": 5, "probes_n": 16, "seeds": 8, "cells": 1})
    show("MINIMAL SMOKE — is the pipeline alive at all",
         {"turns": 10, "epochs": 2, "probes_n": 8, "seeds": 2, "cells": 1})
    print("\n⛔ Nothing has been spent. A local backend makes every figure above "
          "$0.00 marginal;\n   the backbone model is Nate's call either way.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
