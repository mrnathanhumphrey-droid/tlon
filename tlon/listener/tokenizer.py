"""Morpheme-per-token tokenizer. Ours, minted from the lexicon.

Every morpheme is one atomic token. This is the decision that makes the model
"ours" rather than a wrapper: BPE over `hlör`/`hlan`/`hlax` would fragment a
229-symbol closed vocabulary into shared prefixes, and the mask would have to
reason about partial morphemes. Here the token stream is isomorphic to the AST
(the grammar is LL(1)), so a sequence model sees structure directly.

ASPECT IS TWO TOKENS, NOT ONE PER COUNT. `axaxaxas` becomes [ax][REPS_3], not a
distinct symbol per reduplication depth. Reduplication is an ORDINAL scale
(§3.4); one-symbol-per-count would make ×1 and ×4 as unrelated as two different
roots and throw away the ordering the grammar built in.
"""
from __future__ import annotations
import functools

from ..grammar import classes as C
from ..grammar.parse import Scene

PAD, CLS = "[PAD]", "[CLS]"
MAX_LEN = 26


@functools.lru_cache(maxsize=1)
def vocab() -> dict[str, int]:
    lex = C.load()
    toks = [PAD, CLS]
    for cls in ("R", "O", "L", "A", "M", "D", "Q", "T", "F"):
        toks += sorted(lex["classes"][cls])
    toks += [f"[REPS_{i}]" for i in
             range(1, lex["constraints"]["MAX_ASPECT_REPS"] + 1)]
    if len(set(toks)) != len(toks):
        raise RuntimeError("token collision — classes are not surface-disjoint")
    return {t: i for i, t in enumerate(toks)}


@functools.lru_cache(maxsize=1)
def inverse() -> dict[int, str]:
    return {i: t for t, i in vocab().items()}


def size() -> int:
    return len(vocab())


def pieces(text: str) -> list[str]:
    """Surface string -> token strings, expanding aspect into (root, reps)."""
    out = [CLS]
    for tok in text.split():
        cls, payload = C.classify(tok)
        if cls == "A":
            root, reps = payload
            out += [root, f"[REPS_{reps}]"]
        else:
            out.append(payload)
    return out


def encode(text: str, max_len: int = MAX_LEN) -> list[int]:
    v = vocab()
    ids = [v[p] for p in pieces(text)]
    if len(ids) > max_len:
        raise ValueError(f"{len(ids)} tokens exceeds max_len {max_len}: {text!r}")
    return ids + [v[PAD]] * (max_len - len(ids))


def decode(ids: list[int]) -> str:
    inv = inverse()
    out = []
    for i in ids:
        t = inv[int(i)]
        if t in (PAD, CLS):
            continue
        out.append(t)
    return " ".join(out)


def root_ids() -> set[int]:
    """Token ids of verbal roots — used by the bag-of-roots baseline."""
    v = vocab()
    return {v[r] for r in C.load()["classes"]["R"]}
