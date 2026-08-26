"""SPEAK-COLLAPSE RECONNAISSANCE — and it is MULTI-TURN recon, not a render fix.

⛔⛔ RUN 4's SPEAK FELL 97.3 % → 76.2 % AND **60 OF 61 FAILURES WERE "no parseable
JSON"** — only one was a class error. So this is not a class-discipline failure
at all, and it could not be diagnosed at any price because the harness stored
`proposal: null` and threw the text away. That is now fixed; this captures what
was lost.

⭐⭐ WHY IT IS RECONNAISSANCE FOR THE MULTI-TURN CORPUS, NOT A SIDE-QUEST.
`speak` is *"read an accumulated Tlön history → produce the next Scene"* — which
is **structurally the single-turn shadow of every multi-turn turn.** How the
model fails here is a preview of how it fails at depth, and it decides the BUILD
ORDER of the discourse layer:

    if the model cannot produce parseable output while conditioned on Tlön
    history, then CONDITIONING is a lower-level problem than COHERENCE, and the
    multi-turn corpus must fix generation-under-Tlön-conditioning BEFORE it can
    address abide / close / break at all.

Three shapes are scored, because "did it look broken?" is exactly the question a
transcript seduces you into answering by squinting:

    ECHO          the output lifts fragments of the Tlön history verbatim — the
                  OOD-retreat signature already measured in the raw arena, where
                  depth-1 histories produced an 8/10 exact mirror of parse(hist)
    MUSH          near-Tlön: the shape of an answer, structurally broken
    COLLAPSE      retreat to a trivial scene when the history is complex

    python tools/act2_speak_recon.py --model <id> --adapter runs/act2/adapter \\
        --n 64 --depths 1,3,5,8
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.act2 import probes                                   # noqa: E402
from tlon.act2.llm import LLMSpeaker                           # noqa: E402
from tlon.product import schema as PS                          # noqa: E402

_WORD = re.compile(r"[a-zä-ÿ]+", re.IGNORECASE)


def shapes(raw: str, history: tuple[str, ...]) -> dict:
    """Score the three failure shapes. ⛔ Computed, never eyeballed."""
    toks = _WORD.findall(raw.lower())
    hist_toks = {t for h in history for t in _WORD.findall(h.lower())}
    overlap = (sum(t in hist_toks for t in toks) / len(toks)) if toks else 0.0
    # a verbatim run of >=4 history tokens is a lift, not a coincidence
    lifted = max((len(h) for h in history
                  if h and h.lower() in raw.lower()), default=0)
    return {
        "chars": len(raw),
        "starts_json": raw.lstrip().startswith("{"),
        "has_open_brace": "{" in raw,
        "balanced": raw.count("{") == raw.count("}") and "{" in raw,
        "history_token_overlap": round(overlap, 3),
        "verbatim_history_span": lifted,
        "looks_like_tlon_not_json": bool(toks) and "{" not in raw,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--depths", default="1,3,5,8",
                    help="history depths to probe — the arena lives at DEPTH, "
                         "and depth 1 is the deterministic-echo regime")
    ap.add_argument("--out", default="runs/act2/logs/speak_recon.json")
    a = ap.parse_args()

    from act2_backends import LocalBackend

    battery = probes.build(seed=7, n_prod=256, n_comp=256)
    pool = [p.surface for p in battery.comprehension]
    depths = [int(x) for x in a.depths.split(",") if x.strip()]

    back = LocalBackend(a.model, adapter=a.adapter, temperature=0.0)
    sp = LLMSpeaker("recon", back, card=False)

    rows = []
    print(f"SPEAK RECON · adapter={a.adapter} · n={a.n} per depth · "
          f"depths {depths}")
    print("⛔ every raw generation is captured, parseable or not\n")

    for depth in depths:
        ok = 0
        for i in range(a.n):
            hist = tuple(pool[(i * depth) % 200:(i * depth) % 200 + depth])
            if len(hist) < depth:
                continue
            sp.last_failure = None
            proposal = sp.speak(hist, i + 1)
            row = {"depth": depth, "i": i, "history": list(hist)}
            if proposal is None:
                lf = sp.last_failure or {}
                raw = lf.get("raw") or ""
                row.update(outcome="NO_JSON", raw=raw, reason=lf.get("reason"),
                           **shapes(raw, hist))
            else:
                try:
                    PS.validate(proposal)
                    ok += 1
                    row.update(outcome="VALID", proposal=proposal)
                except Exception as exc:                       # noqa: BLE001
                    row.update(outcome="INVALID", proposal=proposal,
                               reason=str(exc)[:200])
            rows.append(row)
        n_d = sum(1 for r in rows if r["depth"] == depth)
        print(f"  depth {depth}: {ok}/{n_d} valid "
              f"({100 * ok / max(1, n_d):.0f} %)")

    # ── the shapes, over the NO_JSON rows ────────────────────────────────
    nojson = [r for r in rows if r["outcome"] == "NO_JSON"]
    print(f"\n  ── {len(nojson)} unparseable generations captured ──")
    if nojson:
        n = len(nojson)
        echo = sum(r["history_token_overlap"] >= 0.5 for r in nojson)
        lift = sum(r["verbatim_history_span"] > 0 for r in nojson)
        tlon = sum(r["looks_like_tlon_not_json"] for r in nojson)
        part = sum(r["has_open_brace"] and not r["balanced"] for r in nojson)
        empty = sum(r["chars"] == 0 for r in nojson)
        print(f"    ECHO   ≥50 % of tokens came from the history : {echo}/{n}"
              f"  ({100 * echo / n:.0f} %)")
        print(f"           a VERBATIM history line was reproduced : {lift}/{n}")
        print(f"    MUSH   emitted Tlön prose, no JSON at all     : {tlon}/{n}"
              f"  ({100 * tlon / n:.0f} %)")
        print(f"           opened a brace and never closed it     : {part}/{n}")
        print(f"    EMPTY  produced nothing at all                : {empty}/{n}")
        lens = sorted(r["chars"] for r in nojson)
        print(f"    length min {lens[0]} · median {lens[len(lens) // 2]} · "
              f"max {lens[-1]}")
        # ⛔ THE DOMINANT SHAPE IS NAMED, not left for a reader to infer.
        top = max((("ECHO", echo), ("MUSH", tlon), ("TRUNCATED_JSON", part),
                   ("EMPTY", empty)), key=lambda kv: kv[1])
        print(f"\n  ⇒ DOMINANT SHAPE: {top[0]} ({top[1]}/{n})")
        print("     ── first three raws, verbatim ──")
        for r in nojson[:3]:
            print(f"       depth {r['depth']}: {r['raw'][:220]!r}")

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"adapter": a.adapter, "rows": rows}, indent=2,
                              ensure_ascii=False), encoding="utf-8", newline="")
    print(f"\n  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
