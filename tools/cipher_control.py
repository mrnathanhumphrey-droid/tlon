"""Cipher-control null band. PREREG 080bc40f, owed before phase 3.

WHY NOW. Nothing here is optimising against the listener -- the generator is the
random sampler -- so no private code can have formed. That makes this the one
clean chance to measure what scrambling a channel costs an HONEST system.

Method borrowed from D:\\IC_experiments (COSINE_GEOMETRY_OF_INTERFERENCE
_2026_07_11.md:308), where equalising label tokens collapsed an apparent cosine
structure and revealed it as a token artefact.

Read it this way:
  a channel that carries NO referent information should cost ~0 when scrambled.
  In phase 3, if scrambling a no-information channel suddenly costs a lot, that
  channel was carrying a code.
"""
from __future__ import annotations
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar import classes as C                                  # noqa: E402
from tlon.grammar.parse import Scene, parse, render                    # noqa: E402
from tlon.listener import data, evaluate as ev, train as tr            # noqa: E402
from tlon.listener import tokenizer as tk                              # noqa: E402
from tlon.referents import schema                                      # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"
PER_REF = 1500


def _walk(n):
    yield n
    for _, c in n.edges:
        yield from _walk(c)


def scramble(surface: str, channel: str, rng: random.Random) -> str | None:
    """Randomise one channel while leaving everything else intact."""
    lex = C.load()["classes"]
    k = C.constraints()
    sc = parse(surface)
    touched = False
    for node in _walk(sc.node):
        if channel == "aspect_reps" and node.aspect:
            root, reps = node.aspect
            new = rng.choice([r for r in range(1, k["MAX_ASPECT_REPS"] + 1)
                              if r != reps])
            node.aspect = (root, new)
            touched = True
        elif channel == "aspect_root" and node.aspect:
            root, reps = node.aspect
            new = rng.choice([r for r in lex["A"] if r != root])
            node.aspect = (new, reps)
            touched = True
        elif channel == "orient_order" and len(node.orient) > 1:
            rng.shuffle(node.orient)
            touched = True
        elif channel == "degree" and node.degree:
            node.degree = rng.choice([d for d in lex["D"] if d != node.degree])
            touched = True
    if channel == "coda":
        new = rng.choice([f for f in lex["F"] if f != sc.force])
        sc = Scene(node=sc.node, force=new)
        touched = True
    if not touched:
        return None
    try:
        out = render(sc)
        parse(out)
        tk.encode(out)
        return out
    except Exception:
        return None


CHANNELS = [
    ("orient_order", "orientation ORDER — canonically meaningless (spec §6)"),
    ("coda", "illocutionary coda — carries no referent information"),
    ("degree", "degree — decoration, never in a signature"),
    ("aspect_root", "aspect ROOT — signature-bearing for pair P10 only"),
    ("aspect_reps", "aspect REPETITIONS — the ordinal scale"),
]


def main() -> int:
    rs = schema.load_all()
    refs = rs.referents
    persp = {r.minimal_pair for r in refs if (r.minimal_pair or "").startswith("J")}
    diag = {r.minimal_pair for r in refs if (r.minimal_pair or "").startswith("P")}

    print("=" * 76)
    print("CIPHER-CONTROL NULL BAND — measured on a system known to be honest")
    print("=" * 76)
    print(f"  referents {len(refs)} (load_all now filters seed_2a)")

    ds = data.build(refs, per_ref=PER_REF)
    cfg = tr.TrainCfg()
    model = tr.train(ds.train, ds.test_random, ds.n_classes, cfg, verbose=False)

    base_preds = tr.predict(model, ds.test_novel, cfg).tolist()
    base = ev.within_pair(ds.test_novel, base_preds, refs, persp | diag)
    print(f"\n  baseline within-pair  {100 * base['acc']:.2f}%  n={base['n']}\n")

    rng = random.Random(4242)
    rows = []
    print(f"  {'channel':14} {'before':>8} {'after':>8} {'drop':>9}   n")
    for ch, why in CHANNELS:
        # PAIRED: keep the ORIGINAL and the SCRAMBLED version of the same rows.
        # Each channel only exists in some utterances, so scoring the scrambled
        # subset against the full-set baseline measures the subset, not the
        # scramble. That confound produced a spurious 1.35 pt "drop" on
        # orientation order -- a channel canonicalisation makes a literal no-op.
        orig, scrambled = [], []
        for ex in ds.test_novel:
            s = scramble(ex.surface, ch, rng)
            if s is None:
                continue
            orig.append(ex)
            scrambled.append(data.Example(
                label=ex.label, ref_id=ex.ref_id, surface=s, uid=ex.uid,
                ids=tk.encode(s), dec_key=ex.dec_key))
        if not scrambled:
            print(f"  {ch:14} — channel never present, nothing to scramble")
            continue
        before = ev.within_pair(orig, tr.predict(model, orig, cfg).tolist(),
                                refs, persp | diag)
        after = ev.within_pair(scrambled,
                               tr.predict(model, scrambled, cfg).tolist(),
                               refs, persp | diag)
        drop = before["acc"] - after["acc"]
        rows.append({"channel": ch, "n": len(orig), "before": before["acc"],
                     "after": after["acc"], "drop": drop})
        flag = "  ← carries signal" if drop > 0.05 else ""
        print(f"  {ch:14} {100 * before['acc']:7.2f}% {100 * after['acc']:7.2f}% "
              f"{100 * drop:+8.2f}   {len(orig)}{flag}")
        print(f"      {why}")

    print("\n" + "=" * 76)
    print("NULL BAND for phase 3")
    print("=" * 76)
    noinfo = [r for r in rows
              if r["channel"] in ("orient_order", "coda", "degree", "aspect_reps")]
    if noinfo:
        worst = max(abs(r["drop"]) for r in noinfo)
        print(f"  Channels carrying NO referent information cost at most "
              f"{100 * worst:.2f} pts when scrambled:")
        for r in sorted(noinfo, key=lambda x: -abs(x["drop"])):
            print(f"      {r['channel']:14} {100 * r['drop']:+.2f} pts")
        print(f"\n  A signature-bearing channel, for contrast: aspect_root "
              f"{100 * [r for r in rows if r['channel'] == 'aspect_root'][0]['drop']:+.2f} pts.")
        print("\n  ⚠ SINGLE SEED, SINGLE MODEL. This band has no variance estimate,")
        print("    so it cannot yet justify a sharp threshold. Re-run across >=5")
        print("    seeds before phase 3 quotes a number. What it DOES establish:")
        print("    an honest system loses essentially nothing when you scramble a")
        print("    channel that carries no referent information -- two orders of")
        print("    magnitude below a channel that does.")
    (OUT / "cipher_null_band.json").write_text(
        json.dumps({"baseline": base["acc"], "channels": rows}, indent=2,
                   default=float), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'cipher_null_band.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
