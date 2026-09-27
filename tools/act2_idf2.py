"""IDF-2 Step 0 — the CPU precondition gate, before a GPU is rented.

`docs/PREREG_IDF2_2026_09_26.md`, LOCK `37363296`. Step 0 gates everything: no
adapter is trained and no read is interpreted until every sub-step below
reports. ⛔ No GPU, no remote box, no spend in this file.

    python tools/act2_idf2.py step0     # 0a .. 0e, in order, one report

⭐ THE STATISTIC IS IMPORTED, NEVER RE-SPELT. `lag_profile`, `permutation_null`,
`resolving_power` and `held` all live in `tlon.discourse.transient` and have
exactly one definition in this campaign. `tests/test_idf2_instruments.py` pins
that by identity, not by agreement.

⛔⛔ AND THE ORACLES SHARE THE GENERATOR. Every arm here is `build_transient`
with ONE argument varied — `barred_fn` — exactly as IDF-1's were. A re-spelt
generator is a second law that agrees with the first until it does not.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.act2 import corpus as C1              # noqa: E402
from tlon.discourse import force_map as FM      # noqa: E402
from tlon.discourse import transient as TR      # noqa: E402

#: Fixed everywhere in this probe. Prereg §3-0a.
SEED = 20624

#: `16abeb8d…`'s manifest, which 0a must match on every held variable.
#: Read off `runs/act2/retrain12_ct/corpus_ct-s20624/manifest.json`, not
#: recalled: chains 1445, turns 12, responsiveness 1.0, seed 20624.
REF_CHAINS = 1445
REF_TURNS = 12
REF_RESPONSIVENESS = 1.0

#: ⛔ The effect-size companion to `check_transience`'s z floor (sign-off #1).
#: `ct-s20624` passed lag-1 at z **+516.30** on 1,445 chains — a number that
#: cannot tell a healthy corpus from a half-collapsed one, which is D1's lesson
#: at corpus scale. So the gate is the RAW profile, and the reference is the
#: reference corpus's own measured value.
REF_LAG1 = 0.9621893677256999
LAG1_TOL = 0.05

#: Prereg §3-0c. The oracles run at IDF-1's read size so their anchors are as
#: precise as IDF-1b's were.
ORACLE_N = 5000
ORACLE_TURNS = 10

#: ⛔⛔ SEEDS PER ARM, RE-LOCKED 2026-09-27 ON STEP P'S MEASURED SD.
#: `DEVIATIONS_IDF2_2026_09_26.md` D4. The prereg body says three; it is LOCKED
#: and is not edited, so the change lives in DEVIATIONS and the operative
#: numbers live HERE, where the pipeline reads them instead of a default
#: someone has to remember.
#:
#: ⭐ THE REASON IS FLOORS, NOT PRECISION IN GENERAL. Step P measured the
#: between-seed SD at 5.79 points. At 3 seeds `SE(M − C1) = 5.79·√(2/3) =
#: 4.73` and the 95 % CI half-width is 13.13 — so a marker that does NOTHING
#: would leave an upper bound of ~13.1 against FLOORS' `< 15`, inside two
#: points of being undeclarable. INSTALLS was never at risk (35 points is
#: 7.4 SE). ⛔ A design whose most informative branch is the one it cannot
#: declare is the "failure that teaches nothing" §3A exists to remove.
#: At 5 seeds: SE 3.66, half-width ~8.4 on 8 df.
#:
#: ⚠️ W2 AND M-SHUFFLE STAY AT THREE, and that is my reading of Wilson's
#: "keep W2 and M-shuffle at the same count" — the count they already had.
#: Both are descriptive and neither gates a cell, so neither needs the power.
#: Say so if the intent was five everywhere; it is +4 reads.
SEEDS_PER_GATING_ARM = 5      # M, C1, M-strip — these gate a §6 cell
SEEDS_PER_DESCRIPTIVE_ARM = 3  # W2, M-shuffle — reported, never gating
GATING_ARMS = ("M", "C1", "M-strip")
DESCRIPTIVE_ARMS = ("W2", "M-shuffle")

#: ⛔ C0's lag-2 is the 8-SEED MEAN from Step P, never the single 120-turn
#: draw. `0.3854` was one read and it came in 2nd-lowest of eight; the
#: campaign cited it through D6, IDF-1 and IDF-1b as though it were central.
C0_LAG2_MEAN = 0.4033
C0_LAG2_SD = 0.0245
C0_LAG2_N_SEEDS = 8

OUT = pathlib.Path("runs/act2/idf2")


def _pool(seed=SEED):
    return C1.build(6000, seed=seed)


def _score(chains, tag, *, shuffles=200, seed=SEED, quiet=False):
    """Raw lag profile 1-4 plus the permutation-null z. -> (prof, z, npairs).

    ⛔ ONE rng for all four lags, drawn in order 1,2,3,4 — the same discipline
    as `act2_idf1.score`. Re-seeding per lag would silently change every z.
    """
    lex_r = TR._lex_roots()
    rng = random.Random(seed)
    prof = TR.lag_profile(chains, max_lag=4, lex_r=lex_r)
    z, npairs = {}, {}
    for lag in (1, 2, 3, 4):
        mu, sd = TR.permutation_null(chains, lag=lag, shuffles=shuffles,
                                     rng=rng, lex_r=lex_r)
        z[lag] = (prof[lag] - mu) / sd if sd else float("nan")
        npairs[lag] = TR.lag_pairs(chains, lag=lag)
    if not quiet:
        print("  %-22s %s" % (tag, " | ".join(
            "lag%d %.4f z%+9.3f" % (k, prof[k], z[k]) for k in (1, 2, 3, 4))))
    return prof, z, npairs


# ── the oracle speakers ────────────────────────────────────────────────────
#
# ⭐ TWO ORACLES, AND THEY ANCHOR OPPOSITE ENDS OF THE SAME SCALE. Every model
# result in §6 is read as a fraction of the gap between them, so these are the
# only two numbers in the probe that are allowed to define "0 %" and "100 %".

def barred_held(out, prev, lex_r):
    """0b. The marker oracle — a window-1 speaker applying the marker exactly.

    ⛔⛔ THIS IS A RED-PROOF AND A SHORTFALL IS A BUG. Under
    `content-transient-held` the generator's bar IS `held`, so this speaker is
    running the generator's own rule: its lag-2 must match the corpus's within
    sampling noise BY CONSTRUCTION. There is no hidden state left for it to
    miss, so a gap here cannot be "the part no surface reader can recover" —
    it can only mean the marker, the bar, or the reader's recomputation is
    wired wrong. Prereg §3-0b reverses an earlier reading that treated the
    shortfall as a finding; that quantity belongs to the OLD recipe, where
    `inherited` was hidden bookkeeping, and IDF-1b already measured it.

    ⭐ It calls `TR.held` rather than restating it — that identity is the point
    of §1 and the thing the test suite asserts.
    """
    return TR.held(out, prev, lex_r)


def barred_blind(out, prev, lex_r):
    """0c. The marker-blind oracle — the 0 % anchor. Bars nothing."""
    return frozenset()


def _speak(barred_fn, *, n=ORACLE_N, turns=ORACLE_TURNS, pool=None, seed=SEED):
    """The generator with ONE argument varied and nothing else."""
    if pool is None:
        pool = _pool(seed)
    return TR.build_transient(n, turns=turns, pairs=pool, seed=seed,
                              responsiveness=REF_RESPONSIVENESS,
                              fmap=FM.DERIVED_v1, verify=False,
                              barred_fn=barred_fn)


# ── 0a ─────────────────────────────────────────────────────────────────────

CORPUS_DIR = OUT / "corpus_held-s20624"


def _persist_corpus(chains, rep, prof, z, npairs):
    """⛔⛔ THE CORPUS EXISTS ON DISK AND IS HASHED BEFORE ANYTHING READS IT.

    §3-0a: *"Record its lag profile, its `n_pairs` per lag, and its sha. Push
    it to the hub before anything else runs."* The first implementation built
    the chains IN MEMORY, scored them, and threw them away — every number in
    Step 0 was real and the object that produced them did not survive the
    process. That is the `s20620` shape and the IDF-1 shape at once: a lost
    adapter, and instruments that existed only in a transcript.

    ⭐ The rows are written with `marker=True`, so the file on disk is the
    training text itself, not a chain dump a later step would have to re-derive
    the marker from.
    """
    import hashlib
    from act2_build_multiturn import rows_from

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    rows = rows_from(chains, marker=True)
    p = CORPUS_DIR / "train.jsonl"
    # ⛔ Temp-then-replace: `open(p, "w")` truncates before the write can fail,
    # so a crash mid-dump leaves a valid-looking short corpus.
    tmp = p.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(p)

    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    man = {"recipe": TR.CONTENT_TRANSIENT_HELD,
           "recipe_VERIFIED": rep["verdict"],
           "prereg": "docs/PREREG_IDF2_2026_09_26.md", "LOCK": "37363296",
           "seed": SEED, "chains": REF_CHAINS, "turns": REF_TURNS,
           "recipe_responsiveness": REF_RESPONSIVENESS,
           "generator": TR.GENERATOR_SPLIT_STREAM,
           "bar": "tlon.discourse.transient.held",
           "marker_prefix": TR.MARKER_PREFIX, "marker_none": TR.MARKER_NONE,
           "recipe_lag_profile": prof, "recipe_z_vs_permutation_null": z,
           "n_pairs": npairs, "rows": len(rows),
           "train_sha256": sha,
           # ⛔ NOT poolable with the factorial cells, and the manifest says so
           # in the field a later reader will actually look at.
           "NOT_IN_FACTORIAL": ("content-transient-held bars `held`, not the "
                                "generator's `inherited`; see PROBE_RECIPES")}
    (CORPUS_DIR / "manifest.json").write_text(
        json.dumps(man, indent=2), encoding="utf-8")
    print("    rows               %d -> %s" % (len(rows), p))
    print("    train sha256       %s" % sha[:16])
    return {"corpus_dir": str(CORPUS_DIR), "train_sha256": sha,
            "rows": len(rows)}


def push_corpus():
    """§3-0a's second half: the hub, before anything else runs."""
    from huggingface_hub import HfApi
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from act2_provision import _hf_token

    api = HfApi(token=_hf_token())
    repo = CT_REPO
    sha = json.loads((CORPUS_DIR / "manifest.json").read_text(
        encoding="utf-8"))["train_sha256"]
    dest = "corpus_held-s20624_%s" % sha[:16]
    print("\n0a · HUB — %s" % dest)
    for f in ("train.jsonl", "manifest.json"):
        api.upload_file(path_or_fileobj=str(CORPUS_DIR / f),
                        path_in_repo="%s/%s" % (dest, f),
                        repo_id=repo, repo_type="model")
        print("    ✅ %s" % f)
    return dest


def step_0a(report):
    """Build `content-transient-held` and make it earn its label."""
    print("\n0a · CORPUS — content-transient-held")
    pool = _pool()
    chains = TR.build_transient(
        REF_CHAINS, turns=REF_TURNS, pairs=pool, seed=SEED,
        responsiveness=REF_RESPONSIVENESS, fmap=FM.DERIVED_v1,
        verify=False, barred_fn=TR.held)

    # ⛔ The label is EARNED through the shared verifier, not asserted. This is
    # the call that would have aborted under the content-free branch before
    # `verify_recipe` learned this recipe's name.
    rep = TR.verify_recipe(chains, TR.CONTENT_TRANSIENT_HELD,
                           lex_r=TR._lex_roots())
    prof, z, npairs = _score(chains, "held corpus")

    lo, hi = REF_LAG1 * (1 - LAG1_TOL), REF_LAG1 * (1 + LAG1_TOL)
    ok = lo <= prof[1] <= hi
    print("    verdict            %s" % rep["verdict"])
    print("    lag-1 raw          %.4f   band [%.4f, %.4f]  %s"
          % (prof[1], lo, hi, "PASS" if ok else "⛔ MISS"))
    print("    lag-2 raw          %.4f   (ct-s20624 corpus: 0.0271)" % prof[2])
    report["0a"] = {"verdict": rep["verdict"], "lag_profile": prof,
                    "z": z, "n_pairs": npairs,
                    "lag1_band": [lo, hi], "lag1_in_band": ok,
                    "chains": REF_CHAINS, "turns": REF_TURNS, "seed": SEED}
    if ok:
        report["0a"].update(_persist_corpus(chains, rep, prof, z, npairs))
    if not ok:
        # ⛔ Prereg §3-0a: the `held` bar acts on what turn t may OFFER, not on
        # how much it echoes, so it is not meant to touch lag-1 at all. A miss
        # is a wiring problem of the same class as a 0b shortfall.
        raise SystemExit(
            "\n⛔ 0a MISS — lag-1 %.4f outside [%.4f, %.4f]. The held bar is "
            "not meant to touch lag-1; this is wiring, not the recipe. STOP "
            "before training (prereg §3-0a)." % (prof[1], lo, hi))
    return chains, prof


# ── 0b / 0c ────────────────────────────────────────────────────────────────

def step_0bc(report, corpus_lag2):
    """The two anchors, and the red-proof that the marker is sufficient."""
    print("\n0c · MARKER-BLIND ORACLE — the 0 %% anchor")
    blind = _speak(barred_blind)
    bprof, bz, bn = _score(blind, "O-A blind")

    print("\n0b · MARKER ORACLE — red-proof, must reproduce the corpus")
    marked = _speak(barred_held)
    mprof, mz, mn = _score(marked, "O-C held")

    # ⛔⛔ THE DENOMINATOR IS THE LOCKED ONE, AND IT IS THE CORPUS.
    # §6: `closes(x) = (blind₀c − x) / (blind₀c − corpus₀c)`. The first
    # implementation used `blind − marker_oracle` instead. Numerically it is
    # 0.19 % of the gap — the bands move by 0.0001 and 0.0003 raw — so nothing
    # material turns on it. It is corrected anyway, because a formula that is
    # locked is not approximated, and Step P's SD is denominated in these
    # units. ⭐ Conflating the two also mistakes 0b's ROLE: the oracle is the
    # red-proof that the marker is sufficient, not the scale's endpoint.
    gap = bprof[2] - corpus_lag2
    shortfall = mprof[2] - corpus_lag2
    print("\n    blind lag-2        %.4f     (0 %% anchor, 0c)" % bprof[2])
    print("    corpus lag-2       %.4f     (100 %% anchor, 0a)" % corpus_lag2)
    print("    marker lag-2       %.4f     (0b red-proof, NOT the anchor)"
          % mprof[2])
    print("    shortfall          %+.4f    (oracle − corpus)" % shortfall)
    print("    GAP                %.4f     ⭐ the ONE denominator (§6)"
          % gap)
    print("    IDF-1's gap was    0.4171   → %.1f %% of it"
          % (100 * gap / 0.4171))
    report["0c"] = {"blind_lag_profile": bprof, "z": bz, "n_pairs": bn}
    report["0b"] = {"marker_lag_profile": mprof, "z": mz, "n_pairs": mn,
                    "corpus_lag2": corpus_lag2, "shortfall": shortfall}
    report["gap"] = gap
    report["gap_definition"] = "blind_0c_lag2 - corpus_0a_lag2  (PREREG §6)"
    report["blind_lag2"] = bprof[2]
    report["corpus_lag2"] = corpus_lag2
    return gap, bprof[2], corpus_lag2


def closes(lag2, *, blind, corpus):
    """The one denominator, defined in 0c and used everywhere (§6)."""
    return 100.0 * (blind - lag2) / (blind - corpus)


# ── 0d · the row audit ─────────────────────────────────────────────────────

def step_0d(report, chains):
    """Every provoke row's input is SYSTEM[provoke] + surface + marker, and
    nothing else. ⛔ EVERY row, not a sample — the failure this guards against
    is one malformed row class, not a uniform format error.
    """
    from act2_build_multiturn import rows_from

    print("\n0d · ROW AUDIT — the marker reaches the training row, alone")
    lex_r = TR._lex_roots()
    rows = rows_from(chains, marker=True)
    prov = [r for r in rows if r["direction"] == "provoke"]

    bad, none_rows = [], 0
    # ⭐ Rebuilt independently from the chains rather than parsed back out of
    # the row: an audit that recomputes the marker the same way the builder
    # did would agree with a bug.
    want = []
    for ch in chains:
        for i, (prev, cur) in enumerate(zip(ch, ch[1:])):
            h = TR.roots_of(prev.surface, lex_r) & TR.roots_of(
                ch[i - 1].surface, lex_r) if i >= 1 else frozenset()
            want.append((prev.surface, h))

    if len(want) != len(prov):
        raise SystemExit("\n⛔ 0d — %d provoke rows for %d transitions"
                         % (len(prov), len(want)))

    for n, (r, (surf, h)) in enumerate(zip(prov, want)):
        parts = r["prompt"].split("\n")
        if len(parts) != 2:
            bad.append((n, "prompt is not exactly surface + one line"))
            continue
        head, line = parts
        if head != surf:
            bad.append((n, "surface altered"))
        if not line.startswith(TR.MARKER_PREFIX):
            bad.append((n, "marker prefix missing"))
            continue
        named = line[len(TR.MARKER_PREFIX):].split()
        if named == [TR.MARKER_NONE]:
            none_rows += 1
            if h:
                bad.append((n, "marker says (none) but held is %s" % sorted(h)))
        elif set(named) != set(h):
            bad.append((n, "marker %s != held %s" % (named, sorted(h))))
        if r.get("context"):
            bad.append((n, "row carries context; the input must be the "
                           "surface and the marker and nothing else"))

    print("    provoke rows       %d" % len(prov))
    print("    (none) rows        %d  (%.1f %%) — turns 1 and 2 of each chain"
          % (none_rows, 100 * none_rows / len(prov)))
    print("    malformed          %d" % len(bad))
    report["0d"] = {"provoke_rows": len(prov), "none_rows": none_rows,
                    "malformed": len(bad),
                    "marker_prefix": TR.MARKER_PREFIX,
                    "marker_none": TR.MARKER_NONE,
                    "example": prov[0]["prompt"],
                    "example_marked": next(
                        (r["prompt"] for r in prov
                         if not r["prompt"].endswith(TR.MARKER_NONE)), None)}
    if bad:
        for n, why in bad[:5]:
            print("      row %d: %s" % (n, why))
        raise SystemExit("\n⛔ 0d FAILED — %d malformed rows" % len(bad))
    print("    ✅ every provoke row is surface + marker, and the marker is "
          "the recomputed `held`")
    return len(prov)


# ── 0e · the reader, and the four arms' markers ────────────────────────────
#
# ⭐ `read_lag_held` IS NOT A SECOND READER. It is `read_lag` with one extra
# argument, so every guard travels unchanged: short chains dropped not counted,
# the sampling stream seeded and the success recorded, per-lag scoreability,
# `resolving_power` vs `threshold_for_lag`, and the T = 0 refusal. §0e asks for
# a wrapper that SHARES the fold; a reader that re-implemented the chain loop
# would be a second instrument that agrees with the first until it does not.

def marker_held(out, lex_r):
    """The **M** arm. The truth: the roots `t−1` and `t−2` both carry.

    ⛔ Calls `TR.held`, the same object the corpus builder was handed in 0a.
    That identity is §1's requirement and `tests/test_idf2_reader.py` asserts
    it rather than trusting that two spellings agree today.
    """
    return TR.marker_line(TR.held(out, out[-1], lex_r))


def marker_none(out, lex_r):
    """The **M-strip** arm. In-distribution shape, no information.

    ⛔⛤ NOT "REMOVE THE LINE". Removing it shows M an input shape it never
    trained on, so any movement could come from the novel shape rather than
    the missing information — the control would confound the two things it
    exists to separate. `held` is empty on turns 1 and 2 of every training
    chain, so `(none)` is a token the model has seen constantly. *(Wilson,
    2026-09-26; prereg §7.)*
    """
    return TR.marker_line(())


def marker_shuffle(seed=SEED):
    """The **M-shuffle** arm. Roots of `t−1` that are NOT held, same count.

    ⭐ The discriminating control. If the model is reading the marker rather
    than recomputing the rule, its avoidance follows the WRONGLY marked roots
    and lag-2 rises. If it ignores the marker, nothing moves.

    ⛔ The shortfall is REPORTED, never padded. When `t−1` carries fewer
    unheld roots than `held` has, the line is short — filling it from `held`
    would put true roots in the false marker and turn the control into a
    weaker copy of M.
    """
    rng = random.Random(seed)
    short = [0, 0]

    def fn(out, lex_r):
        h = TR.held(out, out[-1], lex_r)
        cands = sorted(TR.roots_of(out[-1].surface, lex_r) - h)
        k = min(len(h), len(cands))
        short[0] += 1
        short[1] += 1 if k < len(h) else 0
        return TR.marker_line(rng.sample(cands, k) if k else ())

    # ⛔ The SEED rides in the recorded name. Two shuffle arms at different
    # seeds name different roots and would otherwise write the same
    # `marker_fn` field — the row-indistinguishability this field exists to
    # prevent, one level deeper.
    fn.__qualname__ = "marker_shuffle(seed=%d)" % seed
    fn.shortfall = short
    return fn


def read_lag_held(backend, *, marker=marker_held, **kw):
    """§0e. `read_lag`'s fold, with one line added to each provoke payload."""
    from act2_model_lag import read_lag
    return read_lag(backend, marker_fn=marker, **kw)


# ── 0f ─────────────────────────────────────────────────────────────────────

#: `ct-s20624`'s adapter, which persist_ledger.json says lives here. ⛔ The
#: weights are NOT on disk locally — `adapter_ct-s20624/` holds the config, the
#: tokenizer and an optimizer state, and `checkpoint-3757/` holds no
#: safetensors either. The hub copy is the only copy.
CT_REPO = "keyzersoze04/tlon-act2-adapters"
CT_PATH = "ct-s20624/adapter_model.safetensors"

#: Qwen2.5-7B-Instruct: 28 layers × 7 target modules × 2 tensors (A and B).
#: ⛔⛔ THIS IS THE SHARD TRIPWIRE. `01_OUR_FRONTIER.md:222` records that an rms
#: computed over ONE RANK'S SHARD is "a plausible number, and nothing detects
#: it" — it corrupts the dose, which is the quantity §4 matches on. A count is
#: what detects it, so the count is asserted rather than trusted.
CT_EXPECT_TENSORS = 28 * 7 * 2


def step_0f(report, *, local=None):
    """Recompute `ct-s20624`'s `dose_w`, because nothing recorded it.

    ⛔⛔ THE GATE IN §4 POINTED AT A NUMBER THAT DOES NOT EXIST. `rms` is absent
    from `INSTANCE.json`, `factorial.json`, `persist_ledger.json` and
    `model_lag_ct-s20624.json`, and no committed tool computed it. A tolerance
    against an unrecorded reference is not a gate; it is a sentence.

    `dose_w = delta_norm / sqrt(n_trainable)`, per
    `briefs/wilson_2026_09_25/00_START_HERE.md`. For a LoRA adapter the weight
    delta of a module is `(alpha / r) · B @ A`, so `delta_norm` is the
    Frobenius norm over every module's delta — never over a subset.

    ⚠️ BOTH DENOMINATORS ARE RECORDED. `n_trainable` (the A and B entries) is
    the one the briefs name and the one `dose_w` uses; `n_delta` (the entries
    of the reconstructed ΔW) is reported beside it because the two differ by
    orders of magnitude and a later reader must be able to tell which was
    meant without re-deriving it.
    """
    import numpy as np
    from safetensors.numpy import load_file

    print("\n0f · DOSE — recomputing ct-s20624's rms, which nothing recorded")
    if local is None:
        from huggingface_hub import hf_hub_download
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        from act2_provision import _hf_token
        local = hf_hub_download(CT_REPO, CT_PATH, token=_hf_token())
    tensors = load_file(local)

    n_t = len(tensors)
    print("    tensors            %d  (expect %d)" % (n_t, CT_EXPECT_TENSORS))
    if n_t != CT_EXPECT_TENSORS:
        raise SystemExit(
            "\n⛔⛔ 0f REFUSED — %d LoRA tensors, expected %d. This is the "
            "shard hazard the count exists to catch: an rms over a subset is "
            "a plausible number that nothing else detects, and §4 matches "
            "M, C1 and W2 against it." % (n_t, CT_EXPECT_TENSORS))

    cfg = json.loads((pathlib.Path("runs/act2/retrain12_ct/adapter_ct-s20624")
                      / "adapter_config.json").read_text(encoding="utf-8"))
    scale = cfg["lora_alpha"] / cfg["r"]

    pairs, sq, n_trainable, n_delta = 0, 0.0, 0, 0
    a_of = {k[:-len("lora_A.weight")]: v for k, v in tensors.items()
            if k.endswith("lora_A.weight")}
    b_of = {k[:-len("lora_B.weight")]: v for k, v in tensors.items()
            if k.endswith("lora_B.weight")}
    # ⛔ Every A must have its B. A mismatch here is a half-read checkpoint,
    # which would under-count the delta and pass silently as a small dose.
    if set(a_of) != set(b_of):
        raise SystemExit("\n⛔ 0f REFUSED — %d lora_A vs %d lora_B; the pairing "
                         "is incomplete." % (len(a_of), len(b_of)))
    for mod, A in a_of.items():
        B = b_of[mod]
        d = scale * (B.astype(np.float64) @ A.astype(np.float64))
        sq += float((d * d).sum())
        n_trainable += A.size + B.size
        n_delta += d.size
        pairs += 1

    delta_norm = sq ** 0.5
    dose_w = delta_norm / (n_trainable ** 0.5)
    print("    modules            %d" % pairs)
    print("    scale (alpha/r)    %.4f" % scale)
    print("    delta_norm         %.6g" % delta_norm)
    print("    n_trainable        %d" % n_trainable)
    print("    n_delta            %d   (reported, NOT the denominator)"
          % n_delta)
    print("    ⭐ dose_w (rms)     %.6g" % dose_w)
    band = (dose_w * 0.95, dose_w * 1.05)
    print("    §4 band ±5 %%       [%.6g, %.6g]" % band)
    report["0f"] = {"source": "hf://%s/%s" % (CT_REPO, CT_PATH),
                    "tensors": n_t, "modules": pairs, "scale": scale,
                    "delta_norm": delta_norm, "n_trainable": n_trainable,
                    "n_delta": n_delta, "dose_w": dose_w,
                    "band_5pct": list(band)}
    return dose_w


# ── driver ─────────────────────────────────────────────────────────────────

def cmd_step0(a):
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"prereg": "docs/PREREG_IDF2_2026_09_26.md",
              "LOCK": "37363296", "seed": SEED}
    print("=" * 72)
    print("IDF-2 STEP 0 — CPU precondition gate · prereg LOCK 37363296")
    print("=" * 72)

    chains, prof = step_0a(report)
    gap, blind2, corpus2 = step_0bc(report, prof[2])
    step_0d(report, chains)

    print("\n" + "=" * 72)
    print("STEP 0 SUMMARY")
    print("=" * 72)
    print("  0a corpus   %s · lag-1 %.4f · lag-2 %.4f"
          % (report["0a"]["verdict"], prof[1], prof[2]))
    print("  0c blind    lag-2 %.4f     ← 0 %% anchor" % blind2)
    print("  0a corpus   lag-2 %.4f     ← 100 %% anchor" % corpus2)
    print("  0b oracle   lag-2 %.4f · shortfall %+.4f  (red-proof, NOT an "
          "anchor)" % (report["0b"]["marker_lag_profile"][2],
                       report["0b"]["shortfall"]))
    print("  gap         %.4f" % gap)
    print("\n  ⭐ In §6's units, 15 points = %.4f raw lag-2, 35 points = %.4f"
          % (blind2 - 0.15 * gap, blind2 - 0.35 * gap))

    p = OUT / "step0.json"
    p.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("\n  wrote %s" % p)
    return 0


def cmd_rms(a):
    """0f on its own — it needs the hub, so it is separable from 0a-0c."""
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "step0.json"
    report = (json.loads(p.read_text(encoding="utf-8")) if p.exists()
              else {"prereg": "docs/PREREG_IDF2_2026_09_26.md",
                    "LOCK": "37363296", "seed": SEED})
    step_0f(report, local=a.local)
    p.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("\n  wrote %s" % p)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("step0", help="0a..0c, in order, one report")
    f = sub.add_parser("rms", help="0f — recompute ct-s20624's dose_w")
    f.add_argument("--local", help="a local safetensors, instead of the hub")
    a = ap.parse_args(argv)
    return {"step0": cmd_step0, "rms": cmd_rms}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
