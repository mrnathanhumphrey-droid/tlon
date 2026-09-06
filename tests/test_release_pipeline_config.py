"""THE RELEASE PIPELINE'S CONFIG, PINNED AGAINST LOCK a0450b36 AND ITS DEVIATIONS.

⛔⛔ THE FAILURE THIS EXISTS FOR IS A FLAG ON ONE LEG AND NOT THE OTHER. The
release run trains epoch 1 and epoch 2 as two separate `Trainer` invocations, so
every declared constant has to appear TWICE. `--attn-impl eager` is the newest
and most dangerous of them: the two attention kernels' forwards drift apart with
training (1.2% at step 0, 10.9% by step 13, FINDINGS §10), so a leg that
silently reverted to the default SDPA would be exactly the mid-flight kernel
swap that D-8 exists to forbid — and it would not crash, it would quietly train
on weights fitted to a different numerical function.

⛔ Checked in BOTH directions: that the flag is present on both legs, and that
the value is the one DEVIATIONS declares. A test that only checks presence would
pass on `--attn-impl sdpa`.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PIPE = ROOT / "tools" / "pipeline_fullft.sh"
DEV = ROOT / "docs" / "DEVIATIONS_FULL_FINETUNE_2026_09_05.md"


def _src():
    return PIPE.read_text(encoding="utf-8")


def test_both_training_legs_pass_the_attention_implementation():
    n = _src().count("--attn-impl $ATTN_IMPL")
    assert n == 2, ("expected the flag on BOTH legs, found %d. A leg without it "
                    "reverts to the transformers default (sdpa) mid-run." % n)


def test_the_pinned_kernel_is_eager():
    m = re.search(r"^ATTN_IMPL=(\S+)", _src(), re.M)
    assert m, "ATTN_IMPL is not pinned in the release pipeline"
    assert m.group(1) == "eager", (
        "the release run is pinned to %r; D-8 declares eager, and sdpa is the "
        "configuration that produces non-finite gradients" % m.group(1))


def test_every_locked_constant_appears_on_both_legs():
    """⛔ The same class of bug for the rest of §5, not only the new flag."""
    s = _src()
    for flag in ("--unfreeze-top $UNFREEZE_TOP", "--optim $OPTIM", "--lr $LR",
                 "--seq $SEQ", "--batch $BATCH", "--accum $ACCUM", "--full"):
        assert s.count(flag) >= 2, "%s does not appear on both legs" % flag


def test_the_deviation_is_declared_before_it_can_be_fired():
    """⛔⛔ A config change to a LOCKED prereg that is not written down is a
    silent change. The pipeline must not be able to run a deviation the
    deviations file does not carry."""
    d = DEV.read_text(encoding="utf-8")
    assert "D-8" in d, "D-8 is not declared in DEVIATIONS"
    assert "attn_implementation" in d or "--attn-impl" in d
    assert "eager" in d
    # ⭐ and the reason the swap must be from step 0, not mid-flight
    assert "step 0" in d


def test_the_card_deviation_covers_the_release_run_not_only_a_diagnostic():
    d = DEV.read_text(encoding="utf-8")
    assert "D-7" in d
    assert "sxm5" in d.lower()


def test_corpus_sha_is_still_the_one_the_findings_were_measured_on():
    assert "dd40e22f85b0b6e4" in _src()


def test_the_watchdog_is_armed_before_the_floors():
    """⛔ §8/R5. Floors-first leaves the window where a hang bills unattended."""
    s = _src()
    assert s.index("tlon_arm_watchdog") < s.index("step syntax_floor")
