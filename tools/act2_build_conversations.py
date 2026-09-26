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

⛔⛤ RETRACTED 2026-09-21 — THIS FILE ONCE ARGUED THE OPPOSITE AND WAS WRONG.
It said: "SO THE CONTINUITY IS INHERITED, NOT IMPOSED. A rule of mine ('the
reply must reuse a root') would teach the model my tic and it would surface as
repetitive collapse. The Tlön inherits whatever relation the English had."

The reasoning was sound and its premise was false. The English relation that
got inherited was ANTI-continuity: root recurrence within a conversation
measured **5.3% against a 7.5% shuffled null, p=0.000 over 500 shuffles —
BELOW CHANCE**. The cause was one word in DIALOGUE_SYSTEM below, which asked
for "a FRESH impression ... answering an image with an image". In a language
whose roots ARE happenings, a fresh impression is by construction a DIFFERENT
happening, so the instruction that reads as connection produces anti-connection
once translated. Measured on the corpus it built: of 2,604 P->T pairs, **3 —
0.1% — share a happening-word in English**, and P->T content-word Jaccard is
0.003.

⭐ The old worry was right about one thing and it is why `tlon/act2/carry.py`
enforces a BAND rather than a maximum: forcing maximum reuse would give the
repetitive collapse that decision feared, and the highest-overlap English
measured as near-paraphrase, which breaks the puzzle from the other side. The
gate demands a happening carried AND a happening new.

⛔⛔ THE GATE IS AT STAGE 1 (the English dialogue), AND STAGE 2 MAY ONLY
RESAMPLE WHEN IT IS STEERED. Unsteered, `render_turn` passes only its own
English line to the proposer — it cannot see the prior turn — so the scene is
a faithful, context-free function of that line and no resample can conjure a
happening the English does not name. An unsteered scene gate would reject
~99.9% of turns, exhaust `--retries`, truncate, and drop nearly every
conversation. ⛔ THAT PROHIBITION STANDS AND `test_carry_gate.py` HOLDS IT.

⭐ `--steer` changes the premise rather than the rule. The P line is rendered
first and its roots are passed to the reply's proposal as `require_roots`, so
the reply is TOLD which root to carry. The requirement is then satisfiable and
a resample is doing work instead of rolling the same dice. WHY it was needed:
the writer complied on the happening and the proposer still chose a different
near-synonym root for it — `from` (it drips), `fum` (it floods), `nur` (it
falls) all encode a spill, and `spilled`->`from` while `spilling`->`plung`.
The happening carried; the ROOT, which is what a player decodes against, did
not. Unsteered carry: **40.9% [26.4, 55.4]**.

⛔⛔ FORCED CARRY IS A PUZZLE-ONLY DEVIATION AND THE CORPUS SAYS SO ON EVERY
ROW (`forced_root_carry`, `recipe`). It is the puzzle's crib — a reply that
dependably carries one thing you said is the traction that makes the cipher
solvable — and the RESEARCH's poison, because it is exactly the persistence
the drift measurement must not contain. Never pool a steered conversation into
the research factorial; a docstring would not survive a pooling script, the
stamped field has to be stripped deliberately.

⛔ THE TLÖNIAN'S ENGLISH IS AN INTERMEDIATE AND NEVER SHIPS. It exists only so
Route-A can produce a scene that answers the previous one. Nothing downstream
reads it; the puzzle serves Tlön.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import json
import os
import pathlib
import sys
import threading
import time
import traceback
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
from tlon.act2.carry import (ACCEPTANCE, decide, expand_roots,  # noqa: E402
                             force_variety, gate_dialogue, gloss_synonyms,
                             scene_carry, scene_carry_soft, scene_roots,
                             wilson)


def steer_mode(steer: bool, soft: bool):
    """`(prompt_mode, gate, recipe)` — ONE switch for all three. Pure.

    ⛔⛔ THE REQUIREMENT, THE GATE AND THE STAMP MUST MOVE TOGETHER. Deciding
    them at three separate sites is how an arm ends up steered with a synonym
    family in the prompt and graded by the EXACT gate: every reply the prompt
    invited would be recorded as a carry failure, and the softening would read
    as the treatment not working. Derived once, here, so the three cannot drift.

    ⛔ `--soft-steer --no-steer` is refused rather than quietly resolved. There
    is no carry requirement to soften, and picking either reading for the user
    would run an arm they did not ask for under a stamp that says otherwise.
    """
    if soft and not steer:
        raise SystemExit(
            "⛔⛔ --soft-steer with --no-steer is incoherent: there is no "
            "carry requirement to soften. Pick one.")
    if soft:
        return "synonym", scene_carry_soft, "puzzle_softsteer"
    if steer:
        return "exact", scene_carry, "puzzle_steered"
    return "exact", scene_carry, "puzzle_unsteered"

DEFAULT_LEXICON = "lexicon_expanded.yaml"

# ⛔ Written by the dialogue stage, read by the report. A module-level
# accumulator rather than a return value only because `generate_dialogues`
# already returns the dialogues themselves and threading a second value
# through `build` would be the kind of churn that loses one of them.
_gate_report: collections.Counter = collections.Counter()

DIALOGUE_SYSTEM = """You write short bench conversations for a translation corpus.

The setting: a person sits on a bench and talks quietly about their day. \
Something is sitting beside them. It does not speak a human language and it \
does not answer in words - it answers by naming what is happening. It takes up \
the very happening the person just named and carries it somewhere of its own.

Write the exchange as alternating lines:

P: <what the person says - plain, natural, spoken English, one sentence>
T: <the impression the thing answers with, written in plain English, one \
sentence, present tense, naming something occurring or being perceived>

RULES
- The conversation is ONE moment. Each P line follows from the one before - the \
person is continuing a thought, not starting over.
- Each T line must TAKE UP A HAPPENING THE P LINE JUST NAMED - the same \
occurring, in the same words where the words fit. If the person says they \
WAITED, the T line is about a waiting; if they say the light DIMMED, the T \
line is about a dimming. Use that word itself, not a synonym for it.
- This is the one rule that matters most, and the tempting mistake is to \
answer with an evocative image that stands for what was said. Do not. An \
image that merely suggests the moment names a DIFFERENT happening, and a \
different happening is a non-sequitur here however beautiful it reads.
- Having taken the happening up, the T line must then ADD at least one further \
happening of its own. It carries one thing across and brings something new \
with it. A T line that only restates the P line is as wrong as one that \
changes the subject.
- T lines describe HAPPENINGS and IMPRESSIONS only. No nouns that name people, \
places, brands or objects-as-things; no numbers; no proper names. Prefer \
weather, light, motion, texture, feeling, time passing.
- P lines may mention ordinary life freely, but keep them spoken and plain.
- Vary length and mood across the exchange. Some lines very short.
- VARY WHAT THE T LINE IS DOING, not just what it names. Tlön marks five \
speech acts and a corpus of nothing but statements teaches the speaker only \
one of them. COUNT THEM AS YOU WRITE: in an exchange of five T lines, AT LEAST \
TWO AND OFTEN THREE must not be statements. Asking for a proportion gets you \
one line in five; counting gets you the corpus. ⛔ Do not try to use all four \
in one exchange - there is not room, and forcing it produces lines that answer \
nothing. Pick whichever fit this moment. The four:
    ASK        - end it with a question mark. "Is it still thinning?"
    WONDER     - hold it open rather than settle it. "Perhaps it is \
thinning." / "It may be thinning."
    URGE       - press toward it. "Let it thin." / "Thin, and keep thinning."
    DENY       - say the happening is NOT so. "It is not thinning." / \
"Nothing thins here." ⭐ WRITERS SKIP THIS ONE AND IT MUST NOT BE SKIPPED. The \
trap is reading a denial as contradicting the person. It does not. It takes up \
the happening they named and says that happening is not occurring - not here, \
or not any more. P: "The rain finally stopped." T: "Nothing falls now, and the \
cold stays." That denies a falling while taking the falling up.
  ⛔ The speech act changes, the RULES ABOVE DO NOT. A question still takes up \
the happening the P line named and still adds one of its own; a denial denies \
THAT happening, not some other. Do not use these to change the subject, and \
do not mark them with stage directions or parentheses - write them as the \
plain English sentence they are.

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
                       exchanges: int, workers: int, seed: int,
                       carry_attempts: int = 3) -> list[dict]:
    rejected_p = out.with_name("dialogues_rejected.jsonl")
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
        """⭐ THE CARRY GATE LIVES HERE, WHERE REJECTING IS AFFORDABLE.

        One call writes a whole conversation, so a rejection costs one call —
        and a regenerated conversation can genuinely differ, which is not true
        of a re-proposed scene downstream. Truncation is preferred to
        rejection: the early exchanges of a drifting dialogue are usually
        sound and were already paid for.
        """
        cost = 0.0
        stats = collections.Counter()
        for attempt in range(carry_attempts):
            # ⛔⛤ THE CAP STOPS THE NEXT CALL; IT MUST NOT ERASE THE LAST ONE.
            # Letting BudgetExceeded propagate out of this loop would discard
            # `cost` already incurred on earlier attempts — money spent and not
            # recorded, which is precisely the shape of the `settle()` bug the
            # Budget docstring exists to prevent.
            try:
                budget.reserve()
            except BudgetExceeded:
                stats["stopped_on_budget"] += 1
                return cost, stats
            msg = client.messages.create(
                model=model, max_tokens=1200, temperature=1.0,
                system=[{"type": "text", "text": DIALOGUE_SYSTEM,
                         "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user",
                           "content": "Write one conversation of %d exchanges. "
                                      "Theme: %s." % (exchanges, theme)}])
            u = msg.usage
            cost += (u.input_tokens / 1e6 * 3.0 + u.output_tokens / 1e6 * 15.0
                     + (getattr(u, "cache_creation_input_tokens", 0) or 0)
                     / 1e6 * 3.75
                     + (getattr(u, "cache_read_input_tokens", 0) or 0)
                     / 1e6 * 0.30)
            stats["calls"] += 1
            text = "".join(b.text for b in msg.content
                           if getattr(b, "type", "") == "text")
            turns = parse_dialogue(text)
            kept, verdicts = gate_dialogue(turns)
            stats["pairs_seen"] += len(verdicts)
            stats["pairs_passed"] += sum(1 for v in verdicts if v.ok)
            for v in verdicts:
                if not v.ok:
                    stats["reason: " + v.reason.split(":")[0]] += 1
            if len(kept) >= 4:
                if len(kept) < len(turns):
                    stats["truncated_by_gate"] += 1
                stats["accepted"] += 1
                stats["accepted_on_attempt_%d" % (attempt + 1)] += 1
                _jsonl_append(out, {"id": uuid.uuid4().hex[:12],
                                    "theme": theme, "turns": kept}, lock)
                return cost, stats
            # ⛔⛤ KEEP WHAT THE GATE THREW AWAY. The first sample rejected 19
            # of 20 conversations and kept none of them, so the only way to see
            # WHY was to pay for another run. A rejection is the diagnostic —
            # it is the thing the prompt has to be rewritten against.
            _jsonl_append(rejected_p, {"theme": theme, "attempt": attempt + 1,
                                       "turns": turns,
                                       "verdicts": [{"ok": v.ok,
                                                     "reason": v.reason,
                                                     "carried": sorted(v.carried)}
                                                    for v in verdicts]}, lock)
            stats["regenerated"] += 1
        stats["abandoned"] += 1
        return cost, stats

    spent = 0.0
    gate_stats = collections.Counter()
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, j) for j in jobs]
        for f in cf.as_completed(futs):
            try:
                cost, stats = f.result()
            except BudgetExceeded:
                continue
            except Exception as exc:                       # noqa: BLE001
                print("  dialogue call failed: %s" % exc)
                continue
            gate_stats.update(stats)
            spent += cost
            # ⛔⛔ THIS LINE WAS `budget.settle(budget.spent + spent)` AND
            # `spent` IS THE RUNNING TOTAL, so it re-added everything already
            # spent on every iteration. The figure inflated quadratically, the
            # cap locked out a run that had produced nothing, and the reported
            # overrun was fiction. A DELTA, always.
            budget.add(cost)
    have = _read_jsonl(out)
    print("dialogues: %d on disk (~$%.2f this stage)" % (len(have), spent))
    # ⛔ Same `or 1` shape as the acceptance block below, in the stage that
    # FEEDS it. A denominator guard decides what an absent numerator means,
    # and `or 1` always decides "zero" — a stage that generated nothing would
    # report a 0.0% carry gate rather than say it measured nothing.
    if gate_stats["pairs_seen"]:
        print("  CARRY GATE (stage 1, English): pairs %d · passed %d = %.1f%%"
              % (gate_stats["pairs_seen"], gate_stats["pairs_passed"],
                 100 * gate_stats["pairs_passed"]
                 / gate_stats["pairs_seen"]))
    else:
        print("  CARRY GATE (stage 1, English): MISSING — no pairs were "
              "seen, so nothing was measured (every dialogue reused or "
              "refused)")
    # ⭐ Calls-per-accepted IS the cost model for the full build. It is printed
    # here rather than derived later because the number that prices a build
    # should come out of the build that measured it.
    print("  calls %d · accepted %d · regenerated %d · abandoned %d"
          % (gate_stats["calls"], gate_stats["accepted"],
             gate_stats["regenerated"], gate_stats["abandoned"]))
    if gate_stats["accepted"]:
        print("  calls per accepted conversation: %.2f"
              % (gate_stats["calls"] / gate_stats["accepted"]))
    for key in sorted(k for k in gate_stats if k.startswith("reason: ")):
        print("    %-46s %d" % (key, gate_stats[key]))
    _gate_report.update(gate_stats)
    return have[:want]


def build(args) -> int:
    os.environ[args.lexicon_env] = args.lexicon
    from tlon.grammar import classes as C

    C.load.cache_clear()
    lex = C.load()
    roots = frozenset(lex["classes"]["R"])
    print("lexicon %s  %s  %d roots"
          % (args.lexicon, lex["_hash"], len(roots)))

    import anthropic

    from tlon.product import schema as PS
    from tlon.product.proposer import AnthropicProposer
    from tlon.product.schema import ProposalError

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    dlg_p = out_dir / "dialogues.jsonl"
    conv_p = out_dir / "conversations.jsonl"
    refus_p = out_dir / "refusals.jsonl"
    missed_p = out_dir / "scene_gate_missed.jsonl"
    lock = threading.Lock()

    # ⛔⛔ PUZZLE-ONLY, AND THE CORPUS SAYS SO ON EVERY ROW. Forced root-carry
    # is the puzzle's crib and the research's poison: it is exactly the
    # persistence the drift measurement must not have smuggled in. A docstring
    # note would not survive a pooling script, so `forced_root_carry` is
    # stamped on each conversation and in the build report — a research
    # pooling step has to strip it deliberately rather than inherit it by
    # accident. Same discipline as `factorial.json` carrying no pair key.
    steer = args.steer
    soft = args.soft_steer
    mode, gate, recipe = steer_mode(steer, soft)
    print("root-steer: %s%s"
          % ("ON — FORCED CARRY, PUZZLE CORPUS ONLY" if steer else "OFF",
             "" if steer else "  (the control arm)"))
    if soft:
        n_fam = len({v for v in gloss_synonyms().values()})
        print("            SOFTENED — the requirement is the happening's "
              "gloss family, not the exact root")
        print("            %d families over %d roots · gate=scene_carry_soft "
              "· recipe=%s" % (n_fam, len(gloss_synonyms()), recipe))
        if not gloss_synonyms():
            raise SystemExit(
                "⛔⛔ --soft-steer but tlon/act2/gloss_synonyms.json is empty "
                "or missing. Every root would expand to itself and this would "
                "silently run as the EXACT steer under a softsteer stamp.")

    budget = Budget(args.budget_usd)
    prop = AnthropicProposer(args.model)
    client = anthropic.Anthropic()

    dialogues = generate_dialogues(client, args.model, args.dialogues, dlg_p,
                                   budget, lock, exchanges=args.exchanges,
                                   workers=args.workers, seed=args.seed,
                                   carry_attempts=args.carry_attempts)

    done = {r["id"] for r in _read_jsonl(conv_p)}
    todo = [d for d in dialogues if d["id"] not in done]
    print("conversations: %d done, %d to do, budget left $%.2f"
          % (len(done), len(todo), budget.limit - budget.spent))

    # ⛔ A Counter, not a dict literal. The acceptance block reads keys that the
    # scene stage only creates when it runs, and a build whose dialogue stage
    # accepted nothing reached that block and died on KeyError — losing the
    # verdict for a run that had already been paid for.
    counts: collections.Counter = collections.Counter(
        {"full": 0, "truncated": 0, "dropped": 0, "turns": 0})
    stop = threading.Event()

    def render_turn(english, require_roots=None, carry_mode="exact"):
        """English -> legal Tlön, or None. ⛔ Raises BudgetExceeded upward."""
        feedback = None
        for attempt in range(args.retries + 1):
            budget.reserve()
            try:
                proposal = prop.propose(english, feedback=feedback,
                                        require_roots=require_roots,
                                        carry_mode=carry_mode)
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
        # ⛔⛤ RENDER AND VERIFY ONE EXCHANGE AT A TIME, NOT WHOLE-THEN-CHECK.
        # The first version translated all ten turns, verified afterwards, and
        # truncated at the first failing pair — so a conversation that broke at
        # exchange 1 had already been paid for in full. Measured: 12 of 18
        # conversations were dropped that way, at $0.43 per surviving
        # conversation against roughly $0.10 before the gate existed. Stopping
        # at the break pays for the break and nothing after it.
        rendered = []
        turns = list(d["turns"])
        try:
            for i in range(0, len(turns) - 1, 2):
                (pv, p_en), (tv, t_en) = turns[i], turns[i + 1]
                if pv != "P" or tv != "T":
                    break
                # ⛔⛤ THE P LINE IS RENDERED FIRST AND ITS ROOTS STEER THE
                # REPLY. Unsteered, the writer complied on the HAPPENING and
                # the proposer still picked a different near-synonym root for
                # it — `from` (it drips) / `fum` (it floods) / `nur` (it falls)
                # all encode a spill, and `spilled`->`from` while
                # `spilling`->`plung`. The happening carried; the ROOT, which
                # is what a player decodes against, did not. Carry sat at
                # 40.9% [26.4, 55.4]. Naming P's root removes that degree of
                # freedom.
                got, why = render_turn(p_en)
                if got is None:
                    _jsonl_append(refus_p, {"id": d["id"], "voice": pv,
                                            "english": p_en,
                                            "detail": str(why)[:300]}, lock)
                    break
                p_surface, p_proposal = got
                p_turn = {"voice": pv, "english": p_en, "surface": p_surface,
                          "scene": p_proposal,
                          "roots": sorted(scene_roots(p_proposal, roots))}

                # ⛔⛔ RESAMPLING HERE IS LEGITIMATE ONLY BECAUSE OF THE STEER,
                # and the earlier prohibition was right about the unsteered
                # case. Without `require_roots` the proposer sees only its own
                # English line, so a carry failure is a fact about English
                # already written and a retry cannot repair it — that is why
                # 99.9% of unsteered turns would reject forever. With the root
                # NAMED, the requirement is satisfiable, so the retry is doing
                # work rather than rolling the same dice. ⛔ A resample without
                # a steer remains forbidden; `test_carry_gate.py` holds that.
                exchange, verdict = None, None
                # ⛔⛔ THE REQUIREMENT AND THE VERDICT MUST WIDEN TOGETHER.
                # Handing the proposer a synonym family while grading it with
                # the EXACT gate would reject replies the prompt had just
                # invited, and the corpus would record the softening as a
                # failure of the model. `mode` drives both, from one place.
                if steer and soft:
                    want = sorted(expand_roots(p_turn["roots"]))
                elif steer:
                    want = p_turn["roots"]
                else:
                    want = None
                for _try in range(args.steer_attempts if steer else 1):
                    got, why = render_turn(t_en, require_roots=want,
                                           carry_mode=mode)
                    if got is None:
                        _jsonl_append(refus_p, {"id": d["id"], "voice": tv,
                                                "english": t_en,
                                                "detail": str(why)[:300]}, lock)
                        break
                    t_surface, t_proposal = got
                    t_turn = {"voice": tv, "english": t_en,
                              "surface": t_surface, "scene": t_proposal,
                              "roots": sorted(scene_roots(t_proposal, roots))}
                    counts["steer_attempts"] += 1
                    verdict = gate(p_turn["roots"], t_turn["roots"])
                    exchange = [p_turn, t_turn]
                    if verdict.ok:
                        counts["steer_landed_on_try_%d" % (_try + 1)] += 1
                        break
                if exchange is None:
                    break
                # ── stage 2: VERIFY the band on roots. ⛔ NEVER RESAMPLE ────
                # `render_turn` showed the proposer only this line's English,
                # so a failure is a fact about English already written and a
                # retry cannot touch it. This stops and records; it never pays
                # for the same line twice.
                counts["scene_pairs"] += 1
                if not verdict.ok:
                    counts["scene_failed"] += 1
                    if verdict.echo:
                        counts["scene_echo"] += 1
                    counts["turns_saved_by_early_stop"] += len(turns) - i - 2
                    # ⭐ Keep the losing exchange: it is the only evidence that
                    # says which stage-1 passes are false, and without it the
                    # gate can only be tuned by paying for another run.
                    _jsonl_append(missed_p,
                                  {"id": d["id"], "theme": d["theme"],
                                   "exchange": i // 2 + 1,
                                   "reason": verdict.reason,
                                   "turns": exchange}, lock)
                    # ⛔⛔ THE BAND FILTERS THE TREATMENT, NEVER THE CONTROL.
                    # The scene band measures whether the STEER landed. Dropping
                    # an UNSTEERED exchange for missing it keeps only the
                    # unsteered conversations that happened to carry anyway —
                    # which is not the control arm, it is the treatment arm
                    # selected on the outcome. The dose would then blend two
                    # populations that differ in nothing but luck.
                    #
                    # ⭐ MEASURED, 1,298 dialogues: gating the control kept 27
                    # conversations and dropped 1,271. The pool the shipped
                    # corpus actually used (`corpus_conversations`, 599) avoided
                    # this only by predating the gate. The verdict is still
                    # recorded above and still counted below; it simply does not
                    # get to throw the row away.
                    if steer:
                        break
                counts["scene_passed"] += verdict.ok
                rendered.extend(exchange)
        except BudgetExceeded:
            stop.set()
            return

        if len(rendered) < len(turns):
            counts["truncated_by_scene_gate"] += 1

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
                               "lexicon": lex["_hash"],
                               "forced_root_carry": steer,
                               "recipe": recipe,
                               "turns": rendered}, lock)

    t0 = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(one, d) for d in todo]
        for i, _f in enumerate(cf.as_completed(futs), 1):
            # ⛔⛤ THE RESULT MUST BE RETRIEVED OR THE EXCEPTION IS SWALLOWED.
            # This loop never called `.result()`, so any error inside `one()`
            # vanished with the future: the conversation simply did not appear
            # and the report said "dropped 0" — not even a drop, an absence.
            # A smoke run showed 4 scene pairs passing and 0 conversations
            # written, and the traceback that explained it had been discarded.
            try:
                _f.result()
            except BudgetExceeded:
                stop.set()
            except Exception as exc:                        # noqa: BLE001
                counts["crashed"] += 1
                # ⛔ THE TRACEBACK, NOT THE MESSAGE. "'<' not supported between
                # NoneType and str" names neither the file nor the line, and
                # reproducing it costs another paid run.
                print("  ⛔ conversation raised %s: %s\n%s"
                      % (type(exc).__name__, str(exc)[:200],
                         "".join(traceback.format_exception(
                             type(exc), exc, exc.__traceback__))[-900:]))
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

    # ── the acceptance check, against thresholds registered in carry.py ─────
    # ⛔ COMPUTED HERE, ABOVE THE VERDICT, from the run's own counters. A
    # threshold quoted in prose after the fact is a threshold chosen after
    # seeing the number.
    # ⛔⛤ `english_carry` USED TO READ `pairs_passed / (pairs_seen or 1)`, AND
    # THAT DENOMINATOR-OF-ONE IS THE `except: -> 0` SHAPE THIS PROJECT HAS A
    # RULE ABOUT. `_gate_report` is filled by the stage-1 English build. A run
    # that REUSES dialogues already on disk — which is exactly how the control
    # arm is built, on purpose, so both arms share one population — never runs
    # that stage, so the counters are empty and the line printed
    #
    #     english_carry     0.0%   min  60.0%   ⛔ FAIL
    #
    # for a corpus whose English carry was 72.1%, measured on the very same
    # 958 dialogues by the steered run. A FAIL that reads as a finding, on a
    # quantity nobody measured in this run. MISSING is not zero.
    # ⛔ `spairs` carried the same `or 1`. `decide()` protects the VERDICT at
    # n < 150, so only the printed percentages were exposed — but a printed
    # number that cannot be true teaches the reader to stop checking, and
    # "scene_band 0.0%" on an empty run is a finding about nothing.
    seen = _gate_report["pairs_seen"]
    spairs = counts["scene_pairs"]
    measured = {
        "english_carry": (_gate_report["pairs_passed"] / seen if seen
                          else None),
        "scene_band": (counts["scene_passed"] / spairs if spairs else None),
        "echo": (counts["scene_echo"] / spairs if spairs else None),
    }
    lo, hi = wilson(counts["scene_passed"], counts["scene_pairs"])
    print("\nACCEPTANCE (pre-registered in tlon/act2/carry.py):")
    if measured["english_carry"] is None:
        print("  english_carry  MISSING   min %5.1f%%   ⚠ NOT MEASURED — the "
              "dialogues were reused, so stage 1 did not run. Read it off the "
              "build that WROTE them." % (100 * ACCEPTANCE["english_carry_min"]))
    else:
        print("  english_carry  %6.1f%%   min %5.1f%%   %s"
              % (100 * measured["english_carry"],
                 100 * ACCEPTANCE["english_carry_min"],
                 "PASS" if measured["english_carry"]
                 >= ACCEPTANCE["english_carry_min"] else "⛔ FAIL"))
    if measured["echo"] is None:
        print("  echo           MISSING   max %5.1f%%   ⚠ no scene pairs"
              % (100 * ACCEPTANCE["echo_max"]))
    else:
        print("  echo           %6.1f%%   max %5.1f%%   %s"
              % (100 * measured["echo"], 100 * ACCEPTANCE["echo_max"],
                 "PASS" if measured["echo"] <= ACCEPTANCE["echo_max"]
                 else "⛔ FAIL"))
    print("  scene_band     %s   [%.1f, %.1f] 95%% CI on n=%d pairs"
          % ("MISSING" if measured["scene_band"] is None
             else "%6.1f%%" % (100 * measured["scene_band"]), 100 * lo, 100 * hi,
             counts["scene_pairs"]))
    print("                 target %.0f%% · CI floor %.0f%% · needs n>=%d"
          % (100 * ACCEPTANCE["scene_band_target"],
             100 * ACCEPTANCE["scene_band_ci_floor"],
             ACCEPTANCE["min_pairs_to_decide"]))
    # ⛔⛔ FORCE VARIETY, AND IT GATES. `corpus_bench_dosed` reached production
    # at 99.7% `ka` in voice T because nothing here ever counted the speech
    # acts. Every reply on the public bench then ended in the same particle.
    t_forces = [t.get("scene", {}).get("force")
                for c in convs for t in c.get("turns", [])
                if t.get("voice") == "T"]
    f_ok, f_detail, f_counts = force_variety(t_forces)
    print("  force variety   %s   %s"
          % ("PASS" if f_ok else "⛔ FAIL", f_detail))
    print("                  voice T: %s" % (f_counts or "{}"))

    verdict, detail = decide(counts["scene_passed"], counts["scene_pairs"])
    if not f_ok and verdict == "ACCEPTED":
        # ⛔ A corpus that teaches one speech act is not accepted however well
        # it carries. The carry gate cannot see this and did not.
        verdict, detail = "REJECTED", "force variety: %s" % f_detail
    # ⛔ Same root cause as `english_carry` above, and it printed `nan`. A nan
    # at least cannot be mistaken for a measurement, but it cannot say WHY
    # either, and the reason is the one thing a reader needs.
    # ⛔⛔ `per_conv` IS BOUND ON BOTH BRANCHES AND THE REPORT BELOW READS IT.
    # Rewriting this as a bare if/print left it undefined, which is a NameError
    # raised at the ONE line that writes `build_report.json` — after every
    # dollar of the run has been spent. Caught before it shipped; noted here
    # because the next edit to this block will be tempted the same way.
    per_conv = (_gate_report["calls"] / _gate_report["accepted"]
                if _gate_report["accepted"] else None)
    if per_conv is None:
        print("  dialogue calls per accepted conversation: MISSING  "
              "⚠ dialogues reused; stage 1 did not run this time")
    else:
        print("  dialogue calls per accepted conversation: %.2f  "
              "⭐ this is the cost model for the full build" % per_conv)
    print("VERDICT: %s — %s" % (verdict, detail))
    if verdict != "ACCEPTED":
        print("⛔ DO NOT FUND THE FULL BUILD ON THIS.")
    passed = verdict == "ACCEPTED"

    # ⛔⛤ APPEND THE RUN BEFORE OVERWRITING THE REPORT. `build_report.json` is
    # rewritten every time, so a RESUMED build silently discarded the earlier
    # run's spend — the steered sample cost $3.02 + $2.23 and the file on disk
    # said $1.83. Summing these reports across a corpus therefore UNDERCOUNTS,
    # which is the same failure the Budget class was fixed for: a cost record
    # that quietly loses history reads exactly like a cheap build. The full
    # build is long and resumable, so this is where it would have mattered.
    # ⭐ Append-only ledger, cumulative total derived from it.
    runs_p = out_dir / "build_runs.jsonl"
    _jsonl_append(runs_p, {"finished": time.strftime("%Y-%m-%dT%H:%M:%S"),
                           "usd": budget.spent, "calls": cost["calls"],
                           "conversations_after": len(convs),
                           "scene_pairs": counts["scene_pairs"],
                           "scene_passed": counts["scene_passed"],
                           "recipe": recipe}, lock)
    ledger = _read_jsonl(runs_p)
    cumulative = sum(r.get("usd", 0.0) for r in ledger)
    pooled_pairs = sum(r.get("scene_pairs", 0) for r in ledger)
    pooled_pass = sum(r.get("scene_passed", 0) for r in ledger)
    print("\nLEDGER (%d run%s on this corpus): $%.2f cumulative · "
          "pooled band %d/%d = %.1f%%"
          % (len(ledger), "" if len(ledger) == 1 else "s", cumulative,
             pooled_pass, pooled_pairs,
             100 * pooled_pass / max(1, pooled_pairs)))

    (out_dir / "build_report.json").write_text(
        json.dumps({"counts": counts, "cost": cost,
                    "usd_this_run": budget.spent,
                    "usd_cumulative": cumulative,
                    "runs_on_this_corpus": len(ledger),
                    "pooled_scene_pairs": pooled_pairs,
                    "pooled_scene_passed": pooled_pass,
                    "conversations": len(convs), "lexicon": lex["_hash"],
                    "wall_seconds": round(wall, 1),
                    "stopped_on_budget": stop.is_set(),
                    "carry_gate": dict(_gate_report),
                    "forced_root_carry": steer,
                    "recipe": recipe,
                    "scene_band_ci95": wilson(counts["scene_passed"],
                                              counts["scene_pairs"]),
                    "acceptance": {"thresholds": ACCEPTANCE,
                                   "measured": measured,
                                   "calls_per_conversation": per_conv,
                                   "passed": passed}},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if passed else 3


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dialogues", type=int, default=1400)
    ap.add_argument("--exchanges", type=int, default=5,
                    help="P/T pairs per conversation")
    ap.add_argument("--budget-usd", type=float, required=True,
                    help="⛔ HARD CAP, no default.")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--retries", type=int, default=1,
                    help="⛔ GRAMMAR retries inside the proposer only. This is "
                         "NOT a carry retry — see the module docstring.")
    ap.add_argument("--carry-attempts", type=int, default=3,
                    help="stage-1 regenerations of a dialogue that fails the "
                         "carry gate. Each costs ONE call.")
    ap.add_argument("--no-steer", dest="steer", action="store_false",
                    help="⛔ render the reply WITHOUT naming the prior turn's "
                         "root. Unsteered carry measured 40.9%% [26.4, 55.4]. "
                         "Kept so the steer can be measured against its own "
                         "control rather than against a remembered number.")
    ap.add_argument("--soft-steer", action="store_true",
                    help="⭐ SOFTEN the steer: require a root from the prior "
                         "happening's gloss-derived synonym family rather than "
                         "the exact root, and grade with the matching gate. "
                         "The exact steer bought carry (9%% -> 97%%) and cost "
                         "~14 points of render; this tests whether the "
                         "EXACTNESS was the cost. Stamps recipe "
                         "`puzzle_softsteer`. ⛔ Requires --steer.")
    ap.add_argument("--steer-attempts", type=int, default=2,
                    help="resamples of a STEERED reply that still misses the "
                         "band. ⛔ Meaningless without the steer, and forbidden "
                         "— see the module docstring.")
    ap.set_defaults(steer=True)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--lexicon", default=DEFAULT_LEXICON)
    ap.add_argument("--lexicon-env", default="TLON_LEXICON")
    ap.add_argument("--out", default="runs/act2/corpus_conversations")
    ap.add_argument("--seed", type=int, default=20624)
    return build(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
