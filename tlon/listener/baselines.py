"""Pre-registered baselines. These run BEFORE the transformer.

KILL 1 can fire here: if bag-of-roots comes within 2 points of the model, the
task is solved by root identity alone. Running it first means that kill costs
minutes, not a training run.

Bag-of-roots deliberately throws away everything the grammar adds -- order,
relators, orientations, aspect, degree, modality, nesting -- and keeps only the
MULTISET OF ROOTS. If that suffices, the language's structure is decorative for
this task and the referent set is the thing that needs fixing.
"""
from __future__ import annotations
import random

import torch
import torch.nn as nn

from . import tokenizer as tk
from .data import Example


def _bag(examples: list[Example], root_ids: list[int]) -> torch.Tensor:
    idx = {r: i for i, r in enumerate(root_ids)}
    X = torch.zeros(len(examples), len(root_ids))
    for row, ex in enumerate(examples):
        for t in ex.ids:
            j = idx.get(int(t))
            if j is not None:
                X[row, j] += 1.0
    return X


def _fit_logreg(X, y, n_classes: int, *, epochs: int = 300, lr: float = 0.5,
                seed: int = 0, device: str = "cpu") -> nn.Module:
    torch.manual_seed(seed)
    model = nn.Linear(X.shape[1], n_classes).to(device)
    opt = torch.optim.LBFGS(model.parameters(), lr=lr, max_iter=epochs)
    lossf = nn.CrossEntropyLoss()
    X, y = X.to(device), y.to(device)

    def closure():
        opt.zero_grad()
        loss = lossf(model(X), y)
        loss.backward()
        return loss
    opt.step(closure)
    return model


def _acc(model, X, y) -> float:
    with torch.no_grad():
        return (model(X).argmax(1) == y).float().mean().item()


def majority(train: list[Example], test: list[Example]) -> float:
    counts: dict[int, int] = {}
    for ex in train:
        counts[ex.label] = counts.get(ex.label, 0) + 1
    top = max(counts, key=counts.get)
    return sum(ex.label == top for ex in test) / max(1, len(test))


def bag_of_roots(train: list[Example], tests: dict[str, list[Example]],
                 n_classes: int) -> dict:
    roots = sorted(tk.root_ids())
    Xtr = _bag(train, roots)
    ytr = torch.tensor([e.label for e in train])
    model = _fit_logreg(Xtr, ytr, n_classes)
    out = {"train": _acc(model, Xtr, ytr)}
    preds = {}
    for name, te in tests.items():
        if not te:
            out[name] = float("nan")
            continue
        Xte = _bag(te, roots)
        yte = torch.tensor([e.label for e in te])
        out[name] = _acc(model, Xte, yte)
        with torch.no_grad():
            preds[name] = model(Xte).argmax(1).tolist()
    out["_preds"] = preds
    return out


def shuffled_label_null(train: list[Example], test: list[Example],
                        n_classes: int, seed: int = 13) -> float:
    """Must land at chance. If it does not, the pipeline leaks."""
    rng = random.Random(seed)
    labels = [e.label for e in train]
    rng.shuffle(labels)
    roots = sorted(tk.root_ids())
    Xtr = _bag(train, roots)
    model = _fit_logreg(Xtr, torch.tensor(labels), n_classes)
    Xte = _bag(test, roots)
    yte = torch.tensor([e.label for e in test])
    return _acc(model, Xte, yte)
