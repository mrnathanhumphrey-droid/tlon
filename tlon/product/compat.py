"""THE COMPATIBILITY-SET REVEAL — B2. Where underdetermination becomes visible.

⛔ WHAT IT IS *NOT*. In the research, `consistent()` returns every referent from
a fixed ROSTER that an utterance could denote. The product is open-world: there
is no roster, so that instrument has nothing to enumerate over. Reaching for it
here would be borrowing a research tool for a question it does not answer.

⛔ AND THE SURFACE IS NOT WHERE THE AMBIGUITY LIVES EITHER. The grammar is
EXACTLY INVERTIBLE -- `parse(render(s)) == s` -- so a Tlon utterance determines
its Scene completely. There is no ambiguity to reveal at that level, and a
"compatibility set" built there would be a set of one, every time.

⭐⭐ WHERE IT ACTUALLY LIVES: **MANY ENGLISH SENTENCES COLLAPSE ONTO ONE
IMPRESSION.** That is the real underdetermination a visitor can feel, and the
project already defines the equivalence exactly -- PHASE 5: two utterances
differing only in NON-DENOTING decoration are the SAME IMPRESSION, which is what
pi() computes. So:

    impression(scene) = utterance_id(project(scene))

Two English inputs whose renderings share an impression are ones the language
CANNOT TELL APART. Showing them side by side is the moment:

    "This is what Tlon says for 'my landlord raised the rent again'.
     It is also what it says for 'the pressure keeps coming back'.
     It cannot tell them apart."

⭐ Computed from the corpus, so it costs NOTHING -- no model call, no roster --
and it gets richer as the corpus grows, which is the same corpus Route B needs.
The exhibit and the training set are the same artefact.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..grammar.canon import utterance_id
from ..grammar.denote import project
from ..grammar.parse import Scene
from . import corpus


def impression(scene: Scene) -> str:
    """The identity of a scene AS AN IMPRESSION -- decoration projected away.

    ⛔ `project()` (pi) is the research's own definition of "the same
    impression", not a convenience: it strips exactly the parts that do not
    denote (aspect reps, degree, modal, tense, quant, force) and keeps the
    parts that do. Using anything looser here would let the reveal claim two
    utterances are indistinguishable when the language can in fact separate
    them.
    """
    return utterance_id(project(scene))


@dataclass(frozen=True)
class Compatibility:
    impression: str
    chosen: str                      # the English that produced this rendering
    others: tuple[str, ...]          # distinct English sharing the impression
    surface: str
    unreadable: int = 0              # stored rows that would not decode

    @property
    def n(self) -> int:
        return len(self.others) + 1

    def reveal(self) -> str:
        # ⛔⛔ "compatible with 1" AND "compatible with 0" MUST BE UNREACHABLE,
        # and they are unreachable STRUCTURALLY -- the count is only ever
        # rendered below this early return, where `others` is non-empty and n is
        # therefore at least 2. A corpus of five rows means the empty case IS
        # the common case at launch, and a visitor who reads "compatible with 0
        # things" has been told the feature is broken. It is not: they are the
        # first person to land here, which is the more interesting fact and the
        # true one.
        if not self.others:
            return ("  The first saying to land on this impression. Nothing "
                    "else Tlön has heard collapses onto it — yet." + self._caveat())
        head = (f"  This is compatible with {self.n} things said to it; "
                f"it chose yours.")
        rows = "\n".join(f"    · {o}" for o in self.others[:6])
        more = (f"\n    … and {len(self.others) - 6} more"
                if len(self.others) > 6 else "")
        return (f"{head}\n    · {self.chosen}   ← you\n{rows}{more}\n"
                "  Tlön cannot tell them apart." + self._caveat())

    def _caveat(self) -> str:
        """⛔ AN UNDER-REPORT IS ALSO A LIE, JUST A QUIETER ONE. A stored row
        that will not decode is a row this reveal could not consider, and
        swallowing it would state a smaller set as if it were the whole one."""
        if not self.unreadable:
            return ""
        s = "" if self.unreadable == 1 else "s"
        return (f"\n  ({self.unreadable} stored saying{s} could not be re-read "
                f"and {'was' if self.unreadable == 1 else 'were'} not considered.)")


def compatible_with(scene: Scene, english: str, surface: str,
                    rows: list[dict] | None = None) -> Compatibility:
    """Every distinct English in the corpus that renders to the SAME impression.

    ⛔⛔ MEMBERSHIP IS EXACT EQUALITY OF IMPRESSION IDS AND NOTHING ELSE. There
    is no threshold here, no distance, no "close enough" -- and there could not
    be one, because an impression id is a 128-bit blake2b digest of the
    canonical projected scene, which admits equality and no other comparison.
    That is what makes "Tlön cannot tell them apart" a provable claim rather
    than a generous one: the returned set is EXACTLY the pi-equivalence class of
    `scene` among the corpus, no member missing and no member added.

    ⛔ Compares stored SCENES, never stored surfaces. Two renderings can share
    an impression while differing on the surface (that is precisely what pi
    projects away), so a surface comparison would under-report the set and make
    the reveal look emptier than the truth.
    """
    if rows is None:
        rows = corpus._read(corpus.ACCEPTED)     # noqa: SLF001
    mine = impression(scene)
    seen: list[str] = []
    unreadable = 0
    for r in rows:
        try:
            other_english = r["english"]
            other = impression(corpus.scene_from_canon(r["scene"]))
        except Exception:                         # noqa: BLE001
            # ⛔ COUNTED, NOT SWALLOWED. See Compatibility._caveat.
            unreadable += 1
            continue
        if other_english == english:
            continue
        if other == mine and other_english not in seen:
            seen.append(other_english)
    return Compatibility(impression=mine, chosen=english,
                         others=tuple(seen), surface=surface,
                         unreadable=unreadable)
