"""TWO SPEAKERS, ONE BASE MODEL — and a spy that proves they are actually two.

⛔⛔ THE THIRD DISGUISE OF THE ARC'S ORIGINAL BUG. `LocalBackend` loads a full
7B base per instance (~26 GB observed), so two of them do not fit on a 40 GB
card. The fix is to load the base ONCE and attach both LoRAs, switching with
`set_adapter` per turn.

But that reintroduces the fault it is meant to avoid, in a form that looks
*more* correct than before: two adapter paths on the command line, two labels,
two distinct backend objects — and if `set_adapter` silently no-ops or is not
called per turn, **one set of weights generates both sides of the conversation.**
That is one impression talking to itself again, and `_assert_two` would pass it,
because the objects genuinely differ.

⭐ SO THE SWITCH IS ASSERTED, NOT TRUSTED:
  · every activation reads `active_adapter` BACK from the model and raises if it
    is not what was requested — an operation that can silently do nothing needs
    an assertion that it did something;
  · every activation is appended to `switches`, so a test (and the run itself)
    can prove the two speakers alternated instead of one monopolising the model.
"""
from __future__ import annotations


class AdapterSwitchError(RuntimeError):
    """The requested LoRA is not the one that ended up active."""


class DualAdapterCore:
    """The switching logic, isolated from torch so it can be red-proofed offline.

    `model` need only expose `set_adapter(name)` and an `active_adapter`
    attribute — which is exactly the PEFT surface, and exactly what a fake can
    provide in a test.
    """

    def __init__(self, model, names):
        if len(set(names)) != 2:
            raise ValueError("a dual-adapter model needs TWO DISTINCT adapter "
                             "names; got %r — identical speakers cannot "
                             "converge" % (names,))
        self.model = model
        self.names = tuple(names)
        self.switches: list[str] = []

    def activate(self, name: str) -> None:
        if name not in self.names:
            raise ValueError("unknown adapter %r, have %r" % (name, self.names))
        self.model.set_adapter(name)
        # ⛔ READ IT BACK. `set_adapter` returning None is not evidence.
        active = getattr(self.model, "active_adapter", None)
        if isinstance(active, (list, tuple)):
            active = active[0] if len(active) == 1 else active
        if active != name:
            raise AdapterSwitchError(
                "asked for adapter %r but %r is active — both speakers would "
                "have generated from one set of weights" % (name, active))
        self.switches.append(name)

    # ── what a run can assert about itself ──────────────────────────────────
    def alternated(self) -> bool:
        """Did the two speakers actually take turns?"""
        return all(a != b for a, b in zip(self.switches, self.switches[1:]))

    def usage(self) -> dict:
        return {n: self.switches.count(n) for n in self.names}

    def assert_two_speakers_spoke(self) -> None:
        """⛔⛔ THE RUN-TIME GUARD. A transcript where one adapter never
        activated is one impression and a mirror, whatever the CLI said."""
        u = self.usage()
        missing = [n for n, c in u.items() if c == 0]
        if missing:
            raise AdapterSwitchError(
                "adapter(s) %r never generated a turn — this is one speaker "
                "wearing two labels (usage %r)" % (missing, u))
        if not self.alternated():
            raise AdapterSwitchError(
                "the adapters did not alternate; one side generated "
                "consecutive turns (usage %r)" % (u,))


def build_dual(model_id, adapter_a, adapter_b, *, temperature, max_new_tokens=256):
    """Load the base ONCE, attach both LoRAs, return (core, tokenizer, model).

    ⭐ Memory: one base (~15 GB bf16) plus two small LoRAs, instead of two full
    bases (~52 GB) which does not fit on a 40 GB card.
    """
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_id)
    base = AutoModelForCausalLM.from_pretrained(
        model_id, dtype=torch.bfloat16, device_map="cuda")
    model = PeftModel.from_pretrained(base, adapter_a, adapter_name="A")
    model.load_adapter(adapter_b, adapter_name="B")
    model.eval()
    return DualAdapterCore(model, ("A", "B")), tok, model


def dual_views(model_id, adapter_a, adapter_b, *, temperature,
               max_new_tokens=256, labels=("A", "B")):
    """Two Backend-compatible views over ONE loaded base model.

    ⭐ Subclasses `LocalBackend` rather than reimplementing `call()`, so the
    JSON extraction, the untruncated-raw-on-failure behaviour and the cost log
    stay on the single tested path. Only two things are added: the adapter is
    activated (and read back) before each generation, and the model/tokenizer
    are injected instead of loaded.
    """
    from act2_backends import LocalBackend

    core, tok, model = build_dual(model_id, adapter_a, adapter_b,
                                  temperature=temperature,
                                  max_new_tokens=max_new_tokens)

    class _View(LocalBackend):
        def __init__(self, adapter_name, label):
            self.model_id = model_id
            self.name = "dual:%s" % label
            self.constrained = False
            self.max_new_tokens = max_new_tokens
            self.temperature = temperature
            self.calls = []
            self.tok = tok
            self.model = model
            self._core = core
            self._adapter = adapter_name

        def call(self, **kw):
            # ⛔⛔ Activate FIRST, and `activate` reads the adapter back. If the
            # switch silently no-ops, this raises instead of quietly generating
            # both sides of the conversation from one set of weights.
            self._core.activate(self._adapter)
            return super().call(**kw)

    return core, _View("A", labels[0]), _View("B", labels[1])
