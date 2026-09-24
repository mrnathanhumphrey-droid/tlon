"""THE SPEAKER — English in, Tlön out, and the pure-function translation.

⛔⛔ NOTHING IN THIS FILE SPELLS A PROMPT. The turn shape, the two directions and
the system strings all arrive by import from `tools/tlon_converse.py`, which in
turn imports them from the trainer and raises at import time if the trainer ever
loses a direction it serves under. Run 3 of this project was trained on one
framing and prompted under another, and 27/27 tests stayed green because no test
crossed that boundary. One import, one string, no drift.

⭐ WHAT THE MODEL ACTUALLY DOES, IN TWO GENERATIONS:

    your English  --write-->   Scene -> gate -> YOUR line in Tlön
    your Tlön     --provoke--> Scene -> gate -> ITS reply in Tlön

⛔ IT DOES NOT ANSWER WHAT YOU SAID. It is provoked by it and paints its own
scene. That is the trained behaviour, not a shortfall — `tlon_converse.BANNER`
has said so since the tool was written, and the puzzle's copy should say it too.

⛔⛔ THE MODEL GETS THE WINDOW, AND WITHOUT IT THERE IS NO PUZZLE. A Tlönian
sits down next to you on the bench: that moment and that interaction ARE the
context. If every reply is an unrelated scene, no root ever recurs, and a
reader has nothing to decode — the puzzle is the language, and a language is
only solvable because it repeats.

⭐⭐ HOW THE WINDOW IS FED, AND WHY IT IS NOT THE `arena` SHAPE.
The corpus's provoke rows are `prompt = prev.surface` — ONE bare Tlön surface —
but they are cut from CHAINS, where content walks forward from turn to turn.
So continuity is native to what this model was trained on; the corpus simply
never showed more than one turn inside a single flat string. The `arena` shape
would flatten a transcript into one user message, which is a shape no training
row ever had.

Instead the bench is handed over as REAL CHAT TURNS — prior exchanges as
alternating user/assistant messages, with the final user message still the bare
payload a training row contains. Every individual message keeps its trained
shape; the base is an instruct model that natively expects the alternation. The
conditioning is extended, not replaced.

⛔ THE CONTEXT HAS A TIME-OUT, AND IT IS TWO SEPARATE LIMITS. `CONTEXT_TURNS`
bounds how far back the model is shown; `BENCH_IDLE_MINUTES` ends a bench that
has gone cold, so a reader returning tomorrow starts a new moment rather than
resuming one neither party remembers.
"""
from __future__ import annotations

import os
import pathlib
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ⛔ IMPORTED LEAF-FIRST, NOT `from tlon.act2 import schema_bridge`. That form
# registers as an import of `tlon.act2` — the whole research package — and the
# allow-list guard rightly refused it. Widening the guard to admit the package
# would also admit `falsify` and `weight_delta`. Narrow the import instead.
from tlon.act2.schema_bridge import scene_to_proposal       # noqa: E402
from tlon.grammar.gloss import gloss                        # noqa: E402
from tlon.grammar.parse import ParseError, parse            # noqa: E402
from tlon.product.chat import MAX_ENGLISH_CHARS             # noqa: E402
from tlon.product.literary import literary                  # noqa: E402

from . import bench_prompt                                  # noqa: E402

#: ⛔ Defaults match the configuration the speaker was READ in (temperature 0.7,
#: max_new_tokens 256) so the thing on screen is the thing that was measured.
#: The one knowing exception is 4-bit — see `FOUR_BIT` below.
BASE_MODEL = os.environ.get("TLON_BASE", "Qwen/Qwen2.5-7B-Instruct")

#: ⭐⭐ v1 IS `dosed-s20624`, AND IT WAS CHOSEN ON THREE MEASURED AXES, not on
#: legality alone. At n=256 on battery c0e011637df51c1b:
#:
#:     render 97.3% [94.5, 98.7]   legal Tlön, at the ceiling
#:     carry  27.5% [22.3, 33.2]   the reader's crib, and genuine — bare
#:                                 overlap 27.8%, one echo in 255, so what
#:                                 recurs also says something new
#:     choose 46.5% [40.5, 52.6]
#:
#: It is STRICTLY DOMINANT over the other legal adapters: `rowmatch-s20624`
#: matches it on render (p=0.61) and is IDENTICAL on choose (119/256 both) while
#: carrying 0.8% — 34× less crib for nothing gained. `bench5208-s20624` carries
#: 1.6%. The only adapter that carries more is the fully-steered `bench-s20624`
#: at 77.0%, and it costs 15 points of legality (render 82.4%) — the trade Nate
#: ruled out: default to legal, let the window carry the rest of the coherence.
#:
#: ⛔⛤ THIS WAS `ct-s20624` UNTIL 2026-09-23, the pick made on 2026-09-15 before
#: any of the above existed. `ct` is the research campaign's content-transient
#: cell; it was never measured on carry at all, because no model-side carry
#: probe existed until the day this changed. A default that outlives the
#: evidence it was chosen on is how a product ships the wrong weights while
#: every test stays green.
#:
#: ⛔ The corpus behind it is a BLEND of two conversation populations, accepted
#: deliberately to save $32 when it was an experiment. That caveat is now under
#: a shipped v1; a single-population rebuild retires it and changes nothing else.
ADAPTER = os.environ.get("TLON_ADAPTER",
                         str(ROOT / "runs" / "puzzle_speaker" / "dosed-s20624"))
#: ⛔⛔⛔ THE LANGUAGE THIS ADAPTER SPEAKS, AND IT IS NOT THE PROCESS DEFAULT.
#:
#: `tlon/grammar/classes.py` makes the FROZEN 156-root lexicon the default and
#: says, correctly, that it must stay that way so the research campaign's
#: standing verdicts keep meaning what they say. But the puzzle is the one
#: caller that needs the other language: `tools/pipeline_battery.sh` exports
#: `TLON_LEXICON=lexicon_expanded.yaml`, so render 97.3% / carry 27.5% /
#: choose 46.5% — every number v1 was chosen on — were measured on 218 roots.
#:
#: ⛔⛤ AND NOTHING HERE SET IT. Not this file, not the Dockerfile's ENV, not
#: `fly.toml`, not the entrypoint. A deploy would have run this adapter against
#: the frozen lexicon, where **2,284 of the 4,578 turns in its own training
#: corpus (49.9%) use one of the 62 expanded-only roots** — the gate refuses
#: them, so roughly half of what the model wants to say comes back a refusal.
#: It fails CLOSED, which is why every health check would have stayed green.
#:
#: ⛔ THE ENV IS SET IN THE IMAGE, AND THIS CONSTANT IS THE PROOF IT TOOK. An
#: env var is a thing that can be unset; a hash compared at load is not. Do NOT
#: "simplify" this by calling `os.environ.setdefault` at import — this module is
#: imported by probes that choose their own lexicon, and a default that leaked
#: out of here would re-point their instrument silently.
LEXICON_HASH = os.environ.get("TLON_LEXICON_HASH",
                              "08c03b0a81330e4ba42883fa8b08c873")

TEMPERATURE = float(os.environ.get("TLON_TEMPERATURE", "0.7"))
MAX_NEW_TOKENS = int(os.environ.get("TLON_MAX_NEW_TOKENS", "256"))
DEVICE = os.environ.get("TLON_DEVICE", "cuda")

#: ⛔⛔ 4-BIT CHANGES THE MODEL AND EVERY MEASURED NUMBER IN THIS PROJECT IS
#: bf16. `tlon_converse`'s own `--4bit` help says so. It is on here because the
#: puzzle is a conversation, not a reading: nothing this app prints is a
#: measurement, and NF4 is what fits a 7B beside a KV cache on a 16 GB card
#: (measured: 7.21 GiB peak). ⛔ If anyone ever reads a number off this app,
#: that number is indicative and not comparable to the campaign's.
FOUR_BIT = os.environ.get("TLON_4BIT", "1") not in ("0", "", "false", "no")

#: ⛔ ALWAYS `trained`. Every message handed to the model keeps the bare shape a
#: corpus row has; context arrives as additional CHAT TURNS, not as a transcript
#: flattened into one user message. `arena` is the flattened shape and no
#: training row ever had it.
SHAPE = "trained"

#: How many past exchanges the model is shown. ⭐ THE TIME-OUT, IN TURNS.
#:
#: ⛔⛔ 4, BECAUSE THAT IS THE DEPTH THE CORPUS WAS BUILT AT. This was 8 — a
#: guess made before there was a corpus — and `runs/act2/corpus_bench` carries
#: context at depth ≤ 4. Serving 8 would show the model a history deeper than
#: any training row ever had, which is the ORIGINAL BUG in a new costume: the
#: whole reason context-ON came back worse than context-OFF was a served shape
#: the model had never seen. Train depth and serve depth are one number.
#: `test_puzzle_context.py` asserts no built row exceeds this.
CONTEXT_TURNS = int(os.environ.get("TLON_CONTEXT_TURNS", "4"))

#: ⭐ THE OTHER HALF OF THE TIME-OUT. A bench that has gone quiet this long is
#: over; the next thing said starts a new moment. Without it a reader returning
#: days later resumes a conversation neither they nor the model remember the
#: shape of, and the replies read as non-sequiturs for several turns.
BENCH_IDLE_MINUTES = int(os.environ.get("TLON_BENCH_IDLE_MINUTES", "45"))


class SpeakerError(RuntimeError):
    pass


def trained_pair(direction: str, user_payload: str,
                 assistant_surface: str) -> tuple[str, str]:
    """One prior exchange, in the EXACT shape a training row has.

    ⛔⛔ THE ASSISTANT TURN IS A JSON SCENE, NOT A BARE TLÖN SURFACE, AND
    GETTING THIS WRONG BROKE THE APP SILENTLY. The first version of the bench
    put surfaces in the assistant slots. Turn one worked — no context, so the
    branch was never taken — and turns two onward failed in under a second with
    no JSON in the generation at all: shown two "assistant" turns that were
    bare text, the model stopped emitting the object the gate parses. A bug
    that cannot appear on the first turn of a fresh session is exactly the kind
    that reaches a stranger on a public URL.

    ⭐ SO THE SERIALISATION IS NOT SPELLED HERE. `act2_finetune.row_messages`
    IS the trainer's fold — `act2_token_budget.py` already imports it for the
    same reason — and this hands it a row and takes back the two message
    contents it produces. If the trainer's format ever moves, this moves with
    it instead of drifting.
    """
    from act2_finetune import row_messages

    msgs = row_messages({"direction": direction,
                         "prompt": user_payload,
                         "scene": scene_to_proposal(parse(assistant_surface))})
    return msgs[1]["content"], msgs[2]["content"]


def _bench_backend_class():
    """`LocalBackend`, plus the bench it is sitting on.

    ⛔⛔ SUBCLASSED, NOT EDITED. `LocalBackend` is the campaign's measurement
    path — every F-LOCAL and lag reading in the project goes through it. A
    history parameter added there would change the instrument for the research
    as a side effect of shipping a chat app. This override lives in the puzzle
    and the research never constructs it.

    ⭐ THE ONLY THING IT CHANGES IS THE MESSAGE LIST. `call()` builds its prompt
    in exactly one place — `self._prompt(system, user)` — so overriding that one
    method is the whole of it: same decode, same JSON extraction, same
    `BackendError` with the raw generation attached.
    """
    from act2_backends import LocalBackend
    from tlon.act2.chat_shape import bench_prompt

    class BenchBackend(LocalBackend):

        #: [(user, assistant), ...] — set per call, always for ONE direction.
        conversation: list[tuple[str, str]] = []

        def _prompt(self, system: str, user: str) -> str:
            # ⛔⛔ THE CONSTRUCTION IS NOT SPELLED HERE AND MUST NOT BE. This
            # used to build the message list itself, which meant the serving
            # prompt and the training prompt were two copies of one idea — the
            # exact defect `chat_shape` exists to end. `bench_prompt` IS the
            # fold: the corpus builder reaches the same function through
            # `bench_train_text`, so train-shape equals serve-shape by
            # construction rather than by two people being careful.
            return bench_prompt(self.tok, system,
                                list(getattr(self, "conversation", ()) or ()),
                                user)

    return BenchBackend


class Speaker:
    """One process-wide model, loaded once, called under `guard.slot()`."""

    def __init__(self):
        self._backend = None
        self._lock = threading.Lock()
        self.load_seconds: float | None = None

    # ── loading ─────────────────────────────────────────────────────────────

    @property
    def ready(self) -> bool:
        return self._backend is not None

    def load(self):
        """⛔ IDEMPOTENT AND LOCKED. Two requests arriving before the first load
        finishes would otherwise put two 7B models on one card."""
        if self._backend is not None:
            return self._backend
        with self._lock:
            if self._backend is not None:
                return self._backend
            BenchBackend = _bench_backend_class()

            # ⛔⛔ REFUSE THE WRONG LANGUAGE BEFORE A 7B IS ON THE CARD. Served
            # against the frozen lexicon this adapter's gate refuses ~half its
            # own vocabulary — and every refusal is a valid outcome, so the app
            # would look healthy and merely seem inarticulate. Checked by HASH,
            # not by reading the env back: `TLON_LEXICON` naming a file is not
            # evidence that file is what got loaded.
            from tlon.grammar import classes as _C
            got = _C.load()["_hash"]
            if got != LEXICON_HASH:
                raise SpeakerError(
                    "⛔⛔ REFUSING TO START: this speaker was trained and "
                    "measured on lexicon %s but the process loaded %s (%d "
                    "roots, TLON_LEXICON=%r). Set TLON_LEXICON in the image "
                    "env; see the Dockerfile."
                    % (LEXICON_HASH, got, len(_C.load()["classes"]["R"]),
                       os.environ.get("TLON_LEXICON")))

            adapter = pathlib.Path(ADAPTER)
            if not (adapter / "adapter_model.safetensors").exists():
                # ⛔ FAIL HERE, NAMING THE PATH. Without the adapter this loads
                # the untuned base, which scored 0.0% on write — it would come
                # up healthy and answer in English, and the first person to
                # notice would be a stranger on the public URL.
                raise SpeakerError(
                    "no adapter weights at %s — the trained speaker is missing "
                    "and the untuned base scores 0.0%% write" % adapter)
            t0 = time.perf_counter()
            self._backend = BenchBackend(
                BASE_MODEL, adapter=str(adapter), device=DEVICE,
                load_4bit=FOUR_BIT, max_new_tokens=MAX_NEW_TOKENS,
                temperature=TEMPERATURE)
            self.load_seconds = time.perf_counter() - t0
        return self._backend

    # ── the turn ────────────────────────────────────────────────────────────

    def reply_to(self, provocation: str, provoke_pairs):
        """The Tlonian's answer to one already-rendered line.

        ⭐⭐ EXTRACTED FROM `turn`, WHICH NOW CALLS IT — not copied. This is the
        half of an exchange that can be RE-RUN without changing what the reader
        said: `provocation` is their own line already in Tlön and already shown
        to them, so regenerating from here is the only retry the product could
        honestly offer. A retry that re-rendered their line would be answering
        a different sentence than the one on their screen.

        ⛔ It exists because the onset baseline found the whole conversation is
        decided by turn 1: P(carry | previous carried) = 0.842 against 0.156 if
        it missed, and turn 1 has no context at all. Whether a missed turn 1 is
        DECODE VARIANCE or is determined by the provocation is the question a
        resample answers, and answering it needs exactly this seam.

        ⛔ The backend samples at temperature 0.7 with no per-call seed, so two
        calls here are independent draws. That is the mechanism a retry would
        rely on; it is not something this method arranges.
        """
        from tlon_converse import PROVOKE, generate

        backend = self.load()
        backend.conversation = _bench(PROVOKE, provoke_pairs)
        try:
            # ⭐ The bench's own framing, when it is turned on. Off by default:
            # it is a hypothesis under test, not yet a finding. See
            # `puzzle/bench_prompt.py` for what it overturns and why.
            return generate(backend, PROVOKE, provocation, [], shape=SHAPE,
                            system=bench_prompt.system_for(PROVOKE))
        finally:
            # ⛔ Clear it. A stale bench left on a process-wide object would be
            # handed to the NEXT reader's first turn — one person's
            # conversation conditioning a stranger's. In a `finally` because a
            # raising generate would otherwise leave it set.
            backend.conversation = []

    def turn(self, english: str, write_pairs, provoke_pairs) -> dict:
        """One exchange, ON A BENCH. Returns rows for the store and the page.

        ⛔⛔ THIS IS `tlon_converse.exchange` WITH THE WINDOW ADDED, AND IT IS
        SPELLED OUT HERE ONLY BECAUSE THE CONVERSATION DIFFERS BETWEEN THE TWO
        GENERATIONS. `exchange` makes both calls itself, so there is no seam to
        set `write` context before one and `provoke` context before the other.
        Everything that matters is still imported: the direction names, the
        system prompts behind them and `generate` — which carries the gate. No
        prompt is re-spelt here, which is the invariant that matters.

        ⛔ THE PROVOCATION IS THE SURFACE, NOT THE ENGLISH, and the reply is
        skipped entirely when the first step is refused: a provocation built
        from a line the gate would not accept is not a turn.

        ⛔ A REFUSAL IS AN OUTCOME, NOT AN ERROR, and it is returned in full.
        The gate proves `parse(render(scene)) == scene` against the frozen
        lexicon, so a refusal means the language would not hold what was said —
        which is the language working. Run 4 lost its largest result because 60
        of 61 failures were stored as `null` with the text dropped.
        """
        from tlon_converse import WRITE, generate

        backend = self.load()
        t0 = time.perf_counter()

        # ⭐ The window, trimmed to the time-out and rendered into the shape a
        # training row has — user payload bare, assistant turn a JSON scene.
        # ⛔⛔ CLEARED IN A `finally`, NOT AFTER THE REPLY. `reply_to` clears the
        # bench it sets, but a REFUSED write never reaches it — and that path
        # would leave the WRITE window on a process-wide object, to be handed
        # to the next reader's first turn. The leak only ever appears when a
        # turn is refused, which is the path least likely to be exercised.
        try:
            backend.conversation = _bench(WRITE, write_pairs)
            yours = generate(backend, WRITE, english, [], shape=SHAPE)
        finally:
            backend.conversation = []

        reply = self.reply_to(yours.surface, provoke_pairs) if yours.ok else None

        seconds = time.perf_counter() - t0
        return {"you": _row(yours, english=english),
                "tlon": _row(reply) if reply is not None else None,
                "seconds": round(seconds, 2),
                "shape": SHAPE,
                "context_turns": min(len(list(provoke_pairs)), CONTEXT_TURNS)}


def _bench(direction: str, pairs) -> list[tuple[str, str]]:
    """The window, trimmed and put in the trained shape.

    ⛔ A PAIR THAT WILL NOT RE-PARSE IS DROPPED, NOT RAISED. Every surface here
    came out of the gate so all of them should parse; if one somehow does not,
    losing that single exchange from the context is a far better outcome than
    failing the reader's turn over a line they cannot see and did not write.
    """
    out = []
    for user_payload, assistant_surface in list(pairs)[-CONTEXT_TURNS:]:
        try:
            out.append(trained_pair(direction, user_payload, assistant_surface))
        except (ParseError, KeyError, ValueError):
            continue
    return out


def _row(turn, *, english: str | None = None) -> dict:
    """One generation, flattened. ⛔ `surface` is None exactly when refused."""
    if turn is None:
        return {}
    ok = turn.ok
    return {
        "english": english,
        "surface": turn.surface if ok else None,
        # ⭐ Both renders are computed here, stored, and NOT sent to the browser
        # until the reader asks. See `server.py` — shipping them with the reply
        # would put the answer in the page source of a puzzle whose whole point
        # is that you have to choose to look.
        "gloss": gloss(turn.scene) if ok else None,
        "literary": literary(turn.scene) if ok else None,
        "let_go": list(turn.refused.objects) if ok and turn.refused else [],
        "refused": None if ok else (turn.error or "the gate would not pass it"),
        "seconds": round(turn.seconds, 2),
    }


# ── the translate button ────────────────────────────────────────────────────

def translate(surface: str) -> dict:
    """`gloss(parse(surface))` — pure, deterministic, no model, milliseconds.

    ⭐⭐ THIS IS WHY THE BUTTON IS FREE AND WHY IT IS HONEST. It is not a second
    model paraphrasing; it is the same frozen grammar and lexicon the speaker
    was trained and gated on, run backwards. Nothing here can hallucinate a
    meaning, and nothing here costs a GPU-second — so the ceiling in `guard.py`
    does not apply to it and a reader can translate every line they already have
    without spending anybody's turn.

    ⛔ TWO RENDERS, BOTH RETURNED, BECAUSE THEY ARE DIFFERENT PROMISES.
    `gloss` is the austere one and it is FROZEN — it is the project's
    measurement instrument, so it may never be prettied up. `literary` is the
    Borges-register English. Which one the button shows is a copy decision, and
    the page currently shows both.
    """
    try:
        scene = parse(surface)
    except ParseError as exc:
        # ⛔ Do not swallow this into an empty string. A surface that came out of
        # the gate must re-parse; if one ever does not, that is a real defect in
        # the round trip and it should be visible, not silently blank.
        raise SpeakerError("could not parse %r: %s" % (surface, exc)) from exc
    return {"gloss": gloss(scene), "literary": literary(scene)}


__all__ = ["Speaker", "SpeakerError", "translate", "MAX_ENGLISH_CHARS",
           "BASE_MODEL", "ADAPTER", "SHAPE", "FOUR_BIT", "TEMPERATURE",
           "MAX_NEW_TOKENS"]
