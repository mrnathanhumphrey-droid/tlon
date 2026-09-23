"""⛔⛔ DOSE THE STEER — carry as an OPTION, not a reflex.

⭐ WHY THIS ARM EXISTS, AND WHY IT IS NOT THE ONE THAT WAS SPECCED. The 14-point
render cost was attributed to "the recipe", and the two remaining suspects were
the +40% lexicon expansion and the multi-turn structure. The corpora refute
both: `corpus_bench_steered` and `corpus_bench_rowmatch` have identical row
counts (15,225/14,921), identical sources (natural 8,181 · contrastive 2,466 ·
conversation 4,578), the same expanded lexicon 08c03b0a…, and both are
multi-turn. Neither suspect was ever in the contrast.

⭐⭐ THE ENTIRE DIFFERENCE IS 2,289 PROVOKE ROWS — 15% of the corpus — GOING
FROM 9.3% CARRY TO 100%. Measured prompt->target, which is where the steer
lives: the provoke task is `P.surface -> T.scene`, and at 100% forced carry it
teaches ALWAYS EMIT A ROOT YOU JUST SAW IN THE INPUT. That is a copy reflex,
and the steered model's failures were 23 of 23 "some other class -> R", which
is what a copy reflex looks like leaking into general production.

⛔ The write thread cannot be involved: it is built from P TURNS ONLY
(`w_items = [(t["english"], t["scene"]) for t in p_turns]`), so 12,936 of the
15,225 rows are untouched by the steer by construction.

So the dial is the DOSE. The softened-steer arm, now closed, moved exact-root
copying from 100% to ~81% — a fifth, which is why it measured too weak to test.
This moves it to ~50%.

⛔⛔ THE CAVEAT, ACCEPTED WITH EYES OPEN AND RECORDED HERE. The two pools are
different CONVERSATION SETS, so this is a blend of two populations rather than
a 50% dose of one. A properly dosed rebuild of a single population costs ~$32
of proposer calls; this costs nothing because both pools are already on disk.
They were already compared head-to-head as whole corpora at matched size, which
is what makes the blend acceptable — but it is NOT the clean subtraction, and a
result near the noise floor should be read with that in mind.

⛔ WHOLE CONVERSATIONS, NEVER SPLICED ROWS. Taking individual rows from each
pool would put a conversation's write rows and provoke rows on opposite sides
of the treatment, which is a worse confound than the one above and an invisible
one.
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

from act2_build_multiturn_rows import rows_from_conversation  # noqa: E402

#: ⛔ The dose is the fraction of CONVERSATIONS drawn from the steered pool.
#: The resulting prompt->target carry rate is an OUTCOME of that and is
#: reported, never assumed: 0.5 dose lands near 0.5*100% + 0.5*9.3% = 54.6%.
#: Measured on the built corpus: 54.8% [52.7, 56.8]. The arm sits between its
#: two references — 9.3% (arm1) · 54.8% (this) · 100% (steered).
TOLERANCE = 0.03

#: ⛔⛔ THE READING, FIXED BEFORE THE RUN. Written here and committed before any
#: box is launched, so the verdict cannot be chosen after the numbers land.
#: Reference points, both measured at n=256 on the same battery:
#:     steered  bench-s20624   render 82.4%  ·  choose 61.3%
#:     arm1     rowmatch       render 96.5%  ·  choose 46.5%
READING = {
    "render recovers toward ~96% AND choose stays well above arm1's 46.5%":
        "⭐ THE DOSE WAS THE COST. Carry at 100% taught a copy reflex; at ~55% "
        "it is learned as an option. This is the strong puzzle — render AND "
        "comprehension — and a ship candidate.",
    "render recovers BUT choose falls back to ~arm1":
        "The two are genuinely traded and the trade is roughly linear in the "
        "dose. Then the product call Nate already framed stands, and the dose "
        "is the dial on it rather than a way out of it.",
    "render stays ~82% at half the dose":
        "⛔ THE COPY-REFLEX STORY IS WRONG. A treatment halved that costs the "
        "same render is not dose-dependent, and the cost lives somewhere this "
        "arc has not looked. Say so plainly and stop guessing at mechanisms.",
    "render BELOW 82% or choose BELOW 46.5%":
        "Void. A blend cannot be worse than both parents on the same axis; "
        "that would indict the blend itself — most likely the two conversation "
        "populations differing in some way this arm did not control.",
}


def build(steered, unsteered, *, rows_target, dose, depth, seed):
    """Interleave whole conversations to hit BOTH the row target and the dose."""
    rng = random.Random(seed)
    pools = {"steered": list(steered), "unsteered": list(unsteered)}
    for v in pools.values():
        rng.shuffle(v)
    idx = {"steered": 0, "unsteered": 0}
    cost = {k: [len(rows_from_conversation(c, depth)) for c in v]
            for k, v in pools.items()}

    chosen: list[dict] = []
    got = {"steered": 0, "unsteered": 0}
    total = 0
    while total < rows_target:
        # ⛔ Pick whichever pool moves the running dose TOWARD the target, so
        # the mix is controlled at every step rather than only in expectation.
        # ⛔⛤ THE `+ 1` IS LOAD-BEARING AND A TEST CAUGHT ITS ABSENCE. With
        # `got < dose * total`, a dose of 1.0 flips to the other pool the
        # moment the first conversation lands — `got == total` is not `<` it —
        # so the dial could not reach its own endpoint. Comparing against the
        # total AFTER one more row makes the boundary inclusive, so dose 0.0
        # and 1.0 are exactly the two parent arms and everything between is
        # unbiased at the edges.
        want = "steered" if (got["steered"] < dose * (total + 1)) \
            else "unsteered"
        order = [want, "unsteered" if want == "steered" else "steered"]
        placed = False
        for key in order:
            i = idx[key]
            while i < len(pools[key]):
                n = cost[key][i]
                if total + n <= rows_target:
                    chosen.append(pools[key][i])
                    got[key] += n
                    total += n
                    idx[key] = i + 1
                    placed = True
                    break
                i += 1           # ⛔ SKIP, never truncate a conversation
            if placed:
                break
            idx[key] = i
        if not placed:
            break
    return chosen, got, total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steered",
                    default="runs/act2/corpus_conv_steered/conversations.jsonl")
    ap.add_argument("--unsteered",
                    default="runs/act2/corpus_conversations/conversations.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rows", type=int, default=4578,
                    help="conversation-row target; 4,578 matches BOTH prior "
                         "arms exactly, which is what makes the render delta "
                         "attributable to the dose alone")
    ap.add_argument("--dose", type=float, default=0.50)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20624)
    ap.add_argument("--seed-scan", type=int, default=40,
                    help="how far above --seed to look for the first seed that "
                         "lands EXACTLY on --rows. See the seed rule below.")
    args = ap.parse_args()

    def load(p):
        return [json.loads(l) for l in pathlib.Path(p).open(encoding="utf-8")
                if l.strip()]

    st, un = load(args.steered), load(args.unsteered)
    # ⛔⛔ VERIFY THE POOLS ARE WHAT THEY CLAIM. A pool mislabelled here would
    # produce a corpus stamped `dosed` that is really one arm or the other.
    bad = [c["id"] for c in st if not c.get("forced_root_carry")]
    if bad:
        raise SystemExit("⛔⛔ %d conversations in the STEERED pool are not "
                         "stamped forced_root_carry: %r" % (len(bad), bad[:5]))
    bad = [c["id"] for c in un if c.get("forced_root_carry")]
    if bad:
        raise SystemExit("⛔⛔ %d conversations in the UNSTEERED pool ARE "
                         "stamped forced_root_carry: %r" % (len(bad), bad[:5]))
    print("pools: %d steered · %d unsteered" % (len(st), len(un)))

    # ⛔⛔ THE SEED RULE, STATED SO IT CANNOT LOOK LIKE SEED-SHOPPING. Whole
    # conversations come in indivisible row counts, so most seeds land a row or
    # two short of the target and the size guard below refuses them. The rule is
    # THE FIRST SEED AT OR ABOVE `--seed` THAT LANDS EXACTLY AND IN TOLERANCE —
    # not the best of several, and the search looks only at ROW COUNT and DOSE,
    # both of which are structural and were fixed before any of this ran. No
    # outcome is visible to it. The chosen seed is recorded below.
    used = args.seed
    for cand in range(args.seed, args.seed + args.seed_scan):
        chosen, got, total = build(st, un, rows_target=args.rows,
                                   dose=args.dose, depth=args.depth,
                                   seed=cand)
        if total == args.rows and \
                abs(got["steered"] / total - args.dose) <= TOLERANCE:
            used = cand
            break
    else:
        raise SystemExit("⛔⛔ REFUSING: no seed in [%d, %d) lands exactly on "
                         "%d rows within %.2f of dose %.2f."
                         % (args.seed, args.seed + args.seed_scan, args.rows,
                            TOLERANCE, args.dose))
    if used != args.seed:
        print("seed   %d asked · %d used (first that lands exactly on %d rows)"
              % (args.seed, used, args.rows))
    if total != args.rows:
        raise SystemExit("⛔⛔ REFUSING: reached %d conversation rows, not the "
                         "%d both prior arms used. An unmatched size puts the "
                         "render delta back on the table as a size effect."
                         % (total, args.rows))
    achieved = got["steered"] / total
    print("chosen %d conversations · %d rows (%d steered + %d unsteered)"
          % (len(chosen), total, got["steered"], got["unsteered"]))
    print("dose   %.3f achieved against %.3f asked" % (achieved, args.dose))
    if abs(achieved - args.dose) > TOLERANCE:
        raise SystemExit("⛔⛔ REFUSING: dose %.3f is more than %.2f from the "
                         "%.3f asked for. The arm's whole content is the dose; "
                         "shipping a different one under this name would put a "
                         "number on the record that no run produced."
                         % (achieved, TOLERANCE, args.dose))

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        for c in chosen:
            # ⛔ RESTAMP. Pooling this into research must refuse on the recipe,
            # and neither parent stamp describes a blend.
            c = dict(c, recipe="puzzle_dosed", dose_seed=used,
                     dose_asked=args.dose, dose_achieved=round(achieved, 4),
                     forced_root_carry=bool(c.get("forced_root_carry")),
                     dose_pool=("steered" if c.get("forced_root_carry")
                                else "unsteered"))
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    tmp.replace(out)
    print("wrote %s (%d conversations)" % (out, len(chosen)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
