#!/usr/bin/env python
"""IDF-2 §7's per-root readout: does the model let go of what it was told to?

`PREREG_IDF2_2026_09_26.md` (LOCK `37363296`) §7 defines it exactly:

    P(root of t−1 reappears in t | marked) vs P(… | unmarked), with a CI,
    computed from the M read transcripts (no extra generation). This is the
    direct measure of whether the model uses the marker.

It is a conjunct in §6's **USES-MARKER-PARTIAL** and **FLOORS** cells — the two
branches a null result lands in.

⛔⛔ THIS TOOL HAD NO INPUT UNTIL `--save-transcripts` EXISTED. The lag read
returned aggregates and threw the generated surfaces away, so the readout could
not be computed from a completed run at all. Runs 1 and 2 died before the read
phase, which is the only reason it was never discovered at the end of a full
run. See `act2_model_lag._serialise_chains`.

⛔ §7 SAYS "all three cells of §6" AND §6 SAYS OTHERWISE. INSTALLS lists four
conjuncts and this is not among them; PARTIAL and FLOORS both name it. Two of
three. The discrepancy is inside a locked body and is recorded, not resolved,
here.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# ⛔⛤ THIS TOOL IS THE ONE THAT RUNS ON THE LAPTOP. Every other analysis in the
# campaign runs on the box, where stdout is UTF-8; this one needs no GPU and
# reads a JSON file, so it will be run on Windows — where `sys.stdout.encoding`
# is cp1252 and the first `⛔` in its own output raises UnicodeEncodeError.
# Measured, not assumed: `python -c "print('⛔')"` tracebacks in this shell.
# ⭐ A refusal message that cannot be PRINTED is a refusal nobody receives, and
# the message this raises when transcripts are missing is the whole point of it.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                          # noqa: BLE001
        pass                    # a stream that cannot be reconfigured is fine

# ⛔ THE INSTRUMENT, IMPORTED. `roots_of` and `held` are the same objects the
# corpus builder and the lag reader call — §1 requires one definition and
# `tests/test_idf2_instruments.py` asserts identity, not agreement.
from tlon.discourse.transient import (MARKER_NONE,                  # noqa: E402
                                      MARKER_PREFIX, held, roots_of)
from tlon.discourse.transient import _lex_roots                     # noqa: E402

#: ⛔⛔ THE UNIT THE EXPERIMENT RE-ROLLS IS THE **CHAIN**, NOT THE ROOT.
#: A chain is one seeded conversation; every root observation inside it shares
#: that seed, that topic and that run of the sampler. A binomial CI over ~800
#: root observations would be roughly sqrt(k) too narrow for k roots per chain
#: — and it would be too narrow in the direction that FIRES `PARTIAL`, whose
#: condition is "CI excludes 0". So the CI is a CLUSTER BOOTSTRAP over chains.
#: `feedback_find_the_real_unit_of_independence`: size on what is re-rolled.
BOOTSTRAP = 10_000
CI = 0.95

#: ⛔⛔ THIS INTERVAL IS MEASURED LIBERAL, AND THE NUMBER TRAVELS WITH IT.
#: A plain percentile cluster bootstrap fires on a TRUE NULL far more often
#: than its label claims. Simulated here (independent `reappears`, no marker
#: effect whatsoever, 300 trials per cell):
#:
#:     chains=12   percentile 9.0%   t-corrected 6.3%
#:     chains=24   percentile 8.7%   t-corrected 7.3%
#:     chains=48   percentile 7.3%   t-corrected 7.0%     ← the pipeline's n
#:
#: ⭐ So `--chains 48` (the pipeline's `RCHAINS`) buys a ~7% false-positive
#: rate, not 5%. `USES-MARKER-PARTIAL` fires on "CI excludes 0", so a liberal
#: interval manufactures exactly the cell it is a conjunct of. The correction
#: below is applied because it is never worse and is much better at small n —
#: but it does NOT reach nominal, and saying "95% CI" without this note would
#: be `feedback_the_numbers_resolution_must_match_the_decisions`.
#: `tests/test_idf2_per_root.py` pins the rate so it cannot silently degrade.
MEASURED_FALSE_POSITIVE = {12: 0.063, 24: 0.073, 48: 0.070}


class NoTranscripts(Exception):
    """Raised when a lag file carries no transcripts — which is not a zero."""


def marked_from_line(line, lex_r) -> frozenset | None:
    """The root set the marker NAMED, recovered from the line it was shown as.

    -> a frozenset, or **None** when no marker was shown at all.

    ⛔⛔ None AND frozenset() ARE DIFFERENT AND THE DIFFERENCE IS THE ARM.
    `None` is the C1/`none` arm: the model saw no annotation, so no root was
    marked and the marked/unmarked contrast does not exist for that turn.
    `frozenset()` is `let go: (none)` — a real stimulus the model sees on turns
    1 and 2 of every chain, which says "nothing is barred". Collapsing them
    would silently fold every unmarked arm's turns into the marked arm at a
    rate of zero. `feedback_a_failed_fetch_must_record_missing_never_zero`.
    """
    if line is None:
        return None
    body = line[len(MARKER_PREFIX):].strip() if line.startswith(MARKER_PREFIX) \
        else line.strip()
    if body == MARKER_NONE or not body:
        return frozenset()
    return frozenset(t for t in body.split() if t in lex_r)


def _surfaces(chain) -> list:
    """The chain's surfaces, refusals kept as None so indices stay true."""
    return [t.get("surface") for t in chain]


def observations(chain, lex_r, *, recompute_held: bool = False) -> list:
    """Per-root outcomes for one chain. -> [{turn, root, marked, reappears}]

    For each transition `t−1 → t`: every root of `t−1` is one observation,
    labelled by whether the marker named it, and scored on whether it shows up
    again in `t`.

    ⛔ A REFUSED TURN ENDS THE CHAIN AND IS NOT AN OBSERVATION. `model_chain`
    appends a refusal with `surface=None` and breaks; scoring "did the root
    reappear" against a turn that was never produced would read every refusal
    as a successful letting-go, which is the flattering direction.

    ⭐ `recompute_held=True` derives the bar from the surfaces instead of the
    shown line. That is how the **unmarked** arm gets a baseline: C1 never saw
    a marker, but `held` is a pure function of two surfaces, so the same
    partition can be drawn over its transcripts and the intrinsic stickiness of
    held roots measured where no marker could have caused it.
    """
    obs = []
    for i in range(1, len(chain)):
        prev_s, cur_s = chain[i - 1].get("surface"), chain[i].get("surface")
        if prev_s is None or cur_s is None or chain[i].get("refused"):
            break
        prev_roots = roots_of(prev_s, lex_r)
        if not prev_roots:
            continue
        if recompute_held:
            # ⛔ SPELT EXACTLY AS `act2_idf2.marker_held` SPELLS IT —
            # `held(out, out[-1], lex_r)` over the chain so far — so the
            # baseline partition cannot drift from the one the M arm was
            # actually shown. `held` owns the short-chain guard; repeating it
            # here would be a second spelling of one rule.
            out = [_Dot(s) for s in _surfaces(chain)[:i]]
            marked = held(out, out[-1], lex_r)
        else:
            marked = marked_from_line(chain[i].get("marker"), lex_r)
            if marked is None:
                continue          # ⛔ MISSING, not an unmarked observation
        cur_roots = roots_of(cur_s, lex_r)
        for r in sorted(prev_roots):
            obs.append({"turn": i, "root": r,
                        "marked": r in marked,
                        "reappears": r in cur_roots})
    return obs


class _Dot:
    """`held` and `roots_of` read `.surface`; the transcripts are dicts."""
    __slots__ = ("surface",)

    def __init__(self, surface):
        self.surface = surface


def rates(per_chain) -> dict:
    """Pooled rates and the marked−unmarked difference. -> dict or MISSING.

    ⛔ AN ARM WITH NO OBSERVATIONS IN A CELL IS `None`, NEVER 0.0. A rate of
    zero says "the model always let go"; absence says "this read cannot speak".
    """
    flat = [o for c in per_chain for o in c]
    m = [o["reappears"] for o in flat if o["marked"]]
    u = [o["reappears"] for o in flat if not o["marked"]]
    p_m = (sum(m) / len(m)) if m else None
    p_u = (sum(u) / len(u)) if u else None
    return {"p_marked": p_m, "n_marked": len(m),
            "p_unmarked": p_u, "n_unmarked": len(u),
            "difference": (None if p_m is None or p_u is None else p_m - p_u)}


def bootstrap_ci(per_chain, *, draws: int = BOOTSTRAP, level: float = CI,
                 seed: int = 20624) -> dict:
    """Cluster bootstrap over CHAINS on the marked−unmarked difference.

    ⛔ RESAMPLES CHAINS, NOT ROOTS. See `BOOTSTRAP` above: the root is not the
    unit the experiment re-rolls, and a root-level interval is narrow in the
    direction that fires a cell.

    ⭐ A resample in which either cell is empty yields no difference and is
    DROPPED, with the count reported. Silently treating it as 0.0 would pull
    the interval toward the null and make the readout look better-behaved than
    the data supports.
    """
    if not per_chain:
        raise NoTranscripts("no chains to bootstrap")
    rng = random.Random(seed)
    n, diffs, degenerate = len(per_chain), [], 0
    for _ in range(draws):
        pick = [per_chain[rng.randrange(n)] for _ in range(n)]
        d = rates(pick)["difference"]
        if d is None:
            degenerate += 1
            continue
        diffs.append(d)
    if not diffs:
        raise NoTranscripts("every bootstrap resample was degenerate")
    point = rates(per_chain)["difference"]
    if point is None:
        raise NoTranscripts("the observed read has an empty cell")
    # ⭐ t-CORRECTED, NOT PERCENTILE. Measured: at 12 chains the percentile
    # interval fires on a true null 9.0% of the time and this one 6.3%. The
    # widening factor is a Cornish-Fisher expansion of the t quantile, so it
    # vanishes as the cluster count grows and cannot make a large-n read wider
    # than it should be.
    se = statistics.stdev(diffs) if len(diffs) > 1 else 0.0
    z = statistics.NormalDist().inv_cdf((1 + level) / 2)
    df = max(1, len(per_chain) - 1)
    t = z * (1 + (z * z + 1) / (4 * df))
    lo, hi = point - t * se, point + t * se
    n_ch = len(per_chain)
    nearest = min(MEASURED_FALSE_POSITIVE, key=lambda k: abs(k - n_ch))
    return {"lo": lo, "hi": hi, "point": point, "se": se,
            "draws": len(diffs), "degenerate_draws": degenerate,
            "level": level, "chains": n_ch,
            # ⛔ THE LABEL IS NOT THE BEHAVIOUR. See MEASURED_FALSE_POSITIVE.
            "measured_false_positive_at_nearest_n": MEASURED_FALSE_POSITIVE[nearest],
            "measured_at_chains": nearest,
            "excludes_zero": not (lo <= 0.0 <= hi)}


def read_one(path: pathlib.Path, *, recompute_held: bool = False) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data.get("transcripts_saved") or "transcripts" not in data:
        raise NoTranscripts(
            "⛔⛔ %s carries no transcripts. The read was taken without "
            "--save-transcripts, so §7's per-root readout cannot be computed "
            "from it — and it cannot be recovered later, because the surfaces "
            "existed only in that process. Re-read the adapter with "
            "--save-transcripts." % path.name)
    lex_r = _lex_roots()
    chains = data["transcripts"]
    per_chain = [observations(c, lex_r, recompute_held=recompute_held)
                 for c in chains]
    per_chain = [c for c in per_chain if c]
    out = {"file": path.name,
           "marker_fn": data.get("marker_fn"), "window2": data.get("window2"),
           "adapter": data.get("adapter"), "seed": data.get("seed"),
           "chains_with_observations": len(per_chain),
           "held_recomputed_from_surfaces": recompute_held}
    out.update(rates(per_chain))
    if out["difference"] is None:
        out["ci"] = None
        out["readout"] = "MISSING — one cell is empty; this read cannot speak"
        return out
    out["ci"] = bootstrap_ci(per_chain)
    out["readout"] = ("CI EXCLUDES 0" if out["ci"]["excludes_zero"]
                      else "CI INCLUDES 0")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--marked", required=True,
                    help="the M read's lag json (taken with --save-transcripts)")
    ap.add_argument("--baseline", default=None,
                    help="⭐ NOT §7's quantity. A C1 read, whose `held` is "
                         "recomputed from its surfaces, to measure how much of "
                         "the marked−unmarked gap is intrinsic stickiness "
                         "rather than the marker. See the note this prints.")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    report = {"PREREG": "docs/PREREG_IDF2_2026_09_26.md", "LOCK": "37363296",
              "quantity": "§7 per-root readout — P(reappears|marked) − "
                          "P(reappears|unmarked)",
              "ci_method": "cluster bootstrap over chains, %d draws, %.0f%%"
                           % (BOOTSTRAP, CI * 100)}
    primary = read_one(pathlib.Path(a.marked))
    report["primary"] = primary

    print("\n  IDF-2 §7 PER-ROOT READOUT — %s" % primary["file"])
    print("    marker_fn %s · %d chains with observations"
          % (primary["marker_fn"], primary["chains_with_observations"]))
    for k in ("marked", "unmarked"):
        p, n = primary["p_%s" % k], primary["n_%s" % k]
        print("    P(reappears | %-8s) %s   n=%d"
              % (k, "MISSING" if p is None else "%.4f" % p, n))
    if primary["ci"] is None:
        print("    ⛔ %s" % primary["readout"])
    else:
        ci = primary["ci"]
        print("    difference %+.4f   %.0f%% CI [%+.4f, %+.4f]   ⇒ %s"
              % (primary["difference"], ci["level"] * 100, ci["lo"], ci["hi"],
                 primary["readout"]))
        print("    ⛔ THE LABEL IS NOT THE BEHAVIOUR: this interval was "
              "SIMULATED at %.1f%% false-positive\n       on a true null with "
              "%d chains, not %.0f%%. Cluster bootstraps are liberal at these "
              "counts.\n       PARTIAL fires on 'excludes 0' — so read that "
              "conjunct against this number."
              % (ci["measured_false_positive_at_nearest_n"] * 100,
                 ci["measured_at_chains"], (1 - ci["level"]) * 100))
        if ci["degenerate_draws"]:
            print("    ⚠️ %d of %d resamples had an empty cell and were dropped"
                  % (ci["degenerate_draws"],
                     ci["draws"] + ci["degenerate_draws"]))

    if a.baseline:
        base = read_one(pathlib.Path(a.baseline), recompute_held=True)
        report["baseline_not_prereg"] = base
        print("\n  ⭐ BASELINE — NOT §7's QUANTITY, AND NOT A §6 CONJUNCT")
        print("    ⛔ `held` roots are roots that ALREADY persisted across two "
              "turns, so they are\n       selected for stickiness. A positive "
              "difference in the MARKED arm is therefore\n       not by itself "
              "evidence of the marker: the same partition drawn over an arm "
              "that\n       never saw a marker measures how much of it is "
              "intrinsic.")
        print("    %s · held recomputed from surfaces" % base["file"])
        if base["difference"] is None:
            print("    ⛔ %s" % base["readout"])
        else:
            bc = base["ci"]
            print("    difference %+.4f   CI [%+.4f, %+.4f]   ⇒ %s"
                  % (base["difference"], bc["lo"], bc["hi"], base["readout"]))
            if primary["difference"] is not None:
                dd = primary["difference"] - base["difference"]
                report["difference_in_differences_not_prereg"] = dd
                print("    difference-in-differences %+.4f" % dd)
                print("    ⛔ NO CI ON THIS, AND NO VERDICT FROM IT. It is two "
                      "independent reads\n       differenced; its interval is "
                      "not the bootstrap of either. Reported so the\n       "
                      "confound is visible, not so a cell can be called on it.")

    print("\n  ⛔ §6 CONJUNCTS, NOT A VERDICT. PARTIAL needs this CI to EXCLUDE "
          "0; FLOORS needs\n     it to INCLUDE 0. Each is one conjunct of "
          "several, and no cell is declared here.")

    if a.out:
        p = pathlib.Path(a.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("  wrote %s" % p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
