"""⛔⛔ RED-PROOF FOR THE REPLY-FORCE DIAL — a product knob that must stay one.

The served speaker answers `ka` almost always, and that is FAITHFUL: in
`corpus_bench_dosed`, the corpus its own adapter trained on, the Tlönian's
reply force is ka 99.7%, and the conversation pools behind it are 99.7% / 99.8%
ka in voice T. So this dial does not fix anything — it dresses a symptom, and
the tests below are mostly about keeping it from doing damage on its way past:

  * OFF by default, so nothing changes unless someone asks;
  * `ki` → `ka` untouched, because that is the one derived cell in the language;
  * never able to turn a good turn into a refusal;
  * never read by the research track;
  * and the model's own force recorded either way, so the dial cannot erase the
    evidence of what the model actually said.
"""
from __future__ import annotations

import pathlib
import random
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puzzle import router as R                    # noqa: E402
from puzzle import speaker as SP                  # noqa: E402

from tlon.grammar import classes as C             # noqa: E402
from tlon.grammar.parse import parse              # noqa: E402

REPLY = "hlim hlux les nang axas les ka"

#: ⛔ Gitignored (regenerable from the two committed pools at seed 20624), so
#: the recompute test skips where it is absent rather than failing.
CORPUS = ROOT / "runs" / "act2" / "corpus_bench_force" / "train.jsonl"


#: A WRITE to the dial's environment — assignment, `pop`, or `del`. All three
#: change the variable; none of them INTERPRET it, which is the thing the bar
#: below keeps to one place. ⛔ `pop` is here because clearing a stale knob is
#: how the probe stops itself from silently selecting the legacy table, and a
#: guard that called that a "read" would push the fix back out of the harness.
_DIAL_SET = re.compile(
    r"(?:environ\[\s*[\"']TLON_(?:FORCE_TABLE|KI_WEIGHT)[\"']\s*\]\s*="
    r"|environ\.pop\(\s*[\"']TLON_(?:FORCE_TABLE|KI_WEIGHT)[\"']"
    r"|del\s+os\.environ\[\s*[\"']TLON_(?:FORCE_TABLE|KI_WEIGHT)[\"']\s*\])")

#: ⛔⛔ FILES ALLOWED TO *SET* THE DIAL, AND THE REASON EACH ONE MAY.
#: Setting is not interpreting: these write the variable and then assert that
#: `speaker` agrees, so there is still exactly ONE place that decides what the
#: flag MEANS — which is the whole point of the bar below. Each entry is also
#: checked to contain no LOOKUP, so an allowlisted file cannot quietly become a
#: second interpreter.
_MAY_SET_THE_DIAL = {
    # The off-line force probe. It runs both arms of the dial and refuses to
    # report unless `SP.FORCE_TABLE` matches what it asked for.
    "modal_force_probe.py",
}


def _touches_the_dial(path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    return any(("environ" in line or "getenv" in line)
               and ("TLON_FORCE_TABLE" in line or "TLON_KI_WEIGHT" in line)
               for line in text.splitlines())


def _sets_the_dial(path) -> bool:
    """An ASSIGNMENT into `os.environ`, not a lookup out of it."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return any(_DIAL_SET.search(line) for line in text.splitlines())


def _reads_the_dial(path) -> bool:
    """An env LOOKUP of either knob — the thing that must live in ONE place.

    ⛔ A line that WRITES `os.environ[...]` is excluded: a harness that sets the
    flag and then asserts the module agreed is not a second reader of it. The
    bar is about two places INTERPRETING one flag, and that is preserved
    literally — see `_MAY_SET_THE_DIAL`, which is audited by its own test.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    return any(("environ" in line or "getenv" in line)
               and ("TLON_FORCE_TABLE" in line or "TLON_KI_WEIGHT" in line)
               and not _DIAL_SET.search(line)
               for line in text.splitlines())


@pytest.fixture(autouse=True)
def expanded_lexicon(monkeypatch):
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.reset_caches()
    yield
    monkeypatch.undo()
    C.reset_caches()


class _Turn:
    """The shape `apply_force_dial` touches, and nothing more."""
    def __init__(self, surface):
        self.surface = surface
        self.scene = parse(surface)
        self.ok = True


# ── off by default ─────────────────────────────────────────────────────────

def test_the_dial_is_off_unless_someone_turns_it_on():
    """⛔ Every number this project has published about force was measured with
    this off. A default of ON would silently reinterpret all of them."""
    assert SP.FORCE_TABLE is False


def test_with_the_dial_off_the_reply_is_exactly_what_the_model_made(
        monkeypatch):
    monkeypatch.setattr(SP, "FORCE_TABLE", False)
    t = _Turn(REPLY)
    was, sent = SP.apply_force_dial(t, REPLY)
    assert t.surface == REPLY
    assert (was, sent) == ("ka", "ka")


def test_the_models_force_is_recorded_even_with_the_dial_off(monkeypatch):
    """⭐ So a later comparison does not depend on the flag having been set
    when the row was written."""
    monkeypatch.setattr(SP, "FORCE_TABLE", False)
    was, sent = SP.apply_force_dial(_Turn(REPLY), REPLY)
    assert was == "ka" and sent == "ka"


# ── the one derived cell is not up for redrawing ───────────────────────────

def test_ki_still_answers_ka_with_probability_one():
    """⛔⛔ `ki`→`ka` survived the mutation test and is the ONLY structure the
    corpus carries. A dial that reweighted it would overwrite the single
    derived thing in the language with a product preference."""
    w = SP.force_weights("ki")
    assert w["ka"] == 1.0
    assert sum(v for k, v in w.items() if k != "ka") == 0.0


def test_an_ask_is_never_answered_with_an_ask(monkeypatch):
    monkeypatch.setattr(SP, "FORCE_TABLE", True)
    asked = R.refocus(REPLY, "ki")
    for seed in range(40):
        t = _Turn(REPLY)
        monkeypatch.setattr(SP, "_force_rng", random.Random(seed))
        _was, sent = SP.apply_force_dial(t, asked)
        assert sent == "ka", "an ask was answered with %r" % sent


# ── the weights are what the flag says they are ────────────────────────────

def test_the_default_table_is_the_CORPUS_marginal_not_a_proposal():
    """⛔⛔ THE DIAL SHIPPED WITH AN UNMEASURED DEFAULT AND IT SERVED A LIE.

    `ki_weight=0.35` with the rest split evenly put `ka` — the assertion, the
    thing most utterances are — at **7.4%** on the bench (n=94, temp 0.7), and
    `ki` at 38.3%. That is as false as the `ka` 100% it was built to fix. The
    default is now the corpus's own measured distribution, so the reader sees
    the language as its corpus speaks it.
    """
    w = SP.force_weights("ka")
    assert w["ka"] == pytest.approx(0.526, abs=0.01), w
    assert w["ki"] == pytest.approx(0.227, abs=0.01), w
    # ⭐ The ORDER is the claim that matters: statements dominate, then asks.
    order = [f for f, _ in sorted(w.items(), key=lambda kv: -kv[1])]
    assert order == ["ka", "ki", "ko", "ku", "kä"], order
    assert sum(w.values()) == pytest.approx(1.0)


@pytest.mark.skipif(not CORPUS.exists(), reason="corpus not on this machine")
def test_the_default_table_still_matches_the_corpus_it_claims_to_come_from():
    """⛔⛔ A TABLE COPIED OUT OF A CORPUS DRIFTS FROM IT SILENTLY. Recomputed
    here from the rows themselves, so a rebuilt corpus cannot leave the dial
    speaking the previous one's distribution."""
    import collections
    import json
    got = collections.Counter()
    with CORPUS.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("direction") == "provoke":
                got[(r.get("scene") or {}).get("force")] += 1
    assert dict(got) == SP.FORCE_MARGINAL_COUNTS, (
        "the dial's table no longer matches %s — recompute it or say why it "
        "should differ" % SP.FORCE_MARGINAL_SOURCE)


def test_an_explicit_ki_weight_still_overrides_the_table():
    """⭐ The knob was shipped, so a caller who names a value means it. Only the
    DEFAULT moved."""
    w = SP.force_weights("ka", ki_weight=0.35)
    assert w["ki"] == pytest.approx(0.35)
    assert w != SP.force_weights("ka")


def test_the_env_knob_is_only_honoured_when_it_is_actually_SET():
    """⛔⛔ THE TRAP THIS AVOIDS. `apply_force_dial` passing `KI_WEIGHT`
    unconditionally would hand `force_weights` its module default of 0.35 —
    the corpus table would be dead code and every other test here would still
    pass. The read must be conditional on the variable existing."""
    src = (ROOT / "puzzle" / "speaker.py").read_text(encoding="utf-8")
    assert "_KI_WEIGHT_EXPLICIT" in src
    assert 'KI_WEIGHT if _KI_WEIGHT_EXPLICIT else None' in src, (
        "apply_force_dial no longer distinguishes a SET knob from its default")


def test_the_draw_follows_the_corpus_table_by_default():
    """⭐ A table whose weights nothing draws from is a comment."""
    rng = random.Random(20624)
    drawn = [SP.draw_force("ka", rng=rng) for _ in range(4000)]
    ka = drawn.count("ka") / len(drawn)
    ki = drawn.count("ki") / len(drawn)
    assert 0.49 < ka < 0.56, "ka share %.3f is not near the corpus 0.526" % ka
    assert 0.20 < ki < 0.26, "ki share %.3f is not near the corpus 0.227" % ki
    # ⛔ And `kä` must actually appear — a 1.5% cell rounded out of existence
    # would make the language four-way, which is the bug one level quieter.
    assert "kä" in drawn


def test_the_other_rows_give_ki_its_weight_and_split_the_rest_evenly():
    w = SP.force_weights("ka", ki_weight=0.35)
    assert w["ki"] == pytest.approx(0.35)
    rest = [v for k, v in w.items() if k != "ki"]
    assert len(rest) == 4
    assert all(v == pytest.approx(0.65 / 4) for v in rest)
    assert sum(w.values()) == pytest.approx(1.0)


def test_the_weights_are_a_distribution_over_every_force():
    for prior in sorted(C.load()["classes"]["F"]):
        w = SP.force_weights(prior)
        assert set(w) == set(C.load()["classes"]["F"])
        assert sum(w.values()) == pytest.approx(1.0)
        assert all(v >= 0 for v in w.values())


def test_the_draw_actually_follows_the_weights():
    """⭐ A dial whose knob did nothing would pass every test above."""
    rng = random.Random(20624)
    drawn = [SP.draw_force("ka", rng=rng, ki_weight=0.35) for _ in range(4000)]
    share = drawn.count("ki") / len(drawn)
    assert 0.31 < share < 0.39, "ki share %.3f is not near 0.35" % share


def test_the_ki_weight_is_a_knob_and_not_a_decoration():
    rng = random.Random(7)
    none = [SP.draw_force("ka", rng=rng, ki_weight=0.0) for _ in range(500)]
    assert "ki" not in none
    rng = random.Random(7)
    allof = [SP.draw_force("ka", rng=rng, ki_weight=1.0) for _ in range(500)]
    assert set(allof) == {"ki"}


# ── it cannot make a turn worse ────────────────────────────────────────────

def test_a_redrawn_reply_is_still_legal_and_still_the_same_scene(monkeypatch):
    monkeypatch.setattr(SP, "FORCE_TABLE", True)
    for f in sorted(C.load()["classes"]["F"]):
        t = _Turn(REPLY)
        SP.restamp(t, f)
        assert parse(t.surface) == t.scene, "surface and scene disagree"
        assert parse(t.surface).node == parse(REPLY).node, "the scene moved"
        assert parse(t.surface).force == f


def test_a_refused_reply_is_left_alone(monkeypatch):
    monkeypatch.setattr(SP, "FORCE_TABLE", True)

    class _Refused:
        ok = False
        surface = None
        scene = None

    assert SP.apply_force_dial(_Refused(), REPLY) == (None, None)
    assert SP.apply_force_dial(None, REPLY) == (None, None)


def test_an_unparseable_provocation_leaves_the_reply_untouched(monkeypatch):
    """⛔ The dial reads the PROVOCATION's force to pick a row. If it cannot,
    it must do nothing — not guess, and not fail the turn."""
    monkeypatch.setattr(SP, "FORCE_TABLE", True)
    t = _Turn(REPLY)
    was, sent = SP.apply_force_dial(t, "Are you there")
    assert (was, sent) == ("ka", "ka")
    assert t.surface == REPLY


def test_a_restamp_that_cannot_render_is_swallowed_not_raised(monkeypatch):
    """⛔⛔ A DIAL MUST NEVER TURN A GOOD TURN INTO A REFUSAL. If re-rendering
    fails for any reason the reader gets exactly what the model made."""
    monkeypatch.setattr(SP, "FORCE_TABLE", True)

    def boom(_surface, _force):
        raise R.RouterError("no")

    monkeypatch.setattr(SP.router, "refocus", boom)
    t = _Turn(REPLY)
    was, sent = SP.apply_force_dial(t, REPLY)
    assert (was, sent) == ("ka", "ka")
    assert t.surface == REPLY


# ── it stays on the product side ───────────────────────────────────────────

def test_the_research_track_never_reads_the_dial():
    """⛔⛔ `TLON_FORCE_TABLE` is a product knob. If a research tool ever
    consulted it, a published force number could silently be a number about
    the dial instead of about the model."""
    offenders = [str(p.relative_to(ROOT))
                 for sub in ("tlon", "tools")
                 for p in (ROOT / sub).rglob("*.py")
                 if _reads_the_dial(p)]
    assert not offenders, (
        "the force dial leaked into the research track: %s" % offenders)


def test_only_the_speaker_reads_the_dial():
    """⭐ MENTIONING IT IS FINE — `logbook.py` documents the column it feeds.
    What must stay in one place is the READ, because two readers of one flag
    is two places it can be interpreted differently."""
    seen = sorted(p.name for p in (ROOT / "puzzle").rglob("*.py")
                  if _reads_the_dial(p))
    assert seen == ["speaker.py"], seen


def test_only_named_harnesses_may_SET_the_dial_and_they_may_not_read_it():
    """⛔⛔ THE SECOND HALF OF THE SAME BAR. Setting the flag is legitimate for a
    probe that then asserts the module agreed; becoming a second INTERPRETER of
    it is not. So every setter is named with its reason, and each one is checked
    to contain no lookup — otherwise the allowlist would be a hole rather than a
    record."""
    setters = {p.name for p in (ROOT / "puzzle").rglob("*.py")
               if _sets_the_dial(p)}
    unlisted = setters - _MAY_SET_THE_DIAL
    assert not unlisted, (
        "these set the dial without being named: %s — add them with a reason "
        "or stop setting it" % sorted(unlisted))
    for p in (ROOT / "puzzle").rglob("*.py"):
        if p.name in _MAY_SET_THE_DIAL:
            assert not _reads_the_dial(p), (
                "%s is allowed to SET the dial but it also READS it, which "
                "makes it a second interpreter" % p.name)
    # ⛔ And the research track may not even set it.
    offenders = [str(p.relative_to(ROOT))
                 for sub in ("tlon", "tools")
                 for p in (ROOT / sub).rglob("*.py")
                 if _touches_the_dial(p)]
    assert not offenders, offenders
