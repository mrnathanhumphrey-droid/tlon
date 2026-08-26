"""CONCRETE BACKENDS for Act 2 step 2. ⛔ THESE SPEND. Deliberately outside
`tlon/act2/`, which is tested to be unable to reach a network at all.

⛔⛔ THE BUDGET IS A HARD CEILING, NOT A REPORT. `BudgetExceeded` is raised the
moment the next call would cross the authorised figure, so a run cannot quietly
overspend while nobody is watching the terminal. A cost report printed after the
fact tells you what you already cannot undo; this stops before it.

⭐ The system prompt is identical across every call of a kind, so it is marked
for prompt caching. Measured effect (tools/act2_cost.py): roughly a 2.2×
reduction on the full spec.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.act2.llm import BackendError                        # noqa: E402

PRICES = {"claude-sonnet-5": (3.00, 15.00),
          "claude-haiku-4-5": (1.00, 5.00),
          "claude-opus-5": (15.00, 75.00)}


class BudgetExceeded(RuntimeError):
    """The authorised spend would be crossed by the next call. Nothing sent."""


#: A forced choice given as a bare index -- `2` or `[2]` -- and NOTHING ELSE.
#: ⛔ DELIBERATELY STRICT, ANCHORED AT BOTH ENDS. The whole generation must be
#: the answer. "I think [2] is right" and "between [1] and [3]" both still fail,
#: because a tolerant parser here would launder prose into a comprehension score
#: and inflate the very number AMENDMENT A gates on.
_INDEX_ONLY = re.compile(r"^\s*\[?\s*(\d{1,2})\s*\]?\s*[.)]?\s*$")


def _bare_index(gen: str, kind: str) -> int:
    """Read an index-only answer, or refuse.

    ⛔⛔ THIS EXISTS BECAUSE THE MODEL WAS RIGHT AND THE HARNESS WAS WRONG. The
    CHOOSE prompt asked for "the index of the correct reading" and the model
    returned `[0]`; only the backend demanded JSON. Scoring that as "could not
    answer" put comprehension BELOW chance and made AMENDMENT A's band
    unreachable. Reading the answer the model actually gave is a repair to the
    instrument, not a loosening of the bar.
    """
    m = _INDEX_ONLY.match(gen)
    if not m:
        raise BackendError(
            f"no JSON object and no bare index in the generation for {kind}: "
            f"{gen[:120]!r}")
    return int(m.group(1))


class AnthropicBackend:
    """Hosted. ⛔ Requires an explicit `budget_usd` — there is no default,
    because a run that can spend without a stated ceiling is a run nobody
    authorised a figure for."""

    def __init__(self, model: str, *, budget_usd: float,
                 max_tokens: int = 400, cache: bool = True):
        try:
            import anthropic
        except ImportError as exc:                    # pragma: no cover
            raise BackendError("pip install anthropic") from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise BackendError("ANTHROPIC_API_KEY is not set.")
        if model not in PRICES:
            raise BackendError(f"{model!r}: declare its price before using it.")
        if budget_usd <= 0:
            raise BackendError("budget_usd must be positive and explicit.")
        self._client = anthropic.Anthropic()
        self.model = model
        self.name = f"anthropic:{model}"
        self.budget = float(budget_usd)
        self.max_tokens = max_tokens
        self.cache = cache
        self.usage: list[dict] = []

    # -- the ceiling ---------------------------------------------------
    def spent(self) -> float:
        pin, pout = PRICES[self.model]
        return sum(u["input"] / 1e6 * pin + u["output"] / 1e6 * pout
                   for u in self.usage)

    def _check(self) -> None:
        if self.spent() >= self.budget:
            raise BudgetExceeded(
                f"{self.name}: ${self.spent():.2f} spent of ${self.budget:.2f} "
                f"authorised over {len(self.usage)} calls. Stopping before the "
                "next one. Raise the budget deliberately or reduce the run.")

    def call(self, *, system: str, user: str, schema: dict, kind: str) -> dict:
        self._check()
        sys_block = [{"type": "text", "text": system}]
        if self.cache:
            sys_block[0]["cache_control"] = {"type": "ephemeral"}
        tool = {"name": "emit", "description": f"Act 2 {kind}",
                "input_schema": schema}
        msg = self._client.messages.create(
            model=self.model, max_tokens=self.max_tokens, system=sys_block,
            tools=[tool], tool_choice={"type": "tool", "name": "emit"},
            messages=[{"role": "user", "content": user}])
        u = msg.usage
        self.usage.append({
            "kind": kind, "input": u.input_tokens, "output": u.output_tokens,
            "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
            "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0})
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use":
                return dict(block.input)
        raise BackendError(f"no tool call returned for {kind}: {msg.content!r}")

    def cost_report(self) -> dict:
        by_kind: dict[str, int] = {}
        for u in self.usage:
            by_kind[u["kind"]] = by_kind.get(u["kind"], 0) + 1
        return {"calls": len(self.usage), "by_kind": by_kind,
                "input_tokens": sum(u["input"] for u in self.usage),
                "output_tokens": sum(u["output"] for u in self.usage),
                "cache_read": sum(u["cache_read"] for u in self.usage),
                "usd_total": self.spent(), "budget": self.budget,
                "budget_left": self.budget - self.spent()}


class LocalBackend:
    """⭐ THE $0.00 PATH — owned weights, the prereg's "runs on hardware you have".

    ⛔⛔ UNCONSTRAINED BY DEFAULT, AND THAT IS THE WHOLE POINT. Grammar-constrained
    decoding would make an illegal emission impossible, F-LOCAL would read 1.00
    by construction, and the number would describe the sampler. `constrained` is
    opt-in, `falsify.f_local` REFUSES to score a constrained run, and the flag is
    recorded on every result.

    ⛔ A malformed generation is NOT swallowed. It raises `BackendError`, the
    speaker returns None, and F-LOCAL counts it as a failure -- because "the
    model could not produce a Scene" is exactly what the gate is asking about.
    """

    def __init__(self, model_id: str, *, adapter: str | None = None,
                 device: str = "cuda", dtype: str = "bfloat16",
                 load_4bit: bool = False, max_new_tokens: int = 220,
                 constrained: bool = False, temperature: float = 0.0):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if constrained:
            print("⛔ CONSTRAINED DECODING IS ON. F-LOCAL cannot be scored from "
                  "this backend; falsify.f_local will refuse it.")
        self.model_id = model_id
        self.name = f"local:{pathlib.Path(model_id).name}"
        self.constrained = constrained
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.calls: list[dict] = []

        kw: dict = {"dtype": getattr(torch, dtype), "device_map": device}
        if load_4bit:
            from transformers import BitsAndBytesConfig
            kw["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True)
            kw.pop("dtype")
        self.tok = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, **kw)
        if adapter:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, adapter)
        self.model.eval()

    def _prompt(self, system: str, user: str) -> str:
        msgs = [{"role": "system", "content": system},
                {"role": "user", "content": user}]
        if getattr(self.tok, "chat_template", None):
            return self.tok.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=True)
        return f"{system}\n\n{user}\n\n"

    def call(self, *, system: str, user: str, schema: dict, kind: str) -> dict:
        import torch
        text = self._prompt(system, user)
        ids = self.tok(text, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            out = self.model.generate(
                **ids, max_new_tokens=self.max_new_tokens,
                do_sample=self.temperature > 0,
                temperature=self.temperature or None,
                pad_token_id=self.tok.pad_token_id or self.tok.eos_token_id)
        gen = self.tok.decode(out[0][ids["input_ids"].shape[1]:],
                              skip_special_tokens=True)
        # ⛔ The cost log keeps a short prefix for ACCOUNTING. That is not
        # evidence, and it must never be the only copy — see below.
        self.calls.append({"kind": kind, "raw": gen[:400],
                           "in_tokens": int(ids["input_ids"].shape[1]),
                           "out_tokens": int(out.shape[1] - ids["input_ids"].shape[1])})
        start, end = gen.find("{"), gen.rfind("}")
        if start < 0 or end <= start:
            if kind == "choose":
                return {"choice": _bare_index(gen, kind)}
            # ⛔⛔ THE RAW GOES WITH THE EXCEPTION, IN FULL. This raise is where
            # run 4's speak collapse became undiagnosable: 60 of 61 failures
            # arrived here, the text was dropped, and `proposal: null` was all
            # the ledger kept. `raw=gen` is UNTRUNCATED on purpose — a 400-char
            # clip cannot show a generation that ran long, which is one of the
            # live hypotheses about why this fires.
            raise BackendError(f"no JSON object in the generation for {kind}",
                               raw=gen, kind=kind)
        try:
            return json.loads(gen[start:end + 1])
        except json.JSONDecodeError as exc:
            raise BackendError(f"malformed JSON for {kind}: {exc}",
                               raw=gen, kind=kind) from exc

    def cost_report(self) -> dict:
        return {"calls": len(self.calls), "usd_total": 0.0,
                "input_tokens": sum(c["in_tokens"] for c in self.calls),
                "output_tokens": sum(c["out_tokens"] for c in self.calls),
                "constrained": self.constrained, "model": self.model_id}
