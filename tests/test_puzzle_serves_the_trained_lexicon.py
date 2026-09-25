"""⛔⛔ THE PUZZLE SPEAKS THE LANGUAGE ITS ADAPTER WAS TRAINED ON.

⛔⛤ IT DID NOT, AND NOTHING NOTICED. `tools/pipeline_battery.sh` exports
`TLON_LEXICON=lexicon_expanded.yaml`, so render 97.3%, carry 27.5% and choose
46.5% — every number v1 was chosen on — were measured against 218 roots. The
serving path set it NOWHERE: not `speaker.py`, not the Dockerfile's ENV block,
not `fly.toml [env]`, not `docker-entrypoint.sh`. A deploy would have run the
expanded-lexicon adapter against the frozen 156.

⭐ SIZED BEFORE IT WAS CALLED A BLOCKER: 2,284 of the 4,578 turns in the
adapter's own training corpus — 49.9% — use at least one of the 62
expanded-only roots. The gate refuses those scenes, so about half of what the
model wants to say returns as a refusal.

⛔⛔ AND IT FAILS CLOSED, WHICH IS WHY NO EXISTING TEST COULD SEE IT. A refusal
is a legitimate outcome in this product — `speaker.turn` documents it as "an
outcome, not an error". The container boots, `/healthz` passes, the gate reports
healthy, and the speaker is simply inarticulate. Identical in shape to the
`ct-s20624` default that outlived its evidence for eight days while the suite
stayed green: a suite that only checks the code does what the code says cannot
see a premise that stopped being true.
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

DOCKERFILE = ROOT / "puzzle" / "Dockerfile"
FLY = ROOT / "puzzle" / "fly.toml"
SPEAKER = ROOT / "puzzle" / "speaker.py"

#: The lexicon the served adapter was trained and measured on.
EXPANDED_HASH = "08c03b0a81330e4ba42883fa8b08c873"
FROZEN_HASH = "e2b8527010231a81fd31b6eeb9de3d8c"
EXPANDED_FILE = "lexicon_expanded.yaml"

try:
    import tomllib
except ModuleNotFoundError:                          # pragma: no cover
    tomllib = None


def _code(path: pathlib.Path) -> str:
    """The file with its prose stripped.

    ⛔ Both files EXPLAIN this bug at length and name the frozen lexicon while
    doing it. A raw search would fire on the explanation — this repo has
    shipped that mistake twice, once against a guard's own comment.
    """
    return "\n".join(ln for ln in path.read_text(encoding="utf-8").splitlines()
                     if not ln.lstrip().startswith("#"))


def test_the_image_sets_the_expanded_lexicon():
    m = re.search(r"TLON_LEXICON=(\S+)", _code(DOCKERFILE))
    assert m, ("⛔⛔ the Dockerfile sets no TLON_LEXICON — the container would "
               "serve the expanded-lexicon adapter on the frozen 156 roots")
    assert m.group(1).rstrip("\\") == EXPANDED_FILE


def test_fly_states_the_same_lexicon():
    if tomllib is None:
        pytest.skip("tomllib needs python 3.11+")
    env = tomllib.loads(FLY.read_text(encoding="utf-8")).get("env", {})
    assert env.get("TLON_LEXICON") == EXPANDED_FILE, (
        "⛔ fly.toml and the Dockerfile disagree about the language served")


def test_the_lexicon_file_is_actually_copied_into_the_image():
    """⛔ A correct ENV over an absent file is the `s20620` failure in a new
    costume: the name is right and there is nothing behind it. `lexicon_path`
    RAISES rather than falling back, so this one is at least loud — but it is
    loud at first request, on a public URL."""
    assert (ROOT / "tlon" / "grammar" / EXPANDED_FILE).is_file()
    assert "COPY tlon/" in _code(DOCKERFILE), (
        "the grammar package is not copied, so the lexicon cannot ship")


def test_the_speaker_pins_the_hash_not_merely_the_filename():
    """⛔⛔ AN ENV VAR IS A THING THAT CAN BE UNSET. Asserting the filename
    proves what someone WROTE; asserting the hash proves what got LOADED. The
    difference is the whole bug — every config above said nothing at all, and
    nothing at all is a valid config."""
    body = _code(SPEAKER)
    assert EXPANDED_HASH in body, (
        "⛔ speaker.py does not pin the trained lexicon's hash")
    assert "REFUSING TO START" in body, (
        "⛔ speaker.py does not refuse on a mismatch — it would serve anyway")


def test_the_speaker_does_not_set_the_lexicon_at_import():
    """⛔⛔ THE FIX THAT WOULD BREAK THE INSTRUMENT. `classes.py` is explicit
    that the frozen lexicon must stay the process default so the research
    campaign's standing verdicts keep meaning what they say. This module is
    imported by probes that choose their own lexicon — `act2_onset_carry`
    passes `--lexicon` — and a `setdefault` leaking out of here would re-point
    their instrument depending on import order, silently."""
    body = _code(SPEAKER)
    for bad in ('environ["TLON_LEXICON"]', "environ.setdefault(\"TLON_LEXICON\"",
                "setenv(\"TLON_LEXICON\""):
        assert bad not in body, (
            "⛔⛔ speaker.py assigns TLON_LEXICON at import (%r) — that leaks "
            "into every process that imports it" % bad)


def test_the_two_lexicons_really_are_different_enough_to_matter():
    """⭐ THE PREMISE, MEASURED RATHER THAN ASSERTED. If the expansion were
    cosmetic the blocker above would be theatre. It is not: the roots the
    frozen lexicon lacks are used by half the adapter's training corpus.
    """
    import yaml
    from tlon.grammar import classes as C

    g = ROOT / "tlon" / "grammar"
    frozen = set(yaml.safe_load((g / "lexicon.yaml").read_bytes())
                 ["classes"]["R"])
    expanded = set(yaml.safe_load((g / EXPANDED_FILE).read_bytes())
                   ["classes"]["R"])
    assert len(expanded - frozen) == 62
    assert frozen < expanded, "the expansion must be a superset"

    corpus = ROOT / "runs" / "act2" / "corpus_conv_dosed" / "conversations.jsonl"
    if not corpus.exists():
        pytest.skip("v1's corpus is not in this checkout")

    import json
    C.reset_caches()
    from tlon.act2.carry import scene_roots
    only, total, hit = expanded - frozen, 0, 0
    for line in corpus.read_text(encoding="utf-8").splitlines():
        for t in json.loads(line)["turns"]:
            total += 1
            if scene_roots(t.get("scene"), expanded) & only:
                hit += 1
    share = hit / total
    assert share > 0.40, (
        "⛔ the exposure measured %.1f%%, not the ~49.9%% this guard was "
        "written against — re-derive the blocker before trusting it" % (100 * share))


# ── the guard, RUN rather than read ─────────────────────────────────────────

@pytest.fixture
def speaker_module(monkeypatch):
    """⛔ NO 7B IS LOADED HERE. `_bench_backend_class()` only imports and
    subclasses, and the lexicon check sits BEFORE the adapter path is touched,
    so both cases below return through a raise long before any weights."""
    import importlib
    sys.path.insert(0, str(ROOT / "tools"))
    sp = importlib.import_module("puzzle.speaker")
    # ⛔⛔ A REAL ADAPTER DIRECTORY WOULD MAKE THE POSITIVE CASE LOAD A MODEL ON
    # THIS BOX. Pointed at nothing on purpose: the positive assertion is that
    # the lexicon gate was PASSED, which the adapter error proves.
    monkeypatch.setattr(sp, "ADAPTER", str(ROOT / "runs" / "__no_such_cell__"))
    return sp


def test_the_speaker_refuses_to_load_on_the_frozen_lexicon(
        speaker_module, monkeypatch):
    """⛔⛔ THE WHOLE BLOCKER, EXECUTED. Under the frozen lexicon this adapter's
    gate refuses ~half its own vocabulary and every refusal is a legal outcome,
    so nothing downstream can tell. The refusal has to happen here."""
    from tlon.grammar import classes as C
    sp = speaker_module
    monkeypatch.delenv("TLON_LEXICON", raising=False)
    C.reset_caches()
    try:
        with pytest.raises(sp.SpeakerError) as exc:
            sp.Speaker().load()
        assert "REFUSING TO START" in str(exc.value)
        assert FROZEN_HASH in str(exc.value), (
            "the refusal must name the lexicon it actually loaded")
    finally:
        C.reset_caches()


def test_the_speaker_passes_the_gate_on_the_expanded_lexicon(
        speaker_module, monkeypatch):
    """⭐ THE CONTROL. Without it the test above would pass against a speaker
    that refuses to start under EVERY lexicon — a guard that always fires
    proves nothing about the condition it names."""
    from tlon.grammar import classes as C
    sp = speaker_module
    monkeypatch.setenv("TLON_LEXICON", EXPANDED_FILE)
    C.reset_caches()
    try:
        with pytest.raises(sp.SpeakerError) as exc:
            sp.Speaker().load()
        msg = str(exc.value)
        assert "REFUSING TO START" not in msg, (
            "⛔ the lexicon gate fired on the CORRECT lexicon")
        assert "no adapter weights" in msg, (
            "expected to reach the adapter check, got: %s" % msg)
    finally:
        C.reset_caches()


# ── the bench must never outlive the turn that set it ───────────────────────

def test_a_refused_write_does_not_leak_its_bench_to_the_next_reader(
        speaker_module, monkeypatch):
    """⛔⛔ ONE PERSON'S CONVERSATION CONDITIONING A STRANGER'S.

    `backend.conversation` is a process-wide attribute. `turn` sets it for the
    WRITE call and `reply_to` clears the one it sets — but a REFUSED write
    never reaches `reply_to`, so before the `finally` the WRITE window survived
    the turn and would be handed to the next reader's first exchange.

    ⭐ The leak lives ONLY on the refusal path, which is the path least likely
    to be exercised by hand, and it would present as a stranger's first reply
    being oddly on-topic — not as an error.
    """
    from tlon.grammar import classes as C
    sp = speaker_module
    monkeypatch.setenv("TLON_LEXICON", EXPANDED_FILE)
    C.reset_caches()

    class FakeBackend:
        conversation: list = []

    backend = FakeBackend()
    monkeypatch.setattr(sp.Speaker, "load", lambda self: backend)

    # A REAL surface, because `_bench` silently DROPS a pair whose surface will
    # not re-parse. A made-up one produced an empty bench either way, so the
    # assertion below passed against the unfixed code -- the mutant survived
    # and the guard proved nothing.
    import json as _json
    src = ROOT / "runs" / "act2" / "corpus_conv_steered" / "conversations.jsonl"
    if not src.exists():
        pytest.skip("steered corpus not in this checkout")
    first = _json.loads(src.read_text(encoding="utf-8").splitlines()[0])
    pair = (first["turns"][0]["english"], first["turns"][0]["surface"])
    assert sp._bench(__import__("tlon_converse").WRITE, [pair]), (
        "the fixture pair does not survive _bench, so this test cannot bite")

    class Refused:
        ok = False
        surface = None
        scene = None
        refused = None
        error = "the gate would not pass it"
        seconds = 0.0

    import tlon_converse
    monkeypatch.setattr(tlon_converse, "generate",
                        lambda *a, **k: Refused())
    try:
        out = sp.Speaker().turn("anything", [pair], [])
    finally:
        C.reset_caches()

    assert out["tlon"] is None, "a refused write must produce no reply"
    assert backend.conversation == [], (
        "⛔⛔ the WRITE bench outlived a refused turn: %r"
        % (backend.conversation,))


# ── the second deploy config ────────────────────────────────────────────────

def test_the_modal_deploy_agrees_with_the_fly_one():
    """⛔⛔ TWO DEPLOY CONFIGS IS TWO PLACES TO GET THE LANGUAGE WRONG.

    `puzzle/fly.toml` and `puzzle/modal_app.py` both declare the environment a
    container comes up in. The lexicon defect this file exists for was exactly
    one config forgetting one variable — and it failed CLOSED, so everything
    reported healthy while the gate refused half the speaker's vocabulary.
    Adding a second deploy surface doubles that surface.

    ⭐ The hash check in `speaker.py` still catches it at load either way. This
    catches it at review, which is cheaper than catching it on a GPU.
    """
    import ast

    src = (ROOT / "puzzle" / "modal_app.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    env = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "env":
            for arg in node.args:
                if isinstance(arg, ast.Dict):
                    for k, v in zip(arg.keys, arg.values):
                        if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                            env[k.value] = v.value
    assert env, "could not read modal_app's .env() block"
    assert env.get("TLON_LEXICON") == EXPANDED_FILE, (
        "⛔⛔ the Modal deploy does not set the expanded lexicon (%r)"
        % env.get("TLON_LEXICON"))
    # ⛔ IMPORTED, NOT RE-SPELT.  owns the identity
    # of v1; a second literal here would be a second place to get it wrong.
    import importlib
    V1_CELL = importlib.import_module("test_puzzle_serves_v1").V1_CELL
    assert env.get("TLON_ADAPTER", "").endswith(V1_CELL), (
        "⛔⛔ the Modal deploy points at %r, not v1 (%r)"
        % (env.get("TLON_ADAPTER"), V1_CELL))
    assert "TURNSTILE_SECRET_KEY" not in env, (
        "⛔⛔ the Turnstile SECRET is in modal_app's env block — it is "
        "committed. It belongs in a Modal Secret.")
