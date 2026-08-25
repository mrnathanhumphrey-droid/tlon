"""The learned generator — a conditional policy over the FREE channels.

DESIGN CONSTRAINT THAT DECIDES EVERYTHING: the generator must be CAPABLE of
ciphering, or KILL A cannot fire and phase 3 is vacuous. A policy that can only
pick among signature-satisfying scenes at random would pass every check by being
unable to fail.

So the policy is parameterised exactly where a code would live: a table of
logits over the channels the signature does NOT constrain --

    aspect root · aspect repetitions · degree · illocutionary coda · orientation

conditioned on the referent. If generator and listener co-adapt on
"referent 07 always takes aspect reps = 3", that IS a cipher, it is reachable in
one gradient step, and the scramble probe will see it. Making the failure
reachable is the whole point of building it this way.

Trained by REINFORCE on  reward = M + lambda * (1 - repetition_cost).
"""
from __future__ import annotations
from dataclasses import dataclass

import torch
import torch.nn as nn

from ..grammar import classes as C

# Channels the signature leaves free. NONE is index 0 where the channel is
# optional, so "say nothing here" stays available.
FREE = ("aspect_root", "aspect_reps", "degree", "coda", "orient")


def channel_values() -> dict[str, list]:
    lex = C.load()["classes"]
    k = C.constraints()
    return {
        "aspect_root": [None] + sorted(lex["A"]),
        "aspect_reps": list(range(1, k["MAX_ASPECT_REPS"] + 1)),
        "degree": [None] + sorted(lex["D"]),
        "coda": sorted(lex["F"]),
        "orient": [None] + sorted(lex["O"]),
    }


def _rms_pairwise(x: torch.Tensor) -> float:
    """RMS distance between distinct rows. The scale the trunk actually sees."""
    n = x.shape[0]
    if n < 2:
        return 1.0
    d2 = torch.cdist(x, x).pow(2).sum()
    return float((d2 / (n * (n - 1))).sqrt())


def _standardisation_stats(raw: torch.Tensor) -> dict:
    """Recorded so the fix is auditable rather than invisible."""
    return {"dim": int(raw.shape[1]),
            "rms_pairwise_raw": _rms_pairwise(raw),
            "mean_norm_raw": float(raw.norm(dim=1).mean())}


def _standardise(raw: torch.Tensor) -> torch.Tensor:
    """Centre, then divide by RMS inter-referent distance => RMS pairwise = 1.

    ⛔ A GLOBAL SCALAR, NOT PER-DIMENSION Z-SCORING. Per-dimension
    standardisation does NOT equalise inter-referent distance when the arms have
    different dimensionality -- distance grows like sqrt(dim), so a 24-dim
    one-hot would still sit ~3.4x further apart than a 3-dim lattice after
    z-scoring. Only a global scale on the pairwise distance closes the confound
    that was measured.
    """
    centred = raw - raw.mean(dim=0, keepdim=True)
    return centred / max(_rms_pairwise(centred), 1e-12)


@dataclass
class Choice:
    values: dict[str, object]
    logprob: torch.Tensor
    entropy: torch.Tensor
    select: tuple[int, ...] | None = None
    """Which DEPENDENT slots to utter (indices into signature.contains[1:]).

    None means "utter everything", which is phase 3's behaviour and keeps every
    phase-3 tool and control reproducible. Phase 4 turns this on: PREREG
    c1f7d06c makes the generator choose what to leave out, so reference
    resolution stops being free and a cipher finally has something to buy.
    """


class ChannelPolicy(nn.Module):
    """logits[referent, channel, value] — deliberately a lookup table.

    A table is the most cipher-friendly parameterisation there is: one row per
    referent, nothing shared, nothing forcing generalisation. If a code does not
    form here it will not form in something more constrained.
    """

    def __init__(self, n_refs: int, temperature: float = 1.0,
                 deps: list[int] | None = None,
                 uniform_channels: tuple[str, ...] = (),
                 residues: list[tuple[int, ...]] | None = None,
                 hidden: int = 32, standardize: bool = True):
        super().__init__()
        self.vals = channel_values()
        self.temperature = temperature
        # ── PHASE 13.2: THE RESIDUE-CONDITIONED HEAD ──────────────────────
        # residues=None keeps the TABLE exactly as it was, so phases 3-8 are
        # untouched. Passing coordinates switches the parameterisation to a
        # SHARED trunk over the residue coordinate:
        #
        #     logits[ref] = head_ch(trunk(coord[ref]))
        #
        # ⭐ WHY THIS IS THE ONE CHANGE THAT MAKES THE 2x2 MEAN ANYTHING. The
        # table has one INDEPENDENT row per referent, so nearby residues are no
        # more alike than distant ones and metric structure is unreachable
        # (tools/premise_13_2.py, issue 2). A shared trunk is smooth in the
        # coordinate, so nearby residues get nearby channel distributions --
        # which IS the Pictionary property, made architectural.
        #
        # ⛔⛔ AND THE FALSIFYING CELL IS REACHABLE ON PURPOSE. The trunk is an
        # MLP, not a linear map, so it has the capacity to memorise an ARBITRARY
        # per-residue code exactly as the table did. Having a route is not using
        # it: if the pair trains to an arbitrary code anyway, metric and
        # categorical gap identically UNDER THE HEAD and the architectural claim
        # is false. A linear trunk would have made that outcome unreachable and
        # the 2x2 unfalsifiable.
        #
        # ⛔⛔ RETRACTED, DO NOT RESTORE. This comment used to claim "one-hot
        # coordinates reduce this exactly to a table, so categorical x head
        # should equal categorical x table". FALSE, and it was the 2x2's
        # consistency check until DEVIATIONS_13_2 D16: a one-hot selects a row
        # of the FIRST weight matrix only, and everything above it -- the second
        # trunk layer and every channel head -- is SHARED across all referents.
        # A per-referent EMBEDDING through a shared nonlinear map is not a free
        # per-referent output. The gate is now the per-cell Bayes ceiling
        # (tlon/harness/ceiling.py), which reads what the policy DOES and makes
        # no architectural assumption at all.
        self.residues = residues
        self.trunk = None
        if residues is not None:
            if len(residues) != n_refs:
                raise ValueError(
                    f"{len(residues)} residue coordinates for {n_refs} "
                    "referents; the head is indexed by referent")
            dims = {len(r) for r in residues}
            if len(dims) != 1:
                raise ValueError(
                    f"residue coordinates mix lattice dimensions {sorted(dims)}")
            d = dims.pop()
            raw = torch.tensor(residues, dtype=torch.float32)
            # ⛔⛔ THE SCALE-CONFOUND FIX. Measured before this existed: the
            # categorical arm's coordinates sat 8.3x further apart in raw input
            # space than the metric arm's (mean inter-referent L2 24.04 vs
            # 2.91), because the one-hot scale was chosen to match mean
            # NORMALISED RESIDUE DISTANCE for R (DEVIATIONS_13_2 D7) -- a
            # quantity that at lambda=0 is not even in the reward -- while the
            # same number silently set the input magnitude to the trunk, which
            # is doing all of the work in the head arm. The arms were matched on
            # something that did not matter and left unmatched on the one thing
            # that did, ON THE VERY AXIS THE 2x2 MEASURES.
            #
            # So: centre, then divide by the RMS inter-referent distance. Both
            # arms then present clouds centred at the origin with RMS pairwise
            # distance 1, and differ ONLY in SHAPE -- graded lattice vs
            # mutually-equidistant simplex. That is the contrast the phase is
            # about; location and scale are not.
            #
            # ⭐ Deterministic and derived from the referent set, never learned.
            # An adaptive input scale would be the embedding-distance failure
            # `novelty/distance.py` exists to prevent, in a new place.
            self.coord_stats = _standardisation_stats(raw)
            self.register_buffer("coords", _standardise(raw)
                                 if standardize else raw)
            self.trunk = nn.Sequential(nn.Linear(d, hidden), nn.Tanh(),
                                       nn.Linear(hidden, hidden), nn.Tanh())
            self.heads = nn.ModuleDict(
                {ch: nn.Linear(hidden, len(v)) for ch, v in self.vals.items()})
            # ⛔ ZERO-INIT THE OUTPUT LAYER. The table starts at uniform
            # (torch.zeros), and a head that started at a RANDOM code would
            # hand the head arm a head start at t=0 -- which would corrupt the
            # growth curve at exactly the turns Part B cares most about. Both
            # parameterisations must begin knowing nothing.
            for h in self.heads.values():
                nn.init.zeros_(h.weight)
                nn.init.zeros_(h.bias)
        # Channels the policy is FORBIDDEN to steer: sampled uniformly, no
        # log-prob, no gradient. This is the control that separates a real code
        # from an off-distribution artefact. A concentrated policy makes the
        # co-adapting listener overfit a narrow distribution, and such a
        # listener degrades when ANY channel is scrambled -- code or not. Force
        # a channel uniform and it provably carries no code; if the probe still
        # fires on it, the probe is reading overfitting, not ciphering.
        self.uniform_channels = set(uniform_channels)
        # ⛔ In head mode the table is NOT created. Dead zero-gradient
        # parameters would still be handed to the optimiser and still be
        # counted by any parameter-count comparison between the arms, which is
        # exactly the confound the 2x2 has to be clean of.
        self.logits = nn.ParameterDict({} if residues is not None else {
            ch: nn.Parameter(torch.zeros(n_refs, len(v)))
            for ch, v in self.vals.items()
        })
        # SELECTION HEAD (phase 4). One Bernoulli logit per dependent slot per
        # referent. deps[i] is how many dependents referent i actually has --
        # slots beyond that are never sampled, so a one-dependent referent does
        # not accumulate gradient on a slot it does not possess.
        self.deps = list(deps) if deps else []
        self.n_slots = max(self.deps) if self.deps else 0
        self.select_logits = (
            nn.Parameter(torch.zeros(n_refs, self.n_slots))
            if self.n_slots else None)

    def logit_matrix(self, ch: str) -> torch.Tensor:
        """(n_refs, n_values) under EITHER parameterisation.

        One accessor so every reader -- forward, concentration, any probe --
        sees the same object whichever arm is running. A second code path here
        is how a table statistic would silently get reported for a head run.
        """
        if self.trunk is None:
            return self.logits[ch]
        return self.heads[ch](self.trunk(self.coords))

    def forward(self, ref_idx: int) -> Choice:
        chosen, lps, ents = {}, [], []
        for ch, values in self.vals.items():
            if ch in self.uniform_channels:
                chosen[ch] = values[int(torch.randint(len(values), (1,)))]
                continue
            logits = self.logit_matrix(ch)[ref_idx] / self.temperature
            dist = torch.distributions.Categorical(logits=logits)
            i = dist.sample()
            chosen[ch] = values[int(i)]
            lps.append(dist.log_prob(i))
            ents.append(dist.entropy())

        select = None
        if self.select_logits is not None:
            live = self.deps[ref_idx]
            if live:
                lg = self.select_logits[ref_idx, :live] / self.temperature
                dist = torch.distributions.Bernoulli(logits=lg)
                mask = dist.sample()
                lps.append(dist.log_prob(mask).sum())
                ents.append(dist.entropy().sum())
                select = tuple(i for i in range(live) if mask[i] > 0.5)
            else:
                select = ()
        return Choice(values=chosen, logprob=torch.stack(lps).sum(),
                      entropy=torch.stack(ents).sum(), select=select)

    @torch.no_grad()
    def selection_decidedness(self) -> float:
        """Mean max(p, 1-p) over live slots. 0.50 = undecided, 1.0 = committed.

        THIS is what KILL C must watch, not the mean selection RATE. A policy
        can be utterly decided -- "for referent 12, always utter slot 0, never
        slot 1" -- while its mean rate sits exactly at 0.50. Rate answers "how
        much does it say"; decidedness answers "has it learned to choose", and
        only the second is the question KILL C asks.
        """
        if self.select_logits is None:
            return float("nan")
        tot, n = 0.0, 0
        for i, live in enumerate(self.deps):
            if not live:
                continue
            p = torch.sigmoid(self.select_logits[i, :live])
            tot += float(torch.maximum(p, 1 - p).sum())
            n += live
        return tot / n if n else float("nan")

    @torch.no_grad()
    def selection_rate(self) -> float:
        """Mean P(utter) over live slots. Initialises at 0.50 (logits zero).

        KILL C watches this: a policy that never learns to withhold anything has
        not made M scarce in practice, and phase 4 has reproduced phase 3.
        """
        if self.select_logits is None:
            return float("nan")
        ps, n = 0.0, 0
        for i, live in enumerate(self.deps):
            if not live:
                continue
            ps += float(torch.sigmoid(self.select_logits[i, :live]).sum())
            n += live
        return ps / n if n else float("nan")

    @torch.no_grad()
    def concentration(self) -> dict[str, float]:
        """Per channel: mean max-probability across referents.

        1/n_values means uniform (no code). Approaching 1.0 means the policy has
        collapsed onto one value per referent -- the signature of a cipher, and
        an early warning that is free to compute.
        """
        out = {}
        for ch, values in self.vals.items():
            p = torch.softmax(self.logit_matrix(ch), dim=-1)
            out[ch] = float(p.max(dim=-1).values.mean())
        return out

    def uniform_baseline(self) -> dict[str, float]:
        return {ch: 1.0 / len(v) for ch, v in self.vals.items()}
