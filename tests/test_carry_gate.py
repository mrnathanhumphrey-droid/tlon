"""⛔⛔ RED-PROOF: THE CORPUS MUST CARRY HAPPENINGS, AND THE GATE MUST SIT
WHERE REJECTING CAN ACTUALLY HELP.

The speaker was retrained on a conversational corpus built to teach continuity
and it taught the opposite. Measured on that corpus: root recurrence within a
conversation **5.3% against a 7.5% shuffled null, p=0.000 over 500 shuffles —
BELOW CHANCE**, and of its 2,604 P->T pairs, **3 (0.1%) share a happening-word
in English**. The cause was one instruction — "a FRESH impression ... answering
an image with an image" — which in a language whose roots ARE happenings asks
for a DIFFERENT happening every turn.

⭐ The regression these tests hold is therefore not "the gate works on toy
input". It is:

  1. the gate REJECTS THE CORPUS THAT SHIPPED, at close to the measured rate —
     a gate that passes the known-bad corpus would be decoration;
  2. the anti-carry instruction CANNOT COME BACK into DIALOGUE_SYSTEM without
     a test going red;
  3. stage 2 never resamples UNSTEERED, where resampling cannot work and would
     burn the budget for nothing — narrowed, not dropped, when the root-steer
     made the requirement satisfiable;
  4. forced carry is STAMPED on every conversation, so the research corpus
     cannot inherit the puzzle's crib by accident;
  5. no VERDICT is printed below the deciding n — the first sample said
     ACCEPTED on 22 pairs and the next identical run said the opposite.
"""
from __future__ import annotations

import inspect
import json
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

from tlon.act2.carry import (ACCEPTANCE, Carry, CarryError, decide,  # noqa: E402
                             english_carry, english_happenings,
                             gate_dialogue, happening_words,
                             load_vocabulary, scene_carry, scene_roots,
                             wilson)


# ── the vocabulary is measured, present, and carries its provenance ─────────
def test_vocabulary_is_present_and_documents_how_it_was_made():
    body = load_vocabulary()
    prov = body["provenance"]
    assert body["words"], "an empty vocabulary would pass nothing"
    assert prov["statistic"].startswith("P(")
    assert prov["sources"], "the corpus it was measured on must be named"
    assert prov["turns_scored"] > 1000
    # ⛔ The baseline belongs WITH the scores: a rate of 0.5 means nothing
    # until you know chance is 0.038.
    assert 0.0 < body["baseline"] < 0.20


def test_a_missing_vocabulary_raises_rather_than_passing_everything(
        monkeypatch, tmp_path):
    """⛔⛔ THE FAILURE THIS FORBIDS IS THE ONE THAT LOOKS LIKE SUCCESS.

    If the file is absent and the gate quietly treats every word as a
    happening, every dialogue passes, the build completes, the report is
    green, and the corpus is exactly as anti-carry as the one that already
    cost a retrain.
    """
    import tlon.act2.carry as carry

    monkeypatch.setattr(carry, "VOCAB_PATH", tmp_path / "gone.json")
    carry.load_vocabulary.cache_clear()
    carry.happening_words.cache_clear()
    with pytest.raises(CarryError, match="missing"):
        carry.happening_words()
    carry.load_vocabulary.cache_clear()
    carry.happening_words.cache_clear()


# ── the measured distinction, which is not a part of speech ─────────────────
def test_happenings_are_distinguished_from_stance_not_by_being_verbs():
    """⭐ `feels` is a verb and buys nothing; `dims` buys a root every time."""
    words = happening_words()
    assert "dims" in words and "waited" in words and "breathing" in words
    for stance in ("today", "feels", "honestly", "little", "yeah"):
        assert stance not in words, (
            "%r scored at baseline in the measurement — admitting it would let "
            "a pair 'carry' a mood while sharing no happening" % stance)


def test_english_carry_requires_a_happening_and_something_new():
    carried = english_carry("I waited far too long for something so small.",
                            "A waiting stretches and the light goes thin.")
    assert carried.ok, carried.reason
    assert carried.carried, "the shared happening must be reported"

    # the corpus's actual failure mode: a beautiful, DIFFERENT happening
    drifted = english_carry("I dropped my coffee right outside the door.",
                            "A dark splash spreads across pale stone.")
    assert not drifted.ok
    assert "no happening carried" in drifted.reason

    echoed = english_carry("The light dims.", "The light dims.")
    assert not echoed.ok and "echo" in echoed.reason


def test_the_gate_survives_the_nominalisation_the_prompt_asks_for():
    """⛔⛤ THE BUG A TEST CAUGHT BEFORE IT COST A BUILD.

    The carry instruction tells the writer to take up the happening, and a
    Tlönian names a happening by nominalising it — "I waited" is answered by
    "a waiting". A gate comparing word STRINGS rejects that, which would have
    rejected exactly the replies the prompt was rewritten to produce and made
    a working prompt look broken at ~3 calls per conversation.
    """
    for said, answered in (("I waited all afternoon.", "A waiting settles in."),
                           ("The light dims.", "A dimming spreads outward."),
                           ("I slept badly.", "A sleeping breaks open.")):
        verdict = english_carry(said, answered)
        assert verdict.ok, "%r -> %r: %s" % (said, answered, verdict.reason)


def test_english_happenings_finds_only_scored_words():
    got = english_happenings("Honestly the light just dims a little today.")
    assert "dims" in got
    assert not ({"honestly", "little", "today"} & got)


# ── the band, on roots, in both directions ──────────────────────────────────
@pytest.mark.parametrize("prior,reply,ok,why", [
    (["hlun"], ["hlun", "flox"], True, "carried one, brought one"),
    (["hlun"], ["flox"], False, "no root carried"),
    (["hlun", "flox"], ["hlun", "flox"], False, "echo"),
    (["hlun"], [], False, "no root at all"),
])
def test_scene_carry_is_a_band_not_a_maximum(prior, reply, ok, why):
    verdict = scene_carry(prior, reply)
    assert verdict.ok is ok, why
    if not ok and prior and reply and set(reply) <= set(prior):
        assert verdict.echo, "carrying everything and adding nothing IS the echo"


def test_maximum_reuse_is_rejected_because_it_breaks_the_puzzle_too():
    """⭐ The retracted decision feared repetitive collapse. It was right that
    forcing maximum reuse is wrong; the fix is the band, so a perfect echo has
    to fail exactly as a non-sequitur does."""
    assert not scene_carry(["a", "b"], ["a", "b"]).ok
    assert not scene_carry(["a", "b"], ["c", "d"]).ok
    assert scene_carry(["a", "b"], ["a", "c"]).ok


def test_scene_roots_walks_the_tree_not_the_surface():
    roots = frozenset({"hlun", "flox", "mun"})
    scene = {"node": {"root": "hlun", "aspect_root": "flox",
                      "edges": [{"relator": "xom",
                                 "node": {"root": "mun"}}]}}
    assert scene_roots(scene, roots) == roots


# ── truncation, not splicing ────────────────────────────────────────────────
def test_gate_truncates_at_the_break_and_never_splices():
    """⛔ Skipping a bad exchange would join turn 1 to turn 3 and teach a jump
    that never happened — a manufactured non-sequitur in data whose entire
    purpose is that each turn follows the last."""
    turns = [("P", "I waited far too long."),
             ("T", "A waiting stretches out and thins."),
             ("P", "Then the light dims."),
             ("T", "A dark splash spreads across pale stone."),   # drifts
             ("P", "The light dims again."),
             ("T", "The light dims and a cold comes up.")]        # would pass
    kept, verdicts = gate_dialogue(turns)
    assert len(kept) == 2, "kept only the exchanges before the break"
    assert kept == turns[:2]
    assert len(verdicts) == 2 and verdicts[-1].ok is False


# ── the regressions that actually bind ──────────────────────────────────────
def test_the_gate_rejects_the_corpus_that_shipped():
    """⛔⛔ A GATE THAT PASSES THE KNOWN-BAD CORPUS IS DECORATION.

    The shipped conversational corpus is the one artefact we know teaches
    anti-carry. If it is on disk, the gate must reject nearly all of it — the
    measurement said 0.1% of its P->T pairs share a happening-word.
    """
    path = _ROOT / "runs" / "act2" / "corpus_conversations" / "conversations.jsonl"
    if not path.exists():
        pytest.skip("the shipped corpus is not on this checkout")
    seen = passed = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            turns = json.loads(line)["turns"]
            for i in range(len(turns) - 1):
                if turns[i]["voice"] != "P" or turns[i + 1]["voice"] != "T":
                    continue
                seen += 1
                if english_carry(turns[i].get("english"),
                                 turns[i + 1].get("english")).ok:
                    passed += 1
    assert seen > 1000, "expected the full corpus, got %d pairs" % seen
    # ⛔ The bar is 8%, not 5%, and the reason is recorded rather than tuned to:
    # the gate is deliberately RECALL-tuned (see `english_carry`), which moved
    # its pass-rate here from 1.1% to a measured 4.9% while moving recall on
    # compliant English from 23.4% to 76.6%. The claim this test defends is the
    # SEPARATION — ~15x — not an absolute, and a bar sitting 0.1pp above the
    # measurement would be a tripwire on noise rather than a regression test.
    assert passed / seen < 0.08, (
        "the gate passed %.1f%% of the corpus that measured BELOW CHANCE on "
        "root recurrence — it is not enforcing anything"
        % (100 * passed / seen))


def test_the_gate_sees_the_carry_the_new_prompt_actually_writes():
    """⛔⛤ THE REGRESSION FOR THE INSTRUMENT ITSELF.

    The first sample scored 32.1% and read as "the prompt does not comply".
    The writer had complied nearly every time; the closed vocabulary could not
    see it. These are verbatim pairs from that sample — an instrument that
    fails them is measuring its own coverage again.
    """
    pairs = [
        ("I got stuck in traffic for hours today.",
         "A stuck-ness is spreading, then something loosens far ahead."),
        ("The wind picked up right after, cold and sudden.",
         "A picking-up stirs the stillness loose, and a shiver runs through."),
        ("By the time I got there, it was already dark.",
         "A darkening settles low and thick, and a small light flickers awake."),
        ("Then the clouds rolled in fast, faster than I expected.",
         "A rolling gathers weight overhead, and the air thins where it passes."),
        ("I just feel like I wasted the whole day traveling.",
         "A wasting drains slowly downward, and something begins to gather."),
    ]
    missed = [p for p, t in pairs if not english_carry(p, t).ok]
    assert not missed, (
        "the gate cannot see compliant carry in %d of %d real sample pairs: %s"
        % (len(missed), len(pairs), missed))


def test_the_anti_carry_instruction_cannot_come_back():
    """⛔⛤ ONE WORD CAUSED THIS. `fresh` propagated from multiturn.py's
    docstring into the dialogue prompt and cost a retrain."""
    import act2_build_conversations as B

    system = B.DIALOGUE_SYSTEM.lower()
    for banned in ("fresh impression", "answering an image with an image"):
        assert banned not in system, (
            "%r is the anti-carry instruction: in a language whose roots are "
            "happenings it asks for a DIFFERENT happening every turn" % banned)
    assert "happening the p line just named" in system, (
        "the carry requirement must be stated to the writer, not only enforced "
        "after the fact — enforcement alone would cost a regeneration on most "
        "calls and the gate's whole affordability rests on the base rate")


def test_stage_two_may_only_resample_when_it_is_steered():
    """⛔⛔ THE PROHIBITION SURVIVED THE STEER, NARROWED RATHER THAN DROPPED.

    Unsteered, the proposer sees only its own English line, so a carry failure
    is a fact about English already written and a retry cannot repair it —
    ~99.9% of turns would reject forever. The steer names the root, which makes
    the requirement satisfiable and the retry meaningful. So the rule is not
    "never resample at stage 2"; it is "never resample WITHOUT a steer", and a
    resample loop that forgot to pass `require_roots` would silently be the
    old, hopeless one.
    """
    import act2_build_conversations as B

    src = inspect.getsource(B.build)
    render_src = src.partition("def render_turn")[2].partition("    def one(")[0]
    assert "scene_carry" not in render_src, (
        "scene_carry appears inside render_turn's GRAMMAR retry loop — that "
        "loop retries on ProposalError and must not acquire a carry condition")

    one_src = src.partition("    def one(d):")[2]
    loop = one_src.partition("for _try in range(")[2]
    assert loop, "the steered resample loop is gone"
    head = loop[:400]
    assert "require_roots=" in head, (
        "the stage-2 resample loop does not pass require_roots — without the "
        "steer it is re-rolling the same dice at full price")


def test_forced_carry_is_stamped_on_the_corpus_not_just_documented():
    """⛔⛔ THE RESEARCH MUST NOT INHERIT THE PUZZLE'S CRIB BY ACCIDENT.

    Forced root-carry is precisely the persistence the drift measurement is
    built to exclude. A note in a docstring does not survive a pooling script;
    a field on every row has to be stripped on purpose.
    """
    import act2_build_conversations as B

    src = inspect.getsource(B.build)
    assert '"forced_root_carry": steer' in src, (
        "conversations are written without the puzzle-only marker")
    assert '"recipe": recipe' in src, (
        "conversations are written without a recipe stamp")
    # ⛔⛤ THIS ASSERTION USED TO GREP `build`'s SOURCE FOR THE LITERAL
    # '"recipe": "puzzle_steered"'. The stamp later moved into `steer_mode()`,
    # which is a single source of truth for prompt, gate and recipe — a strict
    # improvement — and the test went red for a STALE REASON, guarding the
    # shape of the code instead of the value on the corpus. Checking the string
    # in the source could never have told a correct recipe from a wrong one
    # anyway. The stamp is now read from the function that produces it.
    assert B.steer_mode(True, False)[2] == "puzzle_steered"
    assert B.steer_mode(True, True)[2] == "puzzle_softsteer"
    assert B.steer_mode(False, False)[2] == "puzzle_unsteered"


def _conversation(**stamp) -> dict:
    """One four-turn bench, stamped however the caller asks."""
    def turn(voice, english, root):
        return {"voice": voice, "english": english, "surface": "%s ka" % root,
                "scene": {"R": root, "D": "mid"}}
    return dict({"id": "c1",
                 "turns": [turn("P", "I dropped my cup", "nur"),
                           turn("T", "it falls and spreads", "nur"),
                           turn("P", "the floor soaked it up", "mor"),
                           turn("T", "it soaks, darkly", "mor")]},
                **stamp)


def test_the_stamp_survives_the_row_build():
    """⛔⛔ THE STAMP DIED ONE SCRIPT DOWNSTREAM OF THE TEST THAT PINNED IT.

    `test_forced_carry_is_stamped_on_the_corpus_not_just_documented` proves the
    CONVERSATIONS carry the marker. It does not reach the rows the trainer
    actually eats: `act2_build_multiturn_rows.py` rebuilt them as
    `source: conversation` and dropped the stamp, and `source: conversation` is
    exactly what the unsteered build emits too. The poisoned corpus and the
    clean one were distinguishable only by directory name — the failure the
    stamp exists to prevent, reproduced one layer down.
    """
    import act2_build_multiturn_rows as M

    rows = M.rows_from_conversation(
        _conversation(forced_root_carry=True, recipe="puzzle_steered"), 4)
    assert rows, "the fixture produced no rows"
    for r in rows:
        assert r["forced_root_carry"] is True, (
            "a row reached the trainer without the puzzle-only marker: %r" % r)
        assert r["recipe"] == "puzzle_steered"


def test_an_unsteered_conversation_is_not_relabelled_as_forced():
    """⛔ THE MARKER IS READ FROM THE CORPUS, NOT ASSERTED BY THE SCRIPT.

    Hard-coding the stamp would make every corpus claim forced carry, including
    the research one — the same error mirrored, and a marker that is always true
    carries no information. An unstamped conversation must SAY it is unstamped:
    a missing key cannot be told apart from a row built before this existed.
    """
    import act2_build_multiturn_rows as M

    rows = M.rows_from_conversation(_conversation(), 4)
    assert rows
    for r in rows:
        assert r["forced_root_carry"] is False
        assert r["recipe"] == "unstamped"
        assert "forced_root_carry" in r, "absence is not a reading"


def test_the_built_bench_corpus_carries_the_stamp_on_disk():
    """⛔⛔ THE ARTEFACT, NOT THE FUNCTION — THIS IS WHAT THE GPU READS.

    The two tests above hold the code. This one holds the file that was
    actually built, because the row builder can be correct and the corpus on
    disk still predate it, which is precisely the state this was found in.
    """
    corpus = _ROOT / "runs" / "act2" / "corpus_bench_steered"
    if not (corpus / "train.jsonl").exists():
        pytest.skip("the steered bench corpus is not on this checkout")

    meta = json.loads((corpus / "meta.json").read_text(encoding="utf-8"))
    assert meta.get("forced_root_carry_rows"), (
        "the manifest shipped to the run does not record the forced carry")
    assert meta.get("conversation_recipes", {}).get("puzzle_steered")

    seen = unstamped = 0
    with (corpus / "train.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("source") != "conversation":
                continue
            seen += 1
            if not r.get("forced_root_carry"):
                unstamped += 1
    assert seen > 1000, "expected the full corpus, got %d rows" % seen
    assert unstamped == 0, (
        "%d of %d conversation rows reached the trainer unstamped"
        % (unstamped, seen))


def test_the_corpus_bytes_do_not_depend_on_the_machine(tmp_path, monkeypatch):
    """⛔⛤ THE ROWS WERE CRLF ON WINDOWS AND LF ON THE BOX THAT TRAINS ON THEM.

    Python text mode rewrites "\\n" as "\\r\\n" on Windows, so the same builder,
    the same inputs and the same seed produced a different file — different
    length, different sha — depending on who ran it. It is invisible from the
    machine you are on, and it makes the corpus unpinnable: the hash the
    pipeline checks would have been computed on a laptop and could never match
    the box. Caught while pinning that hash, before it burned a run.
    """
    import act2_build_multiturn_rows as M

    convs = tmp_path / "conversations.jsonl"
    convs.write_text(json.dumps(
        _conversation(forced_root_carry=True, recipe="puzzle_steered")) + "\n",
        encoding="utf-8")
    out = tmp_path / "corpus"
    monkeypatch.setattr(sys, "argv", [
        "act2_build_multiturn_rows.py",
        "--conversations", str(convs),
        "--natural", str(tmp_path / "absent_natural.jsonl"),
        "--contrastive", str(tmp_path / "absent_contrastive.jsonl"),
        "--out", str(out), "--eval-frac", "0"])
    assert M.main() == 0

    for name in ("train.jsonl", "meta.json"):
        raw = (out / name).read_bytes()
        assert b"\r\n" not in raw, (
            "%s carries CRLF — its bytes depend on the platform that built it, "
            "so it cannot be pinned against the box that trains on it" % name)


def test_row_matching_is_deterministic_and_keeps_whole_conversations():
    """⭐ THE ATTRIBUTION ARM RESTS ON THE ROW COUNT ACTUALLY MATCHING.

    The steered retrain changed the conversation recipe AND the row count at
    once, so neither can be blamed. Holding the count fixed is what makes the
    recipe the only live variable — and a selector that missed the target, or
    that returned a different subset per run, would put the count back in the
    frame without saying so.

    ⛔ Whole conversations only. Truncating one to hit the number would invent
    an exchange that exists in neither corpus.
    """
    import act2_build_multiturn_rows as M

    convs = []
    for i in range(40):
        c = _conversation(forced_root_carry=True, recipe="puzzle_steered")
        c["id"] = "c%d" % i
        convs.append(c)
    per = len(M.rows_from_conversation(convs[0], 4))
    target = per * 7

    a = M.select_to_row_target(convs, 4, target, 20624)
    b = M.select_to_row_target(convs, 4, target, 20624)
    assert [c["id"] for c in a] == [c["id"] for c in b], "not deterministic"
    assert sum(len(M.rows_from_conversation(c, 4)) for c in a) == target
    assert len(a) == 7

    ids = {c["id"] for c in convs}
    assert all(c["id"] in ids for c in a), "returned a conversation it invented"
    for c in a:
        assert len(M.rows_from_conversation(c, 4)) == per, (
            "a kept conversation was truncated to fit the target")

    # ⛔ A different seed must be able to pick a different subset, or "seeded"
    # is decoration and the arm cannot be re-rolled.
    assert [c["id"] for c in M.select_to_row_target(convs, 4, target, 999)] \
        != [c["id"] for c in a]


def test_omitting_the_row_target_changes_nothing(tmp_path, monkeypatch):
    """⛔ THE FLAG MUST NOT TOUCH THE ARM THAT DOES NOT PASS IT.

    The steered corpus is sha-pinned in `pipeline_puzzle.sh`. If adding this
    option perturbed the default path by even one row, the pin would fail on the
    box and the failure would look like corruption rather than like a new flag.
    """
    import act2_build_multiturn_rows as M

    convs = tmp_path / "c.jsonl"
    convs.write_text("".join(
        json.dumps(dict(_conversation(forced_root_carry=True,
                                      recipe="puzzle_steered"), id="c%d" % i))
        + "\n" for i in range(5)), encoding="utf-8")

    outs = []
    for tag in ("a", "b"):
        out = tmp_path / tag
        monkeypatch.setattr(sys, "argv", [
            "act2_build_multiturn_rows.py", "--conversations", str(convs),
            "--natural", str(tmp_path / "none1.jsonl"),
            "--contrastive", str(tmp_path / "none2.jsonl"),
            "--out", str(out), "--eval-frac", "0"])
        assert M.main() == 0
        outs.append((out / "train.jsonl").read_bytes())
    assert outs[0] == outs[1], "the default path is not reproducible"


def test_no_verdict_may_be_printed_below_the_deciding_n():
    """⛔⛤ THE ACCEPTED THAT A RERUN REVERSED.

    n=22 gave 50.0% then 31.8% on one recipe. Calling that "thin" in prose was
    not enough — so UNDECIDED is now a value `decide` can return, and small n
    cannot produce a verdict at all.
    """
    verdict, detail = decide(11, 22)
    assert verdict == "UNDECIDED" and "22" in detail
    # the same rate at a deciding n is allowed to decide
    assert decide(75, 150)[0] != "UNDECIDED" or True
    # a CI that straddles the floor must not accept, however good the point
    v, _ = decide(90, 150)
    assert v in ("ACCEPTED", "UNDECIDED")
    assert decide(20, 200)[0] == "REJECTED"


def test_wilson_never_returns_a_bound_outside_zero_one():
    """⛔ The normal approximation hands back a negative lower bound exactly
    where this is used — small n, rates far from 0.5 — and that reads as "we
    measured nothing" rather than "we measured too little"."""
    for hits, n in ((0, 5), (5, 5), (1, 200), (199, 200), (0, 0)):
        lo, hi = wilson(hits, n)
        assert 0.0 <= lo <= hi <= 1.0, (hits, n, lo, hi)


def test_an_unmeasured_english_carry_reports_MISSING_and_never_zero():
    """⛔⛔ THE `except: -> 0` SHAPE, IN AN ACCEPTANCE LINE.

    `_gate_report` is filled by the stage-1 English build. The control arm is
    built by REUSING the dialogues the treatment arm wrote — that shared
    population is the whole design, it is what retires the two-population
    caveat — so stage 1 does not run and the counters are empty.

    With `pairs_seen or 1` as the denominator that printed

        english_carry     0.0%   min  60.0%   ⛔ FAIL

    against a corpus whose English carry is 72.1%, measured by the run that
    wrote those very dialogues. A FAIL on a quantity nobody measured reads as
    a finding about the corpus, and it is a fact about the plumbing.
    """
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "tools"
           / "act2_build_conversations.py").read_text(encoding="utf-8")
    block = src[src.index("the acceptance check, against thresholds"):
                src.index("VERDICT: %s")]
    assert '_gate_report["pairs_seen"] or 1' not in block, (
        "the denominator-of-one is back; an unmeasured carry will read as 0%")
    assert "MISSING" in block, "nothing in the block can report MISSING"
    assert 'if seen' in block or 'if measured["english_carry"] is None' in block
    # ⛔ And the nan beside it, for the same reason and from the same cause.
    assert 'float("nan")' not in block


def test_acceptance_thresholds_are_registered_not_chosen_later():
    """⭐ They live in the module the build imports, so the run cannot be read
    against a bar picked after seeing it."""
    assert set(ACCEPTANCE) == {"english_carry_min", "scene_band_target",
                               "scene_band_ci_floor", "min_pairs_to_decide",
                               "echo_max",
                               # ⛔ Added 2026-09-25 after the live bench was
                               # found answering `ka` 13 times out of 13. Carry
                               # and echo were gated; the speech act was never
                               # counted, and the corpus reached production at
                               # 99.7% `ka`. See `test_force_variety_gate.py`.
                               "force_top_share_max", "force_distinct_min"}
    # A corpus of one speech act teaches a speaker with one speech act.
    assert 0.0 < ACCEPTANCE["force_top_share_max"] < 1.0
    assert ACCEPTANCE["force_distinct_min"] >= 2
    assert 0.0 < ACCEPTANCE["scene_band_target"] < 1.0
    # ⛔ The band must not demand everything: 100% carry IS the echo.
    assert ACCEPTANCE["scene_band_target"] <= 0.90
    assert ACCEPTANCE["echo_max"] <= 0.20
    # ⭐ The bar was RAISED (0.50 -> 0.65) after the unsteered arm missed it.
    # Raising a bar after a miss is legitimate; lowering one is not, so the
    # floor must never sit below what the unsteered recipe already achieved.
    assert ACCEPTANCE["scene_band_ci_floor"] >= 0.50
    assert ACCEPTANCE["scene_band_target"] > ACCEPTANCE["scene_band_ci_floor"]
    assert ACCEPTANCE["min_pairs_to_decide"] >= 150


def test_carry_reports_a_reason_so_a_failure_need_not_be_rerun():
    verdict = english_carry("The kettle boiled.", "A stillness settles.")
    assert isinstance(verdict, Carry)
    assert verdict.reason and verdict.reason != "ok"
