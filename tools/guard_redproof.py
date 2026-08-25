"""RED-PROOF for the Phase 9.0 comparison guard.

PHASE 9.0 GATES PHASE 9: no referent measurement runs until this exits 0.

WHAT A RED-PROOF HAS TO DO HERE, AND WHY IT IS NOT JUST "ASSERT IT RAISES".

A guard that raises on the cases you wrote for it is not yet evidence -- the
cases might be raising for a reason that has nothing to do with the guard, and
then the guard is decorative and the battery is theatre. So the battery is run
TWICE: once against the real guard, and once against a DECORATIVE stand-in that
subtracts without checking anything. The requirement is

    real guard       -> every unpaired case RAISES
    decorative guard -> every unpaired case COMPUTES A NUMBER
    real guard       -> every paired case does NOT raise

The middle line is the mutation, and it is what proves the battery is sensitive
to the guard rather than to some accident of its own construction. If the
decorative stand-in also raises, the case is testing something else and is
reported as UNINFORMATIVE, not as a pass.

Every unpaired case below is a costume the error has actually worn in this
project. They are named after the run that made them.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.harness import paired as P                                # noqa: E402
from tlon.harness.paired import (Delta, ItemIdentityError,          # noqa: E402
                                 ItemSet, Measurement,
                                 UnpairedComparison, side_by_side)


def m(name, value, kind, keys, **facets):
    return Measurement(name, value, ItemSet.of(kind, keys, **facets))


def decorative_delta(a, b, *, contrast):
    """A guard that is a comment: it subtracts and calls the job done.

    This is the mutation. If the battery below cannot tell this apart from the
    real guard, the battery proves nothing.
    """
    return Delta(value=getattr(a, "value", a) - getattr(b, "value", b),
                 contrast=contrast, left=a, right=b)


# --- the unpaired battery. Each is a real error this project has made. -------

def case_phase3_subset_vs_full(delta):
    """PHASE 3, the contaminated cipher control.

    The scramble arm was evaluated on the SUBSET of items the scramble touched
    and compared against a baseline over the FULL set. It manufactured a
    1.35 pt drop on a channel that is provably a no-op.
    """
    full = [f"u{i:04d}" for i in range(200)]
    subset = full[:120]
    a = m("scrambled", 0.9310, "utterance", subset, arm="scrambled", seed=11)
    b = m("baseline", 0.9445, "utterance", full, arm="honest", seed=11)
    return delta(a, b, contrast="arm")


def case_phase7_floor_curve(delta):
    """PHASE 7, the auditor floor curve -> D10, RETRACTED.

    One point per withholding rate, and each rate draws a DIFFERENT ITEM SET of
    the same size. The curve read flat and I concluded the auditor ignored the
    withheld content. Paired on identical items: 42.8 % vs 34.9 %, 7.9 pts,
    3x what the unpaired curve suggested.
    """
    at25 = [f"gloss-p25-{i:03d}" for i in range(300)]
    at75 = [f"gloss-p75-{i:03d}" for i in range(300)]
    a = m("auditor@0.25", 0.464, "gloss-item", at25, p_utter=0.25, seed=7)
    b = m("auditor@0.75", 0.480, "gloss-item", at75, p_utter=0.75, seed=7)
    return delta(a, b, contrast="p_utter")


def case_phase8_within_run_windows(delta):
    """PHASE 8.3a, the teachability spike.

    Same evaluation items, but the two terms come from different STEPS of one
    run. Policy entropy declines monotonically as training converges, so the
    trend swamps the transient. Naming 'reset' as the contrast while the step
    window also moves is exactly the confound: the delta cannot be attributed.
    """
    ev = [f"eval-{i:03d}" for i in range(400)]
    a = m("entropy pre", 1.842, "eval-row", ev,
          reset="before", step_window="2700-3000", seed=11)
    b = m("entropy post", 1.713, "eval-row", ev,
          reset="after", step_window="3000-3300", seed=11)
    return delta(a, b, contrast="reset")


def case_two_things_at_once(delta):
    """A contrast plus a seed change. Common when arms are re-run piecemeal."""
    ev = [f"eval-{i:03d}" for i in range(400)]
    a = m("pi arm", 0.921, "eval-row", ev, pi=True, seed=11)
    b = m("raw arm", 0.888, "eval-row", ev, pi=False, seed=22)
    return delta(a, b, contrast="pi")


def case_contrast_does_not_differ(delta):
    """DEGENERATE: reports the difference between a thing and itself.

    This is how a 0.00 gets into a table looking like a measured null. See the
    frozen-arm shift that was 0.00 BY CONSTRUCTION because the naive judge was
    byte-identical to the arm's listener.
    """
    ev = [f"eval-{i:03d}" for i in range(400)]
    a = m("naive judge", 0.884, "eval-row", ev, judge="naive", seed=11)
    b = m("arm listener", 0.884, "eval-row", ev, judge="naive", seed=11)
    return delta(a, b, contrast="judge")


def case_undeclared_contrast(delta):
    """The thing under test was never recorded, so it was never controlled."""
    ev = [f"eval-{i:03d}" for i in range(400)]
    a = m("adapted", 0.971, "eval-row", ev, seed=11)
    b = m("naive", 0.883, "eval-row", ev, seed=11)
    return delta(a, b, contrast="listener")


def case_different_kind(delta):
    """Different populations entirely -- the old-set vs new-set shape."""
    a = m("utterance acc", 0.930, "utterance",
          [f"u{i}" for i in range(60)], arm="v1")
    b = m("referent acc", 0.884, "referent",
          [f"r{i}" for i in range(60)], arm="v2")
    return delta(a, b, contrast="arm")


def case_bare_floats(delta):
    """The original sin: two numbers with no record of what they cover."""
    return delta(0.9445, 0.9310, contrast="arm")


UNPAIRED = [
    ("phase3 subset vs full set", case_phase3_subset_vs_full),
    ("phase7 floor curve (different items per rate)", case_phase7_floor_curve),
    ("phase8.3a before/after within one run", case_phase8_within_run_windows),
    ("contrast + seed both change", case_two_things_at_once),
    ("contrast identical on both sides", case_contrast_does_not_differ),
    ("contrast never declared as a facet", case_undeclared_contrast),
    ("different item kinds", case_different_kind),
    ("bare floats, no item set at all", case_bare_floats),
]


# --- the paired battery: these MUST go through. ------------------------------

def case_paired_gloss(delta):
    """PHASE 7 done right: FULL gloss vs HEAD-ONLY on IDENTICAL items -> 7.9 pts."""
    ev = [f"gloss-{i:03d}" for i in range(300)]
    a = m("auditor FULL", 0.428, "gloss-item", ev, gloss="full", seed=7)
    b = m("auditor HEAD-ONLY", 0.349, "gloss-item", ev, gloss="head_only", seed=7)
    return delta(a, b, contrast="gloss")


def case_paired_no_reset_control(delta):
    """PHASE 8.3a's missing control: same seed, event removed, matched step."""
    ev = [f"eval-{i:03d}" for i in range(400)]
    a = m("entropy, reset run", 1.713, "eval-row", ev,
          reset="yes", step=3300, seed=11)
    b = m("entropy, no-reset control", 1.759, "eval-row", ev,
          reset="no", step=3300, seed=11)
    return delta(a, b, contrast="reset")


PAIRED = [
    ("phase7 FULL vs HEAD-ONLY, identical items", case_paired_gloss),
    ("phase8.3a reset vs matched no-reset control", case_paired_no_reset_control),
]


def run(delta_fn):
    out = []
    for name, case in UNPAIRED:
        try:
            got = case(delta_fn)
            out.append((name, False, f"computed {100 * got.value:+.2f} pts"))
        except UnpairedComparison as e:
            out.append((name, True, str(e).splitlines()[0][:64]))
        except Exception as e:                       # noqa: BLE001
            out.append((name, None, f"{type(e).__name__}: {e}"))
    return out


def main() -> int:
    print("=" * 78)
    print("PHASE 9.0 RED-PROOF -- the comparison guard")
    print("=" * 78)
    fails = []

    print("\n  A. UNPAIRED CASES vs THE REAL GUARD  (every one must RAISE)\n")
    real = run(P.paired_delta)
    for name, raised, note in real:
        mark = "ok  " if raised else "FAIL"
        if not raised:
            fails.append(f"real guard did not raise: {name} -- {note}")
        print(f"    [{mark}] {name}")
        if not raised:
            print(f"           -> {note}")

    print("\n  B. THE MUTATION -- same cases vs a DECORATIVE guard that only")
    print("     subtracts. Every one must COMPUTE A NUMBER, or the case is")
    print("     insensitive to the guard and proves nothing.\n")
    dec = run(decorative_delta)
    for name, raised, note in dec:
        if raised is False:
            print(f"    [ok  ] {name}  -> {note}")
        else:
            fails.append(f"case is UNINFORMATIVE (decorative guard also "
                         f"failed): {name} -- {note}")
            print(f"    [FAIL] {name}  -> {note}")

    print("\n  C. PAIRED CASES vs THE REAL GUARD  (must NOT raise)\n")
    for name, case in PAIRED:
        try:
            d = case(P.paired_delta)
            print(f"    [ok  ] {name}  -> {d.pts()} pts")
        except Exception as e:                       # noqa: BLE001
            fails.append(f"guard rejected a legitimate pairing: {name} -- {e}")
            print(f"    [FAIL] {name}  -> {type(e).__name__}: {e}")

    print("\n  D. ITEM IDENTITY -- a set that cannot identify its items\n")
    for label, keys in (("empty item set", []),
                        ("duplicate keys", ["a", "b", "a"])):
        try:
            ItemSet.of("utterance", keys)
            fails.append(f"ItemSet accepted {label}")
            print(f"    [FAIL] {label} was accepted")
        except ItemIdentityError:
            print(f"    [ok  ] {label} refused")

    print("\n  E. SIDE-BY-SIDE -- the unpairable case has no difference operator\n")
    a = m("old set, mean consistency", 1.26, "referent",
          [f"old-{i:02d}" for i in range(60)], referent_set="v1")
    b = m("new set, mean consistency", 1.26, "referent",
          [f"new-{i:02d}" for i in range(60)], referent_set="v2")
    sbs = side_by_side(a, b, reason="different referents; no pairing exists")
    try:
        _ = sbs.delta
        fails.append("SideBySide.delta computed a number")
        print("    [FAIL] .delta returned a value")
    except UnpairedComparison:
        print("    [ok  ] .delta raises; the two numbers can only be reported")
    try:
        side_by_side(a, a, reason="x")
        fails.append("side_by_side accepted an actually-paired comparison")
        print("    [FAIL] accepted a pairable comparison")
    except ValueError:
        print("    [ok  ] refuses a pairable comparison (use paired_delta)")

    print("\n" + "=" * 78)
    if fails:
        print(f"  RED-PROOF FAILED -- {len(fails)} problem(s). PHASE 9 IS GATED.")
        for f in fails:
            print(f"    - {f}")
        return 1
    print("  RED-PROOF PASSED.")
    print(f"    {len(UNPAIRED)} unpaired cases raise against the real guard and")
    print("    compute a number against a decorative one, so the battery is")
    print(f"    sensitive to the guard. {len(PAIRED)} legitimate pairings pass.")
    print("  Phase 9.0 gate is OPEN.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
