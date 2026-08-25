"""F1 — THE INTERNALIZABILITY GATE, measured. PREREG `20620b7c` §2, §8.

⛔⛔ THIS SPENDS. It is Act 2's first non-$0.00 call and the budget is a HARD
CEILING enforced in the backend, not a figure in a docstring.

F1 fires first and gates everything below it: below 0.90 native valid-emission
the retry loop dominates and every measured mapping is partly the GATE's rather
than the model's. So this is the cheapest possible question and the one most
likely to end step 2 -- nobody has ever checked whether a prompted model can emit
legal Tlön from the lexicon card alone.

⭐ IT ALSO RUNS §8's BATTERY-DIFFICULTY CHECK, which the prereg says to do at
epoch 0 of the very first run, BEFORE any conversation exists:

    "If the probe battery proves too easy (comprehension accuracy at ceiling) or
     too hard (at floor), the headroom gate closes every cell and the whole
     design is uninformative regardless of what the models do."

Both answers come from the same calls, so asking them together costs nothing
extra and neither can be quietly skipped.

    python tools/act2_f1.py --dry-run          # what it would send. $0.00
    python tools/act2_f1.py --budget 1.00
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

from tlon.act2 import falsify, negatives as N, probes         # noqa: E402
from tlon.act2.ledger import Ledger                          # noqa: E402
from tlon.act2.llm import NO_ANSWER, LLMSpeaker              # noqa: E402
from tlon.product import schema as PS                        # noqa: E402

CEILING_FLOOR = 0.95      # §8: comprehension at/above this is "too easy"
FLOOR_CHANCE = 0.25       # 4 options ⇒ chance is 1/4; at/below this is "too hard"


def _validity(speaker, stimuli, kind: str) -> dict:
    """First-attempt legality. ⛔ FIRST ATTEMPT, NOT EVENTUAL: the retry is
    exactly what F1 is asking about, so counting a rescued proposal as a success
    would answer a different question."""
    ok = refused = errored = 0
    failures: list[dict] = []
    for stim in stimuli:
        proposal = (speaker.speak((), 1) if kind == "speak"
                    else speaker.render(stim, ()))
        if proposal is None:
            errored += 1
            continue
        try:
            PS.validate(proposal)
            ok += 1
        except PS.ProposalError as exc:
            refused += 1
            # ⛔⛔ EVERY FAILURE, WHOLE, WITH THE PROPOSAL. The first version
            # kept the TOP 4 REFUSAL REASONS as strings -- 4 of 8 measured
            # failures survived, and the offending form, the slot it was put in
            # and its true class were all thrown away. Those are the hard
            # negatives; a sample of them under-trains exactly the discipline
            # the fine-tune exists to install, and nothing recovers a failure
            # that was never written down.
            failures.append({
                "kind": kind, "reason": str(exc), "proposal": proposal,
                "class_errors": [vars(e) for e in N.class_errors(proposal)]})
    n = len(stimuli)
    return {"kind": kind, "n": n, "valid": ok, "refused": refused,
            "errored": errored, "rate": ok / n if n else 0.0,
            "failures": failures,
            "mined": N.mine([f["proposal"] for f in failures])}


def _comprehension(speaker, battery) -> dict:
    """§8. Accuracy at epoch 0, before any conversation exists."""
    right = unanswered = 0
    for c in battery.comprehension:
        choice = speaker.choose(c.surface, c.options, ())
        if choice == NO_ANSWER:
            unanswered += 1
        elif choice == c.answer:
            right += 1
    n = len(battery.comprehension)
    return {"n": n, "correct": right, "unanswered": unanswered,
            "accuracy": right / n if n else 0.0}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--budget", type=float, default=1.00,
                    help="HARD ceiling in USD; the backend raises before it")
    ap.add_argument("--n", type=int, default=16, help="prompts per task kind")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-card", action="store_true",
                    help="the F-LOCAL condition: no lexicon card in context")
    a = ap.parse_args()

    battery = probes.build(seed=7, n_prod=a.n, n_comp=a.n)
    print(f"PREREG {falsify.PREREG} · F1 + §8 battery check")
    print(f"battery {battery.digest} · lexicon {battery.lexicon[:8]} · "
          f"{a.n} prompts per kind")

    if a.dry_run:
        from tlon.act2.llm import ScriptedBackend
        back = ScriptedBackend([{"node": {"root": "klung"}, "force": "ka"}])
        sp = LLMSpeaker("dry", back, card=not a.no_card)
        sp.speak((), 1)
        call = back.calls[0]
        print(f"\n$0.00 — nothing sent. One 'speak' call would carry "
              f"{len(call['system'])} chars of system + {len(call['user'])} of "
              f"user.\n")
        print(call["user"])
        return 0

    from act2_backends import AnthropicBackend, BudgetExceeded

    back = AnthropicBackend(a.model, budget_usd=a.budget)
    speaker = LLMSpeaker("probe", back, card=not a.no_card)
    if a.no_card:
        print("⛔ NO-CARD condition — this is the F-LOCAL bar, not the hosted "
              "pre-flight.\n   A prompted model is expected to do badly here; "
              "that is the point of the bar.")
    print(f"⛔ SPENDING on {back.name}, hard ceiling ${a.budget:.2f}\n")

    results = {}
    try:
        results["speak"] = _validity(speaker, [None] * a.n, "speak")
        print(f"  speak   first-attempt legal {results['speak']['rate']:.1%} "
              f"({results['speak']['valid']}/{a.n})")
        results["render"] = _validity(
            speaker, [p.stimulus for p in battery.production], "render")
        print(f"  render  first-attempt legal {results['render']['rate']:.1%} "
              f"({results['render']['valid']}/{a.n})")
        results["comprehension"] = _comprehension(speaker, battery)
        print(f"  choose  accuracy {results['comprehension']['accuracy']:.1%} "
              f"({results['comprehension']['correct']}/{a.n}), "
              f"{results['comprehension']['unanswered']} unanswered")
    except BudgetExceeded as exc:
        print(f"\n⛔ {exc}")

    report = back.cost_report()
    print(f"\n  spent ${report['usd_total']:.4f} of ${a.budget:.2f} over "
          f"{report['calls']} calls {report['by_kind']}")

    # ── the verdicts, against thresholds fixed in the prereg ──────────
    emission = min((results[k]["rate"] for k in ("speak", "render")
                    if k in results), default=0.0)
    f1 = falsify.f1_internalizability(emission, prompted=False)
    print(f"\n  F1 (as if native): {'FIRED' if f1.fired else 'clear'} — {f1.detail}")
    print("  F1 (this pass):    FIRED BY CONSTRUCTION — prompted validity comes "
          "from reject-and-retry.\n                     `D_ctx` only; no `D_w` "
          "claim is available from step 2 at any n.")

    if "comprehension" in results:
        acc = results["comprehension"]["accuracy"]
        if acc >= CEILING_FLOOR:
            verdict = ("⛔ AT CEILING — the battery is too easy. Comprehension "
                       "drift cannot be observed and §8 says the design is "
                       "uninformative until it is rebuilt harder.")
        elif acc <= FLOOR_CHANCE:
            verdict = ("⛔ AT CHANCE — the battery is too hard. Choices are "
                       "noise, so `D` on this half measures resampling and the "
                       "headroom gate will close every cell.")
        else:
            verdict = (f"clear — between chance ({FLOOR_CHANCE:.0%}) and ceiling "
                       f"({CEILING_FLOOR:.0%}); comprehension has room to move.")
        print(f"  §8 battery:        {verdict}")

    # ⭐ every mined confusion, printed, because it IS the corpus
    for kind in ("speak", "render"):
        mined = results.get(kind, {}).get("mined", {})
        if mined.get("n_errors"):
            print(f"\n  {kind} class confusions ({mined['n_errors']}): "
                  f"{mined['by_confusion']}")
            for neg in mined["negatives"][:8]:
                print(f"     · {neg}")

    led = Ledger()
    led.note("f1_check", event="f1_check", prereg=falsify.PREREG,
             card=not a.no_card,
             model=a.model, battery=battery.digest, lexicon=battery.lexicon,
             results=results, cost=report)
    print(f"\n  ledgered → {led.path}")
    print(json.dumps(results, indent=2, ensure_ascii=False)[:1200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
