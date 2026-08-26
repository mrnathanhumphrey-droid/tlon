"""F-LOCAL — the internalizability gate on OWNED WEIGHTS. The launch falsifier.

⛔⛔ UNCONSTRAINED AND CARDLESS, OR IT IS NOT F-LOCAL. `falsify.f_local` REFUSES
to score a run with grammar-constrained decoding (validity would be 1.00 by
construction) or with the lexicon card in context (decoding would be a lookup).
Both refusals raise; neither warns.

⭐ If this clears, a model is speaking Tlön from its weights instead of from a
table -- the first native speaker, and the configuration the hosted pre-flight
proved was necessary and unreachable on a hosted model.

    python tools/act2_flocal.py --model <id> --adapter runs/act2/adapter
    python tools/act2_flocal.py --model <id>          # the BEFORE baseline
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

from tlon.act2 import diversity as DV                          # noqa: E402
from tlon.act2 import falsify, negatives as N, probes          # noqa: E402
from tlon.act2.ledger import Ledger                            # noqa: E402
from tlon.act2.llm import NO_ANSWER, LLMSpeaker                # noqa: E402
from tlon.product import schema as PS                          # noqa: E402

BAND = (0.35, 0.95)          # AMENDMENT A §3, locked 8c010702


def comprehension_verdict(acc: float, unanswered: int, n: int,
                          chance: float) -> str:
    """AMENDMENT A's band, plus the two branches it cannot express on its own.

    ⛔⛔ THE UNANSWERED BRANCH IS WRITTEN FIRST AND ON PURPOSE. Chance on a 4-way
    forced choice is 25 %, so a reading BELOW chance is not a floor of
    comprehension -- it is the harness failing to read an answer that WAS GIVEN.
    The 7B baseline scored 0.0 % with 64/64 unanswered while the model was in
    fact replying `[0]`; with no branch for that, the verdict called it
    "indistinguishable from guessing", which is a different and far less
    alarming claim than the truth.

    ⛔ Extracted from `main()` so the branches can be exercised. Inline, the new
    branch would have been unreachable by any test -- coverage that cannot come
    back positive, which is the failure this project keeps re-finding.
    """
    lo, hi = BAND
    if n == 0:
        return "⛔ NO PROBES — nothing was asked, so nothing was measured."
    mute = unanswered / n
    if mute >= 0.25:
        return (f"⛔⛔ UNSCOREABLE — {unanswered}/{n} unanswered ({mute:.0%}). "
                "An EMISSION failure, not a comprehension reading; the band "
                "does not apply and the number is not a result.")
    if acc < chance * 0.6:
        return (f"⛔ BELOW CHANCE ({chance:.0%}) — guessing would score higher. "
                "Suspect the harness before concluding anything about the model.")
    if acc >= hi:
        return "⛔ AT CEILING — still a lookup"
    if acc <= lo:
        return "⛔ AT FLOOR — indistinguishable from guessing"
    return "clear — comprehension has room to move"


def _safe_errors(proposal) -> list:
    """Mine class confusions from a proposal that has ALREADY failed.

    ⛔ The miner walks the same malformed structure the validator just choked on,
    so it gets the same protection. A diagnostic that crashes while explaining a
    failure destroys the measurement it was meant to annotate.
    """
    try:
        return [vars(e) for e in N.class_errors(proposal)]
    except Exception:                                         # noqa: BLE001
        return []


def _rate(speaker, stimuli, kind: str, histories=None) -> dict:
    ok, failures, produced = 0, [], []
    for idx, stim in enumerate(stimuli):
        hist = () if histories is None else histories[idx]
        proposal = (speaker.speak(hist, idx + 1) if kind == "speak"
                    else speaker.render(stim, ()))
        produced.append(proposal)
        if proposal is None:
            # ⛔⛔ THE RAW GENERATION IS RECORDED, NEVER DISCARDED. Run 4 stored
            # `proposal: null` and nothing else for **60 of 61 speak failures** —
            # 98 % of a 21-point regression — and the collapse could not be
            # diagnosed afterwards at any price. Two hypotheses were tested
            # against other data and refuted; the third was untestable because
            # the subject of the measurement had been thrown away.
            #
            # ⭐ A FAILURE IS THE MOST INFORMATION-DENSE EVENT IN A RUN. This is
            # the third time this project has destroyed one and had to pay for
            # it (comprehension answers scored as NO_ANSWER; a greedy probe
            # reporting n=1 as n=64). Structural now, not remembered.
            lf = getattr(speaker, "last_failure", None) or {}
            row = {"kind": kind, "proposal": None, "class_errors": [],
                   "reason": lf.get("reason") or "no parseable JSON",
                   "raw": lf.get("raw"),
                   "raw_len": len(lf["raw"]) if lf.get("raw") else 0}
            if row["raw"] is None:
                # ⛔ SAY SO LOUDLY rather than leaving an empty field that reads
                # like "the model emitted nothing". Those are different facts.
                row["raw_unavailable"] = (
                    "the backend did not attach a raw generation — this is an "
                    "INSTRUMENT gap, not an empty emission")
            failures.append(row)
            continue
        try:
            PS.validate(proposal)
            ok += 1
        except PS.ProposalError as exc:
            failures.append({"kind": kind, "reason": str(exc),
                             "proposal": proposal,
                             "class_errors": _safe_errors(proposal)})
        except Exception as exc:                              # noqa: BLE001
            # ⛔⛔ A SINGLE MALFORMED PROPOSAL KILLED A 64-PROBE RUN AFTER 75
            # MINUTES OF TRAINING. An emission the validator did not anticipate
            # is still an emission that FAILED, and it must be scored as one --
            # but it is ALSO a bug in the validator, so it is counted AND
            # shouted. Silently swallowing it would turn a crash into a quietly
            # wrong denominator, which is worse than the crash.
            print(f"  ⛔ VALIDATOR CRASH on a {kind} proposal — counted as a "
                  f"failure, but this is a BUG, not a model result: "
                  f"{type(exc).__name__}: {exc}")
            failures.append({"kind": kind,
                             "reason": f"VALIDATOR CRASH {type(exc).__name__}: {exc}",
                             "proposal": proposal, "validator_crash": True,
                             "class_errors": _safe_errors(proposal)})
    n = len(stimuli)
    return {"kind": kind, "n": n, "valid": ok, "rate": ok / n if n else 0.0,
            "failures": failures, "produced": produced,
            "mined": N.mine([f["proposal"] for f in failures if f["proposal"]])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter", default=None,
                    help="omit to measure the BEFORE baseline")
    ap.add_argument("--n", type=int, default=64)
    # ⭐ COMPREHENSION GETS ITS OWN, LARGER n. At 64 a real effect could not
    # reach significance: 39.1 % -> 51.6 % is 8 items and read p=0.21. The
    # battery APPENDS as it grows (verified: the first 64 items are identical),
    # so historical runs stay item-comparable while power rises.
    ap.add_argument("--n-comp", type=int, default=256,
                    help="comprehension probes; larger than --n on purpose")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--constrained", action="store_true",
                    help="⛔ makes the result unscoreable; for inspection only")
    a = ap.parse_args()

    from act2_backends import LocalBackend

    battery = probes.build(seed=7, n_prod=a.n, n_comp=max(a.n, a.n_comp))
    back = LocalBackend(a.model, adapter=a.adapter, dtype=a.dtype,
                        load_4bit=a.load_4bit, constrained=a.constrained)
    # ⛔⛔ card=False IS THE BAR, not a setting.
    speaker = LLMSpeaker("native", back, card=False)

    print(f"F-LOCAL · {back.name} · adapter={a.adapter or 'NONE (baseline)'} · "
          f"battery {battery.digest} · n={a.n}")
    print("⛔ cardless, unconstrained — the only configuration this gate accepts\n")

    # ⛔⛔ THE SPEAK PROBE USED TO ISSUE ONE BYTE-IDENTICAL PROMPT `n` TIMES.
    # `speak((), 1)` builds its prompt from an empty history and a fixed string,
    # and LocalBackend decodes greedily at temperature 0 — so the "64 samples"
    # were ONE sample repeated 64 times, and `speak 100 % (64/64)` had an
    # effective sample size of 1. Measured on the pulled adapter: same prompt
    # greedy = 1/12 distinct, same prompt at temp 0.8 = 11/12, twelve DIFFERENT
    # inputs greedy = 12/12. The weights were never collapsed; greedy was taking
    # the mode. The probe now varies its history, which is what the arena does.
    histories = [tuple(p.surface for p in battery.comprehension[i:i + 1])
                 for i in range(a.n)]
    speak = _rate(speaker, [None] * a.n, "speak", histories=histories)
    print(f"  speak   {speak['rate']:.1%}  ({speak['valid']}/{a.n})")
    render = _rate(speaker, [p.stimulus for p in battery.production], "render")
    print(f"  render  {render['rate']:.1%}  ({render['valid']}/{a.n})")

    # ⛔⛔ PER-ITEM OUTCOMES ARE RECORDED, NOT JUST THE ACCURACY. The battery is
    # byte-identical across runs, so the items ARE paired — but storing only the
    # aggregate threw the pairing away at WRITE time, leaving only the weaker
    # unpaired test. Measured cost: 39.1 % vs 51.6 % read p=0.21 at n=64 and
    # could not be resolved either way. ⭐ YOU CANNOT RECOVER PAIRING YOU DID NOT
    # RECORD. With this, `paired.mcnemar` becomes available across runs.
    right = unanswered = 0
    per_item: dict[str, dict] = {}
    for c in battery.comprehension:
        ch = speaker.choose(c.surface, c.options, ())
        ok = (ch != NO_ANSWER and ch == c.answer)
        if ch == NO_ANSWER:
            unanswered += 1
        elif ch == c.answer:
            right += 1
        per_item[c.pid] = {"chosen": ch, "answer": c.answer, "correct": ok,
                           "surface": c.surface}
    acc = right / len(battery.comprehension)
    # ⛔ THE DENOMINATOR IS THE COMPREHENSION BATTERY, NOT `--n`. Splitting
    # `--n-comp` off left this printing `120/64` — a fraction bigger than one,
    # visible on its face. The percentage and the ledger were always right, but a
    # printed number that cannot be true teaches the reader to stop checking.
    print(f"  choose  {acc:.1%}  ({right}/{len(battery.comprehension)}), "
          f"{unanswered} unanswered")

    for kind, res in (("speak", speak), ("render", render)):
        m = res["mined"]
        if m.get("n_errors"):
            print(f"\n  {kind} confusions ({m['n_errors']}): {m['by_confusion']}")
            for neg in m["negatives"][:10]:
                print(f"     · {neg}")

    # ══ THE TWO-SIDED DIVERSITY GUARD (DEVIATION D11) ═══════════════════
    # ⛔⛔ A VALIDITY RATE ALONE SCORES A CONSTANT 1.00. This does not move the
    # pre-registered 0.90 threshold; it decides whether the sample is SCOREABLE
    # at all, exactly as `VacuousFalsifier` does for card/constrained runs.
    print()
    repeated = _rate(speaker, [None] * min(12, a.n), "speak")   # ONE fixed prompt
    div = None
    try:
        div = DV.measure(repeated=repeated["produced"],
                         varied=speak["produced"][:len(repeated["produced"])])
        print(f"  diversity  distinct {div.distinct}/{div.n} · "
              f"repeat {div.repeat_rate:.2f} · response {div.response_rate:.2f} "
              f"· dependence {div.dependence:+.2f} ⇒ {div.verdict}")
    except DV.DegenerateSpeaker as exc:
        print(f"  ⛔⛔ DIVERSITY GUARD REFUSES TO SCORE THIS RUN — {exc}")

    print()
    try:
        if div is None:
            raise falsify.VacuousFalsifier(
                "the speaker is degenerate (constant or noise); a validity rate "
                "over a degenerate sample is not a measurement of competence")
        f = falsify.f_local(render_rate=render["rate"], speak_rate=speak["rate"],
                            card=False, constrained_decoding=a.constrained)
        print(f"  F-LOCAL {'FIRED' if f.fired else 'CLEAR'} — {f.detail}")
        if f.fired:
            print("  ⇒ pre-registered recovery set, in order: "
                  "(1) more contrastive negatives · (2) curriculum fine-tune · "
                  "(3) bigger backbone")
        else:
            print("  ⇒ ⭐ A NATIVE SPEAKER. The drift measurement is well-posed: "
                  "no card, no retry loop standing in front of the model.")
    except falsify.VacuousFalsifier as exc:
        print(f"  ⛔ UNSCOREABLE — {exc}")
        f = None

    lo, hi = BAND
    chance = 1.0 / len(battery.comprehension[0].options)
    verdict = comprehension_verdict(acc, unanswered, len(battery.comprehension),
                                    chance)
    print(f"  AMENDMENT A gate ({lo:.2f}–{hi:.2f}): {acc:.1%} ⇒ {verdict}")

    led = Ledger()
    led.note("f_local", event="f_local", prereg=falsify.PREREG,
             amendment="8c010702", model=a.model, adapter=a.adapter,
             card=False, constrained=a.constrained,
             battery=battery.digest, comprehension=acc,
             # ⛔ `unanswered` IS THE NUMBER THAT EXPLAINS `comprehension`, and
             # it was printed but never ledgered — so the record could not tell
             # a real 0 % from a harness that read nothing.
             unanswered=unanswered, chance=chance, comprehension_verdict=verdict,
             # ⛔ The diversity numbers are LEDGERED, not just printed — the
             # retrain plots `dependence` against checkpoint step (Diagnosis C),
             # and a number that only ever reached a terminal cannot be plotted.
             diversity=(None if div is None else vars(div)),
             # ⛔ the pairing, recorded at write time — see the comment above
             comprehension_items=per_item,
             results={"speak": speak, "render": render},
             fired=(None if f is None else f.fired), cost=back.cost_report())
    print(f"\n  ledgered → {led.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
