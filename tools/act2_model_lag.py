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
                                      UnscoreableLag, check_transience,
                                      lag_pairs, lag_profile,
                                      permutation_null, resolving_power,
                                      threshold_for_lag)
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


#: ⛔ Chains shorter than this cannot HAVE a lag-2 and are dropped, never
#: counted. Named so the curve and the CLI cannot disagree about it.
MIN_USABLE_TURNS = 3

#: ⛔⛔ THE DECODER IS PART OF THE MEASUREMENT, NOT A SETTING AROUND IT.
#: 2026-09-16, `epochlevB-s20624`: every in-training lag read in this campaign
#: was taken at temperature 0.0 / 220 tokens, because the curve hands `read_lag`
#: a backend built by `LocalBackend.adopt()`, whose defaults are **F-LOCAL's**
#: (220, greedy — correct THERE, where the modal answer is what you want). The
#: fold was shared; the instrument the fold ran on was not.
#:
#: A greedy decoder repeats content across turns because the same context yields
#: the same continuation, so it inflates persistence at EVERY lag uniformly.
#: Same weights, same step, two decoders:
#:
#:     in-training (T=0.0)  prof 2.213 1.823 1.595 1.417   lag2 z=23.858
#:     standalone  (T=0.7)  prof 0.915 0.266 0.085 0.014   lag2 z= 4.343
#:
#: The first is not a weak reading of persistence, it is a reading of the
#: decoder. It voided the entire release-vs-dose curve, and it puts the one
#: signal that motivated the epochs lever (miscurve's epoch 2 — also an
#: in-training read) under the same suspicion.
#:
#: ⭐ So the values live HERE, `read_lag` applies them to whatever backend it is
#: handed, and it RECORDS them in its own result. A caller can override, but a
#: caller that says nothing now gets the decoder a lag read requires rather than
#: whatever the backend happened to be carrying.
LAG_TEMPERATURE = 0.7
LAG_MAX_NEW_TOKENS = 256


def read_lag(backend, *, chains: int = 12, turns: int = 10, max_lag: int = 4,
             shuffles: int = 200, seed: int = 20624, verbose: bool = True,
             temperature: float = LAG_TEMPERATURE,
             max_new_tokens: int = LAG_MAX_NEW_TOKENS) -> dict:
    """⭐ THE WHOLE OF WHAT A RELEASE READ IS — ONE FOLD, CLI AND CURVE SHARE IT.

    The twin of `act2_flocal.read_rates`, and extracted for the same reason: a
    mid-run read that re-implements the measurement becomes a SECOND, slightly
    different instrument, and then the checkpoint and the verdict disagree with
    no way to tell which is the object and which is the wiring. That failure has
    already cost this campaign four instances of one wiring class.

    ⛔⛔ EVERY GUARD TRAVELS WITH IT, because they are the measurement, not
    decoration around it:

      * short chains DROPPED, never counted -- a chain that refused at turn 3 is
        a 3-turn chain, and counting it reweights the profile toward the chains
        that failed earliest;
      * the sampling stream SEEDED, and whether that succeeded RECORDED -- an
        unseeded profile is one undocumented draw sitting beside a field called
        `seed`;
      * per-lag scoreability, so one empty cell cannot take the whole read down
        with it, and `z: None` beside `n_pairs` is the unscoreable state;
      * `resolving_power` vs `threshold_for_lag` -- ⛔⛔ THE ONE THAT MATTERS
        MOST AT A CHECKPOINT. A small cell yields a small z NO MATTER WHAT THE
        SPEAKER DID, which at lag 1 fabricates a perceive collapse and at lag >=2
        grants a VACUOUS RELEASE PASS. Early checkpoints are exactly where cells
        are small, so a curve that skipped this would manufacture "release
        installed" out of short chains.

    -> the measurement dict. Provenance (which object, which adapter) is the
    caller's to add: this function knows what it measured, not what it was
    pointed at.
    """
    def say(msg):
        if verbose:
            print(msg)

    # ⛔⛔ GREEDY IS NOT A LOW TEMPERATURE, IT IS A DIFFERENT MEASUREMENT.
    # `do_sample = temperature > 0` in every backend here, so temperature 0
    # makes the speaker deterministic and the profile measures the decoder.
    # This is the only setting the read cannot survive, so it is refused
    # outright rather than recorded and regretted.
    if not temperature or temperature <= 0:
        raise ValueError(
            "⛔⛔ read_lag(temperature=%r) is GREEDY decoding. A lag profile "
            "measures whether CONTENT persists across turns; a deterministic "
            "speaker repeats content because the same context yields the same "
            "continuation, which inflates every lag uniformly and measures the "
            "decoder instead. This exact call voided the release-vs-dose curve "
            "on 2026-09-16. Pass temperature > 0 (the lag read's own default "
            "is %.2f)." % (temperature, LAG_TEMPERATURE))

    # ⭐ THE FOLD OWNS THE INSTRUMENT FOR THE DURATION, AND PUTS IT BACK.
    # The mid-run curve BORROWS a live backend (`LocalBackend.adopt`) that the
    # trainer owns and that F-LOCAL reads through at its own settings, so this
    # must restore exactly what it found — the same discipline `isolated_read`
    # applies to training mode and RNG state, for the same reason.
    prior_t = getattr(backend, "temperature", None)
    prior_n = getattr(backend, "max_new_tokens", None)
    backend.temperature = temperature
    backend.max_new_tokens = max_new_tokens
    try:
        m = _read_lag_inner(backend, chains=chains, turns=turns,
                            max_lag=max_lag, shuffles=shuffles, seed=seed,
                            say=say)
    finally:
        if prior_t is not None:
            backend.temperature = prior_t
        if prior_n is not None:
            backend.max_new_tokens = prior_n

    # ⛔⛔ RECORDED BY THE FOLD, NOT BY THE CALLER. `main()` used to add these as
    # provenance, which meant the CLI's readings carried their decoder and the
    # curve's readings carried nothing — so the rows that were WRONG were also
    # the rows with no evidence of being wrong. Now every lag row from every
    # caller states the decoder it was taken with, and
    # `tests/test_readings_carry_their_config.py` asserts it against what a lag
    # read requires.
    m["temperature"] = temperature
    m["max_new_tokens"] = max_new_tokens
    m["decoder_sampled"] = True
    return m


def _read_lag_inner(backend, *, chains, turns, max_lag, shuffles, seed, say):
    """The body of `read_lag`. Split out only so the decoder that `read_lag`
    installs is guaranteed to be restored on every exit path, including the
    refusals and the early `UNSCOREABLE` return."""
    torch_seeded = False
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        torch_seeded = True
    except Exception as exc:                                   # pragma: no cover
        say("  ⚠️ could NOT seed the sampling stream (%s) — recording that" % exc)

    rng = random.Random(seed)
    built, dropped = [], 0
    for i, s in enumerate(seed_surfaces(chains, rng=rng), 1):
        good = usable(model_chain(backend, s, turns=turns))
        if len(good) < MIN_USABLE_TURNS:
            dropped += 1
            say("  chain %2d: only %d usable turn(s) — dropped" % (i, len(good)))
            continue
        built.append(good)
        say("  chain %2d: %d turns  %s" % (i, len(good), good[1].surface))

    if not built:
        # ⛔ NOT an exception at a checkpoint. A curve that raises here loses
        # every reading taken before it; the CLI can still choose to exit.
        return {"lag_profile": {}, "z": {}, "null": {}, "n_pairs": {},
                "resolving_power": {}, "threshold_by_lag": {},
                "chains_requested": chains, "chains_used": 0,
                "chains_dropped_too_short": dropped, "turns_total": 0,
                "turns_requested_per_chain": turns,
                "seed": seed, "sampling_stream_seeded": torch_seeded,
                "unscoreable_lags": list(range(1, max_lag + 1)),
                "unscoreable_why": {k: "no chain survived to turn %d"
                                    % MIN_USABLE_TURNS
                                    for k in range(1, max_lag + 1)},
                "verdict": "UNSCOREABLE",
                "refusal_reason": (
                    "every chain refused before turn %d. The model cannot "
                    "sustain a provoke chain, which is itself an answer -- but "
                    "it is not a lag profile." % MIN_USABLE_TURNS),
                "thresholds": {"z_lag1_min": Z_LAG1_MIN,
                               "z_lagn_max": Z_LAGN_MAX}}

    lex_r = C.load()["classes"]["R"]
    prof = lag_profile(built, max_lag=max_lag, lex_r=lex_r)
    nrng = random.Random(seed)
    zs, nulls, npairs, unscoreable, powers, needs = {}, {}, {}, {}, {}, {}
    for k in range(1, max_lag + 1):
        npairs[k] = lag_pairs(built, lag=k)
        try:
            mu, sd = permutation_null(built, lag=k, shuffles=shuffles,
                                      rng=nrng, lex_r=lex_r)
        except UnscoreableLag as exc:
            zs[k], nulls[k] = None, None
            unscoreable[k] = str(exc)
            say("  ⛔ lag %d UNSCOREABLE — 0 pairs" % k)
            continue
        power = resolving_power(built, lag=k, lex_r=lex_r, mu=mu, sd=sd)
        need = threshold_for_lag(k)
        powers[k], needs[k] = power, need
        if power < need:
            zs[k], nulls[k] = None, {"mean": mu, "sd": sd}
            unscoreable[k] = (
                "UNRESOLVABLE AT LAG %d: %d pair(s) give the null sd=%.4f, so "
                "the highest z this cell can emit is %.3f -- below the %.1f "
                "threshold it would be judged against. The comparison is "
                "decided by arithmetic before the speaker is consulted: at lag "
                "1 that fabricates a perceive collapse, at lag >=2 it grants a "
                "vacuous release pass. Neither is a measurement."
                % (k, npairs[k], sd, power, need))
            say("  ⛔ lag %d UNRESOLVABLE — z_max %.3f < %.1f (n=%d)"
                % (k, power, need, npairs[k]))
            continue
        nulls[k] = {"mean": mu, "sd": sd}
        zs[k] = (prof[k] - mu) / sd if sd else float("nan")

    if unscoreable:
        verdict = "UNSCOREABLE"
        why = ("the speaker produced no exchange long enough to score at lag(s) "
               "%s: %s" % (sorted(unscoreable),
                           " | ".join(unscoreable[k]
                                      for k in sorted(unscoreable))))
    else:
        try:
            check_transience(built, lex_r=lex_r, max_lag=max_lag,
                             shuffles=shuffles, seed=seed)
            verdict, why = "content-transient", ""
        except MultiturnError as exc:
            verdict, why = "REFUSED", str(exc)

    return {
        "chains_requested": chains, "chains_used": len(built),
        "chains_dropped_too_short": dropped,
        "turns_total": sum(len(c) for c in built),
        "turns_requested_per_chain": turns,
        "lag_profile": prof, "z": zs, "null": nulls, "n_pairs": npairs,
        "resolving_power": powers, "threshold_by_lag": needs,
        "seed": seed, "sampling_stream_seeded": torch_seeded,
        "unscoreable_lags": sorted(unscoreable),
        "unscoreable_why": {k: unscoreable[k] for k in sorted(unscoreable)},
        "verdict": verdict, "refusal_reason": why,
        "thresholds": {"z_lag1_min": Z_LAG1_MIN, "z_lagn_max": Z_LAGN_MAX},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    # ⛔⛔ WAS `required=True`, WHICH MADE THE §3 INSTRUMENT UNABLE TO READ THE
    # OBJECT §5 PRODUCES. A full-weight `_w` model has no adapter; `LocalBackend`
    # has always accepted `adapter=None`, so only this line stood in the way.
    # ⛔ Optional is not the same as absent: with no adapter AND no local model
    # path, this reads the BARE BASE MODEL and would write a result file
    # indistinguishable from a treatment read. That is refused below.
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--object-kind", default=None,
                    choices=["adapter", "full_weight"],
                    help="what --model/--adapter names. Required when no "
                         "--adapter is given, so a `_w` read is never mistaken "
                         "for a base-model read.")
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

    if not a.adapter:
        if a.object_kind != "full_weight":
            raise SystemExit(
                "⛔⛔ no --adapter and --object-kind is %r. With neither, this "
                "reads the BARE BASE MODEL and writes a lag profile that looks "
                "exactly like a treatment result. Pass --object-kind "
                "full_weight with a local --model path for a `_w` object."
                % (a.object_kind,))
        if not pathlib.Path(a.model).exists():
            raise SystemExit(
                "⛔⛔ --object-kind full_weight but --model %r is not a local "
                "path. A `_w` read must name the trained weights on disk; a hub "
                "id here is the base model wearing the treatment's label."
                % (a.model,))
    obj = a.adapter or a.model
    kind = a.object_kind or "adapter"

    from act2_backends import LocalBackend
    print("  loading %s + %s ..." % (a.model, a.adapter))
    t0 = time.perf_counter()
    backend = LocalBackend(a.model, adapter=a.adapter, device=a.device,
                           load_4bit=a.four_bit,
                           max_new_tokens=a.max_new_tokens,
                           temperature=a.temperature)
    print("  ready in %.1fs" % (time.perf_counter() - t0))

    # ⛔⛔ THE MEASUREMENT IS `read_lag`, NOT A SECOND COPY OF IT HERE.
    # The CLI's job is to say WHICH OBJECT was read; what a lag read *is* lives
    # in one function, which the mid-run curve calls too. Two spellings of one
    # measurement is the wiring class that has already cost this campaign four
    # instances and one halted run.
    m = read_lag(backend, chains=a.chains, turns=a.turns, max_lag=a.max_lag,
                 shuffles=a.shuffles, seed=a.seed,
                 temperature=a.temperature, max_new_tokens=a.max_new_tokens)
    if m["chains_used"] == 0:
        raise SystemExit("⛔⛔ " + m["refusal_reason"])

    prof, zs, npairs = m["lag_profile"], m["z"], m["n_pairs"]
    verdict, why = m["verdict"], m["refusal_reason"]

    # ⭐ PROVENANCE IS THE CALLER'S TO ADD. `read_lag` knows what it measured;
    # only main() knows what it was pointed at.
    report = dict(m)
    report.update({
        "adapter": a.adapter,
        # ⭐ THE CAVEAT IN THE FIELD. `adapter: null` alone cannot say whether
        # this was a `_w` object or the bare base model; these two can.
        "object": obj, "object_kind": kind,
        "measurement_category": "_w" if kind == "full_weight" else "_ctx",
        "four_bit": a.four_bit,
        # ⛔ `temperature` / `max_new_tokens` are NOT set here any more. They are
        # the measurement's, and `read_lag` records them — a caller that also
        # wrote them could disagree with the decoder actually used, which is the
        # precise failure this arc is fixing.
        "INSTRUMENT": "tlon.discourse.transient — the same functions the corpus "
                      "was gated on, imported not re-spelt",
    })
    outp = pathlib.Path(a.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n  MODEL LAG PROFILE — %s [%s]" % (obj, kind))
    print("    " + "  ".join("lag%d %.4f" % (k, prof[k]) for k in sorted(prof)))
    print("    " + "  ".join(
        "lag%d UNSCOREABLE" % k if zs[k] is None else "lag%d z=%+.2f" % (k, zs[k])
        for k in sorted(zs)))
    print("    " + "  ".join("lag%d n=%d" % (k, npairs[k])
                             for k in sorted(npairs)))
    print("    chains %d used / %d dropped · %d turns"
          % (m["chains_used"], m["chains_dropped_too_short"], m["turns_total"]))
    print("    VERDICT: %s" % verdict)
    if why:
        print("    %s" % why)
    print("\n  wrote %s" % outp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
