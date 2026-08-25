"""Referent-keyed repetition log: bounded, decaying, and checkpointable.

Not raw verbatim history -- each bucket keeps a small rolling set of medoids
with a recency weight, so the log stays bounded however long the system runs.

MEDOIDS, NOT CENTROIDS. You cannot average two event graphs; there is no mean
scene. Each cluster is therefore represented by an ACTUAL scene that was really
uttered, which has the side benefit that every entry in the log is auditable
rather than synthetic.

BUCKETS KEY ON THE GROUND-TRUTH REFERENT (flag ③). In self-play we generated
the referent, so we have it. Keying on a listener's inference of the output
would let the generator cut R by shifting how it gets bucketed rather than by
having a new impression -- novelty for free.

DECAY RUNS ON SEQUENCE NUMBER, NOT WALL CLOCK. Deterministic, so a run replays
identically and two experiments forked from the same ledger snapshot are
comparable.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field

from ..grammar.canon import canon_json, utterance_id
from ..grammar.parse import Scene, parse
from . import distance as D


@dataclass
class Medoid:
    scene: Scene
    surface: str
    uid: str
    weight: float          # undecayed mass at last_seen
    last_seen: int         # sequence number
    hits: int = 1

    def decayed(self, now: int, half_life: float) -> float:
        if half_life <= 0:
            return self.weight
        return self.weight * math.pow(0.5, (now - self.last_seen) / half_life)


@dataclass
class Bucket:
    key: str
    medoids: list[Medoid] = field(default_factory=list)

    def live(self, now: int, half_life: float, floor: float) -> list[tuple[Medoid, float]]:
        out = [(m, m.decayed(now, half_life)) for m in self.medoids]
        return [(m, w) for m, w in out if w >= floor]


@dataclass
class RepetitionLog:
    """One bounded, decaying log per referent bucket."""
    k_per_bucket: int = 8
    half_life: float = 64.0        # in accepted utterances
    weight_floor: float = 0.02     # below this a medoid is dead and evictable
    buckets: dict[str, Bucket] = field(default_factory=dict)
    seq: int = 0

    # ── query ──────────────────────────────────────────────────────────────
    def score(self, bucket_key: str, scene: Scene) -> dict:
        """Novelty cost of saying `scene` about `bucket_key`, right now.

        Nearest live medoid only, scaled by that medoid's decay weight -- the
        shape the brief specifies. Cost is high when the new scene is CLOSE to
        something recently said, which is what repetition means.
        """
        b = self.buckets.get(bucket_key)
        live = b.live(self.seq, self.half_life, self.weight_floor) if b else []
        if not live:
            return {"nearest_dist": None, "decay_weight": None,
                    "novelty_cost": 0.0, "nearest_uid": None}
        best_m, best_w, best_d = None, 0.0, None
        for m, w in live:
            d = D.normalized(scene, m.scene)
            if best_d is None or d < best_d:
                best_m, best_w, best_d = m, w, d
        cost = max(0.0, min(1.0, best_w * (1.0 - best_d)))
        return {"nearest_dist": best_d, "decay_weight": best_w,
                "novelty_cost": cost, "nearest_uid": best_m.uid}

    # ── update ─────────────────────────────────────────────────────────────
    def observe(self, bucket_key: str, scene: Scene, surface: str) -> None:
        """Fold an ACCEPTED utterance into the log. Advances the clock."""
        self.seq += 1
        b = self.buckets.setdefault(bucket_key, Bucket(key=bucket_key))
        uid = utterance_id(scene)

        nearest, nd = None, None
        for m in b.medoids:
            d = D.normalized(scene, m.scene)
            if nd is None or d < nd:
                nearest, nd = m, d

        # An exact canonical repeat reinforces its medoid rather than adding one.
        if nearest is not None and (nearest.uid == uid or nd == 0.0):
            nearest.weight = nearest.decayed(self.seq, self.half_life) + 1.0
            nearest.last_seen = self.seq
            nearest.hits += 1
            return

        b.medoids.append(Medoid(scene=scene, surface=surface, uid=uid,
                                weight=1.0, last_seen=self.seq))
        self._evict(b)

    def _evict(self, b: Bucket) -> None:
        while len(b.medoids) > self.k_per_bucket:
            b.medoids.sort(key=lambda m: (m.decayed(self.seq, self.half_life),
                                          m.last_seen))
            b.medoids.pop(0)

    def sweep(self) -> int:
        """Drop medoids that have decayed below the floor. Returns how many."""
        n = 0
        for b in self.buckets.values():
            keep = [m for m in b.medoids
                    if m.decayed(self.seq, self.half_life) >= self.weight_floor]
            n += len(b.medoids) - len(keep)
            b.medoids = keep
        return n

    def total_medoids(self) -> int:
        return sum(len(b.medoids) for b in self.buckets.values())

    # ── persistence ────────────────────────────────────────────────────────
    # Experiments fork a COPY of a ledger snapshot; the ledger itself is
    # append-only. Without that split, run N's R depends on run N-1's history
    # and two configurations are not comparable.
    def to_dict(self) -> dict:
        return {
            "k_per_bucket": self.k_per_bucket, "half_life": self.half_life,
            "weight_floor": self.weight_floor, "seq": self.seq,
            "buckets": {
                k: [{"surface": m.surface, "uid": m.uid, "weight": m.weight,
                     "last_seen": m.last_seen, "hits": m.hits}
                    for m in b.medoids]
                for k, b in self.buckets.items()},
        }

    @staticmethod
    def from_dict(d: dict) -> "RepetitionLog":
        log = RepetitionLog(k_per_bucket=d["k_per_bucket"],
                            half_life=d["half_life"],
                            weight_floor=d["weight_floor"], seq=d["seq"])
        for k, rows in d["buckets"].items():
            log.buckets[k] = Bucket(key=k, medoids=[
                Medoid(scene=parse(r["surface"]), surface=r["surface"],
                       uid=r["uid"], weight=r["weight"],
                       last_seen=r["last_seen"], hits=r["hits"])
                for r in rows])
        return log

    def fork(self) -> "RepetitionLog":
        """A disposable experiment copy. The original is untouched."""
        return RepetitionLog.from_dict(self.to_dict())
