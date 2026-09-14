"""⛔ THE DOSE-CURVE CALLBACK, CHECKED AT THE SOURCE.

The callback only executes on a GPU with a loaded 7B model, so the properties
that make it safe cannot be exercised here. They CAN be asserted structurally,
which is how this project has checked the other un-runnable paths — and a
structural check that the generation sits inside the isolation guard is worth
more than a runtime check that never runs.
"""
import pathlib
import re

SRC = (pathlib.Path(__file__).resolve().parents[1] / "tools"
       / "act2_finetune.py").read_text(encoding="utf-8")
FLOCAL = (pathlib.Path(__file__).resolve().parents[1] / "tools"
          / "act2_flocal.py").read_text(encoding="utf-8")


def _callback_body() -> str:
    """The `_DoseCurve` class body, so assertions are about the callback and
    not about some other part of a 900-line file."""
    i = SRC.index("class _DoseCurve")
    j = SRC.index("trainer.add_callback(_DoseCurve())")
    return SRC[i:j]


def test_the_generation_happens_inside_the_isolation_guard():
    """⛔⛔ THE ONE THAT MATTERS. If the read escapes `isolated_read`, training
    mode and the RNG stream are not restored, and every step after the first
    checkpoint belongs to a different run than the steps before it."""
    body = _callback_body()
    guard = body.index("with isolated_read(")
    read = body.index("_read_rates(")
    assert guard < read, "the F-LOCAL read is not inside isolated_read"
    # ... and inside the same indented block, not merely after it
    between = body[guard:read]
    assert "\n        " not in between.replace("\n                ", ""), \
        "the read appears to have left the isolated_read block"


def test_the_callback_writes_no_intermediate_weights():
    """⛔ 5 checkpoints x 14.5 GB = 72 GB against 46.8 GB of hub headroom. The
    curve is the READINGS; a save here would fail the run at the last one."""
    body = _callback_body()
    for forbidden in ("save_pretrained", "torch.save", "trainer.save_model"):
        assert forbidden not in body, "callback writes weights: %s" % forbidden


def test_it_uses_the_shared_flocal_fold_not_a_second_copy():
    """⛔⛔ A second F-LOCAL spelled here would drift from the CLI's — which is
    exactly how the trainer and the reader came to build different prompts on
    Mistral. `read_rates` is the one fold."""
    assert "def read_rates(" in FLOCAL
    assert "read_rates(speaker, battery, a.n)" in FLOCAL   # the CLI uses it
    assert "_read_rates(" in _callback_body()              # the curve uses it
    assert "_rate(" not in _callback_body(), \
        "the callback calls the private rate helper directly, bypassing the fold"


def test_the_curve_is_off_by_default():
    """⛔ Every read costs generations. A run that silently paid for five would
    report a wall-clock and a cost nobody pre-registered."""
    m = re.search(r'add_argument\("--dose-curve-out",\s*default=(\w+)', SRC)
    assert m and m.group(1) == "None"


def test_the_curve_refuses_on_the_lora_path():
    """⛔ rms is measured against the §4.1 snapshot, which only the full-weight
    path takes. On the adapter path there is nothing to measure against, and a
    silent None would enter the curve as a dose."""
    assert "if a.dose_curve_out and not a.full:" in SRC


def test_every_reading_records_examples_seen_beside_the_dose():
    """⛔⛤ THE WHOLE REASON THIS DESIGN EXISTS. The rejected design reached a
    matched dose by halting early, which meant ~40 % fewer examples — a rival
    cause of the very crater the run reads. Here the epoch completes, and each
    point carries its own examples_seen so the two quantities can never be
    silently conflated under the word 'dose'."""
    body = _callback_body()
    assert '"examples_seen"' in body
    assert '"rms"' in body


def test_each_reading_stamps_the_battery_so_points_are_comparable():
    """⛔ The cross-run crater finding rests on all three runs sharing battery
    a2b318d6d2e6b98a. A curve whose points did not record it could not make the
    same claim about itself."""
    assert '"battery"' in _callback_body()


def test_the_target_crossing_does_not_halt_training():
    """⭐ The matched dose is OBSERVED, not arranged. If the callback ever
    returned a stop, this design would collapse back into the early-halt one it
    replaced, confound and all."""
    body = _callback_body()
    assert "should_training_stop" not in body
    assert "control.should_training_stop" not in body


def test_the_rms_ladder_owns_the_latching():
    """⛔ Without latching, every later step re-reads a crossed rung and the
    curve fills with duplicates of one point.

    ⭐ The callback must NOT keep its own latch flag: two places deciding
    whether a rung has fired is exactly the partial-wiring shape that cost three
    defects. `TargetLadder` latches, and `tests/test_dose_curve.py` red-proofs
    it — the callback just asks."""
    body = _callback_body()
    assert "_ladder.crossed(" in body
    assert "target_done" not in body, "the callback keeps a second latch"


def test_the_matched_rung_is_recorded_on_the_reading():
    """⭐⭐ THE PAIR HAS TO BE JOINABLE. A matched-rms comparison whose rows only
    carry their own achieved rms leaves the joining to whoever later eyeballs
    two columns; recording the TARGET each read fired on makes the pair explicit
    in the artifact."""
    body = _callback_body()
    assert '"matched_rms_targets"' in body
