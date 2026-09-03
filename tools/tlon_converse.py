"""THE CONVERSANT — English in, Tlön back. The first thing that ever put the
fine-tune in front of a human.

    python tools/tlon_converse.py --adapter runs/act2/recipe_var/adapter_s20621 --4bit

⛔⛔ WHAT THIS IS TESTING, STATED AS THE THING THAT COULD KILL IT. The only
trained direction that REPLIES is `provoke`, and its prompt actively licenses
content-freedom: *"It need not be about what you were shown ... Only the force
carries across."* That clause is load-bearing and mutation-tested. So the
product question -- "it can hold a conversation" -- is not a plumbing question.
It is whether force-without-topic reads as a partner or as static. This tool
exists to answer that with a transcript, not an argument.

⭐ THE TURN IS TWO GENERATIONS, EACH UNDER A PROMPT THE MODEL WAS TRAINED ON:

    your English  --write-->  Scene -> gate -> YOUR line in Tlön
    your Tlön     --provoke-> Scene -> gate -> ITS reply in Tlön

Feeding English straight to `provoke` would be off-distribution: every provoke
row in the corpus is a bare Tlön surface (`act2_build_multiturn.py:54`).

⛔⛔ THE PROMPT SHAPES ARE IMPORTED FROM THE TRAINER, NEVER RE-SPELT. `SYSTEM`
comes from `act2_finetune`, which imports `PROVOCATION` from
`tlon.discourse.provocation`. Run 3 was trained on write/read and prompted at
arena time under a framing it had never seen, and 27/27 green said nothing
because no test crossed the boundary. One import, one string, no drift.

⛔⛔ AND THE DIVERGENCE THIS TOOL WAS WRITTEN TO EXPOSE. `provocation.py` fixed
the SYSTEM string and left the USER message alone. Every training row's user
message is a BARE string -- the English, or one Tlön surface, and nothing else
(`act2_finetune.row_messages`, `corpus.Pair.prompt`, `build_multiturn.rows_from`).
`LLMSpeaker.speak/render/choose` wrap all three in
`"The conversation so far:\\n ...\\n\\nSay the next thing."` So the arena has been
prompting under a user-message shape that was never a training shape -- the same
defect as run 3's, one level down from where it was fixed.

⭐ SO BOTH SHAPES ARE RUNNABLE HERE AND THE DIFFERENCE IS THE MEASUREMENT.
`--shape trained` (default) sends what the corpus contains. `--shape arena`
sends what `LLMSpeaker` sends. If they read the same, the divergence is
harmless and that is worth knowing. If they do not, the arena has been measuring
a prompt the model never saw.

⛔ A FAILED GENERATION IS KEPT IN FULL. Run 4 lost its largest result because
60 of 61 failures were ledgered as `proposal: null` with no text. Every refusal
here carries its raw generation into the log.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from act2_finetune import SYSTEM as TRAINED_SYSTEM              # noqa: E402
from tlon.act2 import schema_bridge as SB                       # noqa: E402
from tlon.act2.llm import BackendError, transcript_block        # noqa: E402
from tlon.discourse.provocation import DIRECTION as PROVOKE     # noqa: E402
from tlon.grammar.gloss import gloss                            # noqa: E402
from tlon.product import schema as PS                           # noqa: E402
#: The product's own door bound, imported rather than re-spelt.
from tlon.product.chat import MAX_ENGLISH_CHARS as PS_MAX       # noqa: E402
from tlon.product.literary import literary                      # noqa: E402
from tlon.product.schema import ProposalError                   # noqa: E402

WRITE = "write"

#: ⛔ The two user-message shapes, named so a transcript can say which it used.
TRAINED, ARENA = "trained", "arena"
SHAPES = (TRAINED, ARENA)

# ⛔⛔ THE IMPORT-TIME CONTRACT. If the trainer ever loses a direction this tool
# serves under, fail HERE -- not three hundred generations into a session whose
# transcript nobody can interpret afterwards.
for _d in (WRITE, PROVOKE):
    if _d not in TRAINED_SYSTEM:
        raise RuntimeError(
            "act2_finetune.SYSTEM has no %r direction, so this tool would be "
            "prompting under a framing the model was never trained on -- the "
            "exact defect tlon/discourse/provocation.py exists to prevent." % _d)


def user_message(direction: str, payload: str, history, *,
                 shape: str = TRAINED, history_limit: int = 60) -> str:
    """The user message, in one of the two shapes.

    ⛔⛔ `TRAINED` IS A BARE STRING AND THAT IS NOT AN OVERSIGHT. Every row in
    the corpus is `{"role": "user", "content": row["prompt"] or row["english"]}`
    where `prompt` is the English (write) or one Tlön surface (read, provoke).
    No preamble, no transcript, no instruction. Adding any is a new shape.

    ⭐ `ARENA` reproduces `LLMSpeaker` exactly, scaffolding and all, so the two
    can be read against each other in one session.
    """
    if shape not in SHAPES:
        # ⛔ RAISE, NEVER DEFAULT. An unrecognised shape silently taking the
        # trained branch would report an arena run as a trained one.
        raise ValueError("unknown shape %r; valid shapes are %s"
                         % (shape, ", ".join(SHAPES)))
    if shape == TRAINED:
        return payload
    block = transcript_block(history, history_limit)
    if direction == WRITE:
        return (f"The conversation so far:\n{block}"
                f"\n\nRender this into Tlön:\n\n{payload}")
    return f"The conversation so far:\n{block}\n\nSay the next thing."


class Turn:
    """One generation, gated. ⭐ Carries its own timing because throughput has
    never been measured -- `PREREG_KI_AS_TARGET` §: "Inference throughput is
    unknown", and the log has been lost to kill-first sequences three times."""

    __slots__ = ("direction", "shape", "surface", "scene", "refused",
                 "seconds", "raw", "error", "sent")

    def __init__(self, direction, shape, *, surface=None, scene=None,
                 refused=None, seconds=0.0, raw=None, error=None, sent=None):
        self.direction, self.shape = direction, shape
        self.surface, self.scene, self.refused = surface, scene, refused
        self.seconds, self.raw, self.error, self.sent = seconds, raw, error, sent

    @property
    def ok(self) -> bool:
        return self.surface is not None

    def as_row(self) -> dict:
        return {"direction": self.direction, "shape": self.shape,
                "sent": self.sent, "surface": self.surface,
                "gloss": gloss(self.scene) if self.scene else None,
                "literary": literary(self.scene) if self.scene else None,
                "refused_objects": list(self.refused.objects) if self.refused else [],
                "note": self.refused.note if self.refused else "",
                "seconds": round(self.seconds, 3),
                "error": self.error,
                # ⛔ FULL, never clipped. A failure is the most information-dense
                # event in a run; run 4's speak collapse was undiagnosable
                # because the raw text was dropped at exactly this point.
                "raw": self.raw}


def generate(backend, direction: str, payload: str, history, *,
             shape: str = TRAINED, history_limit: int = 60) -> Turn:
    """One direction, one generation, through the product's own gate.

    ⛔ The gate is `PS.validate`, which proves `parse(render(scene)) == scene`
    against the frozen lexicon. Nothing here renders; validation does. So no
    generation, however adversarial the English that provoked it, can put an
    illegal utterance on screen.
    """
    sent = user_message(direction, payload, history, shape=shape,
                        history_limit=history_limit)
    t0 = time.perf_counter()
    try:
        proposal = backend.call(system=TRAINED_SYSTEM[direction], user=sent,
                                schema=SB.scene_schema(), kind=direction)
    except BackendError as exc:
        return Turn(direction, shape, seconds=time.perf_counter() - t0,
                    raw=exc.raw, error=str(exc), sent=sent)
    dt = time.perf_counter() - t0
    try:
        scene, surface, refused = PS.validate(proposal)
    except ProposalError as exc:
        return Turn(direction, shape, seconds=dt,
                    raw=json.dumps(proposal, ensure_ascii=False),
                    error="gate refused: %s" % exc, sent=sent)
    return Turn(direction, shape, surface=surface, scene=scene, refused=refused,
                seconds=dt, sent=sent)


def exchange(backend, english: str, history, *, shape: str = TRAINED,
             history_limit: int = 60) -> tuple[Turn, Turn | None]:
    """The full turn: your English into Tlön, then that Tlön provokes a reply.

    ⛔⛔ THE PROVOCATION IS THE SURFACE, NOT THE ENGLISH. Under `TRAINED` the
    payload handed to `provoke` is one bare Tlön surface -- byte-for-byte the
    shape of `prev.surface` in every provoke row of the corpus. Handing it the
    English instead would be a direction the model has never served under.

    ⭐ Returns `(yours, reply)`. `reply` is None when the first step was refused:
    a provocation built from a line the gate would not accept is not a turn, and
    inventing one would put the model in front of input the corpus never had.
    """
    yours = generate(backend, WRITE, english, history, shape=shape,
                     history_limit=history_limit)
    if not yours.ok:
        return yours, None
    reply = generate(backend, PROVOKE, yours.surface, history + [yours.surface],
                     shape=shape, history_limit=history_limit)
    return yours, reply


# ── display ─────────────────────────────────────────────────────────────────

BANNER = """\
────────────────────────────────────────────────────────────────────────
  TLÖN — the southern hemisphere is awake. Say anything, in English.
  It has no nouns, no word for a self and none for you. It will not
  answer what you said; it is provoked by it, and paints its own scene.
    /shape     switch between the trained and arena prompt shapes
    /time      per-generation wall clock so far
    /quit
────────────────────────────────────────────────────────────────────────"""


def show(yours: Turn, reply: Turn | None) -> None:
    print()
    print("  you said")
    if yours.ok:
        print("    in tlön     %s" % yours.surface)
        print("    gloss       %s" % gloss(yours.scene))
        if yours.refused and yours.refused.objects:
            print("    it let go   %s" % " · ".join(yours.refused.objects))
    else:
        # ⛔ A refusal is the language working, not an error. It is displayed as
        # an outcome, with the reason, never swallowed into a retry.
        print("    ⛔ it could not hold that — %s" % yours.error)
    if reply is None:
        print()
        return
    print()
    print("  it answered")
    if reply.ok:
        print("    in tlön     %s" % reply.surface)
        print("    gloss       %s" % gloss(reply.scene))
        print("    in english  %s" % literary(reply.scene))
    else:
        print("    ⛔ refused — %s" % reply.error)
    print()


def timings(turns) -> str:
    done = [t for t in turns if t.seconds > 0]
    if not done:
        return "  nothing generated yet"
    secs = sorted(t.seconds for t in done)
    mid = secs[len(secs) // 2]
    ok = sum(1 for t in turns if t.ok)
    by: dict[str, list[float]] = {}
    for t in done:
        by.setdefault(t.direction, []).append(t.seconds)
    lines = ["  %d generations · %d gated clean (%.0f%%)"
             % (len(turns), ok, 100.0 * ok / len(turns)),
             "  median %.2fs · min %.2fs · max %.2fs" % (mid, secs[0], secs[-1])]
    for d, xs in sorted(by.items()):
        lines.append("    %-8s n=%-3d mean %.2fs" % (d, len(xs), sum(xs) / len(xs)))
    return "\n".join(lines)


# ── the door ────────────────────────────────────────────────────────────────

#: ⛔ Legal scenes for `--offline`. They exercise the gate, the display and the
#: log for $0.00 — they say nothing about whether the model can converse.
_OFFLINE = [
    {"node": {"root": "klung", "orient": ["nar"], "aspect_root": "tes",
              "aspect_reps": 2,
              "edges": [{"relator": "sen", "node": {"root": "lan"}}]},
     "force": "ka"},
    {"node": {"root": "flux"}, "force": "ki"},
    {"node": {"root": "fang", "orient": ["hul"]}, "force": "ko"},
]


def build_backend(a):
    if a.offline:
        from tlon.act2.llm import ScriptedBackend
        print("  ⛔ OFFLINE — scripted scenes. This exercises the gate, the "
              "display and the log.\n     It cannot tell you anything about "
              "whether the model can hold a conversation.")
        return ScriptedBackend(_OFFLINE * 40, name="offline")
    from act2_backends import LocalBackend
    print("  loading %s%s ..." % (a.model, " + " + a.adapter if a.adapter else ""))
    t0 = time.perf_counter()
    b = LocalBackend(a.model, adapter=a.adapter, device=a.device,
                     load_4bit=a.four_bit, max_new_tokens=a.max_new_tokens,
                     temperature=a.temperature)
    print("  ready in %.1fs" % (time.perf_counter() - t0))
    return b


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--offline", action="store_true",
                    help="scripted scenes, $0.00, no GPU — exercises the gate, "
                         "the display and the log, and proves nothing about "
                         "the model")
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--adapter", default=None,
                    help="LoRA directory; without it you are talking to the "
                         "untuned base, which scored 0.0% write")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--4bit", dest="four_bit", action="store_true",
                    help="NF4. ⛔ Changes the model — every measured number in "
                         "this project is bf16, so a 4-bit reading is "
                         "indicative, not comparable.")
    ap.add_argument("--temperature", type=float, default=0.7,
                    help="arena default. ⚠️ falsify.MIN_ARENA_TEMPERATURE is "
                         "flagged MEASURED=False — it came from taste.")
    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--shape", choices=SHAPES, default=TRAINED)
    ap.add_argument("--history-limit", type=int, default=60,
                    help="arena shape only; the trained shape is depth-1 by "
                         "construction and ignores it")
    ap.add_argument("--say", action="append", default=[],
                    help="one line, non-interactive (repeatable)")
    ap.add_argument("--log", default="runs/converse")
    args = ap.parse_args()

    backend = build_backend(args)
    shape = args.shape
    history: list[str] = []
    turns: list[Turn] = []

    out = pathlib.Path(args.log)
    out.mkdir(parents=True, exist_ok=True)
    path = out / ("session_%s.jsonl" % time.strftime("%Y%m%d_%H%M%S"))
    fh = path.open("w", encoding="utf-8")
    fh.write(json.dumps({"kind": "header", "model": args.model,
                         "adapter": args.adapter, "four_bit": args.four_bit,
                         "temperature": args.temperature, "shape": shape,
                         "max_new_tokens": args.max_new_tokens}) + "\n")
    fh.flush()

    def turn(english: str) -> None:
        nonlocal shape
        yours, reply = exchange(backend, english, history, shape=shape,
                                history_limit=args.history_limit)
        turns.append(yours)
        if reply is not None:
            turns.append(reply)
        show(yours, reply)
        # ⭐ The bot's own line enters the history; yours does too, so the arena
        # shape sees the alternation. Under the trained shape only the single
        # provoking surface is ever sent, so this list is a record, not a prompt.
        if yours.ok:
            history.append(yours.surface)
        if reply is not None and reply.ok:
            history.append(reply.surface)
        fh.write(json.dumps({"kind": "turn", "english": english,
                             "yours": yours.as_row(),
                             "reply": reply.as_row() if reply else None},
                            ensure_ascii=False) + "\n")
        fh.flush()

    if args.say:
        for line in args.say:
            print("\n> %s" % line)
            turn(line)
        print(timings(turns))
        print("\n  transcript: %s" % path)
        fh.close()
        return 0

    print(BANNER)
    print("  shape=%s · adapter=%s\n" % (shape, args.adapter or "NONE (base)"))
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in ("/quit", "/q"):
            break
        if line == "/time":
            print(timings(turns))
            continue
        if line == "/shape":
            shape = ARENA if shape == TRAINED else TRAINED
            print("  shape=%s" % shape)
            continue
        if len(line) > PS_MAX:
            # ⛔ REFUSED, NEVER TRUNCATED. A clipped input logged beside a Scene
            # that was never a rendering of the whole of it is a row that
            # validates and lies.
            print("  ⛔ %d chars; the door takes %d." % (len(line), PS_MAX))
            continue
        turn(line)

    print(timings(turns))
    print("\n  transcript: %s" % path)
    fh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
