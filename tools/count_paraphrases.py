"""Phase 0 gate: answer Q1-Q4 of spec §7 exactly, and print the verdict."""
from __future__ import annotations
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar import classes as C, enumerate as E    # noqa: E402
from tlon.grammar.canon import canon_json, fiber_size, utterance_id  # noqa: E402
from tlon.grammar.parse import parse, render             # noqa: E402

BORGES = "hlör u fang axaxaxas mlö ka"


def human(n: int) -> str:
    if n == 0:
        return "0"
    return f"{n:,}" if n < 10 ** 7 else f"{n:.4e}  ({len(str(n))} digits)"


def main() -> int:
    lex = C.load()
    k = lex["constraints"]
    print("=" * 74)
    print("PHASE 0 GATE -- Sur (southern hemisphere), exact counts")
    print(f"lexicon hash {lex['_hash']}")
    print(f"classes: " + "  ".join(f"{c}={n}" for c, n in C.class_sizes().items()))
    print(f"caps: depth<={k['MAX_DEPTH']} morphs<={k['MAX_MORPHS']} "
          f"orient<={k['MAX_ORIENT_PER_PRED']} clauses<={k['MAX_CLAUSES_PER_PRED']}")
    print("=" * 74)

    print("\n--- GOLDEN: the attested Borges line ---")
    s = parse(BORGES)
    print(f"  surface   {BORGES}")
    print(f"  re-render {render(s)}")
    print(f"  canon     {canon_json(s)}")
    print(f"  id        {utterance_id(s)}")

    surf = E.build(ordered=True)
    cano = E.build(ordered=False)

    print("\n--- Q1  |U|  surface strings, by max nesting depth ---")
    for d in sorted(surf["by_depth"]):
        print(f"  depth<={d}   {human(surf['by_depth'][d])}")
    print(f"  TOTAL       {human(surf['total'])}")

    print("\n--- Q2  |U/canon|  distinct MEANINGS ---")
    for d in sorted(cano["by_depth"]):
        print(f"  depth<={d}   {human(cano['by_depth'][d])}")
    print(f"  TOTAL       {human(cano['total'])}")
    ratio = surf["total"] / cano["total"]
    print(f"  surface/canon inflation = {ratio:.4f}x  "
          f"({surf['total'] - cano['total']:,} strings are duplicate meanings)")

    print("\n--- Q3  paraphrases of ONE FIXED scene ---")
    print(f"  fiber(Borges scene)          = {fiber_size(s)}")
    print(f"  max fiber over all legal s   = {E.max_fiber_bound()}  (upper bound)")

    print("\n--- Q4  scenes COMPATIBLE with a referent (matrix root pinned) ---")
    pin = E.build(ordered=False, pin_matrix_root=True)
    print(f"  |{{s : matrix root = 'mlö'}}|  = {human(pin['total'])}")
    print(f"  share of all meanings        = {pin['total'] / cano['total']:.6f}")

    print("\n" + "=" * 74)
    print("VERDICT")
    print("=" * 74)
    q3 = fiber_size(s)
    print(f"  Q3 (paraphrase, same scene):   {q3}")
    print(f"  Q4 (impression-selection):     {human(pin['total'])}")
    if q3 <= 2:
        print("\n  PARAPHRASE IS DEAD. A fixed scene has essentially one form.")
        print("  'Never repeat for the same referent' is IMPOSSIBLE if 'same")
        print("  referent' means 'same scene' -- confirmed by construction,")
        print("  not by argument.")
    print("\n  Novelty must be drawn from Q4, not Q3: pick a DIFFERENT momentary")
    print("  impression compatible with the referent, never a different wording")
    print("  of the same one.")
    if pin["total"] > 10 ** 12:
        yrs = pin["total"] / (1000 * 365)
        print(f"\n  Q4 headroom at 1,000 utterances/day about the same referent:")
        print(f"  {yrs:.3e} years before exhaustion.")
        print("  SCOPE: this bounds the GRAMMAR's capacity, not the entropy of")
        print("  lived experience. Claim = 'the grammar will never be the")
        print("  bottleneck'. NOT 'the counter cannot expire' -- that would need")
        print("  a result about how many distinct moments a user actually supplies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
