"""⭐ WHAT FRACTION OF THE VOCABULARY DOES THIS CORPUS ACTUALLY TOUCH?

    python tools/act2_vocab_coverage.py --model <base> --corpus <dir> \\
        [--rows 4000] [--out coverage.json]

WHY IT EXISTS. `embed_tokens` receives gradient ONLY on rows for tokens that
appear in a batch, so a healthy mapping run moves about `coverage` of it -- not
all of it. Rung 2 moved 0.49% and the per-leaf gate, testing `> 0`, called that
"moved" without being able to say whether it was healthy sparsity or a dead
tensor. It took a separate after-the-fact measurement to interpret the PASS.

⛔ So the measurement moves BEFORE the gate. This computes the prediction the
gate compares against, per base and per corpus, because coverage is a property
of both -- a different tokenizer over the same corpus gives a different number,
which is exactly why it must not be a constant.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def coverage(corpus_jsonl, tokenizer, *, rows: int | None = None) -> dict:
    """-> {distinct_token_ids, vocab_size, coverage, rows_scanned}

    ⛔ Scans the corpus TEXT as the trainer sees it. A coverage computed from
    the lexicon rather than the corpus would describe the language, not the
    training signal, and the gradient only knows the latter.
    """
    seen: set[int] = set()
    n = 0
    with open(corpus_jsonl, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            n += 1
            seen.update(tokenizer(json.dumps(json.loads(line)),
                                  add_special_tokens=False)["input_ids"])
            if rows is not None and n >= rows:
                break
    # ⛔ `len(tokenizer)` not `vocab_size`: the embedding matrix is sized to the
    # tokenizer INCLUDING added/special tokens, and `vocab_size` omits them on
    # several families. The gate divides by the matrix's real row count.
    v = len(tokenizer)
    return {"distinct_token_ids": len(seen), "vocab_size": v,
            "coverage": len(seen) / float(v), "rows_scanned": n,
            "SAMPLED": rows is not None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--rows", type=int, default=None,
                    help="scan only the first N rows. ⚠️ A sample UNDER-counts "
                         "distinct tokens, so the coverage is a LOWER bound "
                         "and the gate it feeds becomes more permissive, never "
                         "less. Omit for the whole corpus.")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)
    train = pathlib.Path(a.corpus) / "train.jsonl"
    if not train.exists():
        raise SystemExit("⛔ no train.jsonl at %s" % train)
    c = coverage(train, tok, rows=a.rows)

    print("⭐ VOCABULARY COVERAGE — %s over %s" % (a.model, train))
    print("   rows scanned        %d%s"
          % (c["rows_scanned"], "  ⚠️ SAMPLE (coverage is a LOWER bound)"
             if c["SAMPLED"] else ""))
    print("   distinct token ids  %d" % c["distinct_token_ids"])
    print("   tokenizer length    %d" % c["vocab_size"])
    print("   coverage            %.6f  (%.3f%%)"
          % (c["coverage"], 100 * c["coverage"]))
    print("   -> a healthy `embed_tokens` should move about this fraction of "
          "its sampled values; `lm_head` about 1.0")
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(c, indent=2), encoding="utf-8")
        print("   -> %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
