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

from act2_two_speaker import (COLD, LIVE, SHARED, YOKED, Replay, exchange_two,
                              store_was_shared,   # noqa: E402
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
    ap.add_argument("--skip-cold", action="store_true",
                    help="COLD is already on disk from the recert pass")
    ap.add_argument("--shared", action="store_true",
                    help="run the SHARED-memory arm (Parfenova Algorithm 1) "
                         "instead of LIVE. PREREG_POSITIVE_CONTROL_KA c0de41c7")
    ap.add_argument("--allow-self-pair", action="store_true",
                    help="⛔⛔ CONTROL ONLY. Pairs an adapter WITH ITSELF, which "
                         "is the fault the whole arc corrected. Identical "
                         "weights ⇒ coinciding marginals, so W2 MUST read ~0; "
                         "anything else means the pipeline manufactures drift. "
                         "Output is tagged self_pair=true and must never be "
                         "pooled with real pairs.")
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

    core = None
    if a.adapter_b is None:
        back_a = LocalBackend(a.model, adapter=a.adapter_a,
                              temperature=a.temperature)
        A = LLMSpeaker("A", back_a, card=False)
        B = None
    else:
        if a.adapter_a == a.adapter_b and not a.allow_self_pair:
            raise SystemExit(
                "⛔⛔ --adapter-a and --adapter-b are the same path. That is one "
                "impression and a mirror: their marginals coincide. "
                "Pass --allow-self-pair ONLY for the control arm.")
        # ⛔⛔ ONE BASE, TWO LoRAs. Two LocalBackends would be two full 7B models
        # (~26 GB each observed) and will not fit on a 40 GB card. The adapter
        # switch is READ BACK on every generation — see act2_dual_backend.
        from act2_dual_backend import dual_views
        core, back_a, back_b = dual_views(
            a.model, a.adapter_a, a.adapter_b, temperature=a.temperature)
        A = LLMSpeaker("A", back_a, card=False)
        B = LLMSpeaker("B", back_b, card=False)
        if a.allow_self_pair and a.adapter_a == a.adapter_b:
            print("  ⛔⛔ SELF-PAIR CONTROL — one adapter as both speakers. "
                  "Identical weights ⇒ marginals coincide, so W2 MUST read ~0. "
                  "Tagged self_pair=true; never pool with real pairs.")

    # ⛔⛔ THE ARM IS NAMED IN THE DATA AND IN THE CONDITION KEY. Writing a
    # shared-memory transcript under the key `live` — with a note saying so —
    # is the caveat-in-prose failure: the note separates from the number and a
    # later reader pools two different memory models under one estimand.
    # `act2_drift.assert_arm` refuses the mismatch on the way back in.
    arm = SHARED if a.shared else LIVE
    arm_key = "shared" if a.shared else "live"
    # ⛔⛔ THE NULL RUNS THE TREATMENT'S MEMORY MODEL. AMENDMENT A to PREREG
    # c0de41c7. Registered arm 2 was the asymmetric YOKED against a SHARED
    # treatment, which varies TWO things — partner-adaptivity AND memory model
    # — so a negative delta could be entirely "long context changes the force
    # rate". PREREG_ACT2_DRIFT §4 rejects a solo control in exactly those words.
    # Only adaptivity may differ between the arms.
    null_mode = SHARED if a.shared else YOKED
    out = {"arm_mode": arm_key, "null_mode": arm_key,
           "self_pair": bool(a.adapter_a == a.adapter_b),
           "turns": a.turns, "temperature": a.temperature, "seed": a.seed,
           "adapter_a": a.adapter_a, "adapter_b": a.adapter_b,
           "injections": None if plan is None else
           {"turns": list(plan.turns), "n": a.injections, "seed": a.seed},
           "conditions": {}}

    # ── COLD — where each speaker starts, alone ─────────────────────────────
    if a.skip_cold and a.adapter_b is None:
        raise SystemExit("⛔ --skip-cold on a solo run leaves nothing to do; "
                         "the solo arm IS the cold arm.")
    if not a.skip_cold:
        print("\n  ── COLD: A alone, own chain only ──")
        cold_a = solo(A, turns=a.turns, seed_history=seed_history,
                      injections=plan, validate=_validate)
        out["conditions"]["cold_a"] = {"log": cold_a,
                                       "surfaces": _surfaces(cold_a)}

    if a.adapter_b is None:
        pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(a.out).write_text(json.dumps(out, indent=1,
                                                  ensure_ascii=False),
                                       encoding="utf-8", newline="")
        print("\n  solo arm only. wrote %s" % a.out)
        return 0

    if not a.skip_cold:
        print("  ── COLD: B alone ──")
        cold_b = solo(B, turns=a.turns, seed_history=seed_history,
                      injections=plan, validate=_validate)
        out["conditions"]["cold_b"] = {"log": cold_b,
                                       "surfaces": _surfaces(cold_b)}

    # ── LIVE — both adapt ───────────────────────────────────────────────────
    print("  ── %s ──" % ("SHARED: one append-only store, both read all of it"
                          if a.shared else
                          "LIVE: A and B, each provoked by the other's latest"))
    live_mark = core.mark() if core is not None else 0
    live = exchange_two(A, B, turns=a.turns, seed_history=seed_history,
                        injections=plan, mode=arm, validate=_validate)
    out["conditions"][arm_key] = {"log": live, "surfaces": _surfaces(live)}
    # ⛔⛔ RUN-TIME PROOF THAT TWO SPEAKERS ACTUALLY SPOKE. A transcript where one
    # adapter never activated, or where one side generated consecutive turns, is
    # one impression wearing two labels whatever the CLI said.
    if core is not None:
        # ⛔ SCOPED TO THE LIVE ARM ONLY. COLD is one speaker alone and each
        # YOKED arm is one live speaker against a recording, so a cumulative
        # check would fail on arms that are correctly one-sided.
        core.assert_two_speakers_spoke(since=live_mark)
        out["adapter_usage_live"] = core.usage_since(live_mark)
        print("    ✅ both adapters generated and alternated: %s"
              % core.usage_since(live_mark))

    # ── YOKED — the null ────────────────────────────────────────────────────
    live_a = [e["surface"] for e in live if e["valid"] and e["speaker"] == "A"]
    live_b = [e["surface"] for e in live if e["valid"] and e["speaker"] == "B"]
    print("  ── YOKED: each against a recording of the other's LIVE turns ──")
    yoked_a = exchange_two(A, Replay(live_b, label="B_rec"), turns=a.turns,
                           seed_history=seed_history, injections=plan,
                           mode=null_mode, validate=_validate)
    yoked_b = exchange_two(B, Replay(live_a, label="A_rec"), turns=a.turns,
                           seed_history=seed_history, injections=plan,
                           mode=null_mode, validate=_validate)
    if a.shared:
        # ⛔⛔ ASSERT THE MATCHED NULL ACTUALLY RAN SHARED, FROM THE TRANSCRIPT.
        # `n_shown` says how much context each turn received, so this cannot be
        # satisfied by a flag that was passed and ignored. A null that quietly
        # ran the asymmetric rule would make the contrast measure context length
        # instead of coupling — and would look like an ordinary result.
        for nm, lg in (("live/shared", live), ("yoked_a", yoked_a),
                       ("yoked_b", yoked_b)):
            if not store_was_shared(lg, turns=a.turns):
                raise SystemExit(
                    "⛔⛔ %s did not run the shared store (n_shown never reached "
                    "the full history). The arms are not matched and the "
                    "contrast would measure context length, not coupling." % nm)
        print("    ✅ all three arms verified SHARED from their own n_shown")
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
