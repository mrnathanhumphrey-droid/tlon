"""Tests for the ki-as-target ordering lock and the locked readings.

⛔⛔ THE POINT: the throughput fallback CHANGES THE MDE (0.040 → 0.060) and
therefore changes what counts as PARTIAL vs UNDERPOWERED. That is legitimate only
if the branch was committed BEFORE any relief datum existed. These tests exercise
the refusals that make the ordering unforgeable rather than promised — an arm
generated before the commitment cannot carry its hash.
"""
from __future__ import annotations

import json
import pathlib
import random
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from act2_ki_target_analyse import (                               # noqa: E402
    Refuse, exchange_rate, load_arm, welch)
from tlon.act2 import corpus as C1                                 # noqa: E402
from tlon.discourse import force_map as FM                         # noqa: E402
from tlon.grammar.parse import parse, render                       # noqa: E402

ROWS = set(FM.COMMON_UNIFORM_ROWS)


@pytest.fixture(scope="module")
def pool():
    """Real round-tripping surfaces indexed by force — synthetic transcripts must
    survive the same one-place oracle the analyser applies."""
    out = {f: [] for f in FM.ORDER}
    for p in C1.build(700, seed=5):
        s = getattr(p, "surface", None)
        if not s:
            continue
        try:
            sc = parse(s)
        except Exception:                                          # noqa: BLE001
            continue
        if render(sc) == s and sc.force in out:
            out[sc.force].append(s)
    assert all(out[f] for f in FM.ORDER), "pool is missing a force"
    return out


def write_arm(path, pool, *, ki_rate, sha, turns=40, seed=0):
    """An exchange whose `ki`-after-common-row rate is approximately `ki_rate`."""
    rng = random.Random(seed)
    common = list(FM.COMMON_UNIFORM_ROWS)
    others = [f for f in FM.ORDER if f != "ki"]
    forces, prev = [], rng.choice(common)
    forces.append(prev)
    for _ in range(turns - 1):
        if prev in ROWS and rng.random() < ki_rate:
            nxt = "ki"
        else:
            nxt = rng.choice(others)
        forces.append(nxt)
        prev = nxt
    surfaces, used = [], set()
    for f in forces:
        cands = [s for s in pool[f] if s not in used] or pool[f]
        s = rng.choice(cands)
        used.add(s)
        surfaces.append(s)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {"temperature": 0.9, "turns": turns, "commitment_sha": sha,
            "transcript_interacting": surfaces, "transcript_control": surfaces}
    path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")


# ── the ordering lock ─────────────────────────────────────────────────────────
def test_arm_without_a_commitment_sha_is_REFUSED(tmp_path, pool):
    """⭐ This is exactly the shape of an arm generated BEFORE the branch was
    committed — the timing-discard exchanges are precisely these."""
    write_arm(tmp_path / "treat_1.json", pool, ki_rate=0.1, sha=None, seed=1)
    with pytest.raises(Refuse, match="commitment sha"):
        load_arm([tmp_path / "treat_1.json"], ROWS, label="T",
                 commitment="abc123", expect_n=1)


def test_arm_with_a_STALE_commitment_sha_is_REFUSED(tmp_path, pool):
    """A commitment that changed after the arms ran is equally uninterpretable."""
    write_arm(tmp_path / "treat_1.json", pool, ki_rate=0.1, sha="OLD", seed=2)
    with pytest.raises(Refuse, match="commitment sha"):
        load_arm([tmp_path / "treat_1.json"], ROWS, label="T",
                 commitment="NEW", expect_n=1)


def test_matching_commitment_is_ACCEPTED(tmp_path, pool):
    """The lock must also pass — a guard that only ever refuses is a dead guard."""
    write_arm(tmp_path / "treat_1.json", pool, ki_rate=0.1, sha="OK", seed=3)
    arm = load_arm([tmp_path / "treat_1.json"], ROWS, label="T",
                   commitment="OK", expect_n=1)
    assert arm["rates"] and 0.0 <= arm["mean"] <= 1.0


def test_arm_count_below_the_committed_N_is_REFUSED(tmp_path, pool):
    """⛔ Reporting fewer exchanges than committed is a design chosen after the
    fact — the optional-stopping shape the whole lock exists to prevent."""
    for i in range(3):
        write_arm(tmp_path / f"treat_{i}.json", pool, ki_rate=0.1, sha="OK",
                  seed=10 + i)
    with pytest.raises(Refuse, match="COMMITTED"):
        load_arm(sorted(tmp_path.glob("treat_*.json")), ROWS, label="T",
                 commitment="OK", expect_n=5)


def test_arm_count_ABOVE_the_committed_N_is_also_REFUSED(tmp_path, pool):
    """Running extra exchanges and keeping the best is the same violation."""
    for i in range(5):
        write_arm(tmp_path / f"treat_{i}.json", pool, ki_rate=0.1, sha="OK",
                  seed=20 + i)
    with pytest.raises(Refuse, match="COMMITTED"):
        load_arm(sorted(tmp_path.glob("treat_*.json")), ROWS, label="T",
                 commitment="OK", expect_n=3)


def test_degenerate_exchange_is_REFUSED(tmp_path, pool):
    p = tmp_path / "treat_1.json"
    p.write_text(json.dumps({"turns": 40, "commitment_sha": "OK",
                             "transcript_interacting": ["x"] * 40,
                             "transcript_control": ["x"] * 40}),
                 encoding="utf-8")
    with pytest.raises(Refuse, match="DEGENERATE"):
        exchange_rate(p, ROWS)


# ── the measure excludes the stipulated row ───────────────────────────────────
def test_primary_measure_ignores_the_stipulated_row(tmp_path, pool):
    """⛔⛔ THE CONFOUND. An exchange where the stipulated row emits `ki` 100 % of
    the time must NOT move the primary measure — that row is not in it."""
    rng = random.Random(7)
    forces = []
    for _ in range(40):
        forces += [FM.STIPULATED_SOURCE, "ki"]
    forces = forces[:40]
    surfaces = [rng.choice(pool[f]) for f in forces]
    p = tmp_path / "t.json"
    p.write_text(json.dumps({"turns": 40, "commitment_sha": "OK",
                             "transcript_interacting": surfaces,
                             "transcript_control": surfaces},
                            ensure_ascii=False), encoding="utf-8")
    e = exchange_rate(p, ROWS)
    assert e["n"] == 0 or e["rate"] in (None, 0.0), (
        "the stipulated row leaked into the primary measure")
    assert e["global_ki"] > 0.4, "sanity: the global marginal DOES move"


# ── the test statistic is on exchange means, matching the power calc ──────────
def test_welch_is_computed_on_exchange_level_means():
    a = {"rates": [0.10] * 10, "mean": 0.10, "sd": 0.0}
    b = {"rates": [0.20] * 10, "mean": 0.20, "sd": 0.0}
    d, _ = welch(a, b)
    assert d == pytest.approx(0.10)


def test_welch_sign_is_treatment_minus_baseline():
    """A sign flip here would invert CONFIRMED and REFUTED."""
    base = {"rates": [0.20] * 5, "mean": 0.20, "sd": 0.01}
    treat = {"rates": [0.10] * 5, "mean": 0.10, "sd": 0.01}
    d, t = welch(base, treat)
    assert d < 0 and t < 0


def test_welch_widens_with_between_exchange_variance():
    """⭐ Clustering must REDUCE significance, or the analyser would disagree with
    the power calculation that sized the run."""
    tight = {"rates": [0.20] * 20, "mean": 0.20, "sd": 0.01}
    loose = {"rates": [0.20] * 20, "mean": 0.20, "sd": 0.10}
    base = {"rates": [0.10] * 20, "mean": 0.10, "sd": 0.01}
    _, t_tight = welch(base, tight)
    _, t_loose = welch(base, loose)
    assert abs(t_loose) < abs(t_tight)
