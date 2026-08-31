"""⛔⛔ THE GRAMMAR IS THE TRIPWIRE.

Three times in this arc a conclusion that drove a decision was stated in a form
that told every reader to stop looking, and three times it survived full
adversarial review:

  1. "identical speakers cannot converge — that's ARITHMETIC, not hypothesis"
     → false; it propagated to 13 places across 7 files, unexamined.
  2. "the experiment is ADAPTER-LIMITED, not replicate-limited"
     → a point estimate reported without its interval; h's 95% CI is
       [0.0000, 0.4033], so the lower bound is zero and the claim is not
       established. It was about to buy 13 adapters.
  3. the self-pair control described as proving coupling IMPOSSIBLE
     → only impossible for the statistic that happened to be chosen.

Vigilance is not the fix — all three passed review by humans and by me. The
common factor is grammatical: **settled-property phrasing** ("X-limited",
"cannot", "by construction", "arithmetic", "impossible") asserts a property of
the world rather than an estimate with a ±, and that form suppresses the request
for an interval.

⭐ So this linter triggers on the FORM, not on the content. A settled-property
phrase in a live decision document must have an interval, a range, or an
explicit not-established marker nearby — or an inline waiver naming why the
claim really is settled.

⛔ It deliberately does NOT judge whether the claim is true. It only enforces
that a claim shaped like a settled fact carries the evidence that would let a
reader check it.
"""
from __future__ import annotations

import pathlib
import re
import sys

#: Live decision documents. Historical run-logs are exempt: the rule is about
#: claims still steering choices, not about rewriting the record.
LIVE_GLOBS = ("STATE.md", "docs/RESULTS_*.md", "docs/PRICING_*.md",
              "docs/SPEC_*.md", "docs/PREREG_*.md")

#: Settled-property phrasing — grammatical forms that close inquiry.
#:
#: ⛔⛔ NARROWED AFTER CALIBRATION, AND THE CALIBRATION IS THE POINT. The first
#: draft also flagged "by construction", "trivially" and "is impossible", giving
#: 35 hits across 29 documents, nearly all CORRECT uses — this repo says
#: "validity is 100 % by construction ⇒ a falsifier that cannot fire", which is a
#: legitimate catch of a vacuous guard, not a suppressed interval. A linter that
#: noisy is ignored, which is worse than no linter. My keyword list was setting
#: the size of the finding: the kw_coverage failure, occurring inside the tool
#: built to enforce discipline.
#:
#: ⭐ What is kept is the form that actually failed: a DIAGNOSIS shaped like a
#: settled property ("X-limited"), plus the two inquiry-closing intensifiers rare
#: enough to be signal rather than noise.
SETTLED = (
    r"\b\w+-limited\b",
    r"\barithmetic\b",
    r"\bnot a hypothesis\b(?!\s+test)",   # "not a hypothesis TEST" is a different, legitimate sense
    r"\bcannot converge\b",
)

#: Evidence that the claim is offered as an ESTIMATE and can be checked.
INTERVAL = (
    r"\bCI\b", r"±", r"\+/-",
    r"\[\s*[−+\-]?\d", r"\binterval\b", r"\brange\b",
    r"\bnot establi", r"\bpoint estimate\b", r"\bprovisional\b",
    r"\bunestablished\b", r"\bcorrected\b", r"\bcorrection\b",
    r"\boriginally said\b", r"\bretract", r"\bbroke that axiom\b",
    r"\bearlier version\b", r"\bthe brief called\b",
)

#: Explicit escape hatch. Use it when the claim genuinely cannot be otherwise,
#: and say why on the same line — a waiver without a reason is the old failure.
WAIVER = "settled-claim-ok:"

# ⛔⛔ CALIBRATED, NOT CHOSEN. At 500 the linter did NOT fire on the actual
# sentence that nearly bought 13 adapters — "CI half-width" sat in the same
# paragraph, but that CI was on the DRIFT ESTIMAND, not on `h`, the parameter the
# diagnosis rested on. The exemption was satisfied by an interval on the WRONG
# QUANTITY: a check whose passing condition is downstream of something other than
# what it must witness. Swept 500→60; 120 is the widest window that still fires
# on the real case while staying quiet on a properly-qualified claim.
WINDOW = 120


def _norm(text: str) -> str:
    """⛔ Whitespace-normalised. A line-oriented scan misses a phrase that wraps
    a line break — that is exactly how a grep declared a file clean while the
    false lemma was still in it."""
    return re.sub(r"\s+", " ", text)


def violations(text: str):
    flat = _norm(text)
    # ⭐ A waiver in the first 400 chars is FILE-LEVEL. Needed because the window
    # is only 120 chars: a document whose whole subject is the uncertainty in a
    # claim would otherwise be flagged on every mention of it.
    if WAIVER in flat[:400]:
        return []
    out = []
    for pat in SETTLED:
        for m in re.finditer(pat, flat, re.I):
            ctx = flat[max(0, m.start() - WINDOW): m.end() + WINDOW]
            if WAIVER in ctx:
                continue
            # ⛔ Case-INSENSITIVE. A verifier that matched its own exemption
            # keywords case-sensitively produced two false positives on a
            # heading reading "IS NOT ARITHMETIC".
            if any(re.search(p, ctx, re.I) for p in INTERVAL):
                continue
            out.append((m.group(0), flat[max(0, m.start() - 90): m.end() + 90]))
    return out


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[1]
    files = sorted({p for g in LIVE_GLOBS for p in root.glob(g)})
    bad = 0
    for f in files:
        for phrase, ctx in violations(f.read_text(encoding="utf-8")):
            bad += 1
            print("⛔ %s\n   [%s] …%s…" % (f.relative_to(root), phrase, ctx))
    print("\nscanned %d live decision documents · %d unqualified settled claims"
          % (len(files), bad))
    if bad:
        print("Each must gain an interval/range, be marked not-established, or "
              "carry an inline `%s <reason>` waiver." % WAIVER)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
