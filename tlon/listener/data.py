"""Dataset for 2b, built to the pre-registered confound controls.

Two controls do real work here:

  DEDUPE BY CANONICAL utterance_id, not by surface string. Permuted orientations
  are the SAME utterance (spec §6); deduping on the string would leave identical
  meanings on both sides of the split and inflate the headline number.

  NOVEL-DECORATION SPLIT. A random split lets the model memorise decoration
  combinations. The honest split holds out whole (aspect, degree, modal, tense,
  quant) signatures, so test scenes wear dress the model has never seen. The gap
  between the two splits IS the memorisation estimate.
"""
from __future__ import annotations
import hashlib
import random
from dataclasses import dataclass, field

from ..grammar.canon import utterance_id
from ..grammar.parse import EventNode, Scene, render
from ..referents.schema import Referent
from ..selfplay import scenes as gen
from . import tokenizer as tk


def decoration_key(n: EventNode) -> str:
    """What the matrix node is wearing, ignoring which happening it is."""
    return "|".join([
        n.aspect[0] if n.aspect else "-",
        str(n.aspect[1]) if n.aspect else "-",
        n.degree or "-", n.modal or "-", n.tense or "-", n.quant or "-",
        str(len(n.orient)), str(len(n.edges)),
    ])


def _held_out(key: str, frac: float, salt: str) -> bool:
    h = hashlib.blake2b((salt + key).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / 2 ** 64 < frac


@dataclass
class Example:
    label: int
    ref_id: str
    surface: str
    uid: str
    ids: list[int]
    dec_key: str


@dataclass
class Dataset:
    refs: list[Referent]
    train: list[Example] = field(default_factory=list)
    test_random: list[Example] = field(default_factory=list)
    test_novel: list[Example] = field(default_factory=list)
    dropped_dupes: int = 0

    @property
    def n_classes(self) -> int:
        return len(self.refs)


def build(refs: list[Referent], *, per_ref: int = 4000, seed: int = 202608019,
          blend_p: float = 0.6, novel_frac: float = 0.25,
          test_frac: float = 0.2) -> Dataset:
    rng = random.Random(seed)
    label_of = {r.id: i for i, r in enumerate(refs)}
    seen: set[str] = set()
    ds = Dataset(refs=refs)

    pool: list[Example] = []
    for ref in refs:
        made, tries = 0, 0
        while made < per_ref and tries < per_ref * 12:
            tries += 1
            sc = gen.sample(ref, rng, blend_pool=refs, blend_p=blend_p)
            uid = utterance_id(sc)
            if uid in seen:                      # canonical dedupe, not surface
                ds.dropped_dupes += 1
                continue
            seen.add(uid)
            surf = render(sc)
            try:
                ids = tk.encode(surf)
            except ValueError:
                continue                         # over token budget; skip
            pool.append(Example(label=label_of[ref.id], ref_id=ref.id,
                                surface=surf, uid=uid, ids=ids,
                                dec_key=decoration_key(sc.node)))
            made += 1

    # novel-decoration split first, so the random split cannot borrow from it
    salt = f"novel-{seed}"
    novel, rest = [], []
    for ex in pool:
        (novel if _held_out(ex.dec_key, novel_frac, salt) else rest).append(ex)

    rng.shuffle(rest)
    cut = int(len(rest) * test_frac)
    ds.test_random = rest[:cut]
    ds.train = rest[cut:]
    ds.test_novel = novel
    return ds
