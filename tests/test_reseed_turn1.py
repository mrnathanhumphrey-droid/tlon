"""⛔⛔ THE RESEED PROBE'S PURE PARTS — selection, and what a retry would buy.

The arithmetic here decides whether the next spend is $6 of training or a few
lines in the server, so it is the part that must not be wrong.
"""
from __future__ import annotations

import importlib
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

RS = importlib.import_module("act2_reseed_turn1")


@pytest.fixture(autouse=True)
def expanded_lexicon(monkeypatch):
    from tlon.grammar import classes as C
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.reset_caches()
    yield
    C.reset_caches()


def turn(depth, carried, prov="nu hlör pön"):
    return {"depth": depth, "carried": carried, "provocation": prov}


def ledger(*convs):
    return {"items": [{"id": "c%d" % i, "theme": "t", "turns": list(ts)}
                      for i, ts in enumerate(convs)]}


# ── selection ───────────────────────────────────────────────────────────────

def test_only_the_first_exchange_is_taken():
    """⛔ A deeper turn carries context. The finding is about the exchange that
    has NONE — the one shown to decide the rest."""
    rows = RS.load_turn1(ledger([turn(0, True), turn(1, False), turn(2, True)]))
    assert len(rows) == 1 and rows[0]["baseline_carried"] is True


def test_an_unscorable_baseline_turn_is_dropped_not_counted_as_a_miss():
    """⛔⛔ THE DENOMINATOR TRAP. A refused turn has no provocation to resample.
    Counting it as a miss would charge the RETRY for the baseline's refusals
    and understate what a retry buys."""
    rows = RS.load_turn1(ledger([turn(0, None)], [turn(0, False)],
                                [{"depth": 0, "carried": False,
                                  "provocation": None}]))
    assert len(rows) == 1
    assert rows[0]["baseline_carried"] is False


# ── the arithmetic ──────────────────────────────────────────────────────────

def rows_with(missed_flags, hit_flags):
    out = []
    for f in missed_flags:
        out.append({"baseline_carried": False, "attempts": f})
    for f in hit_flags:
        out.append({"baseline_carried": True, "attempts": f})
    return out


def test_a_retry_only_rescues_the_misses():
    """⛔⛔ THE FORMULA THAT MUST NOT BE `1-(1-p)^k`. The server retries ONLY
    when the first reply missed, so the conversations that already carried are
    untouched. Treating every draw as a fresh coin would overstate the gain.

    Here: baseline 0.50 (2 hit, 2 missed), and half the misses are rescued.
    New p1 = 0.50 + 0.50*0.50 = 0.75 -- NOT 1-(0.5)^4.
    """
    rows = rows_with([[True, False], [False, False]],
                     [[True, True], [True, False]])
    s = RS.summarise(rows, k=2)
    assert s["baseline_p1"] == 0.5
    assert s["missed"]["rate"] == 0.5
    assert s["projected_p1_with_retry"] == 0.75


def test_no_rescue_leaves_the_joint_exactly_where_it_was():
    """⭐ THE NULL. If the provocation decides, every resample of a missed one
    misses too, and the projection must not drift upward by construction."""
    rows = rows_with([[False, False, False]] * 4, [[True, True, True]] * 4)
    s = RS.summarise(rows, k=3)
    assert s["missed"]["rate"] == 0.0
    assert s["projected_p1_with_retry"] == s["baseline_p1"]
    assert s["projected_joint"] == s["baseline_joint"]


def test_total_rescue_takes_turn_one_to_certainty():
    rows = rows_with([[True]] * 3, [[True]] * 3)
    s = RS.summarise(rows, k=1)
    assert s["projected_p1_with_retry"] == 1.0


def test_the_joint_uses_the_measured_conditional_not_independence():
    """⛔⛔ THE JOINT IS NOT `1-(1-p1)^3`. The onset baseline measured
    P(>=1 carry in turns 2-3 | turn 1 missed) = 0.3325, far below what
    independence implies, because the mode LOCKS. Using independence here
    would promise a reach the measurement refutes.
    """
    rows = rows_with([[False]] * 5, [[True]] * 5)
    s = RS.summarise(rows, k=1)
    p1 = s["baseline_p1"]
    assert s["baseline_joint"] == pytest.approx(p1 + (1 - p1) * 0.3325, abs=1e-4)
    # independence would have claimed materially more
    assert s["baseline_joint"] < 1 - (1 - p1) ** 3


def test_per_attempt_rate_is_reported_for_both_groups():
    """⭐ THE DISCRIMINATING STATISTIC. Decode variance puts the MISS group's
    per-attempt rate near the baseline; a provocation-determined miss puts it
    near zero. The 'any of k' rate alone cannot tell those apart at small k."""
    rows = rows_with([[True, False, False]], [[True, True, True]])
    s = RS.summarise(rows, k=3)
    assert s["missed"]["per_attempt"] == pytest.approx(1 / 3, abs=1e-4)
    assert s["hit"]["per_attempt"] == 1.0


def test_a_replay_ledger_is_refused(tmp_path, monkeypatch):
    """⛔⛔ A --replay ledger's `carried` flags are the CORPUS's, not the
    model's. Resampling against them would compare the model to a transcript
    and the rescue rate would be meaningless."""
    import json
    p = tmp_path / "replay.json"
    p.write_text(json.dumps({"replay": True, "items": []}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["x", "--ledger", str(p)])
    with pytest.raises(SystemExit) as exc:
        RS.main()
    assert "replay" in str(exc.value)


def test_speaker_exposes_the_seam_the_probe_drives():
    """⛔ `reply_to` must be EXTRACTED from `turn`, not a second copy of it. If
    `turn` stopped calling it, the probe would measure a path the product no
    longer serves."""
    import ast
    body = (ROOT / "puzzle" / "speaker.py").read_text(encoding="utf-8")
    tree = ast.parse(body)
    cls = next(n for n in ast.walk(tree)
               if isinstance(n, ast.ClassDef) and n.name == "Speaker")
    names = {n.name for n in cls.body if isinstance(n, ast.FunctionDef)}
    assert "reply_to" in names
    turn_fn = next(n for n in cls.body
                   if isinstance(n, ast.FunctionDef) and n.name == "turn")
    calls = {n.func.attr for n in ast.walk(turn_fn)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "reply_to" in calls, (
        "⛔⛔ turn() no longer calls reply_to — the probe would be measuring a "
        "path the product does not serve")
