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


def _forces(prior_surface: str, proposal) -> dict:
    """The speech act the model was ANSWERING and the one it chose. PURE.

    ⛔⛤ THIS PROBE ALREADY HAD BOTH HALVES AND THREW THEM AWAY. It hands the
    model a Tlön line and reads the reply — which is exactly a `ki`->? draw —
    and scored only the roots. So when the bench started answering `ka` 13
    times out of 13, nothing on the box could say whether the speaker had
    learned the one derived cell the language carries or had simply learned
    to say `ka`.

    ⛔ Unreadable on either side is None, never a default force. A prior that
    does not parse is a probe defect; a reply with no legal force is an
    emission failure; imputing `ka` for either would manufacture the very
    finding this is here to test.
    """
    out = {"prior_force": None, "reply_force": None}
    try:
        from tlon.grammar.parse import parse
        out["prior_force"] = parse((prior_surface or "").strip()).force
    except Exception:                                         # noqa: BLE001
        pass
    if isinstance(proposal, dict):
        from tlon.grammar import classes as C
        f = proposal.get("force")
        # ⛔ `isinstance` FIRST. `schema.py` carries this same note twice: an
        # unhashable force — a model emitting `["ka"]` — raises TypeError on
        # the membership test instead of being refused as the non-force it is,
        # and a diagnostic that crashes on a malformed emission destroys the
        # measurement it was annotating.
        if isinstance(f, str) and f in set(C.load()["classes"]["F"]):
            out["reply_force"] = f
    return out


def score(prior_surface: str, proposal, roots) -> dict:
    """One probe's carry verdict. PURE — no model, no I/O, fully testable.

    `prior_surface` is the Tlön line the model was answering; `proposal` is what
    it produced, or None if nothing parseable came back.
    """
    from tlon.act2.carry import scene_carry, scene_roots
    if proposal is None:
        return {"parsed": False, "carried": None, "reason": "no proposal",
                **_forces(prior_surface, proposal)}
    prior = frozenset(w for w in (prior_surface or "").split() if w in roots)
    reply = scene_roots(proposal, roots)
    if not prior:
        # ⛔ A PROMPT WITH NO ROOT CANNOT BE CARRIED FROM, and scoring it as a
        # failure would charge the model for the probe's shape. Excluded, and
        # counted so the exclusion is visible rather than silent.
        return {"parsed": True, "carried": None, "reason": "prompt has no root",
                "prior": sorted(prior), "reply": sorted(reply),
                **_forces(prior_surface, proposal)}
    v = scene_carry(prior, reply)
    # ⛔ THE FORCE READ IS NOT CONDITIONED ON THE CARRY VERDICT. A reply that
    # changes the subject still picked a speech act, and excluding those would
    # measure force only over the replies that already behaved.
    return {"parsed": True, "carried": bool(v.ok), "reason": v.reason,
            "prior": sorted(prior), "reply": sorted(reply),
            "overlap": sorted(prior & reply), "added": sorted(reply - prior),
            **_forces(prior_surface, proposal)}


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

    # ══ THE SPEECH ACT, PROVOKED — THE PRODUCT-RELEVANT FORCE READ ══════
    # ⛔⛔ THIS IS THE ONE TO COMPARE AGAINST THE BENCH. F-LOCAL's force line is
    # the model speaking into a one-turn history; this is the model answering a
    # provocation, which is the only thing the public page ever asks it to do.
    # `dosed-s20624` answered `ka` 13 times out of 13 there.
    from tlon.act2 import carry as CARRY
    ft = CARRY.force_transitions(
        (r.get("prior_force"), r.get("reply_force")) for r in rows)
    print()
    if not ft["n"]:
        print("  FORCE             ⛔ NOT MEASURED — 0 of %d replies carried a "
              "readable force. MISSING, not a monoculture." % len(rows))
    else:
        print("  FORCE (reply)     %s   (%d/%d readable)" % (
            " · ".join("%s %.0f%%" % (k, 100 * v / ft["n"])
                       for k, v in sorted(ft["marginal"].items(),
                                          key=lambda kv: -kv[1])),
            ft["n"], len(rows)))
        # ⛔⛔ THE MARGINAL CANNOT ANSWER THIS AND THE TABLE CAN. `ki`->`ka` is
        # the single derived cell the corpus carries; a speaker that says `ka`
        # to everything produces the same histogram as one that learned it.
        rate, k, nk = CARRY.derived_cell(ft["table"], "ki", "ka")
        if rate is None:
            print("  ki -> ka          ⛔ NO `ki` PROMPTS IN THE BATTERY — the "
                  "derived cell was not probed, which is not the same as "
                  "not learned")
        else:
            print("  ki -> ka          %.0f%%  (%d/%d)   ⭐ the one derived "
                  "cell" % (100 * rate, k, nk))
        for prior in sorted(ft["table"]):
            row = ft["table"][prior]
            tot = sum(row.values())
            print("      %-3s n=%-4d %s" % (prior, tot, " ".join(
                "%s %d" % (f, c) for f, c in sorted(row.items(),
                                                    key=lambda kv: -kv[1]))))
        if ft["no_prior"]:
            print("      ⛔ %d replies had an UNPARSEABLE prompt and are in "
                  "the marginal but not the table" % ft["no_prior"])

    if a.out:
        out = pathlib.Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(
            {"summary": s, "force": ft, "adapter": a.adapter,
             "battery": battery.digest,
             "seed": a.seed, "n": a.n, "items": rows},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        tmp.replace(out)
        print("\n  ledgered → %s  (per-item, so this is PAIRABLE across "
              "adapters)" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
