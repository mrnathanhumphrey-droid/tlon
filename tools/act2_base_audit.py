"""⛔⛔ THE BASE-ASSUMPTION AUDIT — every point where the harness touches a
base-specific behaviour, asserted against the ACTUAL base instead of assumed
Qwen-shaped.

WHY IT EXISTS, AS THE LOSSES IT IS PREVENTING. Four instances of ONE class, each
found only when a non-Qwen base tripped it, each costing GPU time:

    loader      assumed a causal LM            Ministral-3 is
                                               Mistral3ForConditionalGeneration
                                               -> died at the training leg, ~$0.45
    tokenizer   assumed pad != eos             Mistral has no pad token, so
                                               pad := eos and a by-id collator
                                               masked every real stop
                                               -> speak 0 %, ~$6
    template    assumed a native system role   Mistral v0.3 drops `system` in the
                                               TRAIN shape and keeps it in the
                                               READ shape
                                               -> trained with no instruction,
                                                  read with one, ~$5
    scope       assumed ONE layer stack        a multimodal base pools its vision
                                               tower's layer indices into a set
                                               that looks contiguous
                                               -> 36 vision tensors trained

⭐ SO THIS IS NOT A BUG HUNT. It is an enumeration: for each base-specific
behaviour the harness depends on, READ IT OFF THE BASE and say so. The four
above are fixed; the point of the tool is the fifth, before it costs a run.

⛔⛔ A CHECK THAT CANNOT RUN MUST REPORT `UNKNOWN`, NEVER PASS. Qwen's weights
were archived off this machine, so the tensor-level scope checks have nothing to
read for it — and "no problems found" over a check that never executed is the
vacuous pass this project keeps finding. UNKNOWN is a distinct outcome and it
is counted separately.

    python tools/act2_base_audit.py --base Qwen/Qwen2.5-7B-Instruct
    python tools/act2_base_audit.py --all --out runs/act2/base_audit.json
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from tlon.act2.chat_shape import (prefix_compatible,               # noqa: E402
                                  read_prompt, template_drops)
from tlon.act2.collator import eos_label_probe                     # noqa: E402

OK, FAIL, WARN, UNKNOWN = "OK", "FAIL", "WARN", "UNKNOWN"

#: The campaign's bases and where their weights sit, if they do.
BASES = {
    "Qwen/Qwen2.5-7B-Instruct": None,
    "allenai/Olmo-3-7B-Instruct": r"D:\models\allenai__Olmo-3-7B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3":
        r"D:\models\mistralai__Mistral-7B-Instruct-v0.3",
    "mistralai/Ministral-3-8B-Instruct-2512-BF16":
        r"D:\models\mistralai__Ministral-3-8B-Instruct-2512-BF16",
}


class Audit:
    def __init__(self):
        self.rows: list[dict] = []

    def add(self, path, check, status, detail):
        self.rows.append({"path": path, "check": check, "status": status,
                          "detail": detail})

    def counts(self):
        c = {OK: 0, FAIL: 0, WARN: 0, UNKNOWN: 0}
        for r in self.rows:
            c[r["status"]] += 1
        return c


# ── PATH 1 · THE TOKENIZER ──────────────────────────────────────────────────

def _cfg_vocab(tok):
    """config.vocab_size for this tokenizer's model, or None if unreadable.

    ⭐ Read from the CONFIG, not from the tokenizer: the mapping rung trains an
    embedding whose height is the config's, and the two numbers differ on Qwen.
    """
    try:
        from transformers import AutoConfig
        cfg = AutoConfig.from_pretrained(tok.name_or_path)
        return (getattr(cfg, "vocab_size", None)
                or getattr(getattr(cfg, "text_config", None), "vocab_size", None))
    except Exception:                                            # noqa: BLE001
        return None


def audit_tokenizer(a: Audit, tok, msgs, train_text_fn, seq: int):
    P = "1-tokenizer"

    # pad / eos — the run 3a bug, now structural
    pad, eos = tok.pad_token_id, tok.eos_token_id
    if eos is None:
        a.add(P, "eos exists", FAIL, "no eos_token_id: nothing to train as a stop")
    elif pad is None:
        a.add(P, "pad token", WARN,
              "no pad token of its own -> training sets pad := eos. Safe ONLY "
              "because labels are masked by POSITION (tlon/act2/collator.py).")
    elif pad == eos:
        a.add(P, "pad token", WARN,
              "pad IS eos (%s) -> safe only under position masking" % eos)
    else:
        a.add(P, "pad token", OK, "pad %s != eos %s" % (pad, eos))

    # does a genuine eos survive masking, on the real text at the real seq
    try:
        ev = eos_label_probe(tok, [train_text_fn(tok)], max_length=seq)
        a.add(P, "genuine eos survives label masking",
              OK if ev["n_genuine_eos_MASKED"] == 0 else FAIL,
              "%d genuine eos, %d masked" % (ev["n_genuine_eos"],
                                             ev["n_genuine_eos_MASKED"]))
    except Exception as exc:                                     # noqa: BLE001
        a.add(P, "genuine eos survives label masking", FAIL, str(exc)[:200])

    # ⛔ BOS DOUBLING. The chat template may emit a literal bos AND the fast
    # tokenizer's post-processor may prepend one. Neither is visible in
    # `add_bos_token`, which reads False on Mistral while two arrive anyway.
    def _lead_bos(text):
        ids = tok(text, truncation=True, max_length=seq)["input_ids"]
        n = 0
        for i in ids:
            if i == tok.bos_token_id and tok.bos_token_id is not None:
                n += 1
            else:
                break
        return n, ids[:4]

    n_train, head_train = _lead_bos(train_text_fn(tok))
    n_read, head_read = _lead_bos(read_prompt(tok, msgs[0]["content"],
                                              msgs[1]["content"]))
    if n_train > 1 or n_read > 1:
        a.add(P, "BOS is not duplicated",
              FAIL if n_train != n_read else WARN,
              "leading BOS: train=%d read=%d (add_bos_token=%s, template emits "
              "bos=%s). train head %s / read head %s. %s"
              % (n_train, n_read, getattr(tok, "add_bos_token", "n/a"),
                 bool(tok.bos_token and train_text_fn(tok).startswith(
                     tok.bos_token)), head_train, head_read,
                 "TRAIN AND READ DISAGREE — a prompt-shape mismatch"
                 if n_train != n_read else
                 "consistent across train and read, so not a mismatch — but "
                 "the model never sees a single-BOS sequence"))
    else:
        a.add(P, "BOS is not duplicated", OK,
              "leading BOS: train=%d read=%d" % (n_train, n_read))

    # ⛔ THE MAPPING RUNG TRAINS `embed_tokens`, WHOSE ROW COUNT IS
    # `config.vocab_size` — NOT the number of rows the tokenizer can reach.
    # Qwen pads its embedding to 152,064 while its tokenizer tops out at
    # 151,665, so 399 rows are unreachable and can never receive a gradient.
    # That is not a bug, but it is a BASE-SPECIFIC property of the mapping
    # locus, and a cross-family mapping comparison where one base has 399 dead
    # rows and another has 0 is comparing two different things unless it is
    # said out loud.
    cfg_v = _cfg_vocab(tok)
    n_tok = len(tok)
    dead = (cfg_v - n_tok) if cfg_v else None
    a.add(P, "embedding rows the tokenizer can reach",
          OK if dead in (0, None) else WARN,
          "tok.vocab_size=%s len(tok)=%s added=%d config.vocab_size=%s%s"
          % (getattr(tok, "vocab_size", "?"), n_tok,
             len(getattr(tok, "get_added_vocab", dict)() or {}), cfg_v,
             "" if dead in (0, None) else
             " -> %d UNREACHABLE ROWS in the mapping locus" % dead))

    # every special token the harness may reference must resolve
    unresolved = [n for n in ("eos_token", "pad_token", "unk_token")
                  if getattr(tok, n, None) is not None
                  and tok.convert_tokens_to_ids(getattr(tok, n)) is None]
    a.add(P, "declared special tokens resolve to ids",
          OK if not unresolved else FAIL, str(unresolved or "all resolve"))


# ── PATH 2 · THE CHAT TEMPLATE, EVERY SHAPE THE PIPELINE EMITS ──────────────

def audit_template(a: Audit, tok, shapes):
    P = "2-template"
    if not getattr(tok, "chat_template", None):
        a.add(P, "has a chat template", WARN,
              "no template — the harness falls back to plain concatenation")
        return
    for label, msgs in shapes:
        lost = template_drops(tok, msgs)
        if lost:
            a.add(P, "TRAIN shape keeps every message (%s)" % label, WARN,
                  "template DROPS %s — chat_shape.train_text repairs it by "
                  "rebuilding as read_prompt + answer" % ",".join(lost))
        else:
            a.add(P, "TRAIN shape keeps every message (%s)" % label, OK,
                  "nothing dropped")
        try:
            compat = prefix_compatible(tok, msgs)
        except Exception as exc:                                 # noqa: BLE001
            a.add(P, "read prompt is a PREFIX of the training text (%s)" % label,
                  FAIL, str(exc)[:200])
            continue
        a.add(P, "read prompt is a PREFIX of the training text (%s)" % label,
              OK if compat else FAIL,
              "the reader sends a string training never saw as a prefix"
              if not compat else "prefix holds")
        # the read shape must itself keep the system message
        rp = read_prompt(tok, msgs[0]["content"], msgs[1]["content"])
        keeps = msgs[0]["content"].strip()[:40] in rp
        a.add(P, "READ shape keeps the system message (%s)" % label,
              OK if keeps else FAIL,
              "present" if keeps else "the instruction never reaches the model")


# ── PATH 3 · THE MODEL-LOAD PATH ────────────────────────────────────────────

def audit_load(a: Audit, src: str):
    P = "3-load"
    from transformers import AutoConfig
    from transformers.models.auto.modeling_auto import \
        MODEL_FOR_CAUSAL_LM_MAPPING_NAMES
    try:
        cfg = AutoConfig.from_pretrained(src)
    except Exception as exc:                                     # noqa: BLE001
        a.add(P, "config loads", FAIL, str(exc)[:200])
        return None
    mt = getattr(cfg, "model_type", None)
    a.add(P, "architectures", OK,
          "%s / model_type=%s" % (getattr(cfg, "architectures", None), mt))
    # ⛔ THE MINISTRAL-3 FAILURE, ASKED WITHOUT DOWNLOADING WEIGHTS.
    ok = mt in MODEL_FOR_CAUSAL_LM_MAPPING_NAMES
    a.add(P, "AutoModelForCausalLM supports this config",
          OK if ok else FAIL,
          "model_type %r is %sin the causal-LM mapping%s"
          % (mt, "" if ok else "NOT ",
             "" if ok else " — the training leg would die on "
                           "'Unrecognized configuration class'"))
    tied = bool(getattr(cfg, "tie_word_embeddings", False))
    a.add(P, "embeddings are untied (the mapping rung needs two tensors)",
          OK if not tied else FAIL,
          "tie_word_embeddings=%s%s" % (tied,
          " — mapping_scope cannot address lm_head separately" if tied else ""))
    for k in ("num_hidden_layers", "vocab_size", "hidden_size"):
        v = getattr(cfg, k, None)
        if v is None and hasattr(cfg, "text_config"):
            v = getattr(cfg.text_config, k, None)
        a.add(P, "config.%s" % k, OK if v else UNKNOWN, str(v))
    return cfg


# ── PATH 4 · THE SCOPE PATH, AGAINST REAL TENSORS ───────────────────────────

def audit_scope(a: Audit, weights_dir, cfg):
    P = "4-scope"
    if not weights_dir or not glob.glob(str(pathlib.Path(weights_dir)
                                            / "*.safetensors")):
        a.add(P, "layer stacks / mapping leaves (REAL TENSORS)", UNKNOWN,
              "weights are not on this machine — nothing to read. NOT a pass: "
              "the scope claims can only be made against real tensor names.")
        return
    from safetensors import safe_open

    from tlon.act2.full_weight import (full_weight_scope, layer_stacks,
                                       mapping_scope)
    shapes = {}
    for f in glob.glob(str(pathlib.Path(weights_dir) / "*.safetensors")):
        with safe_open(f, framework="pt") as fh:
            for k in fh.keys():
                shapes[k] = fh.get_slice(k).get_shape()
    names = list(shapes)
    stacks = layer_stacks(names)
    a.add(P, "exactly ONE transformer-layer stack",
          OK if len(stacks) == 1 else FAIL,
          "stacks=%s%s" % ({k or "<root>": len(v) for k, v in stacks.items()},
                           "" if len(stacks) == 1 else
                           " — MULTI-STACK: --stack must restrict the SELECTION, "
                           "not only the count"))
    if len(stacks) != 1:
        return
    n_layers = len(next(iter(stacks.values())))
    half = n_layers // 2
    cfg_n = getattr(cfg, "num_hidden_layers", None) if cfg else None
    a.add(P, "tensor layer count matches the config",
          OK if cfg_n == n_layers else FAIL,
          "tensors=%d config=%s" % (n_layers, cfg_n))
    try:
        lay = full_weight_scope(names, unfreeze_top=half)
        n_lay = sum(int(math.prod(shapes[t])) for t in lay["trainable"])
        a.add(P, "layer rung selects top-HALF", OK,
              "top-%d of %d = %s params in %d tensors"
              % (half, n_layers, "{:,}".format(n_lay), len(lay["trainable"])))
    except Exception as exc:                                     # noqa: BLE001
        a.add(P, "layer rung selects top-HALF", FAIL, str(exc)[:200])
    try:
        mp = mapping_scope(names)
        n_map = sum(int(math.prod(shapes[t])) for t in mp["trainable"])
        a.add(P, "mapping rung addresses BOTH leaves", OK,
              "%s params: %s" % ("{:,}".format(n_map), sorted(mp["trainable"])))
    except Exception as exc:                                     # noqa: BLE001
        a.add(P, "mapping rung addresses BOTH leaves", FAIL, str(exc)[:200])
    # the vocabulary the mapping rung actually trains
    emb = [t for t in names if t.endswith("embed_tokens.weight")]
    if emb and cfg is not None:
        rows = shapes[emb[0]][0]
        cfg_v = getattr(cfg, "vocab_size", None)
        a.add(P, "embed_tokens rows match config.vocab_size",
              OK if rows == cfg_v else FAIL,
              "tensor=%s config=%s" % (rows, cfg_v))


def audit_base(src: str, weights_dir, *, seq: int, corpus: str) -> Audit:
    from transformers import AutoTokenizer

    from act2_finetune import SYSTEM, row_messages, row_to_text
    a = Audit()
    tok = AutoTokenizer.from_pretrained(src)

    rows = []
    with open(pathlib.Path(corpus) / "train.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rows.append(json.loads(line))
            if len(rows) >= 6:
                break
    base_row = rows[0]

    # ⭐ EVERY SHAPE THE PIPELINE EMITS, not one sample. Mistral's template is
    # faithful for (system,user) and lossy for (system,user,assistant), so a
    # single-shape probe passes and proves nothing.
    shapes = []
    for direction in SYSTEM:
        r = dict(base_row)
        r["direction"] = direction
        shapes.append((direction, row_messages(r)))

    audit_tokenizer(a, tok, row_messages(base_row),
                    lambda t: row_to_text(base_row, t), seq)
    audit_template(a, tok, shapes)
    cfg = audit_load(a, src)
    audit_scope(a, weights_dir, cfg)
    return a


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", action="append", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seq", type=int, default=384)
    ap.add_argument("--corpus",
                    default="runs/act2/retrain12_ct/corpus_ct-s20624")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    targets = ([(b, BASES.get(b)) for b in a.base] if a.base
               else list(BASES.items()) if a.all else [])
    if not targets:
        print("give --base <id> or --all")
        return 2

    report, worst = {}, 0
    for src, wd in targets:
        print("\n" + "=" * 78)
        print("BASE  %s" % src)
        print("=" * 78)
        try:
            au = audit_base(src, wd, seq=a.seq, corpus=a.corpus)
        except Exception as exc:                                 # noqa: BLE001
            print("  ⛔ AUDIT ITSELF FAILED: %s" % exc)
            report[src] = {"error": str(exc)}
            worst = max(worst, 1)
            continue
        last = None
        for r in au.rows:
            if r["path"] != last:
                print("\n  -- %s" % r["path"])
                last = r["path"]
            mark = {OK: "✅", FAIL: "⛔", WARN: "⚠️ ", UNKNOWN: "❔"}[r["status"]]
            print("  %s %-52s %s" % (mark, r["check"], r["detail"][:150]))
        c = au.counts()
        print("\n  %s" % "  ".join("%s=%d" % (k, v) for k, v in c.items()))
        report[src] = {"counts": c, "rows": au.rows}
        if c[FAIL]:
            worst = max(worst, 1)

    tot = {OK: 0, FAIL: 0, WARN: 0, UNKNOWN: 0}
    for v in report.values():
        for k, n in (v.get("counts") or {}).items():
            tot[k] += n
    print("\n" + "=" * 78)
    print("TOTAL  %s" % "  ".join("%s=%d" % (k, v) for k, v in tot.items()))
    if tot[UNKNOWN]:
        print("❔ %d check(s) COULD NOT RUN. That is not a pass." % tot[UNKNOWN])
    if a.out:
        pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(a.out).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print("-> %s" % a.out)
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
