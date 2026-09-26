"""⛔⛔ THE SERVED ADAPTER IS v1, AND THE IMAGE AGREES WITH THE CODE.

`puzzle/speaker.py` names a default adapter. `puzzle/Dockerfile` COPIES a
directory and sets `TLON_ADAPTER`. Those are three separate statements of the
same fact, in two files, and nothing made them agree.

⛔⛤ THEY WERE WRONG FOR EIGHT DAYS. All three said `ct-s20624` — the research
campaign's content-transient cell, picked on 2026-09-15 before the puzzle
speaker existed and never measured on carry at all, because no model-side carry
probe existed until 2026-09-23. Every test in this repo stayed green the whole
time: a default that outlives the evidence it was chosen on is invisible to a
suite that only checks the code does what the code says.

⭐ v1 is `dosed-s20624`, chosen on three measured axes at n=256 — render 97.3%,
carry 27.5%, choose 46.5% — and strictly dominant over the other legal
adapters. See `speaker.py` for the comparison.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEAKER = ROOT / "puzzle" / "speaker.py"
DOCKERFILE = ROOT / "puzzle" / "Dockerfile"

#: ⛔ The cell this product serves. Changing it is a product decision and must
#: be made HERE as well as in the two files below, so it cannot be done by
#: accident in one of them.
V1_CELL = "force-s20624"


def _uncommented(path: pathlib.Path) -> str:
    """The file with its prose removed.

    ⛔ Both files EXPLAIN the old cell by name — that is what the prose is for —
    and a raw search would fire on the explanation. This repo has made that
    mistake twice.
    """
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        out.append(line.split("#")[0] if path.suffix != ".py" else line)
    return "\n".join(out)


def test_the_speaker_default_is_v1():
    body = _uncommented(SPEAKER)
    m = re.search(r'"puzzle_speaker"\s*/\s*"([^"]+)"', body)
    assert m, "could not find the default adapter path in speaker.py"
    assert m.group(1) == V1_CELL, (
        "⛔⛔ puzzle/speaker.py serves %r, not v1 (%r)." % (m.group(1), V1_CELL))


def test_the_image_copies_and_names_the_same_cell():
    """⛔⛔ THE DRIFT THAT SHIPS LAST MONTH'S WEIGHTS. A COPY of one cell with
    an ENV naming another either fails loudly at load — the good outcome — or,
    if the old directory happens to be present too, serves the wrong adapter
    while everything reports healthy."""
    body = _uncommented(DOCKERFILE)
    copied = re.search(r"COPY\s+runs/puzzle_speaker/([^/\s]+)/", body)
    named = re.search(r"TLON_ADAPTER=/app/speaker/([^\s\\]+)", body)
    assert copied and named, "Dockerfile no longer states both halves"
    assert copied.group(1) == named.group(1), (
        "⛔⛔ Dockerfile COPIES %r but sets TLON_ADAPTER to %r."
        % (copied.group(1), named.group(1)))
    assert copied.group(1) == V1_CELL, (
        "⛔⛔ the image bakes %r, not v1 (%r)." % (copied.group(1), V1_CELL))


def test_the_weights_are_actually_present_for_that_cell():
    """⛔ A correct name over an empty directory is the `s20620` failure: the
    transfer produced a directory and said nothing. `Speaker.load()` refuses on
    a missing safetensors, but by then a box is already up."""
    d = ROOT / "runs" / "puzzle_speaker" / V1_CELL
    if not d.is_dir():
        import pytest
        pytest.skip("%s not pulled in this checkout" % V1_CELL)
    w = d / "adapter_model.safetensors"
    assert w.is_file() and w.stat().st_size > 100_000_000, (
        "⛔ %s exists but holds no usable weights (%s)"
        % (d, w.stat().st_size if w.exists() else "absent"))


def test_the_old_cell_is_not_still_named_in_live_code():
    """⛔ The prose may — and should — explain what changed and why. The CODE
    may not still reach for it."""
    for path in (SPEAKER, DOCKERFILE):
        body = _uncommented(path)
        assert "ct-s20624" not in body, (
            "⛔⛔ %s still names ct-s20624 outside its prose." % path.name)
