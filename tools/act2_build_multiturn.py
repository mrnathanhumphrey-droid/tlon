"""BUILD THE MULTI-TURN CORPUS — Markov depth-1, force-connected, content-free.

⛔⛔ THIS TOOL DOES NOT COUNT TOKENS. `act2_token_budget.py` already imports the
trainer's own `row_to_text`, so a second counter here would re-spell the fold it
is supposed to measure — the self-confirming-counter shape this project has
shipped twice. **Run the existing counter against the mixed corpus.** The exact
command is printed at the end of this tool's output.

⭐ WHAT IT DOES: generate the chains, refuse a starved corpus BEFORE writing,
serialise into the SAME row schema the single-turn corpus uses (so one trainer
and one counter serve both), mix at `MULTITURN_FRACTION`, and emit a manifest of
what the corpus does and does not contain.

⛔ THE ROWS ARE `direction="provoke"`, which is the direction the ARENA SERVES
UNDER — one string, `tlon/discourse/provocation.py`, imported by both. Before
this existed the trainer knew `write`/`read` and the arena spoke under a prompt
that had never been a training direction.
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

from act2_finetune import row_to_text                          # noqa: E402
from tlon.act2 import corpus as C1                             # noqa: E402
from tlon.act2 import schema_bridge as SB                      # noqa: E402
from tlon.discourse import force_map as FM                     # noqa: E402
from tlon.discourse import multiturn as MT                     # noqa: E402
from tlon.discourse import provocation as PV                   # noqa: E402
from tlon.discourse import transient as TR                     # noqa: E402
from tlon.grammar import classes as C                          # noqa: E402
from tlon.grammar.parse import parse, render                   # noqa: E402


def rows_from(chains) -> list[dict]:
    """One training row per TRANSITION. The first turn of each chain seeds and
    is not itself a target — a painting with no provocation is a cold start."""
    out = []
    for ch in chains:
        for prev, cur in zip(ch, ch[1:]):
            scene = parse(cur.surface)
            assert render(scene) == cur.surface     # the one-place oracle
            out.append({
                "direction": PV.DIRECTION,
                "prompt": prev.surface,
                "english": prev.surface,   # never used; `prompt` wins in the fold
                "surface": cur.surface,
                "scene": SB.scene_to_proposal(scene),
                "prior_force": prev.force,
                "force": cur.force,
                "source": "multiturn"})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chains", type=int, default=1200)
    ap.add_argument("--turns", type=int, default=12)
    ap.add_argument("--pool-n", type=int, default=6000,
                    help="single-turn pairs to draw paintings from")
    ap.add_argument("--multiturn-fraction", type=float, required=True,
                    help="multi-turn share BY COMPUTE (not by rows). REQUIRED, no "
                         "default — a mix fraction with a default is a held "
                         "variable nobody wrote down. Rows are solved for.")
    ap.add_argument("--seed", type=int, default=20620)
    ap.add_argument("--out", default="runs/act2/corpus_mt")
    ap.add_argument("--eval-frac", type=float, default=0.02)
    ap.add_argument("--map", default="derived",
                    choices=("derived", "stipulated"),
                    help="derived = DERIVED_v1 (the real map). stipulated = "
                         "STIPULATED_KI_TARGET_v1, the MECHANISM PROBE ONLY.")
    ap.add_argument("--allow-stipulated", action="store_true",
                    help="⛔ REQUIRED to build a stipulated corpus. An explicit "
                         "second key, so a probe corpus cannot be produced by a "
                         "typo in --map.")
    # ⛔⛔ THE FACTORIAL'S CORPUS AXIS. REQUIRED, NO DEFAULT — this is the
    # variable the whole two-arm design turns on, and a default would make every
    # historical build's recipe a matter of inference rather than record.
    ap.add_argument("--recipe", required=True,
                    choices=TR.ALL_RECIPES,
                    help="content-free = the CONTROL arm (response independent "
                         "of its provocation). content-transient = the FIX "
                         "(response provoked by its provocation; that content "
                         "dies at the end of the turn). content-persistent = "
                         "the DOSE ARM (bars nothing; content walks the chain "
                         "BY CONSTRUCTION). ⛔ A dose arm is a measurement "
                         "probe, never a factorial cell.")
    # ⛔⛔ THE DOSE, AND IT IS CHECKED AGAINST THE RECIPE IN BOTH DIRECTIONS.
    # A negative window bars nothing and therefore PERSISTS; a non-negative one
    # suppresses. Letting the two disagree would put a persisting corpus in the
    # treatment arm under a label that was merely typed correctly.
    ap.add_argument("--suppression-window", type=int, default=0,
                    help="release-suppression dose (prereg 765b6787). 0 = bar "
                         "the one root the previous turn echoed (the gate "
                         "recipe, and the default). k>=1 also bars every root "
                         "of the speaker's own preceding k turns. -1 bars "
                         "nothing and is ONLY valid with "
                         "--recipe content-persistent.")
    ap.add_argument("--responsiveness", type=float,
                    default=TR.RESPONSIVENESS_LEDGERED,
                    help="content-transient only: how often a response must "
                         "echo its provocation. Ledgered at 1.0.")
    a = ap.parse_args()

    if not 0.0 < a.multiturn_fraction < 1.0:
        raise SystemExit("⛔ --multiturn-fraction must be strictly between 0 and "
                         "1. Mix, don't replace: single-turn is what produced "
                         "render 82.0 / speak 97.3.")

    # ⛔⛔ TWO KEYS TO BUILD A STIPULATED CORPUS. `--map stipulated` alone is one
    # character away from `derived` on a command line, and the artifact it
    # produces is a corpus that LOOKS like every other corpus on disk. The
    # stipulation must be impossible to reach by accident and impossible to
    # mistake once reached.
    fmap = FM.DERIVED_v1 if a.map == "derived" else FM.STIPULATED_KI_TARGET_v1
    if fmap.is_stipulated and not a.allow_stipulated:
        raise SystemExit(
            f"⛔⛔ {fmap.label} carries STIPULATED cell(s) "
            f"{sorted(fmap.stipulated)}. Pass --allow-stipulated to confirm this "
            "is the mechanism probe. A stipulated cell is NOT derived, NOT a map "
            "proposal, and is discarded after the probe REGARDLESS OF OUTCOME.")
    if not fmap.is_stipulated:
        fmap.assert_derived("a non-probe corpus")

    print(f"MULTI-TURN CORPUS · Markov depth-1 · RECIPE={a.recipe} · "
          f"MULTITURN_FRACTION={a.multiturn_fraction}")
    if a.recipe == TR.CONTENT_TRANSIENT:
        print("  ⭐ CONTENT-TRANSIENT: the response is provoked BY its "
              "provocation's content,\n     and that content dies at the end of "
              "the turn. Perceive, respond, release.")
    else:
        print("  ⭐ CONTENT-FREE (CONTROL ARM): the response is independent of "
              "its provocation.")
    print(fmap.describe())
    print(f"\n  separation (max reachable fidelity band): "
          f"{fmap.separation():.4f}")
    if fmap.is_stipulated:
        print("  ⚠️  PRIMARY MEASURE EXCLUDES THE STIPULATED ROW. "
              f"common uniform rows = {list(FM.COMMON_UNIFORM_ROWS)}")

    # ⛔⛔ RECIPE AND DOSE MUST AGREE, CHECKED BOTH WAYS. Neither is inferable
    # from the other at read time, so a mismatch here would produce an artifact
    # whose label and whose content describe different experiments.
    if (a.suppression_window < 0) != (a.recipe == TR.CONTENT_PERSISTENT):
        raise SystemExit(
            "⛔⛔ RECIPE/DOSE MISMATCH: --recipe %s with --suppression-window %d. "
            "A negative window bars nothing and PERSISTS by construction, so it "
            "is valid only with --recipe %s; every non-negative window "
            "suppresses and is never %s."
            % (a.recipe, a.suppression_window, TR.CONTENT_PERSISTENT,
               TR.CONTENT_PERSISTENT))

    pool_pairs = C1.build(a.pool_n, seed=a.seed)
    # ⛔⛔ ONE KNOB. Both arms run the SAME force map, the SAME seed and the SAME
    # pool; the only thing `--recipe` changes is whether the painting is drawn
    # near its provocation or from the whole space. `build_transient` splits the
    # RNG so the FORCE sequence is byte-identical across recipes at a given seed
    # -- without that split, content-free-seed-X and content-transient-seed-X
    # would differ in two variables and no contrast between them would be
    # attributable to content.
    #
    # ⛔⛔ BOTH ARMS GO THROUGH ONE GENERATOR, AND THE CONTROL IS `responsiveness=0`.
    # Routing content-free through `MT.build` instead LOOKS equivalent — the draw
    # is uniform either way — but `MT.build` takes force AND content from a SINGLE
    # RNG stream, so its force sequence is perturbed by its content draws and the
    # two arms at one seed no longer share a force sequence. Measured: the
    # force-transition multisets did NOT match. Distributionally the same, as a
    # PAIRED design not the same, and the pairing is the reason for matched seeds.
    #
    # ⚠️ CONSEQUENCE, RECORDED RATHER THAN PAPERED OVER: every adapter built
    # before this change (s20621-23, t30001-3, and the s20624-29 batch now
    # cooking) used the legacy single-stream path. Those pair with a
    # content-transient build BY SEED but NOT by force sequence — an unbiased
    # contrast (same map, same stationary distribution) that is unpaired, so it
    # carries more variance. New builds on both arms are exactly paired.
    chains = TR.build_transient(
        a.chains, turns=a.turns, pairs=pool_pairs, seed=a.seed,
        responsiveness=(0.0 if a.recipe == TR.CONTENT_FREE
                        else a.responsiveness),
        suppression_window=a.suppression_window,
        fmap=fmap, verify=False)
    # refuses BEFORE writing
    fair = MT.check_force_pair_fairness(chains, fmap=fmap)

    # ⛔⛔ THE RECIPE LABEL IS A MEASURED CLAIM, NOT A FLAG THAT WAS TYPED. Both
    # arms are verified on the same instrument, and a mislabelled corpus is
    # refused here rather than discovered as a shrunken effect months later.
    lex_r = C.load()["classes"]["R"]
    trans = TR.verify_recipe(chains, a.recipe, lex_r=lex_r, seed=a.seed)
    print("\n  ✅ recipe verified as %s" % trans["verdict"])
    print("     lag profile " + "  ".join(
        "lag%d %.4f" % (k, v) for k, v in sorted(trans["lag_profile"].items())))
    print("     z vs permutation null " + "  ".join(
        "lag%d %+.2f" % (k, v) for k, v in sorted(trans["z"].items())))
    print(f"\n  ✅ force-pair fairness: worst live cell {fair['worst_cell']} at "
          f"{fair['worst_ratio']:.3f} of its row share "
          f"(floor {fair['floor']:.4f})")

    mt = rows_from(chains)
    # ⛔ THE MIX IS ON ROWS, AND THE TOKEN CHECK IS WHAT MAKES IT HONEST — a row
    # ratio is not a compute ratio, and only the counter can say which you got.
    # ⛔⛔ THE FRACTION IS BY COMPUTE, AND ROWS ARE SOLVED FOR. Asking the caller
    # for a ROW fraction made rows a proxy for compute, and the proxy rotted by
    # 24 points: 0.50 by rows landed at 0.737 by chars, because the provocation
    # system prompt is 711 chars and rides on EVERY provoke row while write/read
    # carry 79/99. Same shape as the `<700` length check — replace the proxy
    # with the property. Compute is the held variable; rows are the dial.
    #
    # ⚠️ CHARS ARE THEMSELVES A PROXY FOR TOKENS — a tighter one (both sides go
    # through the same fold) but not the thing. `act2_token_budget.py` is the
    # arbiter and it runs before training.
    class _NoTok:
        chat_template = None
    mt_chars = sum(len(row_to_text(r, _NoTok())) for r in mt)
    probe = C1.build(200, seed=a.seed + 1)
    probe_chars = 0
    for q in probe:
        base = {"prompt": q.prompt(), "english": q.english, "surface": q.surface,
                "scene": SB.scene_to_proposal(q.scene),
                "impression": q.impression, "source": q.source}
        for d in ("write", "read"):
            probe_chars += len(row_to_text(dict(base, direction=d), _NoTok()))
    chars_per_pair = probe_chars / len(probe)
    target_single_chars = mt_chars * (1 - a.multiturn_fraction) / a.multiturn_fraction
    n_single = int(round(2 * target_single_chars / chars_per_pair))
    print()
    print("  ⭐ HOLDING COMPUTE, SOLVING FOR ROWS")
    print(f"     multi-turn: {len(mt):,} rows, {mt_chars:,} chars "
          f"({mt_chars / len(mt):.0f}/row)")
    print(f"     single-turn needs {target_single_chars:,.0f} chars at "
          f"{chars_per_pair / 2:.0f}/row → {n_single:,} rows")
    # ⛔⛔ BOTH SINGLE-TURN DIRECTIONS, OR SPEAK CRATERS. `corpus.build` emits
    # `write` ONLY; the read half exists because `act2_build_corpus.py` DUPLICATES
    # each row with `direction="read"`. The first version of this tool did not,
    # and would have shipped a corpus with no read rows at all — measured
    # consequence, from that tool's own comment: **render 81.2 %, speak 9.4 %**.
    # A run that lost speak 97.3 → ~9 would have read as "multi-turn training
    # destroyed speak". So the doubling is mirrored here, and the pair count is
    # HALVED so the mix ratio still lands where it was asked to.
    base = C1.build(max(1, n_single // 2), seed=a.seed + 1)
    single = []
    for p in base:
        row = {"prompt": p.prompt(), "english": p.english, "surface": p.surface,
               "scene": SB.scene_to_proposal(p.scene),
               "impression": p.impression, "source": p.source}
        single.append(dict(row, direction="write"))
        single.append(dict(row, direction="read"))

    rows = mt + single
    # ⛔⛔ REFUSE BEFORE WRITING. The first version of this tool produced a
    # corpus with ZERO read rows and nothing complained until speak would have
    # read 9.4 %. This is that catch, moved to write time.
    dirs = MT.check_direction_coverage(rows)
    print("  ✅ direction coverage: "
          + ", ".join(f"{d} {n:,} ({dirs['shares'][d]:.1%})"
                      for d, n in sorted(dirs["counts"].items())))

    rng = random.Random(a.seed)
    rng.shuffle(rows)
    cut = max(1, int(len(rows) * a.eval_frac))
    ev, train = rows[:cut], rows[cut:]

    out_dir = pathlib.Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, part in (("train", train), ("eval", ev)):
        path = out_dir / f"{name}.jsonl"
        with path.open("w", encoding="utf-8", newline="") as fh:
            for r in part:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"  wrote {len(part):,} → {path}")

    counts = MT.transition_counts(chains)
    manifest = {
        # ⛔⛔ THE RECIPE IS THE FIRST FIELD, ABOVE EVEN THE MAP. It is the
        # factorial's corpus axis, and an adapter whose recipe is ambiguous is an
        # adapter that belongs to no cell — it cannot be paired with its matched
        # seed in the other arm, and it silently degrades the matrix into a pile.
        "recipe": a.recipe,
        "recipe_responsiveness": (None if a.recipe == TR.CONTENT_FREE
                                  else a.responsiveness),
        # ⭐ THE DOSE IS IN THE MANIFEST, so an adapter can say which treatment
        # it received. Two content-transient corpora at different windows are
        # different treatments, and one that cannot say its dose will be pooled
        # with the other by an analysis that simply did not know to ask.
        "recipe_suppression_window": a.suppression_window,
        "recipe_VERIFIED": trans["verdict"],
        "recipe_lag_profile": trans["lag_profile"],
        "recipe_z_vs_permutation_null": trans["z"],
        "recipe_null": trans["null"],
        # ⭐ The matched-seed rule, recorded IN the artifact so the pairing is a
        # property of the corpus rather than of somebody's notes.
        "factorial_pair_key": f"seed{a.seed}",
        # ⛔⛔ THE GENERATOR'S IDENTITY, AND IT DECIDES A VARIANCE REGIME. The
        # legacy path coupled force to content in one RNG stream, so its force
        # sequence cannot match a partner's; the split-stream path holds force
        # identical across recipes at a seed. A manifest with NO such field is
        # therefore LEGACY — `factorial.generator_of` defaults that way on
        # purpose, because defaulting an unlabelled corpus to the split-stream
        # id would file the adapters whose pairing is UNKNOWN as the ones whose
        # pairing is BEST.
        "generator": TR.GENERATOR_SPLIT_STREAM,
        "pairing_capability_side": TR.PAIRED_SEED_AND_FORCE,
        "pairing_NOTE": (
            "A PAIR is `seed+force` only if BOTH arms came off the split-stream "
            "generator. One legacy side makes the whole pair `seed`-only: "
            "unbiased (same map, same stationary distribution) but UNPAIRED, "
            "so higher variance. s20621-23, t30001-3 and s20624-29 are legacy."),
        # ⛔⛔ THE MAP'S IDENTITY IS THE FIRST FIELD IN THE MANIFEST, AND THE
        # STIPULATION IS A BOOLEAN NOT A FOOTNOTE. A corpus that cannot say
        # which map made it is a corpus nobody can attribute a result to.
        "map_label": fmap.label,
        "map_is_STIPULATED": fmap.is_stipulated,
        "map_stipulated_cells": {s: fmap.forced_cells[s]
                                 for s in sorted(fmap.stipulated)},
        "map_forced_cells": dict(fmap.forced_cells),
        "map_stationary": fmap.stationary(),
        "PRIMARY_MEASURE_ROWS_common_uniform": list(FM.COMMON_UNIFORM_ROWS),
        "PRIMARY_MEASURE_EXPECTATION": FM.COMMON_UNIFORM_EXPECTATION,
        "multiturn_fraction_requested_BY_COMPUTE": a.multiturn_fraction,
        "multiturn_fraction_by_rows_DERIVED": len(mt) / len(rows),
        "held_variable": "compute (char/token share); rows are the dial",
        "n_multiturn_rows": len(mt), "n_singleturn_rows": len(single),
        "singleturn_directions": sorted({r["direction"] for r in single}),
        "chains": a.chains, "turns": a.turns, "seed": a.seed,
        "direction": PV.DIRECTION,
        "provocation_sha": __import__("hashlib").sha256(
            PV.PROVOCATION.encode()).hexdigest()[:16],
        
        "uniform_rows": list(fmap.uniform_rows()),
        "separation": fmap.separation(),
        "design_zeros": [f"{p}->{r}" for p in FM.ORDER for r in FM.ORDER
                         if fmap.row(p)[r] == 0.0],
        "force_pair_counts": {f"{a_}->{b_}": n for (a_, b_), n in
                              sorted(counts.items())},
        "fairness": {k: v for k, v in fair.items() if k != "counts"},
        # ⛔⛔ RECIPE-DEPENDENT, AND IT HAS TO BE. This list previously asserted
        # "content-adjacency of any kind" was absent — TRUE for content-free and
        # FLATLY FALSE for content-transient, whose whole purpose is within-pair
        # content adjacency. A fixed list here would have shipped a manifest that
        # denied the corpus's defining property, and the caveat would have
        # decayed exactly where it is least recoverable: inside the artifact that
        # outlives everyone's memory of the build.
        "NOT_IN_THIS_CORPUS": (
            ["content-adjacency of any kind (C-D2: association is total)"]
            if a.recipe == TR.CONTENT_FREE else
            ["CROSS-PAIR content adjacency (content dies at the end of its "
             "turn; within-pair adjacency is PRESENT and is this recipe's "
             "defining property — see recipe_lag_profile)",
             "own-chain content persistence (lag 2 is at the permutation null)"]
        ) + [
            "directional evidential adjacency (empirical, the arena's target)",
            "non-forced force-map cells (uniform, not guessed)",
            "the base convention table (§8.1, deferred — base_convention raises)",
        ],
    }
    mp = out_dir / "manifest.json"
    mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                  encoding="utf-8", newline="")
    print(f"  wrote {mp}")
    print(f"\n  rows: {len(mt):,} multi-turn + {len(single):,} single-turn "
          f"= {len(rows):,}  (multi-turn share {len(mt) / len(rows):.3f})")

    print("\n  ⛔⛔ TOKENS ARE NOT COUNTED HERE, ON PURPOSE. A second counter "
          "would re-spell\n     the trainer's fold and verify itself. Run the "
          "one that imports it:\n\n"
          f"     python tools/act2_token_budget.py --model <MODEL> "
          f"--corpus {a.out} \\\n"
          "         --baseline runs/act2/corpus/token_budget.json --tolerance 0.02\n")
    print("  ⚠️  A ROW RATIO IS NOT A COMPUTE RATIO. The multi-turn row is "
          "shorter than a\n     single-turn row (a Tlön surface, not an English "
          "sentence), so the token\n     share will NOT equal "
          f"{a.multiturn_fraction}. The counter is what decides.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
