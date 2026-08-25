# FIX 2 — proposed replacement for the consistency check. **NEEDS NATE'S APPROVAL BEFORE THE RE-RUN.**

**Date:** 2026-08-23 · built: `tlon/harness/ceiling.py`, `tests/test_ceiling.py`
(13 tests, green) · not yet wired as the gate.

---

## What the old check was for — this must be preserved exactly

> It protected against reading **`metric×head ≈ 0`** as *"a metric residue is not
> conventionable"* when the true cause was *"this head emitted a policy that
> cannot express the distinction at all."*

Any replacement that does not protect against **that specific false conclusion**
is not a replacement.

## Why the old one was invalid (D16)

`categorical×head == categorical×table` rested on *"one-hot into a linear layer
is a row lookup."* True of a **single** linear layer. The trunk is
`Linear → Tanh → Linear → Tanh → Linear`: a one-hot selects a 32-dim
**embedding**, and the second trunk layer plus every channel head are **shared
across all 24 referents**. Equality was never going to hold — and the depth that
broke it is the same depth that keeps the falsifying cell reachable.

---

## ⛔ Why I am NOT proposing either of the two candidates you listed

**(b) "categorical×head under supervised training reaches 100 %" — disqualified
by measurement, not by argument.** That is exactly Q1 from the diagnosis, and it
**already returned 100 % on both arms** in the run where `metric×head` collapsed
to 1/24 codes. A gate that passes in the failure case it exists to catch is not
a gate. It would have waved the broken run straight through.

**(a) "categorical×head matches categorical×table's diversity/accuracy" — too
strong, and it re-imports the assumption that just failed.** The table has
independent per-referent logits; the head reaches every output through shared
weights. Demanding behavioural parity is weight-equivalence wearing behavioural
clothes, and it would **re-block on a false failure** the moment the head is
merely *good* rather than *table-equivalent*. It also gates the metric cell only
by proxy, through a different arm.

---

## ⭐ PROPOSED: the **Bayes-ceiling gate**, applied per cell

For each cluster of *k* mates, take the trained policy's **exact** distribution
over the free-channel code space and compute what a Bayes-optimal listener that
*knew the policy* would score:

```
ceiling_cluster = (1/k) · Σ_over_codes  max_over_mates  P_mate(code)
headroom        = mean(ceiling) − floor          (floor = 1/k = 33.3 %)
```

**A cell's residue gap is readable iff `headroom > MDE_floor` (2.96 pts).**

Exact, not estimated: the channels are independent categoricals, so the joint
over all **24,500** codes is enumerated in closed form. No sampling, no
threshold picked to taste — the floor is arithmetic and the bar is the MDE we
already pre-registered.

### What it protects against — the same false conclusion, more directly

A cell whose ceiling sits at its floor is **structurally incapable of showing an
effect**: the best possible listener, knowing everything, cannot beat guessing.
Its ≈0 therefore says nothing about the residue — exactly as a `residue=None`
set would say nothing. The gate refuses that cell and its message says
**"uninformative, *not a null*."**

⭐ It gates **every cell on its own evidence**, including the metric cell —
strictly better than the old check, which could only reach the metric cell by
proxy through the categorical one.

### It is valid under the MLP trunk — and cannot be invalidated the same way again

It reads **what the policy does**, never **how the policy is built**. No
architectural assumption is available to be wrong. That is the specific defect
in D16, removed at the root.

### It fires correctly on everything we have actually seen

| observed cell | separation | ceiling | headroom | gate |
|---|---|---|---|---|
| `metric×head` (the collapse) | `[1,1,1,1,1,1,1,1]` | 33.3 % | **0.0** | ⛔ **REFUSED** |
| `categorical×head` | `[2,3,2,3,3,3,1,2]` | ≈79 % | ≈43 | ✅ readable |
| `table` (both arms) | 24/24 | ≈100 % | ≈67 | ✅ readable |

### ⭐⭐ It also closes Fix 1's named risk, with the same quantity

You flagged that an over-large entropy bonus could **manufacture diversity**. A
*count of distinct codes* would be fooled — a near-uniform policy still has a
varied `argmax`. The ceiling is not: uniform means every mate has the **same**
distribution, so the max-sum is 1 and the ceiling falls to exactly the floor.
**Over-entropy fails this gate for the same arithmetic reason collapse does.**
That is why the sweep's "restores diversity" criterion is written in headroom
and not in code counts. Tested: `test_classifier_names_the_over_entropy_case_argmax_would_miss`.

### Second clause, keeping your calibrate-on-the-control discipline

**The metric cells additionally require `categorical×head` to pass the gate.**
If the head cannot read even a categorical residue, a `metric×head` number rides
on an unproven head. This preserves the old check's *spirit* — validate on the
arm whose behaviour we can predict — without its false invariant.

---

## ⛔ What this gate does **not** catch — stated so it isn't over-trusted

1. **A head that systematically underperforms the table for an unknown reason.**
   The old check would have flagged it. This one won't — it will report both as
   readable and let the difference stand as a finding. I think that is correct
   (it is a result, not a validity failure), but it *is* a reduction in scope
   and you should know it before approving.
2. **High headroom, zero measured gap.** The gate says the policy carried
   signal; it cannot say the *listener* learned it. That combination would be a
   real finding and needs its own diagnosis, not a gate.
3. It says nothing about whether the code the policy found has anything to do
   with the residue's **metric structure** — that is the experiment, not the gate.

---

## The one judgement call in it

**The bar is `headroom > MDE_floor`.** Rationale: a cell that cannot exceed the
MDE even with a perfect listener cannot produce a detectable gap, so reading its
result is meaningless. Using the MDE we already pre-registered avoids inventing
a second threshold.

Alternatives if you want it stricter: `2 × MDE` (what the *sweep* uses, since
selecting a knob deserves margin), or the ceiling must clear the observed
`categorical×head` headroom. **I'd keep it at `1 × MDE` for the gate and
`2 × MDE` for the sweep** — the gate should refuse only cells that are provably
incapable, not cells that are merely weak, or it starts discarding real results.

---

**Approve, amend, or reject.** Nothing runs until you rule. The entropy sweep
(Fix 1) is running now on the control arm only; the re-run of the 2×2 is not.
