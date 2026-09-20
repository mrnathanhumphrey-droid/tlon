"""COHERENT BENCH CONVERSATIONS — the training data that makes context mean something.

⛔⛔ WHY THIS EXISTS, AND IT IS NOT A SHAPE PROBLEM. `tlon/discourse/multiturn.py`
says of itself: "read ONLY the prior turn's force ... paint a FRESH well-formed
scene ... **No accumulation, no content relation**." Every provoke row the
speaker was trained on came from that generator, and measurement agrees — only
27.1% of them share a single content word between the provoking line and the
reply, which is chance overlap on a shared vocabulary.

That is correct for the research: it is the control that stops persistence being
smuggled in by the sampler. It is fatal for the puzzle. A model taught that the
previous turn carries nothing but a force will not connect to the held
conversation no matter how perfectly the serve shape matches — which is exactly
what the live run showed (context-ON connected on 0 of 3 turns, context-OFF on
3 of 4).

⭐ SO THE CONTINUITY IS INHERITED, NOT IMPOSED. A rule of mine ("the reply must
reuse a root") would teach the model my tic and it would surface as repetitive
collapse. Here the model writes a real bench exchange in English — where the
second thing a person says genuinely follows the first — and BOTH voices go
through Route-A. The Tlön inherits whatever relation the English had.

⛔ THE TLÖNIAN'S ENGLISH IS AN INTERMEDIATE AND NEVER SHIPS. It exists only so
Route-A can produce a scene that answers the previous one. Nothing downstream
reads it; the puzzle serves Tlön.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import pathlib
import sys
import threading
import time
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# ⛔ Imported, not re-spelt. The budget ceiling and the append-and-flush
# behaviour are the same ones the single-turn build ran under; two copies would
# drift and the second one is always the one nobody checks.
from act2_build_natural_corpus import (Budget, BudgetExceeded,   # noqa: E402
                                       _jsonl_append, _read_jsonl)

DEFAULT_LEXICON = "lexicon_expanded.yaml"

DIALOGUE_SYSTEM = """You write short bench conversations for a translation corpus.

The setting: a person sits on a bench and talks quietly about their day. \
Something is sitting beside them. It does not speak a human language and it \
does not answer in words - it responds by painting a fresh impression connected \
to what was just said. Think of it as answering an image with an image.

Write the exchange as alternating lines:

P: <what the person says - plain, natural, spoken English, one sentence>
T: <the impression the thing answers with, written in plain English, one \
sentence, present tense, describing something occurring or being perceived>

RULES
- The conversation is ONE moment. Each P line follows from the one before - the \
person is continuing a thought, not starting over.
- Each T line must CONNECT to the P line just above it: it answers, echoes, \
turns or deepens what was said. Never a non-sequitur.
- T lines describe HAPPENINGS and IMPRESSIONS only. No nouns that name people, \
places, brands or objects-as-things; no numbers; no proper names. Prefer \
weather, light, motion, texture, feeling, time passing.
- P lines may mention ordinary life freely, but keep them spoken and plain.
- Vary length and mood across the exchange. Some lines very short.

Emit ONLY the P: and T: lines. No numbering, no commentary, no blank lines."""

THEMES = [
    "a slow uneventful day", "something small that went wrong",
    "running into someone unexpectedly", "being tired for no clear reason",
    "the weather turning", "waiting for something that did not come",
    "a good thing that happened quietly", "not sleeping well",
    "walking somewhere familiar", "missing someone",
    "finishing something difficult", "an ordinary meal",
    "noise from other people", "the end of the afternoon",
    "being alone and not minding", "being alone and minding",
    "a small kindness", "a journey that took too long",
    "coming home", "something remembered in passing",
]


def parse_dialogue(text: str) -> list[tuple[str, str]]:
    """`[("P", line), ("T", line), ...]`, strictly alternating and starting at P.

    ⛔ A MALFORMED DIALOGUE IS TRUNCATED, NOT REPAIRED. Guessing which voice a
    stray line belongs to would put the person's words in the Tlönian's mouth,
    and that row would then teach the model to answer as the human.
    """
    out: list[tuple[str, str]] = []
    want = "P"
    for raw in text.splitlines():
        line = raw.strip()
        if not line or ":" not in line[:3]:
            continue
        tag, _, body = line.partition(":")
        tag, body = tag.strip().upper(), body.strip()
        if tag not in ("P", "T") or not body:
            continue
        if tag != want:
            break
        out.append((tag, body))
        want = "T" if tag == "P" else "P"
    if out and out[-1][0] == "P":
        out.pop()                      # ⛔ a P with no answering T is half a turn
    return out


def generate_dialogues(client, model, want: int, out: pathlib.Path,
                       budget: Budget, lock: threading.Lock, *,
                       exchanges: int, workers: int, seed: int) -> list[dict]:
    have = _read_jsonl(out)
    if len(have) >= want:
        print("dialogues: %d already on disk, reusing" % len(have))
        return have[:want]

    import random

    rng = random.Random(seed)
    need = want - len(have)
    jobs = [THEMES[(i + rng.randrange(len(THEMES))) % len(THEMES)]
            for i in range(need)]
    print("dialogues: have %d, want %d -> %d calls" % (len(have), want, len(jobs)))

    def one(theme):
        budget.reserve()
        msg = client.messages.create(
            model=model, max_tokens=1200, temperature=1.0,
            system=[{"type": "text", "text": DIALOGUE_SYSTEM,
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user",
                       "content": "Write one conversation of %d exchanges. "
                                  "Theme: %s." % (exchanges, theme)}])
        u = msg.usage
        cost = (u.input_tokens / 1e6 * 3.0 + u.output_tokens / 1e6 * 15.0
                + (getattr(u, "cache_creation_input_tokens", 0) or 0) / 1e6 * 3.75
                + (getattr(u, "cache_read_input_tokens", 0) or 0) / 1e6 * 0.30)
        text = "".join(b.text for b in msg.content
                       if getattr(b, "type", "") == "text")
        turns = parse_dialogue(text)
        if len(turns) >= 4:
            _jsonl_append(out, {"id": uuid.uuid4().hex[:12], "theme": theme,
                                "turns": turns}, lock)
        return cost

    spent = 0.0
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, j) for j in jobs]
        for f in cf.as_completed(futs):
            try:
                cost = f.result()
            except BudgetExceeded:
                continue
            except Exception as exc:                       # noqa: BLE001
                print("  dialogue call failed: %s" % exc)
                continue
            spent += cost
            # ⛔⛔ THIS LINE WAS `budget.settle(budget.spent + spent)` AND
            # `spent` IS THE RUNNING TOTAL, so it re-added everything already
            # spent on every iteration. The figure inflated quadratically, the
            # cap locked out a run that had produced nothing, and the reported
            # overrun was fiction. A DELTA, always.
            budget.add(cost)
    have = _read_jsonl(out)
    print("dialogues: %d on disk (~$%.2f this stage)" % (len(have), spent))
    return have[:want]


def build(args) -> int:
    os.environ[args.lexicon_env] = args.lexicon
    from tlon.grammar import classes as C

    C.load.cache_clear()
    lex = C.load()
    print("lexicon %s  %s  %d roots"
          % (args.lexicon, lex["_hash"], len(lex["classes"]["R"])))

    import anthropic

    from tlon.product import schema as PS
    from tlon.product.proposer import AnthropicProposer
    from tlon.product.schema import ProposalError

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    dlg_p = out_dir / "dialogues.jsonl"
    conv_p = out_dir / "conversations.jsonl"
    refus_p = out_dir / "refusals.jsonl"
    lock = threading.Lock()

    budget = Budget(args.budget_usd)
    prop = AnthropicProposer(args.model)
    client = anthropic.Anthropic()

    dialogues = generate_dialogues(client, args.model, args.dialogues, dlg_p,
                                   budget, lock, exchanges=args.exchanges,
                                   workers=args.workers, seed=args.seed)

    done = {r["id"] for r in _read_jsonl(conv_p)}
    todo = [d for d in dialogues if d["id"] not in done]
    print("conversations: %d done, %d to do, budget left $%.2f"
          % (len(done), len(todo), budget.limit - budget.spent))

    counts = {"full": 0, "truncated": 0, "dropped": 0, "turns": 0}
    stop = threading.Event()

    def render_turn(english):
        """English -> legal Tlön, or None. ⛔ Raises BudgetExceeded upward."""
        feedback = None
        for attempt in range(args.retries + 1):
            budget.reserve()
            try:
                proposal = prop.propose(english, feedback=feedback)
            except Exception as exc:                        # noqa: BLE001
                budget.settle_proposer(prop.cost_report()["usd_total"])
                return None, "proposer: %s" % str(exc)[:200]
            budget.settle_proposer(prop.cost_report()["usd_total"])
            try:
                _scene, surface, _ref = PS.validate(proposal)
                return (surface, proposal), None
            except ProposalError as exc:
                feedback = str(exc)
        return None, feedback

    def one(d):
        if stop.is_set():
            return
        rendered = []
        try:
            for voice, english in d["turns"]:
                got, why = render_turn(english)
                if got is None:
                    # ⛔ TRUNCATE AT THE BREAK, DO NOT SKIP THE TURN. Skipping
                    # would splice turn 1 to turn 3 and teach a jump that never
                    # happened — a manufactured non-sequitur in data whose whole
                    # purpose is that each turn follows the last.
                    _jsonl_append(refus_p, {"id": d["id"], "voice": voice,
                                            "english": english,
                                            "detail": str(why)[:300]}, lock)
                    break
                surface, proposal = got
                rendered.append({"voice": voice, "english": english,
                                 "surface": surface, "scene": proposal})
        except BudgetExceeded:
            stop.set()
            return

        # ⛔ A conversation must end on the Tlönian, or its last exchange has a
        # provocation with no reply.
        while rendered and rendered[-1]["voice"] == "P":
            rendered.pop()
        if len(rendered) < 4:
            counts["dropped"] += 1
            return
        counts["full" if len(rendered) == len(d["turns"]) else "truncated"] += 1
        counts["turns"] += len(rendered)
        _jsonl_append(conv_p, {"id": d["id"], "theme": d["theme"],
                               "lexicon": lex["_hash"], "turns": rendered}, lock)

    t0 = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(one, d) for d in todo]
        for i, _f in enumerate(cf.as_completed(futs), 1):
            if i % 50 == 0:
                print("  %4d/%d  full %d  trunc %d  drop %d  $%.2f"
                      % (i, len(todo), counts["full"], counts["truncated"],
                         counts["dropped"], budget.spent))

    wall = time.perf_counter() - t0
    convs = _read_jsonl(conv_p)
    print("\n" + "=" * 68)
    if stop.is_set():
        print("⛔ STOPPED ON BUDGET — the cap held, this is not an error.")
    print("conversations on disk: %d · turns %d · full %d · truncated %d · "
          "dropped %d" % (len(convs), counts["turns"], counts["full"],
                          counts["truncated"], counts["dropped"]))
    cost = prop.cost_report()
    print("calls %d · $%.2f of $%.2f · %.0f min wall"
          % (cost["calls"], budget.spent, budget.limit, wall / 60))
    (out_dir / "build_report.json").write_text(
        json.dumps({"counts": counts, "cost": cost,
                    "conversations": len(convs), "lexicon": lex["_hash"],
                    "wall_seconds": round(wall, 1),
                    "stopped_on_budget": stop.is_set()},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dialogues", type=int, default=1400)
    ap.add_argument("--exchanges", type=int, default=5,
                    help="P/T pairs per conversation")
    ap.add_argument("--budget-usd", type=float, required=True,
                    help="⛔ HARD CAP, no default.")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--lexicon", default=DEFAULT_LEXICON)
    ap.add_argument("--lexicon-env", default="TLON_LEXICON")
    ap.add_argument("--out", default="runs/act2/corpus_conversations")
    ap.add_argument("--seed", type=int, default=20624)
    return build(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
