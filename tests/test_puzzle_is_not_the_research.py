"""⛔⛔ THE ANTI-DRIFT GUARD, AND IT IS HERE BECAUSE THE DRIFT ALREADY HAPPENED.

Tlön is three separable things: the PUZZLE (a chat app — perceive and speak),
the ART PIECE (which needs release, in the weights, perpetually) and the
RESEARCH (which measures whether release installs). They were one thing for
months, and the puzzle stayed hostage to an unresolved research question until
Nate separated them.

The failure mode is not that someone deliberately merges them. It is that the
research code is RIGHT THERE, imports cleanly, and reaches for the same model —
so a plausible edit ("while we're here, let's log the lag") quietly makes a
chat app depend on an instrument, and the next person cannot tell which of the
two a number came from.

⭐ So this test states the boundary as a machine-checkable fact: the puzzle may
import the GRAMMAR, the TRAINED PROMPTS and the LOCAL BACKEND, and nothing else
from the campaign.

⛔ IT WALKS THE AST, NOT THE TEXT. Every module in `puzzle/` names these
forbidden modules in its prose — that is what the prose is FOR — and a
text search would fire on the explanation instead of the import. This repo has
made that exact mistake twice, once grepping `ast.dump` output which includes
docstrings. Only `Import` / `ImportFrom` nodes are read.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PUZZLE = ROOT / "puzzle"

#: What the puzzle is allowed to reach for, and the reason each one is allowed.
ALLOWED_PREFIXES = {
    "tlon.grammar":       "parse/gloss/lexicon — the translate button is these",
    "tlon.product":       "the gate, the literary render, the door bound",
    "tlon.discourse":     "the provocation DIRECTION name, imported not spelt",
    "tlon.act2.llm":      "BackendError and the Backend protocol",
    "tlon.act2.chat_shape": "read_prompt — the ONE fold with the trainer's "
                            "prompt construction, so an empty bench is "
                            "byte-identical to the single-turn path",
    "tlon.act2.schema_bridge": "the scene schema the gate validates against",
    # ⛔ DEV-ONLY, AND THE NARROWEST ENTRY HERE. `mock_speaker` draws
    # already-validated surfaces from the probe generator so the skeleton emits
    # REAL Tlön with no model — which is what keeps `parse`, `gloss` and the
    # translate button exercised instead of stubbed. It is the only puzzle file
    # that may import it, and `mock_speaker.enabled()` refuses to run in a
    # deployed environment at all, so this never reaches a visitor.
    "tlon.act2.probes":   "the probe generator — MOCK SPEAKER ONLY, dev-only, "
                          "refuses to start in a deployed environment. Import "
                          "the LEAF: `from tlon.act2 import probes` registers "
                          "as `tlon.act2` and would allow-list the whole "
                          "research package.",
    "act2_backends":      "LocalBackend — owned weights, the $0.00 path",
    "act2_finetune":      "SYSTEM — the TRAINED prompts, never re-spelt",
    "tlon_converse":      "the turn shape, imported not re-spelt",
}

#: ⛔ Naming the research modules explicitly rather than banning `tlon.act2.*`
#: wholesale: a blanket ban would have to be weakened the first time the puzzle
#: legitimately needs something from that package, and a weakened guard is worse
#: than a narrow one. Narrow the guard; don't weaken it.
FORBIDDEN = {
    "act2_model_lag":     "lag/persistence measurement — research",
    "act2_audit_readings": "the readings audit gate — research",
    "act2_finetune_dose_curve": "the dose curve — research",
    "act2_watchdog":      "remote box control — research",
    "act2_box_persist":   "artifact persistence — research",
    "act2_provision":     "Lambda provisioning — research",
    "act2_dual_backend":  "two-speaker exchange — the ART PIECE, not this",
    "tlon.act2.weight_delta": "the dose — research",
    "tlon.act2.dose_curve": "the dose curve — research",
    "tlon.act2.falsify":  "F-LOCAL and the verdict axes — research",
}


def _modules(path: pathlib.Path) -> set[str]:
    """Every module name this file imports. AST only — never the prose."""
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            # ⛔ A relative import (`from . import guard`) has module None and a
            # level > 0; it is inside the package and is not a campaign import.
            if node.level == 0 and node.module:
                names.add(node.module)
    return names


def _puzzle_files() -> list[pathlib.Path]:
    return sorted(p for p in PUZZLE.rglob("*.py"))


def test_there_are_puzzle_modules_to_check():
    """⛔ A guard that silently checks nothing is the vacuous pass this repo
    keeps paying for. If the glob ever returns empty, every test below passes
    by having no work to do."""
    assert len(_puzzle_files()) >= 4


@pytest.mark.parametrize("path", _puzzle_files(), ids=lambda p: p.name)
def test_the_puzzle_does_not_import_the_research(path):
    imported = _modules(path)
    hits = sorted(m for m in imported
                  if any(m == f or m.startswith(f + ".") for f in FORBIDDEN))
    assert not hits, (
        "⛔⛔ %s imports research code: %s\n"
        "   The puzzle is a chat app. It perceives English and speaks Tlön. "
        "If it now needs a measurement, that belongs to the research or the "
        "art piece — which are different products with different gates."
        % (path.name, ", ".join("%s (%s)" % (h, FORBIDDEN[h.split('.')[0]]
                                             if h.split('.')[0] in FORBIDDEN
                                             else FORBIDDEN.get(h, "research"))
                                for h in hits)))


@pytest.mark.parametrize("path", _puzzle_files(), ids=lambda p: p.name)
def test_every_campaign_import_is_on_the_allow_list(path):
    """⭐ The stronger form. The ban list above can only stop what it enumerated;
    this refuses anything from the campaign that was never argued for."""
    imported = _modules(path)
    campaign = {m for m in imported
                if m.split(".")[0] in ("tlon", "tools")
                or m.startswith("act2_") or m == "tlon_converse"}
    unlisted = sorted(m for m in campaign
                      if not any(m == a or m.startswith(a + ".")
                                 for a in ALLOWED_PREFIXES))
    assert not unlisted, (
        "⛔ %s imports campaign modules that are not on the allow list: %s\n"
        "   Add it with a one-line reason, or do not import it."
        % (path.name, ", ".join(unlisted)))


@pytest.mark.parametrize("path", _puzzle_files(), ids=lambda p: p.name)
def test_the_probe_generator_is_the_MOCKS_alone(path):
    """⛔⛔ NARROW THE GUARD, DO NOT WEAKEN IT — this file's own rule, applied
    to its own allow list.

    `tlon.act2.probes` was added so the MOCK speaker could emit real, validated
    Tlön with no model. But an allow-list entry is granted to every file in the
    package, so on its own it quietly licenses the shipped server to import the
    research probe generator too. It does not: the mock is dev-only and refuses
    to start in a deployed environment, and nothing that CAN reach a visitor may
    depend on it.
    """
    if path.name == "mock_speaker.py":
        return
    assert not any(m == "tlon.act2.probes"
                   or m.startswith("tlon.act2.probes.")
                   for m in _modules(path)), (
        "⛔ %s imports tlon.act2.probes. That entry exists for the dev-only "
        "mock speaker; a file that can serve a visitor must not depend on the "
        "research probe generator." % path.name)


def test_no_anthropic_backend_anywhere_in_the_puzzle():
    """⛔⛔ THE SPEC IS EXPLICIT: this is freeware and a per-request API bill is
    prohibitive. The weights are ours and they run on the box. `AnthropicBackend`
    sits in the same module as `LocalBackend`, one identifier away."""
    for path in _puzzle_files():
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "act2_backends":
                names = {a.name for a in node.names}
                assert "AnthropicBackend" not in names, (
                    "⛔⛔ %s imports AnthropicBackend — the puzzle pays per "
                    "request and it is meant to be free" % path.name)
            if isinstance(node, ast.Name) and node.id == "AnthropicBackend":
                pytest.fail("⛔⛔ %s references AnthropicBackend" % path.name)
