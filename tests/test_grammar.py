"""Borges conformance, round-trip, canonicalisation, and mask soundness."""
from __future__ import annotations
import pathlib
import random
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tlon.grammar import classes as C, fsm            # noqa: E402
from tlon.grammar.canon import canon_json, fiber_size, id_of, utterance_id  # noqa: E402
from tlon.grammar.parse import ParseError, parse, render   # noqa: E402

BORGES = "hlör u fang axaxaxas mlö ka"


# ── the golden test. Never allowed to fail. ────────────────────────────────
def test_borges_line_parses():
    s = parse(BORGES)
    assert s.node.root == "mlö"                       # it mooned
    assert s.node.orient == ["hlör"]                  # upward
    assert len(s.node.edges) == 1
    rel, child = s.node.edges[0]
    assert rel == "u"                                 # beyond / behind
    assert child.root == "fang"                       # the onstreaming
    assert child.aspect == ("ax", 3)                  # ax-ax-ax-as, unceasing
    assert s.force == "ka"


def test_borges_line_round_trips():
    assert render(parse(BORGES)) == BORGES


def test_borges_line_passes_the_mask():
    assert fsm.accepts(BORGES)


def test_attested_morphemes_are_phonotactically_legal():
    lex = C.load()
    p = lex["phonotactics"]
    legal = {o + v + c for o in p["onsets"] for v in p["nuclei"] for c in p["codas"]}
    for form in ("hlör", "u", "fang", "mlö", "ax"):
        assert form in legal, f"{form} left the language"


# ── round-trip over the whole space ────────────────────────────────────────
def _random_scene(rng: random.Random, depth: int, budget: list[int]) -> str:
    """Build a random legal surface string directly, bypassing the FSM, so the
    mask is tested against an independent source of legal utterances."""
    lex = C.load()
    k = C.constraints()
    out: list[str] = []

    def pred(d: int) -> None:
        for cls in ("Q", "T", "M"):
            if budget[0] > d + 2 and rng.random() < 0.25:
                out.append(rng.choice(list(lex["classes"][cls])))
                budget[0] -= 1
        for _ in range(rng.randint(0, k["MAX_ORIENT_PER_PRED"])):
            if budget[0] > d + 2:
                out.append(rng.choice(list(lex["classes"]["O"])))
                budget[0] -= 1
        if d > 0:
            for _ in range(rng.randint(0, k["MAX_CLAUSES_PER_PRED"])):
                if budget[0] > d + 4 and rng.random() < 0.5:
                    out.append(rng.choice(list(lex["classes"]["L"])))
                    budget[0] -= 1
                    pred(d - 1)
        out.append(rng.choice(list(lex["classes"]["R"])))
        budget[0] -= 1
        if budget[0] > d + 6 and rng.random() < 0.4:
            reps = rng.randint(1, k["MAX_ASPECT_REPS"])
            out.append(rng.choice(list(lex["classes"]["A"])) * reps
                       + lex["aspect_closer"])
            budget[0] -= reps + 1
        if budget[0] > d + 2 and rng.random() < 0.3:
            out.append(rng.choice(list(lex["classes"]["D"])))
            budget[0] -= 1

    pred(depth)
    out.append(rng.choice(list(lex["classes"]["F"])))
    return " ".join(out)


def _corpus(n: int = 600) -> list[str]:
    rng = random.Random(20260817)
    k = C.constraints()
    got = []
    while len(got) < n:
        text = _random_scene(rng, rng.randint(0, k["MAX_DEPTH"]),
                             [k["MAX_MORPHS"] - 1])
        try:
            parse(text)
        except ParseError:
            continue
        got.append(text)
    return got


CORPUS = _corpus()


def test_corpus_is_not_trivial():
    """A corpus of bare two-morpheme utterances would pass everything below
    while testing nothing."""
    depths = set()
    for t in CORPUS:
        s = parse(t)

        def d(n, cur=0):
            return max([cur] + [d(c, cur + 1) for _, c in n.edges])
        depths.add(d(s.node))
    assert depths >= {0, 1, 2}, f"corpus never nests deeply: {depths}"
    assert any(parse(t).node.aspect for t in CORPUS)
    assert max(len(t.split()) for t in CORPUS) >= 8


@pytest.mark.parametrize("text", CORPUS[:200])
def test_round_trip(text):
    s = parse(text)
    assert canon_json(parse(render(s))) == canon_json(s)


@pytest.mark.parametrize("text", CORPUS[:200])
def test_mask_is_complete(text):
    """COMPLETENESS: the mask must never block a legal continuation."""
    assert fsm.accepts(text), f"mask rejected a legal utterance: {text}"


def test_mask_is_sound():
    """SOUNDNESS: anything the mask walks to completion must parse."""
    rng = random.Random(7)
    lex = C.load()
    for _ in range(300):
        st = fsm.MaskState()
        toks: list[str] = []
        while not st.done:
            allowed = fsm.legal_classes(st)
            assert allowed, f"mask dead-ended after {' '.join(toks)}"
            cls = rng.choice(sorted(allowed))
            param = rng.choice(sorted(allowed[cls])) if cls == "A" else None
            if cls == "A":
                toks.append(rng.choice(list(lex["classes"]["A"])) * param
                            + lex["aspect_closer"])
            else:
                toks.append(rng.choice(list(lex["classes"][cls])))
            st = fsm.step(st, cls, param)
        parse(" ".join(toks))          # must not raise


# ── canonicalisation: the honesty of the repeat counter ────────────────────
def test_permuted_orientations_collide():
    """Different string, same meaning -> MUST be the same utterance_id, or the
    public 'days without a repeat' counter is a lie."""
    a = "hlör nar mlö ka"
    b = "nar hlör mlö ka"
    assert a != b
    assert id_of(a) == id_of(b)


def test_permuted_sibling_clauses_collide():
    a = "u fang sen tris mlö ka"
    b = "sen tris u fang mlö ka"
    assert a != b
    assert id_of(a) == id_of(b)


def test_different_meanings_do_not_collide():
    """Red-proof for the two tests above: if canon collapsed everything, they
    would pass vacuously."""
    assert id_of("hlör mlö ka") != id_of("nar mlö ka")
    assert id_of("hlör mlö ka") != id_of("hlör fang ka")
    assert id_of("hlör mlö ka") != id_of("hlör mlö ki")   # illocution matters
    assert id_of("mlö axas ka") != id_of("mlö axaxas ka")  # reps matter


def test_absence_is_not_neutrality():
    """Spec §5.2: an unstated modality is not the same as an asserted one."""
    assert id_of("mlö ka") != id_of("ten mlö ka")


def test_fiber_of_a_fixed_scene_is_the_permutation_count():
    assert fiber_size(parse("mlö ka")) == 1
    assert fiber_size(parse(BORGES)) == 1
    assert fiber_size(parse("hlör nar mlö ka")) == 2          # 2! orientations
    assert fiber_size(parse("u fang sen tris mlö ka")) == 2   # 2! siblings


# ── structural constraints actually bite ──────────────────────────────────
def test_duplicate_sibling_clauses_rejected():
    with pytest.raises(ParseError):
        parse("u fang u fang mlö ka")


def test_depth_cap_enforced():
    k = C.constraints()
    text = " ".join(["u"] * (k["MAX_DEPTH"] + 1) + ["fang"]
                    * (k["MAX_DEPTH"] + 2) + ["ka"])
    with pytest.raises(ParseError):
        parse(text)


def test_slot_order_enforced():
    parse("sim nu ten hlör mlö ka")                  # Q T M O R F -- legal
    with pytest.raises(ParseError):
        parse("nu sim hlör mlö ka")                  # T before Q -- illegal


def test_classes_are_surface_disjoint():
    """LL(1) depends on it; classes.load() asserts it, so just prove the
    assertion is reachable."""
    lex = C.load()
    forms = [f for t in lex["classes"].values() for f in t]
    assert len(forms) == len(set(forms))
