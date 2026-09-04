"""⛔⛔ BOX-SIDE PERSISTENCE — the stage that makes `~/DONE` mean PERSISTED.

Red-proof: `tests/test_box_persist.py`.

WHY IT EXISTS, STATED AS THE LOSS IT IS PREVENTING. On 2026-09-04 two boxes
self-terminated with work still on them. `retrain12` **succeeded**, wrote
`~/DONE`, and its own watchdog terminated it within one 300 s poll — taking 84
solo transcripts and the run log. The gate box failed at the `manifest` stage
with a trained, F-LOCAL-cleared adapter sitting on disk, and the watchdog's
process-is-gone branch terminated it too.

⭐ THE DIAGNOSIS IS NOT "THE WATCHDOG IS TOO EAGER". Both terminations were
correct: one run had finished and one had died, and in both cases the box was
billing for nothing. The defect is that **`~/DONE` meant COMPUTED while the
collection it implied lived on another machine**, so every run had a five-minute
window in which the only copy of the work sat on a box that was already trying
to end itself. Two systems had to agree about something neither of them modelled.

⭐ THE FIX REMOVES THE DISAGREEMENT rather than adding a check to one side. The
box pushes its own artifacts to durable storage as a PIPELINE STAGE, and
`~/DONE` is written after that stage. Then terminate-on-DONE is correct instead
of dangerous, the watchdog needs no concept of persistence, and the laptop-side
`collect` becomes a convenience rather than the only path off the box.

⭐ AND IT RUNS PER-ADAPTER, INSIDE THE LOOP. A single persist stage at the end
would still have lost the gate adapter, because the stage that failed sat
BETWEEN the last adapter and the end. Work becomes durable as soon as it exists.

⛔ `HF_TOKEN` is read from the environment (the pipeline sources `~/.tlon_env`)
and is never logged.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tarfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from act2_provision import (TransferError, push_durable,  # noqa: E402
                            sha256_local)

LEDGER = "persist_ledger.json"

#: Files that make an adapter an adapter. ⛔ `factorial.json` is in the REQUIRED
#: set on purpose: an adapter that survives without its cell label is an adapter
#: in no cell of the factorial — the caveat-in-the-name failure with the caveat
#: deleted rather than merely misplaced.
CELL_FILES = ("adapter_model.safetensors", "adapter_config.json",
              "factorial.json")

#: ⛔⛔ The corpus manifest, under a name that cannot collide with the run's
#: ADAPTER manifest. It records the recipe lag profile the model is compared
#: against — the gate run persisted everything except this and nearly lost it.
CORPUS_MANIFEST = "corpus_manifest.json"

#: What `verify` demands before `~/DONE` may be written. ⭐ Strictly wider than
#: CELL_FILES: an adapter without its corpus provenance is a model with no
#: measurement behind it.
REQUIRED_PERSISTED = CELL_FILES + (CORPUS_MANIFEST,)


def ledger_path(root) -> pathlib.Path:
    return pathlib.Path(root) / LEDGER


def read_ledger(root) -> dict:
    p = ledger_path(root)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def write_ledger(root, led) -> None:
    """⛔ Written to a temp file and replaced. A crash midway through a text
    write leaves a truncated ledger, and a truncated ledger reads as "these
    artifacts were never persisted" — which sends the next run re-uploading or,
    worse, re-training."""
    p = ledger_path(root)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(led, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(p)


def solo_logs(root, cell) -> list:
    return sorted((pathlib.Path(root) / "logs").glob("%s_solo_*.json" % cell))


def tar_solo(root, cell, out_path) -> pathlib.Path:
    """Bundle one cell's transcripts into a single deterministic archive.

    ⛔ Fourteen separate uploads per cell is fourteen chances to half-finish.
    One archive is one artifact with one checksum, which is the only shape
    `push_durable` can actually verify.

    ⭐ Deterministic: sorted names, mtime zeroed, ownership stripped. The
    archive's sha256 is then a function of the transcripts alone, so re-running
    the stage is a VERIFIED SKIP rather than a second upload.

    ⛔ ZEROING THE TAR ENTRIES IS NOT ENOUGH — the GZIP HEADER carries its own
    mtime and the source filename, so `tarfile.open(..., "w:gz")` produces
    different bytes every run and `already_persisted` never fires. The gzip
    stream is built explicitly for that reason.
    """
    import gzip
    files = solo_logs(root, cell)
    out_path = pathlib.Path(out_path)
    with open(out_path, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0,
                           compresslevel=6) as gz:
            with tarfile.open(fileobj=gz, mode="w") as tf:
                for f in files:
                    ti = tf.gettarinfo(str(f), arcname=f.name)
                    ti.mtime, ti.uid, ti.gid = 0, 0, 0
                    ti.uname = ti.gname = ""
                    with open(f, "rb") as fh:
                        tf.addfile(ti, fh)
    return out_path


def tar_tree(src_dir, out_path, *, suffix=".json", prefix=None) -> tuple:
    """Bundle a directory of result files deterministically. -> (path, n).

    ⭐ The generic form of `tar_solo`, for pipelines whose output is transcripts
    rather than adapters. `pipeline_positive_control.sh` is one: it self-
    terminates on `~/DONE` exactly like `pipeline_retrain.sh` did, and its own
    header records that its throughput log "has been lost to a kill once
    already". Same class, same fix.
    """
    import gzip
    src_dir = pathlib.Path(src_dir)
    # ⭐ `prefix` lets a run persist ONE build's transcripts at a time out of a
    # flat directory. Per-build beats end-of-run for the same reason the retrain
    # pipeline persists inside its loop: a crash on build 4 must not cost 1-3.
    files = sorted(p for p in src_dir.rglob("*" + suffix)
                   if p.is_file() and (prefix is None
                                       or p.name.startswith(prefix)))
    out_path = pathlib.Path(out_path)
    with open(out_path, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0,
                           compresslevel=6) as gz:
            with tarfile.open(fileobj=gz, mode="w") as tf:
                for f in files:
                    ti = tf.gettarinfo(str(f),
                                       arcname=str(f.relative_to(src_dir)))
                    ti.mtime, ti.uid, ti.gid = 0, 0, 0
                    ti.uname = ti.gname = ""
                    with open(f, "rb") as fh:
                        tf.addfile(ti, fh)
    return out_path, len(files)


def missing_cell_files(root, cell) -> list:
    d = pathlib.Path(root) / ("adapter_%s" % cell)
    return [n for n in CELL_FILES if not (d / n).exists()]


def persist_cell(root, cell, repo, *, solo_n, corpus_manifest,
                 push=push_durable) -> dict:
    """Push one cell's artifacts, verifying each arrival. -> the ledger entry.

    ⛔⛔ `solo_n` IS A PARAMETER, NOT A CONSTANT. The count comes from the
    pipeline's own `N_PER_BUILD`. A literal here would be right for the batch it
    was written against and silently wrong for a gate run — which is precisely
    the defect that killed the gate box (`assert len(out) == 6` in the `manifest`
    stage), and this module is the stage that replaces it.
    """
    root = pathlib.Path(root)
    d = root / ("adapter_%s" % cell)
    miss = missing_cell_files(root, cell)
    if miss:
        raise TransferError(
            "%s: refusing to persist an incomplete cell — missing %s. A partial "
            "adapter in durable storage is worse than none: it reads as saved."
            % (cell, ", ".join(miss)))

    logs = solo_logs(root, cell)
    if len(logs) != solo_n:
        raise TransferError(
            "%s: expected %d solo transcripts, found %d. The frozen ruler is "
            "computed over the full set, so a short set would enter the "
            "population as if it were complete." % (cell, solo_n, len(logs)))

    # ⛔⛔ THE CORPUS MANIFEST IS REQUIRED, NOT OPTIONAL. The gate run persisted
    # weights, config, cell label, transcripts and its run log — and NOT the
    # corpus manifest, which carries the corpus's own recipe lag profile: the
    # comparison quantity for the whole read. It was noticed with the box already
    # terminating and the pull returned 0 bytes. That time it was recoverable by
    # deterministic rebuild, and rebuild-plus-sha-check is a fine RECOVERY but a
    # bad PLAN: it works only while the corpus is deterministic and its sha was
    # written down. ⭐ A keyword with no default, so the gap cannot reopen by
    # someone forgetting an argument.
    cm = pathlib.Path(corpus_manifest)
    if not cm.exists():
        raise TransferError(
            "%s: corpus manifest %s does not exist. It records what this "
            "adapter was actually trained on; persisting the adapter without it "
            "saves the model and loses the measurement it is compared against."
            % (cell, cm))

    entry = {"cell": cell, "files": {}, "solo_n": len(logs),
             "persisted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                            time.gmtime())}
    # ⛔ Copied to a DISTINCT name first. `push_durable` derives the destination
    # from the source filename, and the corpus manifest is called `manifest.json`
    # — the same name as the run's ADAPTER manifest. Two different manifests
    # under one name in one prefix is the ambiguous-name failure, and the one
    # that would be overwritten is the provenance.
    named = pathlib.Path(root) / ("%s_corpus_manifest.json" % cell)
    named.write_bytes(cm.read_bytes())
    entry["files"][CORPUS_MANIFEST] = {
        "sha256": sha256_local(named), "bytes": named.stat().st_size,
        "uri": push(cell, named, repo, private=True, subdir=cell)}
    for fn in CELL_FILES:
        f = d / fn
        entry["files"][fn] = {"sha256": sha256_local(f),
                              "bytes": f.stat().st_size,
                              "uri": push(cell, f, repo, private=True,
                                          subdir=cell)}
    tarball = tar_solo(root, cell, root / ("%s_solo_logs.tar.gz" % cell))
    entry["files"][tarball.name] = {
        "sha256": sha256_local(tarball), "bytes": tarball.stat().st_size,
        "uri": push(cell, tarball, repo, private=True, subdir=cell)}

    # ⛔⛔ ASSERT THE MUTATION, NOT THE CALL. `push_durable` verifies the hub's
    # checksum, but a push that returned None — or a loop that skipped a file —
    # leaves an entry that still READS as a record of success. A silent no-op and
    # a silent success are the same observation unless something checks.
    for fn, meta in entry["files"].items():
        if not meta.get("uri"):
            raise TransferError("%s: %s reported no durable URI after upload"
                                % (cell, fn))
    led = read_ledger(root)
    led[cell] = entry
    write_ledger(root, led)
    return entry


def persist_file(root, path, repo, *, subdir, push=push_durable) -> str:
    """Push one run-level file (the pipeline log, the manifest)."""
    p = pathlib.Path(path)
    if not p.exists():
        raise TransferError("%s does not exist — nothing to persist" % p)
    uri = push(p.name, p, repo, private=True, subdir=subdir)
    if not uri:
        raise TransferError("%s reported no durable URI after upload" % p.name)
    led = read_ledger(root)
    led.setdefault("_run_files", {})[p.name] = {
        "sha256": sha256_local(p), "bytes": p.stat().st_size, "uri": uri}
    write_ledger(root, led)
    return uri


def unpersisted(root, cells) -> list:
    """-> the cells NOT fully recorded in the ledger.

    ⛔ Membership is not enough. An entry missing any required file is not
    persisted, so the ledger is checked against `CELL_FILES` rather than against
    its own key set — otherwise a half-written entry certifies itself.
    """
    led = read_ledger(root)
    out = []
    for c in cells:
        e = led.get(c)
        if not e:
            out.append(c)
            continue
        files = e.get("files", {})
        if any(not files.get(fn, {}).get("uri") for fn in REQUIRED_PERSISTED):
            out.append(c)
    return out


def cmd_cell(a):
    e = persist_cell(a.root, a.cell, a.repo, solo_n=a.solo_n,
                     corpus_manifest=a.corpus_manifest)
    print("  ✅ %s persisted: %d files + %d solo transcripts"
          % (a.cell, len(e["files"]) - 1, e["solo_n"]))
    for fn, m in sorted(e["files"].items()):
        print("     %-32s %s" % (fn, m["uri"]))
    return 0


def cmd_file(a):
    print("  ✅ %s -> %s" % (pathlib.Path(a.path).name,
                            persist_file(a.root, a.path, a.repo,
                                         subdir=a.subdir)))
    return 0


def cmd_verify(a):
    """⛔⛔ THE GATE THE PIPELINE RUNS BEFORE `touch ~/DONE`.

    This is the whole point of the module. `~/DONE` is a claim that the run's
    output is safe, and until this exits 0 that claim is false.
    """
    cells = a.cells.split()
    if not cells:
        # ⛔ `all([])` is True. An empty cell list must REFUSE, or a pipeline
        # whose seed list failed to expand certifies a run with no output — the
        # same vacuous pass `may_terminate` refuses on an empty ledger.
        print("⛔⛔ no cells named — refusing to certify an empty run",
              file=sys.stderr)
        return 1
    bad = unpersisted(a.root, cells)
    if bad:
        print("⛔⛔ NOT PERSISTED: %s — refusing to mark the run done"
              % ", ".join(bad), file=sys.stderr)
        return 1
    print("  ✅ all %d cells verified in durable storage" % len(cells))
    return 0


def cmd_flush(a):
    """⛔⛔ LAST WORDS — called by the watchdog before it terminates.

    A box being killed for a stall or a dead process still holds its run log,
    the record of WHY, which is the one artifact that re-running cannot
    regenerate. `retrain12/pipeline_retrain.log` was lost exactly this way.

    ⭐ Best-effort BY DESIGN, and loud about it. This runs on a box already being
    terminated for cost; a flush that raised and aborted the shutdown would turn
    a bounded failure into an unbounded bill. Every failure is printed and the
    exit code stays 0 so the terminate proceeds.
    """
    root = pathlib.Path(a.root)
    for p in (root / "pipeline_retrain.log", root / "manifest.json",
              root / "watchdog.log"):
        if not p.exists():
            continue
        try:
            print("  flushed %s -> %s"
                  % (p.name, persist_file(root, p, a.repo, subdir=root.name)))
        except Exception as e:                                  # noqa: BLE001
            print("  ⛔ flush FAILED for %s: %s: %s"
                  % (p.name, type(e).__name__, e), file=sys.stderr)
    return 0


def cmd_tree(a):
    """Persist a directory of result files as one verified archive.

    ⛔ REFUSES AN EMPTY TREE. An archive of nothing uploads successfully, and a
    successful upload of nothing is the most convincing form of a lost run.
    """
    root = pathlib.Path(a.root)
    out, n = tar_tree(root / a.dir if a.dir else root,
                      root / ("%s.tar.gz" % a.name), suffix=a.suffix,
                      prefix=a.prefix)
    if n == 0:
        print("⛔⛔ %s holds no %s files matching %r — refusing to persist an "
              "empty archive" % (a.dir or a.root, a.suffix, a.prefix or "*"),
              file=sys.stderr)
        return 1
    if a.expect is not None and n != a.expect:
        # ⛔ A count that is a PARAMETER, never a batch size in the code.
        print("⛔⛔ archived %d files, expected %d — refusing to persist a set "
              "that is not the set that was asked for" % (n, a.expect),
              file=sys.stderr)
        return 1
    print("  ✅ %d files -> %s"
          % (n, persist_file(root, out, a.repo, subdir=root.name)))
    return 0


#: `snapshot_download(local_dir=...)` writes its own bookkeeping under
#: `.cache/huggingface/` — a `.gitignore`, a `CACHEDIR.TAG`, and one
#: `<file>.metadata` per download.
HUB_BOOKKEEPING = ".cache"


def restored_files(root) -> list:
    """-> the ARTIFACTS a restore produced, excluding the hub's own bookkeeping.

    ⛔⛔ COUNTING THE CACHE MAKES THE EMPTINESS GUARD ACCIDENTAL. A restore of 5
    tarballs reported "12 files" — the other 7 were `.cache/huggingface/`
    entries. Today a zero-match pattern happens to write no cache either, so the
    guard fires; but it fires because of how the library behaves this week, not
    because of anything this code checks. ⭐ A guard that is right by coincidence
    is indistinguishable from one that is right, until the coincidence ends.

    ⛔ And the count is reported to a human deciding whether a recovery worked.
    A number that includes bookkeeping is a caveat living in prose instead of in
    the quantity.
    """
    root = pathlib.Path(root)
    return sorted(f.relative_to(root).as_posix()
                  for f in root.rglob("*")
                  if f.is_file()
                  and HUB_BOOKKEEPING not in f.relative_to(root).parts)


def cmd_restore(a):
    """⛔⛔ THE RECOVERY PATH, WRITTEN DOWN AND RUNNABLE.

    The box persists as it goes, so a terminated box no longer costs the work —
    but only if getting it back is a command rather than a plan. `s20620`'s
    recovery step was a runbook line nobody had ever executed, and when it was
    finally run it made an empty directory and said nothing.

    ⭐ `snapshot_download` verifies each file's hash against the hub's record, so
    an incomplete restore raises here instead of arriving quietly.
    """
    from huggingface_hub import snapshot_download
    from act2_provision import _hf_token
    dest = pathlib.Path(a.into)
    dest.mkdir(parents=True, exist_ok=True)
    p = snapshot_download(a.repo, token=_hf_token(), local_dir=str(dest),
                          allow_patterns=[a.pattern] if a.pattern else None)
    got = restored_files(p)
    if not got:
        print("⛔⛔ RESTORED NOTHING from %s (pattern %r). An empty directory "
              "and a directory nobody asked for look identical afterwards — "
              "which is how s20620 was lost." % (a.repo, a.pattern),
              file=sys.stderr)
        return 1
    print("  ✅ restored %d files into %s" % (len(got), p))
    for n in got[:40]:
        print("     %s" % n)
    return 0


def cmd_probe(a):
    """⛔⛔ PROVE THE PERSIST PATH AT PROVISION TIME, NOT AT THE END OF THE RUN.

    Persistence is now a stage this pipeline cannot finish without. A token that
    is absent, read-only, or scoped to the wrong repo would therefore be
    discovered after the GPU time is already spent — which is the same shape as
    a watchdog that finds out it cannot terminate at the moment it needs to.
    `terminate_reachable()` exists for exactly that reason on the kill path;
    this is its counterpart on the save path.

    ⭐ It writes, and verifies the write. A read-only token passes a read probe.
    """
    root = pathlib.Path(a.root)
    root.mkdir(parents=True, exist_ok=True)
    p = root / "_persist_probe.txt"
    p.write_text("persist path probed %s\n"
                 % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 encoding="utf-8")
    uri = push_durable("_probe", p, a.repo, private=True,
                       subdir="_provision_probe")
    if not uri:
        print("⛔⛔ the persist probe returned no URI", file=sys.stderr)
        return 1
    print("  ✅ persist path verified writable: %s" % uri)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="keyzersoze04/tlon-act2-adapters")
    ap.add_argument("--root", required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("cell"); q.set_defaults(fn=cmd_cell)
    q.add_argument("--cell", required=True)
    # ⛔ REQUIRED, NO DEFAULT. The transcript count per build is the pipeline's
    # N_PER_BUILD; defaulting it here would put a batch size back into the code.
    q.add_argument("--solo-n", type=int, required=True)
    # ⛔ REQUIRED, NO DEFAULT — the gap the gate run found. An adapter persisted
    # without its corpus provenance is a model with no measurement behind it.
    q.add_argument("--corpus-manifest", required=True,
                   help="path to the corpus manifest this adapter trained on")
    q = sub.add_parser("file"); q.set_defaults(fn=cmd_file)
    q.add_argument("--path", required=True)
    q.add_argument("--subdir", required=True)
    q = sub.add_parser("verify"); q.set_defaults(fn=cmd_verify)
    q.add_argument("--cells", required=True,
                   help="space-separated cell labels, e.g. 'ct-s20624'")
    q = sub.add_parser("tree"); q.set_defaults(fn=cmd_tree)
    q.add_argument("--dir", default=None, help="subdirectory of --root")
    q.add_argument("--name", required=True, help="archive basename")
    q.add_argument("--suffix", default=".json")
    q.add_argument("--prefix", default=None,
                   help="only files whose name starts with this, e.g. 's20624_'")
    q.add_argument("--expect", type=int, default=None,
                   help="refuse unless exactly this many files are archived")
    q = sub.add_parser("restore"); q.set_defaults(fn=cmd_restore)
    q.add_argument("--into", required=True)
    q.add_argument("--pattern", default=None,
                   help="e.g. 'ct-s20624/*' to restore one cell")
    q = sub.add_parser("flush"); q.set_defaults(fn=cmd_flush)
    q = sub.add_parser("probe"); q.set_defaults(fn=cmd_probe)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
