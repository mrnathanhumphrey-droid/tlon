"""ROUTE-A-INVERSE — manufacture (natural English → legal Tlön) training pairs.

⛔⛔ THE BUG THIS EXISTS TO FIX. `tlon/act2/corpus.py:282` builds every write
pair as `english = gloss(scene)` — the austere machine gloss, never natural
English. So the fine-tune has never seen a sentence a person would type, and
the puzzle sends it exactly that. Measured consequence: the speaker's own line
collapses to two words from turn two onward.

⭐ THE INVERSION. The old pipeline went scene → gloss → train, so the English
side was a rendering. This one goes English → scene → train, so the English side
is REAL: it was the input. The Tlön side is guaranteed legal because nothing
becomes a row until `PS.validate` has proved `parse(render(scene)) == scene`
against the lexicon.

⛔ THE HOSTED MODEL IS USED ONCE, HERE, AT BUILD TIME. The puzzle serves its own
weights and makes no API call — that is the freeware constraint. This tool is
where the ability is bought, and the ledger below is what it cost.

⛔ BUILT AGAINST THE EXPANDED LEXICON. `TLON_LEXICON` is set before the proposer
is constructed, because the proposer bakes `lexicon_card()` in `__init__` — a
proposer built first would be shown 156 roots while the gate accepted 218, and
every new root would go untrained while looking fine.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import pathlib
import random
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

DEFAULT_LEXICON = "lexicon_expanded.yaml"

#: ⭐ §1a's registers. Tlön renders happenings and impressions, so seeds must
#: carry renderable content — sensory, present-tense, event-like — and the mix
#: is weighted toward what a person actually types on a bench.
REGISTERS = [
    ("benchtalk", 30, "ordinary things a person says about their day: what they "
                      "did, where they went, who they saw, how it went"),
    ("weather", 10, "weather and light and the time of day changing"),
    ("presence", 10, "someone arriving, waiting, leaving, being absent, being "
                     "kept company"),
    ("motion", 8, "things moving, falling, turning, drifting, settling"),
    ("perception", 10, "noticing, hearing, seeing, smelling, half-catching "
                       "something"),
    ("feeling", 12, "plain feeling without analysis: tired, uneasy, glad, "
                    "relieved, homesick, restless"),
    ("time", 8, "time passing, repeating, beginning, dragging, running out"),
    ("conversational", 12, "greetings, questions, small replies, brief "
                           "reflections said aloud to someone sitting nearby"),
]

SEED_SYSTEM = """You write single English sentences for a translation corpus.

The target language renders HAPPENINGS and IMPRESSIONS. It has no nouns at all \
- no word for a thing, a person, or a self. Sentences therefore work best when \
they describe something occurring, being perceived, or being felt.

Write plain, natural, spoken English - the register of someone talking quietly \
to a person sitting next to them. Vary length, rhythm and mood. Some sentences \
should be very short. Avoid proper names, brands, numbers, and technical or \
institutional vocabulary.

Emit ONE sentence per line. No numbering, no bullets, no commentary."""


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    """A hard spend ceiling that is checked BEFORE work is dispatched.

    ⛔⛤ A CAP CHECKED AFTER THE FACT IS NOT A CAP. With N workers in flight, a
    ledger read at the end reports an overrun rather than preventing one. This
    reserves an estimate before each call and settles the real figure after, so
    the worst case is bounded by (workers x one call) rather than unbounded.

    ⛔⛔ THERE WAS ONE `settle(actual)` AND IT COST REAL MONEY TWICE. It ASSIGNED
    `_spent = actual`, and two stages called it under incompatible conventions:
    the proposal stage passed a CUMULATIVE ledger (correct, but it then
    overwrote — and so discarded — everything the seed stage had spent), while
    the dialogue stage passed a RUNNING TOTAL each iteration, which added the
    running total over and over and inflated the figure quadratically until the
    cap locked out a run that had produced nothing.

    ⭐ SO THERE IS NO LONGER A METHOD THAT ASSIGNS. `add` takes a delta,
    `settle_proposer` takes a cumulative ledger and applies only the increment.
    Naming the convention in the method makes the mistake unspellable rather
    than merely documented. `test_budget_cap.py` replays both bugs.
    """

    def __init__(self, usd: float, estimate_per_call: float = 0.01):
        self.limit = usd
        self.estimate = estimate_per_call
        self._spent = 0.0
        self._reserved = 0.0
        self._proposer_seen = 0.0
        self._lock = threading.Lock()

    def reserve(self) -> None:
        with self._lock:
            if self._spent + self._reserved + self.estimate > self.limit:
                raise BudgetExceeded(
                    "budget $%.2f would be exceeded (spent $%.2f, reserved "
                    "$%.2f)" % (self.limit, self._spent, self._reserved))
            self._reserved += self.estimate

    def _unreserve(self) -> None:
        self._reserved = max(0.0, self._reserved - self.estimate)

    def add(self, delta: float) -> None:
        """One call's own cost. ⛔ A DELTA, never a total."""
        with self._lock:
            self._unreserve()
            self._spent += max(0.0, delta)

    def settle_proposer(self, cumulative: float) -> None:
        """A proposer's `cost_report()['usd_total']`, which is CUMULATIVE.

        ⛔ Only the increment is applied, so concurrent callers reading an
        ever-growing ledger cannot each add the whole of it. Monotonic, so an
        out-of-order read from another thread contributes nothing rather than
        going backwards.
        """
        with self._lock:
            self._unreserve()
            inc = cumulative - self._proposer_seen
            if inc > 0:
                self._proposer_seen = cumulative
                self._spent += inc

    @property
    def spent(self) -> float:
        with self._lock:
            return self._spent


def _jsonl_append(path: pathlib.Path, row: dict, lock: threading.Lock) -> None:
    """⛔ APPEND AND FLUSH PER ROW. A build runs for an hour; a crash at minute
    50 must cost the last row, not the run. Buffering would trade the whole
    point of resumability for a little I/O."""
    line = json.dumps(row, ensure_ascii=False)
    with lock:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()


def _read_jsonl(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    # ⛔ A half-written final line is what a crash leaves.
                    # Skipping it is correct; refusing the whole file is not.
                    pass
    return out


# ── stage 1: seeds ──────────────────────────────────────────────────────────

def generate_seeds(client, model, want: int, out: pathlib.Path,
                   budget: Budget, lock: threading.Lock, *,
                   per_call: int = 40, workers: int = 4) -> list[str]:
    """Natural English sentences, deduped, resumable.

    ⭐ SEEDS ARE CHEAP AND PROPOSALS ARE NOT, so they are a separate stage with
    its own file. A re-run reuses them and spends nothing here.
    """
    have = [r["english"] for r in _read_jsonl(out)]
    seen = {s.lower() for s in have}
    if len(have) >= want:
        print("seeds: %d already on disk, reusing" % len(have))
        return have[:want]

    weights = [w for _n, w, _d in REGISTERS]
    total_w = sum(weights)
    calls = []
    # ⛔ OVERSAMPLE, BECAUSE DEDUP EATS THE DIFFERENCE. A model asked for 40
    # sentences on the same register 250 times repeats itself heavily, and the
    # dedup below silently drops the repeats — so requesting exactly `need`
    # returns well under it and the stage looks like it simply failed.
    need = int((want - len(have)) * 1.8)
    while sum(n for _t, n, _d in calls) < need:
        for tag, w, desc in REGISTERS:
            n = max(8, round(per_call * w / (total_w / len(REGISTERS))))
            calls.append((tag, min(n, per_call), desc))
            if sum(x for _t, x, _d in calls) >= need:
                break

    print("seeds: have %d, want %d -> %d calls" % (len(have), want, len(calls)))
    lock_local = threading.Lock()

    def one(job):
        tag, n, desc = job
        budget.reserve()
        msg = client.messages.create(
            model=model, max_tokens=2000, temperature=1.0,
            system=[{"type": "text", "text": SEED_SYSTEM,
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user",
                       "content": "Write %d sentences. Register: %s." % (n, desc)}])
        u = msg.usage
        cost = (u.input_tokens / 1e6 * 3.0 + u.output_tokens / 1e6 * 15.0
                + (getattr(u, "cache_creation_input_tokens", 0) or 0) / 1e6 * 3.75
                + (getattr(u, "cache_read_input_tokens", 0) or 0) / 1e6 * 0.30)
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        fresh = []
        for line in text.splitlines():
            s = line.strip().lstrip("-*0123456789. ").strip()
            if not s or len(s) < 8:
                continue
            with lock_local:
                if s.lower() in seen:
                    continue
                seen.add(s.lower())
            fresh.append(s)
            _jsonl_append(out, {"english": s, "register": tag}, lock)
        return cost, len(fresh)

    spent_here = 0.0
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, j) for j in calls]
        for f in cf.as_completed(futs):
            try:
                cost, n = f.result()
            except BudgetExceeded:
                continue
            except Exception as exc:                        # noqa: BLE001
                print("  seed call failed: %s" % exc)
                continue
            spent_here += cost
            budget.add(cost)
    have = [r["english"] for r in _read_jsonl(out)]
    print("seeds: %d on disk (~$%.3f this stage)" % (len(have), spent_here))
    return have[:want]


# ── stage 2: propose + gate ─────────────────────────────────────────────────

def build(args) -> int:
    os.environ[args.lexicon_env] = args.lexicon
    from tlon.grammar import classes as C

    C.load.cache_clear()
    lex = C.load()
    print("lexicon %s  %s  %d roots"
          % (args.lexicon, lex["_hash"], len(lex["classes"]["R"])))

    from tlon.product import schema as PS
    from tlon.product.proposer import AnthropicProposer
    from tlon.product.schema import ProposalError

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    seeds_p = out_dir / "seeds.jsonl"
    pairs_p = out_dir / "pairs.jsonl"
    refus_p = out_dir / "refusals.jsonl"
    lock = threading.Lock()

    budget = Budget(args.budget_usd)
    prop = AnthropicProposer(args.model)
    import anthropic

    client = anthropic.Anthropic()

    seeds = generate_seeds(client, args.model, args.seeds, seeds_p, budget,
                           lock, workers=args.workers)

    done = {r["english"] for r in _read_jsonl(pairs_p)}
    done |= {r["english"] for r in _read_jsonl(refus_p)}
    todo = [s for s in seeds if s not in done]
    random.Random(args.seed).shuffle(todo)
    print("pairs: %d done, %d to do, budget left $%.2f"
          % (len(done), len(todo), budget.limit - budget.spent))

    counts = {"accept": 0, "refuse": 0, "error": 0}
    stop = threading.Event()

    def one(english: str):
        if stop.is_set():
            return
        feedback = None
        for attempt in range(args.retries + 1):
            try:
                budget.reserve()
            except BudgetExceeded:
                stop.set()
                return
            try:
                proposal = prop.propose(english, feedback=feedback)
            except Exception as exc:                        # noqa: BLE001
                budget.settle_proposer(prop.cost_report()["usd_total"])
                counts["error"] += 1
                _jsonl_append(refus_p, {"english": english, "kind": "proposer",
                                        "detail": str(exc)[:400]}, lock)
                return
            budget.settle_proposer(prop.cost_report()["usd_total"])
            try:
                scene, surface, refused = PS.validate(proposal)
            except ProposalError as exc:
                feedback = str(exc)
                if attempt == args.retries:
                    # ⭐ EVERY REFUSAL IS KEPT. These are the evidence for the
                    # grammar question — what the model reached for and the
                    # language would not hold. `corpus.mined_confusions` reads
                    # exactly this shape. n=4 could not answer it; n=hundreds can.
                    counts["refuse"] += 1
                    _jsonl_append(refus_p, {"english": english, "kind": "gate",
                                            "detail": str(exc)[:400],
                                            "proposal": proposal}, lock)
                continue
            counts["accept"] += 1
            _jsonl_append(pairs_p, {
                "direction": "write",
                "prompt": english,
                "english": english,
                "surface": surface,
                "scene": proposal,
                "let_go": list(refused.objects) if refused else [],
                "source": "route_a_inverse",
                "lexicon": lex["_hash"],
                "attempt": attempt,
            }, lock)
            return

    t0 = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(one, s) for s in todo]
        for i, _f in enumerate(cf.as_completed(futs), 1):
            if i % 100 == 0:
                print("  %5d/%d  accept %d  refuse %d  err %d  $%.2f"
                      % (i, len(todo), counts["accept"], counts["refuse"],
                         counts["error"], budget.spent))

    wall = time.perf_counter() - t0
    cost = prop.cost_report()
    total_pairs = len(_read_jsonl(pairs_p))
    n_try = sum(counts.values()) or 1
    print("\n" + "=" * 68)
    if stop.is_set():
        print("⛔ STOPPED ON BUDGET — the cap held, this is not an error.")
    print("accepted %d · refused %d · errors %d · accept rate %.0f%%"
          % (counts["accept"], counts["refuse"], counts["error"],
             100 * counts["accept"] / n_try))
    print("pairs on disk: %d" % total_pairs)
    print("calls %d · $%.2f of $%.2f · %.0f min wall"
          % (cost["calls"], budget.spent, budget.limit, wall / 60))
    (out_dir / "build_report.json").write_text(
        json.dumps({"counts": counts, "cost": cost, "pairs": total_pairs,
                    "lexicon": lex["_hash"], "wall_seconds": round(wall, 1),
                    "stopped_on_budget": stop.is_set()},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seeds", type=int, default=10000,
                    help="target natural-English seed sentences")
    ap.add_argument("--budget-usd", type=float, required=True,
                    help="⛔ HARD CAP, no default. A build that can spend an "
                         "unspecified amount is not a build anyone approved.")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--retries", type=int, default=1,
                    help="gate refusals retried with the parser's own message")
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--lexicon", default=DEFAULT_LEXICON)
    ap.add_argument("--lexicon-env", default="TLON_LEXICON")
    ap.add_argument("--out", default="runs/act2/corpus_natural")
    ap.add_argument("--seed", type=int, default=20624)
    return build(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
