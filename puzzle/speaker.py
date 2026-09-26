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
import random
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
from tlon.grammar import classes as C                       # noqa: E402
from tlon.grammar.parse import ParseError, parse            # noqa: E402
from tlon.product.chat import MAX_ENGLISH_CHARS             # noqa: E402
from tlon.product.literary import literary                  # noqa: E402

from . import bench_prompt                                  # noqa: E402
from . import router                                        # noqa: E402

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

#: ⭐⭐ A PRODUCT DIAL, OFF BY DEFAULT, AND THE RESEARCH TRACK NEVER READS IT.
#:
#: The served speaker answers with `ka` almost always — not a serving fault and
#: not quantisation, but a faithful reproduction of what it was trained on:
#: in `corpus_bench_dosed`, its own corpus, the Tlönian's reply force is
#: **ka 99.7%**, and the conversation pools it was built from are 99.7% / 99.8%
#: ka in voice T. The model is doing exactly what it saw.
#:
#: ⛔⛔ SO THIS DOES NOT FIX ANYTHING — IT DRESSES A SYMPTOM, and it is named
#: that way on purpose. The real repair is a corpus where the Tlönian asks,
#: wonders, urges and denies IN CONTENT rather than in its last particle, and
#: that is a retrain, not a flag. A reply whose force was redrawn here says
#: something its own scene was not painted to say.
#:
#: ⛔ Every number this project has published about force fidelity was measured
#: with this OFF. Any reading taken with it on is a reading of the dial.
FORCE_TABLE = os.environ.get("TLON_FORCE_TABLE", "0") not in (
    "0", "", "false", "no")

#: How much of a non-`ki` row goes to ASK. The other four forces share what is
#: left, evenly. ⛔ Proposed at 0.35, not measured — R4 is what would justify
#: any value at all.
KI_WEIGHT = float(os.environ.get("TLON_KI_WEIGHT", "0.35"))

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

#: ⛔⛔ EXTRA REPLIES THE **FIRST** EXCHANGE MAY DRAW WHEN THE FIRST DOES NOT
#: CARRY. Three, and only on the first exchange. Both halves are measured.
#:
#: ⭐ WHY IT EXISTS. The onset baseline (n=192, depths 0-3) found the whole
#: conversation is settled by its first exchange: P(carry | previous turn
#: carried) = 0.842 against 0.156 if it missed, and turn 1 has no context at
#: all. So the three-turn reach is p1 + (1-p1)*0.3325, and raising p1 is the
#: entire lever. The reseed run (n=188, k=3, provocation held FIXED) measured
#: what a retry buys: **48.9% of missed first replies carry within three more
#: draws**, taking p1 from 0.511 to 0.750 and the three-turn joint from 0.673
#: to 0.833.
#:
#: ⛔ THREE IS THE CEILING, NOT A DIAL. 47 of those 188 provocations (25.0%)
#: never carried in four tries, and 141/188 is exactly 0.750 — k=3 already
#: extracts essentially everything resampling can give. Raising it buys almost
#: nothing and costs latency on the turns that are already hopeless. That floor
#: is a property of the language, not of the weights: inside the STEERED
#: corpus, where carry was forced, those roots still only carried 33.4%.
#:
#: ⛔⛔ FIRST EXCHANGE ONLY, AND THAT IS A PRODUCT DECISION. Resampling for
#: carry on EVERY turn is rejection sampling toward repetition — the
#: "repetitive collapse" `tlon/act2/carry.py` names as the reason the predicate
#: is a BAND rather than a maximum. The puzzle needs ONE foothold a reader can
#: notice, not a parrot. It is also the only case measured.
CARRY_RETRIES = int(os.environ.get("TLON_CARRY_RETRIES", "3"))

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

    def speak_from(self, surface: str, provoke_pairs, *, english: str) -> dict:
        """One exchange whose FIRST HALF NEEDS NO MODEL.

        ⭐⭐ The reader already wrote Tlön — a pasted surface, or a bare force
        word aimed at the Tlönian's last line and re-rendered by
        `router.refocus`. There is nothing for the write step to render, and
        asking it to would be the bug: its training English contains the token
        `ka` in 0 of 12,680 rows, so a Tlön-shaped input is the one thing it
        cannot read.

        ⛔ The reader's bubble still shows what they TYPED. `english` is
        carried through untouched; `surface` is the provocation.
        """
        scene = parse(surface)          # raises if the caller passed a non-surface
        backend_t0 = time.perf_counter()
        reply = self.reply_to(surface, list(provoke_pairs))
        was, sent = apply_force_dial(reply, surface)
        seconds = time.perf_counter() - backend_t0
        return {
            "you": {"english": english, "surface": surface,
                    "gloss": gloss(scene), "literary": literary(scene),
                    # ⭐ Nothing was let go: the reader wrote in Tlön, so no
                    # object had to be refused out of an English sentence.
                    "let_go": [], "refused": None, "seconds": 0.0},
            "tlon": _row(reply) if reply is not None else None,
            "seconds": round(seconds, 2),
            "shape": SHAPE,
            # ⭐ Recorded on EVERY turn, dial on or off, so a later comparison
            # does not depend on the flag having been set when the row was
            # written.
            "force_model": was,
            "force_sent": sent,
            "replies_drawn": 1,
            "context_turns": min(len(list(provoke_pairs)), CONTEXT_TURNS),
        }

    def turn(self, english: str, write_pairs, provoke_pairs,
             force: str | None = None) -> dict:
        """One exchange, ON A BENCH. Returns rows for the store and the page.

        ⭐ `force` stamps the reader's own speech act onto their rendered line —
        the route for English with a force word hung off the end. It is the same
        mechanism the write model already learned for `?`→`ki` (98.8% of 744
        rows), applied where no tag exists for it.

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
        # ⛔ MATERIALISED ONCE. It is read three times below (the bench, the
        # first-exchange test, the recorded depth); a generator would be empty
        # after the first and the turn would silently lose its window.
        provoke_pairs = list(provoke_pairs)

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

        # ⭐ The reader's speech act, stamped on their own rendered line.
        # ⛔ AFTER THE GATE, NEVER INSTEAD OF IT. `refocus` re-parses what it
        # renders and compares it to the scene it built, so a force override
        # cannot smuggle through a surface the gate would have refused. If the
        # write step was refused there is nothing to stamp and nothing to fix.
        if force is not None and yours.ok:
            moved = router.refocus(yours.surface, force)
            yours.surface = moved
            # ⛔ The SCENE moves too. `_row` glosses from `turn.scene`, so
            # leaving it behind would put a reply on screen whose translation
            # disagreed with its own last word.
            yours.scene = parse(moved)

        # ⭐ THE FIRST EXCHANGE MAY DRAW AGAIN IF IT DOES NOT CARRY. See
        # `CARRY_RETRIES` for the measurement this rests on. `provoke_pairs`
        # being empty IS "this is the reader's first message" — the same test
        # the window uses, so the two cannot disagree.
        reply, drawn = None, 0
        if yours.ok:
            budget = 1 + (CARRY_RETRIES if not provoke_pairs else 0)
            candidates = []
            for _ in range(budget):
                candidates.append(self.reply_to(yours.surface, provoke_pairs))
                drawn += 1
                # ⛔ STOP AT THE FIRST CARRY. The retry only ever fires on a
                # miss, so a reader whose first reply already carries waits no
                # longer than before.
                if carries(yours.surface, candidates[-1]):
                    break
            # ⛔ AFTER `pick_reply`, NEVER BEFORE. Selecting among candidates
            # whose forces had already been redrawn would let the dial steer
            # which reply is served, not just how it ends.
            reply = pick_reply(candidates, yours.surface)
        was, sent = apply_force_dial(reply, yours.surface if yours.ok else "")

        seconds = time.perf_counter() - t0
        return {"you": _row(yours, english=english),
                "tlon": _row(reply) if reply is not None else None,
                "seconds": round(seconds, 2),
                "shape": SHAPE,
                "force_model": was,
                "force_sent": sent,
                # ⭐ Recorded so the bench can show what the retry actually
                # cost in production rather than what it cost in a probe.
                "replies_drawn": drawn,
                "context_turns": min(len(provoke_pairs), CONTEXT_TURNS)}


def carries(provocation: str, turn) -> bool:
    """Does this reply take up a happening the provocation offered?

    ⛔ THE BAND, NOT BARE OVERLAP — `scene_carry` demands a root carried AND a
    root new. Retrying on bare overlap would select for the echo the band was
    written to refuse, and a parrot scores 100% on overlap and 0% on the band.

    ⛔ The prior's roots come from SPLITTING THE SURFACE, which is what
    `act2_model_carry.score` does; the reply's come from walking its scene
    tree. Keeping both exactly as the probes compute them is what makes the
    served behaviour the measured behaviour.

    ⛔⛔ `parsed_roots`, NOT `scene_roots`. `generate` returns `.scene` as a
    `Scene` DATACLASS (`aspect` is a pair, `edges` are pairs), not the proposer
    dict (`aspect_root`, `edges:[{relator,node}]`). `scene_roots` reads the
    proposer shape and RAISES on this one — so this function would have thrown
    on every reader's first turn. It is the same two-shapes trap that made the
    onset probe report 0.0% carry, and it reached the SERVING path this time.
    """
    from tlon.act2.carry import parsed_roots, scene_carry
    from tlon.grammar import classes as C

    if turn is None or not getattr(turn, "ok", False):
        return False
    roots = frozenset(C.load()["classes"]["R"])
    prior = frozenset(w for w in (provocation or "").split() if w in roots)
    if not prior:
        # ⛔ Nothing to carry FROM. Retrying would burn the budget on a turn no
        # reply could satisfy, and every draw would be scored a failure.
        return True
    return scene_carry(prior, parsed_roots(turn.scene, roots)).ok


#: ⛔ Its own stream. Sharing the module `random` would let a draw here shift
#: every other sampler in the process, and the dial must not be able to move a
#: number it is not supposed to touch.
_force_rng = random.Random()


def force_weights(prior: str, *, ki_weight: float = None) -> dict[str, float]:
    """The reply-force distribution for a provocation carrying `prior`.

    ⛔⛔ `ki` → `ka` STAYS FIXED. It is the single cell in the whole force map
    that survived the mutation test — the only structure the corpus actually
    carries — and an ask is answered with an assert. A dial that reweighted it
    would be overwriting the one derived thing in the language with a product
    preference.
    """
    lex = sorted(C.load()["classes"]["F"])
    if prior == "ki":
        return {f: (1.0 if f == "ka" else 0.0) for f in lex}
    w = KI_WEIGHT if ki_weight is None else ki_weight
    rest = (1.0 - w) / (len(lex) - 1)
    return {f: (w if f == "ki" else rest) for f in lex}


def draw_force(prior: str, *, rng=None, ki_weight: float = None) -> str:
    """One force, drawn from `force_weights(prior)`."""
    weights = force_weights(prior, ki_weight=ki_weight)
    forms = sorted(weights)
    r = (rng or _force_rng)
    return r.choices(forms, weights=[weights[f] for f in forms])[0]


def restamp(turn, force: str):
    """Put `force` on an already-gated turn, surface and scene together.

    ⛔ THE SCENE MOVES TOO. `_row` glosses from `turn.scene`, so changing only
    the surface would put a reply on screen whose translation disagreed with
    its own last word. `router.refocus` re-parses what it renders, so this
    cannot introduce a surface the gate would have refused.
    """
    moved = router.refocus(turn.surface, force)
    turn.surface = moved
    turn.scene = parse(moved)
    return turn


def apply_force_dial(reply, provocation: str) -> tuple[str | None, str | None]:
    """-> (the model's own force, the force actually served).

    ⭐ BOTH ARE RETURNED EVEN WHEN THE DIAL IS OFF, so the log records what the
    model said in every case and a later comparison does not depend on the flag
    having been on when the row was written.
    """
    if reply is None or not getattr(reply, "ok", False):
        return None, None
    was = reply.scene.force
    if not FORCE_TABLE:
        return was, was
    try:
        prior = parse(provocation).force
    except Exception:                                          # noqa: BLE001
        return was, was
    drawn = draw_force(prior)
    if drawn == was:
        return was, was
    try:
        restamp(reply, drawn)
    except router.RouterError:
        # ⛔ A dial that cannot re-render leaves the reply EXACTLY as the model
        # made it. It must never be able to turn a good turn into a refusal.
        return was, was
    return was, drawn


def pick_reply(candidates, provocation: str):
    """The reply to serve, given every draw that was taken.

    ⛔⛔ A RETRY MUST NEVER MAKE A TURN WORSE THAN NOT RETRYING. Preference is
    (1) the first candidate that CARRIES, (2) failing that the first USABLE
    one, (3) failing that the LAST one — because a refusal carries the text
    explaining itself and `_row` reports it, and returning None instead would
    turn a stated refusal into a blank.
    """
    usable = [c for c in candidates if c is not None and getattr(c, "ok", False)]
    for c in usable:
        if carries(provocation, c):
            return c
    if usable:
        return usable[0]
    return candidates[-1] if candidates else None


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
