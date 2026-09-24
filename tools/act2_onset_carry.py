"""⛔⛔ CARRY BY WINDOW DEPTH, AND THE THREE-TURN JOINT — THE PRODUCT'S NUMBER.

⛔⛤ `act2_model_carry.py` IS A DEPTH-0 PROBE AND WAS READ AS A POOLED ONE. It
calls `speaker.speak((prior,), i+1)` — a ONE-element history — so every item is
a fresh single exchange. That makes v1's published **27.5% carry the TURN-1
number**, and turns 2 and 3 have never been measured on the served model at
all. Every three-turn figure quoted in this arc was therefore an extrapolation
from one point, and it was quoted as though it were an estimate.

⭐⭐ THE PRODUCT TARGET IS A JOINT RATE, NOT A PER-TURN ONE. Nate: "Nat Friedman
can get 3 messages and stare for a while but we're confident it's repeated one
of his words." That is `P(>=1 exact root carry across turns 1-3)`. A per-turn
rate only reaches it through an INDEPENDENCE ASSUMPTION that nothing in this
repo has ever tested — and if the model has a per-conversation propensity,
carries cluster and the true joint sits BELOW the independent prediction.

⭐⭐ SO THIS MEASURES THE JOINT DIRECTLY, PER CONVERSATION, and reports the
independent prediction beside it as a CONTRAST rather than as the answer. The
gap between them is the clustering, quantified instead of hedged.

⛔ THE HUMAN SIDE COMES FROM THE HELD-OUT UNSTEERED POOL, AND BOTH HALVES OF
THAT MATTER.
  * HELD OUT — 265 of the 599 unsteered conversations are inside v1's dosed
    training corpus (verified by id intersection). Probing on those is
    train-on-test. 334 are clean and 293 of those run >=3 exchanges.
  * UNSTEERED — the steered pool's ENGLISH was itself written to carry, so
    feeding it would simulate a reader who cooperates with the puzzle. Nat
    will not. The unsteered English is ordinary dialogue, which is the
    stimulus the product actually meets.

⛔⛔ IT DRIVES THE SERVED `Speaker.turn()` VERBATIM — no loop is reimplemented
here. `puzzle/speaker.py` warns that its own body exists only because the
window has to be set between the two generate calls; duplicating that seam in a
probe would mean measuring a copy of the product and reporting it as the
product. Scenes are recovered from the returned surfaces with the frozen
parser, which is LOSSLESS because every surface has already passed the gate
that proves `parse(render(scene)) == scene`.

⛔ EXACT CARRY IS SCORED BY `act2_model_carry.score` UNCHANGED. Re-deriving the
predicate here — even "better", e.g. walking the prior's tree instead of
splitting its surface — would silently break comparability with the published
27.5% and this probe's whole job is to sit next to that number.

⛔ SOFT CARRY IS REPORTED BESIDE EXACT, NEVER INSTEAD OF IT. The product
sentence has two clauses: one of his words repeated (EXACT) and the others
similar enough to make sense (SOFT). They are two measurements.

⛔⛔ AND IT READS DEPTH 3-4 TOO. An onset adapter that raised carry EVERYWHERE
would be the dose-1.0 cell already rejected on render (82.4%). Without the deep
rows, "the onset worked" is indistinguishable from that failure.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

#: ⛔ The reader's first three messages. This is the product claim's window and
#: it is NOT a tuning knob — changing it changes what is being promised.
ONSET_TURNS = 3

#: ⭐ How deep the probe drives. Must exceed ONSET_TURNS so the conditional can
#: be distinguished from an unconditional lift; capped at the serve window.
MAX_TURNS = 5


# ── selection ───────────────────────────────────────────────────────────────

def held_out(conversations: list[dict], trained_ids) -> list[dict]:
    """Conversations the adapter under test never saw.

    ⛔ BY ID, NOT BY DIRECTORY. The unsteered pool and v1's dosed corpus are
    different FILES that share 265 conversations; a directory-level "this is
    the other corpus" is exactly the reasoning that put trained rows in a test
    set once already in this repo.
    """
    bad = set(trained_ids)
    return [c for c in conversations if c.get("id") not in bad]


def english_thread(conv: dict) -> list[str]:
    """The human side of one conversation, in order.

    ⛔ P TURNS ONLY. The T turns are what the model is being asked to produce;
    feeding them back as stimulus would hand it its own answer.
    """
    return [t["english"] for t in conv["turns"] if t.get("voice") == "P"]


def select(conversations: list[dict], trained_ids, n: int, seed: int,
           min_turns: int = ONSET_TURNS) -> list[dict]:
    """A deterministic held-out sample long enough to carry the claim.

    ⛔ A conversation shorter than `min_turns` cannot contribute to the joint
    and would quietly shrink its denominator while still inflating the per-depth
    counts at depth 0 and 1. Excluded up front, and the count is reported.
    """
    pool = [c for c in held_out(conversations, trained_ids)
            if len(english_thread(c)) >= min_turns]
    rng = random.Random(seed)
    order = sorted(pool, key=lambda c: c["id"])     # ⛔ id-sorted, so the
    rng.shuffle(order)                              # shuffle is reproducible
    return order[:n]                                # regardless of file order


# ── scoring ─────────────────────────────────────────────────────────────────

def as_proposer_shape(roots_found) -> dict:
    """A minimal proposer-shaped scene carrying exactly `roots_found`.

    ⭐⭐ THIS IS WHY `score` STAYS UNTOUCHED. The reply arrives from `parse()`
    in the dataclass shape; rather than re-implement the carry predicate for
    that shape — which would fork the definition the published 27.5% was
    measured with — the ROOTS are translated into the shape `score` already
    reads, and `score` decides. One predicate, two shapes, no second opinion.

    ⛔ A chain of `edges`, not siblings, because `scene_roots` collects `root`
    at every depth but only one `root` per node.
    """
    node: dict = {}
    cur = node
    for r in sorted(roots_found):
        if "root" not in cur:
            cur["root"] = r
        else:
            child: dict = {"root": r}
            cur["edges"] = [{"relator": "pos", "node": child}]
            cur = child
    return {"node": node}


def score_turn(prior_surface, reply_scene, roots) -> dict:
    """Exact band + soft band for one exchange.

    ⛔ `score` IS IMPORTED, NOT REWRITTEN. See the module docstring.

    ⛔⛔ THE REPLY ARRIVES IN THE PARSED SHAPE AND `score` READS THE PROPOSER
    SHAPE. `scene_roots` reads `aspect_root` and `edge["node"]`; a `parse()`
    tree has `aspect` and `(relator, node)`. Handing it straight over returned
    an empty root set, and this probe reported **0.0% carry at every depth,
    with clean confidence intervals**, on a pool an independent instrument had
    already measured at 9.3%. Caught only because the probe was calibrated
    against a known quantity before it was allowed to cost anything.
    """
    from act2_model_carry import score
    from tlon.act2.carry import parsed_roots, scene_carry_soft

    reply = parsed_roots(reply_scene, roots)
    r = dict(score(prior_surface, as_proposer_shape(reply), roots))
    if r.get("carried") is None:
        r["carried_soft"] = None
        return r
    v = scene_carry_soft(frozenset(r["prior"]), frozenset(r["reply"]))
    r["carried_soft"] = bool(v.ok)
    r["reason_soft"] = v.reason
    return r


def by_depth(items: list[dict]) -> dict:
    """Per-depth exact/soft rates. `items` are flat turn records."""
    from tlon.act2.carry import wilson

    out = {}
    depths = sorted({it["depth"] for it in items})
    for d in depths:
        at = [it for it in items if it["depth"] == d]
        scorable = [it for it in at if it.get("carried") is not None]
        n = len(scorable)
        k = sum(1 for it in scorable if it["carried"])
        ks = sum(1 for it in scorable if it.get("carried_soft"))
        lo, hi = wilson(k, n) if n else (0.0, 1.0)
        out[str(d)] = {
            "turns": len(at),
            "refused": sum(1 for it in at if not it.get("parsed")),
            "rootless_prompt": sum(1 for it in at if it.get("parsed")
                                   and it.get("carried") is None),
            "scorable": n,
            "carried": k,
            "carry_rate": round(k / n, 4) if n else None,
            "carry_ci95": [round(lo, 4), round(hi, 4)],
            "soft_rate": round(ks / n, 4) if n else None,
        }
    return out


def joint(conversations: list[dict], window: int = ONSET_TURNS) -> dict:
    """`P(>=1 exact carry within the first `window` turns)`, measured.

    ⛔⛔ THE MARGINALS USED FOR THE INDEPENDENCE CONTRAST ARE COMPUTED ON THE
    CLEAN SUBSET ONLY — the same conversations the observed joint is computed
    on. Taking them from the full per-depth table instead would compare a
    statistic to a reference drawn from a different population, which is the
    error this repo has logged nine times.

    Two denominators, both reported, neither preferred silently:
      CLEAN — conversations where all `window` turns produced a scorable reply.
              This is the number the independence contrast is valid against.
      ALL   — every sampled conversation, with a refusal counted as no-carry.
              This is what a reader actually experiences, because a refusal
              shows them nothing to notice.
    """
    from tlon.act2.carry import wilson

    clean, allc = [], []
    for c in conversations:
        turns = [t for t in c["turns"] if t["depth"] < window]
        got = sorted(turns, key=lambda t: t["depth"])
        allc.append(any(t.get("carried") for t in got))
        if len(got) == window and all(t.get("carried") is not None for t in got):
            clean.append(got)

    n_clean = len(clean)
    k_clean = sum(1 for g in clean if any(t["carried"] for t in g))
    lo, hi = wilson(k_clean, n_clean) if n_clean else (0.0, 1.0)

    # the independence prediction, from THIS subset's own marginals
    pred = None
    marginals = []
    if n_clean:
        prod = 1.0
        for d in range(window):
            hits = sum(1 for g in clean if g[d]["carried"])
            p = hits / n_clean
            marginals.append(round(p, 4))
            prod *= (1.0 - p)
        pred = round(1.0 - prod, 4)

    k_all = sum(1 for v in allc if v)
    lo_a, hi_a = wilson(k_all, len(allc)) if allc else (0.0, 1.0)
    return {
        "window": window,
        "clean_n": n_clean, "clean_hits": k_clean,
        "clean_rate": round(k_clean / n_clean, 4) if n_clean else None,
        "clean_ci95": [round(lo, 4), round(hi, 4)],
        "marginals_clean": marginals,
        "independent_prediction": pred,
        # ⭐ NEGATIVE = carries CLUSTER and the independent figure OVERSTATES
        # the product's reach. This is the quantity that has been assumed away.
        "clustering_gap": (round((k_clean / n_clean) - pred, 4)
                           if n_clean and pred is not None else None),
        "all_n": len(allc), "all_hits": k_all,
        "all_rate": round(k_all / len(allc), 4) if allc else None,
        "all_ci95": [round(lo_a, 4), round(hi_a, 4)],
    }


def summarise(conversations: list[dict]) -> dict:
    items = [t for c in conversations for t in c["turns"]]
    return {"conversations": len(conversations),
            "turns": len(items),
            "by_depth": by_depth(items),
            "joint_onset": joint(conversations, ONSET_TURNS)}


# ── the run ─────────────────────────────────────────────────────────────────

class ReplaySpeaker:
    """⭐⭐ THE INSTRUMENT'S OWN CALIBRATION, AND IT COSTS NOTHING.

    Returns the conversation's RECORDED surfaces instead of generating. Two
    jobs, and the second is the one that matters:

      1. It executes every line of `drive`, `score_turn`, `summarise` and
         `_report` plus the ledger write, so a typo cannot surface twenty
         minutes into a paid run.
      2. Replayed over the unsteered pool it must reproduce that corpus's
         KNOWN carry — ~9% at every depth, measured independently by
         `onset_depth_audit`. A probe that cannot recover a quantity already
         established by another instrument is not ready to measure a new one.

    ⛔ IT IS NOT A MODEL AND ITS OUTPUT IS NOT A RESULT. It reports what the
    corpus already says; the whole question is what the SPEAKER does.
    """

    def __init__(self, conv):
        self.script = []
        turns = conv["turns"]
        for a, b in zip(turns, turns[1:]):
            if a["voice"] == "P" and b["voice"] == "T":
                self.script.append((a["surface"], b["surface"]))

    def turn(self, english, write_pairs, provoke_pairs):
        if not self.script:
            return {"you": {}, "tlon": {}}
        prov, reply = self.script.pop(0)
        return {"you": {"surface": prov, "refused": None},
                "tlon": {"surface": reply, "refused": None}}


def drive(speaker, conv: dict, roots, max_turns: int) -> dict:
    """One conversation against the SERVED turn function.

    ⛔ A REFUSED WRITE PRODUCES NO PROVOCATION, so that turn is recorded and the
    pairs are NOT extended — mirroring the product, where a refusal leaves the
    window untouched and the reader simply tries again. Extending the window
    with a half-exchange would train the probe's context on a shape the server
    never builds.
    """
    from tlon.grammar.parse import ParseError, parse

    write_pairs: list[tuple[str, str]] = []
    provoke_pairs: list[tuple[str, str]] = []
    records = []

    for depth, english in enumerate(english_thread(conv)[:max_turns]):
        out = speaker.turn(english, write_pairs, provoke_pairs)
        you, tlon = out.get("you") or {}, out.get("tlon") or {}
        prov, reply_surface = you.get("surface"), tlon.get("surface")

        rec = {"depth": depth, "english": english,
               "provocation": prov, "reply": reply_surface,
               "write_refused": you.get("refused"),
               "reply_refused": tlon.get("refused")}

        if not prov or not reply_surface:
            rec.update({"parsed": False, "carried": None, "carried_soft": None,
                        "reason": "refused"})
            records.append(rec)
            continue

        # ⭐ LOSSLESS: the surface passed the gate, which proves it re-parses to
        # the scene it was rendered from.
        try:
            scene = parse(reply_surface)
        except (ParseError, KeyError, ValueError) as exc:
            rec.update({"parsed": False, "carried": None, "carried_soft": None,
                        "reason": "reply did not re-parse: %s" % exc})
            records.append(rec)
            continue

        rec.update(score_turn(prov, scene, roots))
        records.append(rec)

        write_pairs.append((english, prov))
        provoke_pairs.append((prov, reply_surface))

    return {"id": conv["id"], "theme": conv.get("theme"), "turns": records}


def _report(s: dict) -> None:
    print("  conversations %d · turns %d" % (s["conversations"], s["turns"]))
    print()
    print("  depth      n   refused   CARRY%   [95% CI]        soft%")
    for d, r in sorted(s["by_depth"].items(), key=lambda kv: int(kv[0])):
        if r["scorable"]:
            print("  %5s  %5d   %5d   %6.1f   [%4.1f,%4.1f]   %6.1f"
                  % (d, r["scorable"], r["refused"], 100 * r["carry_rate"],
                     100 * r["carry_ci95"][0], 100 * r["carry_ci95"][1],
                     100 * r["soft_rate"]))
        else:
            print("  %5s  %5d   %5d        —" % (d, 0, r["refused"]))

    j = s["joint_onset"]
    print()
    print("  ── THE PRODUCT NUMBER · >=1 carry in the first %d turns ──"
          % j["window"])
    if j["clean_rate"] is not None:
        print("    CLEAN  %d/%d = %.1f%%  [%.1f, %.1f]"
              % (j["clean_hits"], j["clean_n"], 100 * j["clean_rate"],
                 100 * j["clean_ci95"][0], 100 * j["clean_ci95"][1]))
        print("    marginals on that subset: %s" % j["marginals_clean"])
        print("    if the turns were INDEPENDENT: %.1f%%"
              % (100 * j["independent_prediction"]))
        gap = j["clustering_gap"]
        print("    clustering gap: %+.1f pts   %s"
              % (100 * gap,
                 "⛔ carries CLUSTER — the independent figure OVERSTATES reach"
                 if gap < -0.02 else
                 "⭐ no material clustering; independence was a fair assumption"
                 if abs(gap) <= 0.02 else
                 "carries ANTI-cluster — spread wider than independent"))
    print("    ALL    %d/%d = %.1f%%  [%.1f, %.1f]   (refusal counts as miss)"
          % (j["all_hits"], j["all_n"], 100 * j["all_rate"],
             100 * j["all_ci95"][0], 100 * j["all_ci95"][1]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--conversations",
                    default="runs/act2/corpus_conversations/conversations.jsonl",
                    help="the UNSTEERED pool — ordinary human dialogue")
    ap.add_argument("--trained-on",
                    default="runs/act2/corpus_conv_dosed/conversations.jsonl",
                    help="⛔ the corpus the adapter under test was TRAINED on; "
                         "its ids are excluded. Pass the right one or this "
                         "measures memorisation.")
    ap.add_argument("--adapter", default=None,
                    help="defaults to whatever puzzle/speaker.py serves")
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--max-turns", type=int, default=MAX_TURNS)
    ap.add_argument("--lexicon", default="lexicon_expanded.yaml",
                    help="⛔⛔ THE LANGUAGE THE ADAPTER WAS TRAINED IN. The "
                         "process default is the FROZEN 156-root lexicon, and "
                         "49.9%% of v1's training turns use a root that exists "
                         "only in the expanded one — so running this probe on "
                         "the default would refuse about half the replies and "
                         "read as a carry collapse.")
    ap.add_argument("--out", default=None)
    ap.add_argument("--replay", action="store_true",
                    help="⭐ no model: replay each conversation's RECORDED "
                         "surfaces. Certifies the probe against the corpus's "
                         "known carry before a paid run. NOT a result.")
    a = ap.parse_args()

    # ⛔⛔ BEFORE ANY `tlon` IMPORT. `classes.load` is lru_cached and
    # `tlon.act2.carry` reads the lexicon at IMPORT time, so setting this later
    # binds the probe to whichever language happened to load first.
    import os
    os.environ["TLON_LEXICON"] = a.lexicon
    if a.adapter:
        os.environ["TLON_ADAPTER"] = a.adapter

    from tlon.grammar import classes as C
    # ⛔⛔ ALL THREE CACHES. `load.cache_clear()` alone leaves `form_class` and
    # `_aspect_re` bound to whichever lexicon loaded first, and `parse` then
    # refuses tokens that exist. See `classes.reset_caches`.
    C.reset_caches()
    lex = C.load()
    roots = frozenset(lex["classes"]["R"])
    print("lexicon %s · %d roots · %s"
          % (a.lexicon, len(roots), lex["_hash"]))

    src = pathlib.Path(a.conversations)
    convs = [json.loads(ln) for ln in src.read_text(encoding="utf-8").splitlines()
             if ln.strip()]
    trained = [json.loads(ln)["id"] for ln
               in pathlib.Path(a.trained_on).read_text(encoding="utf-8").splitlines()
               if ln.strip()]
    sample = select(convs, trained, a.n, a.seed)

    if a.replay:
        speaker, adapter_name = None, "REPLAY (no model)"
    else:
        import importlib
        sp = importlib.import_module("puzzle.speaker")
        speaker, adapter_name = sp.Speaker(), sp.ADAPTER

    print("ONSET CARRY · adapter=%s · n=%d · seed=%d · depths 0-%d"
          % (adapter_name, len(sample), a.seed, a.max_turns - 1))
    print("⛔ held-out: %d of %d pool conversations excluded as trained-on"
          % (len(convs) - len(held_out(convs, trained)), len(convs)))
    if len(sample) < a.n:
        print("  ⚠ asked for %d, only %d held-out conversations run >=%d turns "
              "— report this, do not round it" % (a.n, len(sample), ONSET_TURNS))
    print()

    driven = []
    for i, c in enumerate(sample):
        driven.append(drive(speaker or ReplaySpeaker(c), c, roots, a.max_turns))
        # ⛔ EVERY 10, NOT 25. The watchdog kills on a 45-min stall and one
        # conversation is ~8 generations ≈ 1 min, so 25 would leave 25 min of
        # silence — over half the stall budget, on a healthy run.
        if (i + 1) % 10 == 0:
            print("    %d/%d conversations" % (i + 1, len(sample)), flush=True)

    s = summarise(driven)
    print()
    _report(s)

    if a.out:
        out = pathlib.Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(
            {"summary": s, "adapter": adapter_name, "seed": a.seed,
             "replay": bool(a.replay),
             "n_requested": a.n, "max_turns": a.max_turns,
             "conversations_source": str(src), "trained_on": a.trained_on,
             "items": driven}, ensure_ascii=False, indent=1),
            encoding="utf-8", newline="\n")
        tmp.replace(out)
        # ⛔⛤ THE LAST BATTERY'S PER-ITEM LEDGER DIED WITH ITS BOX AND EVERY
        # COMPARISON SINCE HAS BEEN UNPAIRED. Persist, then pull.
        print("\n  ledgered → %s  (per-item and per-conversation — PULL IT "
              "BEFORE THE BOX DIES)" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
