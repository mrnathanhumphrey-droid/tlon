"""Train the listener and score it exactly as PREREG 080bc40f specifies."""
from __future__ import annotations
import random
from dataclasses import dataclass

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from .data import Example
from .model import Listener


@dataclass
class TrainCfg:
    epochs: int = 12
    batch: int = 256
    lr: float = 3e-4
    weight_decay: float = 0.01
    warmup: float = 0.05
    seed: int = 20260820
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    patience: int = 3


def _tensors(rows: list[Example]) -> TensorDataset:
    X = torch.tensor([r.ids for r in rows], dtype=torch.long)
    y = torch.tensor([r.label for r in rows], dtype=torch.long)
    return TensorDataset(X, y)


@torch.no_grad()
def predict(model: nn.Module, rows: list[Example], cfg: TrainCfg,
            batch: int = 1024) -> torch.Tensor:
    model.eval()
    out = []
    X = torch.tensor([r.ids for r in rows], dtype=torch.long)
    for i in range(0, len(X), batch):
        out.append(model(X[i:i + batch].to(cfg.device)).argmax(1).cpu())
    return torch.cat(out) if out else torch.empty(0, dtype=torch.long)


@torch.no_grad()
def logits(model: nn.Module, rows: list[Example], cfg: TrainCfg,
           batch: int = 1024) -> torch.Tensor:
    model.eval()
    out = []
    X = torch.tensor([r.ids for r in rows], dtype=torch.long)
    for i in range(0, len(X), batch):
        out.append(model(X[i:i + batch].to(cfg.device)).cpu())
    return torch.cat(out)


def train(train_rows: list[Example], val_rows: list[Example], n_classes: int,
          cfg: TrainCfg | None = None, *, verbose: bool = True) -> Listener:
    cfg = cfg or TrainCfg()
    torch.manual_seed(cfg.seed)
    random.seed(cfg.seed)

    model = Listener(n_classes).to(cfg.device)
    dl = DataLoader(_tensors(train_rows), batch_size=cfg.batch, shuffle=True,
                    drop_last=False)
    steps = cfg.epochs * len(dl)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr,
                            weight_decay=cfg.weight_decay)
    warm = max(1, int(steps * cfg.warmup))
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: (s + 1) / warm if s < warm
        else 0.5 * (1 + torch.cos(torch.tensor(
            (s - warm) / max(1, steps - warm) * 3.14159265)).item()))
    lossf = nn.CrossEntropyLoss(label_smoothing=0.05)

    best, best_state, bad = -1.0, None, 0
    for ep in range(cfg.epochs):
        model.train()
        tot = 0.0
        for xb, yb in dl:
            xb, yb = xb.to(cfg.device), yb.to(cfg.device)
            opt.zero_grad(set_to_none=True)
            loss = lossf(model(xb), yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            tot += loss.item() * xb.size(0)
        pred = predict(model, val_rows, cfg)
        acc = (pred == torch.tensor([r.label for r in val_rows])).float().mean().item()
        if verbose:
            print(f"    epoch {ep + 1:2d}  loss {tot / len(train_rows):.4f}  "
                  f"val {100 * acc:.2f}%")
        if acc > best:
            best, bad = acc, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= cfg.patience:
                if verbose:
                    print(f"    early stop at epoch {ep + 1}")
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model
