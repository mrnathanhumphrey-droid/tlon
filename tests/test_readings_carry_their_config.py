"""⭐⭐ THE ONE TEST THAT WOULD HAVE CAUGHT THREE OF THE FOUR.

`epochlevB-s20624`, 2026-09-16, trained 3,760 clean steps and then lost its
end-of-run reads, failed to terminate, silently flushed two patterns that
matched nothing, and recorded its entire in-training lag curve through a GREEDY
decoder. All four were green at the level of configuration.

The generalisation, and it is the arc's: **do not assert that the config should
produce the right reading — assert that the reading carries the right config.**
A declaration can be correct while the wiring is wrong, and only the artefact
knows which happened.

⛔⛔ AND THE GUARD ITSELF IS MUTATION-PROVED, because the last four guards in
this campaign were not, and each one passed while the thing it guarded was
broken:
  * `guard_searches` — a substring search satisfied by a surviving dict key;
  * the pooled §4.1 gate — pinned at 0.5122 and believed because it was a
    plausible middle;
  * `test_lag_read_is_one_fold` — proved the fold was shared while the
    INSTRUMENT the fold ran on drifted;
  * `terminate_reachable` — certified a kill path it had never travelled.
Every mutant below is a real bug this campaign shipped, replayed.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "tools"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import act2_audit_readings as A                                # noqa: E402
import act2_model_lag as ML                                    # noqa: E402


# ── a run tree shaped like the one the pipeline actually writes ─────────────

def build_run(tmp_path, *, cell="epochlevB-s20624", nest_weight_delta=True,
              lag_temp=ML.LAG_TEMPERATURE, lag_tok=ML.LAG_MAX_NEW_TOKENS,
              curve_carries_decoder=True, rows=3):
    """⭐ The REAL layout, including the part that caused the bug: the trainer
    writes `weight_delta.json` and `factorial.json` into `$ROOT/model_<cell>/`,
    one directory DOWN from where the flush used to look."""
    root = tmp_path / ("fullft_%s" % cell)
    model = root / ("model_%s" % cell)
    model.mkdir(parents=True)

    (root / "pipeline_fullft.log").write_text("run log\n", encoding="utf-8")
    (root / "base_audit.json").write_text("{}", encoding="utf-8")
    (root / "eos_guard.json").write_text("{}", encoding="utf-8")
    (root / ("verdict_%s_e1.json" % cell)).write_text(
        json.dumps({"verdict": "STOP — floored"}), encoding="utf-8")
    (root / ("model_lag_%s_e1.json" % cell)).write_text(
        json.dumps({"verdict": "REFUSED", "z": {"2": 4.34},
                    "temperature": lag_temp, "max_new_tokens": lag_tok}),
        encoding="utf-8")

    where = model if nest_weight_delta else root
    (where / "weight_delta.json").write_text(
        json.dumps({"verdict": "OK", "delta_norm_estimated": 18.34,
                    "n_trainable_params": 3489792000}), encoding="utf-8")
    (where / "factorial.json").write_text("{}", encoding="utf-8")

    lines = []
    for i in range(rows):
        lag = {"verdict": "REFUSED", "z": {"2": 4.0 + i}}
        if curve_carries_decoder:
            lag["temperature"] = lag_temp
            lag["max_new_tokens"] = lag_tok
        lines.append(json.dumps({"step": 235 * (i + 1), "rms": 1e-4, "lag": lag}))
    (root / ("dose_curve_%s.jsonl" % cell)).write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    return root


def test_a_correct_run_passes(tmp_path):
    """⛔ The control. A guard that cannot pass is not a guard, it is an
    outage — and every mutant below is only meaningful against this."""
    bad, lines = A.audit(build_run(tmp_path))
    assert bad == 0, "\n".join(lines)


# ── MUTANT 1 · the in-training curve carries no decoder ────────────────────
# THE ACTUAL BUG. Every dose_curve row this campaign wrote was in this state,
# and every one of them was wrong. "No decoder recorded" must fail, because a
# reading that cannot be checked is exactly the one that was silently broken.

def test_MUTANT_curve_rows_without_a_decoder_are_REFUSED(tmp_path):
    bad, lines = A.audit(build_run(tmp_path, curve_carries_decoder=False))
    assert bad >= 3, "\n".join(lines)
    assert any("NO DECODER RECORDED" in ln for ln in lines), "\n".join(lines)


# ── MUTANT 2 · the curve was read GREEDY ───────────────────────────────────
# The mechanism. temperature 0.0 sets do_sample=False, the speaker becomes
# deterministic, and content "persists" because the same context yields the
# same continuation. This is the reading that must never pass as a result.

def test_MUTANT_a_greedy_lag_reading_is_REFUSED(tmp_path):
    bad, lines = A.audit(build_run(tmp_path, lag_temp=0.0))
    assert bad >= 1, "\n".join(lines)
    assert any("GREEDY" in ln for ln in lines), "\n".join(lines)


# ── MUTANT 3 · a decoder that is sampled but NOT the campaign's ────────────
# ⛔ Not the bug that fired, but the one that makes results quietly
# incomparable: 0.9 is not greedy and is not 0.7, and a run read at 0.9 cannot
# sit in a table with the rest.

def test_MUTANT_a_different_sampled_decoder_is_REFUSED(tmp_path):
    bad, lines = A.audit(build_run(tmp_path, lag_temp=0.9))
    assert bad >= 1, "\n".join(lines)
    assert any("not comparable" in ln for ln in lines), "\n".join(lines)


# ── MUTANT 4 · the flush glob goes back to one level ───────────────────────
# ⛔⛔ THE SILENT ONE. `weight_delta*.json` and `factorial.json` sit in
# `model_<cell>/`, so a non-recursive sweep matches NOTHING and says nothing.
# The mutant replaces the recursion, and the audit must notice the absence.

def test_MUTANT_a_non_recursive_sweep_is_CAUGHT(tmp_path, monkeypatch):
    root = build_run(tmp_path, nest_weight_delta=True)

    def one_level(r):
        return {p: sorted(x.relative_to(r).as_posix()
                          for x in r.glob(p) if x.is_file())
                for p in A.FLUSH_PATTERNS}

    monkeypatch.setattr(A, "sweep", one_level)
    bad, lines = A.audit(root)
    assert bad >= 2, "\n".join(lines)
    assert any("weight_delta" in ln and "MATCHED NOTHING" in ln
               for ln in lines), "\n".join(lines)
    assert any("factorial.json" in ln and "MATCHED NOTHING" in ln
               for ln in lines), "\n".join(lines)


# ── MUTANT 5 · the persist step never ran at all ───────────────────────────
# What bug 1 looked like from here: `flush --cell` exited 2, the run aborted,
# and the reads were never written. Absence of the verdict and the lag file is
# the signature, and it must not be mistaken for "nothing to do".

def test_MUTANT_a_run_that_lost_its_reads_is_CAUGHT(tmp_path):
    root = build_run(tmp_path)
    (root / "verdict_epochlevB-s20624_e1.json").unlink()
    (root / "model_lag_epochlevB-s20624_e1.json").unlink()
    bad, lines = A.audit(root)
    assert bad >= 2, "\n".join(lines)
    assert any("verdict_*.json" in ln and "MATCHED NOTHING" in ln
               for ln in lines), "\n".join(lines)


# ── MUTANT 6 · no lag reading at all ───────────────────────────────────────
# ⛔⛔ THE VACUOUS PASS. An audit whose lag section iterates an empty list
# reports nothing wrong. A release run with no release reading is the most
# complete failure there is, so it is named explicitly.

def test_MUTANT_an_empty_lag_set_does_not_pass_VACUOUSLY(tmp_path):
    root = build_run(tmp_path)
    (root / "model_lag_epochlevB-s20624_e1.json").unlink()
    (root / "dose_curve_epochlevB-s20624.jsonl").unlink()
    bad, lines = A.audit(root)
    assert bad >= 1, "\n".join(lines)
    assert any("NO LAG READING FOUND AT ALL" in ln for ln in lines), \
        "\n".join(lines)


# ── the fold's own contract ────────────────────────────────────────────────

class _Backend:
    """⭐ An F-LOCAL backend, exactly as `LocalBackend.adopt()` builds it: 220
    tokens, temperature 0.0. This is the object the in-training curve hands to
    `read_lag`, and handing it over unchanged is what voided the curve."""

    def __init__(self):
        self.temperature = 0.0
        self.max_new_tokens = 220


def test_read_lag_REFUSES_greedy_rather_than_recording_it(tmp_path):
    with pytest.raises(ValueError) as e:
        ML.read_lag(_Backend(), temperature=0.0)
    assert "GREEDY" in str(e.value)


def test_read_lag_INSTALLS_its_own_decoder_on_a_borrowed_backend(monkeypatch):
    """⛔⛔ THE FIX FOR THE BUG ITSELF. `read_lag` must not inherit whatever the
    borrowed backend carries — F-LOCAL's 220/greedy — it must install the
    sampled decoder a lag read requires."""
    b = _Backend()
    seen = {}

    def spy(backend, **kw):
        seen["temperature"] = backend.temperature
        seen["max_new_tokens"] = backend.max_new_tokens
        return {"verdict": "REFUSED", "z": {}, "lag_profile": {}}

    monkeypatch.setattr(ML, "_read_lag_inner", spy)
    out = ML.read_lag(b)
    assert seen == {"temperature": ML.LAG_TEMPERATURE,
                    "max_new_tokens": ML.LAG_MAX_NEW_TOKENS}
    assert out["temperature"] == ML.LAG_TEMPERATURE
    assert out["max_new_tokens"] == ML.LAG_MAX_NEW_TOKENS


def test_read_lag_PUTS_THE_BORROWED_DECODER_BACK(monkeypatch):
    """⛔ The curve borrows a backend the TRAINER owns and that F-LOCAL reads
    through at its own settings. A lag read that left 0.7/256 installed would
    silently change every later F-LOCAL rate read in the same run — the same
    discipline `isolated_read` applies to training mode and RNG state."""
    b = _Backend()
    monkeypatch.setattr(ML, "_read_lag_inner",
                        lambda backend, **kw: {"verdict": "REFUSED"})
    ML.read_lag(b)
    assert (b.temperature, b.max_new_tokens) == (0.0, 220)


def test_the_decoder_is_restored_even_when_the_read_RAISES(monkeypatch):
    """⛔ Restoration on the failure path too — a read that dies mid-chain must
    not leave the trainer's backend reconfigured behind it."""
    b = _Backend()

    def boom(backend, **kw):
        raise RuntimeError("chain collapsed")

    monkeypatch.setattr(ML, "_read_lag_inner", boom)
    with pytest.raises(RuntimeError):
        ML.read_lag(b)
    assert (b.temperature, b.max_new_tokens) == (0.0, 220)


def test_the_audit_sweep_uses_THE_SAME_recursion_as_the_flush():
    """⛔⛔ If this tool's sweep and the real flush ever disagree, the tool
    certifies a sweep that does not happen — which is precisely the class of
    bug it exists to catch, one level out. Asserted on the SOURCE, because a
    behavioural check would need a live hub."""
    import ast
    import inspect
    import act2_box_persist as BP
    flush = ast.parse(inspect.getsource(BP.cmd_flush))
    calls = {n.func.attr for n in ast.walk(flush)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "rglob" in calls, "cmd_flush no longer recurses"
    assert "glob" not in calls, "cmd_flush is sweeping ONE LEVEL again"
    audit = ast.parse(inspect.getsource(A.sweep))
    acalls = {n.func.attr for n in ast.walk(audit)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "rglob" in acalls and "glob" not in acalls


# ── the row must carry what the fold recorded ──────────────────────────────

def test_the_curve_ROW_carries_every_field_read_lag_RECORDS():
    """⛔⛔ THE FIX WAS CORRECT AT THE MEASUREMENT AND LOST AT THE SERIALISATION.

    `read_lag` was fixed to record its decoder. `act2_finetune` then copied a
    HAND-WRITTEN LIST of eleven keys into the dose-curve row — and
    `temperature`, `max_new_tokens` and `decoder_sampled` were not among them.
    Every row of the re-run would have carried no decoder, and the §2.3 audit
    gate would have refused the run after eleven hours of training: the gate
    working, at maximum cost. Caught before firing only because the question
    'does the fixed path actually reach the artefact?' was asked out loud.

    ⭐ Asserted structurally: the row must take the WHOLE dict, never a subset.
    A list of fields is a list, and this repo's standing lesson is to sweep by
    scan rather than by list — so a field added to `read_lag` travels on its own
    rather than waiting for someone to remember one line in another file.
    """
    import ast
    import io as _io
    src = _io.open(ROOT / "tools" / "act2_finetune.py", encoding="utf-8").read()
    tree = ast.parse(src)

    assigns = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Assign):
            continue
        for t in n.targets:
            if (isinstance(t, ast.Subscript)
                    and isinstance(t.value, ast.Name) and t.value.id == "row"
                    and isinstance(t.slice, ast.Constant)
                    and t.slice.value == "lag"):
                assigns.append(n.value)
    assert assigns, "nothing assigns row['lag'] — this guard would be vacuous"

    for v in assigns:
        # ⛔ A DictComp over a literal tuple of names is the defect: it is a
        # hand-written whitelist, and whatever is not on it is silently dropped.
        assert not isinstance(v, ast.DictComp), (
            "row['lag'] is built from a hand-written key list; a field "
            "read_lag records (the DECODER, among others) would be dropped "
            "silently — take the whole dict")


def test_the_decoder_REACHES_the_row_not_only_the_fold(monkeypatch):
    """⭐ The behavioural twin of the structural check above: what `read_lag`
    returns is what a consumer must be able to read back."""
    b = _Backend()
    monkeypatch.setattr(ML, "_read_lag_inner",
                        lambda backend, **kw: {"verdict": "REFUSED", "z": {}})
    out = ML.read_lag(b)
    row_lag = dict(out)          # exactly what act2_finetune now writes
    for k in ("temperature", "max_new_tokens", "decoder_sampled"):
        assert k in row_lag, (
            "%r does not survive into the dose-curve row; the audit gate would "
            "read NO DECODER RECORDED and refuse the run" % k)
    assert row_lag["temperature"] == ML.LAG_TEMPERATURE
