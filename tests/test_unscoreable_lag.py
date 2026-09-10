"""⛔⛔ RED-PROOF: "THE SPEAKER EMITTED NOTHING SCOREABLE" IS A DIAGNOSIS.

Run 0 (`e91f7c11`) trained cleanly, persisted 17.42 GB to the hub, and then died
inside the instrument:

    transient.py  permutation_null
    means.append(sum(len(x & y) for x, y in zip(a, b)) / len(a))
    ZeroDivisionError            # len(a) == 0 -- the chain set is EMPTY

A chain of n turns holds n-lag pairs. The mapping run at 5e-6 was degenerate
enough that no chain survived long enough to hold a pair at the longer lags, so
that cell was empty and the null divided by its length. ⛔ The traceback said
INSTRUMENT; the truth was SPEAKER.

⛔⛔ AND THE OBVIOUS FIX IS THE DANGEROUS ONE. Returning `nan` would not crash --
it would flow into `z`, where `nan >= 6.0` and `nan <= 3.0` are both False. An
unmeasurable lag would then render as "perceive collapsed" or "release
persists": a fabricated finding with a threshold attached. So the tests below
check three separate things, and the middle one is the load-bearing one:

  1. the empty cell raises a NAMED diagnosis carrying the counts
  2. NO consumer can turn that diagnosis into a pass OR into an axis failure
  3. the pipeline HALTS on it instead of buying a second epoch

⭐ Guarded at the level of "what does a degenerate speaker do to each consumer",
not "does permutation_null check its denominator" -- the second is one line and
the first is what actually cost the run.
"""
from __future__ import annotations

import importlib.util
import pathlib
import random
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

from tlon.discourse import transient as TR                       # noqa: E402
from tlon.discourse.multiturn import MultiturnError              # noqa: E402

import act2_model_lag as ML                                      # noqa: E402


LEX = {"fang", "flux", "kor", "vash"}


class _T:
    """Duck-types a turn for the shared instrument: only `.surface` is read."""

    def __init__(self, surface):
        self.surface = surface


def _chain(n):
    """An n-turn chain. ⭐ Content is irrelevant here; LENGTH is the variable."""
    words = ["fang kor", "flux vash", "kor vash", "fang flux"]
    return [_T(words[i % len(words)]) for i in range(n)]


def _v():
    p = _ROOT / "tools" / "act2_fullft_verdict.py"
    spec = importlib.util.spec_from_file_location("_v_unscoreable", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── 1 · the diagnosis exists and carries its evidence ───────────────────────

def test_an_empty_cell_raises_a_NAMED_diagnosis_not_ZeroDivisionError():
    """⛔⛔ THE RUN-0 CRASH, REPRODUCED. Three 3-turn chains hold zero lag-4
    pairs, which is exactly the state the mapping run reached."""
    chains = [_chain(3) for _ in range(3)]
    assert TR.lag_pairs(chains, lag=4) == 0
    with pytest.raises(TR.UnscoreableLag) as exc:
        TR.permutation_null(chains, lag=4, shuffles=10,
                            rng=random.Random(0), lex_r=LEX)
    # ⭐ The counts travel WITH the diagnosis. "Unscoreable" without the chain
    # lengths cannot distinguish "the model died" from "we asked for lag 4 on
    # 3-turn chains", and those prescribe different next actions.
    assert exc.value.lag == 4
    assert exc.value.n_pairs == 0
    assert exc.value.n_chains == 3
    assert exc.value.n_turns == 9
    assert exc.value.lengths == [3, 3, 3]
    assert "SPEAKER" in str(exc.value)


def test_the_diagnosis_is_a_MultiturnError_so_existing_handlers_see_it():
    """⭐ The corpus-side callers already catch `MultiturnError` and turn it into
    a refusal. Subclassing means none of them silently pass an empty cell."""
    assert issubclass(TR.UnscoreableLag, MultiturnError)


def test_no_chains_at_all_is_the_SAME_diagnosis():
    """⛔ No chains means no pairs; a second code path would be a second thing
    to forget."""
    with pytest.raises(TR.UnscoreableLag):
        TR.permutation_null([], lag=1, shuffles=10,
                            rng=random.Random(0), lex_r=LEX)


def test_a_scoreable_cell_is_UNTOUCHED_by_the_guard():
    """⛔⛔ THE GUARD MUST NOT CHANGE A SINGLE MEASURED NUMBER. A refusal that
    also perturbs the working path would silently re-baseline every lag profile
    this run is compared against."""
    chains = [_chain(8) for _ in range(4)]
    mu, sd = TR.permutation_null(chains, lag=2, shuffles=40,
                                 rng=random.Random(11), lex_r=LEX)
    mu2, sd2 = TR.permutation_null(chains, lag=2, shuffles=40,
                                   rng=random.Random(11), lex_r=LEX)
    assert (mu, sd) == (mu2, sd2)
    assert sd > 0


def test_lag_profile_and_lag_pairs_CANNOT_disagree():
    """⭐ The two functions disagreeing about which cells exist is what let a
    `nan` cell sit beside a division by that cell's zero length. `lag_profile`
    asserts the agreement, so a future edit to either one fails loudly."""
    chains = [_chain(3), _chain(7), _chain(4)]
    prof = TR.lag_profile(chains, max_lag=8, lex_r=LEX)
    # ⭐ The correspondence, swept — a value EXACTLY where pairs exist, `nan`
    # exactly where they do not. Only the 7-turn chain reaches lag 4 (3 pairs);
    # nothing reaches lag 7.
    assert TR.lag_pairs(chains, lag=4) == 3
    assert TR.lag_pairs(chains, lag=7) == 0
    for k in range(1, 9):
        n = TR.lag_pairs(chains, lag=k)
        is_nan = prof[k] != prof[k]
        assert is_nan == (n == 0), \
            "lag %d: n_pairs=%d but profile nan=%s" % (k, n, is_nan)
        if n == 0:
            with pytest.raises(TR.UnscoreableLag):
                TR.permutation_null(chains, lag=k, shuffles=5,
                                    rng=random.Random(0), lex_r=LEX)


# ── 1b · ⛔⛔ n_pairs > 0 WAS THE SAME TOO-WEAK THRESHOLD ───────────────────
#
# Closing the n=0 hole moved the probability onto n=1. Run 0's re-read scored
# lag 3 from ONE pair and fed z=+0.253 to `release_ok = all(v <= 3.0)` as a
# number. `n_pairs > 0` is `changed > 0` wearing different clothes.
#
# ⭐ The bar is DERIVED, never picked: the null's sd is the spread of a MEAN
# over n pairs, so it falls like sigma/sqrt(n). A cell is scoreable only if the
# highest z it can physically emit reaches the LOCKED threshold it would be
# judged against.


def test_the_threshold_is_the_LOCKED_one_not_a_new_constant():
    """⛔⛔ Inventing `n >= 20` would be the freeze_procedure sin. The bar here
    is Z_LAG1_MIN and Z_LAGN_MAX, imported, and the quantity compared against it
    is measured from the run's own null."""
    assert TR.threshold_for_lag(1) is TR.Z_LAG1_MIN
    for lag in (2, 3, 4):
        assert TR.threshold_for_lag(lag) is TR.Z_LAGN_MAX


def test_max_attainable_profile_is_the_min_of_the_two_root_counts():
    """⭐ Two turns can share at most min(|a|, |b|) roots — measured from the
    chains, never assumed."""
    chains = [[_T("fang kor"), _T("flux"), _T("kor vash")]]
    # lag 2: pair (fang kor, kor vash) -> min(2, 2) = 2
    assert TR.max_attainable_profile(chains, lag=2, lex_r=LEX) == 2.0
    # lag 1: (fang kor, flux) -> min(2,1)=1 ; (flux, kor vash) -> min(1,2)=1
    assert TR.max_attainable_profile(chains, lag=1, lex_r=LEX) == 1.0


def test_resolving_power_is_just_the_z_of_the_maximum_attainable_profile():
    """⭐ Same null, same formula, no new machinery — which is what makes it a
    derivation rather than a second instrument."""
    chains = [_chain(8) for _ in range(4)]
    mu, sd = TR.permutation_null(chains, lag=2, shuffles=60,
                                 rng=random.Random(5), lex_r=LEX)
    top = TR.max_attainable_profile(chains, lag=2, lex_r=LEX)
    assert TR.resolving_power(chains, lag=2, lex_r=LEX, mu=mu, sd=sd) == \
        (top - mu) / sd


def test_a_TINY_cell_cannot_reach_its_threshold_and_a_LARGE_one_can():
    """⛔⛔ THE CLIFF, MEASURED. Run 0 kept 2 chains of [3, 4]; rung 2 kept 6 of
    ~5; rung 1b′ kept 12 of 10. The first cannot reach either threshold and the
    other two clear both."""
    def power(nch, ln, lag):
        r = random.Random(7)
        words = ["fang kor", "flux vash", "kor vash", "fang flux"]
        ch = [[_T(r.choice(words)) for _ in range(ln)] for _ in range(nch)]
        mu, sd = TR.permutation_null(ch, lag=lag, shuffles=300,
                                     rng=random.Random(1), lex_r=LEX)
        return TR.resolving_power(ch, lag=lag, lex_r=LEX, mu=mu, sd=sd)

    assert power(2, 4, 1) < TR.Z_LAG1_MIN         # Run 0 shaped
    assert power(2, 4, 2) < TR.Z_LAGN_MAX
    assert power(6, 5, 1) >= TR.Z_LAG1_MIN        # rung 2 shaped
    assert power(12, 10, 2) >= TR.Z_LAGN_MAX      # rung 1b′ shaped


def test_the_SMALL_CELL_BIAS_RUNS_IN_A_FIXED_DIRECTION():
    """⛔⛔ THE REASON THIS IS A GUARD AND NOT A NICETY.

    `sd` is the spread of a MEAN over n pairs, so it falls like sigma/sqrt(n).
    A small cell therefore yields a SMALL z whatever the speaker did — and the
    two axes read a small z in OPPOSITE directions:

        lag 1   PASS is z >= 6.0  -> a tiny cell can never pass -> fabricated
                                     "perceive collapsed"
        lag >=2 PASS is z <= 3.0  -> a tiny cell can never fail -> vacuous
                                     "release passed"

    Together those spell §4.2 row (d), which is exactly the verdict a degenerate
    speaker would have received for reasons of arithmetic.
    """
    r = random.Random(3)
    words = ["fang kor", "flux vash", "kor vash", "fang flux"]
    small = [[_T(r.choice(words)) for _ in range(4)] for _ in range(2)]
    big = [[_T(r.choice(words)) for _ in range(10)] for _ in range(12)]

    def sd_of(ch, lag):
        return TR.permutation_null(ch, lag=lag, shuffles=300,
                                   rng=random.Random(1), lex_r=LEX)[1]

    # ⭐ The mechanism itself: a smaller cell has a WIDER null.
    assert sd_of(small, 1) > sd_of(big, 1)
    # ⛔ And so the ceiling on |z| is lower — perceive cannot clear its floor...
    assert TR.resolving_power(small, lag=1, lex_r=LEX,
                              mu=TR.permutation_null(small, lag=1, shuffles=300,
                                                     rng=random.Random(1),
                                                     lex_r=LEX)[0],
                              sd=sd_of(small, 1)) < TR.Z_LAG1_MIN
    # ... and release cannot breach its ceiling, so it "passes" vacuously.
    assert TR.resolving_power(small, lag=2, lex_r=LEX,
                              mu=TR.permutation_null(small, lag=2, shuffles=300,
                                                     rng=random.Random(1),
                                                     lex_r=LEX)[0],
                              sd=sd_of(small, 2)) < TR.Z_LAGN_MAX


def test_zero_spread_resolves_nothing():
    """⛔ The safe direction. A null with no spread places nothing."""
    assert TR.resolving_power([_chain(6)], lag=1, lex_r=LEX,
                              mu=0.5, sd=0.0) == 0.0


def test_the_fired_runs_REMAIN_resolvable():
    """⛔⛔ THE CONTAINMENT CHECK. This rule changes a verdict rule, so it must
    not retroactively unmake the arc's standing results. Computed from each
    run's OWN stored null at the most conservative ceiling (R_max = 2 roots,
    the corpus surface width): rung 1b′ clears its bar by 41.8-49.0 and rung 2
    by 8.1-13.7, against thresholds of 3.0 and 6.0.
    """
    import json
    cases = [
        ("runs/act2/fullft_fw19b-s20624/model_lag_fw19b-s20624_e1.json", 41.7),
        ("runs/act2/fullft_fwmap-s20624/model_lag_fwmap-s20624_e1.json", 8.1),
    ]
    for path, floor in cases:
        p = _ROOT / path
        if not p.exists():                                  # pragma: no cover
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        for k, null in (d["null"] or {}).items():
            z_max = (2.0 - null["mean"]) / null["sd"]
            need = TR.threshold_for_lag(int(k))
            assert z_max >= need, "%s lag%s became unresolvable" % (path, k)
            assert z_max >= floor


# ── 2 · ⛔⛔ NO CONSUMER MAY TURN IT INTO A NUMBER ───────────────────────────

@pytest.mark.parametrize("blind_value", [None, float("nan")])
def test_an_unscoreable_lag_is_NOT_a_release_failure(blind_value):
    """⛔⛔ THE LOAD-BEARING TEST. `None <= 3.0` raises and `nan <= 3.0` is
    False, so the naive verdict tool would report "content persists" — a
    substantive finding — for a lag NOBODY MEASURED."""
    v = _v()
    lag = {"z": {"1": 20.0, "2": 1.0, "3": blind_value},
           "n_pairs": {"1": 30, "2": 20, "3": 0},
           "object_kind": "full_weight"}
    out = v.decide({"verdict": "OK", "fraction_changed": 0.99},
                   lag, {"fired": False}, prereg="0" * 8)
    assert out["verdict"] == v.NO_VERDICT
    assert out["unscoreable_lags"] == [3]
    assert out.get("axes_not_computed") is True
    # ⛔ No axis may carry a PASS or a FAIL when nothing was measured.
    assert "axes" not in out


@pytest.mark.parametrize("blind_value", [None, float("nan")])
def test_an_unscoreable_lag1_is_NOT_a_perceive_failure(blind_value):
    """⛔ `nan >= 6.0` is False, which reads as "collapsed toward content-free" —
    the (d) row — for a speaker that was never scored at all."""
    v = _v()
    lag = {"z": {"1": blind_value, "2": 1.0}, "n_pairs": {"1": 0, "2": 0},
           "object_kind": "full_weight"}
    out = v.decide({"verdict": "OK", "fraction_changed": 0.99},
                   lag, {"fired": False}, prereg="0" * 8)
    assert out["verdict"] == v.NO_VERDICT
    assert out["verdict"] != v.STOP_PERCEIVE


def test_NO_VERDICT_is_distinct_from_INSTRUMENT_FAULT():
    """⛔ §4.1's fault means the WEIGHTS did not move. This means the weights
    moved and the resulting speaker said nothing scoreable. Same halt, different
    finding, and merging them would lose which one happened."""
    v = _v()
    assert v.NO_VERDICT != v.FAULT
    assert v.NO_VERDICT not in (v.GO, v.STOP_FLOORED, v.STOP_CRATERED,
                                v.STOP_PERCEIVE, v.STOP_INCOHERENT)


def test_NO_VERDICT_is_never_a_readable_stop():
    """⛔ `readable_stop` decides what is worth PROTECTING from epoch 2. There is
    nothing to protect here."""
    v = _v()
    assert v.readable_stop({"verdict": v.NO_VERDICT,
                            "axes": {"perceive": {"ok": True},
                                     "f_local": {"ok": True}}}) is False


def test_the_precondition_still_runs_FIRST():
    """⛔⛔ §4.1 outranks everything. A run whose weights did not move must read
    INSTRUMENT FAULT even if its lags are also unscoreable — otherwise the
    unscoreable branch would mask the precondition."""
    v = _v()
    lag = {"z": {"1": None, "2": None}, "object_kind": "full_weight"}
    out = v.decide({"verdict": "INSTRUMENT FAULT", "fraction_changed": 0.0},
                   lag, {"fired": False}, prereg="0" * 8)
    assert out["verdict"] == v.FAULT


def test_a_fully_scoreable_run_is_unchanged_by_all_of_this():
    """⛔⛔ THE REGRESSION GUARD. Every fired run's verdict must be exactly what
    it was, or this change silently re-reads the whole arc."""
    v = _v()
    d = {"verdict": "OK", "fraction_changed": 0.99}
    good = {"z": {"1": 20.0, "2": 1.0, "3": 0.5}, "object_kind": "full_weight"}
    assert v.decide(d, good, {"fired": False}, prereg="0" * 8)["verdict"] == v.GO
    # rung 1a/1b/1b': release fails, perceive and f_local hold -> floored
    floored = {"z": {"1": 24.046, "2": 5.785}, "object_kind": "full_weight"}
    assert v.decide(d, floored, {"fired": False},
                    prereg="0" * 8)["verdict"] == v.STOP_FLOORED
    # rung 2: perceive collapsed
    killed = {"z": {"1": 2.232, "2": 0.681}, "object_kind": "full_weight"}
    assert v.decide(d, killed, {"fired": True},
                    prereg="0" * 8)["verdict"] == v.STOP_PERCEIVE


# ── 3 · the pipeline must HALT, not train more ──────────────────────────────

def test_the_pipeline_branches_on_exit_5_BEFORE_the_epoch_2_else():
    """⛔⛔ WITHOUT ITS OWN BRANCH, EXIT 5 FALLS INTO `else` — WHICH RUNS EPOCH 2.

    That branch's rule is "epoch 1 left no readable state to protect", which is
    true of a FAILED axis and false of an UNMEASURED one. A degenerate speaker
    does not become scoreable by training it further, so the default path would
    buy a second epoch to reproduce the same non-result.
    """
    src = (_ROOT / "tools" / "pipeline_fullft.sh").read_text(encoding="utf-8")
    guard = src.index("$E1 -eq 5")
    else_branch = src.index("epoch 1 is NOT READABLE")
    assert guard < else_branch, \
        "the exit-5 branch must precede the epoch-2 fallthrough"
    tail = src[guard:else_branch]
    assert "exit 1" in tail, "exit 5 must HALT the pipeline"


def test_the_verdict_tool_returns_5_for_an_unscoreable_read(tmp_path, monkeypatch):
    """⭐ The exit code is the pipeline's only channel. Asserted through `main`,
    not by reading the constant — the branch is what the shell sees."""
    v = _v()
    delta = tmp_path / "d.json"
    lag = tmp_path / "l.json"
    ledger = tmp_path / "ledger.jsonl"
    out = tmp_path / "o.json"
    prereg = tmp_path / "PREREG.md"

    import json
    delta.write_text(json.dumps({"verdict": "OK", "fraction_changed": 0.99}))
    lag.write_text(json.dumps({"z": {"1": 20.0, "2": None},
                               "n_pairs": {"1": 12, "2": 0},
                               "object_kind": "full_weight"}))
    ledger.write_text(json.dumps({"event": "f_local", "fired": False}) + "\n")
    prereg.write_text("LOCK `00000000`\n", encoding="utf-8")

    monkeypatch.setattr(v, "verified_prereg_id", lambda p: "0" * 8)
    monkeypatch.setattr(sys, "argv",
                        ["act2_fullft_verdict.py", "--delta", str(delta),
                         "--lag", str(lag), "--ledger", str(ledger),
                         "--out", str(out), "--prereg", str(prereg)])
    assert v.main() == 5
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["verdict"] == v.NO_VERDICT


# ── 4 · the model-side tool records rather than crashes ─────────────────────

def test_the_lag_tool_imports_the_diagnosis_it_handles():
    """⛔ Caught by name, from the one module that defines it."""
    assert ML.UnscoreableLag is TR.UnscoreableLag
    assert ML.lag_pairs is TR.lag_pairs


def test_the_tool_scores_what_it_can_and_names_what_it_cannot():
    """⭐⭐ PER-LAG. Run 0 lost lag 1 and lag 2 — which WERE scoreable — to the
    lag that was not. A partial read is worth strictly more than a traceback."""
    chains = [_chain(3) for _ in range(4)]
    rng = random.Random(3)
    zs, npairs, unscoreable = {}, {}, {}
    for k in range(1, 5):
        npairs[k] = TR.lag_pairs(chains, lag=k)
        try:
            mu, sd = TR.permutation_null(chains, lag=k, shuffles=20,
                                         rng=rng, lex_r=LEX)
        except TR.UnscoreableLag as exc:
            zs[k], unscoreable[k] = None, str(exc)
            continue
        zs[k] = 0.0 if not sd else 1.0
    assert npairs == {1: 8, 2: 4, 3: 0, 4: 0}
    assert sorted(unscoreable) == [3, 4]
    assert zs[1] is not None and zs[2] is not None


def test_the_TOOL_ACTUALLY_APPLIES_the_derived_bar():
    """⛔⛔ A GUARD THE CONSUMER IGNORES IS NOT A GUARD.

    Every other test here exercises `transient.py` directly, so deleting the
    check from `act2_model_lag.py` left the whole suite GREEN — found by
    injecting exactly that. It is the same class as the pipeline's missing
    exit-5 arm: the verdict was right and the thing downstream walked past it.
    """
    from textguard import code_only
    src = code_only((_ROOT / "tools" / "act2_model_lag.py")
                    .read_text(encoding="utf-8"))
    assert "resolving_power(chains, lag=k" in src, \
        "the tool never computes the cell's ceiling"
    assert "threshold_for_lag(k)" in src, \
        "the tool never asks what bar the cell is judged against"
    # ⛔ Computing it and not branching on it is the same as not computing it.
    assert "if power < need:" in src
    branch = src[src.index("if power < need:"):]
    branch = branch[:branch.index("continue")]
    assert "zs[k], nulls[k] = None" in branch, \
        "an unresolvable lag must be recorded as None, never as a number"


def test_the_report_carries_n_pairs_beside_every_z():
    """⭐⭐ THE CAVEAT IN THE FIELD. Rung 2's lag-4 z=-0.48 came off roughly
    EIGHT pairs carried by whichever two chains ran long, and nothing in the
    artifact said so. A z without its cell size cannot be weighed."""
    src = (_ROOT / "tools" / "act2_model_lag.py").read_text(encoding="utf-8")
    assert '"n_pairs": npairs' in src
    assert '"unscoreable_lags"' in src


def test_the_sampling_stream_is_SEEDED_and_the_report_says_so():
    """⛔⛔ `--seed` NAMED A SEED THAT DID NOT CONTROL THE READ. `do_sample=True`
    at temperature 0.70 draws from the torch global RNG, and nothing seeded it —
    `--seed` reached only the seed surfaces and the permutation null. Every lag
    profile in this arc is one undocumented draw sitting beside a field called
    `seed`.

    ⭐ Chain LENGTH is exactly what that randomness moves, and chain length is
    what decides whether a cell is scoreable at all. So the unseeded stream and
    the empty cell are the same story told twice.
    """
    src = (_ROOT / "tools" / "act2_model_lag.py").read_text(encoding="utf-8")
    assert "torch.manual_seed(a.seed)" in src
    assert "torch.cuda.manual_seed_all(a.seed)" in src
    # ⛔ And the claim must be the honest one: seeding fixes WHICH draw, it does
    # not promise bit-reproducibility across GPUs or kernel versions.
    assert '"sampling_stream_seeded": torch_seeded' in src
    assert "reproducible" not in src.lower().split("torch_seeded = False")[0][-1200:]


def test_seeding_happens_BEFORE_any_generation():
    """⛔ A seed set after the first chain is generated seeds nothing that
    matters. Position is the whole guarantee."""
    src = (_ROOT / "tools" / "act2_model_lag.py").read_text(encoding="utf-8")
    seeded = src.index("torch.manual_seed(a.seed)")
    first_gen = src.index("raw = model_chain(backend, s, turns=a.turns)")
    assert seeded < first_gen


def test_UNSCOREABLE_is_not_filed_as_REFUSED():
    """⛔ A refusal is the gate saying the corpus FAILED a criterion it could
    measure. Collapsing the two would file a speaker that emitted nothing under
    the same verdict as one that emitted the wrong thing."""
    src = (_ROOT / "tools" / "act2_model_lag.py").read_text(encoding="utf-8")
    i = src.index("if unscoreable:")
    j = src.index("check_transience(chains", i)
    assert 'verdict = "UNSCOREABLE"' in src[i:j]
    assert '"REFUSED"' not in src[i:j]
