"""THE SAFETY SCAFFOLDING EXISTS ONCE — enforced, not intended.

⛔⛔ THE FAILURE THIS GUARDS IS NOT A BUG, IT IS A DIVERGENCE. Three pipelines
run on boxes that terminate themselves. Both losses on 2026-09-04 were in their
shared safety logic — the `~/DONE` gate and the watchdog. Copied into each
script, the next fix lands in one copy and not the others, and the box running
the most expensive job is the one holding the stale copy. Nothing about that
failure looks wrong when you read either file.

⭐ So this asserts the SHAPE: the live pipelines source the helper and do not
carry their own copy of what it provides. And it PINS the scripts that have not
been converted, so the debt is a number somebody chose rather than a thing that
grew.
"""
import pathlib

import pytest

TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"
LIB = TOOLS / "pipeline_lib.sh"

#: The pipelines that source the helper. ⭐ These are the ones that can still be
#: launched; each is either running today or is the entry point for a locked
#: prereg.
LIVE = ("pipeline_retrain.sh", "pipeline_solo_regen.sh", "pipeline_fullft.sh",
        "pipeline_fullft_trace.sh")

#: ⚠️ THE DEBT, PINNED. Historical one-shots that already ran and still write the
#: marker themselves. Converting them is a re-verification nobody has paid for,
#: so they are recorded rather than silently tolerated — and this tuple is what
#: stops the list growing by one more script without a decision.
UNCONVERTED = (
    "pipeline_asymmetric_recert.sh",
    "pipeline_drift.sh",
    "pipeline_ki_target.sh",
    "pipeline_multiturn.sh",
    "pipeline_positive_control.sh",
    "pipeline_recipe_variance.sh",
    "pipeline_variance_decompose.sh",
)


def _text(name):
    return (TOOLS / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", LIVE)
def test_the_live_pipelines_source_the_helper(name):
    assert 'source "$(dirname "$0")/pipeline_lib.sh"' in _text(name)


@pytest.mark.parametrize("name", LIVE)
def test_no_live_pipeline_keeps_its_own_copy_of_the_scaffolding(name):
    """⛔⛔ THE POINT. A script that sources the helper AND keeps its own
    `trap`/watchdog/`touch ~/DONE` has two copies, and the one that runs is
    whichever appears later — which is exactly the drift, wearing the shape of
    the fix."""
    t = _text(name)
    for token, what in (
            ("trap 'rc=$?", "its own EXIT trap"),
            ("nohup $PY tools/act2_watchdog.py", "its own watchdog arming"),
            ("touch ~/DONE", "its own ~/DONE marker"),
            ('step() { STAGE=', "its own step() definition")):
        assert token not in t, "%s still contains %s" % (name, what)


def test_the_marker_is_written_in_exactly_one_place_among_the_live_set():
    """⛔⛔ `~/DONE` MEANS PERSISTED-AND-VERIFIED. The watchdog terminates within
    one poll of seeing it, so a second writer makes every verification advisory
    — which is the semantics both 2026-09-04 losses turned on."""
    # ⭐ The helper itself is the legitimate writer and is excluded by name,
    # not by a pattern that might also excuse a script called "..._lib.sh".
    writers = [p.name for p in TOOLS.glob("pipeline_*.sh")
               if p.name != LIB.name
               and "touch ~/DONE" in p.read_text(encoding="utf-8")]
    assert "touch ~/DONE" in _text(LIB.name), "the helper must write the marker"
    live_writers = [n for n in writers if n in LIVE]
    assert live_writers == [], (
        "live pipelines writing the marker themselves: %s" % live_writers)


def test_the_unconverted_list_is_exact_in_both_directions():
    """⛔ Checked BOTH ways. A one-directional check passes when someone adds a
    new unconverted pipeline (the debt grows silently) or when someone converts
    one and forgets to update the record (the debt looks larger than it is)."""
    actual = {p.name for p in TOOLS.glob("pipeline_*.sh")
              if p.name != LIB.name
              and "touch ~/DONE" in p.read_text(encoding="utf-8")}
    assert actual == set(UNCONVERTED), (
        "unconverted set drifted — added: %s · removed: %s"
        % (sorted(actual - set(UNCONVERTED)), sorted(set(UNCONVERTED) - actual)))


def test_the_helper_defines_what_the_live_pipelines_call():
    t = _text(LIB.name)
    for fn in ("tlon_trap_init", "tlon_log_init", "tlon_arm_watchdog",
               "tlon_mark_done", "tlon_gate_done", "step"):
        assert ("%s()" % fn) in t, "pipeline_lib.sh does not define %s" % fn


def test_the_full_weight_pipeline_arms_the_watchdog_before_the_floors():
    """⛔⛔ PREREG a0450b36 §8 / R5, AND IT IS A CHANGE FROM THE LoRA ARM. The
    safety net deploys before the risk: floors-first leaves the un-guarded idle
    window that leaked $0.75 twice. Anchored on the `step` lines, not on the
    first mention of either word — the header comment says both."""
    t = _text("pipeline_fullft.sh")
    assert t.index("step watchdog") < t.index("step syntax_floor")


def test_the_full_weight_pipeline_pins_the_corpus_sha_rather_than_recording_it():
    """⭐ Unlike the LoRA batch's new seeds, §5 names a KNOWN sha. Recording it
    would let a broken deterministic rebuild train on a different language and
    say so only in a log line nobody reads."""
    t = _text("pipeline_fullft.sh")
    assert "dd40e22f85b0b6e4" in t
    assert "CORPUS SHA MISMATCH" in t


def test_the_full_weight_pipeline_never_calls_the_factorial_entry_constructor():
    """⛔⛔ §0/§6: a `_w` object gets no cell and no pair key. `weight_arm_entry`
    is the only constructor that will build it."""
    t = _text("pipeline_fullft.sh")
    assert "weight_arm_entry" in t
    assert "factorial import entry" not in t


def test_every_live_pipeline_is_launchable_through_the_orchestrator():
    """⛔⛔ A LAUNCHER NOBODY CAN USE IS A LAUNCHER THAT GETS BYPASSED.

    `pipeline_fullft.sh` was live, tested and shipped for two rungs while
    `act2_retrain_orchestrate.PIPELINES` — the closed set of things `train` will
    start — did not contain it. So both runs were launched by a hand-rolled
    ssh, and the step that path skips is `. ~/.tlon_env`: the credential source
    the spawned watchdog needs to persist before it self-terminates.

    ⭐ The closed set exists because `--pipeline` is interpolated into a remote
    shell, so it must stay closed. This pins the OTHER direction — that it is
    also COMPLETE — so the guard cannot quietly force the bypass it exists to
    prevent."""
    import sys as _sys
    _sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
    from act2_retrain_orchestrate import PIPELINES
    for name in LIVE:
        if name == "pipeline_fullft_trace.sh":
            # ⚠️ Diagnostic-only and deliberately NOT launchable here: it takes
            # ablation switches (ATTN_IMPL, TRAIN_SEED, DUEL_AT) that `train`
            # has no flags for, so listing it would advertise a launch that
            # cannot carry the arguments that make the run mean anything.
            continue
        assert name in PIPELINES, (
            "%s is a live pipeline the orchestrator refuses to launch" % name)
