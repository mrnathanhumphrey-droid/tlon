"""⛔⛔ THE FIRST EXCHANGE MAY DRAW AGAIN. WHAT THAT MUST AND MUST NOT DO.

The onset baseline (n=192) found the conversation is settled by its first
exchange — P(carry | previous turn carried) = 0.842 against 0.156 if it missed,
and turn 1 has no context at all — so the three-turn reach is
`p1 + (1-p1)*0.3325` and raising p1 is the whole lever. The reseed run (n=188,
k=3, provocation held FIXED) measured what a retry buys: 48.9% of missed first
replies carry within three more draws, p1 0.511 -> 0.750, joint 0.673 -> 0.833.

This pins the SHAPE of that retry, which is where it could go wrong:
  * it must never make a turn worse than not retrying
  * it must not fire on later turns, which would be rejection sampling toward
    the repetitive collapse the carry BAND exists to prevent
  * it must not fire when the first reply already carries, or every reader pays
    the latency for the ones who do not
"""
from __future__ import annotations

import importlib
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@pytest.fixture(autouse=True)
def expanded_lexicon(monkeypatch):
    from tlon.grammar import classes as C
    monkeypatch.setenv("TLON_LEXICON", "lexicon_expanded.yaml")
    C.reset_caches()
    yield
    C.reset_caches()


@pytest.fixture
def sp():
    return importlib.import_module("puzzle.speaker")


def corpus_pair():
    """A real (provocation, carrying-reply) pair out of the steered corpus."""
    src = ROOT / "runs" / "act2" / "corpus_conv_steered" / "conversations.jsonl"
    if not src.exists():
        pytest.skip("steered corpus not in this checkout")
    # ⛔⛔ THE SCENE IS RETURNED AS `parse()` RETURNS IT -- a Scene DATACLASS,
    # which is what `generate` hands back. Feeding the corpus's proposer DICT
    # here would test a shape the serving path never sees, and that difference
    # is precisely the bug this file caught.
    from tlon.grammar.parse import parse
    for line in src.read_text(encoding="utf-8").splitlines():
        turns = json.loads(line)["turns"]
        for a, b in zip(turns, turns[1:]):
            if a["voice"] == "P" and b["voice"] == "T":
                return a["surface"], parse(b["surface"])
    pytest.skip("no P->T pair found")


def non_carrying():
    """A real, parseable reply that shares NO root with `corpus_pair()`'s
    provocation — so it fails the band for the right reason.

    ⛔ NOT `None` and NOT `{"node": {}}`. `_row` glosses every reply, and gloss
    wants a Scene; a stand-in of the wrong type makes the test fail on the
    fixture rather than on the behaviour under test.
    """
    from tlon.grammar import classes as C
    from tlon.grammar.parse import parse
    roots = frozenset(C.load()["classes"]["R"])
    prov, _ = corpus_pair()
    prior = frozenset(w for w in prov.split() if w in roots)
    src = ROOT / "runs" / "act2" / "corpus_conv_steered" / "conversations.jsonl"
    for line in src.read_text(encoding="utf-8").splitlines():
        for turn in json.loads(line)["turns"]:
            s = turn["surface"]
            if not (frozenset(w for w in s.split() if w in roots) & prior):
                return parse(s)
    pytest.skip("no disjoint surface found")


class Cand:
    def __init__(self, scene, ok=True, surface="x"):
        self.ok, self.scene, self.surface = ok, scene, surface
        self.refused, self.error, self.seconds = None, None, 0.0


# ── the predicate ───────────────────────────────────────────────────────────

def test_carries_uses_the_band_not_bare_overlap(sp):
    """⛔⛔ A PARROT SCORES 100% ON OVERLAP AND 0% ON THE BAND. Retrying on
    overlap would select for exactly the echo the band refuses."""
    prov, scene = corpus_pair()
    from tlon.act2.carry import scene_roots
    from tlon.grammar import classes as C
    roots = frozenset(C.load()["classes"]["R"])
    prior = frozenset(w for w in prov.split() if w in roots)
    # an echo: every root carried, nothing new
    from tlon.grammar.parse import parse as _parse
    echo = _parse(" ".join(w for w in prov.split()
                           if w not in roots or w == sorted(prior)[0]))
    assert sp.carries(prov, Cand(echo)) is False


def test_a_rootless_provocation_is_not_retried(sp):
    """⛔ Nothing to carry FROM. Retrying would burn the whole budget on a turn
    no reply could satisfy and score every draw a failure."""
    assert sp.carries("ka", Cand(non_carrying())) is True


def test_a_refused_candidate_never_counts_as_carrying(sp):
    prov, scene = corpus_pair()
    assert sp.carries(prov, Cand(scene, ok=False)) is False
    assert sp.carries(prov, None) is False


# ── the choice ──────────────────────────────────────────────────────────────

def test_a_carrying_candidate_is_preferred(sp):
    prov, scene = corpus_pair()
    dud = Cand(non_carrying())
    good = Cand(scene)
    assert sp.pick_reply([dud, good], prov) is good


def test_the_first_usable_candidate_is_kept_when_none_carries(sp):
    """⛔⛔ A RETRY MUST NEVER MAKE A TURN WORSE THAN NOT RETRYING."""
    prov, _ = corpus_pair()
    first = Cand(non_carrying())
    second = Cand(non_carrying())
    assert sp.pick_reply([first, second], prov) is first


def test_a_refusal_survives_rather_than_becoming_a_blank(sp):
    """⛔ `_row` reports a refusal WITH the text explaining it. Returning None
    would turn a stated refusal into an empty panel."""
    prov, _ = corpus_pair()
    last = Cand(None, ok=False)
    got = sp.pick_reply([Cand(None, ok=False), last], prov)
    assert got is last


def test_pick_reply_on_nothing_at_all(sp):
    assert sp.pick_reply([], "nu hlör") is None


# ── the loop, driven through the served turn ────────────────────────────────

class FakeBackend:
    conversation: list = []


def drive(sp, monkeypatch, scenes, provoke_pairs):
    """Run `turn` with scripted provoke replies; returns (out, draw count)."""
    prov, _ = corpus_pair()
    backend = FakeBackend()
    monkeypatch.setattr(sp.Speaker, "load", lambda self: backend)

    # ⛔ `_row` GLOSSES the write turn too, and gloss wants a Scene.
    from tlon.grammar.parse import parse
    written = Cand(parse(prov), surface=prov)
    monkeypatch.setattr(sp, "_bench", lambda direction, pairs: [])

    import tlon_converse
    monkeypatch.setattr(tlon_converse, "generate", lambda *a, **k: written)

    drawn = {"n": 0}
    seq = list(scenes)

    def fake_reply_to(self, provocation, pairs):
        drawn["n"] += 1
        return seq.pop(0) if seq else Cand(non_carrying())

    monkeypatch.setattr(sp.Speaker, "reply_to", fake_reply_to)
    out = sp.Speaker().turn("hello", [], provoke_pairs)
    return out, drawn["n"]


def test_no_retry_when_the_first_reply_already_carries(sp, monkeypatch):
    """⛔ Otherwise every reader pays the latency for the ones who miss."""
    _, scene = corpus_pair()
    out, drawn = drive(sp, monkeypatch, [Cand(scene)], provoke_pairs=[])
    assert drawn == 1
    assert out["replies_drawn"] == 1


def test_the_first_exchange_retries_up_to_the_budget(sp, monkeypatch):
    _, scene = corpus_pair()
    misses = [Cand(non_carrying()), Cand(non_carrying())]
    out, drawn = drive(sp, monkeypatch, misses + [Cand(scene)], provoke_pairs=[])
    assert drawn == 3, "should have drawn again until one carried"
    assert out["replies_drawn"] == 3


def test_the_budget_is_bounded(sp, monkeypatch):
    """⛔ 47 of 188 provocations never carried in four tries. Without a bound a
    hopeless turn would draw forever on a reader's first message."""
    out, drawn = drive(sp, monkeypatch, [Cand(non_carrying())] * 99,
                       provoke_pairs=[])
    assert drawn == 1 + sp.CARRY_RETRIES == 4


def test_a_LATER_exchange_never_retries(sp, monkeypatch):
    """⛔⛔ THE PRODUCT DECISION. Resampling for carry on every turn is
    rejection sampling toward the repetitive collapse the BAND exists to
    prevent — and only the first exchange was ever measured."""
    prov, _ = corpus_pair()
    out, drawn = drive(sp, monkeypatch, [Cand(non_carrying())] * 9,
                       provoke_pairs=[(prov, prov)])
    assert drawn == 1, "a later turn drew %d replies" % drawn


def test_the_retry_can_be_switched_off(sp, monkeypatch):
    monkeypatch.setattr(sp, "CARRY_RETRIES", 0)
    out, drawn = drive(sp, monkeypatch, [Cand(non_carrying())] * 9,
                       provoke_pairs=[])
    assert drawn == 1
