"""⛔⛔ PREFLIGHT: does a genuine end-of-sequence survive label masking?

⭐ WHY THIS EXISTS AT MINUTE ZERO. Every preflight in `pipeline_fullft.sh`
passed before run 3a died — `vram` plans from parameter counts, `cell_guard`
and `hub_capacity` query the hub, `corpus` is CPU-only, and NOT ONE OF THEM
TOUCHES THE TOKENIZER OR THE MODEL. The first thing that met the base's actual
tokenizer was the training leg, 100 minutes and ~$6 in. A base with no pad
token of its own had pad silently set to eos, the by-id collator masked every
genuine stop, and the failure only surfaced as `speak 0%` at the read.

This check is tokenizer-only: no weights, no GPU, seconds. It runs the REAL
corpus rows through the REAL `row_to_text` at the REAL `--seq`, and asserts
against the REAL collator that the model is being taught to stop.

⭐ It is deliberately the same code path training uses, not a re-implementation
— `row_to_text` and `PositionMaskedCollator` are imported, never mirrored. A
probe that formats its own text measures the probe.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from tlon.act2.collator import eos_label_probe                    # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True,
                    help="the pinned corpus dir; train.jsonl is read")
    ap.add_argument("--seq", type=int, required=True,
                    help="MUST match training's --seq: an eos that survives "
                         "masking here but is truncated away there is not the "
                         "thing being asked about")
    ap.add_argument("--rows", type=int, default=32)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    from transformers import AutoTokenizer
    from act2_finetune import row_to_text

    tok = AutoTokenizer.from_pretrained(a.model)
    rows = []
    with open(pathlib.Path(a.corpus) / "train.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rows.append(json.loads(line))
            if len(rows) >= a.rows:
                break
    if not rows:
        print("⛔⛔ corpus train.jsonl is EMPTY — nothing to check")
        return 1

    texts = [row_to_text(r, tok) for r in rows]
    ev = eos_label_probe(tok, texts, max_length=a.seq)

    print("  pad %r (%s) · eos %r (%s) · pad_is_eos=%s"
          % (ev["pad_token"], ev["pad_token_id"], ev["eos_token"],
             ev["eos_token_id"], ev["pad_is_eos"]))
    print("  %d texts · %d genuine eos · %d MASKED · label at first genuine "
          "eos = %d" % (ev["n_texts"], ev["n_genuine_eos"],
                        ev["n_genuine_eos_MASKED"],
                        ev["label_at_first_genuine_eos"]))
    print("  %d pad positions · %d of them masked"
          % (ev["n_pad_positions"], ev["n_pad_positions_masked"]))

    # ⚠️ NOT FATAL, AND NOT SILENT EITHER. A row longer than --seq is truncated
    # before its eos, so it trains with no stop token at all.
    # ⭐ MEASURED 2026-09-11 on the pinned corpus AT THE PIPELINE'S REAL --seq
    # 384: zero truncation on any base — Qwen 96 genuine eos over 32 rows (its
    # template closes every message, not just the assistant turn), OLMo 32,
    # Mistral 32. So the family arm is CLEAN on stop-token coverage and this
    # branch is expected to stay quiet.
    # ⛔ It is still checked every run rather than assumed, because the margin
    # is a property of the TOKENIZER, not of the corpus: at --seq 192 the same
    # rows truncate 6/32 on Qwen and OLMo and 0/32 on Mistral, whose tokenizer
    # is simply more compact on this text. A base with a fatter tokenizer, or
    # any change to --seq or the corpus, moves that line silently.
    n_no = len(ev["texts_with_no_genuine_eos"])
    if n_no:
        print("  ⚠️ %d of %d rows (%.0f%%) are TRUNCATED BEFORE THEIR eos at "
              "--seq %d and train with no stop token. Not fatal — recorded so "
              "the coverage is a number, not an assumption."
              % (n_no, ev["n_texts"], 100.0 * n_no / ev["n_texts"], a.seq))

    if a.out:
        pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(a.out).write_text(json.dumps(ev, indent=2,
                                                  ensure_ascii=False),
                                       encoding="utf-8")

    # ⛔ Two independent ways to fail, and neither is the other's proxy.
    if ev["n_genuine_eos_MASKED"]:
        print("⛔⛔ %d GENUINE END-OF-SEQUENCE TOKENS ARE LABELLED -100. The "
              "model would never be trained to STOP; it would generate to "
              "max_new_tokens and nothing would parse. This is run 3a."
              % ev["n_genuine_eos_MASKED"])
        return 1
    if ev["n_pad_positions"] and ev["n_pad_positions_masked"] != ev["n_pad_positions"]:
        print("⛔⛔ %d of %d PAD positions are NOT masked — padding would be "
              "trained as content."
              % (ev["n_pad_positions"] - ev["n_pad_positions_masked"],
                 ev["n_pad_positions"]))
        return 1
    print("  ✅ every genuine eos is trained; every pad position is ignored")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
