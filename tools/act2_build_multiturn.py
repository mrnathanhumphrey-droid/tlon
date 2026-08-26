"""BUILD THE MULTI-TURN CORPUS — Markov depth-1, force-connected, content-free.

⛔⛔ THIS TOOL DOES NOT COUNT TOKENS. `act2_token_budget.py` already imports the
trainer's own `row_to_text`, so a second counter here would re-spell the fold it
is supposed to measure — the self-confirming-counter shape this project has
shipped twice. **Run the existing counter against the mixed corpus.** The exact
command is printed at the end of this tool's output.

⭐ WHAT IT DOES: generate the chains, refuse a starved corpus BEFORE writing,
serialise into the SAME row schema the single-turn corpus uses (so one trainer
and one counter serve both), mix at `MULTITURN_FRACTION`, and emit a manifest of
what the corpus does and does not contain.

⛔ THE ROWS ARE `direction="provoke"`, which is the direction the ARENA SERVES
UNDER — one string, `tlon/discourse/provocation.py`, imported by both. Before
this existed the trainer knew `write`/`read` and the arena spoke under a prompt
that had never been a training direction.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from act2_finetune import row_to_text                          # noqa: E402
from tlon.act2 import corpus as C1                             # noqa: E402
from tlon.act2 import schema_bridge as SB                      # noqa: E402
from tlon.discourse import force_map as FM                     # noqa: E402
from tlon.discourse import multiturn as MT                     # noqa: E402
from tlon.discourse import provocation as PV                   # noqa: E402
from tlon.grammar.parse import parse, render                   # noqa: E402


def rows_from(chains) -> list[dict]:
    """One training row per TRANSITION. The first turn of each chain seeds and
    is not itself a target — a painting with no provocation is a cold start."""
    out = []
    for ch in chains:
        for prev, cur in zip(ch, ch[1:]):
            scene = parse(cur.surface)
            assert render(scene) == cur.surface     # the one-place oracle
            out.append({
                "direction": PV.DIRECTION,
                "prompt": prev.surface,
                "english": prev.surface,   # never used; `prompt` wins in the fold
                "surface": cur.surface,
                "scene": SB.scene_to_proposal(scene),
                "prior_force": prev.force,
                "force": cur.force,
                "source": "multiturn"})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chains", type=int, default=1200)
    ap.add_argument("--turns", type=int, default=12)
    ap.add_argument("--pool-n", type=int, default=6000,
                    help="single-turn pairs to draw paintings from")
    ap.add_argument("--multiturn-fraction", type=float, required=True,
                    help="multi-turn share BY COMPUTE (not by rows). REQUIRED, no "
                         "default — a mix fraction with a default is a held "
                         "variable nobody wrote down. Rows are solved for.")
    ap.add_argument("--seed", type=int, default=20620)
    ap.add_argument("--out", default="runs/act2/corpus_mt")
    ap.add_argument("--eval-frac", type=float, default=0.02)
    a = ap.parse_args()

    if not 0.0 < a.multiturn_fraction < 1.0:
        raise SystemExit("⛔ --multiturn-fraction must be strictly between 0 and "
                         "1. Mix, don't replace: single-turn is what produced "
                         "render 82.0 / speak 97.3.")

    print(f"MULTI-TURN CORPUS · Markov depth-1 · content-free · "
          f"MULTITURN_FRACTION={a.multiturn_fraction}")
    print(FM.describe())
    print(f"\n  separation (max reachable fidelity band): {FM.separation():.4f}")

    pool_pairs = C1.build(a.pool_n, seed=a.seed)
    chains = MT.build(a.chains, turns=a.turns, pairs=pool_pairs, seed=a.seed)
    fair = MT.check_force_pair_fairness(chains)      # refuses BEFORE writing
    print(f"\n  ✅ force-pair fairness: worst live cell {fair['worst_cell']} at "
          f"{fair['worst_ratio']:.3f} of its row share "
          f"(floor {fair['floor']:.4f})")

    mt = rows_from(chains)
    # ⛔ THE MIX IS ON ROWS, AND THE TOKEN CHECK IS WHAT MAKES IT HONEST — a row
    # ratio is not a compute ratio, and only the counter can say which you got.
    # ⛔⛔ THE FRACTION IS BY COMPUTE, AND ROWS ARE SOLVED FOR. Asking the caller
    # for a ROW fraction made rows a proxy for compute, and the proxy rotted by
    # 24 points: 0.50 by rows landed at 0.737 by chars, because the provocation
    # system prompt is 711 chars and rides on EVERY provoke row while write/read
    # carry 79/99. Same shape as the `<700` length check — replace the proxy
    # with the property. Compute is the held variable; rows are the dial.
    #
    # ⚠️ CHARS ARE THEMSELVES A PROXY FOR TOKENS — a tighter one (both sides go
    # through the same fold) but not the thing. `act2_token_budget.py` is the
    # arbiter and it runs before training.
    class _NoTok:
        chat_template = None
    mt_chars = sum(len(row_to_text(r, _NoTok())) for r in mt)
    probe = C1.build(200, seed=a.seed + 1)
    probe_chars = 0
    for q in probe:
        base = {"prompt": q.prompt(), "english": q.english, "surface": q.surface,
                "scene": SB.scene_to_proposal(q.scene),
                "impression": q.impression, "source": q.source}
        for d in ("write", "read"):
            probe_chars += len(row_to_text(dict(base, direction=d), _NoTok()))
    chars_per_pair = probe_chars / len(probe)
    target_single_chars = mt_chars * (1 - a.multiturn_fraction) / a.multiturn_fraction
    n_single = int(round(2 * target_single_chars / chars_per_pair))
    print()
    print("  ⭐ HOLDING COMPUTE, SOLVING FOR ROWS")
    print(f"     multi-turn: {len(mt):,} rows, {mt_chars:,} chars "
          f"({mt_chars / len(mt):.0f}/row)")
    print(f"     single-turn needs {target_single_chars:,.0f} chars at "
          f"{chars_per_pair / 2:.0f}/row → {n_single:,} rows")
    # ⛔⛔ BOTH SINGLE-TURN DIRECTIONS, OR SPEAK CRATERS. `corpus.build` emits
    # `write` ONLY; the read half exists because `act2_build_corpus.py` DUPLICATES
    # each row with `direction="read"`. The first version of this tool did not,
    # and would have shipped a corpus with no read rows at all — measured
    # consequence, from that tool's own comment: **render 81.2 %, speak 9.4 %**.
    # A run that lost speak 97.3 → ~9 would have read as "multi-turn training
    # destroyed speak". So the doubling is mirrored here, and the pair count is
    # HALVED so the mix ratio still lands where it was asked to.
    base = C1.build(max(1, n_single // 2), seed=a.seed + 1)
    single = []
    for p in base:
        row = {"prompt": p.prompt(), "english": p.english, "surface": p.surface,
               "scene": SB.scene_to_proposal(p.scene),
               "impression": p.impression, "source": p.source}
        single.append(dict(row, direction="write"))
        single.append(dict(row, direction="read"))

    rows = mt + single
    # ⛔⛔ REFUSE BEFORE WRITING. The first version of this tool produced a
    # corpus with ZERO read rows and nothing complained until speak would have
    # read 9.4 %. This is that catch, moved to write time.
    dirs = MT.check_direction_coverage(rows)
    print("  ✅ direction coverage: "
          + ", ".join(f"{d} {n:,} ({dirs['shares'][d]:.1%})"
                      for d, n in sorted(dirs["counts"].items())))

    rng = random.Random(a.seed)
    rng.shuffle(rows)
    cut = max(1, int(len(rows) * a.eval_frac))
    ev, train = rows[:cut], rows[cut:]

    out_dir = pathlib.Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, part in (("train", train), ("eval", ev)):
        path = out_dir / f"{name}.jsonl"
        with path.open("w", encoding="utf-8", newline="") as fh:
            for r in part:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"  wrote {len(part):,} → {path}")

    counts = MT.transition_counts(chains)
    manifest = {
        "multiturn_fraction_requested_BY_COMPUTE": a.multiturn_fraction,
        "multiturn_fraction_by_rows_DERIVED": len(mt) / len(rows),
        "held_variable": "compute (char/token share); rows are the dial",
        "n_multiturn_rows": len(mt), "n_singleturn_rows": len(single),
        "singleturn_directions": sorted({r["direction"] for r in single}),
        "chains": a.chains, "turns": a.turns, "seed": a.seed,
        "direction": PV.DIRECTION,
        "provocation_sha": __import__("hashlib").sha256(
            PV.PROVOCATION.encode()).hexdigest()[:16],
        "forced_cells": FM.FORCED_CELLS,
        "uniform_rows": [f for f in FM.ORDER if FM.verdict(f) == FM.UNIFORM],
        "separation": FM.separation(),
        "design_zeros": [f"{p}->{r}" for p in FM.ORDER for r in FM.ORDER
                         if FM.row(p)[r] == 0.0],
        "force_pair_counts": {f"{a_}->{b_}": n for (a_, b_), n in
                              sorted(counts.items())},
        "fairness": {k: v for k, v in fair.items() if k != "counts"},
        "NOT_IN_THIS_CORPUS": [
            "content-adjacency of any kind (C-D2: association is total)",
            "directional evidential adjacency (empirical, the arena's target)",
            "non-forced force-map cells (uniform, not guessed)",
            "the base convention table (§8.1, deferred — base_convention raises)",
        ],
    }
    mp = out_dir / "manifest.json"
    mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                  encoding="utf-8", newline="")
    print(f"  wrote {mp}")
    print(f"\n  rows: {len(mt):,} multi-turn + {len(single):,} single-turn "
          f"= {len(rows):,}  (multi-turn share {len(mt) / len(rows):.3f})")

    print("\n  ⛔⛔ TOKENS ARE NOT COUNTED HERE, ON PURPOSE. A second counter "
          "would re-spell\n     the trainer's fold and verify itself. Run the "
          "one that imports it:\n\n"
          f"     python tools/act2_token_budget.py --model <MODEL> "
          f"--corpus {a.out} \\\n"
          "         --baseline runs/act2/corpus/token_budget.json --tolerance 0.02\n")
    print("  ⚠️  A ROW RATIO IS NOT A COMPUTE RATIO. The multi-turn row is "
          "shorter than a\n     single-turn row (a Tlön surface, not an English "
          "sentence), so the token\n     share will NOT equal "
          f"{a.multiturn_fraction}. The counter is what decides.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
