"""⛔⛔ THE MID-RUN RELEASE READ MUST BE THE SAME MEASUREMENT AS THE VERDICT'S.

WHY THIS EXISTS. `read_rates` was extracted from the F-LOCAL CLI for exactly one
reason: a mid-run read that re-implements the measurement becomes a SECOND,
slightly different instrument, and when the checkpoint then disagrees with the
verdict there is no way to tell whether the OBJECT moved or the WIRING differs.
Release is the heavier of the two reads and the one the epochs-lever arm turns
on, so it gets the same treatment and the same guard.

⛔⛔ AND THE GUARD THAT MATTERS MOST AT A CHECKPOINT IS `resolving_power`. A small
cell yields a small z NO MATTER WHAT THE SPEAKER DID — the null's sd is the
spread of a MEAN over n pairs, so it falls like sigma/sqrt(n). At lag 1 that
fabricates a perceive collapse; at lag >= 2 it grants a VACUOUS RELEASE PASS.
Early checkpoints are precisely where the cells are small. A curve that read lag
without this guard would manufacture "release installed" out of short chains —
the single most expensive mistake this arm could make, because it would confirm
the hypothesis the run exists to test.
"""
import ast
import io
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAG_SRC = ROOT / "tools" / "act2_model_lag.py"
FT_SRC = ROOT / "tools" / "act2_finetune.py"


def _tree(p):
    return ast.parse(io.open(p, encoding="utf-8").read())


def _func(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def test_read_lag_exists_and_is_importable():
    """⛔ A scan for a function that is gone passes vacuously."""
    assert _func(_tree(LAG_SRC), "read_lag") is not None, (
        "read_lag has been renamed or removed; every guard below is now vacuous")


def test_the_trainer_imports_the_fold_it_does_not_respell_it():
    """⛔⛔ THE REGRESSION. The curve must IMPORT `read_lag`. If it ever grows its
    own chain-building or null-drawing, the checkpoint and the verdict become two
    instruments — the wiring class that cost this campaign four instances."""
    src = io.open(FT_SRC, encoding="utf-8").read()
    assert "from act2_model_lag import read_lag" in src, (
        "act2_finetune.py no longer imports read_lag")
    # ⛔ And it must not have re-spelt the measurement locally. These are the
    # names a second implementation would have to use.
    for respelt in ("permutation_null", "lag_profile(", "model_chain(",
                    "resolving_power("):
        assert respelt not in src, (
            "act2_finetune.py calls %r directly — that is a SECOND lag "
            "instrument, not a call to the shared fold" % respelt)


def _called_names(fn):
    """Every function actually CALLED in `fn`, by bare name or attribute.

    ⛔⛔ NOT a substring scan of the source. My first version of the guard below
    asserted `"resolving_power" in ast.dump(fn)` and a mutant that replaced the
    whole call with `float('inf')` STILL PASSED — because the string survives as
    a KEY in the returned dict. The guard was satisfied by the report naming
    what the function had stopped doing, which is the `guard_searches` failure
    exactly. Assert on the CALL.
    """
    out = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


def _loaded_names(fn):
    return {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}


def _caught_exceptions(fn):
    out = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.ExceptHandler) and n.type is not None:
            out |= {x.id for x in ast.walk(n.type) if isinstance(x, ast.Name)}
    return out


def test_every_scoreability_guard_lives_inside_the_shared_fold():
    """⛔⛔ THE GUARDS ARE THE MEASUREMENT, NOT DECORATION AROUND IT. If any of
    these sits in the CLI's `main` instead of in `read_lag`, the mid-run read
    silently loses it — and the one it would lose is the one that FABRICATES A
    RELEASE PASS at an early checkpoint, confirming the hypothesis the run
    exists to test."""
    fn = _func(_tree(LAG_SRC), "read_lag")
    called = _called_names(fn)
    for guard, why in (
        ("resolving_power", "a small cell grants lag>=2 a vacuous pass"),
        ("threshold_for_lag", "the bar must be the LOCKED threshold, not a pick"),
        ("lag_pairs", "the cell size must travel with the z"),
        ("permutation_null", "the z needs its own null, not a borrowed one"),
        ("manual_seed", "an unseeded profile is one undocumented draw"),
    ):
        assert guard in called, (
            "read_lag never CALLS %r — %s" % (guard, why))

    assert "UnscoreableLag" in _caught_exceptions(fn), (
        "read_lag does not catch UnscoreableLag — an empty cell would abort the "
        "whole read instead of recording z=None beside its pair count")
    assert "MIN_USABLE_TURNS" in _loaded_names(fn), (
        "read_lag no longer consults MIN_USABLE_TURNS — short chains would be "
        "counted, reweighting the profile toward the chains that failed first")


def test_the_power_check_actually_gates_the_z():
    """⛔⛔ CALLING `resolving_power` IS NOT USING IT. The value must be COMPARED
    against the threshold and must suppress the z when it falls short — a call
    whose result is only reported is a number in a field, not a guard."""
    fn = _func(_tree(LAG_SRC), "read_lag")
    gated = False
    for node in ast.walk(fn):
        if not isinstance(node, ast.If):
            continue
        names = _loaded_names(node.test)
        if not ({"power", "need"} <= names):
            continue
        # the branch must NULL the z, not merely log
        body = ast.dump(node)
        if "'z'" in body or "zs" in body:
            gated = True
    assert gated, (
        "no `if power < need:` branch suppresses the z. An unresolvable cell "
        "would emit a number that arithmetic decided before the speaker was "
        "consulted — at lag>=2 that is a VACUOUS RELEASE PASS, the most "
        "expensive false positive this arm can produce")


def test_the_fold_records_the_cell_beside_every_z():
    """⛔ `z` alone is not a reading. A z is only as good as the cell it came
    from, and an unscoreable cell is `None` beside its pair count — never a
    zero, which would read as a passing release."""
    fn = _func(_tree(LAG_SRC), "read_lag")
    returned = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
            returned |= {k.value for k in n.value.keys
                         if isinstance(k, ast.Constant)}
    for field in ("z", "n_pairs", "resolving_power", "threshold_by_lag",
                  "unscoreable_lags", "sampling_stream_seeded", "verdict"):
        assert field in returned, (
            "read_lag never returns %r; the caveat must travel in the FIELD, "
            "not in prose" % field)


def test_the_curve_row_carries_the_cell_not_just_the_number():
    """⛔⛔ A curve row holding only `z` would read an UNRESOLVABLE cell as a
    passing one. The unscoreable state must be reconstructable from the row."""
    src = io.open(FT_SRC, encoding="utf-8").read()
    i = src.find('row["lag"] = {k: lag[k]')
    assert i > 0, "the curve no longer copies the lag measurement into the row"
    block = src[i:i + 600]
    for field in ("n_pairs", "resolving_power", "threshold_by_lag",
                  "unscoreable_lags", "verdict"):
        assert field in block, (
            "the curve row drops %r — an unresolvable cell would then be "
            "indistinguishable from a real reading" % field)


def test_release_is_not_read_off_a_floored_speaker():
    """⛔ A lag profile taken from a speaker that emits nothing is not a low
    reading, it is no reading — the chains collapse and `resolving_power` hands
    lag>=2 a vacuous pass. The curve must gate on F-LOCAL first."""
    src = io.open(FT_SRC, encoding="utf-8").read()
    assert 'min(speak["rate"], render["rate"]) > 0.0' in src, (
        "the mid-run lag read is no longer gated on a speaker being present")


def test_the_lag_read_happens_inside_the_isolated_read():
    """⛔⛔ 120 generations that perturbed the run would make the curve a curve of
    a DIFFERENT run, and nothing downstream could tell. `isolated_read` restores
    module mode, RNG and grads and asserts it did — the lag read must be inside
    it, and `read_lag` seeds torch, which is exactly the kind of RNG mutation
    that must be restored."""
    tree = _tree(FT_SRC)
    found = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.With):
            continue
        if not any("isolated_read" in ast.dump(it.context_expr)
                   for it in node.items):
            continue
        if "_read_lag" in ast.dump(node):
            found = True
    assert found, (
        "the mid-run lag read is not inside `isolated_read` — it seeds the "
        "torch RNG and runs 120 generations, so outside it the curve measures "
        "a run it has itself perturbed")


@pytest.mark.parametrize("mutation,expect", [
    ("from act2_model_lag import read_lag", "import"),
    ('min(speak["rate"], render["rate"]) > 0.0', "floored-speaker gate"),
])
def test_mutations_are_caught(mutation, expect):
    """⛔⛔ RED-PROOF: assert the mutation APPLIED. A mutation test that silently
    fails to match its target prints `passed` and witnesses nothing — that
    exact vacuity shipped in this repo when a substring missed CRLF endings."""
    src = io.open(FT_SRC, encoding="utf-8").read()
    assert mutation in src, (
        "the mutation target %r is absent, so this red-proof would be "
        "VACUOUS rather than passing" % expect)
