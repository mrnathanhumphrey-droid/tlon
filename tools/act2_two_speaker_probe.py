"""TWO-SPEAKER PROBE — the runnable wiring for the asymmetric harness.

Spec: docs/SPEC_TWO_SPEAKER_DRIFT_2026_08_30.md
Harness + red-proofs: tools/act2_two_speaker.py, tests/test_two_speaker_harness.py

⭐ THE FIRST PROBE IN THIS PROJECT THAT LOADS TWO ADAPTERS. `--adapter-a` and
`--adapter-b` build two `LocalBackend`s; `_assert_two()` refuses them if they are
the same object or share a backend. Every prior Act 2 "interaction" was one
adapter and two labels.

THREE CONDITIONS, one injection plan shared by all of them:

    COLD   each speaker alone, own chain only          -> where they START
    LIVE   A and B, own chain + partner's latest       -> mutual adaptation
    YOKED  each against a RECORDING of the other's     -> input held, mutuality
           LIVE turns                                     removed  (THE NULL)

⛔ Drift is LIVE vs YOKED. COLD is the baseline, NOT the null.

⛔ `--no-injections` exists because panel re-certification must run on an arm
with no injected material in it at all: contamination is between-build sd over
within-conversation movement, every build would see the SAME injections, and a
biased pool would compress that sd and certify observables as more build-stable
than they are.
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

from act2_two_speaker import (COLD, LIVE, YOKED, Replay, exchange_two,   # noqa: E402
                              measurable_turns, plan_injections, solo)
from tlon.act2 import falsify as F                                       # noqa: E402
from tlon.act2 import probes                                             # noqa: E402
from tlon.act2.llm import LLMSpeaker                                     # noqa: E402
from tlon.product import schema as PS                                    # noqa: E402


def _validate(proposal):
    """Grammar gate. Returns the surface, or raises so the turn is marked bad."""
    _scene, surface, _ = PS.validate(proposal)
    return surface


def _surfaces(log):
    """⛔ MEASURABLE turns only — never a turn the injection pool was visible
    for. Structural defence, independent of whether the bias is detectable."""
    return [e["surface"] for e in measurable_turns(log)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter-a", required=True)
    ap.add_argument("--adapter-b", default=None,
                    help="omit for a COLD-only (solo) run — the arm used for "
                         "panel re-certification and the cold baseline")
    ap.add_argument("--turns", type=int, default=40)
    ap.add_argument("--temperature", type=float, default=F.MIN_ARENA_TEMPERATURE)
    ap.add_argument("--pool", default="runs/act2/injection_pool_native.json")
    ap.add_argument("--injections", type=int, default=4)
    ap.add_argument("--no-injections", action="store_true",
                    help="⛔ REQUIRED for the panel re-certification arm")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    from act2_backends import LocalBackend

    battery = probes.build(seed=a.seed, n_prod=64, n_comp=64)
    seed_history = tuple(p.surface for p in battery.comprehension[:5])

    plan = None
    if not a.no_injections:
        pool = json.loads(pathlib.Path(a.pool).read_text(encoding="utf-8"))
        plan = plan_injections(seed=a.seed, turns=a.turns, n=a.injections,
                               pool=pool)

    print("TWO-SPEAKER PROBE · %d turns · temp %.2f" % (a.turns, a.temperature))
    print("  A %s" % a.adapter_a)
    print("  B %s" % (a.adapter_b or "(none — COLD/solo arm)"))
    print("  injections %s" % ("OFF (re-certification arm)" if plan is None
                               else "%d at turns %s" % (a.injections, plan.turns)))

    back_a = LocalBackend(a.model, adapter=a.adapter_a, temperature=a.temperature)
    A = LLMSpeaker("A", back_a, card=False)

    out = {"turns": a.turns, "temperature": a.temperature, "seed": a.seed,
           "adapter_a": a.adapter_a, "adapter_b": a.adapter_b,
           "injections": None if plan is None else
           {"turns": list(plan.turns), "n": a.injections, "seed": a.seed},
           "conditions": {}}

    # ── COLD — where each speaker starts, alone ─────────────────────────────
    print("\n  ── COLD: A alone, own chain only ──")
    cold_a = solo(A, turns=a.turns, seed_history=seed_history,
                  injections=plan, validate=_validate)
    out["conditions"]["cold_a"] = {"log": cold_a, "surfaces": _surfaces(cold_a)}

    if a.adapter_b is None:
        pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(a.out).write_text(json.dumps(out, indent=1,
                                                  ensure_ascii=False),
                                       encoding="utf-8", newline="")
        print("\n  solo arm only. wrote %s" % a.out)
        return 0

    back_b = LocalBackend(a.model, adapter=a.adapter_b, temperature=a.temperature)
    B = LLMSpeaker("B", back_b, card=False)
    # ⛔⛔ THE ASSERTION THAT WAS MISSING FOR MONTHS. Two adapter paths can still
    # point at one directory; distinct backend OBJECTS are necessary, and the
    # paths differing is what makes them distinct MODELS.
    if a.adapter_a == a.adapter_b:
        raise SystemExit("⛔⛔ --adapter-a and --adapter-b are the same path. "
                         "That is one impression and a mirror: identical "
                         "speakers cannot converge.")

    print("  ── COLD: B alone ──")
    cold_b = solo(B, turns=a.turns, seed_history=seed_history,
                  injections=plan, validate=_validate)
    out["conditions"]["cold_b"] = {"log": cold_b, "surfaces": _surfaces(cold_b)}

    # ── LIVE — both adapt ───────────────────────────────────────────────────
    print("  ── LIVE: A and B, each provoked by the other's latest ──")
    live = exchange_two(A, B, turns=a.turns, seed_history=seed_history,
                        injections=plan, mode=LIVE, validate=_validate)
    out["conditions"]["live"] = {"log": live, "surfaces": _surfaces(live)}

    # ── YOKED — the null ────────────────────────────────────────────────────
    live_a = [e["surface"] for e in live if e["valid"] and e["speaker"] == "A"]
    live_b = [e["surface"] for e in live if e["valid"] and e["speaker"] == "B"]
    print("  ── YOKED: each against a recording of the other's LIVE turns ──")
    yoked_a = exchange_two(A, Replay(live_b, label="B_rec"), turns=a.turns,
                           seed_history=seed_history, injections=plan,
                           mode=YOKED, validate=_validate)
    yoked_b = exchange_two(B, Replay(live_a, label="A_rec"), turns=a.turns,
                           seed_history=seed_history, injections=plan,
                           mode=YOKED, validate=_validate)
    out["conditions"]["yoked_a"] = {"log": yoked_a, "surfaces": _surfaces(yoked_a)}
    out["conditions"]["yoked_b"] = {"log": yoked_b, "surfaces": _surfaces(yoked_b)}

    for k, v in out["conditions"].items():
        n_inj = sum(e["injected"] for e in v["log"])
        print("    %-9s %2d measurable of %d turns (%d injected, excluded)"
              % (k, len(v["surfaces"]), a.turns, n_inj))

    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                   encoding="utf-8", newline="")
    print("\nwrote %s" % a.out)
    print("⛔ No distance is computed here. The panel is still window-1 "
          "provisional and\n   must be re-certified on THESE transcripts first.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
