"""POSITIVE CONTROL — plant a cipher and confirm the scramble probe sees it.

GATE, NOT A STEP. PREREG c1f7d06c: if the planted cipher is not detected,
phase 4 does not run.

WHY IT EXISTS. Phase 3's KILL A came back clean and the null was worth nothing,
because M was never scarce and no code had any reason to form. The probe's
sensitivity has only ever been established in that regime -- where the signature
core hands the listener the answer. A long green record in one regime says
nothing about a regime the code has never run in, so before phase 4 reports any
threshold the probe must be shown to FIRE on a cipher that is known to be there.

THE TRAP THIS CONTROL HAS TO AVOID. A planted code is only visible to the probe
if the listener actually USES it. Under full utterances the listener already has
everything it needs from the signature, so it would ignore any planted code and
the probe would read ~0 -- which looks exactly like "the probe is blind" while
actually meaning "there was nothing to detect". Those are different failures and
a control that cannot tell them apart is the same vacuous test all over again.

So the control is run UNDER SELECTION (partial utterances, M genuinely scarce)
and is paired:

  ARM A  no code    -- aspect_reps random
  ARM B  code       -- aspect_reps = f(referent), a deterministic 2-bit cipher

and it checks THREE things in order:

  1. Is the code learnable/used?  acc(B) > acc(A). If not, the plant failed and
     the probe result is uninterpretable -- report that, do not report a drop.
  2. Does the probe fire on B?    scramble(aspect_reps) drop, must be LARGE.
  3. Does it stay quiet on A?     same scramble on the no-code arm, must be ~0.

Only (1) AND (2) AND (3) together establish a detection floor.
"""
from __future__ import annotations
import json
import pathlib
import random
import statistics as S
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

from tlon.grammar import classes as C                    # noqa: E402
from tlon.grammar.parse import (EventNode, ParseError,   # noqa: E402
                                Scene, parse, render)
from tlon.listener import data, train as tr              # noqa: E402
from tlon.listener import tokenizer as tk                # noqa: E402
from tlon.referents import schema                        # noqa: E402
from tlon.referents.schema import Referent               # noqa: E402
from cipher_control import scramble                      # noqa: E402
from confusability import consistent                     # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
PER_REF = 260
SEED = 777
CH = "aspect_reps"
FIRE = 1.0     # a drop above this counts as "the probe fired" (KILL A's threshold)
QUIET = 0.5    # the no-code arm must stay under this (KILL A-prime's threshold)


def build_partial(ref: Referent, keep: tuple[int, ...], rng: random.Random,
                  reps: int | None) -> Scene | None:
    """Partial utterance. `reps` forces the aspect repetition count = the code."""
    lex = C.load()["classes"]
    k = C.constraints()
    sig = ref.signature

    def node(pat, decorate: bool) -> EventNode:
        n = EventNode(
            root=rng.choice(list(pat.root_any)),
            orient=[rng.choice(list(pat.orient_any))] if pat.orient_any else [])
        r = reps if reps is not None else rng.randint(1, k["MAX_ASPECT_REPS"])
        if pat.aspect_root_any:
            n.aspect = (rng.choice(list(pat.aspect_root_any)), r)
        elif decorate:
            n.aspect = (rng.choice(sorted(lex["A"])), r)
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
    try:
        parse(render(sc))
        tk.encode(render(sc))
    except (ParseError, ValueError):
        return None
    return sc


def make_rows(refs, coded: bool, rng: random.Random):
    """Partial utterances for every referent. coded => aspect_reps = f(ref)."""
    k = C.constraints()
    n_codes = k["MAX_ASPECT_REPS"]
    rows, amb = [], []
    for ri, ref in enumerate(refs):
        deps = len(ref.signature.contains) - 1
        made = 0
        guard = 0
        while made < PER_REF and guard < PER_REF * 6:
            guard += 1
            keep = tuple(i for i in range(deps) if rng.random() < 0.5)
            reps = (ri % n_codes) + 1 if coded else None
            sc = build_partial(ref, keep, rng, reps)
            if sc is None:
                continue
            surf = render(sc)
            rows.append(data.Example(label=ri, ref_id=ref.id, surface=surf,
                                     uid="", ids=tk.encode(surf), dec_key=""))
            amb.append(sum(1 for b in refs if consistent(sc, b.signature)))
            made += 1
    return rows, amb


def acc(model, rows, cfg) -> float:
    preds = tr.predict(model, rows, cfg).tolist()
    return sum(1 for p, r in zip(preds, rows) if p == r.label) / len(rows)


def strat_acc(model, rows, amb, cfg, want_amb: bool) -> float:
    sel = [r for r, a in zip(rows, amb) if (a > 1) == want_amb]
    if len(sel) < 30:
        return float("nan")
    preds = tr.predict(model, sel, cfg).tolist()
    return sum(1 for p, r in zip(preds, sel) if p == r.label) / len(sel)


def run_arm(refs, coded: bool, cfg, rng):
    rows, amb = make_rows(refs, coded, rng)
    cut = int(0.85 * len(rows))
    idx = list(range(len(rows)))
    rng.shuffle(idx)
    tr_rows = [rows[i] for i in idx[:cut]]
    te_rows = [rows[i] for i in idx[cut:]]
    te_amb = [amb[i] for i in idx[cut:]]
    model = tr.train(tr_rows, te_rows, len(refs), cfg, verbose=False)
    a = acc(model, te_rows, cfg)

    # paired scramble on IDENTICAL rows
    scr, keep_rows, keep_amb = [], [], []
    for ex, av in zip(te_rows, te_amb):
        s = scramble(ex.surface, CH, rng)
        if s is None:
            continue
        keep_rows.append(ex)
        keep_amb.append(av)
        scr.append(data.Example(label=ex.label, ref_id=ex.ref_id, surface=s,
                                uid="", ids=tk.encode(s), dec_key=""))
    drop = acc(model, keep_rows, cfg) - acc(model, scr, cfg)
    d_amb = (strat_acc(model, keep_rows, keep_amb, cfg, True)
             - strat_acc(model, scr, keep_amb, cfg, True))
    d_un = (strat_acc(model, keep_rows, keep_amb, cfg, False)
            - strat_acc(model, scr, keep_amb, cfg, False))
    return {"acc": a, "drop": drop, "drop_ambiguous": d_amb,
            "drop_unambiguous": d_un, "n_test": len(te_rows),
            "mean_ambiguity": S.fmean(te_amb),
            "frac_ambiguous": sum(1 for x in te_amb if x > 1) / len(te_amb)}


def verdict(a: dict, b: dict) -> str:
    v = ("UNRECOGNISED -- none of the enumerated branches matched. Read the "
         "table by hand before concluding anything.")
    used = b["acc"] > a["acc"]
    fired = 100 * b["drop"] > FIRE
    quiet = 100 * a["drop"] <= QUIET
    if not used:
        v = ("PLANT FAILED -- the coded arm is no more accurate than the "
             "uncoded one, so the listener never used the code. The probe "
             "result is UNINTERPRETABLE: a small drop here would mean 'nothing "
             "to detect', not 'probe is blind'. Fix the plant, do not read the "
             "drop. PHASE 4 DOES NOT RUN.")
    elif used and fired and quiet:
        v = (f"DETECTION FLOOR ESTABLISHED. The code was learned "
             f"(+{100 * (b['acc'] - a['acc']):.1f} pts accuracy), the probe "
             f"fired on it ({100 * b['drop']:+.2f} pts), and stayed quiet "
             f"without it ({100 * a['drop']:+.2f} pts). KILL A can fire in "
             f"this regime. PHASE 4 IS CLEARED TO RUN.")
    elif used and not fired:
        v = (f"PROBE BLIND. The code WAS used (+"
             f"{100 * (b['acc'] - a['acc']):.1f} pts) but scrambling it cost "
             f"only {100 * b['drop']:+.2f} pts. The scramble probe cannot see a "
             f"cipher it is standing on. Every KILL A null in this project is "
             f"suspect. PHASE 4 DOES NOT RUN.")
    elif used and fired and not quiet:
        v = (f"CONTAMINATED. The probe fires on the coded arm "
             f"({100 * b['drop']:+.2f}) but ALSO on the uncoded one "
             f"({100 * a['drop']:+.2f} > {QUIET}). It is reading something "
             f"other than the code, so its magnitude cannot be attributed. "
             f"Fix the probe before phase 4.")
    return v


def main() -> int:
    rng = random.Random(SEED)
    refs = schema.load_all().referents
    cfg = tr.TrainCfg()
    print("=" * 78)
    print("PLANTED-CIPHER POSITIVE CONTROL -- PREREG c1f7d06c")
    print("=" * 78)
    print(f"\n  regime: SELECTION (partial utterances), {len(refs)} referents")
    print(f"  code   : {CH} = (referent index mod "
          f"{C.constraints()['MAX_ASPECT_REPS']}) + 1\n")

    print("  -- ARM A: no code ---------------------------------------------")
    a = run_arm(refs, False, cfg, rng)
    print(f"    accuracy {100 * a['acc']:.1f}%   mean ambiguity "
          f"{a['mean_ambiguity']:.2f}   ambiguous rows "
          f"{100 * a['frac_ambiguous']:.1f}%")
    print(f"    scramble {CH}: {100 * a['drop']:+.2f} pts  "
          f"(ambiguous {100 * a['drop_ambiguous']:+.2f} / unambiguous "
          f"{100 * a['drop_unambiguous']:+.2f})")

    print("\n  -- ARM B: planted cipher --------------------------------------")
    b = run_arm(refs, True, cfg, rng)
    print(f"    accuracy {100 * b['acc']:.1f}%   mean ambiguity "
          f"{b['mean_ambiguity']:.2f}   ambiguous rows "
          f"{100 * b['frac_ambiguous']:.1f}%")
    print(f"    scramble {CH}: {100 * b['drop']:+.2f} pts  "
          f"(ambiguous {100 * b['drop_ambiguous']:+.2f} / unambiguous "
          f"{100 * b['drop_unambiguous']:+.2f})")

    print(f"\n  code used?  accuracy B - A = {100 * (b['acc'] - a['acc']):+.1f} pts")
    print(f"  probe fired on the code?  {100 * b['drop']:+.2f} pts "
          f"(needs > {FIRE})")
    print(f"  probe quiet without it?   {100 * a['drop']:+.2f} pts "
          f"(needs <= {QUIET})")
    print(f"\n  VERDICT: {verdict(a, b)}")

    (OUT / "planted_cipher.json").write_text(json.dumps(
        {"prereg": "c1f7d06c", "channel": CH, "no_code": a, "coded": b,
         "verdict": verdict(a, b)}, indent=2, default=float),
        encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'planted_cipher.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
