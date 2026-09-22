"""TRAINING ROWS FOR THE BENCH — context-carrying, in the shape the puzzle serves.

⛔⛔ THE TWO CORPORA DO DIFFERENT JOBS AND BOTH ARE NEEDED.

  `corpus_natural`        8,181 (natural English -> Tlön) pairs. Fixes
                          COMPREHENSION: the frozen corpus trained on
                          `gloss(scene)`, so the model had never seen a sentence
                          a person would type and collapsed to two words.

  `corpus_conversations`  the bench exchanges. Fixes CONTINUITY:
                          `multiturn.py` carries "ONLY the prior turn's force
                          ... no content relation", so the speaker was trained
                          that context is noise.

⛔⛤ THIS DOCSTRING ONCE CLAIMED THAT CORPUS HAD "68% content continuity against
the old corpus's 27.1% (chance)". RETRACTED — that was WORD overlap, and three
quarters of it was degree, tense and relator particles, forms every utterance
needs. At ROOT level, which is what a player decodes against and what the
acceptance check measures, it was 9%; within a conversation it ran BELOW chance
(5.3% against a 7.5% shuffled null, p=0.000). The retrain bought on that number
did not move continuity. ⭐ MEASURE THE CORPUS WITH THE INSTRUMENT THE PRODUCT
IS JUDGED BY.

⭐ The replacement is `runs/act2/corpus_conv_steered`, built with forced
root-carry: **97.0% [93.7, 98.6] on n=203**, root-led (R 56.0% of what carries,
against 9.3% before). Pass `--conversations` that path. ⛔ Its rows are stamped
`forced_root_carry` / `recipe: puzzle_steered` — PUZZLE ONLY, never pooled into
the research factorial.

⛔ CONTEXT IS STORED AS ROWS, NOT AS RENDERED TEXT. The prompt string depends on
the tokenizer, so rendering it here would freeze one base's template into the
corpus and the next base would train on Qwen's punctuation. `row_to_text`
renders at training time through `bench_train_text`, which is the same function
`puzzle/speaker.py` serves through. One fold, two callers, no drift.

⛔ DEPTH 4, MATCHING THE SERVE CAP. `puzzle/speaker.CONTEXT_TURNS` is 4 and the
bench also expires on a 120s clock; whichever binds first, the model is never
shown more history than it was trained on. Training deeper than the serve cap
would waste it; training shallower would put fast typists out of distribution.
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

from tlon.discourse.provocation import DIRECTION as PROVOKE     # noqa: E402

WRITE = "write"
CONTEXT_TURNS = 4


def read_jsonl(path: pathlib.Path) -> list[dict]:
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def _ctx(items, i, depth):
    """The last `depth` completed exchanges before index `i`."""
    return [{"prompt": p, "scene": s} for p, s in items[max(0, i - depth):i]]


def rows_from_conversation(conv: dict, depth: int) -> list[dict]:
    """Both threads of one bench, each direction-homogeneous.

    ⛔⛔ THE THREADS ARE SEPARATE BECAUSE A CHAT TEMPLATE CARRIES ONE SYSTEM
    MESSAGE. `write` turns English into Tlön and `provoke` answers a Tlön line;
    they run under different system prompts, so a single interleaved thread
    would put half the exchanges under a framing that does not govern them.

        write    (english_i            -> your_scene_i)
        provoke  (your_surface_i       -> its_scene_i)
    """
    turns = conv["turns"]
    p_turns = [t for t in turns if t["voice"] == "P"]
    out: list[dict] = []

    # ── the write thread ────────────────────────────────────────────────
    w_items = [(t["english"], t["scene"]) for t in p_turns]
    for i, (english, scene) in enumerate(w_items):
        out.append({"direction": WRITE, "prompt": english, "english": english,
                    "scene": scene, "surface": p_turns[i]["surface"],
                    "context": _ctx(w_items, i, depth),
                    "source": "conversation", "conversation": conv["id"]})

    # ── the provoke thread ──────────────────────────────────────────────
    # ⛔ Pairs are taken by ADJACENCY in the rendered turn list, so a truncated
    # conversation cannot splice a P to a T that never answered it.
    pv_items: list[tuple[str, dict]] = []
    for a, b in zip(turns, turns[1:]):
        if a["voice"] == "P" and b["voice"] == "T":
            pv_items.append((a["surface"], b["scene"]))
    for i, (provoking, scene) in enumerate(pv_items):
        out.append({"direction": PROVOKE, "prompt": provoking,
                    "english": provoking, "scene": scene,
                    "context": _ctx(pv_items, i, depth),
                    "source": "conversation", "conversation": conv["id"]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--natural", default="runs/act2/corpus_natural/pairs.jsonl")
    ap.add_argument("--conversations",
                    default="runs/act2/corpus_conversations/conversations.jsonl")
    ap.add_argument("--contrastive",
                    default="runs/act2/corpus_contrastive/pairs.jsonl",
                    help="minimal pairs for the class boundaries the gate "
                         "actually refused; empty context by design")
    ap.add_argument("--out", default="runs/act2/corpus_bench")
    ap.add_argument("--depth", type=int, default=CONTEXT_TURNS)
    ap.add_argument("--eval-frac", type=float, default=0.02)
    ap.add_argument("--seed", type=int, default=20624)
    args = ap.parse_args()

    natural = read_jsonl(pathlib.Path(args.natural))
    convs = read_jsonl(pathlib.Path(args.conversations))
    print("natural pairs %d · conversations %d" % (len(natural), len(convs)))

    rows: list[dict] = []
    # ⭐ The single-turn natural pairs carry an EMPTY context on purpose. The
    # first turn of every real bench has no history, so the model must be good
    # at depth 0 too — and `bench_prompt` sends exactly `read_prompt` there.
    for r in natural:
        rows.append({"direction": WRITE, "prompt": r["prompt"],
                     "english": r["english"], "scene": r["scene"],
                     "surface": r["surface"], "context": [],
                     "source": "natural"})
    for c in convs:
        rows.extend(rows_from_conversation(c, args.depth))

    # ⭐ CONTRASTIVE ROWS CARRY NO CONTEXT, AND THAT IS THE POINT. The lesson is
    # "which slot does this form belong in", which is a property of a single
    # utterance. Putting a bench history in front of it would make the model
    # read the distinction as something about the conversation.
    contrastive = read_jsonl(pathlib.Path(args.contrastive)) if args.contrastive else []
    for r in contrastive:
        rows.append({"direction": r.get("direction", WRITE), "prompt": r["prompt"],
                     "english": r["english"], "scene": r["scene"],
                     "surface": r["surface"], "context": [],
                     "source": "contrastive"})
    print("contrastive rows %d" % len(contrastive))

    rng = random.Random(args.seed)
    rng.shuffle(rows)
    cut = int(len(rows) * args.eval_frac)
    evl, trn = rows[:cut], rows[cut:]

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, part in (("train.jsonl", trn), ("eval.jsonl", evl)):
        tmp = out_dir / (name + ".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            for r in part:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        tmp.replace(out_dir / name)

    by_dir: dict[str, int] = {}
    by_src: dict[str, int] = {}
    with_ctx = 0
    for r in rows:
        by_dir[r["direction"]] = by_dir.get(r["direction"], 0) + 1
        by_src[r["source"]] = by_src.get(r["source"], 0) + 1
        if r["context"]:
            with_ctx += 1
    meta = {"rows": len(rows), "train": len(trn), "eval": len(evl),
            "by_direction": by_dir, "by_source": by_src,
            "with_context": with_ctx, "depth": args.depth, "seed": args.seed}
    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    print("rows %d (train %d · eval %d)" % (len(rows), len(trn), len(evl)))
    print("  by direction:", by_dir)
    print("  by source   :", by_src)
    print("  with context: %d (%.0f%%)" % (with_ctx, 100 * with_ctx / len(rows)))
    print("wrote %s" % out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
