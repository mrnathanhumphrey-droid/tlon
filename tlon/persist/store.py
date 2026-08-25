"""Two lifetimes on one volume: an append-only ledger, and disposable forks.

Persistent storage makes the counter a real continuous record instead of a
per-run fiction -- but it also makes experiments non-comparable if run N's
repetition log carries state from run N-1. You cannot A/B lambda against a
moving history.

So the same data gets two lifetimes:

    ledger/       append-only, lifetime-scoped, IMMUTABLE. The product and
                  audit artefact. Snapshots are content-addressed, so a
                  snapshot id IS its hash and overwriting is meaningless.
    experiments/  forked from a NAMED ledger snapshot, disposable, and
                  structurally unable to write back.

Every experiment records the snapshot it forked from, so two runs can always be
shown to have started from identical history -- or shown not to have.

Windows note: every write pins newline="" so file bytes match the bytes hashed.
Without it \\n becomes \\r\\n and content addressing silently breaks.
"""
from __future__ import annotations
import datetime as _dt
import hashlib
import json
import pathlib
import shutil
from dataclasses import dataclass

from ..novelty.centroids import RepetitionLog


class LedgerError(RuntimeError):
    pass


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _dump(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _hash(text: str) -> str:
    return hashlib.blake2b(text.encode("utf-8"), digest_size=16).hexdigest()


def _write(path: pathlib.Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


@dataclass
class Experiment:
    run_id: str
    root: pathlib.Path
    forked_from: str

    @property
    def audit_path(self) -> pathlib.Path:
        return self.root / "audit.db"

    @property
    def log_path(self) -> pathlib.Path:
        return self.root / "repetition.json"

    def load_log(self) -> RepetitionLog:
        return RepetitionLog.from_dict(
            json.loads(self.log_path.read_text(encoding="utf-8")))

    def save_log(self, log: RepetitionLog) -> None:
        _write(self.log_path, _dump(log.to_dict()))


class Store:
    def __init__(self, root: str | pathlib.Path):
        self.root = pathlib.Path(root)
        self.snapshots = self.root / "ledger" / "snapshots"
        self.manifest = self.root / "ledger" / "MANIFEST.jsonl"
        self.experiments = self.root / "experiments"
        self.snapshots.mkdir(parents=True, exist_ok=True)
        self.experiments.mkdir(parents=True, exist_ok=True)
        if not self.manifest.exists():
            _write(self.manifest, "")

    @property
    def ledger_audit(self) -> pathlib.Path:
        return self.root / "ledger" / "audit.db"

    # ── ledger ─────────────────────────────────────────────────────────────
    def snapshot(self, log: RepetitionLog, note: str = "") -> str:
        """Content-address a repetition log into the ledger. Idempotent: the
        same log snapshotted twice yields one file and one id."""
        body = _dump(log.to_dict())
        sid = _hash(body)
        path = self.snapshots / f"{sid}.json"
        if path.exists():
            if path.read_text(encoding="utf-8") != body:
                raise LedgerError(f"snapshot {sid} exists with different content")
            return sid
        _write(path, body)
        with self.manifest.open("a", encoding="utf-8", newline="") as fh:
            fh.write(_dump({"snapshot_id": sid, "created_at": _utcnow(),
                            "note": note, "buckets": len(log.buckets),
                            "medoids": log.total_medoids(), "seq": log.seq}) + "\n")
        return sid

    def read_snapshot(self, sid: str) -> RepetitionLog:
        path = self.snapshots / f"{sid}.json"
        if not path.exists():
            raise LedgerError(f"no snapshot {sid}")
        body = path.read_text(encoding="utf-8")
        if _hash(body) != sid:
            raise LedgerError(
                f"snapshot {sid} FAILED verification — content hash is "
                f"{_hash(body)}. The ledger has been altered.")
        return RepetitionLog.from_dict(json.loads(body))

    def verify(self) -> list[str]:
        """Re-hash every snapshot. Returns the ids that no longer match."""
        bad = []
        for p in sorted(self.snapshots.glob("*.json")):
            if _hash(p.read_text(encoding="utf-8")) != p.stem:
                bad.append(p.stem)
        return bad

    def history(self) -> list[dict]:
        text = self.manifest.read_text(encoding="utf-8")
        return [json.loads(ln) for ln in text.splitlines() if ln.strip()]

    # ── experiments ────────────────────────────────────────────────────────
    def fork(self, snapshot_id: str, run_id: str, *,
             overwrite: bool = False) -> Experiment:
        log = self.read_snapshot(snapshot_id)     # verifies before copying
        d = self.experiments / run_id
        if d.exists():
            if not overwrite:
                raise LedgerError(f"experiment {run_id} already exists")
            shutil.rmtree(d)
        d.mkdir(parents=True)
        exp = Experiment(run_id=run_id, root=d, forked_from=snapshot_id)
        _write(d / "forked_from.json",
               _dump({"snapshot_id": snapshot_id, "run_id": run_id,
                      "forked_at": _utcnow()}))
        exp.save_log(log)
        return exp

    def open_experiment(self, run_id: str) -> Experiment:
        d = self.experiments / run_id
        meta = json.loads((d / "forked_from.json").read_text(encoding="utf-8"))
        return Experiment(run_id=run_id, root=d,
                          forked_from=meta["snapshot_id"])

    def same_origin(self, *run_ids: str) -> bool:
        """Were these experiments forked from identical history? If not, any
        A/B between them is confounded by the history they started with."""
        origins = {self.open_experiment(r).forked_from for r in run_ids}
        return len(origins) == 1

    def promote(self, exp: Experiment, note: str = "") -> str:
        """Fold a finished experiment's log back into the ledger as a NEW
        snapshot. The only sanctioned path from experiment to ledger, and it
        appends rather than mutating."""
        return self.snapshot(exp.load_log(), note=note or f"promoted {exp.run_id}")
