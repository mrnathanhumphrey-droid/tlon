# PREREG — asymmetric solo pass: re-certify the panel, re-run the pool gate, test the attractor

**Locked before any generation.** One box pass, `--no-injections`, 7 builds ×
14 solo asymmetric transcripts. Fixed at this commit; later edits are amendments
and say so.

---

## 1 · WHAT RUNS

`tools/act2_two_speaker_probe.py --adapter-a <build> --no-injections` — the COLD
arm only: one speaker, **its own chain accumulated, no interlocutor**, 40 turns,
14 transcripts per build, all 7 same-code same-map builds.

⛔ **`--no-injections` is required, not a saving.** Contamination is between-build
sd over within-conversation movement. Every build would see the *same*
injections, so a biased pool compresses that sd and would certify observables as
more build-stable than they are — the panel would be selected on poisoned data.

⭐ The injected COLD baseline is **not** needed here: the probe emits COLD, LIVE
and YOKED in one invocation, so the drift run generates its own.

## 2 · DELIVERABLE 1 — panel re-certification in-regime

Stage 1 admitted `root TTR`, `force:ka`, `nodes/scene` on **window-1**
transcripts. The drift run is asymmetric-accumulating, and between-build `ka`
spread was 0.037 at window-1 against 0.687 under accumulation (18×). The panel is
therefore certified for a regime the experiment will not use.

Re-run `tools/act2_ranking_stability.py` on these transcripts, identical
admission rule: **jackknife rank range ≤ 2 AND bootstrap 95 % CI upper < 0.50.**

- **≥ 3 admitted** → panel stands, Stage 2 proceeds.
- **1–2 admitted** → reduced panel, recorded as a narrow basis.
- **0 admitted** → ⛔ **HALT.** No distance is definable in the regime it must be
  measured in. More builds, not a metric built on sand.

⚠️ **Certified solo, applied live.** Contamination is a per-build property, so a
partner would contaminate the per-build characterisation — solo is the right
arm. But the drift run measures LIVE. An observable that is build-stable solo
and ill-behaved under interaction would pass this gate and still hurt the
distance. Low risk, explicitly noted, and it goes in the results doc.

## 3 · DELIVERABLE 2 — injection-pool gate, re-run in-regime

`$0` once these transcripts exist. `force:ka` sat at **z = 1.30 against Z_MAX
1.5** at window-1, and depth widened between-build spread 18× last time.

⭐ **PRE-DECLARED: if `force:ka` crosses 1.5 in-regime it is EXCLUDED, the panel
becomes two-axis (`root TTR` + `nodes/scene`), and that is a VALID OUTCOME, not
a failure.** Two axes still define a distance. A gate that only ever confirms the
panel it was given is not a gate.

## 4 · DELIVERABLE 3 — the attractor, and the claim it does NOT license

Each build settled into its own stable `ka` share — 0.119 / 0.806 / 0.278, 8 of 8
conversations each, ranges essentially non-overlapping. That was measured in the
**symmetric shared-backend regime**, which is now known to be one impression
talking to itself with the partner's past retained.

COLD-solo is pure self-accumulation with no partner at all, so it separates:

- **(A) self-accumulation-intrinsic** — attractors reproduce ⇒ a speaker
  deepening its own groove, independent of the broken architecture.
- **(B) symmetric-regime artefact** — attractors vanish ⇒ they were a product of
  the fault.

⛔⛔ **PRE-DECLARED, AND THIS IS THE ONE THAT MATTERS: A POSITIVE RESULT HERE
MEANS "SELF-ACCUMULATION-INTRINSIC". IT DOES NOT MEAN "TLÖN'S METAPHYSICS
PREDICTED IT".**

Any autoregressive model accumulating its own context tends toward
self-reinforcing grooves — mode collapse, repetition traps, self-consistency
pressure. That alternative **survives a positive COLD-solo result completely**,
because it predicts exactly the same observation. Separating *Tlön-specific* from
*generic-transformer* requires a **control language**: the same architecture and
training recipe on a non-Tlön corpus, asking whether the phenomenon is stronger
or different here. **That run does not exist, is not in this pass, and is not
free.** It is named here as DEFERRED so it cannot later be quietly folded into
this pass's interpretation.

⇒ The results doc may write *"the attractor is intrinsic to self-accumulation."*
It may **not** write *"the ontology predicted the pathology."*

## 5 · CARRIED DISCIPLINE

`compileall` under the box's Python 3.10 first; adapter md5s pinned **on the box
against the local values before generation**, since these adapters are uploaded
rather than trained here; **pull the pipeline log FIRST**; analyse locally only;
pull-and-kill at DONE; raw dump on failure, never `tail` on attribution-relevant
output. ⭐ **Log per-build wall time separately from setup** — a fixed cost
divided by a small n is the constant, not a rate, and that error made an earlier
forecast 2× optimistic.

## 6 · WHAT THIS PASS DOES NOT DO

No LIVE arm, no YOKED arm, no pairs, no distance, **no drift number**. σ_cp
remains unmeasured. It generates the first right-regime transcripts in the
project's history and re-certifies the instruments against them.
