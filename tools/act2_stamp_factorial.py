"""STAMP THE ADAPTER LEDGER WITH ITS FACTORIAL CELL — measured, not assumed.

    python tools/act2_stamp_factorial.py --ledger runs/act2/adapter_ledger.json

⛔⛔ THE ARMY IS ONLY A MATRIX IF EVERY ADAPTER CAN SAY WHICH CELL IT IS IN. An
adapter labelled only `adapter_s20621` belongs to no contrast once the terminal
scrollback is gone, and the factorial silently degrades into a pile.

⭐⭐ THE RECIPE IS READ OFF THE CORPUS'S OWN ROWS, NOT INFERRED FROM WHICH
GENERATOR HAPPENED TO EXIST. "These predate `--recipe`, so they must be
content-free" is a plausible derivation and this project has been burned by
plausible derivations. The within-pair lag-1 statistic against a permutation
null is a MEASUREMENT and it is available for every corpus still on disk.

⛔ WHERE THE CORPUS IS GONE, THE RECIPE IS RECORDED AS `unknown` AND SAID SO.
It is not back-filled from a sibling, from the pipeline that probably built it,
or from the date. An unmeasured cell that claims to be measured is worse than an
honest gap, because only the gap gets re-checked.

⛔ THE GENERATOR — and therefore the PAIRING REGIME — comes from the corpus
manifest, where a MISSING field means legacy. See `tlon/act2/factorial.py`.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.act2 import factorial as F                            # noqa: E402
from tlon.discourse import transient as TR                      # noqa: E402
from tlon.grammar import classes as C                           # noqa: E402

#: ⛔ Same threshold the corpus builder gates on, imported not re-spelt.
Z_RESPONSIVE = TR.Z_LAG1_MIN


#: ⛔⛔ ADAPTERS WHOSE CORPUS IS NOT AT THE CONVENTIONAL PATH — and the sha the
#: pipeline itself recorded, so the alias is VERIFIED rather than trusted.
#:
#: `pipeline_variance_decompose.sh` builds ONE corpus at **seed 20620** and
#: trains all three t3000x adapters on it; 30001-3 vary the TRAINER only (init,
#: shuffle, dropout). So their corpus seed is 20620, and the pipeline pins it to
#: EXPECT_TRAIN=263fe3c8… which is byte-identical to B-fresh's corpus.
#:
#: ⭐ THIS DISTINCTION IS LOAD-BEARING FOR THE MATRIX. The pair key must be the
#: CORPUS seed, because the corpus seed is what fixes the force sequence. Keying
#: t30001 on 30001 would look tidy and would pair it with nothing that exists.
CORPUS_ALIASES = {
    "t30001": ("runs/act2/ki_target/corpus_bfresh", 20620),
    "t30002": ("runs/act2/ki_target/corpus_bfresh", 20620),
    "t30003": ("runs/act2/ki_target/corpus_bfresh", 20620),
}
ALIAS_EXPECT_SHA256 = {
    "runs/act2/ki_target/corpus_bfresh":
        "263fe3c8cbc5dd9ea7c517b7940a415f2f3b0f078117904e4205d5ab1a7eeea1",
}


def _sha256(path: pathlib.Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def corpus_for(name: str, local_dir: str) -> tuple[pathlib.Path | None, int | None]:
    """-> (corpus_dir, corpus_seed). ⛔ An alias is CHECKED against its sha.

    The conventional case is `.../adapter_s20621` -> `.../corpus_s20621`. Where
    an alias is used instead, the recorded sha256 must match or this REFUSES:
    a stale alias would silently attribute one corpus's recipe to an adapter
    trained on a different one.
    """
    if name in CORPUS_ALIASES:
        rel, seed = CORPUS_ALIASES[name]
        cand = pathlib.Path(rel)
        train = cand / "train.jsonl"
        if not train.exists():
            return None, seed
        want = ALIAS_EXPECT_SHA256.get(rel)
        got = _sha256(train)
        if want and got != want:
            raise SystemExit(
                "⛔⛔ ALIAS SHA MISMATCH for %s: %s is %s, pipeline recorded %s. "
                "Refusing to attribute this corpus's recipe to an adapter that "
                "may not have trained on it." % (name, rel, got[:16], want[:16]))
        return cand, seed
    p = pathlib.Path(local_dir)
    if not p.name.startswith("adapter_"):
        return None, None
    cand = p.parent / ("corpus_" + p.name[len("adapter_"):])
    if not (cand / "train.jsonl").exists():
        return None, None
    return cand, seed_of(p.name[len("adapter_"):])


def measure_recipe(corpus_dir: pathlib.Path, *, shuffles: int = 120,
                   seed: int = 20620) -> dict:
    """Read the recipe off the rows. ⭐ THE LABEL AS A MEASUREMENT."""
    lex_r = C.load()["classes"]["R"]

    def roots(s):
        return {t for t in s.split() if t in lex_r}

    prompts, resps = [], []
    with (corpus_dir / "train.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("direction") != "provoke":
                continue
            prompts.append(roots(r["prompt"]))
            resps.append(roots(r["surface"]))
    if not prompts:
        raise SystemExit("⛔ %s has no provoke rows — nothing to measure"
                         % corpus_dir)
    obs = sum(len(a & b) for a, b in zip(prompts, resps)) / len(prompts)
    rng = random.Random(seed)
    nulls = []
    for _ in range(shuffles):
        sh = resps[:]
        rng.shuffle(sh)
        nulls.append(sum(len(a & b) for a, b in zip(prompts, sh)) / len(sh))
    mu = sum(nulls) / len(nulls)
    sd = (sum((x - mu) ** 2 for x in nulls) / (len(nulls) - 1)) ** 0.5
    z = (obs - mu) / sd if sd else float("nan")
    return {"recipe": (TR.CONTENT_TRANSIENT if z >= Z_RESPONSIVE
                       else TR.CONTENT_FREE),
            "recipe_source": "measured",
            "within_pair_lag1": round(obs, 5),
            "permutation_null_mean": round(mu, 5),
            "permutation_null_sd": round(sd, 5),
            "z_lag1": round(z, 2),
            "n_provoke_rows": len(prompts),
            "corpus_dir": str(corpus_dir).replace("\\", "/")}


def seed_of(name: str) -> int | None:
    """`s20621` -> 20621, `t30001` -> 30001. ⛔ None rather than a guess."""
    digits = "".join(ch for ch in name if ch.isdigit())
    return int(digits) if digits else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default="runs/act2/adapter_ledger.json")
    ap.add_argument("--write", action="store_true",
                    help="write the stamped ledger back. Without it this is a "
                         "read-only report.")
    a = ap.parse_args()

    path = pathlib.Path(a.ledger)
    led = json.loads(path.read_text(encoding="utf-8"))
    rows = led.get("adapters") or []
    if not rows:
        raise SystemExit("⛔ ledger has no adapters — refusing to stamp nothing")

    print("STAMPING THE FACTORIAL CELL ONTO %d ADAPTER(S)\n" % len(rows))
    print("  %-9s %-16s %-7s %-7s %-7s %s"
          % ("adapter", "recipe", "z_lag1", "corpus", "trainer", "generator"))
    stamped, unknown = [], 0
    for r in rows:
        name = r.get("name")
        trainer_seed = seed_of(name or "")
        cdir, corpus_seed = corpus_for(name or "", r.get("local_dir") or "")
        # ⛔⛔ THE PAIR KEY IS THE CORPUS SEED, NOT THE ADAPTER'S NAME. For the
        # t3000x builds those differ: one corpus at seed 20620, three trainer
        # seeds. Keying on the name would pair them with nothing that exists.
        if corpus_seed is None:
            corpus_seed = trainer_seed
        seed = corpus_seed
        if cdir is not None:
            m = measure_recipe(cdir)
        else:
            # ⛔ NOT back-filled. An unmeasured cell that claims to be measured
            # is worse than a gap, because only the gap gets re-checked.
            m = {"recipe": None, "recipe_source": "unknown",
                 "z_lag1": None, "corpus_dir": None,
                 "NOTE": "corpus not on disk; regenerable from its seed, "
                         "then re-run this tool"}
            unknown += 1
        man = {}
        if cdir is not None and (cdir / "manifest.json").exists():
            man = json.loads((cdir / "manifest.json").read_text(encoding="utf-8"))
        gen = F.generator_of(man)
        fac = {"seed": seed, "corpus_seed": corpus_seed,
               "trainer_seed": trainer_seed, "generator": gen,
               "pairing_capability_side": (
                   TR.PAIRED_SEED_AND_FORCE if gen == TR.GENERATOR_SPLIT_STREAM
                   else TR.PAIRED_SEED_ONLY),
               # ⛔ Keyed on the CORPUS seed — the thing that fixes the force
               # sequence. The trainer seed is a different axis entirely.
               "factorial_pair_key": ("seed%d" % seed) if seed else None}
        if corpus_seed != trainer_seed:
            fac["SEED_NOTE"] = (
                "corpus seed %s differs from trainer seed %s: this adapter "
                "shares its corpus with its siblings and varies only the "
                "trainer draw (init/shuffle/dropout)."
                % (corpus_seed, trainer_seed))
        fac.update(m)
        if m["recipe"]:
            fac["cell"] = F.adapter_label(m["recipe"], seed) if seed else None
        r["factorial"] = fac
        stamped.append(r)
        print("  %-9s %-16s %-7s %-7s %-7s %s"
              % (name, m["recipe"] or "UNKNOWN",
                 ("%+.2f" % m["z_lag1"]) if m["z_lag1"] is not None else "—",
                 corpus_seed, trainer_seed, gen.split("/")[0]))

    led["factorial_NOTE"] = (
        "`recipe` is MEASURED from the corpus's own provoke rows (within-pair "
        "lag-1 shared roots vs a permutation null), never inferred from which "
        "generator existed at the time. `generator` comes from the corpus "
        "manifest and a MISSING field means LEGACY. A PAIR is `seed+force` only "
        "if BOTH arms are split-stream; one legacy side makes the pair `seed`-"
        "only — unbiased but UNPAIRED, and therefore higher variance.")
    print("\n  %d measured, %d unknown" % (len(rows) - unknown, unknown))

    if a.write:
        path.write_text(json.dumps(led, indent=2, ensure_ascii=False),
                        encoding="utf-8")
        print("  wrote %s" % path)
    else:
        print("  (read-only; pass --write to stamp the ledger)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
