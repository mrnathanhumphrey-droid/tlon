"""⛔⛔ THE FORCE READ ON THE *MODEL* — the half of the measurement that was
missing while the bench answered `ka` thirteen times out of thirteen.

`force_variety` gates a CORPUS at build time. Nothing measured the speaker.
The two reads that run on the rented card — `act2_flocal.py` and
`act2_model_carry.py` — both had the force sitting in a parse they were
already doing, and both dropped it. So "the corpus is 99.7% `ka`" and "the
live page always ends in `ka`" were two observations with nothing in between,
and closing that gap meant renting a second box.

⭐ Three separate things are proved here, because they fail separately:
  * the accounting (pure, no model);
  * the gate at the ASSEMBLY point, fired on corpora that really exist;
  * and the wiring — that flocal reads `speak` and never `render`, because a
    render probe is handed its force by the stimulus.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from tlon.act2.carry import derived_cell, force_transitions   # noqa: E402
from tlon.grammar import classes as C                         # noqa: E402

SHIPPED = ROOT / "runs" / "act2" / "corpus_conv_dosed" / "conversations.jsonl"
REBUILT = ROOT / "runs" / "act2" / "corpus_conv_force" / "conversations.jsonl"
GATE = ROOT / "tools" / "act2_force_gate.py"


@pytest.fixture(autouse=True)
def expanded_lexicon(monkeypatch):
    """⛔ PER-TEST, NEVER AT MODULE IMPORT. Setting `TLON_LEXICON` at import
    time poisons every other test at collection — this suite has paid for that
    once already (12 failed, 11 errors)."""
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.reset_caches()
    yield
    monkeypatch.undo()
    C.reset_caches()


def _run_gate(*args):
    return subprocess.run(
        [sys.executable, str(GATE), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT))


# ── the accounting ─────────────────────────────────────────────────────────

def test_the_marginal_and_the_table_are_both_kept():
    ft = force_transitions([("ki", "ka"), ("ka", "ka"), ("ka", "ki")])
    assert ft["n"] == 3
    assert ft["marginal"] == {"ka": 2, "ki": 1}
    assert ft["table"] == {"ki": {"ka": 1}, "ka": {"ka": 1, "ki": 1}}


def test_a_reply_with_no_readable_force_is_dropped_not_imputed():
    """⛔⛔ THE `except: -> 0` SHAPE. An unreadable force counted as `ka`
    would manufacture the exact finding this instrument exists to test."""
    ft = force_transitions([("ki", None), ("ki", ""), ("ki", "ka")])
    assert ft["n"] == 1 and ft["dropped_no_force"] == 2
    assert ft["marginal"] == {"ka": 1}


def test_a_reply_to_an_unparseable_prompt_is_in_the_marginal_not_the_table():
    """⭐ It is still something the model said — it just cannot be attributed
    to a prior act. Dropping it would bias the marginal by the probe's own
    defect rate; folding it into the table would invent a prior."""
    ft = force_transitions([(None, "ka"), ("ki", "ka")])
    assert ft["n"] == 2 and ft["no_prior"] == 1
    assert sum(sum(r.values()) for r in ft["table"].values()) == 1


def test_an_empty_read_is_zero_not_a_clean_bill():
    ft = force_transitions([])
    assert ft["n"] == 0 and ft["marginal"] == {} and ft["table"] == {}


# ── the one derived cell ───────────────────────────────────────────────────

def test_the_derived_cell_is_a_rate_over_its_own_row():
    ft = force_transitions([("ki", "ka")] * 9 + [("ki", "ko")]
                           + [("ka", "ku")] * 50)
    rate, k, n = derived_cell(ft["table"], "ki", "ka")
    assert (k, n) == (9, 10) and rate == pytest.approx(0.9)


def test_an_unprobed_prior_is_NONE_and_never_zero():
    """⛔⛔ A cell with no observations is not a model that refuses the
    structure. Returning 0.0 would read as `ki`->`ka` having been unlearned by
    a battery that never asked."""
    rate, k, n = derived_cell(force_transitions([("ka", "ka")])["table"],
                              "ki", "ka")
    assert rate is None and (k, n) == (0, 0)
    assert derived_cell(None)[0] is None
    assert derived_cell({})[0] is None


def test_the_marginal_alone_cannot_tell_these_two_speakers_apart():
    """⛔⛔ THE REASON THE TABLE EXISTS. A speaker that learned `ki`->`ka` and
    a speaker that only ever says `ka` produce the SAME histogram."""
    learned = force_transitions([("ki", "ka")] * 10 + [("ka", "ka")] * 10)
    parrot = force_transitions([("ki", "ka")] * 10 + [("ka", "ka")] * 10)
    assert learned["marginal"] == parrot["marginal"] == {"ka": 20}
    deaf = force_transitions([("ki", "ko")] * 10 + [("ka", "ko")] * 10)
    assert deaf["marginal"] != learned["marginal"]
    assert derived_cell(learned["table"])[0] == 1.0
    assert derived_cell(deaf["table"])[0] == 0.0


# ── what the provoke probe reads off one exchange ──────────────────────────

def test_both_sides_of_the_exchange_are_read():
    import act2_model_carry as MC
    from tlon.grammar.parse import render
    prior = render(__import__("tlon.grammar.parse", fromlist=["parse"]).parse(
        "hlim hlux les nang axas les ki"))
    out = MC._forces(prior, {"force": "ka", "node": {"root": "hlim"}})
    assert out == {"prior_force": "ki", "reply_force": "ka"}


def test_an_illegal_reply_force_is_not_a_force():
    import act2_model_carry as MC
    for bad in ("kaa", "", None, ["ka"], 7):
        out = MC._forces("hlim hlux les nang axas les ka", {"force": bad})
        assert out["reply_force"] is None, bad


def test_an_unparseable_prompt_reads_MISSING_on_the_prior_side_only():
    import act2_model_carry as MC
    out = MC._forces("this is not Tlon", {"force": "ka"})
    assert out == {"prior_force": None, "reply_force": "ka"}


def test_no_proposal_reads_MISSING_on_both_sides_without_raising():
    import act2_model_carry as MC
    assert MC._forces(None, None) == {"prior_force": None,
                                      "reply_force": None}


def test_the_carry_scorer_reports_force_on_every_branch():
    """⛔ The force read must not be conditioned on the carry verdict. A reply
    that changes the subject still picked a speech act, and reading force only
    over replies that already behaved would measure the well-behaved ones."""
    import act2_model_carry as MC
    roots = frozenset(C.load()["classes"]["R"])
    prior = "hlim hlux les nang axas les ki"
    for proposal in (None,
                     {"force": "ka", "node": {"root": "hlim"}},
                     {"force": "ka", "node": {"root": "nang"}}):
        r = MC.score(prior, proposal, roots)
        assert "prior_force" in r and "reply_force" in r
        assert r["prior_force"] == "ki"


# ── the gate, at the point the rows are assembled ──────────────────────────

@pytest.mark.skipif(not SHIPPED.exists(), reason="corpus not on this machine")
def test_the_gate_refuses_the_corpus_the_live_adapter_trained_on():
    """⛔⛔ THE REAL CASE, not an invented one. A gate calibrated on examples
    it wrote itself is a gate that flatters itself."""
    p = _run_gate(str(SHIPPED))
    assert p.returncode == 1, p.stdout
    assert "99.7%" in p.stdout and "ka" in p.stdout


@pytest.mark.skipif(not REBUILT.exists(), reason="pool not on this machine")
def test_the_gate_accepts_the_rebuilt_pool():
    p = _run_gate(str(REBUILT))
    assert p.returncode == 0, p.stdout
    assert "ACCEPTED" in p.stdout


@pytest.mark.skipif(not SHIPPED.exists(), reason="corpus not on this machine")
def test_reproducing_a_monoculture_arm_must_be_SAID():
    p = _run_gate(str(SHIPPED), "--allow-monoculture")
    assert p.returncode == 0
    assert "recorded choice" in p.stdout


def test_an_unreadable_corpus_exits_DIFFERENTLY_from_a_clean_one(tmp_path):
    """⛔⛔ A FAILED READ IS `MISSING`, NEVER A PASS. rc=2, distinct from both
    the accept and the refusal, so a pipeline cannot mistake one for another."""
    assert _run_gate(str(tmp_path / "nothing.jsonl")).returncode == 2
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    assert _run_gate(str(empty)).returncode == 2
    junk = tmp_path / "junk.jsonl"
    junk.write_text("{not json\n", encoding="utf-8")
    assert _run_gate(str(junk)).returncode == 2


def test_a_corpus_with_no_voice_T_is_unmeasured_not_accepted(tmp_path):
    p = tmp_path / "p_only.jsonl"
    p.write_text(json.dumps({"turns": [{"voice": "P", "scene":
                                        {"force": "ka"}}]}) + "\n",
                 encoding="utf-8")
    r = _run_gate(str(p))
    assert r.returncode == 1 and "no forces" in r.stdout


# ── what flocal's rate loop pulls out of the emissions ────────────────────

class _Scripted:
    """The two calls `_rate` makes, and `last_failure` for the None path."""

    def __init__(self, script):
        self._script = list(script)
        self.last_failure = None

    def _next(self):
        item = self._script.pop(0)
        if isinstance(item, dict) and "raw" in item:
            self.last_failure = {"reason": "no parseable JSON",
                                 "raw": item["raw"]}
            return None
        self.last_failure = None
        return item

    def speak(self, _hist, _i):
        return self._next()

    def render(self, _stim, _hist):
        return self._next()


def _proposal(root: str, force: str) -> dict:
    return {"node": {"root": root}, "force": force,
            "refused_objects": [], "note": ""}


def _valid_surface(root: str, force: str) -> str:
    """⛔ A surface comes from the gate, never from a keyboard."""
    from tlon.product import schema as PS
    _, surface, _ = PS.validate(_proposal(root, force))
    return surface


def test_the_force_is_collected_from_valid_and_bare_emissions_alike():
    """⭐ An emission that fails the ENVELOPE still chose a speech act. The
    gate is right to refuse it and the force read would be biased by exactly
    the envelope-failure rate if it dropped them."""
    import act2_flocal as FL
    sp = _Scripted([_proposal("klung", "ki"),
                    {"raw": _valid_surface("klung", "ko")}])
    res = FL._rate(sp, [None, None], "speak", histories=[(), ()])
    assert sorted(res["forces"]) == ["ki", "ko"]


def test_an_emission_with_an_invented_particle_contributes_no_force():
    """⛔ MISSING, not `ka`. A made-up particle is not a speech act, and
    imputing one would invent the measurement."""
    import act2_flocal as FL
    sp = _Scripted([_proposal("klung", "kaa"), {"raw": "not Tlon at all"}])
    res = FL._rate(sp, [None, None], "speak", histories=[(), ()])
    assert res["forces"] == []


def test_a_bare_surface_is_counted_once_not_twice():
    """⛔ `produced` and `failures` overlap by construction — a failure row
    only reaches the surface parse when its proposal was None — so a reply
    must not land in both lists."""
    import act2_flocal as FL
    sp = _Scripted([{"raw": _valid_surface("klung", "ku")}])
    res = FL._rate(sp, [None], "speak", histories=[()])
    assert res["forces"] == ["ku"]


def test_a_proposal_that_fails_on_its_NODE_still_reports_its_force():
    import act2_flocal as FL
    sp = _Scripted([{"node": {"root": "NOT-A-ROOT"}, "force": "kä",
                     "refused_objects": [], "note": ""}])
    res = FL._rate(sp, [None], "speak", histories=[()])
    assert res["valid"] == 0 and res["forces"] == ["kä"]


# ── the wiring, asserted rather than assumed ───────────────────────────────

def test_the_pipeline_gates_the_pool_it_actually_trains_on():
    """⛔⛔ A GATE NOTHING CALLS IS A COMMENT — and this gate's whole reason
    for existing is that the pool gate sat one transform upstream of the rows
    that reach the trainer."""
    sh = (ROOT / "tools" / "pipeline_puzzle.sh").read_text(encoding="utf-8")
    assert "act2_force_gate.py" in sh, "the pipeline never calls the gate"
    assert sh.index("act2_force_gate.py") < sh.index(
        "act2_build_multiturn_rows.py"), "the gate runs AFTER the rows are built"
    assert 'act2_force_gate.py "$CONV"' in sh, (
        "the gate must read $CONV — the pool that is actually trained on, "
        "however it got there")


def test_the_dose_block_has_no_default_pools():
    """⛔⛔ THE DEFAULTS WERE THE TWO 99.7% `ka` POOLS. Restored, they would
    let a v2 run blend two monocultures and pass every other gate."""
    sh = (ROOT / "tools" / "pipeline_puzzle.sh").read_text(encoding="utf-8")
    dose = sh[sh.index('if [ -n "${DOSE:-}" ]'):sh.index("act2_force_gate.py")]
    assert "--steered \"$POOL_A\"" in dose and "--unsteered \"$POOL_B\"" in dose
    assert "${POOL_A:-runs" not in dose and "${POOL_B:-runs" not in dose
    # ⛔ COMMENTS ARE STRIPPED FIRST. The block explains WHY the old pools were
    # removed and names them to do it; a bare substring search over the whole
    # block would fail on its own documentation, and the honest way past that
    # is to test the executable lines rather than to delete the explanation.
    live = [ln for ln in dose.splitlines() if not ln.lstrip().startswith("#")]
    assert not [ln for ln in live
                if "corpus_conv_steered" in ln or "corpus_conversations" in ln], (
        "an executable line still names one of the 99.7% `ka` pools")


def test_flocal_reads_the_force_off_SPEAK_and_never_off_RENDER():
    """⛔⛔ A RENDER PROBE IS HANDED ITS FORCE BY THE STIMULUS. Tallying it
    would measure `probes.build` and show a healthy spread whatever the
    weights learned — a probe downstream of the transformation."""
    src = (ROOT / "tools" / "act2_flocal.py").read_text(encoding="utf-8")
    assert 'force_transitions((None, f) for f in speak["forces"])' in src
    assert 'render["forces"]' not in src, (
        "flocal tallies the render probe's force, which is the stimulus's")


def test_the_force_read_is_ledgered_not_only_printed():
    src = (ROOT / "tools" / "act2_flocal.py").read_text(encoding="utf-8")
    led = src[src.index("led.note("):src.index("ledgered →")]
    assert "force=ft" in led, "the histogram reaches a terminal and nowhere else"
    mc = (ROOT / "tools" / "act2_model_carry.py").read_text(encoding="utf-8")
    assert '"force": ft' in mc, "model_carry's table is not written to --out"
