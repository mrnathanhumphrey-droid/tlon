"""Gloss-grounded auditor. FROZEN. Audit only, never in the accept loop.

This is the anti-cipher device (flag ⑦, bound as B1). It reads the ENGLISH
GLOSS of a scene -- never the morphemes -- and picks between two referent names.
The generator cannot retrain it and cannot shift what English words mean, so a
private code that says nothing descriptive fails here while scoring perfectly on
the co-trained listener.

FORCED CHOICE BY LOG-PROBABILITY, not by generation. We score both candidate
continuations and take the higher. That removes prompt-format fragility, output
parsing, refusals, and sampling noise -- the auditor must be IMMOVABLE above all
else, and a scorer is more immovable than a generator.

It must never enter the accept/regenerate loop. A yardstick that the artefact
under audit can select against stops being a yardstick.
"""
from __future__ import annotations
import pathlib
from dataclasses import dataclass

import torch

MODEL_ID = "Qwen/Qwen2.5-1.5B"          # base, frozen, never trained here
_CACHE: dict = {}

PROMPT = ("The following is a description of something, written in an unusual "
          "way.\n\nDescription: {gloss}\n\nWhat is being described? Answer: {name}")


@dataclass
class AuditResult:
    n: int
    correct: int

    @property
    def acc(self) -> float:
        return self.correct / max(1, self.n)


def _load(device: str):
    if "m" not in _CACHE:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(MODEL_ID)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, torch_dtype=torch.bfloat16).to(device).eval()
        for p in model.parameters():
            p.requires_grad_(False)          # frozen, structurally
        _CACHE["m"], _CACHE["t"] = model, tok
    return _CACHE["m"], _CACHE["t"]


@torch.no_grad()
def _score(gloss: str, names: list[str], device: str) -> list[float]:
    """Mean log-prob of each candidate name given the gloss. Length-normalised
    so a longer referent name is not penalised for being longer."""
    model, tok = _load(device)
    out = []
    for name in names:
        prefix = PROMPT.format(gloss=gloss, name="")
        full = PROMPT.format(gloss=gloss, name=name)
        pre_ids = tok(prefix, return_tensors="pt").input_ids
        ids = tok(full, return_tensors="pt").input_ids.to(device)
        start = pre_ids.shape[1]
        logits = model(ids).logits[0, :-1]
        tgt = ids[0, 1:]
        lp = torch.log_softmax(logits.float(), dim=-1)
        picked = lp.gather(1, tgt.unsqueeze(1)).squeeze(1)[start - 1:]
        out.append(picked.mean().item() if picked.numel() else -1e9)
    return out


def choose(gloss: str, name_a: str, name_b: str, *, device: str = "cuda") -> int:
    """0 if the gloss reads as name_a, 1 if name_b."""
    sa, sb = _score(gloss, [name_a, name_b], device)
    return 0 if sa >= sb else 1


def choose_n(gloss: str, names: list[str], *, device: str = "cuda") -> int:
    """Index of the best-scoring candidate among many."""
    scores = _score(gloss, names, device)
    return max(range(len(names)), key=lambda i: scores[i])


def audit_pairs(items: list[tuple[str, str, str, int]], *,
                device: str = "cuda", limit: int | None = None) -> AuditResult:
    """items: (gloss, name_a, name_b, correct_index). Returns agreement."""
    rows = items[:limit] if limit else items
    correct = 0
    for gloss, a, b, gold in rows:
        if choose(gloss, a, b, device=device) == gold:
            correct += 1
    return AuditResult(n=len(rows), correct=correct)


def audit_coarse(items: list[tuple[str, list[str], int]], *,
                 device: str = "cuda") -> AuditResult:
    """items: (gloss, candidate_names, correct_index).

    COARSE discrimination against SEMANTICALLY DISTANT distractors, which is the
    task the anti-cipher job actually needs. The auditor never has to tell "the
    light's side" from "the night's side" -- those are two readings of one scene
    and a 1.5B base model measured at chance on them (48.3%,
    runs/auditor_validation.json).

    What it must detect is a gloss that says NOTHING DESCRIPTIVE AT ALL. A
    ciphered utterance carries no imagery, so it cannot beat chance even against
    distractors drawn from unrelated territory -- while an honest one can.
    """
    correct = 0
    for gloss, names, gold in items:
        if choose_n(gloss, names, device=device) == gold:
            correct += 1
    return AuditResult(n=len(items), correct=correct)
