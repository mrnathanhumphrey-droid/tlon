"""HOLD COMPUTE CONSTANT — AND COMPUTE IS TOKENS, NOT ROWS. $0, no GPU.

⛔⛔ THE CONFOUND THIS EXISTS TO KILL SITS DIRECTLY ON THE VARIABLE THE RETRAIN
MEASURES. The §8.2 fix changes tokens-per-row in two independent ways: flooring
slot occupancy fills more slots so every scene gets LONGER, and the contrastive
minimal pairs ADD ROWS. Hold `--n` constant and the token total rises — at which
point a render improvement cannot be told apart from "we trained on more tokens".

⭐ Same discipline as holding the write half byte-identical when the read
direction was added: change one thing, and be able to say which thing.

⛔ IT IMPORTS THE TRAINER'S OWN FORMATTER (`act2_finetune.row_to_text`) rather
than re-spelling it. A token counter that reimplements the formatting is a
verifier that confirms itself, and this project has shipped that twice.

⛔ IT ALSO COUNTS TRUNCATION, which a plain sum would miss entirely. Training
truncates at `--seq`; a corpus whose rows got longer can silently lose the tail
of the Scene JSON — the training TARGET — while the token total still looks fine.

    python tools/act2_token_budget.py --model Qwen/Qwen2.5-7B-Instruct \\
        --corpus runs/act2/corpus --seq 256
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from act2_finetune import row_to_text                          # noqa: E402


def measure(path: pathlib.Path, tok, seq: int) -> dict:
    lens, truncated, by_dir = [], 0, {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            n = len(tok(row_to_text(row, tok))["input_ids"])
            lens.append(min(n, seq))
            if n > seq:
                truncated += 1
            by_dir.setdefault(row.get("direction", "write"), []).append(n)
    lens.sort()
    return {"rows": len(lens), "tokens": sum(lens),
            "mean": sum(lens) / len(lens) if lens else 0,
            "max_untruncated": max((max(v) for v in by_dir.values()), default=0),
            "p99": lens[int(0.99 * (len(lens) - 1))] if lens else 0,
            "truncated": truncated,
            "by_direction": {k: {"rows": len(v), "mean": sum(v) / len(v)}
                             for k, v in sorted(by_dir.items())}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", default="runs/act2/corpus")
    ap.add_argument("--seq", type=int, default=256)
    ap.add_argument("--baseline", help="JSON from a previous run to match against")
    ap.add_argument("--tolerance", type=float, default=0.02,
                    help="fractional token mismatch that still counts as held")
    ap.add_argument("--out", default="runs/act2/corpus/token_budget.json")
    # ⛔ AN EXPLICIT, REPORTED INTERVENTION — never a silent one. The alternative
    # fix for truncation is raising `--seq`, and that is the WRONG fix here: seq
    # enters the VRAM arithmetic and the activation/logit cost, so it is one of
    # the variables being held identical to run 3. Dropping a handful of
    # over-length rows changes the corpus by a countable amount; raising seq
    # changes the run.
    ap.add_argument("--prune-over-seq", action="store_true",
                    help="rewrite train.jsonl without rows that would truncate")
    a = ap.parse_args()

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)

    train = pathlib.Path(a.corpus) / "train.jsonl"

    if a.prune_over_seq:
        kept, dropped = [], []
        with train.open(encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                if len(tok(row_to_text(row, tok))["input_ids"]) > a.seq:
                    dropped.append(row)
                else:
                    kept.append(line)
        if dropped:
            with train.open("w", encoding="utf-8", newline="") as fh:
                fh.writelines(kept)
            print(f"⭐ PRUNED {len(dropped)} over-length row(s) from {train}")
            for row in dropped[:6]:
                print(f"    {row.get('direction','write'):<6} "
                      f"impression {row.get('impression','?')[:12]} · "
                      f"{row.get('surface','')[:70]}")
            print("  ⛔ recorded, not silent: these rows would have had their "
                  "Scene JSON truncated away.\n")
        else:
            print(f"✅ nothing to prune at seq={a.seq}\n")

    rep = measure(train, tok, a.seq)
    rep["pruned_over_seq"] = len(dropped) if a.prune_over_seq else None

    print(f"TOKEN BUDGET · {a.model} · seq {a.seq}")
    print(f"  {train}")
    print(f"    rows              {rep['rows']:>12,}")
    print(f"    TOKENS            {rep['tokens']:>12,}   ← the number to hold")
    print(f"    mean/row          {rep['mean']:>12.1f}")
    print(f"    p99 / max         {rep['p99']:>7} / {rep['max_untruncated']}")
    for d, v in rep["by_direction"].items():
        print(f"    {d:<8} {v['rows']:>10,} rows · {v['mean']:.1f} tok/row")

    # ⛔⛔ TRUNCATION IS NOT A ROUNDING ERROR — IT EATS THE TARGET. The assistant
    # turn is LAST in the chat template, so an over-length row loses the tail of
    # the Scene JSON and the model is trained to emit unparseable output.
    if rep["truncated"]:
        print(f"\n  ⛔⛔ {rep['truncated']:,} ROWS EXCEED seq={a.seq} AND WOULD BE "
              f"TRUNCATED ({100 * rep['truncated'] / rep['rows']:.2f} %).\n"
              "  The assistant turn is last, so truncation removes the TARGET, "
              "not the prompt.\n  ⇒ raise --seq or shorten the corpus. Do not "
              "train through this.")
    else:
        print(f"\n  ✅ no truncation at seq={a.seq} "
              f"(longest row {rep['max_untruncated']})")

    verdict = "UNCOMPARED"
    if a.baseline:
        base = json.loads(pathlib.Path(a.baseline).read_text(encoding="utf-8"))
        b, n = base["tokens"], rep["tokens"]
        delta = (n - b) / b
        print(f"\n  ── AGAINST THE BASELINE ──")
        print(f"    run 3 tokens      {b:>12,}")
        print(f"    new corpus        {n:>12,}")
        print(f"    delta             {n - b:>+12,}  ({delta:+.2%})")
        if abs(delta) <= a.tolerance:
            verdict = "HELD"
            print(f"    ✅ HELD within ±{a.tolerance:.0%} — a render change is "
                  "attributable to the corpus, not to a longer run.")
        else:
            verdict = "NOT HELD"
            direction = "MORE" if delta > 0 else "FEWER"
            print(f"    ⛔ NOT HELD — the new corpus trains on {direction} "
                  f"tokens.\n    A render improvement would be confounded with "
                  "run length. Trim --n and rebuild.")
        rep["baseline_tokens"] = b
        rep["delta_fraction"] = delta
    rep["verdict"] = verdict
    rep["model"] = a.model
    rep["seq"] = a.seq

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=2, ensure_ascii=False),
                   encoding="utf-8", newline="")
    print(f"\n  wrote {out}")
    # ⛔ A NON-ZERO EXIT SO A PIPELINE CANNOT TRAIN THROUGH A FAILED CHECK. The
    # last pipeline in this project wrote DONE unconditionally and reported
    # success while all four stages had failed.
    return 0 if verdict in ("HELD", "UNCOMPARED") and not rep["truncated"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
