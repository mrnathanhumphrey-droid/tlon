"""Scene sampler -- the 2a stand-in for a generator.

In 2a this is RANDOM SEARCH inside the compatible set, not a learned policy.
That is the point: 2a proves the plumbing, so the generator must be the one
component with nothing to learn, or a plumbing failure and a policy failure
become indistinguishable.

What it does is the real task in miniature: pick a scene from the Q4 space for a
referent (3.63e41 of them) rather than pick a wording for a fixed scene (Q3 = 1,
so there is nothing to pick).
"""
from __future__ import annotations
import random

from ..grammar import classes as C
from ..grammar.parse import EventNode, ParseError, Scene, parse, render
from ..referents import match
from ..referents.schema import NodePattern, Referent


class SampleError(RuntimeError):
    pass


def _decorate(n: EventNode, rng: random.Random, lex: dict, p: float) -> None:
    k = C.constraints()
    if rng.random() < p:
        root = rng.choice(list(lex["A"]))
        n.aspect = (root, rng.randint(1, k["MAX_ASPECT_REPS"]))
    if rng.random() < p:
        n.degree = rng.choice(list(lex["D"]))
    if rng.random() < p * 0.6:
        n.modal = rng.choice(list(lex["M"]))
    if rng.random() < p * 0.6:
        n.tense = rng.choice(list(lex["T"]))
    if rng.random() < p * 0.4:
        n.quant = rng.choice(list(lex["Q"]))
    while len(n.orient) < k["MAX_ORIENT_PER_PRED"] and rng.random() < p * 0.5:
        o = rng.choice(list(lex["O"]))
        if o not in n.orient:
            n.orient.append(o)


def _node(p: NodePattern, rng: random.Random, lex: dict) -> EventNode:
    return EventNode(
        root=rng.choice(list(p.root_any)),
        orient=[rng.choice(list(p.orient_any))] if p.orient_any else [],
        aspect=(rng.choice(list(p.aspect_root_any)), rng.randint(1, 3))
        if p.aspect_root_any else None)


def _blend_node(pool: list[Referent], ref: Referent, rng: random.Random,
                lex: dict, donor: Referent | None = None) -> tuple[str, EventNode] | None:
    """Draw an extra happening from ANOTHER referent's signature.

    Without this the sampler only ever emits "required nodes plus uniform
    noise", and a uniformly random root essentially never lands on the specific
    root some other signature requires — so overlap regions are unreachable and
    ambiguity measures 0% while being provably reachable by hand. That would
    hand 2b a training distribution that avoids exactly the hard cases.

    Note this is not a distortion of the task: a real impression of "a river at
    night" may well contain the moon.
    """
    if donor is None:
        others = [r for r in pool if r.id != ref.id]
        if not others:
            return None
        donor = rng.choice(others)
    pat = rng.choice(donor.signature.contains)
    node = _node(pat, rng, lex)
    rel = rng.choice(list(pat.via)) if pat.via else rng.choice(list(lex["L"]))
    return rel, node


def _attempt(ref: Referent, rng: random.Random, decorate_p: float,
             blend_pool: list[Referent] | None = None,
             blend_p: float = 0.0, blend_donor: Referent | None = None) -> Scene:
    lex = C.load()["classes"]
    k = C.constraints()
    sig = ref.signature

    head = _node(sig.contains[0], rng, lex)
    _decorate(head, rng, lex, decorate_p)

    used_rel: set[tuple[str, str]] = set()
    deep: list = []
    for pat in sig.contains[1:]:
        child = _node(pat, rng, lex)
        _decorate(child, rng, lex, decorate_p * 0.5)
        rel = (rng.choice(list(pat.via)) if pat.via
               else rng.choice(list(lex["L"])))
        if (pat.at_depth or 1) > 1:
            deep.append((pat.at_depth, rel, child))    # placed below, see next
            continue
        if (rel, child.root) in used_rel:      # duplicate siblings are illegal
            raise SampleError("sibling clash")
        used_rel.add((rel, child.root))
        head.edges.append((rel, child))

    # Patterns asking for depth > 1 hang off a depth-1 node, not off the matrix.
    # This is the SCOPE contrast (pair P5) and it is the one thing the grammar's
    # recursion buys, so the sampler has to be able to build it.
    for want, rel, child in deep:
        cur, d = head, 0
        while d + 1 < want:
            if not cur.edges:
                raise SampleError(f"no depth-{want} slot available")
            cur = cur.edges[rng.randrange(len(cur.edges))][1]
            d += 1
        if len(cur.edges) >= k["MAX_CLAUSES_PER_PRED"]:
            raise SampleError("clause cap at target depth")
        cur.edges.append((rel, child))

    # Optional flourish: one extra, unrequired happening in the same breath.
    if len(head.edges) < k["MAX_CLAUSES_PER_PRED"] and rng.random() < decorate_p:
        drawn = None
        if blend_pool and rng.random() < blend_p:
            drawn = _blend_node(blend_pool, ref, rng, lex, blend_donor)
        if drawn is None:
            extra = EventNode(root=rng.choice(list(lex["R"])))
            rel = rng.choice(list(lex["L"]))
        else:
            rel, extra = drawn
        _decorate(extra, rng, lex, decorate_p * 0.4)
        if (rel, extra.root) not in used_rel:
            head.edges.append((rel, extra))

    scene = Scene(node=head, force=rng.choices(
        list(lex["F"]), weights=[6, 1, 1, 1, 1], k=1)[0])

    parse(render(scene))                        # must be legal and re-parseable
    if not match.compat(scene, ref):
        raise SampleError("sampled scene does not satisfy its own signature")
    return scene


def sample(ref: Referent, rng: random.Random, *, decorate_p: float = 0.45,
           blend_pool: list[Referent] | None = None, blend_p: float = 0.0,
           blend_donor: Referent | None = None, tries: int = 40) -> Scene:
    last = None
    for _ in range(tries):
        try:
            return _attempt(ref, rng, decorate_p, blend_pool, blend_p,
                            blend_donor)
        except (ParseError, SampleError) as exc:
            last = exc
    raise SampleError(f"no legal scene for referent {ref.id} after {tries}: {last}")
