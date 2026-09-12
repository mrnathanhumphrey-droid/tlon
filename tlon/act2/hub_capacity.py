"""⛔⛔ IS THERE ROOM FOR WHAT THIS RUN WILL PERSIST — asked BEFORE it trains.

WHY IT EXISTS, STATED AS THE LOSS IT IS PREVENTING. On 2026-09-08 rung 1b'
trained a clean epoch on an H100 -- 3,760 steps, `eager`, zero non-finite
gradients, a dose that landed inside its pre-registered band -- and then died
at `persist_leg1` with

    Private repository storage limit reached

The weights were 24 GB on a rented box, the watchdog terminated it as designed,
and the run's actual measurement (F-LOCAL, the lag profile, the verdict) had
never executed. ~2 H100-hours bought three side-findings and not the number the
run was for.

⛔⛔ AND A CHECK HAD ALREADY PASSED. `act2_retrain_orchestrate.cmd_env` writes a
tiny probe file to the hub and reports "persist path verified writable". It is
true and it is not the question. **A 2 KB commit succeeds in a repo with no
room for a 24 GB one**, so the probe proved the PATH and the run depended on the
CAPACITY. That is this project's oldest shape -- a green check on an adjacent
quantity -- and the fix is not a better probe, it is asking the question the run
actually depends on.

⛔ THE OBVIOUS SERVER-SIDE PROBE IS ALSO VACUOUS, AND IT WAS TESTED, NOT
ASSUMED. HF's `preupload` endpoint takes a declared file SIZE, so it looks like
exactly the right thing to ask. It returns `uploadMode: lfs` for a declared
24 GB file in a repo that then refuses the commit -- identical response to a
1 KB file. Quota is enforced at COMMIT, not at preupload. So preupload cannot
be the guard either; it is the same vacuous pass one layer down.

⭐ WHAT IS ACTUALLY KNOWABLE, AND WHAT IS NOT:

  - **used storage IS queryable**, per repo, via `expand=["usedStorage"]`.
  - **the limit is NOT.** `whoami-v2` carries `isPro` and no quota field; there
    is no storage endpoint. So the ceiling cannot be read, and a ceiling TYPED
    IN FROM MEMORY would be a guessed constant governing a $9 decision.

⭐⭐ SO THE CEILING IS A MEASUREMENT, NOT A GUESS: the largest usage this hub
account has been OBSERVED TO HOLD. That number was accepted -- the bytes are
sitting there -- so anything at or below it demonstrably fits. This can refuse a
run that would have fitted (safe, and cheap to re-check), and cannot admit one
that will not (the expensive direction). ⛔ It is a lower bound on the true
limit, deliberately, and it is labelled as one everywhere it is used.
"""
from __future__ import annotations

FITS = "FITS"
NO_ROOM = "NO_ROOM"
UNKNOWN = "UNKNOWN"

#: ⭐ MEASURED, 2026-09-08: `tlon-act2-adapters` was holding exactly this and
#: serving it. Not a plan limit, not a remembered figure -- an observation that
#: this much has been accepted. ⛔ A LOWER BOUND on the true ceiling.
PROVEN_ACCEPTED_BYTES = 94_214_989_055

#: ⭐ MEASURED, the same day: at the usage above, a commit of rung 1b's
#: artifacts (24,098,988,333 B) was REFUSED. So the true limit is bracketed:
#:
#:     94,214,989,055  <=  LIMIT  <  118,313,977,388
#:
#: ⛔ Both ends are observations. The guard uses the LOW end, so it is correct
#: for any limit inside the bracket -- which is the point of recording a
#: bracket instead of picking a number inside it.
OBSERVED_REFUSED_BYTES = 118_313_977_388

#: ⭐ CALIBRATED against rung 1b's real upload: the tensor formula predicted
#: 24,087,429,120 B and the hub received 24,098,988,333 B across all files, a
#: ratio of **1.000480** (the safetensors header plus tokenizer.json and the
#: JSON sidecars). Rounded UP to 1% so the projection is never optimistic --
#: `PLANNER_IS_A_LOWER_BOUND`, the same discipline the VRAM floor uses.
OVERHEAD = 1.01


def projected_artifact_bytes(n_trainable: int, n_frozen: int, *,
                             master_bytes: int = 4, frozen_bytes: int = 2,
                             overhead: float = OVERHEAD) -> int:
    """How many bytes this run will hand the hub.

    ⭐ Derived from the SCOPE, not from a file that does not exist yet -- the
    whole value of this check is that it answers before training, when there is
    nothing on disk to measure.

    ⛔ The two dtypes are not decoration. §5 declares an fp32 master over the
    trainable parameters and leaves the frozen ones bf16, so a single
    `params * 2` would under-project a full-weight run by 40% and pass it
    straight into the wall this module exists to stop.
    """
    if n_trainable < 0 or n_frozen < 0:
        raise ValueError("parameter counts cannot be negative: %r / %r"
                         % (n_trainable, n_frozen))
    tensors = n_trainable * master_bytes + n_frozen * frozen_bytes
    return int(tensors * overhead)


def used_storage_bytes(repo: str, *, api) -> int:
    """Bytes the hub currently charges this repo, INCLUDING dead history.

    ⛔⛔ A MISSING VALUE RAISES; IT NEVER BECOMES ZERO. `used_storage` comes back
    `None` whenever the expand field is unavailable, and `or 0` there would
    report an empty repo -- the guard would pass, loudly and wrongly, in exactly
    the case where it could not see. A failed fetch records MISSING, never 0.

    ⚠️ AND IT IS NOT THE SUM OF THE CURRENT FILES. This repo's live files totalled
    50.72 GB while it was charged 94.21 GB: 43.49 GB was superseded LFS blobs from
    overwritten cells. Summing `siblings` -- the obvious implementation -- would
    have under-reported by 46% and admitted a run that cannot persist.

    ⛔⛔ AND THEN IT INVERTED, WHICH IS WHY THIS NOW TAKES THE MAXIMUM OF BOTH.
    On 2026-09-12 the live files totalled **90.43 GB** while `usedStorage`
    reported **68.88 GB** -- stale by exactly one 21.48 GB model, the cell that
    had just been pushed. The guard said a fourth run FITS (68.88 + 21.69 =
    90.57 against 94.21) when the truth was 90.43 + 21.69 = **112.12 GB**. It
    would have trained for ~62 minutes and died at `persist_leg1` on "storage
    limit reached" -- rung 1b''s exact death, for the second time.

    ⭐ SO NEITHER FIGURE IS SAFE ALONE, AND THEY FAIL IN OPPOSITE DIRECTIONS:

        usedStorage > live files    dead LFS history is being charged
        live files > usedStorage    the summary field has not caught up

    Two independent paths to one quantity; when they disagree, take the
    conservative one and SAY SO. A guard that reads one summary field is a guard
    that trusts a value it did not compute -- the recurring failure this project
    has now paid for at every level of the stack.
    """
    info = api.model_info(repo, expand=["usedStorage"])
    used = getattr(info, "used_storage", None)
    if used is None:
        raise RuntimeError(
            "%s did not report usedStorage. REFUSING to guess: an unmeasured "
            "quota is not an empty one, and treating it as 0 would pass every "
            "run precisely when this check has gone blind." % repo)
    live = live_file_bytes(repo, api=api)
    if live is None:
        # ⛔ Cannot cross-check. Fall back to the reported figure and say that
        # the second opinion is missing, rather than implying agreement.
        return int(used)
    return max(int(used), int(live))


def live_file_bytes(repo: str, *, api):
    """Sum of the repo's CURRENT files, or None if the listing is unavailable.

    ⭐ The second opinion for `used_storage_bytes`. Returns None rather than 0:
    an unreadable listing is not an empty repo.
    """
    try:
        info = api.repo_info(repo, files_metadata=True)
    except Exception:                                            # noqa: BLE001
        return None
    sibs = getattr(info, "siblings", None)
    if not sibs:
        return None
    total = 0
    for f in sibs:
        sz = getattr(f, "size", None)
        if not sz:
            lfs = getattr(f, "lfs", None)
            sz = (lfs.get("size") if isinstance(lfs, dict)
                  else getattr(lfs, "size", None)) or 0
        total += int(sz)
    return total


def check(used: int, projected: int, *,
          ceiling: int = PROVEN_ACCEPTED_BYTES) -> tuple[str, str]:
    """-> (verdict, why). ⭐ `why` is the whole postmortem, so it carries the
    arithmetic rather than a bare pass/fail."""
    after = used + projected
    gb = 1e9
    detail = ("used %.2f GB + projected %.2f GB = %.2f GB against a "
              "PROVEN-ACCEPTED ceiling of %.2f GB (a LOWER BOUND on the true "
              "limit, which the hub does not expose)"
              % (used / gb, projected / gb, after / gb, ceiling / gb))
    if after <= ceiling:
        return FITS, ("room for this run's artifacts: " + detail)
    return NO_ROOM, (
        "NO ROOM: " + detail + ". ⛔ Training would complete and then fail to "
        "persist, which spends the GPU hours and keeps nothing -- the failure "
        "this check exists to move to minute zero. Free space first (dead LFS "
        "history is charged too), then re-run this check.")
