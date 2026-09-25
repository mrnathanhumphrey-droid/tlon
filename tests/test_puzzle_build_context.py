"""⛔⛔ THE IMAGE MUST CARRY THE ADAPTER, AND NOTHING ELSE FROM `runs/`.

`puzzle/Dockerfile` COPIES repo-root-relative paths, so the build context is the
repository root — and the root holds `runs/`, which is 26 GB of adapters,
corpora, ledgers and logs. Docker uploads the whole context before it reads the
first COPY. The image needs 309 MB of it.

⛔ BOTH WAYS THIS GOES WRONG ARE EXPENSIVE AND NEITHER LOOKS WRONG:
  * no `.dockerignore` at all — a 26 GB upload that does not fail fast, it
    crawls and then times out after a long time spent resembling progress;
  * an over-broad one — `runs/` excluded without re-including the served cell,
    so the image builds clean and small and `Speaker.load()` refuses at boot,
    on a GPU machine that has already been paid for and deployed.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
IGNORE = ROOT / ".dockerignore"
DOCKERFILE = ROOT / "puzzle" / "Dockerfile"


@pytest.fixture(scope="module")
def rules() -> list[str]:
    assert IGNORE.exists(), (
        "⛔⛔ no .dockerignore — the build context is the repo root and `runs/` "
        "is 26 GB")
    return [ln.strip() for ln in IGNORE.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")]


def _served_cell() -> str:
    """The cell the Dockerfile actually bakes. ⛔ Read from the Dockerfile, not
    spelt again here: a constant repeated in a test is a constant that can
    disagree with the thing it guards."""
    code = "\n".join(ln for ln in DOCKERFILE.read_text(encoding="utf-8").splitlines()
                     if not ln.lstrip().startswith("#"))
    m = re.search(r"COPY\s+runs/puzzle_speaker/([^/\s]+)/", code)
    assert m, "the Dockerfile no longer bakes an adapter"
    return m.group(1)


def test_runs_is_excluded(rules):
    """⛔ The 26 GB. Without this line the upload is the whole project."""
    assert any(r.rstrip("/") in ("runs", "runs/*") for r in rules), (
        "⛔⛔ .dockerignore does not exclude runs/ — the context is 26 GB")


def test_the_served_cell_is_re_included(rules):
    """⛔⛔ THE FAILURE THAT SURVIVES A CLEAN BUILD. Excluding `runs/` without
    re-including the served cell produces a small, fast, successful image with
    no weights in it. `Speaker.load()` refuses naming the path — at boot, on a
    machine already deployed and billing.

    ⛔ Docker cannot re-include a path whose PARENT is excluded, so the
    directories must be opened one level at a time. A single
    `!runs/puzzle_speaker/dosed-s20624/` after `runs/*` does NOT work, and it
    reads as though it does.
    """
    cell = _served_cell()
    joined = "\n".join(rules)
    assert "!runs/puzzle_speaker/" in joined, (
        "⛔ runs/puzzle_speaker/ is never re-included, so the cell below it "
        "cannot be either")
    assert "runs/puzzle_speaker/*" in joined, (
        "⛔ the intermediate level is not opened — docker cannot re-include a "
        "child of an excluded directory")
    assert ("!runs/puzzle_speaker/%s/" % cell) in joined, (
        "⛔⛔ .dockerignore re-includes a different cell than the Dockerfile "
        "bakes (%r). The image would build clean and ship WITHOUT WEIGHTS." % cell)


def test_the_re_included_cell_actually_holds_weights():
    """⛔ A correct name over an empty directory is the `s20620` failure. The
    rules can be perfect and the file still absent from this checkout."""
    cell = _served_cell()
    d = ROOT / "runs" / "puzzle_speaker" / cell
    if not d.is_dir():
        pytest.skip("%s not pulled in this checkout" % cell)
    w = d / "adapter_model.safetensors"
    assert w.is_file() and w.stat().st_size > 100_000_000


def test_credentials_and_machine_state_never_enter_the_context(rules):
    """⛔⛔ A BUILD CONTEXT IS NOT A PRIVATE CHANNEL. Every layer is readable by
    anyone who can pull the image, and `runs/**/INSTANCE.json` carries live
    instance ids while `.env` carries keys."""
    # ⛔⛤ THIS COMPARED SUBSTRINGS AND A MUTANT DELETING `.env` SURVIVED IT,
    # because `.env.*` on the next line still contains the text `.env`. The
    # rules are matched as WHOLE LINES now. A containment check against a
    # blob of rules can be satisfied by a rule that is not the one meant.
    for secret in (".env", "**/INSTANCE.json"):
        assert secret in rules, (
            "⛔ %r is not excluded from the image (rules: %r)" % (secret, rules))


def test_the_tests_do_not_ship(rules):
    """⭐ Not a security matter — the suite is 2,300 files of fixtures and
    corpora references that the served app never imports."""
    assert any(r.rstrip("/") == "tests" for r in rules)
