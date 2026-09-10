"""THE `_w` OBJECT — its persist shape, and its quarantine from the factorial.

PREREG `PREREG_FULL_FINETUNE_RELEASE_2026_09_05` (LOCK `a0450b36`) §0 and §6: a
full-weight model is a `_w` object. It must never enter the `_ctx` factorial and
must never be measured against the frozen inference ruler (MEASUREMENTS C8).
These tests are about the REFUSALS, because the separation is only worth having
if the code enforces it when nobody remembers to.
"""
import importlib.util
import json
import pathlib

import pytest

from tlon.act2.factorial import (CATEGORY_CTX, CATEGORY_W,  # noqa: E402
                                 CONTENT_FREE, CONTENT_TRANSIENT, FULL_WEIGHT,
                                 FactorialError, check_balanced, entry,
                                 pair_regimes, unpaired, weight_arm_entry)

PREREG = "a0450b36"


def _persist():
    p = (pathlib.Path(__file__).resolve().parents[1] / "tools"
         / "act2_box_persist.py")
    spec = importlib.util.spec_from_file_location("_bp", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── the quarantine ───────────────────────────────────────────────────────────

def test_a_weight_arm_entry_has_no_cell_and_no_pair_key():
    """⛔ The three fields every pooling and pairing routine reads."""
    e = weight_arm_entry("fw", recipe=CONTENT_TRANSIENT, seed=20624,
                         unfreeze_top=14, prereg=PREREG,
                         base_model="Qwen/Qwen2.5-7B-Instruct")
    assert e["cell"] is None
    assert e["factorial_cell"] is None
    assert "factorial_pair_key" not in e
    assert "pairing_capability_side" not in e
    assert e["measurement_category"] == CATEGORY_W


def test_the_recipe_stays_true_because_it_is_what_it_trained_on():
    """⭐ Unlike the dose arm, a `_w` object IS trained on a factorial recipe.
    Refusing the recipe would be a lie about the corpus; refusing the CELL is
    the accurate statement."""
    e = weight_arm_entry("fw", recipe=CONTENT_TRANSIENT, seed=20624,
                         unfreeze_top=14, prereg=PREREG,
                         base_model="Qwen/Qwen2.5-7B-Instruct")
    assert e["recipe"] == CONTENT_TRANSIENT
    assert e["training_mode"] == FULL_WEIGHT
    assert e["unfreeze_top"] == 14


def test_entry_refuses_to_mint_a_cell_for_a_weight_changed_object():
    """⛔⛔ `entry()` is the ONLY place a cell and a pair key are minted, so the
    refusal here is what makes the C8 separation structural."""
    with pytest.raises(FactorialError, match="cannot take a factorial cell"):
        entry("fw", recipe=CONTENT_TRANSIENT, seed=20624,
              training_mode=FULL_WEIGHT)


def test_a_weight_arm_cannot_be_pooled_even_though_its_recipe_is_real():
    """⛔⛔ THE HOLE THE ABSENT CELL DOES NOT CLOSE. The dose arm is safe from
    `pair_regimes` almost by accident — its recipe is outside RECIPES, so every
    recipe-keyed routine drops it. A `_w` object is content-transient at a real
    seed, so it would key exactly like the adapter it must never pair with."""
    ctx = [entry("cf", recipe=CONTENT_FREE, seed=20624),
           entry("ct", recipe=CONTENT_TRANSIENT, seed=20624)]
    assert pair_regimes(ctx) != {}          # the real pair still works

    w = weight_arm_entry("fw", recipe=CONTENT_TRANSIENT, seed=20624,
                         unfreeze_top=14, prereg=PREREG,
                         base_model="Qwen/Qwen2.5-7B-Instruct")
    for fn in (pair_regimes, unpaired, check_balanced):
        with pytest.raises(FactorialError, match="not factorial members"):
            fn(ctx + [w])


def test_the_refusal_raises_rather_than_filtering():
    """⛔ Silently dropping it would leave the caller believing the population
    included it — a count that is right for a reason nobody stated."""
    w = weight_arm_entry("fw", recipe=CONTENT_TRANSIENT, seed=20624,
                         unfreeze_top=14, prereg=PREREG,
                         base_model="Qwen/Qwen2.5-7B-Instruct")
    with pytest.raises(FactorialError):
        pair_regimes([w])


def test_adapters_carry_the_ctx_label_so_a_mixed_set_is_visible():
    e = entry("ct", recipe=CONTENT_TRANSIENT, seed=20624)
    assert e["measurement_category"] == CATEGORY_CTX


def test_unfreeze_top_zero_is_refused_at_the_ledger_too():
    with pytest.raises(FactorialError, match="trains nothing"):
        weight_arm_entry("fw", recipe=CONTENT_TRANSIENT, seed=20624,
                         unfreeze_top=0, prereg=PREREG,
                         base_model="Qwen/Qwen2.5-7B-Instruct")


# ── the persist shape ────────────────────────────────────────────────────────

def _model_dir(tmp_path, *, shards=("model-00001-of-00002.safetensors",
                                    "model-00002-of-00002.safetensors"),
               index=True, delta="OK", write=None):
    d = tmp_path / "model_fw-s20624"
    d.mkdir(parents=True, exist_ok=True)
    for s in (write if write is not None else shards):
        (d / s).write_bytes(b"weights")
    if index:
        (d / "model.safetensors.index.json").write_text(json.dumps(
            {"weight_map": {"layer.%d" % i: s
                            for i, s in enumerate(shards)}}))
    (d / "config.json").write_text("{}")
    (d / "factorial.json").write_text("{}")
    if delta is not None:
        (d / "weight_delta.json").write_text(json.dumps(
            {"verdict": delta, "fraction_changed": 0.99}))
    return d


def test_the_shard_set_comes_from_the_index_not_a_glob(tmp_path):
    bp = _persist()
    d = _model_dir(tmp_path)
    assert bp.shard_files(d) == ["model-00001-of-00002.safetensors",
                                 "model-00002-of-00002.safetensors"]


def test_a_shard_the_index_requires_but_disk_lacks_is_refused(tmp_path):
    """⛔⛔ Persisting the rest would save a model that cannot load, and the
    ledger would record it as complete."""
    bp = _persist()
    d = _model_dir(tmp_path, write=("model-00001-of-00002.safetensors",))
    with pytest.raises(bp.TransferError, match="not on disk"):
        bp.shard_files(d)


def test_a_shard_on_disk_the_index_does_not_reference_is_refused(tmp_path):
    """⛔ Two models' weights under one cell is worse than a missing one,
    because it loads."""
    bp = _persist()
    d = _model_dir(tmp_path)
    (d / "model-00003-of-00003.safetensors").write_bytes(b"stray")
    with pytest.raises(bp.TransferError, match="not referenced by the index"):
        bp.shard_files(d)


def test_a_single_shard_save_without_an_index_still_works(tmp_path):
    bp = _persist()
    d = _model_dir(tmp_path, shards=("model.safetensors",), index=False)
    assert bp.shard_files(d) == ["model.safetensors"]


def test_a_directory_with_no_model_at_all_is_refused(tmp_path):
    bp = _persist()
    d = tmp_path / "empty"
    d.mkdir()
    with pytest.raises(bp.TransferError, match="neither"):
        bp.shard_files(d)


def test_persist_refuses_a_w_object_with_no_weight_delta(tmp_path):
    """⛔⛔ §4.1 makes the delta a precondition on the whole verdict table, so a
    model saved without it cannot be read for anything."""
    bp = _persist()
    _model_dir(tmp_path, delta=None)
    (tmp_path / "corpus_manifest.json").write_text("{}")
    with pytest.raises(bp.TransferError, match="weight_delta.json is required"):
        bp.persist_full_weight(tmp_path, "fw-s20624", "repo",
                               corpus_manifest=tmp_path / "corpus_manifest.json")


def test_persist_records_the_delta_verdict_in_the_ledger(tmp_path):
    """⭐ A faulted run is still persisted — the fault is the finding — but it
    must be visible in the ledger, not discovered later by opening a file."""
    bp = _persist()
    _model_dir(tmp_path, delta="INSTRUMENT_FAULT")
    (tmp_path / "corpus_manifest.json").write_text("{}")
    seen = []

    def fake_push(name, path, repo, private=True, subdir=None):
        seen.append(pathlib.Path(path).name)
        return "hub://%s/%s" % (subdir, pathlib.Path(path).name)

    e = bp.persist_full_weight(tmp_path, "fw-s20624", "repo",
                               corpus_manifest=tmp_path / "corpus_manifest.json",
                               push=fake_push)
    assert e["kind"] == bp.KIND_FULL_WEIGHT
    assert e["weight_delta_verdict"] == "INSTRUMENT_FAULT"
    assert e["n_shards"] == 2
    assert "model.safetensors.index.json" in seen
    assert "weight_delta.json" in seen


def test_unpersisted_checks_a_w_entry_against_the_w_required_set(tmp_path):
    """⛔ An entry with no `kind` predates this arm and is an adapter — the same
    absent-means-legacy rule the factorial uses."""
    bp = _persist()
    led = {
        "fw-s20624": {"kind": bp.KIND_FULL_WEIGHT, "files": {
            n: {"uri": "u"} for n in
            bp.FULL_WEIGHT_REQUIRED + (bp.CORPUS_MANIFEST,)}},
        "legacy": {"files": {n: {"uri": "u"} for n in bp.REQUIRED_PERSISTED}},
    }
    bp.write_ledger(tmp_path, led)
    assert bp.unpersisted(tmp_path, ["fw-s20624", "legacy"]) == []

    led["fw-s20624"]["files"].pop("weight_delta.json")
    bp.write_ledger(tmp_path, led)
    assert bp.unpersisted(tmp_path, ["fw-s20624"]) == ["fw-s20624"]
