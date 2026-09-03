"""⛔⛔ THE PROVISIONER — launch, verified upload, train, verified download,
PERSIST BEFORE TERMINATE.

Red-proof: `tests/test_provision.py`, written before this module.

WHY IT EXISTS, STATED AS THE LOSS IT IS PREVENTING. `s20620` — one of the seven
builds the frozen cold table is computed over — existed only on a Lambda
instance. The recovery step in the runbook was

    scp -r ubuntu@<box>:~/tlon/runs/act2/adapter runs/act2/

and `runs/act2/adapter/` on this machine is an **empty directory, created
2026-08-24, never populated**. The copy made a folder, moved no file, said
nothing, and the instance was terminated. The adapter is gone: never in git
(weights are gitignored, so it was never committed to lose), not on HF, on no
disk here.

⭐ TWO GUARDS, AND THEY ARE THE WHOLE POINT OF THE MODULE:

  1. **Every transfer is verified by checksum computed on BOTH ends**, and a
     missing checksum is a failure rather than a match. An empty arrival and a
     transfer that was never requested look identical afterwards — so the check
     is on the SET of artifacts, not on the existence of a directory.
  2. **Termination is refused** while any artifact is not confirmed local AND
     confirmed in durable storage. Verified-local is not sufficient: a file on
     one laptop is one disk failure from the same loss.

⛔ `LAMBDA_API_KEY` is read from the environment and never logged.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess


class TransferError(RuntimeError):
    """A transfer that cannot be proven correct. ⛔ Raised, never warned — the
    caller's next step is either training on truncated input or terminating a
    box that still holds the only copy."""


def _is_checksum(v) -> bool:
    return isinstance(v, str) and len(v.strip()) >= 32


def verify_checksum(name: str, *, local, remote) -> None:
    """⛔⛔ A MISSING CHECKSUM IS A FAILURE, NOT A MATCH.

    Written the obvious way (`if local != remote: raise`), two absent values
    compare equal and the function certifies a transfer that never happened.
    That is the vacuous pass this project keeps finding, and here it would
    certify an empty file.
    """
    if not _is_checksum(local) or not _is_checksum(remote):
        raise TransferError(
            "%s: cannot verify — checksum missing on %s (local=%r remote=%r). "
            "An unverifiable transfer is a failed transfer."
            % (name, "both ends" if not _is_checksum(local)
               and not _is_checksum(remote) else
               ("this machine" if not _is_checksum(local) else "the box"),
               local, remote))
    if local.strip().lower() != remote.strip().lower():
        raise TransferError(
            "%s: CHECKSUM MISMATCH — box %s, here %s. The copy is corrupt or "
            "truncated; do not consume it and do not terminate."
            % (name, remote, local))


def verify_pulled_set(*, expected, found) -> None:
    """⛔⛔ THE CHECK WHOSE ABSENCE LOST s20620.

    Compares the SET of artifacts that arrived against the set that was asked
    for. `scp -r` of a directory that copies nothing leaves a directory, and a
    presence test on the directory passes. Only a set comparison catches it.
    """
    exp, got = set(expected), set(found)
    missing, extra = sorted(exp - got), sorted(got - exp)
    if missing:
        raise TransferError(
            "PULL INCOMPLETE — %d of %d artifacts did not arrive: %s. This is "
            "exactly how s20620 was lost: an empty directory and a directory "
            "nobody asked for look the same."
            % (len(missing), len(exp), ", ".join(missing)))
    if extra:
        raise TransferError(
            "unexpected artifacts arrived: %s. Something not asked for would "
            "enter the population and move the ruler." % ", ".join(extra))


def may_terminate(records) -> tuple[bool, str]:
    """-> (allowed, reason). ⛔⛔ NO ARTIFACT MAY EXIST ONLY ON A LIVE BOX.

    Every record must carry a name, matching box/local checksums, and a durable
    location. ⛔ An EMPTY record list is REFUSED: `all([])` is True, so the
    obvious implementation permits termination when nothing was tracked at all —
    which is precisely the state s20620 was lost in.
    """
    records = list(records)
    if not records:
        return False, ("no artifacts are tracked — refusing to terminate. An "
                       "empty ledger is indistinguishable from a run whose "
                       "outputs were never collected.")
    bad = []
    for i, r in enumerate(records):
        name = r.get("name")
        if not name:
            bad.append("record %d has no name" % i)
            continue
        if not _is_checksum(r.get("local_md5")):
            bad.append("%s is not on this machine" % name)
            continue
        if not _is_checksum(r.get("box_md5")):
            bad.append("%s has no box-side checksum to compare against" % name)
            continue
        if r["local_md5"].strip().lower() != r["box_md5"].strip().lower():
            bad.append("%s checksum mismatch (box %s / here %s)"
                       % (name, r["box_md5"], r["local_md5"]))
            continue
        if not r.get("durable_uri"):
            bad.append("%s is verified-local but NOT in durable storage" % name)
    if bad:
        return False, ("REFUSING TO TERMINATE — %d problem(s): %s"
                       % (len(bad), "; ".join(bad)))
    return True, "all %d artifacts verified local and persisted" % len(records)


# ── the real world ──────────────────────────────────────────────────────────

def md5_local(path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ssh(host, key, cmd, *, check=True) -> str:
    out = subprocess.run(
        ["ssh", "-i", str(key), "-o", "StrictHostKeyChecking=accept-new",
         "ubuntu@%s" % host, cmd],
        capture_output=True, text=True)
    if check and out.returncode != 0:
        raise TransferError("ssh failed (%d): %s" % (out.returncode, out.stderr))
    return out.stdout.strip()


def md5_remote(host, key, path) -> str:
    """⛔ Computed ON THE BOX, before anything is pulled. A checksum taken after
    the copy, from the copy, verifies the copy against itself."""
    return ssh(host, key, "md5sum %s | cut -d' ' -f1" % path)


def _api(path, payload=None, method="POST"):
    """⛔ `LAMBDA_API_KEY` read from env, never logged, never echoed."""
    import urllib.request
    key = os.environ.get("LAMBDA_API_KEY")
    if not key:
        raise RuntimeError("LAMBDA_API_KEY is not set")
    req = urllib.request.Request(
        "https://cloud.lambdalabs.com/api/v1/" + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": "Bearer %s" % key,
                 "Content-Type": "application/json"},
        method=method)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def launch(instance_type="gpu_1x_a100", region="us-west-1",
           ssh_key_name="tlon", name="tlon-retrain"):
    return _api("instance-operations/launch",
                {"region_name": region, "instance_type_name": instance_type,
                 "ssh_key_names": [ssh_key_name], "name": name})


def instances():
    return _api("instances", method="GET")


def terminate(instance_id, records):
    """⛔⛔ GATED. The persistence check runs HERE, not in the caller, so no code
    path can terminate without passing it."""
    ok, why = may_terminate(records)
    if not ok:
        raise TransferError(why)
    return _api("instance-operations/terminate",
                {"instance_ids": [instance_id]})


def record(name, *, local_path, host, key, remote_path, durable_uri=None):
    """Build one ledger entry, checksumming both ends."""
    box = md5_remote(host, key, remote_path)
    loc = md5_local(local_path) if pathlib.Path(local_path).exists() else None
    verify_checksum(name, local=loc, remote=box)
    return {"name": name, "local_md5": loc, "box_md5": box,
            "local_path": str(local_path), "remote_path": remote_path,
            "durable_uri": durable_uri}


# ── durable persistence, verified ───────────────────────────────────────────

def _hf_token():
    """⛔ Read from the env file, never logged, never returned to a caller that
    prints it."""
    import re
    for cand in (os.environ.get("HF_TOKEN"),):
        if cand:
            return cand
    env = pathlib.Path(r"D:\physics_detector\.env")
    if env.exists():
        m = re.search(r"^HF_TOKEN=(.+)$", env.read_text(encoding="utf-8",
                                                        errors="replace"), re.M)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    raise RuntimeError("no HF_TOKEN available")


def sha256_local(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def push_durable(name, local_path, repo, *, private=True, subdir=None):
    """Upload one adapter and VERIFY IT ARRIVED INTACT.

    ⛔⛔ AN UPLOAD THAT RETURNS 200 IS NOT A VERIFIED UPLOAD. The hub reports the
    LFS sha256 of what it actually stored; this compares that against the sha256
    of the bytes on disk. Without the comparison, "persisted" means "the call did
    not raise", which is the same standard that lost s20620.
    """
    from huggingface_hub import HfApi
    api = HfApi(token=_hf_token())
    api.create_repo(repo, private=private, exist_ok=True)
    src = pathlib.Path(local_path)
    dest = "%s/%s" % (subdir or name, src.name)
    if already_persisted(api, repo, dest, sha256_local(src)):
        return "hf://%s/%s" % (repo, dest)
    api.upload_file(path_or_fileobj=str(src), path_in_repo=dest,
                    repo_id=repo, commit_message="persist %s" % name)
    want = sha256_local(src)
    info = api.model_info(repo, files_metadata=True)
    got = None
    for s in info.siblings:
        if s.rfilename == dest and s.lfs:
            got = s.lfs.get("sha256")
    if got is None:
        # ⛔ SMALL FILES ARE NOT LFS, so the hub reports no sha256 for them.
        # That is not permission to skip verification — it is a different
        # verification: pull the stored bytes back and hash them. A file too
        # small to be worth checking is exactly the kind that goes missing
        # without anyone noticing.
        from huggingface_hub import hf_hub_download
        back = hf_hub_download(repo, dest, token=_hf_token(),
                               force_download=True)
        got = sha256_local(back)
    if got.lower() != want.lower():
        raise TransferError("%s: HUB CHECKSUM MISMATCH for %s (hub %s / local "
                            "%s) — the stored copy is not what was sent"
                            % (name, dest, got, want))
    return "hf://%s/%s" % (repo, dest)


def already_persisted(api, repo, dest, want_sha):
    """⭐ Skip a re-upload only when the hub ALREADY holds the exact bytes.
    Verified skip, never assumed skip."""
    try:
        info = api.model_info(repo, files_metadata=True)
    except Exception:
        return False
    for s in info.siblings:
        if s.rfilename == dest and s.lfs:
            return (s.lfs.get("sha256") or "").lower() == want_sha.lower()
    return False
