"""⛔⛔ A CALL-SITE TEST THAT REQUIRES YOU TO LIST THE SITES HAS THE WIRING'S OWN
BLIND SPOT.

WHY THIS EXISTS, AND IT IS THE FOURTH INSTANCE OF ONE CLASS. The §4.1 pooled
fraction test is invalid for mapping scope. It was fixed:

  1. in `act2_fullft_verdict.py`               (`757c157`)
  2. and `tests/test_call_site_coverage.py` was written to stop exactly this
     class recurring — by enumerating the VERDICT call sites               (`fb7962f`)
  3. ...and the SAME GATE in `act2_finetune.py` was never touched, because the
     author did not think of it — so the identical false FAULT fired inside the
     trainer, returned rc=3, and halted `miscurve75-s20624` before any verdict
     could apply the fix. ~$7.70.

⭐⭐ THE LESSON IS ABOUT THE TEST, NOT THE BUG. An author-maintained list of call
sites catches partial wiring **only among the sites the author already
remembered** — and the bug is always the site they did not. The list and the
wiring share one blind spot, which is why the list caught three instances and
missed the fourth.

⛔ So this test does not check a list. It **finds** the sites: walk every module
under `tools/` and `tlon/`, and flag every `if` whose test compares against a
weight-delta verdict constant. A gate added in a file nobody thought about is
found because the scan does not depend on anybody thinking about it.

⭐ The same move as the flush fix: that bug was not solved by a longer list of
filenames but by *patterns plus a trap over every exit*. Here it is not solved by
a longer list of call sites but by a scan that discovers them.
"""
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: The verdict constants of `weight_delta`, under every alias they are imported
#: as. ⛔ Aliases included deliberately — `act2_finetune.py` imports
#: `INSTRUMENT_FAULT as _FAULT`, and a scan that matched only the canonical name
#: would have missed the very site this module exists for.
DELTA_VERDICT_NAMES = {"INSTRUMENT_FAULT", "_FAULT", "DELTA_OK", "_DELTA_OK",
                       "UNDISCRIMINATING", "_UNDISCRIMINATING", "DIVERGED"}

#: ⭐ The shared exemption. Defined once in `weight_delta.py` precisely so the
#: trainer and the verdict cannot drift apart again.
SHARED = "POOLED_INVALID_FOR_MAPPING"


def _modules():
    for d in ("tools", "tlon"):
        for p in (ROOT / d).rglob("*.py"):
            # weight_delta.py DEFINES the constants; it is not a caller.
            if p.name != "weight_delta.py":
                yield p


def gate_sites():
    """-> [(path, lineno, names)] for every `if` that branches on a delta verdict.

    ⛔ `If` only, not `IfExp`. A ternary picking a print glyph is not a gate, and
    demanding the mapping exemption in display code would train everyone to
    sprinkle the constant around to quiet the test — which is how a guard stops
    meaning anything.
    """
    out = []
    for p in _modules():
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:                                  # pragma: no cover
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue
            hits = {s.id for s in ast.walk(node.test)
                    if isinstance(s, ast.Name) and s.id in DELTA_VERDICT_NAMES}
            if hits:
                out.append((p, node.lineno, sorted(hits)))
    return out


def _enclosing_source(path, lineno):
    """The function body containing `lineno`, so the exemption has to be near
    the gate rather than anywhere in a 1000-line file."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    best = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            if node.lineno <= lineno <= end:
                if best is None or node.lineno > best.lineno:
                    best = node
    return ast.get_source_segment(src, best) if best else src


def test_the_scan_finds_gates_at_all():
    """⛔ A scan that finds nothing passes everything. If the constants are ever
    renamed, this fails rather than silently policing an empty set."""
    sites = gate_sites()
    assert sites, ("the scan found no delta-verdict gates — the constant names "
                   "have probably changed and this guard is now vacuous")


def test_the_scan_finds_the_site_the_author_forgot():
    """⛔⛔ THE REGRESSION. `act2_finetune.py`'s in-process gate is the site the
    hand-written call-site list omitted, at the cost of a run. It must be
    discovered by scanning, not by being listed here — so this asserts the SCAN
    reaches that file, not that someone remembered to name it."""
    files = {p.name for p, _, _ in gate_sites()}
    assert "act2_finetune.py" in files
    assert "act2_fullft_verdict.py" in files


def test_every_discovered_gate_consults_the_shared_exemption():
    """⛔⛔ THE WHOLE POINT. Any branch on a delta verdict must know that the
    pooled test does not govern mapping scope. A gate added in a module nobody
    thought about fails here, because the scan did not need anybody to think
    about it."""
    missing = []
    for p, lineno, names in gate_sites():
        if SHARED not in _enclosing_source(p, lineno):
            missing.append("%s:%d (gates on %s)"
                           % (p.relative_to(ROOT), lineno, ",".join(names)))
    assert not missing, (
        "%d delta-verdict gate(s) do not consult %s:\n  %s"
        % (len(missing), SHARED, "\n  ".join(missing)))


def test_the_exemption_is_defined_once():
    """⭐ Two copies of the allow-list is the drift this whole module is about.
    It lives in `weight_delta.py`; everyone else imports it."""
    from tlon.act2 import weight_delta
    assert weight_delta.POOLED_INVALID_FOR_MAPPING == (
        weight_delta.UNDISCRIMINATING, weight_delta.INSTRUMENT_FAULT)
    defs = [p for p in _modules()
            if ("%s = (" % SHARED) in p.read_text(encoding="utf-8")]
    assert not defs, "a second definition of %s exists in %s" % (SHARED, defs)


def test_diverged_is_not_exempt_anywhere():
    """⛔⛔ `NaN != NaN` is True, so a destroyed leaf COUNTS AS CHANGED — the
    per-leaf evidence is precisely what cannot be trusted on a diverged run. If
    DIVERGED ever joins the exemption, a non-finite run can reach a verdict."""
    from tlon.act2 import weight_delta
    assert weight_delta.DIVERGED not in weight_delta.POOLED_INVALID_FOR_MAPPING
