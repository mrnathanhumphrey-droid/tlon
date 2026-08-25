"""Phase 3 loop: learned generator vs co-adapting listener, under lambda*R.

PREREG 3c49ad47. The generator picks the free channels; the signature core is
fixed so every utterance stays legal and on-referent. Reward is
  M (listener resolves it) + lambda * (1 - repetition cost).

Everything a cipher needs is present: a lossless channel, an exact decoder, free
channels carrying no referent information, and a listener that can co-adapt.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field

import torch

from ..grammar import classes as C
from ..grammar.denote import project
from ..grammar.parse import EventNode, ParseError, Scene, parse, render
from ..listener import tokenizer as tk
from ..listener.train import TrainCfg
from ..novelty.centroids import RepetitionLog
from ..referents.schema import Referent
from .policy import ChannelPolicy


@dataclass
class P3Cfg:
    steps: int = 4000
    lam: float = 1.0
    lr: float = 0.05
    entropy_bonus: float = 0.01
    listener_every: int = 250
    listener_epochs: int = 2
    half_life: float = 48.0
    seed: int = 31415
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    # Baseline scope. A GLOBAL EMA does not remove state-dependent reward
    # variation, and R varies strongly by referent (a sparse bucket scores low
    # whatever you say into it). Then every action sampled at a lucky referent
    # is reinforced together, which is collapse driven by WHICH REFERENT CAME
    # UP rather than by which action was chosen -- and it scales with lambda.
    # Default stays False so the v2 sweep remains reproducible.
    per_ref_baseline: bool = False
    # Divide the advantage by its running sd. lambda enters the reward as a
    # MULTIPLIER, so raising it raises advantage variance (measured: 2.17x from
    # lambda 0 to 2) as well as novelty weight. REINFORCE collapses faster at
    # higher advantage variance, so the two effects are confounded in the raw
    # sweep and lambda cannot be read as novelty pressure alone.
    normalize_advantage: bool = False
    # PHASE 5 (PREREG c09d0fb3). The listener sees pi(scene) and R is computed
    # on pi(scene) too. Projecting only the listener's view would trade the
    # cipher failure for the NOISE failure -- free novelty from wiggling
    # decoration nobody can read. Projecting R as well is also what Q3=1 already
    # forces: two utterances differing only in non-denoting decoration are the
    # SAME IMPRESSION and must not count as novel.
    project: bool = False
    # Reset one pool member to fresh initialisation every N steps (0 = never).
    # A private code has to be re-agreed with each newcomer; honest description
    # transfers for free.
    reset_every: int = 0
    # Freeze the listener: it never updates, so CO-ADAPTATION IS IMPOSSIBLE and
    # no private code can form. The generator still shifts its distribution to
    # be understood. That makes this the control which separates the two things
    # the naive-listener gap otherwise conflates.
    train_listener: bool = True
    # PHASE 8.3. Li & Bowling report it is CRITICAL that new listeners arrive
    # ABRUPTLY, not smoothly: the teachability pressure is the speaker's entropy
    # spike when its listener cannot understand it, and with a rolling 1-of-K
    # reset the majority keeps reward high so the spike never fires. Our phase-5
    # config was exactly that staggered regime. This resets the WHOLE pool at
    # once, which is their simultaneous condition.
    reset_all_at: int = 0


@dataclass
class P3Stats:
    m_rate: list[float] = field(default_factory=list)
    rep_cost: list[float] = field(default_factory=list)
    reward: list[float] = field(default_factory=list)
    entropy: list[float] = field(default_factory=list)   # 8.3a teachability spike
    steps: list[int] = field(default_factory=list)

    # ⛔⛔ STANDING OUTPUT, PHASE 10 ONWARD. NON-NEGOTIABLE, NOT CONTINGENT.
    # `selections[ri]` counts how often each subset was chosen for referent ri:
    #   {referent_index: {subset_tuple: count}}
    #
    # WHY IT IS HERE AT ALL. Nothing in this project has ever recorded WHICH
    # subset the policy chose -- 0 of 9 phase-8 rollout keys, 0 in phase-5 --
    # and that absence is what stalled 9.5 into Outcome 3: P_policy(subset |
    # referent) could not be estimated at ANY resolution because the effective
    # sample size was 0, not merely small. It costs a dict increment per step.
    #
    # ⭐ It is an OUTPUT ONLY. It draws no random numbers and touches no
    # gradient, so every phase 3-8 run reproduces byte-identically with it on.
    # ⛔ TWO LOGS, NOT ONE, AND THEY ANSWER DIFFERENT QUESTIONS.
    #   selections  -- what the policy CHOSE (its distribution)
    #   uttered     -- what actually got BUILT and said (the utterance
    #                  distribution the listener and the detectors see)
    # They differ by the unbuildable subsets: v2 has 11 structural holes (a
    # depth-2 pattern needs a depth-1 sibling), 5.0% of the space. Weighting an
    # utterance statistic by the CHOICE distribution would silently credit mass
    # to utterances that were never said.
    selections: dict = field(default_factory=dict)
    uttered: dict = field(default_factory=dict)
    selection_steps: int = 0
    build_failures: int = 0

    # ⛔⛔ PHASE 13.2 -- THE THIRD LOG, AND THE TEMPORAL DESIGN IS UNMEASURABLE
    # WITHOUT IT. Part B's quantity is the GROWTH CURVE of the residue gap over
    # interaction length, which is a per-turn statistic: an unlogged residue
    # selection cannot be recovered after the run, and the curve simply does not
    # exist. That is the 9.5 stall (effective sample size 0, not merely small)
    # arriving in a new dimension, so the log goes in BEFORE the arms do.
    #   residues[ri] -- {residue_coordinate: count}, over BUILT scenes only,
    #                   because an unbuilt scene was never said.
    residues: dict = field(default_factory=dict)

    def log_selection(self, ri: int, select, *, built: bool,
                      residue: tuple[int, ...] | None = None) -> None:
        key = tuple(select) if select is not None else "ALL"
        d = self.selections.setdefault(ri, {})
        d[key] = d.get(key, 0) + 1
        self.selection_steps += 1
        if built:
            u = self.uttered.setdefault(ri, {})
            u[key] = u.get(key, 0) + 1
            if residue is not None:
                rd = self.residues.setdefault(ri, {})
                rd[residue] = rd.get(residue, 0) + 1
        else:
            self.build_failures += 1

    def selection_ess(self) -> dict:
        """Effective sample size per referent, over UTTERED subsets.

        This is the number 9.5 needed and could not have: it says whether a
        policy-weighted statistic rests on enough rollouts per referent to mean
        anything. Reported so sparsity is checked BEFORE the re-weighting is
        believed, rather than a thin estimate defaulting into a confirming
        answer -- the D1 class, a dead measurement reading perfect.
        """
        return {ri: sum(c.values()) for ri, c in self.uttered.items()}


def build_scene(ref: Referent, choice, rng: random.Random) -> Scene | None:
    """Signature core, generator-chosen free channels."""
    lex = C.load()["classes"]
    sig = ref.signature

    def node(pat, decorate: bool) -> EventNode:
        n = EventNode(
            root=rng.choice(list(pat.root_any)),
            orient=[rng.choice(list(pat.orient_any))] if pat.orient_any else [])
        if pat.aspect_root_any:
            n.aspect = (rng.choice(list(pat.aspect_root_any)),
                        choice.values["aspect_reps"])
        elif decorate and choice.values["aspect_root"]:
            n.aspect = (choice.values["aspect_root"], choice.values["aspect_reps"])
        if decorate and choice.values["degree"]:
            n.degree = choice.values["degree"]
        if decorate and choice.values["orient"] and \
                choice.values["orient"] not in n.orient and \
                len(n.orient) < C.constraints()["MAX_ORIENT_PER_PRED"]:
            n.orient.append(choice.values["orient"])
        # PHASE 13.2 -- THE BUILD GAP. 13.0 gave EventNode a residue, taught pi
        # to keep it, and made canon_json and D see it -- but nothing ever SET
        # one, so every generated scene was residue-free and W_RESIDUE was inert
        # in the loop. `tools/premise_13_2.py` flags it; 13.0's red-proofs could
        # not, because they build scenes by hand and never call build_scene.
        #
        # ⛔ DRAW ONLY WHEN THERE IS A CHOICE TO MAKE. An unconditional
        # rng.choice() here consumes a draw from the shared stream, and every
        # phase 3-8 tool calls build_scene -- so it would silently stop those
        # runs reproducing byte-identically. Sets with no residue_any (archive,
        # v2, CR, TAO) draw nothing at all; a singleton draws nothing either.
        if pat.residue_any:
            n.residue = (pat.residue_any[0] if len(pat.residue_any) == 1
                         else rng.choice(list(pat.residue_any)))
        return n

    head = node(sig.contains[0], True)
    # The head predication is never optional -- the grammar requires a matrix
    # verb. Selection applies only to the dependents. select=None means "utter
    # everything", i.e. phase 3.
    keep = (choice.select if choice.select is not None
            else tuple(range(len(sig.contains) - 1)))
    deep, used = [], set()
    for i in keep:
        pat = sig.contains[1 + i]
        child = node(pat, False)
        rel = rng.choice(list(pat.via)) if pat.via else rng.choice(list(lex["L"]))
        if (pat.at_depth or 1) > 1:
            deep.append((pat.at_depth, rel, child))
            continue
        if (rel, child.root) in used:
            return None
        used.add((rel, child.root))
        head.edges.append((rel, child))
    for want, rel, child in deep:
        cur, d = head, 0
        while d + 1 < want and cur.edges:
            cur = cur.edges[0][1]
            d += 1
        if d + 1 != want:
            return None
        cur.edges.append((rel, child))

    sc = Scene(node=head, force=choice.values["coda"])
    try:
        surf = render(sc)
        parse(surf)
        tk.encode(surf)
    except (ParseError, ValueError, Exception):
        return None
    return sc


_BASE: dict = {"v": None, "per": {}}
_VAR: dict = {"m2": 0.0}


def self_baseline(cfg: "P3Cfg", reward: float, ref_idx: int | None = None,
                  decay: float = 0.99) -> float:
    """EMA of reward, global or per-referent. Reset per run by run().

    Per-referent is the correct scope: the baseline exists to subtract off what
    the policy could not have chosen, and the referent is drawn by the
    environment, not by the policy.
    """
    if cfg.per_ref_baseline and ref_idx is not None:
        b = _BASE["per"].get(ref_idx)
        _BASE["per"][ref_idx] = reward if b is None else decay * b + (1 - decay) * reward
        return b if b is not None else reward
    b = _BASE["v"]
    _BASE["v"] = reward if b is None else decay * b + (1 - decay) * reward
    return b if b is not None else reward


def run(refs: list[Referent], listener, cfg: P3Cfg, *, verbose: bool = True,
        policy: ChannelPolicy | None = None, pool: list | None = None,
        make_listener=None):
    """policy=None builds a phase-3 policy (no selection head). Phase 4 passes
    one constructed with `deps=`, which turns impression-selection on.

    pool: phase 5's listener population. The generator faces a RANDOM member
    each step, so a code must be agreed with all of them. make_listener is the
    factory used by cfg.reset_every to drop a fresh naive member into the pool.
    """
    _BASE["v"], _BASE["per"], _VAR["m2"] = None, {}, 0.0
    torch.manual_seed(cfg.seed)
    rng = random.Random(cfg.seed)
    if policy is None:
        policy = ChannelPolicy(len(refs)).to(cfg.device)
    listeners = pool if pool else [listener]
    reset_ptr = 0
    opt = torch.optim.Adam(policy.parameters(), lr=cfg.lr)
    rep = RepetitionLog(half_life=cfg.half_life)
    st = P3Stats()
    buffer: list[tuple[list[int], int]] = []
    for L in listeners:
        L.train()

    win_m, win_r, win_rw, win_e = [], [], [], []
    for step in range(1, cfg.steps + 1):
        ri = rng.randrange(len(refs))
        ref = refs[ri]
        choice = policy(ri)
        sc = build_scene(ref, choice, rng)
        st.log_selection(ri, choice.select, built=sc is not None,   # STANDING
                         residue=sc.node.residue if sc is not None else None)
        if sc is None:
            continue
        # THE VIEW IS THE OBJECT. Under pi the listener sees the projection and
        # R scores the projection -- one object, so comprehension and novelty
        # are finally measured on the same thing.
        view = project(sc) if cfg.project else sc
        surf = render(view)
        ids = torch.tensor([tk.encode(surf)], device=cfg.device)

        listener = listeners[rng.randrange(len(listeners))]
        with torch.no_grad():
            probs = torch.softmax(listener(ids), dim=1)[0]
        # M BY MARGIN, not 0/1. Accuracy saturates at 100% immediately -- the
        # signature core already determines the referent -- and a constant term
        # has zero gradient, so the gate was never actually under test.
        m = float(probs[ri])
        m_hit = 1.0 if int(probs.argmax()) == ri else 0.0

        score = rep.score(ref.id, view)
        reward = m + cfg.lam * (1.0 - score["novelty_cost"])

        # ADVANTAGE, not raw reward. Reward here is always positive, so plain
        # REINFORCE pushes UP the log-prob of every sampled action and the
        # policy collapses onto whatever it saw first -- which is exactly what
        # happened: concentration hit 0.92 even at lambda=0, where there is no
        # novelty pressure at all. Only better-than-average actions may be
        # reinforced.
        baseline = self_baseline(cfg, reward, ri)
        advantage = reward - baseline
        if cfg.normalize_advantage:
            _VAR["m2"] = 0.99 * _VAR["m2"] + 0.01 * advantage * advantage
            advantage = advantage / max(1e-6, _VAR["m2"] ** 0.5)
        loss = -(choice.logprob * advantage) - cfg.entropy_bonus * choice.entropy
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()

        rep.observe(ref.id, view, surf)
        buffer.append((tk.encode(surf), ri))
        win_m.append(m_hit); win_r.append(score["novelty_cost"]); win_rw.append(reward)
        win_e.append(float(choice.entropy))

        if cfg.reset_all_at and make_listener and step == cfg.reset_all_at:
            for i in range(len(listeners)):
                listeners[i] = make_listener()
            buffer = []          # the newcomers must learn from what comes next
        if cfg.reset_every and make_listener and step % cfg.reset_every == 0:
            listeners[reset_ptr % len(listeners)] = make_listener()
            reset_ptr += 1
        if cfg.train_listener and step % cfg.listener_every == 0:
            for L in listeners:
                _train_listener(L, buffer, cfg)
            buffer = buffer[-4000:]
            st.m_rate.append(sum(win_m) / len(win_m))
            st.rep_cost.append(sum(win_r) / len(win_r))
            st.reward.append(sum(win_rw) / len(win_rw))
            st.entropy.append(sum(win_e) / len(win_e))
            st.steps.append(step)
            if verbose:
                print(f"    step {step:5d}  M {100 * st.m_rate[-1]:5.1f}%  "
                      f"R {st.rep_cost[-1]:.3f}  reward {st.reward[-1]:.3f}")
            win_m, win_r, win_rw, win_e = [], [], [], []
    return policy, rep, st


def _train_listener(listener, buffer, cfg: P3Cfg) -> None:
    if len(buffer) < 64:
        return
    X = torch.tensor([b[0] for b in buffer], dtype=torch.long, device=cfg.device)
    y = torch.tensor([b[1] for b in buffer], dtype=torch.long, device=cfg.device)
    opt = torch.optim.AdamW(listener.parameters(), lr=1e-4)
    lossf = torch.nn.CrossEntropyLoss()
    listener.train()
    for _ in range(cfg.listener_epochs):
        perm = torch.randperm(len(X), device=cfg.device)
        for i in range(0, len(X), 256):
            idx = perm[i:i + 256]
            opt.zero_grad(set_to_none=True)
            lossf(listener(X[idx]), y[idx]).backward()
            opt.step()
