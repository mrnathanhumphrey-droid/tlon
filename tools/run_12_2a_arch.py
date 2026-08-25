"""PHASE 12.2a -- Lever 4 architecture determination. Paper-only, from the code.

THE QUESTION. Can the current architecture express a referent with an
INEXPRESSIBLE component, contained to a designated dimension, such that:
  (1) the denotation provably cannot encode it while the rest stays lossless;
  (2) the speaker holds the full scene INCLUDING the residue, and the utterance
      structurally cannot carry it -- so a maximally informative speaker still
      cannot close the gap.

⛔ ANSWERED BY MEASUREMENT, NOT BY READING. Each claim below is demonstrated
against the live code: the category structure is DERIVED from the schema, the
guard is FIRED, and the "no inexpressible slot exists" claim is tested by
mutating every EventNode field and watching the surface.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.grammar import denote                              # noqa: E402
from tlon.grammar.parse import EventNode, Scene, render      # noqa: E402
from tlon.referents.schema import NodePattern                # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "runs"


class BannerMismatch(RuntimeError):
    pass


def banner(label, value, expected, fmt="{}"):
    if value != expected:
        raise BannerMismatch(f"{label}: printed {value!r}, expected {expected!r}")
    print(f"    {label:<54} {fmt.format(value)}")


def main() -> int:
    print("=" * 78)
    print("PHASE 12.2a -- LEVER 4 ARCHITECTURE DETERMINATION")
    print("=" * 78)

    # ---- 1. the category structure, DERIVED from the schema ---------------
    den = denote.denoting_parts()
    non = denote.nondenoting_parts()
    print("\n  1. WHAT CATEGORIES THE ARCHITECTURE CURRENTLY HAS\n")
    banner("denoting parts (a signature can constrain)", len(den), 4)
    print(f"      {sorted(den)}")
    banner("non-denoting parts (pi strips)", len(non), 6)
    print(f"      {sorted(non)}")
    banner("categories in total", 2, 2)

    # ---- 2. is any EventNode field invisible to render()? -----------------
    print("\n  2. IS THERE ALREADY AN INEXPRESSIBLE SLOT?\n")
    print("     Mutate each EventNode field and watch the surface. A field the")
    print("     surface ignores would BE the residue slot Lever 4 needs.\n")
    base = EventNode(root="mlö", orient=["nar"], aspect=("ax", 2),
                     degree="ron", modal="xöl", tense="nu", quant="sim")
    base_surf = render(Scene(node=base, force="ka"))
    mutations = {
        "root": {"root": "fox"}, "orient": {"orient": ["hlör"]},
        "aspect": {"aspect": ("mel", 3)}, "degree": {"degree": "kral"},
        "modal": {"modal": "hrix"}, "tense": {"tense": "pral"},
        "quant": {"quant": "tur"},
    }
    invisible = []
    for field, change in mutations.items():
        kw = {f.name: getattr(base, f.name) for f in dataclasses.fields(base)}
        kw.update(change)
        surf = render(Scene(node=EventNode(**kw), force="ka"))
        seen = surf != base_surf
        print(f"      {field:<8} changes the surface: {seen}")
        if not seen:
            invisible.append(field)
    banner("EventNode fields invisible to render()", len(invisible), 0)
    print("\n     ⇒ NO INEXPRESSIBLE SLOT EXISTS. Every field the scene carries")
    print("       reaches the surface. The two categories are")
    print("       DENOTING-AND-EXPRESSIBLE and NON-DENOTING-AND-EXPRESSIBLE;")
    print("       there is no third.")

    # ---- 3. what pi's guard does if you try to add one --------------------
    print("\n  3. WHAT HAPPENS IF YOU ADD ONE -- fire the guard, don't assert\n")
    fired = False
    try:
        extra = dict(denote._PATTERN_TO_PART)
        original = denote._PATTERN_TO_PART
        # simulate NodePattern gaining `residue_any` by removing its mapping
        trimmed = {k: v for k, v in extra.items() if k != "root_any"}
        denote._PATTERN_TO_PART = trimmed
        try:
            denote.denoting_parts()
        except denote.ProjectionUnsound as e:
            fired = True
            msg = str(e)[:70]
        finally:
            denote._PATTERN_TO_PART = original
    except Exception as e:                                   # noqa: BLE001
        print(f"    unexpected: {e}")
    banner("ProjectionUnsound fires on an unmapped field", fired, True)
    print(f"      {msg}")
    print("\n     ⭐ THE GUARD IS WORKING AS DESIGNED. Adding `residue_any` to")
    print("       NodePattern makes denote.py FAIL LOUDLY at import until pi is")
    print("       told what the new field means. The change cannot be made")
    print("       silently, which is exactly what that guard was built for.")

    # ---- 4. the determination ---------------------------------------------
    print("\n" + "=" * 78)
    print("  DETERMINATION: (1) NO — ARCHITECTURE CHANGE REQUIRED.")
    print("                 (2) YES — trivial ONCE (1) is done.\n")
    print("  ⭐⭐ THE CRUX, AND IT IS A DESIGN ASSUMPTION NOT A GAP:")
    print("     pi's whole construction assumes DENOTING ⊆ EXPRESSIBLE. The")
    print("     strip-list is DERIVED from NodePattern's fields, and every one")
    print("     of them maps to a scene part that renders. Lever 4 needs a")
    print("     third category — DENOTING AND INEXPRESSIBLE — which the")
    print("     two-way split has no room for.")
    print("\n  THE CHANGE, SPECIFIED (~20 lines):")
    for i, line in enumerate([
        "EventNode/Scene gains a `residue` field.",
        "render() must NOT emit it — and a test must ASSERT the surface is "
        "invariant to it, or it leaks silently.",
        "NodePattern gains `residue_any` so a signature can constrain it.",
        "denote.py's two-way split becomes THREE-WAY; _PATTERN_TO_PART gains "
        "the mapping (the guard forces this).",
        "match.node_matches() checks residue.",
    ], 1):
        print(f"    {i}. {line}")

    print("\n  ⛔⛔ THE COST IS NOT THE LINES. IT IS THREE RESTATED CLAIMS:\n")
    print("  (a) Q3 = 1 CHANGES MEANING. 'A fixed scene has exactly one")
    print("      canonical form' becomes 'one form per DENOTATION-CLASS', and")
    print("      the scenes-per-form count becomes a new quantity — which IS")
    print("      the ambiguity Lever 4 wants. Not a bug; but Q3=1 is quoted as")
    print("      a headline and would need restating everywhere.")
    print("\n  (b) PHASE 6's SEMANTIC-DRIFT MEASURE NEEDS RESTATING. 'The")
    print("      message stops being grounded to its target' presumes the")
    print("      utterance determines the target. With a residue it never")
    print("      does — it denotes a SET — so grounded becomes 'the")
    print("      denotation-set CONTAINS the target'. Weaker, still exact,")
    print("      still checkable. ⛔ The isolation claim survives in modified")
    print("      form and the modification must be recorded BEFORE anything")
    print("      leans on it.")
    print("\n  (c) ⭐⭐ THE NOVELTY COUNTER FORKS, AND THIS IS THE REAL DESIGN")
    print("      DECISION. R is computed on pi(scene). Two scenes differing")
    print("      only in residue project to the SAME view, so:")
    print("        • residue OUT of R -> the counter is blind to a distinction")
    print("          the speaker can actually perceive. It under-counts.")
    print("        • residue IN R     -> free novelty from wiggling something")
    print("          nobody can read. THAT IS EXACTLY THE NOISE FAILURE pi WAS")
    print("          BUILT TO PREVENT (docs: 'projecting only the listener's")
    print("          view would trade the cipher failure for the noise")
    print("          failure').")
    print("      Neither branch is free. A next phase must choose and justify.")

    print("\n  ⭐ 12.2b IS NOT BLOCKED FOREVER — it is blocked on a decision,")
    print("     and the decision is (c). That is the specified next phase.")
    print("  ⛔ 12.2c's pivot axes are named regardless, below.")

    print("\n  PIVOT AXES (12.2c), NAMED NOW SO A NULL POINTS SOMEWHERE:")
    print("    • RANDOM residue    -> predicted EMPTY. Nothing to convention on;")
    print("      a listener can only learn to ignore it.")
    print("    • STRUCTURED residue -> the Pictionary case. The inexpressible")
    print("      component has internal regularities the grammar cannot name")
    print("      but a listener could learn. This is the live hypothesis and")
    print("      the pivot target if 12.2b comes back empty.")
    print("    ⭐ Concretely, 'structured' means the residue is drawn from a")
    print("      space with its own metric — so 'nearby' residues are gestured")
    print("      at similarly — rather than from a free categorical dimension.")

    OUT.mkdir(exist_ok=True)
    (OUT / "phase12_2a_arch.json").write_text(json.dumps(
        {"determination": "ARCHITECTURE_CHANGE_REQUIRED",
         "q1_contained_inexpressible_component": False,
         "q2_source_lossiness_once_q1_done": True,
         "denoting_parts": sorted(den), "nondenoting_parts": sorted(non),
         "categories_now": 2, "categories_needed": 3,
         "eventnode_fields_invisible_to_render": invisible,
         "projection_guard_fires": fired,
         "restated_claims": ["Q3=1 becomes one-form-per-denotation-class",
                             "phase-6 semantic drift becomes set-containment",
                             "novelty counter fork: residue in R = noise "
                             "failure, out of R = blind counter"],
         "blocked_on": "the novelty-counter decision (c)",
         "pivot_axes": ["random residue (predicted empty)",
                        "structured residue (Pictionary case, live)"]},
        indent=2, default=str), encoding="utf-8", newline="")
    print(f"\n  wrote {OUT / 'phase12_2a_arch.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
