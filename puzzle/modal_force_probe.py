"""⛔⛔ THE SAMPLED FORCE READ, ON THE PRODUCT'S OWN SPEAKER — NOT PUBLIC.

Why this file exists rather than a number from the retrain box:

  1. `LocalBackend` defaults to `temperature 0.0` — `do_sample=False`, ARGMAX.
     `f_local` reported "force ka 100% (64/64)" for an adapter whose corpus was
     measured at 52.6% `ka`, and the 100% was the decoder. A greedy probe
     cannot see a distribution; it reports the mode.

  2. Even a SAMPLED `act2_model_carry` would answer a different question. It
     goes through `LLMSpeaker.speak()`; the bench goes through
     `puzzle/speaker.py` and `bench_prompt.py`. Different prompt, different
     task shape. The product question is what the BENCH emits.

  3. And temperature 0.7 is below 1.0, so it SHARPENS. A model perfectly
     calibrated to a 52.6% `ka` corpus will still emit more than 52.6% `ka`
     when served. The corpus number is not a prediction of the served number,
     which is exactly why this has to be measured rather than reasoned about.

So this runs the served class — `puzzle.speaker.Speaker` — at the served
temperature, with the served prompts, and counts what comes out.

⛔⛔ IT IS NOT THE PUBLIC APP AND MUST NEVER BECOME IT.
  * a DIFFERENT app name, so `modal deploy` of the real bench is untouched;
  * NO `@modal.asgi_app`, no FastAPI, no web endpoint, no URL to find;
  * NO Turnstile secret, because there is nothing public to protect;
  * NO bench-db volume, so no reader's conversation is anywhere near this.
The weights volume IS shared, read-only in effect: it is the HF cache holding
the 14 GB base model, and re-downloading it to save a mount would cost more
than this whole measurement.

    modal run puzzle/modal_force_probe.py --n 96 --retries 0
    modal run puzzle/modal_force_probe.py --n 96 --retries 0 --cell dosed-s20624

⛔ `--cell` is restricted to the adapters `CELLS` mounts into the image. A cell
that is not mounted would fall back to the env default — loading one adapter
and labelling the result with another — so it is refused, and the adapter that
actually loaded is asserted against the label before any generation.
"""
from __future__ import annotations

import pathlib

import modal

REPO = pathlib.Path(__file__).resolve().parents[1]

#: ⛔ NOT "tlon-bench". A shared name would redeploy the public bench from a
#: file that has no Turnstile, no rate limiter and no logbook.
app = modal.App("tlon-force-probe")

weights = modal.Volume.from_name("tlon-weights", create_if_missing=True)

#: ⛔⛔ BOTH ADAPTERS ARE MOUNTED AND THE CELL IS A RUNTIME ARGUMENT, because a
#: reading of ONE model cannot say whether this probe can see a difference at
#: all. v2 read `ka` 100% at temperature 0.7 with the carry filter off. If v1 —
#: whose corpus is 99.7% `ka` — reads the same 100%, then the probe is blind on
#: this axis and certifies nothing about either model. A negative result is not
#: evidence until the instrument has been seen to move.
CELLS = ("force-s20624", "dosed-s20624")
CELL = CELLS[0]

image = (
    modal.Image.debian_slim(python_version="3.12")
    # ⛔ torch FIRST and alone, from the CUDA index — same reasoning as
    # `modal_app.py`: a later resolver drags in a wheel built against the wrong
    # runtime and every generate() fails at import depth.
    .pip_install("torch==2.8.0",
                 index_url="https://download.pytorch.org/whl/cu128")
    .pip_install(
        "transformers==5.8.1",
        "peft==0.19.1",
        "bitsandbytes==0.50.1",
        "accelerate==1.13.0",
        "safetensors>=0.4",
        "huggingface_hub>=0.34",
        "fastapi==0.136.1",
        "pydantic>=2.7",
        "PyYAML>=6.0",
    )
    # ⛔⛔ `.env()` BEFORE every `add_local_*` — Modal refuses a build step after
    # a local-file step, and `.env()` is a build step.
    .env({
        # ⛔⛔ THE LANGUAGE THIS ADAPTER SPEAKS. Without it the default is the
        # FROZEN 156-root lexicon and the gate refuses half the speaker's own
        # training corpus — failing CLOSED, so the container looks healthy and
        # merely seems inarticulate. `speaker.py` refuses on a hash mismatch.
        "TLON_LEXICON": "lexicon_expanded.yaml",
        # ⛔ A default only. `probe()` overrides it per cell BEFORE importing
        # `puzzle.speaker`, which reads ADAPTER at module scope.
        "TLON_ADAPTER": "/app/speaker/%s" % CELL,
        "HF_HOME": "/weights/hf",
        # ⛔ The served value, stated rather than inherited, because the whole
        # measurement is about this number.
        "TLON_TEMPERATURE": "0.7",
        "PYTHONUNBUFFERED": "1",
    })
    # ⛔ The same three trees the Dockerfile copies: `puzzle/speaker.py` imports
    # the turn shape and the backend from `tools/`, and that import is the
    # guarantee that the prompts measured here are the prompts served.
    .add_local_dir(REPO / "tlon", remote_path="/app/tlon")
    .add_local_dir(REPO / "tools", remote_path="/app/tools")
    .add_local_dir(REPO / "puzzle", remote_path="/app/puzzle")
    .add_local_dir(REPO / "runs" / "puzzle_speaker" / CELLS[0],
                   remote_path="/app/speaker/%s" % CELLS[0])
    .add_local_dir(REPO / "runs" / "puzzle_speaker" / CELLS[1],
                   remote_path="/app/speaker/%s" % CELLS[1])
)

#: Ordinary English, the register the bench actually receives. ⛔ NOT Tlön and
#: not cherry-picked to invite a question: a prompt set chosen to elicit `ki`
#: would measure the prompt set.
PROVOCATIONS = [
    "I sat on a bench by the river.",
    "The light was going.",
    "My coffee went cold while I was reading.",
    "It rained all afternoon and then stopped.",
    "I waited for a bus that never came.",
    "The room got quiet after everyone left.",
    "I dropped my keys in the snow.",
    "Someone was practising piano upstairs.",
    "The bread didn't rise.",
    "I walked home the long way.",
    "A dog barked twice and stopped.",
    "The window fogged over.",
    "I forgot what I came into the room for.",
    "The ice cracked when I stepped on it.",
    "My hands were shaking from the cold.",
    "The train was late again.",
]


@app.function(image=image, gpu="A10", volumes={"/weights": weights},
              timeout=3600)
def probe(n: int = 128, retries: int = 3, cell: str = CELLS[0],
          four_bit: bool = True, mode: str = "english",
          dial: bool = False, legacy_split: bool = False,
          ki_weight: float = 0.35,
          hub_offline: bool = False,
          base_override: str = "") -> dict:
    """Run `n` first-exchange turns and tally the force the model chose.

    ⛔⛔ `retries` IS THE WHOLE EXPERIMENT, NOT A SETTING. On a first exchange
    `Speaker.turn` draws `1 + CARRY_RETRIES` replies, stops at the first that
    CARRIES, and `pick_reply` then prefers a carrier. That is selection on an
    outcome, and it sits between the model and the page:

      retries=0  → one draw, no selection. THE MODEL'S OWN DISTRIBUTION.
      retries=3  → what the bench actually serves today.

    The first reading of this probe was taken at the default 3 and reported
    `ka` 16 of 16. That number is about the filter at least as much as about
    the speaker, and the two arms are the only way to tell them apart.
    """
    import collections
    import os
    import sys
    import time

    sys.path.insert(0, "/app")
    os.chdir("/app")
    # ⛔⛔ BEFORE THE IMPORT. `CARRY_RETRIES` is read at module scope, so
    # setting this afterwards is a silent no-op — the same shape as the unit
    # test in this repo that patched an attribute the code never reads and
    # tried to spend $1.99/hr because the patch did nothing.
    os.environ["TLON_CARRY_RETRIES"] = str(retries)
    # ⛔ Same window, same reason: `speaker.ADAPTER` is module scope.
    if cell not in CELLS:
        raise SystemExit("⛔ unknown cell %r — only %s are mounted in this "
                         "image, and a cell that is not mounted would silently "
                         "fall back to the default" % (cell, list(CELLS)))
    os.environ["TLON_ADAPTER"] = "/app/speaker/%s" % cell
    # ⛔⛔ THE BENCH SERVES NF4 AND THE CAMPAIGN MEASURES bf16.
    # `speaker.py` says so itself: "4-BIT CHANGES THE MODEL ... if
    # anyone ever reads a number off this app, that number is
    # indicative and not comparable to the campaign's." Every force
    # reading here is off the app, so the quantisation is an ARM.
    os.environ["TLON_4BIT"] = "1" if four_bit else "0"
    # ⛔⛔ SET AT RUNTIME, NOT IN THE IMAGE, AND THAT IS THE WHOLE POINT. Putting
    # a flag in `.env()` rebuilds the image, so the first arm pays a fresh pull
    # and the second does not — two things differ and the pull does the work.
    # That confound is exactly how a GPU-snapshot "62.7s -> 10.8s" got deployed
    # to the live bench and made it SLOWER (22s -> 52s). Here both arms run on
    # one cached image and only this line moves.
    # ⭐ THE PRE-QUANTISED CHECKPOINT, THROUGH THE SHIPPED PATH. The raw
    # transformers comparison proved the WEIGHTS are identical (4/4 greedy);
    # this proves `puzzle.speaker` -> `LocalBackend` can actually load them.
    # ⛔ `TLON_4BIT=0` is REQUIRED with it: the checkpoint already carries its
    # `quantization_config`, and asking bitsandbytes to quantise an
    # already-quantised model is a different operation, not a no-op.
    if base_override:
        os.environ["TLON_BASE"] = base_override
        os.environ["TLON_4BIT"] = "0"
        # ⛔⛔ AND THE ARM LABEL MOVES WITH IT. `four_bit` describes whether
        # bitsandbytes quantises AT LOAD; a pre-quantised checkpoint means it
        # does not, so leaving the flag True would make the assert below fail
        # on a disagreement that is really just a stale label — which is
        # exactly what it did the first time this ran. The guard was right and
        # the caller was wrong.
        four_bit = False
    if hub_offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
    else:
        os.environ.pop("HF_HUB_OFFLINE", None)
        os.environ.pop("TRANSFORMERS_OFFLINE", None)
    # ⛔⛔ THE DIAL IS APPLIED BY `turn()` AND `speak_from()`, NOT BY
    # `reply_to()`. So a dial reading MUST run in `english` mode — which is
    # also the only honest place to take it, because that is the path a reader
    # is actually on. A dial arm in `tlon` mode would silently measure the
    # undialled model and label it "dial on".
    if dial and mode != "english":
        raise SystemExit("⛔⛔ the dial only applies on the `english` path "
                         "(turn/speak_from); mode=%r would report the "
                         "UNDIALLED model as dialled" % mode)
    os.environ["TLON_FORCE_TABLE"] = "1" if dial else "0"
    # ⛔⛔ ONLY WHEN THE LEGACY ARM IS ASKED FOR. `speaker._KI_WEIGHT_EXPLICIT`
    # keys on the variable's PRESENCE, so setting it to its own default selects
    # the old even-split table — which is exactly what this line used to do
    # unconditionally, defeating the corpus table it was run to verify.
    os.environ.pop("TLON_KI_WEIGHT", None)
    if legacy_split:
        os.environ["TLON_KI_WEIGHT"] = str(ki_weight)

    from tlon.grammar import classes as C
    from tlon.grammar.parse import parse

    lex = C.load()
    print("lexicon %s · %d roots" % (lex["_hash"], len(lex["classes"]["R"])),
          flush=True)
    # ⛔⛔ REFUSE, DO NOT REPORT. A force table measured against a different
    # language than the adapter speaks is not a result, and the failure is
    # silent: the gate just refuses more turns.
    if lex["_hash"] != "08c03b0a81330e4ba42883fa8b08c873":
        raise SystemExit("⛔⛔ WRONG LEXICON %s — refusing" % lex["_hash"])

    from puzzle import speaker as SP
    # ⛔ ASSERTED, NOT ASSUMED. If the export above missed its window this
    # reads 3 while the result is labelled 0, and the two arms become one arm
    # reported twice.
    if SP.CARRY_RETRIES != retries:
        raise SystemExit("⛔⛔ CARRY_RETRIES is %d, asked for %d — the env was "
                         "set too late to matter" % (SP.CARRY_RETRIES, retries))
    if SP.FOUR_BIT != four_bit:
        raise SystemExit("⛔⛔ FOUR_BIT is %s, asked for %s — the env "
                         "was set too late" % (SP.FOUR_BIT, four_bit))
    print("quant     %s" % ("NF4 4-bit (as served)" if four_bit
                            else "bf16 (as the campaign measures)"),
          flush=True)
    print("retries   %d  (%s)" % (SP.CARRY_RETRIES,
                                  "the model's own draw, unselected"
                                  if not retries else
                                  "carry-selected, as the bench serves"),
          flush=True)
    if not SP.ADAPTER.endswith(cell):
        raise SystemExit("⛔⛔ loaded adapter %s is not the cell %r "
                         "that this result would be labelled with"
                         % (SP.ADAPTER, cell))
    print("adapter   %s  ✅ matches cell %s" % (SP.ADAPTER, cell),
          flush=True)
    print("temp      %.2f   shape %s   context_turns %d"
          % (SP.TEMPERATURE, SP.SHAPE, SP.CONTEXT_TURNS), flush=True)
    # ⛔⛔ THE DIAL'S STATE IS ASSERTED AGAINST WHAT WAS ASKED FOR, in both
    # directions. An arm that wanted it off and got it on is a reading of a
    # knob labelled as a reading of a speaker; an arm that wanted it on and got
    # it off is the reverse, and reads as "the dial does nothing".
    if SP.FORCE_TABLE != dial:
        raise SystemExit("⛔⛔ FORCE_TABLE is %s, asked for %s — the env was "
                         "set too late" % (SP.FORCE_TABLE, dial))
    # ⛔⛔ ASSERT WHICH TABLE IS LIVE, not which one was intended. The dial
    # has two and they differ by 35 points on `ka`; a run that reports the
    # wrong one reads as a finding about the language.
    if dial:
        _w = SP.force_weights("ka")
        _legacy = abs(_w.get("ki", 0) - ki_weight) < 1e-9
        if _legacy != legacy_split:
            raise SystemExit(
                "⛔⛔ the LIVE dial table is %s but the arm asked for %s — "
                "weights %s" % ("legacy even-split" if _legacy else "corpus",
                                "legacy" if legacy_split else "corpus", _w))
        print("dial table %s · ka %.3f ki %.3f"
              % ("LEGACY even-split" if legacy_split else "CORPUS marginal",
                 _w["ka"], _w["ki"]), flush=True)
    print("force dial %s%s" % (("ON (%s)" % ("legacy %.2f" % SP.KI_WEIGHT
                                             if legacy_split else "corpus"))
                               if dial else "OFF",
                               "  ⛔ every number here is about the DIAL"
                               if dial else " ✅"), flush=True)

    # ══ THE MATCHED-FORCE ARM ═══════════════════════════════════════
    # ⛔⛔ THE `english` ARM CAN ONLY EVER TEST ONE CELL. A reader types a
    # declarative, the write step renders it `ka`, and the reply is drawn from
    # `ka -> ?`. The corpus's strongest non-`ka` signals live in `ko -> ko`
    # (44.1%) and `ku -> ku` (85.7%) and NOTHING in that arm ever reaches them.
    #
    # ⭐ So: real Tlön prompts taken from the corpus, each RESTAMPED to all five
    # forces. Same node, same roots, same length — the force is the only thing
    # that differs between the five members of a group, which is what makes a
    # difference in the reply attributable to it.
    stimuli = []
    if mode == "tlon":
        import json as _json
        from dataclasses import replace as _replace
        from tlon.grammar.parse import render as _render
        bases, seen = [], set()
        # ⛔ `/app/puzzle/`, not `/app/` — `add_local_dir(REPO/"puzzle")` mounts
        # the DIRECTORY, so a file inside it keeps its parent.
        with open("/app/puzzle/corpus_provoke_prompts.txt",
                  encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line in seen:
                    continue
                seen.add(line)
                bases.append(line)
                if len(bases) >= 12:
                    break
        forces = sorted(lex["classes"]["F"])
        for b in bases:
            sc = parse(b)
            for f in forces:
                stimuli.append((f, _render(_replace(sc, force=f))))
        print("matched stimuli: %d bases x %d forces = %d"
              % (len(bases), len(forces), len(stimuli)), flush=True)
        if not stimuli:
            raise SystemExit("⛔ no stimuli built — refusing to report on none")
        _ = _json

    print("hub       %s" % ("OFFLINE (cache only)" if hub_offline
                            else "online (may round-trip)"), flush=True)
    sp = SP.Speaker()
    t0 = time.perf_counter()
    sp.load()
    load_s = time.perf_counter() - t0
    print("loaded in %.1fs" % load_s, flush=True)

    forces = collections.Counter()
    refused = 0
    rows = []
    mismatch = []
    drawn_hist = collections.Counter()
    forces_by_drawn = collections.defaultdict(collections.Counter)
    by_prior = collections.defaultdict(collections.Counter)
    model_side = collections.Counter()
    for i in range(n):
        if mode == "tlon":
            want, prov = stimuli[i % len(stimuli)]
            english = prov
            try:
                # ⛔ `reply_to` IS THE PROVOKE HALF ON ITS OWN. Going through
                # `turn` would re-render an English line and hand the model a
                # `ka` again — measuring the write step a second time instead
                # of the question being asked.
                reply_t = sp.reply_to(prov, [])
            except Exception as exc:                      # noqa: BLE001
                refused += 1
                rows.append({"prior_force": want, "provocation": prov,
                             "error": str(exc)[:160]})
                continue
            if reply_t is None or not getattr(reply_t, "ok", False):
                refused += 1
                rows.append({"prior_force": want, "provocation": prov,
                             "refused": getattr(reply_t, "error", "no reply")})
                continue
            try:
                got = parse(reply_t.surface).force
            except Exception as exc:                      # noqa: BLE001
                refused += 1
                rows.append({"prior_force": want, "provocation": prov,
                             "error": "unparseable: %s" % exc})
                continue
            forces[got] += 1
            by_prior[want][got] += 1
            drawn_hist[1] += 1
            forces_by_drawn[1][got] += 1
            rows.append({"prior_force": want, "provocation": prov,
                         "surface": reply_t.surface, "force": got})
            if (i + 1) % 20 == 0:
                print("  %d/%d  %s" % (i + 1, n, dict(forces)), flush=True)
            continue
        english = PROVOCATIONS[i % len(PROVOCATIONS)]
        try:
            # ⛔ EMPTY PAIRS = A FIRST EXCHANGE, which is what most readers
            # ever send and what `onset` showed settles the conversation.
            res = sp.turn(english, [], [])
        except Exception as exc:                          # noqa: BLE001
            refused += 1
            rows.append({"english": english, "error": str(exc)[:160]})
            continue
        # ⭐⭐ `force_model` IS THE PRODUCT'S OWN RECORD of what the model
        # chose — the same value `logbook.py` writes to its `force_model`
        # column, stamped whether the dial is on or off. Reading it here rather
        # than re-deriving means this measures the field the bench reports.
        reply = res.get("tlon") if isinstance(res, dict) else None
        if not reply or not reply.get("surface"):
            refused += 1
            rows.append({"english": english,
                         "refused": (reply or {}).get("refused")
                         or "no reply"})
            continue
        surface = reply["surface"]
        f = res.get("force_model")
        # ⛔ CROSS-CHECKED against the surface, because two independent paths to
        # one value is the only cheap way to know either is right. A mismatch
        # is a bug in the stamping, not a force reading, and must not be
        # silently averaged into the histogram.
        try:
            parsed = parse(surface).force
        except Exception as exc:                          # noqa: BLE001
            refused += 1
            rows.append({"english": english, "surface": surface,
                         "error": "unparseable: %s" % exc})
            continue
        if f != parsed:
            mismatch.append({"english": english, "surface": surface,
                             "force_model": f, "parsed": parsed})
            f = parsed
        forces[f] += 1
        # ⭐ `replies_drawn` IS THE EVIDENCE THAT SELECTION HAPPENED. A row
        # served on draw 1 was not selected; a row served on draw 3 was chosen
        # over two the reader never saw. Recorded per row, so the force
        # histogram can be re-read conditioned on it.
        drawn = res.get("replies_drawn")
        drawn_hist[drawn] += 1
        forces_by_drawn[drawn][f] += 1
        # ⛔ No `carried` field: `SP.carries` takes the turn OBJECT and `turn()`
        # returns rows, so computing it here would mean re-deriving the gate's
        # own verdict from a gloss. `replies_drawn` already says whether
        # selection fired, which is the thing this arm is about.
        # ⭐⭐ BOTH SIDES OF THE DIAL, PER ROW. `force_model` is what the
        # speaker chose; `force_sent` is what the reader sees. With the dial off
        # they are equal by construction — which is itself the check that the
        # off arm really was off.
        rows.append({"english": english, "surface": surface, "force": f,
                     "force_model": res.get("force_model"),
                     "force_sent": res.get("force_sent"),
                     "replies_drawn": drawn,
                     "you": (res.get("you") or {}).get("surface")})
        if res.get("force_model") is not None:
            model_side[res["force_model"]] += 1
        if (i + 1) % 16 == 0:
            print("  %d/%d  %s" % (i + 1, n, dict(forces)), flush=True)

    total = sum(forces.values())
    return {"n_asked": n, "n_scored": total, "refused": refused,
            "force_stamp_mismatches": mismatch,
            "retries": retries,
            "replies_drawn_hist": dict(drawn_hist),
            "forces_by_replies_drawn":
                {k: dict(v) for k, v in forces_by_drawn.items()},
            "forces": dict(forces),
            "shares": {k: round(v / total, 4) for k, v in forces.items()}
            if total else {},
            "temperature": SP.TEMPERATURE, "adapter": SP.ADAPTER,
            "cell": cell,
            "four_bit": four_bit, "hub_offline": hub_offline,
            "base": SP.BASE_MODEL,
            "load_seconds": round(load_s, 2),
            "mode": mode,
            "dial": dial, "legacy_split": legacy_split,
            "ki_weight": ki_weight if legacy_split else None,
            "dial_table": (None if not dial else
                           ("legacy" if legacy_split
                            else "corpus")),
            "force_model_side": dict(model_side),
            "by_prior_force":
                {k: dict(v) for k, v in by_prior.items()},
            "lexicon": lex["_hash"], "rows": rows}


@app.local_entrypoint()
def main(n: int = 128, retries: int = 3, cell: str = CELLS[0],
         four_bit: bool = True, mode: str = "english",
         dial: bool = False, legacy_split: bool = False,
         ki_weight: float = 0.35, hub_offline: bool = False,
         base_override: str = ""):
    out = probe.remote(n, retries, cell, four_bit, mode, dial,
                       legacy_split, ki_weight, hub_offline,
                       base_override)
    import json
    import pathlib as _p
    print("\n" + "=" * 62)
    print("SAMPLED FORCE READ · temp %.2f · retries %d · %s"
          % (out["temperature"], out["retries"], out["cell"]))
    print("  scored %d of %d asked · %d refused"
          % (out["n_scored"], out["n_asked"], out["refused"]))
    t = out["n_scored"] or 1
    for f, c in sorted(out["forces"].items(), key=lambda kv: -kv[1]):
        print("    %-3s %4d  %5.1f%%" % (f, c, 100 * c / t))
    # ⛔ The reference it has to be read against, printed beside it so the
    # comparison cannot be made from memory.
    print("  corpus the adapter trained on: ka 52.6% ki 22.7% ko 14.5% "
          "ku 8.7% kä 1.5%")
    print("  the adapter it replaces, served: ka 99.7% (13 of 13 on the page)")
    if out.get("by_prior_force"):
        # ⛔ Printed BESIDE the corpus's own conditional, so the comparison is
        # read off one screen instead of out of memory.
        print("  REPLY FORCE GIVEN THE PRIOR'S FORCE "
              "(matched: same node, force restamped)")
        for pf in sorted(out["by_prior_force"]):
            row = out["by_prior_force"][pf]
            t = sum(row.values()) or 1
            print("    prior %-3s n=%-4d %s"
                  % (pf, t, "  ".join("%s %.0f%%" % (k, 100 * v / t)
                                      for k, v in sorted(row.items(),
                                                         key=lambda kv: -kv[1]))))
        print("  corpus says: ka->ka 54.6 · ki->ki 50.0 · ko->ko 44.1 · "
              "ku->ku 85.7 · kä->ka 50.5")
    if out.get("dial"):
        ms = out.get("force_model_side") or {}
        tm = sum(ms.values()) or 1
        print("  ⛔ DIAL ON · table=%s — the histogram above is the DIAL."
              % out.get("dial_table"))
        print("     what the MODEL chose underneath: %s"
              % "  ".join("%s %.0f%%" % (k, 100 * v / tm)
                          for k, v in sorted(ms.items(), key=lambda kv: -kv[1])))
    print("  LOAD %.2fs   base=%s   ⭐ the cold-start term"
          % (out.get("load_seconds", -1), out.get("base")))
    print("  draws taken: %s" % out["replies_drawn_hist"])
    for d in sorted(out["forces_by_replies_drawn"]):
        print("    served on draw %s: %s"
              % (d, out["forces_by_replies_drawn"][d]))
    dest = _p.Path("runs/act2/puzzle_force/force_probe_%s_r%d_%s_%s_dial%d.json"
                   % (out["cell"], out["retries"],
                      "nf4" if out["four_bit"] else "bf16",
                      out.get("mode", "english"),
                      int(bool(out.get("dial")))))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                    encoding="utf-8", newline="\n")
    print("  written → %s" % dest)


@app.function(image=image, gpu="A10", volumes={"/weights": weights},
              timeout=1800)
def load_breakdown() -> dict:
    """⛔⛔ IS THE COLD START READ-BOUND? DECIDE IT, DO NOT INFER IT.

    The evidence so far is that bf16 and NF4 load in the SAME time (17.0s vs
    17.5s), which is CONSISTENT with a read-dominated load — and equally
    consistent with quantisation simply being cheap while something else
    dominates. Those imply opposite decisions: a pre-quantised checkpoint
    (~4.5 GB instead of ~15 GB) is the whole fix under the first and worthless
    under the second.

    So this times the three terms separately on the same container:
      1. raw bytes off the volume, no model construction at all;
      2. `from_pretrained` on the base model;
      3. attaching the LoRA.
    """
    import glob
    import os
    import sys
    import time

    sys.path.insert(0, "/app")
    os.chdir("/app")
    os.environ["TLON_LEXICON"] = "lexicon_expanded.yaml"

    cache = "/weights/hf"
    shards = sorted(glob.glob(cache + "/**/*.safetensors", recursive=True))
    total = sum(os.path.getsize(f) for f in shards)
    t0 = time.perf_counter()
    read = 0
    for f in shards:
        with open(f, "rb", buffering=0) as fh:
            while True:
                b = fh.read(1 << 24)
                if not b:
                    break
                read += len(b)
    raw = time.perf_counter() - t0
    print("RAW READ  %d shards · %.2f GB · %.1fs · %.0f MB/s"
          % (len(shards), total / 1e9, raw, (read / 1e6) / max(raw, 1e-9)),
          flush=True)

    from puzzle import speaker as SP
    t1 = time.perf_counter()
    sp = SP.Speaker()
    sp.load()
    full = time.perf_counter() - t1
    print("FULL LOAD %.1fs" % full, flush=True)
    return {"shards": len(shards), "bytes": total,
            "raw_read_seconds": round(raw, 2),
            "raw_mb_per_s": round((read / 1e6) / max(raw, 1e-9), 1),
            "full_load_seconds": round(full, 2),
            "read_share": round(raw / full, 3) if full else None}


@app.local_entrypoint()
def breakdown():
    out = load_breakdown.remote()
    print("\n" + "=" * 58)
    print("COLD-START LOAD BREAKDOWN")
    print("  weights on volume   %.2f GB in %d shards"
          % (out["bytes"] / 1e9, out["shards"]))
    print("  raw read            %.1fs  (%.0f MB/s)"
          % (out["raw_read_seconds"], out["raw_mb_per_s"]))
    print("  full speaker load   %.1fs" % out["full_load_seconds"])
    print("  read share          %.0f%%" % (100 * (out["read_share"] or 0)))
    print("⭐ read share HIGH  => a pre-quantised (~4.5 GB) checkpoint is the fix")
    print("⛔ read share LOW   => the time is construction; a smaller file buys")
    print("                       nothing and this lever is dead")


@app.function(image=image, gpu="A10", volumes={"/weights": weights},
              timeout=3600)
def build_nf4() -> dict:
    """⭐ SAVE THE BASE MODEL ALREADY QUANTISED, ONCE.

    Measured: the cold start is 90% raw read — 13.8s of a 15.3s load is 15.23 GB
    of bf16 safetensors coming off the volume at 1100 MB/s. NF4 on disk is ~4.5
    GB, so the read term should fall by ~3x and take the load with it.

    ⛔ This writes to the SHARED `tlon-weights` volume under its own directory.
    It does not touch the HF cache the current path reads, so the live bench is
    unaffected until something is pointed at the new directory on purpose.
    """
    import os
    import shutil
    import sys
    import time

    sys.path.insert(0, "/app")
    os.chdir("/app")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    base = os.environ.get("TLON_BASE", "Qwen/Qwen2.5-7B-Instruct")
    dest = "/weights/nf4/qwen2.5-7b-instruct-nf4"

    # ⛔ The EXACT quantisation the speaker serves under, or this is a different
    # model wearing the same name. `act2_backends.LocalBackend` builds NF4 with
    # double quant and a bf16 compute dtype.
    qc = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    t0 = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(
        base, quantization_config=qc, dtype=torch.bfloat16, device_map={"": 0})
    load_s = time.perf_counter() - t0
    print("loaded+quantised in %.1fs" % load_s, flush=True)

    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)
    t1 = time.perf_counter()
    model.save_pretrained(dest, safe_serialization=True)
    AutoTokenizer.from_pretrained(base).save_pretrained(dest)
    save_s = time.perf_counter() - t1

    size = sum(os.path.getsize(os.path.join(dp, f))
               for dp, _dn, fn in os.walk(dest) for f in fn)
    print("saved %.2f GB in %.1fs -> %s" % (size / 1e9, save_s, dest), flush=True)
    # ⛔⛔ COMMIT, OR IT IS NOT THERE. A Modal volume write is not visible to the
    # next container until the volume is committed, and a silent loss here would
    # look exactly like "the pre-quantised path did not help".
    weights.commit()
    print("volume committed", flush=True)
    return {"dest": dest, "bytes": size, "gb": round(size / 1e9, 2),
            "quantise_seconds": round(load_s, 1),
            "save_seconds": round(save_s, 1)}


@app.local_entrypoint()
def nf4():
    out = build_nf4.remote()
    print("\n" + "=" * 58)
    print("PRE-QUANTISED CHECKPOINT")
    print("  path      %s" % out["dest"])
    print("  size      %.2f GB   (was 15.23 GB bf16)" % out["gb"])
    print("  quantise  %.1fs · save %.1fs  — ONE OFF" %
          (out["quantise_seconds"], out["save_seconds"]))


@app.function(image=image, gpu="A10", volumes={"/weights": weights},
              timeout=3600)
def verify_nf4() -> dict:
    """⛔⛔ IS THE PRE-QUANTISED CHECKPOINT THE SAME SPEAKER?

    Quantisation is deterministic, so NF4-on-disk and NF4-quantised-at-load
    SHOULD produce identical logits. "Should" is why this exists: if they
    diverge, the faster path is a different model, and every number measured
    tonight stops describing what is served.

    ⛔ GREEDY, and that is the point — at temperature 0.7 two identical models
    disagree constantly and the comparison says nothing. `do_sample=False`
    makes any difference in the weights show up as a difference in the tokens.
    """
    import os
    import sys
    import time

    sys.path.insert(0, "/app")
    os.chdir("/app")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    base = os.environ.get("TLON_BASE", "Qwen/Qwen2.5-7B-Instruct")
    pre = "/weights/nf4/qwen2.5-7b-instruct-nf4"
    qc = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                            bnb_4bit_use_double_quant=True,
                            bnb_4bit_compute_dtype=torch.bfloat16)
    tok = AutoTokenizer.from_pretrained(base)
    prompts = ["The rain has stopped.", "I sat by the river.",
               "Say something about thinning.", "What happens next?"]

    def gen(model):
        out = []
        for p in prompts:
            # ⛔ `apply_chat_template(return_tensors=...)` hands back a
            # BatchEncoding in transformers 5.x, not a tensor. Render to text,
            # then tokenise — one shape, no version guessing.
            text = tok.apply_chat_template([{"role": "user", "content": p}],
                                           add_generation_prompt=True,
                                           tokenize=False)
            enc = tok(text, return_tensors="pt").to(model.device)
            n_in = enc["input_ids"].shape[-1]
            with torch.no_grad():
                y = model.generate(**enc, max_new_tokens=48, do_sample=False)
            out.append(tok.decode(y[0][n_in:], skip_special_tokens=True))
        return out

    t0 = time.perf_counter()
    m_old = AutoModelForCausalLM.from_pretrained(
        base, quantization_config=qc, dtype=torch.bfloat16, device_map={"": 0})
    t_old = time.perf_counter() - t0
    g_old = gen(m_old)
    del m_old
    torch.cuda.empty_cache()

    t1 = time.perf_counter()
    m_new = AutoModelForCausalLM.from_pretrained(pre, device_map={"": 0})
    t_new = time.perf_counter() - t1
    g_new = gen(m_new)

    same = sum(1 for a, b in zip(g_old, g_new) if a == b)
    print("load  on-the-fly %.1fs   pre-quantised %.1fs" % (t_old, t_new),
          flush=True)
    print("identical greedy generations: %d/%d" % (same, len(prompts)),
          flush=True)
    for a, b in zip(g_old, g_new):
        if a != b:
            print("  ⛔ DIVERGED\n     old: %r\n     new: %r"
                  % (a[:90], b[:90]), flush=True)
    return {"load_on_the_fly": round(t_old, 2),
            "load_pre_quantised": round(t_new, 2),
            "identical": same, "n": len(prompts),
            "speedup": round(t_old / t_new, 2) if t_new else None}


@app.local_entrypoint()
def verify():
    out = verify_nf4.remote()
    print("\n" + "=" * 58)
    print("PRE-QUANTISED CHECKPOINT — VERIFICATION")
    print("  load on-the-fly     %.1fs" % out["load_on_the_fly"])
    print("  load pre-quantised  %.1fs   (%.2fx)"
          % (out["load_pre_quantised"], out["speedup"] or 0))
    print("  identical greedy    %d/%d" % (out["identical"], out["n"]))
    if out["identical"] != out["n"]:
        print("  ⛔⛔ NOT THE SAME SPEAKER — do not ship this path")
    else:
        print("  ✅ same weights, same tokens — safe to point the bench at it")
