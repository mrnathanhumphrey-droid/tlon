"""The listener: a from-scratch transformer encoder. ~5M params, random init.

Small on purpose. Syntax and semantics are exact Python (FSM + LL(1) parser), so
the model's only job is reference resolution over <=26-token sequences in a
234-symbol closed vocabulary. That is not an 8B job. Every lever here -- vocab,
init, depth, width -- is ours.
"""
from __future__ import annotations
import math

import torch
import torch.nn as nn

from . import tokenizer as tk


class Listener(nn.Module):
    def __init__(self, n_classes: int, d_model: int = 256, n_layers: int = 6,
                 n_heads: int = 8, d_ff: int = 1024, dropout: float = 0.1,
                 max_len: int = tk.MAX_LEN):
        super().__init__()
        self.pad = tk.vocab()[tk.PAD]
        self.embed = nn.Embedding(tk.size(), d_model, padding_idx=self.pad)
        self.pos = nn.Parameter(torch.zeros(1, max_len, d_model))
        nn.init.normal_(self.pos, std=0.02)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_ff,
            dropout=dropout, batch_first=True, norm_first=True,
            activation="gelu")
        self.enc = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, n_classes)
        self.apply(self._init)

    @staticmethod
    def _init(m):
        if isinstance(m, nn.Linear):
            nn.init.trunc_normal_(m.weight, std=0.02)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.Embedding):
            nn.init.trunc_normal_(m.weight, std=0.02)

    def forward(self, ids: torch.Tensor) -> torch.Tensor:
        mask = ids.eq(self.pad)
        x = self.embed(ids) * math.sqrt(self.embed.embedding_dim)
        x = x + self.pos[:, : ids.size(1)]
        x = self.enc(x, src_key_padding_mask=mask)
        return self.head(self.norm(x[:, 0]))          # [CLS]

    def n_params(self) -> int:
        return sum(p.numel() for p in self.parameters())
