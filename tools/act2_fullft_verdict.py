"""THE §4.2 VERDICT TABLE, APPLIED — three axes, and the precondition first.

    python tools/act2_fullft_verdict.py --delta runs/.../weight_delta.json \\
        --lag runs/.../model_lag_fw.json --ledger runs/act2/ledger.jsonl \\
        --out runs/.../verdict_epoch1.json

⛔⛔ THE THRESHOLDS ARE IMPORTED, NEVER RE-SPELT. PREREG a0450b36 §3/§4 requires
the constants the corpus and the LoRA gate were read against, and a number typed
here would let the gate be tuned after seeing the model. Identity is asserted,
not assumed.

⛔⛔ AND THE PRECONDITION RUNS FIRST. §4.1: if the weights did not move, NO ROW
of the table may be read — not GO, not any STOP. A run whose optimizer wrote
nothing is not evidence about the substrate, and the only way to keep that true
is to refuse to compute the other axes at all.

Exit codes are the pipeline's branch: 0 = GO, 1 = a STOP row, 3 = the
precondition failed. ⭐ The epoch-1 early-stop in §5 is exactly `exit 0 here`.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.act2.weight_delta import INSTRUMENT_FAULT, OK as DELTA_OK
from tlon.discourse.transient import Z_LAG1_MIN, Z_LAGN_MAX

GO = "GO"
STOP_FLOORED = "STOP — floored"
STOP_CRATERED = "STOP — fluency cratered"
STOP_PERCEIVE = "STOP — perceive killed"
STOP_INCOHERENT = "STOP — incoherent"
FAULT = "INSTRUMENT FAULT"


def last_f_local(ledger_path) -> dict:
    """The most recent `f_local` row. ⛔ The ledger is append-only, so the LAST
    one is this run's — reading the first would score a previous build."""
    p = pathlib.Path(ledger_path)
    if not p.exists():
        raise SystemExit("⛔ no ledger at %s — F-LOCAL is a GO axis (§4) and "
                         "an unmeasured axis is not a passed one." % p)
    row = None
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("event") == "f_local":
            row = r
    if row is None:
        raise SystemExit("⛔ no f_local row in %s" % p)
    return row


def readable_stop(out: dict) -> bool:
    """Is this a STOP that is nonetheless worth PROTECTING from a later epoch?

    ⭐ PREREG `9ccf98d6` §3. A floored-but-fluent verdict — release fails while
    perceive and F-LOCAL both hold, with the §4.1 precondition passed — is a
    complete, coherent, interpretable measurement. Rung 1a produced exactly one
    of those at epoch 1 and then trained past it.

    ⛔ Deliberately narrow. A cratered, perceive-killed or incoherent row is NOT
    readable-and-worth-protecting: there is nothing there an epoch 2 could
    destroy that has not already been lost. Widening this would convert the stop
    from "protect a result" into "halt on anything", which is a different
    procedure than the one hashed into the body.
    """
    if out.get("verdict") != STOP_FLOORED:
        return False
    axes = out.get("axes") or {}
    return bool(axes.get("perceive", {}).get("ok")
                and axes.get("f_local", {}).get("ok"))


def decide(delta: dict, lag: dict, flocal: dict) -> dict:
    """§4.2, in the order the table is written."""
    # ── the precondition, before anything else ──────────────────────────────
    if delta.get("verdict") != DELTA_OK:
        return {
            "verdict": FAULT,
            "why": ("§4.1 precondition did not pass (%s): %s NO ROW OF THE "
                    "VERDICT TABLE MAY BE READ. This run is not evidence about "
                    "the substrate."
                    % (delta.get("verdict"), delta.get("why", ""))),
            "delta_verdict": delta.get("verdict"),
            "fraction_changed": delta.get("fraction_changed"),
            "axes_not_computed": True,
        }

    z = {int(k): v for k, v in (lag.get("z") or {}).items()}
    if 1 not in z or 2 not in z:
        return {"verdict": STOP_INCOHERENT,
                "why": "lag profile is missing lag-1 or lag-2; the instrument "
                       "did not produce a readable profile.",
                "axes_not_computed": True}

    longer = {k: v for k, v in z.items() if k >= 2}
    release_ok = all(v <= Z_LAGN_MAX for v in longer.values())
    perceive_ok = z[1] >= Z_LAG1_MIN
    # ⛔ `fired` TRUE MEANS F-LOCAL FAILED. And `None` means UNSCOREABLE, which
    # is not a pass: a degenerate speaker cannot be scored, and treating an
    # unscoreable axis as clear is the vacuous pass this project keeps finding.
    fired = flocal.get("fired")
    flocal_ok = fired is False

    axes = {
        "release": {"ok": release_ok, "z_by_lag": longer,
                    "ceiling": Z_LAGN_MAX},
        "perceive": {"ok": perceive_ok, "z_lag1": z[1], "floor": Z_LAG1_MIN},
        "f_local": {"ok": flocal_ok, "fired": fired,
                    "unscoreable": fired is None},
    }

    if release_ok and perceive_ok and flocal_ok:
        v, why = GO, ("release transmits, perceive holds, F-LOCAL clears. The "
                      "module is buildable; the drift measurement is un-blocked.")
    elif not release_ok and perceive_ok and flocal_ok:
        v, why = STOP_FLOORED, (
            "(b). Persistence survives the unfreezing declared in §5. ⛔ NOT "
            "YET A SUBSTRATE FINDING — §7.1's escalation ladder must be "
            "exhausted first (more layers, then embeddings, then the wall).")
    elif release_ok and perceive_ok and not flocal_ok:
        v, why = STOP_CRATERED, (
            "(c). Release installed at the cost of the native speaker. "
            "Pre-declared dial-back: LR -> 5e-6, as a NEW pre-registered run.")
    elif release_ok and not perceive_ok:
        v, why = STOP_PERCEIVE, (
            "(d). Collapsed toward content-free. The ENTANGLED fork re-opens "
            "at the weight level.")
    else:
        v, why = STOP_INCOHERENT, (
            "mixed profile: instrument or training fault before interpretation.")

    return {"verdict": v, "why": why, "axes": axes,
            "delta_verdict": delta.get("verdict"),
            "fraction_changed": delta.get("fraction_changed"),
            "measurement_category": "_w",
            "PREREG": "a0450b36",
            "thresholds": {"z_lag1_min": Z_LAG1_MIN, "z_lagn_max": Z_LAGN_MAX},
            "THRESHOLDS_IMPORTED_FROM": "tlon.discourse.transient"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delta", required=True)
    ap.add_argument("--lag", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    # ⛔ §3's identity assertion, at the point of use.
    import tlon.discourse.transient as _t
    assert Z_LAG1_MIN is _t.Z_LAG1_MIN and Z_LAGN_MAX is _t.Z_LAGN_MAX, \
        "⛔⛔ thresholds are not the corpus's own constants"

    delta = json.loads(pathlib.Path(a.delta).read_text(encoding="utf-8"))
    lag = json.loads(pathlib.Path(a.lag).read_text(encoding="utf-8"))
    # ⛔ The lag read must be OF the `_w` object. A profile recorded against an
    # adapter, or against the bare base model, answers a different question.
    if lag.get("object_kind") != "full_weight":
        raise SystemExit(
            "⛔⛔ the lag profile at %s has object_kind=%r, not 'full_weight'. "
            "This verdict is about a `_w` object; reading a `_ctx` profile here "
            "would pool the categories C8 separates."
            % (a.lag, lag.get("object_kind")))
    flocal = last_f_local(a.ledger)

    out = decide(delta, lag, flocal)
    outp = pathlib.Path(a.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=2), encoding="utf-8")

    mark = "⭐" if out["verdict"] == GO else "⛔⛔"
    print("\n%s §4.2 VERDICT: %s" % (mark, out["verdict"]))
    print("   " + out["why"])
    for name, ax in (out.get("axes") or {}).items():
        print("   %-9s %s" % (name, "PASS" if ax["ok"] else "FAIL"))
    print("   -> %s" % outp)

    if out["verdict"] == FAULT:
        return 3
    if out["verdict"] == GO:
        return 0
    # ⭐⭐ EXIT 4 = A READABLE STOP. PREREG `9ccf98d6` §3, and it is the
    # procedural fix rung 1a needed and did not have.
    #
    # ⛔⛔ Rung 1a's early stop fired only on GO, so its clean epoch-1
    # floored-but-fluent state — release FAIL, perceive PASS, f_local PASS, the
    # §4.1 precondition satisfied — could not halt the run. Epoch 2 then
    # over-fit past it and destroyed the readable state (every lag rose, f_local
    # cratered), and the verdict of record became uninterpretable.
    #
    # ⭐ A floored-but-fluent epoch 1 is EXACTLY the state an epoch-2 over-fit
    # destroys, so the caller has to be able to see it. GO and floored-but-fluent
    # are both READABLE; every other STOP is not, and only those run epoch 2.
    #
    # ⛔ This changes WHEN a run halts, never a threshold. Z_LAG1_MIN and
    # Z_LAGN_MAX are untouched and still imported.
    if readable_stop(out):
        return 4
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
