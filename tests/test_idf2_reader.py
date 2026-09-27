"""IDF-2 §0e — the reader shares the fold, and the marker is spelt once.

LOCK `37363296`. Every test here runs against a **fake backend**: no GPU, no
weights, no spend. The thing under test is the plumbing — which payload reaches
`generate` — and that is decidable without a model.

⛔⛔ THE CENTRAL ASSERTION IS A NEGATIVE ONE. `marker_fn=None` must send the
BARE SURFACE, byte for byte, because every pre-IDF-2 caller takes that path:
the dose curve, the CLI, `act2_model_carry`. If threading IDF-2's argument
through `model_chain` changed the default payload by one character, every
release read in the campaign would silently become a different measurement
than the one its number was recorded under — and nothing else would notice.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from tlon.discourse import transient as TR              # noqa: E402


class Recorder:
    """A backend that records nothing and generates a fixed legal surface.

    ⭐ It captures the PAYLOAD, which is the only thing these tests are about.
    """

    def __init__(self, reply):
        self.reply = reply
        self.payloads = []


@pytest.fixture
def capture(monkeypatch):
    """Intercept `generate` and hand back a scripted surface. -> the payloads."""
    import act2_model_lag as ML

    seen = []

    class T:
        ok = True
        seconds = 0.0

        def __init__(self, surface):
            self.surface = surface

    def fake_generate(backend, direction, payload, history, **kw):
        seen.append(payload)
        return T(backend.reply)

    monkeypatch.setattr(ML, "generate", fake_generate)
    return seen


@pytest.fixture(scope="module")
def lex_r():
    return TR._lex_roots()


@pytest.fixture(scope="module")
def roots(lex_r):
    return sorted(lex_r)[:8]


# ── the negative assertion ─────────────────────────────────────────────────

def test_marker_none_sends_the_bare_surface_byte_for_byte(capture, roots):
    """⛔⛔ The default path is UNCHANGED. Every pre-IDF-2 reading depends on
    it, and a one-character drift here would redefine them all silently."""
    import act2_model_lag as ML
    seed = " ".join(roots[0:3])
    reply = " ".join(roots[2:5])
    ML.model_chain(Recorder(reply), seed, turns=4)
    assert capture == [seed, reply, reply]
    assert all("\n" not in p for p in capture)
    assert all(TR.MARKER_PREFIX not in p for p in capture)


def test_the_default_is_literally_none_not_a_none_marker():
    """⭐ `marker_fn=None` and `marker=marker_none` are DIFFERENT ARMS — one is
    the historical reader, the other is M-strip. Conflating them would make
    the control look like the baseline."""
    assert TR.marker_stimulus("x", None) == "x"
    assert TR.marker_stimulus("x", TR.marker_line(())) == "x\nlet go: (none)"


# ── the marker reaches the payload, on its own line ────────────────────────

def test_the_marker_is_its_own_line_and_the_surface_is_untouched(capture,
                                                                 roots, lex_r):
    import act2_idf2 as I
    import act2_model_lag as ML
    seed = " ".join(roots[0:3])
    reply = " ".join(roots[1:4])
    ML.model_chain(Recorder(reply), seed, turns=4,
                   marker_fn=I.marker_held, lex_r=lex_r)
    for p in capture:
        head, _, tail = p.partition("\n")
        # ⛔ The Tlön surface is byte-identical to what the bare path sends;
        # everything added is after the newline, so it strips exactly.
        assert head in (seed, reply)
        assert tail.startswith(TR.MARKER_PREFIX)


def test_held_is_none_on_the_first_two_turns_at_read_time(capture, roots,
                                                          lex_r):
    """⛔ §1's off-by-one, asserted on the READER as well as the builder.
    Generating turn 2 leaves `out` one element long, so there is no `t−2`."""
    import act2_idf2 as I
    import act2_model_lag as ML
    seed = " ".join(roots[0:3])
    reply = " ".join(roots[1:4])
    ML.model_chain(Recorder(reply), seed, turns=4,
                   marker_fn=I.marker_held, lex_r=lex_r)
    assert capture[0].endswith(TR.MARKER_NONE), (
        "the marker on the first generated turn must be (none)")
    # ⭐ And it must NOT stay (none) forever, or the M arm is silently M-strip.
    assert not capture[-1].endswith(TR.MARKER_NONE)


def test_the_held_marker_names_the_real_intersection(capture, roots, lex_r):
    import act2_idf2 as I
    import act2_model_lag as ML
    seed = " ".join(roots[0:3])
    reply = " ".join(roots[1:4])
    ML.model_chain(Recorder(reply), seed, turns=4,
                   marker_fn=I.marker_held, lex_r=lex_r)
    # turn 3 onward: prev and t-2 are both `reply`, so held == roots(reply)
    named = capture[-1].split("\n")[1][len(TR.MARKER_PREFIX):].split()
    assert set(named) == set(roots[1:4])


# ── M-shuffle is a real control, not a weaker M ────────────────────────────

def test_shuffle_never_names_a_held_root(capture, roots, lex_r):
    """⛔ If the false marker leaked true roots it would be a weaker copy of M,
    and its prediction (lag-2 RISES) could not be distinguished from M's."""
    import act2_idf2 as I
    import act2_model_lag as ML
    seed = " ".join(roots[0:5])
    reply = " ".join(roots[2:8])
    fn = I.marker_shuffle(seed=1)
    ML.model_chain(Recorder(reply), seed, turns=6, marker_fn=fn, lex_r=lex_r)
    for p in capture[1:]:
        named = set(p.split("\n")[1][len(TR.MARKER_PREFIX):].split())
        named.discard(TR.MARKER_NONE)
        prev = p.split("\n")[0]
        # every named root is from t-1 ...
        assert named <= TR.roots_of(prev, lex_r)
    assert fn.shortfall[0] > 0, "the shortfall counter must actually count"


# ── the identity §1 requires ───────────────────────────────────────────────

def test_the_reader_calls_the_same_held_object_as_the_builder():
    """⛔⛔ §1: builder, row builder and reader resolve THE SAME OBJECT."""
    import act2_idf2 as I
    import act2_model_lag as ML
    assert ML.TRheld is TR.held
    assert I.TR.held is TR.held
    src = pathlib.Path(I.__file__).read_text(encoding="utf-8")
    assert "TR.marker_line(TR.held(out, out[-1], lex_r))" in src


def test_the_marker_spelling_is_imported_not_restated():
    for mod in ("tools/act2_idf2.py", "tools/act2_model_lag.py"):
        src = (ROOT / mod).read_text(encoding="utf-8")
        assert '"let go:"' not in src, (
            "%s restates the marker prefix; it must import MARKER_PREFIX" % mod)
        assert '"(none)"' not in src, (
            "%s restates the (none) token; it must import MARKER_NONE" % mod)


def test_the_reader_refuses_greedy(monkeypatch):
    """⛔ §0e: the wrapper inherits `read_lag`'s T = 0 refusal, unweakened."""
    import act2_idf2 as I
    with pytest.raises(ValueError, match="GREEDY"):
        I.read_lag_held(object(), temperature=0.0)


@pytest.fixture(scope="module")
def real_chains():
    """⛔ REAL chains from the real generator. `rows_from` parses every target
    surface and asserts `render(parse(s)) == s`, so a hand-built fixture of
    bare roots is not merely unrealistic — it cannot reach the code under
    test at all.
    ⚠️ Sized UP rather than gated down. `build_transient` runs
    `check_force_pair_fairness` unconditionally and at 6 chains a force pair
    goes unrepresented by chance — IDF-1b's D2, met again. The guard is
    correct; the fixture was too small.
    """
    from tlon.act2 import corpus as C1
    from tlon.discourse import force_map as FM
    return TR.build_transient(60, turns=8, pairs=C1.build(800, seed=7), seed=7,
                              responsiveness=1.0, fmap=FM.DERIVED_v1,
                              verify=False, barred_fn=TR.held)


def test_the_row_builder_default_is_byte_identical(real_chains):
    """⛔⛔ THE OTHER DEFAULT PATH. Every corpus in this campaign was built by
    `rows_from(chains)` with no marker. If threading IDF-2's flag changed that
    output by one character, every existing corpus would stop being
    reproducible from its own manifest — and the diff would be invisible."""
    from act2_build_multiturn import rows_from
    rows = rows_from(real_chains)
    want = [prev.surface for ch in real_chains
            for prev, _ in zip(ch, ch[1:])]
    assert [r["prompt"] for r in rows] == want
    assert all("\n" not in r["prompt"] for r in rows)
    assert all(TR.MARKER_PREFIX not in r["prompt"] for r in rows)


def test_the_row_builders_marker_uses_the_chain_up_to_and_including_prev(
        real_chains, lex_r):
    """⛔⛔ THE SLICE, PINNED. `ch[:i+1]` is what `out` was when `cur` was
    drawn. `ch` would mark every row with the chain's FUTURE and `ch[:i]`
    would be off by one turn — and neither would raise."""
    from act2_build_multiturn import rows_from
    rows = rows_from(real_chains, marker=True)
    k, nonempty = 0, 0
    for ch in real_chains:
        for i, (prev, _) in enumerate(zip(ch, ch[1:])):
            line = rows[k]["prompt"].split("\n")[1]
            want = (frozenset() if i == 0 else
                    TR.roots_of(prev.surface, lex_r)
                    & TR.roots_of(ch[i - 1].surface, lex_r))
            assert line == TR.marker_line(want), "row %d" % k
            nonempty += 1 if want else 0
            k += 1
    assert nonempty, "no row carried a non-empty marker — the test is vacuous"


def test_builder_and_reader_produce_the_same_marker_for_the_same_chain(
        real_chains, lex_r):
    """⭐⭐ THE IDENTITY THAT MATTERS AT READ TIME. A corpus marked one way and
    read another puts the model off-distribution, and the arm would measure
    the mismatch instead of the marker."""
    import act2_idf2 as I
    from act2_build_multiturn import rows_from
    rows = rows_from(real_chains, marker=True)
    built = [r["prompt"].split("\n")[1] for r in rows]
    read = [I.marker_held(ch[:i + 1], lex_r)
            for ch in real_chains for i in range(len(ch) - 1)]
    assert built == read


def test_the_wrapper_adds_no_second_fold():
    """⭐ It must be a call, not a copy. A reader that re-implemented the chain
    loop would drop the guards that ARE the measurement."""
    import act2_idf2 as I
    src = pathlib.Path(I.__file__).read_text(encoding="utf-8")
    body = src.split("def read_lag_held", 1)[1].split("\ndef ", 1)[0]
    assert "return read_lag(" in body
    for guard in ("MIN_USABLE_TURNS", "resolving_power", "permutation_null"):
        assert guard not in body, (
            "read_lag_held re-implements %s instead of inheriting it" % guard)
