"""⛔⛔ THE GATE THAT DID NOT EXIST, AND THE CORPUS THAT PROVES IT WAS NEEDED.

Tlön marks five speech acts: `ka` assert, `ki` ask, `ko` wonder, `ku` urge,
`kä` deny. The corpus the LIVE adapter trained on uses one of them. Voice T in
`corpus_conv_dosed` is **99.7% `ka`**, so every reply on the public bench ends
in the same particle — 13 of 13 in production — and a reader who notices that
Tlön has five endings has no way to ever see four of them.

The model is faithful. The corpus is not varied. Nothing between them looked:
carry was gated, echo was gated, force was never counted at all. It took a
reader saying a Tlön word back for anyone to find it.

⭐ So the first thing this suite does is fire the new gate on the REAL corpus.
A gate calibrated on invented examples is a gate that flatters itself; this
repo has already learned that once, in `test_settled_claim_lint.py`.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tlon.act2.carry import ACCEPTANCE, force_variety   # noqa: E402

SHIPPED = ROOT / "runs" / "act2" / "corpus_conv_dosed" / "conversations.jsonl"


def _voice_t_forces(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            for t in json.loads(line).get("turns", []):
                if t.get("voice") == "T":
                    out.append((t.get("scene") or {}).get("force"))
    return out


# ── it fires on the corpus that actually shipped ───────────────────────────

@pytest.mark.skipif(not SHIPPED.exists(), reason="corpus not on this machine")
def test_it_rejects_the_corpus_the_live_adapter_trained_on():
    """⛔⛔ THE REAL CASE. If this ever passes, either the corpus was rebuilt
    or the gate stopped working — and only one of those is good news."""
    forces = _voice_t_forces(SHIPPED)
    assert forces, "no voice-T forces found; the corpus shape moved"
    ok, detail, counts = force_variety(forces)
    assert not ok, (
        "the gate does not fire on the 99.7%% `ka` corpus that shipped: %s"
        % detail)
    assert counts.get("ka", 0) / sum(counts.values()) > 0.99, counts


@pytest.mark.skipif(not SHIPPED.exists(), reason="corpus not on this machine")
def test_the_detail_names_the_offending_force_and_its_share():
    """⭐ A gate that returns a bare verdict gets debugged by rebuilding the
    corpus, and rebuilding THIS corpus means paying the proposer again."""
    ok, detail, counts = force_variety(_voice_t_forces(SHIPPED))
    assert not ok
    assert "ka" in detail and "%" in detail
    assert counts, "counts must be reported on failure, not just on success"


# ── and it passes a corpus that uses the language ──────────────────────────

def test_a_varied_corpus_passes():
    forces = (["ka"] * 55) + (["ki"] * 20) + (["ko"] * 10) + (["ku"] * 8) \
        + (["kä"] * 7)
    ok, detail, counts = force_variety(forces)
    assert ok, detail
    assert sum(counts.values()) == 100


def test_statements_are_allowed_to_dominate():
    """⭐ THE THRESHOLD IS DELIBERATELY LOOSE. Most of what anyone says is a
    statement, and a gate that demanded five-way balance would be a gate that
    reshaped the language to suit itself."""
    ok, detail, _counts = force_variety(
        (["ka"] * 59) + (["ki"] * 25) + (["ko"] * 16))
    assert ok, detail


def test_one_point_over_the_cap_fails():
    ok, detail, _ = force_variety((["ka"] * 61) + (["ki"] * 39))
    assert not ok and "cap" in detail


# ── the second condition catches what a share alone would miss ─────────────

def test_two_forces_is_not_variety_however_even_the_split():
    """⛔ A 50/50 corpus of `ka` and `ki` passes the share test and still
    teaches three of the five acts as nonexistent. Both conditions are needed
    and this is the one the share cannot see."""
    ok, detail, _ = force_variety((["ka"] * 50) + (["ki"] * 50))
    assert not ok
    assert "distinct" in detail


def test_the_thresholds_are_registered_not_inlined():
    """⛔ A threshold quoted in prose after the fact is a threshold chosen
    after seeing the number. Both live in ACCEPTANCE beside the carry ones."""
    assert ACCEPTANCE["force_top_share_max"] == 0.60
    assert ACCEPTANCE["force_distinct_min"] == 3


# ── it cannot pass by accident ─────────────────────────────────────────────

def test_an_empty_corpus_is_a_failure_not_a_pass():
    """⛔⛔ A measurement over nothing must never read as a clean bill. This is
    the `except: -> 0` shape that has shipped fabricated data in three arcs."""
    ok, detail, counts = force_variety([])
    assert not ok and counts == {}
    assert "no forces" in detail


def test_missing_forces_are_dropped_not_counted_as_a_force():
    ok, _detail, counts = force_variety(["ka", None, "ki", "", "ko", "ku"])
    assert None not in counts and "" not in counts
    assert sum(counts.values()) == 4


def test_the_builder_actually_consults_the_gate():
    """⛔⛔ A GATE NOTHING CALLS IS A COMMENT. The carry gate existed and this
    one did not, which is the whole reason the corpus shipped — so the wiring
    is asserted, not assumed."""
    src = (ROOT / "tools" / "act2_build_conversations.py").read_text(
        encoding="utf-8")
    assert "force_variety(" in src, "the builder never calls the gate"
    assert 'verdict, detail = "REJECTED"' in src, (
        "the gate is computed but cannot change the verdict")


def test_the_dialogue_prompt_now_asks_for_more_than_descriptions():
    """⛔ The root cause was one clause: every T line was specified as
    'describing something occurring or being perceived'. The model complied
    perfectly. If that clause returns, so does the monoculture."""
    # ⛔ By PATH, not `from tools import ...` — `tools` is also a package in
    # site-packages and the import silently resolves to that one.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_bc", ROOT / "tools" / "act2_build_conversations.py")
    src = (ROOT / "tools" / "act2_build_conversations.py").read_text(
        encoding="utf-8")
    assert spec is not None
    prompt = src[src.index("DIALOGUE_SYSTEM = "):src.index("Emit ONLY the P:")]
    assert "describing something occurring" not in prompt
    for act in ("ASK", "WONDER", "URGE", "DENY"):
        assert act in prompt, "the prompt never asks for %s" % act
