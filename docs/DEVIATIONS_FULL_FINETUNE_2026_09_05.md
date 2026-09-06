# DEVIATIONS — `PREREG_FULL_FINETUNE_RELEASE_2026_09_05` (LOCK `a0450b36`)

Every discrepancy between the locked body and what the machinery actually does,
recorded before the run fires. ⭐ Including the immaterial ones: the mechanism is
only trustworthy for the material deviations if the habit of recording them has
not eroded on the trivial ones.

⛔ The locked body is not edited. That is what locked means. This file is how the
difference is carried.

---

## D-1 · The §5 fit figure is 65.8 GiB, not 65.7 — rounding

**Locked text (§5, batch × accum row):** "51.4 GiB planner, **65.7 GiB** with the
planner's own 28% worst-observed miss applied — **14.3 GiB margin on 80**."

**What the repository computes:** `51.4` → **`65.8`**, margin **14.2**.

**Cause.** The locked figure came from a session scratch script that passed
`7.62` B to the activation term and `7.616` B to the weight terms. The tool now
uses `7.616` throughout. The planner figure (51.4) is unchanged; only the ×1.28
product differs, in the third significant figure.

**Materiality: none.** The decision was "does it fit on 80 GiB with real margin
rather than the 3 GiB the all-fp32 layout would have left", and 14.2 answers it
exactly as 14.3 did.

**Where it now lives.** `tools/act2_finetune.py::plan(trainable_b=...)`, pinned
by `tests/test_full_weight.py::test_the_locked_section_5_fit_is_reproducible`,
which asserts **65.8** and carries this deviation in its docstring. §5's number
was previously reproducible only from scrollback; it is now reproducible from the
repository, which is the actual fix.

---

## D-2 · "2 epochs" is two single-epoch legs, so the Adam moments restart

**Locked text (§5, epochs row):** "**2 declared**, with a **mandatory read at end
of epoch 1** … Pre-declared early-stop: if epoch 1 is GO on all three axes,
**stop there** … If epoch 1 is not GO-on-all-three, epoch 2 runs and epoch 2 is
the verdict."

**What `pipeline_fullft.sh` does.** Leg 1 trains one epoch and saves. The three
axes are read. If the verdict is GO, the run stops — literally the locked
early-stop. If it is not, leg 2 trains a second epoch **as a separate `Trainer`
invocation** starting from the leg-1 weights.

**The deviation.** A continuous two-epoch run carries the Adam first/second
moment estimates across the epoch boundary; two legs do not — they restart at
zero and re-warm over the first ~100 optimizer steps of leg 2. The data seen,
the LR, and the number of epochs are as declared; the optimizer's momentum state
across the boundary is not.

**Why it is built this way.** Reading the three axes *during* training is what
the mandatory epoch-1 read means, and the early-stop is only a saving if the
decision happens before epoch 2 is paid for. Preserving optimizer state across
that decision needs HF checkpoint resume threaded through a training call that is
also carrying the §4.1 snapshot — more moving parts in the one path that costs
H100-hours and cannot be cheaply re-run. Two legs is the simpler machine.

⚠️ **Not silently absorbed.** The tradeoff is a real one and the alternative is
a buildable thing, not an impossible one. If the run returns **STOP — floored**,
this deviation is on the list of things to rule out before climbing §7.1's
ladder: a momentum reset midway is a plausible, if unlikely, reason a fine-tune
under-installs.

**Where it is recorded in the machinery.** `tools/pipeline_fullft.sh`, the
`train_leg2` stage comment.

---

## D-3 · The §4.1 delta is measured from the base model across both legs

**Not a deviation — a note on how the locked requirement is met**, recorded
because the naive implementation would have broken it.

§4.1 requires `||theta_final - theta_init||` and the fraction of trainable
parameters that changed. With two legs, a snapshot taken at the start of leg 2
would measure **one epoch** of movement and report it as the total. A run whose
first epoch moved the weights and whose second did not would then read
INSTRUMENT FAULT — the guard firing on a run that worked.

`--delta-snapshot-out` / `--delta-snapshot-in` carry the base-model snapshot from
leg 1 into leg 2, so "from `theta_init`" means from the base weights however many
legs the early-stop rule produces.

---

## D-4 · Two guards were added that the locked body does not name

Recorded because they change what the run refuses, and a reader comparing the
prereg to the code should not have to discover them.

**(a) `enable_input_require_grads()`.** With `embed_tokens` frozen, the input to
the first gradient-checkpointed block does not require grad, and reentrant
checkpointing then skips the backward through that segment — **every trainable
layer receives zero gradient**, training "succeeds", and the weights do not move.
This is §4.1's failure arriving through a mechanism the prereg did not anticipate
(checkpointing, not optimizer precision). The delta precondition would have
caught it after the fact; this prevents it.

**(b) The empty-scope refusal** in `tlon/act2/full_weight.py`. A layer selector
that matches nothing freezes the whole model, which trains to a *perfect* zero
delta — the most convincing possible false (b). Refused at scope-selection time,
before any GPU time, rather than caught at the delta check after it.

Neither weakens any threshold or changes any axis. Both make an
INSTRUMENT-FAULT-shaped outcome harder to reach by accident.

---

## D-5 · `act2_model_lag.py` had `--adapter` as required

The §3 instrument could not read the object §5 produces. `--adapter` is now
optional, and a read with no adapter must pass `--object-kind full_weight` **and**
a local `--model` path — otherwise it would read the bare base model and write a
lag profile indistinguishable from a treatment result. The output now carries
`object`, `object_kind` and `measurement_category`, so a `_w` profile can never
be mistaken for a `_ctx` one (C8, §6).

---

## D-6 · `bitsandbytes` was not in the runbook-pinned venv — installed by hand

**Found by the provision-time optimizer probe**, on its first real use:
`ModuleNotFoundError: No module named 'bitsandbytes'` on the freshly provisioned
H100. §5 declares `adamw_bnb_8bit`, and fp32 moments do not fit on 80 GiB — so
without that wheel there was no declared config to run at all.

**What was done.** `bitsandbytes==0.50.1` installed into the box's venv by hand,
pinned to the version the local box runs, and the probe re-run to confirm.

**Why it is a deviation.** `cmd_provision` pins the box to a git sha precisely so
the run happens against the code it was designed against. A package installed
outside that pin is environment state the sha does not describe. Recorded here
rather than smoothed over, because "the box had one more package than the commit
says" is exactly the kind of thing that is invisible six weeks later.

⭐ **The probe is the finding, not the failure.** Discovered at provision time
for ~$0.20 of idle box; without it, the first optimizer step of a paid training
run would have raised, hours in — or, on a code path that fell back silently,
trained with the wrong optimizer and produced a delta nobody could interpret.

**Follow-up: DONE.** `cmd_provision` now installs `bitsandbytes==0.50.1` as
part of the runbook-pinned venv, for every box rather than gated on the arm — it
is small, a LoRA box ignoring a package it never imports costs nothing, and a
conditional is one more way for the next `_w` box to arrive without it. Pinned
by `tests/test_provision.py::test_bitsandbytes_is_runbook_pinned_in_the_venv`,
alongside a guard that the write probe itself still runs at provision time.

⛔ THIS DOES NOT UN-DEVIATE THE RUNNING BOX. `cd5a786b53314777bf59a5cabfd6b690`
is pinned at `2d80803`, which does not contain the line above; its bitsandbytes
was installed by hand and that remains true of the run now in flight. The fix
applies to the next `_w` box, not this one.
