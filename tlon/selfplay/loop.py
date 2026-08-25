"""The 2a self-play loop. Zero GPU, zero model.

M is structural signature matching (exact, free). Every mechanism that can fail
for a non-neural reason fails here, where the failure is legible: bucket keying,
decay, orbit arithmetic, the audit schema, tree edit distance, the collision
counter.

⚠️ 2a PROVES PLUMBING, NEVER PRAGMATICS. Structural compat cannot tell a vivid
impression from a barely relevant one. A good score here means the pipes do not
leak. It is not evidence that anything communicated.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field

from ..audit import log as audit
from ..grammar import classes as C
from ..grammar.canon import canon_json, utterance_id
from ..grammar.gloss import gloss
from ..grammar.parse import Scene, render
from ..novelty.centroids import RepetitionLog
from ..novelty.orbit import Decision, Orbit, Policy
from ..referents import match, schema
from . import scenes


def _depth(n) -> int:
    return 0 if not n.edges else 1 + max(_depth(c) for _, c in n.edges)


@dataclass
class Config:
    turns: int = 400
    seed: int = 20260818
    arc_len: int = 12                 # utterances per orbit before a new arc
    orbit_budget: float = 3.0
    policy: Policy = Policy.CLOSE_ORBIT
    k_per_bucket: int = 8
    half_life: float = 64.0
    novelty_reject: float = 0.85      # above this, regenerate rather than emit
    max_attempts: int = 12
    decorate_p: float = 0.45


@dataclass
class Stats:
    emitted: int = 0
    accepted: int = 0
    m_fail: int = 0
    novelty_reject: int = 0
    collisions: int = 0
    ambiguous: int = 0
    orbits_closed: int = 0
    repeats_allowed: int = 0
    attempts: int = 0
    ambiguity_pairs: dict = field(default_factory=dict)


def run(con, cfg: Config, *, run_id: str, refs=None) -> tuple[Stats, RepetitionLog]:
    rs = schema.load()
    seeds = refs if refs is not None else rs.seeds()
    if not seeds:
        raise RuntimeError("no seeded referents")

    lex = C.load()
    audit.start_run(con, run_id=run_id, phase="2a",
                    grammar_family=rs.grammar_family,
                    lexicon_hash=lex["_hash"], referents_hash=rs.review_status,
                    notes="structural compat; no model; plumbing only")

    rng = random.Random(cfg.seed)
    rep = RepetitionLog(k_per_bucket=cfg.k_per_bucket, half_life=cfg.half_life)
    st = Stats()
    orbit = Orbit(f"{run_id}-arc0", budget=cfg.orbit_budget, policy=cfg.policy)
    arc_i, arc_used = 0, 0

    for seq in range(1, cfg.turns + 1):
        if orbit.closed or arc_used >= cfg.arc_len:
            arc_i += 1
            arc_used = 0
            orbit = Orbit(f"{run_id}-arc{arc_i}", budget=cfg.orbit_budget,
                          policy=cfg.policy)
        ref = rng.choice(seeds)

        chosen: Scene | None = None
        score = None
        reject = None
        chosen_attempt = 1
        for attempt in range(1, cfg.max_attempts + 1):
            st.attempts += 1
            scene = scenes.sample(ref, rng, decorate_p=cfg.decorate_p)
            resolved = match.resolve(scene, seeds)
            if ref.id not in {r.id for r in resolved}:
                st.m_fail += 1
                reject = "M_FAIL"
                _log(con, run_id, seq, ref, scene, resolved, rep, None,
                     accepted=False, reason="M_FAIL", attempt=attempt,
                     orbit=orbit)
                continue
            s = rep.score(ref.id, scene)
            if s["novelty_cost"] > cfg.novelty_reject and attempt < cfg.max_attempts:
                st.novelty_reject += 1
                reject = "TOO_REPETITIVE"
                _log(con, run_id, seq, ref, scene, resolved, rep, s,
                     accepted=False, reason="TOO_REPETITIVE", attempt=attempt,
                     orbit=orbit)
                continue
            chosen, score, chosen_attempt = scene, s, attempt
            break

        if chosen is None:
            continue

        decision = orbit.offer(ref.id, score["novelty_cost"])
        orbit.commit(ref.id, score["novelty_cost"], decision)
        if decision is Decision.CLOSE:
            st.orbits_closed += 1
            continue
        if decision is Decision.REPEAT:
            st.repeats_allowed += 1

        # Record the attempt the winner actually came from, not 1. It is the
        # rejection-count signal flag ② wants, and logging it as 1 collided
        # with the rejected row already written for this seq.
        resolved = match.resolve(chosen, seeds)
        row = _log(con, run_id, seq, ref, chosen, resolved, rep, score,
                   accepted=True, reason=None, attempt=chosen_attempt,
                   orbit=orbit)
        rep.observe(ref.id, chosen, render(chosen))
        st.emitted += 1
        st.accepted += 1
        arc_used += 1
        if row["collision"]:
            st.collisions += 1
        if len(resolved) > 1:
            st.ambiguous += 1
            key = "+".join(sorted(r.id for r in resolved))
            st.ambiguity_pairs[key] = st.ambiguity_pairs.get(key, 0) + 1

    return st, rep


def _log(con, run_id, seq, ref, scene, resolved, rep, score, *, accepted,
         reason, attempt, orbit) -> dict:
    surface = render(scene)
    rec = audit.UtteranceRecord(
        run_id=run_id, seq=seq, referent_id=ref.id, surface=surface,
        canon_json=canon_json(scene), utterance_id=utterance_id(scene),
        gloss=gloss(scene), morphs=len(surface.split()),
        depth=_depth(scene.node), m_pass=accepted or reason != "M_FAIL",
        m_kind="STRUCTURAL", m_margin=None,
        resolved_to=[r.id for r in resolved], bucket=ref.id,
        nearest_dist=(score or {}).get("nearest_dist"),
        decay_weight=(score or {}).get("decay_weight"),
        novelty_cost=(score or {}).get("novelty_cost"),
        orbit_id=orbit.orbit_id, orbit_spent=orbit.spent,
        accepted=accepted, reject_reason=reason, attempt=attempt)
    row_id = audit.log_utterance(con, rec)
    return dict(con.execute("SELECT * FROM utterance WHERE row_id=?",
                            (row_id,)).fetchone())
