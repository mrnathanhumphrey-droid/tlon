"""SCORE A GATE BOTH WAYS — as-scored, and crediting valid Tlön surfaces. $0.

⛔⛔ THIS EXISTS BECAUSE THE ANSWER IS NOT OBVIOUS AND MUST NOT BE DECIDED BY
WHOEVER HAPPENS TO WRITE THE SCORER. Run 4's speak fell to 76.2 %, and the
recon on that same adapter found **16 of 16** unparseable generations were
grammatical Tlön that round-trips exactly — the model answered a Tlön history
IN TLÖN and the harness scored it zero for not being JSON.

⭐ THE CASE FOR CREDITING: F-LOCAL's bar is *"first-attempt legal emission,
cardless, unconstrained"*. A valid surface **is** a legal emission; the grammar
is exactly invertible so `parse()` recovers the Scene with **zero ambiguity**;
and the ARENA EXCHANGES SURFACES, NOT JSON — so this behaviour suits the arena
better, not worse.

⛔ THE CASE AGAINST: the probe prompt says *"Emit ONLY the JSON object"*, so a
model ignoring it is failing an instruction; the product gate is the schema; and
runs 3–4 CANNOT be re-scored this way because their raws were discarded, so a
rule change breaks cross-run comparability.

⛔⛔ SO THIS TOOL DECIDES NOTHING. It prints both numbers side by side and names
which rows moved. **Changing a scoring rule after seeing that it favours the
model is the exact shape this project refuses**, and the only defence is to make
the choice explicit, in advance of using either number as a result.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.grammar.parse import parse, render                   # noqa: E402


def credit(raw: str | None) -> tuple[bool, bool]:
    """(parses as Tlön, round-trips exactly). ⛔ BOTH are reported: a surface
    that parses but does not round-trip is a parser question, not a model one,
    and lumping them would hide it."""
    if not raw or not raw.strip():
        return False, False
    try:
        scene = parse(raw.strip())
    except Exception:                                          # noqa: BLE001
        return False, False
    try:
        return True, render(scene) == raw.strip()
    except Exception:                                          # noqa: BLE001
        return True, False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    rows = [json.loads(x) for x in
            pathlib.Path(a.ledger).read_text(encoding="utf-8").splitlines()
            if x.strip()]
    runs = [r for r in rows if r.get("event") == "f_local"
            and r.get("results", {}).get("render", {}).get("n") == a.n]
    if not runs:
        raise SystemExit(f"⛔ no f_local row at n={a.n} in {a.ledger}")
    run = runs[-1]

    print(f"DUAL SCORE · {a.ledger} · battery {run.get('battery')} · n={a.n}")
    print("⛔ NOTHING IS DECIDED HERE — both numbers, so the rule can be chosen "
          "deliberately.\n")
    print(f"  {'task':<8}{'as scored':>12}{'+valid Tlön':>14}{'Δ':>7}   "
          f"{'round-trips':>12}  {'no-raw':>7}")

    out = {}
    for kind in ("render", "speak"):
        d = run["results"].get(kind, {})
        n = d.get("n") or 0
        valid = d.get("valid") or 0
        fails = d.get("failures", [])
        tlon = rt = noraw = 0
        for f in fails:
            if f.get("proposal") is not None:
                continue                      # JSON that failed the schema
            raw = f.get("raw")
            if raw is None:
                noraw += 1
                continue
            p, r = credit(raw)
            tlon += p
            rt += r
        out[kind] = {"n": n, "as_scored": valid, "credited": valid + tlon,
                     "tlon_surfaces": tlon, "round_trips": rt, "no_raw": noraw}
        if not n:
            continue
        print(f"  {kind:<8}{100 * valid / n:>11.1f}%{100 * (valid + tlon) / n:>13.1f}%"
              f"{100 * tlon / n:>+6.1f}%{rt:>10}/{tlon:<3}{noraw:>7}")

    # ⛔ A ROW WITH NO RAW IS AN INSTRUMENT GAP, NOT A MODEL RESULT, AND IT MUST
    # NOT BE COUNTED EITHER WAY WITHOUT BEING SEEN.
    gaps = sum(v["no_raw"] for v in out.values())
    if gaps:
        print(f"\n  ⛔⛔ {gaps} failure row(s) carry NO RAW. Those predate the "
              "harness fix or came from a backend that\n     does not attach "
              "one — they cannot be scored either way and are counted as "
              "failures\n     in BOTH columns. The credited number is therefore "
              "a LOWER bound.")
    else:
        print("\n  ✅ every failure row carries its raw — both columns are "
              "complete.")

    print("\n  ── what the crediting rule would change ──")
    for kind, v in out.items():
        if v["tlon_surfaces"]:
            print(f"    {kind}: {v['tlon_surfaces']} generation(s) that are legal "
                  f"Tlön, {v['round_trips']} of which round-trip exactly")
        else:
            print(f"    {kind}: nothing moves — no unparseable generation was "
                  "valid Tlön")

    if a.out:
        p = pathlib.Path(a.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2, ensure_ascii=False),
                     encoding="utf-8", newline="")
        print(f"\n  wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
