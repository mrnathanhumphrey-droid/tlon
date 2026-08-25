"""Grammar-mask state machine (spec §4.2).

The legal-next set is a pure function of (slot cursor, depth, counts, budget) --
a finite state machine with a bounded stack. No parser generator, no per-token
model call: masking is O(1) amortised per token, which is why syntax costs zero
inference in self-play.

Two properties this must have, both tested:
  SOUND       -- any walk the FSM allows to completion parses.
  COMPLETE    -- the FSM never blocks a continuation of a legal utterance.
A mask that is merely sound silently shrinks the language.
"""
from __future__ import annotations
import copy
from dataclasses import dataclass, field

from . import classes as C

PRE, POST_R, POST_A = "PRE", "POST_R", "POST_A"
# slot cursor positions inside a predication
_SLOT = {"Q": 0, "T": 1, "M": 2, "O": 3, "L": 4}


@dataclass
class _Frame:
    slot: int = 0
    n_orient: int = 0
    n_clause: int = 0
    phase: str = PRE


@dataclass
class MaskState:
    stack: list[_Frame] = field(default_factory=lambda: [_Frame()])
    used: int = 0
    done: bool = False

    def clone(self) -> "MaskState":
        return copy.deepcopy(self)


def _required(st: MaskState) -> int:
    """Minimum further morphemes needed to close legally: one root per frame
    still awaiting a nucleus, plus the illocutionary coda."""
    return sum(1 for f in st.stack if f.phase == PRE) + 1


def legal_classes(st: MaskState) -> dict[str, set[int]]:
    """class label -> set of legal aspect-repetition counts (empty set means
    the class takes no parameter)."""
    if st.done:
        return {}
    k = C.constraints()
    budget = k["MAX_MORPHS"]
    out: dict[str, set[int]] = {}

    def offer(cls: str, cost: int, param: int | None = None) -> None:
        # cost of this token + what is still required afterwards must fit
        extra = 0 if cls in ("R", "F") else 0
        need = _required(st)
        if cls == "R":
            need -= 1                       # this token IS that frame's root
        elif cls == "L":
            need += 1                       # opens a frame needing its own root
        elif cls == "F":
            need -= 1                       # this token IS the coda
        if st.used + cost + need + extra > budget:
            return
        out.setdefault(cls, set())
        if param is not None:
            out[cls].add(param)

    if not st.stack:
        offer("F", 1)
        return out

    # Walk the close-chain: a frame that may end hands control to its parent.
    view = st.clone()
    while True:
        if not view.stack:
            offer("F", 1)
            break
        top = view.stack[-1]
        if top.phase == PRE:
            depth_left = C.constraints()["MAX_DEPTH"] - (len(view.stack) - 1)
            if top.slot <= _SLOT["Q"]:
                offer("Q", 1)
            if top.slot <= _SLOT["T"]:
                offer("T", 1)
            if top.slot <= _SLOT["M"]:
                offer("M", 1)
            if top.slot <= _SLOT["O"] and top.n_orient < C.constraints()["MAX_ORIENT_PER_PRED"]:
                offer("O", 1)
            if (top.slot <= _SLOT["L"]
                    and top.n_clause < C.constraints()["MAX_CLAUSES_PER_PRED"]
                    and depth_left > 0):
                offer("L", 1)
            offer("R", 1)
            break                           # a PRE frame cannot close
        if top.phase == POST_R:
            for reps in range(1, C.constraints()["MAX_ASPECT_REPS"] + 1):
                offer("A", reps + 1, reps)
            offer("D", 1)
        elif top.phase == POST_A:
            offer("D", 1)
        view.stack.pop()                    # this frame may end here
        if view.stack:
            view.stack[-1].n_clause += 1
            view.stack[-1].slot = _SLOT["L"]
    return out


def step(st: MaskState, cls: str, param: int | None = None) -> MaskState:
    """Advance the state. Raises if the transition is not legal."""
    allowed = legal_classes(st)
    if cls not in allowed:
        raise ValueError(f"{cls} not legal here (allowed: {sorted(allowed)})")
    if cls == "A" and param not in allowed["A"]:
        raise ValueError(f"aspect reps {param} not legal here")

    st = st.clone()
    # close frames until the one this token belongs to is on top
    while st.stack and st.stack[-1].phase != PRE:
        top = st.stack[-1]
        if cls in ("A", "D") and (
                (top.phase == POST_R and cls in ("A", "D"))
                or (top.phase == POST_A and cls == "D")):
            break
        st.stack.pop()
        if st.stack:
            st.stack[-1].n_clause += 1
            st.stack[-1].slot = _SLOT["L"]

    cost = (param + 1) if cls == "A" else 1
    st.used += cost

    if cls == "F":
        st.done = True
        return st
    if cls in ("Q", "T", "M"):
        st.stack[-1].slot = _SLOT[cls] + 1
    elif cls == "O":
        st.stack[-1].slot = _SLOT["O"]
        st.stack[-1].n_orient += 1
    elif cls == "L":
        st.stack[-1].slot = _SLOT["L"]
        st.stack.append(_Frame())
    elif cls == "R":
        st.stack[-1].phase = POST_R
    elif cls == "A":
        st.stack[-1].phase = POST_A
    elif cls == "D":
        st.stack.pop()
        if st.stack:
            st.stack[-1].n_clause += 1
            st.stack[-1].slot = _SLOT["L"]
    return st


def legal_forms(st: MaskState) -> set[str]:
    """Concrete surface forms permitted next -- what a LogitsProcessor masks to."""
    lex = C.load()
    out: set[str] = set()
    for cls, params in legal_classes(st).items():
        if cls == "A":
            for root in lex["classes"]["A"]:
                for reps in params:
                    out.add(root * reps + lex["aspect_closer"])
        else:
            out.update(lex["classes"][cls])
    return out


def accepts(text: str) -> bool:
    """Replay a surface string through the mask; True iff every token was
    permitted and the walk ended closed."""
    st = MaskState()
    for tok in text.split():
        cls, payload = C.classify(tok)
        param = payload[1] if cls == "A" else None
        try:
            st = step(st, cls, param)
        except ValueError:
            return False
    return st.done
