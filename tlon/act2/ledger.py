"""THE RUN LEDGER, AND THE NO-TRANSCRIPT RULE MADE MECHANICAL — PREREG §5.6.

⛔⛔ THE RULE: no conversation transcript is read by any human until `ΔD`, `ΔC`,
the covariates and the ledger entry are computed and written.

A rule that lives in a document is a rule someone follows until the evening they
are curious. This project's standing move is to make the error UNEXPRESSABLE
rather than remembered against -- the way `Measurement.__sub__` refuses -- so the
transcript is returned SEALED. The machine may compute over it (leakage,
covariates, impressions); a human cannot read it until the ledger entry for that
run exists, and unsealing is itself recorded.

⭐ WHY THIS IS THE LOAD-BEARING PROCEDURE AND NOT MERE TIDINESS. Two models
talking will look alive. Once you have watched them chatter in Tlon you will see
drift whether it is there or not -- the human pattern-matcher is the
confabulation engine. Sealing the transcript until the number is banked is what
stops the number being chosen after the story.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parents[2] / "runs" / "act2"


class TranscriptSealed(RuntimeError):
    """A human tried to read a transcript before its result was banked."""


class LedgerError(RuntimeError):
    pass


@dataclass
class SealedTranscript:
    """A conversation the machine can measure and a person cannot yet read."""
    run_id: str
    _turns: tuple[str, ...]
    _impressions: tuple[str, ...]
    _stats: dict
    _unsealed_reason: str | None = field(default=None)

    # -- allowed while sealed: derived statistics, never the text -------
    def __len__(self) -> int:
        return len(self._turns)

    def impressions(self) -> frozenset[str]:
        """For the leakage check (F5). A set of digests is not a transcript."""
        return frozenset(self._impressions)

    def covariates(self) -> dict:
        """F4's pre-committed covariates. Numbers, not prose."""
        return dict(self._stats)

    @property
    def sealed(self) -> bool:
        return self._unsealed_reason is None

    # -- blocked while sealed ------------------------------------------
    @property
    def turns(self) -> tuple[str, ...]:
        self._check()
        return self._turns

    def text(self) -> str:
        self._check()
        return "\n".join(self._turns)

    def _check(self) -> None:
        if self.sealed:
            raise TranscriptSealed(
                f"run {self.run_id}: the transcript is SEALED until this run's "
                "result is in the ledger (PREREG §5.6). Compute ΔD, ΔC and the "
                "covariates, write the entry, then unseal(ledger, reason=...). "
                "Anything you notice in a transcript afterwards is EXPLORATORY "
                "and can never enter a verdict or a re-decomposition decision.")

    def unseal(self, ledger: "Ledger", *, reason: str) -> "SealedTranscript":
        """⛔ Requires the ledger entry to ALREADY EXIST. The check is on the
        written record, not on an intention to write one."""
        if not reason.strip():
            raise LedgerError("unsealing needs a written reason; it is recorded.")
        if not ledger.has(self.run_id):
            raise LedgerError(
                f"run {self.run_id} has no ledger entry. The result must be "
                "banked BEFORE the transcript is read -- that ordering is the "
                "entire protection against reading a story into the numbers.")
        ledger.note(self.run_id, event="unseal", reason=reason)
        self._unsealed_reason = reason
        return self


@dataclass
class Ledger:
    """Append-only JSONL. One line per run result, one per unsealing."""
    path: pathlib.Path = field(default_factory=lambda: ROOT / "ledger.jsonl")

    def _append(self, row: dict) -> dict:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row = dict(row, ts=_dt.datetime.now(_dt.timezone.utc)
                   .strftime("%Y-%m-%dT%H:%M:%SZ"))
        with self.path.open("a", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return row

    def rows(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(l) for l in
                self.path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def has(self, run_id: str) -> bool:
        return any(r.get("run_id") == run_id and r.get("event") == "result"
                   for r in self.rows())

    def record(self, run_id: str, *, arm: str, seed: int, axis: str,
               battery: str, prereg: str, **payload) -> dict:
        """⛔ `arm`, `seed`, `axis` and `battery` are required, not optional
        metadata: a result that does not say which arm it came from, over which
        battery, cannot be paired with anything later."""
        return self._append({"event": "result", "run_id": run_id, "arm": arm,
                             "seed": seed, "axis": axis, "battery": battery,
                             "prereg": prereg, **payload})

    def note(self, run_id: str, *, event: str, **payload) -> dict:
        return self._append({"event": event, "run_id": run_id, **payload})
