"""THE FORK: does 7B-vs-7B hold a coherent exchange RAW, or degenerate?

⛔⛔ THE CRITERIA ARE WRITTEN BEFORE THE DATA AND ARE NOT NEGOTIABLE AFTERWARDS.
"Did it hold together?" is exactly the question a transcript seduces you into
answering by reading it — two people read the same exchange and one sees a
private language forming while the other sees two models stuck in a groove. So
the verdict is computed from three pre-specified signatures, and the transcript
stays sealed until they are.

    DEGENERATES if ANY of:
      (a) validity in the LAST quarter < 0.90       -- they stop speaking legally
      (b) root type/token declines > 25 % first->last window
                                                     -- F4's own pre-registered
                                                        threshold, reused
      (c) an absorbing state: a cycle of period <= 3 persisting >= 6 turns
                                                     -- the mutual-collapse
                                                        signature that reads
                                                        ΔC = +100 in the dry run

⭐ AND IT RUNS A CONTROL, because degeneration on its own is not communication-
driven. Each speaker also runs against a PRE-RECORDED non-adaptive partner. If
the interacting pair degenerates and the control does too, the finding is about
the model, not about two of them meeting — the same yoked logic the arena uses.

⛔ Runs at or above `falsify.MIN_ARENA_TEMPERATURE`; `arena_preconditions`
refuses below it, because greedy makes drift impossible by construction.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.act2 import falsify as F                             # noqa: E402
from tlon.act2 import probes                                   # noqa: E402
from tlon.act2.llm import LLMSpeaker                           # noqa: E402
from tlon.grammar.parse import render                          # noqa: E402
from tlon.product import schema as PS                          # noqa: E402

# ── PRE-SPECIFIED, LOCKED BEFORE THE RUN ─────────────────────────────────
LAST_QUARTER_VALIDITY = 0.90
TTR_DECLINE = F.ROOT_DIVERSITY_DECLINE        # 0.25, reused from F4
CYCLE_MAX_PERIOD = 3
CYCLE_MIN_RUN = 6
WINDOW = 8


def _roots(scene) -> list[str]:
    out, stack = [], [scene.node]
    while stack:
        n = stack.pop()
        out.append(n.root)
        stack.extend(c for _, c in n.edges)
    return out


def _ttr(scenes) -> float:
    toks = [r for s in scenes for r in _roots(s)]
    return len(set(toks)) / len(toks) if toks else 0.0


def _find_cycle(surfaces: list[str]) -> tuple[int, int]:
    """Longest run of a repeating cycle of period <= CYCLE_MAX_PERIOD."""
    best = (0, 0)
    for p in range(1, CYCLE_MAX_PERIOD + 1):
        run = 0
        for i in range(p, len(surfaces)):
            if surfaces[i] == surfaces[i - p]:
                run += 1
                if run > best[1]:
                    best = (p, run)
            else:
                run = 0
    return best


def exchange(speaker_a, speaker_b, *, turns: int, seed_history: tuple,
             history_window: int | None = None):
    """Alternating turns. Each speaker sees only TLÖN — never a gloss.

    ⛔⛔ `history_window` IS THE LOCALITY ARCHITECTURE'S LOAD-BEARING KNOB. At
    `window=1` the speaker is handed exactly one prior surface, so turn 40 is
    structurally identical to turn 1 and the OOD-at-depth collapse has no
    substrate. **The truncation applies from turn 0, including into the seed
    history** — a version that truncated only after the seed had accumulated
    would silently give early turns full context and the run would be
    uninterpretable in exactly the direction that flatters the hypothesis.

    ⭐ RED-PROOFED IN `tests/test_exchange_history_window.py` WITH A SPY SPEAKER
    THAT RECORDS WHAT IT ACTUALLY RECEIVED. A knob that silently no-ops returns
    "locality works" for the worst possible reason: the model saw everything and
    happened not to collapse, which says nothing about depth-1.
    """
    if history_window is not None and history_window < 1:
        raise ValueError("history_window must be >= 1 (a speaker provoked by "
                         "nothing is not a depth-1 painter, it is a cold start)")
    hist = list(seed_history)
    log = []
    for t in range(turns):
        sp = speaker_a if t % 2 == 0 else speaker_b
        shown = hist if history_window is None else hist[-history_window:]
        proposal = sp.speak(tuple(shown), t + 1)
        entry = {"turn": t, "speaker": "A" if t % 2 == 0 else "B",
                 "proposal": proposal, "valid": False, "surface": None}
        if proposal is not None:
            try:
                scene, surface, _ = PS.validate(proposal)
                entry.update(valid=True, surface=surface)
                hist.append(surface)
            except Exception:                                  # noqa: BLE001
                pass
        log.append(entry)
    return log


def analyse(log) -> dict:
    valid = [e["valid"] for e in log]
    n = len(log)
    q = max(1, n // 4)
    last_q = sum(valid[-q:]) / q

    scenes = []
    from tlon.grammar.parse import parse
    for e in log:
        if e["valid"]:
            try:
                scenes.append(parse(e["surface"]))
            except Exception:                                  # noqa: BLE001
                pass
    first_w, last_w = scenes[:WINDOW], scenes[-WINDOW:]
    ttr_first, ttr_last = _ttr(first_w), _ttr(last_w)
    decline = (ttr_first - ttr_last) / ttr_first if ttr_first else 0.0

    surfaces = [e["surface"] for e in log if e["valid"]]
    period, run = _find_cycle(surfaces)

    fired = []
    if last_q < LAST_QUARTER_VALIDITY:
        fired.append(f"(a) last-quarter validity {last_q:.0%} < "
                     f"{LAST_QUARTER_VALIDITY:.0%}")
    if decline > TTR_DECLINE:
        fired.append(f"(b) root TTR declined {decline:.0%} > {TTR_DECLINE:.0%} "
                     f"({ttr_first:.2f} → {ttr_last:.2f})")
    if run >= CYCLE_MIN_RUN:
        fired.append(f"(c) absorbing state: period-{period} cycle for {run} turns")

    return {"n_turns": n, "validity_overall": sum(valid) / n,
            "validity_last_quarter": last_q, "ttr_first": ttr_first,
            "ttr_last": ttr_last, "ttr_decline": decline,
            "cycle_period": period, "cycle_run": run,
            "fired": fired, "degenerates": bool(fired)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--turns", type=int, default=40)
    ap.add_argument("--history-window", type=int, default=None,
                    help="truncate what each speaker sees to the last N "
                         "surfaces. 1 = the locality architecture. "
                         "OMITTED = accumulate (the measured null).")
    ap.add_argument("--temperature", type=float,
                    default=F.MIN_ARENA_TEMPERATURE)
    ap.add_argument("--out", default="runs/act2/logs/exchange_probe.json")
    a = ap.parse_args()

    from act2_backends import LocalBackend

    battery = probes.build(seed=7, n_prod=64, n_comp=64)
    # ⛔ THE SEED IS DEEP ON PURPOSE. Measured: at depth 1 the model
    # deterministically ECHOES parse(history) — 8/10, 1/8 distinct — so a
    # depth-1 seed measures a mirror and the precondition would (correctly)
    # refuse. Validity decays with depth (10/10 at 1 → 5/10 at 8), so the arena
    # must be probed where it will actually live, not at its easiest point.
    seed_history = tuple(p.surface for p in battery.comprehension[:5])

    print(f"EXCHANGE PROBE · {a.turns} turns · temperature {a.temperature}")
    print("⛔ criteria locked before the run: last-quarter validity ≥ 0.90 · "
          f"TTR decline ≤ {TTR_DECLINE:.0%} · no period≤3 cycle for ≥6 turns\n")

    back = LocalBackend(a.model, adapter=a.adapter, temperature=a.temperature)
    A = LLMSpeaker("A", back, card=False)
    B = LLMSpeaker("B", back, card=False)

    # ⛔ THE PRECONDITION RUNS FIRST. If the speaker cannot vary, nothing below
    # means anything and the run must not proceed to produce a tidy null.
    warmup = [A.speak(seed_history, 1) for _ in range(F.PRECONDITION_SAMPLES)]
    F.arena_preconditions(temperature=a.temperature, same_history_samples=warmup)
    print("  ✅ vacuity precondition passed — the speaker can vary at this "
          "temperature\n")

    print("  ── INTERACTING: A and B, each adapting to the other ──")
    inter = exchange(A, B, turns=a.turns, seed_history=seed_history,
                     history_window=a.history_window)
    ri = analyse(inter)

    # ⭐ THE CONTROL. Each speaker against a PRE-RECORDED, non-adaptive partner:
    # the same number of turns, the same seed, but nobody is listening back.
    frozen = [e["surface"] for e in inter if e["valid"]][:a.turns]
    print("  ── CONTROL: A against a PRE-RECORDED partner (nobody adapts back) ──")

    class _Frozen:
        def __init__(self, turns): self._t = list(turns)
        def speak(self, history, turn):
            i = (turn - 1) // 2
            if i >= len(self._t):
                return None
            from tlon.grammar.parse import parse
            return _to_proposal(parse(self._t[i]))

    def _to_proposal(scene):
        from tlon.act2 import schema_bridge as SB
        return SB.scene_to_proposal(scene)

    ctrl = exchange(A, _Frozen(frozen), turns=a.turns,
                    seed_history=seed_history,
                    history_window=a.history_window)
    rc = analyse(ctrl)

    for name, r in (("INTERACTING", ri), ("CONTROL", rc)):
        print(f"\n  {name}")
        print(f"    validity overall      {r['validity_overall']:.0%}")
        print(f"    validity last quarter {r['validity_last_quarter']:.0%}")
        print(f"    root TTR {r['ttr_first']:.2f} → {r['ttr_last']:.2f} "
              f"({r['ttr_decline']:+.0%})")
        print(f"    longest cycle         period {r['cycle_period']}, "
              f"{r['cycle_run']} turns")
        print(f"    ⇒ {'DEGENERATES' if r['degenerates'] else 'HOLDS'}"
              + ("  [" + " · ".join(r["fired"]) + "]" if r["fired"] else ""))

    # ⛔ THE PAIRED READING. Degeneration in BOTH arms is a fact about the model;
    # only degeneration that is WORSE when someone is listening back is a fact
    # about the exchange.
    if ri["degenerates"] and rc["degenerates"]:
        verdict = ("⛔ DEGENERATES IN BOTH ARMS — this is the MODEL, not the "
                   "exchange. An intrusive-thought generator would be papering "
                   "over a speaker that cannot sustain generation at all.")
    elif ri["degenerates"]:
        verdict = ("⛔ DEGENERATES ONLY WHEN INTERACTING — the exchange itself "
                   "collapses the pair. ⭐ THIS is the case an intrusive-thought "
                   "generator is for: the arena needs an exogenous source of "
                   "novelty or the pair will find a groove and stay in it.")
    elif rc["degenerates"]:
        verdict = ("⚠️ control degenerates but the interacting pair does not — "
                   "interaction is HOLDING it together. Unexpected; inspect "
                   "before trusting.")
    else:
        verdict = ("✅ HOLDS RAW IN BOTH ARMS — 7B-vs-7B sustains a coherent "
                   "exchange with no exogenous input. The intrusive-thought "
                   "generator is an AXIS to vary, not a crutch the arena needs.")
    print(f"\n  VERDICT: {verdict}")

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"temperature": a.temperature, "turns": a.turns,
         "criteria": {"last_quarter_validity": LAST_QUARTER_VALIDITY,
                      "ttr_decline": TTR_DECLINE,
                      "cycle_max_period": CYCLE_MAX_PERIOD,
                      "cycle_min_run": CYCLE_MIN_RUN},
         "interacting": ri, "control": rc, "verdict": verdict,
         "transcript_interacting": [e["surface"] for e in inter],
         "transcript_control": [e["surface"] for e in ctrl]},
        indent=2, ensure_ascii=False), encoding="utf-8", newline="")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
