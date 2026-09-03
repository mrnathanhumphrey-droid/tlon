"""THE MODEL-SIDE LAG PROFILE — the same instrument, pointed at the model.

    python tools/act2_model_lag.py --adapter runs/act2/.../adapter_ct-s20624 \
        --chains 12 --turns 10 --out runs/act2/model_lag/ct-s20624.json

⛔⛔ THE ASSUMPTION THIS EXISTS TO TEST, AND NOTHING DOWNSTREAM IS VALID WITHOUT
IT. The content-transient CORPUS has lag-1 responsiveness: measured +120 sigma.
That is a property of the training data. **Corpus responsiveness is not model
behaviour**, and the content-free arm is the proof: its corpus had no
content-connection and the model faithfully learned to have none. The inverse is
untested. Does a corpus WITH lag-1 responsiveness produce a MODEL that perceives
content in the moment and releases it -- or does the fine-tune wash it out, hold
it too long, or learn something adjacent?

⭐⭐ ONE ADAPTER ANSWERS THIS. TWELVE ASSUME IT. The factorial, the remaining
eleven builds and the whole chatbot deliverable are downstream of this one
number, so it is measured before they are bought.

⛔⛔ THE SAME INSTRUMENT, BOTH SIDES. This module does NOT define a lag statistic.
It imports `lag_profile`, `permutation_null` and `check_transience` from
`tlon.discourse.transient` -- the exact functions the corpus was gated on. A
model-side statistic re-spelt here could differ from the corpus-side one in some
detail nobody wrote down, and then "the model matches the corpus" would be a
claim about two instruments rather than about the model. Same code, both sides,
so they cannot disagree by measurement choice.

⭐ THE CHAIN IS BUILT THE WAY THE CORPUS'S CHAINS ARE: a seed surface, then each
turn provoked by the one before it under the `provoke` direction with a BARE
surface as the user message -- byte-for-byte the shape of `prev.surface` in
every provoke row. Anything else measures a prompt the model never trained on.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# ⛔ THE INSTRUMENT, IMPORTED. Not re-implemented, not re-parameterised.
from tlon.discourse.transient import (Z_LAG1_MIN, Z_LAGN_MAX,      # noqa: E402
                                      check_transience, lag_profile,
                                      permutation_null)
from tlon.discourse.multiturn import MultiturnError                # noqa: E402
from tlon.discourse.provocation import DIRECTION as PROVOKE        # noqa: E402
from tlon.grammar import classes as C                              # noqa: E402
from tlon_converse import TRAINED, generate                        # noqa: E402


class ModelTurn:
    """⭐ Duck-types the corpus `Turn` for the shared instrument: it only ever
    reads `.surface`. Deliberately the same shape so one function serves both."""

    __slots__ = ("surface", "force", "seconds", "refused")

    def __init__(self, surface, force=None, seconds=0.0, refused=False):
        self.surface, self.force = surface, force
        self.seconds, self.refused = seconds, refused


def model_chain(backend, seed_surface: str, *, turns: int) -> list[ModelTurn]:
    """Seed, then let the model paint each next turn from the one before it.

    ⛔ A REFUSED TURN ENDS THE CHAIN, IT IS NOT SKIPPED. Skipping would splice
    turn t-1 to turn t+1 and report an adjacency the model never produced --
    manufacturing lag-1 evidence out of a gap.
    """
    out = [ModelTurn(seed_surface)]
    for _ in range(turns - 1):
        t = generate(backend, PROVOKE, out[-1].surface, [], shape=TRAINED)
        if not t.ok:
            out.append(ModelTurn(None, seconds=t.seconds, refused=True))
            break
        out.append(ModelTurn(t.surface, seconds=t.seconds))
    return out


def usable(chain) -> list[ModelTurn]:
    """The leading run of non-refused turns. ⛔ A chain that refused at turn 3 is
    a 3-turn chain, never a 10-turn chain with a hole."""
    good = []
    for t in chain:
        if t.refused or not t.surface:
            break
        good.append(t)
    return good


def seed_surfaces(n: int, *, rng: random.Random) -> list[str]:
    """Legal seeds drawn from the same corpus builder the training data uses."""
    from tlon.act2 import corpus as C1
    pairs = C1.build(max(200, n * 4), seed=rng.randint(1, 10 ** 6))
    surfaces = [p.surface for p in pairs if getattr(p, "surface", None)]
    rng.shuffle(surfaces)
    return surfaces[:n]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--4bit", dest="four_bit", action="store_true")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--chains", type=int, default=12)
    ap.add_argument("--turns", type=int, default=10)
    ap.add_argument("--max-lag", type=int, default=4)
    ap.add_argument("--shuffles", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20620)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    from act2_backends import LocalBackend
    print("  loading %s + %s ..." % (a.model, a.adapter))
    t0 = time.perf_counter()
    backend = LocalBackend(a.model, adapter=a.adapter, device=a.device,
                           load_4bit=a.four_bit,
                           max_new_tokens=a.max_new_tokens,
                           temperature=a.temperature)
    print("  ready in %.1fs" % (time.perf_counter() - t0))

    rng = random.Random(a.seed)
    seeds = seed_surfaces(a.chains, rng=rng)
    chains, dropped = [], 0
    for i, s in enumerate(seeds, 1):
        raw = model_chain(backend, s, turns=a.turns)
        good = usable(raw)
        if len(good) < 3:
            # ⛔ A chain too short to HAVE a lag-2 cannot contribute to the
            # measurement, and counting it would silently reweight the profile
            # toward chains that refused early.
            dropped += 1
            print("  chain %2d: only %d usable turn(s) — dropped" % (i, len(good)))
            continue
        chains.append(good)
        print("  chain %2d: %d turns  %s" % (i, len(good), good[1].surface))

    if not chains:
        raise SystemExit("⛔⛔ every chain refused before turn 3. The model "
                         "cannot sustain a provoke chain, which is itself the "
                         "answer — but it is not a lag profile.")

    lex_r = C.load()["classes"]["R"]
    prof = lag_profile(chains, max_lag=a.max_lag, lex_r=lex_r)
    nrng = random.Random(a.seed)
    zs, nulls = {}, {}
    for k in range(1, a.max_lag + 1):
        mu, sd = permutation_null(chains, lag=k, shuffles=a.shuffles,
                                  rng=nrng, lex_r=lex_r)
        nulls[k] = {"mean": mu, "sd": sd}
        zs[k] = (prof[k] - mu) / sd if sd else float("nan")

    # ⭐ THE GATE ITSELF, RUN BY THE CORPUS-SIDE FUNCTION. Not a re-implementation
    # of its logic with model-shaped variable names.
    try:
        check_transience(chains, lex_r=lex_r, max_lag=a.max_lag,
                         shuffles=a.shuffles, seed=a.seed)
        verdict, why = "content-transient", ""
    except MultiturnError as exc:
        verdict, why = "REFUSED", str(exc)

    n_turns = sum(len(c) for c in chains)
    report = {
        "adapter": a.adapter, "four_bit": a.four_bit,
        "temperature": a.temperature, "max_new_tokens": a.max_new_tokens,
        "chains_requested": a.chains, "chains_used": len(chains),
        "chains_dropped_too_short": dropped, "turns_total": n_turns,
        "turns_requested_per_chain": a.turns,
        "lag_profile": prof, "z": zs, "null": nulls,
        "verdict": verdict, "refusal_reason": why,
        "thresholds": {"z_lag1_min": Z_LAG1_MIN, "z_lagn_max": Z_LAGN_MAX},
        "INSTRUMENT": "tlon.discourse.transient — the same functions the corpus "
                      "was gated on, imported not re-spelt",
    }
    outp = pathlib.Path(a.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n  MODEL LAG PROFILE — %s" % a.adapter)
    print("    " + "  ".join("lag%d %.4f" % (k, prof[k])
                             for k in sorted(prof)))
    print("    " + "  ".join("lag%d z=%+.2f" % (k, zs[k]) for k in sorted(zs)))
    print("    chains %d used / %d dropped · %d turns"
          % (len(chains), dropped, n_turns))
    print("    VERDICT: %s" % verdict)
    if why:
        print("    %s" % why)
    print("\n  wrote %s" % outp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
