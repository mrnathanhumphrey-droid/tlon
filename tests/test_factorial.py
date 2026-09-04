"""⛔⛔ THE FACTORIAL'S STRUCTURAL GUARANTEES — the matrix, not the pile.

An army of adapters is only analysable if every contrast changes ONE knob. The
three properties that make that true are not obvious from reading any single
file, so they are asserted here:

  1. **Matched seeds give matched force sequences.** content-free-seed-X and
     content-transient-seed-X must differ in content and in NOTHING ELSE.
  2. **Both recipes come from one generator.** The control is `responsiveness=0`
     on the same code path, not a second generator that could drift.
  3. **Every pipeline names its recipe explicitly.** An adapter whose recipe is
     implicit belongs to no cell and cannot be paired.

⛔⛔ PROPERTY 1 WAS FALSE WHEN FIRST CLAIMED, AND THE CLAIM WAS CHECKED THE WRONG
WAY. It was verified by comparing `chain_transient(1.0)` against
`chain_transient(0.0)` -- both on the NEW path -- while the builder's control arm
actually ran `multiturn.build`, which draws force and content from ONE RNG
stream. The force multisets did not match. A green check on the wrong pair.
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from tlon.discourse import transient as TR                      # noqa: E402

PIPELINES = ("tools/pipeline_retrain.sh", "tools/pipeline_recipe_variance.sh")

#: ⛔⛔ THE SCOPE WIDENED, SO THE RULE IS RE-DERIVED RATHER THAN STRETCHED. The
#: fragile-handler defect was found in one pipeline and was present in SEVEN of
#: eight — including `pipeline_positive_control.sh`, which had not run yet. A
#: guard scoped to the file where a defect was noticed only ever catches that
#: file again.
ALL_PIPELINES = sorted(p.as_posix()
                       for p in (_ROOT / "tools").glob("pipeline_*.sh"))


# ── 1 · matched seeds, matched forces ──────────────────────────────────────

@pytest.mark.parametrize("seed", (20624, 20629))
def test_matched_seeds_give_IDENTICAL_force_sequences_across_recipes(seed):
    """⛔⛔ THE PAIRED DESIGN. If the force sequence moves with the recipe, the
    two arms differ in two variables and no difference between them is
    attributable to content."""
    from tlon.act2 import corpus as C1
    pairs = C1.build(300, seed=seed)
    # ⛔ Sized so `check_force_pair_fairness` is satisfied. A smaller fixture
    # starves a live cell and the run fails on COVERAGE, which would look like a
    # pairing failure and is a different thing entirely.
    kw = dict(turns=10, pairs=pairs, seed=seed, verify=False)
    a = TR.build_transient(200, responsiveness=1.0, **kw)
    b = TR.build_transient(200, responsiveness=0.0, **kw)
    fa = [t.force for ch in a for t in ch]
    fb = [t.force for ch in b for t in ch]
    assert fa == fb, "responsiveness perturbed the force sequence"
    sa = [t.surface for ch in a for t in ch]
    sb = [t.surface for ch in b for t in ch]
    assert sa != sb, "content did not move — the recipes are not distinguishable"


def test_the_control_arm_is_REACHABLE_FROM_THE_SAME_GENERATOR():
    """⭐ `responsiveness=0` must BE the control, so the arms cannot drift the
    way two separate generators would."""
    import inspect
    src = inspect.getsource(TR.chain_transient)
    assert "rng_content" in src, "the content stream is not separated"
    assert "responsiveness" in src


def test_the_two_rng_streams_are_SEPARATE_in_build_transient():
    """⛔ One stream is the defect: the responsive branch consumes a different
    amount of randomness than the flat branch, so the FORCE draw downstream
    diverges between arms at the same seed."""
    import inspect
    src = inspect.getsource(TR.build_transient)
    assert src.count("random.Random(") >= 2, \
        "build_transient uses a single RNG; force and content are coupled"


# ── 2 · the recipe vocabulary is defined once ─────────────────────────────

def test_the_recipe_names_are_defined_ONCE_and_imported():
    """⛔ A recipe label spelt separately in the builder, the manifest and the
    adapter filename is three chances to disagree, and the matrix is
    reconstructed from exactly those strings."""
    assert TR.RECIPES == (TR.CONTENT_FREE, TR.CONTENT_TRANSIENT)
    # ⛔⛔ THE DOSE ARM IS DELIBERATELY OUTSIDE `RECIPES`. `tlon.act2.factorial`
    # validates every recipe against that tuple, so `content-persistent` cannot
    # become a cell, be labelled, or be paired. That exclusion IS the quarantine
    # and it has to stay structural rather than conventional.
    assert TR.CONTENT_PERSISTENT not in TR.RECIPES
    assert TR.ALL_RECIPES == TR.RECIPES + (TR.CONTENT_PERSISTENT,)
    builder = (_ROOT / "tools/act2_build_multiturn.py").read_text(encoding="utf-8")
    assert "TR.CONTENT_FREE" in builder and "TR.CONTENT_TRANSIENT" in builder
    assert 'choices=TR.ALL_RECIPES' in builder, \
        "the builder re-spells the recipe names instead of importing them"


def test_the_builder_REQUIRES_an_explicit_recipe():
    """⛔⛔ NO DEFAULT. A defaulted recipe makes every historical build's arm a
    matter of inference rather than record."""
    builder = (_ROOT / "tools/act2_build_multiturn.py").read_text(encoding="utf-8")
    m = re.search(r'add_argument\("--recipe".*?\)', builder, re.S)
    assert m, "the builder has no --recipe argument"
    assert "required=True" in m.group(0)
    assert "default=" not in m.group(0)


# ── 3 · ⛔ the pipelines, which is where an implicit recipe would hide ─────

@pytest.mark.parametrize("path", PIPELINES)
def test_every_pipeline_names_its_recipe_EXPLICITLY(path):
    """⛔⛔ An adapter whose recipe is implicit belongs to no cell of the matrix
    and cannot be paired with its matched seed in the other arm."""
    src = (_ROOT / path).read_text(encoding="utf-8")
    for line in src.splitlines():
        if "act2_build_multiturn.py" in line and not line.strip().startswith("#"):
            assert "--recipe" in line, \
                "%s invokes the corpus builder without naming a recipe" % path
            if any(r in line for r in TR.RECIPES):
                break                       # a literal recipe — unambiguous
            # ⭐ A SHELL VARIABLE IS ALSO FINE, BUT ONLY IF IT HAS NO DEFAULT.
            # `--recipe $RECIPE` with `RECIPE=${RECIPE:?…}` is stronger than a
            # literal: one pipeline serves both arms and neither can be reached
            # by forgetting to set it. `RECIPE=${RECIPE:-content-free}` would be
            # the opposite — a default that silently files a batch in an arm.
            m = re.search(r"--recipe\s+\$\{?(\w+)", line)
            assert m, "%s: --recipe has neither a literal nor a variable" % path
            var = m.group(1)
            assert re.search(r"^%s=\$\{%s:\?" % (var, var), src, re.M), (
                "%s: --recipe uses $%s, but %s is not declared required "
                "(${%s:?...}). A defaulted recipe files a batch in an arm "
                "nobody chose." % (path, var, var, var))
            break
    else:
        pytest.skip("%s does not build a corpus" % path)


@pytest.mark.parametrize("path", ALL_PIPELINES)
def test_an_EXIT_trap_cannot_depend_on_variables_set_after_it(path):
    """⛔⛔ The trap is armed before $STAGE/$LOG exist. Under `set -u` a bare
    $STAGE makes the HANDLER fail on any early exit -- and the handler is the
    only thing that reports why the run stopped, so its own failure erases the
    diagnosis exactly when there is one to report."""
    src = (_ROOT / path).read_text(encoding="utf-8")
    # ⛔ The handler is sometimes an inline `trap '...' EXIT` and sometimes a
    # `finish()` function -- scoping this to the inline form would have missed
    # pipeline_act2.sh, which carries the same defect in the other shape.
    for line in src.splitlines():
        if "FAILED at stage" not in line:
            continue
        assert "${STAGE:" in line, (
            "%s: the failure handler dereferences $STAGE without a default. It "
            "is armed BEFORE $STAGE exists, so under `set -u` the handler dies "
            "on an early exit -- erasing the diagnosis exactly when there is "
            "one to report. Offending line: %s" % (path, line.strip()))


@pytest.mark.parametrize("path", PIPELINES)
def test_no_LITERAL_backslash_n_in_a_shell_script(path):
    """⛔⛔ A BUG I SHIPPED INTO THESE FILES AND `bash -n` PASSED ANYWAY.

    An edit wrote the two characters `\\` `n` where a line continuation was
    meant. To the shell that is an escaped `n` -- a literal `n` argument -- so
    the script is SYNTACTICALLY VALID and fails only at run time, on a box, in a
    stage that has already cost GPU hours. `bash -n` is not the instrument that
    catches this; a byte check is.
    """
    raw = (_ROOT / path).read_bytes()
    bad = (chr(92) + "n").encode()
    assert bad not in raw, (
        "%s contains a literal backslash-n; the shell reads it as an argument "
        "'n' and the pipeline fails at run time, not at parse time" % path)


@pytest.mark.parametrize("path", PIPELINES)
def test_the_pipeline_seeds_are_RECORDED_so_pairs_are_reconstructable(path):
    """⛔ The matched-pair rule needs the seeds to be replicable from the repo,
    not from a terminal scrollback that is already gone."""
    src = (_ROOT / path).read_text(encoding="utf-8")
    assert "--seed" in src, "%s does not pass a seed" % path
    assert re.search(r'(NEW|SEEDS|BUILDS)=\"[0-9 ]+\"', src), \
        "%s has no literal seed list; the batch cannot be matched later" % path
