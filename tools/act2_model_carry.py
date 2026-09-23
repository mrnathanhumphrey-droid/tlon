"""⛔⛔ MODEL-SIDE CARRY — does the SPEAKER take up the happening it was given?

⛔⛤ THIS DID NOT EXIST, AND ITS ABSENCE WAS LOAD-BEARING. Every carry number in
this arc — 9.3%, 54.8%, 97.1% — is a property of a CORPUS, measured at build
time on text a hosted proposer wrote. Not one of them says whether the trained
7B speaker carries anything. `act2_flocal.py` contains the word "carry" zero
times. So "the strong puzzle is render AND carry" was half unmeasurable, and
the dosed arm was adjudicated on render and `choose` with carry simply absent.

⭐⭐ NO NEW GENERATION HARNESS, AND THAT IS THE POINT. F-LOCAL's `speak` probe
already hands the model a ONE-TURN history — a Tlön surface — and asks for the
next turn:

    histories = [tuple(p.surface for p in battery.comprehension[i:i+1]) ...]
    speak = _rate(speaker, [None] * n, "speak", histories=histories)

That is exactly the `provoke` task the steer was applied to. The probe was
already being run; nobody was scoring ROOT OVERLAP on it. So this reuses
`probes.build`, `LocalBackend` and `LLMSpeaker` unchanged, at the same seed —
which means these items are the SAME items F-LOCAL scored, and a carry number
is paired with that adapter's render and speak numbers rather than measured on
a different draw.

⛔ THE BAND IS THE SAME ONE THE CORPUS WAS GATED ON. `scene_carry` demands a
root carried AND a root added: a reply that carries nothing is a non-sequitur,
and a reply that adds nothing is an echo. Reporting bare overlap would score a
parrot at 100% — which is the failure mode a forced-carry steer produces, so it
is precisely the one this must not reward.

⛔ A reply that fails to PARSE is not a carry failure and is not a carry
success. It is counted separately and excluded from the rate, because folding
invalid emissions into a carry denominator would let a model that emits garbage
look like a model that changes the subject.
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


def score(prior_surface: str, proposal, roots) -> dict:
    """One probe's carry verdict. PURE — no model, no I/O, fully testable.

    `prior_surface` is the Tlön line the model was answering; `proposal` is what
    it produced, or None if nothing parseable came back.
    """
    from tlon.act2.carry import scene_carry, scene_roots
    if proposal is None:
        return {"parsed": False, "carried": None, "reason": "no proposal"}
    prior = frozenset(w for w in (prior_surface or "").split() if w in roots)
    reply = scene_roots(proposal, roots)
    if not prior:
        # ⛔ A PROMPT WITH NO ROOT CANNOT BE CARRIED FROM, and scoring it as a
        # failure would charge the model for the probe's shape. Excluded, and
        # counted so the exclusion is visible rather than silent.
        return {"parsed": True, "carried": None, "reason": "prompt has no root",
                "prior": sorted(prior), "reply": sorted(reply)}
    v = scene_carry(prior, reply)
    return {"parsed": True, "carried": bool(v.ok), "reason": v.reason,
            "prior": sorted(prior), "reply": sorted(reply),
            "overlap": sorted(prior & reply), "added": sorted(reply - prior)}


def summarise(rows) -> dict:
    from tlon.act2.carry import wilson
    scorable = [r for r in rows if r.get("carried") is not None]
    n = len(scorable)
    k = sum(1 for r in scorable if r["carried"])
    lo, hi = wilson(k, n) if n else (0.0, 1.0)
    # ⛔ The two ways the band refuses, kept apart: they mean opposite things.
    # "no root carried" is a non-sequitur; "echo" is a parrot.
    nonseq = sum(1 for r in scorable
                 if not r["carried"] and "no root carried" in (r["reason"] or ""))
    echo = sum(1 for r in scorable
               if not r["carried"] and "echo" in (r["reason"] or ""))
    # ⭐ BARE OVERLAP, reported ALONGSIDE the band and never instead of it: a
    # parrot scores 100% here and 0% on the band, and the gap is the diagnosis.
    overlap = sum(1 for r in scorable if r.get("overlap"))
    return {"n_probes": len(rows),
            "unparseable": sum(1 for r in rows if not r.get("parsed")),
            "excluded_rootless_prompt": sum(
                1 for r in rows if r.get("parsed")
                and r.get("carried") is None),
            "scorable": n, "carried": k,
            "carry_rate": round(k / n, 4) if n else 0.0,
            "carry_ci95": [round(lo, 4), round(hi, 4)],
            "bare_overlap_rate": round(overlap / n, 4) if n else 0.0,
            "refused_non_sequitur": nonseq, "refused_echo": echo}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--seed", type=int, default=7,
                    help="⛔ 7 is F-LOCAL's battery seed. Changing it makes "
                         "this a different probe set and the carry number "
                         "stops being paired with that adapter's render.")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    from act2_backends import LocalBackend
    from tlon.act2 import probes
    from tlon.grammar import classes as C
    from tlon.act2.llm import LLMSpeaker

    roots = frozenset(C.load()["classes"]["R"])
    battery = probes.build(seed=a.seed, n_prod=a.n, n_comp=a.n)
    back = LocalBackend(a.model, adapter=a.adapter, dtype=a.dtype)
    speaker = LLMSpeaker("native", back, card=False)

    print("MODEL CARRY · %s · adapter=%s · battery %s · n=%d"
          % (back.name, a.adapter or "NONE (baseline)", battery.digest, a.n))
    print("⛔ cardless — the same configuration F-LOCAL reads, on the same "
          "battery, so this number is PAIRED with that adapter's render\n")

    rows = []
    for i in range(a.n):
        prior = battery.comprehension[i].surface
        proposal = speaker.speak((prior,), i + 1)
        r = score(prior, proposal, roots)
        r["prior_surface"] = prior
        rows.append(r)

    s = summarise(rows)
    print("  probes            %d" % s["n_probes"])
    print("  unparseable       %d  (excluded — not a carry failure)"
          % s["unparseable"])
    print("  rootless prompt   %d  (excluded — nothing to carry FROM)"
          % s["excluded_rootless_prompt"])
    print("  scorable          %d" % s["scorable"])
    print()
    print("  CARRY (band)      %.1f%%  [%.1f, %.1f]   %d/%d"
          % (100 * s["carry_rate"], 100 * s["carry_ci95"][0],
             100 * s["carry_ci95"][1], s["carried"], s["scorable"]))
    print("  bare overlap      %.1f%%   ⛔ a parrot scores 100%% here and 0%% "
          "on the band" % (100 * s["bare_overlap_rate"]))
    print("  refused: non-sequitur %d · echo %d"
          % (s["refused_non_sequitur"], s["refused_echo"]))

    if a.out:
        out = pathlib.Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(
            {"summary": s, "adapter": a.adapter, "battery": battery.digest,
             "seed": a.seed, "n": a.n, "items": rows},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        tmp.replace(out)
        print("\n  ledgered → %s  (per-item, so this is PAIRABLE across "
              "adapters)" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
