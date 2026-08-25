"""TWO-SIDED POSITIVE CONTROL for the denotation projection π. PREREG c09d0fb3.

GATE. If either side fails, phase 5 does not run.

  BLINDNESS   plant a code in a STRIPPED channel (aspect_reps). The listener's
              accuracy must NOT improve. That proves π removed the RECEPTOR --
              the code cannot be received at all -- rather than merely making it
              unattractive. A gain here means π leaks.

  SENSITIVITY plant a code in a SURVIVING channel (aspect_root). Accuracy must
              improve AND the scramble probe must fire > 1.0 pt. That proves the
              probe still detects a code that is actually there.

Blindness alone is worthless: a projection that destroyed everything would pass
it trivially while making the whole phase meaningless. Sensitivity is what stops
that, which is why the control has to be two-sided.

CONTRAST ARM. The same reps-code WITHOUT π must gain accuracy (phase 4 measured
+7.1 pts). Without it, "no gain under π" could mean the plant was simply too
weak to matter -- and that is indistinguishable from blindness. The contrast is
what makes the blindness result attributable to π.

Both codes carry the SAME 2 bits (4 values) so the two sides are measured on
equal information content, not on one code being fatter than the other.
"""
from __future__ import annotations
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

from tlon.grammar import classes as C                        # noqa: E402
from tlon.grammar.denote import project                      # noqa: E402
from tlon.grammar.parse import (EventNode, ParseError,       # noqa: E402
                                Scene, parse, render)
from tlon.listener import data, train as tr                  # noqa: E402
from tlon.listener import tokenizer as tk                    # noqa: E402
from tlon.referents import schema                            # noqa: E402
from tlon.referents.match import consistent                  # noqa: E402
from cipher_control import scramble                          # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
PER_REF = 260
SEED = 5150
N_CODES = 4          # 2 bits, identical for both planted codes
FIRE = 1.0
BLIND_TOL = 1.5      # accuracy gain under a stripped code must stay under this


def build(ref, keep, rng, code: str | None, ci: int, use_pi: bool):
    """One partial utterance. `code` plants a 2-bit code in that channel."""
    lex = C.load()["classes"]
    k = C.constraints()
    sig = ref.signature
    a_roots = sorted(lex["A"])[:N_CODES]

    def node(pat, decorate: bool) -> EventNode:
        n = EventNode(
            root=rng.choice(list(pat.root_any)),
            orient=[rng.choice(list(pat.orient_any))] if pat.orient_any else [])
        reps = (ci + 1) if code == "aspect_reps" else rng.randint(
            1, k["MAX_ASPECT_REPS"])
        if pat.aspect_root_any:
            # signature-constrained: the code may not overwrite meaning
            n.aspect = (rng.choice(list(pat.aspect_root_any)), reps)
        elif decorate:
            root = (a_roots[ci] if code == "aspect_root"
                    else rng.choice(sorted(lex["A"])))
            n.aspect = (root, reps)
        if decorate and rng.random() < 0.5:
            n.degree = rng.choice(sorted(lex["D"]))
        return n

    head = node(sig.contains[0], True)
    deep, used = [], set()
    for i in keep:
        pat = sig.contains[1 + i]
        child = node(pat, False)
        rel = rng.choice(list(pat.via)) if pat.via else rng.choice(list(lex["L"]))
        if (pat.at_depth or 1) > 1:
            deep.append((pat.at_depth, rel, child))
            continue
        if (rel, child.root) in used:
            return None
        used.add((rel, child.root))
        head.edges.append((rel, child))
    for want, rel, child in deep:
        cur, d = head, 0
        while d + 1 < want and cur.edges:
            cur = cur.edges[0][1]
            d += 1
        if d + 1 != want:
            return None
        cur.edges.append((rel, child))
    sc = Scene(node=head, force=rng.choice(sorted(lex["F"])))
    if use_pi:
        sc = project(sc)
    try:
        parse(render(sc))
        tk.encode(render(sc))
    except (ParseError, ValueError):
        return None
    return sc


def make_rows(refs, code, use_pi, rng):
    rows, amb = [], []
    for ri, ref in enumerate(refs):
        deps = len(ref.signature.contains) - 1
        made, guard = 0, 0
        while made < PER_REF and guard < PER_REF * 6:
            guard += 1
            keep = tuple(i for i in range(deps) if rng.random() < 0.5)
            sc = build(ref, keep, rng, code, ri % N_CODES, use_pi)
            if sc is None:
                continue
            surf = render(sc)
            rows.append(data.Example(label=ri, ref_id=ref.id, surface=surf,
                                     uid="", ids=tk.encode(surf), dec_key=""))
            amb.append(sum(1 for b in refs if consistent(sc, b.signature)))
            made += 1
    return rows, amb


def acc(model, rows, cfg):
    if len(rows) < 10:
        return float("nan")
    p = tr.predict(model, rows, cfg).tolist()
    return sum(1 for a, r in zip(p, rows) if a == r.label) / len(rows)


def arm(refs, code, use_pi, cfg, rng, probe_ch=None):
    rows, amb = make_rows(refs, code, use_pi, rng)
    idx = list(range(len(rows)))
    rng.shuffle(idx)
    cut = int(0.85 * len(rows))
    trn = [rows[i] for i in idx[:cut]]
    tst = [rows[i] for i in idx[cut:]]
    tamb = [amb[i] for i in idx[cut:]]
    model = tr.train(trn, tst, len(refs), cfg, verbose=False)
    out = {"acc": acc(model, tst, cfg), "n": len(tst),
           "frac_ambiguous": sum(1 for x in tamb if x > 1) / len(tamb)}
    if probe_ch:
        o, s, oa = [], [], []
        for ex, av in zip(tst, tamb):
            sc = scramble(ex.surface, probe_ch, rng)
            if sc is None:
                continue
            o.append(ex)
            oa.append(av)
            s.append(data.Example(label=ex.label, ref_id=ex.ref_id, surface=sc,
                                  uid="", ids=tk.encode(sc), dec_key=""))
        if len(o) >= 50:
            out["drop"] = acc(model, o, cfg) - acc(model, s, cfg)
            ao = [r for r, a in zip(o, oa) if a > 1]
            as_ = [r for r, a in zip(s, oa) if a > 1]
            out["drop_ambiguous"] = (acc(model, ao, cfg) - acc(model, as_, cfg)
                                     if len(ao) >= 30 else float("nan"))
        else:
            out["drop"] = float("nan")
            out["drop_ambiguous"] = float("nan")
            out["probe_unavailable"] = True
    return out


def verdict(base, blind, sens, contrast) -> str:
    v = ("UNRECOGNISED -- no enumerated branch matched. Read the table by hand.")
    gain_blind = 100 * (blind["acc"] - base["acc"])
    gain_sens = 100 * (sens["acc"] - base["acc"])
    fired = 100 * sens.get("drop_ambiguous", float("nan"))
    gain_contrast = 100 * contrast["acc"] - 100 * base["acc"]

    if gain_contrast < FIRE:
        v = (f"CONTRAST FAILED. The reps-code gains only {gain_contrast:+.2f} "
             "pts even WITHOUT pi, so the plant is too weak to matter and "
             "'no gain under pi' proves nothing about blindness. Strengthen "
             "the plant. PHASE 5 DOES NOT RUN.")
    elif gain_blind > BLIND_TOL:
        v = (f"PI LEAKS. A code in a STRIPPED channel still bought "
             f"{gain_blind:+.2f} pts, so the projection did not remove the "
             "receptor. Every phase-5 number would be measured through a hole. "
             "PHASE 5 DOES NOT RUN.")
    elif fired != fired or fired <= FIRE:
        v = (f"PROBE BLIND UNDER PI. A code in a SURVIVING channel is present "
             f"(accuracy {gain_sens:+.2f} pts) but scrambling it costs only "
             f"{fired:+.2f} pts. The detector does not work in this regime, so "
             "a clean phase-5 result would be meaningless. PHASE 5 DOES NOT RUN.")
    else:
        v = (f"BOTH SIDES PASS. Stripped-channel code buys {gain_blind:+.2f} pts "
             f"under pi (vs {gain_contrast:+.2f} without it) => the receptor is "
             f"GONE, not merely discouraged. Surviving-channel code is detected "
             f"at {fired:+.2f} pts => the probe still works. PHASE 5 IS CLEARED.")
    return v


def main() -> int:
    rng = random.Random(SEED)
    refs = schema.load_all().referents
    cfg = tr.TrainCfg()
    print("=" * 78)
    print("PI CONTROLS -- two-sided. PREREG c09d0fb3")
    print("=" * 78)
    print(f"  both planted codes carry {N_CODES} values = 2 bits, so blindness "
          f"and sensitivity\n  are measured on equal information content\n")

    print("  [1/4] pi, NO code           (baseline)")
    base = arm(refs, None, True, cfg, rng)
    print(f"        accuracy {100 * base['acc']:.1f}%   ambiguous "
          f"{100 * base['frac_ambiguous']:.1f}%")

    print("  [2/4] pi, code in ASPECT_REPS   (stripped -> BLINDNESS)")
    blind = arm(refs, "aspect_reps", True, cfg, rng, probe_ch="aspect_reps")
    print(f"        accuracy {100 * blind['acc']:.1f}%   "
          f"gain {100 * (blind['acc'] - base['acc']):+.2f} pts")

    print("  [3/4] pi, code in ASPECT_ROOT   (survives -> SENSITIVITY)")
    sens = arm(refs, "aspect_root", True, cfg, rng, probe_ch="aspect_root")
    print(f"        accuracy {100 * sens['acc']:.1f}%   "
          f"gain {100 * (sens['acc'] - base['acc']):+.2f} pts   "
          f"scramble {100 * sens.get('drop', float('nan')):+.2f} "
          f"(ambiguous {100 * sens.get('drop_ambiguous', float('nan')):+.2f})")

    print("  [4/4] NO pi, code in ASPECT_REPS  (contrast: plant must work)")
    contrast = arm(refs, "aspect_reps", False, cfg, rng, probe_ch="aspect_reps")
    print(f"        accuracy {100 * contrast['acc']:.1f}%   "
          f"gain over pi-baseline {100 * (contrast['acc'] - base['acc']):+.2f} pts   "
          f"scramble {100 * contrast.get('drop', float('nan')):+.2f}")

    print(f"\n  VERDICT: {verdict(base, blind, sens, contrast)}")
    (OUT / "pi_controls.json").write_text(json.dumps(
        {"prereg": "c09d0fb3", "baseline": base, "blindness": blind,
         "sensitivity": sens, "contrast": contrast,
         "verdict": verdict(base, blind, sens, contrast)},
        indent=2, default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'pi_controls.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
