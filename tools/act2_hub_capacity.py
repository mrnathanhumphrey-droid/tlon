"""⛔⛔ THE PERSIST-CAPACITY FLOOR — run BEFORE train_leg1, exit 1 if there is
no room.

    python tools/act2_hub_capacity.py --repo <repo> \\
        --n-trainable 4428098048 --n-frozen 3187518464

Rung 1b' trained a clean epoch and then could not persist it, because the check
that ran was "can I write a byte to this repo" and the thing it depended on was
"is there room for 24 GB". This asks the second question, at the floors, where
a refusal costs nothing.

⛔ It REFUSES rather than warns. A warning in a pipeline log is a line nobody
reads at 03:04 while an H100 bills.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from tlon.act2.hub_capacity import (FITS, PROVEN_ACCEPTED_BYTES,  # noqa: E402
                                    check, projected_artifact_bytes,
                                    used_storage_bytes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    # ⛔ BILLIONS, matching `act2_finetune.py --params/--trainable-params`, so
    # the floor is fed the pipeline's OWN scope variables. Exact integer counts
    # would have to be typed in, and would go stale the moment UNFREEZE_TOP
    # moves -- a floor sized on a scope the run no longer has is decoration.
    ap.add_argument("--trainable-b", type=float, required=True,
                    help="trainable parameters in billions (e.g. 4.428)")
    ap.add_argument("--total-b", type=float, required=True,
                    help="TOTAL model parameters in billions (e.g. 7.616); "
                         "frozen is the difference")
    ap.add_argument("--master-bytes", type=int, default=4,
                    help="bytes per TRAINABLE parameter as persisted. 4 = the "
                         "fp32 master §5 declares; a full-weight run that "
                         "projected 2 here would under-count by 40%%.")
    ap.add_argument("--frozen-bytes", type=int, default=2)
    ap.add_argument("--ceiling", type=int, default=PROVEN_ACCEPTED_BYTES)
    a = ap.parse_args()

    import act2_provision as prov
    from huggingface_hub import HfApi

    n_trainable = int(round(a.trainable_b * 1e9))
    n_frozen = int(round((a.total_b - a.trainable_b) * 1e9))
    if n_frozen < 0:
        raise SystemExit("⛔ --trainable-b %.3f exceeds --total-b %.3f"
                         % (a.trainable_b, a.total_b))

    api = HfApi(token=prov._hf_token())
    used = used_storage_bytes(a.repo, api=api)
    # ⛔⛔ BOTH FIGURES, PRINTED. They fail in opposite directions — dead LFS
    # history inflates `usedStorage`, and a recent push leaves it STALE and
    # too low. On 2026-09-12 it read 68.88 GB against 90.43 GB of live files
    # and would have admitted a run that could not persist.
    from tlon.act2.hub_capacity import live_file_bytes
    _live = live_file_bytes(a.repo, api=api)
    _rep = getattr(api.model_info(a.repo, expand=["usedStorage"]),
                   "used_storage", None)
    if _live is None:
        print("   ⚠️ live-file listing unavailable — NO second opinion on the "
              "reported figure")
    else:
        print("   reported %10.2f GB   live files %.2f GB   -> using %.2f GB%s"
              % ((_rep or 0) / 1e9, _live / 1e9, used / 1e9,
                 "" if abs((_rep or 0) - _live) < 1e9 else
                 "  ⛔ THEY DISAGREE by %.2f GB — taking the larger"
                 % (abs((_rep or 0) - _live) / 1e9)))
    projected = projected_artifact_bytes(n_trainable, n_frozen,
                                         master_bytes=a.master_bytes,
                                         frozen_bytes=a.frozen_bytes)
    verdict, why = check(used, projected, ceiling=a.ceiling)

    gb = 1e9
    print("⭐ PERSIST-CAPACITY FLOOR — %s" % a.repo)
    print("   used now       %10.2f GB   ⛔ INCLUDES dead LFS history, which "
          "is charged" % (used / gb))
    print("   this run needs %10.2f GB   (%d trainable x %dB + %d frozen x %dB)"
          % (projected / gb, n_trainable, a.master_bytes,
             n_frozen, a.frozen_bytes))
    print("   ceiling        %10.2f GB   ⚠️ PROVEN-ACCEPTED, a LOWER BOUND — "
          "the hub exposes no quota field" % (a.ceiling / gb))
    print("   %s" % why)

    if verdict == FITS:
        print("   ✅ %s" % verdict)
        return 0
    print("   ⛔⛔ %s — REFUSING to start a run that cannot keep its result."
          % verdict)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
