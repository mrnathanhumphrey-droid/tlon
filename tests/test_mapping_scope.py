"""RUNG 2's SCOPE — and the false floor it must be unable to manufacture.

⛔⛔ THE STAKES ARE SPECIFIC TO THIS RUNG. Rung 2 unfreezes `embed_tokens` +
`lm_head` to ask whether release lives in the token mapping, and the outcome it
is most likely to produce is a FLOOR. So a selector that matches nothing, a
freeze that does not take, or a mapping that never moves all yield exactly the
reading the run is hunting -- *the false floor and the finding are the same
observation*, and nothing downstream can tell them apart.

⭐ Therefore every assertion here is POSITIVE AND NAMED. "Everything except the
layers" is satisfied by matching nothing; "these two tensors, by name, are
trainable, and no layer tensor is" is not.
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tlon.act2.full_weight import (MAPPING_FROZEN,  # noqa: E402
                                   MAPPING_LEAVES, MAPPING_MOVED,
                                   MAPPING_UNVERIFIED, ScopeError,
                                   expected_moved_fraction,
                                   full_weight_scope, mapping_moved,
                                   mapping_scope)

#: Measured on rung 2: 921 distinct ids over a 152,064-row embedding.
COVERAGE = 921 / 152064.0

#: The real Qwen2.5-7B-Instruct naming, trimmed to 3 layers.
def _names(n_layers=3):
    out = ["model.embed_tokens.weight"]
    for i in range(n_layers):
        for leaf in ("self_attn.q_proj.weight", "self_attn.q_proj.bias",
                     "self_attn.k_proj.weight", "mlp.gate_proj.weight",
                     "input_layernorm.weight"):
            out.append("model.layers.%d.%s" % (i, leaf))
    out += ["model.norm.weight", "lm_head.weight"]
    return out


def _row(changed=4096, dn=0.5):
    return {"n": 545003776, "sampled": 4096, "changed": changed,
            "fraction_changed": changed / 4096.0, "delta_norm_estimated": dn}


def _embed_row(frac=COVERAGE, dn=1.97):
    """A HEALTHY embed_tokens row: sparse by construction, ~coverage."""
    return {"n": 545003776, "sampled": 4096, "changed": int(4096 * frac),
            "fraction_changed": frac, "delta_norm_estimated": dn}


def _delta(embed=_embed_row, head=_row, **kw):
    per = {}
    if embed is not None:
        per["model.embed_tokens.weight"] = embed() if callable(embed) else embed
    if head is not None:
        per["lm_head.weight"] = head() if callable(head) else head
    per["model.layers.0.self_attn.q_proj.weight"] = _row(changed=0, dn=0.0)
    d = {"verdict": "OK", "per_module": per}
    d.update(kw)
    return d


# ── the selection is POSITIVE ──────────────────────────────────────────────

def test_it_selects_exactly_the_two_mapping_tensors():
    s = mapping_scope(_names())
    assert sorted(s["trainable"]) == ["lm_head.weight",
                                      "model.embed_tokens.weight"]
    assert s["scope_mode"] == "mapping"
    assert s["unfreeze_top"] == 0


def test_every_transformer_layer_is_frozen():
    """⛔ The point of Option A. One layer in the trainable set is Option B by
    accident, re-confounding the run with the capacity that tested flat."""
    s = mapping_scope(_names())
    assert not [n for n in s["trainable"] if ".layers." in n]
    assert len([n for n in s["frozen"] if ".layers." in n]) == 15


def test_model_norm_stays_frozen():
    """⭐ The final RMSNorm is not part of the token mapping."""
    assert "model.norm.weight" in mapping_scope(_names())["frozen"]


# ── the false floor, in each way it could be manufactured ──────────────────

def test_a_TIED_model_is_REFUSED_not_silently_halved():
    """⛔⛔ On a tied model `lm_head` is not its own parameter, so the scope
    would silently be 545 M instead of the declared 1.090 B -- a smaller
    experiment than the one locked, with no symptom."""
    tied = [n for n in _names() if n != "lm_head.weight"]
    with pytest.raises(ScopeError, match="lm_head"):
        mapping_scope(tied)


def test_a_renamed_embedding_is_REFUSED():
    """⛔ A different architecture's naming must refuse, not select nothing."""
    renamed = [n.replace("model.embed_tokens.weight", "transformer.wte.weight")
               for n in _names()]
    with pytest.raises(ScopeError, match="embed_tokens"):
        mapping_scope(renamed)


def test_names_with_no_layers_at_all_are_REFUSED():
    """⛔ If no layer matches, 'the layers are frozen' is unverifiable — and an
    unverifiable freeze is what makes a false floor look like a finding."""
    with pytest.raises(ScopeError, match="frozen"):
        mapping_scope(["model.embed_tokens.weight", "lm_head.weight"])


def test_empty_names_are_REFUSED():
    with pytest.raises(ScopeError):
        mapping_scope([])


def test_a_mapping_leaf_inside_a_layer_does_not_count_as_the_mapping():
    """⛔ A hypothetical `layers.0.lm_head.weight` must not satisfy the lm_head
    requirement -- that would let a layer tensor stand in for the mapping."""
    odd = [n for n in _names() if n != "lm_head.weight"]
    odd.append("model.layers.0.lm_head.weight")
    with pytest.raises(ScopeError, match="lm_head"):
        mapping_scope(odd)


# ── the DELTA guard: floor-vs-no-op ────────────────────────────────────────

def test_both_leaves_moved_reads_MOVED():
    v, why = mapping_moved(_delta(), vocab_coverage=COVERAGE)
    assert v == MAPPING_MOVED, why


def test_a_frozen_embedding_is_caught_even_though_lm_head_MOVED():
    """⛔⛔ THE CASE THE GLOBAL §4.1 PRECONDITION CANNOT SEE. A nonzero global
    delta, carried entirely by the half that worked, passes §4.1 -- while the
    tensor the rung is actually about never moved. Per declared leaf, or the
    guard is satisfied by the wrong half."""
    d = _delta(embed=_row(changed=0, dn=0.0))
    v, why = mapping_moved(d, vocab_coverage=COVERAGE)
    assert v == MAPPING_FROZEN, why
    assert "embed_tokens" in why


def test_a_frozen_lm_head_is_caught_symmetrically():
    v, why = mapping_moved(_delta(head=_row(changed=0, dn=0.0)), vocab_coverage=COVERAGE)
    assert v == MAPPING_FROZEN and "lm_head" in why


def test_changed_nonzero_but_delta_norm_zero_is_still_FROZEN():
    """⛔ Both conditions, not either: a count that moved with zero norm is a
    sampling artefact, not movement."""
    v, _ = mapping_moved(_delta(embed=_row(changed=4096, dn=0.0)), vocab_coverage=COVERAGE)
    assert v == MAPPING_FROZEN


def test_a_missing_per_module_record_REFUSES_rather_than_certifying():
    """⛔⛔ An unmeasured mapping is not a moved one. `or 0` thinking here would
    certify silence."""
    v, why = mapping_moved({"verdict": "OK"}, vocab_coverage=COVERAGE)
    assert v == MAPPING_FROZEN and "REFUSING" in why


def test_a_missing_leaf_row_REFUSES():
    v, why = mapping_moved(_delta(head=None), vocab_coverage=COVERAGE)
    assert v == MAPPING_FROZEN and "lm_head" in why


# ── the existing scope is untouched ────────────────────────────────────────

def test_the_layer_scope_still_behaves_and_still_freezes_the_mapping():
    """⛔ Rungs 1a/1b/1b' must remain reproducible: their scope is unchanged and
    the mapping is still frozen there."""
    s = full_weight_scope(_names(), unfreeze_top=2)
    assert "model.embed_tokens.weight" in s["frozen"]
    assert "lm_head.weight" in s["frozen"]
    assert all(".layers." in n for n in s["trainable"])


def test_unfreeze_top_zero_is_still_refused():
    """⛔ The empty-selector guard that rung 2 must be built AROUND, not
    through."""
    with pytest.raises(ScopeError, match="outside 1"):
        full_weight_scope(_names(), unfreeze_top=0)


# ── the mode has to be REACHABLE, or it is not built ──────────────────────

FT = (ROOT / "tools" / "act2_finetune.py").read_text(encoding="utf-8")


def test_the_trainer_exposes_the_mapping_mode():
    """⛔⛔ A SCOPE MODE NOTHING CAN INVOKE IS NOT BUILT. Tonight's own lesson:
    `pipeline_fullft.sh` was live and tested for two rungs while sitting outside
    the orchestrator's allow-list, so both runs were launched by hand-rolled
    ssh that skipped the credential source. A capability the pipeline cannot
    reach gets reached around."""
    assert '"--scope-mode"' in FT
    assert 'choices=("layers", "mapping")' in FT
    assert "apply_mapping_scope" in FT


def test_mixing_the_two_scopes_is_REFUSED_not_ignored():
    """⛔ `--unfreeze-top` on a mapping run names a layer count nothing
    applies. Silently ignoring it would print a scope the run does not have --
    on a floor-hunting rung, a mislabelled finding."""
    assert "--unfreeze-top names nothing" in FT


def test_the_mapping_run_prints_its_actual_trainable_tensors():
    """⭐ The resolved scope is PRINTED, like the resolved attention kernel. A
    default never printed is a decision nobody made -- and here it is the
    difference between the finding and a frozen no-op."""
    assert 'print("   trainable tensors: %s" % sorted(scope["trainable"]))' in FT


def test_the_two_scopes_are_complements_on_the_mapping():
    """⭐ Rung 2 is exactly the inversion of §5's freeze, so the pair is defined
    once and cannot drift."""
    from tlon.act2.full_weight import FROZEN_LEAVES
    assert MAPPING_LEAVES == FROZEN_LEAVES


# ── the THIRD call site of the zero-scope guard ────────────────────────────

def test_the_factorial_entry_accepts_the_mapping_scope():
    """⛔⛔ THE GUARD FAMILY'S THIRD CALL SITE, AND IT COST A RUN.

    `full_weight_scope` was extended for rung 2 and the trainer was wired, but
    `weight_arm_entry` carries its OWN copy of the zero-trainable refusal and
    nothing asked it. Rung 2 trained 3,760 clean steps, then died at
    `factorial_json` on `unfreeze_top=0 trains nothing` -- ~$9 and 45 minutes,
    one step after the training that produced the result.

    ⭐ Same lesson as the prereg id, in the same session: a fix written on the
    file that got caught does not close the failure mode. The scope WIDENED to
    a second locus, so the rule is RE-DERIVED, not stretched."""
    from tlon.act2.factorial import weight_arm_entry
    from tlon.discourse.transient import CONTENT_TRANSIENT
    e = weight_arm_entry("fwmap", recipe=CONTENT_TRANSIENT, seed=20624,
                         unfreeze_top=0, scope_mode="mapping", prereg="c2a4f0ca",
                         base_model="Qwen/Qwen2.5-7B-Instruct")
    assert e["scope_mode"] == "mapping"
    assert e["unfreeze_top"] == 0
    # ⭐ POSITIVE: the artifact names what moved, so "trains nothing" is
    # falsifiable from the record rather than inferred from a zero.
    assert e["trainable_leaves"] == ["embed_tokens", "lm_head"]
    assert e["cell"] is None and e["measurement_category"] == "_w"


def test_the_zero_LAYER_scope_is_still_refused():
    """⛔ The guard's PURPOSE is untouched: a scope that trains nothing is
    still refused. Only the inference from a layer count changed."""
    from tlon.act2.factorial import FactorialError, weight_arm_entry
    from tlon.discourse.transient import CONTENT_TRANSIENT
    with pytest.raises(FactorialError, match="trains nothing"):
        weight_arm_entry("x", recipe=CONTENT_TRANSIENT, seed=1,
                         unfreeze_top=0, prereg="p",
                         base_model="Qwen/Qwen2.5-7B-Instruct")


def test_a_mapping_scope_with_a_LAYER_COUNT_is_refused():
    """⛔ That would record Option B while training Option A."""
    from tlon.act2.factorial import FactorialError, weight_arm_entry
    from tlon.discourse.transient import CONTENT_TRANSIENT
    with pytest.raises(FactorialError, match="unfreeze_top must be 0"):
        weight_arm_entry("x", recipe=CONTENT_TRANSIENT, seed=1,
                         unfreeze_top=19, scope_mode="mapping", prereg="p",
                         base_model="Qwen/Qwen2.5-7B-Instruct")


def test_an_unnamed_scope_mode_is_refused():
    from tlon.act2.factorial import FactorialError, weight_arm_entry
    from tlon.discourse.transient import CONTENT_TRANSIENT
    with pytest.raises(FactorialError, match="unknown scope_mode"):
        weight_arm_entry("x", recipe=CONTENT_TRANSIENT, seed=1,
                         unfreeze_top=0, scope_mode="everything", prereg="p",
                         base_model="Qwen/Qwen2.5-7B-Instruct")


def test_the_pipeline_passes_the_scope_mode_to_the_factorial_entry():
    """⛔ The artifact must record the scope the run actually had. Wiring the
    trainer alone is what left this call site behind the first time."""
    sys.path.insert(0, str(ROOT / "tests"))
    from textguard import code_only
    pipe = (ROOT / "tools" / "pipeline_fullft.sh").read_text(encoding="utf-8")
    assert 'scope_mode="$SCOPE_MODE"' in code_only(pipe)

# ── THE FIX: a PASS must be self-interpreting ──────────────────────────────
#
# ⛔⛔ The first gate tested `changed > 0 and delta_norm > 0`. On rung 2 that
# passed an embed_tokens at 20/4096 -- and the PASS could not be read until the
# corpus was measured AFTERWARDS to show 0.49% is what sparse embedding
# gradients predict. A guard whose PASS needs a follow-up investigation is not
# yet a guard, and the same threshold would have passed 1/4096.

#: Rung 2's real per-tensor record, copied from
#: runs/act2/fullft_fwmap-s20624/weight_delta.json.
RUNG2_EMBED = {"n": 545003776, "sampled": 4096, "changed": 20,
               "fraction_changed": 0.0048828125,
               "delta_norm_estimated": 1.9659427065311268}
RUNG2_HEAD = {"n": 545003776, "sampled": 4096, "changed": 4096,
              "fraction_changed": 1.0,
              "delta_norm_estimated": 18.101913613716174}


def test_rung_2s_REAL_numbers_still_pass_because_sparsity_predicts_them():
    """⭐ THE RUN THAT MOTIVATED THE FIX MUST STILL PASS. Its embed_tokens moved
    0.49% against a predicted 0.61% -- healthy sparse training, correctly
    certified. The fix must not retroactively invalidate a good run."""
    d = _delta(embed=RUNG2_EMBED, head=RUNG2_HEAD)
    v, why = mapping_moved(d, vocab_coverage=COVERAGE)
    assert v == MAPPING_MOVED, why
    assert "PREDICTED" in why


def test_a_DEAD_embedding_is_now_CAUGHT_where_the_old_gate_passed_it():
    """⛔⛔ THE WHOLE POINT. 1 changed value in 4,096 is a dead tensor, and
    `changed > 0` called it moved. Against the prediction it is an order of
    magnitude short and is refused."""
    dead = {"n": 545003776, "sampled": 4096, "changed": 1,
            "fraction_changed": 1 / 4096.0, "delta_norm_estimated": 0.01}
    v, why = mapping_moved(_delta(embed=dead, head=RUNG2_HEAD),
                           vocab_coverage=COVERAGE)
    assert v == MAPPING_FROZEN, why
    assert "UNDER-MOVED" in why and "embed_tokens" in why


def test_a_HALF_TRAINED_lm_head_is_caught_against_its_DENSE_prediction():
    """⛔ The two leaves get DIFFERENT predictions. lm_head is dense (1.0), so
    30% is badly short for it -- while 30% would be wildly healthy for the
    sparse embedding. One threshold for both could not do this."""
    lazy = {"n": 545003776, "sampled": 4096, "changed": 1200,
            "fraction_changed": 0.293, "delta_norm_estimated": 5.0}
    v, why = mapping_moved(_delta(head=lazy), vocab_coverage=COVERAGE)
    assert v == MAPPING_FROZEN and "lm_head" in why


def test_the_sparse_prediction_is_NOT_applied_to_lm_head():
    assert expected_moved_fraction("lm_head", vocab_coverage=COVERAGE) == 1.0
    assert expected_moved_fraction("embed_tokens",
                                   vocab_coverage=COVERAGE) == COVERAGE


def test_no_coverage_means_UNVERIFIED_not_a_bare_nonzero_pass():
    """⛔⛔ An unpredicted movement is not a verified one. Falling back to
    `> 0` here would reinstate exactly the threshold being replaced."""
    v, why = mapping_moved(_delta(), vocab_coverage=None)
    assert v == MAPPING_UNVERIFIED
    assert "REFUSING" in why and v != MAPPING_MOVED


def test_a_nonsense_coverage_is_UNVERIFIED():
    for bad in (0.0, -0.1, 1.5):
        v, _ = mapping_moved(_delta(), vocab_coverage=bad)
        assert v == MAPPING_UNVERIFIED, bad


def test_UNVERIFIED_blocks_the_floor_exactly_as_FROZEN_does():
    """⭐ Three states, and only ONE of them lets a floor be read."""
    assert MAPPING_UNVERIFIED != MAPPING_MOVED
    assert MAPPING_FROZEN != MAPPING_MOVED
