"""⛔⛔ RED-PROOF FOR THE FACTORIAL'S BOOKKEEPING.

An adapter that cannot say which cell it is in belongs to no contrast, and the
army degrades into a pile the moment the terminal scrollback is gone. The guards
here are the ones whose absence is silent:

  * a MISSING generator label must mean LEGACY, never matched -- otherwise every
    adapter whose pairing is UNKNOWN gets filed as the ones whose pairing is BEST;
  * pairing is a property of the PAIR, so one legacy side makes the whole pair
    seed-only;
  * a seed present in only one arm is not a pair and must not be counted as one.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from tlon.act2.factorial import (FactorialError, adapter_label,  # noqa: E402
                                 check_balanced, entry, generator_of,
                                 pair_regimes, pairing_regime, recipe_of,
                                 unpaired)
from tlon.discourse.transient import (CONTENT_FREE,               # noqa: E402
                                      CONTENT_TRANSIENT,
                                      GENERATOR_LEGACY,
                                      GENERATOR_SPLIT_STREAM,
                                      PAIRED_SEED_AND_FORCE,
                                      PAIRED_SEED_ONLY)

FRESH = {"recipe": CONTENT_TRANSIENT, "generator": GENERATOR_SPLIT_STREAM}
LEGACY = {"recipe": CONTENT_FREE}          # no `generator` field at all


def e(recipe, seed, *, fresh=True):
    return entry("a%d" % seed, recipe=recipe, seed=seed,
                 generator=GENERATOR_SPLIT_STREAM if fresh else GENERATOR_LEGACY)


# ── 1 · ⛔⛔ the missing-field trap ─────────────────────────────────────────

def test_a_MISSING_generator_field_means_LEGACY_not_matched():
    """⛔⛔ THE VACUOUS PASS. Every corpus built before the split-stream path has
    no `generator` field. Defaulting it to the split-stream id would take the
    adapters whose pairing is UNKNOWN and file them as the BEST-paired ones."""
    assert generator_of({}) == GENERATOR_LEGACY
    assert generator_of(LEGACY) == GENERATOR_LEGACY
    assert generator_of({"generator": None}) == GENERATOR_LEGACY
    assert generator_of(FRESH) == GENERATOR_SPLIT_STREAM


def test_a_missing_recipe_RAISES_rather_than_being_guessed():
    """⛔ An adapter whose recipe is unknown belongs to no cell. Guessing places
    it in a contrast it was never part of."""
    with pytest.raises(FactorialError, match="recipe"):
        recipe_of({})
    with pytest.raises(FactorialError, match="recipe"):
        recipe_of({"recipe": "content-ish"})
    assert recipe_of(FRESH) == CONTENT_TRANSIENT


# ── 2 · ⛔⛔ pairing is a property of the PAIR ─────────────────────────────

def test_ONE_legacy_side_makes_the_WHOLE_pair_seed_only():
    """⛔⛔ THE WORST OF THE SIDES, NOT THE BEST. The legacy side's force
    sequence was perturbed by its own content draws, so it does not match its
    partner's no matter how the partner was built."""
    assert pairing_regime(FRESH, FRESH) == PAIRED_SEED_AND_FORCE
    assert pairing_regime(FRESH, LEGACY) == PAIRED_SEED_ONLY
    assert pairing_regime(LEGACY, FRESH) == PAIRED_SEED_ONLY
    assert pairing_regime(LEGACY, LEGACY) == PAIRED_SEED_ONLY


def test_a_single_side_is_reported_CONSERVATIVELY():
    assert pairing_regime(LEGACY) == PAIRED_SEED_ONLY


def test_a_side_entry_never_claims_to_BE_a_pair_regime():
    """⛔ The field is named `pairing_capability_side` on purpose: a lone adapter
    cannot have a pair regime, and a field called `pairing_regime` on one
    adapter would be read as the pair's."""
    row = e(CONTENT_TRANSIENT, 20624)
    assert "pairing_capability_side" in row
    assert "pairing_regime" not in row


def test_pairing_requires_manifests():
    with pytest.raises(FactorialError):
        pairing_regime()


# ── 3 · a seed in one arm is not a pair ───────────────────────────────────

def test_a_seed_present_in_only_ONE_arm_is_NOT_counted_as_a_pair():
    """⛔⛔ Counting it would inflate the matched-cell count with contrasts that
    do not exist."""
    rows = [e(CONTENT_FREE, 1), e(CONTENT_FREE, 2), e(CONTENT_TRANSIENT, 1)]
    assert set(pair_regimes(rows)) == {1}
    assert unpaired(rows)[CONTENT_FREE] == [2]


def test_pair_regimes_marks_a_legacy_backed_pair_as_seed_only():
    rows = [e(CONTENT_FREE, 20624, fresh=False), e(CONTENT_TRANSIENT, 20624)]
    assert pair_regimes(rows) == {20624: PAIRED_SEED_ONLY}


def test_pair_regimes_marks_a_fresh_pair_as_matched():
    rows = [e(CONTENT_FREE, 20624), e(CONTENT_TRANSIENT, 20624)]
    assert pair_regimes(rows) == {20624: PAIRED_SEED_AND_FORCE}


# ── 4 · the balance gate refuses an unanalysable matrix ───────────────────

def test_an_EMPTY_ledger_is_REFUSED():
    """⛔⛔ `all([])` is True. An empty factorial is indistinguishable from one
    whose entries were never recorded."""
    with pytest.raises(FactorialError, match="no adapters"):
        check_balanced([])


def test_a_ONE_ARMED_factorial_is_REFUSED():
    with pytest.raises(FactorialError, match="ARM EMPTY"):
        check_balanced([e(CONTENT_FREE, 1), e(CONTENT_FREE, 2)])


def test_BOTH_ARMS_BUT_NO_SHARED_SEED_is_REFUSED():
    """⛔⛔ The subtle one: both arms are populated, the counts even look
    balanced, and yet every contrast changes recipe AND identity at once."""
    rows = [e(CONTENT_FREE, 1), e(CONTENT_FREE, 2),
            e(CONTENT_TRANSIENT, 3), e(CONTENT_TRANSIENT, 4)]
    with pytest.raises(FactorialError, match="NO MATCHED SEEDS"):
        check_balanced(rows)


def test_a_balanced_matrix_PASSES_and_reports_both_regimes():
    """⛔ Non-vacuity, plus the report the analysis actually needs: which seeds
    are low-variance matched pairs and which are the higher-variance ones."""
    rows = [e(CONTENT_FREE, 20624, fresh=False), e(CONTENT_TRANSIENT, 20624),
            e(CONTENT_FREE, 20625), e(CONTENT_TRANSIENT, 20625)]
    rep = check_balanced(rows)
    assert rep["pairs"] == 2
    assert rep["matched_seeds"] == [20625]
    assert rep["seed_only_seeds"] == [20624]
    assert rep["n_by_recipe"] == {CONTENT_FREE: 2, CONTENT_TRANSIENT: 2}


# ── 5 · the cell is in the name ───────────────────────────────────────────

def test_the_adapter_label_carries_recipe_AND_seed():
    """⛔ `adapter_s20624` cannot say which arm it is in."""
    assert adapter_label(CONTENT_TRANSIENT, 20624) == "ct-s20624"
    assert adapter_label(CONTENT_FREE, 20624) == "cf-s20624"
    assert adapter_label(CONTENT_TRANSIENT, 20624) != \
        adapter_label(CONTENT_FREE, 20624)


def test_an_unknown_recipe_cannot_produce_a_label():
    with pytest.raises(FactorialError):
        adapter_label("content-ish", 1)


def test_the_ledger_entry_carries_every_field_the_matrix_is_rebuilt_from():
    row = entry("s20624", recipe=CONTENT_TRANSIENT, seed=20624, manifest=FRESH)
    for k in ("name", "recipe", "seed", "cell", "generator",
              "pairing_capability_side", "factorial_pair_key"):
        assert k in row, k
    assert row["generator"] == GENERATOR_SPLIT_STREAM
    assert row["factorial_pair_key"] == "seed20624"


def test_an_entry_built_from_an_UNLABELLED_manifest_is_legacy():
    """⛔⛔ The missing-field trap, one level up — at the point the ledger is
    actually written."""
    row = entry("s20624", recipe=CONTENT_FREE, seed=20624, manifest={})
    assert row["generator"] == GENERATOR_LEGACY
    assert row["pairing_capability_side"] == PAIRED_SEED_ONLY


# ── 6 · ⛔⛔ the stamper: corpus seed is not the adapter's name ─────────────

def _stamper():
    sys.path.insert(0, str(_ROOT / "tools"))
    import act2_stamp_factorial as S
    return S


def needs_artefact(*rel):
    """⛔⛔ SKIP, DO NOT FAIL, WHEN A GITIGNORED RUN ARTEFACT IS ABSENT.

    Corpora under `runs/act2/` are gitignored, so they exist on this laptop and
    NOT on a fresh clone — which is exactly what a rented box has. Two tests
    below read real corpus directories, passed here for months, and **failed on
    the box** at the `tests` floor stage of `pipeline_solo_regen.sh` — before the
    watchdog arms, so the box sat idle and billing with no guard.

    ⭐ THE LESSON IS THE HERMETIC ONE: the suite was verified in the environment
    that has the artefacts, and the target environment is the one that does not.
    A floor that depends on un-cloned state is not a floor, it is a local
    coincidence. These assertions are still worth making where the data exists,
    so they skip with a reason that names the file rather than being deleted.
    """
    missing = [r for r in rel if not (_ROOT / r).exists()]
    return pytest.mark.skipif(
        bool(missing),
        reason="needs gitignored run artefact(s) %s — absent on a fresh clone"
               % ", ".join(missing))


def test_the_pair_key_is_the_CORPUS_seed_not_the_TRAINER_seed():
    """⛔⛔ `pipeline_variance_decompose.sh` builds ONE corpus at seed 20620 and
    trains t30001/2/3 on it; 30001-3 vary the TRAINER only. Keying the pair on
    the adapter's name would look tidy and would pair those three with nothing
    that exists."""
    S = _stamper()
    for name in ("t30001", "t30002", "t30003"):
        _dir, corpus_seed = S.corpus_for(name, "runs/act2/var_decomp/adapter_" + name)
        assert corpus_seed == 20620, (name, corpus_seed)
        assert S.seed_of(name) != corpus_seed, \
            "the trainer seed and corpus seed are being conflated"


@needs_artefact("runs/act2/recipe_var/corpus_s20621/train.jsonl")
def test_the_conventional_case_uses_its_own_seed():
    S = _stamper()
    _dir, corpus_seed = S.corpus_for(
        "s20621", "runs/act2/recipe_var/adapter_s20621")
    assert corpus_seed == 20621


@needs_artefact("runs/act2/ki_target/corpus_bfresh/train.jsonl")
def test_a_STALE_alias_is_REFUSED_by_its_recorded_sha(monkeypatch):
    """⛔⛔ An alias points one adapter at another's corpus. If the file it names
    is not the file the pipeline recorded, attributing that corpus's recipe to
    this adapter is a fabricated measurement."""
    S = _stamper()
    monkeypatch.setitem(S.ALIAS_EXPECT_SHA256,
                        "runs/act2/ki_target/corpus_bfresh", "0" * 64)
    with pytest.raises(SystemExit, match="ALIAS SHA MISMATCH"):
        S.corpus_for("t30001", "runs/act2/var_decomp/adapter_t30001")


def test_an_adapter_with_no_corpus_returns_no_dir_rather_than_guessing():
    S = _stamper()
    d, _seed = S.corpus_for("zzz999", "runs/act2/nowhere/adapter_zzz999")
    assert d is None


# ── the DOSE ARM is quarantined by construction ────────────────────────────

def test_a_DOSE_ARM_gets_NO_CELL_and_NO_PAIR_KEY():
    """⛔⛔ STRUCTURALLY UN-POOLABLE, NOT MERELY LABELLED. `content-persistent`
    exists only to anchor the low end of the release-suppression slope (prereg
    765b6787): its corpus PERSISTS by construction, so it is a measurement probe
    and never a member of the population.

    ⭐ It therefore carries none of the three fields every pooling and pairing
    routine reads — `cell`, `factorial_pair_key`, `pairing_capability_side`. An
    arm that carried them could be pooled by a later analysis that simply forgot
    what it was; without them it cannot be, whether or not anyone remembers.
    Same discipline as the drift run's self-pair control.
    """
    from tlon.act2.factorial import dose_arm_entry
    from tlon.discourse.transient import CONTENT_PERSISTENT
    e = dose_arm_entry("cp-s20624", recipe=CONTENT_PERSISTENT, seed=20624,
                       suppression_window=-1, manifest=FRESH)
    assert e["DOSE_ARM"] is True
    assert e["cell"] is None and e["factorial_cell"] is None
    assert "factorial_pair_key" not in e
    assert "pairing_capability_side" not in e
    assert e["suppression_window"] == -1


def test_a_FACTORIAL_recipe_cannot_be_built_as_a_dose_arm():
    """⛔ Non-vacuity in the other direction: the quarantine must not become a
    convenient way to smuggle a real cell out of the matrix."""
    from tlon.act2.factorial import dose_arm_entry
    with pytest.raises(FactorialError, match="factorial recipe"):
        dose_arm_entry("ct-s20624", recipe=CONTENT_TRANSIENT, seed=20624,
                       suppression_window=1, manifest=FRESH)


def test_the_DOSE_ARM_RECIPE_cannot_become_a_CELL_by_any_route():
    """⛔⛔ THE QUARANTINE IS THE `RECIPES` TUPLE. Every factorial entry point
    validates against it, so a dose arm cannot be labelled, entered or paired —
    and that is structural rather than a rule somebody follows."""
    from tlon.discourse.transient import CONTENT_PERSISTENT
    for fn, kw in ((adapter_label, {}), ):
        with pytest.raises(FactorialError):
            fn(CONTENT_PERSISTENT, 20624, **kw)
    with pytest.raises(FactorialError):
        entry("cp-s20624", recipe=CONTENT_PERSISTENT, seed=20624,
              manifest=FRESH)
    with pytest.raises(FactorialError):
        recipe_of({"recipe": CONTENT_PERSISTENT})


def test_a_NEGATIVE_window_cannot_be_a_content_transient_CELL():
    """⛔⛔ A negative window bars nothing, so the corpus PERSISTS. No label typed
    on a command line makes that a treatment cell."""
    with pytest.raises(FactorialError, match="bars nothing"):
        entry("ctw-1-s20624", recipe=CONTENT_TRANSIENT, seed=20624,
              manifest=FRESH, suppression_window=-1)


def test_the_DOSE_rides_with_a_normal_entry():
    """⭐ Two content-transient adapters at different windows are DIFFERENT
    treatments. One that cannot say its dose will be pooled with the other."""
    e = entry("ctw1-s20624", recipe=CONTENT_TRANSIENT, seed=20624,
              manifest=FRESH, suppression_window=1)
    assert e["suppression_window"] == 1
    assert e["factorial_pair_key"] == "seed20624"
