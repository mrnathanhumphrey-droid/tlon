"""⛔⛔ THE POOLED §4.1 FRACTION TEST IS INVALID FOR MAPPING SCOPE.

WHY THIS EXISTS, STATED AS THE LOSS IT IS PREVENTING. On 2026-09-13 the Mistral
mapping rung (`mismap-s20624`, PREREG `afe75eca`) trained cleanly, moved both
mapping leaves exactly as predicted, produced a full F-LOCAL and lag reading —
and emitted NO VERDICT, because the §4.1 pooled-fraction precondition returned
`UNDISCRIMINATING`. ~$3.84 and a complete measurement, unreadable.

⭐ THE POOLED TEST COMPARES AGAINST A WORKING PREDICTION OF 1.0 — "every
trainable weight moves". That is true of a LAYER rung and FALSE of a MAPPING
rung: `embed_tokens` receives gradient only on rows whose tokens occur, so a
PERFECTLY HEALTHY mapping run predicts about `(1.0 + coverage) / 2`.

    Qwen    mapping  observed 0.5024  dead-zone 0.1865  crossover 0.432  -> OK
    Mistral mapping  observed 0.5122  dead-zone 0.5616  (>= 0.5)  -> UNDISCRIMINATING

⛔⛔ QWEN PASSED BY LUCK, ON A QUANTITY THAT WAS NEVER MEASURING WHAT THE TEST
THOUGHT — clear of its crossover by 0.07. Mistral's mapping weights are smaller
(69.4 % of `embed_tokens` under the 2.56e-3 ceiling against Qwen's pooled
18.7 %, measured over 48 M values off the real safetensors), so the identical
healthy run reads as unmeasurable. ⛔ And at the pre-registered 5e-6 dial-back
the measured dead-zone prediction is 0.340, crossover 0.583 — ABOVE the
structural 0.512 — so the same healthy run would read as a FAULT, which is
worse: it asserts the optimizer did not write.

⭐ THE WAIVER IS BY A STRICTLY STRONGER TEST. `mapping_moved` checks EACH leaf
against ITS OWN computed prediction. These tests exist to prove that it cannot
become a way to wave a run through.
"""
import importlib.util
import math
import pathlib


def _v():
    p = (pathlib.Path(__file__).resolve().parents[1] / "tools"
         / "act2_fullft_verdict.py")
    spec = importlib.util.spec_from_file_location("_vp", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PREREG_ID = "0" * 8


def _delta(verdict="OK", fraction=0.5122):
    return {"verdict": verdict, "fraction_changed": fraction,
            "why": "the bf16 dead-zone prediction is 0.562, ..."}


def _lag(z1=20.0, z2=1.0, z3=0.5):
    return {"z": {"1": z1, "2": z2, "3": z3}, "object_kind": "full_weight"}


def _fl(fired=False):
    return {"fired": fired}


def _moved(verdict="MAPPING_MOVED"):
    return {"verdict": verdict, "why": "every declared mapping leaf moved",
            "vocab_coverage": 0.024139}


# ── the containment half: nothing that used to refuse may now pass ──────────

def test_layer_scope_run_with_a_bad_delta_still_refuses():
    """⛔⛔ CONTAINMENT. A layer rung has no mapping record, so the pooled
    precondition must gate it exactly as before. If this ever passes, the fix
    has widened into 'halt on nothing'."""
    v = _v()
    out = v.decide(_delta("UNDISCRIMINATING"), _lag(), _fl(), prereg=PREREG_ID)
    assert out["verdict"] == v.FAULT
    assert out.get("axes_not_computed") is True


def test_a_still_leaf_still_refuses_even_in_mapping_scope():
    """⛔ The waiver is `MAPPING_MOVED`, not 'a mapping record exists'. A frozen
    leaf is the fake-floor case PREREG §5 was written for."""
    v = _v()
    for bad in ("MAPPING_FROZEN", "MAPPING_UNVERIFIED"):
        out = v.decide(_delta("UNDISCRIMINATING"), _lag(), _fl(),
                       prereg=PREREG_ID, mapping=_moved(bad))
        assert out["verdict"] == v.FAULT, bad
        assert out.get("axes_not_computed") is True


def test_diverged_delta_is_not_waivable_either():
    """⛔ A non-finite delta is not a fraction-test limitation — the run itself
    is off the axis the predictions describe. Per-leaf movement says nothing
    about NaN, so it must not carry it."""
    v = _v()
    out = v.decide(_delta("DIVERGED"), _lag(), _fl(), prereg=PREREG_ID,
                   mapping=_moved())
    assert out["verdict"] == v.FAULT


def test_an_absent_mapping_record_is_not_a_pass():
    """⛔ `None` means no per-leaf evidence exists. It must never read as
    'the per-leaf test was fine'."""
    v = _v()
    out = v.decide(_delta("UNDISCRIMINATING"), _lag(), _fl(),
                   prereg=PREREG_ID, mapping=None)
    assert out["verdict"] == v.FAULT


# ── the fix half: a moved mapping makes the reading readable ────────────────

def test_moved_mapping_carries_the_precondition():
    v = _v()
    out = v.decide(_delta("UNDISCRIMINATING"), _lag(), _fl(),
                   prereg=PREREG_ID, mapping=_moved())
    assert out["verdict"] != v.FAULT
    assert out.get("axes_not_computed") is not True
    assert out["axes"]["release"]["ok"] is True


def test_the_waiver_is_stamped_so_it_can_never_read_as_a_pooled_pass():
    """⭐ A reader must be able to tell which test carried the precondition."""
    v = _v()
    out = v.decide(_delta("UNDISCRIMINATING"), _lag(), _fl(),
                   prereg=PREREG_ID, mapping=_moved())
    assert "mapping_moved" in out["precondition_via"]
    assert out["delta_verdict_pooled"] == "UNDISCRIMINATING"


def test_a_pooled_pass_is_not_stamped():
    """⛔ The stamp must mark the exception, not decorate every run — otherwise
    it stops carrying information."""
    v = _v()
    out = v.decide(_delta("OK"), _lag(), _fl(), prereg=PREREG_ID,
                   mapping=_moved())
    assert "precondition_via" not in out
    assert "delta_verdict_pooled" not in out


def test_the_waiver_does_not_invent_an_axis_result():
    """⛔⛔ Carrying the precondition must change NOTHING about how the axes are
    scored. A cratered speaker stays cratered."""
    v = _v()
    waived = v.decide(_delta("UNDISCRIMINATING"), _lag(z2=99.0), _fl(fired=True),
                      prereg=PREREG_ID, mapping=_moved())
    straight = v.decide(_delta("OK"), _lag(z2=99.0), _fl(fired=True),
                        prereg=PREREG_ID)
    assert waived["verdict"] == straight["verdict"]
    assert waived["axes"] == straight["axes"]


# ── the arithmetic the fix rests on, recomputed rather than asserted ────────

def _pooled_verdict(observed, dead_zone):
    """A local restatement of `weight_delta._verdict`'s branch order, so this
    file can show WHY the pooled test fails here without importing around it."""
    if dead_zone >= 0.5:
        return "UNDISCRIMINATING"
    d_work = abs(math.log(observed) - math.log(1.0))
    d_dead = abs(math.log(observed) - math.log(dead_zone))
    return "FAULT" if d_dead < d_work else "OK"


def test_the_pooled_test_matches_what_it_actually_returned_on_both_bases():
    """⭐ The restatement above must reproduce the two FIRED runs, or the
    reasoning in this module's docstring is about a function that does not
    exist."""
    assert _pooled_verdict(0.5024, 0.1865) == "OK"              # Qwen, as run
    assert _pooled_verdict(0.5122, 0.5616) == "UNDISCRIMINATING"  # Mistral


def test_qwen_mapping_cleared_by_luck_not_by_margin():
    """⛔⛔ The crossover is `sqrt(dead_zone)`. Qwen's sat at 0.432 against an
    observed 0.502 — a 0.07 margin on a quantity the test was misreading."""
    assert math.isclose(math.sqrt(0.1865), 0.4319, abs_tol=1e-3)
    assert 0.5024 > math.sqrt(0.1865)


def test_the_dial_back_would_have_produced_a_false_fault():
    """⛔⛔ THE REASON THIS FIX HAD TO COME BEFORE THE RE-FIRE. At LR 5e-6 the
    measured dead-zone prediction is 0.340, so the pooled test DISCRIMINATES —
    and lands on FAULT for every fraction a healthy mapping run can produce,
    because the structural value is about (1.0 + coverage) / 2."""
    structural = (1.0 + 0.024139) / 2
    assert _pooled_verdict(structural, 0.3398) == "FAULT"
    # and not narrowly: the whole plausible band reads the same way
    for observed in (0.35, 0.40, 0.45, 0.50, 0.5122):
        assert _pooled_verdict(observed, 0.3398) == "FAULT", observed
    # the crossover sits ABOVE anything a mapping run reaches
    assert math.sqrt(0.3398) > structural
